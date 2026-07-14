"""Advanced module 1: use real SQL to perform business diagnostics.

This script loads the training labels and the cached user-merchant features into
an in-memory SQLite database. It then runs reusable SQL queries and writes the
results and a chart to advanced/outputs.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = PROJECT_DIR.parent
CACHE_PATH = PROJECT_DIR / "cache" / "pair_features.csv"
TRAIN_PATH = WORKSPACE_DIR / "data_format1" / "train_format1.csv"
OUTPUT_DIR = PROJECT_DIR / "advanced" / "outputs"
DATABASE_PATH = PROJECT_DIR / "advanced" / "database" / "tmall_analysis.sqlite"


def run_query(connection: sqlite3.Connection, name: str, sql: str) -> pd.DataFrame:
    """Run one SQL query, save its result, and return it for further analysis."""
    result = pd.read_sql_query(sql, connection)
    result.to_csv(OUTPUT_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
    print(f"\n[{name}]")
    print(result.to_string(index=False))
    return result


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CACHE_PATH.exists():
        raise FileNotFoundError(
            "未找到特征缓存。请先运行：python tmall_repurchase_project\\src\\run_pipeline.py"
        )

    print("加载训练标签与已构建的用户—商家特征…")
    train = pd.read_csv(TRAIN_PATH)
    features = pd.read_csv(CACHE_PATH)

    # Only keep training pairs. The cache also contains test pairs, which have no label.
    analysis_base = train.merge(features, on=["user_id", "merchant_id"], how="left")
    print(f"训练样本：{len(analysis_base):,}；分析字段：{len(analysis_base.columns)}")

    # SQLite is included with Python. A file database can be opened directly in Navicat.
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
    connection = sqlite3.connect(DATABASE_PATH)
    analysis_base.to_sql("analysis_base", connection, index=False, if_exists="replace")
    connection.execute(
        'CREATE INDEX idx_user_merchant ON analysis_base (user_id, merchant_id)'
    )

    overview = run_query(
        connection,
        "01_overview",
        """
        SELECT
            COUNT(*) AS sample_count,
            SUM(label) AS repeat_purchase_count,
            ROUND(AVG(label) * 100, 2) AS repeat_purchase_rate_pct,
            COUNT(DISTINCT user_id) AS user_count,
            COUNT(DISTINCT merchant_id) AS merchant_count
        FROM analysis_base;
        """,
    )

    behavior_segment = run_query(
        connection,
        "02_behavior_segment",
        """
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
        """,
    )

    demographic = run_query(
        connection,
        "03_demographic_segment",
        """
        SELECT
            CASE
                WHEN age_range IS NULL OR age_range = -1 THEN '未知年龄'
                ELSE CAST(age_range AS TEXT)
            END AS age_group,
            CASE
                WHEN gender = 0 THEN '女性'
                WHEN gender = 1 THEN '男性'
                ELSE '未知性别'
            END AS gender_group,
            COUNT(*) AS sample_count,
            ROUND(AVG(label) * 100, 2) AS repeat_purchase_rate_pct
        FROM analysis_base
        GROUP BY age_group, gender_group
        HAVING COUNT(*) >= 100
        ORDER BY repeat_purchase_rate_pct DESC, sample_count DESC;
        """,
    )

    merchant = run_query(
        connection,
        "04_top_merchants",
        """
        SELECT
            merchant_id,
            COUNT(*) AS sample_count,
            ROUND(AVG(label) * 100, 2) AS repeat_purchase_rate_pct,
            ROUND(AVG("该商家总行为次数"), 2) AS avg_merchant_actions
        FROM analysis_base
        GROUP BY merchant_id
        HAVING COUNT(*) >= 100
        ORDER BY repeat_purchase_rate_pct DESC, sample_count DESC
        LIMIT 15;
        """,
    )

    # A data-quality query: a user-merchant pair should only have one training label.
    quality = run_query(
        connection,
        "05_data_quality",
        """
        SELECT
            COUNT(*) AS duplicated_pair_count
        FROM (
            SELECT user_id, merchant_id
            FROM analysis_base
            GROUP BY user_id, merchant_id
            HAVING COUNT(*) > 1
        );
        """,
    )

    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False
    chart_data = behavior_segment.sort_values("repeat_purchase_rate_pct")
    plt.figure(figsize=(8, 4.8))
    bars = plt.barh(
        chart_data["behavior_segment"],
        chart_data["repeat_purchase_rate_pct"],
        color="#2563eb",
    )
    plt.title("不同商家行为阶段的复购率")
    plt.xlabel("复购率（%）")
    for bar, value in zip(bars, chart_data["repeat_purchase_rate_pct"]):
        plt.text(value, bar.get_y() + bar.get_height() / 2, f" {value:.2f}%", va="center")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "behavior_segment_repeat_rate.png", dpi=180)
    plt.close()

    connection.close()
    print("\nSQL 分析完成，结果目录：", OUTPUT_DIR)
    print("Navicat 数据库文件：", DATABASE_PATH)
    print("总览复购率：", overview.loc[0, "repeat_purchase_rate_pct"], "%")
    print("数据质量：重复用户—商家样本数 =", quality.loc[0, "duplicated_pair_count"])
    print("画像分组行数：", len(demographic), "；商家榜单行数：", len(merchant))


if __name__ == "__main__":
    main()
