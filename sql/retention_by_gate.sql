-- Day-1 / Day-7 retention and engagement by assigned gate.
SELECT
    version AS gate_group,
    COUNT(*) AS players,
    AVG(CAST(retention_1 AS INTEGER)) AS day1_retention,
    AVG(CAST(retention_7 AS INTEGER)) AS day7_retention,
    AVG(sum_gamerounds) AS mean_game_rounds,
    MEDIAN(sum_gamerounds) AS median_game_rounds
FROM player_experiment
GROUP BY version
ORDER BY version;
