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

# --- MAPPING NAMA KOLOM ---
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

# --- MAPPING REBRANDING ---
CAR_RENAME_MAP = {
    "BYD Atto 1": "Standard",
    "Geely EX5 Max": "Premium"
}

def load_perf_data():
    try:
        response = supabase.table("perf_data").select("*").execute()
        if response.data:
            df = pd.DataFrame(response.data)
            df = df.rename(columns=REV_COL_MAP)
            if 'Merek' in df.columns:
                df['Merek'] = df['Merek'].replace(CAR_RENAME_MAP)
            return df
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Gagal tarik data: {e}")
        return pd.DataFrame()

def save_perf_data(df):
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
st.set_page_config(page_title="EV Fleet Management System", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 3. KAMUS BAHASA
# ==========================================
trans = {
    'ID': {
        'nav_title': "Navigasi", 'menu_dash': "Dashboard", 'menu_perf': "Performa Driver", 'menu_data': "Data Driver",
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
        'data_title': "Data Driver", 'upload_data': "Upload Data Driver (.xlsx)", 'stat_total': "Total Driver", 'stat_active': "Active"
    },
    'CN': {
        'nav_title': "导航 (Navigasi)", 'menu_dash': "仪表板 (Dashboard)", 'menu_perf': "司机表现 (Driver Performance)", 'menu_data': "司机数据 (Driver Data)",
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
        'data_title': "司机数据 (Driver Data)", 'upload_data': "上传司机数据 (.xlsx)", 'stat_total': "总司机", 'stat_active': "活跃 (Active)"
    }
}

# ==========================================
# 4. SIDEBAR & NAVIGASI
# ==========================================
start_d, end_d = None, None

with st.sidebar:
    lang_opt = st.radio("Language / 语言", ["ID", "CN"], horizontal=True, key="language")
    
    def t(key):
        lang = st.session_state.get('language', 'ID')
        return trans[lang].get(key, key)

    st.markdown("---")
    st.header(t('nav_title'))
    nav_options = {'dash': t('menu_dash'), 'perf': t('menu_perf'), 'data': t('menu_data')}
    selected_page = st.radio("Menu", list(nav_options.keys()), format_func=lambda x: nav_options[x])
    
    # --- FILTER TANGGAL (GLOBAL) ---
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
# 5. HALAMAN 1: DASHBOARD (AMAN - TIDAK DIUBAH)
# ==========================================
if selected_page == 'dash':
    st.title(t('dash_title'))
    
    if 'perf_data' not in st.session_state or st.session_state['perf_data'].empty:
        st.info(t('no_data'))
    else:
        df = st.session_state['perf_data'].copy()
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        
        if 'Platform' not in df.columns: df['Platform'] = 'Unknown'

        # Filter Data
        mask = (df['Tanggal'].dt.date >= start_d) & (df['Tanggal'].dt.date <= end_d)
        df_filt = df.loc[mask]
        
        if df_filt.empty:
            st.error(t('no_data_range'))
        else:
            # --- CALCULATE METRICS ---
            tot_omset = df_filt['Net Earnings'].sum()
            tot_order = df_filt['Total Completed Order'].sum()
            tot_cust_canc = df_filt['Total Customer Cancelled'].sum()
            tot_drv_canc = df_filt['Total Driver Cancelled'].sum()
            tot_driver = df_filt['Nama Driver'].nunique()
            
            avg_earn_per_order = tot_omset / tot_order if tot_order > 0 else 0
            unique_days = df_filt['Tanggal'].nunique()
            avg_earn_per_day = tot_omset / unique_days if unique_days > 0 else 0

            # --- RINGKASAN GABUNGAN ---
            st.subheader(f"📊 {t('summary_all')}")
            col_main_metrics, col_main_pie = st.columns([2.5, 1])
            with col_main_metrics:
                r1c1, r1c2, r1c3 = st.columns(3)
                r1c1.metric(t('rev'), format_rupiah(tot_omset))
                r1c2.metric(t('orders'), f"{tot_order}")
                r1c3.metric(t('drivers'), f"{tot_driver}")
                
                r2c1, r2c2, r2c3 = st.columns(3)
                r2c1.metric(t('avg_day'), format_rupiah(avg_earn_per_day))
                r2c2.metric(t('avg_ord'), format_rupiah(avg_earn_per_order))
                r2c3.metric("Total Cancelled", f"{tot_cust_canc + tot_drv_canc}")

            with col_main_pie:
                pie_data_level = df_filt.groupby('Merek')['Net Earnings'].sum().reset_index()
                if not pie_data_level.empty:
                    fig_pie_main = px.pie(pie_data_level, values='Net Earnings', names='Merek', 
                                          title="Standard vs Premium", hole=0.4,
                                          color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_pie_main.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=220, showlegend=False)
                    fig_pie_main.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig_pie_main, use_container_width=True)

            st.markdown("---")

            # --- DETAIL PER LEVEL ---
            st.subheader(f"🚗 {t('metrics_title')}")
            target_levels = ["Standard", "Premium"]
            
            for level in target_levels:
                level_df = df_filt[df_filt['Merek'] == level]
                if not level_df.empty:
                    st.markdown(f"**Level: {level}**")
                    l_omset = level_df['Net Earnings'].sum()
                    l_order = level_df['Total Completed Order'].sum()
                    l_cust = level_df['Total Customer Cancelled'].sum()
                    l_drv = level_df['Total Driver Cancelled'].sum()
                    l_drivers = level_df['Nama Driver'].nunique()
                    l_avg_ord = l_omset / l_order if l_order > 0 else 0
                    l_days = level_df['Tanggal'].nunique()
                    l_avg_day = l_omset / l_days if l_days > 0 else 0
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric(t('rev'), format_rupiah(l_omset))
                    c2.metric(t('orders'), f"{l_order}")
                    c3.metric(t('avg_ord'), format_rupiah(l_avg_ord))
                    c4.metric(t('avg_day'), format_rupiah(l_avg_day))
                    
                    c5, c6, c7, c8 = st.columns(4)
                    c5.metric(t('cust_cancel'), f"{l_cust}")
                    c6.metric(t('drv_cancel'), f"{l_drv}")
                    c7.metric(t('drivers'), f"{l_drivers}")
                    c8.write("") 
                    st.divider()

            # --- GRAFIK ---
            df_filt['DateStr'] = df_filt['Tanggal'].dt.strftime('%Y-%m-%d')
            df_daily_agg = df_filt.groupby(['DateStr', 'Merek', 'Platform'])['Net Earnings'].sum().reset_index()

            col_g1, col_g2 = st.columns(2)
            with col_g1:
                st.subheader(f"Standard (Gojek vs Grab)")
                data_std = df_daily_agg[df_daily_agg['Merek'] == 'Standard']
                if not data_std.empty:
                    fig_std = px.line(data_std, x='DateStr', y='Net Earnings', color='Platform', markers=True)
                    fig_std.update_xaxes(tickformat="%d-%b", dtick="D1")
                    fig_std.update_layout(xaxis_title="Date", yaxis_title="Omset")
                    st.plotly_chart(fig_std, use_container_width=True)
                else: st.info("No Data.")

            with col_g2:
                st.subheader(f"Premium (Gojek vs Grab)")
                data_prm = df_daily_agg[df_daily_agg['Merek'] == 'Premium']
                if not data_prm.empty:
                    fig_prm = px.line(data_prm, x='DateStr', y='Net Earnings', color='Platform', markers=True)
                    fig_prm.update_xaxes(tickformat="%d-%b", dtick="D1")
                    fig_prm.update_layout(xaxis_title="Date", yaxis_title="Omset")
                    st.plotly_chart(fig_prm, use_container_width=True)
                else: st.info("No Data.")
            
            st.subheader(t('chart_total'))
            df_total_daily = df_filt.groupby('DateStr')['Net Earnings'].sum().reset_index()
            fig_d = px.line(df_total_daily, x='DateStr', y='Net Earnings', markers=True)
            fig_d.update_xaxes(tickformat="%d-%b", dtick="D1")
            fig_d.update_layout(xaxis_title="Date", yaxis_title="Total Omset")
            st.plotly_chart(fig_d, use_container_width=True)
            
            st.subheader(t('chart_month'))
            df_filt['MonthObj'] = df_filt['Tanggal'].dt.to_period('M')
            df_mon = df_filt.groupby('MonthObj')['Net Earnings'].sum().reset_index()
            df_mon['MonthLabel'] = df_mon['MonthObj'].dt.strftime("%b'%y")
            fig_m = px.line(df_mon, x='MonthLabel', y='Net Earnings', markers=True)
            fig_m.update_layout(xaxis_title="Month", yaxis_title="Total Omset")
            st.plotly_chart(fig_m, use_container_width=True)

