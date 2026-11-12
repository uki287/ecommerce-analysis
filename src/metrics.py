"""Chart-ready aggregate tables for the Olist e-commerce dataset.

Every table is designed to be consumed by a BI tool or a plotting library:

* one row per chart category or time bucket;
* stable English column names;
* rates/shares expressed as decimals (0-1), not percentages;
* no hidden global state.

The module does not import matplotlib or any other plotting package.  Charts
can be built later from the CSV/XLSX outputs without changing this code.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .config import (
    ANALYSIS_END,
    ANALYSIS_START,
    DELAY_LABELS,
    DELIVERY_DAY_LABELS,
    ORDER_VALUE_LABELS,
)
from .prepare import PreparedData

logger = logging.getLogger(__name__)


def _div(numerator, denominator):
    """Divide safely, returning NaN rather than inf when the denominator is 0."""

    if isinstance(denominator, pd.Series):
        clean = denominator.replace(0, np.nan)
        return (numerator / clean).replace([np.inf, -np.inf], np.nan)
    if denominator is None or pd.isna(denominator) or denominator == 0:
        return np.nan
    return numerator / denominator


_COUNT_COLUMNS = {
    "orders",
    "orders_all",
    "orders_valid",
    "orders_delivered",
    "orders_canceled",
    "orders_unavailable",
    "orders_with_payment",
    "orders_without_payment",
    "orders_matching_within_0_01",
    "orders_mismatch",
    "customers",
    "customers_unique",
    "new_customers",
    "repeat_customers",
    "canceled_orders",
    "unavailable_orders",
    "delivered_orders",
    "delivered_with_dates",
    "items",
    "sellers",
    "categories",
    "units",
    "reviews",
    "review_count",
    "comments",
    "low_review_orders",
    "five_star_orders",
    "late_orders",
    "on_time_orders",
    "payment_rows",
    "installment_rows_gt1",
    "cohort_size",
    "period_number",
    "top_n_sellers",
    "repeat_orders",
}


def _round_table(df: pd.DataFrame) -> pd.DataFrame:
    """Apply readable but precise rounding for CSV/Excel output."""

    out = df.copy()
    for column in out.columns:
        if column in _COUNT_COLUMNS and pd.api.types.is_numeric_dtype(out[column]):
            out[column] = out[column].fillna(0).round().astype("int64")
        if not pd.api.types.is_float_dtype(out[column]):
            continue
        name = column.lower()
        if "rate" in name or "share" in name or "coverage" in name:
            decimals = 4
        elif "days" in name or "score" in name:
            decimals = 2
        elif any(
            token in name
            for token in (
                "value",
                "gmv",
                "revenue",
                "monetary",
                "freight",
                "price",
                "payment",
                "aov",
                "avg_order",
            )
        ):
            decimals = 2
        else:
            decimals = 4
        out[column] = out[column].round(decimals)
    return out


def _late_flag(frame: pd.DataFrame) -> pd.Series:
    return frame["is_late"].fillna(False).astype(int)


# ---------------------------------------------------------------------------
# Executive overview and time series
# ---------------------------------------------------------------------------
def build_overview(orders: pd.DataFrame, items: pd.DataFrame) -> pd.DataFrame:
    """One-row KPI table for headline cards."""

    scope = orders.loc[orders["is_in_window"]].copy()
    valid = scope.loc[scope["is_valid_order"]].copy()
    delivered = scope.loc[scope["is_delivered"] & scope["delay_days"].notna()].copy()
    reviewed = valid.loc[valid["review_score"].notna()].copy()
    valid_items = items.loc[items["is_in_window"] & items["is_valid_order"]].copy()

    frequency = valid.groupby("customer_unique_id").size()
    repeat_customers = int((frequency > 1).sum())
    customers = int(valid["customer_unique_id"].nunique())
    new_customers = int(
        valid.loc[valid["is_first_purchase"], "customer_unique_id"].nunique()
    )
    late_orders = int(_late_flag(delivered).sum())

    row = {
        "analysis_start": ANALYSIS_START.date().isoformat(),
        "analysis_end": ANALYSIS_END.date().isoformat(),
        "orders_all": len(scope),
        "orders_valid": len(valid),
        "orders_delivered": int(scope["is_delivered"].sum()),
        "orders_canceled": int(scope["is_canceled"].sum()),
        "orders_unavailable": int(scope["is_unavailable"].sum()),
        "customers_unique": customers,
        "new_customers": new_customers,
        "repeat_customers": repeat_customers,
        "repeat_customer_rate": _div(repeat_customers, customers),
        "items": int(valid["item_count"].sum()),
        "sellers": int(valid_items["seller_id"].nunique()),
        "categories": int(valid_items["product_category_label"].nunique()),
        "merchandise_value": float(valid["merchandise_value"].sum()),
        "freight_value": float(valid["freight_value"].sum()),
        "gross_order_value": float(valid["gross_order_value"].sum()),
        "payment_value": float(valid["payment_value"].sum()),
        "gmv": float(valid["merchandise_value"].sum()),
        "aov": _div(valid["gross_order_value"].sum(), len(valid)),
        "avg_merchandise_value": _div(valid["merchandise_value"].sum(), len(valid)),
        "avg_items_per_order": _div(valid["item_count"].sum(), len(valid)),
        "avg_freight_per_order": _div(valid["freight_value"].sum(), len(valid)),
        "freight_share": _div(
            valid["freight_value"].sum(), valid["gross_order_value"].sum()
        ),
        "avg_review_score": reviewed["review_score"].mean(),
        "review_coverage": _div(len(reviewed), len(valid)),
        "review_comment_rate": reviewed["latest_review_has_comment"].mean(),
        "low_review_rate": _div((reviewed["review_score"] <= 2).sum(), len(reviewed)),
        "positive_review_rate": _div((reviewed["review_score"] >= 4).sum(), len(reviewed)),
        "delivered_with_dates": len(delivered),
        "late_orders": late_orders,
        "on_time_orders": len(delivered) - late_orders,
        "late_rate": _div(late_orders, len(delivered)),
        "on_time_rate": _div(len(delivered) - late_orders, len(delivered)),
        "avg_delivery_days": delivered["delivery_days"].mean(),
        "median_delivery_days": delivered["delivery_days"].median(),
        "p90_delivery_days": delivered["delivery_days"].quantile(0.90),
        "avg_delay_days": delivered["delay_days"].mean(),
        "cancel_rate": _div(
            scope["is_canceled"].sum() + scope["is_unavailable"].sum(), len(scope)
        ),
        "delivered_rate": _div(scope["is_delivered"].sum(), len(scope)),
        "orders_with_payment": int(valid["payment_count"].gt(0).sum()),
        "payment_gap_total": float(valid["payment_gap"].sum()),
        "payment_match_rate": _div(
            valid["payment_gap"].abs().le(0.01).sum(), valid["payment_count"].gt(0).sum()
        ),
    }
    return _round_table(pd.DataFrame([row]))


def build_monthly_kpis(orders: pd.DataFrame) -> pd.DataFrame:
    """Monthly trend table for line/column charts."""

    scope = orders.loc[orders["is_in_window"]].copy()
    scope["late_flag"] = _late_flag(scope)

    all_agg = scope.groupby("purchase_month", as_index=False).agg(
        orders_all=("order_id", "size"),
        canceled_orders=("is_canceled", "sum"),
        unavailable_orders=("is_unavailable", "sum"),
        delivered_orders=("is_delivered", "sum"),
    )

    valid = scope.loc[scope["is_valid_order"]].copy()
    valid["low_review"] = (valid["review_score"] <= 2).fillna(False).astype(int)
    valid_agg = valid.groupby("purchase_month", as_index=False).agg(
        orders_valid=("order_id", "nunique"),
        customers=("customer_unique_id", "nunique"),
        new_customers=("is_first_purchase", "sum"),
        repeat_orders=("is_first_purchase", lambda values: int((~values).sum())),
        items=("item_count", "sum"),
        merchandise_value=("merchandise_value", "sum"),
        freight_value=("freight_value", "sum"),
        gross_order_value=("gross_order_value", "sum"),
        payment_value=("payment_value", "sum"),
        review_score=("review_score", "mean"),
        review_count=("review_score", "count"),
        comment_count=("latest_review_has_comment", "sum"),
        low_review_orders=("low_review", "sum"),
    )

    delivered = scope.loc[scope["is_delivered"] & scope["delay_days"].notna()].copy()
    deliv_agg = delivered.groupby("purchase_month", as_index=False).agg(
        delivered_with_dates=("order_id", "size"),
        late_orders=("late_flag", "sum"),
        avg_delivery_days=("delivery_days", "mean"),
        median_delivery_days=("delivery_days", "median"),
        p90_delivery_days=("delivery_days", lambda values: values.quantile(0.90)),
        avg_delay_days=("delay_days", "mean"),
    )

    monthly = (
        all_agg.merge(valid_agg, on="purchase_month", how="left", validate="one_to_one")
        .merge(deliv_agg, on="purchase_month", how="left", validate="one_to_one")
        .rename(columns={"purchase_month": "month"})
        .sort_values("month")
        .reset_index(drop=True)
    )

    for column in monthly.columns:
        if column not in {"month"}:
            monthly[column] = monthly[column].fillna(0)

    monthly["gmv"] = monthly["merchandise_value"]
    monthly["aov"] = _div(monthly["gross_order_value"], monthly["orders_valid"])
    monthly["avg_items_per_order"] = _div(monthly["items"], monthly["orders_valid"])
    monthly["freight_share"] = _div(
        monthly["freight_value"], monthly["gross_order_value"]
    )
    monthly["review_coverage"] = _div(monthly["review_count"], monthly["orders_valid"])
    monthly["low_review_rate"] = _div(
        monthly["low_review_orders"], monthly["review_count"]
    )
    monthly["comment_rate"] = _div(monthly["comment_count"], monthly["review_count"])
    monthly["late_rate"] = _div(monthly["late_orders"], monthly["delivered_with_dates"])
    monthly["on_time_rate"] = 1 - monthly["late_rate"]
    monthly["cancel_rate"] = _div(
        monthly["canceled_orders"] + monthly["unavailable_orders"], monthly["orders_all"]
    )
    monthly["repeat_order_rate"] = _div(
        monthly["repeat_orders"], monthly["orders_valid"]
    )
    return _round_table(monthly)


def build_order_status_summary(orders: pd.DataFrame) -> pd.DataFrame:
    """Order-count and value profile by status."""

    scope = orders.loc[orders["is_in_window"]].copy()
    scope["valid_gross"] = scope["gross_order_value"].where(
        scope["is_valid_order"], 0
    )
    scope["valid_gmv"] = scope["merchandise_value"].where(
        scope["is_valid_order"], 0
    )
    scope["late_flag"] = _late_flag(scope)

    status = scope.groupby("order_status", as_index=False).agg(
        orders=("order_id", "nunique"),
        items=("item_count", "sum"),
        potential_gross_value=("gross_order_value", "sum"),
        gmv=("valid_gmv", "sum"),
        gross_order_value=("valid_gross", "sum"),
        payment_value=("payment_value", "sum"),
        avg_review_score=("review_score", "mean"),
        late_orders=("late_flag", "sum"),
        delivered_with_dates=("delay_days", "count"),
    )
    total_orders = status["orders"].sum()
    status["order_share"] = _div(status["orders"], total_orders)
    status["late_rate"] = _div(status["late_orders"], status["delivered_with_dates"])
    status = status.sort_values("orders", ascending=False).reset_index(drop=True)
    return _round_table(status)


# ---------------------------------------------------------------------------
# Category, geography, seller, and product dimensions
# ---------------------------------------------------------------------------
def build_category_kpis(order_category: pd.DataFrame) -> pd.DataFrame:
    """Category-level revenue, satisfaction, and delivery metrics."""

    oc = order_category.loc[order_category["is_in_window"]].copy()
    oc["late_flag"] = _late_flag(oc)

    all_agg = oc.groupby("product_category_label", as_index=False).agg(
        orders_all=("order_id", "nunique"),
        canceled_orders=("is_canceled", "sum"),
        unavailable_orders=("is_unavailable", "sum"),
    )
    valid = oc.loc[oc["is_valid_order"]].copy()
    valid_agg = valid.groupby("product_category_label", as_index=False).agg(
        orders_valid=("order_id", "nunique"),
        customers=("customer_unique_id", "nunique"),
        items=("item_count", "sum"),
        merchandise_value=("merchandise_value", "sum"),
        freight_value=("freight_value", "sum"),
        gross_order_value=("gross_value", "sum"),
        review_score=("review_score", "mean"),
        review_count=("review_score", "count"),
    )
    delivered = oc.loc[oc["is_delivered"] & oc["delay_days"].notna()].copy()
    deliv_agg = delivered.groupby("product_category_label", as_index=False).agg(
        delivered_orders=("order_id", "nunique"),
        late_orders=("late_flag", "sum"),
    )

    category = (
        all_agg.merge(valid_agg, on="product_category_label", how="left")
        .merge(deliv_agg, on="product_category_label", how="left")
        .rename(columns={"product_category_label": "category"})
    )
    for column in category.columns:
        if column != "category":
            category[column] = category[column].fillna(0)
    category["gmv"] = category["merchandise_value"]
    category["aov"] = _div(category["gross_order_value"], category["orders_valid"])
    category["avg_item_value"] = _div(category["merchandise_value"], category["items"])
    category["freight_share"] = _div(
        category["freight_value"], category["gross_order_value"]
    )
    category["cancel_rate"] = _div(
        category["canceled_orders"] + category["unavailable_orders"],
        category["orders_all"],
    )
    category["late_rate"] = _div(
        category["late_orders"], category["delivered_orders"]
    )
    category["on_time_rate"] = 1 - category["late_rate"]
    category["gmv_share"] = _div(
        category["gmv"], category["gmv"].sum()
    )
    category = category.sort_values("gmv", ascending=False).reset_index(drop=True)
    category["category_rank"] = np.arange(1, len(category) + 1)
    columns = [
        "category_rank",
        "category",
        "orders_all",
        "orders_valid",
        "canceled_orders",
        "unavailable_orders",
        "cancel_rate",
        "items",
        "customers",
        "merchandise_value",
        "freight_value",
        "gross_order_value",
        "gmv",
        "gmv_share",
        "avg_item_value",
        "aov",
        "freight_share",
        "review_score",
        "review_count",
        "delivered_orders",
        "late_orders",
        "late_rate",
        "on_time_rate",
    ]
    return _round_table(category[columns])


def build_category_monthly(order_category: pd.DataFrame) -> pd.DataFrame:
    """Monthly category trend for small-multiple or line charts."""

    oc = order_category.loc[order_category["is_in_window"]].copy()
    oc["late_flag"] = _late_flag(oc)

    all_agg = oc.groupby(
        ["purchase_month", "product_category_label"], as_index=False
    ).agg(
        orders_all=("order_id", "nunique"),
        canceled_orders=("is_canceled", "sum"),
        unavailable_orders=("is_unavailable", "sum"),
    )
    valid = oc.loc[oc["is_valid_order"]].copy()
    valid_agg = valid.groupby(
        ["purchase_month", "product_category_label"], as_index=False
    ).agg(
        orders_valid=("order_id", "nunique"),
        gmv=("merchandise_value", "sum"),
        gross_order_value=("gross_value", "sum"),
        items=("item_count", "sum"),
        review_score=("review_score", "mean"),
    )
    delivered = oc.loc[oc["is_delivered"] & oc["delay_days"].notna()].copy()
    deliv_agg = delivered.groupby(
        ["purchase_month", "product_category_label"], as_index=False
    ).agg(
        delivered_orders=("order_id", "nunique"),
        late_orders=("late_flag", "sum"),
    )

    monthly = (
        all_agg.merge(valid_agg, on=["purchase_month", "product_category_label"], how="left")
        .merge(
            deliv_agg, on=["purchase_month", "product_category_label"], how="left"
        )
        .rename(
            columns={
                "purchase_month": "month",
                "product_category_label": "category",
            }
        )
        .sort_values(["month", "category"])
    )
    for column in monthly.columns:
        if column not in {"month", "category"}:
            monthly[column] = monthly[column].fillna(0)
    monthly["aov"] = _div(monthly["gross_order_value"], monthly["orders_valid"])
    monthly["late_rate"] = _div(monthly["late_orders"], monthly["delivered_orders"])
    monthly["cancel_rate"] = _div(
        monthly["canceled_orders"] + monthly["unavailable_orders"], monthly["orders_all"]
    )
    return _round_table(monthly.reset_index(drop=True))


def build_state_kpis(
    orders: pd.DataFrame, rfm: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """State-level demand, delivery, and customer metrics plus monthly trend."""

    scope = orders.loc[orders["is_in_window"]].copy()
    scope["late_flag"] = _late_flag(scope)

    all_agg = scope.groupby("customer_state", as_index=False).agg(
        orders_all=("order_id", "nunique"),
        canceled_orders=("is_canceled", "sum"),
        unavailable_orders=("is_unavailable", "sum"),
        delivered_orders=("is_delivered", "sum"),
        customer_lat=("customer_lat", "mean"),
        customer_lng=("customer_lng", "mean"),
    )
    valid = scope.loc[scope["is_valid_order"]].copy()
    valid_agg = valid.groupby("customer_state", as_index=False).agg(
        orders_valid=("order_id", "nunique"),
        customers=("customer_unique_id", "nunique"),
        items=("item_count", "sum"),
        gmv=("merchandise_value", "sum"),
        freight_value=("freight_value", "sum"),
        gross_order_value=("gross_order_value", "sum"),
        review_score=("review_score", "mean"),
        review_count=("review_score", "count"),
    )
    delivered = scope.loc[scope["is_delivered"] & scope["delay_days"].notna()].copy()
    deliv_agg = delivered.groupby("customer_state", as_index=False).agg(
        delivered_with_dates=("order_id", "size"),
        late_orders=("late_flag", "sum"),
        avg_delivery_days=("delivery_days", "mean"),
        median_delivery_days=("delivery_days", "median"),
        p90_delivery_days=("delivery_days", lambda values: values.quantile(0.90)),
        avg_delay_days=("delay_days", "mean"),
    )
    repeat = (
        rfm.loc[rfm["customer_type"].eq("Repeat")]
        .groupby("customer_state", as_index=False)
        .agg(repeat_customers=("customer_unique_id", "nunique"))
    )

    state = (
        all_agg.merge(valid_agg, on="customer_state", how="left")
        .merge(deliv_agg, on="customer_state", how="left")
        .merge(repeat, on="customer_state", how="left")
        .rename(columns={"customer_state": "state"})
    )
    for column in state.columns:
        if column not in {"state"}:
            state[column] = state[column].fillna(0)
    state["aov"] = _div(state["gross_order_value"], state["orders_valid"])
    state["freight_share"] = _div(
        state["freight_value"], state["gross_order_value"]
    )
    state["cancel_rate"] = _div(
        state["canceled_orders"] + state["unavailable_orders"], state["orders_all"]
    )
    state["late_rate"] = _div(state["late_orders"], state["delivered_with_dates"])
    state["on_time_rate"] = 1 - state["late_rate"]
    state["repeat_customer_rate"] = _div(state["repeat_customers"], state["customers"])
    state["gmv_share"] = _div(state["gmv"], state["gmv"].sum())
    state["orders_share"] = _div(state["orders_all"], state["orders_all"].sum())
    state = state.sort_values("gmv", ascending=False).reset_index(drop=True)
    state["state_rank"] = np.arange(1, len(state) + 1)

    state_columns = [
        "state_rank",
        "state",
        "orders_all",
        "orders_valid",
        "canceled_orders",
        "unavailable_orders",
        "cancel_rate",
        "customers",
        "repeat_customers",
        "repeat_customer_rate",
        "items",
        "gmv",
        "gmv_share",
        "orders_share",
        "freight_value",
        "gross_order_value",
        "aov",
        "freight_share",
        "review_score",
        "review_count",
        "delivered_with_dates",
        "late_orders",
        "late_rate",
        "on_time_rate",
        "avg_delivery_days",
        "median_delivery_days",
        "p90_delivery_days",
        "avg_delay_days",
        "customer_lat",
        "customer_lng",
    ]
    state = _round_table(state[state_columns])

    valid_month = scope.loc[scope["is_valid_order"]].copy()
    month_agg = valid_month.groupby(
        ["purchase_month", "customer_state"], as_index=False
    ).agg(
        orders_valid=("order_id", "nunique"),
        customers=("customer_unique_id", "nunique"),
        gmv=("merchandise_value", "sum"),
        gross_order_value=("gross_order_value", "sum"),
        review_score=("review_score", "mean"),
    )
    month_deliv = delivered.groupby(
        ["purchase_month", "customer_state"], as_index=False
    ).agg(
        delivered_with_dates=("order_id", "size"),
        late_orders=("late_flag", "sum"),
    )
    state_monthly = (
        month_agg.merge(
            month_deliv, on=["purchase_month", "customer_state"], how="left"
        )
        .rename(columns={"purchase_month": "month", "customer_state": "state"})
        .sort_values(["month", "state"])
    )
    for column in state_monthly.columns:
        if column not in {"month", "state"}:
            state_monthly[column] = state_monthly[column].fillna(0)
    state_monthly["aov"] = _div(
        state_monthly["gross_order_value"], state_monthly["orders_valid"]
    )
    state_monthly["late_rate"] = _div(
        state_monthly["late_orders"], state_monthly["delivered_with_dates"]
    )
    return state, _round_table(state_monthly.reset_index(drop=True))


def build_seller_kpis(order_seller: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Seller performance table and Pareto concentration summary."""

    os_ = order_seller.loc[order_seller["is_in_window"]].copy()
    os_["late_flag"] = _late_flag(os_)

    all_agg = os_.groupby("seller_id", as_index=False).agg(
        orders_all=("order_id", "nunique"),
        canceled_orders=("is_canceled", "sum"),
        unavailable_orders=("is_unavailable", "sum"),
        delivered_orders=("is_delivered", "sum"),
        seller_state=("seller_state", "first"),
        seller_city=("seller_city", "first"),
    )
    valid = os_.loc[os_["is_valid_order"]].copy()
    valid_agg = valid.groupby("seller_id", as_index=False).agg(
        orders_valid=("order_id", "nunique"),
        customers=("customer_unique_id", "nunique"),
        items=("item_count", "sum"),
        gmv=("merchandise_value", "sum"),
        freight_value=("freight_value", "sum"),
        gross_order_value=("gross_value", "sum"),
        review_score=("review_score", "mean"),
        review_count=("review_score", "count"),
    )
    delivered = os_.loc[os_["is_delivered"] & os_["delay_days"].notna()].copy()
    deliv_agg = delivered.groupby("seller_id", as_index=False).agg(
        delivered_with_dates=("order_id", "nunique"),
        late_orders=("late_flag", "sum"),
        avg_delivery_days=("delivery_days", "mean"),
        avg_delay_days=("delay_days", "mean"),
    )

    seller = (
        all_agg.merge(valid_agg, on="seller_id", how="left")
        .merge(deliv_agg, on="seller_id", how="left")
    )
    for column in seller.columns:
        if column not in {"seller_id", "seller_state", "seller_city"}:
            seller[column] = seller[column].fillna(0)
    seller["aov"] = _div(seller["gross_order_value"], seller["orders_valid"])
    seller["cancel_rate"] = _div(
        seller["canceled_orders"] + seller["unavailable_orders"], seller["orders_all"]
    )
    seller["late_rate"] = _div(seller["late_orders"], seller["delivered_with_dates"])
    seller["on_time_rate"] = 1 - seller["late_rate"]
    seller["gmv_share"] = _div(seller["gmv"], seller["gmv"].sum())
    seller = seller.sort_values("gmv", ascending=False).reset_index(drop=True)
    seller["seller_rank"] = np.arange(1, len(seller) + 1)
    seller["cumulative_gmv_share"] = seller["gmv_share"].cumsum()

    columns = [
        "seller_rank",
        "seller_id",
        "seller_state",
        "seller_city",
        "orders_all",
        "orders_valid",
        "canceled_orders",
        "unavailable_orders",
        "cancel_rate",
        "items",
        "customers",
        "gmv",
        "gmv_share",
        "cumulative_gmv_share",
        "freight_value",
        "gross_order_value",
        "aov",
        "review_score",
        "review_count",
        "delivered_with_dates",
        "late_orders",
        "late_rate",
        "on_time_rate",
        "avg_delivery_days",
        "avg_delay_days",
    ]
    seller = _round_table(seller[columns])

    total_gmv = float(seller["gmv"].sum())
    total_sellers = len(seller)
    top_values = [1, 5, 10, 25, 50, 100, 500, 1000, total_sellers]
    rows = []
    for top_n in sorted(set(top_values)):
        top = seller.head(top_n)
        rows.append(
            {
                "top_n_sellers": top_n,
                "seller_share": _div(top_n, total_sellers),
                "gmv": float(top["gmv"].sum()),
                "gmv_share": _div(top["gmv"].sum(), total_gmv),
            }
        )
    pareto = pd.DataFrame(rows)
    pareto["gmv_share"] = pareto["gmv_share"].fillna(0)
    pareto["seller_share"] = pareto["seller_share"].fillna(0)
    return seller, _round_table(pareto)


