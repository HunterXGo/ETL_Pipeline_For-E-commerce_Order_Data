"""
=============================================================================
PHASE 2 & 3 — ETL PIPELINE (Extract, Transform, Load)
=============================================================================
Script:   02_etl_pipeline.py
Dataset:  UCI Online Retail (D:\OnlineRetail.csv)
Purpose:  Production-grade ETL pipeline — clean, transform, and load data
          into star-schema fact and dimension tables.
Author:   Analytics Pipeline — Automated
Date:     2026-05-27
=============================================================================
Outputs:
  - data/cleaned/fact_transactions.csv
  - data/dashboard_ready/dim_customers.csv
  - data/dashboard_ready/dim_products.csv
  - data/dashboard_ready/dim_date.csv
  - outputs/logs/etl_log.txt
=============================================================================
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
RAW_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "OnlineRetail.csv")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEANED_DIR = os.path.join(PROJECT_ROOT, "data", "cleaned")
DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "data", "dashboard_ready")
LOGS_DIR = os.path.join(PROJECT_ROOT, "outputs", "logs")
ENCODING = "latin-1"

# Ensure directories exist
for d in [CLEANED_DIR, DASHBOARD_DIR, LOGS_DIR]:
    os.makedirs(d, exist_ok=True)

# ---------------------------------------------------------------------------
# LOGGING SETUP
# ---------------------------------------------------------------------------
log_path = os.path.join(LOGS_DIR, "etl_log.txt")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[
        logging.FileHandler(log_path, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("ETL_Pipeline")


def separator(title):
    line = "=" * 80
    logger.info(f"\n{line}\n  {title}\n{line}")


# =====================================================================
# PHASE: EXTRACT
# =====================================================================
def extract(path):
    """Load raw CSV and validate schema."""
    separator("EXTRACT PHASE")
    
    logger.info(f"Loading raw data from: {path}")
    try:
        df = pd.read_csv(path, encoding=ENCODING)
        logger.info(f"✓ Loaded {len(df):,} rows × {len(df.columns)} columns")
    except Exception as e:
        logger.error(f"✗ Failed to load data: {e}")
        sys.exit(1)

    # Schema validation
    expected_cols = ["InvoiceNo", "StockCode", "Description", "Quantity",
                     "InvoiceDate", "UnitPrice", "CustomerID", "Country"]
    actual_cols = list(df.columns)
    
    if actual_cols == expected_cols:
        logger.info("✓ Schema validation PASSED — all expected columns present")
    else:
        missing = set(expected_cols) - set(actual_cols)
        extra = set(actual_cols) - set(expected_cols)
        if missing:
            logger.warning(f"⚠ Missing columns: {missing}")
        if extra:
            logger.warning(f"⚠ Extra columns: {extra}")

    # Data quality baseline
    mem_before = df.memory_usage(deep=True).sum() / (1024**2)
    logger.info(f"  Memory usage: {mem_before:.1f} MB")
    logger.info(f"  Null counts:\n{df.isnull().sum().to_string()}")
    logger.info(f"  Dtypes:\n{df.dtypes.to_string()}")
    
    return df, mem_before


# =====================================================================
# PHASE: TRANSFORM
# =====================================================================
def transform(df):
    """Apply all cleaning and transformation rules."""
    separator("TRANSFORM PHASE")
    
    initial_rows = len(df)
    stats = {"initial_rows": initial_rows}
    
    # ---- 1. Convert InvoiceDate to datetime ----
    logger.info("Step 1: Converting InvoiceDate to datetime...")
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], format="mixed", dayfirst=False)
    logger.info(f"  ✓ Date range: {df['InvoiceDate'].min()} to {df['InvoiceDate'].max()}")
    
    # ---- 2. Flag Cancellations ----
    logger.info("Step 2: Flagging cancellation invoices...")
    df["InvoiceNo"] = df["InvoiceNo"].astype(str)
    df["IsCancellation"] = df["InvoiceNo"].str.startswith("C").astype(int)
    n_cancel = df["IsCancellation"].sum()
    logger.info(f"  ✓ {n_cancel:,} cancellation line items flagged ({n_cancel/len(df)*100:.1f}%)")
    stats["cancellations"] = n_cancel
    
    # ---- 3. Flag Returns (negative quantity) ----
    logger.info("Step 3: Flagging returns (negative quantity)...")
    df["IsReturn"] = (df["Quantity"] < 0).astype(int)
    n_returns = df["IsReturn"].sum()
    logger.info(f"  ✓ {n_returns:,} return line items flagged")
    stats["returns"] = n_returns
    
    # ---- 4. Remove exact duplicates ----
    logger.info("Step 4: Removing exact duplicate rows...")
    n_dupes = df.duplicated().sum()
    df = df.drop_duplicates()
    logger.info(f"  ✓ Removed {n_dupes:,} exact duplicates → {len(df):,} rows remaining")
    stats["duplicates_removed"] = n_dupes
    
    # ---- 5. Handle missing CustomerID ----
    logger.info("Step 5: Handling missing CustomerID...")
    null_cust = df["CustomerID"].isnull().sum()
    logger.info(f"  Found {null_cust:,} rows with null CustomerID ({null_cust/len(df)*100:.1f}%)")
    # Drop null CustomerID rows — cannot do customer analytics without them
    df = df.dropna(subset=["CustomerID"])
    df["CustomerID"] = df["CustomerID"].astype(int)
    logger.info(f"  ✓ Dropped null CustomerID rows → {len(df):,} rows remaining")
    stats["null_customerid_dropped"] = null_cust
    
    # ---- 6. Handle missing Description ----
    logger.info("Step 6: Handling missing Description...")
    null_desc = df["Description"].isnull().sum()
    df["Description"] = df["Description"].fillna("UNKNOWN")
    logger.info(f"  ✓ Filled {null_desc:,} null descriptions with 'UNKNOWN'")
    
    # ---- 7. Remove invalid transactions ----
    logger.info("Step 7: Removing invalid transactions...")
    # Remove zero/negative UnitPrice (except for valid returns)
    invalid_price = ((df["UnitPrice"] <= 0) & (df["IsCancellation"] == 0)).sum()
    df = df[~((df["UnitPrice"] <= 0) & (df["IsCancellation"] == 0))]
    logger.info(f"  ✓ Removed {invalid_price:,} rows with invalid UnitPrice → {len(df):,} remaining")
    stats["invalid_price_removed"] = invalid_price
    
    # ---- 8. Create calculated fields ----
    logger.info("Step 8: Creating calculated fields...")
    df["TotalAmount"] = df["Quantity"] * df["UnitPrice"]
    df["Year"] = df["InvoiceDate"].dt.year
    df["Month"] = df["InvoiceDate"].dt.month
    df["DayOfWeek"] = df["InvoiceDate"].dt.day_name()
    df["Hour"] = df["InvoiceDate"].dt.hour
    df["Quarter"] = df["InvoiceDate"].dt.quarter
    df["YearMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)
    df["DateKey"] = df["InvoiceDate"].dt.strftime("%Y-%m-%d")
    logger.info("  ✓ Added: TotalAmount, Year, Month, DayOfWeek, Hour, Quarter, YearMonth, DateKey")
    
    # ---- 9. Standardize Country names ----
    logger.info("Step 9: Standardizing country names...")
    df["Country"] = df["Country"].str.strip().str.title()
    # Fix known variants
    country_map = {
        "Eire": "Ireland",
        "Rsa": "South Africa",
        "Channel Islands": "Channel Islands",
        "Unspecified": "Unspecified",
    }
    df["Country"] = df["Country"].replace(country_map)
    n_countries = df["Country"].nunique()
    logger.info(f"  ✓ Standardized {n_countries} unique countries")
    
    # ---- 10. Optimize dtypes ----
    logger.info("Step 10: Optimizing data types for memory...")
    mem_before_opt = df.memory_usage(deep=True).sum() / (1024**2)
    df["StockCode"] = df["StockCode"].astype(str)
    df["Month"] = df["Month"].astype("int8")
    df["Hour"] = df["Hour"].astype("int8")
    df["Quarter"] = df["Quarter"].astype("int8")
    df["Year"] = df["Year"].astype("int16")
    df["IsCancellation"] = df["IsCancellation"].astype("int8")
    df["IsReturn"] = df["IsReturn"].astype("int8")
    df["Country"] = df["Country"].astype("category")
    df["DayOfWeek"] = df["DayOfWeek"].astype("category")
    mem_after_opt = df.memory_usage(deep=True).sum() / (1024**2)
    logger.info(f"  ✓ Memory: {mem_before_opt:.1f} MB → {mem_after_opt:.1f} MB ({(1-mem_after_opt/mem_before_opt)*100:.1f}% reduction)")
    stats["mem_before"] = mem_before_opt
    stats["mem_after"] = mem_after_opt
    stats["final_rows"] = len(df)
    
    return df, stats


# =====================================================================
# BUILD DIMENSION TABLES
# =====================================================================
def build_dimensions(df):
    """Create star-schema dimension tables from the fact data."""
    separator("BUILDING DIMENSION TABLES")
    
    # ---- dim_customers ----
    logger.info("Building dim_customers...")
    cust_agg = df.groupby("CustomerID").agg(
        Country=("Country", "first"),
        FirstPurchaseDate=("InvoiceDate", "min"),
        LastPurchaseDate=("InvoiceDate", "max"),
        TotalOrders=("InvoiceNo", "nunique"),
        TotalItems=("Quantity", "sum"),
        TotalRevenue=("TotalAmount", "sum"),
        AvgOrderValue=("TotalAmount", "mean"),
        UniqueProducts=("StockCode", "nunique"),
    ).reset_index()
    cust_agg["CustomerTenureDays"] = (cust_agg["LastPurchaseDate"] - cust_agg["FirstPurchaseDate"]).dt.days
    cust_agg["Country"] = cust_agg["Country"].astype(str)
    logger.info(f"  ✓ dim_customers: {len(cust_agg):,} customers")
    
    # ---- dim_products ----
    logger.info("Building dim_products...")
    prod_agg = df.groupby("StockCode").agg(
        Description=("Description", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "UNKNOWN"),
        AvgUnitPrice=("UnitPrice", "mean"),
        MinUnitPrice=("UnitPrice", "min"),
        MaxUnitPrice=("UnitPrice", "max"),
        TotalQtySold=("Quantity", "sum"),
        TotalRevenue=("TotalAmount", "sum"),
        TimesOrdered=("InvoiceNo", "nunique"),
    ).reset_index()
    logger.info(f"  ✓ dim_products: {len(prod_agg):,} products")
    
    # ---- dim_date ----
    logger.info("Building dim_date...")
    dates = df["InvoiceDate"].dt.date.unique()
    date_df = pd.DataFrame({"Date": sorted(dates)})
    date_df["Date"] = pd.to_datetime(date_df["Date"])
    date_df["Year"] = date_df["Date"].dt.year
    date_df["Month"] = date_df["Date"].dt.month
    date_df["MonthName"] = date_df["Date"].dt.month_name()
    date_df["Quarter"] = date_df["Date"].dt.quarter
    date_df["DayOfWeek"] = date_df["Date"].dt.day_name()
    date_df["DayOfMonth"] = date_df["Date"].dt.day
    date_df["WeekOfYear"] = date_df["Date"].dt.isocalendar().week.astype(int)
    date_df["IsWeekend"] = date_df["Date"].dt.dayofweek.isin([5, 6]).astype(int)
    date_df["DateKey"] = date_df["Date"].dt.strftime("%Y-%m-%d")
    logger.info(f"  ✓ dim_date: {len(date_df):,} unique dates")
    
    return cust_agg, prod_agg, date_df


# =====================================================================
# PHASE: LOAD
# =====================================================================
def load(df, dim_cust, dim_prod, dim_date, stats):
    """Save all outputs to disk."""
    separator("LOAD PHASE")
    
    # Save fact table
    fact_path = os.path.join(CLEANED_DIR, "fact_transactions.csv")
    df.to_csv(fact_path, index=False)
    logger.info(f"✓ Saved fact_transactions.csv ({len(df):,} rows)")
    
    # Save dimension tables
    cust_path = os.path.join(DASHBOARD_DIR, "dim_customers.csv")
    dim_cust.to_csv(cust_path, index=False)
    logger.info(f"✓ Saved dim_customers.csv ({len(dim_cust):,} rows)")
    
    prod_path = os.path.join(DASHBOARD_DIR, "dim_products.csv")
    dim_prod.to_csv(prod_path, index=False)
    logger.info(f"✓ Saved dim_products.csv ({len(dim_prod):,} rows)")
    
    date_path = os.path.join(DASHBOARD_DIR, "dim_date.csv")
    dim_date.to_csv(date_path, index=False)
    logger.info(f"✓ Saved dim_date.csv ({len(dim_date):,} rows)")
    
    # Print summary
    separator("ETL PIPELINE SUMMARY")
    logger.info(f"""
  ╔══════════════════════════════════════════════════════════════╗
  ║                    ETL PIPELINE RESULTS                     ║
  ╠══════════════════════════════════════════════════════════════╣
  ║  Input Rows          : {stats['initial_rows']:>10,}                         ║
  ║  Duplicates Removed  : {stats['duplicates_removed']:>10,}                         ║
  ║  Null CustID Dropped : {stats['null_customerid_dropped']:>10,}                         ║
  ║  Invalid Price Removed: {stats['invalid_price_removed']:>9,}                         ║
  ║  Cancellations Flagged: {stats['cancellations']:>9,}                         ║
  ║  Returns Flagged     : {stats['returns']:>10,}                         ║
  ║  Final Output Rows   : {stats['final_rows']:>10,}                         ║
  ║  Memory Optimized    : {stats['mem_before']:.1f} MB → {stats['mem_after']:.1f} MB            ║
  ╠══════════════════════════════════════════════════════════════╣
  ║  Fact Table          : fact_transactions.csv                ║
  ║  Dim: Customers      : dim_customers.csv ({len(dim_cust):,} records)       ║
  ║  Dim: Products       : dim_products.csv ({len(dim_prod):,} records)        ║
  ║  Dim: Date           : dim_date.csv ({len(dim_date):,} records)              ║
  ╚══════════════════════════════════════════════════════════════╝
    """)


# =====================================================================
# MAIN
# =====================================================================
def main():
    start = datetime.now()
    logger.info(f"ETL Pipeline started at {start.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # EXTRACT
    df, mem_raw = extract(RAW_DATA_PATH)
    
    # TRANSFORM
    df, stats = transform(df)
    
    # BUILD DIMENSIONS
    dim_cust, dim_prod, dim_date = build_dimensions(df)
    
    # LOAD
    load(df, dim_cust, dim_prod, dim_date, stats)
    
    end = datetime.now()
    duration = (end - start).total_seconds()
    logger.info(f"\nETL Pipeline completed in {duration:.1f} seconds")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
