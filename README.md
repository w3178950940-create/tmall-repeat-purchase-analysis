# 天猫用户复购预测与用户增长分析

本项目使用 `data_format1` 的用户—商家标签、用户画像和全量行为日志，完成：

1. 诊断复购率与用户行为结构；
2. 构建用户、用户—商家层面的行为特征；
3. 训练复购倾向模型，并用 AUC、PR-AUC、Recall@Top20%、Lift@Top20% 评估；
4. 对测试集用户输出运营分层与触达建议。

## 运行

在 VS Code 中打开当前工作区后，在终端执行：

```powershell
python .\tmall_repurchase_project\src\run_pipeline.py
```

首次运行会读取约 1.9GB 的行为日志，耗时取决于电脑性能。运行完成后，在 `tmall_repurchase_project/outputs/` 查看：

- `metrics.json`：模型指标；
- `project_report.md`：可用于项目汇报的结论；
- `test_repeat_purchase_predictions.csv`：测试集复购概率；
- `user_growth_strategy.csv`：用户分层和运营建议；
- `*.png`：数据与模型图表。

## 数据说明

- `train_format1.csv`：训练标签；`label=1` 表示用户会再次购买该商家。
- `test_format1.csv`：待预测的用户—商家组合。
- `user_log_format1.csv`：行为明细。`action_type`：0 浏览、1 加购、2 购买、3 收藏。
- `user_info_format1.csv`：用户年龄段和性别。

> 模型的离线指标不等于真实线上增长结果。线上策略必须通过 A/B 测试，以增量复购率、GMV 与 ROI 验证。

## 本次运行结果

基于全量 54,925,330 条行为日志运行得到：

| 指标 | 结果 |
| --- | ---: |
| 训练样本复购率 | 6.11% |
| ROC-AUC | 0.5813 |
| PR-AUC | 0.0896 |
| Top 20% 用户复购率 | 9.47% |
| Recall@Top20% | 30.97% |
| Lift@Top20% | 1.55x |

因此，在离线验证集中，优先触达模型筛选出的前 20% 用户，可将复购密度从 6.11% 提升至 9.47%。详细分析见 [`outputs/project_report.md`](outputs/project_report.md)，图表见 `outputs/`。

## 仓库结构

```text
tmall_repurchase_project/
├── src/run_pipeline.py       # 全量日志处理、建模、分层的主程序
├── outputs/                  # 可展示的报告、指标和图表
├── requirements.txt          # 运行依赖
└── .gitignore                # 排除原始数据和大体积中间文件
```
