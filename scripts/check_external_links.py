"""Inventory and check external HTTP(S) links in the documentation tree.

The code masking helper follows the behavior of ``check_docs._without_code``
while keeping this scheduled, read-only checker in the Python standard library.
"""

from __future__ import annotations

import argparse
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
import html
import json
import re
import socket
import ssl
import sys
from threading import BoundedSemaphore, Lock
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT = 8.0
DEFAULT_RETRIES = 1
USER_AGENT = "docs-external-link-checker/1.0 (read-only; +https://github.com/)"
MAX_GET_BYTES = 4096
MAX_WORKERS = 4
PER_HOST_WORKERS = 2


@dataclass(frozen=True, order=True)
class Source:
    file: str
    line: int


@dataclass
class Link:
    url: str
    sources: list[Source] = field(default_factory=list)


@dataclass
class CheckResult:
    url: str
    sources: list[Source]
    status: str
    detail: str = ""
    http_status: int | None = None
    method: str | None = None
    final_url: str | None = None


@dataclass
class ResponseInfo:
    status: int
    final_url: str


def _without_code(text: str) -> str:
    """Blank fenced, indented, and inline code while preserving line positions."""
    lines = text.splitlines(keepends=True)
    result: list[str] = []
    fence_char: str | None = None
    fence_size = 0
    for line in lines:
        fence = re.match(r"^ {0,3}(?:> ?)*(`{3,}|~{3,})", line)
        if fence_char is not None:
            close = re.match(
                rf"^ {{0,3}}(?:> ?)*{re.escape(fence_char)}{{{fence_size},}}[ \t]*(?:\r?\n)?$",
                line,
            )
            if close:
                fence_char = None
                fence_size = 0
            result.append("\n" if line.endswith("\n") else "")
            continue
        if fence:
            fence_char = fence.group(1)[0]
            fence_size = len(fence.group(1))
            result.append("\n" if line.endswith("\n") else "")
        elif re.match(r"^ {0,3}(?:> ?)* {4,}", line) or re.match(r"^ {0,3}(?:> ?)*\t", line):
            result.append("\n" if line.endswith("\n") else "")
        else:
            result.append(line)
    text = "".join(result)
    return re.sub(
        r"(`+)(.*?)\1",
        lambda match: "".join("\n" if char == "\n" else " " for char in match.group(0)),
        text,
        flags=re.DOTALL,
    )


def _front_matter_body(text: str) -> str:
    text = text.removeprefix("\ufeff")
    match = re.match(r"\A---[ \t]*\r?\n.*?\r?\n---[ \t]*(?:\r?\n|\Z)", text, re.DOTALL)
    if not match:
        return text
    body = text[match.end():]
    return "\n" * text[:match.end()].count("\n") + body


def _markdown_unescape(value: str) -> str:
    value = html.unescape(value.strip())
    return re.sub(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])", r"\1", value)


def _inline_destination(text: str, open_paren: int) -> tuple[str, int] | None:
    """Read a Markdown link destination, handling angle and balanced forms."""
    start = open_paren + 1
    while start < len(text) and text[start].isspace():
        start += 1
    if start >= len(text):
        return None
    if text[start] == "<":
        end = start + 1
        while end < len(text):
            if text[end] == ">" and (end == 0 or text[end - 1] != "\\"):
                close = text.find(")", end + 1)
                return (text[start + 1:end], close) if close >= 0 else None
            end += 1
        return None

    depth = 0
    escaped = False
    end = start
    while end < len(text):
        char = text[end]
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "(":
            depth += 1
        elif char == ")":
            if depth == 0:
                break
            depth -= 1
        end += 1
    if end >= len(text):
        return None
    destination = text[start:end].strip()
    destination = re.sub(r"\s+[\"'].*[\"']\s*$", "", destination)
    return destination, end


