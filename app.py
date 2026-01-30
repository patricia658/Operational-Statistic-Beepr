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
    if uploaded_file is None: return None
    try:
        file_ext = uploaded_file.name.split('.')[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        bucket_name = "car_documents"
        file_bytes = uploaded_file.getvalue()
        supabase.storage.from_(bucket_name).upload(path=file_name, file=file_bytes, file_options={"content-type": uploaded_file.type})
        return supabase.storage.from_(bucket_name).get_public_url(file_name)
    except Exception as e:
        st.error(f"❌ Error Upload Storage: {str(e)}")
        return None

# --- FUNGSI EMAIL ---
def send_email_notification(subject, body_text):
    if not EMAIL_SENDER or not EMAIL_PASSWORD: return False
    try:
        msg = MIMEMultipart(); msg['From'] = EMAIL_SENDER; msg['To'] = EMAIL_RECEIVER; msg['Subject'] = subject
        msg.attach(MIMEText(body_text, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string()); server.quit()
        return True
    except: return False

# ==========================================
# PATCH 1: Tambah Fungsi Normalize Shift (WAJIB)
# ==========================================
def format_rupiah(value): return f"Rp {value:,.0f}"

# ✅ NORMALIZE SHIFT VALUE (Sesuai Patch 1 di foto)
def normalize_shift(val):
    if pd.isna(val):
        return "Full day"
    v = str(val).strip().lower()
    
    if v in ["pagi", "morning"]:
        return "Pagi"
    if v in ["malam", "night"]:
        return "Malam"
    
    # Semua variasi Full Day
    if v in ["full day", "fullday", "full-day", "full_day", "seharian"]:
        return "Full day"
    
    # Default fallback
    return "Full day"

# ==========================================
# MAPPING DATA (STEP 1: Tambah kolom Shift)
# ==========================================
COL_MAP = {
    "Tanggal": "tanggal", 
    "Nama Driver": "nama_driver", 
    "Kode PT": "kode_pt",
    "Plat No": "plat_no", 
    "Merek": "merek", 
    "Platform": "platform",
    "Shift": "shift",  # ✅ STEP 1-A: Added to COL_MAP
    "Net Earnings": "net_earnings", 
    "Total Online Hours": "total_online_hours",
    "Total Trip Hours": "total_trip_hours", 
    "Total Completed Order": "total_completed_order",
    "Total Customer Cancelled": "total_customer_cancelled", 
    "Total Driver Cancelled": "total_driver_cancelled"
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

# --- FUNGSI LOAD & SAVE ---
def load_perf_data():
    try:
        response = supabase.table("perf_data").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data).rename(columns=REV_COL_MAP)
            if 'Merek' in df.columns: df['Merek'] = df['Merek'].replace(CAR_RENAME_MAP)
            
            # ✅ PATCH 2: Normalize Shift Saat Load Data
            if "Shift" in df.columns:
                df["Shift"] = df["Shift"].apply(normalize_shift)
                
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def save_perf_data(df):
    try:
        df_db = df.rename(columns=COL_MAP)
        
        # ✅ PATCH 3: Normalize Shift Saat Upload Excel
        if "shift" in df_db.columns:
            df_db["shift"] = df_db["shift"].apply(normalize_shift)
            
        df_db = df_db.dropna(subset=['tanggal'])
        valid = list(COL_MAP.values())
        df_db = df_db[[c for c in valid if c in df_db.columns]]
        num_cols = ['net_earnings', 'total_online_hours', 'total_trip_hours', 'total_completed_order', 'total_customer_cancelled', 'total_driver_cancelled']
        for col in num_cols:
            if col in df_db.columns: df_db[col] = df_db[col].fillna(0)
        df_db['tanggal'] = pd.to_datetime(df_db['tanggal']).dt.strftime('%Y-%m-%d')
        supabase.table("perf_data").upsert(df_db.to_dict('records'), on_conflict="tanggal,nama_driver,platform").execute()
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return False

def delete_perf_data_by_date(date_obj):
    try:
        supabase.table("perf_data").delete().eq("tanggal", date_obj.strftime('%Y-%m-%d')).execute()
        return True
    except: return False

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
        return True
    except: return False

def delete_driver_by_name(name):
    try:
        supabase.table("driver_data").delete().eq("nama_driver", name).execute()
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
        return True
    except Exception as e:
        st.error(f"Gagal simpan database: {e}"); return False

def delete_car_by_code(code):
    try:
        supabase.table("car_data").delete().eq("kode_mobil", code).execute()
        return True
    except: return False

# ==========================================
# 1. LOGIN & INIT
# ==========================================
def check_password():
    def password_entered():
        if st.session_state["password"] == "admin123":
            st.session_state["password_correct"] = True; del st.session_state["password"]
        else: st.session_state["password_correct"] = False
    if "password_correct" not in st.session_state:
        st.markdown("<h2 style='text-align: center;'>EV Fleet Management System</h2>", unsafe_allow_html=True)
        st.text_input("Masukkan Password", type="password", on_change=password_entered, key="password"); return False
    elif not st.session_state["password_correct"]:
        st.text_input("Masukkan Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password salah."); return False
    else: return True

if not check_password(): st.stop()

if 'perf_data' not in st.session_state: st.session_state['perf_data'] = load_perf_data()
if 'driver_data' not in st.session_state: st.session_state['driver_data'] = load_driver_data()
if 'car_data' not in st.session_state: st.session_state['car_data'] = load_car_data()

# ==========================================
# 3. KAMUS BAHASA (BILINGUAL PATCH)
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
        'filter_title': "Filter", 'shift_filter': "Filter Shift", 'target_analysis': "Analisis Target", 'summary_driver': "Summary Driver", 'detail_daily': "Detail Harian",
        'income': "Pendapatan", 'online_hours': "Jam Online", 'standard': "STANDARD", 'premium': "PREMIUM",
        'deleted': "Deleted", 'success_upload': "Upload & Update Berhasil!", 'shift_income': "Omset per Shift",
        'car_title': "Database Armada & Asuransi", 'upload_car': "Upload Data Mobil (.xlsx)", 
        'reminder_check': "Cek & Kirim Reminder", 'reminder_desc': "Cek Pajak/Asuransi yang mau habis (<30 hari) dan kirim email."
    },
    '中文': {
        'nav_title': "导航", 'menu_dash': "仪表盘", 'menu_perf': "司机表现", 'menu_data': "司机数据", 'menu_car': "车辆管理",
        'dash_title': "主仪表盘", 'filter_date': "日期筛选", 'start_date': "开始日期", 'end_date': "结束日期",
        'summary_all': "综合汇总 (全部车队)", 'metrics_title': "等级详情 (Standard & Premium)", 'brand': "等级", 'platform': "平台",
        'rev': "总收入", 'orders': "完成订单总数", 'drivers': "司机数量",
        'avg_ord': "每单平均收入", 'avg_day': "每日平均收入", 'cust_cancel': "乘客取消", 'drv_cancel': "司机取消",
        'chart_total': "每日总收入图表", 'chart_month': "每月总收入图表",
        'no_data': "暂无数据，请上传 Excel 文件。", 'no_data_range': "该日期范围内没有数据。",
        'perf_title': "司机表现分析", 'upload_perf': "上传表现数据 (.xlsx)", 'download_tmpl': "下载 Excel 模板",
        'manage_data': "数据管理 (按日期删除)", 'del_date': "选择日期", 'btn_del': "永久删除数据",
        'filter_title': "筛选", 'shift_filter': "班次筛选", 'target_analysis': "目标分析", 'summary_driver': "司机汇总", 'detail_daily': "每日明细",
        'income': "收入", 'online_hours': "在线时长", 'standard': "标准车", 'premium': "高端车",
        'deleted': "已删除", 'success_upload': "上传更新成功！", 'shift_income': "按班次收入",
        'car_title': "车辆数据库与保险管理", 'upload_car': "上传车辆数据 (.xlsx)",
        'reminder_check': "检查并发送提醒", 'reminder_desc': "检查即将到期的税务/保险 (30天内) 并发送邮件提醒。"
    }
}

