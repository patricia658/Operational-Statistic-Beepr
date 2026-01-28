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
        supabase.storage.from_(bucket_name).upload(file_name, file_bytes, {"content-type": uploaded_file.type})
        return supabase.storage.from_(bucket_name).get_public_url(file_name)
    except Exception as e:
        st.error(f"Gagal upload foto: {e}")
        return None

# --- FUNGSI EMAIL ---
def send_email_notification(subject, body_text):
    if not EMAIL_SENDER or not EMAIL_PASSWORD:
        st.error("Settingan email belum ada di secrets.toml!")
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
    except Exception as e:
        st.error(f"Gagal kirim email: {e}")
        return False

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

# --- FUNGSI LOAD & SAVE ---
def load_perf_data():
    try:
        response = supabase.table("perf_data").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data).rename(columns=REV_COL_MAP)
            if 'Merek' in df.columns: df['Merek'] = df['Merek'].replace(CAR_RENAME_MAP)
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
        return True
    except: return False

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
    except: return False

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
    },
    'CN': {
        'nav_title': "导航 (Navigasi)", 'menu_dash': "仪表板 (Dashboard)", 'menu_perf': "司机表现 (Driver Performance)", 'menu_data': "司机数据 (Driver Data)", 'menu_car': "车队数据 (Fleet Data)",
        'dash_title': "主仪表板 (Main Dashboard)", 'filter_date': "日期筛选 (Date Filter)", 'start_date': "开始日期 (Start Date)", 'end_date': "结束日期 (End Date)",
        'summary_all': "综合摘要 (所有车队)", 'metrics_title': "各级别详情 (Detail by Level)", 'brand': "级别 (Level)", 'platform': "平台 (Platform)",
        'rev': "总收入 (Total Revenue)", 'orders': "总完成订单 (Total Orders)", 'cust_cancel': "客户取消 (Cust Cancel)", 'drv_cancel': "司机取消 (Driver Cancel)",
        'avg_ord': "平均订单 (Avg Order)", 'avg_day': "平均/天 (Avg/Day)", 'drivers': "司机总数 (Total Drivers)",
        'chart_comp': "收入对比图表", 'chart_plat': "收入对比图表",
        'chart_total': "每日总收入图表 (综合)", 'chart_month': "每月总收入图表",
        'no_data': "暂无数据。请下载模板并上传 Excel。", 'no_data_range': "在此日期范围内没有数据。",
        'perf_title': "司机表现分析 (Driver Performance Analysis)", 'upload_perf': "上传表现数据 (.xlsx)", 'download_tmpl': "下载 Excel 模板",
        'manage_data': "数据管理 (按日期删除)", 'del_date': "选择日期", 'btn_del': "删除数据 (Delete Data)",
        'search_driver': "搜索司机 (姓名)", 'filter_brand': "筛选级别 (Filter Level)", 'filter_plat': "筛选平台 (Filter Platform)",
        'filter_earn': "筛选收入 (Filter Earnings)", 'filter_hour': "筛选在线时长 (Filter Online Hours)",
        'data_title': "司机数据库 (Driver Database)", 'upload_data': "上传司机数据 (.xlsx)", 'stat_total': "总司机", 'stat_active': "活跃 (Active)", 'stat_resign': "离职 (Resigned)",
        'input_manual': "手动输入司机 (Manual Input)", 'del_manual': "手动删除司机 (Manual Delete)", 'btn_add': "添加司机", 'btn_del_drv': "删除司机",
        'car_title': "车队与保险数据库 (Fleet & Insurance)", 'upload_car': "上传车辆数据 (.xlsx)", 
        'stat_car_total': "总车辆", 'stat_car_active': "活跃 (Active)", 'stat_car_maint': "维护中 (Maintenance)", 'stat_car_broken': "损坏 (Broken)", 'stat_car_unused': "闲置 (Unused)",
        'input_car': "手动输入车辆 (Manual Input)", 'del_car': "手动删除车辆 (Manual Delete)", 'btn_add_car': "添加车辆", 'btn_del_car': "删除车辆",
        'car_status_opt': ["Active", "Maintenance", "Rusak", "Tidak Dipakai"], 'driver_status_opt': ["Active", "Resigned"],
        'reminder_check': "检查并发送提醒 (Check & Send Reminder)", 'reminder_desc': "检查即将过期的税务/保险（<30天）并发送电子邮件。"
    }
}

