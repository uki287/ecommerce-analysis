# Dashboard 连接说明

这个文件夹用于放你的 BI 文件（`.pbix`、`.twbx`、`.xlsx` 等）。分析代码负责生成数据底表；图表示例在 `../notebooks/02_olist_10_charts.ipynb`，Power BI 的操作步骤见 `../report/PowerBI操作手册.docx`。

## 先看

- **Power BI 操作手册**：`../report/PowerBI操作手册.docx`
- **路线 A 粘贴包**：`pbi_paste_pack/`（DAX、主题、逐图配方、10 张 PNG）
- **PBIP 修改补丁**：`pbi_pbip_patch/`（PBIX 不能直接改，先另存为 PBIP 再应用）
- **Power BI 主题**：`olist_theme.json`（视图 → 主题 → 浏览主题）
- **目标效果**：`../report/Olist_10_charts.html`

## 数据源

做中文图表时，优先连接 `../report/tables_zh/` 下的 CSV；文件名为 `*_zh.csv`，表头和业务标签已经是中文。需要和代码/英文文档对应时，再用 `../report/tables/` 的英文标准表。

常用中文文件：

- `overview_kpis_zh.csv`：KPI 卡片
- `monthly_kpis_zh.csv`：月度趋势
- `category_kpis_zh.csv` / `category_monthly_zh.csv`：品类
- `state_kpis_zh.csv` / `state_monthly_zh.csv`：地域
- `seller_kpis_zh.csv` / `seller_pareto_zh.csv`：卖家
- `product_kpis_zh.csv` / `top_products_zh.csv`：商品
- `payment_type_kpis_zh.csv` / `installment_distribution_zh.csv`：支付
- `review_distribution_zh.csv` / `review_by_delivery_zh.csv`：评论
- `delivery_distribution_zh.csv` / `delivery_delay_distribution_zh.csv`：履约
- `rfm_segment_summary_zh.csv` / `rfm_score_matrix_zh.csv`：客户
- `cohort_retention_wide_zh.csv`：cohort 热力图

也可以直接使用 `../report/Olist_analysis_tables_zh.xlsx`，28 个工作表已中文化。

## 推荐页面

1. **经营总览**：6 个 KPI + 月度 GMV/订单 + 品类 Top 10 + 州份地图。
2. **品类商品**：品类排名/树图/散点 + 商品 Top 20。
3. **履约体验**：送达时长分布、延迟结构、州份迟到率、评论与准时性。
4. **客户增长**：RFM 客群、cohort 留存、复购结构、支付方式。
5. **卖家**：帕累托 + 头部卖家表。

详细字段和操作见 [`../report/analysis_guide.md`](../report/analysis_guide.md)。

## 连接注意

- CSV 编码是 **UTF-8 with BOM**；Power BI / Tableau / Excel 选 `65001`。
- 比例列是 0–1 小数，显示为百分比，不要再乘 100。
- 中文表的月份列叫 `月份`（值仍是 `YYYY-MM`），英文表叫 `month`；做时间轴时转换成日期（`YYYY-MM-01`）。
- 中文表的有序类别已经改成“0-3天 / 迟到1-3天”等中文标签，仍然要设置自定义排序，不要按字母排序。
- 巴西城市名、ID、日期和文件名保留原值；这是为了关联和排查，不是漏翻译。
- 不要手改 CSV；重新运行 `python src/run_analysis.py` 后，在 BI 里刷新数据源即可。

## 建议的关系

如果要把多张表放进同一个模型：

- `monthly_kpis[month]` ↔ `category_monthly[month]` / `state_monthly[month]`
- `category_kpis[category]` ↔ `category_monthly[category]` / `product_kpis[category]`
- `state_kpis[state]` ↔ `state_monthly[state]`
- `seller_kpis[seller_id]` ↔ `data/processed/order_seller.csv[seller_id]`
- `product_kpis[product_id]` ↔ `data/processed/items_enriched.csv[product_id]`
- `customer_rfm[customer_unique_id]` 可用于客户明细下钻（注意粒度）。

跨表拼接前先确认粒度：**订单数在品类/卖家/商品维度可能重复计数，收入可加**。具体解释见 `report/analysis_guide.md` 的「口径」部分。

中文表的关系列名示例：`月份`、`品类`、`州`、`卖家ID`、`商品ID`、`客户唯一ID`；含义与上表一一对应。