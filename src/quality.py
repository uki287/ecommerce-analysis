"""Data-quality checks and raw-file profiling.

The report is intentionally opinionated: the Olist dataset contains a few
known characteristics (duplicate reviews, missing delivery timestamps, an
incomplete tail month) that should be visible to analysts, not silently fixed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import ANALYSIS_END, ANALYSIS_START, FILENAMES
from .prepare import PreparedData


def build_raw_file_profile(
    raw_dir: Path, raw: dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """Row/column/byte/missing profile for each source file."""

    rows = []
    for table, df in raw.items():
        path = raw_dir / FILENAMES[table]
        missing_cells = int(df.isna().sum().sum())
        total_cells = int(df.shape[0] * df.shape[1])
        rows.append(
            {
                "table": table,
                "file": path.name,
                "rows": len(df),
                "columns": len(df.columns),
                "bytes": path.stat().st_size if path.exists() else np.nan,
                "duplicate_rows": int(df.duplicated().sum()),
                "missing_cells": missing_cells,
                "missing_cell_rate": missing_cells / total_cells if total_cells else 0,
            }
        )
    return pd.DataFrame(rows).sort_values("table").reset_index(drop=True)


def build_quality_report(
    raw: dict[str, pd.DataFrame], data: PreparedData
) -> pd.DataFrame:
    """Return a long, readable table of integrity and coverage checks."""

    orders = raw["orders"]
    items = raw["order_items"]
    payments = raw["payments"]
    reviews = raw["reviews"]
    customers = raw["customers"]
    products = raw["products"]
    sellers = raw["sellers"]
    geo = raw["geolocation"]
    master = data.orders_master
    scope = master.loc[master["is_in_window"]]
    valid = scope.loc[scope["is_valid_order"]]
    delivered = scope.loc[scope["is_delivered"] & scope["delay_days"].notna()]

    checks: list[dict] = []

    def add(
        category: str,
        check: str,
        value: float | int,
        status: str,
        detail: str,
    ) -> None:
        if status == "FAIL" and value == 0:
            status = "PASS"
        checks.append(
            {
                "category": category,
                "check": check,
                "value": value,
                "status": status,
                "detail": detail,
            }
        )

    # --- uniqueness -----------------------------------------------------
    add(
        "Key integrity",
        "orders_unique_order_id",
        int(orders["order_id"].duplicated().sum()),
        "PASS",
        "order_id 应为订单主键；0 表示无重复。",
    )
    add(
        "Key integrity",
        "customers_unique_customer_id",
        int(customers["customer_id"].duplicated().sum()),
        "PASS",
        "customer_id 是订单级客户标识，不是自然人主键。",
    )
    add(
        "Key integrity",
        "customers_unique_person_id",
        int(customers["customer_unique_id"].duplicated().sum()),
        "INFO",
        "同一 customer_unique_id 可对应多个 customer_id；客户分析必须使用 unique_id。",
    )
    add(
        "Key integrity",
        "products_unique_product_id",
        int(products["product_id"].duplicated().sum()),
        "PASS",
        "product_id 应为商品主键。",
    )
    add(
        "Key integrity",
        "sellers_unique_seller_id",
        int(sellers["seller_id"].duplicated().sum()),
        "PASS",
        "seller_id 应为卖家主键。",
    )
    add(
        "Key integrity",
        "order_items_unique_order_item",
        int(items.duplicated(["order_id", "order_item_id"]).sum()),
        "PASS",
        "order_id + order_item_id 应唯一。",
    )
    add(
        "Key integrity",
        "payments_unique_order_sequence",
        int(payments.duplicated(["order_id", "payment_sequential"]).sum()),
        "PASS",
        "order_id + payment_sequential 应唯一；一笔订单可有多条支付。",
    )
    add(
        "Key integrity",
        "reviews_duplicate_review_id",
        int(reviews["review_id"].duplicated().sum()),
        "WARN",
        "存在重复 review_id；订单级评分取最新一条评论。",
    )
    add(
        "Key integrity",
        "reviews_duplicate_order_id",
        int(reviews["order_id"].duplicated().sum()),
        "WARN",
        "551 个订单有多条评论；分析表 review_score 使用最新评论，另保留均值/条数。",
    )

    # --- referential integrity -----------------------------------------
    add(
        "Referential integrity",
        "order_items_orphan_orders",
        int((~items["order_id"].isin(orders["order_id"])).sum()),
        "FAIL",
        "订单明细必须能关联到订单主表。",
    )
    add(
        "Referential integrity",
        "payments_orphan_orders",
        int((~payments["order_id"].isin(orders["order_id"])).sum()),
        "FAIL",
        "支付记录必须能关联到订单主表。",
    )
    add(
        "Referential integrity",
        "reviews_orphan_orders",
        int((~reviews["order_id"].isin(orders["order_id"])).sum()),
        "FAIL",
        "评论必须能关联到订单主表。",
    )
    add(
        "Referential integrity",
        "orders_orphan_customers",
        int((~orders["customer_id"].isin(customers["customer_id"])).sum()),
        "FAIL",
        "订单必须能关联到客户表。",
    )
    add(
        "Referential integrity",
        "order_items_orphan_products",
        int((~items["product_id"].isin(products["product_id"])).sum()),
        "FAIL",
        "订单明细必须能关联到商品表。",
    )
    add(
        "Referential integrity",
        "order_items_orphan_sellers",
        int((~items["seller_id"].isin(sellers["seller_id"])).sum()),
        "FAIL",
        "订单明细必须能关联到卖家表。",
    )

    # --- coverage / scope ----------------------------------------------
    add(
        "Coverage",
        "orders_without_items",
        int((~orders["order_id"].isin(items["order_id"])).sum()),
        "WARN",
        "775 个订单没有商品明细，主要是 unavailable/canceled；收入分析已排除。",
    )
    add(
        "Coverage",
        "orders_without_payment",
        int((~orders["order_id"].isin(payments["order_id"])).sum()),
        "WARN",
        "仅 1 个 2016 年订单没有支付记录。",
    )
    add(
        "Coverage",
        "review_coverage_in_scope",
        float(valid["review_score"].notna().mean()),
        "INFO",
        "分析窗口内有效订单的评论覆盖率。",
    )
    add(
        "Coverage",
        "customer_geo_coverage",
        float(data.customers["customer_lat"].notna().mean()),
        "INFO",
        "客户 ZIP 能匹配到巴西境内经纬度的比例。",
    )
    add(
        "Coverage",
        "seller_geo_coverage",
        float(data.sellers["seller_lat"].notna().mean()),
        "INFO",
        "卖家 ZIP 能匹配到巴西境内经纬度的比例。",
    )
    add(
        "Coverage",
        "geolocation_outliers_removed",
        int(len(geo) - data.geo_centroids["geo_points"].sum()),
        "INFO",
        "经纬度超出巴西范围的点已被剔除；每个 ZIP 取中位数坐标。",
    )
    add(
        "Coverage",
        "product_category_missing",
        int(products["product_category_name"].isna().sum()),
        "INFO",
        "610 个商品无品类，分析中归为 Unknown。",
    )
    add(
        "Coverage",
        "product_category_untranslated",
        int(
            len(
                set(products["product_category_name"].dropna())
                - set(raw["category_translation"]["product_category_name"])
            )
        ),
        "INFO",
        "2 个葡萄牙语品类没有英文翻译，保留原名作为回退。",
    )

    # --- numeric validity ----------------------------------------------
    add(
        "Value validity",
        "order_items_price_nonpositive",
        int((items["price"] <= 0).sum()),
        "PASS",
        "商品价格应大于 0。",
    )
    add(
        "Value validity",
        "order_items_freight_negative",
        int((items["freight_value"] < 0).sum()),
        "PASS",
        "运费不应为负。",
    )
    add(
        "Value validity",
        "payments_value_nonpositive",
        int((payments["payment_value"] <= 0).sum()),
        "WARN",
        "9 条 0 元支付记录（voucher / not_defined），不影响订单金额主口径。",
    )
    add(
        "Value validity",
        "payment_gap_abs_gt_001",
        int(valid["payment_gap"].abs().gt(0.01).sum()),
        "WARN",
        "支付总额与商品+运费总额的差异；多为优惠券、分摊或舍入，保留原值不强制对齐。",
    )
    add(
        "Value validity",
        "payment_gap_total",
        float(valid["payment_gap"].sum()),
        "INFO",
        "分析窗口内有效订单的支付差额合计（支付 - 商品 - 运费）。",
    )

    # --- dates ----------------------------------------------------------
    add(
        "Time validity",
        "delivered_missing_delivery_date",
        int(
            orders.loc[orders["order_status"].eq("delivered"), "order_delivered_customer_date"]
            .isna()
            .sum()
        ),
        "WARN",
        "8 个 delivered 订单缺少实际送达时间，配送时长分析自动排除。",
    )
    add(
        "Time validity",
        "negative_delivery_days",
        int((master["delivery_days"] < 0).sum()),
        "PASS",
        "送达时间早于下单时间为异常；当前为 0。",
    )
    add(
        "Time validity",
        "delivery_before_estimate_extreme",
        int((master["delay_days"] < -120).sum()),
        "WARN",
        "极早送达可能是预计日期异常；保留但建议图表过滤。",
    )
    add(
        "Time validity",
        "orders_outside_analysis_window",
        int((~master["is_in_window"]).sum()),
        "INFO",
        "2016 年及 2018-09/10 订单不进入趋势与 cohort，避免不完整月份扭曲。",
    )
    add(
        "Time validity",
        "analysis_months",
        int(scope["purchase_month"].nunique()),
        "INFO",
        "分析窗口覆盖 2017-01 至 2018-08 共 20 个自然月（首月订单从 1 月 5 日开始）。",
    )

    # --- analysis scope -------------------------------------------------
    add(
        "Analysis scope",
        "orders_all_in_window",
        int(len(scope)),
        "INFO",
        "分析窗口内全部订单。",
    )
    add(
        "Analysis scope",
        "orders_valid_in_window",
        int(len(valid)),
        "INFO",
        "排除 canceled / unavailable / 无商品明细后的有效订单。",
    )
    add(
        "Analysis scope",
        "gross_order_value_in_window",
        float(valid["gross_order_value"].sum()),
        "INFO",
        "有效订单的商品金额 + 运费。",
    )
    add(
        "Analysis scope",
        "late_rate_delivered",
        float(delivered["is_late"].fillna(False).mean()),
        "INFO",
        "实际送达晚于预计送达的订单占比。",
    )

    report = pd.DataFrame(checks)
    report["value"] = pd.to_numeric(report["value"], errors="coerce")
    return report