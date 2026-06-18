import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import random

st.set_page_config(
    page_title="Dashboard Pengiriman",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Background */
.stApp {
    background-color: #0D1117;
    color: #E6EDF3;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #161B22 !important;
    border-right: 1px solid #30363D;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span {
    color: #8B949E !important;
}

/* Metric cards */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #161B22 0%, #1C2128 100%);
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 20px 24px;
    transition: border-color 0.2s ease;
}
div[data-testid="metric-container"]:hover {
    border-color: #58A6FF;
}
div[data-testid="metric-container"] > div:first-child {
    color: #8B949E !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #E6EDF3 !important;
    font-size: 28px !important;
    font-weight: 700 !important;
    font-family: 'JetBrains Mono', monospace !important;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 12px !important;
}

/* Section headers */
.section-header {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #58A6FF;
    margin: 32px 0 16px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #21262D;
}

/* Tables */
.dataframe {
    background-color: #161B22 !important;
    color: #E6EDF3 !important;
    border-radius: 8px !important;
    border: 1px solid #30363D !important;
    font-size: 13px !important;
}
.dataframe th {
    background-color: #21262D !important;
    color: #8B949E !important;
    font-weight: 500 !important;
    font-size: 11px !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    background-color: #161B22;
    border-bottom: 1px solid #30363D;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    color: #8B949E;
    font-size: 13px;
    font-weight: 500;
    padding: 12px 20px;
    border-bottom: 2px solid transparent;
}
.stTabs [aria-selected="true"] {
    color: #58A6FF !important;
    border-bottom: 2px solid #58A6FF !important;
    background-color: transparent !important;
}

/* Selectbox */
div[data-baseweb="select"] > div {
    background-color: #21262D !important;
    border-color: #30363D !important;
    color: #E6EDF3 !important;
}

