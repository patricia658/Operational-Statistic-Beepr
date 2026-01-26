import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import io
from supabase import create_client

# ==========================================
# 0. SUPABASE CONNECTION & HELPER
# ==========================================
# Pastikan st.secrets sudah diisi di Dashboard Streamlit
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except:
    st.error("Secrets Supabase belum disetting dengan benar.")
    st.stop()

# --- MAPPING NAMA KOLOM (Excel <-> Database) ---
# Kiri: Nama di Excel/Dashboard (Kapital)
# Kanan: Nama di Supabase (Huruf Kecil, tanpa spasi)
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

# Fungsi Membalikkan Mapping (Database -> Dashboard)
REV_COL_MAP = {v: k for k, v in COL_MAP.items()}

def load_perf_data():
    """Tarik data dari Supabase dan ubah nama kolomnya jadi format Dashboard"""
    try:
        response = supabase.table("perf_data").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            # Rename balik ke format Kapital agar Dashboard terbaca
            df = df.rename(columns=REV_COL_MAP)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Gagal tarik data: {e}")
        return pd.DataFrame()

def save_perf_data(df):
    """Simpan data Excel ke Supabase"""
    try:
        # 1. Rename kolom Kapital -> Huruf Kecil
        df_db = df.rename(columns=COL_MAP)
        
        # 2. Ambil hanya kolom yang dikenali database
        valid_cols = list(COL_MAP.values())
        df_db = df_db[[c for c in valid_cols if c in df_db.columns]]
        
        # 3. Format Tanggal jadi string (YYYY-MM-DD)
        df_db['tanggal'] = pd.to_datetime(df_db['tanggal']).dt.strftime('%Y-%m-%d')
        
        # 4. Convert ke Dictionary dan Upload
        data_records = df_db.to_dict(orient='records')
        supabase.table("perf_data").insert(data_records).execute()
        return True
    except Exception as e:
        st.error(f"Gagal simpan data: {e}")
        return False

def delete_perf_data_by_date(date_obj):
    """Hapus data di Supabase berdasarkan tanggal"""
    try:
        date_str = date_obj.strftime('%Y-%m-%d')
        supabase.table("perf_data").delete().eq("tanggal", date_str).execute()
        return True
    except Exception as e:
        st.error(f"Gagal hapus data: {e}")
        return False

# ==========================================
# 1. SISTEM LOGIN (KEAMANAN)
# ==========================================
def check_password():
    """Mengembalikan True jika user memasukkan password yang benar."""
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
        st.error("😕 Password salah. Silakan coba lagi.")
        return False
    else:
        return True

if not check_password():
    st.stop()

