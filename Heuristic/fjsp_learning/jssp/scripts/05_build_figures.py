"""Construct section 05 examples with fixed, explicit dispatch tie breakers."""

import importlib.util
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from jssp_paths import CHECKS_DIR, SCRIPT_DIR

spec = importlib.util.spec_from_file_location("section02", SCRIPT_DIR / "02_build_figures.py")
shared = importlib.util.module_from_spec(spec)
spec.loader.exec_module(shared)
OPS, JOBS = shared.OPS, shared.JOBS


def construct(rule, framework="append", *, job_tie_only=False):
    next_k = {j: 1 for j in range(1, 4)}
    job_end = {j: 0 for j in range(1, 4)}
    machine_end = {r: 0 for r in range(1, 4)}
    rows = [[] for _ in range(3)]
    starts, trace = {}, []
    while len(starts) < len(OPS):
        candidates = []
        for j in range(1, 4):
            k = next_k[j]
            if k > 3:
                continue
            v = (j, k)
            r, p = OPS[v]
            e = max(job_end[j], machine_end[r])
            remaining = sum(OPS[j, t][1] for t in range(k, 4))
            candidates.append(dict(op=v, machine=r, p=p, e=e, finish=e+p, R=remaining))
        pool = candidates
        pivot = None
        if framework == "gt":
            pivot = min(candidates, key=lambda c: (c["finish"], c["e"], *c["op"]))
            pool = [c for c in candidates if c["machine"] == pivot["machine"]
                    and c["e"] < pivot["finish"]]
        assert pool

        def key(c):
            score = {"SPT": c["p"], "LPT": -c["p"], "MWKR": -c["R"]}[rule]
            return (score, *c["op"]) if job_tie_only else (score, c["e"], *c["op"])

        chosen = min(pool, key=key)
        j, k = chosen["op"]
        r = chosen["machine"]
        starts[j, k] = chosen["e"]
        job_end[j] = machine_end[r] = chosen["finish"]
        rows[r-1].append((j,k))
        next_k[j] += 1
        trace.append(dict(candidates=candidates, pool=pool, pivot=pivot, chosen=chosen,
                          job_end=list(job_end.values()), machine_end=list(machine_end.values())))
    return dict(starts=starts, rows=rows, trace=trace, job_end=list(job_end.values()),
                makespan=max(job_end.values()), rule=rule, framework=framework)


def permissible_left_shifts(data):
    """Try every earlier insertion gap while leaving all other starts fixed."""
    moves = {}
    starts = data["starts"]
    for v,(r,p) in OPS.items():
        j,k=v
        release = starts[j,k-1]+OPS[j,k-1][1] if k>1 else 0
        deadline = starts[j,k+1] if k<3 else float("inf")
        other = sorted((u for u,(machine,_) in OPS.items() if machine==r and u!=v),
                       key=lambda u:starts[u])
        gap_start = 0
        for u in other + [None]:
            gap_end = starts[u] if u is not None else float("inf")
            candidate = max(release,gap_start)
            if candidate < starts[v] and candidate+p <= min(gap_end,deadline):
                moves[v]=candidate
                break
            if u is not None:
                gap_start=starts[u]+OPS[u][1]
    return moves


