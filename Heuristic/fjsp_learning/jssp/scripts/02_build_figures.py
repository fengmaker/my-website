"""Regenerate section 02 figures and check the shared 3x3 example.

Run from any directory: python path/to/02_build_figures.py
"""

from collections import deque
from itertools import combinations, permutations, product

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from jssp_paths import ASSETS_DIR

OPS = {
    (1, 1): (1, 3), (1, 2): (2, 2), (1, 3): (3, 2),
    (2, 1): (2, 2), (2, 2): (3, 1), (2, 3): (1, 4),
    (3, 1): (3, 4), (3, 2): (1, 3), (3, 3): (2, 1),
}
JOBS = [[(j, k) for k in range(1, 4)] for j in range(1, 4)]
MACHINES = [[o for o, (m, _) in OPS.items() if m == r] for r in range(1, 4)]
GOOD = [[(1, 1), (3, 2), (2, 3)], [(2, 1), (1, 2), (3, 3)],
        [(3, 1), (2, 2), (1, 3)]]
BAD = [[(2, 3), (1, 1), (3, 2)], [(2, 1), (1, 2), (3, 3)],
       [(1, 3), (2, 2), (3, 1)]]
CYCLE = [(1, 1), (1, 2), (1, 3), (2, 2), (2, 3)]
JOB_ARCS = [(row[k], row[k + 1]) for row in JOBS for k in range(2)]
COLORS = {1: "#2563eb", 2: "#b45309", 3: "#047857"}
PALE = {1: "#eff6ff", 2: "#fff7ed", 3: "#ecfdf5"}
INK = "#374151"
MACHINE_COLOR = "#2563eb"

plt.rcParams.update({
    "font.family": "Microsoft YaHei", "mathtext.fontset": "dejavusans",
    "svg.fonttype": "none", "font.size": 12, "figure.facecolor": "white",
})


def machine_arcs(rows, full=False):
    return [(a, b) for row in rows for a, b in
            (combinations(row, 2) if full else zip(row, row[1:]))]


def earliest(rows, full=False):
    edges = set(JOB_ARCS + machine_arcs(rows, full))
    successors = {o: [] for o in OPS}
    indegrees = {o: 0 for o in OPS}
    starts = {o: 0 for o in OPS}
    for a, b in edges:
        successors[a].append(b)
        indegrees[b] += 1
    queue = deque(o for o in OPS if indegrees[o] == 0)
    visited = 0
    while queue:
        a = queue.popleft()
        visited += 1
        for b in successors[a]:
            starts[b] = max(starts[b], starts[a] + OPS[a][1])
            indegrees[b] -= 1
            if indegrees[b] == 0:
                queue.append(b)
    return starts if visited == len(OPS) else None


def verify():
    expected = {(1, 1): 0, (1, 2): 3, (1, 3): 5,
                (2, 1): 0, (2, 2): 4, (2, 3): 7,
                (3, 1): 0, (3, 2): 4, (3, 3): 7}
    starts = earliest(GOOD)
    assert starts == expected
    assert max(starts[o] + OPS[o][1] for o in OPS) == 11
    assert earliest(BAD) is None
    bad_edges = set(JOB_ARCS + machine_arcs(BAD))
    assert all((a, b) in bad_edges for a, b in zip(CYCLE, CYCLE[1:] + CYCLE[:1]))
    assert sum(OPS[o][1] for o in CYCLE) == 12
    partial = set(JOB_ARCS + machine_arcs(GOOD)) - {((3, 2), (2, 3))}
    overlapping_starts = dict(expected)
    overlapping_starts[(2, 3)] = 5
    assert all(overlapping_starts[b] >= overlapping_starts[a] + OPS[a][1]
               for a, b in partial)
    assert overlapping_starts[(2, 3)] < overlapping_starts[(3, 2)] + 3
    for rows in product(*(list(permutations(row)) for row in MACHINES)):
        assert earliest(rows, full=True) == earliest(rows)
    print("Checked: original starts and Cmax=11; bad-order cycle weight=12;")
    print("deleted-arc overlap example; full/adjacent equivalence on all 216 orders.")


def canvas(width, height, xmax, ymax, title, subtitle):
    fig, ax = plt.subplots(figsize=(width, height))
    fig.subplots_adjust(left=.02, right=.98, bottom=.03, top=.97)
    ax.set(xlim=(0, xmax), ylim=(0, ymax), aspect="equal")
    ax.axis("off")
    ax.text(.25, ymax - .25, title, va="top", fontsize=20, weight="bold", color="#111827")
    ax.text(.25, ymax - .85, subtitle, va="top", fontsize=12, color="#6b7280")
    return fig, ax


def node(ax, op, xy, width=1.4, height=.95):
    x, y = xy
    if isinstance(op, tuple):
        j, k = op
        edge, face = COLORS[j], PALE[j]
        label = rf"$O_{{{j},{k}}}$"
        m, duration = OPS[op]
        detail = rf"$M_{{{m}}},\ p_{{{j},{k}}}={duration}$"
    else:
        edge, face = "#6b7280", "#f3f4f6"
        label = rf"$\{op}$"
        detail = rf"$p_{{\{op}}}=0$"
    patch = FancyBboxPatch((x - width/2, y - height/2), width, height,
                          boxstyle="round,pad=0.02,rounding_size=0.13",
                          facecolor=face, edgecolor=edge, linewidth=1.8, zorder=5)
    ax.add_patch(patch)
    ax.text(x, y + .16, label, ha="center", va="center", fontsize=17, color=edge, zorder=6)
    ax.text(x, y - .21, detail, ha="center", va="center", fontsize=10.5, color=INK, zorder=6)
    return patch