# AUTO LOAD DATA SETELAH LOGIN
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
# 3. KAMUS BAHASA (ID & CN)
# ==========================================
trans = {
    'ID': {
        'nav_title': "Navigasi", 'menu_dash': "Dashboard", 'menu_perf': "Performa Driver", 'menu_data': "Data Driver",
        'dash_title': "Dashboard Utama", 'filter_date': "Filter Tanggal", 'start_date': "Tanggal Mulai", 'end_date': "Tanggal Akhir",
        'summary_all': "Ringkasan Gabungan (Semua Armada)", 'metrics_title': "Detail Per Merek Mobil", 'brand': "Merek", 'platform': "Platform",
        'rev': "Total Omset", 'orders': "Total Completed Order", 'cust_cancel': "Customer Cancelled", 'drv_cancel': "Driver Cancelled",
        'avg_ord': "Rata-rata Order", 'drivers': "Jumlah Driver", 'on_hours': "Jam Online (Total)", 'avg_on': "Jam Online (Rata-rata)",
        'chart_comp': "Grafik Perbandingan Omset (BYD vs Geely)", 'chart_plat': "Grafik Perbandingan Omset (Gojek vs Grab)",
        'chart_total': "Grafik Total Omset Harian (Gabungan)", 'chart_month': "Grafik Total Omset Bulanan", 'no_data_range': "Tidak ada data pada rentang tanggal ini.",
        'perf_title': "Analisa Performa Driver", 'upload_perf': "Upload Data Performa (.xlsx)", 'download_tmpl': "Download Template Excel",
        'manage_data': "Kelola Data (Hapus per Tanggal)", 'del_date': "Pilih Tanggal", 'btn_del': "Hapus Data Permanen", 'success_del': "Data berhasil dihapus dari Database.",
        'search_driver': "Cari Driver (Nama)", 'filter_brand': "Filter Merek Mobil", 'filter_plat': "Filter Platform", 'filter_earn': "Filter Pendapatan (Harian)",
        'filter_hour': "Filter Jam Online (Harian)", 'summary': "Ringkasan Hasil Filter", 'tbl_summary_driver': "Rangkuman Performa Per Driver (Akumulasi)",
        'days_worked': "Hari Kerja", 'total_earn': "Total Pendapatan", 'total_trip': "Total Trip Hours", 'table_detail': "Tabel Detail Transaksi Harian",
        'total_filt_earn': "Total Pendapatan (Filter)", 'data_title': "Database Driver", 'stat_active': "Driver Aktif", 'stat_resigned': "Driver Resigned",
        'stat_total': "Total Driver Terdaftar", 'upload_data': "Upload Data Driver (.xlsx)", 'err_dup': "GAGAL UPLOAD: Nama Driver duplikat!",
        'del_driver_title': "Hapus Data Driver", 'sel_del_driver': "Pilih Nama Driver", 'btn_del_driver': "Hapus Driver Ini",
        'filter_stat': "Filter Status", 'edit_instr': "Edit Status lalu Simpan.", 'btn_save': "Simpan Perubahan", 'success_save': "Data berhasil diperbarui!",
        'all': "Semua", 'no_data': "Belum ada data. Silakan upload Excel.", 'upload_success': "File berhasil disimpan ke Database!"
    },
    'CN': {
        'nav_title': "导航 (Navigasi)", 'menu_dash': "仪表板 (Dashboard)", 'menu_perf': "司机表现 (Driver Performance)", 'menu_data': "司机数据 (Driver Data)",
        'dash_title': "主仪表板 (Main Dashboard)", 'filter_date': "日期筛选 (Date Filter)", 'start_date': "开始日期 (Start Date)", 'end_date': "结束日期 (End Date)",
        'summary_all': "综合摘要 (所有车队)", 'metrics_title': "各车型详情 (Detail by Brand)", 'brand': "品牌 (Brand)", 'platform': "平台 (Platform)",
        'rev': "总收入 (Total Revenue)", 'orders': "总完成订单 (Total Orders)", 'cust_cancel': "客户取消 (Cust Cancel)", 'drv_cancel': "司机取消 (Driver Cancel)",
        'avg_ord': "平均订单 (Avg Order)", 'drivers': "司机总数 (Total Drivers)", 'on_hours': "在线时长-总计 (Total Online Hours)", 'avg_on': "在线时长-平均 (Avg Online Hours)",
        'chart_comp': "收入对比图表 (BYD vs Geely)", 'chart_plat': "收入对比图表 (Gojek vs Grab)", 'chart_total': "每日总收入图表 (综合)", 'chart_month': "每月总收入图表",
        'no_data_range': "在此日期范围内没有数据。", 'perf_title': "司机表现分析 (Driver Performance Analysis)", 'upload_perf': "上传表现数据 (.xlsx)",
        'download_tmpl': "下载 Excel 模板", 'manage_data': "数据管理 (按日期删除)", 'del_date': "选择日期", 'btn_del': "删除数据 (Delete Data)",
        'success_del': "数据已成功删除。", 'search_driver': "搜索司机 (姓名)", 'filter_brand': "筛选车型 (Filter Brand)", 'filter_plat': "筛选平台 (Filter Platform)",
        'filter_earn': "筛选收入 (Filter Earnings - Daily)", 'filter_hour': "筛选在线时长 (Filter Online Hours - Daily)", 'summary': "筛选结果摘要 (Filter Summary)",
        'tbl_summary_driver': "每位司机表现摘要 (累计)", 'days_worked': "工作天数 (Days Worked)", 'total_earn': "总收入 (Total Earnings)",
        'total_trip': "总行程时长 (Total Trip Hours)", 'table_detail': "每日交易详情表", 'total_filt_earn': "总收入 (筛选后)", 'data_title': "司机数据库 (Driver Database)",
        'stat_active': "活跃司机 (Active)", 'stat_resigned': "离职司机 (Resigned)", 'stat_total': "总注册司机 (Total)", 'upload_data': "上传司机数据 (.xlsx)",
        'err_dup': "上传失败：Excel 文件中检测到重复的司机姓名！", 'del_driver_title': "删除司机数据 (Delete Driver)", 'sel_del_driver': "选择要删除的司机姓名",
        'btn_del_driver': "删除此司机", 'filter_stat': "筛选状态 (Filter Status)", 'edit_instr': "编辑状态 (Active -> Resigned) 然后点击保存。",
        'btn_save': "保存更改 (Save Changes)", 'success_save': "数据已成功更新！", 'all': "全部 (All)", 'no_data': "暂无数据。请下载模板并上传 Excel。",
        'upload_success': "文件上传成功！"
    }
}

