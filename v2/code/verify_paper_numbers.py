#!/usr/bin/env python3
"""Recompute every number the paper reports, from the released measurements alone.

Each check prints the value published in the paper alongside the value computed here.
The script exits non-zero if any check fails, so it can be used as a regression test
on the released artifacts.

Requires pandas. Krippendorff's alpha is checked only if the `krippendorff` package
is installed; without it that one check is skipped rather than failed.

Usage, from the repository root or from this directory:

    python code/verify_paper_numbers.py
"""

import sys
from pathlib import Path

import pandas as pd

STAGES = ("front", "second", "third")
KPIS = ("FCD", "FGR", "FDF", "ECS", "OSR")

# Weighting configurations of Table 2, in the order w1..w5 = FCD, FGR, FDF, ECS, OSR.
CONFIGS = {
    "Baseline": (0.200, 0.200, 0.200, 0.200, 0.200),
    "ObservabilityAware": (0.125, 0.125, 0.250, 0.250, 0.250),
    "SecurityFirst": (0.250, 0.250, 0.167, 0.167, 0.166),
    "ResearchMode": (0.100, 0.100, 0.267, 0.267, 0.266),
    "ExtremeObservability": (0.080, 0.080, 0.280, 0.280, 0.280),
}

N_AGENTS = 3
ATTAINABLE_RANGE = 1 / 3  # spanned by [-w3-w4-w5, w1+w2] / N_AGENTS for weights summing to one

failures = []
skipped = []


def check(label, published, computed, tol=5e-4, fmt="{:.4f}"):
    """Compare a computed value against the one printed in the paper."""
    ok = abs(computed - published) <= tol
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label:52s} paper {fmt.format(published):>9s}   computed {fmt.format(computed):>9s}")
    if not ok:
        failures.append(label)


def find_root():
    here = Path(__file__).resolve().parent
    for candidate in (here.parent, here, Path.cwd()):
        if (candidate / "data" / "kpi_per_prompt.csv").exists():
            return candidate
    sys.exit("Could not locate data/kpi_per_prompt.csv. Run from the repository root.")


def ths(df, stage, weights, include_osr=True):
    """Total Hallucination Score of Equation 1. More negative means stronger mitigation."""
    w1, w2, w3, w4, w5 = weights
    total = w1 * df[f"{stage}_FCD"] + w2 * df[f"{stage}_FGR"] - w3 * df[f"{stage}_FDF"] - w4 * df[f"{stage}_ECS"]
    denom = sum(weights)
    if include_osr:
        total = total - w5 * df[f"{stage}_OSR"]
    else:
        denom = sum(weights[:4])
    return (total / (N_AGENTS * denom)).mean()


