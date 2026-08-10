#!/usr/bin/env python3
"""
regen_figures.py - regenerate the six appendix figures under the corrected
FGR sign of Equation 1 (FCD and FGR both enter positively; FDF, ECS, OSR are
subtracted). Reads only the released per-prompt dataset.

    python3 regen_figures.py pipeline_results_with_NL.csv outdir/
"""
import ast
import sys
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

CSV = sys.argv[1] if len(sys.argv) > 1 else "pipeline_results_with_NL.csv"
OUT = sys.argv[2] if len(sys.argv) > 2 else "."
os.makedirs(OUT, exist_ok=True)

K = ["FCD", "FGR", "FDF", "ECS", "OSR"]
SIGN = {"FCD": +1, "FGR": +1, "FDF": -1, "ECS": -1, "OSR": -1}
NA = 3
STAGES = [("FrontEndAgent", "1st: FrontEndAgent"),
          ("SecondLevelReviewer", "2nd: SecondLevelReviewer"),
          ("ThirdLevelReviewer", "3rd: ThirdLevelReviewer")]
CFG = {"Baseline": (.200, .200, .200, .200, .200),
       "ObservAware": (.125, .125, .250, .250, .250),
       "SecurityFirst": (.250, .250, .167, .167, .166),
       "ResearchMode": (.100, .100, .267, .267, .266),
       "ExtremeObs": (.080, .080, .280, .280, .280)}
COL = ["#c0504d", "#4f81bd", "#4a7c59"]

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "legend.fontsize": 8, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.grid": True, "grid.alpha": .25, "grid.linewidth": .5,
    "axes.spines.top": False, "axes.spines.right": False,
    "figure.dpi": 200, "savefig.dpi": 200, "savefig.bbox": "tight",
})

d = pd.read_csv(CSV).sort_values("promptid").reset_index(drop=True)
for col, _ in STAGES:
    parsed = d[col].map(ast.literal_eval)
    for k in K:
        d[f"{col}__{k}"] = parsed.map(lambda x: x[k])


def ths(col, w):
    z = sum(w.values())
    return sum(SIGN[k] * w[k] * d[f"{col}__{k}"] for k in K) / (NA * z)


def wdict(t):
    return dict(zip(K, t))


def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p)
    plt.close(fig)
    print("wrote", p)


# ---------------------------------------------------------------- figure 1
fig, ax = plt.subplots(figsize=(9.0, 3.4))
x = np.arange(len(K))
wid = .26
for i, (col, lab) in enumerate(STAGES):
    means = [d[f"{col}__{k}"].mean() for k in K]
    errs = [d[f"{col}__{k}"].std() / np.sqrt(len(d)) for k in K]
    b = ax.bar(x + (i - 1) * wid, means, wid, yerr=errs, capsize=2,
               label=lab, color=COL[i], edgecolor="white", linewidth=.6)
    ax.bar_label(b, fmt="%.3f", fontsize=6.5, padding=1)
ax.set_xticks(x)
ax.set_xticklabels(["FCD\n(lower better)", "FGR\n(lower better)",
                    "FDF\n(higher better)", "ECS\n(higher better)",
                    "OSR\n(higher better)"])
ax.set_ylabel("mean KPI value")
ax.set_ylim(0, max(d[f"{c}__{k}"].mean() for c, _ in STAGES for k in K) * 1.35)
ax.legend(loc="upper right", frameon=False, ncol=1)
ax.set_title("KPI means per pipeline stage, all 310 prompts "
             "(error bars: standard error of the mean)")
save(fig, "kpi_comparison_all_agents.png")

# ---------------------------------------------------------------- figure 2
hits = (d[["frontend_cache_hit", "second_cache_hit",
           "third_cache_hit"]].astype(bool).sum(axis=1))
fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.1))
a = axes[0]
a.plot(d.promptid, hits.cumsum(), color="#4f81bd", lw=1.6)
a.set_xlabel("prompt index")
a.set_ylabel("cumulative cache hits")
a.set_title("(a) cumulative hits over the run (total %d of %d calls, %.1f%%)"
            % (int(hits.sum()), 3 * len(d), 100 * hits.sum() / (3 * len(d))))
