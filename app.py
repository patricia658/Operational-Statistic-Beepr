import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import io

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="EV Fleet Management System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. KAMUS BAHASA (ID & CN)
# ==========================================
trans = {
    'ID': {
        'nav_title': "Navigasi",
        'menu_dash': "Dashboard",
        'menu_perf': "Performa Driver",
        'menu_data': "Data Driver",
        
        # Dashboard
        'dash_title': "Dashboard Utama",
        'filter_date': "Filter Tanggal",
        'start_date': "Tanggal Mulai",
        'end_date': "Tanggal Akhir",
        'summary_all': "Ringkasan Gabungan (Semua Armada)",
        'metrics_title': "Detail Per Merek Mobil",
        'brand': "Merek",
        'platform': "Platform",
        'rev': "Total Omset",
        'orders': "Total Completed Order",
        'cust_cancel': "Customer Cancelled",
        'drv_cancel': "Driver Cancelled",
        'avg_ord': "Rata-rata Order",
        'drivers': "Jumlah Driver",
        'on_hours': "Jam Online (Total)",
        'avg_on': "Jam Online (Rata-rata)",
        'chart_comp': "Grafik Perbandingan Omset (BYD vs Geely)",
        'chart_plat': "Grafik Perbandingan Omset (Gojek vs Grab)",
        'chart_total': "Grafik Total Omset Harian (Gabungan)",
        'chart_month': "Grafik Total Omset Bulanan",
        'no_data_range': "Tidak ada data pada rentang tanggal ini.",

        # Performa
        'perf_title': "Analisa Performa Driver",
        'upload_perf': "Upload Data Performa (.xlsx)",
        'download_tmpl': "Download Template Excel",
        'manage_data': "Kelola Data (Hapus per Tanggal)",
        'del_date': "Pilih Tanggal",
        'btn_del': "Hapus Data",
        'success_del': "Data berhasil dihapus.",
        'search_driver': "Cari Driver (Nama)",
        'filter_brand': "Filter Merek Mobil",
        'filter_plat': "Filter Platform",
        'filter_earn': "Filter Pendapatan (Harian)",
        'filter_hour': "Filter Jam Online (Harian)",
        'summary': "Ringkasan Hasil Filter",
        'tbl_summary_driver': "Rangkuman Performa Per Driver (Akumulasi)",
        'days_worked': "Hari Kerja",
        'total_earn': "Total Pendapatan",
        'total_trip': "Total Trip Hours",
        'table_detail': "Tabel Detail Transaksi Harian",
        'total_filt_earn': "Total Pendapatan (Filter)",
        
        # Data Driver
        'data_title': "Database Driver",
        'stat_active': "Driver Aktif",
        'stat_resigned': "Driver Resigned",
        'stat_total': "Total Driver Terdaftar",
        'upload_data': "Upload Data Driver (.xlsx)",
        'err_dup': "GAGAL UPLOAD: Terdeteksi Nama Driver duplikat di file Excel!",
        'del_driver_title': "Hapus Data Driver",
        'sel_del_driver': "Pilih Nama Driver untuk Dihapus",
        'btn_del_driver': "Hapus Driver Ini",
        'filter_stat': "Filter Status",
        'edit_instr': "Edit Status (Active -> Resigned) lalu klik Simpan.",
        'btn_save': "Simpan Perubahan",
        'success_save': "Data berhasil diperbarui!",
        
        # Umum
        'all': "Semua",
        'no_data': "Belum ada data. Silakan download template dan upload Excel.",
        'upload_success': "File berhasil diupload!"
    },
    
    # === VERSI MANDARIN (CN) ===
    'CN': {
        'nav_title': "导航 (Navigasi)",
        'menu_dash': "仪表板 (Dashboard)",
        'menu_perf': "司机表现 (Driver Performance)",
        'menu_data': "司机数据 (Driver Data)",
        
        # Dashboard
        'dash_title': "主仪表板 (Main Dashboard)",
        'filter_date': "日期筛选 (Date Filter)",
        'start_date': "开始日期 (Start Date)",
        'end_date': "结束日期 (End Date)",
        'summary_all': "综合摘要 (所有车队)",
        'metrics_title': "各车型详情 (Detail by Brand)",
        'brand': "品牌 (Brand)",
        'platform': "平台 (Platform)",
        'rev': "总收入 (Total Revenue)",
        'orders': "总完成订单 (Total Orders)",
        'cust_cancel': "客户取消 (Cust Cancel)",
        'drv_cancel': "司机取消 (Driver Cancel)",
        'avg_ord': "平均订单 (Avg Order)",
        'drivers': "司机总数 (Total Drivers)",
        'on_hours': "在线时长-总计 (Total Online Hours)",
        'avg_on': "在线时长-平均 (Avg Online Hours)",
        'chart_comp': "收入对比图表 (BYD vs Geely)",
        'chart_plat': "收入对比图表 (Gojek vs Grab)",
        'chart_total': "每日总收入图表 (综合)",
        'chart_month': "每月总收入图表",
        'no_data_range': "在此日期范围内没有数据。",

        # Performa
        'perf_title': "司机表现分析 (Driver Performance Analysis)",
        'upload_perf': "上传表现数据 (.xlsx)",
        'download_tmpl': "下载 Excel 模板",
        'manage_data': "数据管理 (按日期删除)",
        'del_date': "选择日期",
        'btn_del': "删除数据 (Delete Data)",
        'success_del': "数据已成功删除。",
        'search_driver': "搜索司机 (姓名)",
        'filter_brand': "筛选车型 (Filter Brand)",
        'filter_plat': "筛选平台 (Filter Platform)",
        'filter_earn': "筛选收入 (Filter Earnings - Daily)",
        'filter_hour': "筛选在线时长 (Filter Online Hours - Daily)",
        'summary': "筛选结果摘要 (Filter Summary)",
        'tbl_summary_driver': "每位司机表现摘要 (累计)",
        'days_worked': "工作天数 (Days Worked)",
        'total_earn': "总收入 (Total Earnings)",
        'total_trip': "总行程时长 (Total Trip Hours)",
        'table_detail': "每日交易详情表",
        'total_filt_earn': "总收入 (筛选后)",
        
        # Data Driver
        'data_title': "司机数据库 (Driver Database)",
        'stat_active': "活跃司机 (Active)",
        'stat_resigned': "离职司机 (Resigned)",
        'stat_total': "总注册司机 (Total)",
        'upload_data': "上传司机数据 (.xlsx)",
        'err_dup': "上传失败：Excel 文件中检测到重复的司机姓名！",
        'del_driver_title': "删除司机数据 (Delete Driver)",
        'sel_del_driver': "选择要删除的司机姓名",
        'btn_del_driver': "删除此司机",
        'filter_stat': "筛选状态 (Filter Status)",
        'edit_instr': "编辑状态 (Active -> Resigned) 然后点击保存。",
        'btn_save': "保存更改 (Save Changes)",
        'success_save': "数据已成功更新！",
        
        # Umum
        'all': "全部 (All)",
        'no_data': "暂无数据。请下载模板并上传 Excel。",
        'upload_success': "File berhasil diupload!"
    }
}

