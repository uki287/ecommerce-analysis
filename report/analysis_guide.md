# 图表底表与操作指南

> 这份文档解决三件事：**每张表能画什么图、图上的字段怎么放、哪些口径不能混**。  
> 英文标准表在 `report/tables/`，明细表在 `data/processed/`；中文显示副本在 `report/tables_zh/`、`data/processed_zh/`，中文明细在 `report/Olist_analysis_tables_zh.xlsx`。主分析代码只生成数据表，示例图表在 `notebooks/02_olist_10_charts.ipynb`。
>
> **如果图表要中文显示，优先用 `report/tables_zh/`。** 本文为了和代码对应，字段仍用英文名说明；中文副本的列是一一对应的，例如 `orders_valid` → `有效订单数`、`gmv` → `商品GMV`、`late_rate` → `迟到率`。中文副本已经翻译订单状态、支付方式、州、品类、配送区间、RFM 客群和质量状态；ID、日期、城市名保留原值。
>
> 已经做好的 10 张示例图见 `report/figures/`，对应的可执行 notebook 是 `notebooks/02_olist_10_charts.ipynb`，10 张图的清单见 `report/figures/README.md`。

---

## 一、先记住 6 条口径

1. **时间窗口**：只使用 `2017-01` 至 `2018-08` 的 20 个自然月（首月订单从 1 月 5 日开始）。不要直接把 2016 和 2018-09/10 放进趋势图。
2. **有效订单**：`orders_valid` 已排除 `canceled`、`unavailable` 和无商品明细的订单。订单量、GMV、AOV、复购等经营指标都应以它为准。
3. **收入**：
   - `gmv` = 商品金额（不含运费），用于商品/品类/卖家规模；
   - `gross_order_value` = 商品 + 运费，用于订单总额和 AOV；
   - `payment_value` = 实际支付，只用于支付分析和对账。
4. **比例**：所有 `*_rate`、`*_share`、`*_coverage` 都是 **0–1 小数**。在 Excel/BI 里设置成百分比格式，不要先乘 100。
5. **客户**：客户级分析用 `customer_unique_id`；`customer_id` 是订单级标识，不是人。
6. **分母**：
   - `late_rate` = 迟到订单 / 有实际送达日期的 delivered 订单；
   - `cancel_rate` = (canceled + unavailable) / 全部订单；
   - `review_score` = 有评论订单的平均分（最新一条评论）。

---

## 二、推荐仪表盘结构

### 第 1 页：经营总览

| 组件 | 数据表 | 字段/操作 |
|---|---|---|
| KPI 卡片 ×6 | `overview_kpis` | `orders_valid`、`gmv`、`aov`、`repeat_customer_rate`、`avg_review_score`、`late_rate` |
| 月度 GMV + 订单 | `monthly_kpis` | 柱：`gmv`；线：`orders_valid`（次坐标轴） |
| 品类 Top 10 | `category_kpis` | 横向柱，`category` × `gmv`，按 `gmv` 降序，过滤 `category_rank <= 10` |
| 州份地图/条形 | `state_kpis` | 地图用 `state`；颜色 `late_rate` 或大小 `gmv` |

### 第 2 页：品类与商品

| 组件 | 数据表 | 字段/操作 |
|---|---|---|
| 品类销售排名 | `category_kpis` | `category` × `gmv`，Top 15；可加 `gmv_share` 标签 |
| 品类结构树图 | `category_kpis` | 层级 `category`，值 `gmv`；排除 `Unknown` 或单独标注 |
| 品类月度趋势 | `category_monthly` | x `month`，y `gmv`，颜色 `category`；只选 Top 5–8 品类，避免 74 条线 |
| 品类体验散点 | `category_kpis` | x `gmv`（对数轴可选），y `review_score`，气泡 `orders_valid`，颜色 `late_rate` |
| 商品 Top 20 | `top_products` | 横向柱，`product_id` × `gmv`；标签加 `category` |
| 商品效率散点 | `product_kpis` | x `gmv`，y `review_score`，气泡 `orders_valid`；过滤 `orders_valid >= 30` |

### 第 3 页：履约与体验

| 组件 | 数据表 | 字段/操作 |
|---|---|---|
| 送达时长分布 | `delivery_distribution` | x `delivery_days_bucket`，y `orders`；**必须按自定义顺序排序** |
| 延迟结构 | `delivery_delay_distribution` | x `delay_bucket`，y `orders`；顺序：准时/提前 → 1–3 天 → 4–7 天 → 8–14 天 → 15+ |
| 州份迟到率 | `state_kpis` | 横向柱/地图，`state` × `late_rate`；加 `delivered_with_dates` 作为样本量提示 |
| 评论与准时性 | `review_by_delivery` | 分组柱：`delivery_status` × `avg_review_score`；或 100% 堆叠的 `low_review_rate` |
| 评分分布 | `review_distribution` | 1–5 分柱状图；`review_score` 当作类别，不要只画平均分 |
| 延迟与评分 | `review_by_delay_bucket` | x `delay_bucket`（自定义顺序），y `avg_review_score`；副轴 `low_review_rate` |

