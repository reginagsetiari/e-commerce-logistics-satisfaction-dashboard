# Dashboard Analisis Data: E-Commerce Public Dataset

# Import Semua Packages/Library yang Digunakan
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import geopandas as gpd
import plotly.express as px
import os

# Menyiapkan DataFrame
# --- KONFIGURASI HALAMAN DASAR ---
st.set_page_config(page_title="E-Commerce Logistics & Satisfaction Dashboard", layout="wide")

# --- HELPER FUNCTIONS ---
# Helper Function create_summary_q1
def create_summary_q1(df):
    # Hitung rata-rata skor per kategori dan status pengiriman
    summary = (df.groupby(['product_category_name_english', 'delivery_status'])['review_score']
                 .mean().unstack()
    )
    
    # Filter 10 kategori dengan jumlah transaksi terbanyak agar grafik tidak sesak
    top_10_categories = df['product_category_name_english'].value_counts().nlargest(10).index
    summary = summary.loc[summary.index.isin(top_10_categories)]

    order = ['Early', 'On-Time', 'Delayed']
    # Memastikan kolom tersedia sebelum di-reorder
    existing_columns = [col for col in order if col in summary.columns]
    return summary[existing_columns]


# Helper Function create_summary_q2
def create_summary_q2(df):
    # Menghitung rata-rata rating per freight ratio bin
    # observed=False digunakan untuk menangani tipe data Categorical
    summary = (
        df.groupby('freight_ratio_bin', observed=False)['review_score']
          .mean()
    )
    return summary

# Helper Function get_brazil_map
@st.cache_data 
def get_brazil_map():
    url = 'https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson'
    return gpd.read_file(url)

# Helper Function create_geo_analysis
def create_geo_analysis(df, brazil_map):
    # Agregasi data berdasarkan state dari df (final_df)
    geo_data = (
        df.groupby('customer_state')
          .agg({'delay_rate': 'mean',
                'review_score': 'mean',
                'seller_state': 'count'}) # Sebagai proxy jumlah seller
          .reset_index()
          .rename(columns={'seller_state': 'seller_count'})
    )

    # Merge dengan peta
    merged = brazil_map.merge(geo_data, left_on='sigla', right_on='customer_state', how='left')
    
    # Isi data kosong (jika ada state yang tidak ada transaksinya karena filter)
    merged[['delay_rate', 'review_score', 'seller_count']] = merged[['delay_rate', 'review_score', 'seller_count']].fillna(0)
    
    # Hitung Centroid untuk Bubble Plot
    # Proyeksi ke EPSG:5880 untuk akurasi titik tengah
    projected = merged.to_crs(epsg=5880)
    centroids = projected.geometry.centroid.to_crs(merged.crs)
    
    merged['centroid_x'] = centroids.x
    merged['centroid_y'] = centroids.y
    
    return merged

# --- LOAD DATA ---
@st.cache_data
def load_data():
    base_dir = os.path.dirname(__file__) # Mencari path relatif terhadap file dashboard.py ini sendiri
    file_path = os.path.join(base_dir, 'main_data_dashboard.csv')
    
    main_df = pd.read_csv(file_path)
    return main_df

# Membuat Komponen Widget
# --- SIDEBAR FILTER GLOBAL ---
st.sidebar.header("Global Filters")

# Filter 1: Kategori (Default: All agar Tab 2 tidak sepi di awal)
view_option = st.sidebar.radio(
    "Select Category Scope:", 
    ["All Categories", "Top 5 Categories"], 
    index=0  # Index 0 artinya 'All Categories' terpilih duluan
)

# Filter 2: State
all_states = sorted(main_df['customer_state'].unique())
selected_states = st.sidebar.multiselect("Select States:", options=all_states, default=all_states)

# --- PROSES FILTER DATA ---
if view_option == "Top 5 Categories":
    final_df = main_df[(main_df['is_top_5'] == True) & (main_df['customer_state'].isin(selected_states))]
else:
    final_df = main_df[main_df['customer_state'].isin(selected_states)]


# Melengkapi Dashboard dengan Berbagai Visualisasi Data
tab1, tab2 = st.tabs(["Strategic Insights", "Geographic Distribution"])

