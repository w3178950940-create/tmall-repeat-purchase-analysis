"""Advanced module 2: compare a baseline model with random forest fairly.

Both models use the same features and exactly the same stratified validation
set. Besides point estimates, bootstrap confidence intervals are calculated
for ROC-AUC so the evaluation is not based on a single random split alone.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


RANDOM_STATE = 42
PROJECT_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = PROJECT_DIR.parent
TRAIN_PATH = WORKSPACE_DIR / "data_format1" / "train_format1.csv"
FEATURE_PATH = PROJECT_DIR / "cache" / "pair_features.csv"
OUTPUT_DIR = PROJECT_DIR / "advanced" / "outputs"


def evaluate_top_k(y_true: np.ndarray, scores: np.ndarray, fraction: float = 0.2) -> dict[str, float]:
    """Evaluate the business value of contacting only the highest-scored users."""
    top_n = max(1, int(len(scores) * fraction))
    top_indices = np.argsort(scores)[-top_n:]
    top_labels = y_true[top_indices]
    precision = float(top_labels.mean())
    base_rate = float(y_true.mean())
    return {
        "top20_precision": precision,
        "top20_recall": float(top_labels.sum() / y_true.sum()),
        "top20_lift": float(precision / base_rate),
    }


def bootstrap_auc_ci(y_true: np.ndarray, scores: np.ndarray, n_bootstrap: int = 200) -> tuple[float, float]:
    """Use resampling to estimate a 95% confidence interval of ROC-AUC."""
    rng = np.random.default_rng(RANDOM_STATE)
    values: list[float] = []
    for _ in range(n_bootstrap):
        indices = rng.integers(0, len(y_true), len(y_true))
        # A resample could theoretically contain one class; skip it in that case.
        if np.unique(y_true[indices]).size == 2:
            values.append(float(roc_auc_score(y_true[indices], scores[indices])))
    return tuple(np.percentile(values, [2.5, 97.5]))


def bootstrap_auc_difference_ci(
    y_true: np.ndarray,
    first_scores: np.ndarray,
    second_scores: np.ndarray,
    n_bootstrap: int = 200,
) -> tuple[float, float]:
    """Paired bootstrap CI for AUC(first model) - AUC(second model)."""
    rng = np.random.default_rng(RANDOM_STATE + 1)
    differences: list[float] = []
    for _ in range(n_bootstrap):
        indices = rng.integers(0, len(y_true), len(y_true))
        if np.unique(y_true[indices]).size == 2:
            difference = roc_auc_score(y_true[indices], first_scores[indices]) - roc_auc_score(
                y_true[indices], second_scores[indices]
            )
            differences.append(float(difference))
    return tuple(np.percentile(differences, [2.5, 97.5]))


def metric_row(name: str, y_true: np.ndarray, scores: np.ndarray) -> dict[str, float | str]:
    top_metrics = evaluate_top_k(y_true, scores)
    auc_lower, auc_upper = bootstrap_auc_ci(y_true, scores)
    return {
        "model": name,
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "roc_auc_ci_lower": float(auc_lower),
        "roc_auc_ci_upper": float(auc_upper),
        "pr_auc": float(average_precision_score(y_true, scores)),
        **top_metrics,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("读取训练数据与已构建特征…")
    train = pd.read_csv(TRAIN_PATH)
    features = pd.read_csv(FEATURE_PATH)
    data = train.merge(features, on=["user_id", "merchant_id"], how="left")
    feature_columns = [column for column in features.columns if column not in {"user_id", "merchant_id"}]
    x = data[feature_columns].replace([np.inf, -np.inf], np.nan).fillna(0)
    y = data["label"].astype(int)

    x_train, x_valid, y_train, y_valid = train_test_split(
        x, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )
    print(f"训练集：{len(x_train):,}；验证集：{len(x_valid):,}；验证集复购率：{y_valid.mean():.2%}")

    # Baseline: standardized features + logistic regression. It is simple and interpretable.
    logistic = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "model",
                LogisticRegression(
                    max_iter=1000,
                    class_weight="balanced",
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    print("训练逻辑回归基线模型…")
    logistic.fit(x_train, y_train)
    logistic_scores = logistic.predict_proba(x_valid)[:, 1]

    # Candidate model: the same random forest setting used in the main project.
    forest = RandomForestClassifier(
        n_estimators=160,
        max_depth=14,
        min_samples_leaf=15,
        max_features=0.75,
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )
    print("训练随机森林候选模型…")
    forest.fit(x_train, y_train)
    forest_scores = forest.predict_proba(x_valid)[:, 1]

    y_valid_array = y_valid.to_numpy()
    results = pd.DataFrame(
        [
            metric_row("逻辑回归（基线）", y_valid_array, logistic_scores),
            metric_row("随机森林（候选）", y_valid_array, forest_scores),
        ]
    )
    results.to_csv(OUTPUT_DIR / "model_comparison_metrics.csv", index=False, encoding="utf-8-sig")
    auc_difference_ci = bootstrap_auc_difference_ci(
        y_valid_array, logistic_scores, forest_scores
    )
    print("\n模型对比结果：")
    print(results.round(4).to_string(index=False))
    print(
        "逻辑回归 AUC - 随机森林 AUC 的 95% 配对自助法置信区间："
        f"{auc_difference_ci[0]:.4f} 至 {auc_difference_ci[1]:.4f}"
    )

    # Visualize business-facing and statistical metrics separately.
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    axes[0].bar(results["model"], results["roc_auc"], color=["#94a3b8", "#2563eb"])
    axes[0].set_title("模型整体区分能力（ROC-AUC）")
    axes[0].set_ylim(0.5, max(0.65, results["roc_auc"].max() + 0.03))
    for index, value in enumerate(results["roc_auc"]):
        axes[0].text(index, value + 0.003, f"{value:.4f}", ha="center")

    axes[1].bar(results["model"], results["top20_lift"], color=["#94a3b8", "#14b8a6"])
    axes[1].set_title("定向触达效率（Lift@Top20%）")
    axes[1].set_ylabel("倍数")
    for index, value in enumerate(results["top20_lift"]):
        axes[1].text(index, value + 0.02, f"{value:.2f}", ha="center")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "model_comparison.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    report_lines = [
        "# 进阶模块：模型对比与科学评估",
        "",
        "两种模型使用相同的特征、相同的 80/20 分层训练验证切分。",
        "ROC-AUC 置信区间通过 200 次自助法重采样计算。",
        f"逻辑回归相对随机森林的 AUC 差值 95% 配对自助法置信区间：{auc_difference_ci[0]:.4f}–{auc_difference_ci[1]:.4f}。",
        "",
    ]
    for _, row in results.iterrows():
        report_lines.append(
            f"- {row['model']}：ROC-AUC {row['roc_auc']:.4f} "
            f"（95% CI {row['roc_auc_ci_lower']:.4f}–{row['roc_auc_ci_upper']:.4f}），"
            f"PR-AUC {row['pr_auc']:.4f}，Lift@Top20% {row['top20_lift']:.2f}。"
        )
    (OUTPUT_DIR / "model_comparison_report.md").write_text("\n".join(report_lines), encoding="utf-8")
    print("\n完成：结果 CSV、图表和报告已保存到", OUTPUT_DIR)


if __name__ == "__main__":
    main()