# ==========================================
# 3. SIDEBAR & FUNGSI TRANSLATE
# ==========================================
with st.sidebar:
    # --- PILIHAN BAHASA (MODEL TOMBOL) ---
    lang_opt = st.radio(
        "Language / 语言", 
        ["ID", "CN"], 
        horizontal=True,
        key="language"
    )
    st.markdown("---")
    
    # Fungsi Helper Translate
    def t(key):
        lang = st.session_state.get('language', 'ID')
        return trans[lang].get(key, key)

    st.header(t('nav_title'))
    
    # Navigation
    nav_options = {
        'dash': t('menu_dash'),
        'perf': t('menu_perf'),
        'data': t('menu_data')
    }
    
    selected_page = st.radio("Menu", list(nav_options.keys()), format_func=lambda x: nav_options[x])

# ==========================================
# 4. FUNGSI UTILITIES
# ==========================================
def generate_excel_template(type_data):
    buffer = io.BytesIO()
    if type_data == 'perf':
        columns = [
            "Tanggal", "Nama Driver", "Kode PT", "Plat No", "Merek", "Platform",
            "Net Earnings", "Total Online Hours", "Total Trip Hours", 
            "Total Completed Order", "Total Customer Cancelled", "Total Driver Cancelled"
        ]
    else:
        columns = [
            "Nama Driver", "Pengalaman App", "Waktu Masuk Kerja", 
            "Jenis Kelamin", "Domisili", "Kode PT", "Status"
        ]
    
    df = pd.DataFrame([], columns=columns)
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
    return buffer