a.axhline(hits.sum(), ls=":", lw=.8, color="grey")
b = axes[1]
roll = (hits / 3).rolling(10, min_periods=1).mean()
b.plot(d.promptid, roll, color="#c0504d", lw=1.2)
b.axhline(hits.sum() / (3 * len(d)), ls="--", lw=.9, color="k",
          label="run mean %.1f%%" % (100 * hits.sum() / (3 * len(d))))
b.axvline(216.5, ls=":", lw=.9, color="#4a7c59")
b.text(219, .05, "stress subset", fontsize=7, color="#4a7c59", rotation=90)
b.yaxis.set_major_formatter(PercentFormatter(1.0))
b.set_ylim(0, 1)
b.set_xlabel("prompt index")
b.set_ylabel("hit rate, rolling 10 prompts")
b.set_title("(b) rolling hit rate; spikes track benchmark redundancy")
b.legend(frameon=False, loc="lower right")
save(fig, "nl_memory_utilization.png")

# ---------------------------------------------------------------- figure 3
wB = wdict(CFG["Baseline"])
t = {c: ths(c, wB) for c, _ in STAGES}
fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.1))
a = axes[0]
for i, (c, lab) in enumerate(STAGES):
    a.plot(d.promptid, t[c], lw=.7, alpha=.85, color=COL[i], label=lab)
a.set_xlabel("prompt index")
a.set_ylabel("THS (Baseline weighting)")
a.set_title("(a) per-prompt THS by stage, corrected FGR sign")
a.legend(frameon=False, fontsize=7, loc="upper left")
a2 = a.twinx()
a2.plot(d.promptid, hits.cumsum(), color="grey", lw=1.0, ls="--")
a2.set_ylabel("cumulative cache hits", color="grey")
a2.tick_params(axis="y", colors="grey")
a2.grid(False)
b = axes[1]
delta = t["SecondLevelReviewer"] - t["FrontEndAgent"]
b.bar(d.promptid, delta, width=1.0,
      color=np.where(delta < 0, "#4a7c59", "#c0504d"))
b.axhline(delta.mean(), ls="--", lw=1.0, color="k",
          label="mean %+.4f" % delta.mean())
b.set_xlabel("prompt index")
b.set_ylabel(r"$\Delta$THS, 1st $\to$ 2nd")
b.set_title("(b) per-prompt change at the first review stage\n"
            "(green = THS falls, i.e. stronger mitigation signal)")
b.legend(frameon=False, loc="lower right")
save(fig, "nl_ths_evolution.png")

# ---------------------------------------------------------------- figure 4
fig, ax = plt.subplots(figsize=(8.0, 3.3))
names = list(CFG)
x = np.arange(len(names))
wid = .26
for i, (c, lab) in enumerate(STAGES):
    vals = [ths(c, wdict(CFG[n])).mean() for n in names]
    bb = ax.bar(x + (i - 1) * wid, vals, wid, label=lab, color=COL[i],
                edgecolor="white", linewidth=.6)
    ax.bar_label(bb, fmt="%.3f", fontsize=6.5, padding=2)
ax.axhline(0, color="k", lw=.8)
ax.set_xticks(x)
ax.set_xticklabels(names)
ax.set_ylabel("mean THS")
ax.set_title("Mean THS per stage across weighting configurations "
             "(not comparable across configurations)")
ax.legend(frameon=False, ncol=3, loc="lower center",
          bbox_to_anchor=(.5, -.42))
save(fig, "nl_ths_comparison_all_scenarios.png")