# --- TAB 1: STRATEGIC INSIGHTS ---
with tab1:
    # Panggil helper function
    summary_q1 = create_summary_q1(final_df)
    summary_q2 = create_summary_q2(final_df)

    st.header("Strategic Insights: Delivery & Pricing")
    
    # KPI Cards
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

    with col_kpi1:
        total_orders = len(final_df)
        st.metric("Total Orders", f"{total_orders:,}")
    
    with col_kpi2:
        avg_review = final_df['review_score'].mean()
        st.metric("Avg. Review Score", f"{avg_review:.2f} / 5.0")
        
    with col_kpi3:
        delay_rate = final_df['delay_rate'].mean()
        st.metric("Delayed Rate", f"{delay_rate:.2f}%")

    st.divider()

    # Visualisasi 1 : Impact of Delay
    st.subheader("The Impact of Delivery Delays on Customer Ratings")

    if view_option == "All Categories":
        st.write("*(Showing Top 10 categories by transaction volume)*")
    else:
        st.write("*(Showing Top 5 Strategic Categories)*")

    # Plotting Logic
    is_horizontal = len(summary_q1) > 5 # Tentukan jenis plot: Jika kategori > 5, pakai horizontal
    fig1, ax1 = plt.subplots(figsize=(12, 8 if is_horizontal else 6))
    kind_plot = 'barh' if is_horizontal else 'bar'
    
    summary_q1.plot(kind=kind_plot, 
                    ax=ax1, 
                    color=["#2ecc71", "#3498db", "#e74c3c"],
                    width=0.8)
    
    # Threshold line
    if is_horizontal:
        ax1.axvline(x=4, color='red', linestyle='--', alpha=0.6, label='Threshold (4.0)')
        ax1.set_xlabel('Average Review Score')
        ax1.set_ylabel('Product Category')
    else:
        ax1.axhline(y=4, color='red', linestyle='--', alpha=0.6, label='Threshold (4.0)')
        ax1.set_ylabel('Average Review Score')
        ax1.set_xlabel('Product Category')
        plt.xticks(rotation=15)

    # Bar labels
    for container in ax1.containers:
        ax1.bar_label(container, padding=3, fmt='%.2f', fontsize=8)

    ax1.legend(title='Delivery Status', bbox_to_anchor=(1, 1))
    ax1.grid(axis='x' if is_horizontal else 'y', linestyle='--', alpha=0.3)
    st.pyplot(fig1)
    if view_option == "All Categories":
        st.caption("Note: To maintain readability, only the top 10 most transacted categories are displayed.")
    
    st.info("💡 **Insight:** Delayed deliveries consistently push satisfaction levels below the 4.0 threshold.")

    st.divider()

    # Visualisasi 2 : Freight Price Ratio
    st.subheader("How Freight-Price Ratios Influence Customer Satisfaction")

    # Plotting Logic
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    summary_q2.plot(kind='line', 
                    marker='o', 
                    color='darkblue', 
                    linewidth=2, 
                    markersize=8, 
                    ax=ax2)
    
    # Threshold line
    ax2.axhline(y=4, color='red', linestyle='--', label='Threshold (4.0)')
    
    # Fill area below 4.0
    x_axis = range(len(summary_q2))
    ax2.fill_between(x_axis, 4, summary_q2, where=(summary_q2 < 4), 
                    color='red', alpha=0.2, interpolate=True)

    ax2.set_title('Critical Thresholds Identification', fontsize=12)
    ax2.set_xlabel('Freight Price Ratio (%)')
    ax2.set_ylabel('Average Review Score')
    ax2.set_ylim(3, 5)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    st.pyplot(fig2)
    st.caption("Note: The red area indicates where freight costs start hurting the customer experience.")

# --- TAB 2: GEOGRAPHIC DISTRIBUTION ---
with tab2:
    # Panggil helper function
    brazil_map_raw = get_brazil_map()
    merged_map = create_geo_analysis(final_df, brazil_map_raw)

    st.header("Geographic Analysis: Logistics vs Seller Density")
    st.markdown("This map shows the **Delay Rate** (color) and **Seller Density** (bubble size).")

    # Visualisasi 3 : Geospatial Map
    # Plotting Logic
    fig_map, ax_map = plt.subplots(figsize=(12, 10))

    # Layer 1: Choropleth (Delay Rate)
    merged_map.plot(column='delay_rate', cmap='Reds', 
                    ax=ax_map, edgecolor='0.8')

    # Layer 2: Bubble (Seller Count & Review Score)
    # Proteksi jika seller_count semuanya 0 agar tidak error
    if merged_map['seller_count'].sum() > 0:
        scatter = (
            ax_map.scatter(merged_map['centroid_x'],
                           merged_map['centroid_y'],
                           s=merged_map['seller_count'] * 0.5, 
                           c=merged_map['review_score'],
                           cmap='viridis',
                           alpha=0.7,
                           edgecolors='black')
        )

    # Legend 1: Untuk Review Score (Scatter)
    cbar_review = fig_map.colorbar(scatter, ax=ax_map, orientation="vertical", shrink=0.5, pad=0.02)
    cbar_review.set_label("Avg. Review Score", fontsize=10)

    # Legend 2: Untuk Delay Rate (Choropleth) secara manual agar sinkron
    sm = plt.cm.ScalarMappable(cmap='Reds', norm=plt.Normalize(vmin=merged_map['delay_rate'].min(), vmax=merged_map['delay_rate'].max()))
    cbar_delay = fig_map.colorbar(sm, ax=ax_map, orientation="vertical", shrink=0.5, pad=0.08)
    cbar_delay.set_label("Avg. Delay Rate (%)", fontsize=10)

    # Annotations untuk Top States
    # Filter data agar tidak memproses baris kosong
    top_delay = merged_map[merged_map['delay_rate'] > 0].nlargest(3, 'delay_rate')
    top_seller = merged_map[merged_map['seller_count'] > 0].nlargest(3, 'seller_count')

    # Anotasi untuk High Delay (Merah/Masalah)
    for _, row in top_delay.iterrows():
        ax_map.annotate(
            text=row['sigla'],
            xy=(row['centroid_x'], row['centroid_y']),
            xytext=(row['centroid_x'] + 7.5, row['centroid_y'] + 1.5), # Geser ke kanan atas
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2", color="black"),
            fontsize=11, fontweight='bold', color="black"
        )

    # Anotasi untuk Top Sellers (Pusat Ekonomi)
    for _, row in top_seller.iterrows():
        ax_map.annotate(
            text=row['sigla'],
            xy=(row['centroid_x'], row['centroid_y']),
            xytext=(row['centroid_x'] + 7, row['centroid_y'] - 6), # Geser ke kanan bawah agar tidak tabrakan
            arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.2", color="black"),
            fontsize=11, fontweight='bold'
        )

    ax_map.set_axis_off()
    st.pyplot(fig_map, use_container_width=True)

    # Footnote/Legend Explanation
    st.caption("🔴 Redder areas indicate higher delay rates. 🔵 Larger bubbles indicate higher seller concentration.")

