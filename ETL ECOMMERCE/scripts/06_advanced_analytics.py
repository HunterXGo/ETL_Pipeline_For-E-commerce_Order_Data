"""
=============================================================================
PHASE 11 — ADVANCED ANALYTICS
=============================================================================
Script:   06_advanced_analytics.py
Purpose:  Customer clustering, time series forecasting, anomaly detection,
          correlation analysis, and market basket analysis.
=============================================================================
"""

import matplotlib
matplotlib.use('Agg')
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import os
import warnings
from datetime import datetime
from itertools import combinations
from collections import Counter

warnings.filterwarnings('ignore')

# ---------------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------------
RAW_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "OnlineRetail.csv")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARTS_DIR = os.path.join(PROJECT_ROOT, "outputs", "charts")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "outputs", "reports")
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

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
    print("  PHASE 11 — ADVANCED ANALYTICS")
    print("=" * 80)

    df = clean_data()
    print(f"\n✓ Loaded and cleaned data: {len(df):,} rows")

    # ========================================================================
    # 1. CUSTOMER CLUSTERING (K-Means)
    # ========================================================================
    print("\n--- 1. Customer Clustering (K-Means on RFM) ---")
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA

    max_date = df['InvoiceDate'].max() + pd.Timedelta(days=1)
    rfm = df.groupby('CustomerID').agg(
        Recency=('InvoiceDate', lambda x: (max_date - x.max()).days),
        Frequency=('InvoiceNo', 'nunique'),
        Monetary=('TotalAmount', 'sum')
    )

    # Log transform to handle skew
    rfm_log = np.log1p(rfm)
    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(rfm_log)

    # Elbow method
    inertias = []
    K_range = range(2, 11)
    for k in K_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(rfm_scaled)
        inertias.append(km.inertia_)

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#0D1117')
    ax.plot(list(K_range), inertias, 'o-', color='#2E86AB', linewidth=2.5, markersize=8)
    ax.axvline(4, color='#F18F01', linestyle='--', linewidth=2, alpha=0.7, label='Optimal K=4')
    ax.set_title('Elbow Method — Optimal K Selection', fontsize=18, fontweight='bold')
    ax.set_xlabel('Number of Clusters (K)', fontsize=13)
    ax.set_ylabel('Inertia (Within-Cluster Sum of Squares)', fontsize=13)
    ax.legend(fontsize=12, facecolor='#161B22', edgecolor='#30363D')
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, 'elbow_plot.png'), dpi=150, bbox_inches='tight',
                facecolor='#0D1117')
    plt.close('all')
    print("  ✓ Saved elbow_plot.png")

    # Fit with optimal K=4
    optimal_k = 4
    km = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    rfm['Cluster'] = km.fit_predict(rfm_scaled)

    # PCA for 2D visualization
    pca = PCA(n_components=2)
    rfm_2d = pca.fit_transform(rfm_scaled)

    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('#0D1117')
    for i in range(optimal_k):
        mask = rfm['Cluster'] == i
        ax.scatter(rfm_2d[mask, 0], rfm_2d[mask, 1], c=COLORS[i], label=f'Cluster {i}',
                   alpha=0.5, s=20, edgecolors='none')
    ax.set_title('Customer Segments — PCA Projection of RFM Clusters', fontsize=18,
                 fontweight='bold')
    ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% variance)', fontsize=13)
    ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% variance)', fontsize=13)
    ax.legend(fontsize=12, facecolor='#161B22', edgecolor='#30363D')
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, 'customer_clusters.png'), dpi=150, bbox_inches='tight',
                facecolor='#0D1117')
    plt.close('all')
    print("  ✓ Saved customer_clusters.png")

    # Cluster profiles
    print("\n  Cluster Profiles:")
    profiles = rfm.groupby('Cluster').agg(
        Avg_Recency=('Recency', 'mean'),
        Avg_Frequency=('Frequency', 'mean'),
        Avg_Monetary=('Monetary', 'mean'),
        Count=('Recency', 'count')
    ).round(1)
    
    labels = {0: 'Champions', 1: 'At Risk', 2: 'Loyal Customers', 3: 'New/Casual'}
    # Assign labels based on monetary value (highest = Champions, etc.)
    sorted_clusters = profiles.sort_values('Avg_Monetary', ascending=False).index
    label_list = ['Champions', 'Loyal Customers', 'At Risk', 'New/Casual']
    cluster_labels = dict(zip(sorted_clusters, label_list))
    
    for idx, row in profiles.iterrows():
        label = cluster_labels.get(idx, f'Cluster {idx}')
        print(f"    Cluster {idx} ({label}): {row['Count']:.0f} customers | "
              f"Recency: {row['Avg_Recency']:.0f} days | "
              f"Frequency: {row['Avg_Frequency']:.0f} orders | "
              f"Monetary: £{row['Avg_Monetary']:,.0f}")

    # ========================================================================
    # 2. TIME SERIES FORECASTING
    # ========================================================================
    print("\n--- 2. Time Series Forecasting ---")
    
    monthly_rev = df.groupby(df['InvoiceDate'].dt.to_period('M'))['TotalAmount'].sum()
    monthly_rev.index = monthly_rev.index.to_timestamp()
    
    # Simple Moving Average (3-month)
    sma = monthly_rev.rolling(window=3, min_periods=1).mean()
    
    # Exponential smoothing (manual implementation)
    alpha = 0.3
    exp_smooth = pd.Series(index=monthly_rev.index, dtype=float)
    exp_smooth.iloc[0] = monthly_rev.iloc[0]
    for i in range(1, len(monthly_rev)):
        exp_smooth.iloc[i] = alpha * monthly_rev.iloc[i] + (1 - alpha) * exp_smooth.iloc[i-1]

    # Forecast next 3 months
    last_date = monthly_rev.index[-1]
    forecast_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=3, freq='MS')
    
    sma_forecast = pd.Series([sma.iloc[-1]] * 3, index=forecast_dates)
    exp_forecast = pd.Series([exp_smooth.iloc[-1]] * 3, index=forecast_dates)

    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor('#0D1117')
    ax.plot(monthly_rev.index, monthly_rev.values, 'o-', color='#2E86AB', linewidth=2.5,
            markersize=6, label='Actual Revenue')
    ax.plot(sma.index, sma.values, '--', color='#F18F01', linewidth=2, label='3-Month SMA')
    ax.plot(exp_smooth.index, exp_smooth.values, '--', color='#A23B72', linewidth=2,
            label=f'Exponential Smoothing (α={alpha})')
    ax.plot(forecast_dates, sma_forecast.values, 'o--', color='#F18F01', linewidth=2,
            markersize=8, alpha=0.5, label='SMA Forecast')
    ax.plot(forecast_dates, exp_forecast.values, 'o--', color='#A23B72', linewidth=2,
            markersize=8, alpha=0.5, label='Exp. Smoothing Forecast')
    ax.axvline(last_date, color='#C73E1D', linestyle=':', alpha=0.5, label='Forecast Start')
    ax.set_title('Monthly Revenue — Actual vs Forecast', fontsize=18, fontweight='bold')
    ax.set_xlabel('Month', fontsize=13)
    ax.set_ylabel('Revenue (£)', fontsize=13)
    ax.legend(fontsize=11, facecolor='#161B22', edgecolor='#30363D')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, 'revenue_forecast.png'), dpi=150, bbox_inches='tight',
                facecolor='#0D1117')
    plt.close('all')
    print("  ✓ Saved revenue_forecast.png")
    print(f"  SMA Forecast (next month): £{sma_forecast.iloc[0]:,.0f}")
    print(f"  Exp. Smoothing Forecast (next month): £{exp_forecast.iloc[0]:,.0f}")

    # ========================================================================
    # 3. ANOMALY DETECTION
    # ========================================================================
    print("\n--- 3. Anomaly Detection ---")
    
    daily_rev = df.groupby(df['InvoiceDate'].dt.date)['TotalAmount'].sum()
    daily_rev.index = pd.to_datetime(daily_rev.index)
    
    # Z-score method for daily revenue
    z_scores = (daily_rev - daily_rev.mean()) / daily_rev.std()
    anomaly_threshold = 2.5
    anomalies = daily_rev[np.abs(z_scores) > anomaly_threshold]
    
    # IQR method for transaction-level
    Q1 = df['TotalAmount'].quantile(0.25)
    Q3 = df['TotalAmount'].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    txn_anomalies = df[(df['TotalAmount'] < lower) | (df['TotalAmount'] > upper)]
    
    print(f"  Daily anomalies (Z-score > {anomaly_threshold}): {len(anomalies)}")
    print(f"  Transaction anomalies (IQR method): {len(txn_anomalies):,}")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
    fig.patch.set_facecolor('#0D1117')
    fig.suptitle('Anomaly Detection Analysis', fontsize=20, fontweight='bold', color='white', y=0.98)

    # Daily revenue with anomalies
    ax1.plot(daily_rev.index, daily_rev.values, color='#2E86AB', linewidth=1.2, alpha=0.7)
    ax1.scatter(anomalies.index, anomalies.values, color='#C73E1D', s=80, zorder=5,
                label=f'Anomalies ({len(anomalies)} days)', edgecolors='white', linewidth=1)
    ax1.axhline(daily_rev.mean(), color='#F18F01', linestyle='--', alpha=0.5, label='Mean')
    ax1.fill_between(daily_rev.index,
                     daily_rev.mean() - anomaly_threshold * daily_rev.std(),
                     daily_rev.mean() + anomaly_threshold * daily_rev.std(),
                     alpha=0.1, color='#44BBA4', label=f'±{anomaly_threshold}σ band')
    ax1.set_title('Daily Revenue with Anomaly Detection (Z-Score)', fontsize=15, fontweight='bold')
    ax1.set_ylabel('Daily Revenue (£)', fontsize=12)
    ax1.legend(fontsize=10, facecolor='#161B22', edgecolor='#30363D')

    # Transaction amount distribution with outliers
    ax2.hist(df['TotalAmount'][df['TotalAmount'] <= upper].values, bins=100,
             color='#2E86AB', edgecolor='#0D1117', alpha=0.8, label='Normal')
    ax2.axvline(upper, color='#C73E1D', linestyle='--', linewidth=2,
                label=f'Upper IQR Bound: £{upper:.0f}')
    ax2.set_title('Transaction Amount Distribution with IQR Bounds', fontsize=15, fontweight='bold')
    ax2.set_xlabel('Transaction Amount (£)', fontsize=12)
    ax2.set_ylabel('Frequency', fontsize=12)
    ax2.legend(fontsize=10, facecolor='#161B22', edgecolor='#30363D')

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(os.path.join(CHARTS_DIR, 'anomaly_detection.png'), dpi=150, bbox_inches='tight',
                facecolor='#0D1117')
    plt.close('all')
    print("  ✓ Saved anomaly_detection.png")

    # ========================================================================
    # 4. CORRELATION ANALYSIS
    # ========================================================================
    print("\n--- 4. Correlation Analysis ---")
    
    cust_features = df.groupby('CustomerID').agg(
        Recency=('InvoiceDate', lambda x: (max_date - x.max()).days),
        Frequency=('InvoiceNo', 'nunique'),
        Monetary=('TotalAmount', 'sum'),
        AvgOrderValue=('TotalAmount', 'mean'),
        TotalItems=('Quantity', 'sum'),
        UniqueProducts=('StockCode', 'nunique'),
        AvgUnitPrice=('UnitPrice', 'mean'),
    )

    corr = cust_features.corr()

    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_facecolor('#0D1117')
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                ax=ax, square=True, linewidths=1, cbar_kws={'shrink': 0.8},
                vmin=-1, vmax=1)
    ax.set_title('Customer Feature Correlation Matrix', fontsize=18, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(CHARTS_DIR, 'correlation_matrix.png'), dpi=150, bbox_inches='tight',
                facecolor='#0D1117')
    plt.close('all')
    print("  ✓ Saved correlation_matrix.png")
    
    # Print top correlations
    upper_tri = corr.where(mask == False)
    top_corr = upper_tri.unstack().dropna().sort_values(key=abs, ascending=False).head(5)
    print("  Top correlations:")
    for (c1, c2), val in top_corr.items():
        print(f"    {c1} ↔ {c2}: {val:.3f}")

    # ========================================================================
    # 5. MARKET BASKET ANALYSIS (Simplified)
    # ========================================================================
    print("\n--- 5. Market Basket Analysis ---")
    
    # Group products by invoice
    basket = df.groupby('InvoiceNo')['Description'].apply(list)
    
    # Count product pairs (sample for performance)
    pair_counter = Counter()
    sample_size = min(10000, len(basket))
    basket_sample = basket.sample(n=sample_size, random_state=42)
    
    for items in basket_sample:
        unique_items = list(set(items))
        if len(unique_items) >= 2:
            for pair in combinations(sorted(unique_items)[:10], 2):  # Limit per basket
                pair_counter[pair] += 1
    
    top_pairs = pair_counter.most_common(20)
    
    # Save to file
    pairs_path = os.path.join(REPORTS_DIR, "product_pairs.txt")
    with open(pairs_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("  TOP 20 PRODUCT PAIRS — Market Basket Analysis\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"  Analysis based on {sample_size:,} sampled invoices\n")
        f.write(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"  {'Rank':<6} {'Co-occurrence':<10} {'Product Pair'}\n")
        f.write(f"  {'-'*6} {'-'*10} {'-'*60}\n")
        for rank, (pair, count) in enumerate(top_pairs, 1):
            f.write(f"  {rank:<6} {count:<10} {pair[0][:40]} + {pair[1][:40]}\n")
    
    print(f"  ✓ Saved product_pairs.txt ({len(top_pairs)} pairs)")
    print("  Top 5 product pairs:")
    for pair, count in top_pairs[:5]:
        print(f"    [{count:>4}x] {pair[0][:35]} + {pair[1][:35]}")

    print("\n" + "=" * 80)
    print("  PHASE 11 COMPLETE — All advanced analytics generated.")
    print("=" * 80)


if __name__ == '__main__':
    main()