def main():
    root = find_root()
    df = pd.read_csv(root / "data" / "kpi_per_prompt.csv")

    print(f"\nkpi_per_prompt.csv: {len(df)} rows, subsets {df.subset.value_counts().to_dict()}")

    print("\n== Benchmark composition (Table 1) ==")
    check("prompt count", 310, len(df), tol=0, fmt="{:.0f}")
    check("realistic prompts", 217, (df.subset == "realistic").sum(), tol=0, fmt="{:.0f}")
    check("stress prompts", 93, (df.subset == "stress").sum(), tol=0, fmt="{:.0f}")

    print("\n== Weighting configurations sum to one (Table 2) ==")
    for name, w in CONFIGS.items():
        check(f"sum of weights, {name}", 1.0, sum(w), tol=1e-9, fmt="{:.3f}")

    print("\n== Mean KPI per stage (Table 3) ==")
    published_kpi = {
        "FCD": (0.480, 0.429, 0.474),
        "FGR": (0.283, 0.298, 0.259),
        "FDF": (0.178, 0.236, 0.187),
        "ECS": (0.438, 0.581, 0.640),
        "OSR": (0.153, 0.378, 0.083),
    }
    for kpi, pub in published_kpi.items():
        for stage, value in zip(STAGES, pub):
            check(f"{kpi} at {stage} stage", value, df[f"{stage}_{kpi}"].mean(), tol=5e-4, fmt="{:.3f}")

    print("\n== Four-KPI THS, the primary convention with w5 = 0 (Section 6.4) ==")
    equal = (0.25, 0.25, 0.25, 0.25, 0.0)
    v = [ths(df, s, equal, include_osr=False) for s in STAGES]
    check("THS at front stage", +0.0123, v[0])
    check("THS at second stage", -0.0075, v[1])
    check("THS at third stage", -0.0080, v[2])
    check("end-to-end change", -0.0202, v[2] - v[0])
    check("end-to-end as share of attainable range", 6.1, abs(v[2] - v[0]) / ATTAINABLE_RANGE * 100, tol=0.05, fmt="{:.1f}")
    check("first review step", -0.0198, v[1] - v[0])
    check("first review step as share of total", 97.7, abs(v[1] - v[0]) / abs(v[2] - v[0]) * 100, tol=0.05, fmt="{:.1f}")
    check("second review step", -0.0005, v[2] - v[1])

    print("\n== Exact per-KPI decomposition, end to end (Section 7) ==")
    deltas = {k: df[f"third_{k}"].mean() - df[f"front_{k}"].mean() for k in KPIS[:4]}
    signs = {"FCD": +1, "FGR": +1, "FDF": -1, "ECS": -1}
    contrib = {k: signs[k] * 0.25 * deltas[k] / N_AGENTS for k in deltas}
    total = sum(contrib.values())
    for kpi, pub in (("ECS", 83.5), ("FGR", 10.0), ("FDF", 3.8), ("FCD", 2.6)):
        check(f"share of movement, {kpi}", pub, contrib[kpi] / total * 100, tol=0.05, fmt="{:.1f}")
    check("shares sum to 100", 100.0, sum(contrib[k] / total * 100 for k in contrib), tol=0.05, fmt="{:.1f}")

    print("\n== Five-KPI THS per stage (Table 7) ==")
    published_ths = {
        "Baseline": (-0.0004, -0.0312, -0.0119, -0.0115),
        "ObservabilityAware": (-0.0323, -0.0693, -0.0454, -0.0131),
        "SecurityFirst": (+0.0208, -0.0058, +0.0103, -0.0105),
        "ResearchMode": (-0.0430, -0.0820, -0.0566, -0.0137),
        "ExtremeObservability": (-0.0514, -0.0922, -0.0655, -0.0141),
    }
    for name, w in CONFIGS.items():
        stages = [ths(df, s, w) for s in STAGES]
        pub = published_ths[name]
        for stage, value, p in zip(STAGES, stages, pub[:3]):
            check(f"{name} at {stage} stage", p, value)
        check(f"{name} end to end", pub[3], stages[2] - stages[0])

    print("\n== Sign reversal of the aggregate in w5 (Section 6.1) ==")
    a = deltas["FCD"] + deltas["FGR"] - deltas["FDF"] - deltas["ECS"]
    b = -(df["third_OSR"].mean() - df["front_OSR"].mean())
    for w5, pub in ((0.00, -0.0202), (0.20, -0.0115), (0.60, +0.0060)):
        check(f"end-to-end change at w5 = {w5:.2f}", pub, ((1 - w5) / 4 * a + w5 * b) / N_AGENTS)
    check("crossing point w5*", 0.463, (-a / 4) / (b - a / 4), tol=5e-4, fmt="{:.3f}")

    print("\n== Semantic cache (Table 5) ==")
    hits = [int(df[f"{s}_cache_hit"].sum()) for s in STAGES]
    for stage, h, pub in zip(STAGES, hits, (46.1, 47.4, 49.7)):
        check(f"hit rate at {stage} stage", pub, h / len(df) * 100, tol=0.05, fmt="{:.1f}")
    check("total cache hits", 444, sum(hits), tol=0, fmt="{:.0f}")
    check("aggregate hit rate", 47.7, sum(hits) / (len(df) * N_AGENTS) * 100, tol=0.05, fmt="{:.1f}")
    check("fresh inference calls", 486, len(df) * N_AGENTS - sum(hits), tol=0, fmt="{:.0f}")

    print("\n== ECS by subset (Appendix A) ==")
    realistic = df[df.subset == "realistic"]
    stress = df[df.subset == "stress"]
    check("first-stage ECS, realistic", 0.432, realistic.front_ECS.mean(), tol=5e-4, fmt="{:.3f}")
    check("first-stage ECS, stress", 0.450, stress.front_ECS.mean(), tol=5e-4, fmt="{:.3f}")
    check("final-stage ECS, realistic", 0.560, realistic.third_ECS.mean(), tol=5e-4, fmt="{:.3f}")
    check("final-stage ECS, stress", 0.828, stress.third_ECS.mean(), tol=5e-4, fmt="{:.3f}")
    check("front-to-third rise, realistic", 0.128, realistic.third_ECS.mean() - realistic.front_ECS.mean(), tol=5e-4, fmt="{:.3f}")
    check("front-to-third rise, stress", 0.378, stress.third_ECS.mean() - stress.front_ECS.mean(), tol=5e-4, fmt="{:.3f}")
    check("pooled rise", 0.203, df.third_ECS.mean() - df.front_ECS.mean(), tol=5e-4, fmt="{:.3f}")

    print("\n== Known defects of the run (Section 11) ==")
    check("substituted evaluator rows", 27, int(df.evaluator_substituted.sum()), tol=0, fmt="{:.0f}")
    check("third-stage responses on the OSR clamp floor", 197, int((df.third_OSR == 0.05).sum()), tol=0, fmt="{:.0f}")
    check("mean response length, first stage, words", 308, df.front_len_words.mean(), tol=0.5, fmt="{:.0f}")
    check("mean response length, third stage, words", 45, df.third_len_words.mean(), tol=0.5, fmt="{:.0f}")

    ann_path = root / "annotation" / "REF3_scored.csv"
    if ann_path.exists():
        ann = pd.read_csv(ann_path)
        print("\n== Human annotation of the fabrication subset (Section 8.1) ==")
        check("items labelled", 93, len(ann), tol=0, fmt="{:.0f}")
        endorse = ann["final"].isin([3, 4]).sum()
        check("endorsement rate, percent", 10.8, endorse / len(ann) * 100, tol=0.05, fmt="{:.1f}")
        check("refutation or non-verification, percent", 60.2, ann["final"].isin([0, 1]).sum() / len(ann) * 100, tol=0.05, fmt="{:.1f}")
        check("silent on the referent, percent", 29.0, (ann["final"] == 2).sum() / len(ann) * 100, tol=0.05, fmt="{:.1f}")
        per_coder = sorted(ann[c].isin([3, 4]).sum() / len(ann) * 100 for c in "ABC")
        check("lowest per-coder endorsement, percent", 6.5, per_coder[0], tol=0.05, fmt="{:.1f}")
        check("highest per-coder endorsement, percent", 19.4, per_coder[-1], tol=0.05, fmt="{:.1f}")
        for code, pub in ((0, 0.947), (1, 0.908), (2, 0.740), (3, 0.495)):
            check(f"mean ECS at resolved code {code}", pub, ann[ann["final"] == code].ECS.mean(), tol=5e-4, fmt="{:.3f}")
        non_end = ann[ann["final"].isin([0, 1])].ECS.mean()
        check("ECS gap, endorsing minus non-endorsing", -0.435, ann[ann["final"].isin([3, 4])].ECS.mean() - non_end, tol=5e-4, fmt="{:.3f}")
        check("responses at ECS 1.0", 54, int((ann.ECS == 1.0).sum()), tol=0, fmt="{:.0f}")
        check("endorsing responses at ECS 1.0", 0, int((ann[ann["final"].isin([3, 4])].ECS == 1.0).sum()), tol=0, fmt="{:.0f}")

        try:
            import itertools

            import krippendorff

            print("\n== Inter-annotator agreement (Section 8.1) ==")
            alpha = krippendorff.alpha(reliability_data=ann[["A", "B", "C"]].T.values, level_of_measurement="ordinal")
            check("Krippendorff's ordinal alpha, three coders", 0.586, alpha, tol=5e-4, fmt="{:.3f}")
            pairwise = sorted(
                krippendorff.alpha(reliability_data=ann[[x, y]].T.values, level_of_measurement="ordinal")
                for x, y in itertools.combinations("ABC", 2)
            )
            for pub, value in zip((0.499, 0.552, 0.712), pairwise):
                check(f"pairwise alpha {pub:.3f}", pub, value, tol=5e-4, fmt="{:.3f}")
        except ImportError:
            print("\n== Inter-annotator agreement: SKIPPED, the krippendorff package is not installed ==")
            skipped.append("Krippendorff's alpha")

        print("\n== Alignment of each judge with the human labels (Table 8) ==")
        judges = {
            "l-orig": None,
            "l-spec": "judge_llama3_1_latest_930.csv",
            "g-spec": "judge_gemma4_12b_930.csv",
            "q-spec": "judge_qwen3_8b_930.csv",
        }
        published_rho = {"l-orig": -0.477, "l-spec": -0.599, "g-spec": -0.772, "q-spec": -0.627}
        for name, filename in judges.items():
            if filename is None:
                ecs = ann.set_index("promptid").ECS
            else:
                path = root / "data" / filename
                if not path.exists():
                    print(f"  [SKIP] {name}: {filename} not found")
                    skipped.append(name)
                    continue
                j = pd.read_csv(path)
                ecs = j[j.stage == "third"].set_index("promptid").ECS
            merged = ann.set_index("promptid").join(ecs.rename("judge_ecs"), how="inner")
            rho = merged["judge_ecs"].corr(merged["final"], method="spearman")
            check(f"Spearman rho, {name} against resolved label", published_rho[name], rho, tol=5e-4, fmt="{:.3f}")
    else:
        print("\n== Human annotation: SKIPPED, annotation/REF3_scored.csv not found ==")
        skipped.append("human annotation")

    print()
    if failures:
        print(f"{len(failures)} CHECK(S) FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("All checks passed." + (f" Skipped: {', '.join(skipped)}." if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
