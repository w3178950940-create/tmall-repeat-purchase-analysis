USE tmall_analysis;

-- 1. 项目总览：COUNT 计数，SUM 求复购人数，AVG(label) 即复购率。
SELECT
    COUNT(*) AS sample_count,
    SUM(label) AS repeat_purchase_count,
    ROUND(AVG(label) * 100, 2) AS repeat_purchase_rate_pct,
    COUNT(DISTINCT user_id) AS user_count,
    COUNT(DISTINCT merchant_id) AS merchant_count
FROM analysis_base;

-- 2. 行为分层：CASE WHEN 创建业务标签，GROUP BY 分组统计。
SELECT
    CASE
        WHEN merchant_cart_cnt > 0 THEN '有加购行为'
        WHEN merchant_buy_cnt > 0 THEN '有购买历史'
        WHEN merchant_favorite_cnt > 0 THEN '有收藏行为'
        ELSE '仅浏览或无互动'
    END AS behavior_segment,
    COUNT(*) AS sample_count,
    SUM(label) AS repeat_purchase_count,
    ROUND(AVG(label) * 100, 2) AS repeat_purchase_rate_pct
FROM analysis_base
GROUP BY behavior_segment
ORDER BY repeat_purchase_rate_pct DESC;

-- 3. 数据质量：同一个用户—商家在训练集中应只有一条样本。
SELECT
    COUNT(*) AS duplicated_pair_count
FROM (
    SELECT user_id, merchant_id
    FROM analysis_base
    GROUP BY user_id, merchant_id
    HAVING COUNT(*) > 1
) AS duplicated_pairs;

-- 4. 商家维度：只看样本量不少于 100 的商家，避免小样本偶然波动。
SELECT
    merchant_id,
    COUNT(*) AS sample_count,
    ROUND(AVG(label) * 100, 2) AS repeat_purchase_rate_pct,
    ROUND(AVG(merchant_total_actions), 2) AS avg_merchant_actions
FROM analysis_base
GROUP BY merchant_id
HAVING COUNT(*) >= 100
ORDER BY repeat_purchase_rate_pct DESC, sample_count DESC
LIMIT 15;