# ==========================================
# 4. SIDEBAR
# ==========================================
start_d, end_d = None, None
with st.sidebar:
    # ✅ Sidebar Language (Sesuai Foto 1)
    lang_opt = st.radio("Language", ["ID", "中文"], horizontal=True, key="language")
    def t(key):
        lang = st.session_state.get('language', 'ID'); return trans[lang].get(key, key)
    st.markdown("---"); st.header(t('nav_title'))
    nav_options = {'dash': t('menu_dash'), 'perf': t('menu_perf'), 'data': t('menu_data'), 'car': t('menu_car')}
    selected_page = st.radio("Menu", list(nav_options.keys()), format_func=lambda x: nav_options[x])
    
    st.markdown("---"); st.subheader(f"🔍 {t('filter_title')}")
    st.subheader(f"🗓️ {t('filter_date')}")
    if not st.session_state['perf_data'].empty:
        df_temp = st.session_state['perf_data'].copy()
        df_temp['Tanggal'] = pd.to_datetime(df_temp['Tanggal'])
        min_date = df_temp['Tanggal'].min().date()
        max_date = df_temp['Tanggal'].max().date()
    else: min_date = max_date = pd.to_datetime('today').date()
    start_d = st.date_input(t('start_date'), min_date)
    end_d = st.date_input(t('end_date'), max_date)

