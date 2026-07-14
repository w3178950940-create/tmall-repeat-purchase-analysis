# Power BI DAX 度量值

导入数据后，在 Power BI 中选择“建模 → 新建度量值”，逐条创建。表名使用导入后的默认名称。

```DAX
训练集复购率 =
CALCULATE (
    MAX ( kpi_metrics[value] ),
    kpi_metrics[metric] = "训练集复购率"
)
```

```DAX
验证集 ROC-AUC =
CALCULATE (
    MAX ( kpi_metrics[value] ),
    kpi_metrics[metric] = "验证集 ROC-AUC"
)
```

```DAX
Top20% Lift =
CALCULATE (
    MAX ( kpi_metrics[value] ),
    kpi_metrics[metric] = "Top20% Lift"
)
```

```DAX
高潜用户数 =
CALCULATE (
    MAX ( kpi_metrics[value] ),
    kpi_metrics[metric] = "高潜用户数"
)
```

```DAX
用户数 = SUM ( user_segment_summary[用户数] )
```

```DAX
平均复购得分 = AVERAGE ( user_segment_summary[平均复购得分] )
```

```DAX
行为分层复购率 = AVERAGE ( behavior_segment_summary[复购率] )
```

格式建议：训练集复购率、行为分层复购率格式设为“百分比”；ROC-AUC 设为小数点后 4 位；Top20% Lift 设为小数点后 2 位；高潜用户数设为整数。
