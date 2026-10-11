import json
import socket
import ssl
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_external_links as checker


class FakeResponse:
    def __init__(self, status=200, url="https://example.test/path"):
        self.status = status
        self.url = url
        self.read_sizes = []
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()

    def geturl(self):
        return self.url

    def read(self, size=-1):
        self.read_sizes.append(size)
        return b"limited body"

    def close(self):
        self.closed = True


def response(status, url="https://example.test/path"):
    return FakeResponse(status, url)


class ExternalLinkExtractionTests(unittest.TestCase):
    def test_extracts_markdown_reference_autolink_html_and_bare_urls_once(self):
        text = """---
title: metadata https://not-rendered.test/
---
[inline](https://example.test/path) and ![image](https://img.test/a.png)
[reference][ref], [collapsed][] and <https://auto.test/>
[ref]: https://reference.test/page
[collapsed]: <https://collapsed.test/page>
<a href="https://html.test/">link</a> <img src='https://img.test/a.png'>
Plain extension URL: http://bare.test/end.
`[sample](https://inline-code.test/)`
```md
[sample](https://fence.test/)
<img src="https://fence-image.test/">
```
    [sample](https://indented.test/)
"""

        links = checker.extract_links(text, "docs/page.md")
        by_url = {link.url: link for link in links}

        self.assertEqual(
            set(by_url),
            {
                "https://example.test/path",
                "https://img.test/a.png",
                "https://auto.test/",
                "https://reference.test/page",
                "https://collapsed.test/page",
                "https://html.test/",
                "http://bare.test/end",
            },
        )
        self.assertEqual(
            by_url["https://img.test/a.png"].sources,
            [checker.Source("docs/page.md", 4), checker.Source("docs/page.md", 8)],
        )
        self.assertEqual(
            by_url["https://reference.test/page"].sources,
            [checker.Source("docs/page.md", 5), checker.Source("docs/page.md", 6)],
        )
        self.assertFalse(any("code.test" in link.url or "fence.test" in link.url for link in links))

    def test_duplicate_urls_merge_file_locations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "a.md").write_text("[a](https://same.test/)\n", encoding="utf-8")
            (docs / "b.md").write_text("<https://same.test/>\n", encoding="utf-8")

            links = checker.inventory(root)

        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].url, "https://same.test/")
        self.assertEqual([source.file for source in links[0].sources], ["docs/a.md", "docs/b.md"])

    def test_normalizes_unicode_urls_and_deduplicates_fragments(self):
        text = """[unicode](https://例子.测试/路径?q=你好#section)
[ascii](https://xn--fsqu00a.xn--0zwm56d/%E8%B7%AF%E5%BE%84?q=%E4%BD%A0%E5%A5%BD#other)
"""

        links = checker.extract_links(text, "docs/page.md")

        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].url, "https://xn--fsqu00a.xn--0zwm56d/%E8%B7%AF%E5%BE%84?q=%E4%BD%A0%E5%A5%BD")
        self.assertEqual(len(links[0].sources), 2)

    def test_bare_scanner_skips_parsed_destinations_and_trims_chinese_punctuation(self):
        text = """[official](https://developers.google.com/optimization/scheduling/job_shop)。FJSP
[reference][source]
[source]: https://reference.test/page
[unused]: https://unused-reference.test/page
<a href="https://html.test/path">HTML link</a>
<span data-note="https://html-attribute.test/not-a-link">Text</span>
<https://auto.test/path>、后文
Bare balanced URL: https://bare.test/a_(b)。后文
Bare unmatched URL: https://bare.test/path)。后文
Unicode URL: https://例子.测试/路径?q=你好，后文
"""

        links = checker.extract_links(text, "docs/page.md")

        self.assertEqual(
            {link.url for link in links},
            {
                "https://developers.google.com/optimization/scheduling/job_shop",
                "https://reference.test/page",
                "https://html.test/path",
                "https://auto.test/path",
                "https://bare.test/a_(b)",
                "https://bare.test/path",
                "https://xn--fsqu00a.xn--0zwm56d/%E8%B7%AF%E5%BE%84?q=%E4%BD%A0%E5%A5%BD",
            },
        )

    def test_urls_with_user_or_password_are_excluded(self):
        self.assertIsNone(checker._http_url("https://user:secret@example.test/path"))
        self.assertIsNone(checker._http_url("https://user@example.test/path"))
        links = checker.extract_links("[private](https://user:secret@example.test/path)", "docs/private.md")
        self.assertEqual(links, [])

    def test_multiline_inline_code_preserves_later_source_line_numbers(self):
        text = """An inline span starts here: `sample
https://ignored.test/example`
[actual](https://line-number.test/path)
"""

        links = checker.extract_links(text, "docs/lines.md")

        self.assertEqual([link.url for link in links], ["https://line-number.test/path"])
        self.assertEqual(links[0].sources, [checker.Source("docs/lines.md", 3)])


