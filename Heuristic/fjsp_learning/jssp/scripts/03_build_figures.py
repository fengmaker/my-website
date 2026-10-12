"""Rebuild section 03 diagrams and verify its queue trace and numerical examples.

Uses the shared 3x3 data and drawing helpers from section 02.
"""

from collections import deque
import importlib.util
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from jssp_paths import SCRIPT_DIR

spec = importlib.util.spec_from_file_location("section02", SCRIPT_DIR / "02_build_figures.py")
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
OPS, JOBS, GOOD, BAD = shared.OPS, shared.JOBS, shared.GOOD, shared.BAD
ALPHA, OMEGA = "alpha", "omega"
VERTICES = [ALPHA, *OPS, OMEGA]


def graph(rows):
    for r, row in enumerate(rows, 1):
        required = {o for o, (machine, _) in OPS.items() if machine == r}
        if len(row) != len(required) or set(row) != required:
            raise ValueError("Machine row is not a complete permutation.")
    assert len(rows) == 3
    successors = {v: [] for v in VERTICES}
    arcs = set()

    def add(a, b):
        if (a, b) not in arcs:
            arcs.add((a, b))
            successors[a].append(b)

    for row in JOBS:
        chain = [ALPHA, *row, OMEGA]
        for a, b in zip(chain, chain[1:]):
            add(a, b)
    for row in rows:
        for a, b in zip(row, row[1:]):
            add(a, b)
    return successors, arcs


def duration(v, changed=False):
    if v in (ALPHA, OMEGA):
        return 0
    return 4 if changed and v == (3, 2) else OPS[v][1]


def decode(rows, changed=False, lifo=False):
    successors, arcs = graph(rows)
    degree = {v: 0 for v in VERTICES}
    for a, b in arcs:
        degree[b] += 1
    queue = deque(v for v in VERTICES if degree[v] == 0)
    times = {v: float("-inf") for v in VERTICES}
    times[ALPHA] = 0
    order, trace = [], []
    while queue:
        u = queue.pop() if lifo else queue.popleft()
        assert times[u] != float("-inf")
        order.append(u)
        newly_ready = []
        for v in successors[u]:
            times[v] = max(times[v], times[u] + duration(u, changed))
            degree[v] -= 1
            if degree[v] == 0:
                newly_ready.append(v)
                queue.append(v)
        trace.append((u, newly_ready, list(queue)))
    feasible = len(order) == len(VERTICES)
    return feasible, times if feasible else None, order, trace


def label(v):
    return v if isinstance(v, str) else f"O_{v[0]},{v[1]}"


def verify():
    feasible, times, order, trace = decode(GOOD)
    expected = {ALPHA: 0, OMEGA: 11,
                (1, 1): 0, (1, 2): 3, (1, 3): 5,
                (2, 1): 0, (2, 2): 4, (2, 3): 7,
                (3, 1): 0, (3, 2): 4, (3, 3): 7}
    expected_order = [ALPHA, (1, 1), (2, 1), (3, 1), (1, 2), (3, 2),
                      (2, 2), (3, 3), (2, 3), (1, 3), OMEGA]
    assert feasible and times == expected and order == expected_order
    expected_new = [[(1, 1), (2, 1), (3, 1)], [], [(1, 2)],
                    [(3, 2), (2, 2)], [], [(3, 3)], [(2, 3), (1, 3)],
                    [], [], [OMEGA], []]
    assert [new for _, new, _ in trace] == expected_new
    successors, arcs = graph(GOOD)
    assert len(arcs) == 18

    # Independent check: enumerate every source path on this tiny DAG.
    path_max = {v: float("-inf") for v in VERTICES}
    longest = []

    def visit(v, length, path):
        path_max[v] = max(path_max[v], length)
        if v == OMEGA:
            longest.append((length, path))
        for w in successors[v]:
            visit(w, length + duration(v), path + [w])

    visit(ALPHA, 0, [ALPHA])
    assert path_max == times
    witness = [ALPHA, (3, 1), (3, 2), (2, 3), OMEGA]
    assert (11, witness) in longest and max(length for length, _ in longest) == 11
    for row in JOBS + GOOD:
        for a, b in zip(row, row[1:]):
            assert times[b] >= times[a] + duration(a)
    assert decode(GOOD, lifo=True)[1] == times
    bad_feasible, bad_times, bad_order, _ = decode(BAD)
    assert not bad_feasible and bad_times is None and bad_order == [ALPHA, (2, 1)]
    changed_feasible, changed_times, _, _ = decode(GOOD, changed=True)
    assert changed_feasible and changed_times[(2, 3)] == 8
    assert changed_times[(3, 3)] == 8 and changed_times[OMEGA] == 12
    print("Checked: all FIFO queue steps; original starts and Cmax=11;")
    print("all source-path lengths; alternate topological order; bad graph processes 2/11;")
    print("p_3,2=4 gives both successor starts=8 and Cmax=12.")
    report = {"makespan": times[OMEGA], "arc_count": len(arcs),
              "trace": [{"pop": label(v), "enqueue": [label(x) for x in new],
                         "queue_after": [label(x) for x in queue]} for v, new, queue in trace],
              "longest_path": [label(x) for x in witness]}
    return times, report


