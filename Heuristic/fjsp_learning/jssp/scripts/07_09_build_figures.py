"""Rebuild chapters 07–09 figures and independently check their toy examples.

Run from any directory: python <path to this file>.
The 216-state enumeration is a numerical check for the teaching instance,
not a general proof of a neighbourhood property.
"""

from itertools import permutations, product
import importlib.util
import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

from jssp_paths import CHECKS_DIR, SCRIPT_DIR


def load_section(number):
    spec = importlib.util.spec_from_file_location(
        "section" + number, SCRIPT_DIR / (number + "_build_figures.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


local = load_section("06")
critical = load_section("04")
shared = local.shared
OPS = shared.OPS


def blocks(path):
    result = []
    for v in path:
        if not result or OPS[result[-1][-1]][0] != OPS[v][0]:
            result.append([v])
        else:
            result[-1].append(v)
    return result


def n5(rows, path):
    """Return distinct (machine, left position), both 1-based."""
    runs = blocks(path)
    if len(runs) <= 1:
        return []
    moves = set()
    for index, run in enumerate(runs):
        if len(run) < 2:
            continue
        pairs = []
        if index > 0:
            pairs.append(run[:2])
        if index < len(runs) - 1:
            pairs.append(run[-2:])
        for u, v in pairs:
            r = OPS[u][0]
            i = rows[r - 1].index(u) + 1
            assert rows[r - 1][i] == v
            moves.add((r, i))
    return sorted(moves)


def critical_paths(rows):
    data = critical.analyse(rows)
    return [path[1:-1] for length, path in critical.all_paths(data)
            if length == data["T"]]


def move_key(rows, r, i):
    return (r, tuple(sorted(rows[r - 1][i - 1:i + 1])))


def run_sa_trace():
    rows = local.LOCAL
    best = local.evaluate(rows)
    trace = [{"step": 0, "current": best, "best": best}]
    # Deliberately supplied proposals/draws: an auditable trace, not a random run.
    for step, (r, i, draw) in enumerate(
            [(2, 1, None), (3, 2, None), (1, 2, .20),
             (1, 2, None), (2, 1, .80)], 1):
        candidate = local.swap(rows, r, i)
        value = local.evaluate(candidate)
        delta = value - local.evaluate(rows)
        probability = 1.0 if delta <= 0 else math.exp(-delta / 2)
        accepted = delta <= 0 or draw < probability
        if accepted:
            rows = candidate
            best = min(best, value)
        trace.append(dict(step=step, move=[r, i], candidate=value,
                          delta=delta, probability=probability, draw=draw,
                          accepted=accepted, current=local.evaluate(rows), best=best))
    assert [x["current"] for x in trace] == [12, 12, 11, 13, 11, 11]
    assert [x["best"] for x in trace] == [12, 12, 11, 11, 11, 11]
    return trace


def run_ts_trace():
    rows = local.LOCAL
    best = local.evaluate(rows)
    expiry = {}
    trace = []
    for t in range(1, 4):
        candidates = []
        for r, i, value in local.scan(rows):
            if value is None:
                continue
            key = move_key(rows, r, i)
            tabu = t <= expiry.get(key, 0)
            beats_best = value < best
            candidates.append(dict(machine=r, left=i, value=value,
                                   tabu=tabu, beats_best=beats_best,
                                   aspiration_used=tabu and beats_best,
                                   admissible=not tabu or beats_best))
        allowed = [x for x in candidates if x["admissible"]]
        chosen = min(allowed, key=lambda x: (x["value"], x["machine"], x["left"]))
        r, i = chosen["machine"], chosen["left"]
        key = move_key(rows, r, i)
        rows = local.swap(rows, r, i)
        best = min(best, chosen["value"])
        expiry[key] = max(expiry.get(key, 0), t + 2)
        trace.append(dict(iteration=t, candidates=candidates, chosen=[r, i],
                          current=chosen["value"], best=best, expiry=t + 2))
    assert [x["chosen"] for x in trace] == [[2, 1], [3, 2], [2, 2]]
    assert [x["current"] for x in trace] == [12, 11, 12]
    return trace


def verify():
    n_paths = n_moves = 0
    n_states = n_feasible = 0
    for rows in product(*(permutations(row) for row in shared.MACHINES)):
        n_states += 1
        rows = local.freeze(rows)
        if local.evaluate(rows) is None:
            continue
        n_feasible += 1
        for path in critical_paths(rows):
            n_paths += 1
            for r, i in n5(rows, path):
                n_moves += 1
                u, v = rows[r - 1][i - 1:i + 1]
                starts = shared.earliest(rows)
                assert starts[v] == starts[u] + OPS[u][1]
                assert local.evaluate(local.swap(rows, r, i)) is not None
    expected = {
        "SPT": (local.SPT, [[3, 2]], [11]),
        "GOOD": (local.GOOD, [[1, 2]], [13]),
    }
    examples = {}
    for name, (rows, moves, values) in expected.items():
        path = critical_paths(rows)[0]
        actual = n5(rows, path)
        assert list(map(list, actual)) == moves
        actual_values = [local.evaluate(local.swap(rows, *move)) for move in actual]
        assert actual_values == values
        examples[name] = dict(path=path, blocks=blocks(path), moves=moves, values=values)
    assert n_states == 216 and n_feasible == 64
    return dict(queue_combinations=n_states, feasible_queues=n_feasible,
                critical_paths_checked=n_paths, n5_candidates_checked=n_moves,
                n5_examples=examples, sa_trace=run_sa_trace(), ts_trace=run_ts_trace(),
                probability_delta2={str(t): math.exp(-2 / t) for t in [.5, 1, 2, 5, 10]},
                calibration_T0=-2 / math.log(.8))


def block_figure():
    path = critical_paths(local.SPT)[0]
    fig, ax = plt.subplots(figsize=(13, 4.4))
    fig.subplots_adjust(left=.025, right=.98, top=.96, bottom=.06)
    ax.set(xlim=(0, 13), ylim=(0, 4.4))
    ax.axis("off")
    ax.text(.15, 4.05, "SPT 起点：沿一条关键路径划分机器块", fontsize=20, weight="bold")
    ax.text(.15, 3.42, "块是路径上的最大连续同机片段；单工序块也保留编号。", fontsize=12, color="#64748b")
    xs = [1, 3, 5, 7, 9, 11]
    for k, (v, x) in enumerate(zip(path, xs)):
        selected = v in [(1, 3), (3, 1)]
        box = FancyBboxPatch((x-.74, 1.72), 1.48, .8,
                             boxstyle="round,pad=.04", linewidth=2,
                             edgecolor="#dc2626" if selected else "#64748b",
                             facecolor="#fef2f2" if selected else "#f8fafc")
        ax.add_patch(box)
        ax.text(x, 2.12, rf"$O_{{{v[0]},{v[1]}}}$", ha="center", va="center", fontsize=19)
        ax.text(x, 1.42, rf"$M_{{{OPS[v][0]}}},\ p={OPS[v][1]}$", ha="center", fontsize=12)
        if k < len(path)-1:
            ax.annotate("", (xs[k+1]-.82, 2.12), (x+.82, 2.12),
                        arrowprops=dict(arrowstyle="->", color="#475569"))
    for left, right, label in [(0.2, 1.8, "$B_1$"), (2.2, 3.8, "$B_2$"),
                                (4.2, 7.8, "$B_3$"), (8.2, 9.8, "$B_4$"),
                                (10.2, 11.8, "$B_5$")]:
        ax.plot([left, right], [2.86, 2.86], color="#2563eb", linewidth=3)
        ax.text((left+right)/2, 2.99, label, ha="center", fontsize=14)
    ax.text(6.5, .58, r"唯一 N5 候选：交换 $M_3$ 上 $O_{1,3},O_{3,1}$，重新解码得到 $15\to11$",
            ha="center", fontsize=14, color="#b91c1c")
    shared.save(fig, "07_n5_blocks")


def sa_figure(trace):
    fig, axes = plt.subplots(1, 2, figsize=(13.4, 5.7))
    fig.subplots_adjust(left=.07, right=.98, top=.80, bottom=.23, wspace=.30)
    fig.text(.04, .94, "温度控制变差接受；历史最好值单独保存", fontsize=20, weight="bold")
    ts = [i/40 for i in range(1, 401)]
    for delta, color in [(1, "#059669"), (2, "#2563eb"), (4, "#dc2626")]:
        axes[0].plot(ts, [math.exp(-delta/t) for t in ts],
                     label=rf"$\Delta={delta}$", color=color, linewidth=2)
    axes[0].set(xlabel="温度 $T$（同目标值单位）", ylabel="变差接受概率", ylim=(0, 1), xlim=(0, 10))
    axes[0].legend()
    steps = [x["step"] for x in trace]
    axes[1].plot(steps, [x["current"] for x in trace], "o-", color="#d97706", label="current")
    axes[1].plot(steps, [x["best"] for x in trace], "s--", color="#059669", label="best")
    axes[1].set(xlabel="提议步数（含拒绝）", ylabel=r"$C_{\max}$", xticks=steps, yticks=[11, 12, 13])
    axes[1].legend()
    for ax in axes:
        ax.grid(alpha=.18)
    fig.text(.54, .035, r"右图是正文给定提议与随机数的手算轨迹，固定 $T=2$；不代表性能实验。",
             ha="center", fontsize=11, color="#64748b")
    shared.save(fig, "08_acceptance_current_best")


def tenure_figure():
    fig, ax = plt.subplots(figsize=(12, 4.1))
    fig.subplots_adjust(left=.04, right=.98, top=.96, bottom=.06)
    ax.set(xlim=(0, 12), ylim=(0, 4.1))
    ax.axis("off")
    ax.text(.1, 3.75, "禁忌期限：记录工序身份，按迭代编号到期", fontsize=20, weight="bold")
    ax.text(.1, 3.12, r"第 1 轮接受一次交换，$\tau=2$，记录 $e=1+2=3$；检查条件为 $t\leq e$。",
            fontsize=12, color="#64748b")
    labels = ["第 1 轮", "第 2 轮", "第 3 轮", "第 4 轮"]
    captions = ["交换后登记", "禁止该工序对回退", "仍在禁忌期限内", "到期，可再次考虑"]
    for x, label, caption, face, edge in zip([1.5, 4.5, 7.5, 10.5], labels, captions,
                                           ["#eff6ff", "#fef2f2", "#fef2f2", "#ecfdf5"],
                                           ["#2563eb", "#dc2626", "#dc2626", "#059669"]):
        ax.add_patch(FancyBboxPatch((x-1.25, 1.2), 2.5, 1.2,
                                   boxstyle="round,pad=.04", facecolor=face, edgecolor=edge, linewidth=2))
        ax.text(x, 2.03, label, ha="center", fontsize=17, color=edge)
        ax.text(x, 1.52, caption, ha="center", fontsize=10.5, color=edge)
    ax.text(6, .50, "候选若严格刷新历史最好值，可按本章特赦规则解除禁忌；仍须先通过可行性检查。",
            ha="center", fontsize=12, color="#475569")
    shared.save(fig, "09_tabu_tenure")


if __name__ == "__main__":
    report = verify()
    block_figure()
    sa_figure(report["sa_trace"])
    tenure_figure()
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    (CHECKS_DIR / "07_09_numerical_check.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["critical_paths_checked", "n5_candidates_checked", "calibration_T0"]}))
    print("Generated 3 PNG and 3 SVG figures for chapters 07–09.")
