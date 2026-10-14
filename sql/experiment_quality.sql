-- Run only after checking the experiment's intended assignment ratio.
SELECT
    version AS gate_group,
    COUNT(*) AS assigned_players,
    COUNT(DISTINCT userid) AS unique_players,
    COUNT(*) - COUNT(DISTINCT userid) AS duplicate_ids,
    SUM(CASE WHEN sum_gamerounds < 0 THEN 1 ELSE 0 END) AS negative_rounds
FROM player_experiment
GROUP BY version
ORDER BY version;
