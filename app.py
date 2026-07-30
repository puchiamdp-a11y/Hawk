import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ============================================
# CONFIGURACIÓN
# ============================================
st.set_page_config(
    page_title="Hawk - Reportes",
    layout="wide",
    initial_sidebar_state="expanded"
)

GOOGLE_DRIVE_ID = "1gZPD9XUspcN8e4FGrgdEl1AacDew68RU"
URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_DRIVE_ID}/export?format=xlsx"

# ============================================
# ESTILOS CORPORATIVOS (OPTIMIZADO PARA MOBILE)
# ============================================
st.markdown("""
<style>
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    body {
        background-color: #FFFFFF !important;
    }
    
    .main {
        padding: 0.5rem;
    }
    
    h1, h2, h3 {
        margin: 0.5rem 0 !important;
        padding: 0 !important;
    }
    
    h1 {
        font-size: 24px !important;
    }
    
    h3 {
        font-size: 16px !important;
        margin-top: 1rem !important;
    }
    
    .metrics-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin: 10px 0;
    }
    
    .metric-box {
        background-color: #1E3A8A;
        color: white;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
    }
    
    .metric-title {
        font-size: 11px;
        opacity: 0.9;
        margin-bottom: 4px;
    }
    
    .metric-value {
        font-size: 18px;
        font-weight: bold;
        margin: 3px 0;
        word-break: break-word;
    }
    
    .metric-subtitle {
        font-size: 9px;
        opacity: 0.85;
    }
    
    .emission-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0;
        margin: 10px 0;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .emission-cell {
        padding: 12px;
        border-right: 1px solid #E5E7EB;
        border-bottom: 1px solid #E5E7EB;
        text-align: center;
    }
    
    .emission-cell:nth-child(2n) {
        border-right: none;
    }
    
    .emission-cell:nth-last-child(-n+2) {
        border-bottom: none;
    }
    
    .emission-label {
        font-size: 14px;
        font-weight: 600;
        color: #666;
        margin-bottom: 8px;
    }
    
    .emission-value {
        font-size: 32px;
        font-weight: bold;
        color: #1E3A8A;
    }
    
    .alert-card {
        background-color: #1E3A8A;
        color: white;
        padding: 12px;
        border-radius: 8px;
        margin: 8px 0;
    }
    
    .alert-title {
        font-size: 15px;
        font-weight: bold;
        margin-bottom: 6px;
    }
    
    .alert-content {
        font-size: 12px;
        line-height: 1.5;
    }
    
    .stMetric {
        background-color: transparent;
        padding: 0 !important;
    }
    
    .stMetric > div:first-child {
        font-size: 10px !important;
    }
    
    .stMetric label {
        font-size: 10px !important;
    }
    
    /* SIDEBAR COMPACTO Y PROFESIONAL */
    [data-testid="stSidebar"] {
        width: 120px !important;
        background-color: #FFFFFF !important;
        border-right: 1px solid #E5E7EB;
    }
    
    [data-testid="stSidebarContent"] {
        width: 120px !important;
    }
    
   .stButton > button {
        width: 100%;
        height: 100px !important;
        font-size: 60px !important;
        padding: 0 !important;
        border-radius: 8px !important;
        background-color: #F3F4F6 !important;
        color: #1E3A8A !important;
        border: 1px solid #E5E7EB !important;
        margin-bottom: 10px !important;
        transition: all 0.3s ease !important;
        box-shadow: none !important;
    }
    
    .stButton > button:hover {
        color: #2E5AB5 !important;
        background-color: #E0E7FF !important;
        transform: scale(1.05) !important;
        border: 1px solid #C7D2FE !important;
    }
    
    .stButton > button:active {
        color: #1a2a5c !important;
        background-color: #C7D2FE !important;
        transform: scale(0.95) !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CARGAR DATOS (CON CACHE)
# ============================================
@st.cache_data(ttl=300)  # Cache de 5 minutos
def cargar_datos():
    """Carga datos frescos de Google Drive (con cache de 5 min)"""
    response = requests.get(URL, timeout=10)
    archivo_excel = BytesIO(response.content)
    
    datos = {}
    excel_file = pd.ExcelFile(archivo_excel)
    
    for pestaña in excel_file.sheet_names:
        datos[pestaña] = pd.read_excel(archivo_excel, sheet_name=pestaña)
    
    return datos

datos = cargar_datos()
# ============================================
# SELECTOR DE PANTALLA (SIDEBAR COMPACTO)
# ============================================
with st.sidebar:
    st.write("")
    st.write("")
    
    if "pantalla_actual" not in st.session_state:
        st.session_state.pantalla_actual = "Resumen Ejecutivo"
    
    col1, col2, col3, col4, col5 = st.columns(1)
    
    if st.button("📊", key="btn_resumen"):
        st.session_state.pantalla_actual = "Resumen Ejecutivo"
    
    if st.button("👥", key="btn_vip"):
        st.session_state.pantalla_actual = "Fichas VIP"
    
    if st.button("💰", key="btn_costos"):
        st.session_state.pantalla_actual = "Machete Costos"
    
    if st.button("📦", key="btn_prov"):
        st.session_state.pantalla_actual = "Proveedores"
    
    st.write("")
    st.markdown("---")
    st.write("")
    
    if st.button("🔄", key="btn_refresh"):
        st.cache_data.clear()

# Forzar cierre de sidebar con CSS
st.markdown("""
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const sidebar = document.querySelector('[data-testid="stSidebar"]');
        if (sidebar) {
            sidebar.style.marginLeft = '-250px';
            sidebar.style.transition = 'margin-left 0.3s';
            setTimeout(() => {
                sidebar.style.marginLeft = '0px';
            }, 100);
        }
    });
