# E-Commerce Data Analysis Dashboard 📊

## Project Overview
Dashboard ini dibuat untuk memberikan wawasan strategis mengenai performa logistik dan kepuasan pelanggan pada ekosistem E-Commerce. Fokus utama analisis meliputi dampak keterlambatan pengiriman terhadap rating, korelasi biaya ongkir, serta distribusi geografis kepadatan seller di Brasil.

## Features
- **Strategic Insights Tab**: 

    Analisis kategori produk dengan delay tertinggi dan pengaruh biaya pengiriman (Freight-Price Ratio) terhadap kepuasan.
- **Geographic Distribution Tab**: 

    Visualisasi peta interaktif (Choropleth + Bubble) yang menunjukkan korelasi antara *Delay Rate* dan kepadatan *Seller* di setiap negara bagian.
- **Global Filters**: 
    
    Kemampuan untuk memfilter data berdasarkan cakupan kategori (Top 5 vs All) dan wilayah (States).

## Setup Environment (Local)
1. Clone atau download folder ini.
2. Pastikan Python sudah terinstal.
3. Buat dan aktifkan Virtual Environment:
    ```
    python -m venv venv
    .\venv\Scripts\activate
    ```
4. Instal semua library yang dibutuhkan:    
    ```
    pip install -r requirements.txt
    ```
    
## How to Run the Dashboard
Pastikan terminal berada di dalam folder dashboard, lalu jalankan:
```
streamlit run dashboard.py

```

## Live Dashboard
Kamu bisa mengakses dashboard interaktif ini di sini: 

(https://dashboard-e-commerce-logistics-satisfaction-dashboard.streamlit.app/)


