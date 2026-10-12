"""Rebuild section 06 figures and verify every local-search example."""

from collections import deque
from itertools import permutations, product
import importlib.util
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

from jssp_paths import CHECKS_DIR, SCRIPT_DIR

spec = importlib.util.spec_from_file_location("section05", SCRIPT_DIR / "05_build_figures.py")
previous = importlib.util.module_from_spec(spec)
spec.loader.exec_module(previous)
shared = previous.shared
OPS, JOBS = shared.OPS, shared.JOBS


def freeze(rows):
    return tuple(tuple(row) for row in rows)


GOOD = freeze(shared.GOOD)
SPT = freeze([[(1, 1), (2, 3), (3, 2)], [(2, 1), (1, 2), (3, 3)],
              [(2, 2), (1, 3), (3, 1)]])
IMPROVED = freeze([[(1, 1), (2, 3), (3, 2)], [(2, 1), (1, 2), (3, 3)],
                   [(2, 2), (3, 1), (1, 3)]])
LOCAL = freeze([[(1, 1), (3, 2), (2, 3)], [(1, 2), (2, 1), (3, 3)],
                [(3, 1), (1, 3), (2, 2)]])
PLATEAU = freeze([[(1, 1), (3, 2), (2, 3)], [(2, 1), (1, 2), (3, 3)],
                  [(3, 1), (1, 3), (2, 2)]])
CYCLE = [(1, 2), (1, 3), (3, 1), (3, 2), (3, 3)]


def swap(rows, r, i):
    """Machine and left position use 1-based indices, as in the note."""
    changed = [list(row) for row in rows]
    changed[r - 1][i - 1], changed[r - 1][i] = changed[r - 1][i], changed[r - 1][i - 1]
    return freeze(changed)


def evaluate(rows):
    starts = shared.earliest(rows)
    if starts is None:
        return None
    return max(starts[v] + OPS[v][1] for v in OPS)


def scan(rows):
    return [(r, i, evaluate(swap(rows, r, i)))
            for r in range(1, 4) for i in range(1, 3)]


def relaxation_decode(rows):
    """Independent max-plus relaxation: positive cycles prevent convergence."""
    starts = {v: 0 for v in OPS}
    edges = shared.JOB_ARCS + shared.machine_arcs(rows)
    for _ in range(len(OPS)):
        changed = False
        for u, v in edges:
            bound = starts[u] + OPS[u][1]
            if bound > starts[v]:
                starts[v] = bound
                changed = True
        if not changed:
            return starts
    return None


def reaches(edges, u, v):
    seen, queue = {u}, deque([u])
    while queue:
        node = queue.popleft()
        for a, b in edges:
            if a == node:
                if b == v:
                    return True
                if b not in seen:
                    seen.add(b)
                    queue.append(b)
    return False


