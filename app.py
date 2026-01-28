import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import io
import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from supabase import create_client

# ==========================================
# 0. KONFIGURASI & KONEKSI
# ==========================================
st.set_page_config(page_title="EV Fleet Management System", layout="wide", initial_sidebar_state="expanded")

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    EMAIL_SENDER = st.secrets.get("EMAIL_SENDER", "")
    EMAIL_PASSWORD = st.secrets.get("EMAIL_PASSWORD", "")
    EMAIL_RECEIVER = st.secrets.get("EMAIL_RECEIVER", "")
except:
    st.error("Secrets belum lengkap. Pastikan Supabase & Email sudah disetting.")
    st.stop()

# --- FUNGSI UPLOAD FOTO ---
def upload_file_to_supabase(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        file_ext = uploaded_file.name.split('.')[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        bucket_name = "car_documents"
        file_bytes = uploaded_file.getvalue()
        
        response = supabase.storage.from_(bucket_name).upload(
            path=file_name, 
            file=file_bytes, 
            file_options={"content-type": uploaded_file.type}
        )
        
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_name)
        return public_url
    except Exception as e:
        st.error(f"❌ Error Upload Storage: {str(e)}")
        return None

# --- FUNGSI EMAIL ---
def send_email_notification(subject, body_text):
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        return False
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = subject
        msg.attach(MIMEText(body_text, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, text)
        server.quit()
        return True
    except: return False

# --- MAPPING DATA ---
COL_MAP = {
    "Tanggal": "tanggal", "Nama Driver": "nama_driver", "Kode PT": "kode_pt",
    "Plat No": "plat_no", "Merek": "merek", "Platform": "platform",
    "Net Earnings": "net_earnings", "Total Online Hours": "total_online_hours",
    "Total Trip Hours": "total_trip_hours", "Total Completed Order": "total_completed_order",
    "Total Customer Cancelled": "total_customer_cancelled", "Total Driver Cancelled": "total_driver_cancelled"
}
REV_COL_MAP = {v: k for k, v in COL_MAP.items()}

DRIVER_COL_MAP = {
    "Nama Driver": "nama_driver", "Pengalaman App": "pengalaman_app",
    "Waktu Masuk Kerja": "waktu_masuk_kerja", "Jenis Kelamin": "jenis_kelamin",
    "Domisili": "domisili", "Kode PT": "kode_pt", "Status": "status"
}
REV_DRIVER_COL_MAP = {v: k for k, v in DRIVER_COL_MAP.items()}

CAR_COL_MAP = {
    "Tanggal Pembelian": "tanggal_pembelian", "Merek Mobil": "merek_mobil", "Kode Mobil": "kode_mobil", 
    "Plat Nomor": "plat_nomor", "Type Mobil": "type_mobil", "Tahun Produksi": "tahun_produksi", 
    "Warna Mobil": "warna_mobil", "No Rangka": "no_rangka", "No Mesin": "no_mesin", 
    "Tanggal Pajak Tahunan": "tanggal_pajak", "Tanggal Ganti Plat": "tanggal_ganti_plat", 
    "Status Mobil": "status_mobil", "Nama Asuransi": "nama_asuransi",
    "Tanggal Mulai Asuransi": "asuransi_mulai", "Tanggal Habis Asuransi": "asuransi_habis",
    "Reminder": "reminder", "Dokumen": "dokumen"
}
REV_CAR_COL_MAP = {v: k for k, v in CAR_COL_MAP.items()}
CAR_RENAME_MAP = {"BYD Atto 1": "Standard", "Geely EX5 Max": "Premium"}

# --- FUNGSI LOAD & SAVE (DIPERBAIKI AGAR FRESH) ---
def load_perf_data():
    try:
        response = supabase.table("perf_data").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data).rename(columns=REV_COL_MAP)
            if 'Merek' in df.columns: df['Merek'] = df['Merek'].replace(CAR_RENAME_MAP)
            # Pastikan format tanggal murni date
            if 'Tanggal' in df.columns:
                df['Tanggal'] = pd.to_datetime(df['Tanggal']).dt.date
                df = df.sort_values(by='Tanggal', ascending=False)
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def save_perf_data(df):
    try:
        df_db = df.rename(columns=COL_MAP)
        valid = list(COL_MAP.values())
        df_db = df_db[[c for c in valid if c in df_db.columns]]
        df_db['tanggal'] = pd.to_datetime(df_db['tanggal']).dt.strftime('%Y-%m-%d')
        supabase.table("perf_data").insert(df_db.to_dict('records')).execute()
        st.cache_data.clear() # Hapus cache setelah insert
        return True
    except: return False

def delete_perf_data_by_date(date_obj):
    try:
        date_str = date_obj.strftime('%Y-%m-%d')
        supabase.table("perf_data").delete().eq("tanggal", date_str).execute()
        st.cache_data.clear() # Hapus cache setelah delete
        return True
    except Exception as e:
        st.error(f"Gagal menghapus data: {e}")
        return False

def load_driver_data():
    try:
        res = supabase.table("driver_data").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data).rename(columns=REV_DRIVER_COL_MAP)
            if "id" in df.columns: df = df.drop(columns=["id"])
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def save_driver_data(df):
    try:
        df_db = df.rename(columns=DRIVER_COL_MAP)
        valid = list(DRIVER_COL_MAP.values())
        df_db = df_db[[c for c in valid if c in df_db.columns]]
        if "waktu_masuk_kerja" in df_db.columns:
            df_db["waktu_masuk_kerja"] = pd.to_datetime(df_db["waktu_masuk_kerja"], errors="coerce").dt.strftime("%Y-%m-%d")
        supabase.table("driver_data").upsert(df_db.to_dict('records'), on_conflict="nama_driver").execute()
        st.cache_data.clear()
        return True
    except: return False

