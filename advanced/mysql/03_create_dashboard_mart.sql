-- 基于原始分析表和策略表，建立 Power BI 可直接读取的业务数据集市（视图）。
USE tmall_analysis;

DROP TABLE IF EXISTS model_evaluation;
CREATE TABLE model_evaluation (
    model_name VARCHAR(64) PRIMARY KEY,
    roc_auc DOUBLE NOT NULL,
    pr_auc DOUBLE NOT NULL,
    top20_precision DOUBLE NOT NULL,
    top20_recall DOUBLE NOT NULL,
    top20_lift DOUBLE NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO model_evaluation VALUES
('逻辑回归（最终模型）', 0.6126953904, 0.1032919562, 0.1060954572, 0.3470219436, 1.7352094942),
('随机森林（对比模型）', 0.5813081271, 0.0895603328, 0.0946904351, 0.3097178683, 1.5486783923);

CREATE OR REPLACE VIEW v_behavior_repurchase AS
SELECT
    CASE
        WHEN merchant_cart_cnt > 0 THEN '有加购行为'
        WHEN merchant_buy_cnt > 0 THEN '有购买历史'
        WHEN merchant_favorite_cnt > 0 THEN '有收藏行为'
        ELSE '仅浏览或无互动'
    END AS behavior_segment,
    COUNT(*) AS sample_count,
    SUM(label) AS repeat_purchase_count,
    AVG(label) AS repeat_purchase_rate
FROM analysis_base
GROUP BY behavior_segment;

CREATE OR REPLACE VIEW v_demographic_repurchase AS
SELECT
    CASE WHEN age_range = -1 THEN '未知年龄' ELSE CAST(age_range AS CHAR) END AS age_group,
    CASE WHEN gender = 0 THEN '女性' WHEN gender = 1 THEN '男性' ELSE '未知性别' END AS gender_group,
    COUNT(*) AS sample_count,
    SUM(label) AS repeat_purchase_count,
    AVG(label) AS repeat_purchase_rate
FROM analysis_base
GROUP BY age_group, gender_group
HAVING COUNT(*) >= 100;

CREATE OR REPLACE VIEW v_merchant_repurchase AS
SELECT
    merchant_id,
    COUNT(*) AS sample_count,
    AVG(label) AS repeat_purchase_rate,
    AVG(merchant_total_actions) AS avg_merchant_actions
FROM analysis_base
GROUP BY merchant_id
HAVING COUNT(*) >= 100;

CREATE OR REPLACE VIEW v_growth_segment AS
SELECT
    user_segment,
    recommended_action,
    COUNT(*) AS user_count,
    AVG(repeat_purchase_score) AS avg_repeat_purchase_score
FROM growth_strategy
GROUP BY user_segment, recommended_action;