def verify():
    states = {}
    for rows in product(*(permutations(row) for row in shared.MACHINES)):
        rows = freeze(rows)
        topo_starts = shared.earliest(rows)
        assert topo_starts == relaxation_decode(rows)
        assert topo_starts == shared.earliest(rows, full=True)
        if topo_starts is not None:
            for row in JOBS + [list(row) for row in rows]:
                assert all(topo_starts[v] >= topo_starts[u] + OPS[u][1]
                           for u, v in zip(row, row[1:]))
        states[rows] = evaluate(rows)
    feasible = {rows: value for rows, value in states.items() if value is not None}
    assert len(states) == 216 and len(feasible) == 64
    assert min(feasible.values()) == 11
    assert {rows for rows, value in feasible.items() if value == 11} == {GOOD, IMPROVED}

    assert evaluate(SPT) == 15
    assert [v for _, _, v in scan(SPT)] == [22, 18, 18, None, 16, 11]
    assert swap(SPT, 3, 2) == IMPROVED
    assert [v for _, _, v in scan(IMPROVED)] == [14, 14, 16, 15, 13, 15]
    assert [v for _, _, v in scan(GOOD)] == [14, 13, 12, 12, 14, 12]
    assert [v for _, _, v in scan(LOCAL)] == [19, 16, 12, 15, 18, 12]
    assert swap(LOCAL, 2, 1) == PLATEAU
    assert swap(PLATEAU, 3, 2) == GOOD
    assert [evaluate(q) for q in [LOCAL, PLATEAU, GOOD]] == [12, 12, 11]
    assert previous.construct("LPT")["rows"] == [list(row) for row in PLATEAU]

    expected = {(1, 1): 0, (1, 2): 3, (1, 3): 7,
                (2, 1): 0, (2, 2): 2, (2, 3): 3,
                (3, 1): 3, (3, 2): 7, (3, 3): 10}
    assert shared.earliest(IMPROVED) == expected
    assert [expected[j, 3] + OPS[j, 3][1] for j in range(1, 4)] == [9, 7, 11]
    local_starts = shared.earliest(LOCAL)
    assert [local_starts[j, 3] + OPS[j, 3][1] for j in range(1, 4)] == [7, 12, 8]
    assert local_starts[2, 1] == 5
    assert shared.earliest(PLATEAU)[2, 1] == 0

    invalid = swap(SPT, 2, 2)
    edges = set(shared.JOB_ARCS + shared.machine_arcs(invalid))
    assert all((u, v) in edges for u, v in zip(CYCLE, CYCLE[1:] + CYCLE[:1]))
    assert sum(OPS[v][1] for v in CYCLE) == 12
    spt_path = [(1, 1), (1, 2), (1, 3), (3, 1), (3, 2), (3, 3)]
    assert sum(OPS[v][1] for v in spt_path) == 15
    assert all((u, v) in set(shared.JOB_ARCS + shared.machine_arcs(SPT))
               for u, v in zip(spt_path, spt_path[1:]))

    # Compare the full-pair single-reversal reachability test with actual queue moves.
    comparisons = 0
    for rows in feasible:
        for r, i, candidate_value in scan(rows):
            u, v = rows[r - 1][i - 1:i + 1]
            machine_edges = shared.machine_arcs(rows, full=True)
            remaining = set(shared.JOB_ARCS + [edge for edge in machine_edges if edge != (u, v)])
            assert reaches(remaining, u, v) == (candidate_value is None)
            comparisons += 1
    assert comparisons == 384
    # Duplicate support must survive deletion of the machine constraint.
    duplicate_fixed = [("u", "v")]
    duplicate_machine = [("u", "v")]
    remaining = duplicate_fixed + [e for e in duplicate_machine if e != ("u", "v")]
    assert reaches(remaining, "u", "v")

    descent_states = [SPT]
    current = SPT
    while True:
        values = [(value, r, i) for r, i, value in scan(current) if value is not None]
        value, r, i = min(values)
        if value >= evaluate(current):
            break
        current = swap(current, r, i)
        descent_states.append(current)
    assert descent_states == [SPT, IMPROVED]
    report = {"enumerated_queue_triples": len(states), "feasible_triples": len(feasible),
              "global_minimum": min(feasible.values()), "global_minimum_count": 2,
              "reachability_comparisons": comparisons, "cycle_duration": 12,
              "states": {name: {"queues": rows, "makespan": evaluate(rows),
                                 "neighbors": scan(rows),
                                 "intervals": [{"op": v, "machine": OPS[v][0],
                                                "start": shared.earliest(rows)[v],
                                                "end": shared.earliest(rows)[v] + OPS[v][1]}
                                               for v in OPS]}
                         for name, rows in [("SPT", SPT), ("improved", IMPROVED),
                                            ("original", GOOD), ("local", LOCAL),
                                            ("plateau", PLATEAU)]}}
    print("Checked all 216 machine-queue triples with independent relaxation:")
    print("64 feasible; optimum 11 at exactly two states; all 384 adjacent-move")
    print("reachability tests agree with DAG checks; SPT descent 15 -> 11;")
    print("complete neighbor tables; cycle weight 12; plateau escape 12 -> 12 -> 11.")
    return report


def improvement_figure():
    fig, axes = plt.subplots(2, 1, figsize=(14, 8.7))
    fig.subplots_adjust(left=.08, right=.97, top=.80, bottom=.09, hspace=.48)
    previous.gantt(axes[0], OPS, shared.earliest(SPT), 15,
                   r"起点 $\pi^{\mathrm{S}}$：SPT 构造结果，$C_{\max}=15$")
    previous.gantt(axes[1], OPS, shared.earliest(IMPROVED), 15,
                   r"候选 $\pi^*$：交换 $M_3$ 上的 $O_{1,3},\ O_{3,1}$，$C_{\max}=11$")
    axes[-1].set_xlabel("时间（同加工时间单位）")
    fig.text(.04, .95, "改变一对机器顺序，重新计算整张排程", fontsize=21, weight="bold")
    fig.text(.04, .89, "交换后先判环，再按最长路解码；其他机器上的后继时间也可能变化。",
             fontsize=12, color="#6b7280")
    shared.save(fig, "06_improving_move")


