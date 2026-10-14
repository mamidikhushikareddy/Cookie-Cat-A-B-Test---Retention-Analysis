"""Deterministic statistics. Effect = gate_40 - gate_30 (percentage points)."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd
from scipy import stats as st

CONTROL, TREATMENT = "gate_30", "gate_40"


def wilson(x: int, n: int, conf: float = 0.95) -> tuple[float, float]:
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 <= x <= n:
        raise ValueError("successes must be within [0, n]")
    z = st.norm.ppf(1 - (1 - conf) / 2)
    p = x / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def newcombe_diff(x_t: int, n_t: int, x_c: int, n_c: int, conf: float = 0.95) -> tuple[float, float]:
    """Newcombe (1998) method 10: hybrid score interval for p_t - p_c."""
    p_t, p_c = x_t / n_t, x_c / n_c
    lt, ut = wilson(x_t, n_t, conf)
    lc, uc = wilson(x_c, n_c, conf)
    d = p_t - p_c
    lo = d - math.sqrt((p_t - lt) ** 2 + (uc - p_c) ** 2)
    hi = d + math.sqrt((ut - p_t) ** 2 + (p_c - lc) ** 2)
    return lo, hi


def wald_diff(x_t, n_t, x_c, n_c, conf=0.95):
    p_t, p_c = x_t / n_t, x_c / n_c
    se = math.sqrt(p_t * (1 - p_t) / n_t + p_c * (1 - p_c) / n_c)
    z = st.norm.ppf(1 - (1 - conf) / 2)
    d = p_t - p_c
    return d - z * se, d + z * se


def two_prop_ztest(x_t: int, n_t: int, x_c: int, n_c: int) -> dict:
    """Two-sided pooled two-proportion z-test. H0: p_t == p_c."""
    if min(n_t, n_c) <= 0:
        raise ValueError("group sizes must be positive")
    pooled = (x_t + x_c) / (n_t + n_c)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n_t + 1 / n_c))
    if se == 0:  # all events or no events in both arms: no evidence of difference
        return {"pooled": pooled, "se": 0.0, "z": 0.0, "p_value": 1.0}
    z = (x_t / n_t - x_c / n_c) / se
    return {"pooled": pooled, "se": se, "z": z, "p_value": float(2 * st.norm.sf(abs(z)))}


def holm(pvals: dict[str, float]) -> dict[str, float]:
    """Holm step-down adjustment over the stated family."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, out, running = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[k] = running
    return out


def retention_effect(df: pd.DataFrame, outcome: str, conf: float = 0.95) -> dict:
    g = {k: df[df["version"] == k] for k in (CONTROL, TREATMENT)}
    n_c, n_t = len(g[CONTROL]), len(g[TREATMENT])
    x_c, x_t = int(g[CONTROL][outcome].sum()), int(g[TREATMENT][outcome].sum())
    p_c, p_t = x_c / n_c, x_t / n_t
    test = two_prop_ztest(x_t, n_t, x_c, n_c)
    nlo, nhi = newcombe_diff(x_t, n_t, x_c, n_c, conf)
    wlo, whi = wald_diff(x_t, n_t, x_c, n_c, conf)
    return {
        "outcome": outcome, "control": CONTROL, "treatment": TREATMENT, "confidence": conf,
        "n_control": n_c, "n_treatment": n_t, "retained_control": x_c, "retained_treatment": x_t,
        "rate_control": p_c, "rate_treatment": p_t,
        "diff_pp": (p_t - p_c) * 100,
        "relative_change_pct": ((p_t - p_c) / p_c * 100) if p_c > 0 else None,  # denominator: control rate
        "ci_newcombe_pp": [nlo * 100, nhi * 100],
        "ci_wald_pp": [wlo * 100, whi * 100],
        "z": test["z"], "p_value": test["p_value"], "pooled": test["pooled"],
        "method": "pooled two-proportion z-test (two-sided); Newcombe-Wilson hybrid score CI (primary), Wald CI (reference)",
        "null": "p_gate40 = p_gate30", "alternative": "p_gate40 != p_gate30",
    }


def srm(observed: dict[str, int], expected_alloc: dict[str, float], alpha: float = 0.05) -> dict:
    """Chi-square goodness-of-fit for sample ratio mismatch. A warning, never proof of failed randomisation."""
    if set(observed) != set(expected_alloc):
        raise ValueError("observed and expected groups must match")
    if any(v < 0 for v in expected_alloc.values()) or abs(sum(expected_alloc.values()) - 1) > 1e-9:
        raise ValueError("expected allocation must be non-negative and sum to 1")
    if any(v == 0 for v in expected_alloc.values()):
        raise ValueError("expected proportions must be > 0")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0,1)")
    total = sum(observed.values())
    exp = {k: total * expected_alloc[k] for k in observed}
    chi2 = sum((observed[k] - exp[k]) ** 2 / exp[k] for k in observed)
    dof = len(observed) - 1
    p = float(st.chi2.sf(chi2, dof))
    return {
        "observed": observed, "observed_prop": {k: v / total for k, v in observed.items()},
        "expected_alloc": expected_alloc, "expected_counts": exp, "chi2": chi2, "dof": dof,
        "p_value": p, "alpha": alpha, "warning": p < alpha,
        "interpretation": ("Observed split is inconsistent with the assumed allocation at the chosen threshold. "
                           "This is a warning: it does not identify a cause. Confirm the planned allocation and "
                           "inspect assignment/logging pipelines." if p < alpha else
                           "No evidence against the assumed allocation at this threshold."),
        "limitations": "Result is conditional on the assumed allocation, which is not in the dataset.",
    }


def engagement(df: pd.DataFrame) -> dict:
    a = df.loc[df.version == CONTROL, "sum_gamerounds"]
    b = df.loc[df.version == TREATMENT, "sum_gamerounds"]
    u = st.mannwhitneyu(b, a, alternative="two-sided", method="asymptotic")
    return {"mann_whitney_u": float(u.statistic), "p_value": float(u.pvalue),
            "prob_superiority_treatment": float(u.statistic / (len(a) * len(b))),
            "median_control": float(a.median()), "median_treatment": float(b.median()),
            "mean_control": float(a.mean()), "mean_treatment": float(b.mean()),
            "note": "Tests stochastic ordering of the distributions, not a difference in medians. Ties handled by mid-ranks."}
