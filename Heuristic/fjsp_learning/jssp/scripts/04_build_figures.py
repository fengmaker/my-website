"""Rebuild section 04 figures and check its critical-structure examples."""

from collections import deque
import importlib.util
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Patch

from jssp_paths import SCRIPT_DIR

spec = importlib.util.spec_from_file_location("section03", SCRIPT_DIR / "03_build_figures.py")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
shared = previous.shared
OPS, GOOD, JOBS = previous.OPS, previous.GOOD, previous.JOBS
ALPHA, OMEGA, VERTICES = previous.ALPHA, previous.OMEGA, previous.VERTICES
RED = "#b91c1c"


def analyse(rows, changes=None):
    changes = changes or {}
    p = {v: changes.get(v, previous.duration(v)) for v in VERTICES}
    successors, arcs = previous.graph(rows)
    indegree = {v: 0 for v in VERTICES}
    for u, v in arcs:
        indegree[v] += 1
    queue = deque(v for v in VERTICES if indegree[v] == 0)
    h = {v: float("-inf") for v in VERTICES}
    h[ALPHA] = 0
    topo = []
    while queue:
        u = queue.popleft()
        topo.append(u)
        for v in successors[u]:
            h[v] = max(h[v], h[u] + p[u])
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)
    assert len(topo) == len(VERTICES), "Cyclic candidate"
    q = {OMEGA: 0}
    for v in reversed(topo):
        if v != OMEGA:
            q[v] = max(p[w] + q[w] for w in successors[v])
    T = h[OMEGA]
    latest = {v: T - p[v] - q[v] for v in VERTICES}
    total = {v: latest[v] - h[v] for v in VERTICES}
    critical = {v for v in VERTICES if total[v] == 0}
    critical_arcs = {(u, v) for u, v in arcs
                     if h[u] + p[u] + p[v] + q[v] == T}
    free = {v: min(h[w] for w in successors[v]) - h[v] - p[v]
            for v in VERTICES if v != OMEGA}
    return dict(h=h, q=q, p=p, latest=latest, total=total, free=free,
                critical=critical, critical_arcs=critical_arcs, T=T,
                topo=topo, successors=successors, arcs=arcs)


def all_paths(data):
    paths = []

    def visit(v, length, route):
        if v == OMEGA:
            paths.append((length, route))
        for w in data["successors"][v]:
            visit(w, length + data["p"][v], route + [w])

    visit(ALPHA, 0, [ALPHA])
    return paths


def check_schedule(starts, data):
    assert starts[ALPHA] == 0
    assert all(starts[v] >= 0 for v in VERTICES)
    assert all(starts[v] >= starts[u] + data["p"][u] for u, v in data["arcs"])
    assert max(starts[v] + data["p"][v] for v in OPS) <= data["T"]


def verify():
    data = analyse(GOOD)
    h, p, q = data["h"], data["p"], data["q"]
    assert data["T"] == 11
    assert h == previous.decode(GOOD)[1]
    expected_q = {ALPHA: 11, OMEGA: 0,
                  (1, 1): 7, (1, 2): 2, (1, 3): 0,
                  (2, 1): 5, (2, 2): 4, (2, 3): 0,
                  (3, 1): 7, (3, 2): 4, (3, 3): 0}
    assert q == expected_q
    assert [data["total"][v] for v in OPS] == [1, 4, 4, 4, 2, 0, 0, 0, 3]
    assert [data["latest"][v] for v in OPS] == [1, 7, 9, 4, 6, 7, 0, 4, 10]
    assert [data["free"][v] for v in OPS] == [0, 0, 4, 1, 0, 0, 0, 0, 3]

    # Independent check of every formula against explicit paths of the tiny DAG.
    paths = all_paths(data)
    longest = [path for length, path in paths if length == data["T"]]
    assert longest == [[ALPHA, (3, 1), (3, 2), (2, 3), OMEGA]]
    assert data["critical"] == set().union(*map(set, longest))
    assert data["critical_arcs"] == set().union(
        *(set(zip(path, path[1:])) for path in longest))
    for v in VERTICES:
        through = max(length for length, path in paths if v in path)
        assert h[v] + p[v] + q[v] == through
        suffix = max(sum(p[w] for w in path[path.index(v) + 1:])
                     for _, path in paths if v in path)
        assert suffix == q[v]
    for u, v in data["arcs"]:
        through = max(length for length, path in paths
                      if (u, v) in set(zip(path, path[1:])))
        assert h[u] + p[u] + p[v] + q[v] == through
        assert ((u, v) in data["critical_arcs"]) == (
            u in data["critical"] and v in data["critical"] and h[u] + p[u] == h[v])

    check_schedule(data["latest"], data)
    adjusted = dict(h)
    adjusted.update({(1, 1): 1, (1, 2): 4, (1, 3): 6})
    check_schedule(adjusted, data)
    solo = dict(h)
    solo[(1, 1)] = 1
    assert solo[(1, 2)] < solo[(1, 1)] + p[(1, 1)]

    tied = analyse(GOOD, {(1, 1): 4})
    tied_paths = [path for length, path in all_paths(tied) if length == tied["T"]]
    assert tied["T"] == 11 and len(tied_paths) == 2
    assert tied["critical"] - {ALPHA, OMEGA} == {(1, 1), (3, 1), (3, 2), (2, 3)}
    assert analyse(GOOD, {(1, 1): 4, (3, 1): 3})["T"] == 11

    swapped = [list(row) for row in GOOD]
    swapped[0] = [(1, 1), (2, 3), (3, 2)]
    changed = analyse(swapped)
    assert changed["T"] == 13
    assert [changed["h"][v] for v in [(2, 3), (3, 2), (3, 3)]] == [5, 9, 12]
    witness = [ALPHA, (3, 1), (2, 2), (2, 3), (3, 2), (3, 3), OMEGA]
    assert (13, witness) in all_paths(changed)
    assert all(changed["h"][v] == h[v] for v in OPS if v not in [(2, 3), (3, 2), (3, 3)])
    print("Checked head/tail, latest starts, total/free floats, all critical nodes/arcs")
    print("against all source-sink paths; latest and adjusted schedules are feasible;")
    print("two critical paths at p_1,1=4; shortening only one leaves Cmax=11;")
    print("critical-block swap is acyclic and gives starts 5/9/12, Cmax=13.")
    report = {"makespan": data["T"], "paths": len(paths),
              "operations": [{"operation": previous.label(v), "h": h[v], "p": p[v],
                              "q": q[v], "latest": data["latest"][v],
                              "total_float": data["total"][v], "free_float": data["free"][v]}
                             for v in OPS],
              "multiple_critical_paths": len(tied_paths), "swapped_makespan": changed["T"]}
    return data, report


