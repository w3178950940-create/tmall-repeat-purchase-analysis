-- 在 Navicat 连接到 MySQL 后执行本文件。
CREATE DATABASE IF NOT EXISTS tmall_analysis
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE tmall_analysis;

DROP TABLE IF EXISTS analysis_base;

CREATE TABLE analysis_base (
    user_id BIGINT NOT NULL,
    merchant_id BIGINT NOT NULL,
    label TINYINT NOT NULL COMMENT '1=复购，0=未复购',
    user_browse_cnt INT NOT NULL,
    merchant_browse_cnt INT NOT NULL,
    user_cart_cnt INT NOT NULL,
    merchant_cart_cnt INT NOT NULL,
    user_buy_cnt INT NOT NULL,
    merchant_buy_cnt INT NOT NULL,
    user_favorite_cnt INT NOT NULL,
    merchant_favorite_cnt INT NOT NULL,
    user_total_actions INT NOT NULL,
    merchant_total_actions INT NOT NULL,
    user_last_active INT NOT NULL,
    merchant_last_interaction INT NOT NULL,
    user_active_gap INT NOT NULL,
    merchant_interaction_gap INT NOT NULL,
    merchant_action_share DOUBLE NOT NULL,
    merchant_purchase_share DOUBLE NOT NULL,
    user_purchase_share DOUBLE NOT NULL,
    cart_to_purchase_rate DOUBLE NOT NULL,
    age_range INT NOT NULL,
    gender INT NOT NULL,
    PRIMARY KEY (user_id, merchant_id),
    INDEX idx_merchant_id (merchant_id),
    INDEX idx_label (label)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
