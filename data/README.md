# 本地数据说明

本项目不上传原始天猫数据、用户级预测结果或 MySQL 导入明细，避免仓库体积过大并保护用户级数据。

- 原始数据放在项目上一级目录的 `data_format1/`：`train_format1.csv`、`test_format1.csv`、`user_info_format1.csv`、`user_log_format1.csv`。
- 运行 `scripts/prepare_mysql_import.py` 和 `scripts/prepare_growth_strategy_mysql.py` 后，会在 `data/mysql_import/` 生成仅供本机 Navicat 导入的 CSV。
- GitHub 中保留 `dashboard/data/` 的聚合副本，便于查看看板指标，但该副本不包含用户级明细。
