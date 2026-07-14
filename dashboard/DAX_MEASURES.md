# Power BI DAX 度量值（MySQL 视图版）

先按 [`POWER_BI_GUIDE.md`](POWER_BI_GUIDE.md) 从 MySQL 导入 5 张表/视图，再在 Power BI 中选择“建模 → 新建度量值”。

```DAX
最终模型 AUC =
CALCULATE (
    MAX ( model_evaluation[roc_auc] ),
    model_evaluation[model_name] = "逻辑回归（最终模型）"
)
```

```DAX
最终模型 Top20% Lift =
CALCULATE (
    MAX ( model_evaluation[top20_lift] ),
    model_evaluation[model_name] = "逻辑回归（最终模型）"
)
```

```DAX
整体复购率 =
DIVIDE (
    SUM ( v_behavior_repurchase[repeat_purchase_count] ),
    SUM ( v_behavior_repurchase[sample_count] )
)
```

```DAX
高潜用户数 =
CALCULATE (
    SUM ( v_growth_segment[user_count] ),
    v_growth_segment[user_segment] <> "低潜用户"
)
```

```DAX
用户数 = SUM ( v_growth_segment[user_count] )
```

```DAX
行为分层复购率 = AVERAGE ( v_behavior_repurchase[repeat_purchase_rate] )
```

```DAX
商家平均复购率 = AVERAGE ( v_merchant_repurchase[repeat_purchase_rate] )
```

格式建议：AUC 设为小数点后 4 位；复购率设为百分比；Lift 设为小数点后 2 位；用户数与样本数设为整数。
