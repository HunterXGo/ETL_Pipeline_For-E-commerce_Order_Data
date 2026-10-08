"""
==============================================================================
PHASE 4 — Deep Exploratory Data Analysis
E-Commerce Online Retail Pipeline
==============================================================================
Comprehensive EDA covering sales, customer, product, and order analytics
with professional-grade visualizations and business interpretations.
==============================================================================
"""

import matplotlib
matplotlib.use('Agg')

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ── Configuration ──────────────────────────────────────────────────────────
import os as _os
DATASET_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "data", "raw", "OnlineRetail.csv")
CHARTS_DIR = Path(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "outputs", "charts"))
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B']
PALETTE = sns.color_palette(COLORS)
sns.set_style("darkgrid")
plt.rcParams.update({
    'figure.figsize': (12, 6),
    'font.size': 11,
    'axes.titlesize': 14,
    'axes.titleweight': 'bold',
    'axes.labelsize': 12,
})


def clean_data(filepath=DATASET_PATH):
    """Load and clean the Online Retail dataset."""
    print("Loading dataset...")
    df = pd.read_csv(filepath, encoding='latin-1')
    print(f"  Raw rows: {len(df):,}")

    # Drop null CustomerID
    df = df.dropna(subset=['CustomerID'])
    df['CustomerID'] = df['CustomerID'].astype(int)

    # Remove duplicates
    df = df.drop_duplicates()

    # Convert InvoiceDate
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

    # Remove cancelled orders (InvoiceNo starting with 'C')
    df = df[~df['InvoiceNo'].astype(str).str.startswith('C')]

    # Remove non-positive Quantity / UnitPrice
    df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]

    # Create TotalAmount
    df['TotalAmount'] = df['Quantity'] * df['UnitPrice']

    print(f"  Clean rows: {len(df):,}")
    return df


def load_raw_with_cancellations(filepath=DATASET_PATH):
    """Load raw data keeping cancellations for cancellation rate analysis."""
    df = pd.read_csv(filepath, encoding='latin-1')
    df = df.dropna(subset=['CustomerID'])
    df['CustomerID'] = df['CustomerID'].astype(int)
    df = df.drop_duplicates()
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df['TotalAmount'] = df['Quantity'] * df['UnitPrice']
    df['IsCancelled'] = df['InvoiceNo'].astype(str).str.startswith('C').astype(int)
    return df


def annotate_bars(ax, fmt='{:,.0f}', fontsize=9, rotation=0):
    """Add value annotations on top of bars."""
    for bar in ax.patches:
        val = bar.get_height()
        if val > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2, val,
                fmt.format(val), ha='center', va='bottom',
                fontsize=fontsize, fontweight='bold', rotation=rotation
            )


