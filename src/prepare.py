"""Build clean, analysis-ready tables from the raw Olist files.

The functions in this module intentionally keep the raw data immutable.  All
derived frames are returned in memory and can be persisted by
``run_analysis.py`` or explored interactively from a notebook.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import (
    ANALYSIS_END,
    ANALYSIS_START,
    BRAZIL_LAT_RANGE,
    BRAZIL_LNG_RANGE,
    DELAY_BINS,
    DELAY_LABELS,
    DELIVERY_DAY_BINS,
    DELIVERY_DAY_LABELS,
    INSTALLMENT_BINS,
    INSTALLMENT_LABELS,
    INVALID_SALE_STATUSES,
    ORDER_VALUE_BINS,
    ORDER_VALUE_LABELS,
    RFM_SEGMENT_CN,
    SNAPSHOT_TS,
)

logger = logging.getLogger(__name__)


@dataclass
class PreparedData:
    """Container for all derived datasets consumed by the metrics layer."""

    orders_master: pd.DataFrame
    items: pd.DataFrame
    order_category: pd.DataFrame
    order_seller: pd.DataFrame
    customers: pd.DataFrame
    products: pd.DataFrame
    sellers: pd.DataFrame
    payment_rows: pd.DataFrame
    reviews_latest: pd.DataFrame
    reviews_raw: pd.DataFrame
    geo_centroids: pd.DataFrame
    rfm: pd.DataFrame
    cohort: pd.DataFrame
    cohort_wide: pd.DataFrame


# ---------------------------------------------------------------------------
# Dimension tables
# ---------------------------------------------------------------------------
def _pretty_category(value: object) -> str:
    if pd.isna(value):
        return "Unknown"
    text = str(value).replace("_", " ").strip()
    return text.title() if text else "Unknown"


def build_geo_centroids(geolocation: pd.DataFrame) -> pd.DataFrame:
    """Collapse ~1M geolocation rows to one median point per ZIP prefix."""

    lat_min, lat_max = BRAZIL_LAT_RANGE
    lng_min, lng_max = BRAZIL_LNG_RANGE

    geo = geolocation.dropna(
        subset=["geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng"]
    ).copy()
    before = len(geo)
    geo = geo[
        geo["geolocation_lat"].between(lat_min, lat_max)
        & geo["geolocation_lng"].between(lng_min, lng_max)
    ]

    centroids = (
        geo.groupby("geolocation_zip_code_prefix", as_index=False)
        .agg(
            geo_lat=("geolocation_lat", "median"),
            geo_lng=("geolocation_lng", "median"),
            geo_points=("geolocation_lat", "size"),
            geo_state=("geolocation_state", "first"),
        )
        .rename(columns={"geolocation_zip_code_prefix": "zip_code_prefix"})
    )

    logger.info(
        "Geolocation: kept %s/%s rows, %s ZIP centroids (removed %s out-of-Brazil points)",
        f"{len(geo):,}",
        f"{before:,}",
        f"{len(centroids):,}",
        f"{before - len(geo):,}",
    )
    return centroids


def build_products(
    products: pd.DataFrame, translation: pd.DataFrame
) -> pd.DataFrame:
    """Clean product attributes and attach English category labels."""

    prod = products.copy()
    prod = prod.rename(
        columns={
            "product_name_lenght": "product_name_length",
            "product_description_lenght": "product_description_length",
        }
    )

    prod["product_category_name"] = prod["product_category_name"].fillna("unknown")
    prod = prod.merge(
        translation.rename(
            columns={
                "product_category_name_english": "product_category_english"
            }
        ),
        on="product_category_name",
        how="left",
        validate="many_to_one",
    )
    prod["product_category_english"] = prod["product_category_english"].fillna(
        prod["product_category_name"]
    )
    prod["product_category_label"] = prod["product_category_english"].map(
        _pretty_category
    )

    return prod


def build_customers(
    customers: pd.DataFrame, geo_centroids: pd.DataFrame
) -> pd.DataFrame:
    """Attach approximate coordinates to each customer record."""

    cust = customers.copy()
    geo = geo_centroids.rename(
        columns={
            "zip_code_prefix": "customer_zip_code_prefix",
            "geo_lat": "customer_lat",
            "geo_lng": "customer_lng",
            "geo_points": "customer_geo_points",
        }
    )
    cust = cust.merge(
        geo,
        on="customer_zip_code_prefix",
        how="left",
        validate="many_to_one",
    )
    return cust


def build_sellers(sellers: pd.DataFrame, geo_centroids: pd.DataFrame) -> pd.DataFrame:
    """Attach approximate coordinates to each seller record."""

    sel = sellers.copy()
    geo = geo_centroids.rename(
        columns={
            "zip_code_prefix": "seller_zip_code_prefix",
            "geo_lat": "seller_lat",
            "geo_lng": "seller_lng",
            "geo_points": "seller_geo_points",
        }
    )
    sel = sel.merge(
        geo,
        on="seller_zip_code_prefix",
        how="left",
        validate="many_to_one",
    )
    return sel


# ---------------------------------------------------------------------------
# Fact-table aggregations
# ---------------------------------------------------------------------------
def build_reviews(reviews: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return raw reviews plus one latest review row per order.

    A small number of orders have more than one review.  ``review_score`` on
    the order-level table uses the latest review (by creation time, then answer
    time), while the mean and count are retained so the choice is transparent.
    """

    raw = reviews.copy()
    raw["review_has_comment"] = raw["review_comment_message"].notna()

    latest = (
        raw.sort_values(
            [
                "order_id",
                "review_creation_date",
                "review_answer_timestamp",
                "review_id",
            ],
            na_position="first",
        )
        .drop_duplicates("order_id", keep="last")
        .rename(
            columns={
                "review_id": "latest_review_id",
                "review_creation_date": "latest_review_creation_date",
                "review_answer_timestamp": "latest_review_answer_timestamp",
                "review_comment_title": "latest_review_comment_title",
                "review_comment_message": "latest_review_comment_message",
                "review_has_comment": "latest_review_has_comment",
            }
        )
    )

    agg = raw.groupby("order_id", as_index=False).agg(
        review_count=("review_id", "size"),
        review_score_mean=("review_score", "mean"),
        review_comment_count=("review_has_comment", "sum"),
    )
    latest = latest.merge(agg, on="order_id", how="left", validate="one_to_one")
    return raw, latest


