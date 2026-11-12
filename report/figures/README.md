# 图表文件说明

本目录包含 10 张中文图表，全部由 `notebooks/02_olist_10_charts.ipynb` 生成，数据来自 `report/tables_zh/` 与 `data/processed_zh/`。

无需 Jupyter 的 HTML 预览：`report/Olist_10_charts.html`。

## 图表清单

| 文件 | 类型 | 回答的问题 | 主要数据 |
|---|---|---|---|
| `01_monthly_gmv_orders.png` | 双轴组合图 | 月度 GMV 与有效订单如何变化？ | `monthly_kpis_zh` |
| `02_category_top10.png` | 横向条形图 | 哪些品类贡献最多 GMV？ | `category_kpis_zh` |
| `03_payment_donut.png` | 环形图 | 支付金额由哪些方式构成？ | `payment_type_kpis_zh` |
| `04_category_bubble.png` | 气泡散点图 | 品类规模、评分、订单量、迟到率的关系？ | `category_kpis_zh` |
| `05_state_bubble_map.png` | 地理气泡图 | 州级 GMV 与迟到率如何分布？ | `state_kpis_zh` |
| `06_delivery_histogram.png` | 直方图 | 送达天数集中在什么区间？ | `orders_master_zh` |
| `07_category_boxplot.png` | 箱线图 | 头部品类订单金额分布差异？ | `order_category_zh` |
| `08_cohort_heatmap.png` | 热力图 | 首购后 1–12 个月留存如何？ | `cohort_retention_wide_zh` |
| `09_seller_pareto.png` | 帕累托图 | 卖家 GMV 是否高度集中？ | `seller_kpis_zh` |
| `10_state_radar.png` | 雷达图 | Top 5 州的多指标谁更均衡？ | `state_kpis_zh` |

`contact_sheet.png` 是 10 张图的拼图预览。

## 主要结论

1. **月度**：2017-11 是 GMV 峰值（约 R$1.00M、7,421 单），之后订单量在 6,000–7,500 区间波动。
2. **品类**：美妆个护第一，但只占 9.3%；Top 3 合计约 25.9%，没有单一品类依赖。
3. **支付**：信用卡占支付金额约 78.5%，银行票据约 18.0%。
4. **品类体验**：规模大的品类多在 4.0–4.2 分；迟到率高的品类不一定规模大，适合做质量专题。
5. **地域**：圣保罗州占 GMV 38.3%，前五州合计 73.9%；北部/东北部部分州迟到率偏高。
6. **配送**：送达中位数 10.2 天，均值 12.3 天，P90 22.9 天；30 天以上是明显长尾。
7. **品类金额**：头部品类中位数多在 R$80–150，手表礼品中位数和上四分位更高。
8. **Cohort**：首购后 1–12 个月留存整体低于 1%，复购极低。
9. **卖家**：前 100 名卖家累计贡献约 45.3% GMV，集中度中等，长尾很长。
10. **州份雷达**：SP 规模最大但客单价不突出；RJ 规模第二但评分/准时率偏弱；MG 更均衡。

## 重新生成

```powershell
# 1) 运行绘图脚本（可选，用于快速检查）
& "C:\ProgramData\anaconda3\python.exe" notebooks/02_olist_10_charts.py

# 2) 执行 notebook，生成内嵌输出
& "C:\ProgramData\anaconda3\python.exe" -m nbconvert `
  --to notebook --execute --inplace `
  --ExecutePreprocessor.timeout=600 `
  notebooks/02_olist_10_charts.ipynb
```

> 如果你自己的 Jupyter 环境已安装 `matplotlib`，直接打开 notebook 逐格运行即可；不需要 Anaconda 的绝对路径。

## 备注

- 图表使用中文显示版数据，表头和业务标签均为中文；ID、日期、城市名保留原值。
- 比例字段仍是 0–1 小数，图中已按百分比格式化。
- 图表只做展示，不重新定义口径；口径详见 `report/analysis_guide.md`。
- 颜色、字体、图片尺寸可在 notebook 开头的 `plt.rcParams` 和 `PALETTE` 中调整。