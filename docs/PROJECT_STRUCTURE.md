# 项目结构说明

```text
tmall_repurchase_project/
├── src/                         # 主分析流程（按实际业务顺序编号）
│   ├── 01_data_preparation.py   # 分块处理行为日志、构建特征与基线结果
│   ├── 02_model_evaluation.py   # 逻辑回归、随机森林与 Bootstrap 评估
│   └── 03_growth_strategy.py    # 用户分层、策略输出与看板聚合数据
├── sql/                         # MySQL 建表、业务分析与数据集市视图
├── scripts/                     # MySQL 导入文件和 SQL 截图的辅助脚本
├── dashboard/                   # Power BI 文件、DAX、数据副本与搭建说明
├── data/                        # 不公开的本地导入文件说明
├── outputs/                     # 可展示的图表、指标、报告与聚合结果
│   ├── diagnosis/
│   └── model_evaluation/
├── cache/                       # 大体积特征缓存（不上传）
├── docs/                        # 项目说明和截图
└── requirements.txt
```

## 不上传 GitHub 的文件

- 原始数据：仓库外同级目录 `../data_format1/`
- 行为特征缓存：`cache/`
- 用户级预测名单、策略名单
- MySQL 导入用的用户级 CSV：`data/mysql_import/`

仓库只保留可复现代码、SQL、聚合后的看板数据、图表、指标和说明文档。