def build_payment_rows(
    payments: pd.DataFrame, orders: pd.DataFrame
) -> pd.DataFrame:
    """Attach order status/date fields to the payment rows."""

    order_flags = orders[
        [
            "order_id",
            "order_status",
            "order_purchase_timestamp",
            "order_estimated_delivery_date",
            "order_delivered_customer_date",
        ]
    ].copy()
    pay = payments.merge(order_flags, on="order_id", how="left", validate="many_to_one")
    pay["purchase_month"] = pay["order_purchase_timestamp"].dt.strftime("%Y-%m")
    pay["is_in_window"] = pay["order_purchase_timestamp"].between(
        ANALYSIS_START, ANALYSIS_END
    )
    pay["is_canceled"] = pay["order_status"].eq("canceled")
    pay["is_unavailable"] = pay["order_status"].eq("unavailable")
    pay["is_valid_order"] = ~pay["order_status"].isin(INVALID_SALE_STATUSES)
    pay["installment_bucket"] = pd.cut(
        pay["payment_installments"],
        bins=INSTALLMENT_BINS,
        labels=INSTALLMENT_LABELS,
        include_lowest=True,
    ).astype("string")
    return pay


def _build_item_aggregates(
    items: pd.DataFrame, products: pd.DataFrame
) -> pd.DataFrame:
    item_with_category = items.merge(
        products[["product_id", "product_category_name"]],
        on="product_id",
        how="left",
        validate="many_to_one",
    )
    agg = (
        items.groupby("order_id", as_index=False)
        .agg(
            item_count=("order_item_id", "size"),
            product_count=("product_id", "nunique"),
            seller_count=("seller_id", "nunique"),
            merchandise_value=("price", "sum"),
            freight_value=("freight_value", "sum"),
        )
    )
    category_count = (
        item_with_category.groupby("order_id", as_index=False)
        .agg(category_count=("product_category_name", "nunique"))
    )
    return agg.merge(category_count, on="order_id", how="left", validate="one_to_one")


