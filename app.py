import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import io
from supabase import create_client

# ==========================================
# 0. SUPABASE CONNECTION & HELPER
# ==========================================
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except:
    st.error("Secrets Supabase belum disetting dengan benar.")
    st.stop()

# --- MAPPING NAMA KOLOM (Excel <-> Database) ---
COL_MAP = {
    "Tanggal": "tanggal",
    "Nama Driver": "nama_driver",
    "Kode PT": "kode_pt",
    "Plat No": "plat_no",
    "Merek": "merek",
    "Platform": "platform",
    "Net Earnings": "net_earnings",
    "Total Online Hours": "total_online_hours",
    "Total Trip Hours": "total_trip_hours",
    "Total Completed Order": "total_completed_order",
    "Total Customer Cancelled": "total_customer_cancelled",
    "Total Driver Cancelled": "total_driver_cancelled"
}

REV_COL_MAP = {v: k for k, v in COL_MAP.items()}

# --- MAPPING REBRANDING (BYD->Standard, Geely->Premium) ---
CAR_RENAME_MAP = {
    "BYD Atto 1": "Standard",
    "Geely EX5 Max": "Premium"
}

def load_perf_data():
    """Tarik data dari Supabase dan ubah nama kolomnya jadi format Dashboard"""
    try:
        response = supabase.table("perf_data").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df = df.rename(columns=REV_COL_MAP)
            
            # --- UBAH NAMA MEREK MENJADI LEVEL (STANDARD/PREMIUM) ---
            if 'Merek' in df.columns:
                df['Merek'] = df['Merek'].replace(CAR_RENAME_MAP)
                
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Gagal tarik data: {e}")
        return pd.DataFrame()

def save_perf_data(df):
    """Simpan data Excel ke Supabase"""
    try:
        df_db = df.rename(columns=COL_MAP)
        valid_cols = list(COL_MAP.values())
        df_db = df_db[[c for c in valid_cols if c in df_db.columns]]
        df_db['tanggal'] = pd.to_datetime(df_db['tanggal']).dt.strftime('%Y-%m-%d')
        data_records = df_db.to_dict(orient='records')
        supabase.table("perf_data").insert(data_records).execute()
        return True
    except Exception as e:
        st.error(f"Gagal simpan data: {e}")
        return False

def delete_perf_data_by_date(date_obj):
    try:
        date_str = date_obj.strftime('%Y-%m-%d')
        supabase.table("perf_data").delete().eq("tanggal", date_str).execute()
        return True
    except Exception as e:
        st.error(f"Gagal hapus data: {e}")
        return False

# ==========================================
# 1. SISTEM LOGIN
# ==========================================
def check_password():
    def password_entered():
        if st.session_state["password"] == "admin123":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>EV Fleet Management System</h2>", unsafe_allow_html=True)
        st.text_input("Masukkan Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center;'>EV Fleet Management System</h2>", unsafe_allow_html=True)
        st.text_input("Masukkan Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password salah.")
        return False
    else:
        return True

if not check_password():
    st.stop()

if 'perf_data' not in st.session_state:
    st.session_state['perf_data'] = load_perf_data()

# ==========================================
# 2. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="EV Fleet Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 3. SIDEBAR & NAVIGASI
# ==========================================
with st.sidebar:
    st.header("Navigasi")
    nav_options = {'dash': "Dashboard", 'perf': "Performa Driver", 'data': "Data Driver"}
    selected_page = st.radio("Menu", list(nav_options.keys()), format_func=lambda x: nav_options[x])

def generate_excel_template(type_data):
    buffer = io.BytesIO()
    if type_data == 'perf':
        columns = list(COL_MAP.keys())
    else:
        columns = ["Nama Driver", "Pengalaman App", "Waktu Masuk Kerja", "Jenis Kelamin", "Domisili", "Kode PT", "Status"]
    df = pd.DataFrame([], columns=columns)
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
    return buffer

def format_rupiah(value):
    return f"Rp {value:,.0f}"

