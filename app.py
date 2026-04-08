import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium
import pandas as pd
import base64

# Pastikan set_page_config adalah arahan pertama selepas import
st.set_page_config(layout="wide", page_title="Keputusan PRU Semenanjung")

# --- FUNGSI LOG MASUK (LOGIN) ---
def semak_login():
    """Fungsi untuk menguruskan sistem log masuk ringkas"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("""
            <style>
            .login-box {
                background-color: rgba(255, 255, 255, 0.9);
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0px 4px 20px rgba(0,0,0,0.2);
                max-width: 400px;
                margin: auto;
            }
            </style>
        """, unsafe_allow_html=True)
        
        st.title("🔐 Akses Terhad")
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                user_id = st.text_input("ID Pengguna")
                password = st.text_input("Kata Laluan", type="password")
                if st.button("Log Masuk"):
                    # Anda boleh menukar ID dan Password di sini
                    if user_id == "admin" and password == "pru123":
                        st.session_state.authenticated = True
                        st.rerun()
                    else:
                        st.error("ID atau Kata Laluan salah!")
        return False
    return True

# --- 1. KONFIGURASI WARNA ---
WARNA_MASTER = {
    "BN": "#0070FF", "PH": "#FF0000", "PN": "#002673",
    "PAS": "#4CE600", "DAP": "#FF0000", "PKR": "#00C5FF",
    "MUDA": "#FFFF00", "BEBAS": "#B2B2B2",
}

# --- 2. FUNGSI IMEJ LATAR BELAKANG ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except:
        return None

img_path = "C:/PRN2021/atlas B4 gaya moden no blur.png"
bin_str = get_base64_of_bin_file(img_path)

if bin_str:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-color: #f0f2f6;
        }}
        /* Tajuk Utama Styling */
        .main-title {{
            font-size: 42px !important;
            font-weight: bold;
            color: #1a202c;
            text-align: center;
            margin-bottom: 0px;
            text-shadow: 2px 2px 4px rgba(255,255,255,0.8);
        }}
        .stats-card, .stDataFrame, div[data-testid="stVerticalBlock"] > div {{
            background-color: rgba(255, 255, 255, 0.85) !important;
            border-radius: 17px;
            padding: 14px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# --- JALANKAN LOGIK APLIKASI ---
if semak_login():
    # --- 3. FUNGSI MUAT DATA ---
    @st.cache_data
    def muat_data_gis():
        path = "C:/PRN2021/parlimen/parlimen_semenanjung.shp"
        gdf = gpd.read_file(path)
        geom_name = gdf.geometry.name
        gdf.columns = [x.upper() for x in gdf.columns]
        gdf = gdf.set_geometry(geom_name.upper())
        gdf = gdf.to_crs(epsg=4326)
        return gdf

    try:
        gdf = muat_data_gis()
        lajur_negeri = 'NEGERI' 
        lajur_nama_parlimen = 'NAMAPARLIM' if 'NAMAPARLIM' in gdf.columns else gdf.columns[0]

        # --- SIDEBAR ---
        st.sidebar.title("⚙️ Kawalan")
        if st.sidebar.button("Log Keluar"):
            st.session_state.authenticated = False
            st.rerun()
            
        pilihan_pru = st.sidebar.radio("Pilih Tahun PRU:", ["PRU 13", "PRU 14", "PRU 15"])
        senarai_negeri = ["SEMUA NEGERI"] + sorted(gdf[lajur_negeri].unique().tolist())
        pilihan_negeri = st.sidebar.selectbox("Pilih Negeri:", senarai_negeri)
        nama_lajur_pru = pilihan_pru.replace(" ", "")

        # --- 4. LOGIK FILTER & ZOOM ---
        if pilihan_negeri != "SEMUA NEGERI":
            gdf_fokus = gdf[gdf[lajur_negeri] == pilihan_negeri]
            gdf_luar = gdf[gdf[lajur_negeri] != pilihan_negeri]
            bounds = gdf_fokus.total_bounds
            center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
            zoom = 9
        else:
            gdf_fokus = gdf
            gdf_luar = pd.DataFrame()
            center = [4.2105, 101.9758]
            zoom = 7

        # --- 5. TAJUK & STATISTIK ---
        st.markdown('<p class="main-title">KEPUTUSAN PILIHAN RAYA SEMENANJUNG MALAYSIA</p>', unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center; color: #4a5568;'>🗳️ Dashboard {pilihan_pru}: {pilihan_negeri}</h3>", unsafe_allow_html=True)
        
        kiraan_parti = gdf_fokus[nama_lajur_pru].value_counts()
        
        if not kiraan_parti.empty:
            cols = st.columns(len(kiraan_parti))
            for i, (parti, jumlah) in enumerate(kiraan_parti.items()):
                warna = WARNA_MASTER.get(str(parti).upper(), "#B2B2B2")
                with cols[i]:
                    st.markdown(f"""
                        <div class="stats-card" style="border-top: 5px solid {warna}; text-align:center;">
                            <h4 style="margin:0; color:{warna};">{parti}</h4>
                            <h2 style="margin:0;">{jumlah}</h2>
                        </div>
                    """, unsafe_allow_html=True)

        # --- 6. PETA & ANALISIS (WIDE LAYOUT) ---
        st.write("---") 
        col_map, col_legend = st.columns([3.5, 1])
        
        with col_map:
            m = folium.Map(location=center, zoom_start=zoom, tiles="CartoDB positron")
            if not gdf_luar.empty:
                folium.GeoJson(gdf_luar, style_function=lambda f: {'fillColor': '#D1D5DB', 'color': 'white', 'weight': 0.5, 'fillOpacity': 0.15}).add_to(m)
            
            folium.GeoJson(gdf_fokus, style_function=lambda f: {
                    'fillColor': WARNA_MASTER.get(str(f['properties'][nama_lajur_pru]).upper(), "#E2E8F0"),
                    'color': 'white', 'weight': 1.2, 'fillOpacity': 0.7
                },
                tooltip=folium.GeoJsonTooltip(fields=[lajur_nama_parlimen, nama_lajur_pru], aliases=['Parlimen:', 'Pemenang:'])
            ).add_to(m)
            
            st_folium(m, width=1100, height=650, key=f"map_{pilihan_negeri}_{pilihan_pru}")

        with col_legend:
            st.subheader("📊 Analisis")
            st.bar_chart(kiraan_parti)
            st.write("**Data Kerusi:**")
            st.dataframe(kiraan_parti, use_container_width=True)

    except Exception as e:
        st.error(f"Ralat: {e}")