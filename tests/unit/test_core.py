import math
import numpy as np, pandas as pd, pytest
from cookie_cat import stats, decision, evidence, contract, data, sqlchecks

def frame(n_c, x_c, n_t, x_t):
    rows = ([("gate_30", i < x_c) for i in range(n_c)] + [("gate_40", i < x_t) for i in range(n_t)])
    return pd.DataFrame({"userid": range(len(rows)), "version": [r[0] for r in rows], "sum_gamerounds": 5,
                         "retention_1": [r[1] for r in rows], "retention_7": [r[1] for r in rows]})

def test_counts_and_sign():
    e = stats.retention_effect(frame(100, 20, 100, 10), "retention_7")
    assert (e["retained_control"], e["retained_treatment"]) == (20, 10)
    assert e["diff_pp"] == pytest.approx(-10.0)
    assert e["relative_change_pct"] == pytest.approx(-50.0)

def test_identical_proportions():
    e = stats.retention_effect(frame(200, 40, 200, 40), "retention_7")
    assert e["diff_pp"] == 0 and e["p_value"] == pytest.approx(1.0)
    lo, hi = e["ci_newcombe_pp"]; assert lo < 0 < hi

def test_zero_and_all_events_do_not_crash():
    assert stats.two_prop_ztest(0, 50, 0, 50)["p_value"] == 1.0
    assert stats.two_prop_ztest(50, 50, 50, 50)["p_value"] == 1.0
    lo, hi = stats.newcombe_diff(0, 30, 0, 30); assert lo < 0 < hi
    assert stats.wilson(0, 10)[0] == pytest.approx(0, abs=1e-12) and stats.wilson(10, 10)[1] == pytest.approx(1, abs=1e-12)

def test_wilson_validates():
    with pytest.raises(ValueError): stats.wilson(5, 0)
    with pytest.raises(ValueError): stats.wilson(11, 10)

def test_relative_change_zero_control_guard():
    assert stats.retention_effect(frame(50, 0, 50, 5), "retention_7")["relative_change_pct"] is None

def test_newcombe_matches_statsmodels():
    from statsmodels.stats.proportion import confint_proportions_2indep
    for xt, nt, xc, nc in [(10, 56, 1, 29), (8279, 45489, 8502, 44700), (3, 40, 12, 40)]:
        lo, hi = stats.newcombe_diff(xt, nt, xc, nc)
        slo, shi = confint_proportions_2indep(xt, nt, xc, nc, method="newcomb", compare="diff")
        assert lo == pytest.approx(slo, abs=1e-9) and hi == pytest.approx(shi, abs=1e-9)

def test_holm_known():
    adj = stats.holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adj["a"] == pytest.approx(0.03) and adj["c"] == pytest.approx(0.06) and adj["b"] == pytest.approx(0.06)

def test_srm_equal_and_unequal():
    eq = stats.srm({"a": 500, "b": 500}, {"a": .5, "b": .5}); assert eq["chi2"] == 0 and not eq["warning"]
    uneq = stats.srm({"a": 800, "b": 200}, {"a": .8, "b": .2}); assert uneq["chi2"] == pytest.approx(0)
    assert stats.srm({"a": 600, "b": 400}, {"a": .5, "b": .5})["warning"]
    with pytest.raises(ValueError): stats.srm({"a": 1, "b": 1}, {"a": .6, "b": .6})

def test_decision_boundaries_and_invariants():
    e = stats.retention_effect(frame(20000, 4000, 20000, 3800), "retention_7")
    base = decision.decide(e, False, decision.Policy())
    assert base["action"] == decision.REJECT
    held = decision.decide(e, True, decision.Policy())
    assert held["action"] == decision.HOLD
    lenient = decision.decide(e, False, decision.Policy(max_loss_pp=5))
    assert lenient["action"] == decision.HOLD
    assert base["invariants"] == held["invariants"] == lenient["invariants"]
    with pytest.raises(ValueError): decision.Policy(-1, 0.5).validate()

def test_ship_requires_ci_above_threshold():
    e = stats.retention_effect(frame(20000, 3800, 20000, 4200), "retention_7")
    assert decision.decide(e, False, decision.Policy(min_improvement_pp=0.5))["action"] == decision.SHIP
    assert decision.decide(e, False, decision.Policy(min_improvement_pp=3))["action"] == decision.HOLD

def test_stability_map_is_deterministic_and_bounded():
    e = stats.retention_effect(frame(1000, 200, 1000, 180), "retention_7")
    a = decision.stability_map(e, True, [0, 1], [0, 1]); b = decision.stability_map(e, True, [0, 1], [0, 1])
    assert a == b
    with pytest.raises(ValueError): decision.stability_map(e, True, range(60), range(60))

def test_graph_branch_local_invalidation():
    g = evidence.build_cookie_cat_graph("abc", True)
    hit = g.invalidate("srm_assumption")
    assert {"srm", "rec"} <= hit
    assert g.nodes["effect7"].status == "current" and g.nodes["viz_style"].status == "current"
    g2 = evidence.build_cookie_cat_graph("abc", True)
    assert {"policy", "rec"} == g2.invalidate("policy")
    assert g2.nodes["effect7"].status == "current" and g2.nodes["srm"].status == "current"
    g3 = evidence.build_cookie_cat_graph("abc", True)
    hit3 = g3.invalidate("groups")
    assert {"groups", "ret7", "effect7", "srm", "rec"} <= hit3 and "policy" not in hit3 and "dataset" not in hit3

def test_graph_rejects_cycles_and_missing():
    g = evidence.EvidenceGraph()
    for i in "ab": g.add_node(evidence.Node(i, "metric", i))
    g.add_edge("a", "b", "DEPENDS_ON")
    with pytest.raises(ValueError): g.add_edge("b", "a", "DEPENDS_ON")
    with pytest.raises(KeyError): g.add_edge("a", "zz", "DEPENDS_ON")

def test_contract_flags_problems():
    df = frame(10, 2, 10, 2); df.loc[0, "version"] = "gate_99"; df.loc[1, "userid"] = df.loc[2, "userid"]
    df.loc[3, "sum_gamerounds"] = -1
    a = contract.audit(df)
    failed = {r["rule_id"] for r in a["rules"] if r["status"] == "fail"}
    assert {"C004", "C005", "C008"} <= failed and a["blocked"]
    with pytest.raises(ValueError): contract.to_analysis_frame(df)
    assert contract.audit(pd.DataFrame())["blocked"]

def test_duckdb_agrees_with_pandas():
    assert sqlchecks.crosscheck(frame(60, 10, 40, 9))["status"] == "AGREE"

def test_unapproved_dataset_refused():
    with pytest.raises(data.DatasetNotApproved): data.resolve("../../etc/passwd")