# ==========================================
# 4. SIDEBAR
# ==========================================
start_d, end_d = None, None
with st.sidebar:
    lang_opt = st.radio("Language / 语言", ["ID", "CN"], horizontal=True, key="language")
    def t(key):
        lang = st.session_state.get('language', 'ID')
        return trans[lang].get(key, key)

    st.markdown("---")
    st.header(t('nav_title'))
    nav_options = {'dash': t('menu_dash'), 'perf': t('menu_perf'), 'data': t('menu_data'), 'car': t('menu_car')}
    selected_page = st.radio("Menu", list(nav_options.keys()), format_func=lambda x: nav_options[x])
    
    st.markdown("---")
    st.subheader(f"🗓️ {t('filter_date')}")
    if not st.session_state['perf_data'].empty:
        df_temp = st.session_state['perf_data']
        df_temp['Tanggal'] = pd.to_datetime(df_temp['Tanggal'])
        min_date = df_temp['Tanggal'].min().date()
        max_date = df_temp['Tanggal'].max().date()
    else:
        min_date = pd.to_datetime('today').date()
        max_date = pd.to_datetime('today').date()
    start_d = st.date_input(t('start_date'), min_date)
    end_d = st.date_input(t('end_date'), max_date)

def generate_excel_template(type_data):
    buffer = io.BytesIO()
    if type_data == 'perf': columns = list(COL_MAP.keys())
    elif type_data == 'driver': columns = list(DRIVER_COL_MAP.keys())
    elif type_data == 'car': columns = list(CAR_COL_MAP.keys())
    df = pd.DataFrame([], columns=columns)
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
    return buffer

def format_rupiah(value): return f"Rp {value:,.0f}"

