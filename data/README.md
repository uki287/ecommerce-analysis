# 数据目录

## raw/

原始 Olist CSV 的默认位置。当前实际文件在项目根目录的 `Brazilian-Data/raw/`，`src/config.py` 会自动识别；如果把它们移动到 `data/raw/`，代码无需修改。

不要修改原始 CSV。清洗和派生逻辑全部在 `src/prepare.py`，输出写到 `data/processed/`。

## processed/

由 `python src/run_analysis.py` 生成，可随时删除重跑：

| 文件 | 粒度 |
|---|---|
| `orders_master.csv` | 一行一个订单 |
| `items_enriched.csv` | 一行一个订单商品 |
| `order_category.csv` | 一行一个订单-品类 |
| `order_seller.csv` | 一行一个订单-卖家 |
| `customer_rfm.csv` | 一行一个客户 |
| `zip_centroids.csv` | 一行一个 ZIP 的经纬度中位数 |
| `reviews_latest.csv` | 一行一个订单的最新评论 |

图表用的聚合表在 `../report/tables/`，不要在这里手工做报表。

## processed_zh/

`processed/` 的中文显示副本，表头、状态、州、品类、区间标签已转为中文；ID、日期、城市名保留原值。文件名为 `*_zh.csv`，例如 `orders_master_zh.csv`。

## 中文图表底表

`../report/tables_zh/` 是 `../report/tables/` 的中文显示副本，文件名为 `*_zh.csv`，适合直接接入 BI 做中文图表。英文标准表仍保留，供代码和跨表关联使用。