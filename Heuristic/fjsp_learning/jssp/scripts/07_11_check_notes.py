"""Check chapter 07–11 Markdown and toy bounds; emit a temporary HTML preview.

Dependencies: markdown-it-py (preview), existing figure script dependencies.
The preview loads MathJax 3 from jsDelivr; it is not an IDE-renderer test.
"""

from collections import deque
from html import escape
import importlib.util
from itertools import permutations
import json
from pathlib import Path
import re
import tempfile

from markdown_it import MarkdownIt

from jssp_paths import ASSETS_DIR, CHECKS_DIR, NOTES_DIR, SCRIPT_DIR

NOTES = NOTES_DIR
spec = importlib.util.spec_from_file_location("section06", SCRIPT_DIR / "06_build_figures.py")
local = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local)
shared = local.shared
OPS = shared.OPS


def partial_decode(fixed):
    edges = set(shared.JOB_ARCS)
    for row in fixed.values():
        edges.update(zip(row, row[1:]))
    successors = {v: [] for v in OPS}
    indegree = {v: 0 for v in OPS}
    for u, v in edges:
        successors[u].append(v)
        indegree[v] += 1
    queue = deque(v for v in OPS if indegree[v] == 0)
    head = {v: 0 for v in OPS}
    topo = []
    while queue:
        u = queue.popleft()
        topo.append(u)
        for v in successors[u]:
            head[v] = max(head[v], head[u] + OPS[u][1])
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    assert len(topo) == len(OPS)
    tail = {}
    for u in reversed(topo):
        tail[u] = max((OPS[v][1] + tail[v] for v in successors[u]), default=0)
    return head, tail, max(head[v] + OPS[v][1] for v in OPS)


def single_machine(machine, head, tail):
    trials = []
    operations = sorted(v for v in OPS if OPS[v][0] == machine)
    for row in permutations(operations):
        ready = 0
        intervals = []
        z = 0
        for v in row:
            start = max(ready, head[v])
            ready = start + OPS[v][1]
            intervals.append([start, ready])
            z = max(z, ready + tail[v])
        trials.append(dict(order=row, intervals=intervals, value=z))
    optimum = min(x["value"] for x in trials)
    return dict(value=optimum, trials=trials,
                optimal_orders=[x["order"] for x in trials if x["value"] == optimum])


def verify_bounds():
    head, tail, longest = partial_decode({})
    assert longest == 8 and sum(p for _, p in OPS.values()) == 22
    initial = {r: single_machine(r, head, tail) for r in [1, 2, 3]}
    assert [initial[r]["value"] for r in [1, 2, 3]] == [11, 8, 9]
    assert [x["value"] for x in initial[1]["trials"]] == [11, 11, 14, 17, 14, 18]
    fixed = {}
    stages = []
    for r, expected_values in [(1, [11, 8, 9]), (2, [11, 11]), (3, [11])]:
        head, tail, longest = partial_decode(fixed)
        candidates = {k: single_machine(k, head, tail) for k in [1, 2, 3] if k not in fixed}
        assert [x["value"] for x in candidates.values()] == expected_values
        selected = candidates[r]["optimal_orders"][0]
        fixed[r] = selected
        head_after, tail_after, length_after = partial_decode(fixed)
        reoptimised_values = {}
        for k in fixed:
            if k == r:
                continue
            without_k = {a: b for a, b in fixed.items() if a != k}
            h, q, _ = partial_decode(without_k)
            subproblem = single_machine(k, h, q)
            assert fixed[k] in subproblem["optimal_orders"]
            reoptimised_values[k] = subproblem["value"]
        stages.append(dict(selected_machine=r, selected_order=selected,
                           subproblem_values={k: x["value"] for k, x in candidates.items()},
                           partial_longest_before=longest, partial_longest_after=length_after,
                           reoptimised_values=reoptimised_values,
                           heads={str(v): head_after[v] for v in OPS},
                           tails={str(v): tail_after[v] for v in OPS}))
    rows = tuple(fixed[r] for r in [1, 2, 3])
    assert rows == local.IMPROVED
    assert shared.earliest(rows) == head_after
    assert local.evaluate(rows) == 11
    # Check all pairwise Big-M constraints on the independently decoded UB.
    for row in rows:
        for index, a in enumerate(row):
            for b in row[index + 1:]:
                assert head_after[a] + OPS[a][1] <= head_after[b]
                assert head_after[b] + OPS[b][1] <= head_after[a] + 22
    return dict(initial_single_machine=initial, shifting_bottleneck_stages=stages,
                lower_bound=11, feasible_upper_bound=11, safe_horizon=22)


