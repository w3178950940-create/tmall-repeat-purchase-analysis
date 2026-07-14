-- 本文件是 advanced/01_sql_business_analysis.py 中 SQL 的可阅读版本。
-- Python 会先把 train_format1.csv 与 pair_features.csv 合并后写入 analysis_base 表。

-- 1. 项目总览：样本量、复购率、用户数、商家数
SELECT
    COUNT(*) AS sample_count,
    SUM(label) AS repeat_purchase_count,
    ROUND(AVG(label) * 100, 2) AS repeat_purchase_rate_pct,
    COUNT(DISTINCT user_id) AS user_count,
    COUNT(DISTINCT merchant_id) AS merchant_count
FROM analysis_base;

-- 2. 根据用户在该商家的行为，观察不同人群的复购率
WITH segmented AS (
    SELECT
        label,
        CASE
            WHEN "商家_加购_次数" > 0 THEN '有加购行为'
            WHEN "商家_购买_次数" > 0 THEN '有购买历史'
            WHEN "商家_收藏_次数" > 0 THEN '有收藏行为'
            ELSE '仅浏览或无互动'
        END AS behavior_segment
    FROM analysis_base
)
SELECT
    behavior_segment,
    COUNT(*) AS sample_count,
    SUM(label) AS repeat_purchase_count,
    ROUND(AVG(label) * 100, 2) AS repeat_purchase_rate_pct
FROM segmented
GROUP BY behavior_segment
ORDER BY repeat_purchase_rate_pct DESC;

-- 3. 数据质量：检查同一用户—商家是否有重复训练样本
SELECT COUNT(*) AS duplicated_pair_count
FROM (
    SELECT user_id, merchant_id
    FROM analysis_base
    GROUP BY user_id, merchant_id
    HAVING COUNT(*) > 1
);