def cycle_figure():
    fig, ax = shared.canvas(11.2, 9.0, 11.2, 9.0,
                            "同机相邻交换，也可能制造跨机器有向环",
                            "SPT 解上交换机器队列中的两道工序；下图仅截取新图中的五节点环。")
    xy = dict(zip(CYCLE, [(5.6, 6.65), (8.7, 4.95), (7.5, 2.15),
                         (3.7, 2.15), (2.5, 4.95)]))
    patches = {v: shared.node(ax, v, pos, width=1.8, height=1.05) for v, pos in xy.items()}
    for u, v in zip(CYCLE, CYCLE[1:] + CYCLE[:1]):
        machine = (u, v) in {((1, 3), (3, 1)), ((3, 3), (1, 2))}
        shared.edge(ax, xy[u], xy[v], patches[u], patches[v], machine=machine,
                    color="#b91c1c" if machine else shared.INK)
    ax.text(8.85, 3.50, r"$M_3$ 的已有机器弧", ha="center", fontsize=11, color="#b91c1c")
    ax.text(2.55, 6.05, r"$M_2$ 的新机器弧", ha="center", fontsize=11, color="#b91c1c")
    ax.text(5.6, 4.18, "每台机器的队列都合法\n合起来却互相等待", ha="center", fontsize=16,
            color="#b91c1c", weight="bold", linespacing=1.6)
    ax.text(5.6, .60, r"$s_{1,2}\geq s_{1,2}+2+2+4+3+1=s_{1,2}+12$",
            ha="center", fontsize=16, color="#b91c1c")
    shared.save(fig, "06_swap_cycle")


def plateau_figure():
    fig, ax = plt.subplots(figsize=(13.6, 5.0))
    fig.subplots_adjust(left=.025, right=.975, top=.97, bottom=.04)
    ax.set(xlim=(0, 13.6), ylim=(0, 5.0))
    ax.axis("off")
    ax.text(.2, 4.75, "没有一步严格改善，仍可沿平台走向更好解", fontsize=21, weight="bold", va="top")
    ax.text(.2, 4.12, "三组队列都通过判环；箭头各表示一次相邻交换，不表示下降算法会接受每一步。",
            fontsize=12, color="#6b7280", va="top")
    positions = [2.0, 6.8, 11.6]
    boxes = []
    for x, label, value, detail, edge, face in zip(
            positions, [r"$\pi^{\mathrm{L}}$", r"$\pi^{\mathrm{B}}$", r"$\pi^0$"],
            [12, 12, 11], ["相邻交换局部最优", "等值邻居（上一节 LPT 解）", "原来贯穿的排程"],
            ["#b45309", "#475569", "#047857"], ["#fff7ed", "#f8fafc", "#ecfdf5"]):
        box = FancyBboxPatch((x - 1.65, 1.9), 3.3, 1.3,
                             boxstyle="round,pad=.03,rounding_size=.13", edgecolor=edge,
                             facecolor=face, linewidth=2)
        ax.add_patch(box)
        boxes.append(box)
        ax.text(x, 2.84, label, ha="center", va="center", fontsize=22, color=edge)
        ax.text(x, 2.29, rf"$C_{{\max}}={value}$", ha="center", va="center", fontsize=20, color=edge)
        ax.text(x, 1.57, detail, ha="center", va="center", fontsize=12, color=edge)
    for index in range(2):
        ax.add_patch(FancyArrowPatch((positions[index], 2.55), (positions[index+1], 2.55),
                                     patchA=boxes[index], patchB=boxes[index+1],
                                     arrowstyle="-|>", mutation_scale=22, linewidth=2,
                                     color="#475569", shrinkA=8, shrinkB=8))
    ax.text(4.4, 3.48, r"交换 $M_2$ 上 $O_{1,2},\ O_{2,1}$", ha="center", fontsize=12)
    ax.text(9.2, 3.48, r"交换 $M_3$ 上 $O_{1,3},\ O_{2,2}$", ha="center", fontsize=12)
    ax.text(4.4, 1.02, r"$\Delta=0$：平台步", ha="center", fontsize=15, color="#b45309")
    ax.text(9.2, 1.02, r"$\Delta=-1$：改善步", ha="center", fontsize=15, color="#047857")
    ax.text(6.8, .30, "直接接受所有等值步可能来回循环；需要额外的步数、记忆或去重规则。",
            ha="center", fontsize=12, color="#6b7280")
    shared.save(fig, "06_plateau_escape")


if __name__ == "__main__":
    report = verify()
    improvement_figure()
    cycle_figure()
    plateau_figure()
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    (CHECKS_DIR / "06_numerical_check.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Generated 3 PNG diagrams and 3 SVG files with native text.")
