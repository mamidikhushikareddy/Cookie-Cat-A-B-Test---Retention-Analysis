# Cookie Cat — Cookie Cats A/B Test Retention Analysis

## The pain point
Product teams can over-rely on a single p-value when deciding whether to ship an experiment. Statistical significance does not by itself determine practical importance, validate experiment assignment, or settle a product decision.

## What Cookie Cat does
Cookie Cat reproduces the classic Cookie Cats level-gate A/B test and adds an interactive decision stress test. A user can adjust the minimum worthwhile lift and acceptable downside, inspect the observed effect and uncertainty, review experiment-health diagnostics, and export a decision memo.

## Original resume claim to reproduce
“Conducted an A/B test on Cookie Cats' level-gate placement, analyzing 7-day retention across 90,189 players; found significantly lower retention with the level-40 gate (19.02% vs. 18.20%, p=0.0016) and recommended holding the rollout.”

These numbers are not hardcoded as analysis results. The actual dataset run must verify them before describing them as reproduced.

## What is distinct
The project's contribution is not a new statistical test or a new dataset. It is a transparent, configurable decision-policy layer that demonstrates how product thresholds interact with effect estimates and uncertainty.

## How to run
1. Create/activate a Python environment.
2. Install `requirements.txt`.
3. Run `python run_all.py` to download, validate, and analyze the dataset.
4. Run `pytest -q`.
5. Run `streamlit run app.py`.

## Evidence to include in the final portfolio
- Screenshot of the decision room.
- Screenshot showing different decisions under different policy thresholds.
- Test results.
- Actual calculated metrics from the downloaded dataset.
- An exported decision memo.
- A limitations section explaining what the dataset cannot establish.