# ... (generate_excel_template function remains same)
def generate_excel_template(type_data):
    buffer = io.BytesIO()
    if type_data == 'perf': columns = list(COL_MAP.keys())
    elif type_data == 'driver': columns = list(DRIVER_COL_MAP.keys())
    elif type_data == 'car': columns = list(CAR_COL_MAP.keys())
    df = pd.DataFrame([], columns=columns)
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
    return buffer

# ==========================================
# 5. DASHBOARD
# ==========================================
if selected_page == 'dash':
    st.title(t('dash_title'))
    if st.session_state['perf_data'].empty: st.info(t('no_data'))
    else:
        df = st.session_state['perf_data'].copy(); df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        if 'Platform' not in df.columns: df['Platform'] = 'Unknown'
        df_filt = df.loc[(df['Tanggal'].dt.date >= start_d) & (df['Tanggal'].dt.date <= end_d)]
        if df_filt.empty: st.error(t('no_data_range'))
        else:
            tot_omset = df_filt['Net Earnings'].sum(); tot_order = df_filt['Total Completed Order'].sum()
            tot_cust_canc = df_filt['Total Customer Cancelled'].sum(); tot_drv_canc = df_filt['Total Driver Cancelled'].sum()
            tot_driver = df_filt['Nama Driver'].nunique(); unique_days = df_filt['Tanggal'].nunique()
            avg_earn_per_day = tot_omset / unique_days if unique_days > 0 else 0
            
            st.subheader(f"📊 {t('summary_all')}")
            c1, c2 = st.columns([2.5, 1])
            
            with c1:
                r1a, r1b, r1c = st.columns(3); r1a.metric(t('rev'), format_rupiah(tot_omset)); r1b.metric(t('orders'), f"{tot_order}"); r1c.metric(t('drivers'), f"{tot_driver}")
                r2a, r2b, r2c = st.columns(3); r2a.metric(t('avg_day'), format_rupiah(avg_earn_per_day)); r2b.metric(t('avg_ord'), format_rupiah(tot_omset/tot_order if tot_order>0 else 0)); r2c.metric("Total Cancelled", f"{tot_cust_canc + tot_drv_canc}")
                
                if "Shift" in df_filt.columns:
                    df_filt["Shift"] = df_filt["Shift"].apply(normalize_shift)
                    shift_summary = df_filt.groupby("Shift")["Net Earnings"].sum()
                    pagi = shift_summary.get("Pagi", 0)
                    malam = shift_summary.get("Malam", 0)
                    full_day = shift_summary.get("Full day", 0)
                    
                    st.markdown(f"### 💰 {t('shift_income')}")
                    s1, s2, s3 = st.columns(3)
                    s1.metric("Pagi", format_rupiah(pagi))
                    s2.metric("Malam", format_rupiah(malam))
                    s3.metric("Full day", format_rupiah(full_day))

            # ... (charts code remains same)
            with c2:
                pie_data = df_filt.groupby('Merek')['Net Earnings'].sum().reset_index()
                if not pie_data.empty:
                    fig = px.pie(pie_data, values='Net Earnings', names='Merek', title="Standard vs Premium", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=220, showlegend=False); fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                
                if "Shift" in df_filt.columns:
                    pie_shift = df_filt.groupby("Shift")["Net Earnings"].sum().reset_index()
                    if not pie_shift.empty:
                        fig2 = px.pie(pie_shift, values="Net Earnings", names="Shift", title="Pagi vs Malam vs Full Day", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                        fig2.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=220, showlegend=False); fig2.update_traces(textposition="inside", textinfo="percent+label")
                        st.plotly_chart(fig2, use_container_width=True)

            st.markdown("---"); st.subheader(f"🚗 {t('metrics_title')}")
            for level in ["Standard", "Premium"]:
                l_df = df_filt[df_filt['Merek'] == level]
                if not l_df.empty:
                    st.markdown(f"**Level: {level}**"); lo = l_df['Net Earnings'].sum(); lord = l_df['Total Completed Order'].sum(); lday = l_df['Tanggal'].nunique()
                    ca, cb, cc, cd = st.columns(4); ca.metric(t('rev'), format_rupiah(lo)); cb.metric(t('orders'), f"{lord}"); cc.metric(t('avg_ord'), format_rupiah(lo/lord if lord>0 else 0)); cd.metric(t('avg_day'), format_rupiah(lo/lday if lday>0 else 0))
                    ce, cf, cg, ch = st.columns(4); ce.metric(t('cust_cancel'), f"{l_df['Total Customer Cancelled'].sum()}"); cf.metric(t('drv_cancel'), f"{l_df['Total Driver Cancelled'].sum()}"); cg.metric(t('drivers'), f"{l_df['Nama Driver'].nunique()}"); st.divider()
            
            df_filt['DateStr'] = df_filt['Tanggal'].dt.strftime('%Y-%m-%d'); daily = df_filt.groupby(['DateStr', 'Merek', 'Platform'])['Net Earnings'].sum().reset_index()
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("Standard (Gojek vs Grab)"); ds = daily[daily['Merek']=='Standard']
                if not ds.empty: f1 = px.line(ds, x='DateStr', y='Net Earnings', color='Platform', markers=True); f1.update_xaxes(tickformat="%d-%b", dtick="D1"); st.plotly_chart(f1, use_container_width=True)
            with g2:
                st.subheader("Premium (Gojek vs Grab)"); dp = daily[daily['Merek']=='Premium']
                if not dp.empty: f2 = px.line(dp, x='DateStr', y='Net Earnings', color='Platform', markers=True); f2.update_xaxes(tickformat="%d-%b", dtick="D1"); st.plotly_chart(f2, use_container_width=True)
            st.subheader(t('chart_total')); dtot = df_filt.groupby('DateStr')['Net Earnings'].sum().reset_index()
            f3 = px.line(dtot, x='DateStr', y='Net Earnings', markers=True); f3.update_xaxes(tickformat="%d-%b", dtick="D1"); st.plotly_chart(f3, use_container_width=True)
            st.subheader(t('chart_month')); df_filt['M'] = df_filt['Tanggal'].dt.to_period('M'); dm = df_filt.groupby('M')['Net Earnings'].sum().reset_index(); dm['L'] = dm['M'].dt.strftime("%b'%y")
            f4 = px.line(dm, x='L', y='Net Earnings', markers=True); st.plotly_chart(f4, use_container_width=True)