# ==========================================
# 4. SIDEBAR & FUNGSI UTILITIES
# ==========================================
with st.sidebar:
    lang_opt = st.radio("Language / 语言", ["ID", "CN"], horizontal=True, key="language")
    st.markdown("---")
    
    def t(key):
        lang = st.session_state.get('language', 'ID')
        return trans[lang].get(key, key)

    st.header(t('nav_title'))
    nav_options = {'dash': t('menu_dash'), 'perf': t('menu_perf'), 'data': t('menu_data')}
    selected_page = st.radio("Menu", list(nav_options.keys()), format_func=lambda x: nav_options[x])

def generate_excel_template(type_data):
    buffer = io.BytesIO()
    if type_data == 'perf':
        columns = list(COL_MAP.keys()) # Pakai mapping agar konsisten
    else:
        columns = ["Nama Driver", "Pengalaman App", "Waktu Masuk Kerja", "Jenis Kelamin", "Domisili", "Kode PT", "Status"]
    
    df = pd.DataFrame([], columns=columns)
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
    return buffer

def format_rupiah(value):
    return f"Rp {value:,.0f}"

# ==========================================
# 5. HALAMAN 1: DASHBOARD
# ==========================================
if selected_page == 'dash':
    st.title(t('dash_title'))
    
    if 'perf_data' not in st.session_state or st.session_state['perf_data'].empty:
        st.info(t('no_data'))
    else:
        df = st.session_state['perf_data'].copy()
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        
        if 'Platform' not in df.columns:
            df['Platform'] = 'Unknown'

        with st.expander(t('filter_date'), expanded=True):
            c1, c2 = st.columns(2)
            min_d = df['Tanggal'].min().date()
            max_d = df['Tanggal'].max().date()
            start_d = c1.date_input(t('start_date'), min_d)
            end_d = c2.date_input(t('end_date'), max_d)
        
        mask = (df['Tanggal'].dt.date >= start_d) & (df['Tanggal'].dt.date <= end_d)
        df_filt = df.loc[mask]
        
        if df_filt.empty:
            st.error(t('no_data_range'))
        else:
            st.divider()
            st.subheader(f"📊 {t('summary_all')}")
            
            tot_omset = df_filt['Net Earnings'].sum()
            tot_order = df_filt['Total Completed Order'].sum()
            tot_cust_canc = df_filt['Total Customer Cancelled'].sum()
            tot_drv_canc = df_filt['Total Driver Cancelled'].sum()
            avg_order = df_filt['Total Completed Order'].mean()
            tot_driver = df_filt['Nama Driver'].nunique()
            tot_hours = df_filt['Total Online Hours'].sum()
            avg_hours = df_filt['Total Online Hours'].mean()

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(t('rev'), f"Rp {tot_omset:,.0f}")
            m2.metric(t('orders'), f"{tot_order}")
            m3.metric(t('cust_cancel'), f"{tot_cust_canc}")
            m4.metric(t('drv_cancel'), f"{tot_drv_canc}")
            
            m5, m6, m7, m8 = st.columns(4)
            m5.metric(t('avg_ord'), f"{avg_order:.1f}")
            m6.metric(t('drivers'), f"{tot_driver}")
            m7.metric(t('on_hours'), f"{tot_hours:,.2f}")
            m8.metric(t('avg_on'), f"{avg_hours:.2f}")
            
            st.markdown("---")
            st.subheader(f"🚗 {t('metrics_title')}")
            target_cars = ["BYD Atto 1", "Geely EX5 Max"]
            
            for car in target_cars:
                st.markdown(f"**{t('brand')}: {car}**")
                car_df = df_filt[df_filt['Merek'] == car]
                if not car_df.empty:
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric(t('rev'), f"Rp {car_df['Net Earnings'].sum():,.0f}")
                    c2.metric(t('orders'), f"{car_df['Total Completed Order'].sum()}")
                    c3.metric(t('cust_cancel'), f"{car_df['Total Customer Cancelled'].sum()}")
                    c4.metric(t('drv_cancel'), f"{car_df['Total Driver Cancelled'].sum()}")
                else:
                    st.warning(f"No data for {car}")
                st.markdown("---")

            df_filt['DateOnly'] = df_filt['Tanggal'].dt.strftime('%Y-%m-%d')
            
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                st.subheader(t('chart_comp'))
                df_comp = df_filt.groupby(['DateOnly', 'Merek'])['Net Earnings'].sum().reset_index()
                fig_comp = px.line(df_comp, x='DateOnly', y='Net Earnings', color='Merek', markers=True)
                st.plotly_chart(fig_comp, use_container_width=True)

            with row1_col2:
                st.subheader(t('chart_plat'))
                df_plat = df_filt.groupby(['DateOnly', 'Platform'])['Net Earnings'].sum().reset_index()
                fig_plat = px.line(df_plat, x='DateOnly', y='Net Earnings', color='Platform', markers=True)
                st.plotly_chart(fig_plat, use_container_width=True)
            
            c_chart1, c_chart2 = st.columns(2)
            with c_chart1:
                st.subheader(t('chart_total')) 
                df_day = df_filt.groupby(['DateOnly'])['Net Earnings'].sum().reset_index()
                fig_d = px.line(df_day, x='DateOnly', y='Net Earnings', markers=True)
                st.plotly_chart(fig_d, use_container_width=True)
                
            with c_chart2:
                st.subheader(t('chart_month'))
                df_filt['Month'] = df_filt['Tanggal'].dt.strftime('%Y-%m')
                df_mon = df_filt.groupby(['Month'])['Net Earnings'].sum().reset_index()
                fig_m = px.line(df_mon, x='Month', y='Net Earnings', markers=True)
                st.plotly_chart(fig_m, use_container_width=True)