def verify():
    results = {rule: construct(rule) for rule in ["SPT", "LPT", "MWKR"]}
    assert [results[r]["makespan"] for r in results] == [15,12,11]
    expected_sequences = {
        "SPT": [(2,1),(2,2),(1,1),(1,2),(1,3),(2,3),(3,1),(3,2),(3,3)],
        "LPT": [(3,1),(1,1),(3,2),(2,1),(1,2),(1,3),(2,2),(2,3),(3,3)],
        "MWKR": [(3,1),(1,1),(2,1),(2,2),(1,2),(3,2),(2,3),(1,3),(3,3)]}
    for rule, data in results.items():
        assert [step["chosen"]["op"] for step in data["trace"]] == expected_sequences[rule]
        # Independent decoder reconstructs the final times from machine queues.
        assert shared.earliest(data["rows"]) == data["starts"]
        for chain in JOBS + data["rows"]:
            for u,v in zip(chain,chain[1:]):
                assert data["starts"][v] >= data["starts"][u] + OPS[u][1]
    assert results["MWKR"]["rows"] == shared.GOOD
    assert results["MWKR"]["job_end"] == [7,11,8]
    assert results["LPT"]["starts"][(2,2)] == 7
    assert results["LPT"]["starts"][(1,3)] == 5
    # LPT's idle interval [4,5) can hold O_2,2 without delaying any operation.
    shifted = dict(results["LPT"]["starts"])
    shifted[(2,2)] = 4
    changed_rows = [[(1,1),(3,2),(2,3)], [(2,1),(1,2),(3,3)], [(3,1),(2,2),(1,3)]]
    for chain in JOBS + changed_rows:
        for u,v in zip(chain,chain[1:]):
            assert shifted[v] >= shifted[u] + OPS[u][1]
    assert construct("MWKR", job_tie_only=True)["makespan"] == 13

    gt = {rule: construct(rule,"gt") for rule in results}
    assert [gt[r]["makespan"] for r in gt] == [15,13,11]
    assert gt["MWKR"]["rows"] == shared.GOOD
    for data in gt.values():
        assert shared.earliest(data["rows"]) == data["starts"]
        assert all(step["chosen"] in step["pool"] for step in data["trace"])
        assert not permissible_left_shifts(data)
    assert permissible_left_shifts(results["LPT"])[(2,2)] == 4
    step = gt["MWKR"]["trace"][2]
    assert step["pivot"]["op"] == (2,2)
    assert [(c["op"],c["e"],c["finish"]) for c in step["candidates"]] == [
        ((1,2),3,5), ((2,2),2,3), ((3,1),0,4)]
    assert [c["op"] for c in step["pool"]] == [(2,2),(3,1)]
    assert step["chosen"]["op"] == (3,1)

    # Independent two-job counterexample: all machines visited once per job.
    counter = {(1,1):(1,10),(1,2):(2,1),(1,3):(3,1),
               (2,1):(2,1),(2,2):(1,1),(2,3):(3,10)}
    busy = {(1,1):0,(1,2):10,(1,3):11,(2,1):0,(2,2):10,(2,3):12}
    wait = {(1,1):2,(1,2):12,(1,3):13,(2,1):0,(2,2):1,(2,3):2}
    for starts, makespan in [(busy,22),(wait,14)]:
        for j in [1,2]:
            for k in [1,2]:
                assert starts[j,k+1] >= starts[j,k] + counter[j,k][1]
        for r in [1,2,3]:
            line = sorted((v for v,(m,p) in counter.items() if m==r),key=lambda v:starts[v])
            for u,v in zip(line,line[1:]):
                assert starts[v] >= starts[u] + counter[u][1]
        assert max(starts[v]+counter[v][1] for v in counter)==makespan
    print("Checked complete append traces: SPT=15, LPT=12, MWKR=11;")
    print("final queues reproduce every start through independent DAG decoding;")
    print("job-only MWKR ties give 13; GT SPT/LPT/MWKR give 15/13/11;")
    print("GT conflict set; all GT outputs are active by independent gap checks;")
    print("LPT's permissible left shift; idle counterexample 22 versus 14.")
    report = {rule: {"makespan":data["makespan"], "job_completion":data["job_end"],
                     "sequence":[str(step["chosen"]["op"]) for step in data["trace"]],
                     "queues":data["rows"], "trace":data["trace"]} for rule,data in results.items()}
    report["GT"] = {rule:{"makespan":data["makespan"],"trace":data["trace"]} for rule,data in gt.items()}
    return results, counter, busy, wait, report


