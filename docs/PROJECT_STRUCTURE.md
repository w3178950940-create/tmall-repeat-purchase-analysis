# 项目结构说明

```text
tmall_repurchase_project/
├── src/                         # 基础版：全量行为日志处理与随机森林基线
├── advanced/                    # 进阶分析代码
│   ├── 01_sql_business_analysis.py
│   ├── 02_model_comparison.py
│   ├── 03_final_logistic_strategy.py
│   └── mysql/                   # MySQL 建表、导入和查询 SQL
├── dashboard/                   # Power BI 数据、DAX 与搭建说明
│   ├── data/                    # 可上传的聚合数据
│   ├── POWER_BI_GUIDE.md
│   └── DAX_MEASURES.md
├── docs/
│   ├── images/                  # 文档截图和图示
│   └── PROJECT_STRUCTURE.md
├── outputs/                     # 模型指标、图表与最终报告
├── cache/                       # 大体积特征缓存（不上传）
└── requirements.txt
```

## 不上传 GitHub 的文件

- 原始数据：`data_format1/`
- 行为特征缓存：`cache/`
- 用户级预测名单/策略名单
- MySQL 导入用的用户级 CSV
- 本地 SQLite 数据库

仓库只保留可复现代码、SQL、聚合后的看板数据、图表、指标和说明文档。
