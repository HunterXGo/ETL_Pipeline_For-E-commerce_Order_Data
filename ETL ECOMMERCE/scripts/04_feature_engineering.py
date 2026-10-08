"""
==============================================================================
PHASE 5 — Feature Engineering
E-Commerce Online Retail Pipeline
==============================================================================
Customer-level feature creation, RFM analysis, customer segmentation,
and feature diagnostics with professional visualizations.
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
DATA_DIR = Path(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "data", "dashboard_ready"))
CHARTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

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

    df = df.dropna(subset=['CustomerID'])
    df['CustomerID'] = df['CustomerID'].astype(int)
    df = df.drop_duplicates()
    df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
    df = df[~df['InvoiceNo'].astype(str).str.startswith('C')]
    df = df[(df['Quantity'] > 0) & (df['UnitPrice'] > 0)]
    df['TotalAmount'] = df['Quantity'] * df['UnitPrice']

    print(f"  Clean rows: {len(df):,}")
    return df


# ============================================================================
# CUSTOMER-LEVEL FEATURE ENGINEERING
# ============================================================================
def build_customer_features(df):
    print("\n" + "=" * 70)
    print("BUILDING CUSTOMER-LEVEL FEATURES")
    print("=" * 70)

    max_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)
    print(f"  Reference date (max + 1 day): {max_date.date()}")

    # Group-level aggregations
    cust = df.groupby('CustomerID').agg(
        total_revenue=('TotalAmount', 'sum'),
        total_items=('Quantity', 'sum'),
        total_orders=('InvoiceNo', 'nunique'),
        first_purchase=('InvoiceDate', 'min'),
        last_purchase=('InvoiceDate', 'max'),
        unique_products=('StockCode', 'nunique'),
        avg_unit_price=('UnitPrice', 'mean'),
    ).reset_index()

    # Derived features
    cust['avg_order_value'] = cust['total_revenue'] / cust['total_orders']
    cust['avg_items_per_order'] = cust['total_items'] / cust['total_orders']
    cust['customer_tenure_days'] = (cust['last_purchase'] - cust['first_purchase']).dt.days
    cust['recency_days'] = (max_date - cust['last_purchase']).dt.days
    cust['revenue_per_item'] = cust['total_revenue'] / cust['total_items']
    cust['is_repeat_customer'] = (cust['total_orders'] > 1).astype(int)

    # Purchase frequency (orders per month of tenure; handle zero-tenure)
    cust['customer_tenure_months'] = cust['customer_tenure_days'] / 30.44
    cust['purchase_frequency'] = np.where(
        cust['customer_tenure_months'] > 0,
        cust['total_orders'] / cust['customer_tenure_months'],
        cust['total_orders']
    )

    # Unique categories (first 2 chars of StockCode)
    df['Category'] = df['StockCode'].astype(str).str[:2]
    unique_cats = df.groupby('CustomerID')['Category'].nunique().reset_index()
    unique_cats.columns = ['CustomerID', 'unique_categories']
    cust = cust.merge(unique_cats, on='CustomerID', how='left')

    # Preferred day of week
    df['DayOfWeek'] = df['InvoiceDate'].dt.dayofweek
    pref_day = df.groupby('CustomerID')['DayOfWeek'].agg(lambda x: x.mode().iloc[0]).reset_index()
    pref_day.columns = ['CustomerID', 'preferred_day']
    cust = cust.merge(pref_day, on='CustomerID', how='left')

    # Preferred hour
    df['Hour'] = df['InvoiceDate'].dt.hour
    pref_hour = df.groupby('CustomerID')['Hour'].agg(lambda x: x.mode().iloc[0]).reset_index()
    pref_hour.columns = ['CustomerID', 'preferred_hour']
    cust = cust.merge(pref_hour, on='CustomerID', how='left')

    # Country (most frequent)
    country = df.groupby('CustomerID')['Country'].agg(lambda x: x.mode().iloc[0]).reset_index()
    country.columns = ['CustomerID', 'country']
    cust = cust.merge(country, on='CustomerID', how='left')

    # Clean up temp columns
    cust = cust.drop(columns=['first_purchase', 'last_purchase', 'customer_tenure_months'], errors='ignore')

    print(f"\n  ✅ Created {len(cust.columns) - 1} customer-level features for {len(cust):,} customers")
    print(f"\n  Feature list:")
    for col in cust.columns:
        if col != 'CustomerID':
            print(f"    • {col}")

    return cust


# ============================================================================
# RFM ANALYSIS
# ============================================================================
def rfm_analysis(df):
    print("\n" + "=" * 70)
    print("RFM ANALYSIS & SEGMENTATION")
    print("=" * 70)

    max_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)

    rfm = df.groupby('CustomerID').agg(
        Recency=('InvoiceDate', lambda x: (max_date - x.max()).days),
        Frequency=('InvoiceNo', 'nunique'),
        Monetary=('TotalAmount', 'sum')
    ).reset_index()

    # RFM scoring (1-5 quintiles)
    rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), 5, labels=[1, 2, 3, 4, 5]).astype(int)

    rfm['RFM_Score'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)
    rfm['RFM_Total'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']

    # Segmentation rules
    def segment_customer(row):
        r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
        if r >= 4 and f >= 4 and m >= 4:
            return 'Champions'
        elif r >= 3 and f >= 3 and m >= 3:
            return 'Loyal Customers'
        elif r >= 4 and f <= 2:
            return 'New Customers'
        elif r >= 3 and f >= 1 and m >= 2:
            return 'Potential Loyalists'
        elif r >= 3 and f <= 2 and m <= 2:
            return 'Promising'
        elif r == 3 and f == 3:
            return 'Need Attention'
        elif r <= 2 and f >= 3 and m >= 3:
            return 'At Risk'
        elif r <= 2 and f >= 4 and m >= 4:
            return 'Cant Lose Them'
        elif r <= 2 and f <= 2:
            return 'Lost'
        elif r <= 2 and f >= 2:
            return 'Hibernating'
        else:
            return 'About to Sleep'

    rfm['Segment'] = rfm.apply(segment_customer, axis=1)

    # Summary
    seg_summary = rfm.groupby('Segment').agg(
        Count=('CustomerID', 'count'),
        Avg_Recency=('Recency', 'mean'),
        Avg_Frequency=('Frequency', 'mean'),
        Avg_Monetary=('Monetary', 'mean')
    ).sort_values('Count', ascending=False)

    print(f"\n  RFM Segment Distribution:")
    print(f"  {'Segment':<25} {'Count':>8}  {'Avg Recency':>12} {'Avg Freq':>10} {'Avg Monetary':>14}")
    print(f"  {'─' * 75}")
    for seg, row in seg_summary.iterrows():
        print(f"  {seg:<25} {row['Count']:>8,}  {row['Avg_Recency']:>12.1f} {row['Avg_Frequency']:>10.1f} £{row['Avg_Monetary']:>12,.2f}")

    print(f"\n  📊 RFM Insight: Champions represent {rfm[rfm['Segment']=='Champions'].shape[0]:,} customers")
    champ_rev = rfm[rfm['Segment'] == 'Champions']['Monetary'].sum()
    total_rev = rfm['Monetary'].sum()
    print(f"     contributing £{champ_rev:,.0f} ({champ_rev/total_rev*100:.1f}% of total revenue).")
    at_risk = rfm[rfm['Segment'].isin(['At Risk', 'Cant Lose Them'])].shape[0]
    print(f"     {at_risk:,} customers are 'At Risk' or 'Can't Lose Them' — immediate re-engagement recommended.")

    return rfm


# ============================================================================
# VISUALIZATIONS
# ============================================================================
def generate_visualizations(cust_features, rfm):
    print("\n" + "=" * 70)
    print("GENERATING FEATURE ENGINEERING VISUALIZATIONS")
    print("=" * 70)

    # ── RFM Segment Distribution ──
    seg_counts = rfm['Segment'].value_counts()

    fig, ax = plt.subplots(figsize=(14, 7))
    bars = ax.bar(range(len(seg_counts)), seg_counts.values,
                  color=[COLORS[i % len(COLORS)] for i in range(len(seg_counts))],
                  edgecolor='white')
    ax.set_xticks(range(len(seg_counts)))
    ax.set_xticklabels(seg_counts.index, rotation=45, ha='right')
    ax.set_title('RFM Customer Segment Distribution', pad=15)
    ax.set_ylabel('Number of Customers')
    for bar, val in zip(bars, seg_counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val,
                f'{val:,}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'rfm_segments.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: rfm_segments.png")

    # ── Customer Segments Treemap ──
    try:
        import squarify
        has_squarify = True
    except ImportError:
        has_squarify = False

    if has_squarify:
        seg_data = rfm.groupby('Segment').agg(
            count=('CustomerID', 'count'),
            revenue=('Monetary', 'sum')
        ).sort_values('revenue', ascending=False)

        fig, ax = plt.subplots(figsize=(16, 10))
        labels = [f"{seg}\n{row['count']:,} customers\n£{row['revenue']:,.0f}"
                  for seg, row in seg_data.iterrows()]
        colors_treemap = plt.cm.RdYlBu_r(np.linspace(0.15, 0.85, len(seg_data)))
        squarify.plot(sizes=seg_data['revenue'].values, label=labels,
                      color=colors_treemap, alpha=0.85, ax=ax,
                      text_kwargs={'fontsize': 9, 'fontweight': 'bold'})
        ax.set_title('Customer Segments Treemap (sized by Revenue)', pad=15, fontsize=16)
        ax.axis('off')
        plt.tight_layout()
        plt.savefig(CHARTS_DIR / 'customer_segments_treemap.png', dpi=150, bbox_inches='tight')
        plt.close('all')
        print("  ✅ Saved: customer_segments_treemap.png")
    else:
        # Fallback: horizontal bar chart as treemap alternative
        seg_data = rfm.groupby('Segment').agg(
            count=('CustomerID', 'count'),
            revenue=('Monetary', 'sum')
        ).sort_values('revenue', ascending=True)

        fig, ax = plt.subplots(figsize=(14, 8))
        colors_bar = [COLORS[i % len(COLORS)] for i in range(len(seg_data))]
        ax.barh(seg_data.index, seg_data['revenue'], color=colors_bar, edgecolor='white')
        for i, (seg, row) in enumerate(seg_data.iterrows()):
            ax.text(row['revenue'], i, f"  {row['count']:,} customers | £{row['revenue']:,.0f}",
                    ha='left', va='center', fontsize=9, fontweight='bold')
        ax.set_title('Customer Segments by Revenue (Treemap Alternative)', pad=15, fontsize=14)
        ax.set_xlabel('Revenue (£)')
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'£{x:,.0f}'))
        plt.tight_layout()
        plt.savefig(CHARTS_DIR / 'customer_segments_treemap.png', dpi=150, bbox_inches='tight')
        plt.close('all')
        print("  ✅ Saved: customer_segments_treemap.png (bar chart fallback)")

    # ── Feature Correlation Heatmap ──
    numeric_cols = cust_features.select_dtypes(include=[np.number]).columns.tolist()
    # Remove CustomerID from correlation
    if 'CustomerID' in numeric_cols:
        numeric_cols.remove('CustomerID')

    corr_matrix = cust_features[numeric_cols].corr()

    fig, ax = plt.subplots(figsize=(16, 12))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
    sns.heatmap(corr_matrix, mask=mask, annot=True, fmt='.2f', cmap='RdBu_r',
                center=0, vmin=-1, vmax=1, square=True, linewidths=0.5,
                annot_kws={'size': 7}, ax=ax)
    ax.set_title('Customer Feature Correlation Heatmap', pad=15, fontsize=16)
    plt.xticks(rotation=45, ha='right', fontsize=9)
    plt.yticks(fontsize=9)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / 'feature_correlation.png', dpi=150, bbox_inches='tight')
    plt.close('all')
    print("  ✅ Saved: feature_correlation.png")

    # Print highly correlated pairs
    print("\n  📊 Top Correlated Feature Pairs (|r| > 0.7):")
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            val = corr_matrix.iloc[i, j]
            if abs(val) > 0.7:
                print(f"    • {corr_matrix.columns[i]} <-> {corr_matrix.columns[j]}: {val:.3f}")


# ============================================================================
# MAIN
# ============================================================================
if __name__ == '__main__':
    print("=" * 70)
    print("  E-COMMERCE PIPELINE — PHASE 5: FEATURE ENGINEERING")
    print("=" * 70)

    df = clean_data()

    # Build customer features
    cust_features = build_customer_features(df)
    cust_features.to_csv(DATA_DIR / 'customer_features.csv', index=False)
    print(f"\n  ✅ Customer features saved to: {DATA_DIR / 'customer_features.csv'}")

    # RFM Analysis
    rfm = rfm_analysis(df)
    rfm.to_csv(DATA_DIR / 'rfm_segments.csv', index=False)
    print(f"  ✅ RFM segments saved to: {DATA_DIR / 'rfm_segments.csv'}")

    # Visualizations
    generate_visualizations(cust_features, rfm)

    print("\n" + "=" * 70)
    print("  ✅ FEATURE ENGINEERING COMPLETE")
    print(f"     Features: {DATA_DIR / 'customer_features.csv'}")
    print(f"     RFM:      {DATA_DIR / 'rfm_segments.csv'}")
    print(f"     Charts:   {CHARTS_DIR}")
    print("=" * 70)
