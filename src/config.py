"""Project-wide configuration and shared constants.

The project deliberately keeps the raw files where the user received them
(``Brazilian-Data/raw``) while also supporting the conventional ``data/raw``
layout.  Every output path is derived from the project root, so the pipeline
can be moved to another folder without editing hard-coded absolute paths.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw"
LEGACY_RAW_DIR = PROJECT_ROOT / "Brazilian-Data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_ZH_DIR = PROJECT_ROOT / "data" / "processed_zh"
REPORT_DIR = PROJECT_ROOT / "report"
TABLE_DIR = REPORT_DIR / "tables"
TABLE_ZH_DIR = REPORT_DIR / "tables_zh"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"

# ---------------------------------------------------------------------------
# Analysis scope
# ---------------------------------------------------------------------------
# 2016 is incomplete and 2018-09/2018-10 contain only a handful of orders.
# Restricting the analysis to full calendar months keeps month-over-month
# comparisons and cohort retention from being distorted by partial periods.
ANALYSIS_START = pd.Timestamp("2017-01-01 00:00:00")
ANALYSIS_END = pd.Timestamp("2018-08-31 23:59:59")
SNAPSHOT_TS = pd.Timestamp("2018-09-01 00:00:00")

# ---------------------------------------------------------------------------
# Source files and expected columns
# ---------------------------------------------------------------------------
FILENAMES = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

EXPECTED_COLUMNS = {
    "orders": [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ],
    "payments": [
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    ],
    "reviews": [
        "review_id",
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
    ],
    "customers": [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ],
    "products": [
        "product_id",
        "product_category_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ],
    "sellers": [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state",
    ],
    "geolocation": [
        "geolocation_zip_code_prefix",
        "geolocation_lat",
        "geolocation_lng",
        "geolocation_city",
        "geolocation_state",
    ],
    "category_translation": [
        "product_category_name",
        "product_category_name_english",
    ],
}

DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}

# CSV identifiers must stay strings: leading zeros are meaningful for ZIP
# prefixes, and hashes must never be coerced to numbers.
STRING_COLUMNS = {
    "orders": ["order_id", "customer_id", "order_status"],
    "order_items": ["order_id", "product_id", "seller_id"],
    "payments": ["order_id", "payment_type"],
    "reviews": ["review_id", "order_id"],
    "customers": [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ],
    "products": ["product_id", "product_category_name"],
    "sellers": [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state",
    ],
    "geolocation": [
        "geolocation_zip_code_prefix",
        "geolocation_city",
        "geolocation_state",
    ],
    "category_translation": [
        "product_category_name",
        "product_category_name_english",
    ],
}

# Brazil bounding box (generous) used to remove obviously wrong coordinates.
BRAZIL_LAT_RANGE = (-35.0, 6.0)
BRAZIL_LNG_RANGE = (-75.0, -33.0)

# Order statuses that are not realised demand.
INVALID_SALE_STATUSES = {"canceled", "unavailable"}

# ---------------------------------------------------------------------------
# Presentation constants
# ---------------------------------------------------------------------------
ORDER_VALUE_BINS = [0, 50, 100, 200, 500, 1000, float("inf")]
ORDER_VALUE_LABELS = [
    "0-50",
    "50-100",
    "100-200",
    "200-500",
    "500-1000",
    "1000+",
]

DELIVERY_DAY_BINS = [-0.001, 3, 7, 14, 21, 30, 60, float("inf")]
DELIVERY_DAY_LABELS = ["0-3", "4-7", "8-14", "15-21", "22-30", "31-60", "60+"]

DELAY_BINS = [float("-inf"), 0, 3, 7, 14, float("inf")]
DELAY_LABELS = [
    "On time or early",
    "1-3 days late",
    "4-7 days late",
    "8-14 days late",
    "15+ days late",
]

INSTALLMENT_BINS = [-0.001, 0, 1, 3, 6, 12, float("inf")]
INSTALLMENT_LABELS = ["0", "1", "2-3", "4-6", "7-12", "13+"]

# English segment names are used as keys; Chinese labels are provided for
# dashboards aimed at Chinese-speaking stakeholders.
RFM_SEGMENT_CN = {
    "Champions": "冠军客户",
    "Loyal": "忠诚客户",
    "Potential Loyalist": "潜力客户",
    "New": "新客户",
    "Need Attention": "需关注",
    "At Risk": "流失风险",
    "Hibernating": "沉睡客户",
    "Others": "其他",
}


def resolve_raw_dir(raw_dir: str | Path | None = None) -> Path:
    """Return the first existing raw-data directory.

    Priority: explicit CLI argument, ``data/raw``, then the original
    ``Brazilian-Data/raw`` folder.
    """

    candidates: list[Path] = []
    if raw_dir is not None:
        candidate = Path(raw_dir).expanduser()
        candidates.append(candidate if candidate.is_absolute() else PROJECT_ROOT / candidate)
    candidates.extend([DEFAULT_RAW_DIR, LEGACY_RAW_DIR])

    for candidate in candidates:
        if (candidate / FILENAMES["orders"]).exists():
            return candidate.resolve()

    checked = "\n".join(f"  - {path}" for path in candidates)
    raise FileNotFoundError(
        "Could not find the Olist raw CSV files. Checked:\n"
        f"{checked}\n"
        "Pass --raw-dir <folder containing olist_orders_dataset.csv>."
    )


def ensure_output_dirs() -> None:
    """Create all output directories used by the pipeline."""

    for path in (
        PROCESSED_DIR,
        PROCESSED_ZH_DIR,
        REPORT_DIR,
        TABLE_DIR,
        TABLE_ZH_DIR,
        DASHBOARD_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)