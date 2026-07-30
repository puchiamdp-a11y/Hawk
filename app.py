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
    
    /* GRILLA 2x2 PARA MÉTRICAS */
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
    
    /* GRILLA DE EMISIÓN */
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
        font-size: 10px;
        color: #666;
        margin-bottom: 6px;
    }
    
    .emission-value {
        font-size: 24px;
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
</style>
""", unsafe_allow_html=True)

# ============================================
# CARGAR DATOS
# ============================================
def cargar_datos():
    """Carga datos frescos de Google Drive (sin cache)"""
    response = requests.get(URL, timeout=10)
    archivo_excel = BytesIO(response.content)
    
    datos = {}
    excel_file = pd.ExcelFile(archivo_excel)
    
    for pestaña in excel_file.sheet_names:
        datos[pestaña] = pd.read_excel(archivo_excel, sheet_name=pestaña)
    
    return datos

# Cargar datos (siempre frescos)
datos = cargar_datos()

# ============================================
# SELECTOR DE PANTALLA (SIDEBAR)
# ============================================
with st.sidebar:
    st.write("### 📺 Pantallas")
    pantalla_actual = st.selectbox(
        "Selecciona una pantalla:",
        ["Resumen Ejecutivo", "Fichas VIP", "Machete Costos", "Proveedores"],
        label_visibility="collapsed"
    )

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
# PANTALLA 2: FICHAS VIP (PLACEHOLDER)
# ============================================
elif pantalla_actual == "Fichas VIP":
    st.title("Fichas de Clientes VIP")
    st.info("🚀 Pantalla en desarrollo para el PASO 4")

# ============================================
# PANTALLA 3: MACHETE (PLACEHOLDER)
# ============================================
elif pantalla_actual == "Machete Costos":
    st.title("Machete Digital - Costos Sancor")
    st.info("🚀 Pantalla en desarrollo para el PASO 5")

# ============================================
# PANTALLA 4: PROVEEDORES (PLACEHOLDER)
# ============================================
elif pantalla_actual == "Proveedores":
    st.title("Facturación de Proveedores")
    st.info("🚀 Pantalla en desarrollo para el PASO 5")
