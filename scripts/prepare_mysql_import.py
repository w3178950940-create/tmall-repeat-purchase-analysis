"""Prepare a clean English-column CSV for importing this project into MySQL."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = PROJECT_DIR.parent
TRAIN_PATH = WORKSPACE_DIR / "data_format1" / "train_format1.csv"
FEATURE_PATH = PROJECT_DIR / "cache" / "pair_features.csv"
EXPORT_PATH = PROJECT_DIR / "data" / "mysql_import" / "analysis_base_mysql.csv"

COLUMN_RENAME = {
    "user_浏览_次数": "user_browse_cnt",
    "商家_浏览_次数": "merchant_browse_cnt",
    "user_加购_次数": "user_cart_cnt",
    "商家_加购_次数": "merchant_cart_cnt",
    "user_购买_次数": "user_buy_cnt",
    "商家_购买_次数": "merchant_buy_cnt",
    "user_收藏_次数": "user_favorite_cnt",
    "商家_收藏_次数": "merchant_favorite_cnt",
    "用户总行为次数": "user_total_actions",
    "该商家总行为次数": "merchant_total_actions",
    "用户最近活跃时间": "user_last_active",
    "该商家最近互动时间": "merchant_last_interaction",
    "用户活跃间隔": "user_active_gap",
    "商家互动间隔": "merchant_interaction_gap",
    "商家行为占比": "merchant_action_share",
    "商家购买占比": "merchant_purchase_share",
    "用户购买占比": "user_purchase_share",
    "加购后购买率": "cart_to_purchase_rate",
}


def main() -> None:
    if not FEATURE_PATH.exists():
        raise FileNotFoundError("未找到特征文件，请先运行完整项目管道。")

    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    print("读取训练集与特征缓存，准备 MySQL 导入文件…")
    train = pd.read_csv(TRAIN_PATH)
    features = pd.read_csv(FEATURE_PATH)
    analysis_base = train.merge(features, on=["user_id", "merchant_id"], how="left")
    analysis_base = analysis_base.rename(columns=COLUMN_RENAME)

    # MySQL import is more reliable when integer fields contain no floating-point .0.
    integer_columns = [
        "user_id", "merchant_id", "label", "user_browse_cnt", "merchant_browse_cnt",
        "user_cart_cnt", "merchant_cart_cnt", "user_buy_cnt", "merchant_buy_cnt",
        "user_favorite_cnt", "merchant_favorite_cnt", "user_total_actions",
        "merchant_total_actions", "user_last_active", "merchant_last_interaction",
        "user_active_gap", "merchant_interaction_gap", "age_range", "gender",
    ]
    for column in integer_columns:
        analysis_base[column] = analysis_base[column].fillna(-1).astype("int64")

    analysis_base.to_csv(EXPORT_PATH, index=False, encoding="utf-8-sig")
    print(f"导出完成：{EXPORT_PATH}")
    print(f"行数：{len(analysis_base):,}；列数：{len(analysis_base.columns)}")
    print("字段：", ", ".join(analysis_base.columns))


if __name__ == "__main__":
    main()