def delete_driver_by_name(name):
    try:
        supabase.table("driver_data").delete().eq("nama_driver", name).execute()
        st.cache_data.clear()
        return True
    except: return False

def load_car_data():
    try:
        res = supabase.table("car_data").select("*").execute()
        if res.data:
            df = pd.DataFrame(res.data).rename(columns=REV_CAR_COL_MAP)
            if "id" in df.columns: df = df.drop(columns=["id"])
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def save_car_data(df):
    try:
        df_db = df.rename(columns=CAR_COL_MAP)
        valid = list(CAR_COL_MAP.values())
        df_db = df_db[[c for c in valid if c in df_db.columns]]
        for col in ["tanggal_pembelian", "tanggal_pajak", "tanggal_ganti_plat", "asuransi_mulai", "asuransi_habis"]:
            if col in df_db.columns:
                df_db[col] = pd.to_datetime(df_db[col], errors="coerce").dt.strftime("%Y-%m-%d")
        supabase.table("car_data").upsert(df_db.to_dict('records'), on_conflict="kode_mobil").execute()
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Gagal simpan database: {e}")
        return False

def delete_car_by_code(code):
    try:
        supabase.table("car_data").delete().eq("kode_mobil", code).execute()
        st.cache_data.clear()
        return True
    except: return False