def format_rupiah(value):
    """Helper untuk format Rp manual agar pasti muncul di tabel"""
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
        
        # Handle Platform Column
        if 'Platform' not in df.columns:
            df['Platform'] = 'Unknown'

        # Filter Tanggal
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
            
            # --- A. RINGKASAN GABUNGAN ---
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

            # --- B. DETAIL PER MEREK ---
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
                    
                    c5, c6, c7, c8 = st.columns(4)
                    c5.metric(t('avg_ord'), f"{car_df['Total Completed Order'].mean():.1f}")
                    c6.metric(t('drivers'), f"{car_df['Nama Driver'].nunique()}")
                    c7.metric(t('on_hours'), f"{car_df['Total Online Hours'].sum():,.2f}")
                    c8.metric(t('avg_on'), f"{car_df['Total Online Hours'].mean():.2f}")
                else:
                    st.warning(f"No data for {car}")
                st.markdown("---")

            # --- C. GRAFIK (HANYA TANGGAL) ---
            df_filt['DateOnly'] = df_filt['Tanggal'].dt.strftime('%Y-%m-%d')
            
            # --- ROW 1: COMPARISON CHARTS (SIDE BY SIDE) ---
            # Ini modifikasinya: Kita buat 2 kolom untuk grafik atas biar tidak terlalu lebar
            row1_col1, row1_col2 = st.columns(2)
            
            # 1. Grafik Mobil (BYD vs Geely)
            with row1_col1:
                st.subheader(t('chart_comp'))
                df_comp = df_filt.groupby(['DateOnly', 'Merek'])['Net Earnings'].sum().reset_index()
                fig_comp = px.line(df_comp, x='DateOnly', y='Net Earnings', color='Merek', markers=True)
                fig_comp.update_layout(xaxis_title="Tanggal", yaxis_title="Omset (Rp)")
                fig_comp.update_xaxes(type='category') 
                st.plotly_chart(fig_comp, use_container_width=True)

            # 2. Grafik Platform (Gojek vs Grab)
            with row1_col2:
                st.subheader(t('chart_plat'))
                df_plat = df_filt.groupby(['DateOnly', 'Platform'])['Net Earnings'].sum().reset_index()
                fig_plat = px.line(df_plat, x='DateOnly', y='Net Earnings', color='Platform', markers=True)
                fig_plat.update_layout(xaxis_title="Tanggal", yaxis_title="Omset (Rp)")
                fig_plat.update_xaxes(type='category')
                st.plotly_chart(fig_plat, use_container_width=True)
            
            # --- ROW 2: TOTAL CHARTS (SIDE BY SIDE) ---
            c_chart1, c_chart2 = st.columns(2)
            
            with c_chart1:
                st.subheader(t('chart_total')) 
                df_day = df_filt.groupby(['DateOnly'])['Net Earnings'].sum().reset_index()
                fig_d = px.line(df_day, x='DateOnly', y='Net Earnings', markers=True)
                fig_d.update_layout(xaxis_title="Tanggal", yaxis_title="Total Omset (Rp)")
                fig_d.update_xaxes(type='category')
                st.plotly_chart(fig_d, use_container_width=True)
                
            with c_chart2:
                st.subheader(t('chart_month'))
                df_filt['Month'] = df_filt['Tanggal'].dt.strftime('%Y-%m')
                df_mon = df_filt.groupby(['Month'])['Net Earnings'].sum().reset_index()
                fig_m = px.line(df_mon, x='Month', y='Net Earnings', markers=True)
                fig_m.update_layout(xaxis_title="Bulan", yaxis_title="Total Omset (Rp)")
                fig_m.update_xaxes(type='category')
                st.plotly_chart(fig_m, use_container_width=True)