def _normalize_url(value: str) -> str | None:
    """Return a request-safe canonical HTTP(S) URL without a fragment."""
    value = _markdown_unescape(value)
    try:
        parsed = urlsplit(value)
        scheme = parsed.scheme.casefold()
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        return None
    if scheme not in {"http", "https"} or not parsed.netloc or not hostname or any(c.isspace() for c in hostname):
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    try:
        if ":" in hostname:  # IPv6 literals already use ASCII and need brackets in netloc.
            normalized_host = f"[{hostname.casefold()}]"
        else:
            normalized_host = hostname.encode("idna").decode("ascii").casefold()
    except UnicodeError:
        return None

    if port is not None and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        normalized_host += f":{port}"
    netloc = normalized_host

    def encode_component(component: str, safe: str) -> str:
        component = re.sub(r"%(?![a-fA-F0-9]{2})", "%25", component)
        quoted = quote(component, safe=safe)
        return re.sub(r"%[a-fA-F0-9]{2}", lambda match: match.group().upper(), quoted)

    path = encode_component(parsed.path or "/", "/%:@!$&'()*+,;=-._~")
    query = encode_component(parsed.query, "/?%:@!$&'()*+,;=-._~")
    return urlunsplit((scheme, netloc, path, query, ""))


def _http_url(value: str) -> str | None:
    return _normalize_url(value)


def extract_links(markdown: str, display_path: str) -> list[Link]:
    """Extract external HTTP(S) destinations and their Markdown source lines."""
    text = _without_code(_front_matter_body(markdown))
    found: dict[str, set[Source]] = {}
    covered = bytearray(len(text))

    def cover(start: int, end: int) -> None:
        start = max(0, start)
        end = min(len(text), end)
        if end > start:
            covered[start:end] = b"\1" * (end - start)

    def add(raw_url: str, offset: int) -> None:
        url = _http_url(raw_url)
        if url:
            found.setdefault(url, set()).add(Source(display_path, text.count("\n", 0, offset) + 1))

    # Definitions are removed from the reference scan; references use the line
    # where the destination appears in rendered content as the source location.
    definitions: dict[str, tuple[str, int]] = {}
    definition_lines: list[tuple[int, int]] = []
    definition_re = re.compile(r"(?m)^ {0,3}\[([^\]]+)\]:\s*(<[^>]*>|\S+)(?:\s+.*)?$")
    for match in definition_re.finditer(text):
        raw = match.group(2)
        destination = raw[1:-1] if raw.startswith("<") and raw.endswith(">") else raw
        definitions[" ".join(match.group(1).split()).casefold()] = (destination, match.start())
        definition_lines.append((match.start(), match.end()))
        cover(match.start(), match.end())
    reference_text = list(text)
    for start, end in definition_lines:
        for index in range(start, end):
            if reference_text[index] != "\n":
                reference_text[index] = " "
    reference_text = "".join(reference_text)

    # Inline Markdown links and images, including nested parentheses in URLs.
    inline_re = re.compile(r"!?\[(?:[^\[\]\n]|\[[^\[\]\n]*\])*\]\s*\(")
    for match in inline_re.finditer(text):
        parsed = _inline_destination(text, match.end() - 1)
        if parsed:
            add(parsed[0], match.start())
            cover(match.start(), parsed[1] + 1)

    # Full, collapsed, and shortcut reference links/images.
    ref_re = re.compile(r"!?\[((?:[^\[\]\n]|\[[^\[\]\n]*\])+)\](?:\s*\[([^\]\n]*)\])?")
    for match in ref_re.finditer(reference_text):
        if match.end() < len(reference_text) and reference_text[match.end()] == "(":
            continue
        label = match.group(2) or match.group(1)
        item = definitions.get(" ".join(label.split()).casefold())
        if item:
            add(item[0], match.start())
            add(item[0], item[1])

    # CommonMark autolinks and HTML anchor/image/media attributes.
    for match in re.finditer(r"<((?:https?://)[^\s<>]+)>", text, flags=re.IGNORECASE):
        add(match.group(1), match.start())
        cover(match.start(), match.end())

    line_offsets = [0]
    line_offsets.extend(match.end() for match in re.finditer("\n", text))

    class LinkTagParser(HTMLParser):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            line, column = self.getpos()
            tag_offset = line_offsets[line - 1] + column
            raw_tag = self.get_starttag_text() or ""
            cover(tag_offset, tag_offset + len(raw_tag))
            names = {
                "a": {"href"},
                "img": {"src"},
                "source": {"src"},
                "video": {"src"},
                "audio": {"src"},
                "iframe": {"src"},
                "embed": {"src"},
                "track": {"src"},
            }
            for name, value in attrs:
                if value and name.casefold() in names.get(tag.casefold(), set()):
                    # HTMLParser exposes a line and column but not an absolute offset.
                    url = _http_url(value)
                    if url:
                        found.setdefault(url, set()).add(Source(display_path, line))

    parser = LinkTagParser(convert_charrefs=True)
    parser.feed(text)

    # Bare web URLs are commonly rendered as links by site extensions and are
    # useful to inventory even where the Markdown flavor treats them as text.
    bare_re = re.compile(r"https?://[^\s<>\]\[\"'，。；：！？、）】》」』”’]+", flags=re.IGNORECASE)
    for match in bare_re.finditer(text):
        if any(covered[match.start():match.end()]):
            continue
        value = match.group(0).rstrip(".,;:!?")
        while value.endswith(")") and value.count(")") > value.count("("):
            value = value[:-1]
        add(value, match.start())

    return [Link(url, sorted(sources)) for url, sources in sorted(found.items())]


