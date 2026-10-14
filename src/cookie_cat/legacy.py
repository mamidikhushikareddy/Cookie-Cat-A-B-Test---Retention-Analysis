"""Validated analysis and decision stress testing for the Cookie Cats experiment."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import math
import pandas as pd
import numpy as np
from scipy.stats import norm, mannwhitneyu, chi2_contingency
from statsmodels.stats.proportion import proportions_ztest, proportion_confint
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

REQUIRED = {"userid", "version", "sum_gamerounds", "retention_1", "retention_7"}
GROUP_ORDER = ["gate_30", "gate_40"]

@dataclass
class GroupMetric:
    group: str
    n: int
    retention_1_count: int
    retention_1_rate: float
    retention_7_count: int
    retention_7_rate: float
    mean_rounds: float
    median_rounds: float

def load_and_validate(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = REQUIRED - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if df.empty:
        raise ValueError("Dataset is empty.")
    if df["userid"].isna().any() or df["userid"].duplicated().any():
        raise ValueError("userid must be non-null and unique.")
    df["version"] = df["version"].astype(str).str.strip()
    if not set(df["version"].unique()).issubset(set(GROUP_ORDER)) or set(df["version"].unique()) != set(GROUP_ORDER):
        raise ValueError("Expected both groups: gate_30 and gate_40.")
    df["sum_gamerounds"] = pd.to_numeric(df["sum_gamerounds"], errors="coerce")
    if df["sum_gamerounds"].isna().any() or (df["sum_gamerounds"] < 0).any():
        raise ValueError("sum_gamerounds must be numeric and non-negative.")
    for col in ["retention_1", "retention_7"]:
        if df[col].isna().any():
            raise ValueError(f"{col} contains missing values.")
        normalized = df[col].map(lambda x: str(x).strip().lower())
        mapping = {"true": True, "false": False, "1": True, "0": False}
        if not normalized.isin(mapping).all():
            raise ValueError(f"{col} must contain boolean values.")
        df[col] = normalized.map(mapping).astype(bool)
    return df

def _wilson(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    lo, hi = proportion_confint(successes, n, alpha=alpha, method="wilson")
    return float(lo), float(hi)

def analyze(df: pd.DataFrame) -> dict:
    """Compute baseline results from observed rows; no result is hardcoded."""
    metrics = []
    for group in GROUP_ORDER:
        g = df.loc[df.version == group]
        n = int(len(g))
        d = GroupMetric(
            group=group, n=n,
            retention_1_count=int(g.retention_1.sum()),
            retention_1_rate=float(g.retention_1.mean()),
            retention_7_count=int(g.retention_7.sum()),
            retention_7_rate=float(g.retention_7.mean()),
            mean_rounds=float(g.sum_gamerounds.mean()),
            median_rounds=float(g.sum_gamerounds.median()),
        )
        metrics.append(asdict(d))
    by = {m["group"]: m for m in metrics}
    c, t = by["gate_30"], by["gate_40"]
    # Positive effect means gate_40 minus gate_30; preserve explicit direction.
    x = np.array([t["retention_7_count"], c["retention_7_count"]], dtype=float)
    n = np.array([t["n"], c["n"]], dtype=float)
    z_stat, p_value = proportions_ztest(x, n, alternative="two-sided")
    diff = t["retention_7_rate"] - c["retention_7_rate"]
    # Newcombe hybrid Wilson interval for independent proportions.
    tlo, thi = _wilson(t["retention_7_count"], t["n"])
    clo, chi = _wilson(c["retention_7_count"], c["n"])
    ci_low = diff - math.sqrt((t["retention_7_rate"] - tlo)**2 + (chi - c["retention_7_rate"])**2)
    ci_high = diff + math.sqrt((thi - t["retention_7_rate"])**2 + (c["retention_7_rate"] - clo)**2)
    p1_stat, p1 = proportions_ztest(
        [t["retention_1_count"], c["retention_1_count"]], [t["n"], c["n"]]
    )
    # Sample-ratio mismatch diagnostic against a 50/50 assignment assumption.
    observed = np.array([c["n"], t["n"]], dtype=float)
    # Goodness-of-fit against a 50/50 allocation assumption. Confirm the actual design.
    expected = np.repeat(observed.sum()/2, 2)
    srm_chi2 = float(np.sum((observed - expected)**2 / expected))
    from scipy.stats import chi2
    srm_p = float(chi2.sf(srm_chi2, df=1))
    rounds_c = df.loc[df.version == "gate_30", "sum_gamerounds"].to_numpy()
    rounds_t = df.loc[df.version == "gate_40", "sum_gamerounds"].to_numpy()
    mw = mannwhitneyu(rounds_t, rounds_c, alternative="two-sided", method="asymptotic")
    # Approximate common-language effect P(random gate_40 rounds > random gate_30 rounds).
    # U/(n_t*n_c) is directionally meaningful but tied observations are counted half by Mann–Whitney.
    cles = float(mw.statistic / (len(rounds_t) * len(rounds_c)))
    # Two-sided p-values for retention_1 and retention_7; Holm adjustment.
    raw_ps = sorted([(float(p1), "retention_1"), (float(p_value), "retention_7")])
    holm = {}
    for rank, (p, name) in enumerate(raw_ps):
        holm[name] = min(1.0, p * (len(raw_ps) - rank))
    # Sample size per group for 80% power at alpha .05 for selected MDE in absolute points.
    base = c["retention_7_rate"]
    target = min(0.999, max(0.001, base + 0.01))
    effect = abs(proportion_effectsize(target, base))
    try:
        n_per_arm_1pp = int(math.ceil(NormalIndPower().solve_power(effect_size=effect, power=.80, alpha=.05, ratio=1, alternative="two-sided")))
    except Exception:
        n_per_arm_1pp = None
    recommendation = "HOLD / INVESTIGATE" if (diff < 0 or srm_p < .01) else "CONSIDER ROLLOUT"
    reasons = []
    if diff < 0:
        reasons.append("The gate_40 group has lower observed Day-7 retention.")
    if srm_p < .01:
        reasons.append("The observed allocation differs from an assumed 50/50 split; verify the randomization plan and assignment logs before relying on the experiment.")
    if not reasons:
        reasons.append("The observed Day-7 result is not negative and no severe 50/50 allocation warning was detected; evaluate the pre-registered guardrails before shipping.")
    return {
        "n_total": int(len(df)),
        "groups": metrics,
        "retention_7": {
            "gate_30": c["retention_7_rate"], "gate_40": t["retention_7_rate"],
            "gate_30_count": c["retention_7_count"], "gate_40_count": t["retention_7_count"],
            "difference_pp": float(diff * 100), "difference": float(diff),
            "ci_low_pp": float(ci_low * 100), "ci_high_pp": float(ci_high * 100),
            "z_statistic": float(z_stat), "p_value": float(p_value), "holm_adjusted_p": float(holm["retention_7"]),
        },
        "retention_1": {
            "gate_30": c["retention_1_rate"], "gate_40": t["retention_1_rate"],
            "difference_pp": float((t["retention_1_rate"] - c["retention_1_rate"]) * 100),
            "p_value": float(p1), "holm_adjusted_p": float(holm["retention_1"]),
        },
        "experiment_health": {
            "srm_chi2": float(srm_chi2), "srm_p_value": float(srm_p),
            "assumption": "50/50 assignment expected; confirm against actual experiment design.",
            "warning": bool(srm_p < .01),
        },
        "engagement": {
            "mann_whitney_u": float(mw.statistic), "p_value": float(mw.pvalue),
            "common_language_effect_gate40_gt_gate30": cles,
            "interpretation": "Probability-scale effect estimate based on rank statistic; not a causal explanation."
        },
        "planning": {"approx_n_per_arm_for_1pp_mde_80pct_power": n_per_arm_1pp, "alpha": .05, "power": .80},
        "decision": {"recommendation": recommendation, "reasons": reasons},
        "data_quality": {
            "row_count": int(len(df)), "unique_users": int(df.userid.nunique()),
            "duplicate_user_ids": int(df.userid.duplicated().sum()),
            "missing_cells": int(df.isna().sum().sum()),
            "negative_rounds": int((df.sum_gamerounds < 0).sum()),
            "group_counts": {g: int((df.version == g).sum()) for g in GROUP_ORDER},
        },
    }

def stress_test(result: dict, practical_threshold_pp: float = 0.5, max_acceptable_loss_pp: float = 0.25,
                confidence_level: float = 0.95) -> dict:
    """Decision rule explorer; thresholds are user-selected policy, not statistical facts."""
    r = result["retention_7"]
    diff = r["difference_pp"]
    alpha = 1.0 - confidence_level
    g30 = next(g for g in result["groups"] if g["group"] == "gate_30")
    g40 = next(g for g in result["groups"] if g["group"] == "gate_40")
    lo_t, hi_t = _wilson(g40["retention_7_count"], g40["n"], alpha=alpha)
    lo_c, hi_c = _wilson(g30["retention_7_count"], g30["n"], alpha=alpha)
    p_t, p_c = g40["retention_7_rate"], g30["retention_7_rate"]
    lo = (p_t-p_c) - math.sqrt((p_t-lo_t)**2 + (hi_c-p_c)**2)
    hi = (p_t-p_c) + math.sqrt((hi_t-p_t)**2 + (p_c-lo_c)**2)
    lo, hi = lo*100, hi*100
    p = r["p_value"]
    meaningful_gain = diff >= practical_threshold_pp and lo > 0
    meaningful_harm = hi < -max_acceptable_loss_pp
    statistically_clear = p < alpha
    if meaningful_harm:
        decision = "HOLD"
        explanation = "The confidence interval is consistent with a loss larger than your tolerated downside."
    elif meaningful_gain:
        decision = "POTENTIAL SHIP"
        explanation = "The observed lift clears your practical threshold and the confidence interval is above zero. Check experiment health and guardrails."
    elif lo <= 0 <= hi:
        decision = "INCONCLUSIVE"
        explanation = "The interval includes no effect. The data does not establish a clear positive or negative effect at this confidence level."
    elif diff < 0:
        decision = "HOLD"
        explanation = "The observed effect is negative. Compare the estimated downside with your tolerance and verify experiment integrity."
    else:
        decision = "INVESTIGATE"
        explanation = "The effect is positive but does not clear your practical improvement threshold."
    return {
        "decision": decision, "explanation": explanation,
        "thresholds": {"practical_threshold_pp": float(practical_threshold_pp),
                       "max_acceptable_loss_pp": float(max_acceptable_loss_pp),
                       "confidence_level": float(confidence_level), "alpha": float(alpha)},
        "observed": {"difference_pp": float(diff), "ci_low_pp": float(lo), "ci_high_pp": float(hi),
                     "p_value": float(p), "statistically_clear": bool(statistically_clear)},
        "caution": "Decision thresholds are policy inputs. This tool does not infer revenue, player satisfaction, or causal mechanisms absent from the dataset."
    }

def build_decision_memo(result: dict, stress: dict | None = None) -> str:
    r = result["retention_7"]
    c = next(g for g in result["groups"] if g["group"] == "gate_30")
    t = next(g for g in result["groups"] if g["group"] == "gate_40")
    stress = stress or stress_test(result)
    return f"""# Cookie Cat — Experiment Decision Memo

