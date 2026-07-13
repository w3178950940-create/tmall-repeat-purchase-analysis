"""End-to-end Tmall repeat-purchase analysis and user-growth pipeline."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split


RANDOM_STATE = 42
PAIR_FACTOR = 10_000  # merchant_id is below this value in this dataset
ACTION_NAMES = {0: "浏览", 1: "加购", 2: "购买", 3: "收藏"}


def find_workspace() -> Path:
    """Resolve workspace root from this source file, independent of cwd."""
    return Path(__file__).resolve().parents[2]


def make_dirs(project_dir: Path) -> tuple[Path, Path]:
    output_dir = project_dir / "outputs"
    cache_dir = project_dir / "cache"
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return output_dir, cache_dir


def make_pair_code(users: np.ndarray, merchants: np.ndarray) -> np.ndarray:
    return users.astype(np.int64) * PAIR_FACTOR + merchants.astype(np.int64)


def load_tables(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train = pd.read_csv(data_dir / "train_format1.csv")
    test = pd.read_csv(data_dir / "test_format1.csv")
    user_info = pd.read_csv(data_dir / "user_info_format1.csv")
    return train, test, user_info


def build_behavior_features(
    data_dir: Path,
    train: pd.DataFrame,
    test: pd.DataFrame,
    user_info: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Read the large log in chunks and aggregate only arrays needed for features."""
    pair_source = pd.concat(
        [
            train[["user_id", "merchant_id"]],
            test[["user_id", "merchant_id"]],
        ],
        ignore_index=True,
    ).drop_duplicates()
    pair_codes = make_pair_code(
        pair_source["user_id"].to_numpy(), pair_source["merchant_id"].to_numpy()
    )
    order = np.argsort(pair_codes)
    sorted_codes = pair_codes[order]

    max_user_id = int(
        max(
            user_info["user_id"].max(),
            pair_source["user_id"].max(),
        )
    )
    n_pairs = len(pair_source)
    user_counts = np.zeros((max_user_id + 1, 4), dtype=np.uint32)
    pair_counts = np.zeros((n_pairs, 4), dtype=np.uint32)
    user_last = np.zeros(max_user_id + 1, dtype=np.int32)
    pair_last = np.zeros(n_pairs, dtype=np.int32)
    all_action_counts = np.zeros(4, dtype=np.int64)
    max_timestamp = 0

    log_path = data_dir / "user_log_format1.csv"
    file_size_gb = log_path.stat().st_size / 1024**3
    print(f"读取全量行为日志（{file_size_gb:.2f} GB），请耐心等待…")
    start = time.time()
    rows_read = 0

    dtypes = {
        "user_id": "int32",
        "seller_id": "int32",
        "action_type": "int8",
    }
    reader = pd.read_csv(
        log_path,
        usecols=["user_id", "seller_id", "time_stamp", "action_type"],
        dtype=dtypes,
        chunksize=1_000_000,
    )
    target_users = pair_source["user_id"].to_numpy()

    for chunk_number, chunk in enumerate(reader, start=1):
        rows_read += len(chunk)
        timestamps = pd.to_numeric(chunk["time_stamp"], errors="coerce").fillna(0).astype(np.int32).to_numpy()
        max_timestamp = max(max_timestamp, int(timestamps.max()))
        actions = chunk["action_type"].to_numpy()
        action_valid = (actions >= 0) & (actions < 4)
        all_action_counts += np.bincount(actions[action_valid], minlength=4)

        # User-level behavior features for users that occur in train/test pairs.
        user_ids = chunk["user_id"].to_numpy()
        user_mask = np.isin(user_ids, target_users) & action_valid
        if user_mask.any():
            selected_users = user_ids[user_mask]
            selected_actions = actions[user_mask]
            selected_times = timestamps[user_mask]
            for action in range(4):
                action_users = selected_users[selected_actions == action]
                if len(action_users):
                    user_counts[:, action] += np.bincount(
                        action_users, minlength=max_user_id + 1
                    ).astype(np.uint32)
            np.maximum.at(user_last, selected_users, selected_times)

        # User-merchant behavior features for only the requested pairs.
        codes = make_pair_code(user_ids, chunk["seller_id"].to_numpy())
        positions = np.searchsorted(sorted_codes, codes)
        pair_mask = positions < len(sorted_codes)
        safe_positions = positions[pair_mask]
        matched_mask = np.zeros(len(chunk), dtype=bool)
        matched_mask[pair_mask] = sorted_codes[safe_positions] == codes[pair_mask]
        matched_mask &= action_valid
        if matched_mask.any():
            pair_indices = order[positions[matched_mask]]
            pair_actions = actions[matched_mask]
            pair_times = timestamps[matched_mask]
            for action in range(4):
                action_pairs = pair_indices[pair_actions == action]
                if len(action_pairs):
                    pair_counts[:, action] += np.bincount(
                        action_pairs, minlength=n_pairs
                    ).astype(np.uint32)
            np.maximum.at(pair_last, pair_indices, pair_times)

        if chunk_number % 10 == 0:
            print(f"已处理 {rows_read / 1_000_000:.0f} 百万条行为，耗时 {time.time() - start:.0f} 秒")

    print(f"日志处理完成：{rows_read:,} 条，耗时 {time.time() - start:.1f} 秒")

    features = pair_source.copy()
    for action, name in ACTION_NAMES.items():
        features[f"user_{name}_次数"] = user_counts[features["user_id"].to_numpy(), action]
        features[f"商家_{name}_次数"] = pair_counts[:, action]

    user_total = user_counts.sum(axis=1)
    pair_total = pair_counts.sum(axis=1)
    feature_users = features["user_id"].to_numpy()
    features["用户总行为次数"] = user_total[feature_users]
    features["该商家总行为次数"] = pair_total
    features["用户最近活跃时间"] = user_last[feature_users]
    features["该商家最近互动时间"] = pair_last
    features["用户活跃间隔"] = max_timestamp - user_last[feature_users]
    features["商家互动间隔"] = max_timestamp - pair_last
    features["商家行为占比"] = pair_total / np.maximum(user_total[feature_users], 1)
    features["商家购买占比"] = pair_counts[:, 2] / np.maximum(pair_total, 1)
    features["用户购买占比"] = user_counts[feature_users, 2] / np.maximum(user_total[feature_users], 1)
    features["加购后购买率"] = pair_counts[:, 2] / np.maximum(pair_counts[:, 1], 1)

    features = features.merge(user_info, on="user_id", how="left")
    features["age_range"] = features["age_range"].fillna(-1)
    features["gender"] = features["gender"].fillna(-1)

    behavior_stats = {ACTION_NAMES[key]: int(value) for key, value in enumerate(all_action_counts)}
    return features, behavior_stats