def build_orders_master(
    orders: pd.DataFrame,
    customers: pd.DataFrame,
    items: pd.DataFrame,
    products: pd.DataFrame,
    payments: pd.DataFrame,
    reviews_latest: pd.DataFrame,
) -> pd.DataFrame:
    """Create the central one-row-per-order analysis table."""

    cust = customers[
        [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
            "customer_lat",
            "customer_lng",
        ]
    ].copy()

    payment_agg = payments.groupby("order_id", as_index=False).agg(
        payment_value=("payment_value", "sum"),
        payment_count=("payment_sequential", "size"),
        payment_method_count=("payment_type", "nunique"),
        payment_installments_max=("payment_installments", "max"),
    )
    payment_types = (
        payments.groupby("order_id")["payment_type"]
        .agg(lambda values: "|".join(sorted(set(values.dropna()))))
        .rename("payment_types")
        .reset_index()
    )
    payment_agg = payment_agg.merge(
        payment_types, on="order_id", how="left", validate="one_to_one"
    )

    primary_payment = (
        payments.sort_values(
            ["order_id", "payment_value", "payment_sequential"],
            ascending=[True, False, True],
        )
        .drop_duplicates("order_id", keep="first")[["order_id", "payment_type"]]
        .rename(columns={"payment_type": "primary_payment_type"})
    )
    payment_agg = payment_agg.merge(
        primary_payment, on="order_id", how="left", validate="one_to_one"
    )

    item_agg = _build_item_aggregates(items, products)
    review_cols = [
        "order_id",
        "review_count",
        "review_score",
        "review_score_mean",
        "review_comment_count",
        "latest_review_has_comment",
    ]

    master = orders.merge(cust, on="customer_id", how="left", validate="many_to_one")
    master = master.merge(item_agg, on="order_id", how="left", validate="one_to_one")
    master = master.merge(payment_agg, on="order_id", how="left", validate="one_to_one")
    master = master.merge(
        reviews_latest[review_cols], on="order_id", how="left", validate="one_to_one"
    )

    for column in (
        "item_count",
        "product_count",
        "seller_count",
        "category_count",
        "merchandise_value",
        "freight_value",
        "payment_value",
        "payment_count",
        "payment_method_count",
    ):
        master[column] = master[column].fillna(0)

    master["payment_installments_max"] = master["payment_installments_max"].fillna(0)
    master["has_items"] = master["item_count"] > 0
    master["merchandise_value"] = master["merchandise_value"].astype(float)
    master["freight_value"] = master["freight_value"].astype(float)
    master["gross_order_value"] = (
        master["merchandise_value"] + master["freight_value"]
    )
    master["payment_gap"] = master["payment_value"] - master["gross_order_value"]

    master["purchase_ts"] = master["order_purchase_timestamp"]
    master["purchase_date"] = master["purchase_ts"].dt.date
    master["purchase_month"] = master["purchase_ts"].dt.strftime("%Y-%m")
    master["is_in_window"] = master["purchase_ts"].between(ANALYSIS_START, ANALYSIS_END)

    master["is_canceled"] = master["order_status"].eq("canceled")
    master["is_unavailable"] = master["order_status"].eq("unavailable")
    master["is_delivered"] = master["order_status"].eq("delivered")
    master["is_valid_order"] = (
        ~master["order_status"].isin(INVALID_SALE_STATUSES) & master["has_items"]
    )

    master["delivery_days"] = (
        master["order_delivered_customer_date"] - master["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    master["estimated_days"] = (
        master["order_estimated_delivery_date"] - master["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400
    master["delay_days"] = (
        master["order_delivered_customer_date"]
        - master["order_estimated_delivery_date"]
    ).dt.total_seconds() / 86400

    delivered_mask = master["is_delivered"] & master["delay_days"].notna()
    master["is_late"] = pd.Series(pd.NA, index=master.index, dtype="boolean")
    master.loc[delivered_mask, "is_late"] = master.loc[
        delivered_mask, "delay_days"
    ].gt(0)
    master["delivery_status"] = pd.Series(pd.NA, index=master.index, dtype="string")
    master.loc[delivered_mask, "delivery_status"] = np.where(
        master.loc[delivered_mask, "delay_days"].gt(0), "Late", "On time"
    )

    master["order_value_band"] = pd.cut(
        master["gross_order_value"],
        bins=ORDER_VALUE_BINS,
        labels=ORDER_VALUE_LABELS,
        include_lowest=True,
    ).astype("string")
    master["delivery_days_bucket"] = pd.cut(
        master["delivery_days"],
        bins=DELIVERY_DAY_BINS,
        labels=DELIVERY_DAY_LABELS,
        include_lowest=True,
    ).astype("string")
    master["delay_bucket"] = pd.cut(
        master["delay_days"],
        bins=DELAY_BINS,
        labels=DELAY_LABELS,
        include_lowest=True,
    ).astype("string")

    # Sequence number and first-purchase flag are based on all valid orders,
    # not only the analysis window, so an old customer is never called "new".
    valid_all = master.loc[master["is_valid_order"]].sort_values(
        ["customer_unique_id", "purchase_ts", "order_id"]
    )
    valid_all["customer_order_number"] = (
        valid_all.groupby("customer_unique_id").cumcount() + 1
    )
    valid_all["is_first_purchase"] = valid_all["customer_order_number"].eq(1)
    master = master.merge(
        valid_all[["order_id", "customer_order_number", "is_first_purchase"]],
        on="order_id",
        how="left",
        validate="one_to_one",
    )
    master["customer_order_number"] = master["customer_order_number"].fillna(0).astype(int)
    master["is_first_purchase"] = master["is_first_purchase"].fillna(False).astype(bool)

    return master


def build_items_enriched(
    items: pd.DataFrame,
    orders_master: pd.DataFrame,
    products: pd.DataFrame,
    sellers: pd.DataFrame,
) -> pd.DataFrame:
    """Item-grain fact table for product/category/seller drill-downs."""

    order_cols = [
        "order_id",
        "order_purchase_timestamp",
        "purchase_month",
        "order_status",
        "is_valid_order",
        "is_delivered",
        "is_canceled",
        "is_unavailable",
        "is_in_window",
        "customer_unique_id",
        "customer_state",
        "customer_city",
        "customer_lat",
        "customer_lng",
        "review_score",
        "delivery_days",
        "delay_days",
        "is_late",
    ]
    item = items.merge(
        orders_master[order_cols],
        on="order_id",
        how="left",
        validate="many_to_one",
    )
    item = item.merge(
        products[
            [
                "product_id",
                "product_category_name",
                "product_category_english",
                "product_category_label",
                "product_name_length",
                "product_description_length",
                "product_photos_qty",
                "product_weight_g",
                "product_length_cm",
                "product_height_cm",
                "product_width_cm",
            ]
        ],
        on="product_id",
        how="left",
        validate="many_to_one",
    )
    item = item.merge(
        sellers[
            [
                "seller_id",
                "seller_city",
                "seller_state",
                "seller_lat",
                "seller_lng",
            ]
        ],
        on="seller_id",
        how="left",
        validate="many_to_one",
    )

    item["gmv"] = item["price"].astype(float)
    item["item_total"] = item["gmv"] + item["freight_value"].astype(float)
    item["purchase_ts"] = item["order_purchase_timestamp"]
    return item


def build_order_dimensions(
    items: pd.DataFrame, orders_master: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build order-category and order-seller grains.

    These grains are the correct denominators for category/seller review and
    delivery metrics.  Revenue in these tables is still additive at item level;
    only the order counts are duplicated when an order spans several
    categories or sellers.
    """

    order_info_cols = [
        "order_id",
        "purchase_month",
        "order_status",
        "is_valid_order",
        "is_delivered",
        "is_canceled",
        "is_unavailable",
        "is_in_window",
        "review_score",
        "delay_days",
        "delivery_days",
        "is_late",
        "customer_state",
        "customer_unique_id",
    ]
    order_info = orders_master[order_info_cols].copy()

    order_category = (
        items.groupby(["order_id", "product_category_label"], as_index=False)
        .agg(
            item_count=("order_item_id", "size"),
            product_count=("product_id", "nunique"),
            seller_count=("seller_id", "nunique"),
            merchandise_value=("price", "sum"),
            freight_value=("freight_value", "sum"),
        )
        .merge(order_info, on="order_id", how="left", validate="many_to_one")
    )
    order_category["gross_value"] = (
        order_category["merchandise_value"] + order_category["freight_value"]
    )

    order_seller = (
        items.groupby(["order_id", "seller_id"], as_index=False)
        .agg(
            item_count=("order_item_id", "size"),
            product_count=("product_id", "nunique"),
            merchandise_value=("price", "sum"),
            freight_value=("freight_value", "sum"),
            seller_state=("seller_state", "first"),
            seller_city=("seller_city", "first"),
        )
        .merge(order_info, on="order_id", how="left", validate="many_to_one")
    )
    order_seller["gross_value"] = (
        order_seller["merchandise_value"] + order_seller["freight_value"]
    )
    return order_category, order_seller


# ---------------------------------------------------------------------------
# Customer analytics
# ---------------------------------------------------------------------------
def _score_quintile(values: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """Return 1-5 scores that are stable when many values are tied.

    Values are ranked from low to high, split into quintiles, then inverted for
    metrics where a lower value is better (for example recency).
    """

    ranked = values.rank(method="first", ascending=True)
    buckets = pd.qcut(ranked, 5, labels=False, duplicates="drop")
    scores = buckets + 1
    if not higher_is_better:
        scores = 6 - scores
    return scores.astype(int)


def _rfm_segment(row: pd.Series) -> str:
    recency = int(row["r_score"])
    frequency = int(row["f_score"])
    monetary = int(row["m_score"])

    if recency >= 4 and frequency >= 4 and monetary >= 4:
        return "Champions"
    if recency >= 3 and frequency >= 3:
        return "Loyal"
    if recency >= 4 and frequency == 1:
        return "New"
    if recency >= 3 and frequency <= 2:
        return "Potential Loyalist"
    if recency <= 2 and frequency >= 3:
        return "At Risk"
    if recency <= 2 and frequency <= 2:
        return "Hibernating"
    if monetary >= 4 and recency == 3:
        return "Need Attention"
    return "Others"


def build_customer_rfm(
    orders_master: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create customer-level RFM scores and a cohort retention table."""

    valid = orders_master.loc[
        orders_master["is_valid_order"] & orders_master["is_in_window"]
    ].copy()

    first_purchase_all = (
        orders_master.loc[orders_master["is_valid_order"]]
        .groupby("customer_unique_id", as_index=False)["purchase_ts"]
        .min()
        .rename(columns={"purchase_ts": "first_purchase_ts"})
    )
    first_purchase_all["cohort_month"] = (
        first_purchase_all["first_purchase_ts"].dt.strftime("%Y-%m")
    )

    latest_customer = (
        valid.sort_values(["customer_unique_id", "purchase_ts", "order_id"])
        .drop_duplicates("customer_unique_id", keep="last")[
            [
                "customer_unique_id",
                "customer_state",
                "customer_city",
                "customer_lat",
                "customer_lng",
            ]
        ]
    )

    rfm = valid.groupby("customer_unique_id", as_index=False).agg(
        first_order_ts=("purchase_ts", "min"),
        last_order_ts=("purchase_ts", "max"),
        frequency=("order_id", "nunique"),
        monetary=("gross_order_value", "sum"),
        merchandise_value=("merchandise_value", "sum"),
        freight_value=("freight_value", "sum"),
        item_count=("item_count", "sum"),
        avg_order_value=("gross_order_value", "mean"),
        avg_review_score=("review_score", "mean"),
        total_reviews=("review_score", "count"),
    )
    rfm = rfm.merge(
        latest_customer, on="customer_unique_id", how="left", validate="one_to_one"
    )
    rfm = rfm.merge(
        first_purchase_all, on="customer_unique_id", how="left", validate="one_to_one"
    )

    rfm["recency_days"] = (SNAPSHOT_TS - rfm["last_order_ts"]).dt.total_seconds() / 86400
    rfm["recency_days"] = rfm["recency_days"].round().astype(int)
    rfm["r_score"] = _score_quintile(rfm["recency_days"], higher_is_better=False)
    rfm["f_score"] = pd.cut(
        rfm["frequency"],
        bins=[0, 1, 2, 3, 5, float("inf")],
        labels=[1, 2, 3, 4, 5],
        include_lowest=True,
    ).astype(int)
    rfm["m_score"] = _score_quintile(rfm["monetary"], higher_is_better=True)
    rfm["rfm_total_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]
    rfm["rfm_cell"] = (
        rfm["r_score"].astype(str)
        + rfm["f_score"].astype(str)
        + rfm["m_score"].astype(str)
    )
    rfm["rfm_segment"] = rfm.apply(_rfm_segment, axis=1)
    rfm["rfm_segment_cn"] = rfm["rfm_segment"].map(RFM_SEGMENT_CN).fillna("其他")
    rfm["customer_type"] = np.where(
        rfm["frequency"] > 1, "Repeat", "One-time"
    )

    # Cohort table: first purchase is based on all valid orders, activity is
    # measured inside the analysis window.  Cohorts before 2017-01 are omitted
    # because the source data is incomplete before January 2017.
    cohort_orders = orders_master.loc[
        orders_master["is_valid_order"] & orders_master["purchase_ts"].notna()
    ].copy()
    cohort_orders = cohort_orders.merge(
        first_purchase_all[["customer_unique_id", "cohort_month"]],
        on="customer_unique_id",
        how="left",
        validate="many_to_one",
    )
    cohort_orders = cohort_orders.loc[
        cohort_orders["is_in_window"]
        & cohort_orders["cohort_month"].ge("2017-01")
    ].copy()
    cohort_start = pd.to_datetime(cohort_orders["cohort_month"] + "-01")
    cohort_orders["period_number"] = (
        (cohort_orders["purchase_ts"].dt.year - cohort_start.dt.year) * 12
        + (cohort_orders["purchase_ts"].dt.month - cohort_start.dt.month)
    )

    cohort = (
        cohort_orders.groupby(["cohort_month", "period_number"], as_index=False)
        .agg(
            customers=("customer_unique_id", "nunique"),
            orders=("order_id", "nunique"),
            gross_value=("gross_order_value", "sum"),
            review_score=("review_score", "mean"),
        )
        .sort_values(["cohort_month", "period_number"])
    )
    cohort_size = (
        cohort.loc[cohort["period_number"].eq(0), ["cohort_month", "customers"]]
        .rename(columns={"customers": "cohort_size"})
    )
    cohort = cohort.merge(cohort_size, on="cohort_month", how="left", validate="many_to_one")
    cohort["retention_rate"] = cohort["customers"] / cohort["cohort_size"]
    cohort["revenue_per_cohort_customer"] = cohort["gross_value"] / cohort["cohort_size"]

    wide = cohort.pivot(
        index="cohort_month", columns="period_number", values="retention_rate"
    )
    all_periods = range(0, int(cohort["period_number"].max()) + 1)
    wide = wide.reindex(columns=all_periods)
    wide.columns = [f"period_{int(column)}" for column in wide.columns]
    wide = wide.sort_index().reset_index()

    return rfm, (cohort, wide)


def prepare_all(raw: dict[str, pd.DataFrame]) -> PreparedData:
    """Run all preparation steps in dependency order."""

    logger.info("Preparing dimension tables")
    geo_centroids = build_geo_centroids(raw["geolocation"])
    products = build_products(raw["products"], raw["category_translation"])
    customers = build_customers(raw["customers"], geo_centroids)
    sellers = build_sellers(raw["sellers"], geo_centroids)

    logger.info("Preparing review and payment facts")
    reviews_raw, reviews_latest = build_reviews(raw["reviews"])
    payment_rows = build_payment_rows(raw["payments"], raw["orders"])

    logger.info("Building order master")
    orders_master = build_orders_master(
        orders=raw["orders"],
        customers=customers,
        items=raw["order_items"],
        products=products,
        payments=raw["payments"],
        reviews_latest=reviews_latest,
    )

    logger.info("Building item and order-dimension tables")
    items = build_items_enriched(
        raw["order_items"], orders_master, products, sellers
    )
    order_category, order_seller = build_order_dimensions(items, orders_master)

    logger.info("Building customer RFM and cohorts")
    rfm, (cohort, cohort_wide) = build_customer_rfm(orders_master)

    return PreparedData(
        orders_master=orders_master,
        items=items,
        order_category=order_category,
        order_seller=order_seller,
        customers=customers,
        products=products,
        sellers=sellers,
        payment_rows=payment_rows,
        reviews_latest=reviews_latest,
        reviews_raw=reviews_raw,
        geo_centroids=geo_centroids,
        rfm=rfm,
        cohort=cohort,
        cohort_wide=cohort_wide,
    )