def build_product_kpis(items: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Product-level sales and quality table, plus a top-100 slice.

    Metrics are calculated on an order-product grain first.  This prevents a
    multi-unit order from inflating delivery/review rates (the earlier
    item-grain version could produce late rates above 100%).
    """

    item = items.loc[items["is_in_window"]].copy()
    order_info_cols = [
        "order_id",
        "customer_unique_id",
        "order_status",
        "is_valid_order",
        "is_delivered",
        "is_canceled",
        "is_unavailable",
        "review_score",
        "delay_days",
        "is_late",
    ]
    order_info = item.drop_duplicates("order_id")[order_info_cols].copy()

    order_product = (
        item.groupby(["order_id", "product_id"], as_index=False)
        .agg(
            units=("order_item_id", "size"),
            gmv=("price", "sum"),
            freight_value=("freight_value", "sum"),
            gross_order_value=("item_total", "sum"),
            category=("product_category_label", "first"),
            seller_count=("seller_id", "nunique"),
        )
        .merge(order_info, on="order_id", how="left", validate="many_to_one")
    )
    order_product["late_flag"] = _late_flag(order_product)

    all_agg = order_product.groupby("product_id", as_index=False).agg(
        orders_all=("order_id", "nunique"),
        canceled_orders=("is_canceled", "sum"),
        unavailable_orders=("is_unavailable", "sum"),
        delivered_orders=("is_delivered", "sum"),
        category=("category", "first"),
    )
    valid = order_product.loc[order_product["is_valid_order"]].copy()
    valid_agg = valid.groupby("product_id", as_index=False).agg(
        orders_valid=("order_id", "nunique"),
        customers=("customer_unique_id", "nunique"),
        units=("units", "sum"),
        gmv=("gmv", "sum"),
        freight_value=("freight_value", "sum"),
        gross_order_value=("gross_order_value", "sum"),
        review_score=("review_score", "mean"),
        review_count=("review_score", "count"),
    )
    seller_count = (
        item.loc[item["is_valid_order"]]
        .groupby("product_id", as_index=False)
        .agg(sellers=("seller_id", "nunique"))
    )
    delivered = order_product.loc[
        order_product["is_delivered"] & order_product["delay_days"].notna()
    ].copy()
    deliv_agg = delivered.groupby("product_id", as_index=False).agg(
        delivered_with_dates=("order_id", "nunique"),
        late_orders=("late_flag", "sum"),
    )

    product = (
        all_agg.merge(valid_agg, on="product_id", how="left")
        .merge(seller_count, on="product_id", how="left")
        .merge(deliv_agg, on="product_id", how="left")
    )
    for column in product.columns:
        if column not in {"product_id", "category"}:
            product[column] = product[column].fillna(0)
    product["avg_price"] = _div(product["gmv"], product["units"])
    product["avg_freight"] = _div(product["freight_value"], product["units"])
    product["aov"] = _div(product["gross_order_value"], product["orders_valid"])
    product["cancel_rate"] = _div(
        product["canceled_orders"] + product["unavailable_orders"],
        product["orders_all"],
    )
    product["late_rate"] = _div(
        product["late_orders"], product["delivered_with_dates"]
    )
    product["on_time_rate"] = 1 - product["late_rate"]
    product["gmv_share"] = _div(product["gmv"], product["gmv"].sum())
    product = product.sort_values("gmv", ascending=False).reset_index(drop=True)
    product["product_rank"] = np.arange(1, len(product) + 1)
    product["cumulative_gmv_share"] = product["gmv_share"].cumsum()

    columns = [
        "product_rank",
        "product_id",
        "category",
        "orders_all",
        "orders_valid",
        "canceled_orders",
        "unavailable_orders",
        "cancel_rate",
        "units",
        "customers",
        "sellers",
        "gmv",
        "gmv_share",
        "cumulative_gmv_share",
        "freight_value",
        "gross_order_value",
        "avg_price",
        "avg_freight",
        "aov",
        "review_score",
        "review_count",
        "delivered_with_dates",
        "late_orders",
        "late_rate",
        "on_time_rate",
    ]
    product = _round_table(product[columns])
    return product, product.head(100).copy()


# ---------------------------------------------------------------------------
# Payment, review, and logistics tables
# ---------------------------------------------------------------------------
def build_payment_kpis(
    payment_rows: pd.DataFrame, orders: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Payment-method mix, installment distribution, and reconciliation."""

    valid_order_ids = set(
        orders.loc[orders["is_in_window"] & orders["is_valid_order"], "order_id"]
    )
    pay = payment_rows.loc[
        payment_rows["is_in_window"] & payment_rows["order_id"].isin(valid_order_ids)
    ].copy()
    total_orders = len(valid_order_ids)

    pay["more_than_one_installment"] = pay["payment_installments"].gt(1)
    payment = pay.groupby("payment_type", as_index=False).agg(
        payment_rows=("order_id", "size"),
        orders=("order_id", "nunique"),
        payment_value=("payment_value", "sum"),
        avg_payment_value=("payment_value", "mean"),
        avg_installments=("payment_installments", "mean"),
        installment_rows_gt1=("more_than_one_installment", "sum"),
    )
    payment["payment_value_share"] = _div(
        payment["payment_value"], payment["payment_value"].sum()
    )
    payment["order_share"] = _div(payment["orders"], total_orders)
    payment["installment_row_share_gt1"] = _div(
        payment["installment_rows_gt1"], payment["payment_rows"]
    )
    payment = payment.sort_values("payment_value", ascending=False).reset_index(drop=True)

    installments = pay.groupby(
        ["payment_type", "installment_bucket"], as_index=False
    ).agg(
        payment_rows=("order_id", "size"),
        orders=("order_id", "nunique"),
        payment_value=("payment_value", "sum"),
    )
    type_value = installments.groupby("payment_type")["payment_value"].transform("sum")
    installments["payment_value_share_of_type"] = _div(
        installments["payment_value"], type_value
    )
    installments["payment_value_share_of_all"] = _div(
        installments["payment_value"], installments["payment_value"].sum()
    )
    installments = installments.sort_values(
        ["payment_type", "installment_bucket"]
    ).reset_index(drop=True)

    scope = orders.loc[orders["is_in_window"] & orders["is_valid_order"]]
    reconciliation = pd.DataFrame(
        [
            {
                "orders_with_payment": int(scope["payment_count"].gt(0).sum()),
                "orders_without_payment": int(scope["payment_count"].eq(0).sum()),
                "total_payment_value": float(scope["payment_value"].sum()),
                "total_order_value": float(scope["gross_order_value"].sum()),
                "total_gap": float(scope["payment_gap"].sum()),
                "orders_matching_within_0_01": int(
                    scope["payment_gap"].abs().le(0.01).sum()
                ),
                "orders_mismatch": int(scope["payment_gap"].abs().gt(0.01).sum()),
                "match_rate": _div(
                    scope["payment_gap"].abs().le(0.01).sum(),
                    scope["payment_count"].gt(0).sum(),
                ),
            }
        ]
    )
    return (
        _round_table(payment),
        _round_table(installments),
        _round_table(reconciliation),
    )


def build_review_tables(
    orders: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Review score distribution and satisfaction by delivery outcome."""

    scope = orders.loc[orders["is_in_window"]].copy()
    reviewed = scope.loc[scope["is_valid_order"] & scope["review_score"].notna()].copy()
    reviewed["late_flag"] = _late_flag(reviewed)
    reviewed["low_review"] = reviewed["review_score"].le(2)

    distribution = reviewed.groupby("review_score", as_index=False).agg(
        orders=("order_id", "nunique"),
        comments=("latest_review_has_comment", "sum"),
        avg_order_value=("gross_order_value", "mean"),
        delivered_with_dates=("delay_days", "count"),
        late_orders=("late_flag", "sum"),
    )
    distribution["share"] = _div(distribution["orders"], distribution["orders"].sum())
    distribution["comment_rate"] = _div(distribution["comments"], distribution["orders"])
    distribution["late_rate"] = _div(
        distribution["late_orders"], distribution["delivered_with_dates"]
    )
    distribution = (
        distribution.set_index("review_score")
        .reindex([1, 2, 3, 4, 5])
        .rename_axis("review_score")
        .reset_index()
    )
    distribution["orders"] = distribution["orders"].fillna(0).astype(int)
    distribution["share"] = distribution["share"].fillna(0)

    monthly = reviewed.groupby("purchase_month", as_index=False).agg(
        reviews=("order_id", "nunique"),
        avg_review_score=("review_score", "mean"),
        low_review_orders=("low_review", "sum"),
        five_star_orders=("review_score", lambda values: int((values == 5).sum())),
        comments=("latest_review_has_comment", "sum"),
    )
    monthly["low_review_rate"] = _div(monthly["low_review_orders"], monthly["reviews"])
    monthly["five_star_rate"] = _div(monthly["five_star_orders"], monthly["reviews"])
    monthly["comment_rate"] = _div(monthly["comments"], monthly["reviews"])
    monthly = monthly.rename(columns={"purchase_month": "month"})

    by_delivery = reviewed.loc[reviewed["delivery_status"].notna()].groupby(
        "delivery_status", as_index=False
    ).agg(
        orders=("order_id", "nunique"),
        avg_review_score=("review_score", "mean"),
        low_review_orders=("low_review", "sum"),
        five_star_orders=("review_score", lambda values: int((values == 5).sum())),
        comments=("latest_review_has_comment", "sum"),
    )
    by_delivery["low_review_rate"] = _div(
        by_delivery["low_review_orders"], by_delivery["orders"]
    )
    by_delivery["five_star_rate"] = _div(
        by_delivery["five_star_orders"], by_delivery["orders"]
    )
    by_delivery["comment_rate"] = _div(
        by_delivery["comments"], by_delivery["orders"]
    )
    by_delivery = by_delivery.sort_values("avg_review_score", ascending=False)

    by_delay = reviewed.loc[reviewed["delay_bucket"].notna()].groupby(
        "delay_bucket", as_index=False
    ).agg(
        orders=("order_id", "nunique"),
        avg_review_score=("review_score", "mean"),
        low_review_orders=("low_review", "sum"),
        five_star_orders=("review_score", lambda values: int((values == 5).sum())),
    )
    by_delay["low_review_rate"] = _div(
        by_delay["low_review_orders"], by_delay["orders"]
    )
    by_delay["five_star_rate"] = _div(
        by_delay["five_star_orders"], by_delay["orders"]
    )
    by_delay["delay_bucket"] = pd.Categorical(
        by_delay["delay_bucket"], categories=DELAY_LABELS, ordered=True
    )
    by_delay = by_delay.sort_values("delay_bucket").reset_index(drop=True)
    by_delay["delay_bucket"] = by_delay["delay_bucket"].astype("string")

    return (
        _round_table(distribution),
        _round_table(monthly),
        _round_table(by_delivery),
        _round_table(by_delay),
    )


def build_delivery_tables(orders: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Delivery-time histogram, delay mix, and order-value bands."""

    scope = orders.loc[orders["is_in_window"]].copy()
    delivered = scope.loc[
        scope["is_delivered"] & scope["delivery_days"].notna()
    ].copy()
    delivered["late_flag"] = _late_flag(delivered)

    day_dist = delivered.groupby("delivery_days_bucket", as_index=False).agg(
        orders=("order_id", "size"),
        avg_review_score=("review_score", "mean"),
        late_orders=("late_flag", "sum"),
        avg_delay_days=("delay_days", "mean"),
    )
    day_dist["share"] = _div(day_dist["orders"], day_dist["orders"].sum())
    day_dist["late_rate"] = _div(day_dist["late_orders"], day_dist["orders"])
    day_dist["delivery_days_bucket"] = pd.Categorical(
        day_dist["delivery_days_bucket"], categories=DELIVERY_DAY_LABELS, ordered=True
    )
    day_dist = (
        day_dist.set_index("delivery_days_bucket")
        .reindex(DELIVERY_DAY_LABELS)
        .rename_axis("delivery_days_bucket")
        .reset_index()
    )
    day_dist["orders"] = day_dist["orders"].fillna(0).astype(int)
    day_dist["share"] = day_dist["share"].fillna(0)

    delay_dist = delivered.groupby("delay_bucket", as_index=False).agg(
        orders=("order_id", "size"),
        avg_review_score=("review_score", "mean"),
        avg_delay_days=("delay_days", "mean"),
        avg_delivery_days=("delivery_days", "mean"),
    )
    delay_dist["share"] = _div(delay_dist["orders"], delay_dist["orders"].sum())
    delay_dist["delay_bucket"] = pd.Categorical(
        delay_dist["delay_bucket"], categories=DELAY_LABELS, ordered=True
    )
    delay_dist = (
        delay_dist.set_index("delay_bucket")
        .reindex(DELAY_LABELS)
        .rename_axis("delay_bucket")
        .reset_index()
    )
    delay_dist["orders"] = delay_dist["orders"].fillna(0).astype(int)
    delay_dist["share"] = delay_dist["share"].fillna(0)

    valid = scope.loc[scope["is_valid_order"]].copy()
    valid["late_flag"] = _late_flag(valid)
    value_dist = valid.groupby("order_value_band", as_index=False).agg(
        orders=("order_id", "size"),
        gmv=("merchandise_value", "sum"),
        gross_order_value=("gross_order_value", "sum"),
        avg_items_per_order=("item_count", "mean"),
        avg_review_score=("review_score", "mean"),
        delivered_with_dates=("delay_days", "count"),
        late_orders=("late_flag", "sum"),
    )
    value_dist["share"] = _div(value_dist["orders"], value_dist["orders"].sum())
    value_dist["aov"] = _div(value_dist["gross_order_value"], value_dist["orders"])
    value_dist["late_rate"] = _div(
        value_dist["late_orders"], value_dist["delivered_with_dates"]
    )
    value_dist["order_value_band"] = pd.Categorical(
        value_dist["order_value_band"], categories=ORDER_VALUE_LABELS, ordered=True
    )
    value_dist = (
        value_dist.set_index("order_value_band")
        .reindex(ORDER_VALUE_LABELS)
        .rename_axis("order_value_band")
        .reset_index()
    )
    value_dist["orders"] = value_dist["orders"].fillna(0).astype(int)
    value_dist["share"] = value_dist["share"].fillna(0)

    return (
        _round_table(day_dist),
        _round_table(delay_dist),
        _round_table(value_dist),
    )


# ---------------------------------------------------------------------------
# Customer segmentation and cohort tables
# ---------------------------------------------------------------------------
def build_customer_tables(
    rfm: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """RFM segment summary, score heatmap, and repeat-purchase summary."""

    segment = rfm.groupby(["rfm_segment", "rfm_segment_cn"], as_index=False).agg(
        customers=("customer_unique_id", "nunique"),
        orders=("frequency", "sum"),
        revenue=("monetary", "sum"),
        avg_monetary=("monetary", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_recency_days=("recency_days", "mean"),
        avg_review_score=("avg_review_score", "mean"),
        repeat_customers=("customer_type", lambda values: int((values == "Repeat").sum())),
    )
    segment["customer_share"] = _div(
        segment["customers"], segment["customers"].sum()
    )
    segment["revenue_share"] = _div(segment["revenue"], segment["revenue"].sum())
    segment["repeat_rate"] = _div(segment["repeat_customers"], segment["customers"])
    segment = segment.sort_values("revenue", ascending=False).reset_index(drop=True)

    matrix = rfm.groupby(["r_score", "f_score"], as_index=False).agg(
        customers=("customer_unique_id", "nunique"),
        revenue=("monetary", "sum"),
        avg_monetary=("monetary", "mean"),
    )
    matrix["customer_share"] = _div(matrix["customers"], matrix["customers"].sum())

    repeat = rfm.groupby("customer_type", as_index=False).agg(
        customers=("customer_unique_id", "nunique"),
        orders=("frequency", "sum"),
        revenue=("monetary", "sum"),
        avg_monetary=("monetary", "mean"),
        avg_frequency=("frequency", "mean"),
        avg_recency_days=("recency_days", "mean"),
        avg_review_score=("avg_review_score", "mean"),
    )
    repeat["customer_share"] = _div(repeat["customers"], repeat["customers"].sum())
    repeat["revenue_share"] = _div(repeat["revenue"], repeat["revenue"].sum())
    return _round_table(segment), _round_table(matrix), _round_table(repeat)


# ---------------------------------------------------------------------------
# Public orchestration
# ---------------------------------------------------------------------------
def build_all_metrics(data: PreparedData) -> dict[str, pd.DataFrame]:
    """Build every chart-ready aggregate table."""

    logger.info("Building executive overview and monthly KPIs")
    overview = build_overview(data.orders_master, data.items)
    monthly = build_monthly_kpis(data.orders_master)
    status = build_order_status_summary(data.orders_master)

    logger.info("Building category / state / seller / product tables")
    category = build_category_kpis(data.order_category)
    category_monthly = build_category_monthly(data.order_category)
    state, state_monthly = build_state_kpis(data.orders_master, data.rfm)
    seller, seller_pareto = build_seller_kpis(data.order_seller)
    product, top_products = build_product_kpis(data.items)

    logger.info("Building payment / review / delivery tables")
    payment, installments, reconciliation = build_payment_kpis(
        data.payment_rows, data.orders_master
    )
    review_dist, review_monthly, review_delivery, review_delay = build_review_tables(
        data.orders_master
    )
    delivery_dist, delay_dist, value_dist = build_delivery_tables(data.orders_master)

    logger.info("Building customer segment tables")
    segment, rfm_matrix, repeat = build_customer_tables(data.rfm)

    return {
        "overview_kpis": overview,
        "monthly_kpis": monthly,
        "order_status_summary": status,
        "category_kpis": category,
        "category_monthly": category_monthly,
        "state_kpis": state,
        "state_monthly": state_monthly,
        "seller_kpis": seller,
        "seller_pareto": seller_pareto,
        "product_kpis": product,
        "top_products": top_products,
        "payment_type_kpis": payment,
        "installment_distribution": installments,
        "payment_reconciliation": reconciliation,
        "review_distribution": review_dist,
        "review_monthly": review_monthly,
        "review_by_delivery": review_delivery,
        "review_by_delay_bucket": review_delay,
        "delivery_distribution": delivery_dist,
        "delivery_delay_distribution": delay_dist,
        "order_value_distribution": value_dist,
        "rfm_segment_summary": segment,
        "rfm_score_matrix": rfm_matrix,
        "customer_repeat_summary": repeat,
        "cohort_retention": data.cohort,
        "cohort_retention_wide": data.cohort_wide,
    }