def gantt(ax, ops, starts, xmax, title):
    for v,(r,p) in ops.items():
        j,k=v
        s=starts[v]
        ax.barh(4-r,p,left=s,height=.52,color=shared.PALE[j],
                edgecolor=shared.COLORS[j],linewidth=1.6,zorder=3)
        label=rf"$O_{{{j},{k}}}$"
        ax.text(s+p/2,4-r,label,ha="center",va="center",fontsize=11,
                color=shared.COLORS[j],zorder=4)
        ax.text(s+p/2,4-r-.36,rf"$[{s},{s+p})$",ha="center",va="center",fontsize=8,
                color="#475569")
    ax.set_yticks([1,2,3],[r"$M_3$",r"$M_2$",r"$M_1$"],fontsize=13)
    ax.set(xlim=(-.1,xmax+.2),ylim=(.35,3.8))
    ax.set_xticks(range(xmax+1))
    ax.xaxis.grid(True,color="#e2e8f0",zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y",length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(title,loc="left",fontsize=14,pad=10)


def rules_figure(results):
    fig,axes=plt.subplots(3,1,figsize=(14,11.6))
    fig.subplots_adjust(left=.08,right=.97,top=.85,bottom=.07,hspace=.42)
    for ax,(rule,data) in zip(axes,results.items()):
        gantt(ax,OPS,data["starts"],15,rf"{rule}：$C_{{\max}}={data['makespan']}$")
    axes[-1].set_xlabel("时间（同加工时间单位）")
    fig.text(.04,.955,"同一末尾追加构造，三种优先级规则",fontsize=21,weight="bold")
    fig.text(.04,.91,"并列时先选当前最早开始时刻更小的工序，再按 job 与工序编号；结果仅对应本例。",
             fontsize=12,color="#6b7280")
    shared.save(fig,"05_dispatch_rules")


def conflict_figure():
    fig,ax=plt.subplots(figsize=(12.6,5.7))
    fig.subplots_adjust(left=.14,right=.96,top=.67,bottom=.18)
    # These are hypothetical next-placement intervals, never a feasible joint schedule.
    for y,v,e,p in [(2,(2,2),2,1),(1,(3,1),0,4)]:
        j,k=v
        ax.barh(y,p,left=e,height=.52,color=shared.PALE[j],edgecolor=shared.COLORS[j],linewidth=2)
        ax.text(e+p/2,y,rf"$O_{{{j},{k}}}$",ha="center",va="center",fontsize=16,color=shared.COLORS[j])
        ax.text(e+p/2,y-.38,rf"$e_{{{j},{k}}}={e},\ \widehat c_{{{j},{k}}}={e+p}$",
                ha="center",va="top",fontsize=12)
    ax.axvline(3,color="#b91c1c",linestyle="--",linewidth=1.8)
    ax.text(3.04,2.65,r"$c^*=3$",color="#b91c1c",fontsize=16)
    ax.set_yticks([1,2],[r"$M_3$：候选二",r"$M_3$：候选一"],fontsize=12)
    ax.set(xlim=(-.1,5),ylim=(.3,2.9),xlabel="假设当前选择该工序时，末尾追加的候选区间")
    ax.set_xticks(range(6))
    ax.xaxis.grid(True,color="#e2e8f0")
    ax.set_axisbelow(True)
    ax.tick_params(axis="y",length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.text(.04,.94,"GT 冲突集：与最早完成候选争用同一台机器",fontsize=19,weight="bold")
    fig.text(.04,.865,"已安排两道首工序；两行是互斥的候选区间，不是同时加工的安排。",fontsize=12,color="#6b7280")
    fig.text(.04,.79,r"$O_{2,2}$ 最早完成，但 $e_{3,1}=0<c^*=3$，所以 $O_{3,1}$ 也在冲突集中。",fontsize=14)
    shared.save(fig,"05_gt_conflict")


def idle_figure(counter,busy,wait):
    fig,axes=plt.subplots(2,1,figsize=(14,8.7))
    fig.subplots_adjust(left=.08,right=.97,top=.81,bottom=.09,hspace=.5)
    gantt(axes[0],counter,busy,22,r"无延迟安排示例：$M_1$ 从 0 立即加工，$C_{\max}=22$")
    gantt(axes[1],counter,wait,22,r"允许主动等待：$M_1$ 等到 1，$C_{\max}=14$")
    axes[1].axvspan(0,1,ymin=.68,ymax=.87,facecolor="#fef3c7",edgecolor="#d97706",hatch="///",zorder=1)
    axes[-1].set_xlabel("时间（同加工时间单位）")
    fig.text(.04,.95,"独立反例：忙碌程度与最大完工时间不是同一个目标",fontsize=20,weight="bold")
    fig.text(.04,.895,"本图使用两作业、三机器的新数据；浅黄色标记机器主动等待的一个时间单位。",fontsize=12,color="#6b7280")
    shared.save(fig,"05_deliberate_idle")


if __name__=="__main__":
    results,counter,busy,wait,report=verify()
    rules_figure(results)
    conflict_figure()
    idle_figure(counter,busy,wait)
    print("Generated 3 PNG diagrams and 3 SVG files with native text.")
    CHECKS_DIR.mkdir(parents=True, exist_ok=True)
    (CHECKS_DIR / "05_numerical_check.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({r:{"Cmax":d["makespan"],"completion":d["job_end"],
                         "sequence":[s["chosen"]["op"] for s in d["trace"]]} for r,d in results.items()}))
