# Data Dictionary — UCI Online Retail Dataset

**Generated:** 2026-10-02 19:27:51  
**Source:** `C:\Users\karth\Downloads\ETL ECOMMERCE\data\raw\OnlineRetail.csv`  
**Records:** 541,909  
**Columns:** 8  

---

## Column Definitions

| # | Column | Data Type | Non-Null Count | Null Count | Null % | Unique Values | Description |
|---|--------|-----------|----------------|------------|--------|---------------|-------------|
| 1 | `InvoiceNo` | `str` | 541,909 | 0 | 0.00% | 25,900 | 6-digit invoice number; 'C' prefix = cancellation |
| 2 | `StockCode` | `str` | 541,909 | 0 | 0.00% | 4,070 | Product/item code (SKU) |
| 3 | `Description` | `str` | 540,455 | 1,454 | 0.27% | 4,223 | Product name/description (free text) |
| 4 | `Quantity` | `int64` | 541,909 | 0 | 0.00% | 722 | Units purchased (negative = return) |
| 5 | `InvoiceDate` | `str` | 541,909 | 0 | 0.00% | 23,260 | Transaction timestamp (MM/DD/YYYY HH:MM) |
| 6 | `UnitPrice` | `float64` | 541,909 | 0 | 0.00% | 1,630 | Price per unit in GBP |
| 7 | `CustomerID` | `float64` | 406,829 | 135,080 | 24.93% | 4,372 | 5-digit customer ID (nullable) |
| 8 | `Country` | `str` | 541,909 | 0 | 0.00% | 38 | Customer's country of residence |

---

## Detailed Business Context

### `InvoiceNo`

6-digit invoice identifier. Uniquely identifies each transaction.  
Invoices starting with 'C' indicate CANCELLATIONS/RETURNS.  
Multiple line items can share the same InvoiceNo (one invoice, many products).  
Business use: Order tracking, return rate analysis.  

### `StockCode`

Product code (typically 5-digit numeric or alphanumeric).  
Acts as the primary product identifier / SKU.  
Special codes exist: POST (postage), DOT (dotcom postage), M (manual adjustment),  
BANKCHARGES, AMAZONFEE, etc.  
Business use: Product-level revenue analysis, inventory management.  

### `Description`

Free-text product description (e.g., 'WHITE HANGING HEART T-LIGHT HOLDER').  
Not perfectly standardized — same product may have slight description variations.  
Some rows have NULL descriptions (data quality issue).  
Business use: Product categorization, search, catalog management.  

### `Quantity`

Number of units purchased in this line item.  
POSITIVE values = sales/purchases.  
NEGATIVE values = returns/cancellations (paired with 'C' invoices).  
Business use: Sales volume, return rate, demand forecasting.  

### `InvoiceDate`

Timestamp of when the invoice was generated (MM/DD/YYYY HH:MM format).  
Covers Dec 2010 to Dec 2011 (~13 months of data).  
Business use: Time-series analysis, seasonality, peak hours.  

### `UnitPrice`

Price per unit in GBP (British Pounds Sterling).  
Most values are positive; zero prices indicate free items or samples.  
Negative prices are rare anomalies.  
Business use: Revenue calculation, price elasticity, margin analysis.  

### `CustomerID`

5-digit customer identifier (float due to NaN values).  
~25% of rows have NULL CustomerID (anonymous/guest purchases).  
Business use: Customer segmentation, RFM analysis, lifetime value.  

### `Country`

Country where the customer is located.  
~90% of transactions are from 'United Kingdom'.  
38 countries total — international e-commerce presence.  
Business use: Geographic revenue analysis, market expansion decisions.  

---

## Data Quality Summary

- **Total rows:** 541,909
- **Exact duplicates:** 5,268
- **Total missing values:** 136,534 (3.15%)
- **Negative quantities (returns):** 10,624
- **Cancellation invoices:** 9,288

---

## Proposed Star Schema

| Table | Type | Key | Description |
|-------|------|-----|-------------|
| `fact_transactions` | Fact | InvoiceNo + StockCode | Cleaned line-item transactions |
| `dim_customers` | Dimension | CustomerID | Customer attributes & geography |
| `dim_products` | Dimension | StockCode | Product catalog |
| `dim_date` | Dimension | Date | Calendar dimension |
