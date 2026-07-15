# 天猫用户复购预测与用户增长分析

一个围绕“如何在有限触达成本下识别高潜复购用户”的端到端数据分析项目。项目从全量用户行为日志出发，完成特征构建、SQL 业务诊断、模型评估、用户分层、MySQL 数据集市和 Power BI 运营看板搭建。

![Power BI 用户复购增长运营看板预览](outputs/powerbi_dashboard_preview.png)

## 业务问题

大促后商家往往面临整体复购率低、全量触达成本高的问题。本项目以用户—商家为分析粒度，目标是识别更值得触达的复购人群，并为不同分层输出可执行的运营动作。

```text
原始行为日志
  → 数据质量校验与特征工程
  → SQL 业务诊断
  → 模型对比与统计评估
  → 用户分层与增长策略
  → MySQL 业务视图
  → Power BI 复购增长运营看板
  → 线上 A/B 测试验证
```

## 实际运行结果

以下结果由本地代码在固定的 80/20 分层验证集上实际运行得到。

| 指标 | 逻辑回归（最终模型） | 随机森林（对比模型） |
| --- | ---: | ---: |
| ROC-AUC | **0.6127** | 0.5813 |
| PR-AUC | **0.1033** | 0.0896 |
| Top20% 用户复购率 | **10.61%** | 9.47% |
| Recall@Top20% | **34.70%** | 30.97% |
| Lift@Top20% | **1.74** | 1.55 |

- 逻辑回归相对随机森林的 AUC 差异，使用 200 次配对 Bootstrap 得到 95% 置信区间 **[0.0220, 0.0403]**，因此选择逻辑回归作为当前排序模型。
- 训练集共 **260,864** 条用户—商家样本，整体复购率为 **6.12%**；行为日志约 **5,492 万**条。
- 测试集策略输出中，识别出 **51,730** 名高潜老客与 **566** 名高潜加购用户，共 **52,296** 名优先触达人群。

> `repeat_purchase_score` 只用于排序和分层。模型训练使用了类别权重，得分不等同于严格校准的真实复购概率；真实线上效果仍需通过随机分流 A/B 测试验证。

## 项目产出

| 模块 | 解决的问题 | 核心产出 |
| --- | --- | --- |
| 数据准备 | 1.9GB 行为日志无法一次性读入 | Pandas 分块聚合 20 个用户—商家行为与画像特征 |
| 业务诊断 | 不清楚复购发生在哪些行为与商家中 | SQL 分层、商家复购率、样本重复校验 |
| 模型评估 | 如何公平选择可用的排序模型 | ROC-AUC、PR-AUC、Top20% Lift、Bootstrap 置信区间 |
| 增长策略 | 模型分数如何转成运营动作 | 高潜老客、高潜加购、低潜用户的差异化触达建议 |
| BI 看板 | 分析结果如何让业务方持续使用 | MySQL 视图、DAX 度量值、Power BI 单页运营看板 |

## Power BI 看板

- [Power BI 成果文件：天猫用户复购增长运营看板.pbix](dashboard/天猫用户复购增长运营看板.pbix)
- [Power BI + MySQL 真实数据链路说明](dashboard/POWER_BI_GUIDE.md)
- [DAX 度量值](dashboard/DAX_MEASURES.md)
- [`dashboard/data/`](dashboard/data/)：可公开查看的聚合数据副本；正式看板连接本机 MySQL 业务视图。

看板包含：模型 AUC、Top20% Lift、整体复购率、高潜用户数、用户分层分布、行为阶段复购率、模型 ROC-AUC 对比，以及各分层的运营动作建议。

## 快速复现

### 1. 准备环境与原始数据

```cmd
pip install -r requirements.txt
```

将原始数据放在项目上一级目录 `../data_format1/`，目录内需要包含：

```text
train_format1.csv
test_format1.csv
user_info_format1.csv
user_log_format1.csv
```

### 2. 按业务流程运行

```cmd
python src/01_data_preparation.py
python src/02_model_evaluation.py
python src/03_growth_strategy.py
```

第一步会分块读取约 1.9GB 的行为日志，并将中间特征缓存在 `cache/`；后续重复运行会复用缓存。业务诊断在 Navicat 中执行 `sql/01_business_analysis_mysql.sql`，MySQL 是本项目唯一的业务数据库。所有用户级缓存和预测明细均被 `.gitignore` 排除，不会上传。

### 3. 建立 MySQL 与 Power BI 数据链路（可选）

```cmd
python scripts/prepare_mysql_import.py
python scripts/prepare_growth_strategy_mysql.py
```

随后在 Navicat 中依次执行：

1. [`sql/00_create_schema.sql`](sql/00_create_schema.sql)，创建 `analysis_base` 表；导入 `data/mysql_import/analysis_base_mysql.csv`。
2. [`sql/01_business_analysis_mysql.sql`](sql/01_business_analysis_mysql.sql)，查看业务诊断 SQL。
3. [`sql/02_create_growth_strategy_table.sql`](sql/02_create_growth_strategy_table.sql)，创建 `growth_strategy` 表；导入 `data/mysql_import/growth_strategy_mysql.csv`。
4. [`sql/03_create_dashboard_mart.sql`](sql/03_create_dashboard_mart.sql)，创建 Power BI 使用的模型评估表与业务视图。

详细 Power BI 操作见 [看板说明](dashboard/POWER_BI_GUIDE.md)。

## 目录结构

详见 [项目结构说明](docs/PROJECT_STRUCTURE.md)。

```text
src/        主分析流程
sql/        MySQL 建表、业务分析与数据集市 SQL
scripts/    数据导入和文档辅助脚本
dashboard/  Power BI 文件、DAX、数据副本和说明
outputs/    图表、指标与报告
docs/       项目说明和截图
```

## 数据与结论边界

- 原始数据、行为特征缓存、用户级预测名单、策略名单和 MySQL 明细 CSV 不上传 GitHub。
- 本项目的模型效果是离线评估结果；运营方案是待验证的策略建议，而非已上线的增长结论。
- 推荐在真实业务中，对高潜用户随机分为实验组与对照组，以 30 天增量复购率、增量 GMV、ROI 为核心指标，并使用双样本比例检验评估显著性。
