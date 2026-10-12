"""Rebuild chapters 12–14 figures and audit all numerical teaching examples.

The chapter 13 runs are deliberately illustrative, never solver measurements.
Dependencies: matplotlib; the existing chapter 06/02 helpers.
"""

import csv
import importlib.util
from itertools import combinations, permutations, product
import json
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from jssp_paths import ASSETS_DIR, CHECKS_DIR, SCRIPT_DIR

OUT = ASSETS_DIR
spec = importlib.util.spec_from_file_location("chapter06", SCRIPT_DIR / "06_build_figures.py")
local = importlib.util.module_from_spec(spec)
spec.loader.exec_module(local)
shared = local.shared


def distance(a, b):
    return sum((a[r].index(u) < a[r].index(v)) !=
               (b[r].index(u) < b[r].index(v))
               for r in range(len(a)) for u, v in combinations(a[r], 2))


def validate(options, schedule, reported):
    """Check intervals directly, independently of any decoder's feasibility flag."""
    assert set(schedule) == set(options)
    for (j, k), (r, start, end) in schedule.items():
        assert r in options[j, k] and start >= 0
        assert end - start == options[j, k][r]
        if (j, k - 1) in options:
            assert schedule[j, k - 1][2] <= start
    for r in {row[0] for row in schedule.values()}:
        intervals = sorted((s, e) for m, s, e in schedule.values() if m == r)
        assert all(e <= ns for (_, e), (ns, _) in zip(intervals, intervals[1:]))
    assert max(e for _, _, e in schedule.values()) == reported


def jssp_schedule(rows):
    starts = shared.earliest(rows)
    value = local.evaluate(rows)
    assert starts is not None
    schedule = {v: (r, starts[v], starts[v] + p) for v, (r, p) in shared.OPS.items()}
    validate({v: {r: p} for v, (r, p) in shared.OPS.items()}, schedule, value)
    return schedule


def verify_pr():
    current, guide = local.LOCAL, local.IMPROVED
    trace = []
    while True:
        value = local.evaluate(current)
        schedule = jssp_schedule(current)
        item = dict(step=len(trace), distance=distance(current, guide), value=value,
                    best=min([x["value"] for x in trace] + [value]),
                    queues=current, schedule={str(v): row for v, row in schedule.items()})
        trace.append(item)
        if current == guide:
            break
        candidates = []
        for r in range(1, 4):
            for i in range(1, 3):
                candidate = local.swap(current, r, i)
                if distance(candidate, guide) != distance(current, guide) - 1:
                    continue
                z = local.evaluate(candidate)
                if z is not None:
                    jssp_schedule(candidate)
                    candidates.append((z, r, i, candidate))
        assert candidates
        z, r, i, current = min(candidates)
        item["candidates"] = [[v, mr, pos] for v, mr, pos, _ in candidates]
        item["accepted_move"] = [r, i]
    assert [x["value"] for x in trace] == [12, 12, 11, 13, 11]
    assert [x["distance"] for x in trace] == [4, 3, 2, 1, 0]
    assert [x["best"] for x in trace] == [12, 12, 11, 11, 11]
    assert [x["accepted_move"] for x in trace[:-1]] == [[2, 1], [3, 2], [1, 2], [3, 1]]
    assert distance(local.GOOD, guide) == 2
    # An adjacent swap changes one pair orientation, whether feasible or not.
    for rows in [local.LOCAL, local.PLATEAU, local.GOOD, guide]:
        for r in range(1, 4):
            for i in range(1, 3):
                assert distance(rows, local.swap(rows, r, i)) == 1
    return trace


ILLUSTRATIVE = {"LS_example": [12, 12, 12, 11, 12],
                "SA_example": [11, 12, 11, 11, 11]}