def edge(ax, xy1, xy2, patch1, patch2, machine=False, directed=True, rad=0, color=None):
    patch = FancyArrowPatch(xy1, xy2, patchA=patch1, patchB=patch2,
                            arrowstyle="-|>" if directed else "-",
                            mutation_scale=20, linewidth=2,
                            color=color or (MACHINE_COLOR if machine else INK),
                            linestyle=(0, (5, 3)) if machine else "-",
                            connectionstyle=f"arc3,rad={rad}",
                            shrinkA=4, shrinkB=4, zorder=3 if machine else 2)
    if machine:
        patch.set_path_effects([pe.Stroke(linewidth=5, foreground="white"), pe.Normal()])
    ax.add_patch(patch)


def save(fig, stem):
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(ASSETS_DIR / f"{stem}.png", dpi=160)
    fig.savefig(ASSETS_DIR / f"{stem}.svg")
    plt.close(fig)


def constraints_figure():
    fig, ax = canvas(14, 8.4, 14, 8.4, "同一实例，两类关系", "每个节点是工序；节点内列出指定机器和加工时间。左右两侧按标号对应同一组工序。")
    ax.plot([6.9, 6.9], [.8, 6.7], color="#e5e7eb", lw=1.5)
    ax.text(.4, 6.95, "工艺弧：方向由输入固定", fontsize=14, weight="bold", color=INK)
    ax.text(7.2, 6.95, "机器冲突：每一对都要选择先后", fontsize=14, weight="bold", color=INK)
    for index, row in enumerate(JOBS):
        y = 5.75 - 1.9 * index
        xy = {o: (1.6 + 1.95 * k, y) for k, o in enumerate(row)}
        patches = {o: node(ax, o, xy[o]) for o in row}
        ax.text(.2, y, rf"$J_{{{index+1}}}$", fontsize=16, va="center")
        for a, b in zip(row, row[1:]):
            edge(ax, xy[a], xy[b], patches[a], patches[b])
    for index, row in enumerate(MACHINES):
        y = 5.75 - 1.9 * index
        xy = {o: (8.6 + 1.95 * k, y) for k, o in enumerate(row)}
        patches = {o: node(ax, o, xy[o]) for o in row}
        ax.text(7.15, y, rf"$M_{{{index+1}}}$", fontsize=16, va="center")
        for a, b in combinations(row, 2):
            edge(ax, xy[a], xy[b], patches[a], patches[b], True, False,
                 rad=-.32 if (a, b) == (row[0], row[2]) else 0)
    ax.text(.4, .45, "起点、终点及其连接弧省略。右侧的位置不表示加工顺序。", color="#6b7280", fontsize=12)
    save(fig, "02_constraints")


def oriented_figure():
    fig, ax = canvas(12, 8.8, 12, 8.8, "选择机器顺序后的有向图", "灰色实线：固定弧。蓝色虚线箭头：相邻机器弧。节点位置不表示时间。")
    xy = {o: (2.3 + 3.05 * (o[1]-1), 6.5 - 2.25*(o[0]-1)) for o in OPS}
    xy.update(alpha=(.6, 4.25), omega=(11.1, 4.25))
    patches = {o: node(ax, o, pos, width=1.55 if isinstance(o, tuple) else .9)
               for o, pos in xy.items()}
    fixed = JOB_ARCS + [("alpha", row[0]) for row in JOBS] + [(row[-1], "omega") for row in JOBS]
    for a, b in fixed:
        edge(ax, xy[a], xy[b], patches[a], patches[b])
    for a, b in machine_arcs(GOOD):
        edge(ax, xy[a], xy[b], patches[a], patches[b], machine=True)
    ax.text(.4, .65, "完整队列已确定：非相邻机器弧由路径隐含。没有节点的交叉处不表示连接。", color="#6b7280", fontsize=12)
    save(fig, "02_oriented_graph")


def cycle_figure():
    fig, ax = canvas(10.5, 9.1, 10.5, 9.1, "跨机器的循环依赖", "只截取反例中的五个节点；灰色为工艺弧，红色虚线为机器弧。")
    xy = dict(zip(CYCLE, [(5.25, 6.75), (8.05, 5.05), (7.2, 2.25),
                         (3.3, 2.25), (2.45, 5.05)]))
    patches = {o: node(ax, o, pos, width=1.6, height=1.1) for o, pos in xy.items()}
    for a, b in zip(CYCLE, CYCLE[1:] + CYCLE[:1]):
        machine = (a, b) in {((1, 3), (2, 2)), ((2, 3), (1, 1))}
        edge(ax, xy[a], xy[b], patches[a], patches[b], machine=machine,
             color="#b91c1c" if machine else INK)
    ax.text(7.2, 6.25, "工艺", color=INK)
    ax.text(8.05, 3.55, "工艺", color=INK)
    ax.text(5.25, 1.8, "$M_3$", ha="center", color="#b91c1c", fontsize=15)
    ax.text(1.65, 3.55, "工艺", color=INK)
    ax.text(3.35, 6.3, "$M_1$", color="#b91c1c", fontsize=15)
    ax.text(5.25, 4.35, "等完一圈，又要先等自己", ha="center", fontsize=16, color="#b91c1c", weight="bold")
    ax.text(5.25, .65, "$s_{1,1}\\geq s_{1,1}+3+2+2+1+4=s_{1,1}+12$",
            ha="center", fontsize=16, color="#b91c1c")
    save(fig, "02_cycle")


if __name__ == "__main__":
    verify()
    constraints_figure()
    oriented_figure()
    cycle_figure()
    print("Generated 3 PNG figures and 3 SVG files with native text.")
