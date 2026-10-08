"""
=============================================================================
PHASE 1 — DATA UNDERSTANDING
=============================================================================
Script:   01_data_understanding.py
Dataset:  UCI Online Retail (D:\OnlineRetail.csv)
Purpose:  Comprehensive data profiling before building the ETL pipeline.
Author:   ETL Pipeline — Automated
Date:     2026-05-27
=============================================================================
Outputs:
  - docs/data_dictionary.md          — Business-context column definitions
  - outputs/reports/data_quality_report.txt — Full quality assessment
  - Console output                   — All findings printed live
=============================================================================
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from collections import OrderedDict

# Fix Windows console encoding for Unicode characters
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
RAW_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "OnlineRetail.csv")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "outputs", "reports")
ENCODING = "latin-1"  # Required for this dataset — contains £ and accented chars

# Ensure output directories exist
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def separator(title: str, char: str = "=", width: int = 80) -> str:
    """Return a formatted section separator for console/report output."""
    line = char * width
    return f"\n{line}\n  {title}\n{line}"


def print_and_collect(msg: str, report_lines: list) -> None:
    """Print to console AND collect for the text report."""
    print(msg)
    report_lines.append(msg)


# =====================================================================
# MAIN PIPELINE
# =====================================================================
def main():
    start_time = datetime.now()
    report: list[str] = []  # accumulator for the data quality report

    header = separator("PHASE 1 — DATA UNDERSTANDING", "=", 80)
    print_and_collect(header, report)
    print_and_collect(f"  Run started : {start_time.strftime('%Y-%m-%d %H:%M:%S')}", report)
    print_and_collect(f"  Source file : {RAW_DATA_PATH}", report)

    # ------------------------------------------------------------------
    # 1. LOAD RAW DATA
    # ------------------------------------------------------------------
    section = separator("1. LOADING RAW DATA")
    print_and_collect(section, report)

    try:
        df = pd.read_csv(RAW_DATA_PATH, encoding=ENCODING)
        print_and_collect(f"  ✓ Successfully loaded {len(df):,} rows × {len(df.columns)} columns", report)
    except FileNotFoundError:
        print_and_collect(f"  ✗ ERROR: File not found at {RAW_DATA_PATH}", report)
        sys.exit(1)
    except Exception as e:
        print_and_collect(f"  ✗ ERROR loading file: {e}", report)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 2. BASIC SHAPE & STRUCTURE
    # ------------------------------------------------------------------
    section = separator("2. BASIC SHAPE & STRUCTURE")
    print_and_collect(section, report)
    print_and_collect(f"  Rows       : {df.shape[0]:,}", report)
    print_and_collect(f"  Columns    : {df.shape[1]}", report)
    print_and_collect(f"  Column list: {list(df.columns)}", report)

    # Memory usage
    mem_bytes = df.memory_usage(deep=True).sum()
    mem_mb = mem_bytes / (1024 ** 2)
    print_and_collect(f"\n  Total memory usage: {mem_mb:.2f} MB ({mem_bytes:,} bytes)", report)
    print_and_collect("\n  Per-column memory usage:", report)
    for col in df.columns:
        col_mem = df[col].memory_usage(deep=True)
        print_and_collect(f"    {col:<15} : {col_mem / 1024:.1f} KB", report)

    # ------------------------------------------------------------------
    # 3. DATA TYPES
    # ------------------------------------------------------------------
    section = separator("3. DATA TYPES (as loaded)")
    print_and_collect(section, report)
    for col in df.columns:
        print_and_collect(f"  {col:<15} : {df[col].dtype}", report)

    # First 5 rows for visual inspection
    print_and_collect("\n  First 5 rows (sample):", report)
    sample_str = df.head(5).to_string(index=False)
    for line in sample_str.split("\n"):
        print_and_collect(f"    {line}", report)

    # ------------------------------------------------------------------
    # 4. MISSING VALUES ANALYSIS
    # ------------------------------------------------------------------
    section = separator("4. MISSING VALUES ANALYSIS")
    print_and_collect(section, report)

    total_rows = len(df)
    missing_info = []
    for col in df.columns:
        n_missing = df[col].isna().sum()
        pct = (n_missing / total_rows) * 100
        missing_info.append((col, n_missing, pct))
        status = "⚠" if n_missing > 0 else "✓"
        print_and_collect(
            f"  {status} {col:<15} : {n_missing:>8,} missing  ({pct:>6.2f}%)", report
        )

    total_missing = df.isna().sum().sum()
    total_cells = total_rows * len(df.columns)
    print_and_collect(
        f"\n  Overall: {total_missing:,} missing values out of {total_cells:,} cells "
        f"({(total_missing / total_cells) * 100:.2f}%)", report
    )

    # Business impact commentary
    print_and_collect("\n  Business Impact Notes:", report)
    for col, n_miss, pct in missing_info:
        if n_miss == 0:
            continue
        if col == "CustomerID":
            print_and_collect(
                f"    • CustomerID — {n_miss:,} rows ({pct:.1f}%) have no customer linkage.\n"
                f"      These are likely guest/anonymous purchases or POS transactions.\n"
                f"      Impact: Cannot build customer-level analytics for these rows.\n"
                f"      Recommendation: Keep for revenue analysis, flag for customer analytics.",
                report,
            )
        elif col == "Description":
            print_and_collect(
                f"    • Description — {n_miss:,} rows ({pct:.1f}%) have no product description.\n"
                f"      Likely data-entry gaps or system-generated adjustment records.\n"
                f"      Impact: Product dimension table will have gaps.\n"
                f"      Recommendation: Impute from StockCode lookup or mark 'UNKNOWN'.",
                report,
            )

    # ------------------------------------------------------------------
    # 5. DUPLICATE DETECTION
    # ------------------------------------------------------------------
    section = separator("5. DUPLICATE DETECTION")
    print_and_collect(section, report)

    # Exact duplicates (all columns identical)
    exact_dupes = df.duplicated().sum()
    print_and_collect(f"  Exact duplicate rows (all columns): {exact_dupes:,}", report)
    if exact_dupes > 0:
        print_and_collect(
            f"    → {exact_dupes:,} rows are perfect copies of earlier rows.\n"
            f"    → Represent {(exact_dupes / total_rows) * 100:.2f}% of total data.\n"
            f"    → Recommendation: Remove in ETL Transform phase.", report
        )

    # Partial duplicates — same invoice + product (potential double-scan)
    partial_keys = ["InvoiceNo", "StockCode", "Quantity", "InvoiceDate"]
    existing_keys = [k for k in partial_keys if k in df.columns]
    partial_dupes = df.duplicated(subset=existing_keys).sum()
    print_and_collect(
        f"\n  Partial duplicates ({', '.join(existing_keys)}): {partial_dupes:,}", report
    )
    if partial_dupes > exact_dupes:
        print_and_collect(
            f"    → {partial_dupes - exact_dupes:,} additional rows share the same\n"
            f"      invoice + product + qty + date but differ in other fields.\n"
            f"    → May indicate legitimate multi-line items or data quality issues.", report
        )

    # ------------------------------------------------------------------
    # 6. UNIQUE VALUE COUNTS & CARDINALITY
    # ------------------------------------------------------------------
    section = separator("6. UNIQUE VALUE COUNTS & CARDINALITY")
    print_and_collect(section, report)
    for col in df.columns:
        n_unique = df[col].nunique()
        ratio = n_unique / total_rows
        card_label = "HIGH" if ratio > 0.5 else ("MEDIUM" if ratio > 0.05 else "LOW")
        print_and_collect(
            f"  {col:<15} : {n_unique:>8,} unique values  (cardinality: {card_label})", report
        )

    # ------------------------------------------------------------------
    # 7. NUMERIC COLUMN STATISTICS
    # ------------------------------------------------------------------
    section = separator("7. NUMERIC COLUMN STATISTICS")
    print_and_collect(section, report)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        stats = df[numeric_cols].describe().T
        stats["skew"] = df[numeric_cols].skew()
        stats["kurtosis"] = df[numeric_cols].kurtosis()
        stats_str = stats.to_string()
        for line in stats_str.split("\n"):
            print_and_collect(f"    {line}", report)
    else:
        print_and_collect("  No numeric columns found.", report)

    # Flag anomalies
    print_and_collect("\n  Anomaly Flags:", report)
    if "Quantity" in df.columns:
        neg_qty = (df["Quantity"] < 0).sum()
        zero_qty = (df["Quantity"] == 0).sum()
        print_and_collect(f"    • Quantity < 0  : {neg_qty:,} rows (returns/cancellations)", report)
        print_and_collect(f"    • Quantity == 0 : {zero_qty:,} rows (adjustments)", report)
    if "UnitPrice" in df.columns:
        neg_price = (df["UnitPrice"] < 0).sum()
        zero_price = (df["UnitPrice"] == 0).sum()
        print_and_collect(f"    • UnitPrice < 0 : {neg_price:,} rows", report)
        print_and_collect(f"    • UnitPrice == 0: {zero_price:,} rows (free items / samples)", report)

    # ------------------------------------------------------------------
    # 8. CATEGORICAL / TEXT COLUMN ANALYSIS
    # ------------------------------------------------------------------
    section = separator("8. CATEGORICAL / TEXT COLUMN ANALYSIS")
    print_and_collect(section, report)
    cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
    for col in cat_cols:
        print_and_collect(f"\n  Column: {col}", report)
        print_and_collect(f"    Unique values: {df[col].nunique():,}", report)
        top_vals = df[col].value_counts().head(10)
        print_and_collect(f"    Top 10 values:", report)
        for val, cnt in top_vals.items():
            pct = (cnt / total_rows) * 100
            print_and_collect(f"      {str(val):<40} : {cnt:>7,}  ({pct:.2f}%)", report)

    # Cancellation invoice pattern
    if "InvoiceNo" in df.columns:
        cancel_mask = df["InvoiceNo"].astype(str).str.startswith("C")
        n_cancel = cancel_mask.sum()
        print_and_collect(
            f"\n  Cancellation invoices (start with 'C'): {n_cancel:,} "
            f"({(n_cancel / total_rows) * 100:.2f}%)", report
        )

    # Country distribution
    if "Country" in df.columns:
        n_countries = df["Country"].nunique()
        top_country = df["Country"].value_counts().head(1)
        print_and_collect(f"\n  Countries represented: {n_countries}", report)
        for c, cnt in top_country.items():
            print_and_collect(
                f"    Dominant market: {c} — {cnt:,} transactions ({(cnt / total_rows) * 100:.1f}%)", report
            )

    # ------------------------------------------------------------------
    # 9. DATE RANGE ANALYSIS
    # ------------------------------------------------------------------
    section = separator("9. DATE RANGE ANALYSIS")
    print_and_collect(section, report)
    if "InvoiceDate" in df.columns:
        try:
            dates = pd.to_datetime(df["InvoiceDate"], format="mixed", dayfirst=False)
            print_and_collect(f"  Earliest transaction : {dates.min()}", report)
            print_and_collect(f"  Latest transaction   : {dates.max()}", report)
            date_range = dates.max() - dates.min()
            print_and_collect(f"  Date span            : {date_range.days} days (~{date_range.days // 30} months)", report)

            # Monthly distribution
            monthly = dates.dt.to_period("M").value_counts().sort_index()
            print_and_collect("\n  Monthly transaction volume:", report)
            for period, cnt in monthly.items():
                bar = "█" * max(1, int(cnt / monthly.max() * 40))
                print_and_collect(f"    {period} : {cnt:>7,}  {bar}", report)
        except Exception as e:
            print_and_collect(f"  ⚠ Could not parse InvoiceDate: {e}", report)

    # ------------------------------------------------------------------
    # 10. FACT vs DIMENSION TABLE IDENTIFICATION
    # ------------------------------------------------------------------
    section = separator("10. FACT vs DIMENSION TABLE IDENTIFICATION")
    print_and_collect(section, report)
    print_and_collect("""
  This flat file contains a DENORMALIZED transactional dataset.
  For a proper star-schema data warehouse, we decompose it as follows:

  ┌─────────────────────────────────────────────────────────────┐
  │                     STAR SCHEMA DESIGN                     │
  ├─────────────────────────────────────────────────────────────┤
  │                                                             │
  │   dim_customers ──┐                                         │
  │     CustomerID    │                                         │
  │     Country       ├──►  fact_transactions                   │
  │     FirstPurchase │       InvoiceNo                         │
  │                   │       StockCode  ◄── dim_products       │
  │   dim_date ───────┤       CustomerID      StockCode         │
  │     Date          │       DateKey          Description      │
  │     Year          │       Quantity         AvgUnitPrice     │
  │     Month         │       UnitPrice                         │
  │     Quarter       │       TotalAmount                       │
  │     DayOfWeek     │       IsCancellation                    │
  │                   │                                         │
  └─────────────────────────────────────────────────────────────┘

  FACT TABLE (fact_transactions):
    - Grain: One row per invoice line item
    - Measures: Quantity, UnitPrice, TotalAmount
    - Foreign keys: CustomerID, StockCode, DateKey
    - Additive measures allow SUM, AVG, COUNT aggregations

  DIMENSION TABLES:
    - dim_customers : Customer attributes & geography
    - dim_products  : Product catalog with descriptions & pricing
    - dim_date      : Calendar dimension for time-based analysis
