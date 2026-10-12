"""Check new Markdown, local links and numeric examples; emit MathJax previews.

Browser visual inspection is a separate step; this script never claims to perform it.
Uses the CommonMark/math protection helper from the chapter 07–11 checker.
"""

import importlib.util
import json
from pathlib import Path
import re
import tempfile

from jssp_paths import ASSETS_DIR, CHECKS_DIR, NOTES_DIR, SCRIPT_DIR

OUT = ASSETS_DIR
NOTES = NOTES_DIR


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, SCRIPT_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


old = load("old_notes_checker", "07_11_check_notes.py")
numerical = load("new_numerical_checker", "12_14_build_figures.py")

STYLE = """
body{max-width:1080px;margin:32px auto;padding:0 30px;font:17px/1.85 'Microsoft YaHei',sans-serif;color:#172033}
h1{font-size:30px;line-height:1.4}h2{margin-top:44px;font-size:24px;scroll-margin-top:20px}h3{font-size:20px}
table{border-collapse:collapse;width:100%;font-size:15px;margin:22px 0}td,th{border:1px solid #cbd5e1;padding:9px 12px;text-align:left}th{background:#f1f5f9}
img{max-width:100%;height:auto}pre{padding:18px;background:#f1f5f9;overflow-x:auto;line-height:1.65;font-size:14px}
a{color:#1764c0}mjx-container[display=true]{overflow-x:auto;overflow-y:hidden;padding:8px 0}
.qa-pass{padding:14px 20px;background:#ecfdf5;color:#065f46;border:1px solid #a7f3d0}
"""
MATHJAX = """
<script>window.MathJax={startup:{ready:()=>{MathJax.startup.defaultReady();MathJax.startup.promise.then(()=>{
const errors=document.querySelectorAll('mjx-merror,[data-mjx-error]').length;
const broken=[...document.images].filter(i=>!i.complete||i.naturalWidth===0).length;
document.documentElement.dataset.mathReady='true';
document.documentElement.dataset.mathErrors=String(errors);
document.documentElement.dataset.brokenImages=String(broken);
document.documentElement.dataset.horizontalOverflow=String(document.documentElement.scrollWidth>innerWidth);
const qa=document.querySelector('.qa-pass'); if(qa)qa.textContent='MathJax 完成；公式错误 '+errors+'；缺失图片 '+broken+'。';
})}}};</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
"""


def page_html(content):
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<style>' + STYLE + '</style>' + MATHJAX + '</head><body>' + content + '</body></html>')


def check_one(path):
    source = path.read_text(encoding="utf-8")
    html, math_count, tables = old.render(source)
    targets = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", source)
    local_count = 0
    for target in targets:
        if not target.startswith(("https://", "http://", "#")):
            assert (path.parent / target.split("#")[0]).exists(), (path.name, target)
            local_count += 1
    # Detect unbalanced braces in each TeX expression (ignoring escaped literals).
    _, expressions = old.protect_math(source)
    for _, tex in expressions:
        depth = 0
        for i, char in enumerate(tex):
            if i and tex[i-1] == "\\":
                continue
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                assert depth >= 0, (path.name, tex)
        assert depth == 0, (path.name, tex)
    for match in re.finditer(r'src="(assets/[^"<>]+)"', html):
        html = html.replace(match.group(), 'src="' + (NOTES / match.group(1)).as_uri() + '"')
    return html, dict(characters=len(source), math_expressions=math_count,
                      tables=tables, local_links_checked=local_count)


def check_all():
    preview = Path(tempfile.gettempdir()) / "jssp_notes_12_14_preview"
    preview.mkdir(exist_ok=True)
    result = {}
    for number in [12, 13, 14]:
        matches = list(NOTES.glob(f"{number}_*.md"))
        assert len(matches) == 1
        source = matches[0].read_text(encoding="utf-8")
        assert re.search(r"(?m)^状态：.*待(?:用户)?\s*review", source)
        assert "易错点" in source and "自检题" in source and "参考答案" in source and "复习速记卡" in source
        html, checks = check_one(matches[0])
        (preview / f"{number}.html").write_text(page_html(html), encoding="utf-8")
        result[matches[0].name] = checks
    for path in [NOTES / "index.md", OUT / "12_sources_verified.md", OUT / "14_sources_verified.md",
                 OUT / "12_14_validation.md"]:
        _, result[path.name] = check_one(path)
    # A compact page containing real paragraphs, math, tables and figures from each chapter.
    snippets = ['<h1>第 12–14 节渲染抽查</h1><p class="qa-pass">等待 MathJax 完成。</p>']
    selections = [(12, ["12.2", "12.7"]), (13, ["13.8", "13.9"]), (14, ["14.4", "14.6", "14.10"])]
    for number, sections in selections:
        path = next(NOTES.glob(f"{number}_*.md"))
        source = path.read_text(encoding="utf-8")
        for section in sections:
            match = re.search(r"(?ms)^## " + re.escape(section) + r" .+?(?=^## |\Z)", source)
            assert match
            rendered, _, _ = old.render(match.group())
            rendered = re.sub(r'src="assets/([^"<>]+)"',
                              lambda m: 'src="' + (OUT / m.group(1)).as_uri() + '"', rendered)
            snippets.append(rendered)
    (preview / "qa.html").write_text(page_html("\n".join(snippets)), encoding="utf-8")
    return preview, result


if __name__ == "__main__":
    trace = numerical.verify_pr()
    stats = numerical.verify_statistics()
    fjsp, _ = numerical.verify_fjsp()
    preview, formats = check_all()
    report = dict(preview_directory=str(preview), markdown=formats,
                  pr_values=[x["value"] for x in trace],
                  statistics=stats, fjsp_enumeration=fjsp,
                  browser_visual_qa="See 12_14_validation.md for actual coverage")
    (CHECKS_DIR / "12_14_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"preview_directory": str(preview), "markdown": formats,
                      "pr_values": report["pr_values"], "fjsp_optimum": fjsp["optimum"]}, ensure_ascii=False, indent=2))
