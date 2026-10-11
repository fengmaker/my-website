import contextlib
import http.server
import io
import json
import socket
import tempfile
import threading
import time
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from measure_site import audit_site, main, measure_url, read_external_javascript_urls


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/slow":
            time.sleep(0.2)
            body = b"late"
            status = 200
        elif self.path == "/status":
            body = b"temporarily unavailable"
            status = 503
        else:
            body = b"small local payload"
            status = 200
        self.send_response(status)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except OSError:
            pass

    def log_message(self, _format, *_args):
        pass


class MeasureSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.server.daemon_threads = True
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def _site(self, root: Path):
        site = root / "site"
        (site / "search").mkdir(parents=True)
        (site / "assets").mkdir()
        (site / "index.html").write_bytes(b"<html>home</html>")
        (site / "search" / "search_index.json").write_bytes(b'{"docs": []}')
        (site / "assets" / "app.js").write_bytes(b"let app = true;")
        (site / "assets" / "site.css").write_bytes(b"body { color: black; }")
        (site / "assets" / "large.bin").write_bytes(b"x" * (256 * 1024 + 1))
        config = root / "mkdocs.yml"
        config.write_text(
            "extra_javascript:\n"
            "  - javascripts/mathjax.js\n"
            "  - https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js\n",
            encoding="utf-8",
        )
        return site, config

    def test_static_audit_categorizes_sizes_and_mathjax_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            site, config = self._site(Path(tmp))
            report = audit_site(site, config)

        self.assertEqual(report["file_count"], 5)
        self.assertEqual(report["totals"]["html"]["files"], 1)
        self.assertEqual(report["totals"]["search_index"]["bytes"], len(b'{"docs": []}'))
        self.assertEqual(report["totals"]["javascript"]["files"], 1)
        self.assertEqual(report["totals"]["css"]["files"], 1)
        self.assertEqual(len(report["large_resources"]), 1)
        self.assertEqual(report["external_mathjax_urls"], [
            "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
        ])

    def test_config_parse_failure_is_reported_and_missing_site_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = root / "site"
            site.mkdir()
            config = root / "mkdocs.yml"
            config.write_text("extra_javascript: [unterminated\n", encoding="utf-8")
            _urls, errors = read_external_javascript_urls(config)
            self.assertTrue(errors)

            with self.assertRaises(FileNotFoundError):
                audit_site(root / "missing", config)

    def test_python_name_tags_are_preserved_as_opaque_and_urls_are_extracted(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "mkdocs.yml"
            config.write_text(
                "markdown_extensions:\n"
                "  - pymdownx.emoji:\n"
                "      emoji_index: !!python/name:os.system\n"
                "extra_javascript:\n"
                "  - https://cdn.example.test/mathjax.js\n",
                encoding="utf-8",
            )

            urls, errors = read_external_javascript_urls(config)

        self.assertEqual(errors, [])
        self.assertEqual(urls, ["https://cdn.example.test/mathjax.js"])

    def test_repository_mkdocs_config_parses_with_python_name_tags(self):
        urls, errors = read_external_javascript_urls(ROOT / "mkdocs.yml")

        self.assertEqual(errors, [])
        self.assertTrue(any("mathjax" in url.casefold() for url in urls))

    def test_successful_http_samples_include_full_body_size_and_timing(self):
        result = measure_url(f"{self.base_url}/ok", samples=2, timeout=2)

        self.assertEqual(result["success_count"], 2)
        self.assertEqual(result["successful_median_bytes"], len(b"small local payload"))
        for sample in result["samples"]:
            self.assertEqual(sample["status"], 200)
            self.assertTrue(sample["completed"])
            self.assertIsNotNone(sample["time_to_headers_ms"])
            self.assertIsNotNone(sample["body_download_ms"])

    def test_http_status_is_counted_and_classified(self):
        result = measure_url(f"{self.base_url}/status", samples=1, timeout=2)

        self.assertEqual(result["success_count"], 0)
        self.assertEqual(result["failure_counts"], {"http_status": 1})
        self.assertEqual(result["samples"][0]["status"], 503)
        self.assertEqual(result["samples"][0]["bytes"], len(b"temporarily unavailable"))

    def test_timeout_and_invalid_url_have_clear_failure_classes(self):
        slow = measure_url(f"{self.base_url}/slow", samples=1, timeout=0.03)
        invalid = measure_url("file:///etc/passwd", samples=2)

        self.assertEqual(slow["failure_counts"], {"timeout": 1})
        self.assertEqual(invalid["failure_counts"], {"invalid_url": 2})
        self.assertEqual(invalid["samples"][0]["status"], None)

    def test_connection_failure_classification(self):
        with mock.patch(
            "measure_site.urllib.request.urlopen",
            side_effect=urllib.error.URLError(socket.gaierror("name resolution failed")),
        ):
            result = measure_url("https://example.invalid/resource", samples=1)

        self.assertEqual(result["failure_counts"], {"dns_error": 1})

    def test_cli_default_is_offline_and_writes_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site, config = self._site(root)
            json_path = root / "out" / "audit.json"
            markdown_path = root / "out" / "audit.md"
            with contextlib.redirect_stdout(io.StringIO()):
                code = main([
                    "--site", str(site), "--config", str(config),
                    "--output", str(json_path), "--report", str(markdown_path),
                ])

            data = json.loads(json_path.read_text(encoding="utf-8"))
            markdown = markdown_path.read_text(encoding="utf-8")

        self.assertEqual(code, 0)
        self.assertFalse(data["network_requested"])
        self.assertEqual(data["network_measurements"], [])
        self.assertRegex(data["generated_at"], r"Z$")
        self.assertIn("FCP, LCP", markdown)
        self.assertIn("Generated at (UTC):", markdown)
        self.assertTrue(all(line == line.rstrip() for line in markdown.splitlines()))
        self.assertIn("Not run.", markdown)

    def test_cli_explicit_url_opts_into_network_samples(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site, config = self._site(root)
            output = root / "audit.json"
            with contextlib.redirect_stdout(io.StringIO()):
                code = main([
                    "--site", str(site), "--config", str(config),
                    "--url", f"{self.base_url}/ok", "--samples", "1",
                    "--network-label", "local test server", "--output", str(output),
                ])
            data = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertTrue(data["network_requested"])
        self.assertEqual(data["network_label"], "local test server")
        self.assertEqual(len(data["network_measurements"]), 1)
        self.assertEqual(data["network_measurements"][0]["success_count"], 1)

    def test_cli_measure_network_uses_only_configured_http_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site, config = self._site(root)
            config.write_text(
                f"extra_javascript:\n  - {self.base_url}/mathjax.js\n",
                encoding="utf-8",
            )
            output = root / "audit.json"
            with contextlib.redirect_stdout(io.StringIO()):
                code = main([
                    "--site", str(site), "--config", str(config),
                    "--measure-network", "--samples", "1", "--output", str(output),
                ])
            data = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(data["network_measurements"][0]["url"], f"{self.base_url}/mathjax.js")
        self.assertEqual(data["network_measurements"][0]["success_count"], 1)

    def test_samples_and_timeout_must_be_positive(self):
        with self.assertRaises(ValueError):
            measure_url("https://example.invalid/", samples=0)
        with self.assertRaises(ValueError):
            measure_url("https://example.invalid/", timeout=0)


if __name__ == "__main__":
    unittest.main()
