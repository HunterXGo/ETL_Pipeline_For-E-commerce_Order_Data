"""
=============================================================================
PHASE 7 & 9 — KPI GENERATION & EXECUTIVE VISUALIZATIONS
=============================================================================
Script:   05_kpi_dashboard.py
Purpose:  Generate executive KPIs and publication-quality visualizations.
=============================================================================
"""

import matplotlib
matplotlib.use('Agg')
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import pandas as pd
import numpy as np
import os
from datetime import datetime

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
RAW_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "OnlineRetail.csv")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(PROJECT_ROOT, "outputs", "charts")
KPIS_DIR = os.path.join(PROJECT_ROOT, "outputs", "kpis")
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(KPIS_DIR, exist_ok=True)

COLORS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B',
          '#44BBA4', '#E94F37', '#393E41', '#D4A373', '#6C5B7B']

sns.set_theme(style="darkgrid")
plt.rcParams.update({
    'figure.figsize': (14, 7), 'font.size': 12,
    'axes.titlesize': 16, 'axes.titleweight': 'bold',
    'figure.facecolor': '#0D1117', 'axes.facecolor': '#161B22',
    'text.color': '#C9D1D9', 'axes.labelcolor': '#C9D1D9',
    'xtick.color': '#8B949E', 'ytick.color': '#8B949E',
})


def clean_data():
    """Load and clean the raw data."""
    df = pd.read_csv(RAW_DATA_PATH, encoding='latin-1')
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], format='mixed')
    df.dropna(subset=['CustomerID'], inplace=True)
    df.drop_duplicates(inplace=True)
    df['CustomerID'] = df['CustomerID'].astype(int)
    df['InvoiceNo'] = df['InvoiceNo'].astype(str)
    df = df[~df['InvoiceNo'].str.startswith('C')]
    df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]
    df['TotalAmount'] = df['Quantity'] * df['UnitPrice']
    return df


