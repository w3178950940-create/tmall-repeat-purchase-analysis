-- 先执行本文件，再使用 Navicat 将 growth_strategy_mysql.csv 导入 growth_strategy 表。
USE tmall_analysis;

DROP TABLE IF EXISTS growth_strategy;

CREATE TABLE growth_strategy (
    user_id BIGINT NOT NULL,
    merchant_id BIGINT NOT NULL,
    repeat_purchase_score DOUBLE NOT NULL COMMENT '用于复购排序的得分，非严格校准概率',
    user_segment VARCHAR(32) NOT NULL,
    recommended_action VARCHAR(128) NOT NULL,
    merchant_cart_cnt INT NOT NULL,
    merchant_buy_cnt INT NOT NULL,
    merchant_favorite_cnt INT NOT NULL,
    PRIMARY KEY (user_id, merchant_id),
    INDEX idx_segment (user_segment),
    INDEX idx_score (repeat_purchase_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