# ==========================================
# 6. HALAMAN 2: PERFORMA DRIVER
# ==========================================
elif selected_page == 'perf':
    st.title(t('perf_title'))
    
    col_up, col_dl = st.columns([3, 1])
    with col_up:
        uploaded = st.file_uploader(t('upload_perf'), type=['xlsx'])
        if uploaded:
            try:
                st.session_state['perf_data'] = pd.read_excel(uploaded)
                st.success(t('upload_success'))
            except Exception as e:
                st.error(f"Error: {e}")

    with col_dl:
        st.write("")
        st.write("")
        st.download_button(
            label=f"📥 {t('download_tmpl')}",
            data=generate_excel_template('perf'),
            file_name="template_performa.xlsx",
            mime="application/vnd.ms-excel"
        )
        
    if 'perf_data' in st.session_state and not st.session_state['perf_data'].empty:
        df = st.session_state['perf_data']
        if 'Platform' not in df.columns:
            df['Platform'] = 'Unknown'

        # Kelola Data (Hapus)
        with st.expander(t('manage_data')):
            del_dt = st.date_input(t('del_date'))
            if st.button(t('btn_del')):
                df['Tanggal'] = pd.to_datetime(df['Tanggal'])
                st.session_state['perf_data'] = df[df['Tanggal'].dt.date != del_dt]
                st.success(t('success_del'))
                st.rerun()
                
        st.divider()
        
        # --- FILTERING ---
        # 1. Search Driver
        drivers_list = sorted(df['Nama Driver'].astype(str).unique().tolist())
        sel_drivers = st.multiselect(t('search_driver'), drivers_list)
        
        # 2. Filter Merek
        brands_list = sorted(df['Merek'].astype(str).unique().tolist())
        sel_brands = st.multiselect(t('filter_brand'), brands_list)

        # 3. Filter Platform
        plat_list = sorted(df['Platform'].astype(str).unique().tolist())
        sel_plat = st.multiselect(t('filter_plat'), plat_list)
        
        # --- LOGIKA FILTER PENDAPATAN DINAMIS ---
        earn_options = [t('all')]
        
        is_byd = False
        is_geely = False
        
        # Cek apa yang dipilih di filter merek
        if sel_brands:
            if "BYD Atto 1" in sel_brands and len(sel_brands) == 1:
                is_byd = True
            elif "Geely EX5 Max" in sel_brands and len(sel_brands) == 1:
                is_geely = True
        
        # Opsi Filter Sesuai Request
        if is_byd:
            # Range BYD: < 300, 300-400, >= 400
            earn_options.extend(["< Rp 300rb", "Rp 300rb - 400rb", ">= Rp 400rb"])
        elif is_geely:
            # Range Geely: < 500, 500-600, >= 600
            earn_options.extend(["< Rp 500rb", "Rp 500rb - 600rb", ">= Rp 600rb"])
        else:
            # Range Default (Campuran/Umum)
            earn_options.extend(["< Rp 300rb", "Rp 300rb - 600rb", ">= Rp 600rb"])

        # Filter Jam Online
        hour_options = [t('all'), "< 7 Jam", "7 - 9 Jam", ">= 9 Jam"]

        c1, c2 = st.columns(2)
        earn_opt = c1.selectbox(t('filter_earn'), earn_options)
        hour_opt = c2.selectbox(t('filter_hour'), hour_options)
        
        # Logic Filter Implementation
        df_view = df.copy()
        
        # Apply Filter Dasar
        if sel_drivers:
            df_view = df_view[df_view['Nama Driver'].isin(sel_drivers)]
        if sel_brands:
            df_view = df_view[df_view['Merek'].isin(sel_brands)]
        if sel_plat:
            df_view = df_view[df_view['Platform'].isin(sel_plat)]
            
        # Apply Filter Pendapatan (Harian)
        if earn_opt != t('all'):
            if is_byd:
                if earn_opt == "< Rp 300rb":
                    df_view = df_view[df_view['Net Earnings'] < 300000]
                elif earn_opt == "Rp 300rb - 400rb":
                    df_view = df_view[(df_view['Net Earnings'] >= 300000) & (df_view['Net Earnings'] < 400000)]
                elif earn_opt == ">= Rp 400rb":
                    df_view = df_view[df_view['Net Earnings'] >= 400000]
            elif is_geely:
                if earn_opt == "< Rp 500rb":
                    df_view = df_view[df_view['Net Earnings'] < 500000]
                elif earn_opt == "Rp 500rb - 600rb":
                    df_view = df_view[(df_view['Net Earnings'] >= 500000) & (df_view['Net Earnings'] < 600000)]
                elif earn_opt == ">= Rp 600rb":
                    df_view = df_view[df_view['Net Earnings'] >= 600000]
            else:
                # Default Logic
                if earn_opt == "< Rp 300rb":
                    df_view = df_view[df_view['Net Earnings'] <= 300000]
                elif earn_opt == "Rp 300rb - 600rb":
                    df_view = df_view[(df_view['Net Earnings'] > 300000) & (df_view['Net Earnings'] < 600000)]
                elif earn_opt == ">= Rp 600rb":
                    df_view = df_view[df_view['Net Earnings'] >= 600000]

        # Apply Filter Jam Online (Harian)
        if hour_opt == "< 7 Jam":
            df_view = df_view[df_view['Total Online Hours'] < 7]
        elif hour_opt == "7 - 9 Jam":
            df_view = df_view[(df_view['Total Online Hours'] >= 7) & (df_view['Total Online Hours'] < 9)]
        elif hour_opt == ">= 9 Jam":
            df_view = df_view[df_view['Total Online Hours'] >= 9]
            
        st.divider()
        
        # Summary
        st.subheader(t('summary'))
        s1, s2, s3, s4 = st.columns(4)
        s1.metric(t('total_filt_earn'), f"Rp {df_view['Net Earnings'].sum():,.0f}")
        s2.metric(t('orders'), f"{df_view['Total Completed Order'].sum()}")
        s3.metric(t('cust_cancel'), f"{df_view['Total Customer Cancelled'].sum()}")
        s4.metric(t('drv_cancel'), f"{df_view['Total Driver Cancelled'].sum()}")
        
        # --- SUMMARY PER DRIVER TABLE ---
        st.subheader(f"📋 {t('tbl_summary_driver')}")
        
        if not df_view.empty:
            driver_summary = df_view.groupby('Nama Driver').agg({
                'Tanggal': 'nunique',
                'Net Earnings': 'sum',
                'Total Online Hours': 'sum',
                'Total Trip Hours': 'sum',
                'Total Completed Order': 'sum',
                'Total Customer Cancelled': 'sum',
                'Total Driver Cancelled': 'sum'
            }).reset_index()
            
            # --- FORMATTING AGAR RP MUNCUL ---
            # Kita buat kolom baru string khusus display
            driver_summary['Display Earnings'] = driver_summary['Net Earnings'].apply(format_rupiah)
            
            driver_summary = driver_summary.rename(columns={
                'Tanggal': t('days_worked'),
                'Display Earnings': t('total_earn') # Tampilkan kolom string ini
            })
            
            st.dataframe(
                driver_summary[['Nama Driver', t('days_worked'), t('total_earn'), 
                                'Total Online Hours', 'Total Trip Hours', 'Total Completed Order']], 
                use_container_width=True,
                column_config={
                    "Total Online Hours": st.column_config.NumberColumn(format="%.2f h"),
                    "Total Trip Hours": st.column_config.NumberColumn(format="%.2f h")
                }
            )
        else:
            st.warning("No data based on filter.")
        
        st.markdown("---")
        
        # Table Detail Harian
        st.subheader(t('table_detail'))
        
        # Buat copy untuk display agar format Rp string
        df_display_detail = df_view.copy()
        df_display_detail['Net Earnings'] = df_display_detail['Net Earnings'].apply(format_rupiah)
        
        st.dataframe(
            df_display_detail,
            use_container_width=True,
            column_config={
                "Tanggal": st.column_config.DateColumn(format="DD/MM/YYYY"),
            }
        )
        
    else:
        st.info(t('no_data'))