# ==========================================
# 5. DASHBOARD
# ==========================================
if selected_page == 'dash':
    st.title(t('dash_title'))
    if 'perf_data' not in st.session_state or st.session_state['perf_data'].empty:
        st.info(t('no_data'))
    else:
        df = st.session_state['perf_data'].copy()
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        if 'Platform' not in df.columns: df['Platform'] = 'Unknown'
        mask = (df['Tanggal'].dt.date >= start_d) & (df['Tanggal'].dt.date <= end_d)
        df_filt = df.loc[mask]
        
        if df_filt.empty: st.error(t('no_data_range'))
        else:
            tot_omset = df_filt['Net Earnings'].sum()
            tot_order = df_filt['Total Completed Order'].sum()
            tot_cust_canc = df_filt['Total Customer Cancelled'].sum()
            tot_drv_canc = df_filt['Total Driver Cancelled'].sum()
            tot_driver = df_filt['Nama Driver'].nunique()
            avg_earn_per_order = tot_omset / tot_order if tot_order > 0 else 0
            unique_days = df_filt['Tanggal'].nunique()
            avg_earn_per_day = tot_omset / unique_days if unique_days > 0 else 0

            st.subheader(f"📊 {t('summary_all')}")
            c1, c2 = st.columns([2.5, 1])
            with c1:
                r1a, r1b, r1c = st.columns(3)
                r1a.metric(t('rev'), format_rupiah(tot_omset))
                r1b.metric(t('orders'), f"{tot_order}")
                r1c.metric(t('drivers'), f"{tot_driver}")
                r2a, r2b, r2c = st.columns(3)
                r2a.metric(t('avg_day'), format_rupiah(avg_earn_per_day))
                r2b.metric(t('avg_ord'), format_rupiah(avg_earn_per_order))
                r2c.metric("Total Cancelled", f"{tot_cust_canc + tot_drv_canc}")
            with c2:
                pie_data = df_filt.groupby('Merek')['Net Earnings'].sum().reset_index()
                if not pie_data.empty:
                    fig = px.pie(pie_data, values='Net Earnings', names='Merek', title="Standard vs Premium", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=220, showlegend=False)
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            st.subheader(f"🚗 {t('metrics_title')}")
            for level in ["Standard", "Premium"]:
                l_df = df_filt[df_filt['Merek'] == level]
                if not l_df.empty:
                    st.markdown(f"**Level: {level}**")
                    lo = l_df['Net Earnings'].sum()
                    lord = l_df['Total Completed Order'].sum()
                    lavg = lo / lord if lord > 0 else 0
                    lday = l_df['Tanggal'].nunique()
                    lavgd = lo / lday if lday > 0 else 0
                    ca, cb, cc, cd = st.columns(4)
                    ca.metric(t('rev'), format_rupiah(lo))
                    cb.metric(t('orders'), f"{lord}")
                    cc.metric(t('avg_ord'), format_rupiah(lavg))
                    cd.metric(t('avg_day'), format_rupiah(lavgd))
                    ce, cf, cg, ch = st.columns(4)
                    ce.metric(t('cust_cancel'), f"{l_df['Total Customer Cancelled'].sum()}")
                    cf.metric(t('drv_cancel'), f"{l_df['Total Driver Cancelled'].sum()}")
                    cg.metric(t('drivers'), f"{l_df['Nama Driver'].nunique()}")
                    st.divider()

            df_filt['DateStr'] = df_filt['Tanggal'].dt.strftime('%Y-%m-%d')
            daily = df_filt.groupby(['DateStr', 'Merek', 'Platform'])['Net Earnings'].sum().reset_index()
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("Standard (Gojek vs Grab)")
                ds = daily[daily['Merek']=='Standard']
                if not ds.empty:
                    f1 = px.line(ds, x='DateStr', y='Net Earnings', color='Platform', markers=True)
                    f1.update_xaxes(tickformat="%d-%b", dtick="D1")
                    st.plotly_chart(f1, use_container_width=True)
            with g2:
                st.subheader("Premium (Gojek vs Grab)")
                dp = daily[daily['Merek']=='Premium']
                if not dp.empty:
                    f2 = px.line(dp, x='DateStr', y='Net Earnings', color='Platform', markers=True)
                    f2.update_xaxes(tickformat="%d-%b", dtick="D1")
                    st.plotly_chart(f2, use_container_width=True)
            
            st.subheader(t('chart_total'))
            dtot = df_filt.groupby('DateStr')['Net Earnings'].sum().reset_index()
            f3 = px.line(dtot, x='DateStr', y='Net Earnings', markers=True)
            f3.update_xaxes(tickformat="%d-%b", dtick="D1")
            st.plotly_chart(f3, use_container_width=True)

            st.subheader(t('chart_month'))
            df_filt['M'] = df_filt['Tanggal'].dt.to_period('M')
            dm = df_filt.groupby('M')['Net Earnings'].sum().reset_index()
            dm['L'] = dm['M'].dt.strftime("%b'%y")
            f4 = px.line(dm, x='L', y='Net Earnings', markers=True)
            st.plotly_chart(f4, use_container_width=True)