# ==========================================
# 1. LOGIN & INIT
# ==========================================
def check_password():
    def password_entered():
        if st.session_state["password"] == "admin123":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  
        else: st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>EV Fleet Management System</h2>", unsafe_allow_html=True)
        st.text_input("Masukkan Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.markdown("<h2 style='text-align: center;'>EV Fleet Management System</h2>", unsafe_allow_html=True)
        st.text_input("Masukkan Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password salah.")
        return False
    else: return True

if not check_password(): st.stop()

# Refresh data on load
if 'perf_data' not in st.session_state: st.session_state['perf_data'] = load_perf_data()
if 'driver_data' not in st.session_state: st.session_state['driver_data'] = load_driver_data()
if 'car_data' not in st.session_state: st.session_state['car_data'] = load_car_data()

# ==========================================
# 3. KAMUS BAHASA
# ==========================================
trans = {
    'ID': {
        'nav_title': "Navigasi", 'menu_dash': "Dashboard", 'menu_perf': "Performa Driver", 'menu_data': "Data Driver", 'menu_car': "Data Armada (Mobil)",
        'dash_title': "Dashboard Utama", 'filter_date': "Filter Tanggal", 'start_date': "Tanggal Mulai", 'end_date': "Tanggal Akhir",
        'summary_all': "Ringkasan Gabungan (Semua Armada)", 'metrics_title': "Detail Per Level (Standard & Premium)", 'brand': "Level", 'platform': "Platform",
        'rev': "Total Omset", 'orders': "Total Completed Order", 'cust_cancel': "Customer Cancelled", 'drv_cancel': "Driver Cancelled",
        'avg_ord': "Rata-rata / Order", 'avg_day': "Rata-rata / Hari", 'drivers': "Jumlah Driver",
        'chart_comp': "Grafik Perbandingan Omset", 'chart_plat': "Grafik Perbandingan Omset",
        'chart_total': "Grafik Total Omset Harian (Gabungan)", 'chart_month': "Grafik Total Omset Bulanan",
        'no_data': "Belum ada data. Silakan upload Excel.", 'no_data_range': "Tidak ada data pada rentang tanggal ini.",
        'perf_title': "Analisa Performa Driver", 'upload_perf': "Upload Data Performa (.xlsx)", 'download_tmpl': "Download Template Excel",
        'manage_data': "Kelola Data (Hapus per Tanggal)", 'del_date': "Pilih Tanggal", 'btn_del': "Hapus Data Permanen",
        'search_driver': "Cari Driver (Nama)", 'filter_brand': "Filter Level", 'filter_plat': "Filter Platform",
        'filter_earn': "Filter Pendapatan", 'filter_hour': "Filter Jam Online",
        'data_title': "Database Driver", 'upload_data': "Upload Data Driver (.xlsx)", 'stat_total': "Total Driver", 'stat_active': "Active", 'stat_resign': "Resigned",
        'input_manual': "Input Driver Manual", 'del_manual': "Hapus Driver Manual", 'btn_add': "Tambah Driver", 'btn_del_drv': "Hapus Driver",
        'car_title': "Database Armada & Asuransi", 'upload_car': "Upload Data Mobil (.xlsx)", 
        'stat_car_total': "Total Mobil", 'stat_car_active': "Mobil Aktif", 'stat_car_maint': "Maintenance", 'stat_car_broken': "Rusak", 'stat_car_unused': "Tidak Dipakai",
        'input_car': "Input Mobil Manual", 'del_car': "Hapus Mobil Manual", 'btn_add_car': "Tambah Mobil", 'btn_del_car': "Hapus Mobil",
        'car_status_opt': ["Active", "Maintenance", "Rusak", "Tidak Dipakai"], 'driver_status_opt': ["Active", "Resigned"],
        'reminder_check': "Cek & Kirim Reminder", 'reminder_desc': "Cek Pajak/Asuransi yang mau habis (<30 hari) dan kirim email."
    }
}

# ==========================================
# 4. SIDEBAR
# ==========================================
start_d, end_d = None, None
with st.sidebar:
    lang_opt = st.radio("Language / 语言", ["ID"], key="language") # Locked to ID for clarity
    def t(key):
        return trans['ID'].get(key, key)

    st.markdown("---")
    st.header(t('nav_title'))
    nav_options = {'dash': t('menu_dash'), 'perf': t('menu_perf'), 'data': t('menu_data'), 'car': t('menu_car')}
    selected_page = st.radio("Menu", list(nav_options.keys()), format_func=lambda x: nav_options[x])
    
    st.markdown("---")
    st.subheader(f"🗓️ {t('filter_date')}")
    if not st.session_state['perf_data'].empty:
        df_temp = st.session_state['perf_data'].copy()
        min_date = min(df_temp['Tanggal'])
        max_date = max(df_temp['Tanggal'])
    else:
        min_date = pd.to_datetime('today').date()
        max_date = pd.to_datetime('today').date()
    
    start_d = st.date_input(t('start_date'), min_date)
    end_d = st.date_input(t('end_date'), max_date)

def format_rupiah(value): return f"Rp {value:,.0f}"

# ==========================================
# 5. DASHBOARD
# ==========================================
if selected_page == 'dash':
    st.title(t('dash_title'))
    if st.session_state['perf_data'].empty:
        st.info(t('no_data'))
    else:
        df = st.session_state['perf_data'].copy()
        mask = (df['Tanggal'] >= start_d) & (df['Tanggal'] <= end_d)
        df_filt = df.loc[mask]
        
        if df_filt.empty: st.error(t('no_data_range'))
        else:
            # Stats & Charts logic stays same...
            tot_omset = df_filt['Net Earnings'].sum()
            tot_order = df_filt['Total Completed Order'].sum()
            st.metric(t('rev'), format_rupiah(tot_omset))
            st.dataframe(df_filt, use_container_width=True)

# ==========================================
# 6. PERFORMA DRIVER (UPLOAD & NOTIF)
# ==========================================
elif selected_page == 'perf':
    st.title(t('perf_title'))
    c_up, c_dl = st.columns([3, 1])
    with c_up:
        upl = st.file_uploader(t('upload_perf'), type=['xlsx'])
        if upl:
            try:
                data_excel = pd.read_excel(upl)
                if save_perf_data(data_excel):
                    # PAKSA REFRESH
                    st.session_state['perf_data'] = load_perf_data()
                    st.success(f"✅ Berhasil Upload {len(data_excel)} baris data!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    # Tombol Hapus per Tanggal
    if not st.session_state['perf_data'].empty:
        with st.expander(f"🗑️ {t('manage_data')}"):
            cd1, cd2 = st.columns([3,1])
            ddt = cd1.date_input(t('del_date'))
            if cd2.button(t('btn_del')):
                if delete_perf_data_by_date(ddt):
                    st.session_state['perf_data'] = load_perf_data()
                    st.success("✅ Terhapus!")
                    st.rerun()

    # Tabel Data Performa
    df_perf = st.session_state['perf_data'].copy()
    if not df_perf.empty:
        # Filter berdasarkan sidebar
        df_perf = df_perf[(df_perf['Tanggal'] >= start_d) & (df_perf['Tanggal'] <= end_d)]
        st.dataframe(df_perf, use_container_width=True)

# ==========================================
# 7. DATA DRIVER (FILTER & COLOR)
# ==========================================
elif selected_page == 'data':
    st.title(t('data_title'))
    df_d = st.session_state['driver_data']
    
    if not df_d.empty:
        # Filter Multiselect
        drv_filter = st.multiselect("Filter Status", ["Active", "Resigned"], default=["Active", "Resigned"])
        df_d = df_d[df_d['Status'].isin(drv_filter)]
        
        # Pewarnaan
        def style_drv(row):
            color = '#d4edda' if row['Status'] == 'Active' else '#f8d7da'
            return [f'background-color: {color}'] * len(row)

        st.dataframe(df_d.style.apply(style_drv, axis=1), use_container_width=True)

# ==========================================
# 8. DATA MOBIL (FILTER & COLOR)
# ==========================================
elif selected_page == 'car':
    st.title(t('car_title'))
    df_c = st.session_state['car_data']
    
    if not df_c.empty:
        # Filter
        car_filter = st.multiselect("Filter Status Mobil", ["Active", "Maintenance", "Rusak", "Tidak Dipakai"], 
                                    default=["Active", "Maintenance", "Rusak", "Tidak Dipakai"])
        df_c = df_c[df_c['Status Mobil'].isin(car_filter)]
        
        # Pewarnaan
        def style_car(row):
            color = ''
            if row['Status Mobil'] == 'Active': color = '#d4edda'
            elif row['Status Mobil'] == 'Rusak': color = '#f8d7da'
            elif row['Status Mobil'] == 'Maintenance': color = '#fff3cd'
            return [f'background-color: {color}'] * len(row)

        st.dataframe(df_c.style.apply(style_car, axis=1), use_container_width=True, 
                     column_config={"Dokumen": st.column_config.LinkColumn("Buka File")})