# ==========================================
# 6. HALAMAN 2: PERFORMA DRIVER (CONNECTED TO DB)
# ==========================================
elif selected_page == 'perf':
    st.title(t('perf_title'))
    
    col_up, col_dl = st.columns([3, 1])
    with col_up:
        uploaded = st.file_uploader(t('upload_perf'), type=['xlsx'])
        if uploaded:
            try:
                df_new = pd.read_excel(uploaded)
                # --- PUSH KE SUPABASE ---
                with st.spinner("Menyimpan ke Database..."):
                    success = save_perf_data(df_new)
                    if success:
                        st.session_state['perf_data'] = load_perf_data() # Reload
                        st.success(t('upload_success'))
            except Exception as e:
                st.error(f"Error: {e}")

    with col_dl:
        st.write(""); st.write("")
        st.download_button(label=f"📥 {t('download_tmpl')}", data=generate_excel_template('perf'), file_name="template_performa.xlsx", mime="application/vnd.ms-excel")
        
    if 'perf_data' in st.session_state and not st.session_state['perf_data'].empty:
        df = st.session_state['perf_data']
        if 'Platform' not in df.columns:
            df['Platform'] = 'Unknown'

        with st.expander(t('manage_data')):
            del_dt = st.date_input(t('del_date'))
            if st.button(t('btn_del')):
                # --- DELETE DI SUPABASE ---
                with st.spinner("Menghapus data di Database..."):
                    if delete_perf_data_by_date(del_dt):
                        st.session_state['perf_data'] = load_perf_data() # Reload
                        st.success(t('success_del'))
                        st.rerun()
                
        st.divider()
        drivers_list = sorted(df['Nama Driver'].astype(str).unique().tolist())
        sel_drivers = st.multiselect(t('search_driver'), drivers_list)
        brands_list = sorted(df['Merek'].astype(str).unique().tolist())
        sel_brands = st.multiselect(t('filter_brand'), brands_list)
        plat_list = sorted(df['Platform'].astype(str).unique().tolist())
        sel_plat = st.multiselect(t('filter_plat'), plat_list)
        
        earn_options = [t('all')]
        # Logika filter pendapatan (disederhanakan sedikit untuk kerapian)
        earn_options.extend(["< Rp 300rb", "Rp 300rb - 600rb", ">= Rp 600rb"])
        
        hour_options = [t('all'), "< 7 Jam", "7 - 9 Jam", ">= 9 Jam"]
        c1, c2 = st.columns(2)
        earn_opt = c1.selectbox(t('filter_earn'), earn_options)
        hour_opt = c2.selectbox(t('filter_hour'), hour_options)
        
        df_view = df.copy()
        if sel_drivers: df_view = df_view[df_view['Nama Driver'].isin(sel_drivers)]
        if sel_brands: df_view = df_view[df_view['Merek'].isin(sel_brands)]
        if sel_plat: df_view = df_view[df_view['Platform'].isin(sel_plat)]
            
        # Filter Pendapatan & Jam (Logika tetap sama)
        if earn_opt == "< Rp 300rb": df_view = df_view[df_view['Net Earnings'] < 300000]
        elif earn_opt == "Rp 300rb - 600rb": df_view = df_view[(df_view['Net Earnings'] >= 300000) & (df_view['Net Earnings'] < 600000)]
        elif earn_opt == ">= Rp 600rb": df_view = df_view[df_view['Net Earnings'] >= 600000]

        if hour_opt == "< 7 Jam": df_view = df_view[df_view['Total Online Hours'] < 7]
        elif hour_opt == "7 - 9 Jam": df_view = df_view[(df_view['Total Online Hours'] >= 7) & (df_view['Total Online Hours'] < 9)]
        elif hour_opt == ">= 9 Jam": df_view = df_view[df_view['Total Online Hours'] >= 9]
            
        st.divider()
        st.subheader(t('summary'))
        s1, s2, s3, s4 = st.columns(4)
        s1.metric(t('total_filt_earn'), f"Rp {df_view['Net Earnings'].sum():,.0f}")
        s2.metric(t('orders'), f"{df_view['Total Completed Order'].sum()}")
        s3.metric(t('cust_cancel'), f"{df_view['Total Customer Cancelled'].sum()}")
        s4.metric(t('drv_cancel'), f"{df_view['Total Driver Cancelled'].sum()}")
        
        st.subheader(f"📋 {t('tbl_summary_driver')}")
        if not df_view.empty:
            driver_summary = df_view.groupby('Nama Driver').agg({'Tanggal': 'nunique', 'Net Earnings': 'sum', 'Total Online Hours': 'sum', 'Total Trip Hours': 'sum', 'Total Completed Order': 'sum'}).reset_index()
            driver_summary['Display Earnings'] = driver_summary['Net Earnings'].apply(format_rupiah)
            driver_summary = driver_summary.rename(columns={'Tanggal': t('days_worked'), 'Display Earnings': t('total_earn')})
            st.dataframe(driver_summary, use_container_width=True)
        
        st.subheader(t('table_detail'))
        st.dataframe(df_view, use_container_width=True)
    else:
        st.info(t('no_data'))