def data_node(ax, v, xy, data):
    x, y = xy
    if isinstance(v, tuple):
        j, k = v
        width, face = 2.18, shared.PALE[j]
        border = RED if data["total"][v] == 0 else shared.COLORS[j]
        lines = [rf"$O_{{{j},{k}}}$",
                 rf"$M_{{{OPS[v][0]}}},\ p_{{{j},{k}}}={data['p'][v]}$",
                 rf"$h_{{{j},{k}}}={data['h'][v]},\ q_{{{j},{k}}}={data['q'][v]}$",
                 rf"$F_{{{j},{k}}}={data['total'][v]}$"]
    else:
        width, face, border = 1.05, "#f3f4f6", RED
        lines = [rf"$\{v}$", rf"$p_{{\{v}}}=0$",
                 rf"$h_{{\{v}}}={data['h'][v]}$", rf"$q_{{\{v}}}={data['q'][v]}$"]
    patch = FancyBboxPatch((x-width/2, y-.83), width, 1.66,
                          boxstyle="round,pad=0.02,rounding_size=0.13",
                          facecolor=face, edgecolor=border, linewidth=2, zorder=5)
    ax.add_patch(patch)
    for line, offset, size in zip(lines, [.56, .18, -.18, -.55], [17, 10.5, 10.5, 11.5]):
        ax.text(x, y+offset, line, ha="center", va="center", fontsize=size,
                color=border if offset in (.56, -.55) else shared.INK, zorder=6)
    return patch


def graph_figure(data):
    fig, ax = shared.canvas(13.4, 10.8, 13.4, 10.8,
                            "双向标注：head、tail 与总松弛量",
                            "灰色实线为工艺弧，蓝色虚线为机器弧；红色节点与弧为当前关键结构。")
    xy = {v: (2.8 + 3.6*(v[1]-1), 7.9 - 2.8*(v[0]-1)) for v in OPS}
    xy.update(alpha=(.6, 5.1), omega=(12.75, 5.1))
    patches = {v: data_node(ax, v, pos, data) for v, pos in xy.items()}
    fixed = shared.JOB_ARCS + [(ALPHA, row[0]) for row in JOBS] + [(row[-1], OMEGA) for row in JOBS]
    for u, v in fixed:
        shared.edge(ax, xy[u], xy[v], patches[u], patches[v],
                    color=RED if (u, v) in data["critical_arcs"] else None)
    for u, v in shared.machine_arcs(GOOD):
        shared.edge(ax, xy[u], xy[v], patches[u], patches[v], machine=True,
                    color=RED if (u, v) in data["critical_arcs"] else None)
    ax.text(6.7, .92, r"$F_{j,k}=11-(h_{j,k}+p_{j,k}+q_{j,k})$", ha="center", fontsize=17)
    ax.text(6.7, .35, "两端的路径长度都排除自身加工；红色结构仅对应这组固定机器顺序。",
            ha="center", fontsize=11, color="#6b7280")
    shared.save(fig, "04_head_tail")