## Decision
**{stress['decision']}** — {stress['explanation']}

## Evidence
- Players analyzed: {result['n_total']:,}
- Gate at level 30 Day-7 retention: {c['retention_7_rate']:.2%} ({c['retention_7_count']:,}/{c['n']:,})
- Gate at level 40 Day-7 retention: {t['retention_7_rate']:.2%} ({t['retention_7_count']:,}/{t['n']:,})
- Difference (gate_40 minus gate_30): {r['difference_pp']:+.2f} percentage points
- {stress['thresholds']['confidence_level']:.0%} Newcombe/Wilson-style interval: [{stress['observed']['ci_low_pp']:+.2f}, {stress['observed']['ci_high_pp']:+.2f}] percentage points
- Two-sided two-proportion z-test p-value: {r['p_value']:.6g}
- Holm-adjusted p-value across Day-1 and Day-7 retention tests: {r['holm_adjusted_p']:.6g}
- Sample-ratio mismatch diagnostic p-value (assuming 50/50 allocation): {result['experiment_health']['srm_p_value']:.6g}

## Decision policy used
- Minimum practically important lift: {stress['thresholds']['practical_threshold_pp']:.2f} pp
- Maximum tolerated loss: {stress['thresholds']['max_acceptable_loss_pp']:.2f} pp
- Confidence level: {stress['thresholds']['confidence_level']:.0%}

