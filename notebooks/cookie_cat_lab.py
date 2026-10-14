import marimo

__generated_with = "0.14.0"
app = marimo.App(width="medium")

@app.cell
def _():
    import sys
    from pathlib import Path
    import pandas as pd
    import plotly.express as px
    import marimo as mo
    ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT))
    from src.cookie_cat import load_and_validate, analyze, stress_test
    return ROOT, analyze, load_and_validate, mo, pd, px, stress_test

@app.cell
def _(ROOT, load_and_validate, mo):
    data_path = ROOT / "data" / "raw" / "cookie_cats.csv"
    if not data_path.exists():
        mo.md("**Dataset not found.** From the project root, run `python run_all.py` once to download and validate it.")
        df = None
    else:
        df = load_and_validate(data_path)
        mo.md(f"## 🧪 Cookie Cat reactive experiment lab\\nValidated **{len(df):,}** player rows.")
    return (df,)

@app.cell
def _(df, mo):
    if df is None:
        mo.stop(True)
    confidence = mo.ui.slider(80, 99, value=95, label="Confidence level (%)")
    practical_lift = mo.ui.slider(0, 200, value=50, step=10, label="Minimum worthwhile lift (hundredths of a pp)")
    mo.vstack([confidence, practical_lift])
    return confidence, practical_lift

@app.cell
def _(analyze, confidence, df, mo, practical_lift, stress_test):
    result = analyze(df)
    decision = stress_test(
        result,
        practical_threshold_pp=practical_lift.value / 100,
        max_acceptable_loss_pp=0.25,
        confidence_level=confidence.value / 100,
    )
    mo.md(
        f"""### Experiment snapshot

        - Gate 30 Day-7 retention: **{result['retention_7']['gate_30']:.2%}**
        - Gate 40 Day-7 retention: **{result['retention_7']['gate_40']:.2%}**
        - Difference: **{result['retention_7']['difference_pp']:+.2f} pp**
        - Unadjusted p-value: **{result['retention_7']['p_value']:.4g}**
        - Decision under selected policy: **{decision['decision']}**

        {decision['explanation']}
        """
    )
    return decision, result

@app.cell
def _(df, mo, px):
    if df is None:
        mo.stop(True)
    chart_df = df.groupby("version", as_index=False).agg(
        players=("userid", "count"),
        day7_retention=("retention_7", "mean"),
        median_rounds=("sum_gamerounds", "median"),
    )
    fig = px.bar(chart_df, x="version", y="day7_retention", color="version",
                 title="Day-7 retention by gate", text=chart_df["day7_retention"].map(lambda x:f"{x:.2%}"))
    fig.update_layout(showlegend=False, yaxis_tickformat=".0%")
    mo.ui.plotly(fig)
    return (chart_df,)

if __name__ == "__main__":
    app.run()
