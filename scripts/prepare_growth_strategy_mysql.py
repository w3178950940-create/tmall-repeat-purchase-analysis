"""Convert the final user-growth strategy output into a MySQL import CSV."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
SOURCE = PROJECT_DIR / "outputs" / "final_user_growth_strategy.csv"
DESTINATION = PROJECT_DIR / "data" / "mysql_import" / "growth_strategy_mysql.csv"


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError("未找到最终策略文件，请先运行 src/03_growth_strategy.py")
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    strategy = pd.read_csv(SOURCE)
    mysql_data = strategy.rename(
        columns={
            "repeat_purchase_score": "repeat_purchase_score",
            "用户分层": "user_segment",
            "建议动作": "recommended_action",
            "商家_加购_次数": "merchant_cart_cnt",
            "商家_购买_次数": "merchant_buy_cnt",
            "商家_收藏_次数": "merchant_favorite_cnt",
        }
    )[
        [
            "user_id",
            "merchant_id",
            "repeat_purchase_score",
            "user_segment",
            "recommended_action",
            "merchant_cart_cnt",
            "merchant_buy_cnt",
            "merchant_favorite_cnt",
        ]
    ]
    mysql_data.to_csv(DESTINATION, index=False, encoding="utf-8-sig")
    print(f"导出完成：{DESTINATION}")
    print(f"行数：{len(mysql_data):,}；字段：{', '.join(mysql_data.columns)}")


if __name__ == "__main__":
    main()