def verify_statistics():
    records, result = [], {}
    for name, values in ILLUSTRATIVE.items():
        for seed, value in enumerate(values):
            # The final schedules exist, but frequencies and algorithm labels are artificial.
            jssp_schedule(local.GOOD if value == 11 else local.LOCAL)
            records.append(dict(data_kind="illustrative", instance="toy_3x3",
                                algorithm=name, seed=seed, makespan=value,
                                feasible="true", elapsed="", evaluations=""))
        mean = statistics.mean(values)
        result[name] = dict(best=min(values), mean=mean, median=statistics.median(values),
                            worst=max(values), sample_std=statistics.stdev(values),
                            mean_rpd_bks=statistics.mean(100 * (z - 11) / 11 for z in values),
                            mean_improvement=statistics.mean(100 * (15 - z) / 15 for z in values),
                            optimal_hits=values.count(11), runs=len(values))
        assert abs(result[name]["sample_std"] - (0.2 ** .5)) < 1e-12
    assert result["LS_example"]["mean"] == 11.8
    assert result["SA_example"]["mean"] == 11.2
    assert [result[n]["optimal_hits"] for n in ILLUSTRATIVE] == [1, 4]
    with (OUT / "13_example_runs.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    # Reload the archived CSV and regenerate means rather than only checking memory.
    with (OUT / "13_example_runs.csv").open(encoding="utf-8", newline="") as handle:
        archived = list(csv.DictReader(handle))
    for name in ILLUSTRATIVE:
        rows = [x for x in archived if x["algorithm"] == name]
        assert statistics.mean(int(x["makespan"]) for x in rows) == result[name]["mean"]
        assert all(x["data_kind"] == "illustrative" and not x["elapsed"] for x in rows)
    assert abs(100 * (115 - 110) / 110 - 4.545454545454546) < 1e-12
    assert 100 * (115 - 100) / 100 == 15
    return result


FJSP = {(1, 1): {1: 3, 2: 5}, (1, 2): {2: 2},
        (2, 1): {1: 2, 2: 4}, (2, 2): {1: 4, 2: 3}}
ASSIGNMENT = {(1, 1): 1, (1, 2): 2, (2, 1): 1, (2, 2): 2}


def append_decode(os, ms, options=FJSP):
    job_ready, machine_ready, counts, schedule = {}, {}, {}, {}
    for j in os:
        counts[j] = counts.get(j, 0) + 1
        v = j, counts[j]
        r = ms[v]
        start = max(job_ready.get(j, 0), machine_ready.get(r, 0))
        end = start + options[v][r]
        schedule[v] = r, start, end
        job_ready[j], machine_ready[r] = end, end
    value = max(e for _, _, e in schedule.values())
    validate(options, schedule, value)
    return value, schedule


def fixed_queue_decode(options, ms, queues):
    """Independent DAG decoder for all FJSP assignments and machine queues."""
    edges = {(v, (v[0], v[1] + 1)) for v in options if (v[0], v[1] + 1) in options}
    edges.update((u, v) for row in queues for u, v in zip(row, row[1:]))
    predecessors = {v: {u for u, w in edges if w == v} for v in options}
    end, schedule = {}, {}
    while len(end) < len(options):
        ready = sorted(v for v in options if v not in end and predecessors[v] <= end.keys())
        if not ready:
            return None
        for v in ready:
            start = max((end[u] for u in predecessors[v]), default=0)
            end[v] = start + options[v][ms[v]]
            schedule[v] = ms[v], start, end[v]
    value = max(end.values())
    validate(options, schedule, value)
    return value, schedule


def verify_fjsp():
    a = append_decode([1, 2, 1, 2], ASSIGNMENT)
    b = append_decode([2, 1, 2, 1], ASSIGNMENT)
    assert a[0] == 8 and b[0] == 7
    vertices = list(FJSP)
    values, assignments, queue_count, feasible_count = [], 0, 0, 0
    for chosen in product(*(FJSP[v] for v in vertices)):
        assignments += 1
        ms = dict(zip(vertices, chosen))
        members = [[v for v in vertices if ms[v] == r] for r in [1, 2]]
        for queues in product(*(permutations(row) for row in members)):
            queue_count += 1
            decoded = fixed_queue_decode(FJSP, ms, queues)
            if decoded is not None:
                feasible_count += 1
                values.append(decoded[0])
    assert assignments == 8 and min(values) == 7
    assert max(sum(min(FJSP[j, k].values()) for k in [1, 2]) for j in [1, 2]) == 5
    assert sum(min(x.values()) for x in FJSP.values()) == 10
    independent = {(j, 1): {1: 2, 2: 3} for j in [1, 2, 3]}
    all_fast = append_decode([1, 2, 3], {(j, 1): 1 for j in [1, 2, 3]}, independent)
    split = append_decode([1, 2, 3], {(1, 1): 1, (2, 1): 1, (3, 1): 2}, independent)
    assert all_fast[0] == 6 and split[0] == 4
    return dict(A={"value": a[0], "schedule": {str(v): x for v, x in a[1].items()}},
                B={"value": b[0], "schedule": {str(v): x for v, x in b[1].items()}},
                assignments=assignments, queue_combinations=queue_count,
                feasible_queues=feasible_count, optimum=min(values), job_bound=5,
                workload_bound=5, fastest_machine_value=6, split_machine_value=4), [a, b]


def figure_pr(trace):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.4))
    fig.subplots_adjust(left=.075, right=.98, bottom=.23, top=.79, wspace=.27)
    fig.text(.04, .93, "路径重连：距离下降，目标值仍可能反弹", fontsize=20, weight="bold")
    steps = [x["step"] for x in trace]
    axes[0].plot(steps, [x["value"] for x in trace], "o-", color="#b45309", label="路径当前值")
    axes[0].plot(steps, [x["best"] for x in trace], "s--", color="#047857", label="路径最好值")
    axes[0].set(xlabel="接受步数", ylabel=r"$C_{\max}$", xticks=steps, yticks=[11, 12, 13], ylim=(10.7, 13.4))
    axes[0].legend()
    axes[1].plot(steps, [x["distance"] for x in trace], "o-", color="#2563eb")
    axes[1].set(xlabel="接受步数", ylabel=r"$d(\pi,\pi^{\mathrm{G}})$", xticks=steps, yticks=steps)
    for ax in axes:
        ax.grid(alpha=.18)
    fig.text(.5, .07, "3×3 贯穿实例的教学轨迹；每个点均通过区间校验，不代表性能实验。",
             ha="center", fontsize=11, color="#64748b")
    shared.save(fig, "12_path_relinking")