### 第 4 页：客户与增长

| 组件 | 数据表 | 字段/操作 |
|---|---|---|
| RFM 客群规模 | `rfm_segment_summary` | 横向柱/树图：`rfm_segment` × `customers`，颜色 `revenue_share` |
| RFM 得分热力图 | `rfm_score_matrix` | 行 `r_score`（5 在上），列 `f_score`，值 `customers` 或 `revenue` |
| 复购结构 | `customer_repeat_summary` | 环形图/柱：`customer_type` × `customers` 或 `revenue` |
|  cohort 留存热力图 | `cohort_retention_wide` | 行 `cohort_month`，列 `period_0…period_19`，值 retention；格式 0.0% |
|  cohort 明细 | `cohort_retention` | 需要 `cohort_size`、`orders`、`gross_value` 时用长表 |
| 支付方式 | `payment_type_kpis` | 环形图：`payment_type` × `payment_value_share`；不要用 `order_share` 画饼图 |
| 分期结构 | `installment_distribution` | 堆叠柱：`installment_bucket` × `payment_rows`，按 `payment_type` 分面 |

### 第 5 页：卖家（可选）

| 组件 | 数据表 | 字段/操作 |
|---|---|---|
| 卖家帕累托 | `seller_kpis` / `seller_pareto` | x `seller_rank`（对数轴可选），y `cumulative_gmv_share`；加 80% 参考线 |
| 头部卖家表 | `seller_kpis` | 过滤 `seller_rank <= 20`，展示 `gmv`、`aov`、`review_score`、`late_rate` |
| 卖家体验散点 | `seller_kpis` | x `gmv`，y `review_score`，气泡 `orders_valid`；过滤 `orders_valid >= 30` |

---

## 三、底表清单与推荐图形

| 文件 | 行数（本次） | 粒度 | 推荐图形 | 关键字段 |
|---|---:|---|---|---|
| `overview_kpis.csv` | 1 | 全期汇总 | KPI 卡片 | 所有指标 |
| `monthly_kpis.csv` | 20 | 月 | 柱线组合 | `month`, `gmv`, `orders_valid`, `aov`, `late_rate` |
| `order_status_summary.csv` | 8 | 状态 | 条形/环形 | `order_status`, `orders`, `order_share` |
| `category_kpis.csv` | 74 | 品类 | 横向柱、树图、散点 | `category`, `gmv`, `aov`, `review_score`, `late_rate` |
| `category_monthly.csv` | 1,246 | 月 × 品类 | 小倍数折线 | `month`, `category`, `gmv` |
| `state_kpis.csv` | 27 | 州 | 地图、条形 | `state`, `gmv`, `late_rate`, `customer_lat/lng` |
| `state_monthly.csv` | 533 | 月 × 州 | 折线/地图动画 | `month`, `state`, `gmv` |
| `seller_kpis.csv` | 3,068 | 卖家 | 帕累托、散点、表 | `seller_rank`, `gmv`, `cumulative_gmv_share`, `late_rate` |
| `seller_pareto.csv` | 9 | Top N | 帕累托摘要 | `top_n_sellers`, `gmv_share` |
| `product_kpis.csv` | 32,787 | 商品 | Top N、散点 | `product_rank`, `gmv`, `review_score`, `late_rate` |
| `top_products.csv` | 100 | Top 100 商品 | 横向柱/表 | 同上 |
| `payment_type_kpis.csv` | 4 | 支付方式 | 环形/柱 | `payment_type`, `payment_value_share` |
| `installment_distribution.csv` | 9 | 支付方式 × 分期段 | 堆叠柱 | `installment_bucket`, `payment_rows` |
| `payment_reconciliation.csv` | 1 | 对账 | KPI | `match_rate`, `total_gap` |
| `review_distribution.csv` | 5 | 评分 | 柱状/百分比堆叠 | `review_score`, `orders`, `share` |
| `review_monthly.csv` | 20 | 月 | 折线 | `month`, `avg_review_score`, `low_review_rate` |
| `review_by_delivery.csv` | 2 | 准时/迟到 | 分组柱 | `delivery_status`, `avg_review_score` |
| `review_by_delay_bucket.csv` | 5 | 延迟段 | 折线/柱 | `delay_bucket`, `avg_review_score` |
| `delivery_distribution.csv` | 7 | 送达时长段 | 直方图 | `delivery_days_bucket`, `orders`, `late_rate` |
| `delivery_delay_distribution.csv` | 5 | 延迟段 | 柱状 | `delay_bucket`, `orders` |
| `order_value_distribution.csv` | 6 | 订单金额段 | 直方图 | `order_value_band`, `orders`, `aov` |
| `rfm_segment_summary.csv` | 6 | RFM 客群 | 横向柱/树图 | `rfm_segment`, `customers`, `revenue_share` |
| `rfm_score_matrix.csv` | 24 | R × F | 热力图 | `r_score`, `f_score`, `customers` |
| `customer_repeat_summary.csv` | 2 | 新客/复购 | 环形/柱 | `customer_type`, `customers`, `revenue` |
| `cohort_retention.csv` | 207 | cohort × 月序 | 长表热力图/折线 | `cohort_month`, `period_number`, `retention_rate` |
| `cohort_retention_wide.csv` | 20 | cohort | 热力图矩阵 | `cohort_month`, `period_0…period_19` |
| `data_quality_report.csv` | 37 | 检查项 | 表 | `status`, `check`, `detail` |
| `raw_file_profile.csv` | 9 | 源文件 | 表 | `table`, `rows`, `missing_cell_rate` |

