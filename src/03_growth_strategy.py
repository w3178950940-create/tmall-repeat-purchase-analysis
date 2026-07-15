"""Step 3: train the selected logistic model and prepare dashboard data.

The logistic model was selected because it outperformed random forest in
src/02_model_evaluation.py on the same validation split.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


RANDOM_STATE = 42
PROJECT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = PROJECT_DIR.parent
DATA_DIR = WORKSPACE_DIR / "data_format1"
FEATURE_PATH = PROJECT_DIR / "cache" / "pair_features.csv"
OUTPUT_DIR = PROJECT_DIR / "outputs"
DASHBOARD_DATA_DIR = PROJECT_DIR / "dashboard" / "data"


def top20_metrics(y_true: np.ndarray, scores: np.ndarray) -> dict[str, float | int]:
    top_n = max(1, int(len(scores) * 0.2))
    top_labels = y_true[np.argsort(scores)[-top_n:]]
    precision = float(top_labels.mean())
    return {
        "top_fraction": 0.2,
        "top_n": top_n,
        "top20_precision": precision,
        "top20_recall": float(top_labels.sum() / y_true.sum()),
        "top20_lift": float(precision / y_true.mean()),
    }


def behavior_segment(data: pd.DataFrame) -> pd.Series:
    return pd.Series(
        np.select(
            [
                data["商家_加购_次数"] > 0,
                data["商家_购买_次数"] > 0,
                data["商家_收藏_次数"] > 0,
            ],
            ["有加购行为", "有购买历史", "有收藏行为"],
            default="仅浏览或无互动",
        ),
        index=data.index,
    )


def build_dashboard_data(
    train_data: pd.DataFrame,
    strategy: pd.DataFrame,
    metrics: dict[str, float | int],
    coefficients: pd.DataFrame,
) -> None:
    """Write small aggregated CSV files that Power BI can import directly."""
    DASHBOARD_DATA_DIR.mkdir(parents=True, exist_ok=True)

    kpi = pd.DataFrame(
        [
            {"metric": "训练集复购率", "value": train_data["label"].mean(), "display_format": "percent"},
            {"metric": "验证集 ROC-AUC", "value": metrics["roc_auc"], "display_format": "decimal"},
            {"metric": "Top20% Lift", "value": metrics["top20_lift"], "display_format": "decimal"},
            {"metric": "高潜用户数", "value": int((strategy["用户分层"] != "低潜用户").sum()), "display_format": "integer"},
        ]
    )
    kpi.to_csv(DASHBOARD_DATA_DIR / "kpi_metrics.csv", index=False, encoding="utf-8-sig")

    segment_summary = (
        strategy.groupby(["用户分层", "建议动作"], as_index=False)
        .agg(用户数=("user_id", "size"), 平均复购得分=("repeat_purchase_score", "mean"))
        .sort_values("用户数", ascending=False)
    )
    segment_summary.to_csv(DASHBOARD_DATA_DIR / "user_segment_summary.csv", index=False, encoding="utf-8-sig")

    behavior = train_data.assign(行为分层=behavior_segment(train_data))
    behavior_summary = (
        behavior.groupby("行为分层", as_index=False)
        .agg(样本数=("label", "size"), 复购人数=("label", "sum"), 复购率=("label", "mean"))
        .sort_values("复购率", ascending=False)
    )
    behavior_summary.to_csv(DASHBOARD_DATA_DIR / "behavior_segment_summary.csv", index=False, encoding="utf-8-sig")

    demographic = train_data.assign(
        年龄段=train_data["age_range"].fillna(-1).replace(-1, "未知年龄").astype(str),
        性别=np.select(
            [train_data["gender"] == 0, train_data["gender"] == 1],
            ["女性", "男性"],
            default="未知性别",
        ),
    )
    demographic_summary = (
        demographic.groupby(["年龄段", "性别"], as_index=False)
        .agg(样本数=("label", "size"), 复购率=("label", "mean"))
        .query("样本数 >= 100")
        .sort_values("复购率", ascending=False)
    )
    demographic_summary.to_csv(DASHBOARD_DATA_DIR / "demographic_summary.csv", index=False, encoding="utf-8-sig")

    merchant_summary = (
        train_data.groupby("merchant_id", as_index=False)
        .agg(
            样本数=("label", "size"),
            复购率=("label", "mean"),
            平均商家互动次数=("该商家总行为次数", "mean"),
        )
        .query("样本数 >= 100")
        .sort_values(["复购率", "样本数"], ascending=False)
        .head(20)
    )
    merchant_summary.to_csv(DASHBOARD_DATA_DIR / "top_merchant_summary.csv", index=False, encoding="utf-8-sig")
    coefficients.head(15).to_csv(DASHBOARD_DATA_DIR / "top_feature_coefficients.csv", index=False, encoding="utf-8-sig")

    comparison_path = PROJECT_DIR / "outputs" / "model_evaluation" / "model_comparison_metrics.csv"
    if comparison_path.exists():
        pd.read_csv(comparison_path).to_csv(
            DASHBOARD_DATA_DIR / "model_comparison_metrics.csv", index=False, encoding="utf-8-sig"
        )


def create_dashboard_preview(
    kpi: pd.DataFrame,
    segment_summary: pd.DataFrame,
    behavior_summary: pd.DataFrame,
    comparison: pd.DataFrame,
) -> None:
    """Create an actual-data preview of the recommended Power BI page."""
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False
    fig = plt.figure(figsize=(14, 8), facecolor="#f8fafc")
    grid = fig.add_gridspec(3, 4, height_ratios=[0.8, 2, 2])
    fig.suptitle("天猫用户复购增长运营看板（Power BI 设计预览）", fontsize=18, fontweight="bold", y=0.98)

    for index, row in kpi.iterrows():
        axis = fig.add_subplot(grid[0, index])
        axis.set_facecolor("white")
        axis.set_xticks([])
        axis.set_yticks([])
        value = row["value"]
        if row["display_format"] == "percent":
            shown = f"{value:.2%}"
        elif row["display_format"] == "integer":
            shown = f"{int(value):,}"
        else:
            shown = f"{value:.4f}" if "AUC" in row["metric"] else f"{value:.2f}x"
        axis.text(0.5, 0.63, row["metric"], ha="center", fontsize=10, color="#475569")
        axis.text(0.5, 0.26, shown, ha="center", fontsize=19, fontweight="bold", color="#0f172a")

    axis_segment = fig.add_subplot(grid[1, :2])
    axis_segment.pie(segment_summary["用户数"], labels=segment_summary["用户分层"], autopct="%.1f%%", startangle=90)
    axis_segment.set_title("测试集用户分层分布")

    axis_behavior = fig.add_subplot(grid[1, 2:])
    behavior = behavior_summary.sort_values("复购率")
    axis_behavior.barh(behavior["行为分层"], behavior["复购率"], color="#2563eb")
    axis_behavior.set_title("不同商家行为阶段的复购率")
    axis_behavior.set_xlabel("复购率")
    axis_behavior.xaxis.set_major_formatter("{x:.0%}")

    axis_model = fig.add_subplot(grid[2, :2])
    axis_model.bar(comparison["model"], comparison["roc_auc"], color=["#94a3b8", "#14b8a6"])
    axis_model.set_title("模型对比：ROC-AUC")
    axis_model.set_ylim(0.5, 0.65)
    for index, value in enumerate(comparison["roc_auc"]):
        axis_model.text(index, value + 0.003, f"{value:.4f}", ha="center")

    axis_lift = fig.add_subplot(grid[2, 2:])
    axis_lift.bar(comparison["model"], comparison["top20_lift"], color=["#94a3b8", "#f59e0b"])
    axis_lift.set_title("模型对比：Lift@Top20%")
    axis_lift.set_ylabel("倍数")
    for index, value in enumerate(comparison["top20_lift"]):
        axis_lift.text(index, value + 0.02, f"{value:.2f}x", ha="center")

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(OUTPUT_DIR / "powerbi_dashboard_preview.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    train = pd.read_csv(DATA_DIR / "train_format1.csv")
    test = pd.read_csv(DATA_DIR / "test_format1.csv")
    features = pd.read_csv(FEATURE_PATH)
    train_data = train.merge(features, on=["user_id", "merchant_id"], how="left")
    test_data = test.merge(features, on=["user_id", "merchant_id"], how="left")
    feature_columns = [column for column in features.columns if column not in {"user_id", "merchant_id"}]
    x = train_data[feature_columns].replace([np.inf, -np.inf], np.nan).fillna(0)
    y = train_data["label"].astype(int)
    x_test = test_data[feature_columns].replace([np.inf, -np.inf], np.nan).fillna(0)

    x_train, x_valid, y_train, y_valid = train_test_split(
        x, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )
    model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE)),
        ]
    )
    print("训练最终逻辑回归模型…")
    model.fit(x_train, y_train)
    valid_scores = model.predict_proba(x_valid)[:, 1]
    metrics: dict[str, float | int] = {
        "validation_rows": int(len(y_valid)),
        "positive_rate": float(y_valid.mean()),
        "roc_auc": float(roc_auc_score(y_valid, valid_scores)),
        "pr_auc": float(average_precision_score(y_valid, valid_scores)),
    }
    metrics.update(top20_metrics(y_valid.to_numpy(), valid_scores))
    print(json.dumps(metrics, ensure_ascii=False, indent=2))

    # Refit on all labeled data before scoring test pairs.
    final_model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE)),
        ]
    )
    final_model.fit(x, y)
    test_scores = final_model.predict_proba(x_test)[:, 1]
    predictions = test[["user_id", "merchant_id"]].copy()
    # class_weight improves ranking on imbalanced data; the output is used as a score,
    # not claimed as a calibrated real-world probability.
    predictions["repeat_purchase_score"] = test_scores
    predictions.to_csv(OUTPUT_DIR / "final_logistic_predictions.csv", index=False, encoding="utf-8-sig")

    strategy = predictions.join(test_data[["商家_加购_次数", "商家_购买_次数", "商家_收藏_次数"]])
    high = strategy["repeat_purchase_score"] >= strategy["repeat_purchase_score"].quantile(0.8)
    strategy["用户分层"] = "低潜用户"
    strategy.loc[high & (strategy["商家_加购_次数"] > 0), "用户分层"] = "高潜加购用户"
    strategy.loc[high & (strategy["商家_加购_次数"] == 0) & (strategy["商家_购买_次数"] > 0), "用户分层"] = "高潜老客"
    strategy.loc[high & (strategy["商家_加购_次数"] == 0) & (strategy["商家_购买_次数"] == 0), "用户分层"] = "高潜浏览用户"
    action_map = {
        "高潜加购用户": "加购商品降价提醒 + 限时优惠券",
        "高潜老客": "新品/补货提醒 + 老客专属权益",
        "高潜浏览用户": "相似商品推荐 + 内容种草触达",
        "低潜用户": "低成本触达或暂不投放",
    }
    strategy["建议动作"] = strategy["用户分层"].map(action_map)
    strategy.to_csv(OUTPUT_DIR / "final_user_growth_strategy.csv", index=False, encoding="utf-8-sig")

    coefficients = pd.DataFrame(
        {
            "feature": feature_columns,
            "standardized_coefficient": final_model.named_steps["model"].coef_[0],
        }
    )
    coefficients["absolute_coefficient"] = coefficients["standardized_coefficient"].abs()
    coefficients = coefficients.sort_values("absolute_coefficient", ascending=False)
    coefficients.to_csv(OUTPUT_DIR / "final_logistic_feature_coefficients.csv", index=False, encoding="utf-8-sig")

    build_dashboard_data(train_data, strategy, metrics, coefficients)
    kpi = pd.read_csv(DASHBOARD_DATA_DIR / "kpi_metrics.csv")
    segments = pd.read_csv(DASHBOARD_DATA_DIR / "user_segment_summary.csv")
    behavior = pd.read_csv(DASHBOARD_DATA_DIR / "behavior_segment_summary.csv")
    comparison = pd.read_csv(DASHBOARD_DATA_DIR / "model_comparison_metrics.csv")
    create_dashboard_preview(kpi, segments, behavior, comparison)

    (OUTPUT_DIR / "final_logistic_metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    segment_counts = strategy["用户分层"].value_counts().to_dict()
    report = f"""# 最终模型与用户增长策略\n\n
## 模型选择\n\n
在同一分层验证集上，逻辑回归的 ROC-AUC 为 {metrics['roc_auc']:.4f}、PR-AUC 为 {metrics['pr_auc']:.4f}，优于随机森林，因此作为最终复购排序模型。\n\n
## 离线验证结果\n\n
- 验证集样本：{metrics['validation_rows']:,}\n
- 基准复购率：{metrics['positive_rate']:.2%}\n
- Top20% 用户复购率：{metrics['top20_precision']:.2%}\n
- Recall@Top20%：{metrics['top20_recall']:.2%}\n
- Lift@Top20%：{metrics['top20_lift']:.2f}\n\n
## 测试集用户分层\n\n
{segment_counts}\n\n
> 以上均为离线模型结果。真实增长效果应通过高潜人群随机分流，以增量复购率、GMV 和 ROI 进行 A/B 测试验证。\n"""
    (OUTPUT_DIR / "final_logistic_report.md").write_text(report, encoding="utf-8")
    print("完成：最终策略、Power BI 聚合数据和看板预览已生成。")


if __name__ == "__main__":
    main()