</script>
""", unsafe_allow_html=True)

pantalla_actual = st.session_state.pantalla_actual
# ============================================
# PROCESAR DATOS RESUMEN
# ============================================
df_resumen = datos['Resumen']

def obtener_fila_mes(df, mes_nombre):
    """Encuentra la fila que contiene el mes especificado"""
    for idx, row in df.iterrows():
        if str(row.iloc[3]).strip().lower() == mes_nombre.lower():
            return row
    return None

mayo = obtener_fila_mes(df_resumen, "Mayo")
junio = obtener_fila_mes(df_resumen, "Junio")

# ============================================
# PROCESAR DATOS COMERCIOS
# ============================================
df_comercios = datos['Comercios']

total_comercios = None
pendientes_emitir = None
ya_emitidos = None
promedio_ventas_pendientes = None

for idx, row in df_comercios.iterrows():
    if str(row.iloc[8]).strip() == "TOTAL DE COMERCIOS :":
        total_comercios = int(row.iloc[9])
    elif str(row.iloc[8]).strip() == "PENDIENTES":
        pendientes_emitir = int(row.iloc[9])
        promedio_ventas_pendientes = row.iloc[10]
    elif str(row.iloc[8]).strip() == "EMITIDOS":
        ya_emitidos = int(row.iloc[9])

# ============================================
# PROCESAR DATOS VENTAS PENDIENTES DE INFORMAR
# ============================================
df_pendiente = datos['Pendiente de informar']

fila_totales = df_pendiente.iloc[-1]

comercios_pendientes = {
    'PARDO': {
        'meses_pendientes': [],
        'certificados': fila_totales.iloc[3],  # D19
        'premio': fila_totales.iloc[4]  # E19
    },
    'DRICCO': {
        'meses_pendientes': [],
        'certificados': fila_totales.iloc[7],  # H19
        'premio': fila_totales.iloc[8]  # I19
    },
    'SENSEI': {
        'meses_pendientes': [],
        'certificados': fila_totales.iloc[11],  # L19
        'premio': fila_totales.iloc[12]  # M19
    }
}

meses_orden = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"]

comercios_cols = {
    'PARDO': {'cant': 3, 'ge': 4, 'cant_ass': 5, 'ass': 6},
    'DRICCO': {'cant': 7, 'ge': 8, 'cant_ass': 9, 'ass': 10},
    'SENSEI': {'cant': 11, 'ge': 12, 'cant_ass': 13, 'ass': 14}
}

for comercio in comercios_pendientes.keys():
    for idx, row in df_pendiente.iterrows():
        mes = str(row.iloc[2]).strip()
        
        if mes in meses_orden:
            cant_val = row.iloc[comercios_cols[comercio]['cant']]
            if pd.notna(cant_val) and cant_val != 0:
                comercios_pendientes[comercio]['meses_pendientes'].append(mes)

# ============================================
# PANTALLA 1: RESUMEN EJECUTIVO
# ============================================
if pantalla_actual == "Resumen Ejecutivo":
    st.title("Hawk - Reportes Internos")
    
    # BLOQUE 1: MÉTRICAS DE JUNIO
    st.write("**Junio 2026**")
    
    if junio is not None:
        st.markdown(f"""
        <div class="metrics-grid">
            <div class="metric-box">
                <div class="metric-title">Garantías</div>
                <div class="metric-value">{int(junio.iloc[7]):,}</div>
                <div class="metric-subtitle">Cantidad</div>
            </div>
            <div class="metric-box">
                <div class="metric-title">Garantías</div>
                <div class="metric-value">${junio.iloc[8]:,.0f}</div>
                <div class="metric-subtitle">Premio</div>
            </div>
            <div class="metric-box">
                <div class="metric-title">Asistencias</div>
                <div class="metric-value">{int(junio.iloc[10]):,}</div>
                <div class="metric-subtitle">Cantidad</div>
            </div>
            <div class="metric-box">
                <div class="metric-title">Asistencias</div>
                <div class="metric-value">${junio.iloc[11]:,.0f}</div>
                <div class="metric-subtitle">Premio</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
   # BLOQUE 2: COMERCIOS FALTANTES (GRILLA 2x2)
    st.write("**Estado de Emisión**")
    
    st.markdown(f"""
    <div class="emission-grid">
        <div class="emission-cell">
            <div class="emission-label">📊 Total</div>
            <div class="emission-value">{total_comercios}</div>
        </div>
        <div class="emission-cell">
            <div class="emission-label">⚠️ Pendientes</div>
            <div class="emission-value">{pendientes_emitir}</div>
        </div>
        <div class="emission-cell">
            <div class="emission-label">✅ Emitidos</div>
            <div class="emission-value">{ya_emitidos}</div>
        </div>
        <div class="emission-cell">
            <div class="emission-label">📈 Cant Promedio</div>
            <div class="emission-value">{int(promedio_ventas_pendientes) if pd.notna(promedio_ventas_pendientes) else 0}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # BLOQUE 3: VENTAS PENDIENTES DE INFORMAR
    st.write("**Ventas Pendientes**")
    
    for comercio, datos_comercio in comercios_pendientes.items():
        if datos_comercio['meses_pendientes']:
            meses_str = ", ".join(datos_comercio['meses_pendientes'])
            certs = int(datos_comercio['certificados']) if pd.notna(datos_comercio['certificados']) else 0
            premio = datos_comercio['premio'] if pd.notna(datos_comercio['premio']) else 0
            
            st.markdown(f"""
            <div class="alert-card">
                <div class="alert-title">{comercio}</div>
                <div class="alert-content">
                    <strong>Meses:</strong> {meses_str}<br>
                    <strong>Certs:</strong> {certs:,} | <strong>Premio:</strong> ${premio:,.0f}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("✅ Datos actualizados desde Google Drive")

# ============================================
# PANTALLA 2: FICHAS VIP CON TABS
# ============================================
elif pantalla_actual == "Fichas VIP":
    st.title("Fichas de Clientes VIP")
    
    clientes_vip = {
        "SYNA": "FC SYNA",
        "BAZAR": "FC BAZAR",
        "TOYOS": "FC TOYOS",
        "DRICCO": "FC DRICCO",
        "SENSEI": "FC SENSEI"
    }
    
    tabs = st.tabs([f"📌 {cliente}" for cliente in clientes_vip.keys()])
    
    for tab, (cliente, pestaña_fc) in zip(tabs, clientes_vip.items()):
        with tab:
            if pestaña_fc in datos:
                df_cliente = datos[pestaña_fc]
                st.write(f"## {cliente}")
                
                # ============================================
                # INFORMACIÓN ADICIONAL (B16:E21)
                # ============================================
                st.write("### 📋 Información del Cliente")
                
                # Extraer desde fila 15 (índice 15, que es fila 16 en Excel)
                info_rows = df_cliente.iloc[15:22]  # B16:E21
                
                # Limpiar y mostrar información
                info_data = []
                for idx, row in info_rows.iterrows():
                    # Columna B: Etiqueta (Comercial, Administrativa, etc)
                    # Columna C-E: Valores
                    etiqueta = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                    valor1 = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
                    valor2 = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
                    valor3 = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ""
                    
                    if etiqueta and etiqueta.lower() not in ["nan", "", "none"]:
                        valor_completo = f"{valor1} {valor2} {valor3}".strip()
                        info_data.append({"Dato": etiqueta, "Valor": valor_completo})
                
                if info_data:
                    df_info = pd.DataFrame(info_data)
                    st.dataframe(df_info, use_container_width=True, hide_index=True)
                else:
                    st.info("No hay información adicional disponible")
                
                st.markdown("---")
                
                # Extraer datos (filas 3-9 tienen los meses)
                df_datos = df_cliente.iloc[3:10].copy()
                df_datos = df_datos.dropna(subset=['Unnamed: 1'], how='all')
                
                # ============================================
                # TOYOS: 4 columnas (solo GARANTIAS)
                # ============================================
                if cliente == "TOYOS":
                    st.write("### 📊 Garantías - Ventas Mensuales")
                    
                    df_table = df_datos[['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3']].copy()
                    df_table.columns = ['Mes', 'GAR_Cant', 'GAR_Premio']
                    df_table = df_table[df_table['Mes'].notna()]
                    
                    # Formatear para tabla
                    df_display = df_table.copy()
                    df_display['GAR_Cant'] = pd.to_numeric(df_display['GAR_Cant'], errors='coerce').fillna(0).astype(int)
                    df_display['GAR_Premio'] = df_display['GAR_Premio'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) and x != 0 else "")
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    
                    # Gráfico de COLUMNAS
                    st.write("### 📈 Evolución de Ventas")
                    df_graph = df_table.copy()
                    df_graph['GAR_Cant'] = pd.to_numeric(df_graph['GAR_Cant'], errors='coerce')
                    df_graph = df_graph[df_graph['Mes'].notna() & (df_graph['GAR_Cant'] > 0)]
                    
                    if not df_graph.empty:
                        st.bar_chart(df_graph.set_index('Mes')['GAR_Cant'])
                
                # ============================================
                # SYNA, BAZAR, DRICCO, SENSEI: 8 columnas
                # ============================================
                else:
                    st.write("### 📊 Ventas por Cobertura")
                    
                    df_table = df_datos[['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4', 'Unnamed: 5', 'Unnamed: 6', 'Unnamed: 7']].copy()
                    df_table.columns = ['Mes', 'ASS_Cant', 'ASS_Premio', 'GAR_Cant', 'GAR_Premio', 'TOT_Cant', 'TOT_Premio']
                    df_table = df_table[df_table['Mes'].notna()]
                    
                    # Mostrar en 3 columnas
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**Asistencias**")
                        df_ass = df_table[['Mes', 'ASS_Cant', 'ASS_Premio']].copy()
                        df_ass['ASS_Cant'] = pd.to_numeric(df_ass['ASS_Cant'], errors='coerce').fillna(0).astype(int)
                        df_ass['ASS_Premio'] = df_ass['ASS_Premio'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) and x != 0 else "")
                        st.dataframe(df_ass, use_container_width=True, hide_index=True)
                    
                    with col2:
                        st.write("**Garantías**")
                        df_gar = df_table[['Mes', 'GAR_Cant', 'GAR_Premio']].copy()
                        df_gar['GAR_Cant'] = pd.to_numeric(df_gar['GAR_Cant'], errors='coerce').fillna(0).astype(int)
                        df_gar['GAR_Premio'] = df_gar['GAR_Premio'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) and x != 0 else "")
                        st.dataframe(df_gar, use_container_width=True, hide_index=True)
                    
                    with col3:
                        st.write("**Total**")
                        df_tot = df_table[['Mes', 'TOT_Cant', 'TOT_Premio']].copy()
                        df_tot['TOT_Cant'] = pd.to_numeric(df_tot['TOT_Cant'], errors='coerce').fillna(0).astype(int)
                        df_tot['TOT_Premio'] = df_tot['TOT_Premio'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) and x != 0 else "")
                        st.dataframe(df_tot, use_container_width=True, hide_index=True)
                    
                    # Gráfico TOTAL de COLUMNAS
                    st.write("### 📈 Evolución Total de Ventas")
                    df_graph = df_table.copy()
                    df_graph['TOT_Cant'] = pd.to_numeric(df_graph['TOT_Cant'], errors='coerce')
                    df_graph = df_graph[df_graph['Mes'].notna() & (df_graph['TOT_Cant'] > 0)]
                    
                    if not df_graph.empty:
                        st.bar_chart(df_graph.set_index('Mes')['TOT_Cant'])
            
            else:
                st.error(f"❌ Pestaña '{pestaña_fc}' no encontrada")
    
    st.markdown("---")
    st.caption("✅ Fichas VIP cargadas desde Google Drive")
