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
    initial_sidebar_state="collapsed",
    theme="light"  # Fuerza tema claro en celular
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
    
    /* Reducir padding general */
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
    
    .metric-box {
        background-color: #1E3A8A;
        color: white;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        margin: 5px 0;
    }
    
    .metric-title {
        font-size: 11px;
        opacity: 0.9;
        margin-bottom: 4px;
    }
    
    .metric-value {
        font-size: 20px;
        font-weight: bold;
        margin: 3px 0;
    }
    
    .metric-subtitle {
        font-size: 10px;
        opacity: 0.85;
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
    
    /* Ocultar decoraciones innecesarias */
    .stMetric {
        background-color: transparent;
        padding: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# CARGAR DATOS
# ============================================
@st.cache_data
def cargar_datos():
    response = requests.get(URL, timeout=10)
    archivo_excel = BytesIO(response.content)
    
    datos = {}
    excel_file = pd.ExcelFile(archivo_excel)
    
    for pestaña in excel_file.sheet_names:
        datos[pestaña] = pd.read_excel(archivo_excel, sheet_name=pestaña)
    
    return datos

datos = cargar_datos()

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

# Encontrar fila 19 (índice 18 en pandas, que es después del header)
# La fila 19 es la última con los totales
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
# ENCABEZADO (SIN HALCÓN)
# ============================================
st.title("Hawk - Reportes Internos")

# ============================================
# BLOQUE 1: MÉTRICAS DE JUNIO
# ============================================
st.write("**Junio 2026**")

col1, col2, col3, col4 = st.columns(4)

if junio is not None:
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Garantías</div>
            <div class="metric-value">{int(junio.iloc[7]):,}</div>
            <div class="metric-subtitle">Cantidad</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Garantías</div>
            <div class="metric-value">${junio.iloc[8]:,.0f}</div>
            <div class="metric-subtitle">Premio</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Asistencias</div>
            <div class="metric-value">{int(junio.iloc[10]):,}</div>
            <div class="metric-subtitle">Cantidad</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Asistencias</div>
            <div class="metric-value">${junio.iloc[11]:,.0f}</div>
            <div class="metric-subtitle">Premio</div>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# BLOQUE 2: COMERCIOS FALTANTES
# ============================================
st.write("**Estado de Emisión**")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total", total_comercios, delta=None)

with col2:
    st.metric("Pendientes", f"{pendientes_emitir} ⚠️", delta=None)

with col3:
    st.metric("Emitidos", f"{ya_emitidos} ✅", delta=None)

with col4:
    st.metric("Promedio", f"${promedio_ventas_pendientes:,.0f}", delta=None)

# ============================================
# BLOQUE 3: VENTAS PENDIENTES DE INFORMAR
# ============================================
st.write("**Ventas Pendientes**")

for comercio, datos_comercio in comercios_pendientes.items():
    if datos_comercio['meses_pendientes']:  # Solo mostrar si hay meses pendientes
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
