import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ============================================
# CONFIGURACIÓN
# ============================================
st.set_page_config(
    page_title="🦅 Hawk - Reportes",
    layout="wide",
    initial_sidebar_state="collapsed"
)

GOOGLE_DRIVE_ID = "1gZPD9XUspcN8e4FGrgdEl1AacDew68RU"
URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_DRIVE_ID}/export?format=xlsx"

# ============================================
# ESTILOS CORPORATIVOS
# ============================================
st.markdown("""
<style>
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    body {
        background-color: #FFFFFF;
    }
    .metric-box {
        background-color: #1E3A8A;
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    .metric-title {
        font-size: 14px;
        opacity: 0.9;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        margin: 5px 0;
    }
    .metric-subtitle {
        font-size: 12px;
        opacity: 0.85;
    }
    .alert-card {
        background-color: #1E3A8A;
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .alert-title {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .alert-content {
        font-size: 14px;
        line-height: 1.6;
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

# Encontrar filas de Mayo y Junio
def obtener_fila_mes(df, mes_nombre):
    """Encuentra la fila que contiene el mes especificado"""
    for idx, row in df.iterrows():
        if str(row.iloc[3]).strip().lower() == mes_nombre.lower():
            return row
    return None

mayo = obtener_fila_mes(df_resumen, "Mayo")
junio = obtener_fila_mes(df_resumen, "Junio")

# Índices de columnas (basado en estructura)
# TOTAL: Cant=4, Premio=5, Costo=6
# GARANTIAS: Cant=7, Premio=8, Costo=9
# ASISTENCIAS: Cant=10, Premio=11, Costo=12

# ============================================
# PROCESAR DATOS COMERCIOS
# ============================================
df_comercios = datos['Comercios']

# Buscar los valores en J2, J3, J4, K3
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

# Encontrar comercios y sus meses pendientes
comercios_pendientes = {}

# Columnas de comercios en la pestaña: PARDO (3-6), DRICCO (7-10), SENSEI (11-14)
comercios_cols = {
    'PARDO': {'cant': 3, 'ge': 4, 'cant_ass': 5, 'ass': 6},
    'DRICCO': {'cant': 7, 'ge': 8, 'cant_ass': 9, 'ass': 10},
    'SENSEI': {'cant': 11, 'ge': 12, 'cant_ass': 13, 'ass': 14}
}

meses_orden = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio"]

for comercio, cols in comercios_cols.items():
    comercios_pendientes[comercio] = {
        'meses_pendientes': [],
        'total_pendiente': 0
    }
    
    # Buscar meses con datos
    for idx, row in df_pendiente.iterrows():
        mes = str(row.iloc[2]).strip()
        
        if mes in meses_orden:
            # Verificar si hay datos (no NaN y no 0)
            cant_val = row.iloc[cols['cant']]
            if pd.notna(cant_val) and cant_val != 0:
                comercios_pendientes[comercio]['meses_pendientes'].append(mes)
    
    # Obtener total de la fila 19 (última fila con totales)
    if len(df_pendiente) >= 19:
        fila_total = df_pendiente.iloc[-1]  # Última fila
        total_cant = fila_total.iloc[cols['cant']]
        if pd.notna(total_cant):
            comercios_pendientes[comercio]['total_pendiente'] = total_cant

# ============================================
# ENCABEZADO
# ============================================
st.title("🦅 Hawk - Reportes Internos")
st.markdown("---")

# ============================================
# BLOQUE 1: MÉTRICAS DE JUNIO VS MAYO
# ============================================
st.write("### 📊 Resumen Ejecutivo - Junio 2026")

col1, col2, col3, col4 = st.columns(4)

if junio is not None:
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Garantías (Cantidad)</div>
            <div class="metric-value">{int(junio.iloc[7]):,}</div>
            <div class="metric-subtitle">Junio 2026</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Garantías (Premio)</div>
            <div class="metric-value">${junio.iloc[8]:,.0f}</div>
            <div class="metric-subtitle">Valor total</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Asistencias (Cantidad)</div>
            <div class="metric-value">{int(junio.iloc[10]):,}</div>
            <div class="metric-subtitle">Junio 2026</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-title">Asistencias (Premio)</div>
            <div class="metric-value">${junio.iloc[11]:,.0f}</div>
            <div class="metric-subtitle">Valor total</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ============================================
# BLOQUE 2: COMERCIOS FALTANTES
# ============================================
st.write("### 📋 Estado de Emisión - Junio")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total de Comercios", value=total_comercios)

with col2:
    st.metric(label="Pendientes de Emitir", value=f"{pendientes_emitir} ⚠️")

with col3:
    st.metric(label="Ya Emitidos", value=f"{ya_emitidos} ✅")

with col4:
    st.metric(label="Promedio Pendiente", value=f"${promedio_ventas_pendientes:,.0f}")

st.markdown("---")

# ============================================
# BLOQUE 3: VENTAS PENDIENTES DE INFORMAR
# ============================================
st.write("### 📌 Ventas Pendientes de Informar")

for comercio, datos_comercio in comercios_pendientes.items():
    if datos_comercio['meses_pendientes']:  # Solo mostrar si hay meses pendientes
        meses_str = ", ".join(datos_comercio['meses_pendientes'])
        st.markdown(f"""
        <div class="alert-card">
            <div class="alert-title">🔴 {comercio}</div>
            <div class="alert-content">
                <strong>Meses Pendientes:</strong> {meses_str}<br>
                <strong>Total Pendiente:</strong> ${datos_comercio['total_pendiente']:,.0f}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.success("✅ Datos cargados exitosamente desde Google Drive")