# ==========================================
# 6. PERFORMA DRIVER
# ==========================================
elif selected_page == 'perf':
    st.title(t('perf_title'))
    c_up, c_dl = st.columns([3, 1])
    with c_up:
        upl = st.file_uploader(t('upload_perf'), type=['xlsx'])
        if upl:
            if save_perf_data(pd.read_excel(upl)):
                st.session_state['perf_data'] = load_perf_data()
                st.success("Success!")
                st.rerun()
    with c_dl:
        st.write(""); st.write("")
        st.download_button(f"📥 {t('download_tmpl')}", generate_excel_template('perf'), "template.xlsx")

    if 'perf_data' in st.session_state and not st.session_state['perf_data'].empty:
        df = st.session_state['perf_data'].copy()
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        
        with st.expander(f"🗑️ {t('manage_data')}"):
            cd1, cd2 = st.columns([3,1])
            ddt = cd1.date_input(t('del_date'))
            if cd2.button(t('btn_del')):
                if delete_perf_data_by_date(ddt):
                    st.session_state['perf_data'] = load_perf_data()
                    st.success("Deleted")
                    st.rerun()
        
        mask = (df['Tanggal'].dt.date >= start_d) & (df['Tanggal'].dt.date <= end_d)
        df = df.loc[mask]

        st.sidebar.markdown("---")
        st.sidebar.subheader("🔍 Filter")
        levs = st.sidebar.multiselect(t('filter_brand'), ["Standard", "Premium"], default=["Standard", "Premium"])
        hrs = st.sidebar.selectbox(t('filter_hour'), ["Semua", "< 7 Jam", "7 - 9 Jam", ">= 9 Jam"])
        earns = ["Semua"]
        if "Standard" in levs: earns.extend(["Standard < 300rb", "Standard 300rb-400rb", "Standard >= 400rb"])
        if "Premium" in levs: earns.extend(["Premium < 500rb", "Premium 500rb-600rb", "Premium >= 600rb"])
        sel_earn = st.sidebar.selectbox(t('filter_earn'), list(dict.fromkeys(earns)))

        if levs: df = df[df['Merek'].isin(levs)]
        if hrs == "< 7 Jam": df = df[df['Total Online Hours'] < 7]
        elif hrs == "7 - 9 Jam": df = df[(df['Total Online Hours'] >= 7) & (df['Total Online Hours'] < 9)]
        elif hrs == ">= 9 Jam": df = df[df['Total Online Hours'] >= 9]

        if sel_earn != "Semua":
            if "Standard < 300rb" in sel_earn: df = df[(df['Merek']=='Standard') & (df['Net Earnings'] < 300000)]
            elif "Standard 300rb-400rb" in sel_earn: df = df[(df['Merek']=='Standard') & (df['Net Earnings'] >= 300000) & (df['Net Earnings'] < 400000)]
            elif "Standard >= 400rb" in sel_earn: df = df[(df['Merek']=='Standard') & (df['Net Earnings'] >= 400000)]
            elif "Premium < 500rb" in sel_earn: df = df[(df['Merek']=='Premium') & (df['Net Earnings'] < 500000)]
            elif "Premium 500rb-600rb" in sel_earn: df = df[(df['Merek']=='Premium') & (df['Net Earnings'] >= 500000) & (df['Net Earnings'] < 600000)]
            elif "Premium >= 600rb" in sel_earn: df = df[(df['Merek']=='Premium') & (df['Net Earnings'] >= 600000)]

        df_disp = df.rename(columns={'Merek': 'Level'})
        
        st.divider()
        st.subheader("📊 Analisis Target")
        def bucketer(row):
            e, l = row['Net Earnings'], row['Level']
            if l == 'Standard': return '<300rb' if e<300000 else '300-400rb' if e<400000 else '>400rb'
            if l == 'Premium': return '<500rb' if e<500000 else '500-600rb' if e<600000 else '>600rb'
            return 'Other'
        df_disp['Bucket'] = df_disp.apply(bucketer, axis=1)
        
        def get_stats(sub, bkts, name):
            res = []
            tot = sub['Net Earnings'].sum()
            for k, v in bkts.items():
                f = sub[v]
                o = f['Net Earnings'].sum()
                res.append({name: k, "Omset": format_rupiah(o), "Persentase": f"{(o/tot*100) if tot>0 else 0:.1f}%", "Jumlah Driver": f['Nama Driver'].nunique()})
            res.append({name: "Total", "Omset": format_rupiah(tot), "Persentase": "100%", "Jumlah Driver": sub['Nama Driver'].nunique()})
            return pd.DataFrame(res)

        ds = df[df['Merek']=='Standard']
        dp = df[df['Merek']=='Premium']
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### STANDARD")
            if not ds.empty:
                st.write("Pendapatan")
                st.dataframe(get_stats(ds, {"<300rb": ds['Net Earnings']<300000, "300-400rb": (ds['Net Earnings']>=300000)&(ds['Net Earnings']<400000), ">400rb": ds['Net Earnings']>=400000}, "Klasifikasi"), hide_index=True)
                st.write("Jam Online")
                st.dataframe(get_stats(ds, {"<7 jam": ds['Total Online Hours']<7, "7-9 jam": (ds['Total Online Hours']>=7)&(ds['Total Online Hours']<9), ">9 jam": ds['Total Online Hours']>=9}, "Klasifikasi"), hide_index=True)
        with c2:
            st.markdown("### PREMIUM")
            if not dp.empty:
                st.write("Pendapatan")
                st.dataframe(get_stats(dp, {"<500rb": dp['Net Earnings']<500000, "500-600rb": (dp['Net Earnings']>=500000)&(dp['Net Earnings']<600000), ">600rb": dp['Net Earnings']>=600000}, "Klasifikasi"), hide_index=True)
                st.write("Jam Online")
                st.dataframe(get_stats(dp, {"<7 jam": dp['Total Online Hours']<7, "7-9 jam": (dp['Total Online Hours']>=7)&(dp['Total Online Hours']<9), ">9 jam": dp['Total Online Hours']>=9}, "Klasifikasi"), hide_index=True)

        st.divider()
        st.subheader("📋 Summary Driver")
        if not df_disp.empty:
            if 'Kode PT' not in df_disp.columns: df_disp['Kode PT'] = '-'
            summ = df_disp.groupby(['Nama Driver', 'Kode PT', 'Level']).agg({
                'Tanggal': 'nunique', 'Net Earnings': 'sum', 'Total Online Hours': 'sum', 'Total Trip Hours': 'sum',
                'Total Completed Order': 'sum', 'Total Customer Cancelled': 'sum', 'Total Driver Cancelled': 'sum'
            }).reset_index()
            summ['Rank'] = summ['Net Earnings'].rank(ascending=False).astype(int)
            summ['Avg'] = summ['Net Earnings'] / summ['Total Completed Order'].replace(0,1)
            summ = summ.sort_values('Rank')
            summ['Pendapatan Bersih'] = summ['Net Earnings'].apply(format_rupiah)
            summ['Earning Rata2'] = summ['Avg'].apply(format_rupiah)
            
            # Index No
            summ.reset_index(drop=True, inplace=True)
            summ.index += 1
            
            show = summ.rename(columns={'Tanggal': 'Total Hari Kerja', 'Total Online Hours': 'Jam Online', 'Total Trip Hours': 'Jam Trip'})
            st.dataframe(show[['Nama Driver', 'Kode PT', 'Total Hari Kerja', 'Rank', 'Pendapatan Bersih', 'Jam Online', 'Jam Trip', 'Total Completed Order', 'Total Customer Cancelled', 'Total Driver Cancelled', 'Earning Rata2']], use_container_width=True)

        st.divider()
        st.subheader("📝 Detail Harian")
        df_disp['Tanggal'] = pd.to_datetime(df_disp['Tanggal']).dt.date
        def hl(row):
            e, h, l = row['Net Earnings'], row['Total Online Hours'], row['Level']
            c = ''
            if l == 'Standard':
                if e<300000 and h<7: c='#ffcccc'
                elif 300000<=e<400000 and 7<=h<9: c='#fff4cc'
                elif e>=400000 and h>=9: c='#ccffcc'
                elif e>=600000 and h>=9: c='#99ff99'
            elif l == 'Premium':
                if e<500000 and h<7: c='#ffcccc'
                elif 500000<=e<600000 and 7<=h<9: c='#fff4cc'
                elif e>=600000 and h>=9: c='#ccffcc'
            return [f'background-color: {c}']*len(row) if c else ['']*len(row)
        
        st.dataframe(df_disp.style.apply(hl, axis=1), hide_index=True, use_container_width=True, column_config={"Net Earnings": st.column_config.NumberColumn(format="Rp %.0f")})