def figure_statistics(result):
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.3))
    fig.subplots_adjust(left=.075, right=.97, top=.78, bottom=.23, wspace=.32)
    fig.text(.04, .94, "教学示意数据：最好值相同，出现频次不同", fontsize=20, weight="bold")
    colors = ["#2563eb", "#b45309"]
    for i, (name, values) in enumerate(ILLUSTRATIVE.items(), 1):
        axes[0].scatter([i + x for x in [-.16, -.08, 0, .08, .16]], values,
                        s=75, color=colors[i-1], alpha=.8)
        axes[0].scatter([i], [result[name]["mean"]], marker="D", s=90,
                        facecolors="white", edgecolors=colors[i-1], linewidths=2, zorder=4)
        axes[0].text(i+.2, result[name]["mean"], f"均值 {result[name]['mean']}", fontsize=10, va="center")
    axes[0].set(xlim=(.55, 2.8), ylim=(10.8, 12.3), xticks=[1, 2],
                xticklabels=["LS 示例", "SA 示例"], yticks=[11, 11.5, 12], ylabel=r"$C_{\max}$")
    axes[0].grid(axis="y", alpha=.18)
    axes[1].bar([1, 2], [.2, .8], color=colors, width=.5)
    for i, label, value in [(1, "1/5", .2), (2, "4/5", .8)]:
        axes[1].text(i, value+.04, label, ha="center", fontsize=14)
    axes[1].set(xticks=[1, 2], xticklabels=["LS 示例", "SA 示例"], ylim=(0, 1.05),
                ylabel=r"达到已证最优值 $11$ 的比例", yticks=[0, .2, .4, .6, .8, 1])
    fig.text(.5, .065, "频次由人工安排，未运行 LS/SA；圆点为五条记录，空心菱形为均值。",
             ha="center", fontsize=11, color="#64748b")
    shared.save(fig, "13_repeated_runs")


def figure_fjsp(schedules):
    fig, axes = plt.subplots(2, 1, figsize=(11.8, 7))
    fig.subplots_adjust(left=.08, right=.98, top=.86, bottom=.24, hspace=.70)
    fig.text(.04, .95, "机器选择相同，排序使最大完工时间从 8 变成 7", fontsize=19, weight="bold")
    for ax, (name, (value, schedule)) in zip(axes, zip(["A", "B"], schedules)):
        for (j, k), (r, start, end) in schedule.items():
            ax.barh(r, end-start, left=start, height=.55,
                    color=shared.COLORS[j], edgecolor="white", linewidth=1.5)
            ax.text((start+end)/2, r, rf"$O_{{{j},{k}}}$", color="white", ha="center", va="center", fontsize=15)
        ax.set(xlim=(0, 8.6), ylim=(.4, 2.6), yticks=[1, 2], yticklabels=[r"$M_1$", r"$M_2$"],
               xticks=list(range(9)), xlabel="时间")
        ax.set_title(rf"排程 {name}：$C_{{\max}}={value}$", loc="left", fontsize=15, pad=9)
        ax.grid(axis="x", alpha=.15)
        ax.set_axisbelow(True)
    fig.legend(handles=[Patch(color=shared.COLORS[j], label=rf"$J_{j}$") for j in [1, 2]],
               loc="lower center", bbox_to_anchor=(.5, .075), ncol=2, frameon=False)
    fig.text(.5, .035, "两张排程使用相同 MS；各区间与正文表格一致，半开区间端点可衔接。",
             ha="center", fontsize=11, color="#64748b")
    shared.save(fig, "14_fjsp_orders")


if __name__ == "__main__":
    trace = verify_pr()
    stats = verify_statistics()
    fjsp, schedules = verify_fjsp()
    figure_pr(trace)
    figure_statistics(stats)
    figure_fjsp(schedules)
    report = dict(path_relinking=trace, illustrative_statistics=stats, fjsp=fjsp)
    (CHECKS_DIR / "12_14_numerical_check.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pr_values": [x["value"] for x in trace],
                      "illustrative_means": [x["mean"] for x in stats.values()],
                      "fjsp_enumeration": fjsp}, ensure_ascii=False, indent=2))
    print("Generated 3 PNG, 3 SVG figures and an explicitly illustrative CSV.")
