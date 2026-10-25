-- Q: How long does a fix take today, by channel? Median and 90th percentile hours, and the unresolved share.
SELECT channel,
       COUNT(*)                                                                                         AS issues,
       ROUND((percentile_cont(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600))::numeric, 1) AS median_hours,
       ROUND((percentile_cont(0.9) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (resolved_at - created_at)) / 3600))::numeric, 1) AS p90_hours,
       ROUND(100.0 * AVG(CASE WHEN resolved_at IS NULL THEN 1 ELSE 0 END), 1)                           AS pct_unresolved
FROM issues
GROUP BY channel
ORDER BY issues DESC;