class ExternalLinkRequestTests(unittest.TestCase):
    def test_request_uses_normalized_fragment_free_url(self):
        expected = "https://xn--fsqu00a.xn--0zwm56d/%E8%B7%AF%E5%BE%84"
        url = checker._http_url("https://例子.测试/路径#section")
        with patch.object(checker, "urlopen", return_value=response(200, expected)) as open_url:
            checker.check_link(checker.Link(url))

        self.assertEqual(open_url.call_args.args[0].full_url, expected)

    def test_http_categories_and_429_is_not_retried(self):
        for code, expected in ((401, "restricted"), (403, "restricted"), (429, "rate_limited")):
            with self.subTest(code=code), patch.object(checker, "urlopen", return_value=response(code)) as open_url:
                result = checker.check_link(checker.Link("https://example.test/path"), retries=2)

            self.assertEqual(result.status, expected)
            self.assertEqual(result.http_status, code)
            self.assertEqual(open_url.call_count, 1)

    def test_head_404_and_410_require_get_confirmation(self):
        for code in (404, 410):
            with self.subTest(code=code), patch.object(checker, "urlopen", side_effect=[response(code), response(code)]) as open_url:
                result = checker.check_link(checker.Link("https://example.test/path"))
            self.assertEqual(result.status, "permanent_failure")
            self.assertEqual(result.http_status, code)
            self.assertEqual(result.method, "GET")
            self.assertEqual(open_url.call_count, 2)

        with patch.object(checker, "urlopen", side_effect=[response(404), response(200)]) as open_url:
            recovered = checker.check_link(checker.Link("https://example.test/path"))
        self.assertEqual(recovered.status, "success")
        self.assertEqual(open_url.call_count, 2)

    def test_unsupported_head_falls_back_to_small_get(self):
        get_response = response(200)
        with patch.object(checker, "urlopen", side_effect=[response(405), get_response]) as open_url:
            result = checker.check_link(checker.Link("https://example.test/path"))

        self.assertEqual(result.status, "success")
        self.assertEqual(result.method, "GET")
        self.assertEqual([call.args[0].get_method() for call in open_url.call_args_list], ["HEAD", "GET"])
        self.assertEqual(get_response.read_sizes, [checker.MAX_GET_BYTES])

    def test_redirects_are_a_distinct_success_category(self):
        target = response(200, "https://example.test/new-path")
        with patch.object(checker, "urlopen", return_value=target):
            result = checker.check_link(checker.Link("https://example.test/path"))

        self.assertEqual(result.status, "redirected")
        self.assertEqual(result.final_url, "https://example.test/new-path")

        with patch.object(checker, "urlopen", return_value=response(500, "https://example.test/new-path")):
            failed_target = checker.check_link(checker.Link("https://example.test/path"))
        self.assertEqual(failed_target.status, "http_error")
        self.assertEqual(failed_target.http_status, 500)

    def test_timeouts_are_classified_and_retried_once(self):
        with patch.object(checker, "urlopen", side_effect=socket.timeout("slow")) as open_url:
            result = checker.check_link(checker.Link("https://example.test/path"), retries=1)

        self.assertEqual(result.status, "timeout")
        self.assertEqual(open_url.call_count, 2)

    def test_tls_failures_are_separate_and_http_5xx_retries(self):
        with patch.object(checker, "urlopen", side_effect=ssl.SSLError("certificate verify failed")) as open_url:
            tls_result = checker.check_link(checker.Link("https://example.test/path"), retries=2)
        self.assertEqual(tls_result.status, "tls_error")
        self.assertEqual(open_url.call_count, 1)

        with patch.object(checker, "urlopen", side_effect=[response(503), response(200)]) as open_url:
            http_result = checker.check_link(checker.Link("https://example.test/path"), retries=1)
        self.assertEqual(http_result.status, "success")
        self.assertEqual(open_url.call_count, 2)

    def test_parallel_results_keep_order_and_limit_per_host(self):
        links = [checker.Link(f"https://same.test/{index}") for index in range(6)]
        links.append(checker.Link("https://other.test/page"))
        active: dict[str, int] = {}
        maximum: dict[str, int] = {}
        guard = threading.Lock()

        def fake_check(link, **_kwargs):
            host = checker.urlsplit(link.url).hostname
            with guard:
                active[host] = active.get(host, 0) + 1
                maximum[host] = max(maximum.get(host, 0), active[host])
            time.sleep(0.02)
            with guard:
                active[host] -= 1
            return checker.CheckResult(link.url, link.sources, "success")

        with patch.object(checker, "check_link", side_effect=fake_check):
            results = checker.check_links(links, workers=4)

        self.assertEqual([item.url for item in results], [item.url for item in links])
        self.assertLessEqual(maximum["same.test"], checker.PER_HOST_WORKERS)

    def test_time_budget_marks_unscheduled_urls_not_checked(self):
        links = [checker.Link(f"https://budget.test/{index}") for index in range(3)]

        def slow_check(link, **_kwargs):
            time.sleep(0.02)
            return checker.CheckResult(link.url, link.sources, "success")

        with patch.object(checker, "check_link", side_effect=slow_check):
            results = checker.check_links(links, workers=1, max_seconds=0.005)

        self.assertEqual([item.status for item in results], ["success", "not_checked", "not_checked"])

    def test_inventory_only_and_strict_exit_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "index.md").write_text("[missing](https://dead.test/)\n", encoding="utf-8")
            json_path = root / "report.json"
            with patch.object(checker, "urlopen") as open_url, patch("builtins.print"):
                self.assertEqual(
                    checker.main(["--root", str(root), "--inventory-only", "--workers", "2", "--output", str(json_path)]),
                    0,
                )
            open_url.assert_not_called()
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["results"][0]["status"], "not_checked")

            with patch.object(checker, "urlopen", return_value=response(404)), patch("builtins.print"):
                self.assertEqual(checker.main(["--root", str(root)]), 0)
            with patch.object(checker, "urlopen", return_value=response(404)), patch("builtins.print"):
                self.assertEqual(checker.main(["--root", str(root), "--strict"]), 1)


if __name__ == "__main__":
    unittest.main()