# ============================================================================
# SALES ANALYSIS
# ============================================================================
def sales_analysis(df):
    print("\n" + "=" * 70)
    print("SALES ANALYSIS")
    print("=" * 70)

    total_revenue = df['TotalAmount'].sum()
    total_orders = df['InvoiceNo'].nunique()
    total_items = df['Quantity'].sum()

    print(f"\n  Total Revenue:     £{total_revenue:,.2f}")
    print(f"  Total Orders:      {total_orders:,}")
    print(f"  Total Items Sold:  {total_items:,}")
    print(f"  Avg Order Value:   £{total_revenue / total_orders:,.2f}")
    print(f"\n  📊 Business Insight: The business generated £{total_revenue/1e6:.1f}M in revenue")
    print(f"     across {total_orders:,} orders, with an average basket size of £{total_revenue/total_orders:.2f}.")

    # ── Monthly Revenue Trend ──
    df['YearMonth'] = df['InvoiceDate'].dt.to_period('M')
    monthly_rev = df.groupby('YearMonth')['TotalAmount'].sum().reset_index()
    monthly_rev['YearMonth'] = monthly_rev['YearMonth'].astype(str)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(monthly_rev['YearMonth'], monthly_rev['TotalAmount'],
            color=COLORS[0], linewidth=2.5, marker='o', markersize=8, zorder=5)
    ax.fill_between(range(len(monthly_rev)), monthly_rev['TotalAmount'],
                    alpha=0.15, color=COLORS[0])
    ax.set_title('Monthly Revenue Trend', pad=15)
    ax.set_xlabel('Month')
    ax.set_ylabel('Revenue (£)')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'£{x:,.0f}'))
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'monthly_revenue_trend.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: monthly_revenue_trend.png")

    print(f"\n  📊 Revenue Trend Insight: Peak month was {monthly_rev.loc[monthly_rev['TotalAmount'].idxmax(), 'YearMonth']}")
    print(f"     with £{monthly_rev['TotalAmount'].max():,.2f}. The trend shows seasonal patterns typical of retail.")

    # ── Revenue by Country (Top 10) ──
    country_rev = df.groupby('Country')['TotalAmount'].sum().sort_values(ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(range(len(country_rev)), country_rev.values, color=PALETTE[:len(country_rev)])
    ax.set_xticks(range(len(country_rev)))
    ax.set_xticklabels(country_rev.index, rotation=45, ha='right')
    ax.set_title('Top 10 Countries by Revenue', pad=15)
    ax.set_ylabel('Revenue (£)')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'£{x:,.0f}'))
    for i, (val, bar) in enumerate(zip(country_rev.values, bars)):
        ax.text(bar.get_x() + bar.get_width() / 2, val,
                f'£{val:,.0f}', ha='center', va='bottom', fontsize=8, fontweight='bold')
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'revenue_by_country.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: revenue_by_country.png")

    uk_pct = country_rev.iloc[0] / total_revenue * 100
    print(f"\n  📊 Geographic Insight: {country_rev.index[0]} dominates with {uk_pct:.1f}% of total revenue.")
    print(f"     Top 3 international markets: {', '.join(country_rev.index[1:4])}")

    # ── Revenue by Day of Week ──
    df['DayOfWeek'] = df['InvoiceDate'].dt.day_name()
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_rev = df.groupby('DayOfWeek')['TotalAmount'].sum().reindex(day_order).dropna()

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(day_rev.index, day_rev.values, color=[COLORS[i % len(COLORS)] for i in range(len(day_rev))])
    ax.set_title('Revenue by Day of Week', pad=15)
    ax.set_ylabel('Revenue (£)')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'£{x:,.0f}'))
    for bar, val in zip(bars, day_rev.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val,
                f'£{val:,.0f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'revenue_by_dayofweek.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: revenue_by_dayofweek.png")

    best_day = day_rev.idxmax()
    print(f"\n  📊 Day-of-Week Insight: {best_day} generates the highest revenue (£{day_rev.max():,.0f}).")

    # ── Revenue by Hour of Day ──
    df['Hour'] = df['InvoiceDate'].dt.hour
    hour_rev = df.groupby('Hour')['TotalAmount'].sum()

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(hour_rev.index, hour_rev.values, color=COLORS[0], alpha=0.85, edgecolor='white')
    ax.set_title('Revenue by Hour of Day', pad=15)
    ax.set_xlabel('Hour (24h format)')
    ax.set_ylabel('Revenue (£)')
    ax.set_xticks(range(0, 24))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'£{x:,.0f}'))
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'revenue_by_hour.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: revenue_by_hour.png")

    peak_hour = hour_rev.idxmax()
    print(f"\n  📊 Hourly Insight: Peak revenue hour is {peak_hour}:00 (£{hour_rev.max():,.0f}).")
    print(f"     Most activity occurs between 10:00-15:00, suggesting B2B buying patterns.")

    # ── Monthly Order Volume ──
    monthly_orders = df.groupby('YearMonth')['InvoiceNo'].nunique().reset_index()
    monthly_orders['YearMonth'] = monthly_orders['YearMonth'].astype(str)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(monthly_orders['YearMonth'], monthly_orders['InvoiceNo'],
           color=COLORS[1], alpha=0.85, edgecolor='white')
    ax.set_title('Monthly Order Volume', pad=15)
    ax.set_xlabel('Month')
    ax.set_ylabel('Number of Orders')
    for i, (val, ym) in enumerate(zip(monthly_orders['InvoiceNo'], monthly_orders['YearMonth'])):
        ax.text(i, val, f'{val:,}', ha='center', va='bottom', fontsize=8, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'monthly_orders_trend.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: monthly_orders_trend.png")


# ============================================================================
# CUSTOMER ANALYSIS
# ============================================================================
def customer_analysis(df):
    print("\n" + "=" * 70)
    print("CUSTOMER ANALYSIS")
    print("=" * 70)

    total_customers = df['CustomerID'].nunique()
    orders_per_cust = df.groupby('CustomerID')['InvoiceNo'].nunique()
    repeat_customers = (orders_per_cust > 1).sum()
    onetime_customers = (orders_per_cust == 1).sum()

    print(f"\n  Total Unique Customers:   {total_customers:,}")
    print(f"  Repeat Customers:         {repeat_customers:,} ({repeat_customers/total_customers*100:.1f}%)")
    print(f"  One-Time Customers:       {onetime_customers:,} ({onetime_customers/total_customers*100:.1f}%)")
    print(f"\n  📊 Retention Insight: {repeat_customers/total_customers*100:.1f}% of customers return for multiple purchases.")
    print(f"     This indicates {'strong' if repeat_customers/total_customers > 0.5 else 'moderate'} customer loyalty.")

    # ── Customer Distribution by Country ──
    cust_country = df.groupby('Country')['CustomerID'].nunique().sort_values(ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(range(len(cust_country)), cust_country.values,
                  color=[COLORS[i % len(COLORS)] for i in range(len(cust_country))])
    ax.set_xticks(range(len(cust_country)))
    ax.set_xticklabels(cust_country.index, rotation=45, ha='right')
    ax.set_title('Customer Distribution by Country (Top 10)', pad=15)
    ax.set_ylabel('Number of Customers')
    for bar, val in zip(bars, cust_country.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val,
                f'{val:,}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'customers_by_country.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: customers_by_country.png")

    # ── Order Frequency Distribution ──
    fig, ax = plt.subplots(figsize=(12, 6))
    freq_data = orders_per_cust.clip(upper=30)  # clip for readability
    ax.hist(freq_data, bins=30, color=COLORS[0], edgecolor='white', alpha=0.85)
    ax.set_title('Order Frequency Distribution', pad=15)
    ax.set_xlabel('Number of Orders per Customer')
    ax.set_ylabel('Number of Customers')
    ax.axvline(orders_per_cust.median(), color=COLORS[3], linestyle='--', linewidth=2,
               label=f'Median: {orders_per_cust.median():.0f} orders')
    ax.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'order_frequency_dist.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: order_frequency_dist.png")

    print(f"\n  📊 Frequency Insight: Median orders per customer = {orders_per_cust.median():.0f}.")
    print(f"     Mean = {orders_per_cust.mean():.1f}, showing a right-skewed distribution (few heavy buyers).")

    # ── Top 10 Customers by Revenue ──
    cust_revenue = df.groupby('CustomerID')['TotalAmount'].sum().sort_values(ascending=False).head(10)

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(range(len(cust_revenue)), cust_revenue.values, color=COLORS[0], edgecolor='white')
    ax.set_yticks(range(len(cust_revenue)))
    ax.set_yticklabels([f'Customer {int(c)}' for c in cust_revenue.index])
    ax.set_title('Top 10 Customers by Revenue', pad=15)
    ax.set_xlabel('Revenue (£)')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'£{x:,.0f}'))
    ax.invert_yaxis()
    for bar, val in zip(bars, cust_revenue.values):
        ax.text(val, bar.get_y() + bar.get_height() / 2,
                f' £{val:,.0f}', ha='left', va='center', fontsize=9, fontweight='bold')
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'top_customers_revenue.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: top_customers_revenue.png")

    top_pct = cust_revenue.sum() / df['TotalAmount'].sum() * 100
    print(f"\n  📊 Top Customer Insight: Top 10 customers account for {top_pct:.1f}% of total revenue.")
    print(f"     Highest spender (Customer {int(cust_revenue.index[0])}): £{cust_revenue.iloc[0]:,.2f}")

    # ── New vs Returning Customers by Month ──
    df['YearMonth'] = df['InvoiceDate'].dt.to_period('M')
    first_purchase = df.groupby('CustomerID')['YearMonth'].min().reset_index()
    first_purchase.columns = ['CustomerID', 'FirstMonth']

    monthly_cust = df.merge(first_purchase, on='CustomerID')
    monthly_cust['IsNew'] = (monthly_cust['YearMonth'] == monthly_cust['FirstMonth']).astype(int)

    monthly_new_ret = monthly_cust.groupby(['YearMonth', 'IsNew'])['CustomerID'].nunique().unstack(fill_value=0)
    monthly_new_ret.columns = ['Returning', 'New']
    monthly_new_ret = monthly_new_ret.reset_index()
    monthly_new_ret['YearMonth'] = monthly_new_ret['YearMonth'].astype(str)

    fig, ax = plt.subplots(figsize=(14, 6))
    x = range(len(monthly_new_ret))
    ax.bar(x, monthly_new_ret['New'], label='New Customers', color=COLORS[0], edgecolor='white')
    ax.bar(x, monthly_new_ret['Returning'], bottom=monthly_new_ret['New'],
           label='Returning Customers', color=COLORS[1], edgecolor='white')
    ax.set_xticks(x)
    ax.set_xticklabels(monthly_new_ret['YearMonth'], rotation=45, ha='right')
    ax.set_title('New vs Returning Customers by Month', pad=15)
    ax.set_ylabel('Number of Customers')
    ax.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'new_vs_returning.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: new_vs_returning.png")


# ============================================================================
# PRODUCT ANALYSIS
# ============================================================================
def product_analysis(df):
    print("\n" + "=" * 70)
    print("PRODUCT ANALYSIS")
    print("=" * 70)

    total_products = df['StockCode'].nunique()
    print(f"\n  Total Unique Products: {total_products:,}")

    # ── Top 20 Products by Revenue ──
    prod_rev = df.groupby(['StockCode', 'Description'])['TotalAmount'].sum().sort_values(ascending=False).head(20)

    fig, ax = plt.subplots(figsize=(14, 8))
    labels = [f"{code}\n{desc[:30]}" for (code, desc) in prod_rev.index]
    bars = ax.barh(range(len(prod_rev)), prod_rev.values, color=COLORS[0], edgecolor='white')
    ax.set_yticks(range(len(prod_rev)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_title('Top 20 Products by Revenue', pad=15)
    ax.set_xlabel('Revenue (£)')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'£{x:,.0f}'))
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'top_products_revenue.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: top_products_revenue.png")

    top_prod = prod_rev.index[0]
    print(f"\n  📊 Top Product: {top_prod[1]} ({top_prod[0]}) — £{prod_rev.iloc[0]:,.2f}")

    # ── Top 20 Products by Quantity ──
    prod_qty = df.groupby(['StockCode', 'Description'])['Quantity'].sum().sort_values(ascending=False).head(20)

    fig, ax = plt.subplots(figsize=(14, 8))
    labels = [f"{code}\n{desc[:30]}" for (code, desc) in prod_qty.index]
    bars = ax.barh(range(len(prod_qty)), prod_qty.values, color=COLORS[1], edgecolor='white')
    ax.set_yticks(range(len(prod_qty)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_title('Top 20 Products by Quantity Sold', pad=15)
    ax.set_xlabel('Quantity Sold')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax.invert_yaxis()
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'top_products_quantity.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: top_products_quantity.png")

    # ── Price Distribution ──
    fig, ax = plt.subplots(figsize=(12, 6))
    prices = df['UnitPrice'].clip(upper=df['UnitPrice'].quantile(0.95))
    ax.hist(prices, bins=50, color=COLORS[0], edgecolor='white', alpha=0.85)
    ax.set_title('Product Price Distribution (clipped at 95th percentile)', pad=15)
    ax.set_xlabel('Unit Price (£)')
    ax.set_ylabel('Frequency')
    ax.axvline(df['UnitPrice'].median(), color=COLORS[3], linestyle='--', linewidth=2,
               label=f'Median: £{df["UnitPrice"].median():.2f}')
    ax.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'price_distribution.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: price_distribution.png")

    print(f"\n  📊 Pricing Insight: Median price is £{df['UnitPrice'].median():.2f}, "
          f"mean £{df['UnitPrice'].mean():.2f}.")
    print(f"     Price range: £{df['UnitPrice'].min():.2f} – £{df['UnitPrice'].max():.2f}")

    # ── Products per Invoice ──
    products_per_inv = df.groupby('InvoiceNo')['StockCode'].nunique()

    fig, ax = plt.subplots(figsize=(12, 6))
    clipped = products_per_inv.clip(upper=50)
    ax.hist(clipped, bins=50, color=COLORS[2], edgecolor='white', alpha=0.85)
    ax.set_title('Products per Invoice Distribution', pad=15)
    ax.set_xlabel('Number of Unique Products per Invoice')
    ax.set_ylabel('Frequency')
    ax.axvline(products_per_inv.median(), color=COLORS[3], linestyle='--', linewidth=2,
               label=f'Median: {products_per_inv.median():.0f} products')
    ax.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'products_per_invoice.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: products_per_invoice.png")

    print(f"\n  📊 Basket Insight: Median products per invoice = {products_per_inv.median():.0f}.")
    print(f"     Average = {products_per_inv.mean():.1f}. Indicates customers buy multiple items per visit.")


# ============================================================================
# ORDER ANALYSIS
# ============================================================================
def order_analysis(df):
    print("\n" + "=" * 70)
    print("ORDER ANALYSIS")
    print("=" * 70)

    df['YearMonth'] = df['InvoiceDate'].dt.to_period('M')

    # ── Average Order Value Trend ──
    order_totals = df.groupby(['YearMonth', 'InvoiceNo'])['TotalAmount'].sum().reset_index()
    aov = order_totals.groupby('YearMonth')['TotalAmount'].mean().reset_index()
    aov['YearMonth'] = aov['YearMonth'].astype(str)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(aov['YearMonth'], aov['TotalAmount'], color=COLORS[0],
            linewidth=2.5, marker='o', markersize=8)
    ax.fill_between(range(len(aov)), aov['TotalAmount'], alpha=0.15, color=COLORS[0])
    ax.set_title('Average Order Value (AOV) Trend', pad=15)
    ax.set_xlabel('Month')
    ax.set_ylabel('Average Order Value (£)')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'£{x:,.0f}'))
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'aov_trend.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: aov_trend.png")

    overall_aov = df.groupby('InvoiceNo')['TotalAmount'].sum().mean()
    print(f"\n  📊 AOV Insight: Overall average order value is £{overall_aov:,.2f}.")

    # ── Order Size Distribution ──
    order_sizes = df.groupby('InvoiceNo')['TotalAmount'].sum()

    fig, ax = plt.subplots(figsize=(12, 6))
    clipped = order_sizes.clip(upper=order_sizes.quantile(0.95))
    ax.hist(clipped, bins=50, color=COLORS[1], edgecolor='white', alpha=0.85)
    ax.set_title('Order Size Distribution (£, clipped at 95th percentile)', pad=15)
    ax.set_xlabel('Order Value (£)')
    ax.set_ylabel('Frequency')
    ax.axvline(order_sizes.median(), color=COLORS[3], linestyle='--', linewidth=2,
               label=f'Median: £{order_sizes.median():.2f}')
    ax.legend(fontsize=11)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'order_size_dist.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: order_size_dist.png")

    print(f"\n  📊 Order Size Insight: Median order = £{order_sizes.median():.2f}, "
          f"mean = £{order_sizes.mean():.2f}.")

    # ── Cancellation Rate by Month (uses raw data with cancellations) ──
    print("\n  Loading raw data for cancellation analysis...")
    df_raw = load_raw_with_cancellations()
    df_raw['YearMonth'] = df_raw['InvoiceDate'].dt.to_period('M')

    cancel_monthly = df_raw.groupby('YearMonth').agg(
        total_invoices=('InvoiceNo', 'nunique'),
        cancelled=('IsCancelled', 'sum')
    ).reset_index()
    cancel_monthly['cancel_rate'] = cancel_monthly['cancelled'] / cancel_monthly['total_invoices'] * 100
    cancel_monthly['YearMonth'] = cancel_monthly['YearMonth'].astype(str)

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(cancel_monthly['YearMonth'], cancel_monthly['cancel_rate'],
           color=COLORS[3], alpha=0.85, edgecolor='white')
    ax.set_title('Cancellation Rate by Month (%)', pad=15)
    ax.set_xlabel('Month')
    ax.set_ylabel('Cancellation Rate (%)')
    for i, val in enumerate(cancel_monthly['cancel_rate']):
        ax.text(i, val, f'{val:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'cancellation_rate.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: cancellation_rate.png")

    avg_cancel = cancel_monthly['cancel_rate'].mean()
    print(f"\n  📊 Cancellation Insight: Average monthly cancellation rate is {avg_cancel:.1f}%.")
    print(f"     Highest cancellation month: {cancel_monthly.loc[cancel_monthly['cancel_rate'].idxmax(), 'YearMonth']}")


# ============================================================================
# MAIN
# ============================================================================
if __name__ == '__main__':
    print("=" * 70)
    print("  E-COMMERCE PIPELINE — PHASE 4: DEEP EDA")
    print("=" * 70)

    df = clean_data()

    sales_analysis(df)
    customer_analysis(df)
    product_analysis(df)
    order_analysis(df)

    print("\n" + "=" * 70)
    print("  ✅ EDA COMPLETE — All charts saved to:")
    print(f"     {CHARTS_DIR}")
    print("=" * 70)