# ==========================================
# 7. HALAMAN 3: DATA DRIVER
# ==========================================
elif selected_page == 'data':
    st.title(t('data_title'))
    c_up, c_dl = st.columns([3, 1])
    with c_up:
        upl = st.file_uploader(t('upload_data'), type=['xlsx'])
        if upl:
            if save_driver_data(pd.read_excel(upl)):
                st.session_state['driver_data'] = load_driver_data()
                st.success("Success!")
    with c_dl:
        st.write(""); st.write("")
        st.download_button(f"📥 {t('download_tmpl')}", generate_excel_template('driver'), "template_driver.xlsx")

    df_d = st.session_state['driver_data']
    
    # METRICS
    m1, m2, m3 = st.columns(3)
    total = len(df_d) if not df_d.empty else 0
    active = len(df_d[df_d['Status']=='Active']) if not df_d.empty else 0
    resign = len(df_d[df_d['Status']=='Resigned']) if not df_d.empty else 0
    
    m1.metric(t('stat_total'), total)
    m2.metric(t('stat_active'), active)
    m3.metric(t('stat_resign'), resign)
    
    st.divider()
    
    col_in, col_del = st.columns(2)
    with col_in:
        with st.expander(f"➕ {t('input_manual')}"):
            with st.form("add_driver_form"):
                dn = st.text_input("Nama Driver")
                dc = st.text_input("Kode PT")
                de = st.text_input("Pengalaman App")
                dw = st.date_input("Waktu Masuk Kerja")
                dj = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
                dd = st.text_input("Domisili")
                ds = st.selectbox("Status", t('driver_status_opt'))
                if st.form_submit_button(t('btn_add')):
                    if save_driver_data(pd.DataFrame([{"Nama Driver": dn, "Kode PT": dc, "Pengalaman App": de, "Waktu Masuk Kerja": dw, "Jenis Kelamin": dj, "Domisili": dd, "Status": ds}])):
                        st.session_state['driver_data'] = load_driver_data()
                        st.success("Saved!")
                        st.rerun()
    with col_del:
        with st.expander(f"🗑️ {t('del_manual')}"):
            if not df_d.empty:
                del_name = st.selectbox("Pilih Driver", df_d['Nama Driver'].unique())
                if st.button(t('btn_del_drv')):
                    if delete_driver_by_name(del_name):
                        st.session_state['driver_data'] = load_driver_data()
                        st.success("Deleted!")
                        st.rerun()
    
    st.markdown("### List Driver")
    if not df_d.empty:
        df_show = df_d.reset_index(drop=True)
        df_show.index += 1
        st.dataframe(df_show, use_container_width=True)

