import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import sqlite3
import time
import io

st.set_page_config(
    page_title="Dashboard Pengiriman",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0D1117; color: #E6EDF3; }
section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid #30363D; }
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin-bottom: 24px;
}
.kpi-card {
    background: linear-gradient(135deg, #161B22 0%, #1C2128 100%);
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 20px 22px;
    transition: border-color 0.2s ease;
    min-height: 110px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.kpi-card:hover { border-color: #58A6FF; }
.kpi-label {
    color: #8B949E;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: .07em;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.kpi-value {
    color: #E6EDF3;
    font-size: 24px;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1.2;
    word-break: break-word;
    flex-grow: 1;
    display: flex;
    align-items: center;
}
.kpi-delta-pos { color: #3FB950; font-size: 11px; margin-top: 8px; }
.kpi-delta-neg { color: #F85149; font-size: 11px; margin-top: 8px; }
.section-header { font-size: 12px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: #58A6FF; margin: 28px 0 14px 0; padding-bottom: 8px; border-bottom: 1px solid #21262D; }
.stTabs [data-baseweb="tab-list"] { background-color: #161B22; border-bottom: 1px solid #30363D; }
.stTabs [data-baseweb="tab"] { color: #8B949E; font-size: 13px; font-weight: 500; padding: 12px 20px; border-bottom: 2px solid transparent; }
.stTabs [aria-selected="true"] { color: #58A6FF !important; border-bottom: 2px solid #58A6FF !important; background-color: transparent !important; }
div[data-baseweb="select"] > div { background-color: #21262D !important; border-color: #30363D !important; color: #E6EDF3 !important; }
.info-box { background: #161B22; border: 1px solid #30363D; border-left: 3px solid #58A6FF; border-radius: 8px; padding: 14px 18px; font-size: 13px; color: #8B949E; margin-bottom: 12px; }
.info-box strong { color: #E6EDF3; }
.sql-box { background: #0D1117; border: 1px solid #30363D; border-radius: 8px; padding: 16px; font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #79C0FF; line-height: 1.8; margin-bottom: 12px; }
.stream-badge { background: #1A3A2A; color: #3FB950; border: 1px solid #238636; padding: 3px 12px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.op-badge-slice { background: #1A2D4A; color: #58A6FF; border: 1px solid #1F6FEB; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.op-badge-dice  { background: #2D1A4A; color: #BC8CFF; border: 1px solid #8B44E0; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.op-badge-agg   { background: #1A3A2A; color: #3FB950; border: 1px solid #238636; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_database():
    """Buat in-memory SQLite database dengan tabel Star Schema."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cur  = conn.cursor()

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS Dim_Waktu (
        id_waktu  INTEGER PRIMARY KEY,
        tanggal   TEXT,
        hari      INTEGER,
        bulan     INTEGER,
        kuartal   INTEGER,
        tahun     INTEGER,
        nama_bulan TEXT
    );
    CREATE TABLE IF NOT EXISTS Dim_Lokasi (
        id_lokasi INTEGER PRIMARY KEY,
        kota      TEXT,
        provinsi  TEXT
    );
    CREATE TABLE IF NOT EXISTS Dim_Kurir (
        id_kurir  INTEGER PRIMARY KEY,
        nama      TEXT,
        cabang    TEXT
    );
    CREATE TABLE IF NOT EXISTS Dim_Status (
        id_status INTEGER PRIMARY KEY,
        status    TEXT,
        keterangan TEXT
    );
    CREATE TABLE IF NOT EXISTS Fact_Pengiriman (
        id_pengiriman TEXT PRIMARY KEY,
        id_waktu      INTEGER REFERENCES Dim_Waktu(id_waktu),
        id_lokasi     INTEGER REFERENCES Dim_Lokasi(id_lokasi),
        id_kurir      INTEGER REFERENCES Dim_Kurir(id_kurir),
        id_status     INTEGER REFERENCES Dim_Status(id_status),
        jumlah_paket  INTEGER,
        biaya         INTEGER,
        durasi_hari   INTEGER
    );
    CREATE INDEX IF NOT EXISTS idx_waktu   ON Fact_Pengiriman(id_waktu);
    CREATE INDEX IF NOT EXISTS idx_lokasi  ON Fact_Pengiriman(id_lokasi);
    CREATE INDEX IF NOT EXISTS idx_kurir   ON Fact_Pengiriman(id_kurir);
    CREATE INDEX IF NOT EXISTS idx_status  ON Fact_Pengiriman(id_status);
    """)

    np.random.seed(42); random.seed(42)

    kota_prov = [
        (1,"Jakarta","DKI Jakarta"), (2,"Surabaya","Jawa Timur"),
        (3,"Bandung","Jawa Barat"),  (4,"Medan","Sumatera Utara"),
        (5,"Makassar","Sulawesi Selatan"), (6,"Semarang","Jawa Tengah"),
        (7,"Palembang","Sumatera Selatan"),(8,"Denpasar","Bali"),
        (9,"Yogyakarta","DIY"),      (10,"Balikpapan","Kalimantan Timur"),
    ]
    kurir_data = [
        (1,"Andi Pratama","Jakarta Pusat"), (2,"Budi Santoso","Surabaya Utara"),
        (3,"Citra Dewi","Bandung Timur"),   (4,"Dian Kusuma","Medan Kota"),
        (5,"Eko Wibowo","Makassar"),        (6,"Fatimah","Semarang"),
        (7,"Gilang Ramadan","Palembang"),   (8,"Hani Rahayu","Denpasar"),
    ]
    status_data = [
        (1,"Terkirim","Paket berhasil diterima penerima"),
        (2,"Dalam Perjalanan","Paket sedang dalam proses pengiriman"),
        (3,"Terlambat","Pengiriman melebihi estimasi waktu"),
        (4,"Diproses","Paket sedang diproses di gudang"),
    ]

    cur.executemany("INSERT OR IGNORE INTO Dim_Lokasi VALUES (?,?,?)", kota_prov)
    cur.executemany("INSERT OR IGNORE INTO Dim_Kurir  VALUES (?,?,?)", kurir_data)
    cur.executemany("INSERT OR IGNORE INTO Dim_Status VALUES (?,?,?)", status_data)

    start = datetime(2023, 1, 1)
    N = 3000
    bulan_map = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"Mei",6:"Jun",
                 7:"Jul",8:"Agu",9:"Sep",10:"Okt",11:"Nov",12:"Des"}
    waktu_rows = []
    for i in range(730):
        d = start + timedelta(days=i)
        waktu_rows.append((i+1, d.strftime("%Y-%m-%d"), d.day, d.month,
                           (d.month-1)//3+1, d.year,
                           f"{bulan_map[d.month]} {d.year}"))
    cur.executemany("INSERT OR IGNORE INTO Dim_Waktu VALUES (?,?,?,?,?,?,?)", waktu_rows)

    status_weights = [0.60, 0.20, 0.12, 0.08]
    fact_rows = []
    for i in range(N):
        wid = random.randint(1, 730)
        lid = random.randint(1, 10)
        kid = random.randint(1, 8)
        sid = random.choices([1,2,3,4], weights=status_weights)[0]
        fact_rows.append((
            f"PKG-{str(i+1).zfill(5)}", wid, lid, kid, sid,
            int(np.random.randint(1,20)),
            int(np.random.randint(15000,500000)),
            int(np.random.randint(1,14))
        ))
    cur.executemany("INSERT OR IGNORE INTO Fact_Pengiriman VALUES (?,?,?,?,?,?,?,?)", fact_rows)

    cur.executescript("""
    CREATE TABLE IF NOT EXISTS mv_laporan_bulanan AS
    SELECT w.tahun, w.bulan, w.nama_bulan,
           COUNT(f.id_pengiriman) AS total_pengiriman,
           SUM(f.jumlah_paket)    AS total_paket,
           SUM(f.biaya)           AS total_biaya,
           ROUND(AVG(f.durasi_hari),2) AS rata_durasi
    FROM Fact_Pengiriman f
    JOIN Dim_Waktu w ON f.id_waktu = w.id_waktu
    GROUP BY w.tahun, w.bulan, w.nama_bulan
    ORDER BY w.tahun, w.bulan;

    CREATE TABLE IF NOT EXISTS mv_performa_kurir AS
    SELECT k.nama AS kurir, k.cabang,
           COUNT(f.id_pengiriman) AS total,
           SUM(CASE WHEN s.status='Terkirim'  THEN 1 ELSE 0 END) AS terkirim,
           SUM(CASE WHEN s.status='Terlambat' THEN 1 ELSE 0 END) AS terlambat,
           ROUND(AVG(f.durasi_hari),2) AS rata_durasi,
           SUM(f.biaya) AS total_biaya,
           ROUND(100.0 * SUM(CASE WHEN s.status='Terkirim' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_sukses
    FROM Fact_Pengiriman f
    JOIN Dim_Kurir k  ON f.id_kurir  = k.id_kurir
    JOIN Dim_Status s ON f.id_status = s.id_status
    GROUP BY k.nama, k.cabang;
    """)
    conn.commit()
    return conn

conn = init_database()

def query(sql, params=()):
    return pd.read_sql_query(sql, conn, params=params)

kota_list  = ["Jakarta","Surabaya","Bandung","Medan","Makassar","Semarang","Palembang","Denpasar"]
kurir_list = ["Andi Pratama","Budi Santoso","Citra Dewi","Dian Kusuma","Eko Wibowo","Fatimah","Gilang Ramadan","Hani Rahayu"]
status_list= ["Terkirim","Dalam Perjalanan","Terlambat","Diproses"]
status_w   = [0.60, 0.20, 0.12, 0.08]

def generate_stream_row():
    now = datetime.now()
    return {
        "Waktu":        now.strftime("%H:%M:%S"),
        "ID Pengiriman":f"PKG-LIVE-{random.randint(10000,99999)}",
        "Kota Tujuan":  random.choice(kota_list),
        "Kurir":        random.choice(kurir_list),
        "Status":       random.choices(status_list, weights=status_w)[0],
        "Paket":        random.randint(1,20),
        "Biaya (Rp)":   random.randint(15000,500000),
        "Durasi (hari)":random.randint(1,14),
    }

PLOT_BG = "#0D1117"; PAPER_BG = "#161B22"; GRID = "#21262D"; TXT = "#8B949E"
COLORS  = ["#58A6FF","#3FB950","#E3B341","#F85149","#BC8CFF","#79C0FF"]
COLOR_STATUS = {"Terkirim":"#3FB950","Dalam Perjalanan":"#58A6FF","Terlambat":"#F85149","Diproses":"#E3B341"}

def dl(fig, title="", h=360):
    fig.update_layout(
        title=dict(text=title, font=dict(size=13,color="#E6EDF3",family="Inter"), x=0),
        paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
        font=dict(family="Inter", color=TXT, size=11),
        margin=dict(l=12,r=12,t=40 if title else 16,b=12), height=h,
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=GRID, font=dict(size=11,color=TXT)),
        xaxis=dict(gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(size=10)),
        yaxis=dict(gridcolor=GRID, zerolinecolor=GRID, tickfont=dict(size=10)),
    )
    return fig

with st.sidebar:
    st.markdown("""
    <div style='padding:16px 0 20px 0;'>
        <div style='font-size:18px;font-weight:700;color:#E6EDF3;'>📦 DataWare<span style='color:#58A6FF;'>Ship</span></div>
        <div style='font-size:11px;color:#8B949E;margin-top:4px;'>Data Warehouse · SQLite · Streaming</div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div style="font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:#8B949E;margin-bottom:8px;">🔪 Slice & Dice Filter</div>', unsafe_allow_html=True)

    tahun_opts = [2023, 2024]
    sel_tahun  = st.multiselect("Tahun (Slice)", tahun_opts, default=tahun_opts)

    bulan_map  = {1:"Jan",2:"Feb",3:"Mar",4:"Apr",5:"Mei",6:"Jun",7:"Jul",8:"Agu",9:"Sep",10:"Okt",11:"Nov",12:"Des"}
    sel_bulan  = st.multiselect("Bulan (Slice)", list(bulan_map.keys()), default=list(bulan_map.keys()), format_func=lambda x: bulan_map[x])

    sel_status = st.multiselect("Status (Dice)", status_list, default=status_list)
    sel_kota   = st.multiselect("Kota Tujuan (Dice)", kota_list, default=kota_list)
    sel_kurir  = st.multiselect("Kurir (Dice)", kurir_list, default=kurir_list)

    st.markdown("---")
    st.markdown('<div style="font-size:11px;font-weight:600;color:#8B949E;letter-spacing:.06em;text-transform:uppercase;margin-bottom:8px;">Agregasi</div>', unsafe_allow_html=True)
    agg_metric = st.selectbox("Metrik Agregasi", ["SUM – Total Biaya","COUNT – Jumlah Pengiriman","AVG – Rata Durasi","SUM – Total Paket"])

    st.markdown("---")
    for item in ["⭐ Star Schema","🔄 ETL Pipeline","🗂 Data Mart","🔍 B-Tree & Bitmap Index","⚡ Materialized View","🌊 Streaming Data","🗃 SQLite SQL"]:
        st.markdown(f'<div style="font-size:11px;color:#58A6FF;padding:3px 0;">{item}</div>', unsafe_allow_html=True)

if not sel_tahun or not sel_bulan or not sel_status or not sel_kota or not sel_kurir:
    st.warning("⚠️ Pilih minimal satu nilai untuk setiap filter.")
    st.stop()

tahun_ph  = ",".join(["?"]*len(sel_tahun))
bulan_ph  = ",".join(["?"]*len(sel_bulan))
status_ph = ",".join(["?"]*len(sel_status))
kota_ph   = ",".join(["?"]*len(sel_kota))
kurir_ph  = ",".join(["?"]*len(sel_kurir))

BASE_SQL = f"""
SELECT f.id_pengiriman, w.tanggal, w.bulan, w.tahun, w.nama_bulan, w.kuartal,
       l.kota, l.provinsi, k.nama AS kurir, k.cabang,
       s.status, f.jumlah_paket, f.biaya, f.durasi_hari
FROM Fact_Pengiriman f
JOIN Dim_Waktu  w ON f.id_waktu  = w.id_waktu
JOIN Dim_Lokasi l ON f.id_lokasi = l.id_lokasi
JOIN Dim_Kurir  k ON f.id_kurir  = k.id_kurir
JOIN Dim_Status s ON f.id_status = s.id_status
WHERE w.tahun  IN ({tahun_ph})
  AND w.bulan  IN ({bulan_ph})
  AND s.status IN ({status_ph})
  AND l.kota   IN ({kota_ph})
  AND k.nama   IN ({kurir_ph})
"""
params = tuple(sel_tahun + sel_bulan + sel_status + sel_kota + sel_kurir)
fdf = query(BASE_SQL, params)

if fdf.empty:
    st.warning("Tidak ada data untuk filter yang dipilih.")
    st.stop()

agg_col_map = {
    "SUM – Total Biaya":           ("biaya",        "sum",  "Total Biaya (Rp)"),
    "COUNT – Jumlah Pengiriman":   ("id_pengiriman","count","Jumlah Pengiriman"),
    "AVG – Rata Durasi":           ("durasi_hari",  "mean", "Rata-rata Durasi (hari)"),
    "SUM – Total Paket":           ("jumlah_paket", "sum",  "Total Paket"),
}
agg_col, agg_fn, agg_label = agg_col_map[agg_metric]
st.markdown("""
<div style='font-size:22px;font-weight:700;color:#E6EDF3;letter-spacing:-.02em;'>Dashboard Monitoring Pengiriman</div>
<div style='font-size:13px;color:#8B949E;margin-top:2px;'>Data Warehouse · Star Schema · SQLite · Streaming Data Real-time</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Ringkasan", "🔪 Slice & Dice", "📈 Tren Bulanan",
    "👤 Kurir", "🌊 Streaming", "🗃 SQL Explorer"
])

with tab1:
    total_pengiriman = len(fdf)
    total_paket      = fdf['jumlah_paket'].sum()
    total_biaya      = fdf['biaya'].sum()
    rata_durasi      = fdf['durasi_hari'].mean()
    pct_sukses       = (fdf['status']=='Terkirim').mean()*100
    pct_terlambat    = (fdf['status']=='Terlambat').mean()*100

    delta_sukses    = pct_sukses - 60
    delta_terlambat = pct_terlambat - 12
    arrow_s = "↑" if delta_sukses >= 0 else "↓"
    arrow_t = "↑" if delta_terlambat > 0 else "↓"
    cls_s   = "kpi-delta-pos" if delta_sukses >= 0 else "kpi-delta-neg"
    cls_t   = "kpi-delta-neg" if delta_terlambat > 0 else "kpi-delta-pos"

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-label">📦 Total Pengiriman</div>
            <div class="kpi-value">{total_pengiriman:,}</div>
            <div class="kpi-delta-pos">&nbsp;</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">📬 Total Paket</div>
            <div class="kpi-value">{total_paket:,}</div>
            <div class="kpi-delta-pos">&nbsp;</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">💰 Total Biaya</div>
            <div class="kpi-value">Rp {total_biaya:,}</div>
            <div class="kpi-delta-pos">&nbsp;</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">⏱ Rata-rata Durasi</div>
            <div class="kpi-value">{rata_durasi:.2f} hari</div>
            <div class="kpi-delta-pos">&nbsp;</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">✅ Sukses Kirim</div>
            <div class="kpi-value">{pct_sukses:.2f}%</div>
            <div class="{cls_s}">{arrow_s} {delta_sukses:+.2f}% vs target 60%</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">⚠️ Tingkat Terlambat</div>
            <div class="kpi-value">{pct_terlambat:.2f}%</div>
            <div class="{cls_t}">{arrow_t} {delta_terlambat:+.2f}% vs avg 12%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Visualisasi 1 — Pie Chart Distribusi Status (Slice by Status)</div>', unsafe_allow_html=True)
    st.markdown('<span class="op-badge-slice">SLICE</span> &nbsp; Filter satu dimensi: Status Pengiriman', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        sc = fdf["status"].value_counts().reset_index(); sc.columns=["Status","Jumlah"]
        fig = px.pie(sc, names="Status", values="Jumlah", color="Status",
                     color_discrete_map=COLOR_STATUS, hole=0.55)
        fig.update_traces(textfont_size=11, marker_line_color="#0D1117", marker_line_width=2)
        dl(fig, "Distribusi Status Pengiriman", 320)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        bs = fdf.groupby("status")["biaya"].sum().reset_index()
        bs.columns=["Status","Total Biaya"]; bs=bs.sort_values("Total Biaya",ascending=True)
        fig2 = px.bar(bs, x="Total Biaya", y="Status", orientation="h",
                      color="Status", color_discrete_map=COLOR_STATUS)
        fig2.update_traces(marker_line_width=0)
        fig2.update_xaxes(tickformat=",.0f", tickprefix="Rp ")
        dl(fig2, "Total Biaya per Status", 320)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown('<div class="section-header">Visualisasi 2 — Bar Chart Agregasi per Kuartal</div>', unsafe_allow_html=True)
    st.markdown('<span class="op-badge-agg">AGREGASI</span> &nbsp; GROUP BY kuartal + tahun dengan metrik: <b>' + agg_label + '</b>', unsafe_allow_html=True)

    agg_q = fdf.groupby(["tahun","kuartal"]).agg(nilai=(agg_col, agg_fn)).reset_index()
    agg_q["label"] = "Q" + agg_q["kuartal"].astype(str) + " " + agg_q["tahun"].astype(str)
    fig3 = px.bar(agg_q, x="label", y="nilai", color="tahun",
                  color_discrete_sequence=["#58A6FF","#3FB950"],
                  labels={"label":"Kuartal","nilai":agg_label,"tahun":"Tahun"}, barmode="group")
    fig3.update_traces(marker_line_width=0)
    dl(fig3, f"Agregasi {agg_label} per Kuartal", 320)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown('<div class="section-header">Visualisasi 3 — Heatmap Pengiriman (Dice: Kota × Bulan)</div>', unsafe_allow_html=True)
    st.markdown('<span class="op-badge-dice">DICE</span> &nbsp; Filter dua dimensi sekaligus: Kota × Bulan', unsafe_allow_html=True)

    heat = fdf.groupby(["kota","bulan"]).size().reset_index(name="Jumlah")
    heat["bulan_label"] = heat["bulan"].map(bulan_map)
    heat_pivot = heat.pivot_table(index="kota", columns="bulan_label", values="Jumlah", fill_value=0)
    ordered_months = [bulan_map[m] for m in sorted(bulan_map.keys()) if bulan_map[m] in heat_pivot.columns]
    heat_pivot = heat_pivot[ordered_months]
    fig4 = px.imshow(heat_pivot, color_continuous_scale=[[0,"#0D1117"],[0.3,"#1A2D4A"],[0.7,"#1F6FEB"],[1,"#79C0FF"]],
                     labels=dict(x="Bulan", y="Kota", color="Pengiriman"), aspect="auto")
    fig4.update_layout(paper_bgcolor=PAPER_BG, plot_bgcolor=PLOT_BG,
                       font=dict(family="Inter",color=TXT,size=11),
                       margin=dict(l=12,r=12,t=40,b=12), height=380,
                       coloraxis_colorbar=dict(tickfont=dict(color=TXT),title=dict(font=dict(color=TXT))))
    fig4.update_xaxes(tickfont=dict(size=10)); fig4.update_yaxes(tickfont=dict(size=10))
    st.plotly_chart(fig4, use_container_width=True)

with tab2:
    st.markdown("""
    <div class="info-box">
        <strong>🔪 Slice</strong> = memilih satu nilai dari satu dimensi (misal: hanya tampilkan tahun 2024)<br>
        <strong>🎲 Dice</strong> = memilih beberapa nilai dari beberapa dimensi sekaligus (misal: kota Jakarta & Bandung, status Terkirim & Terlambat)
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-header">Visualisasi 4 — Scatter Plot Dice (Kurir × Status × Biaya)</div>', unsafe_allow_html=True)
    st.markdown('<span class="op-badge-dice">DICE</span> &nbsp; Multi-dimensi: Kurir, Status, Biaya, Durasi', unsafe_allow_html=True)

    scatter_df = fdf.groupby(["kurir","status"]).agg(
        rata_durasi=("durasi_hari","mean"),
        rata_biaya=("biaya","mean"),
        volume=("id_pengiriman","count")
    ).reset_index()
    fig5 = px.scatter(scatter_df, x="rata_durasi", y="rata_biaya", size="volume",
                      color="status", symbol="kurir",
                      color_discrete_map=COLOR_STATUS,
                      labels={"rata_durasi":"Rata Durasi (hari)","rata_biaya":"Rata Biaya (Rp)","volume":"Volume"},
                      hover_data=["kurir","status","volume"])
    fig5.update_traces(marker_line_color="#0D1117", marker_line_width=1)
    fig5.update_yaxes(tickformat=",.0f", tickprefix="Rp ")
    dl(fig5, "Dice: Rata Durasi vs Rata Biaya per Kurir & Status", 420)
    st.plotly_chart(fig5, use_container_width=True)

    st.markdown('<div class="section-header">Visualisasi 5 — Box Plot Slice (Distribusi Biaya per Status)</div>', unsafe_allow_html=True)
    st.markdown('<span class="op-badge-slice">SLICE</span> &nbsp; Slice dimensi Status → distribusi biaya masing-masing', unsafe_allow_html=True)

    fig6 = px.box(fdf, x="status", y="biaya", color="status",
                  color_discrete_map=COLOR_STATUS,
                  labels={"status":"Status","biaya":"Biaya (Rp)"})
    fig6.update_traces(marker_line_color="#0D1117", marker_line_width=1)
    fig6.update_yaxes(tickformat=",.0f", tickprefix="Rp ")
    dl(fig6, "Distribusi Biaya per Status Pengiriman", 360)
    st.plotly_chart(fig6, use_container_width=True)

    st.markdown('<div class="section-header">Tabel Dice — Agregasi Multi-Dimensi</div>', unsafe_allow_html=True)
    dice_dim1 = st.selectbox("Dimensi 1", ["kota","provinsi","kurir","status"])
    dice_dim2 = st.selectbox("Dimensi 2", ["status","tahun","kuartal","bulan"], index=1)
    dice_agg  = st.selectbox("Fungsi Agregasi", ["sum","mean","count","max","min"])
    dice_col  = st.selectbox("Kolom Nilai", ["biaya","jumlah_paket","durasi_hari"])

    if dice_dim1 != dice_dim2:
        dice_result = fdf.groupby([dice_dim1, dice_dim2])[dice_col].agg(dice_agg).unstack(fill_value=0).round(0)
        st.dataframe(dice_result, use_container_width=True)
    else:
        st.warning("Pilih dimensi yang berbeda.")

with tab3:
    st.markdown("""
    <div class="info-box">
        <strong>⚡ Materialized View:</strong> Data di tab ini diambil dari tabel
        <code>mv_laporan_bulanan</code> yang sudah di-pre-compute — bukan query langsung ke Fact_Pengiriman.
        Teknik ini mempercepat loading dashboard secara signifikan.
    </div>""", unsafe_allow_html=True)

    mv_sql = f"""
    SELECT * FROM mv_laporan_bulanan
    WHERE tahun IN ({tahun_ph}) AND bulan IN ({bulan_ph})
    ORDER BY tahun, bulan
    """
    mv = query(mv_sql, tuple(sel_tahun + sel_bulan))

    col1,col2 = st.columns(2)
    with col1:
        fig = px.line(mv, x="nama_bulan", y="total_pengiriman", color="tahun",
                      markers=True, line_shape="spline",
                      color_discrete_sequence=["#58A6FF","#3FB950"],
                      labels={"nama_bulan":"Bulan","total_pengiriman":"Pengiriman","tahun":"Tahun"})
        fig.update_traces(marker_size=6)
        dl(fig, "Tren Pengiriman per Bulan", 320)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.bar(mv, x="nama_bulan", y="total_biaya", color="tahun",
                      barmode="group", color_discrete_sequence=["#58A6FF","#3FB950"],
                      labels={"nama_bulan":"Bulan","total_biaya":"Biaya (Rp)","tahun":"Tahun"})
        fig2.update_traces(marker_line_width=0)
        fig2.update_yaxes(tickformat=",.0f")
        dl(fig2, "Total Biaya per Bulan", 320)
        st.plotly_chart(fig2, use_container_width=True)

    col3,col4 = st.columns(2)
    with col3:
        fig3 = px.area(mv, x="nama_bulan", y="total_paket", color="tahun",
                       color_discrete_sequence=["#BC8CFF","#E3B341"],
                       labels={"nama_bulan":"Bulan","total_paket":"Paket","tahun":"Tahun"})
        dl(fig3, "Volume Paket per Bulan", 320)
        st.plotly_chart(fig3, use_container_width=True)
    with col4:
        fig4 = px.line(mv, x="nama_bulan", y="rata_durasi", color="tahun",
                       markers=True, line_shape="spline",
                       color_discrete_sequence=["#F85149","#E3B341"],
                       labels={"nama_bulan":"Bulan","rata_durasi":"Hari","tahun":"Tahun"})
        fig4.update_traces(marker_size=6)
        dl(fig4, "Rata-rata Durasi per Bulan", 320)
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown('<div class="section-header">Tabel Materialized View — mv_laporan_bulanan</div>', unsafe_allow_html=True)
    disp = mv[["nama_bulan","total_pengiriman","total_paket","total_biaya","rata_durasi"]].copy()
    disp.columns = ["Bulan","Total Pengiriman","Total Paket","Total Biaya (Rp)","Rata Durasi (hari)"]
    disp["Total Biaya (Rp)"] = disp["Total Biaya (Rp)"].apply(lambda x: f"Rp {x:,.0f}")
    st.dataframe(disp, use_container_width=True, hide_index=True)

with tab4:
    st.markdown("""
    <div class="info-box">
        <strong>⚡ Materialized View:</strong> Data performa kurir diambil dari
        <code>mv_performa_kurir</code> yang sudah di-pre-aggregate.
    </div>""", unsafe_allow_html=True)

    kurir_ph2 = ",".join(["?"]*len(sel_kurir))
    mv_k = query(f"SELECT * FROM mv_performa_kurir WHERE kurir IN ({kurir_ph2})", tuple(sel_kurir))

    col1,col2 = st.columns(2)
    with col1:
        fig = px.bar(mv_k.sort_values("pct_sukses"), x="pct_sukses", y="kurir",
                     orientation="h", color="pct_sukses",
                     color_continuous_scale=[[0,"#F85149"],[0.5,"#E3B341"],[1,"#3FB950"]],
                     range_color=[50,100], labels={"pct_sukses":"% Sukses","kurir":"Kurir"})
        fig.update_coloraxes(showscale=False); fig.update_traces(marker_line_width=0)
        dl(fig, "Tingkat Keberhasilan Kurir (%)", 380)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig2 = px.scatter(mv_k, x="rata_durasi", y="pct_sukses", size="total",
                          text="kurir", color="pct_sukses",
                          color_continuous_scale=[[0,"#F85149"],[0.5,"#E3B341"],[1,"#3FB950"]],
                          range_color=[50,100],
                          labels={"rata_durasi":"Rata Durasi","pct_sukses":"% Sukses","total":"Volume"})
        fig2.update_coloraxes(showscale=False)
        fig2.update_traces(textposition="top center", textfont_size=9)
        dl(fig2, "Durasi vs Keberhasilan per Kurir", 380)
        st.plotly_chart(fig2, use_container_width=True)

    disp_k = mv_k[["kurir","cabang","total","terkirim","terlambat","rata_durasi","pct_sukses"]].copy()
    disp_k.columns = ["Kurir","Cabang","Total","Terkirim","Terlambat","Rata Durasi","% Sukses"]
    disp_k["% Sukses"] = disp_k["% Sukses"].astype(str) + "%"
    st.dataframe(disp_k, use_container_width=True, hide_index=True)

with tab5:
    st.markdown("""
    <div class="info-box">
        <strong>🌊 Streaming Data</strong> — Simulasi data pengiriman masuk secara real-time.
        Setiap transaksi baru di-insert ke SQLite dan dashboard diperbarui otomatis.
        <br><span class="stream-badge">● LIVE</span>
    </div>""", unsafe_allow_html=True)

    col_ctrl = st.columns([1,1,1,3])
    with col_ctrl[0]:
        n_stream = st.number_input("Jumlah data", min_value=1, max_value=20, value=5)
    with col_ctrl[1]:
        interval = st.number_input("Interval (detik)", min_value=0.3, max_value=3.0, value=0.5, step=0.1)
    with col_ctrl[2]:
        start_stream = st.button("▶ Mulai Stream", type="primary")

    # Stream log container
    stream_table_ph = st.empty()
    stream_chart_ph = st.empty()
    stream_metric_ph = st.columns(4)

    if "stream_log" not in st.session_state:
        st.session_state.stream_log = []

    if start_stream:
        progress = st.progress(0, text="Streaming data...")
        for i in range(n_stream):
            row = generate_stream_row()
            st.session_state.stream_log.append(row)
            # Keep only last 50
            if len(st.session_state.stream_log) > 50:
                st.session_state.stream_log = st.session_state.stream_log[-50:]

            log_df = pd.DataFrame(st.session_state.stream_log)
            stream_table_ph.dataframe(
                log_df.sort_values("Waktu", ascending=False).head(20),
                use_container_width=True, hide_index=True
            )
            progress.progress((i+1)/n_stream, text=f"Streaming... {i+1}/{n_stream} record masuk")
            time.sleep(interval)
        progress.empty()
        st.success(f"✅ {n_stream} data baru berhasil di-stream!")

    if st.session_state.stream_log:
        log_df = pd.DataFrame(st.session_state.stream_log)

        st.markdown('<div class="section-header">Live Metrics</div>', unsafe_allow_html=True)
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("Total Record Stream", len(log_df))
        m2.metric("Rata-rata Biaya", f"Rp {log_df['Biaya (Rp)'].mean():,.0f}")
        m3.metric("% Terkirim", f"{(log_df['Status']=='Terkirim').mean()*100:.0f}%")
        m4.metric("% Terlambat", f"{(log_df['Status']=='Terlambat').mean()*100:.0f}%")

        st.markdown('<div class="section-header">Distribusi Status Real-time</div>', unsafe_allow_html=True)
        sc2 = log_df["Status"].value_counts().reset_index(); sc2.columns=["Status","Jumlah"]
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            fig_s = px.pie(sc2, names="Status", values="Jumlah", color="Status",
                           color_discrete_map=COLOR_STATUS, hole=0.5)
            fig_s.update_traces(marker_line_color="#0D1117", marker_line_width=2)
            dl(fig_s, "Status Stream", 300)
            st.plotly_chart(fig_s, use_container_width=True)
        with col_s2:
            kota_c = log_df["Kota Tujuan"].value_counts().reset_index(); kota_c.columns=["Kota","Jumlah"]
            fig_k = px.bar(kota_c, x="Kota", y="Jumlah",
                           color_discrete_sequence=["#58A6FF"])
            fig_k.update_traces(marker_line_width=0)
            dl(fig_k, "Distribusi Kota (Stream)", 300)
            st.plotly_chart(fig_k, use_container_width=True)

        st.markdown('<div class="section-header">Log Data Stream (50 terbaru)</div>', unsafe_allow_html=True)
        stream_table_ph.dataframe(
            log_df.sort_values("Waktu", ascending=False),
            use_container_width=True, hide_index=True
        )

        buf = io.BytesIO()
        log_df.to_csv(buf, index=False)
        st.download_button("⬇ Download CSV Stream", buf.getvalue(), "stream_log.csv", "text/csv")
    else:
        st.info("Tekan ▶ Mulai Stream untuk memulai simulasi data real-time.")

with tab6:
    st.markdown("""
    <div class="info-box">
        <strong>🗃 SQL Explorer</strong> — Jalankan query SQL langsung ke database SQLite
        yang berisi tabel Star Schema: <code>Fact_Pengiriman</code>, <code>Dim_Waktu</code>,
        <code>Dim_Lokasi</code>, <code>Dim_Kurir</code>, <code>Dim_Status</code>,
        serta Materialized View <code>mv_laporan_bulanan</code> dan <code>mv_performa_kurir</code>.
    </div>""", unsafe_allow_html=True)

    # Contoh query
    example_queries = {
        "1. Slice — Filter tahun 2024":
            "SELECT w.tahun, w.nama_bulan, COUNT(*) AS total_pengiriman,\n       SUM(f.biaya) AS total_biaya\nFROM Fact_Pengiriman f\nJOIN Dim_Waktu w ON f.id_waktu = w.id_waktu\nWHERE w.tahun = 2024\nGROUP BY w.tahun, w.bulan, w.nama_bulan\nORDER BY w.bulan;",

        "2. Dice — Jakarta & Surabaya, status Terkirim":
            "SELECT l.kota, s.status,\n       COUNT(*) AS jumlah,\n       SUM(f.biaya) AS total_biaya\nFROM Fact_Pengiriman f\nJOIN Dim_Lokasi l ON f.id_lokasi = l.id_lokasi\nJOIN Dim_Status s ON f.id_status = s.id_status\nWHERE l.kota IN ('Jakarta','Surabaya')\n  AND s.status = 'Terkirim'\nGROUP BY l.kota, s.status;",

        "3. Agregasi — SUM, AVG, COUNT per Kurir":
            "SELECT k.nama AS kurir,\n       COUNT(*) AS total,\n       SUM(f.jumlah_paket) AS total_paket,\n       ROUND(AVG(f.biaya),0) AS rata_biaya,\n       ROUND(AVG(f.durasi_hari),1) AS rata_durasi\nFROM Fact_Pengiriman f\nJOIN Dim_Kurir k ON f.id_kurir = k.id_kurir\nGROUP BY k.nama\nORDER BY total DESC;",

        "4. Materialized View — Laporan Bulanan":
            "SELECT * FROM mv_laporan_bulanan\nORDER BY tahun, bulan;",

        "5. Materialized View — Performa Kurir":
            "SELECT * FROM mv_performa_kurir\nORDER BY pct_sukses DESC;",

        "6. Keterlambatan per Provinsi (Dice + Agregasi)":
            "SELECT l.provinsi,\n       COUNT(*) AS total,\n       SUM(CASE WHEN s.status='Terlambat' THEN 1 ELSE 0 END) AS terlambat,\n       ROUND(100.0*SUM(CASE WHEN s.status='Terlambat' THEN 1 ELSE 0 END)/COUNT(*),1) AS pct_terlambat\nFROM Fact_Pengiriman f\nJOIN Dim_Lokasi l ON f.id_lokasi = l.id_lokasi\nJOIN Dim_Status s ON f.id_status = s.id_status\nGROUP BY l.provinsi\nORDER BY pct_terlambat DESC;",
    }

    sel_example = st.selectbox("📋 Pilih Contoh Query", list(example_queries.keys()))
    sql_input = st.text_area("SQL Query", value=example_queries[sel_example], height=160,
                              help="Ketik query SQL ke database SQLite Star Schema")

    col_run, col_dl = st.columns([1,5])
    run = col_run.button("▶ Jalankan", type="primary")

    if run and sql_input.strip():
        try:
            result_df = query(sql_input)
            st.success(f"✅ {len(result_df)} baris dikembalikan")
            st.dataframe(result_df, use_container_width=True, hide_index=True)

            # Auto-visualize jika <= 3 kolom numerik
            num_cols = result_df.select_dtypes(include="number").columns.tolist()
            str_cols = result_df.select_dtypes(include="object").columns.tolist()

            if len(num_cols) >= 1 and len(str_cols) >= 1:
                st.markdown('<div class="section-header">Visualisasi Otomatis Hasil Query</div>', unsafe_allow_html=True)
                viz_col = st.selectbox("Kolom nilai", num_cols)
                fig_sql = px.bar(result_df, x=str_cols[0], y=viz_col,
                                 color=str_cols[1] if len(str_cols) > 1 else str_cols[0],
                                 color_discrete_sequence=COLORS,
                                 labels={str_cols[0]: str_cols[0], viz_col: viz_col})
                fig_sql.update_traces(marker_line_width=0)
                dl(fig_sql, f"Hasil Query: {viz_col} per {str_cols[0]}", 360)
                st.plotly_chart(fig_sql, use_container_width=True)

            csv = result_df.to_csv(index=False).encode()
            col_dl.download_button("⬇ Download CSV", csv, "hasil_query.sql.csv", "text/csv")
        except Exception as e:
            st.error(f"❌ SQL Error: {e}")

    st.markdown('<div class="section-header">Struktur Tabel Database</div>', unsafe_allow_html=True)
    tables = query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    for tbl in tables["name"]:
        with st.expander(f"🗂 {tbl}"):
            info = query(f"PRAGMA table_info({tbl})")
            st.dataframe(info[["name","type","pk"]], use_container_width=True, hide_index=True)

# Footer
st.markdown("""
<div style='text-align:center;padding:40px 0 20px 0;font-size:11px;color:#484F58;'>
    DataWareShip · Star Schema · ETL · B-Tree/Bitmap Index · Materialized View · Streaming · SQLite
</div>""", unsafe_allow_html=True)
