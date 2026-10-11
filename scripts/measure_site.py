"""Measure the built site's static footprint and, on request, HTTP transfers.

The network check streams and discards each explicitly selected HTTP(S) response.
It never evaluates JavaScript or discovers/downloads a dependency tree.
"""

from __future__ import annotations

import argparse
import json
import math
import socket
import ssl
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit, urlunsplit

try:
    import yaml
except ImportError:  # pragma: no cover - MkDocs already depends on PyYAML
    yaml = None


if yaml is not None:
    class _SafeMkDocsConfigLoader(yaml.SafeLoader):
        """SafeLoader that treats MkDocs' Python-name tags as opaque values."""

        def construct_python_name(self, _suffix: str, node: Any) -> None:
            # MkDocs configs can use !!python/name for callback references. This
            # audit only needs plain URL strings, so preserve no executable object.
            self.construct_scalar(node)
            return None

    _SafeMkDocsConfigLoader.add_multi_constructor(
        "tag:yaml.org,2002:python/name:", _SafeMkDocsConfigLoader.construct_python_name
    )
else:  # pragma: no cover - dependency-free fallback is exercised only without MkDocs
    _SafeMkDocsConfigLoader = None


DEFAULT_TIMEOUT = 15.0
DEFAULT_TOP_N = 10
LARGE_FILE_BYTES = 256 * 1024
CHUNK_BYTES = 64 * 1024
IMAGE_EXTENSIONS = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
FONT_EXTENSIONS = {".eot", ".otf", ".ttf", ".woff", ".woff2"}


def _category(path: Path) -> str:
    suffix = path.suffix.lower()
    if path.name.lower() == "search_index.json" or "search_index" in path.name.lower():
        return "search_index"
    if suffix in {".html", ".htm"}:
        return "html"
    if suffix in {".js", ".mjs"}:
        return "javascript"
    if suffix == ".css":
        return "css"
    if suffix in IMAGE_EXTENSIONS:
        return "images"
    if suffix in FONT_EXTENSIONS:
        return "fonts"
    return "other"


def _http_url(value: str) -> str | None:
    """Return a fragment-free HTTP(S) URL, or None for unsupported/unsafe input."""
    try:
        parsed = urlsplit(value.strip())
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            return None
        # Avoid putting credentials in requests, output reports, or logs.
        if parsed.username is not None or parsed.password is not None:
            return None
        _ = parsed.port  # Validate malformed ports before passing to urllib.
    except (ValueError, AttributeError):
        return None
    return urlunsplit((parsed.scheme.lower(), parsed.netloc, parsed.path, parsed.query, ""))


def read_external_javascript_urls(config_path: Path) -> tuple[list[str], list[str]]:
    """Read HTTP(S) extra_javascript URLs and identify the MathJax entries."""
    if not config_path.is_file():
        return [], [f"MkDocs config not found: {config_path}"]
    try:
        content = config_path.read_text(encoding="utf-8")
        if yaml is not None:
            config = yaml.load(content, Loader=_SafeMkDocsConfigLoader) or {}
            entries = config.get("extra_javascript", []) if isinstance(config, dict) else []
        else:
            # Keep the script usable with the standard library if PyYAML is absent.
            import re

            block = re.search(r"(?ms)^extra_javascript:\s*\n((?:^[ \t]+.*\n?)*)", content)
            entries = re.findall(r"https?://[^\s'\"]+", block.group(1)) if block else []
        if not isinstance(entries, list):
            return [], ["mkdocs.yml extra_javascript must be a list"]
        urls = []
        for entry in entries:
            if isinstance(entry, str):
                url = _http_url(entry)
                if url:
                    urls.append(url)
        urls = list(dict.fromkeys(urls))
        mathjax = [url for url in urls if "mathjax" in url.casefold()]
        return urls, []
    except (OSError, UnicodeError) as exc:
        return [], [f"Could not read MkDocs config: {type(exc).__name__}"]
    except Exception as exc:
        return [], [f"Could not parse MkDocs config: {type(exc).__name__}"]


