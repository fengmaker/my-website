"""Regenerate portfolio figures from the committed, audited experiment tables.

Optional dependency: matplotlib. Run from any directory; this does not run solvers.
"""
from pathlib import Path
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/assets/projects"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.facecolor": "white", "axes.facecolor": "white"})


def read_table(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def plot_gmrp():
    rows = read_table(ASSETS / "gmrp/m7-methods.csv")
    labels = {"initial": "Initial", "relocate": "Relocate", "vnd": "VND", "random-lns": "Random LNS",
              "alns": "Adaptive ALNS", "restricted": "ALNS + restricted repair"}
    positions = np.arange(len(rows))
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), gridspec_kw={"width_ratios": [1.2, 1]})
    colors = ["#596b86" if row["method"] not in {"alns", "restricted"} else "#187d9a" for row in rows]
    values = [float(row["mean_improvement_percent"]) for row in rows]
    axes[0].barh(positions, values, color=colors, height=.62)
    axes[0].set_yticks(positions, [labels[row["method"]] for row in rows])
    axes[0].invert_yaxis()
    axes[0].set_xlim(0, max(values) * 1.2)
    axes[0].set_xlabel("Mean cost reduction from initial assignment (%)")
    axes[0].set_title("Returned solution quality", loc="left", fontweight="bold")
    for y, value in zip(positions, values):
        axes[0].text(value + .18, y, f"{value:.3f}%", va="center", fontsize=9)
    runtime = [float(row["mean_solver_seconds"]) for row in rows]
    axes[1].barh(positions, runtime, color=colors, height=.62)
    axes[1].axvline(1.1, color="#b85a26", linestyle="--", linewidth=1.4, label="1.1 s overrun threshold")
    axes[1].set_yticks(positions, [""] * len(rows))
    axes[1].invert_yaxis()
    axes[1].set_xlim(0, max(runtime) * 1.55)
    axes[1].set_xlabel("Mean complete solver-call time (s)")
    axes[1].set_title("Time and overruns", loc="left", fontweight="bold")
    for y, value, row in zip(positions, runtime, rows):
        axes[1].text(value + .02, y, f"{value:.3f} s | {row['overruns']}/100", va="center", fontsize=9)
    handles, legend_labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="lower left", bbox_to_anchor=(.64, .07), fontsize=9, frameon=False)
    fig.suptitle("GMRP M7 | 20 instances x 5 seeds per main method", x=.03, ha="left", fontweight="bold")
    fig.text(.03, .015, "Requested budget: 1 s. Overrun counts are per method; results include overruns. Lower cost is better.", fontsize=9)
    fig.tight_layout(rect=[0, .16, 1, .93])
    fig.savefig(ASSETS / "gmrp/m7-quality-runtime.png", dpi=170)
    plt.close(fig)


def plot_vrptw():
    rows = [row for row in read_table(ASSETS / "vrptw/four-solver-summary.csv") if row["solver"] == "ours"]
    rows.sort(key=lambda row: float(row["budget_seconds"]))
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), gridspec_kw={"width_ratios": [1.1, 1]})
    positions = np.arange(len(rows))
    left = np.zeros(len(rows))
    for key, label, color in [("vehicle_better_vs_pyvrp", "Fewer vehicles", "#187d9a"),
                              ("vehicle_equal_vs_pyvrp", "Same vehicles", "#94a5ba"),
                              ("vehicle_worse_vs_pyvrp", "More vehicles", "#c27736")]:
        values = np.array([int(row[key]) for row in rows])
        axes[0].barh(positions, values, left=left, color=color, label=label, height=.5)
        for y, value, offset in zip(positions, values, left):
            if value:
                axes[0].text(offset + value / 2, y, str(value), ha="center", va="center", color="white", fontweight="bold")
        left += values
    labels = [f"{float(row['budget_seconds']):g} s" for row in rows]
    axes[0].set_yticks(positions, labels)
    axes[0].invert_yaxis()
    axes[0].set_xlim(0, 56)
    axes[0].set_xlabel("Instances (56 total; ours compared with configured PyVRP)")
    axes[0].set_title("Vehicle count comes first", loc="left", fontweight="bold")
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="lower left", bbox_to_anchor=(.04, .07), ncol=3, fontsize=9, frameon=False)
    for shift, key, label, color in [(-.16, "same_vehicle_distance_gap_median_percent", "Median", "#187d9a"),
                                    (.16, "same_vehicle_distance_gap_p90_percent", "P90", "#94a5ba")]:
        values = [float(row[key]) for row in rows]
        axes[1].barh(positions + shift, values, height=.28, color=color, label=label)
        for y, value in zip(positions + shift, values):
            axes[1].text(value + .6, y, f"{value:.3f}%", va="center", fontsize=9)
    axes[1].set_yticks(positions, [f"{label} (n={row['same_vehicle_distance_gap_count']})" for label, row in zip(labels, rows)])
    axes[1].invert_yaxis()
    axes[1].set_xlim(0, 55)
    axes[1].set_xlabel("(Ours / PyVRP - 1) x 100%; lower is better")
    axes[1].set_title("Distance on equal-vehicle cases only", loc="left", fontweight="bold")
    handles, legend_labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="lower left", bbox_to_anchor=(.62, .07), ncol=2, fontsize=9, frameon=False)
    fig.suptitle("VRPTW four-solver study | our M12 vs configured PyVRP", x=.03, ha="left", fontweight="bold")
    fig.text(.03, .015, "Seed 0; equal-vehicle subsets selected separately per budget. No best-known-value or optimality claim.", fontsize=9)
    fig.tight_layout(rect=[0, .16, 1, .93])
    fig.savefig(ASSETS / "vrptw/fleet-distance.png", dpi=170)
    plt.close(fig)


if __name__ == "__main__":
    plot_gmrp()
    plot_vrptw()
    print("Regenerated 2 portfolio figures; no solvers executed.")
