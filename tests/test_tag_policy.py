import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from check_docs import check_tag_policy


class TagPolicyTests(unittest.TestCase):
    def check(self, pages, policy):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            docs = root / "docs"
            files = []
            for name, content in pages.items():
                path = docs / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                files.append(path)
            config = root / "tags.yml"
            config.write_text(policy, encoding="utf-8")
            return check_tag_policy(config, files, docs)

    def test_missing_unknown_and_nested_scope(self):
        errors = self.check(
            {"OR/deep/a.md": "# Missing", "OR/b.md": "---\ntags: [typo]\n---\n# B", "other.md": "# Other"},
            "required: ['OR/**/*.md', 'OR/*.md']\nexclude: []\nallowed: [建模]\n",
        )
        self.assertEqual(len(errors), 2)
        self.assertTrue(any("tags required" in error for error in errors))
        self.assertTrue(any("unknown tag" in error for error in errors))

    def test_excluded_utility_page_and_valid_tags(self):
        self.assertEqual(self.check(
            {"OR/index.md": "# Utility", "OR/a.md": "---\ntags: [建模]\n---\n# A"},
            "required: ['OR/*.md']\nexclude: ['OR/index.md']\nallowed: [建模]\n",
        ), [])

    def test_invalid_policy_fails_actionably(self):
        errors = self.check({"a.md": "# A"}, "required: ['*.md']\nexclude: []\nallowed: 建模\n")
        self.assertEqual(len(errors), 1)
        self.assertIn("invalid tag policy", errors[0])


if __name__ == "__main__":
    unittest.main()