def main():
    print("=" * 80)
    print("  PHASE 7 & 9 — KPI GENERATION & EXECUTIVE VISUALIZATIONS")
    print("=" * 80)

    df = clean_data()
    print(f"\n✓ Loaded and cleaned data: {len(df):,} rows")

    # ========================================================================
    # EXECUTIVE KPIs
    # ========================================================================
    total_revenue = df['TotalAmount'].sum()
    total_orders = df['InvoiceNo'].nunique()
    total_customers = df['CustomerID'].nunique()
    total_items = df['Quantity'].sum()
    aov = total_revenue / total_orders
    rev_per_customer = total_revenue / total_customers
    items_per_order = total_items / total_orders

    # Repeat customers
    orders_per_cust = df.groupby('CustomerID')['InvoiceNo'].nunique()
    repeat_customers = (orders_per_cust > 1).sum()
    repeat_rate = repeat_customers / total_customers * 100

    # Top country and product
    top_country = df.groupby('Country')['TotalAmount'].sum().idxmax()
    top_product = df.groupby('Description')['TotalAmount'].sum().idxmax()

    # Monthly revenue for growth calc
    df['YearMonth'] = df['InvoiceDate'].dt.to_period('M')
    monthly_rev = df.groupby('YearMonth')['TotalAmount'].sum().sort_index()
    first_month_rev = monthly_rev.iloc[0]
    last_month_rev = monthly_rev.iloc[-1]
    growth_pct = ((last_month_rev - first_month_rev) / first_month_rev) * 100

    kpi_text = f"""
╔══════════════════════════════════════════════════════════════════════╗
║                    EXECUTIVE KPI DASHBOARD                          ║
║                    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}                        ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  💰 Total Revenue          : £{total_revenue:>14,.2f}                     ║
║  📦 Total Orders           : {total_orders:>14,}                          ║
║  👥 Total Customers        : {total_customers:>14,}                          ║
║  📊 Average Order Value    : £{aov:>14,.2f}                     ║
║  💵 Revenue Per Customer   : £{rev_per_customer:>14,.2f}                     ║
║  🔁 Repeat Customer Rate   : {repeat_rate:>13.1f}%                          ║
║  🛒 Avg Items Per Order    : {items_per_order:>14.1f}                          ║
║  🌍 Top Country            : {top_country:<30}               ║
║  🏆 Top Product            : {top_product[:30]:<30}               ║
║  📈 Revenue Growth (M/M)   : {growth_pct:>+13.1f}%                          ║
║  🔄 Retention Proxy        : {repeat_rate:>13.1f}%                          ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""
    print(kpi_text)
    with open(os.path.join(KPIS_DIR, "executive_kpis.txt"), "w", encoding="utf-8") as f:
        f.write(kpi_text)
    print("✓ Saved executive_kpis.txt")

    # ========================================================================
    # KPI DASHBOARD (Matplotlib Cards)
    # ========================================================================
    fig, axes = plt.subplots(2, 4, figsize=(20, 8))
    fig.suptitle('EXECUTIVE KPI DASHBOARD', fontsize=22, fontweight='bold', color='white', y=0.98)
    fig.patch.set_facecolor('#0D1117')

    kpis = [
        ('Total Revenue', f'£{total_revenue:,.0f}', '#2E86AB'),
        ('Total Orders', f'{total_orders:,}', '#A23B72'),
        ('Total Customers', f'{total_customers:,}', '#F18F01'),
        ('Avg Order Value', f'£{aov:,.2f}', '#C73E1D'),
        ('Rev/Customer', f'£{rev_per_customer:,.2f}', '#44BBA4'),
        ('Repeat Rate', f'{repeat_rate:.1f}%', '#E94F37'),
        ('Items/Order', f'{items_per_order:.1f}', '#6C5B7B'),
        ('Growth %', f'{growth_pct:+.1f}%', '#D4A373'),
    ]

    for ax, (label, value, color) in zip(axes.flatten(), kpis):
        ax.set_facecolor('#161B22')
        ax.text(0.5, 0.65, value, ha='center', va='center', fontsize=24,
                fontweight='bold', color=color, transform=ax.transAxes)
        ax.text(0.5, 0.25, label, ha='center', va='center', fontsize=12,
                color='#8B949E', transform=ax.transAxes)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color('#30363D')
            spine.set_linewidth(2)

    plt.tight_layout(rect=[0, 0, 1, 0.92])
    plt.savefig(os.path.join(CHARTS_DIR, 'kpi_dashboard.png'), dpi=150, bbox_inches='tight',
                facecolor='#0D1117')
    plt.close('all')
    print("✓ Saved kpi_dashboard.png")

    # ========================================================================
    # COHORT HEATMAP
    # ========================================================================
    df['OrderMonth'] = df['InvoiceDate'].dt.to_period('M')
    df['CohortMonth'] = df.groupby('CustomerID')['InvoiceDate'].transform('min').dt.to_period('M')

    cohort_data = df.groupby(['CohortMonth', 'OrderMonth']).agg(
        n_customers=('CustomerID', 'nunique')
    ).reset_index()

    cohort_data['CohortIndex'] = (cohort_data['OrderMonth'] - cohort_data['CohortMonth']).apply(lambda x: x.n)

    cohort_pivot = cohort_data.pivot_table(index='CohortMonth', columns='CohortIndex',
                                           values='n_customers')

    cohort_size = cohort_pivot.iloc[:, 0]
    retention = cohort_pivot.divide(cohort_size, axis=0) * 100

    fig, ax = plt.subplots(figsize=(16, 10))
    fig.patch.set_facecolor('#0D1117')
    sns.heatmap(retention.iloc[:10, :10], annot=True, fmt='.0f', cmap='YlOrRd',
                ax=ax, cbar_kws={'label': 'Retention %'}, linewidths=0.5)
    ax.set_title('Customer Retention Cohort Analysis', fontsize=18, fontweight='bold', pad=15)
    ax.set_xlabel('Months Since First Purchase', fontsize=13)
    ax.set_ylabel('Cohort Month', fontsize=13)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, 'cohort_heatmap.png'), dpi=150, bbox_inches='tight',
                facecolor='#0D1117')
    plt.close('all')
    print("✓ Saved cohort_heatmap.png")

    # ========================================================================
    # CLV DISTRIBUTION
    # ========================================================================
    customer_rev = df.groupby('CustomerID')['TotalAmount'].sum()

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor('#0D1117')
    # Clip to 99th percentile for readability
    clip_val = customer_rev.quantile(0.99)
    ax.hist(customer_rev[customer_rev <= clip_val], bins=50, color='#2E86AB',
            edgecolor='#0D1117', alpha=0.85)
    ax.axvline(customer_rev.median(), color='#F18F01', linestyle='--', linewidth=2,
               label=f'Median: £{customer_rev.median():,.0f}')
    ax.axvline(customer_rev.mean(), color='#C73E1D', linestyle='--', linewidth=2,
               label=f'Mean: £{customer_rev.mean():,.0f}')
    ax.set_title('Customer Lifetime Value Distribution', fontsize=18, fontweight='bold')
    ax.set_xlabel('Total Revenue (£)', fontsize=13)
    ax.set_ylabel('Number of Customers', fontsize=13)
    ax.legend(fontsize=12, facecolor='#161B22', edgecolor='#30363D')
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, 'clv_distribution.png'), dpi=150, bbox_inches='tight',
                facecolor='#0D1117')
    plt.close('all')
    print("✓ Saved clv_distribution.png")

    # ========================================================================
    # REVENUE vs ORDERS SCATTER
    # ========================================================================
    cust_metrics = df.groupby('CustomerID').agg(
        Revenue=('TotalAmount', 'sum'),
        Orders=('InvoiceNo', 'nunique')
    )

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor('#0D1117')
    scatter = ax.scatter(cust_metrics['Orders'], cust_metrics['Revenue'],
                         alpha=0.4, c='#2E86AB', s=15, edgecolors='none')
    ax.set_title('Revenue vs Order Frequency by Customer', fontsize=18, fontweight='bold')
    ax.set_xlabel('Number of Orders', fontsize=13)
    ax.set_ylabel('Total Revenue (£)', fontsize=13)
    ax.set_xlim(0, cust_metrics['Orders'].quantile(0.99))
    ax.set_ylim(0, cust_metrics['Revenue'].quantile(0.99))
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, 'revenue_orders_scatter.png'), dpi=150,
                bbox_inches='tight', facecolor='#0D1117')
    plt.close('all')
    print("✓ Saved revenue_orders_scatter.png")

    # ========================================================================
    # GEOGRAPHIC REVENUE
    # ========================================================================
    country_rev = df.groupby('Country')['TotalAmount'].sum().sort_values(ascending=True).tail(15)

    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('#0D1117')
    bars = ax.barh(range(len(country_rev)), country_rev.values, color=COLORS[:len(country_rev)])
    ax.set_yticks(range(len(country_rev)))
    ax.set_yticklabels(country_rev.index, fontsize=11)
    ax.set_title('Revenue by Country (Top 15)', fontsize=18, fontweight='bold')
    ax.set_xlabel('Total Revenue (£)', fontsize=13)
    for i, (val, label) in enumerate(zip(country_rev.values, country_rev.index)):
        ax.text(val + country_rev.max()*0.01, i, f'£{val:,.0f}', va='center',
                fontsize=10, color='#C9D1D9')
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, 'geographic_revenue.png'), dpi=150,
                bbox_inches='tight', facecolor='#0D1117')
    plt.close('all')
    print("✓ Saved geographic_revenue.png")

    # ========================================================================
    # PARETO CHART (80/20 Rule)
    # ========================================================================
    cust_rev_sorted = customer_rev.sort_values(ascending=False)
    cumulative = cust_rev_sorted.cumsum() / cust_rev_sorted.sum() * 100
    pct_customers = np.arange(1, len(cumulative) + 1) / len(cumulative) * 100

    fig, ax1 = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor('#0D1117')
    ax1.bar(range(len(cust_rev_sorted)), cust_rev_sorted.values, color='#2E86AB', alpha=0.6, width=1.0)
    ax1.set_xlabel('Customers (ranked by revenue)', fontsize=13)
    ax1.set_ylabel('Individual Revenue (£)', fontsize=13, color='#2E86AB')
    ax1.set_xlim(0, len(cust_rev_sorted))

    ax2 = ax1.twinx()
    ax2.plot(range(len(cumulative)), cumulative.values, color='#F18F01', linewidth=2.5)
    ax2.axhline(80, color='#C73E1D', linestyle='--', alpha=0.7, label='80% Revenue Line')
    ax2.set_ylabel('Cumulative Revenue %', fontsize=13, color='#F18F01')
    ax2.set_ylim(0, 105)

    # Find where 80% is reached
    pct_at_80 = np.searchsorted(cumulative.values, 80)
    pct_cust_80 = pct_at_80 / len(cumulative) * 100
    ax1.set_title(f'Pareto Analysis — Top {pct_cust_80:.0f}% Customers Drive 80% of Revenue',
                  fontsize=16, fontweight='bold')
    ax2.legend(fontsize=12, facecolor='#161B22', edgecolor='#30363D', loc='center right')
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, 'pareto_chart.png'), dpi=150, bbox_inches='tight',
                facecolor='#0D1117')
    plt.close('all')
    print("✓ Saved pareto_chart.png")

    print("\n" + "=" * 80)
    print("  PHASE 7 & 9 COMPLETE — All KPIs and visualizations generated.")
    print("=" * 80)


if __name__ == '__main__':
    main()