---

## 四、具体操作细节

### 1. 月度趋势

- 用 `month` 作为 x 轴；它是文本 `YYYY-MM`，在 Power BI 中建议另建 `Date = DATEVALUE([month] & "-01")` 并按日期排序，避免按字母排序。
- 柱：`gmv`；线：`orders_valid`；不要同时放 `gmv` 与 `gross_order_value`，否则两条柱子含义重叠。
- 双轴时明确标注左右轴；AOV 适合单独一张小图，不要和 GMV 共用轴。
- 2017-11 是峰值月（黑五），可以加注释；但不要把峰值当作常态。

### 2. 品类图

- 先过滤 `category_rank <= 15` 再画，74 个品类一次画完不可读。
- 横向柱按 `gmv` 降序；`category` 已经是英文可读标签，`Unknown` 单独用灰色。
- 树图用 `gmv`，不要用 `orders_valid` 做面积；订单数会被多品类订单重复计数。
- 散点图：x `gmv`，y `review_score`，气泡 `orders_valid`，颜色 `late_rate`；加 `orders_valid >= 30` 过滤，避免长尾噪声。
- 品类评论分是订单-品类粒度，一个多品类订单会进入多个品类；不要把它当成「商品级评分」。

### 3. 州份地图

- `state_kpis` 的 `state` 是巴西两字母州代码（SP、RJ、MG…），大多数 BI 工具能直接识别。
- 如果地图识别不了，用 `customer_lat` / `customer_lng` 做散点地图；这两个字段是该州订单客户坐标的均值，只适合看相对位置。
- 颜色建议用 `late_rate`，大小用 `gmv`；同时把 `delivered_with_dates` 放在 tooltip，提醒样本量。
- SP 占 GMV 约 38%，不要用未归一化的地图颜色直接比较绝对量；绝对量看 `gmv`，体验看 `late_rate`。

### 4. 配送时长与延迟

- `delivery_days_bucket`、`delay_bucket`、`order_value_band` 都是**有序类别**。Excel 里用「自定义排序」，Power BI 里建「按列排序」的排序列，Tableau 里手动排序；不要让工具按字母排。
- `delivery_distribution` 的 `orders` 是 delivered 且有时长的订单；`late_rate` 的分母是同一桶的订单。
- 31–60 天桶的迟到率很高（本次 81%），但样本只占 4.4%；做结论时同时展示 `orders` 或 `share`。
- `avg_delay_days` 为负表示「比预计早到」，不是延迟；命名上不要显示成「平均延迟」而不解释。

### 5. 评论

- `review_score` 是 1–5 的类别，不是连续变量；至少画分布，不要只画平均分。
- `review_by_delivery` 是很有说服力的一张图：本次准时订单平均 4.29 分，迟到订单 2.57 分；但这是相关关系，不是因果。
- `review_distribution` 的 `share` 分母是「有评论的订单」，不是全部订单；`review_coverage` 在 `overview_kpis` 里约 99%。
- 一个订单多条评论时已取最新一条；如果要做评论文本分析，用 `data/processed/reviews_latest.csv` 的 `latest_review_comment_message`，并注意 551 个订单有重复评论。

### 6. 支付

- 环形图用 `payment_value_share`（按金额），不要用 `order_share`：一个订单可能同时有 voucher + credit_card，`order_share` 相加会超过 100%。
- 信用卡占支付金额约 78.5%，是绝对主力；`installment_distribution` 里信用卡分期是重点。
- `payment_reconciliation` 的 `match_rate` 约 99.6%；剩余差异主要来自优惠券/分摊/舍入，不建议为了「对齐」而改收入。

### 7. RFM