def audit_site(site_dir: Path, config_path: Path, *, top_n: int = DEFAULT_TOP_N) -> dict[str, Any]:
    """Collect deterministic file sizes and classify the built site."""
    if not site_dir.is_dir():
        raise FileNotFoundError(f"Built site directory does not exist: {site_dir}")

    totals: dict[str, dict[str, int]] = {}
    files: list[dict[str, Any]] = []
    for path in sorted(site_dir.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(site_dir).as_posix()
        size = path.stat().st_size
        category = _category(path)
        bucket = totals.setdefault(category, {"files": 0, "bytes": 0})
        bucket["files"] += 1
        bucket["bytes"] += size
        files.append({"path": relative, "bytes": size, "category": category})

    def largest(group: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        # Stable path ordering makes reports reproducible when sizes tie.
        return sorted(group, key=lambda row: (-row["bytes"], row["path"]))[:top_n]

    html_files = [item for item in files if item["category"] == "html"]
    resources = [item for item in files if item["category"] != "html"]
    javascript_urls, config_errors = read_external_javascript_urls(config_path)
    mathjax_urls = [url for url in javascript_urls if "mathjax" in url.casefold()]
    total_bytes = sum(bucket["bytes"] for bucket in totals.values())

    return {
        "site_dir": str(site_dir),
        "file_count": len(files),
        "total_bytes": total_bytes,
        "large_file_threshold_bytes": LARGE_FILE_BYTES,
        "totals": {name: totals[name] for name in sorted(totals)},
        "large_html_pages": [row for row in largest(html_files) if row["bytes"] >= LARGE_FILE_BYTES],
        "largest_html_pages": largest(html_files),
        "large_resources": [row for row in largest(resources) if row["bytes"] >= LARGE_FILE_BYTES],
        "largest_resources": largest(resources),
        "external_javascript_urls": javascript_urls,
        "external_mathjax_urls": mathjax_urls,
        "config_errors": config_errors,
    }


def _failure_class(exc: BaseException) -> str:
    if isinstance(exc, (socket.timeout, TimeoutError)):
        return "timeout"
    if isinstance(exc, ssl.SSLError):
        return "tls_error"
    if isinstance(exc, socket.gaierror):
        return "dns_error"
    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        if isinstance(reason, (socket.timeout, TimeoutError)):
            return "timeout"
        if isinstance(reason, ssl.SSLError):
            return "tls_error"
        if isinstance(reason, socket.gaierror):
            return "dns_error"
        return "connection_error"
    if isinstance(exc, OSError):
        return "connection_error"
    return "request_error"


def _read_response(response: Any, *, start: float, status: int | None) -> dict[str, Any]:
    headers_at = time.perf_counter()
    byte_count = 0
    read_error: BaseException | None = None
    try:
        while True:
            chunk = response.read(CHUNK_BYTES)
            if not chunk:
                break
            byte_count += len(chunk)
    except Exception as exc:  # Report interrupted body reads as a sample failure.
        read_error = exc
    end = time.perf_counter()
    result: dict[str, Any] = {
        "status": status,
        "bytes": byte_count,
        # Includes name resolution, connection, TLS, request, and response headers.
        "time_to_headers_ms": round((headers_at - start) * 1000, 3),
        "body_download_ms": round((end - headers_at) * 1000, 3),
        "total_ms": round((end - start) * 1000, 3),
        "completed": read_error is None,
        "error_class": None,
        "error": None,
    }
    if read_error is not None:
        failure = _failure_class(read_error)
        result["error_class"] = failure if failure in {"timeout", "tls_error"} else "read_error"
        result["error"] = type(read_error).__name__
    elif status is None or not 200 <= status < 300:
        result["error_class"] = "http_status"
        result["error"] = f"HTTP {status}" if status is not None else "Missing HTTP status"
    return result


def measure_url(url: str, *, samples: int = 3, timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Stream an HTTP(S) response for each sample, discarding its contents."""
    normalized_url = _http_url(url)
    sample_rows: list[dict[str, Any]] = []
    if samples < 1:
        raise ValueError("samples must be at least 1")
    if timeout <= 0 or not math.isfinite(timeout):
        raise ValueError("timeout must be a positive finite number")

    if normalized_url is None:
        for index in range(1, samples + 1):
            sample_rows.append({
                "sample": index,
                "status": None,
                "bytes": 0,
                "time_to_headers_ms": None,
                "body_download_ms": None,
                "total_ms": None,
                "completed": False,
                "error_class": "invalid_url",
                "error": "Only credential-free HTTP(S) URLs are accepted",
            })
    else:
        request = urllib.request.Request(
            normalized_url,
            headers={"User-Agent": "MkDocsSiteMeasurement/1.0 (+static performance audit)"},
            method="GET",
        )
        tls_context = ssl.create_default_context()
        for index in range(1, samples + 1):
            start = time.perf_counter()
            try:
                response = urllib.request.urlopen(request, timeout=timeout, context=tls_context)
            except urllib.error.HTTPError as exc:
                # HTTPError is also a response stream; count its body and retain status.
                try:
                    row = _read_response(exc, start=start, status=exc.code)
                finally:
                    exc.close()
            except Exception as exc:
                row = {
                    "status": None,
                    "bytes": 0,
                    "time_to_headers_ms": None,
                    "body_download_ms": None,
                    "total_ms": round((time.perf_counter() - start) * 1000, 3),
                    "completed": False,
                    "error_class": _failure_class(exc),
                    "error": type(exc).__name__,
                }
            else:
                try:
                    row = _read_response(response, start=start, status=response.getcode())
                finally:
                    response.close()
            row["sample"] = index
            sample_rows.append(row)

    successful = [row for row in sample_rows if row["error_class"] is None]
    failures = Counter(row["error_class"] for row in sample_rows if row["error_class"])

    def median(field: str) -> float | None:
        values = [row[field] for row in successful if row[field] is not None]
        return round(statistics.median(values), 3) if values else None

    return {
        "url": normalized_url or url,
        "samples_requested": samples,
        "success_count": len(successful),
        "failure_counts": dict(sorted(failures.items())),
        "successful_median_time_to_headers_ms": median("time_to_headers_ms"),
        "successful_median_body_download_ms": median("body_download_ms"),
        "successful_median_total_ms": median("total_ms"),
        "successful_median_bytes": median("bytes"),
        "samples": sample_rows,
    }


def _markdown_report(data: dict[str, Any]) -> str:
    static = data["static_audit"]
    lines = [
        "# MkDocs site measurement",
        "",
        f"Network label: **{data['network_label']}**",
        "",
        "Static file sizes describe the built files. HTTP values describe streamed transfers for explicitly selected URLs.",
        "`time_to_headers_ms` includes DNS, connection, TLS, request, and response-header time; it is not a pure server TTFB.",
        "HTTP byte counts cover response bodies and exclude headers and protocol framing.",
        "This tool does not run a browser: FCP, LCP, and actual MathJax formula-render time were not measured.",
        "",
        f"Generated at (UTC): {data['generated_at']}",
        "",
        "## Static site",
        "",
        f"Files: {static['file_count']}",
        "",
        f"Total: {static['total_bytes']} bytes",
        "",
        f"Large-file threshold: {static['large_file_threshold_bytes']} bytes",
        "",
        "| Category | Files | Bytes |",
        "|---|---:|---:|",
    ]
    for category, summary in static["totals"].items():
        lines.append(f"| {category} | {summary['files']} | {summary['bytes']} |")
    lines.extend(["", "External MathJax URLs in `mkdocs.yml`:"])
    if static["external_mathjax_urls"]:
        lines.extend(f"- `{url}`" for url in static["external_mathjax_urls"])
    else:
        lines.append("- None found")
    if static["config_errors"]:
        lines.extend(["", "Config notes:"])
        lines.extend(f"- {error}" for error in static["config_errors"])

    def add_files(title: str, items: list[dict[str, Any]]) -> None:
        lines.extend(["", title, ""])
        if not items:
            lines.append("- None")
            return
        lines.extend(["| Path | Bytes |", "|---|---:|"])
        lines.extend(f"| `{item['path']}` | {item['bytes']} |" for item in items)

    add_files("Largest HTML pages", static["largest_html_pages"])
    add_files("Largest non-HTML resources", static["largest_resources"])
    lines.extend(["", "## HTTP measurements", ""])
    if not data["network_requested"]:
        lines.append("Not run. Add `--measure-network` or one or more `--url` arguments to opt in.")
    elif not data["network_measurements"]:
        lines.append("No eligible HTTP(S) URLs were selected.")
    else:
        lines.extend([
            "| URL | Successes | Median headers (ms) | Median body (ms) | Median total (ms) | Median bytes | Failures |",
            "|---|---:|---:|---:|---:|---:|---|",
        ])
        for item in data["network_measurements"]:
            failures = ", ".join(f"{name}: {count}" for name, count in item["failure_counts"].items()) or "None"
            lines.append(
                f"| `{item['url']}` | {item['success_count']}/{item['samples_requested']} | "
                f"{item['successful_median_time_to_headers_ms']} | {item['successful_median_body_download_ms']} | "
                f"{item['successful_median_total_ms']} | {item['successful_median_bytes']} | {failures} |"
            )
        for item in data["network_measurements"]:
            lines.extend(["", f"Samples for `{item['url']}`:", ""])
            for row in item["samples"]:
                detail = f"HTTP {row['status']}" if row["status"] is not None else row["error_class"]
                lines.append(
                    f"- #{row['sample']}: {detail}; {row['bytes']} bytes; "
                    f"total {row['total_ms']} ms"
                    + (f" ({row['error']})" if row["error"] else "")
                )
    lines.append("")
    return "\n".join(lines)


def _write_text(path: str | None, content: str) -> None:
    if path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site", type=Path, default=Path("site"), help="built MkDocs directory (default: site)")
    parser.add_argument("--config", type=Path, default=Path("mkdocs.yml"), help="MkDocs config (default: mkdocs.yml)")
    parser.add_argument("--output", metavar="JSON", help="write machine-readable JSON to this path")
    parser.add_argument("--report", metavar="MARKDOWN", help="write a human-readable Markdown report")
    parser.add_argument("--samples", type=int, default=3, help="HTTP samples per URL (default: 3)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help=f"per-request timeout in seconds (default: {DEFAULT_TIMEOUT:g})")
    parser.add_argument("--network-label", default="unspecified", help="operator-provided network label; no network simulation is performed")
    parser.add_argument("--measure-network", action="store_true", help="measure HTTP(S) JavaScript URLs from mkdocs.yml")
    parser.add_argument("--url", action="append", nargs="+", default=[], metavar="URL", help="explicit HTTP(S) URL(s) to measure; repeatable")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.samples < 1:
        parser.error("--samples must be at least 1")
    if args.timeout <= 0 or not math.isfinite(args.timeout):
        parser.error("--timeout must be a positive finite number")

    try:
        static = audit_site(args.site, args.config)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    explicit_urls = [url for group in args.url for url in group]
    network_urls = list(dict.fromkeys(explicit_urls))
    if args.measure_network:
        configured, _ = read_external_javascript_urls(args.config)
        network_urls = list(dict.fromkeys(configured + network_urls))

    measurements = [measure_url(url, samples=args.samples, timeout=args.timeout) for url in network_urls]
    data = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "network_requested": bool(args.measure_network or explicit_urls),
        "network_label": args.network_label,
        "network_label_note": "Operator supplied; this tool does not emulate or infer a network type.",
        "limitations": [
            "Static file sizes do not measure browser transfer scheduling or cache behavior.",
            "HTTP time_to_headers_ms includes DNS, connection, TLS, request, and response-header time; it is not pure server TTFB.",
            "FCP, LCP, and actual MathJax formula-render time require browser instrumentation and are not measured.",
            "HTTP byte counts cover response bodies, excluding headers and protocol framing; bodies are streamed and discarded.",
            "JavaScript is never executed.",
        ],
        "static_audit": static,
        "network_measurements": measurements,
    }
    json_text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        _write_text(args.output, json_text)
    if args.report:
        _write_text(args.report, _markdown_report(data))
    if not args.output and not args.report:
        sys.stdout.write(json_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