def inventory(root: Path) -> list[Link]:
    docs_dir = root.resolve() / "docs"
    merged: dict[str, set[Source]] = {}
    for path in sorted(docs_dir.rglob("*.md")):
        relative = path.relative_to(root.resolve()).as_posix()
        for link in extract_links(path.read_text(encoding="utf-8"), relative):
            merged.setdefault(link.url, set()).update(link.sources)
    return [Link(url, sorted(sources)) for url, sources in sorted(merged.items())]


def _exception_status(exc: BaseException) -> tuple[str, str]:
    reason: BaseException = exc.reason if isinstance(exc, URLError) and isinstance(exc.reason, BaseException) else exc
    if isinstance(reason, (socket.timeout, TimeoutError)):
        return "timeout", str(reason) or "request timed out"
    if isinstance(reason, ssl.SSLError):
        return "tls_error", str(reason)
    if isinstance(exc, ssl.SSLError):
        return "tls_error", str(exc)
    return "network_error", str(reason) or reason.__class__.__name__


def _request_once(url: str, method: str, timeout: float) -> ResponseInfo:
    request = Request(url, method=method, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urlopen(request, timeout=timeout) as response:
            if method == "GET":
                response.read(MAX_GET_BYTES)
            final_url = _normalize_url(response.geturl()) or response.geturl()
            return ResponseInfo(response.status, final_url)
    except HTTPError as exc:
        try:
            final_url = _normalize_url(exc.geturl()) or exc.geturl()
            return ResponseInfo(exc.code, final_url)
        finally:
            exc.close()


def _classify_response(response: ResponseInfo, original_url: str, method: str) -> CheckResult:
    status = response.status
    if status in (404, 410):
        category = "not_found"
    elif status in (401, 403):
        category = "restricted"
    elif status == 429:
        category = "rate_limited"
    elif 400 <= status < 600:
        category = "http_error"
    elif 300 <= status < 400 or (200 <= status < 300 and response.final_url != original_url):
        category = "redirected"
    elif 200 <= status < 300:
        category = "success"
    else:
        category = "http_error"
    detail = ""
    if category == "redirected" and response.final_url != original_url:
        detail = f"final URL: {response.final_url}"
    return CheckResult(
        original_url,
        [],
        category,
        detail=detail,
        http_status=status,
        method=method,
        final_url=response.final_url,
    )


def check_link(link: Link, timeout: float = DEFAULT_TIMEOUT, retries: int = DEFAULT_RETRIES) -> CheckResult:
    """Check one URL, confirming HEAD 404/410 with one bounded GET."""
    method = "HEAD"
    for current_method in ("HEAD", "GET"):
        method = current_method
        attempts = retries + 1
        for attempt in range(attempts):
            try:
                response = _request_once(link.url, method, timeout)
            except (HTTPError, URLError, OSError, ssl.SSLError, TimeoutError) as exc:
                status, detail = _exception_status(exc)
                result = CheckResult(link.url, link.sources, status, detail=detail, method=method)
                retryable = status in {"timeout", "network_error"}
            else:
                result = _classify_response(response, link.url, method)
                retryable = result.status == "http_error" and bool(result.http_status and result.http_status >= 500)

            if retryable and attempt + 1 < attempts:
                time.sleep(min(0.25 * (attempt + 1), 1.0))
                continue

            # Confirm permanent failures with GET; some sites reject HEAD generally.
            if method == "HEAD" and result.http_status in {404, 410, 405, 501}:
                break
            if method == "GET" and result.http_status in {404, 410}:
                result.status = "permanent_failure"
            result.sources = link.sources
            return result
        else:
            result.sources = link.sources
            return result
    result.sources = link.sources
    return result


def _not_checked(link: Link, detail: str) -> CheckResult:
    return CheckResult(link.url, link.sources, "not_checked", detail=detail)


def _check_with_host_limit(
    link: Link,
    timeout: float,
    retries: int,
    deadline: float | None,
    host_semaphores: dict[str, BoundedSemaphore],
    semaphore_lock: Lock,
) -> CheckResult:
    host = (urlsplit(link.url).hostname or "").casefold()
    with semaphore_lock:
        semaphore = host_semaphores.setdefault(host, BoundedSemaphore(PER_HOST_WORKERS))
    with semaphore:
        if deadline is not None and time.monotonic() >= deadline:
            return _not_checked(link, "time budget reached before request")
        return check_link(link, timeout=timeout, retries=retries)


def check_links(
    links: list[Link],
    *,
    timeout: float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    limit: int | None = None,
    max_seconds: float | None = None,
    workers: int = MAX_WORKERS,
    inventory_only: bool = False,
) -> list[CheckResult]:
    """Check links concurrently with stable result order and bounded scheduling."""
    if not 1 <= workers <= MAX_WORKERS:
        raise ValueError(f"workers must be between 1 and {MAX_WORKERS}")
    selected_end = len(links) if limit is None else min(len(links), limit)
    results: list[CheckResult | None] = [None] * len(links)
    for index, link in enumerate(links):
        if inventory_only:
            results[index] = _not_checked(link, "inventory only")
        elif index >= selected_end:
            results[index] = _not_checked(link, "outside --limit")
    if inventory_only or selected_end == 0:
        return [result for result in results if result is not None]

    deadline = time.monotonic() + max_seconds if max_seconds is not None else None
    host_semaphores: dict[str, BoundedSemaphore] = {}
    semaphore_lock = Lock()
    next_index = 0
    pending: dict[Future[CheckResult], int] = {}
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="link-check") as executor:
        while next_index < selected_end or pending:
            while next_index < selected_end and len(pending) < workers:
                if deadline is not None and time.monotonic() >= deadline:
                    break
                link = links[next_index]
                future = executor.submit(
                    _check_with_host_limit,
                    link,
                    timeout,
                    retries,
                    deadline,
                    host_semaphores,
                    semaphore_lock,
                )
                pending[future] = next_index
                next_index += 1

            if pending:
                wait_timeout = None
                if next_index < selected_end and deadline is not None:
                    wait_timeout = max(0.0, deadline - time.monotonic())
                completed, _ = wait(pending, timeout=wait_timeout, return_when=FIRST_COMPLETED)
                if not completed and deadline is not None and time.monotonic() >= deadline:
                    for index in range(next_index, selected_end):
                        results[index] = _not_checked(links[index], "time budget reached")
                    next_index = selected_end
                    completed, _ = wait(pending, return_when=FIRST_COMPLETED)
                for future in completed:
                    index = pending.pop(future)
                    results[index] = future.result()
            elif next_index < selected_end:
                for index in range(next_index, selected_end):
                    results[index] = _not_checked(links[index], "time budget reached")
                next_index = selected_end

    return [result for result in results if result is not None]