# ==========================================
# 6. HALAMAN 2: PERFORMA DRIVER (UPDATE TABEL BUCKETS)
# ==========================================
elif selected_page == 'perf':
    st.title(t('perf_title'))
    
    col_up, col_dl = st.columns([3, 1])
    with col_up:
        uploaded = st.file_uploader(t('upload_perf'), type=['xlsx'])
        if uploaded:
            try:
                df_new = pd.read_excel(uploaded)
                with st.spinner("Saving..."):
                    if save_perf_data(df_new):
                        st.session_state['perf_data'] = load_perf_data()
                        st.success("Success!")
                        st.rerun()
            except Exception as e: st.error(f"Error: {e}")
    with col_dl:
        st.write(""); st.write("")
        st.download_button(f"📥 {t('download_tmpl')}", generate_excel_template('perf'), "template.xlsx")
    
    # LOAD DATA
    if 'perf_data' in st.session_state and not st.session_state['perf_data'].empty:
        df = st.session_state['perf_data'].copy()
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])

        # DELETE DATA
        with st.expander(f"🗑️ {t('manage_data')}"):
            c_del1, c_del2 = st.columns([3, 1])
            del_dt = c_del1.date_input(t('del_date'), key='del_dt_picker')
            if c_del2.button(t('btn_del')):
                with st.spinner("Deleting..."):
                    if delete_perf_data_by_date(del_dt):
                        st.session_state['perf_data'] = load_perf_data()
                        st.success("Data Deleted.")
                        st.rerun()

        # APPLY GLOBAL FILTER
        mask = (df['Tanggal'].dt.date >= start_d) & (df['Tanggal'].dt.date <= end_d)
        df = df.loc[mask]

        # --- 4. ANALISIS BUCKET (TABEL SESUAI GAMBAR) ---
        st.divider()
        st.subheader("📊 Rangkuman Performa Driver (Summary)")

        # Prepare Helper Function
        def get_bucket_stats(sub_df, buckets, bucket_col):
            stats = []
            total_rev_all = sub_df['Net Earnings'].sum()
            
            for b_name, condition in buckets.items():
                filtered = sub_df[condition]
                omset = filtered['Net Earnings'].sum()
                # Persentase dari total omset level tersebut
                pct = (omset / total_rev_all * 100) if total_rev_all > 0 else 0
                count_drivers = filtered['Nama Driver'].nunique() # Count unique driver interactions
                
                stats.append({
                    bucket_col: b_name,
                    "Omset": format_rupiah(omset),
                    "Persentase": f"{pct:.1f}%",
                    "Jumlah Driver": count_drivers
                })
            
            # Row Total
            stats.append({
                bucket_col: "Total",
                "Omset": format_rupiah(total_rev_all),
                "Persentase": "100%",
                "Jumlah Driver": sub_df['Nama Driver'].nunique()
            })
            return pd.DataFrame(stats)

        # Split Data
        df_std = df[df['Merek'] == 'Standard']
        df_prm = df[df['Merek'] == 'Premium']

        col_tbl1, col_tbl2 = st.columns(2)

        # === STANDARD TABLES ===
        with col_tbl1:
            st.markdown("### STANDARD")
            if not df_std.empty:
                # 1. Pendapatan Buckets
                std_inc_buckets = {
                    "<Rp 300,000": (df_std['Net Earnings'] < 300000),
                    "Rp 300,000 - Rp 400,000": (df_std['Net Earnings'] >= 300000) & (df_std['Net Earnings'] < 400000),
                    ">= Rp 400,000": (df_std['Net Earnings'] >= 400000)
                }
                st.write("**Klasifikasi Pendapatan**")
                st.dataframe(get_bucket_stats(df_std, std_inc_buckets, "Klasifikasi Pendapatan"), hide_index=True, use_container_width=True)

                # 2. Jam Online Buckets
                std_hour_buckets = {
                    "< 7 jam": (df_std['Total Online Hours'] < 7),
                    "7-9 jam": (df_std['Total Online Hours'] >= 7) & (df_std['Total Online Hours'] < 9),
                    ">= 9 jam": (df_std['Total Online Hours'] >= 9)
                }
                st.write("**Klasifikasi Jam Online**")
                st.dataframe(get_bucket_stats(df_std, std_hour_buckets, "Klasifikasi Jam Online"), hide_index=True, use_container_width=True)
            else:
                st.info("Tidak ada data Standard.")

        # === PREMIUM TABLES ===
        with col_tbl2:
            st.markdown("### PREMIUM")
            if not df_prm.empty:
                # 1. Pendapatan Buckets
                prm_inc_buckets = {
                    "<Rp 500,000": (df_prm['Net Earnings'] < 500000),
                    "Rp 500,000 - Rp 600,000": (df_prm['Net Earnings'] >= 500000) & (df_prm['Net Earnings'] < 600000),
                    ">= Rp 600,000": (df_prm['Net Earnings'] >= 600000)
                }
                st.write("**Klasifikasi Pendapatan**")
                st.dataframe(get_bucket_stats(df_prm, prm_inc_buckets, "Klasifikasi Pendapatan"), hide_index=True, use_container_width=True)

                # 2. Jam Online Buckets
                prm_hour_buckets = {
                    "< 7 jam": (df_prm['Total Online Hours'] < 7),
                    "7-9 jam": (df_prm['Total Online Hours'] >= 7) & (df_prm['Total Online Hours'] < 9),
                    ">= 9 jam": (df_prm['Total Online Hours'] >= 9)
                }
                st.write("**Klasifikasi Jam Online**")
                st.dataframe(get_bucket_stats(df_prm, prm_hour_buckets, "Klasifikasi Jam Online"), hide_index=True, use_container_width=True)
            else:
                st.info("Tidak ada data Premium.")

        # --- 6. TABEL DETAIL HARIAN (WARNA WARNI) ---
        st.divider()
        st.subheader("📝 Detail Transaksi Harian")
        
        # Rename for display
        df_display = df.rename(columns={'Merek': 'Level'})
        df_display['Tanggal'] = pd.to_datetime(df_display['Tanggal']).dt.date
        
        # Logic Pewarnaan
        def highlight_logic(row):
            earn = row['Net Earnings']
            hours = row['Total Online Hours']
            level = row['Level']
            color = ''
            
            if level == 'Standard':
                if earn < 300000 and hours < 7: color = 'background-color: #ffcccc' # Red
                elif (300000 <= earn < 400000) and (7 <= hours < 9): color = 'background-color: #fff4cc' # Yellow
                elif earn >= 400000 and hours >= 9: color = 'background-color: #ccffcc' # Green
                elif earn >= 600000 and hours >= 9: color = 'background-color: #99ff99' # Darker Green
            
            elif level == 'Premium':
                if earn < 500000 and hours < 7: color = 'background-color: #ffcccc'
                elif (500000 <= earn < 600000) and (7 <= hours < 9): color = 'background-color: #fff4cc'
                elif earn >= 600000 and hours >= 9: color = 'background-color: #ccffcc'
            
            return [color] * len(row)

        st.dataframe(
            df_display.style.apply(highlight_logic, axis=1),
            hide_index=True,
            use_container_width=True,
            column_config={
                "Tanggal": st.column_config.DateColumn("Tanggal", format="YYYY-MM-DD"),
                "Net Earnings": st.column_config.NumberColumn("Pendapatan Bersih", format="Rp %.0f"),
                "Total Online Hours": st.column_config.NumberColumn("Jam Online", format="%.2f"),
                "Total Trip Hours": st.column_config.NumberColumn("Jam Trip", format="%.2f"),
                "Total Completed Order": st.column_config.NumberColumn("Order Selesai"),
            }
        )

    else:
        st.info(t('no_data'))