# ==========================================
# 7. HALAMAN 3: DATA DRIVER
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
            except Exception as e:
                st.error(f"Error: {e}")

    with col_dl:
        st.write("")
        st.write("")
        st.download_button(
            label=f"📥 {t('download_tmpl')}",
            data=generate_excel_template('driver'),
            file_name="template_data_driver.xlsx",
            mime="application/vnd.ms-excel"
        )
            
    if 'driver_data' in st.session_state and not st.session_state['driver_data'].empty:
        df_d = st.session_state['driver_data']
        
        if 'Waktu Masuk Kerja' in df_d.columns:
            df_d['Waktu Masuk Kerja'] = pd.to_datetime(df_d['Waktu Masuk Kerja'], errors='coerce').dt.date

        # --- STATISTIK DRIVER (REQ 2) ---
        st.divider()
        total_drv = len(df_d)
        active_drv = len(df_d[df_d['Status'] == 'Active'])
        resigned_drv = len(df_d[df_d['Status'] == 'Resigned'])
        
        k1, k2, k3 = st.columns(3)
        k1.metric(t('stat_total'), total_drv)
        k2.metric(t('stat_active'), active_drv)
        k3.metric(t('stat_resigned'), resigned_drv)
        st.divider()

        with st.expander(t('del_driver_title')):
            driver_list_del = df_d['Nama Driver'].tolist()
            sel_del = st.selectbox(t('sel_del_driver'), driver_list_del)
            if st.button(t('btn_del_driver')):
                st.session_state['driver_data'] = df_d[df_d['Nama Driver'] != sel_del]
                st.success(f"Driver {sel_del} deleted.")
                st.rerun()

        st.divider()

        stat_sel = st.selectbox(t('filter_stat'), [t('all'), "Active", "Resigned"])
        
        if stat_sel != t('all'):
            df_show = df_d[df_d['Status'] == stat_sel]
        else:
            df_show = df_d
            
        st.info(t('edit_instr'))
        
        edited_df = st.data_editor(
            df_show,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Active", "Resigned"],
                    required=True
                ),
                "Waktu Masuk Kerja": st.column_config.DateColumn(format="DD/MM/YYYY")
            }
        )
        
        if st.button(t('btn_save')):
            st.session_state['driver_data'].update(edited_df)
            st.success(t('success_save'))
    else:
        st.info(t('no_data'))