"""Read, validate, and lightly normalise the raw Olist CSV files."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .config import (
    DATE_COLUMNS,
    EXPECTED_COLUMNS,
    FILENAMES,
    STRING_COLUMNS,
)

logger = logging.getLogger(__name__)


def _build_dtype_map(table: str) -> dict[str, str]:
    """Use string dtype for identifiers and categorical text columns."""

    return {column: "string" for column in STRING_COLUMNS.get(table, [])}


def _validate_columns(table: str, df: pd.DataFrame, path: Path) -> None:
    required = EXPECTED_COLUMNS[table]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(
            f"{path.name} is missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )


def _normalise_text(df: pd.DataFrame) -> pd.DataFrame:
    """Lower-case city names and normalise state/payment/status codes."""

    for column in ("customer_city", "seller_city", "geolocation_city"):
        if column in df.columns:
            df[column] = df[column].astype("string").str.strip().str.lower()

    for column in ("customer_state", "seller_state", "geolocation_state"):
        if column in df.columns:
            df[column] = df[column].astype("string").str.strip().str.upper()

    for column in ("order_status", "payment_type"):
        if column in df.columns:
            df[column] = df[column].astype("string").str.strip().str.lower()

    for column in ("product_category_name", "product_category_name_english"):
        if column in df.columns:
            df[column] = df[column].astype("string").str.strip().str.lower()

    for column in (
        "customer_zip_code_prefix",
        "seller_zip_code_prefix",
        "geolocation_zip_code_prefix",
    ):
        if column in df.columns:
            # The source is already 5 characters; zfill keeps the code safe
            # if a user supplies a file where leading zeros were dropped.
            df[column] = df[column].astype("string").str.strip().str.zfill(5)

    return df


def read_tables(raw_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Load all nine source tables.

    Parameters
    ----------
    raw_dir:
        Folder containing the ``olist_*`` CSV files.

    Returns
    -------
    dict[str, pandas.DataFrame]
        Keys are the short table names from ``config.FILENAMES``.

    Raises
    ------
    FileNotFoundError
        If a required CSV is missing.
    ValueError
        If a required column is missing.
    """

    raw_path = Path(raw_dir)
    tables: dict[str, pd.DataFrame] = {}

    for table, filename in FILENAMES.items():
        path = raw_path / filename
        if not path.exists():
            raise FileNotFoundError(f"Required source file not found: {path}")

        logger.info("Reading %s (%s)", filename, path)
        df = pd.read_csv(
            path,
            dtype=_build_dtype_map(table),
            low_memory=False,
        )
        _validate_columns(table, df, path)

        for column in DATE_COLUMNS.get(table, []):
            df[column] = pd.to_datetime(df[column], errors="coerce")

        df = _normalise_text(df)
        tables[table] = df

        logger.info("  %s rows x %s columns", f"{len(df):,}", len(df.columns))

    _log_date_ranges(tables)
    return tables


def _log_date_ranges(tables: dict[str, pd.DataFrame]) -> None:
    orders = tables["orders"]
    logger.info(
        "Order purchase range: %s -> %s",
        orders["order_purchase_timestamp"].min(),
        orders["order_purchase_timestamp"].max(),
    )
    logger.info(
        "Order status counts: %s",
        orders["order_status"].value_counts(dropna=False).to_dict(),
    )