# Notebook 说明

- `01_analysis_walkthrough.ipynb`：加载英文标准表，查看关键结果；字段名与 `src/` 代码一致。
- `02_olist_10_charts.ipynb`：**10 种中文图表**，已执行并内嵌图片；同时把 PNG 保存到 `report/figures/`。
- `02_olist_10_charts.py`：同上的脚本版，方便不开 Jupyter 时直接运行。
- 中文图表数据：把路径 `report/tables` 换成 `report/tables_zh`，文件名加 `_zh` 即可，例如：
  - `report/tables/monthly_kpis.csv` → `report/tables_zh/monthly_kpis_zh.csv`
  - `report/tables/category_kpis.csv` → `report/tables_zh/category_kpis_zh.csv`
- 中文明细表：`data/processed_zh/*_zh.csv`。
- 中文 Excel：`report/Olist_analysis_tables_zh.xlsx`。

中文副本只翻译表头和业务标签，ID、日期、城市名保留原值；比例仍是 0–1 小数。