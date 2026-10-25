-- Q: How many installs are lost to "not serviceable", and where? Funnel by pincode.
WITH steps AS (
  SELECT customer_id,
         MAX(pincode)                                                                     AS pincode,
         BOOL_OR(event_name = 'install')                                                  AS installed,
         BOOL_OR(event_name = 'otp_verified')                                             AS verified,
         BOOL_OR(event_name = 'serviceability_result' AND is_serviceable)                 AS serviceable,
         BOOL_OR(event_name = 'serviceability_result' AND NOT is_serviceable)             AS unserviceable,
         BOOL_OR(event_name = 'first_order')                                              AS ordered
  FROM app_events
  GROUP BY customer_id
)
SELECT pincode,
       COUNT(*) FILTER (WHERE installed)                                                  AS installs,
       COUNT(*) FILTER (WHERE verified)                                                   AS otp_verified,
       COUNT(*) FILTER (WHERE unserviceable)                                              AS hit_unserviceable,
       ROUND(100.0 * COUNT(*) FILTER (WHERE unserviceable AND verified) / NULLIF(COUNT(*) FILTER (WHERE verified), 0), 1) AS pct_verified_then_unserviceable,
       ROUND(100.0 * COUNT(*) FILTER (WHERE ordered) / NULLIF(COUNT(*) FILTER (WHERE installed), 0), 1) AS pct_install_to_first_order
FROM steps
GROUP BY pincode
HAVING COUNT(*) FILTER (WHERE installed) >= 50
ORDER BY hit_unserviceable DESC
LIMIT 25;