def _summary(results: list[CheckResult]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    return dict(sorted(counts.items()))


def _json_document(results: list[CheckResult], inventory_count: int) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inventory_count": inventory_count,
        "checked_count": sum(item.status != "not_checked" for item in results),
        "summary": _summary(results),
        "results": [asdict(item) for item in results],
    }


def _markdown_report(results: list[CheckResult], inventory_count: int) -> str:
    lines = [
        "# External link check",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- URLs in inventory: {inventory_count}",
        f"- Checked URLs: {sum(item.status != 'not_checked' for item in results)}",
        "- Summary: " + (", ".join(f"{name}: {count}" for name, count in _summary(results).items()) or "no URLs"),
        "",
        "| Status | HTTP | URL | Source | Detail |",
        "|---|---:|---|---|---|",
    ]
    for item in results:
        source_text = "<br>".join(f"{source.file}:{source.line}" for source in item.sources)
        cells = [item.status, str(item.http_status or ""), item.url, source_text, item.detail]
        lines.append("| " + " | ".join(value.replace("|", "\\|").replace("\n", " ") for value in cells) + " |")
    lines.append("")
    lines.extend([
        "The checker scans Markdown inline and reference links, images, CommonMark autolinks, HTML `href`/`src`, and bare HTTP(S) URLs.",
        "It ignores fenced, indented, and inline code. It does not evaluate MkDocs macros, JavaScript-generated URLs, HTML `srcset`, or custom Markdown extensions that synthesize links.",
        "A 2xx response after a redirect is reported as redirected; the HTTP status alone does not confirm that the target page content is readable.",
        "HTTP 401/403/429, transient network failures, timeouts, TLS failures, and other HTTP errors are reported separately; strict mode fails only after a GET confirms 404/410.",
    ])
    return "\n".join(lines)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def _positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return number


