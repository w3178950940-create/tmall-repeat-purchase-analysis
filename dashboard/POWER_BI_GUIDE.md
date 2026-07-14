# Power BI：天猫用户复购增长运营看板

## 看板目的

本看板面向运营/产品负责人，回答四个问题：

1. 当前复购问题的规模与模型识别效果如何？
2. 应优先触达多少高潜用户？
3. 哪些行为阶段与人群的复购表现更高？
4. 逻辑回归为什么被选为最终排序模型？

## 已准备的数据

`dashboard/data/` 中是已聚合的数据，**不包含原始用户行为日志和用户级名单**，可安全上传到 GitHub：

| 文件 | 用途 |
| --- | --- |
| `kpi_metrics.csv` | 顶部 KPI 卡片 |
| `user_segment_summary.csv` | 用户分层与运营动作 |
| `behavior_segment_summary.csv` | 行为阶段与复购率 |
| `demographic_summary.csv` | 年龄段、性别复购率 |
| `top_merchant_summary.csv` | 高复购商家榜单 |
| `model_comparison_metrics.csv` | 逻辑回归与随机森林对比 |
| `top_feature_coefficients.csv` | 逻辑回归主要特征 |

## 在 Power BI Desktop 中搭建

1. 打开 Power BI Desktop，点击“获取数据 → 文本/CSV”。
2. 将 `dashboard/data/` 中的 7 个 CSV 全部导入；点击“加载”。
3. 所有表均是汇总表，当前版本不需要建立表关系。
4. 新建页面，命名为 **用户复购增长运营看板**。
5. 按以下布局建立视觉对象：

| 位置 | 视觉对象 | 字段/度量值 |
| --- | --- | --- |
| 顶部 | 4 张卡片 | 训练集复购率、验证集 ROC-AUC、Top20% Lift、高潜用户数 |
| 左中 | 圆环图 | `user_segment_summary`：图例=用户分层，值=用户数 |
| 右中 | 簇状条形图 | `behavior_segment_summary`：轴=行为分层，值=复购率 |
| 左下 | 簇状柱形图 | `model_comparison_metrics`：轴=model，值=roc_auc、top20_lift |
| 右下 | 表格 | `top_merchant_summary`：商家 ID、样本数、复购率、平均商家互动次数 |
| 右侧（可选） | 切片器/矩阵 | `demographic_summary`：年龄段、性别、复购率 |

推荐主题色：深蓝 `#2563EB`、青绿 `#14B8A6`、灰色 `#94A3B8`、橙色 `#F59E0B`。

## 关键说明

- `repeat_purchase_score` 是用于排序和分层的模型得分；由于训练时使用了类别权重，不应将其表述为严格校准的真实复购概率。
- Top20% Lift=1.74 表示高分前 20% 用户的复购率约为总体平均水平的 1.74 倍。
- 看板展示离线分析结果；线上效果仍需 A/B 测试验证。

## 设计预览

![看板预览](../outputs/powerbi_dashboard_preview.png)