def save_eda_charts(train: pd.DataFrame, behavior_stats: dict[str, int], output_dir: Path) -> None:
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    label_counts = train["label"].value_counts().sort_index()
    axes[0].bar(["未复购", "复购"], label_counts.values, color=["#9aa5b1", "#3b82f6"])
    axes[0].set_title("训练集复购标签分布")
    axes[0].set_ylabel("样本数")
    for index, value in enumerate(label_counts.values):
        axes[0].text(index, value, f"{value:,}", ha="center", va="bottom")

    names = list(behavior_stats)
    values = list(behavior_stats.values())
    axes[1].bar(names, values, color="#14b8a6")
    axes[1].set_title("全量行为日志的行为类型分布")
    axes[1].set_ylabel("行为次数")
    axes[1].ticklabel_format(style="plain", axis="y")
    fig.tight_layout()
    fig.savefig(output_dir / "eda_overview.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def evaluate_top_k(y_true: np.ndarray, scores: np.ndarray, fraction: float = 0.2) -> dict[str, float]:
    top_n = max(1, int(len(scores) * fraction))
    top_indices = np.argsort(scores)[-top_n:]
    top_labels = y_true[top_indices]
    precision = float(top_labels.mean())
    recall = float(top_labels.sum() / max(y_true.sum(), 1))
    base_rate = float(y_true.mean())
    return {
        "top_fraction": fraction,
        "top_n": top_n,
        "precision_at_top_k": precision,
        "recall_at_top_k": recall,
        "lift_at_top_k": float(precision / base_rate) if base_rate else 0.0,
    }


def train_and_score(
    train: pd.DataFrame,
    test: pd.DataFrame,
    all_features: pd.DataFrame,
    output_dir: Path,
) -> tuple[dict[str, float], pd.DataFrame, pd.DataFrame]:
    train_data = train.merge(all_features, on=["user_id", "merchant_id"], how="left")
    test_data = test.merge(all_features, on=["user_id", "merchant_id"], how="left")
    feature_columns = [
        column
        for column in all_features.columns
        if column not in {"user_id", "merchant_id"}
    ]
    x = train_data[feature_columns].replace([np.inf, -np.inf], np.nan).fillna(0)
    y = train_data["label"].astype(int)
    x_test = test_data[feature_columns].replace([np.inf, -np.inf], np.nan).fillna(0)

    x_train, x_valid, y_train, y_valid = train_test_split(
        x, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )
    model = RandomForestClassifier(
        n_estimators=160,
        max_depth=14,
        min_samples_leaf=15,
        max_features=0.75,
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )
    print("训练随机森林复购模型…")
    model.fit(x_train, y_train)
    valid_scores = model.predict_proba(x_valid)[:, 1]
    metrics = {
        "validation_rows": int(len(y_valid)),
        "positive_rate": float(y_valid.mean()),
        "roc_auc": float(roc_auc_score(y_valid, valid_scores)),
        "pr_auc": float(average_precision_score(y_valid, valid_scores)),
    }
    metrics.update(evaluate_top_k(y_valid.to_numpy(), valid_scores, 0.2))

    importance = pd.DataFrame(
        {"feature": feature_columns, "importance": model.feature_importances_}
    ).sort_values("importance", ascending=False)
    importance.to_csv(output_dir / "feature_importance.csv", index=False, encoding="utf-8-sig")

    plt.figure(figsize=(8, 5))
    top_features = importance.head(12).sort_values("importance")
    plt.barh(top_features["feature"], top_features["importance"], color="#2563eb")
    plt.title("复购预测模型：Top 12 特征重要性")
    plt.xlabel("特征重要性")
    plt.tight_layout()
    plt.savefig(output_dir / "feature_importance.png", dpi=180, bbox_inches="tight")
    plt.close()

    final_model = RandomForestClassifier(
        n_estimators=160,
        max_depth=14,
        min_samples_leaf=15,
        max_features=0.75,
        class_weight="balanced_subsample",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )
    final_model.fit(x, y)
    test_scores = final_model.predict_proba(x_test)[:, 1]
    predictions = test[["user_id", "merchant_id"]].copy()
    predictions["repeat_purchase_probability"] = test_scores
    predictions.to_csv(
        output_dir / "test_repeat_purchase_predictions.csv", index=False, encoding="utf-8-sig"
    )

    strategy = predictions.copy()
    strategy = strategy.join(
        test_data[["商家_加购_次数", "商家_购买_次数"]]
    )
    high_threshold = strategy["repeat_purchase_probability"].quantile(0.8)
    strategy["用户分层"] = "低潜用户"
    high = strategy["repeat_purchase_probability"] >= high_threshold
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
    strategy.to_csv(output_dir / "user_growth_strategy.csv", index=False, encoding="utf-8-sig")
    return metrics, importance, strategy


def write_report(
    train: pd.DataFrame,
    behavior_stats: dict[str, int],
    metrics: dict[str, float],
    importance: pd.DataFrame,
    strategy: pd.DataFrame,
    output_dir: Path,
) -> None:
    top_feature_text = "、".join(importance.head(5)["feature"].tolist())
    segment_counts = strategy["用户分层"].value_counts().to_dict()
    report = f"""# 天猫用户复购预测与用户增长分析报告

## 1. 业务问题

大促后商家面临新客留存不足、全量营销成本高的问题。本项目通过预测用户对特定商家的复购倾向，为定向运营提供排序名单与人群策略。

## 2. 数据与方法

- 训练样本：{len(train):,} 条用户—商家记录；复购样本占比 {train['label'].mean():.2%}。
- 行为日志：浏览 {behavior_stats['浏览']:,}、加购 {behavior_stats['加购']:,}、购买 {behavior_stats['购买']:,}、收藏 {behavior_stats['收藏']:,} 次。
- 特征：用户总体行为、用户—商家行为、活跃间隔、购买/加购转化、年龄段和性别等。
- 方法：随机森林；使用分层训练/验证集切分，避免正负样本分布失衡。

## 3. 离线模型结果

- ROC-AUC：{metrics['roc_auc']:.4f}
- PR-AUC：{metrics['pr_auc']:.4f}
- Top 20% 用户的复购率：{metrics['precision_at_top_k']:.2%}
- Recall@Top20%：{metrics['recall_at_top_k']:.2%}
- Lift@Top20%：{metrics['lift_at_top_k']:.2f} 倍

Top 特征：{top_feature_text}。

## 4. 运营建议

- 高潜加购用户：加购商品降价提醒与限时优惠券；
- 高潜老客：新品/补货提醒与老客专属权益；
- 高潜浏览用户：相似商品推荐与内容种草；
- 低潜用户：低成本触达或暂不投放。

测试集分层数量：{segment_counts}。

## 5. 线上验证设计

将高潜人群随机拆分为实验组和对照组：实验组执行定向权益触达，对照组使用常规策略或不触达。以 30 天增量复购率、增量 GMV、ROI 为核心指标，并通过双样本比例检验判断复购率差异是否显著。

> 本报告的模型指标是离线结果，不等同于真实线上增量；线上效果必须以 A/B 测试为准。
"""
    (output_dir / "project_report.md").write_text(report, encoding="utf-8")


def main() -> None:
    workspace = find_workspace()
    project_dir = Path(__file__).resolve().parents[1]
    data_dir = workspace / "data_format1"
    if not data_dir.exists():
        sys.exit(f"未找到数据目录：{data_dir}")
    output_dir, cache_dir = make_dirs(project_dir)

    print("加载训练集、测试集与用户画像…")
    train, test, user_info = load_tables(data_dir)
    features_path = cache_dir / "pair_features.csv"
    stats_path = cache_dir / "behavior_stats.json"
    if features_path.exists() and stats_path.exists():
        print("发现已缓存特征，直接读取；如需重新处理日志，请删除 cache 文件夹。")
        all_features = pd.read_csv(features_path)
        behavior_stats = json.loads(stats_path.read_text(encoding="utf-8"))
    else:
        all_features, behavior_stats = build_behavior_features(data_dir, train, test, user_info)
        all_features.to_csv(features_path, index=False)
        stats_path.write_text(json.dumps(behavior_stats, ensure_ascii=False), encoding="utf-8")

    save_eda_charts(train, behavior_stats, output_dir)
    metrics, importance, strategy = train_and_score(train, test, all_features, output_dir)
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_report(train, behavior_stats, metrics, importance, strategy, output_dir)
    print("\n项目完成。关键指标：")
    for name, value in metrics.items():
        print(f"{name}: {value}")
    print(f"\n结果目录：{output_dir}")


if __name__ == "__main__":
    main()