# ==========================================
# 6. PERFORMA DRIVER
# ==========================================
elif selected_page == 'perf':
    st.title(t('perf_title')); c_up, c_dl = st.columns([3, 1])
    with c_up:
        upl = st.file_uploader(t('upload_perf'), type=['xlsx'], key="perf_uploader")
        if upl:
            if "last_perf_file" not in st.session_state or st.session_state["last_perf_file"] != upl.name:
                try:
                    temp_perf_df = pd.read_excel(upl); required_cols_perf = list(COL_MAP.keys())
                    missing_cols_perf = [col for col in required_cols_perf if col not in temp_perf_df.columns]
                    if missing_cols_perf: 
                        st.error(f"❌ Upload Gagal! Kolom tidak ditemukan:\n {', '.join(missing_cols_perf)}")
                    else:
                        if save_perf_data(temp_perf_df):
                            st.session_state["last_perf_file"] = upl.name
                            st.session_state['perf_data'] = load_perf_data()
                            st.success(t('success_upload')); st.rerun()
                except Exception as e: st.error(f"Error: {e}")
    with c_dl: st.write(""); st.write(""); st.download_button(f"📥 {t('download_tmpl')}", generate_excel_template('perf'), "template_performa.xlsx")
    
    if not st.session_state['perf_data'].empty:
        df = st.session_state['perf_data'].copy(); df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        with st.expander(f"🗑️ {t('manage_data')}"):
            cd1, cd2 = st.columns([3,1]); ddt = cd1.date_input(t('del_date'))
            if cd2.button(t('btn_del')):
                if delete_perf_data_by_date(ddt): 
                    st.session_state['perf_data'] = load_perf_data()
                    st.success(t('deleted')); st.rerun()
        
        df = df.loc[(df['Tanggal'].dt.date >= start_d) & (df['Tanggal'].dt.date <= end_d)]
        
        # ✅ Filter Shift (Sesuai Foto 4)
        shift_opt = st.sidebar.multiselect(
            t("shift_filter"),
            ["Pagi", "Malam", "Full day"],
            default=["Pagi", "Malam", "Full day"]
        )
        
        # ... (hrs, earns logic same)
        hrs = st.sidebar.selectbox(t('filter_hour'), ["Semua", "< 7 Jam", "7 - 9 Jam", ">= 9 Jam"])
        earns = ["Semua"]
        # ... (rest of filtering)

        if "Shift" in df.columns:
            df["Shift"] = df["Shift"].apply(normalize_shift)
            df = df[df["Shift"].isin(shift_opt)]

        df_disp = df.rename(columns={'Merek': 'Level'})
        
        # ✅ Analisis Target Header (Sesuai Foto 4)
        st.divider(); st.subheader(f"📊 {t('target_analysis')}")
        
        # (get_stats function)
        def get_stats(sub, bkts, name):
            res = []; tot = sub['Net Earnings'].sum()
            for k, v in bkts.items():
                f = sub[v]; o = f['Net Earnings'].sum()
                res.append({name: k, "Omset": format_rupiah(o), "Persentase": f"{(o/tot*100) if tot>0 else 0:.1f}%", "Jumlah Driver": f['Nama Driver'].nunique()})
            res.append({name: "Total", "Omset": format_rupiah(tot), "Persentase": "100%", "Jumlah Driver": sub['Nama Driver'].nunique()})
            return pd.DataFrame(res)
        
        ds = df[df['Merek']=='Standard']; dp = df[df['Merek']=='Premium']; c1, c2 = st.columns(2)
        with c1:
            # ✅ Standard Header (Sesuai Foto 5)
            st.markdown(f"### {t('standard')}")
            if not ds.empty:
                st.write(t("income")); st.dataframe(get_stats(ds, {"<300rb": ds['Net Earnings']<300000, "300-400rb": (ds['Net Earnings']>=300000)&(ds['Net Earnings']<400000), ">400rb": ds['Net Earnings']>=400000}, "Klasifikasi"), hide_index=True)
                st.write(t("online_hours")); st.dataframe(get_stats(ds, {"<7 jam": ds['Total Online Hours']<7, "7-9 jam": (ds['Total Online Hours']>=7)&(ds['Total Online Hours']<9), ">9 jam": ds['Total Online Hours']>=9}, "Klasifikasi"), hide_index=True)
        with c2:
            # ✅ Premium Header (Sesuai Foto 5)
            st.markdown(f"### {t('premium')}")
            if not dp.empty:
                st.write(t("income")); st.dataframe(get_stats(dp, {"<500rb": dp['Net Earnings']<500000, "500-600rb": (dp['Net Earnings']>=500000)&(dp['Net Earnings']<600000), ">600rb": dp['Net Earnings']>=600000}, "Klasifikasi"), hide_index=True)
                st.write(t("online_hours")); st.dataframe(get_stats(dp, {"<7 jam": dp['Total Online Hours']<7, "7-9 jam": (dp['Total Online Hours']>=7)&(dp['Total Online Hours']<9), ">9 jam": dp['Total Online Hours']>=9}, "Klasifikasi"), hide_index=True)
        
        # ✅ Summary Driver Header (Sesuai Foto 5)
        st.divider(); st.subheader(f"📋 {t('summary_driver')}")
        if not df_disp.empty:
            if 'Kode PT' not in df_disp.columns: df_disp['Kode PT'] = '-'
            summ = df_disp.groupby(['Nama Driver', 'Kode PT', 'Level']).agg({'Tanggal': 'nunique', 'Net Earnings': 'sum', 'Total Online Hours': 'sum', 'Total Trip Hours': 'sum', 'Total Completed Order': 'sum', 'Total Customer Cancelled': 'sum', 'Total Driver Cancelled': 'sum'}).reset_index()
            # ... (summ logic same)
            summ['Rank'] = summ['Net Earnings'].rank(ascending=False).astype(int); summ['Avg'] = summ['Net Earnings'] / summ['Total Completed Order'].replace(0,1); summ = summ.sort_values('Rank')
            summ['Pendapatan Bersih'] = summ['Net Earnings'].apply(format_rupiah); summ['Earning Rata2'] = summ['Avg'].apply(format_rupiah); summ.reset_index(drop=True, inplace=True); summ.index += 1
            show = summ.rename(columns={'Tanggal': 'Total Hari Kerja', 'Total Online Hours': 'Jam Online', 'Total Trip Hours': 'Jam Trip'})
            st.dataframe(show[['Nama Driver', 'Kode PT', 'Total Hari Kerja', 'Rank', 'Pendapatan Bersih', 'Jam Online', 'Jam Trip', 'Total Completed Order', 'Total Customer Cancelled', 'Total Driver Cancelled', 'Earning Rata2']], use_container_width=True)
        
        # ✅ Detail Harian Header (Sesuai Foto 5)
        st.divider(); st.subheader(f"📝 {t('detail_daily')}")
        df_disp['Tanggal'] = pd.to_datetime(df_disp['Tanggal']).dt.date
        df_show_harian = df_disp.copy()
        
        # (Avg / Order and ID logic)
        df_show_harian["Avg / Order"] = (df_show_harian["Net Earnings"] / df_show_harian["Total Completed Order"].replace(0, 1))
        cols = list(df_show_harian.columns)
        if "Net Earnings" in cols and "Avg / Order" in cols:
            net_idx = cols.index("Net Earnings")
            cols.remove("Avg / Order"); cols.insert(net_idx + 1, "Avg / Order")
            df_show_harian = df_show_harian[cols]
        df_show_harian['id'] = range(1, len(df_show_harian) + 1)

        # (HL function same)
        def hl(row):
            e, h, l, c = row['Net Earnings'], row['Total Online Hours'], row['Level'], ''
            if l == 'Standard':
                if e<300000 and h<7: c='#ffcccc'
                elif 300000<=e<400000 and 7<=h<9: c='#fff4cc'
                elif e>=400000 and h>=9: c='#ccffcc'
            elif l == 'Premium':
                if e<500000 and h<7: c='#ffcccc'
                elif 500000<=e<600000 and 7<=h<9: c='#fff4cc'
                elif e>=600000 and h>=9: c='#ccffcc'
            return [f'background-color: {c}']*len(row) if c else ['']*len(row)

        st.dataframe(df_show_harian.style.apply(hl, axis=1), hide_index=True, use_container_width=True, column_config={"Net Earnings": st.column_config.NumberColumn(format="Rp %.0f"), "Avg / Order": st.column_config.NumberColumn(format="Rp %.0f")})

# ... (rest of the code for data driver and car remains same)
elif selected_page == 'data':
    st.title(t('data_title'))
    # ...
elif selected_page == 'car':
    st.title(t('car_title'))
    # ...