def length_figure(data):
    fig, ax = plt.subplots(figsize=(12.6, 8.5))
    fig.subplots_adjust(left=.13, right=.96, bottom=.13, top=.82)
    ops = list(OPS)
    head_color, tail_color = "#94a3b8", "#bae6fd"
    for index, v in enumerate(ops):
        y = len(ops)-1-index
        h, p, q, f = (data[key][v] for key in ["h", "p", "q", "total"])
        starts = [0, h, h+p, h+p+q]
        lengths = [h, p, q, f]
        colors = [head_color, shared.COLORS[v[0]], tail_color, "#f8fafc"]
        for start, length, color, part in zip(starts, lengths, colors, ["h", "p", "q", "F"]):
            if length:
                ax.barh(y, length, left=start, height=.6, color=color,
                        edgecolor="#64748b" if part == "F" else "white",
                        hatch="///" if part == "F" else None, linewidth=.8)
                ax.text(start+length/2, y, str(length), ha="center", va="center", fontsize=13,
                        color="white" if part == "p" else "#334155")
        if f == 0:
            ax.add_patch(FancyBboxPatch((0, y-.33), 11, .66,
                                       boxstyle="round,pad=0.01,rounding_size=0.06",
                                       facecolor="none", edgecolor=RED, linewidth=1.8))
    ax.set_yticks(range(9), [rf"$O_{{{v[0]},{v[1]}}}$" for v in reversed(ops)], fontsize=14)
    ax.set_xticks(range(12))
    ax.set(xlim=(-.05,11.1), ylim=(-.7,8.7), xlabel="路径长度（同加工时间单位）")
    ax.xaxis.grid(True, color="#e2e8f0", zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.text(.04, .95, "长度分解：head + 加工 + tail + 总松弛量 = 11", fontsize=19, weight="bold")
    fig.text(.04, .895, "每行对应经过该工序的最长完整路径；不是机器甘特图。红框表示零松弛。", fontsize=11, color="#6b7280")
    legend = [Patch(facecolor=head_color, label="Head（不含自己）"),
              Patch(facecolor="#475569", label="自身加工（按 job 着色）"),
              Patch(facecolor=tail_color, label="Tail（不含自己）"),
              Patch(facecolor="#f8fafc", edgecolor="#64748b", hatch="///", label="总松弛量")]
    fig.legend(handles=legend, loc="lower center", ncol=4, frameon=False, fontsize=10.5,
               bbox_to_anchor=(.5,.025))
    shared.save(fig, "04_path_lengths")


def block_figure(data):
    fig, ax = shared.canvas(13.4, 6.5, 13.4, 6.5,
                            "关键块：在一条选定路径上，按机器切分",
                            "原例的真实路径为三道工序；每个块是同机的极大连续段。")
    for x, width, label in [(1.55, 2.3, r"$B_1=(O_{3,1})$"),
                             (4.85, 6.65, r"$B_2=(O_{3,2},O_{2,3})$")]:
        ax.add_patch(FancyBboxPatch((x,2.2),width,2.1,
                                   boxstyle="round,pad=0.02,rounding_size=0.15",
                                   facecolor="#fef2f2", edgecolor="#fca5a5", linewidth=1.5))
        ax.text(x+width/2,4.65,label,ha="center",fontsize=17,color=RED)
    route = [ALPHA, (3,1), (3,2), (2,3), OMEGA]
    xs = [.6,2.7,6.0,10.35,12.75]
    xy = {v:(x,3.2) for v,x in zip(route,xs)}
    patches = {v:shared.node(ax,v,xy[v],width=1.95 if isinstance(v,tuple) else .95,height=1.0)
               for v in route}
    for u,v in zip(route,route[1:]):
        shared.edge(ax,xy[u],xy[v],patches[u],patches[v],
                    machine=(u,v)==((3,2),(2,3)),color=RED)
    for v,interval in [((3,1),"[0,4)"),((3,2),"[4,7)"),((2,3),"[7,11)")]:
        ax.text(xy[v][0],2.45,rf"${interval}$",ha="center",fontsize=13)
    ax.text(6.7,1.35,"单工序段用于完整分割路径；可提供块内交换的是含两道工序的段。",
            ha="center",fontsize=12,color=shared.INK)
    ax.text(6.7,.6,r"$\mu_{3,1}=M_3,\qquad \mu_{3,2}=\mu_{2,3}=M_1,\qquad C_{\max}=11$",
            ha="center",fontsize=17,color=RED)
    shared.save(fig,"04_critical_blocks")


if __name__ == "__main__":
    data, report = verify()
    graph_figure(data)
    length_figure(data)
    block_figure(data)
    print("Generated 3 PNG diagrams and 3 SVG files with native text.")
    print(json.dumps(report, ensure_ascii=False))