""", report)

    # ------------------------------------------------------------------
    # 11. BUSINESS-CONTEXT COLUMN EXPLANATIONS
    # ------------------------------------------------------------------
    section = separator("11. BUSINESS-CONTEXT COLUMN EXPLANATIONS")
    print_and_collect(section, report)

    column_explanations = OrderedDict([
        ("InvoiceNo", (
            "6-digit invoice identifier. Uniquely identifies each transaction.\n"
            "      Invoices starting with 'C' indicate CANCELLATIONS/RETURNS.\n"
            "      Multiple line items can share the same InvoiceNo (one invoice, many products).\n"
            "      Business use: Order tracking, return rate analysis."
        )),
        ("StockCode", (
            "Product code (typically 5-digit numeric or alphanumeric).\n"
            "      Acts as the primary product identifier / SKU.\n"
            "      Special codes exist: POST (postage), DOT (dotcom postage), M (manual adjustment),\n"
            "      BANKCHARGES, AMAZONFEE, etc.\n"
            "      Business use: Product-level revenue analysis, inventory management."
        )),
        ("Description", (
            "Free-text product description (e.g., 'WHITE HANGING HEART T-LIGHT HOLDER').\n"
            "      Not perfectly standardized — same product may have slight description variations.\n"
            "      Some rows have NULL descriptions (data quality issue).\n"
            "      Business use: Product categorization, search, catalog management."
        )),
        ("Quantity", (
            "Number of units purchased in this line item.\n"
            "      POSITIVE values = sales/purchases.\n"
            "      NEGATIVE values = returns/cancellations (paired with 'C' invoices).\n"
            "      Business use: Sales volume, return rate, demand forecasting."
        )),
        ("InvoiceDate", (
            "Timestamp of when the invoice was generated (MM/DD/YYYY HH:MM format).\n"
            "      Covers Dec 2010 to Dec 2011 (~13 months of data).\n"
            "      Business use: Time-series analysis, seasonality, peak hours."
        )),
        ("UnitPrice", (
            "Price per unit in GBP (British Pounds Sterling).\n"
            "      Most values are positive; zero prices indicate free items or samples.\n"
            "      Negative prices are rare anomalies.\n"
            "      Business use: Revenue calculation, price elasticity, margin analysis."
        )),
        ("CustomerID", (
            "5-digit customer identifier (float due to NaN values).\n"
            "      ~25% of rows have NULL CustomerID (anonymous/guest purchases).\n"
            "      Business use: Customer segmentation, RFM analysis, lifetime value."
        )),
        ("Country", (
            "Country where the customer is located.\n"
            "      ~90% of transactions are from 'United Kingdom'.\n"
            "      38 countries total — international e-commerce presence.\n"
            "      Business use: Geographic revenue analysis, market expansion decisions."
        )),
    ])

    for col, explanation in column_explanations.items():
        print_and_collect(f"\n  {col}:", report)
        for line in explanation.split("\n"):
            print_and_collect(f"    {line.strip()}", report)

    # ------------------------------------------------------------------
    # 12. GENERATE DATA DICTIONARY (Markdown)
    # ------------------------------------------------------------------
    section = separator("12. SAVING DATA DICTIONARY")
    print_and_collect(section, report)

    dict_path = os.path.join(DOCS_DIR, "data_dictionary.md")
    with open(dict_path, "w", encoding="utf-8") as f:
        f.write("# Data Dictionary — UCI Online Retail Dataset\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n")
        f.write(f"**Source:** `{RAW_DATA_PATH}`  \n")
        f.write(f"**Records:** {total_rows:,}  \n")
        f.write(f"**Columns:** {len(df.columns)}  \n\n")
        f.write("---\n\n")

        f.write("## Column Definitions\n\n")
        f.write("| # | Column | Data Type | Non-Null Count | Null Count | Null % | Unique Values | Description |\n")
        f.write("|---|--------|-----------|----------------|------------|--------|---------------|-------------|\n")
        for i, col in enumerate(df.columns, 1):
            dtype = str(df[col].dtype)
            non_null = df[col].notna().sum()
            n_null = df[col].isna().sum()
            pct_null = f"{(n_null / total_rows) * 100:.2f}%"
            n_unique = df[col].nunique()
            # Short description for the table
            short_desc = {
                "InvoiceNo": "6-digit invoice number; 'C' prefix = cancellation",
                "StockCode": "Product/item code (SKU)",
                "Description": "Product name/description (free text)",
                "Quantity": "Units purchased (negative = return)",
                "InvoiceDate": "Transaction timestamp (MM/DD/YYYY HH:MM)",
                "UnitPrice": "Price per unit in GBP",
                "CustomerID": "5-digit customer ID (nullable)",
                "Country": "Customer's country of residence",
            }.get(col, "—")
            f.write(f"| {i} | `{col}` | `{dtype}` | {non_null:,} | {n_null:,} | {pct_null} | {n_unique:,} | {short_desc} |\n")

        f.write("\n---\n\n")
        f.write("## Detailed Business Context\n\n")
        for col, explanation in column_explanations.items():
            f.write(f"### `{col}`\n\n")
            for line in explanation.split("\n"):
                f.write(f"{line.strip()}  \n")
            f.write("\n")

        f.write("---\n\n")
        f.write("## Data Quality Summary\n\n")
        f.write(f"- **Total rows:** {total_rows:,}\n")
        f.write(f"- **Exact duplicates:** {exact_dupes:,}\n")
        f.write(f"- **Total missing values:** {total_missing:,} ({(total_missing / total_cells) * 100:.2f}%)\n")
        if "Quantity" in df.columns:
            neg_qty = (df["Quantity"] < 0).sum()
            f.write(f"- **Negative quantities (returns):** {neg_qty:,}\n")
        if "InvoiceNo" in df.columns:
            cancel_mask = df["InvoiceNo"].astype(str).str.startswith("C")
            f.write(f"- **Cancellation invoices:** {cancel_mask.sum():,}\n")
        f.write(f"\n---\n\n")
        f.write("## Proposed Star Schema\n\n")
        f.write("| Table | Type | Key | Description |\n")
        f.write("|-------|------|-----|-------------|\n")
        f.write("| `fact_transactions` | Fact | InvoiceNo + StockCode | Cleaned line-item transactions |\n")
        f.write("| `dim_customers` | Dimension | CustomerID | Customer attributes & geography |\n")
        f.write("| `dim_products` | Dimension | StockCode | Product catalog |\n")
        f.write("| `dim_date` | Dimension | Date | Calendar dimension |\n")

    print_and_collect(f"  ✓ Data dictionary saved to: {dict_path}", report)

    # ------------------------------------------------------------------
    # 13. SAVE DATA QUALITY REPORT
    # ------------------------------------------------------------------
    section = separator("13. SAVING DATA QUALITY REPORT")
    print_and_collect(section, report)

    report_path = os.path.join(REPORTS_DIR, "data_quality_report.txt")
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Add footer
    footer = separator("END OF DATA QUALITY REPORT")
    print_and_collect(footer, report)
    print_and_collect(f"  Completed : {end_time.strftime('%Y-%m-%d %H:%M:%S')}", report)
    print_and_collect(f"  Duration  : {duration:.1f} seconds", report)

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    print(f"\n  ✓ Data quality report saved to: {report_path}")
    print(f"\n{'=' * 80}")
    print(f"  PHASE 1 COMPLETE — All outputs generated successfully.")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
