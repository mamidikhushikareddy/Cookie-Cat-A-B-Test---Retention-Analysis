# Cookie Cat methodology

## Research question
Did Day-7 retention differ between players assigned to the level-30 gate and players assigned to the level-40 gate?

## Primary estimand
The observed absolute difference in Day-7 retention:
`retention_7(gate_40) - retention_7(gate_30)`, expressed in percentage points.

## Statistical methods
- Two-sided two-proportion z-test for Day-7 retention.
- Wilson intervals for each proportion, combined into a Newcombe-style interval for the difference.
- Holm correction across Day-1 and Day-7 retention tests, reported separately from the unadjusted Day-7 p-value.
- Sample-ratio mismatch diagnostic against a 50/50 allocation assumption. Confirm the intended assignment ratio before treating this as a defect.
- Mann–Whitney test for the skewed game-round distribution.
- Sample-size planning approximation for a 1 percentage-point minimum detectable effect, 80% power, and alpha 0.05.

## Decision stress test
Users set practical-lift and tolerated-loss thresholds. The rule returns a transparent recommendation. These thresholds are policy choices, not statistical truths. The stress test recalculates the Newcombe-style interval for the selected confidence level and applies the corresponding alpha threshold to the p-value.

## Data limits
The source data has one record per player and includes assignment, total game rounds, and Day-1 / Day-7 retention. It has no session event sequence, revenue, satisfaction, acquisition channel, or explicit churn reason. Consequently, Cookie Cat does not claim to measure funnel conversion, lifetime value, monetization impact, or causal churn mechanisms.

## Reproducing the resume claim
The resume values (90,189 players, 19.02% versus 18.20%, p=0.0016) are acceptance criteria to verify against the exact public data and test implementation. The software computes metrics from the downloaded CSV and does not hardcode those results. If a calculated value differs, inspect the source file, group labels, test choice, and rounding rather than forcing the output to match.
