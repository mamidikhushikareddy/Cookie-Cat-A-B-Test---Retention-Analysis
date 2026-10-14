import pandas as pd
import numpy as np
import pytest
from src.cookie_cat import load_and_validate, analyze, stress_test, build_decision_memo

def fixture_df(n=2000):
    rng = np.random.default_rng(7)
    versions = np.array(["gate_30"]*(n//2) + ["gate_40"]*(n-n//2))
    rng.shuffle(versions)
    p7 = np.where(versions=="gate_30", .20, .18)
    p1 = np.where(versions=="gate_30", .45, .44)
    return pd.DataFrame({
        "userid": np.arange(n),
        "version": versions,
        "sum_gamerounds": rng.poisson(8, n),
        "retention_1": rng.random(n) < p1,
        "retention_7": rng.random(n) < p7,
    })

def test_analysis_uses_all_rows_and_returns_expected_keys():
    df = fixture_df()
    result = analyze(df)
    assert result["n_total"] == 2000
    assert result["data_quality"]["unique_users"] == 2000
    assert set(result["retention_7"]) >= {"p_value","difference_pp","ci_low_pp","ci_high_pp"}
    assert result["retention_7"]["difference_pp"] < 0

def test_stress_test_has_a_decision_and_caveat():
    result = analyze(fixture_df())
    scenario = stress_test(result, practical_threshold_pp=.5, max_acceptable_loss_pp=.25, confidence_level=.95)
    assert scenario["decision"] in {"HOLD","POTENTIAL SHIP","INCONCLUSIVE","INVESTIGATE"}
    assert "does not infer revenue" in scenario["caution"]

def test_memo_contains_limitations():
    memo = build_decision_memo(analyze(fixture_df()))
    assert "Limitations" in memo
    assert "Players analyzed: 2,000" in memo

def test_load_rejects_duplicate_ids(tmp_path):
    df = fixture_df(20)
    df.loc[1, "userid"] = df.loc[0, "userid"]
    path = tmp_path / "bad.csv"
    df.to_csv(path,index=False)
    with pytest.raises(ValueError, match="unique"):
        load_and_validate(path)

def test_load_rejects_negative_rounds(tmp_path):
    df = fixture_df(20)
    df.loc[0,"sum_gamerounds"] = -1
    path = tmp_path / "bad.csv"
    df.to_csv(path,index=False)
    with pytest.raises(ValueError, match="non-negative"):
        load_and_validate(path)

def test_holm_adjusted_p_is_not_below_raw_p():
    result = analyze(fixture_df())
    assert result["retention_7"]["holm_adjusted_p"] >= result["retention_7"]["p_value"]


def test_stress_test_recalculates_interval_for_confidence_level():
    result = analyze(fixture_df())
    interval_80 = stress_test(result, confidence_level=.80)["observed"]
    interval_99 = stress_test(result, confidence_level=.99)["observed"]
    assert interval_99["ci_low_pp"] <= interval_80["ci_low_pp"]
    assert interval_99["ci_high_pp"] >= interval_80["ci_high_pp"]

def test_save_outputs_writes_reports_and_figures(tmp_path):
    from src.cookie_cat import save_outputs
    result = analyze(fixture_df())
    save_outputs(result, tmp_path)
    for name in ["analysis.json", "decision_memo.md", "group_metrics.csv",
                 "retention_comparison.png", "retention_effect_interval.png"]:
        assert (tmp_path / name).exists()
        assert (tmp_path / name).stat().st_size > 0


def test_tooling_artifacts_exist():
    from pathlib import Path
    project_root = Path(__file__).resolve().parents[1]
    assert (project_root / ".github" / "workflows" / "tests.yml").exists()
    assert (project_root / "sql" / "retention_by_gate.sql").exists()
    assert (project_root / "notebooks" / "cookie_cat_lab.py").exists()
    assert "Quest Arcade" in (project_root / "app.py").read_text(encoding="utf-8")