def layers_figure():
    fig, ax = shared.canvas(15, 8.6, 15, 8.6, "拓扑分层：层号是依赖深度", "每轮同时移除所有剩余入度为 0 的节点；同层内可按任意次序计算。")
    columns = [.6, 2.7, 6.5, 10.3, 14.2]
    for index in range(1, 4):
        x = columns[index]
        panel = FancyBboxPatch((x - 1.05, 1.05), 2.1, 5.6,
                              boxstyle="round,pad=0.02,rounding_size=0.15",
                              facecolor="#f8fafc", edgecolor="#e2e8f0", zorder=0)
        ax.add_patch(panel)
        for row in JOBS:
            op = row[index - 1]
            shared.node(ax, op, (x, 5.8 - 1.9*(op[0]-1)), width=1.65)
    shared.node(ax, ALPHA, (columns[0], 3.9), width=.9)
    shared.node(ax, OMEGA, (columns[4], 3.9), width=.9)
    for index, x in enumerate(columns):
        ax.text(x, 6.92, f"层 {index}", fontsize=15, ha="center", weight="bold", color="#374151")
    for x1, x2 in zip(columns, columns[1:]):
        ax.annotate("", xy=(x2-1.25 if x2 != columns[-1] else x2-.6, 3.9),
                    xytext=(x1+.6 if x1 == columns[0] else x1+1.25, 3.9),
                    arrowprops={"arrowstyle": "->", "color": "#9ca3af", "lw": 1.6})
    ax.text(.3, .55, "层与层之间的箭头仅表示计算阶段推进，不是额外的工艺弧或机器弧。", color="#6b7280", fontsize=12)
    shared.save(fig, "03_topological_layers")


def time_node(ax, v, xy, times):
    x, y = xy
    if isinstance(v, tuple):
        j, k = v
        border, face = shared.COLORS[j], shared.PALE[j]
        width = 1.95
        main = rf"$O_{{{j},{k}}}$"
        machine, p = OPS[v]
        detail = rf"$M_{{{machine}}},\ p_{{{j},{k}}}={p}$"
        interval = rf"$d_{{{j},{k}}}={times[v]},\ [{times[v]},{times[v]+p})$"
    else:
        border, face, width = "#6b7280", "#f3f4f6", 1.05
        main = rf"$\{v}$"
        detail = rf"$p_{{\{v}}}=0$"
        interval = rf"$d_{{\{v}}}={times[v]}$"
    patch = FancyBboxPatch((x-width/2, y-.72), width, 1.44,
                          boxstyle="round,pad=0.02,rounding_size=0.13",
                          facecolor=face, edgecolor=border, linewidth=1.8, zorder=5)
    ax.add_patch(patch)
    ax.text(x, y+.38, main, ha="center", va="center", fontsize=17, color=border, zorder=6)
    ax.text(x, y, detail, ha="center", va="center", fontsize=10, color=shared.INK, zorder=6)
    ax.text(x, y-.37, interval, ha="center", va="center", fontsize=10.5, color=shared.INK, zorder=6)
    return patch


def longest_figure(times):
    fig, ax = shared.canvas(12.6, 10, 12.6, 10, "最长路标注：最早开始与加工区间", "灰色实线为工艺弧，蓝色虚线为机器弧；红色标出一条长度为 11 的路径。")
    xy = {o: (2.6 + 3.4*(o[1]-1), 7.15 - 2.5*(o[0]-1)) for o in OPS}
    xy.update(alpha=(.6, 4.65), omega=(11.95, 4.65))
    patches = {v: time_node(ax, v, pos, times) for v, pos in xy.items()}
    witness = [ALPHA, (3, 1), (3, 2), (2, 3), OMEGA]
    highlighted = set(zip(witness, witness[1:]))
    fixed = shared.JOB_ARCS + [(ALPHA, row[0]) for row in JOBS] + [(row[-1], OMEGA) for row in JOBS]
    for a, b in fixed:
        shared.edge(ax, xy[a], xy[b], patches[a], patches[b],
                    color="#b91c1c" if (a, b) in highlighted else None)
    for a, b in shared.machine_arcs(GOOD):
        shared.edge(ax, xy[a], xy[b], patches[a], patches[b], machine=True,
                    color="#b91c1c" if (a, b) in highlighted else None)
    ax.text(6.3, .85, "$d_{\\omega}=0+4+3+4=11$", ha="center", fontsize=17, color="#b91c1c")
    ax.text(6.3, .3, "路径长度取弧权和。红色路径中的机器弧依赖于已选队列；结论仅对应固定顺序。",
            ha="center", fontsize=11, color="#6b7280")
    shared.save(fig, "03_longest_path")


if __name__ == "__main__":
    times, report = verify()
    layers_figure()
    longest_figure(times)
    print("Generated 2 PNG diagrams and 2 SVG files with native text.")
    # Keep the console trace checkable without adding another learning chapter.
    print(json.dumps(report, ensure_ascii=False))
