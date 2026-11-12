"""End-to-end command-line pipeline for the Olist analysis.

Usage (from the project root)::

    python src/run_analysis.py
    python src/run_analysis.py --raw-dir Brazilian-Data/raw
    python -m src.run_analysis --no-excel

The script writes chart-ready CSV tables to ``report/tables``, analysis-ready
detail tables to ``data/processed``, and a multi-sheet Excel workbook to
``report``.  It also writes Chinese display copies to ``report/tables_zh``,
``data/processed_zh`` and ``Olist_analysis_tables_zh.xlsx``.  It does not create
any charts.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Support both ``python -m src.run_analysis`` and ``python src/run_analysis.py``.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.config import (
    ANALYSIS_END,
    ANALYSIS_START,
    PROCESSED_DIR,
    PROCESSED_ZH_DIR,
    REPORT_DIR,
    TABLE_DIR,
    TABLE_ZH_DIR,
    ensure_output_dirs,
    resolve_raw_dir,
)
from src.data_loader import read_tables
from src.localize_zh import (
    CATEGORY_ZH,
    EXCEL_SHEETS_ZH,
    RFM_SEGMENT_ZH,
    STATE_ZH,
    localize_table,
)
from src.metrics import build_all_metrics
from src.prepare import prepare_all
from src.quality import build_quality_report, build_raw_file_profile

logger = logging.getLogger("olist.analysis")

# Tables included in the Excel workbook.  Large detail tables stay CSV-only so
# Excel remains responsive for non-technical users.
EXCEL_TABLES = [
    ("monthly_kpis", "monthly"),
    ("order_status_summary", "order_status"),
    ("category_kpis", "category"),
    ("category_monthly", "category_monthly"),
    ("state_kpis", "state"),
    ("state_monthly", "state_monthly"),
    ("seller_kpis", "seller"),
    ("seller_pareto", "seller_pareto"),
    ("top_products", "top_products"),
    ("payment_type_kpis", "payment_type"),
    ("installment_distribution", "installments"),
    ("payment_reconciliation", "payment_reconciliation"),
    ("review_distribution", "review_dist"),
    ("review_monthly", "review_monthly"),
    ("review_by_delivery", "review_delivery"),
    ("review_by_delay_bucket", "review_delay"),
    ("delivery_distribution", "delivery_days"),
    ("delivery_delay_distribution", "delivery_delay"),
    ("order_value_distribution", "order_value"),
    ("rfm_segment_summary", "rfm_segments"),
    ("rfm_score_matrix", "rfm_matrix"),
    ("customer_repeat_summary", "repeat_summary"),
    ("cohort_retention", "cohort_long"),
    ("cohort_retention_wide", "cohort_wide"),
    ("data_quality_report", "quality"),
    ("raw_file_profile", "raw_profile"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build clean Olist analysis tables and chart-ready aggregates."
    )
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=None,
        help="Folder with the olist_* CSV files. Defaults to data/raw or Brazilian-Data/raw.",
    )
    parser.add_argument(
        "--no-excel",
        action="store_true",
        help="Skip the multi-sheet Excel workbook.",
    )
    parser.add_argument(
        "--no-zh",
        action="store_true",
        help="Skip the Chinese display copies (tables_zh / processed_zh / _zh.xlsx).",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
    )
    return parser.parse_args()


def configure_logging(level: str) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = REPORT_DIR / "analysis_run.log"
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_path, mode="w", encoding="utf-8"),
    ]
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        handlers=handlers,
        force=True,
    )


def _write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(
        path,
        index=False,
        encoding="utf-8-sig",
        date_format="%Y-%m-%d %H:%M:%S",
        na_rep="",
    )


def write_detail_tables(data, tables: dict[str, pd.DataFrame]) -> dict[str, dict]:
    """Persist large, analysis-ready tables for custom drill-downs."""

    detail_tables = {
        "orders_master": data.orders_master,
        "items_enriched": data.items,
        "order_category": data.order_category,
        "order_seller": data.order_seller,
        "customer_rfm": data.rfm,
        "zip_centroids": data.geo_centroids,
        "reviews_latest": data.reviews_latest,
    }
    manifest: dict[str, dict] = {}
    for name, df in detail_tables.items():
        path = PROCESSED_DIR / f"{name}.csv"
        logger.info("Writing %-20s %8s rows -> %s", name, f"{len(df):,}", path)
        _write_csv(df, path)
        manifest[name] = {
            "path": str(path.relative_to(PROCESSED_DIR.parents[1])),
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
        }
    return manifest


def write_metric_tables(tables: dict[str, pd.DataFrame]) -> dict[str, dict]:
    """Persist all aggregate tables as chart-ready UTF-8 CSV files."""

    manifest: dict[str, dict] = {}
    for name, df in tables.items():
        path = TABLE_DIR / f"{name}.csv"
        logger.info("Writing metric %-28s %8s rows -> %s", name, f"{len(df):,}", path)
        _write_csv(df, path)
        manifest[name] = {
            "path": str(path.relative_to(REPORT_DIR.parent)),
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "columns_list": list(df.columns),
        }
    return manifest


def write_detail_tables_zh(data) -> dict[str, dict]:
    """Persist Chinese display copies of the large detail tables."""

    detail_tables = {
        "orders_master": data.orders_master,
        "items_enriched": data.items,
        "order_category": data.order_category,
        "order_seller": data.order_seller,
        "customer_rfm": data.rfm,
        "zip_centroids": data.geo_centroids,
        "reviews_latest": data.reviews_latest,
    }
    manifest: dict[str, dict] = {}
    for name, df in detail_tables.items():
        path = PROCESSED_ZH_DIR / f"{name}_zh.csv"
        zh = localize_table(df, name)
        logger.info("Writing ZH detail %-18s %8s rows -> %s", name, f"{len(zh):,}", path)
        _write_csv(zh, path)
        manifest[name] = {
            "path": str(path.relative_to(PROCESSED_ZH_DIR.parents[1])),
            "rows": int(len(zh)),
            "columns": int(len(zh.columns)),
        }
    return manifest


def write_metric_tables_zh(tables: dict[str, pd.DataFrame]) -> dict[str, dict]:
    """Persist Chinese display copies of all chart-ready metric tables."""

    manifest: dict[str, dict] = {}
    for name, df in tables.items():
        path = TABLE_ZH_DIR / f"{name}_zh.csv"
        zh = localize_table(df, name)
        logger.info("Writing ZH metric %-26s %8s rows -> %s", name, f"{len(zh):,}", path)
        _write_csv(zh, path)
        manifest[name] = {
            "path": str(path.relative_to(REPORT_DIR.parent)),
            "rows": int(len(zh)),
            "columns": int(len(zh.columns)),
            "columns_list": list(zh.columns),
        }
    return manifest


def _excel_column_format_zh(column: str):
    """Infer number formats from the Chinese display header."""

    name = column
    if any(token in name for token in ("率", "占比", "覆盖", "份额")):
        return "percent"
    if any(
        token in name
        for token in ("金额", "GMV", "客单价", "运费", "支付", "收入", "差额", "销售额")
    ):
        return "money"
    if any(token in name for token in ("天数", "评分", "评论分", "P90")):
        return "decimal"
    if any(
        token in name
        for token in (
            "订单",
            "客户",
            "商品",
            "卖家",
            "品类",
            "数量",
            "件数",
            "笔数",
            "行数",
            "列数",
            "人数",
            "条数",
            "评论数",
            "次数",
        )
    ):
        return "integer"
    return "general"


def _excel_column_format(column: str):
    name = column.lower()
    if any(token in name for token in ("rate", "share", "coverage")):
        return "percent"
    if column in {
        "orders",
        "orders_all",
        "orders_valid",
        "orders_delivered",
        "orders_canceled",
        "orders_unavailable",
        "customers",
        "new_customers",
        "repeat_customers",
        "items",
        "units",
        "review_count",
        "comments",
        "late_orders",
        "on_time_orders",
        "payment_rows",
        "cohort_size",
    }:
        return "integer"
    if any(token in name for token in ("value", "gmv", "revenue", "monetary", "freight", "price", "aov", "payment")):
        return "money"
    if "days" in name:
        return "decimal"
    if "score" in name:
        return "decimal"
    if "rank" in name or "period" in name:
        return "integer"
    return "general"


def write_excel(
    path: Path,
    tables: dict[str, pd.DataFrame],
    overview: pd.DataFrame,
    *,
    sheet_map: dict[str, str] | None = None,
    notes: pd.DataFrame | None = None,
    format_func=None,
    overview_headers: tuple[str, str] = ("metric", "value"),
    notes_sheet: str = "README",
    overview_sheet: str = "overview",
) -> None:
    """Write a formatted workbook with the main dashboard tables.

    ``sheet_map``/``notes``/``format_func`` allow the same writer to produce
    the English canonical workbook and the Chinese display workbook.
    """

    sheet_map = sheet_map or {}
    format_func = format_func or _excel_column_format
    overview_long = overview.T.reset_index()
    overview_long.columns = list(overview_headers)

    if notes is None:
        notes = pd.DataFrame(
            {
                "项目": [
                    "数据范围",
                    "收入口径",
                    "有效订单",
                    "评论口径",
                    "图表使用",
                    "说明文档",
                ],
                "说明": [
                    f"{ANALYSIS_START.date()} 至 {ANALYSIS_END.date()}（20 个自然月；首月从 1 月 5 日开始）",
                    "gmv = 商品金额；gross_order_value = 商品金额 + 运费；payment_value = 实际支付",
                    "排除 canceled、unavailable 以及没有商品明细的订单",
                    "一个订单多条评论时取最新一条；review_count / review_score_mean 保留透明度",
                    "本工作簿只有聚合表，没有图表；图表可在 BI 或 notebook 中基于这些表生成",
                    "report/analysis_guide.md；字段定义和推荐图表均在其中",
                ],
            }
        )

    with pd.ExcelWriter(path, engine="xlsxwriter", datetime_format="yyyy-mm-dd hh:mm:ss") as writer:
        workbook = writer.book
        header_format = workbook.add_format(
            {
                "bold": True,
                "font_color": "#FFFFFF",
                "bg_color": "#1F4E79",
                "border": 0,
                "valign": "vcenter",
            }
        )
        formats = {
            "percent": workbook.add_format({"num_format": "0.00%"}),
            "integer": workbook.add_format({"num_format": "#,##0"}),
            "money": workbook.add_format({"num_format": "#,##0.00"}),
            "decimal": workbook.add_format({"num_format": "0.00"}),
            "general": workbook.add_format({}),
        }

        # A short read-me sheet avoids ambiguity about revenue and scope.
        notes.to_excel(writer, sheet_name=notes_sheet, index=False)
        ws = writer.sheets[notes_sheet]
        ws.set_column(0, 0, 18)
        ws.set_column(1, 1, 100)
        ws.freeze_panes(1, 0)
        for col_num, value in enumerate(notes.columns):
            ws.write(0, col_num, value, header_format)

        overview_long.to_excel(writer, sheet_name=overview_sheet, index=False)
        ws = writer.sheets[overview_sheet]
        ws.set_column(0, 0, 38)
        ws.set_column(1, 1, 28)
        ws.freeze_panes(1, 0)
        for col_num, value in enumerate(overview_long.columns):
            ws.write(0, col_num, value, header_format)

        for table_name, default_sheet in EXCEL_TABLES:
            sheet_name = sheet_map.get(table_name, default_sheet)
            df = tables.get(table_name)
            if df is None or df.empty:
                continue
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            worksheet = writer.sheets[sheet_name]
            worksheet.freeze_panes(1, 0)
            worksheet.set_row(0, 24)
            worksheet.autofilter(0, 0, len(df), max(len(df.columns) - 1, 0))
            for col_num, column in enumerate(df.columns):
                if len(df):
                    sample = df[column].head(250).astype("string").fillna("")
                    width = max(len(str(column)), sample.str.len().max() or 0) + 2
                else:
                    width = len(str(column)) + 2
                width = min(max(width, 10), 42)
                kind = format_func(column)
                worksheet.set_column(
                    col_num, col_num, width, formats[kind]
                )
                worksheet.write(0, col_num, column, header_format)

    logger.info("Wrote Excel workbook: %s", path)


def write_excel_zh(path: Path, tables_zh: dict[str, pd.DataFrame]) -> None:
    """Write the Chinese display workbook (Chinese sheets and headers)."""

    notes = pd.DataFrame(
        {
            "项目": [
                "数据范围",
                "收入口径",
                "有效订单",
                "评论口径",
                "中文显示",
                "图表使用",
                "说明文档",
            ],
            "说明": [
                f"{ANALYSIS_START.date()} 至 {ANALYSIS_END.date()}（20 个自然月；首月从 1 月 5 日开始）",
                "商品GMV = 商品金额；含运费订单总额 = 商品金额 + 运费；支付金额 = 实际支付",
                "排除已取消、不可用以及没有商品明细的订单",
                "一个订单多条评论时取最新一条；评论数和评论分均值保留原始信息",
                "表头、订单状态、支付方式、州、品类、RFM 客群和区间标签已转为中文；ID、日期、城市和文件名保留原值",
                "本工作簿没有图表；图表可直接使用 report/tables_zh/ 的中文底表",
                "report/analysis_guide.md 与 report/analysis_summary.md",
            ],
        }
    )
    write_excel(
        path,
        tables_zh,
        tables_zh["overview_kpis"],
        sheet_map=EXCEL_SHEETS_ZH,
        notes=notes,
        format_func=_excel_column_format_zh,
        overview_headers=("指标", "数值"),
        notes_sheet="说明",
        overview_sheet="总览",
    )


def _money(value: float) -> str:
    return f"R$ {value:,.0f}"


def _pct(value: float) -> str:
    return f"{value:.1%}" if pd.notna(value) else "n/a"


def _number(value: float) -> str:
    return f"{value:,.2f}" if pd.notna(value) else "n/a"


def build_summary_markdown(
    tables: dict[str, pd.DataFrame],
    raw_dir: Path,
    generated_at: datetime,
) -> str:
    """Create a human-readable snapshot; it contains findings, not charts."""

    overview = tables["overview_kpis"].iloc[0]
    monthly = tables["monthly_kpis"]
    category = tables["category_kpis"]
    state = tables["state_kpis"]
    payment = tables["payment_type_kpis"]
    segment = tables["rfm_segment_summary"]
    review_delivery = tables["review_by_delivery"]
    delivery = tables["delivery_distribution"]
    pareto = tables["seller_pareto"]

    peak_month = monthly.loc[monthly["gmv"].idxmax()]
    top_categories = category.head(5)
    top_states = state.head(5)
    top_category_share = top_categories["gmv_share"].head(3).sum()
    credit_card = payment.loc[payment["payment_type"].eq("credit_card")]
    credit_card_share = (
        credit_card["payment_value_share"].iloc[0] if len(credit_card) else float("nan")
    )
    top_segment = segment.iloc[0]
    late_review = review_delivery.loc[
        review_delivery["delivery_status"].eq("Late")
    ]
    ontime_review = review_delivery.loc[
        review_delivery["delivery_status"].eq("On time")
    ]
    slow_bucket = delivery.loc[delivery["delivery_days_bucket"].eq("31-60")]
    pareto_10 = pareto.loc[pareto["top_n_sellers"].eq(10)]

    lines = [
        "# Olist 电商数据分析摘要",
        "",
        f"> 自动生成于 {generated_at:%Y-%m-%d %H:%M}；原始数据目录：`{raw_dir}`。",
        "> 本文件只给出分析结论和口径，不包含图表；中文图表底表见 `report/tables_zh/`，英文标准表见 `report/tables/`。",
        "",
        "## 一、分析范围",
        "",
        f"- **时间范围**：{overview['analysis_start']} 至 {overview['analysis_end']}（20 个自然月；首月从 1 月 5 日开始）。",
        "- **排除**：2016 年样本、2018-09/10 不完整月份、`canceled` / `unavailable` 订单。",
        "- **收入主口径**：`gmv` 为商品金额，`gross_order_value` 为商品金额 + 运费；`payment_value` 为实际支付，仅用于对账。",
        "",
        "## 二、核心指标",
        "",
        "| 指标 | 数值 |",
        "|---|---:|",
        f"| 有效订单 | {int(overview['orders_valid']):,} |",
        f"| 商品 GMV | {_money(overview['gmv'])} |",
        f"| 含运费订单总额 | {_money(overview['gross_order_value'])} |",
        f"| 客单价 AOV | {_money(overview['aov'])} |",
        f"| 独立客户 | {int(overview['customers_unique']):,} |",
        f"| 复购客户占比 | {_pct(overview['repeat_customer_rate'])} |",
        f"| 平均评论分 | {_number(overview['avg_review_score'])} / 5 |",
        f"| 平均送达天数 | {_number(overview['avg_delivery_days'])} 天 |",
        f"| 迟到订单占比 | {_pct(overview['late_rate'])} |",
        f"| 取消/不可用率 | {_pct(overview['cancel_rate'])} |",
        "",
        "## 三、关键发现",
        "",
        f"1. **规模与峰值**：分析期有效订单 {int(overview['orders_valid']):,} 单、GMV {_money(overview['gmv'])}；"
        f"GMV 最高的月份是 **{peak_month['month']}**（{_money(peak_month['gmv'])}，{int(peak_month['orders_valid']):,} 单）。",
        f"2. **品类集中度**：前三品类贡献 **{_pct(top_category_share)}** 的 GMV；"
        f"第一是 **{CATEGORY_ZH.get(top_categories.iloc[0]['category'], top_categories.iloc[0]['category'])}**"
        f"（{_money(top_categories.iloc[0]['gmv'])}，{_pct(top_categories.iloc[0]['gmv_share'])}）。",
        f"3. **地域集中度**：**{STATE_ZH.get(top_states.iloc[0]['state'], top_states.iloc[0]['state'])}** 占 GMV 的 "
        f"**{_pct(top_states.iloc[0]['gmv_share'])}**，前五州合计 "
        f"**{_pct(top_states['gmv_share'].sum())}**；跨州物流是体验差异的重要来源。",
        f"4. **物流体验**：整体迟到率 **{_pct(overview['late_rate'])}**；"
        f"31–60 天送达的订单迟到率高达 **{_pct(slow_bucket['late_rate'].iloc[0]) if len(slow_bucket) else 'n/a'}**。",
        f"5. **评论与时效**：迟到订单平均评分 "
        f"**{_number(late_review['avg_review_score'].iloc[0]) if len(late_review) else 'n/a'}**，"
        f"准时订单 **{_number(ontime_review['avg_review_score'].iloc[0]) if len(ontime_review) else 'n/a'}**；"
        "配送时效是差评的最强相关因素之一（相关不等于因果）。",
        f"6. **支付结构**：信用卡占支付金额 **{_pct(credit_card_share)}**；"
        "分期订单主要集中在信用卡，适合单独做分期段位分析。",
        f"7. **客户结构**：复购率仅 **{_pct(overview['repeat_customer_rate'])}**，"
        f"RFM 中客户数最多的分层是 **{RFM_SEGMENT_ZH.get(top_segment['rfm_segment'], top_segment['rfm_segment'])}**"
        f"（{int(top_segment['customers']):,} 人）；"
        "增长重点应放在首购转化与二次购买，而不是只做高价值客户运营。",
        f"8. **卖家集中度**：前 10 个卖家贡献 **{_pct(pareto_10['gmv_share'].iloc[0]) if len(pareto_10) else 'n/a'}** 的 GMV；"
        "长尾卖家数量多，适合用帕累托图观察头部依赖。",
        "",
        "## 四、口径与注意事项",
        "",
        "- **客户主键**：订单表 `customer_id` 是订单级标识；客户分析使用 `customer_unique_id`，否则复购率会被低估。",
        "- **评论重复**：551 个订单有多条评论；订单级 `review_score` 取最新一条，另外保留 `review_score_mean` 和 `review_count`。",
        "- **多品类/多卖家订单**：品类和卖家表按 order-category / order-seller 粒度统计，收入可加，但订单数会在多个维度重复计数。",
        "- **支付差额**：约 0.4% 订单的支付总额与商品+运费不一致，可能来自优惠券、分摊或舍入；不要为了对齐而强行改收入。",
        "- **地理坐标**：每个 ZIP 取巴西境内经纬度中位数；地图只适合看相对分布，不适合精确地址。",
        "",
        "## 五、下一步",
        "",
        "1. 用 `report/tables_zh/monthly_kpis_zh.csv` 做月度趋势和 KPI 卡片。",
        "2. 用 `category_kpis_zh.csv` / `state_kpis_zh.csv` 做品类与地域对比。",
        "3. 用 `review_by_delivery_zh.csv`、`delivery_distribution_zh.csv` 做体验专题。",
        "4. 用 `rfm_segment_summary_zh.csv`、`cohort_retention_wide_zh.csv` 做客户运营专题。",
        "5. 中文表头字段和推荐图形见 `report/analysis_guide.md`；英文标准表继续用于代码关联。",
        "",
    ]
    return "\n".join(lines)


def write_manifest(
    path: Path,
    raw_dir: Path,
    detail_manifest: dict[str, dict],
    metric_manifest: dict[str, dict],
    generated_at: datetime,
    excel_path: Path | None,
    zh_detail_manifest: dict[str, dict] | None = None,
    zh_metric_manifest: dict[str, dict] | None = None,
    zh_excel_path: Path | None = None,
) -> None:
    payload = {
        "project": "Olist e-commerce analysis",
        "generated_at": generated_at.isoformat(timespec="seconds"),
        "raw_dir": str(raw_dir),
        "analysis_window": {
            "start": ANALYSIS_START.isoformat(),
            "end": ANALYSIS_END.isoformat(),
            "timezone": "Asia/Shanghai",
        },
        "detail_tables": detail_manifest,
        "metric_tables": metric_manifest,
        "summary": str((REPORT_DIR / "analysis_summary.md").relative_to(REPORT_DIR.parent)),
    }
    if excel_path is not None and excel_path.exists():
        payload["excel"] = str(excel_path.relative_to(REPORT_DIR.parent))
    if zh_detail_manifest is not None:
        payload["zh_detail_tables"] = zh_detail_manifest
    if zh_metric_manifest is not None:
        payload["zh_metric_tables"] = zh_metric_manifest
    if zh_excel_path is not None and zh_excel_path.exists():
        payload["zh_excel"] = str(zh_excel_path.relative_to(REPORT_DIR.parent))
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    configure_logging(args.log_level)
    ensure_output_dirs()
    generated_at = datetime.now()

    raw_dir = resolve_raw_dir(args.raw_dir)
    logger.info("Project root: %s", Path(__file__).resolve().parents[1])
    logger.info("Raw data: %s", raw_dir)
    logger.info("Analysis window: %s -> %s", ANALYSIS_START.date(), ANALYSIS_END.date())

    raw = read_tables(raw_dir)
    data = prepare_all(raw)
    logger.info(
        "Prepared: orders=%s, items=%s, customers(RFM)=%s, categories=%s",
        f"{len(data.orders_master):,}",
        f"{len(data.items):,}",
        f"{len(data.rfm):,}",
        f"{data.items['product_category_label'].nunique():,}",
    )

    tables = build_all_metrics(data)
    tables["data_quality_report"] = build_quality_report(raw, data)
    tables["raw_file_profile"] = build_raw_file_profile(raw_dir, raw)

    detail_manifest = write_detail_tables(data, tables)
    metric_manifest = write_metric_tables(tables)

    zh_detail_manifest: dict[str, dict] | None = None
    zh_metric_manifest: dict[str, dict] | None = None
    zh_excel_path: Path | None = None
    tables_zh: dict[str, pd.DataFrame] | None = None
    if not args.no_zh:
        logger.info("Building Chinese display copies")
        zh_detail_manifest = write_detail_tables_zh(data)
        zh_metric_manifest = write_metric_tables_zh(tables)
        tables_zh = {
            name: localize_table(df, name) for name, df in tables.items()
        }

    summary = build_summary_markdown(tables, raw_dir, generated_at)
    summary_path = REPORT_DIR / "analysis_summary.md"
    summary_path.write_text(summary, encoding="utf-8")
    logger.info("Wrote analysis summary: %s", summary_path)

    if not args.no_excel:
        excel_path = REPORT_DIR / "Olist_analysis_tables.xlsx"
        try:
            write_excel(excel_path, tables, tables["overview_kpis"])
        except Exception:
            logger.exception("Excel export failed; CSV outputs are still available")
            raise

        if not args.no_zh:
            zh_excel_path = REPORT_DIR / "Olist_analysis_tables_zh.xlsx"
            try:
                write_excel_zh(zh_excel_path, tables_zh)
            except Exception:
                logger.exception(
                    "Chinese Excel export failed; Chinese CSV outputs are still available"
                )
                raise
    else:
        excel_path = None

    write_manifest(
        REPORT_DIR / "run_manifest.json",
        raw_dir,
        detail_manifest,
        metric_manifest,
        generated_at,
        excel_path,
        zh_detail_manifest,
        zh_metric_manifest,
        zh_excel_path,
    )
    logger.info("Done. Start with report/analysis_guide.md and report/analysis_summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())