MD = MarkdownIt("commonmark", {"html": True}).enable("table")
MATH = re.compile(r"\$\$([\s\S]*?)\$\$|\$([^$\n]+?)\$")
FENCE = re.compile(r"(?m)^(```|~~~)[^\n]*\n[\s\S]*?^\1[ \t]*$")


def protect_math(source):
    fences = []
    source = FENCE.sub(lambda m: store_token(fences, m.group(), "FENCE"), source)
    expressions = []

    def math_token(match):
        block = match.group(1) is not None
        tex = match.group(1) if block else match.group(2)
        expressions.append((block, tex))
        return f"MATHPLACEHOLDER{len(expressions)-1}END"

    source = MATH.sub(math_token, source)
    assert "$" not in source, "Unpaired math delimiter"
    for i, value in enumerate(fences):
        source = source.replace(f"FENCEPLACEHOLDER{i}END", value)
    return source, expressions


def store_token(items, value, kind):
    items.append(value)
    return f"{kind}PLACEHOLDER{len(items)-1}END"


def render(source):
    protected, expressions = protect_math(source)
    tokens = MD.parse(protected)
    leaked = [child.content for token in tokens if token.children for child in token.children
              if child.type == "text" and "**" in child.content]
    assert not leaked, f"Unparsed bold markers: {leaked}"
    html = MD.render(protected)
    for i, (block, tex) in enumerate(expressions):
        delimiters = (r"\[", r"\]") if block else (r"\(", r"\)")
        replacement = escape(delimiters[0] + tex + delimiters[1])
        html = html.replace(f"MATHPLACEHOLDER{i}END", replacement)
    html = re.sub(r"<h2>(\d+\.\d+)", r'<h2 id="s\1">\1', html)
    return html, len(expressions), len([t for t in tokens if t.type == "table_open"])


def check_and_preview():
    preview = Path(tempfile.gettempdir()) / "jssp_notes_07_11_preview"
    preview.mkdir(exist_ok=True)
    report = {}
    for number in range(7, 12):
        files = list(NOTES.glob(f"{number:02d}_*.md"))
        assert len(files) == 1, f"Missing/ambiguous chapter {number}"
        path = files[0]
        source = path.read_text(encoding="utf-8")
        content, math_count, tables = render(source)
        for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", source):
            if not target.startswith(("https://", "http://", "#")):
                assert (NOTES / target.split("#")[0]).exists(), (path.name, target)
        content = re.sub(
            r'src="assets/([^"<>]+)"',
            lambda match: f'src="{(ASSETS_DIR / match.group(1)).as_uri()}"',
            content,
        )
        page = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{max-width:1080px;margin:36px auto;padding:0 32px;font:17px/1.85 'Microsoft YaHei',sans-serif;color:#172033}h1{font-size:30px}h2{margin-top:48px;font-size:25px;scroll-margin-top:24px}h3{font-size:20px}table{border-collapse:collapse;width:100%;font-size:15px;margin:24px 0}td,th{border:1px solid #cbd5e1;padding:9px 12px;text-align:left}th{background:#f1f5f9}img{max-width:100%;height:auto}pre{padding:20px;background:#f1f5f9;overflow-x:auto;line-height:1.65;font-size:14px}a{color:#1764c0}mjx-container[display=true]{overflow-x:auto;overflow-y:hidden;padding:8px 0}</style>
<script>window.MathJax={startup:{ready:()=>{MathJax.startup.defaultReady();MathJax.startup.promise.then(()=>{document.documentElement.dataset.mathReady='true'})}}};</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
</head><body>""" + content + "</body></html>"
        (preview / f"{number:02d}.html").write_text(page, encoding="utf-8")
        report[path.name] = dict(math_expressions=math_count, tables=tables,
                                 characters=len(source), preview=f"{number:02d}.html")
    return preview, report


if __name__ == "__main__":
    bounds = verify_bounds()
    preview, formats = check_and_preview()
    report = dict(bounds=bounds, markdown=formats)
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    (CHECKS_DIR / "07_11_validation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"preview_directory": str(preview), "format_checks": formats,
                      "bounds": [bounds["lower_bound"], bounds["feasible_upper_bound"]]},
                     ensure_ascii=False, indent=2))
