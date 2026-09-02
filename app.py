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
    /* TARJETAS DE INFORMACIÓN - CLIENTES VIP */
    .info-card {
        background: linear-gradient(135deg, #1E3A8A 0%, #2E5AB5 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    
    .info-card h3 {
        color: white !important;
        margin-top: 0 !important;
        font-size: 18px !important;
    }
    
    .info-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        margin-bottom: 15px;
    }
    
    .info-item {
        background-color: rgba(255, 255, 255, 0.1);
        padding: 12px;
        border-radius: 8px;
        border-left: 3px solid #FFD700;
    }
    
    .info-label {
        font-size: 11px;
        opacity: 0.9;
        margin-bottom: 5px;
        text-transform: uppercase;
        font-weight: 600;
    }
    
    .info-value {
        font-size: 16px;
        font-weight: bold;
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
     /* TARJETAS DE SECCIONES */
    .section-card {
        background: linear-gradient(135deg, #1E3A8A 0%, #2E5AB5 100%);
        color: white;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 5px solid #FFD700;
    }
    
    .section-title {
        font-size: 18px;
        font-weight: bold;
        color: white !important;
        margin: 0 !important;
    }
    
    .provider-header {
        background-color: #E0E7FF;
        border-left: 4px solid #1E3A8A;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 12px;
        margin-top: 20px;
    }
    
    .provider-header h4 {
        color: #1E3A8A !important;
        margin: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CARGAR DATOS (CON CACHE)
# ============================================
@st.cache_data(ttl=3600)  # Cache de 1 hora
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

# DEBUG: Mostrar hojas disponibles
st.write("DEBUG - Hojas disponibles:", list(datos.keys()))

# ============================================
# SELECTOR DE PANTALLA (SIDEBAR COMPACTO)
# ============================================
with st.sidebar:
    st.write("")
    st.write("")
    
    if "pantalla_actual" not in st.session_state:
        st.session_state.pantalla_actual = "Resumen Ejecutivo"
    
    if st.button("📊", key="btn_resumen", use_container_width=True):
        st.session_state.pantalla_actual = "Resumen Ejecutivo"
    
    if st.button("👥", key="btn_vip", use_container_width=True):
        st.session_state.pantalla_actual = "Fichas VIP"
    
    if st.button("💰", key="btn_costos", use_container_width=True):
        st.session_state.pantalla_actual = "Machete Costos"
    
    if st.button("📦", key="btn_prov", use_container_width=True):
        st.session_state.pantalla_actual = "Proveedores"

    if st.button("📋", key="btn_post_emision", use_container_width=True):
        st.session_state.pantalla_actual = "Post Emisión"

    st.write("")
    st.markdown("---")
    st.write("")

    if st.button("🔄", key="btn_refresh", use_container_width=True):
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
# PROCESAR DATOS POST EMISIÓN
# ============================================
post_emision_data = {}
if "General" in datos:
    df_general = datos['General']

    # Estructura de columnas:
    # B: Meses, C: GESA Cant, D: GESA Premio, E: GESA IVA, F: GESA Sellos
    # G: BLISTER Cant, H: BLISTER Premio, I: BLISTER IVA, J: BLISTER Sellos
    # K: Total Cant, L: Total Premio, M: Ajustes
    meses_post = ["Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio"]

    for idx, row in df_general.iterrows():
        mes = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""

        if mes in meses_post:
            try:
                post_emision_data[mes] = {
                    'GESA': {
                        'cant': pd.to_numeric(row.iloc[2], errors='coerce') if pd.notna(row.iloc[2]) else 0,
                        'premio': pd.to_numeric(row.iloc[3], errors='coerce') if pd.notna(row.iloc[3]) else 0,
                        'iva': pd.to_numeric(row.iloc[4], errors='coerce') if pd.notna(row.iloc[4]) else 0,
                        'sellos': pd.to_numeric(row.iloc[5], errors='coerce') if pd.notna(row.iloc[5]) else 0,
                    },
                    'BLISTER': {
                        'cant': pd.to_numeric(row.iloc[6], errors='coerce') if pd.notna(row.iloc[6]) else 0,
                        'premio': pd.to_numeric(row.iloc[7], errors='coerce') if pd.notna(row.iloc[7]) else 0,
                        'iva': pd.to_numeric(row.iloc[8], errors='coerce') if pd.notna(row.iloc[8]) else 0,
                        'sellos': pd.to_numeric(row.iloc[9], errors='coerce') if pd.notna(row.iloc[9]) else 0,
                    },
                    'TOTALES': {
                        'cant': pd.to_numeric(row.iloc[10], errors='coerce') if pd.notna(row.iloc[10]) else 0,
                        'total': pd.to_numeric(row.iloc[11], errors='coerce') if pd.notna(row.iloc[11]) else 0,
                        'ajuste': pd.to_numeric(row.iloc[12], errors='coerce') if pd.notna(row.iloc[12]) else 0,
                    }
                }
            except (IndexError, ValueError):
                pass

    # Obtener el último mes con datos
    ultimo_mes = None
    if post_emision_data:
        # Ordenar meses en orden cronológico
        meses_con_datos = [m for m in meses_post if m in post_emision_data]
        ultimo_mes = meses_con_datos[-1] if meses_con_datos else None

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
                
                # INFORMACIÓN ADICIONAL (B15:E21)
                st.write("### 📋 Información del Cliente")
                
                info_rows = df_cliente.iloc[14:21]
                info_data = []
                
                for idx, row in info_rows.iterrows():
                    etiqueta = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                    valores = []
                    for col_idx in range(2, len(row)):
                        if col_idx < len(row) and pd.notna(row.iloc[col_idx]):
                            val = str(row.iloc[col_idx]).strip()
                            if val and val.lower() != "nan":
                                valores.append(val)
                    
                    if etiqueta and etiqueta.lower() not in ["nan", "", "none"]:
                        valor_completo = " ".join(valores).strip()
                        info_data.append({"Dato": etiqueta, "Valor": valor_completo})
                
                if info_data:
                    st.markdown("""
                    <div class="info-card">
                    <h3>📋 Datos Principales</h3>
                    """, unsafe_allow_html=True)
                    
                    for i in range(0, len(info_data), 2):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            item = info_data[i]
                            st.markdown(f"""
                            <div class="info-item">
                                <div class="info-label">{item['Dato']}</div>
                                <div class="info-value">{item['Valor']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        if i + 1 < len(info_data):
                            with col2:
                                item = info_data[i + 1]
                                st.markdown(f"""
                                <div class="info-item">
                                    <div class="info-label">{item['Dato']}</div>
                                    <div class="info-value">{item['Valor']}</div>
                                </div>
                                """, unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("---")
                
                # Extraer datos mensuales
                df_datos = df_cliente.iloc[3:10].copy()
                df_datos = df_datos.dropna(subset=['Unnamed: 1'], how='all')
                
                if cliente == "TOYOS":
                    st.write("### 📊 Garantías - Ventas Mensuales")
                    
                    df_table = df_datos[['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3']].copy()
                    df_table.columns = ['Mes', 'GAR_Cant', 'GAR_Premio']
                    df_table = df_table[df_table['Mes'].notna()]
                    
                    df_display = df_table.copy()
                    df_display['GAR_Cant'] = pd.to_numeric(df_display['GAR_Cant'], errors='coerce').fillna(0).astype(int)
                    df_display['GAR_Premio'] = df_display['GAR_Premio'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) and x != 0 else "")
                    
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    
                    st.write("### 📈 Evolución de Ventas")
                    df_graph = df_table.copy()
                    df_graph['GAR_Cant'] = pd.to_numeric(df_graph['GAR_Cant'], errors='coerce')
                    df_graph = df_graph[df_graph['Mes'].notna() & (df_graph['GAR_Cant'] > 0)]
                    
                    if not df_graph.empty:
                        st.bar_chart(df_graph.set_index('Mes')['GAR_Cant'])
                
                else:
                    st.write("### 📊 Ventas por Cobertura")
                    
                    df_table = df_datos[['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4', 'Unnamed: 5', 'Unnamed: 6', 'Unnamed: 7']].copy()
                    df_table.columns = ['Mes', 'ASS_Cant', 'ASS_Premio', 'GAR_Cant', 'GAR_Premio', 'TOT_Cant', 'TOT_Premio']
                    df_table = df_table[df_table['Mes'].notna()]
                    
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
# ============================================
# PANTALLA 3: COSTOS SANCOR
# ============================================
elif pantalla_actual == "Machete Costos":
    st.title("Costos Sancor")
    
    if "Costos Sancor" in datos:
        df_costos = datos["Costos Sancor"]
        
        st.markdown("""
        <div class="section-card">
            <div class="section-title">💰 Matriz de Coberturas y Costos</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Extraer datos
        df_tabla = df_costos.iloc[2:16].copy()
        
        df_con_max = df_tabla[['Unnamed: 3', 'Unnamed: 4']].copy()
        df_con_max.columns = ['Cobertura', 'Costo']
        df_con_max = df_con_max[df_con_max['Cobertura'].notna()]
        
        df_sin_max = df_tabla[['Unnamed: 6', 'Unnamed: 7']].copy()
        df_sin_max.columns = ['Cobertura', 'Costo']
        df_sin_max = df_sin_max[df_sin_max['Cobertura'].notna()]
        
        # Mostrar en dos columnas
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="provider-header">
                <h4>📌 CON MAX</h4>
            </div>
            """, unsafe_allow_html=True)
            df_display_max = df_con_max.copy()
            df_display_max['Costo'] = df_display_max['Costo'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "")
            st.dataframe(df_display_max, use_container_width=True, hide_index=True)
        
        with col2:
            st.markdown("""
            <div class="provider-header">
                <h4>📌 SIN MAX</h4>
            </div>
            """, unsafe_allow_html=True)
            df_display_sin_max = df_sin_max.copy()
            df_display_sin_max['Costo'] = df_display_sin_max['Costo'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "")
            st.dataframe(df_display_sin_max, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.caption("✅ Tabla de referencia rápida de coberturas Sancor")
    
    else:
        st.error("❌ Pestaña 'Costos Sancor' no encontrada")
# ============================================
# PANTALLA 4: FACTURACIÓN DE PROVEEDORES
# ============================================
elif pantalla_actual == "Proveedores":
    st.title("Facturación de Proveedores")
    
    if "FC Proveedores" in datos:
        df_prov = datos["FC Proveedores"]
        
        st.markdown("""
        <div class="section-card">
            <div class="section-title">📊 Comparativa de Facturación por Proveedor</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Extraer datos
        df_datos = df_prov.iloc[3:10].copy()
        df_datos = df_datos.dropna(subset=['Unnamed: 1'], how='all')
        
        df_tabla = df_datos[['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4', 'Unnamed: 5', 
                             'Unnamed: 6', 'Unnamed: 7', 'Unnamed: 8', 'Unnamed: 9', 'Unnamed: 10', 'Unnamed: 11']].copy()
        
        df_tabla.columns = ['Mes', 'Cardinal_Cant', 'Cardinal_Precio', 'Addiuva_Cant', 'Addiuva_Precio',
                           'BZR_Cant', 'BZR_Precio', 'GRAL_Cant', 'GRAL_Precio', 'Imprenta_Cant', 'Imprenta_Precio']
        
        df_tabla = df_tabla[df_tabla['Mes'].notna()]
        
        # CARDINAL
        st.markdown("""
        <div class="provider-header">
            <h4>🏥 Cardinal</h4>
        </div>
        """, unsafe_allow_html=True)
        df_cardinal = df_tabla[['Mes', 'Cardinal_Cant', 'Cardinal_Precio']].copy()
        df_cardinal.columns = ['Mes', 'Cantidad', 'Precio']
        df_cardinal['Cantidad'] = pd.to_numeric(df_cardinal['Cantidad'], errors='coerce').fillna(0).astype(int)
        df_cardinal['Precio'] = df_cardinal['Precio'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) and x != 0 else "")
        st.dataframe(df_cardinal, use_container_width=True, hide_index=True)
        
        # ADDIUVA
        st.markdown("""
        <div class="provider-header">
            <h4>💊 Addiuva</h4>
        </div>
        """, unsafe_allow_html=True)
        df_addiuva = df_tabla[['Mes', 'Addiuva_Cant', 'Addiuva_Precio']].copy()
        df_addiuva.columns = ['Mes', 'Cantidad', 'Precio']
        df_addiuva['Cantidad'] = pd.to_numeric(df_addiuva['Cantidad'], errors='coerce').fillna(0).astype(int)
        df_addiuva['Precio'] = df_addiuva['Precio'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) and x != 0 else "")
        st.dataframe(df_addiuva, use_container_width=True, hide_index=True)
        
        # LLAMADAS AL DOCTOR - BZR
        st.markdown("""
        <div class="provider-header">
            <h4>☎️ Llamadas al Doctor - BZR</h4>
        </div>
        """, unsafe_allow_html=True)
        df_bzr = df_tabla[['Mes', 'BZR_Cant', 'BZR_Precio']].copy()
        df_bzr.columns = ['Mes', 'Cantidad', 'Precio']
        df_bzr['Cantidad'] = pd.to_numeric(df_bzr['Cantidad'], errors='coerce').fillna(0).astype(int)
        df_bzr['Precio'] = df_bzr['Precio'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) and x != 0 else "")
        st.dataframe(df_bzr, use_container_width=True, hide_index=True)
        
        # LLAMADAS AL DOCTOR - GRAL
        st.markdown("""
        <div class="provider-header">
            <h4>☎️ Llamadas al Doctor - GRAL</h4>
        </div>
        """, unsafe_allow_html=True)
        df_gral = df_tabla[['Mes', 'GRAL_Cant', 'GRAL_Precio']].copy()
        df_gral.columns = ['Mes', 'Cantidad', 'Precio']
        df_gral['Cantidad'] = pd.to_numeric(df_gral['Cantidad'], errors='coerce').fillna(0).astype(int)
        df_gral['Precio'] = df_gral['Precio'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) and x != 0 else "")
        st.dataframe(df_gral, use_container_width=True, hide_index=True)
        
        # IMPRENTA
        st.markdown("""
        <div class="provider-header">
            <h4>🖨️ Imprenta</h4>
        </div>
        """, unsafe_allow_html=True)
        df_imprenta = df_tabla[['Mes', 'Imprenta_Cant', 'Imprenta_Precio']].copy()
        df_imprenta.columns = ['Mes', 'Cantidad', 'Precio']
        df_imprenta['Cantidad'] = pd.to_numeric(df_imprenta['Cantidad'], errors='coerce').fillna(0).astype(int)
        df_imprenta['Precio'] = df_imprenta['Precio'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) and x != 0 else "")
        st.dataframe(df_imprenta, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.caption("✅ Datos de facturación cargados desde Google Drive")
    
    else:
        st.error("❌ Pestaña 'FC Proveedores' no encontrada")

# ============================================
# PANTALLA 5: POST EMISIÓN
# ============================================
elif pantalla_actual == "Post Emisión":
    st.title("Post Emisión")

    if "General" in datos and post_emision_data:
        # SECCIÓN SUPERIOR: ÚLTIMO MES CON DATOS
        if ultimo_mes:
            datos_ultimo = post_emision_data[ultimo_mes]

            st.markdown(f"""
            <div class="section-card">
                <div class="section-title">📊 {ultimo_mes} 2026</div>
            </div>
            """, unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("""
                <div class="info-card">
                <h3 style="color: #FF00FF !important;">🏢 GESA</h3>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="info-item" style="border-left-color: #FF00FF;">
                    <div class="info-label">Cantidad</div>
                    <div class="info-value">{int(datos_ultimo['GESA']['cant']):,}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="info-item" style="border-left-color: #FF00FF; margin-top: 10px;">
                    <div class="info-label">Premio</div>
                    <div class="info-value">${datos_ultimo['GESA']['premio']:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            with col2:
                st.markdown("""
                <div class="info-card">
                <h3 style="color: #0066FF !important;">🏢 BLISTER</h3>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="info-item" style="border-left-color: #0066FF;">
                    <div class="info-label">Cantidad</div>
                    <div class="info-value">{int(datos_ultimo['BLISTER']['cant']):,}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="info-item" style="border-left-color: #0066FF; margin-top: 10px;">
                    <div class="info-label">Premio</div>
                    <div class="info-value">${datos_ultimo['BLISTER']['premio']:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            with col3:
                st.markdown("""
                <div class="info-card">
                <h3 style="color: #1E3A8A !important;">📈 TOTALES</h3>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="info-item" style="border-left-color: #1E3A8A;">
                    <div class="info-label">Cantidad</div>
                    <div class="info-value">{int(datos_ultimo['TOTALES']['cant']):,}</div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                <div class="info-item" style="border-left-color: #1E3A8A; margin-top: 10px;">
                    <div class="info-label">Total</div>
                    <div class="info-value">${datos_ultimo['TOTALES']['total']:,.0f}</div>
                </div>
                """, unsafe_allow_html=True)

                # Solo mostrar Ajuste si tiene datos (no es 0)
                if datos_ultimo['TOTALES']['ajuste'] != 0:
                    st.markdown(f"""
                    <div class="info-item" style="border-left-color: #1E3A8A; margin-top: 10px;">
                        <div class="info-label">Ajuste</div>
                        <div class="info-value">${datos_ultimo['TOTALES']['ajuste']:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # TABLA HISTÓRICA
        st.write("### 📊 Histórico de Datos")

        # Construir tabla para visualización
        tabla_datos = []
        for mes in [m for m in ["Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio"] if m in post_emision_data]:
            datos_mes = post_emision_data[mes]
            tabla_datos.append({
                'Mes': mes,
                'GESA - Cant': int(datos_mes['GESA']['cant']),
                'GESA - Premio': f"${datos_mes['GESA']['premio']:,.0f}",
                'GESA - IVA': f"${datos_mes['GESA']['iva']:,.0f}",
                'GESA - Sellos': f"${datos_mes['GESA']['sellos']:,.0f}",
                'BLISTER - Cant': int(datos_mes['BLISTER']['cant']),
                'BLISTER - Premio': f"${datos_mes['BLISTER']['premio']:,.0f}",
                'BLISTER - IVA': f"${datos_mes['BLISTER']['iva']:,.0f}",
                'BLISTER - Sellos': f"${datos_mes['BLISTER']['sellos']:,.0f}",
                'TOTALES - Cant': int(datos_mes['TOTALES']['cant']),
                'TOTALES - Total': f"${datos_mes['TOTALES']['total']:,.0f}",
                'TOTALES - Ajuste': f"${datos_mes['TOTALES']['ajuste']:,.0f}",
            })

        if tabla_datos:
            df_historico = pd.DataFrame(tabla_datos)
            st.dataframe(df_historico, use_container_width=True, hide_index=True)
        else:
            st.info("📭 No hay datos disponibles para mostrar")

        st.markdown("---")
        st.caption("✅ Datos de Post Emisión cargados en vivo desde Google Drive")

    else:
        st.error("❌ No se encontraron datos en la pestaña 'General' o no hay información disponible")