/* Status badges */
.badge-delivered   { background:#1A3A2A; color:#3FB950; border:1px solid #238636; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:600; }
.badge-transit     { background:#1A2D4A; color:#58A6FF; border:1px solid #1F6FEB; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:600; }
.badge-late        { background:#3A1A1A; color:#F85149; border:1px solid #DA3633; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:600; }
.badge-processing  { background:#2D2A1A; color:#E3B341; border:1px solid #9E6A03; padding:2px 10px; border-radius:20px; font-size:11px; font-weight:600; }

/* Page title */
.page-title {
    font-size: 22px;
    font-weight: 700;
    color: #E6EDF3;
    letter-spacing: -0.02em;
}
.page-subtitle {
    font-size: 13px;
    color: #8B949E;
    margin-top: 2px;
}

/* Info boxes */
.info-box {
    background: #161B22;
    border: 1px solid #30363D;
    border-left: 3px solid #58A6FF;
    border-radius: 8px;
    padding: 14px 18px;
    font-size: 13px;
    color: #8B949E;
    margin-bottom: 12px;
}
.info-box strong { color: #E6EDF3; }

/* Chart containers */
.chart-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 20px;
}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def generate_data(n=3000, seed=42):
    np.random.seed(seed)
    random.seed(seed)

    kota_provinsi = {
        "Jakarta": "DKI Jakarta", "Surabaya": "Jawa Timur", "Bandung": "Jawa Barat",
        "Medan": "Sumatera Utara", "Makassar": "Sulawesi Selatan",
        "Semarang": "Jawa Tengah", "Palembang": "Sumatera Selatan",
        "Denpasar": "Bali", "Yogyakarta": "DIY", "Balikpapan": "Kalimantan Timur",
    }
    kurir_cabang = {
        "Andi Pratama": "Jakarta Pusat", "Budi Santoso": "Surabaya Utara",
        "Citra Dewi": "Bandung Timur",  "Dian Kusuma": "Medan Kota",
        "Eko Wibowo": "Makassar",        "Fatimah": "Semarang",
        "Gilang Ramadan": "Palembang",   "Hani Rahayu": "Denpasar",
    }
    status_list   = ["Terkirim", "Dalam Perjalanan", "Terlambat", "Diproses"]
    status_weight = [0.60, 0.20, 0.12, 0.08]

    start = datetime(2023, 1, 1)
    dates = [start + timedelta(days=random.randint(0, 729)) for _ in range(n)]

    kota_list  = list(kota_provinsi.keys())
    kurir_list = list(kurir_cabang.keys())

    df = pd.DataFrame({
        "id_pengiriman": [f"PKG-{str(i+1).zfill(5)}" for i in range(n)],
        "tanggal":       dates,
        "kota_asal":     [random.choice(kota_list) for _ in range(n)],
        "kota_tujuan":   [random.choice(kota_list) for _ in range(n)],
        "kurir":         [random.choice(kurir_list) for _ in range(n)],
        "status":        random.choices(status_list, weights=status_weight, k=n),
        "jumlah_paket":  np.random.randint(1, 20, n),
        "biaya":         np.random.randint(15000, 500000, n),
        "durasi_hari":   np.random.randint(1, 14, n),
    })

    df["bulan"]    = df["tanggal"].dt.month
    df["tahun"]    = df["tanggal"].dt.year
    df["kuartal"]  = df["tanggal"].dt.quarter
    df["provinsi_asal"]   = df["kota_asal"].map(kota_provinsi)
    df["provinsi_tujuan"] = df["kota_tujuan"].map(kota_provinsi)
    df["cabang_kurir"]    = df["kurir"].map(kurir_cabang)
    df["nama_bulan"] = df["tanggal"].dt.strftime("%b %Y")

    return df

df = generate_data()

@st.cache_data
def mv_laporan_bulanan(data):
    return (data.groupby(["tahun", "bulan", "nama_bulan"])
            .agg(total_paket=("jumlah_paket","sum"),
                 total_biaya=("biaya","sum"),
                 total_pengiriman=("id_pengiriman","count"),
                 rata_durasi=("durasi_hari","mean"))
            .reset_index()
            .sort_values(["tahun","bulan"]))

@st.cache_data
def mv_performa_kurir(data):
    return (data.groupby("kurir")
            .agg(total=("id_pengiriman","count"),
                 terkirim=("status", lambda x: (x=="Terkirim").sum()),
                 terlambat=("status", lambda x: (x=="Terlambat").sum()),
                 rata_durasi=("durasi_hari","mean"),
                 total_biaya=("biaya","sum"))
            .reset_index()
            .assign(pct_sukses=lambda x: (x.terkirim/x.total*100).round(1))
            .sort_values("pct_sukses", ascending=False))

@st.cache_data
def mv_distribusi_wilayah(data):
    return (data.groupby("kota_tujuan")
            .agg(total=("id_pengiriman","count"),
                 paket=("jumlah_paket","sum"),
                 biaya=("biaya","sum"))
            .reset_index()
            .sort_values("total", ascending=False))

PLOT_BG   = "#0D1117"
PAPER_BG  = "#161B22"
GRID_CLR  = "#21262D"
TEXT_CLR  = "#8B949E"
COLORS    = ["#58A6FF", "#3FB950", "#E3B341", "#F85149", "#BC8CFF", "#79C0FF"]

def dark_layout(fig, title="", height=360):
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#E6EDF3", family="Inter"), x=0),
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        font=dict(family="Inter", color=TEXT_CLR, size=11),
        margin=dict(l=12, r=12, t=40 if title else 16, b=12),
        height=height,
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=GRID_CLR,
                    font=dict(size=11, color=TEXT_CLR)),
        xaxis=dict(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR, tickfont=dict(size=10)),
        yaxis=dict(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR, tickfont=dict(size=10)),
    )
    return fig

with st.sidebar:
    st.markdown("""
    <div style='padding:16px 0 24px 0;'>
        <div style='font-size:18px;font-weight:700;color:#E6EDF3;'>📦 DataWare<span style='color:#58A6FF;'>Ship</span></div>
        <div style='font-size:11px;color:#8B949E;margin-top:4px;'>Sistem Analisis Pengiriman</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#8B949E;margin-bottom:8px;">Filter Data</div>', unsafe_allow_html=True)

    tahun_opts = sorted(df["tahun"].unique())
    sel_tahun  = st.multiselect("Tahun", tahun_opts, default=tahun_opts)

    bulan_map  = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"Mei",6:"Jun",
                  7:"Jul",8:"Agu",9:"Sep",10:"Okt",11:"Nov",12:"Des"}
    sel_bulan  = st.multiselect("Bulan", list(bulan_map.keys()),
                                default=list(bulan_map.keys()),
                                format_func=lambda x: bulan_map[x])

    status_opts = df["status"].unique().tolist()
    sel_status  = st.multiselect("Status Pengiriman", status_opts, default=status_opts)

    kota_opts  = sorted(df["kota_tujuan"].unique())
    sel_kota   = st.multiselect("Kota Tujuan", kota_opts, default=kota_opts)

    kurir_opts = sorted(df["kurir"].unique())
    sel_kurir  = st.multiselect("Kurir", kurir_opts, default=kurir_opts)

    st.markdown("---")
    st.markdown('<div style="font-size:11px;color:#8B949E;">Arsitektur Data Warehouse</div>', unsafe_allow_html=True)
    for item in ["⭐ Star Schema", "🔄 ETL Pipeline", "🗂 Data Mart", "🔍 B-Tree & Bitmap Index", "⚡ Materialized View"]:
        st.markdown(f'<div style="font-size:11px;color:#58A6FF;padding:3px 0;">{item}</div>', unsafe_allow_html=True)

mask = (
    df["tahun"].isin(sel_tahun) &
    df["bulan"].isin(sel_bulan) &
    df["status"].isin(sel_status) &
    df["kota_tujuan"].isin(sel_kota) &
    df["kurir"].isin(sel_kurir)
)
fdf = df[mask].copy()

if fdf.empty:
    st.warning("⚠️ Tidak ada data untuk filter yang dipilih.")
    st.stop()

st.markdown("""
<div class="page-title">Dashboard Monitoring Pengiriman</div>
<div class="page-subtitle">Data Warehouse · Star Schema · Real-time Analytics</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Ringkasan", "📈 Tren Bulanan", "👤 Performa Kurir",
    "🗺 Distribusi Wilayah", "🏗 Arsitektur DW"
])

with tab1:
    # KPI Row
    total_pengiriman = len(fdf)
    total_paket      = fdf["jumlah_paket"].sum()
    total_biaya      = fdf["biaya"].sum()
    rata_durasi      = fdf["durasi_hari"].mean()
    pct_terkirim     = (fdf["status"]=="Terkirim").mean() * 100
    pct_terlambat    = (fdf["status"]=="Terlambat").mean() * 100

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Pengiriman", f"{total_pengiriman:,}")
    c2.metric("Total Paket",      f"{total_paket:,}")
    c3.metric("Total Biaya",      f"Rp {total_biaya/1e6:.1f}M")
    c4.metric("Rata Durasi",      f"{rata_durasi:.1f} hari")
    c5.metric("Sukses Kirim",     f"{pct_terkirim:.1f}%",
              delta=f"+{pct_terkirim - 60:.1f}% vs target")
    c6.metric("Tingkat Terlambat",f"{pct_terlambat:.1f}%",
              delta=f"{pct_terlambat - 12:.1f}% vs avg", delta_color="inverse")

    st.markdown('<div class="section-header">Distribusi Status & Biaya</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        status_count = fdf["status"].value_counts().reset_index()
        status_count.columns = ["Status", "Jumlah"]
        color_map = {"Terkirim":"#3FB950","Dalam Perjalanan":"#58A6FF",
                     "Terlambat":"#F85149","Diproses":"#E3B341"}
        fig = px.pie(status_count, names="Status", values="Jumlah",
                     color="Status", color_discrete_map=color_map,
                     hole=0.55)
        fig.update_traces(textfont_size=11, marker_line_color="#0D1117", marker_line_width=2)
        fig.update_layout(showlegend=True)
        dark_layout(fig, "Distribusi Status Pengiriman", 320)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        biaya_status = fdf.groupby("status")["biaya"].sum().reset_index()
        biaya_status.columns = ["Status", "Total Biaya"]
        biaya_status = biaya_status.sort_values("Total Biaya", ascending=True)
        fig2 = px.bar(biaya_status, x="Total Biaya", y="Status", orientation="h",
                      color="Status", color_discrete_map=color_map)
        fig2.update_traces(marker_line_width=0)
        fig2.update_xaxes(tickformat=",.0f", tickprefix="Rp ")
        dark_layout(fig2, "Total Biaya per Status", 320)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-header">Distribusi Durasi Pengiriman</div>', unsafe_allow_html=True)
    fig3 = px.histogram(fdf, x="durasi_hari", nbins=13, color="status",
                        color_discrete_map=color_map, barmode="overlay",
                        labels={"durasi_hari":"Durasi (hari)"})
    fig3.update_traces(opacity=0.8, marker_line_width=0)
    dark_layout(fig3, "", 300)
    st.plotly_chart(fig3, use_container_width=True)

with tab2:
    st.markdown("""
    <div class="info-box">
        <strong>⚡ Materialized View:</strong> Data laporan bulanan di bawah ini
        diambil dari <code>mv_laporan_bulanan</code> — hasil query yang di-cache
        untuk performa dashboard yang lebih cepat.
    </div>
    """, unsafe_allow_html=True)

    mv_bulanan = mv_laporan_bulanan(fdf)
    mv_bulanan["label"] = mv_bulanan["nama_bulan"]

    col1, col2 = st.columns(2)
    with col1:
        fig = px.line(mv_bulanan, x="label", y="total_pengiriman",
                      markers=True, line_shape="spline",
                      labels={"label":"Bulan","total_pengiriman":"Jumlah"})
        fig.update_traces(line_color="#58A6FF", marker_color="#58A6FF", marker_size=6)
        dark_layout(fig, "Total Pengiriman per Bulan", 320)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(mv_bulanan, x="label", y="total_biaya",
                      labels={"label":"Bulan","total_biaya":"Biaya (Rp)"})
        fig2.update_traces(marker_color="#3FB950", marker_line_width=0)
        fig2.update_yaxes(tickformat=",.0f")
        dark_layout(fig2, "Total Biaya per Bulan", 320)
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        fig3 = px.area(mv_bulanan, x="label", y="total_paket",
                       labels={"label":"Bulan","total_paket":"Jumlah Paket"})
        fig3.update_traces(line_color="#BC8CFF", fillcolor="rgba(188,140,255,0.15)")
        dark_layout(fig3, "Volume Paket per Bulan", 320)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        fig4 = px.line(mv_bulanan, x="label", y="rata_durasi",
                       markers=True, line_shape="spline",
                       labels={"label":"Bulan","rata_durasi":"Hari"})
        fig4.update_traces(line_color="#E3B341", marker_color="#E3B341", marker_size=6)
        fig4.add_hline(y=fdf["durasi_hari"].mean(), line_dash="dot",
                       line_color="#F85149", annotation_text="Rata-rata")
        dark_layout(fig4, "Rata-rata Durasi per Bulan", 320)
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown('<div class="section-header">Tabel Laporan Bulanan</div>', unsafe_allow_html=True)
    display_mv = mv_bulanan[["nama_bulan","total_pengiriman","total_paket","total_biaya","rata_durasi"]].copy()
    display_mv.columns = ["Bulan","Total Pengiriman","Total Paket","Total Biaya (Rp)","Rata Durasi (hari)"]
    display_mv["Total Biaya (Rp)"] = display_mv["Total Biaya (Rp)"].apply(lambda x: f"Rp {x:,.0f}")
    display_mv["Rata Durasi (hari)"] = display_mv["Rata Durasi (hari)"].round(2)
    st.dataframe(display_mv, use_container_width=True, hide_index=True)

with tab3:
    perf = mv_performa_kurir(fdf)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(perf.sort_values("pct_sukses"), x="pct_sukses", y="kurir",
                     orientation="h", color="pct_sukses",
                     color_continuous_scale=[[0,"#F85149"],[0.5,"#E3B341"],[1,"#3FB950"]],
                     range_color=[50,100],
                     labels={"pct_sukses":"% Sukses","kurir":"Kurir"})
        fig.update_coloraxes(showscale=False)
        fig.update_traces(marker_line_width=0)
        dark_layout(fig, "Tingkat Keberhasilan Kurir (%)", 380)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.scatter(perf, x="rata_durasi", y="pct_sukses",
                          size="total", text="kurir",
                          color="pct_sukses",
                          color_continuous_scale=[[0,"#F85149"],[0.5,"#E3B341"],[1,"#3FB950"]],
                          range_color=[50,100],
                          labels={"rata_durasi":"Rata Durasi (hari)","pct_sukses":"% Sukses","total":"Volume"})
        fig2.update_coloraxes(showscale=False)
        fig2.update_traces(textposition="top center", textfont_size=9)
        dark_layout(fig2, "Durasi vs Keberhasilan", 380)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-header">Detail Performa Kurir</div>', unsafe_allow_html=True)

    status_by_kurir = fdf.groupby(["kurir","status"]).size().unstack(fill_value=0).reset_index()
    fig3 = px.bar(status_by_kurir.melt(id_vars="kurir", var_name="Status", value_name="Jumlah"),
                  x="kurir", y="Jumlah", color="Status",
                  color_discrete_map={"Terkirim":"#3FB950","Dalam Perjalanan":"#58A6FF",
                                      "Terlambat":"#F85149","Diproses":"#E3B341"},
                  barmode="stack")
    fig3.update_traces(marker_line_width=0)
    dark_layout(fig3, "Distribusi Status per Kurir", 340)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<div class="section-header">Tabel Performa</div>', unsafe_allow_html=True)
    display_perf = perf[["kurir","total","terkirim","terlambat","rata_durasi","total_biaya","pct_sukses"]].copy()
    display_perf.columns = ["Kurir","Total","Terkirim","Terlambat","Rata Durasi","Total Biaya","% Sukses"]
    display_perf["Total Biaya"] = display_perf["Total Biaya"].apply(lambda x: f"Rp {x:,.0f}")
    display_perf["Rata Durasi"] = display_perf["Rata Durasi"].round(1).astype(str) + " hari"
    display_perf["% Sukses"]    = display_perf["% Sukses"].astype(str) + "%"
    st.dataframe(display_perf, use_container_width=True, hide_index=True)

with tab4:
    wilayah = mv_distribusi_wilayah(fdf)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(wilayah.head(10), x="kota_tujuan", y="total",
                     labels={"kota_tujuan":"Kota","total":"Jumlah"})
        fig.update_traces(marker_color="#58A6FF", marker_line_width=0)
        dark_layout(fig, "Top 10 Kota Tujuan", 340)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.treemap(wilayah, path=["kota_tujuan"], values="total",
                          color="total",
                          color_continuous_scale=["#1A2D4A","#1F6FEB","#58A6FF","#79C0FF"])
        fig2.update_traces(marker_line_width=0.5, marker_line_color="#0D1117")
        fig2.update_coloraxes(showscale=False)
        dark_layout(fig2, "Proporsi Volume per Kota", 340)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-header">Analisis Rute Pengiriman</div>', unsafe_allow_html=True)

    rute = (fdf.groupby(["kota_asal","kota_tujuan"])
               .agg(jumlah=("id_pengiriman","count"),
                    biaya_rata=("biaya","mean"),
                    durasi_rata=("durasi_hari","mean"))
               .reset_index()
               .sort_values("jumlah", ascending=False)
               .head(15))

    fig3 = px.scatter(rute, x="durasi_rata", y="biaya_rata",
                      size="jumlah", text="kota_tujuan",
                      color="jumlah",
                      color_continuous_scale=["#1A3A2A","#238636","#3FB950"],
                      labels={"durasi_rata":"Rata Durasi (hari)",
                              "biaya_rata":"Rata Biaya (Rp)",
                              "jumlah":"Volume Rute"})
    fig3.update_traces(textposition="top center", textfont_size=9)
    fig3.update_coloraxes(showscale=False)
    fig3.update_yaxes(tickformat=",.0f", tickprefix="Rp ")
    dark_layout(fig3, "Analisis Rute: Durasi vs Biaya vs Volume", 380)
    st.plotly_chart(fig3, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        prov = (fdf.groupby("provinsi_tujuan")
                   .agg(total=("id_pengiriman","count"))
                   .reset_index()
                   .sort_values("total", ascending=False))
        fig4 = px.pie(prov, names="provinsi_tujuan", values="total",
                      color_discrete_sequence=COLORS, hole=0.4)
        fig4.update_traces(marker_line_color="#0D1117", marker_line_width=2)
        dark_layout(fig4, "Distribusi per Provinsi", 320)
        st.plotly_chart(fig4, use_container_width=True)

    with col4:
        asal = (fdf.groupby("kota_asal")
                   .agg(total=("id_pengiriman","count"))
                   .reset_index()
                   .sort_values("total", ascending=False)
                   .head(8))
        fig5 = px.funnel(asal, x="total", y="kota_asal",
                         labels={"total":"Pengiriman","kota_asal":"Kota Asal"},
                         color_discrete_sequence=["#58A6FF"])
        dark_layout(fig5, "Kota Asal Teratas", 320)
        st.plotly_chart(fig5, use_container_width=True)

with tab5:
    st.markdown('<div class="section-header">Skema Star Schema</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:12px;padding:28px;font-family:'JetBrains Mono',monospace;font-size:12px;line-height:2;">
<pre style="color:#8B949E;margin:0;">
                        ┌─────────────────────┐
                        │    <span style="color:#E3B341">Dim_Waktu</span>          │
                        │─────────────────────│
                        │ 🔑 id_waktu          │
                        │    tanggal           │
                        │    bulan             │
                        │    kuartal           │
                        │    tahun             │
                        └──────────┬──────────┘
                                   │
    ┌────────────────────┐         │         ┌─────────────────────┐
    │    <span style="color:#58A6FF">Dim_Lokasi</span>      │         │         │    <span style="color:#3FB950">Dim_Kurir</span>          │
    │────────────────────│         │         │─────────────────────│
    │ 🔑 id_lokasi        │         │         │ 🔑 id_kurir          │
    │    kota            │         │         │    nama_kurir        │
    │    provinsi        │◄────────┼────────►│    cabang            │
    └────────────────────┘         │         └─────────────────────┘
                                   │
                        ┌──────────▼──────────┐
                        │   <span style="color:#BC8CFF">Fact_Pengiriman</span>    │
                        │─────────────────────│
                        │ 🔑 id_pengiriman     │
                        │ 🔗 id_waktu (FK)     │
                        │ 🔗 id_lokasi (FK)    │
                        │ 🔗 id_kurir (FK)     │
                        │ 🔗 id_status (FK)    │
                        │    jumlah_paket      │
                        │    biaya             │
                        │    durasi_hari       │
                        └──────────┬──────────┘
                                   │
                        ┌──────────▼──────────┐
                        │    <span style="color:#F85149">Dim_Status</span>         │
                        │─────────────────────│
                        │ 🔑 id_status         │
                        │    status_pengiriman │
                        │    keterangan        │
                        └─────────────────────┘
</pre>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Komponen Teknis</div>', unsafe_allow_html=True)

    comp1, comp2 = st.columns(2)
    with comp1:
        st.markdown("""
        <div class="info-box">
            <strong>🔄 ETL Pipeline</strong><br>
            <span>Extract → Transform → Load</span><br><br>
            • <strong>Extract:</strong> Tarik data dari sistem operasional (POS, CRM, WMS)<br>
            • <strong>Transform:</strong> Normalisasi format tanggal, cleaning data null,
              standardisasi nama kota/kurir<br>
            • <strong>Load:</strong> Muat ke tabel dimensi lalu ke Fact_Pengiriman
        </div>
        <div class="info-box">
            <strong>🔍 B-Tree Index</strong><br>
            Digunakan pada kolom dengan kardinalitas tinggi:<br><br>
            <code>CREATE INDEX idx_waktu ON Fact_Pengiriman (id_waktu);</code><br>
            <code>CREATE INDEX idx_lokasi ON Fact_Pengiriman (id_lokasi);</code><br><br>
            Mempercepat pencarian rentang tanggal dan filter lokasi.
        </div>
        """, unsafe_allow_html=True)

    with comp2:
        st.markdown("""
        <div class="info-box">
            <strong>🗂 Bitmap Index</strong><br>
            Digunakan pada Dim_Status karena kardinalitas rendah (4 nilai):<br><br>
            <code>CREATE BITMAP INDEX idx_status ON Fact_Pengiriman (id_status);</code><br><br>
            Sangat efisien untuk filter <em>WHERE status = 'Terlambat'</em> pada volume besar.
        </div>
        <div class="info-box">
            <strong>⚡ Materialized View</strong><br>
            Cache hasil query berat untuk dashboard:<br><br>
            <code>CREATE MATERIALIZED VIEW mv_laporan_bulanan AS<br>
            SELECT tahun, bulan, SUM(jumlah_paket),<br>
            &nbsp;&nbsp;SUM(biaya), AVG(durasi_hari)<br>
            FROM Fact_Pengiriman f JOIN Dim_Waktu w ...<br>
            GROUP BY tahun, bulan;</code>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Statistik Data Warehouse</div>', unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total Record (Fact)", f"{len(df):,}")
    s2.metric("Tabel Dimensi", "4")
    s3.metric("Index Aktif", "6 (4 B-Tree + 2 Bitmap)")
    s4.metric("Materialized View", "3 View")

st.markdown("""
<div style='text-align:center;padding:40px 0 20px 0;font-size:11px;color:#484F58;'>
    DataWareShip · Data Warehouse Sistem Pengiriman ·
    Star Schema + ETL + B-Tree/Bitmap Index + Materialized View
</div>
""", unsafe_allow_html=True)
