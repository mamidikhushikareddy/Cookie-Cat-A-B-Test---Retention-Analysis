-- name: group_retention
SELECT version, COUNT(*) AS n, SUM(retention_1::INT) AS r1, SUM(retention_7::INT) AS r7,
       AVG(retention_1::INT) AS r1_rate, AVG(retention_7::INT) AS r7_rate
FROM players GROUP BY version ORDER BY version;
-- name: duplicate_ids
SELECT COUNT(*) - COUNT(DISTINCT userid) AS duplicate_ids FROM players;
-- name: missing_values
SELECT COUNT(*) FILTER (WHERE userid IS NULL) AS userid_null, COUNT(*) FILTER (WHERE version IS NULL) AS version_null,
       COUNT(*) FILTER (WHERE sum_gamerounds IS NULL) AS rounds_null FROM players;
-- name: rounds_distribution
SELECT version, MIN(sum_gamerounds) AS min, quantile_cont(sum_gamerounds, 0.5) AS median,
       quantile_cont(sum_gamerounds, 0.99) AS p99, MAX(sum_gamerounds) AS max FROM players GROUP BY version ORDER BY version;
-- name: retention_by_engagement_band
SELECT CASE WHEN sum_gamerounds = 0 THEN '0' WHEN sum_gamerounds < 10 THEN '1-9'
            WHEN sum_gamerounds < 50 THEN '10-49' ELSE '50+' END AS band,
       version, COUNT(*) AS n, AVG(retention_7::INT) AS r7_rate
FROM players GROUP BY band, version ORDER BY band, version;