## Required follow-up
1. Confirm the intended randomization ratio and investigate assignment/logging if the SRM warning is active.
2. Review the pre-specified primary metric and guardrails before rollout.
3. If evidence remains inconclusive, design a follow-up experiment with a pre-registered minimum detectable effect and sample-size plan.

## Limitations
The dataset includes player ID, assigned gate, total game rounds, and Day-1/Day-7 retention indicators. It does not contain session-level journeys, revenue, satisfaction, or a measured churn reason. Do not infer those outcomes from this dataset.

---
Generated from the validated dataset by Cookie Cat. Decision thresholds are configurable policy choices, not scientific constants.
"""

def save_static_figures(result: dict, out_dir: str | Path) -> None:
    """Write lightweight publication-style Matplotlib figures for the report/notebook."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = Path(out_dir)
    groups = {g["group"]: g for g in result["groups"]}
    names = ["Gate 30", "Gate 40"]
    keys = ["gate_30", "gate_40"]
    rates = [groups[k]["retention_7_rate"] * 100 for k in keys]
    fig, ax = plt.subplots(figsize=(7.4, 4.4), constrained_layout=True)
    bars = ax.bar(names, rates, color=["#194b39", "#f6a45a"], width=.55)
    ax.set_ylabel("Day-7 retention (%)")
    ax.set_title("Cookie Cats · Day-7 retention by gate")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=.2)
    ax.set_axisbelow(True)
    ax.bar_label(bars, fmt="%.2f%%", padding=4)
    fig.savefig(out / "retention_comparison.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    r = result["retention_7"]
    fig, ax = plt.subplots(figsize=(7.4, 2.8), constrained_layout=True)
    ax.axvline(0, color="#718078", linestyle="--", linewidth=1.3)
    ax.errorbar(
        x=[r["difference_pp"]],
        y=[0],
        xerr=[[r["difference_pp"] - r["ci_low_pp"]], [r["ci_high_pp"] - r["difference_pp"]]],
        fmt="o", color="#194b39", ecolor="#194b39", capsize=6, markersize=7,
    )
    ax.set_yticks([])
    ax.set_xlabel("Gate 40 − Gate 30 (percentage points)")
    ax.set_title("Day-7 retention effect · 95% interval")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", alpha=.2)
    fig.savefig(out / "retention_effect_interval.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

def save_outputs(result: dict, out_dir: str | Path, stress: dict | None = None) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stress = stress or stress_test(result)
    (out / "analysis.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (out / "decision_memo.md").write_text(build_decision_memo(result, stress), encoding="utf-8")
    pd.DataFrame(result["groups"]).to_csv(out / "group_metrics.csv", index=False)
    save_static_figures(result, out)