def _nonnegative_int(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return number


def _worker_count(value: str) -> int:
    number = int(value)
    if not 1 <= number <= MAX_WORKERS:
        raise argparse.ArgumentTypeError(f"must be between 1 and {MAX_WORKERS}")
    return number


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Inventory and check external links in docs Markdown.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="repository root")
    parser.add_argument("--output", type=Path, help="write a UTF-8 JSON report to this path")
    parser.add_argument("--report", type=Path, help="write a UTF-8 Markdown report to this path")
    parser.add_argument("--inventory-only", action="store_true", help="collect URLs without making network requests")
    parser.add_argument("--timeout", type=_positive_float, default=DEFAULT_TIMEOUT, help=f"per-request timeout in seconds (default: {DEFAULT_TIMEOUT:g})")
    parser.add_argument("--retries", type=_nonnegative_int, default=DEFAULT_RETRIES, help="retries for timeouts, network failures, and HTTP 5xx (default: 1)")
    parser.add_argument("--limit", type=_nonnegative_int, help="check at most this many URLs")
    parser.add_argument("--max-seconds", type=_positive_float, help="stop scheduling checks after this time budget; in-flight requests finish")
    parser.add_argument("--workers", type=_worker_count, default=MAX_WORKERS, help=f"worker count, 1-{MAX_WORKERS} (default: {MAX_WORKERS}); at most {PER_HOST_WORKERS} per host")
    parser.add_argument("--strict", action="store_true", help="return nonzero only after GET confirms HTTP 404 or 410")
    args = parser.parse_args(argv)

    links = inventory(args.root)
    results = check_links(
        links,
        timeout=args.timeout,
        retries=args.retries,
        limit=args.limit,
        max_seconds=args.max_seconds,
        workers=args.workers,
        inventory_only=args.inventory_only,
    )

    document = _json_document(results, len(links))
    if args.output:
        _write_text(args.output, json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    if args.report:
        _write_text(args.report, _markdown_report(results, len(links)))
    print(f"External URLs: {len(links)}; checked: {document['checked_count']}; statuses: " + (", ".join(f"{key}={value}" for key, value in document["summary"].items()) or "none"))
    print(f"Source: docs/**/*.md under {args.root.resolve()}")
    if args.output:
        print(f"JSON: {args.output}")
    if args.report:
        print(f"Markdown report: {args.report}")
    for item in results:
        if item.status in {"success", "not_checked"}:
            continue
        locations = ", ".join(f"{source.file}:{source.line}" for source in item.sources)
        code = f" HTTP {item.http_status}" if item.http_status is not None else ""
        suffix = f" — {locations}" if locations else ""
        detail = f" ({item.detail})" if item.detail else ""
        print(f"{item.status}{code}: {item.url}{detail}{suffix}")
    return int(args.strict and any(item.status == "permanent_failure" for item in results))


if __name__ == "__main__":
    sys.exit(main())
