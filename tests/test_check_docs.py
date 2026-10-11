import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_docs import check_images, check_navigation, check_tags, find_duplicate_articles


class CheckDocsTests(unittest.TestCase):
    def test_chinese_relative_image_with_encoding_query_and_fragment(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            page_dir = docs / "教程"
            assets = docs / "图片"
            page_dir.mkdir(parents=True)
            assets.mkdir()
            (assets / "中文 图片.png").write_bytes(b"image")
            page = page_dir / "开始.md"
            markdown = "![示意](../%E5%9B%BE%E7%89%87/%E4%B8%AD%E6%96%87%20%E5%9B%BE%E7%89%87.png?raw=1#preview)"

            count, errors = check_images(markdown, page, docs)

            self.assertEqual(count, 1)
            self.assertEqual(errors, [])

    def test_external_data_and_code_images_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp) / "docs"
            docs.mkdir()
            page = docs / "guide.md"
            markdown = """![web](https://example.com/p.png)
![protocol-relative](//example.com/p.png)
![data](data:image/png;base64,AAAA)
`![inline](missing-inline.png)`

```markdown
![fenced](missing-fenced.png)
```
    ![indented](missing-indented.png)
> ```markdown
> ![blockquote-fenced](missing-quoted-fence.png)
> ```
![missing](missing.png)
"""

            count, errors = check_images(markdown, page, docs)

            self.assertEqual(count, 4)
            self.assertEqual(len(errors), 1)
            self.assertIn("missing.png", errors[0])

    def test_malformed_tag_front_matter_is_reported(self):
        malformed = "---\ntags: [算法, 算法, '   ']\n---\n内容\n"
        scalar = "---\ntags: 算法\n---\n内容\n"

        has_tags, errors = check_tags(malformed, "docs/a.md")
        scalar_has_tags, scalar_errors = check_tags(scalar, "docs/b.md")

        self.assertTrue(has_tags)
        self.assertEqual(len(errors), 2)
        self.assertTrue(scalar_has_tags)
        self.assertEqual(len(scalar_errors), 1)

    def test_navigation_reports_missing_and_repeated_targets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            docs.mkdir()
            (docs / "index.md").write_text("# Home\n", encoding="utf-8")
            config = root / "mkdocs.yml"
            config.write_text(
                "site_name: Test\ndocs_dir: docs\nnav:\n  - Home: index.md\n  - Copy: index.md\n  - Missing: missing.md\n",
                encoding="utf-8",
            )

            count, errors = check_navigation(config, docs)

            self.assertEqual(count, 3)
            self.assertEqual(len(errors), 2)
            self.assertTrue(any("duplicate navigation target" in error for error in errors))
            self.assertTrue(any("does not exist" in error for error in errors))

    def test_exact_body_duplicates_are_hints_but_related_text_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            a = docs / "overview.md"
            b = docs / "copy.md"
            c = docs / "detail.md"
            a.write_text("---\ntags: [a]\n---\n# Topic\n\nSame body.  \n", encoding="utf-8")
            b.write_text("---\ntags: [b]\n---\n# Topic\n\nSame body.\n\n", encoding="utf-8")
            c.write_text("# Topic\n\nSame body, with details.\n", encoding="utf-8")

            groups = find_duplicate_articles([a, b, c], docs)

            self.assertEqual(groups, [["copy.md", "overview.md"]])


if __name__ == "__main__":
    unittest.main()