# ==========================================
# 7. HALAMAN 3: DATA DRIVER (LOCAL ONLY)
# ==========================================
elif selected_page == 'data':
    st.title(t('data_title'))
    col_up, col_dl = st.columns([3, 1])
    with col_up:
        up_driver = st.file_uploader(t('upload_data'), type=['xlsx'])
        if up_driver:
            try:
                temp_df = pd.read_excel(up_driver)
                if temp_df['Nama Driver'].duplicated().any():
                    st.error(t('err_dup'))
                else:
                    st.session_state['driver_data'] = temp_df
                    st.success(t('upload_success'))
            except Exception as e: st.error(f"Error: {e}")

    with col_dl:
        st.write(""); st.write("")
        st.download_button(label=f"📥 {t('download_tmpl')}", data=generate_excel_template('driver'), file_name="template_data_driver.xlsx", mime="application/vnd.ms-excel")
            
    if 'driver_data' in st.session_state and not st.session_state['driver_data'].empty:
        df_d = st.session_state['driver_data']
        if 'Waktu Masuk Kerja' in df_d.columns:
            df_d['Waktu Masuk Kerja'] = pd.to_datetime(df_d['Waktu Masuk Kerja'], errors='coerce').dt.date

        st.divider()
        k1, k2, k3 = st.columns(3)
        k1.metric(t('stat_total'), len(df_d))
        k2.metric(t('stat_active'), len(df_d[df_d['Status'] == 'Active']))
        k3.metric(t('stat_resigned'), len(df_d[df_d['Status'] == 'Resigned']))
        
        with st.expander(t('del_driver_title')):
            sel_del = st.selectbox(t('sel_del_driver'), df_d['Nama Driver'].tolist())
            if st.button(t('btn_del_driver')):
                st.session_state['driver_data'] = df_d[df_d['Nama Driver'] != sel_del]
                st.rerun()

        st.info(t('edit_instr'))
        st.data_editor(df_d, num_rows="dynamic", use_container_width=True)
    else:
        st.info(t('no_data'))
