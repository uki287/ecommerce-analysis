# Power BI 粘贴包（路线 A）

这个包用于在 **Power BI Desktop 里手工粘贴/插入**，不依赖 PBIP、不需要我远程控制 Power BI。

## 最终形态

- **8 张原生可交互图**：月度、品类、支付、气泡、地图、配送、Cohort、卖家帕累托。
- **2 张静态图兜底**：箱线图、雷达图。Power BI 原生不支持，直接插入 PNG；如果租户允许 AppSource，也可以用自定义视觉对象替代。
- **1 套 DAX 度量值**：复制到 Power BI 的「新建度量值」。
- **1 个主题 JSON**：导入后统一配色/字体。
- **1 份逐图操作配方**：`recipes/10_visuals_step_by_step.md`。

## 目录

```text
pbi_paste_pack/
├─ README.md
├─ field_mapping.csv              # 图号 → 视觉对象 → 表/字段
├─ dax/
│  ├─ 01_core_measures.dax        # KPI 卡片/核心度量
│  ├─ 02_quick_visual_measures.dax# 气泡分组、雷达归一化、Cohort
│  ├─ 03_full_model_measures.dax  # 可选：订单事实表完整版
│  └─ 04_optional_svg_measure.dax # 可选：SVG KPI 卡
├─ theme/
│  └─ olist_theme.json
├─ recipes/
│  └─ 10_visuals_step_by_step.md
└─ png/
   ├─ 01_monthly_gmv_orders.png
   ├─ 02_category_top10.png
   ├─ 03_payment_donut.png
   ├─ 04_category_bubble.png
   ├─ 05_state_bubble_map.png
   ├─ 06_delivery_histogram.png
   ├─ 07_category_boxplot.png
   ├─ 08_cohort_heatmap.png
   ├─ 09_seller_pareto.png
   └─ 10_state_radar.png
```

## 5 分钟接入

1. **确认表已导入**：当前模型至少需要
   `monthly_kpis_zh`、`category_kpis_zh`、`payment_type_kpis_zh`、`state_kpis_zh`、`cohort_retention_zh`。
   还缺 `seller_kpis_zh`、`delivery_distribution_zh` 的话，用「获取数据 → 文本/CSV」补导入。
2. **导入主题**：视图 → 主题 → 浏览主题 → `theme/olist_theme.json`。
3. **粘贴 DAX**：右键任意表 → 新建度量值 → 把 `dax/01_core_measures.dax` 里的度量值逐条粘贴。
4. **按配方做 8 张原生图**：打开 `recipes/10_visuals_step_by_step.md`，从图 1 做到图 10。
5. **插入 2 张 PNG**：图 7 箱线图、图 10 雷达图用「插入 → 图像」。
6. **统一格式**：金额 R$ #,##0.00，比例 0.0%，标题写结论，脚注写数据来源。

## 字段名注意

当前 Power BI 模型里如果 `monthly_kpis_zh` 的月份列叫 **`年月文本`**（截图里是这个名字），
就把配方里的 `月份` 替换成 `年月文本`。DAX 度量值本身不依赖月份列，不需要改。

如果表名被改成了中文别名（例如 `月度KPI`），把 DAX 里的 `'monthly_kpis_zh'` 替换成你的表名。

## 重要边界

- 2 张 PNG **不会联动、不会随切片器变化**，这是为了绕开 Power BI 原生不支持的箱线图/雷达图。
- `04_optional_svg_measure.dax` 只适合做 KPI 卡/迷你图，不能替代原生折线图、条形图、地图。
- 本包没有生成 `.pbix`；它设计成“你粘贴进已有 Power BI 文件”的形态，最稳、不依赖版本适配。
- 如果公司租户允许 AppSource，可以把图 7/10 换成 Box and Whisker / Radar Chart 自定义视觉对象；
  配方里给了可选步骤。

## 推荐顺序

先做图 1（月度）+ 图 2（品类）验证字段是否正确；再做图 8（Cohort）验证长表粒度；
最后做图 5（地图）和图 9（帕累托）。箱线图和雷达图放最后，直接插 PNG 即可。