# ==========================================
# 7. HALAMAN 3: DATA DRIVER (TETAP)
# ==========================================
elif selected_page == 'data':
    st.title(t('data_title'))
    
    col_up, col_dl = st.columns([3, 1])
    with col_up:
        up_driver = st.file_uploader(t('upload_data'), type=['xlsx'])
        if up_driver:
            try:
                temp_df = pd.read_excel(up_driver)
                if 'Nama Driver' in temp_df.columns and temp_df['Nama Driver'].duplicated().any():
                    st.error("Error: Duplicate Name")
                else:
                    st.session_state['driver_data'] = temp_df
                    st.success("Success!")
            except Exception as e: st.error(f"Error: {e}")

    with col_dl:
        st.write(""); st.write("")
        st.download_button(f"📥 {t('download_tmpl')}", generate_excel_template('driver'), "template_driver.xlsx")
        
    if 'driver_data' in st.session_state:
        df_d = st.session_state['driver_data']
        k1, k2 = st.columns(2)
        k1.metric(t('stat_total'), len(df_d))
        active = len(df_d[df_d['Status'] == 'Active']) if 'Status' in df_d.columns else 0
        k2.metric(t('stat_active'), active)
        st.data_editor(df_d, num_rows="dynamic", use_container_width=True)
    else:
        st.info(t('no_data'))