# ==========================================
# 8. HALAMAN 4: DATA MOBIL (VALIDASI ERROR)
# ==========================================
elif selected_page == 'car':
    st.title(t('car_title'))
    
    # 1. NOTIFIKASI & EMAIL
    with st.expander(f"📧 {t('reminder_check')}"):
        st.write(t('reminder_desc'))
        if st.button("Check & Send Email"):
            df_check = st.session_state['car_data'].copy()
            if not df_check.empty:
                today = datetime.now().date()
                alert_msg = ""
                for _, row in df_check.iterrows():
                    if pd.notnull(row['Tanggal Habis Asuransi']):
                        exp_date = pd.to_datetime(row['Tanggal Habis Asuransi']).date()
                        days_left = (exp_date - today).days
                        if 0 <= days_left <= 30:
                            alert_msg += f"- Mobil {row['Kode Mobil']} (Asuransi): Expired {days_left} hari lagi ({row['Tanggal Habis Asuransi']})\n"
                    if pd.notnull(row['Tanggal Pajak Tahunan']):
                        tax_date = pd.to_datetime(row['Tanggal Pajak Tahunan']).date()
                        days_left_tax = (tax_date - today).days
                        if 0 <= days_left_tax <= 30:
                            alert_msg += f"- Mobil {row['Kode Mobil']} (Pajak): Expired {days_left_tax} hari lagi ({row['Tanggal Pajak Tahunan']})\n"

                if alert_msg:
                    st.warning("Found expiring items:\n" + alert_msg)
                    if send_email_notification("REMINDER: Armada Expiring Soon", f"Halo,\n\nBerikut daftar armada yang perlu perhatian:\n\n{alert_msg}\n\nTerima kasih."):
                        st.success("Email sent successfully!")
                else: st.info("No items expiring within 30 days.")
            else: st.error("No car data found.")

    c_up, c_dl = st.columns([3, 1])
    with c_up:
        upl = st.file_uploader(t('upload_car'), type=['xlsx'])
        if upl:
            try:
                temp_df = pd.read_excel(upl)
                
                # --- VALIDASI KOLOM (BARU) ---
                required_cols = list(CAR_COL_MAP.keys())
                missing_cols = [col for col in required_cols if col not in temp_df.columns]
                
                if missing_cols:
                    st.error(f"❌ Upload Gagal! Kolom berikut tidak ditemukan di Excel:\n {', '.join(missing_cols)}")
                    st.info("💡 Solusi: Download Template Excel terbaru di sebelah kanan dan gunakan format tersebut.")
                else:
                    if save_car_data(temp_df):
                        st.session_state['car_data'] = load_car_data()
                        st.success("✅ Upload Berhasil! Data mobil telah disimpan.")
                        st.rerun()
            except Exception as e:
                st.error(f"Terjadi kesalahan saat membaca file: {e}")

    with c_dl:
        st.write(""); st.write("")
        st.download_button(f"📥 {t('download_tmpl')}", generate_excel_template('car'), "template_car.xlsx")

    df_c = st.session_state['car_data']
    k1, k2, k3, k4, k5 = st.columns(5)
    tot_c = len(df_c) if not df_c.empty else 0
    act_c = len(df_c[df_c['Status Mobil']=='Active']) if not df_c.empty else 0
    mnt_c = len(df_c[df_c['Status Mobil']=='Maintenance']) if not df_c.empty else 0
    brk_c = len(df_c[df_c['Status Mobil']=='Rusak']) if not df_c.empty else 0
    uns_c = len(df_c[df_c['Status Mobil']=='Tidak Dipakai']) if not df_c.empty else 0

    k1.metric(t('stat_car_total'), tot_c)
    k2.metric(t('stat_car_active'), act_c)
    k3.metric(t('stat_car_maint'), mnt_c)
    k4.metric(t('stat_car_broken'), brk_c)
    k5.metric(t('stat_car_unused'), uns_c)

    st.divider()

    ci, cd = st.columns(2)
    with ci:
        with st.expander(f"➕ {t('input_car')}"):
            with st.form("add_car_form"):
                c1, c2 = st.columns(2)
                with c1:
                    c_buy = st.date_input("Tanggal Pembelian")
                    c_brand = st.text_input("Merek Mobil")
                    c_code = st.text_input("Kode Mobil")
                    c_plat = st.text_input("Plat Nomor")
                    c_type = st.text_input("Type Mobil")
                    c_year = st.text_input("Tahun Produksi")
                    c_col = st.text_input("Warna Mobil")
                    c_chassis = st.text_input("No Rangka")
                    c_engine = st.text_input("No Mesin")
                with c2:
                    c_tax = st.date_input("Tanggal Pajak Tahunan")
                    c_plat_dt = st.date_input("Tanggal Ganti Plat")
                    c_stat = st.selectbox("Status Mobil", t('car_status_opt'))
                    c_ins_n = st.text_input("Nama Asuransi")
                    c_ins_s = st.date_input("Asuransi Mulai")
                    c_ins_e = st.date_input("Asuransi Habis")
                    c_rem = st.text_input("Reminder")
                    c_doc_file = st.file_uploader("Upload Dokumen/Foto (STNK/Polis)", type=['png', 'jpg', 'jpeg', 'pdf'])

                if st.form_submit_button(t('btn_add_car')):
                    doc_url = ""
                    if c_doc_file:
                        with st.spinner("Mengupload foto..."):
                            url = upload_file_to_supabase(c_doc_file)
                            if url: doc_url = url
                    
                    new_car = pd.DataFrame([{
                        "Tanggal Pembelian": c_buy, "Merek Mobil": c_brand, "Kode Mobil": c_code, 
                        "Plat Nomor": c_plat, "Type Mobil": c_type, "Tahun Produksi": c_year, 
                        "Warna Mobil": c_col, "No Rangka": c_chassis, "No Mesin": c_engine, 
                        "Tanggal Pajak Tahunan": c_tax, "Tanggal Ganti Plat": c_plat_dt,
                        "Status Mobil": c_stat, "Nama Asuransi": c_ins_n, "Tanggal Mulai Asuransi": c_ins_s,
                        "Tanggal Habis Asuransi": c_ins_e, "Reminder": c_rem, 
                        "Dokumen": doc_url
                    }])
                    
                    # Validasi Duplikat (Manual Check)
                    if not df_c.empty and c_code in df_c['Kode Mobil'].values:
                        st.warning(f"⚠️ Kode Mobil '{c_code}' sudah ada! Data akan di-update.")
                    
                    if save_car_data(new_car):
                        st.session_state['car_data'] = load_car_data()
                        st.success("Saved!")
                        st.rerun()

    with cd:
        with st.expander(f"🗑️ {t('del_car')}"):
            if not df_c.empty:
                del_code = st.selectbox("Pilih Kode Mobil", df_c['Kode Mobil'].unique())
                if st.button(t('btn_del_car')):
                    if delete_car_by_code(del_code):
                        st.session_state['car_data'] = load_car_data()
                        st.success("Deleted!")
                        st.rerun()
            else: st.info("No Data")

    st.markdown("### List Armada")
    if not df_c.empty:
        df_show_c = df_c.reset_index(drop=True)
        df_show_c.index += 1
        st.dataframe(df_show_c, use_container_width=True, column_config={"Dokumen": st.column_config.LinkColumn("Lihat Dokumen", display_text="Buka File")})