- `r_score`：5 = 最近买过，1 = 很久没买；`f_score`：1 = 只买 1 次，5 = 6 次及以上；`m_score`：5 = 金额最高。
- `rfm_score_matrix` 只有 24 个有客户的组合，不是完整 25 格；热力图要保留空组合，否则会误读。
- `rfm_segment_summary` 按收入排序，`Hibernating` 可能排第一，因为它包含大量「很久没买但历史上买过一次」的客户；这不是「高价值活跃客群」，看图和命名时要说明。
- 复购率只有约 3.0%，大多数客户只买一次；RFM 的运营重点应是首购转二次购买，而不是只对 Champions 做活动。

### 8. Cohort

- 用 `cohort_retention_wide` 画热力图：行 `cohort_month`，列 `period_0…period_19`，值 retention，格式 0.0%。
- `period_0` 一定是 100%，它是 cohort 基数；真正要看的是 `period_1` 以后。
- 每个 cohort 的可观察期不同（2018-08 只有 period_0），不要横向比较不同 cohort 的「总留存」；只比较同一 period。
- `cohort_size` 在长表 `cohort_retention.csv` 里；热力图的 tooltip 建议带上 cohort 人数，避免小样本误读。
- 本数据复购很低，留存曲线会很平且接近 0；这是数据事实，不是代码把复购算漏了。

### 9. 卖家帕累托

- x 用 `seller_rank`，y 用 `cumulative_gmv_share`；前 10 个卖家约占 13.2% GMV，不是典型的 80/20。
- 卖家数量 3,068，长尾很长；帕累托图可以看「头部依赖度」，但不要用 Top 10 代替整体。
- 卖家评论/时效用 order-seller 粒度；一个订单多卖家时，同一订单会进入多个卖家，订单数会重复计数，收入可加。

### 10. 商品

- 用 `top_products.csv` 画 Top 20，不要直接画 32,787 个商品。
- 商品散点先过滤 `orders_valid >= 30`，否则大量 1 单商品的评分/迟到率是 0 或 1，噪声很大。
- `product_kpis` 是订单-商品粒度优先，迟到率不会超过 100%；仍建议样本量过滤。

---

## 五、在 Excel / Power BI / Tableau 中打开

### Excel

1. `数据` → `从文本/CSV` → 选 `report/tables/*.csv`。
2. 文件原始格式选 `65001: Unicode (UTF-8)`；分隔符逗号；第一行作为标题。
3. 比例列设置为 `0.00%`；金额列 `R$ #,##0.00`；日期列按日期解析。
4. 透视表/透视图直接引用表；不要手工改 CSV，重新运行 `python src/run_analysis.py` 即可刷新。

### Power BI

1. `获取数据` → `文本/CSV` → 编码 `65001`。
2. 将 `month` 转成日期列（`month & "-01"`），或用 `month` 文本加排序表。
3. 把 `overview_kpis` 逆透视成 `指标/值` 做卡片。
4. `state` 地图需要开启形状地图或使用经纬度散点；`customer_lat/lng` 可用。
5. 所有比例的度量值直接显示，不要再乘 100。

### Tableau

1. 连接文本文件，编码 UTF-8；`month` 设为日期。
2. 对 `delivery_days_bucket`、`delay_bucket`、`order_value_band` 建自定义排序。
3. 热力图用 `cohort_retention_wide` 的透视表，列 `period_0…`。
4. 帕累托用 `seller_rank` + `cumulative_gmv_share`，x 轴可设对数。

---

## 六、不能做的分析

- **利润/毛利率**：没有商品成本、平台佣金、退款成本。
- **ROI/ROAS/CAC**：没有广告花费、流量、渠道数据。
- **真实流失**：数据只覆盖到 2018-08；RFM 的「沉睡」是快照定义，不是已确认流失。
- **因果结论**：迟到与差评强相关，但不能直接说「迟到导致差评」；可能有品类、距离、卖家质量等混杂因素。
- **精确地理**：坐标是 ZIP 中位数，不是收货地址；地图只适合看相对分布。
- **跨期货币比较**：金额未做通胀调整；巴西雷亚尔（BRL）跨两年比较要谨慎。

---

## 七、扩展建议

如果后面要补图表或新指标，优先在 `src/metrics.py` 里加聚合函数，不要在 notebook 里重复清洗逻辑。推荐新增：

- 按「首购月 × 品类」的 cohort；
- 按「州 × 品类」的交叉表（注意样本量）；
- 卖家/商品的质量-规模四象限；
- 迟到订单的评论关键词（用 `reviews_latest.csv` 的文本）；
- 支付分期与 AOV 的关系（注意分期是支付方式，不是价格）。

新增后重新运行 `python src/run_analysis.py`，CSV 和 Excel 会自动更新。