# ==========================================
# 5. HALAMAN 1: DASHBOARD (DIPERBARUI SESUAI GAMBAR)
# ==========================================
if selected_page == 'dash':
    st.title("Dashboard Utama")
    
    if 'perf_data' not in st.session_state or st.session_state['perf_data'].empty:
        st.info("Belum ada data. Silakan upload Excel.")
    else:
        df = st.session_state['perf_data'].copy()
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        
        if 'Platform' not in df.columns:
            df['Platform'] = 'Unknown'

        # --- 1. FILTER TANGGAL (Side by Side) ---
        with st.container():
            st.subheader("Filter Tanggal")
            c1, c2 = st.columns(2)
            min_d = df['Tanggal'].min().date()
            max_d = df['Tanggal'].max().date()
            start_d = c1.date_input("Tanggal Mulai", min_d)
            end_d = c2.date_input("Tanggal Akhir", max_d)
        
        mask = (df['Tanggal'].dt.date >= start_d) & (df['Tanggal'].dt.date <= end_d)
        df_filt = df.loc[mask]
        
        if df_filt.empty:
            st.error("Tidak ada data pada rentang tanggal ini.")
        else:
            st.divider()
            
            # --- CALCULATE METRICS ---
            tot_omset = df_filt['Net Earnings'].sum()
            tot_order = df_filt['Total Completed Order'].sum()
            tot_cust_canc = df_filt['Total Customer Cancelled'].sum()
            tot_drv_canc = df_filt['Total Driver Cancelled'].sum()
            tot_driver = df_filt['Nama Driver'].nunique()
            
            # Metric Baru: Rata-rata
            avg_earn_per_order = tot_omset / tot_order if tot_order > 0 else 0
            unique_days = df_filt['Tanggal'].nunique()
            avg_earn_per_day = tot_omset / unique_days if unique_days > 0 else 0

            # --- 2. RINGKASAN GABUNGAN ---
            st.subheader("📊 Ringkasan Gabungan (Semua Armada)")
            
            # Baris 1: Metric Utama + Rata-rata
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Omset", format_rupiah(tot_omset))
            m2.metric("Total Completed Order", f"{tot_order}")
            m3.metric("Rata-rata / Order", format_rupiah(avg_earn_per_order))
            m4.metric("Rata-rata / Hari", format_rupiah(avg_earn_per_day))
            
            # Baris 2: Metric Tambahan
            m5, m6, m7 = st.columns(3)
            m5.metric("Customer Cancelled", f"{tot_cust_canc}")
            m6.metric("Driver Cancelled", f"{tot_drv_canc}")
            m7.metric("Jumlah Driver Aktif", f"{tot_driver}")
            
            st.markdown("---")

            # --- 3. DETAIL PER LEVEL (STANDARD & PREMIUM) ---
            st.subheader("🚗 Detail Per Level (Standard & Premium)")
            
            target_levels = ["Standard", "Premium"]
            
            for level in target_levels:
                level_df = df_filt[df_filt['Merek'] == level]
                
                if not level_df.empty:
                    st.markdown(f"### Level: {level}")
                    
                    # Hitung Metrics Level
                    l_omset = level_df['Net Earnings'].sum()
                    l_order = level_df['Total Completed Order'].sum()
                    l_avg_ord = l_omset / l_order if l_order > 0 else 0
                    l_days = level_df['Tanggal'].nunique()
                    l_avg_day = l_omset / l_days if l_days > 0 else 0
                    
                    # Layout: Metrics di Kiri (2/3), Pie Chart di Kanan (1/3)
                    col_metrics, col_chart = st.columns([2, 1])
                    
                    with col_metrics:
                        # Baris 1 Metric Level
                        c1, c2 = st.columns(2)
                        c1.metric("Total Omset", format_rupiah(l_omset))
                        c2.metric("Total Order", f"{l_order}")
                        
                        # Baris 2 Metric Level
                        c3, c4 = st.columns(2)
                        c3.metric("Rata-rata / Order", format_rupiah(l_avg_ord))
                        c4.metric("Rata-rata / Hari", format_rupiah(l_avg_day))

                        # Baris 3 Metric Level
                        c5, c6 = st.columns(2)
                        c5.metric("Cust Cancel", level_df['Total Customer Cancelled'].sum())
                        c6.metric("Driver Cancel", level_df['Total Driver Cancelled'].sum())
                    
                    with col_chart:
                        # Pie Chart: Proporsi Omset berdasarkan Platform (Gojek vs Grab)
                        pie_data = level_df.groupby('Platform')['Net Earnings'].sum().reset_index()
                        fig_pie = px.pie(pie_data, values='Net Earnings', names='Platform', 
                                         title=f"Proporsi Omset {level}", 
                                         hole=0.4)
                        # Hide legend agar compact
                        fig_pie.update_layout(showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5), margin=dict(t=40, b=0, l=0, r=0), height=300)
                        st.plotly_chart(fig_pie, use_container_width=True)
                    
                    st.divider()

            # --- 4. GRAFIK PERBANDINGAN & TOTAL ---
            # Siapkan Data Harian (DateOnly)
            df_filt['DateOnly'] = df_filt['Tanggal'].dt.strftime('%Y-%m-%d')
            
            # Grouping Data Utama
            df_chart = df_filt.groupby(['DateOnly', 'Merek', 'Platform'])['Net Earnings'].sum().reset_index()

            # Kolom untuk 2 Grafik Perbandingan
            col_g1, col_g2 = st.columns(2)
            
            # Grafik 1: Standard (Gojek vs Grab)
            with col_g1:
                st.subheader("Grafik Standard (Gojek vs Grab)")
                data_std = df_chart[df_chart['Merek'] == 'Standard']
                if not data_std.empty:
                    fig_std = px.line(data_std, x='DateOnly', y='Net Earnings', color='Platform', markers=True)
                    fig_std.update_layout(xaxis_title="Tanggal", yaxis_title="Omset")
                    st.plotly_chart(fig_std, use_container_width=True)
                else:
                    st.info("Tidak ada data Standard.")

            # Grafik 2: Premium (Gojek vs Grab)
            with col_g2:
                st.subheader("Grafik Premium (Gojek vs Grab)")
                data_prm = df_chart[df_chart['Merek'] == 'Premium']
                if not data_prm.empty:
                    fig_prm = px.line(data_prm, x='DateOnly', y='Net Earnings', color='Platform', markers=True)
                    fig_prm.update_layout(xaxis_title="Tanggal", yaxis_title="Omset")
                    st.plotly_chart(fig_prm, use_container_width=True)
                else:
                    st.info("Tidak ada data Premium.")
            
            # Grafik 3: Total Omset Harian (Gabungan)
            st.subheader("Grafik Total Omset Harian (Gabungan)")
            df_day = df_filt.groupby(['DateOnly'])['Net Earnings'].sum().reset_index()
            fig_d = px.line(df_day, x='DateOnly', y='Net Earnings', markers=True)
            # Pastikan format sumbu X hanya tanggal
            fig_d.update_layout(xaxis_title="Tanggal", yaxis_title="Total Omset", xaxis=dict(tickformat="%d-%m-%Y"))
            st.plotly_chart(fig_d, use_container_width=True)
            
            # Grafik 4: Total Omset Bulanan
            st.subheader("Grafik Total Omset Bulanan")
            df_filt['Month'] = df_filt['Tanggal'].dt.strftime('%Y-%m')
            df_mon = df_filt.groupby(['Month'])['Net Earnings'].sum().reset_index()
            fig_m = px.line(df_mon, x='Month', y='Net Earnings', markers=True)
            fig_m.update_layout(xaxis_title="Bulan", yaxis_title="Total Omset")
            st.plotly_chart(fig_m, use_container_width=True)

# ==========================================
# 6. HALAMAN LAIN (TETAP SAMA / TIDAK DIUBAH)
# ==========================================
elif selected_page == 'perf':
    st.title("Analisa Performa Driver")
    
    col_up, col_dl = st.columns([3, 1])
    with col_up:
        uploaded = st.file_uploader("Upload Data Performa (.xlsx)", type=['xlsx'])
        if uploaded:
            try:
                df_new = pd.read_excel(uploaded)
                with st.spinner("Menyimpan ke Database..."):
                    if save_perf_data(df_new):
                        st.session_state['perf_data'] = load_perf_data()
                        st.success("Sukses Upload!")
            except Exception as e: st.error(f"Error: {e}")
    with col_dl:
        st.write(""); st.write("")
        st.download_button("📥 Download Template", generate_excel_template('perf'), "template.xlsx")
    
    if 'perf_data' in st.session_state:
        st.dataframe(st.session_state['perf_data'], use_container_width=True)

elif selected_page == 'data':
    st.title("Data Driver")
    st.info("Halaman ini belum diubah (sesuai permintaan).")