# ---------------------------------------------------------------- figures 5-6
def distribution_figure(cfgname, fname):
    w = wdict(CFG[cfgname])
    tt = {c: ths(c, w) for c, _ in STAGES}
    fig, axes = plt.subplots(2, 2, figsize=(9.0, 6.0))

    a = axes[0, 0]
    for i, (c, lab) in enumerate(STAGES):
        a.plot(d.promptid, tt[c], lw=.6, alpha=.8, color=COL[i], label=lab)
    a.set_xlabel("prompt index")
    a.set_ylabel("THS")
    a.set_title("(a) per-prompt THS progression")
    a.legend(frameon=False, fontsize=7)

    b = axes[0, 1]
    means = [tt[c].mean() for c, _ in STAGES]
    steps = [means[0], means[1] - means[0], means[2] - means[1]]
    labels = ["1st\n(level)", r"1st $\to$ 2nd", r"2nd $\to$ 3rd"]
    base = [0, means[0], means[1]]
    cols = ["#7f7f7f",
            "#4a7c59" if steps[1] < 0 else "#c0504d",
            "#4a7c59" if steps[2] < 0 else "#c0504d"]
    for i in range(3):
        b.bar(i, steps[i], bottom=base[i], color=cols[i],
              edgecolor="white", linewidth=.8)
        b.text(i, base[i] + steps[i] + (.0012 if steps[i] > 0 else -.0022),
               "%+.4f" % steps[i], ha="center", fontsize=7.5)
    b.axhline(0, color="k", lw=.8)
    b.axhline(means[2], ls=":", lw=.8, color="grey")
    b.set_xticks(range(3))
    b.set_xticklabels(labels)
    b.set_ylabel("mean THS")
    b.set_title("(b) where the end-to-end change comes from\n"
                "(total %+.5f, front-stage level %+.5f)"
                % (means[2] - means[0], means[0]))

    c3 = axes[1, 0]
    third = tt["ThirdLevelReviewer"]
    hit = d.third_cache_hit.astype(bool)
    bins = np.linspace(third.min(), third.max(), 26)
    c3.hist([third[hit], third[~hit]], bins=bins, stacked=False,
            color=["#4f81bd", "#d9a55c"], edgecolor="white", linewidth=.5,
            label=["cache hit (n=%d)" % int(hit.sum()),
                   "freshly generated (n=%d)" % int((~hit).sum())])
    c3.axvline(third[hit].mean(), color="#4f81bd", ls="--", lw=1.0)
    c3.axvline(third[~hit].mean(), color="#d9a55c", ls="--", lw=1.0)
    c3.set_xlabel("third-stage THS")
    c3.set_ylabel("prompts")
    c3.set_title("(c) third-stage THS, cache-served vs fresh\n"
                 "means %+.5f vs %+.5f (difference %+.5f)"
                 % (third[hit].mean(), third[~hit].mean(),
                    third[hit].mean() - third[~hit].mean()))
    c3.legend(frameon=False, fontsize=7)

    d4 = axes[1, 1]
    for i, (c, lab) in enumerate(STAGES):
        v = np.sort(tt[c].values)
        d4.plot(v, np.arange(1, len(v) + 1) / len(v), lw=1.3,
                color=COL[i], label=lab)
    d4.set_xlabel("THS")
    d4.set_ylabel("cumulative fraction")
    d4.yaxis.set_major_formatter(PercentFormatter(1.0))
    d4.set_title("(d) cumulative distribution by stage")
    d4.legend(frameon=False, fontsize=7, loc="lower right")

    fig.suptitle("THS distribution, %s weighting, corrected FGR sign"
                 % cfgname, fontsize=10.5, y=1.01)
    fig.tight_layout()
    save(fig, fname)


distribution_figure("Baseline", "ths_distribution_baseline.png")
distribution_figure("ExtremeObs", "ths_distribution_extremeobservability.png")
distribution_figure("ObservAware", "ths_distribution_observabilityaware.png")
distribution_figure("ResearchMode", "ths_distribution_researchmode.png")
distribution_figure("SecurityFirst", "ths_distribution_securityfirst.png")

# ------------------------------------------------- numbers for the appendix
print("\nper-stage means and cache-hit vs fresh difference at stage 3,")
print("corrected FGR sign, all 310 prompts:")
for n in CFG:
    w = wdict(CFG[n])
    tt = {c: ths(c, w) for c, _ in STAGES}
    third = tt["ThirdLevelReviewer"]
    h = d.third_cache_hit.astype(bool)
    print("  %-14s %+.5f -> %+.5f -> %+.5f   hit %+.5f vs fresh %+.5f"
          "  diff %+.5f" % (n, tt["FrontEndAgent"].mean(),
                            tt["SecondLevelReviewer"].mean(), third.mean(),
                            third[h].mean(), third[~h].mean(),
                            third[h].mean() - third[~h].mean()))
