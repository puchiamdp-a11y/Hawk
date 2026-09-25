import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# Import defensivo: si falta una dependencia (ej. psycopg2 recién agregado
# a requirements.txt y todavía no instalado en el servidor) o la base de
# SYNA no está configurada, esto NO debe tirar abajo el resto de Hawk
# (Zeus, emisión, etc.) - solo la pantalla de Cobranzas SYNA debe verse
# afectada.
try:
    from syna_db import inicializar_db
    from syna_ui import pantalla_syna_admin, pantalla_syna_viewer, pantalla_syna_con_autenticacion
    _SYNA_IMPORT_ERROR = None
except Exception as _e:
    _SYNA_IMPORT_ERROR = _e

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
    :root{
        --ink:#0B0F19; --ink-soft:#232838; --muted:#6B7280; --faint:#9CA3AF;
        --primary:#2E5CFF; --primary-2:#7B61FF; --cyan:#00C2FF;
        --bg:#F5F7FC; --white:#FFFFFF; --line:#E7EAF3; --line-soft:#EEF1F8;
        --success:#12B76A; --success-bg:#E7F9EF; --success-ink:#0A8F53;
        --danger:#F5384E; --danger-bg:#FDEAEC; --danger-ink:#C81E3A;
        --warning:#FF9F0A; --warning-bg:#FFF4E0; --warning-ink:#B26B00;
        --grad-hero: linear-gradient(135deg,#2E5CFF 0%,#6A4CFF 55%,#00C2FF 100%);
        --grad-icon: linear-gradient(135deg,#2E5CFF,#7B61FF);
        --shadow-sm: 0 2px 8px rgba(16,24,64,.06);
        --shadow-md: 0 10px 28px rgba(16,24,64,.10);
    }

    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    body, .stApp {
        background-color: var(--bg) !important;
        background-image:
            radial-gradient(900px 420px at 92% -8%, rgba(123,97,255,.10), transparent 60%),
            radial-gradient(700px 360px at -4% 8%, rgba(46,92,255,.08), transparent 55%) !important;
        color: var(--ink);
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

    /* HERO (título principal de cada pantalla) */
    .hawk-hero {
        border-radius: 22px;
        padding: 26px 30px;
        margin: 4px 0 22px 0;
        background: var(--grad-hero);
        box-shadow: 0 20px 48px rgba(46,92,255,.30);
        position: relative;
        overflow: hidden;
    }
    .hawk-hero::before {
        content: "";
        position: absolute; top: -60px; right: -40px; width: 220px; height: 220px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(255,255,255,.16), transparent 70%);
    }
    .hawk-hero::after {
        content: "";
        position: absolute; bottom: -90px; left: 30%; width: 200px; height: 200px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(0,194,255,.20), transparent 70%);
    }
    .hawk-hero-kicker {
        position: relative;
        font-size: 11px; font-weight: 700; color: rgba(255,255,255,.8);
        text-transform: uppercase; letter-spacing: .8px;
    }
    .hawk-hero-title {
        position: relative;
        margin: 6px 0 0 0; font-size: 25px; font-weight: 700; color: #fff; letter-spacing: -.4px;
    }
    .hawk-hero-subtitle {
        position: relative;
        font-size: 13px; color: rgba(255,255,255,.85); margin-top: 6px; max-width: 640px;
    }
    .hawk-header {
        margin: 4px 0 22px 0;
    }
    .hawk-header h1 {
        margin: 0 !important; font-size: 26px !important; font-weight: 700 !important;
        color: var(--ink) !important; letter-spacing: -.4px;
    }
    .hawk-header .hawk-header-subtitle {
        font-size: 13.5px; color: var(--muted); margin-top: 5px; font-weight: 500;
    }

    /* Card genérica reutilizable, estilo Blister Assist */
    .card {
        background: var(--white);
        border: 1px solid var(--line-soft);
        border-radius: 18px;
        box-shadow: var(--shadow-sm);
    }
    .icon-chip {
        width: 38px; height: 38px; border-radius: 11px;
        display: flex; align-items: center; justify-content: center; flex-shrink: 0;
        box-shadow: 0 6px 14px rgba(46,92,255,.24);
        font-size: 18px;
    }
    .stat-label {
        font-size: 11px; font-weight: 700; color: var(--muted);
        text-transform: uppercase; letter-spacing: .6px;
    }
    .stat-grad {
        font-weight: 800;
        background: var(--grad-icon);
        -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
    }

    .metrics-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 8px;
        margin: 10px 0;
    }

    .metric-box {
        background: var(--grad-icon);
        color: white;
        padding: 14px;
        border-radius: 14px;
        text-align: center;
        box-shadow: var(--shadow-sm);
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
        background: var(--white);
        border: 1px solid var(--line-soft);
        border-radius: 18px;
        box-shadow: var(--shadow-sm);
        overflow: hidden;
    }

    .emission-cell {
        padding: 16px;
        border-right: 1px solid var(--line-soft);
        border-bottom: 1px solid var(--line-soft);
        text-align: center;
    }

    .emission-cell:nth-child(2n) {
        border-right: none;
    }

    .emission-cell:nth-last-child(-n+2) {
        border-bottom: none;
    }

    .emission-label {
        font-size: 11px;
        font-weight: 700;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: .5px;
        margin-bottom: 8px;
    }

    .emission-value {
        font-size: 30px;
        font-weight: 800;
        color: var(--ink);
        font-variant-numeric: tabular-nums;
    }

    .alert-card {
        background: var(--grad-icon);
        color: white;
        padding: 12px;
        border-radius: 12px;
        margin: 8px 0;
        box-shadow: var(--shadow-sm);
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
    /* TARJETAS DE INFORMACIÓN - CLIENTES VIP / KPIs */
    .info-card {
        background: var(--white);
        color: var(--ink);
        padding: 20px;
        border-radius: 18px;
        margin-bottom: 20px;
        border: 1px solid var(--line-soft);
        box-shadow: var(--shadow-sm);
    }

    .info-card h3 {
        color: var(--ink) !important;
        margin-top: 0 !important;
        font-size: 15px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: .5px;
    }

    .info-row {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 15px;
        margin-bottom: 15px;
    }

    .info-item {
        background: linear-gradient(160deg,#F0F3FF,#fff);
        padding: 12px 14px;
        border-radius: 11px;
        border: 1px solid var(--line-soft);
        border-left: 3px solid var(--primary-2);
        box-shadow: var(--shadow-sm);
    }

    .info-label {
        font-size: 11px;
        color: var(--muted);
        margin-bottom: 5px;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: .5px;
    }

    .info-value {
        font-size: 16px;
        font-weight: 700;
        color: var(--ink);
        font-variant-numeric: tabular-nums;
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
        width: 210px !important;
        background-color: var(--white) !important;
        border-right: 1px solid var(--line-soft);
    }

    [data-testid="stSidebarContent"] {
        width: 210px !important;
    }

    .stButton {
        width: 100% !important;
    }

   .stButton > button {
        width: 100%;
        height: auto !important;
        font-size: 13.5px !important;
        font-weight: 600 !important;
        padding: 10px 13px !important;
        border-radius: 12px !important;
        background-color: transparent !important;
        color: var(--ink-soft) !important;
        border: none !important;
        margin-bottom: 4px !important;
        transition: background .2s ease, transform .2s ease !important;
        box-shadow: none !important;
        text-align: left;
    }

    .stButton > button:hover {
        color: var(--primary) !important;
        background-color: #F0F3FF !important;
        transform: translateX(2px) !important;
        border: none !important;
    }

    .stButton > button:active,
    .stButton > button:focus:not(:hover) {
        color: #fff !important;
        background: var(--grad-icon) !important;
        box-shadow: 0 8px 18px rgba(46,92,255,.32) !important;
    }
     /* TARJETAS DE SECCIONES */
    .section-card {
        background: var(--white);
        color: var(--ink);
        padding: 18px 20px;
        border-radius: 18px;
        margin-bottom: 15px;
        border: 1px solid var(--line-soft);
        border-left: 3px solid var(--primary);
        box-shadow: var(--shadow-sm);
    }

    .section-title {
        font-size: 16px;
        font-weight: 800;
        color: var(--ink) !important;
        margin: 0 !important;
        text-transform: uppercase;
        letter-spacing: .4px;
    }

    .section-title-simple {
        font-size: 18px;
        font-weight: bold;
        color: var(--ink) !important;
        margin: 15px 0 !important;
        padding: 0 !important;
        background: none !important;
    }

    .section-divider {
        border: none;
        border-top: 1px solid var(--line-soft);
        margin: 26px 0 20px 0;
    }

    .alert-container {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin: 12px 0;
    }

    .alert-card-inline {
        background: var(--white);
        color: var(--ink);
        padding: 12px 16px;
        border-radius: 12px;
        border: 1px solid var(--line-soft);
        border-left: 3px solid var(--warning);
        box-shadow: var(--shadow-sm);
        flex: 0 1 auto;
        min-width: fit-content;
        width: auto;
    }

    .alert-title-inline {
        font-size: 14px;
        font-weight: 700;
        margin-bottom: 6px;
        color: var(--ink);
    }

    .alert-content-inline {
        font-size: 12px;
        line-height: 1.5;
        color: var(--muted);
    }

    .resumen-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
        font-size: 13px;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: var(--shadow-sm);
    }

    .resumen-table td, .resumen-table th {
        padding: 10px;
        text-align: right;
        border: 1px solid var(--line-soft);
    }

    .resumen-table th {
        font-weight: 700;
        color: white;
        text-align: center;
        text-transform: uppercase;
        letter-spacing: .3px;
        font-size: 11px;
    }

    .resumen-table td:first-child, .resumen-table th:first-child {
        text-align: left;
    }

    .resumen-header-garantias {
        background: linear-gradient(90deg,#0F9D58,#12B76A);
        color: white;
    }

    .resumen-header-asistencias {
        background: linear-gradient(90deg,#2E5CFF,#7B61FF);
        color: white;
    }

    .resumen-header-total {
        background: linear-gradient(90deg,#12183099,#2E5CFF);
        color: white;
    }

    .resumen-row-garantias {
        background-color: var(--success-bg);
    }

    .resumen-row-asistencias {
        background-color: var(--warning-bg);
    }

    .resumen-row-total {
        background-color: #F0F3FF;
    }

    .resumen-cant {
        font-weight: bold;
    }

    .resumen-premio {
        font-weight: bold;
    }

    .provider-header {
        background: #F0F3FF;
        border: 1px solid var(--line-soft);
        border-left: 4px solid var(--primary);
        padding: 14px;
        border-radius: 12px;
        margin-bottom: 12px;
        margin-top: 20px;
        box-shadow: var(--shadow-sm);
    }

    .provider-header h4 {
        color: var(--primary) !important;
        margin: 0 !important;
    }

    /* OPTIMIZAR ESPACIADO DE COLUMNAS EN TABLAS */
    [data-testid="dataFrame"] {
        width: 100% !important;
    }

    [data-testid="dataFrame"] td {
        padding: 8px 4px !important;
    }

    [data-testid="dataFrame"] th {
        padding: 8px 4px !important;
    }

    .stDataFrame {
        width: 100% !important;
    }

    .stDataFrame > div {
        width: 100% !important;
    }

    /* ESTILOS PARA EXPANDERS COMPACTOS Y CENTRADOS */
    /* Aumentar tamaño del expander y su label */
    [data-testid="stExpander"] {
        margin: 8px 0 !important;
        padding: 0 !important;
        width: 100% !important;
    }

    [data-testid="stExpander"] summary {
        font-size: 16px !important;
        font-weight: bold !important;
        padding: 12px !important;
    }

    /* Reducir espaciado dentro de expanders */
    [data-testid="expanderContent"] {
        padding: 8px 0 !important;
        margin: 0 !important;
    }

    /* Centrar valores numéricos en dataframes - selectores más específicos */
    div[data-testid="dataFrame"] table td,
    div[data-testid="dataFrame"] table th {
        text-align: center !important;
        padding: 6px 4px !important;
    }

    /* Alineación especial para primera columna (Mes) - a la izquierda */
    div[data-testid="dataFrame"] table td:first-child,
    div[data-testid="dataFrame"] table th:first-child {
        text-align: left !important;
    }

    /* Asegurar que todas las celdas estén centradas */
    [role="gridcell"] {
        text-align: center !important;
    }

    [role="columnheader"] {
        text-align: center !important;
    }

    /* Primera columna siempre a la izquierda */
    [role="row"] > [role="gridcell"]:first-child,
    [role="row"] > [role="columnheader"]:first-child {
        text-align: left !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# DETECTAR ROL (ADMIN vs VIEWER)
# ============================================
query_params = st.query_params
if query_params.get("role") == "viewer":
    # Modo Cintia (viewer) - SOLO BALANCE
    if _SYNA_IMPORT_ERROR is not None:
        st.error(f"No se pudo cargar el módulo SYNA: {_SYNA_IMPORT_ERROR}")
        st.stop()

    try:
        inicializar_db()
    except Exception as _e:
        st.error(f"No se pudo conectar a la base de datos de SYNA: {_e}")
        st.stop()

    if "syna_authenticated" not in st.session_state:
        st.session_state.syna_authenticated = False

    if not st.session_state.syna_authenticated:
        pantalla_syna_con_autenticacion()
        st.stop()
    else:
        # Usuario autenticado - mostrar SOLO tab balance
        pantalla_syna_viewer()
        st.stop()

# ============================================
# CARGAR DATOS (CON CACHE OPTIMIZADO)
# ============================================
import time
from datetime import datetime

@st.cache_data(ttl=300)  # Cache de 5 minutos (antes era 1 hora)
def cargar_datos():
    """Carga datos frescos de Google Drive (con cache de 5 min)"""
    response = requests.get(URL, timeout=10)
    archivo_excel = BytesIO(response.content)

    datos = {}
    excel_file = pd.ExcelFile(archivo_excel)

    for pestaña in excel_file.sheet_names:
        datos[pestaña] = pd.read_excel(archivo_excel, sheet_name=pestaña)

    return datos

# Inicializar session state para el timestamp
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = datetime.now()

datos = cargar_datos()

# Actualizar timestamp después de cargar los datos
if st.session_state.get('force_refresh', False):
    st.session_state.last_update_time = datetime.now()
    st.session_state.force_refresh = False

# ============================================
# SELECTOR DE PANTALLA (SIDEBAR COMPACTO)
# ============================================
with st.sidebar:
    st.write("")
    st.write("")
    
    if "pantalla_actual" not in st.session_state:
        st.session_state.pantalla_actual = "Resumen Ejecutivo"

    if st.button("Resumen", key="btn_resumen", use_container_width=True):
        st.session_state.pantalla_actual = "Resumen Ejecutivo"

    if st.button("Fichas", key="btn_vip", use_container_width=True):
        st.session_state.pantalla_actual = "Fichas VIP"

    if st.button("Costos Sancor", key="btn_costos", use_container_width=True):
        st.session_state.pantalla_actual = "Machete Costos"

    if st.button("Proveedores", key="btn_prov", use_container_width=True):
        st.session_state.pantalla_actual = "Proveedores"

    if st.button("Post Emisión", key="btn_post_emision", use_container_width=True):
        st.session_state.pantalla_actual = "Post Emisión"

    if st.button("Cobranzas SYNA", key="btn_syna", use_container_width=True):
        st.session_state.pantalla_actual = "Cobranzas SYNA"

    st.write("")
    st.markdown("---")
    st.write("")

    # Mostrar timestamp de última actualización
    last_update = st.session_state.last_update_time
    time_since_update = (datetime.now() - last_update).total_seconds()

    if time_since_update < 60:
        time_text = "Hace unos segundos"
    elif time_since_update < 3600:
        mins = int(time_since_update // 60)
        time_text = f"Hace {mins} min"
    else:
        hours = int(time_since_update // 3600)
        time_text = f"Hace {hours}h"

    st.caption(f"📅 {time_text}")

    if st.button("🔄 Actualizar", key="btn_refresh", use_container_width=True, help="Actualizar datos ahora de Google Sheets"):
        st.cache_data.clear()
        st.session_state.force_refresh = True
        st.rerun()

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

def obtener_ultima_fila_con_datos(df, col_indice=4):
    """Encuentra la última fila con valor > 0 en la columna especificada (Costo Total - columna E, índice 4)"""
    for idx in range(len(df) - 1, -1, -1):
        try:
            valor = pd.to_numeric(df.iloc[idx, col_indice], errors='coerce')
            if pd.notna(valor) and valor > 0:
                return df.iloc[idx]
        except:
            continue
    return None

ultima_fila_resumen = obtener_ultima_fila_con_datos(df_resumen)

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

meses_orden = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

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
if "Post Emision" in datos:
    df_general = datos['Post Emision']

    # Estructura de columnas:
    # B: Meses, C: GESA Cant, D: GESA Premio, E: GESA IVA, F: GESA Sellos
    # G: BLISTER Cant, H: BLISTER Premio, I: BLISTER IVA, J: BLISTER Sellos
    # K: Total Cant, L: Total Premio, M: Ajustes
    meses_validos = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    for idx, row in df_general.iterrows():
        mes = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""

        if mes in meses_validos:
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

    # Obtener el último mes con datos (último que tenga valor en columna L - Total)
    ultimo_mes = None
    ultima_fila_datos = None

    if "Post Emision" in datos:
        df_general = datos['Post Emision']
        # Buscar la última fila que tenga datos en la columna L (índice 11 - Total)
        for idx in range(len(df_general) - 1, -1, -1):
            row = df_general.iloc[idx]
            total_value = pd.to_numeric(row.iloc[11], errors='coerce') if pd.notna(row.iloc[11]) else 0
            if total_value > 0:  # Última fila con datos
                mes = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                if mes in meses_validos:
                    ultimo_mes = mes
                    ultima_fila_datos = row
                    break

# ============================================
# PANTALLA 1: RESUMEN EJECUTIVO
# ============================================
if pantalla_actual == "Resumen Ejecutivo":
    st.markdown("""
    <div class="hawk-hero">
        <div class="hawk-hero-kicker">Reportes internos</div>
        <h1 class="hawk-hero-title">Hawk — Resumen Ejecutivo</h1>
        <div class="hawk-hero-subtitle">Vista consolidada de Garantías, Asistencias y estado de emisión del mes.</div>
    </div>
    """, unsafe_allow_html=True)

    # BLOQUE 4: RESUMEN - MES ACTUAL (PRIMERO)
    if ultima_fila_resumen is not None:
        try:
            # Estructura de la hoja Resumen:
            # B=Mes, C-E=TOTAL(Cant,Premio,Costo), F-H=GARANTIAS(Cant,Premio,Costo), I-K=ASISTENCIAS(Cant,Premio,Costo)
            # Índices (0-based): 1=Mes, 2-4=TOTAL, 5-7=GARANTIAS, 8-10=ASISTENCIAS

            mes_resumen = str(ultima_fila_resumen.iloc[1]).strip() if pd.notna(ultima_fila_resumen.iloc[1]) else "Mes"

            # TOTAL: índices 2, 3 (Cantidad, Premio)
            total_cant = int(pd.to_numeric(ultima_fila_resumen.iloc[2], errors='coerce') or 0)
            total_premio = float(pd.to_numeric(ultima_fila_resumen.iloc[3], errors='coerce') or 0)

            # GARANTÍAS: índices 5, 6 (Cantidad, Premio)
            garantias_cant = int(pd.to_numeric(ultima_fila_resumen.iloc[5], errors='coerce') or 0)
            garantias_premio = float(pd.to_numeric(ultima_fila_resumen.iloc[6], errors='coerce') or 0)

            # ASISTENCIAS: índices 8, 9 (Cantidad, Premio)
            asistencias_cant = int(pd.to_numeric(ultima_fila_resumen.iloc[8], errors='coerce') or 0)
            asistencias_premio = float(pd.to_numeric(ultima_fila_resumen.iloc[9], errors='coerce') or 0)

            # TÍTULO CON MES - CON LÍNEA DIVISORIA
            st.write(f"**📊 Resumen - Mes Actual ({mes_resumen})**")

            # TARJETAS EN 3 COLUMNAS
            col1, col2, col3 = st.columns(3)

            # GARANTÍAS
            with col1:
                st.markdown(f"""
                <div class="card" style="padding: 22px 24px;">
                    <div class="icon-chip" style="background: linear-gradient(135deg,#12B76A,#3DD68C); margin-bottom: 14px;">🛡️</div>
                    <div class="stat-label">Garantías · cantidad</div>
                    <div style="font-size: 27px; font-weight: 800; margin-top: 6px; font-variant-numeric: tabular-nums;">{garantias_cant:,}</div>
                    <div style="height: 1px; background: var(--line-soft); margin: 14px 0;"></div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <span style="font-size: 11px; color: var(--muted); font-weight: 600;">Premio</span>
                        <span class="stat-grad" style="font-size: 17px; font-variant-numeric: tabular-nums;">${garantias_premio:,.0f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # ASISTENCIAS
            with col2:
                st.markdown(f"""
                <div class="card" style="padding: 22px 24px;">
                    <div class="icon-chip" style="background: var(--grad-icon); margin-bottom: 14px;">📞</div>
                    <div class="stat-label">Asistencias · cantidad</div>
                    <div style="font-size: 27px; font-weight: 800; margin-top: 6px; font-variant-numeric: tabular-nums;">{asistencias_cant:,}</div>
                    <div style="height: 1px; background: var(--line-soft); margin: 14px 0;"></div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <span style="font-size: 11px; color: var(--muted); font-weight: 600;">Premio</span>
                        <span class="stat-grad" style="font-size: 17px; font-variant-numeric: tabular-nums;">${asistencias_premio:,.0f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # TOTAL
            with col3:
                st.markdown(f"""
                <div class="card" style="padding: 22px 24px; background: linear-gradient(160deg,#fff,#F5F7FF);">
                    <div class="icon-chip" style="background: linear-gradient(135deg,#0B0F19,#3D4560); margin-bottom: 14px;">📈</div>
                    <div class="stat-label">Total · cantidad</div>
                    <div style="font-size: 27px; font-weight: 800; margin-top: 6px; font-variant-numeric: tabular-nums;">{total_cant:,}</div>
                    <div style="height: 1px; background: var(--line-soft); margin: 14px 0;"></div>
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <span style="font-size: 11px; color: var(--muted); font-weight: 600;">Premio</span>
                        <span class="stat-grad" style="font-size: 18px; font-variant-numeric: tabular-nums;">${total_premio:,.0f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        except (ValueError, IndexError) as e:
            st.warning(f"⚠️ Error al procesar datos de resumen: {e}")

    # BLOQUE 3: VENTAS SIN INFORMAR (SEGUNDO)
    st.markdown("""
    <div class="section-divider"></div>
    """, unsafe_allow_html=True)
    st.write("**Ventas sin informar**")

    # Construir todas las tarjetas en un contenedor flex
    tarjetas_html = '<div class="alert-container">'
    for comercio, datos_comercio in comercios_pendientes.items():
        if datos_comercio['meses_pendientes']:
            meses_str = ", ".join(datos_comercio['meses_pendientes'])
            certs = int(pd.to_numeric(datos_comercio['certificados'], errors='coerce') or 0)
            premio = float(pd.to_numeric(datos_comercio['premio'], errors='coerce') or 0)
            tarjetas_html += f'<div class="alert-card-inline"><div class="alert-title-inline">{comercio}</div><div class="alert-content-inline"><strong>Meses:</strong> {meses_str}<br><strong>Cert:</strong> {certs:,} | <strong>Premio:</strong> ${premio:,.2f}</div></div>'
    tarjetas_html += '</div>'
    st.markdown(tarjetas_html, unsafe_allow_html=True)

    # BLOQUE 2: ESTADO DE EMISIÓN (TERCERO)
    st.markdown("""
    <div class="section-divider"></div>
    """, unsafe_allow_html=True)
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

    st.markdown("---")
    last_update = st.session_state.last_update_time
    formatted_time = last_update.strftime("%H:%M:%S")
    st.caption(f"✅ Última actualización: {formatted_time} | Próxima auto-actualización en ~5 min")

    # TABLA COMPLETA - HISTÓRICO DE MESES
    st.markdown("""
    <div class="section-divider"></div>
    """, unsafe_allow_html=True)
    st.write("**📅 Histórico de Meses**")

    try:
        # Extraer datos de todas las filas hasta la última con valor > 0 en columna D
        ultima_fila_idx = 0
        for idx in range(len(df_resumen) - 1, -1, -1):
            try:
                valor = pd.to_numeric(df_resumen.iloc[idx, 3], errors='coerce')
                if pd.notna(valor) and valor > 0:
                    ultima_fila_idx = idx
                    break
            except:
                continue

        # Construir tabla HTML
        tabla_html = '<table class="resumen-table">'

        # Encabezados principales
        tabla_html += '<tr>'
        tabla_html += '<th style="text-align: left;">Mes</th>'
        tabla_html += '<th colspan="3" class="resumen-header-garantias">GARANTÍAS</th>'
        tabla_html += '<th colspan="3" class="resumen-header-asistencias">ASISTENCIAS</th>'
        tabla_html += '<th colspan="3" class="resumen-header-total">TOTAL</th>'
        tabla_html += '</tr>'

        # Sub-encabezados
        tabla_html += '<tr>'
        tabla_html += '<th style="text-align: left;"></th>'
        tabla_html += '<th class="resumen-header-garantias">Cant</th>'
        tabla_html += '<th class="resumen-header-garantias">Premio</th>'
        tabla_html += '<th class="resumen-header-garantias">Costo</th>'
        tabla_html += '<th class="resumen-header-asistencias">Cant</th>'
        tabla_html += '<th class="resumen-header-asistencias">Premio</th>'
        tabla_html += '<th class="resumen-header-asistencias">Costo</th>'
        tabla_html += '<th class="resumen-header-total">Cant</th>'
        tabla_html += '<th class="resumen-header-total">Premio</th>'
        tabla_html += '<th class="resumen-header-total">Costo</th>'
        tabla_html += '</tr>'

        # Filas de datos
        for idx in range(1, ultima_fila_idx + 1):  # Empezar desde 1 para saltar encabezado
            fila = df_resumen.iloc[idx]
            mes = str(fila.iloc[1]).strip() if pd.notna(fila.iloc[1]) else ""
            if mes and mes.lower() != "mes":
                # Garantías
                gtr_cant = int(pd.to_numeric(fila.iloc[5], errors='coerce') or 0)
                gtr_premio = float(pd.to_numeric(fila.iloc[6], errors='coerce') or 0)
                gtr_costo = float(pd.to_numeric(fila.iloc[7], errors='coerce') or 0)

                # Asistencias
                ast_cant = int(pd.to_numeric(fila.iloc[8], errors='coerce') or 0)
                ast_premio = float(pd.to_numeric(fila.iloc[9], errors='coerce') or 0)
                ast_costo = float(pd.to_numeric(fila.iloc[10], errors='coerce') or 0)

                # Total
                tot_cant = int(pd.to_numeric(fila.iloc[2], errors='coerce') or 0)
                tot_premio = float(pd.to_numeric(fila.iloc[3], errors='coerce') or 0)
                tot_costo = float(pd.to_numeric(fila.iloc[4], errors='coerce') or 0)

                tabla_html += '<tr>'
                tabla_html += f'<td style="text-align: left; font-weight: bold;">{mes}</td>'
                tabla_html += f'<td class="resumen-row-garantias resumen-cant">{gtr_cant:,.0f}</td>'
                tabla_html += f'<td class="resumen-row-garantias resumen-premio">${gtr_premio:,.2f}</td>'
                tabla_html += f'<td class="resumen-row-garantias">${gtr_costo:,.2f}</td>'
                tabla_html += f'<td class="resumen-row-asistencias resumen-cant">{ast_cant:,.0f}</td>'
                tabla_html += f'<td class="resumen-row-asistencias resumen-premio">${ast_premio:,.2f}</td>'
                tabla_html += f'<td class="resumen-row-asistencias">${ast_costo:,.2f}</td>'
                tabla_html += f'<td class="resumen-row-total resumen-cant">{tot_cant:,.0f}</td>'
                tabla_html += f'<td class="resumen-row-total resumen-premio">${tot_premio:,.2f}</td>'
                tabla_html += f'<td class="resumen-row-total">${tot_costo:,.2f}</td>'
                tabla_html += '</tr>'

        tabla_html += '</table>'
        st.markdown(tabla_html, unsafe_allow_html=True)

    except (ValueError, IndexError) as e:
        st.warning(f"⚠️ Error al procesar tabla histórica: {e}")

# ============================================
# PANTALLA 2: FICHAS VIP CON TABS
# ============================================
# GUÍA DE ESTÉTICA PARA FICHAS
# Al crear nuevas fichas, aplicar los siguientes colores desaturados:
# - Encabezados de CATEGORÍAS (Asistencias, Garantías): Azul suave #9DBDD9
#   st.markdown("<div style='background-color: #9DBDD9; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>Nombre Categoría</b></div>", unsafe_allow_html=True)
# - Encabezados de TOTALES (Total, Total Gral, etc): Naranja suave #E0C9B0
#   st.markdown("<div style='background-color: #E0C9B0; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>Nombre Total</b></div>", unsafe_allow_html=True)
# - Separadores entre columnas: 3px solid borders (#1E3A8A para datos, #FF6B00 para totales)
# ============================================
elif pantalla_actual == "Fichas VIP":
    st.markdown("""
    <div class="hawk-header">
        <h1>Fichas de Clientes VIP</h1>
        <div class="hawk-header-subtitle">Datos comerciales y facturación por cliente</div>
    </div>
    """, unsafe_allow_html=True)

    clientes_vip = {
        "SYNA": "FC SYNA",
        "BAZAR": "FC BAZAR",
        "TOYOS": "FC TOYOS",
        "LAS MALVINAS": "FC Las malvinas",
        "CASA REIG": "FC Casa Reig",
        "DRICCO": "FC DRICCO",
        "SENSEI": "FC SENSEI"
    }
    
    tabs = st.tabs([f"📌 {cliente}" for cliente in clientes_vip.keys()])
    
    for tab, (cliente, pestaña_fc) in zip(tabs, clientes_vip.items()):
        with tab:
            if pestaña_fc in datos:
                df_cliente = datos[pestaña_fc]
                st.write(f"## {cliente}")
                
                # INFORMACIÓN ADICIONAL - Rango varía según cliente
                st.write("### 📋 Información del Cliente")

                # Las Malvinas tiene información desde B13 (iloc 12), otros desde B18 (iloc 17)
                if cliente == "LAS MALVINAS":
                    info_rows = df_cliente.iloc[12:18]
                else:
                    info_rows = df_cliente.iloc[17:24]

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

                # Extraer datos mensuales (movido 2 filas hacia abajo)
                df_datos = df_cliente.iloc[5:12].copy()
                df_datos = df_datos.dropna(subset=['Unnamed: 1'], how='all')
                
                if cliente == "TOYOS":
                    st.markdown("<h3 style='background-color: #9DBDD9; padding: 10px; border-radius: 5px; margin-bottom: 10px; margin-top: 0;'>📊 Garantías - Ventas Mensuales</h3>", unsafe_allow_html=True)

                    df_table = df_datos[['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3']].copy()
                    df_table.columns = ['Mes', 'GAR_Cant', 'GAR_Premio']
                    df_table = df_table[df_table['Mes'].notna()]

                    df_display = df_table.copy()
                    df_display['GAR_Cant'] = pd.to_numeric(df_display['GAR_Cant'], errors='coerce').fillna(0).astype(int)
                    df_display['GAR_Premio'] = df_display['GAR_Premio'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) and x != 0 else "")

                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                elif cliente == "BAZAR":
                    # BAZAR tiene estructura especial: SPM y CPM (dos tipos de garantías)
                    st.write("### 📊 Facturación Bazar 2026 (SPM y CPM)")

                    # Leer todas las columnas: Mes, ASS, GAR_SPM, GAR_CPM, TOTAL_GE, GENERAL
                    df_table = df_datos[['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4', 'Unnamed: 5', 'Unnamed: 6', 'Unnamed: 7', 'Unnamed: 8', 'Unnamed: 9', 'Unnamed: 10', 'Unnamed: 11']].copy()
                    df_table.columns = ['Mes', 'ASS_Cant', 'ASS_Premio', 'GAR_SPM_Cant', 'GAR_SPM_Premio', 'GAR_CPM_Cant', 'GAR_CPM_Premio', 'TOTAL_Cant', 'TOTAL_Premio', 'GENERAL_Cant', 'GENERAL_Premio']
                    df_table = df_table[df_table['Mes'].notna()]

                    # Convertir a números
                    for col in df_table.columns:
                        if col != 'Mes':
                            df_table[col] = pd.to_numeric(df_table[col], errors='coerce').fillna(0)

                    # Mostrar HORIZONTAL en columnas con separadores
                    col1, col2, col3, col4, col5 = st.columns(5)

                    # ASISTENCIAS
                    with col1:
                        st.markdown("<div style='background-color: #9DBDD9; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>📞 ASISTENCIAS</b></div>", unsafe_allow_html=True)
                        df_ass = df_table[['Mes', 'ASS_Cant', 'ASS_Premio']].copy()
                        df_ass['ASS_Cant'] = df_ass['ASS_Cant'].astype(int)
                        df_ass['ASS_Premio'] = df_ass['ASS_Premio'].apply(lambda x: f"${x:,.0f}")
                        df_ass.columns = ['Mes', 'Cant', 'Premio']
                        st.dataframe(df_ass, use_container_width=False, hide_index=True)

                    # Separador 1
                    st.markdown("<div style='border-left: 3px solid #1E3A8A;'>&nbsp;</div>", unsafe_allow_html=True)

                    # GARANTIAS SPM
                    with col2:
                        st.markdown("<div style='background-color: #9DBDD9; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>🛡️ GAR SPM</b></div>", unsafe_allow_html=True)
                        df_spm = df_table[['Mes', 'GAR_SPM_Cant', 'GAR_SPM_Premio']].copy()
                        df_spm['GAR_SPM_Cant'] = df_spm['GAR_SPM_Cant'].astype(int)
                        df_spm['GAR_SPM_Premio'] = df_spm['GAR_SPM_Premio'].apply(lambda x: f"${x:,.0f}")
                        df_spm.columns = ['Mes', 'Cant', 'Premio']
                        st.dataframe(df_spm, use_container_width=False, hide_index=True)

                    # Separador 2
                    st.markdown("<div style='border-left: 3px solid #1E3A8A;'>&nbsp;</div>", unsafe_allow_html=True)

                    # GARANTIAS CPM
                    with col3:
                        st.markdown("<div style='background-color: #9DBDD9; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>🛡️ GAR CPM</b></div>", unsafe_allow_html=True)
                        df_cpm = df_table[['Mes', 'GAR_CPM_Cant', 'GAR_CPM_Premio']].copy()
                        df_cpm['GAR_CPM_Cant'] = df_cpm['GAR_CPM_Cant'].astype(int)
                        df_cpm['GAR_CPM_Premio'] = df_cpm['GAR_CPM_Premio'].apply(lambda x: f"${x:,.0f}")
                        df_cpm.columns = ['Mes', 'Cant', 'Premio']
                        st.dataframe(df_cpm, use_container_width=False, hide_index=True)

                    # Separador 3 (NARANJA para Totales)
                    st.markdown("<div style='border-left: 3px solid #FF6B00;'>&nbsp;</div>", unsafe_allow_html=True)

                    # TOTAL (Solo Garantías: SPM + CPM)
                    with col4:
                        st.markdown("<div style='background-color: #E0C9B0; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>💰 TOTAL GTIAS</b></div>", unsafe_allow_html=True)
                        df_tot = df_table[['Mes', 'TOTAL_Cant', 'TOTAL_Premio']].copy()
                        df_tot['TOTAL_Cant'] = df_tot['TOTAL_Cant'].astype(int)
                        df_tot['TOTAL_Premio'] = df_tot['TOTAL_Premio'].apply(lambda x: f"${x:,.0f}")
                        df_tot.columns = ['Mes', 'Cant', 'Premio']
                        st.dataframe(df_tot, use_container_width=False, hide_index=True)

                    # Separador 4 (NARANJA para Totales)
                    st.markdown("<div style='border-left: 3px solid #FF6B00;'>&nbsp;</div>", unsafe_allow_html=True)

                    # TOTAL GENERAL (ASS + SPM + CPM)
                    with col5:
                        st.markdown("<div style='background-color: #E0C9B0; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>🌟 TOTAL GRAL</b></div>", unsafe_allow_html=True)
                        df_gen = df_table[['Mes', 'GENERAL_Cant', 'GENERAL_Premio']].copy()
                        df_gen['GENERAL_Cant'] = df_gen['GENERAL_Cant'].astype(int)
                        df_gen['GENERAL_Premio'] = df_gen['GENERAL_Premio'].apply(lambda x: f"${x:,.0f}")
                        df_gen.columns = ['Mes', 'Cant', 'Premio']
                        st.dataframe(df_gen, use_container_width=False, hide_index=True)

                    # TABLA DE COBERTURAS (Filas 26-33)
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<h3 style='background-color: #E0C9B0; padding: 10px; border-radius: 5px; margin-bottom: 10px;'>📋 Coberturas y Costos</h3>", unsafe_allow_html=True)

                    df_coberturas = df_cliente.iloc[25:33].copy()
                    df_cob = df_coberturas[['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4']].copy()
                    df_cob.columns = ['% Total', '% Sancor', '% Blister', 'Cobertura']
                    df_cob = df_cob[df_cob['% Total'].notna()]

                    # Convertir valores numéricos
                    df_cob['% Total'] = df_cob['% Total'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) and isinstance(x, (int, float)) else str(x))
                    df_cob['% Sancor'] = df_cob['% Sancor'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) and isinstance(x, (int, float)) else str(x))
                    df_cob['% Blister'] = df_cob['% Blister'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) and isinstance(x, (int, float)) else str(x))

                    # Renderizar tabla con HTML para resaltar valores en negrita
                    tabla_html = '<table class="resumen-table" style="width: auto; border-collapse: collapse;">'
                    tabla_html += '<tr style="background-color: #1E3A8A; color: white;"><th style="padding: 10px; text-align: center; border: 2px solid #1E3A8A;">% Total</th><th style="padding: 10px; text-align: center; border: 2px solid #1E3A8A;">% Sancor</th><th style="padding: 10px; text-align: center; border: 2px solid #1E3A8A;">% Blister</th><th style="padding: 10px; text-align: left; border: 2px solid #1E3A8A;">Cobertura</th></tr>'

                    for idx, row in df_cob.iterrows():
                        tabla_html += '<tr style="border-bottom: 2px solid #1E3A8A;">'
                        # % Total
                        val_total = str(row['% Total']).strip()
                        tabla_html += f'<td style="text-align: center; font-weight: bold; padding: 8px; border: 1px solid #ddd;">{val_total}</td>'
                        # % Sancor
                        val_sancor = str(row['% Sancor']).strip()
                        tabla_html += f'<td style="text-align: center; font-weight: bold; padding: 8px; border: 1px solid #ddd;">{val_sancor}</td>'
                        # % Blister
                        val_blister = str(row['% Blister']).strip()
                        tabla_html += f'<td style="text-align: center; font-weight: bold; padding: 8px; border: 1px solid #ddd;">{val_blister}</td>'
                        # Cobertura
                        cobertura = str(row['Cobertura']).strip()
                        tabla_html += f'<td style="text-align: left; padding: 8px; border: 1px solid #ddd;"><b>{cobertura}</b></td>'
                        tabla_html += '</tr>'

                    tabla_html += '</table>'
                    st.markdown(tabla_html, unsafe_allow_html=True)

                elif cliente == "LAS MALVINAS":
                    st.write("### 📊 Facturación Las Malvinas 2026")

                    # Datos de Las Malvinas (B2:E11 en Excel = filas 2-11, iloc[3:11] para incluir headers en fila 4)
                    df_datos_malvinas = df_cliente.iloc[3:11].copy()
                    df_table = df_datos_malvinas[['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4']].copy()
                    df_table.columns = ['Mes', 'GAR_Cant', 'GAR_Premio', 'Restante_Deuda']
                    df_table = df_table[df_table['Mes'].notna()]

                    # Convertir a números
                    df_table['GAR_Cant'] = pd.to_numeric(df_table['GAR_Cant'], errors='coerce').fillna(0).astype(int)
                    df_table['GAR_Premio'] = pd.to_numeric(df_table['GAR_Premio'], errors='coerce').fillna(0)
                    df_table['Restante_Deuda'] = pd.to_numeric(df_table['Restante_Deuda'], errors='coerce').fillna(0)

                    # Filtrar solo las filas donde GAR_Cant > 0
                    df_table = df_table[df_table['GAR_Cant'] > 0]

                    # Mostrar en 2 columnas
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("<div style='background-color: #9DBDD9; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>🛡️ GARANTÍAS</b></div>", unsafe_allow_html=True)
                        df_gar = df_table[['Mes', 'GAR_Cant', 'GAR_Premio']].copy()
                        df_gar['GAR_Premio'] = df_gar['GAR_Premio'].apply(lambda x: f"${x:,.0f}" if x != 0 else "-")
                        df_gar.columns = ['Mes', 'Cant', 'Premio']
                        st.dataframe(df_gar, use_container_width=True, hide_index=True)

                    with col2:
                        st.markdown("<div style='background-color: #E0C9B0; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>💰 RESTANTE DE DEUDA</b></div>", unsafe_allow_html=True)
                        df_deuda = df_table[['Mes', 'Restante_Deuda']].copy()
                        df_deuda['Restante_Deuda'] = df_deuda['Restante_Deuda'].apply(lambda x: f"${x:,.0f}" if x != 0 else "-")
                        df_deuda.columns = ['Mes', 'Deuda']
                        st.dataframe(df_deuda, use_container_width=True, hide_index=True)

                elif cliente == "CASA REIG":
                    st.write("### 📊 Facturación Casa Reig 2026")

                    # Datos de Casa Reig (filas 4-14 en Excel, iloc 3:13)
                    df_datos_reig = df_cliente.iloc[3:13].copy()
                    df_table = df_datos_reig[['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4']].copy()
                    df_table.columns = ['Mes', 'GAR_Cant', 'GAR_Premio', 'Pagos']
                    df_table = df_table[df_table['Mes'].notna()]

                    # Convertir a números
                    df_table['GAR_Cant'] = pd.to_numeric(df_table['GAR_Cant'], errors='coerce').fillna(0).astype(int)
                    df_table['GAR_Premio'] = pd.to_numeric(df_table['GAR_Premio'], errors='coerce').fillna(0)

                    # Mostrar en 2 columnas
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("<div style='background-color: #9DBDD9; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>🛡️ GARANTÍAS</b></div>", unsafe_allow_html=True)
                        df_gar = df_table[['Mes', 'GAR_Cant', 'GAR_Premio']].copy()
                        df_gar['GAR_Premio'] = df_gar['GAR_Premio'].apply(lambda x: f"${x:,.0f}" if x != 0 else "-")
                        df_gar.columns = ['Mes', 'Cant', 'Premio']
                        st.dataframe(df_gar, use_container_width=True, hide_index=True)

                    with col2:
                        st.markdown("<div style='background-color: #E0C9B0; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>💳 PAGOS</b></div>", unsafe_allow_html=True)
                        df_pagos = df_table[['Mes', 'Pagos']].copy()
                        df_pagos['Pagos'] = df_pagos['Pagos'].apply(lambda x: str(x).strip() if pd.notna(x) else "-")
                        df_pagos.columns = ['Mes', 'SI/NO']
                        st.dataframe(df_pagos, use_container_width=True, hide_index=True)

                else:
                    st.write("### 📊 Ventas por Cobertura")

                    df_table = df_datos[['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4', 'Unnamed: 5', 'Unnamed: 6', 'Unnamed: 7']].copy()
                    df_table.columns = ['Mes', 'ASS_Cant', 'ASS_Premio', 'GAR_Cant', 'GAR_Premio', 'TOT_Cant', 'TOT_Premio']
                    df_table = df_table[df_table['Mes'].notna()]

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("<div style='background-color: #9DBDD9; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>Asistencias</b></div>", unsafe_allow_html=True)
                        df_ass = df_table[['Mes', 'ASS_Cant', 'ASS_Premio']].copy()
                        df_ass['ASS_Cant'] = pd.to_numeric(df_ass['ASS_Cant'], errors='coerce').fillna(0).astype(int)
                        df_ass['ASS_Premio'] = df_ass['ASS_Premio'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) and x != 0 else "")
                        st.dataframe(df_ass, use_container_width=True, hide_index=True)

                    with col2:
                        st.markdown("<div style='background-color: #9DBDD9; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>Garantías</b></div>", unsafe_allow_html=True)
                        df_gar = df_table[['Mes', 'GAR_Cant', 'GAR_Premio']].copy()
                        df_gar['GAR_Cant'] = pd.to_numeric(df_gar['GAR_Cant'], errors='coerce').fillna(0).astype(int)
                        df_gar['GAR_Premio'] = df_gar['GAR_Premio'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) and x != 0 else "")
                        st.dataframe(df_gar, use_container_width=True, hide_index=True)

                    with col3:
                        st.markdown("<div style='background-color: #E0C9B0; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><b>Total</b></div>", unsafe_allow_html=True)
                        df_tot = df_table[['Mes', 'TOT_Cant', 'TOT_Premio']].copy()
                        df_tot['TOT_Cant'] = pd.to_numeric(df_tot['TOT_Cant'], errors='coerce').fillna(0).astype(int)
                        df_tot['TOT_Premio'] = df_tot['TOT_Premio'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) and x != 0 else "")
                        st.dataframe(df_tot, use_container_width=True, hide_index=True)
            
            else:
                st.error(f"❌ Pestaña '{pestaña_fc}' no encontrada")
    
    st.markdown("---")
    st.caption("✅ Fichas VIP cargadas desde Google Drive")
# ============================================
# PANTALLA 3: COSTOS SANCOR
# ============================================
elif pantalla_actual == "Machete Costos":
    st.markdown("""
    <div class="hawk-header">
        <h1>Costos Sancor</h1>
        <div class="hawk-header-subtitle">Matriz de coberturas y costos</div>
    </div>
    """, unsafe_allow_html=True)
    
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
    st.markdown("""
    <div class="hawk-header">
        <h1>Facturación de Proveedores</h1>
        <div class="hawk-header-subtitle">Comparativa de facturación por proveedor</div>
    </div>
    """, unsafe_allow_html=True)
    
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
        with st.expander("🏥 **Cardinal**"):
            df_cardinal = df_tabla[['Mes', 'Cardinal_Cant', 'Cardinal_Precio']].copy()
            df_cardinal.columns = ['Mes', 'Cantidad', 'Precio']
            df_cardinal['Cantidad'] = pd.to_numeric(df_cardinal['Cantidad'], errors='coerce').fillna(0).astype(int)
            df_cardinal['Precio'] = df_cardinal['Precio'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) and x != 0 else "")
            st.dataframe(df_cardinal, hide_index=True, width=600)

        # ADDIUVA
        with st.expander("💊 **Addiuva**"):
            df_addiuva = df_tabla[['Mes', 'Addiuva_Cant', 'Addiuva_Precio']].copy()
            df_addiuva.columns = ['Mes', 'Cantidad', 'Precio']
            df_addiuva['Cantidad'] = pd.to_numeric(df_addiuva['Cantidad'], errors='coerce').fillna(0).astype(int)
            df_addiuva['Precio'] = df_addiuva['Precio'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) and x != 0 else "")
            st.dataframe(df_addiuva, hide_index=True, width=600)

        # LLAMADAS AL DOCTOR - BZR
        with st.expander("☎️ **Llamadas al Doctor BZR**"):
            df_bzr = df_tabla[['Mes', 'BZR_Cant', 'BZR_Precio']].copy()
            df_bzr.columns = ['Mes', 'Cantidad', 'Precio']
            df_bzr['Cantidad'] = pd.to_numeric(df_bzr['Cantidad'], errors='coerce').fillna(0).astype(int)
            df_bzr['Precio'] = df_bzr['Precio'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) and x != 0 else "")
            st.dataframe(df_bzr, hide_index=True, width=600)

        # LLAMADAS AL DOCTOR - GRAL
        with st.expander("☎️ **Llamadas al Doctor GRAL**"):
            df_gral = df_tabla[['Mes', 'GRAL_Cant', 'GRAL_Precio']].copy()
            df_gral.columns = ['Mes', 'Cantidad', 'Precio']
            df_gral['Cantidad'] = pd.to_numeric(df_gral['Cantidad'], errors='coerce').fillna(0).astype(int)
            df_gral['Precio'] = df_gral['Precio'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) and x != 0 else "")
            st.dataframe(df_gral, hide_index=True, width=600)

        # IMPRENTA
        with st.expander("🖨️ **Imprenta**"):
            df_imprenta = df_tabla[['Mes', 'Imprenta_Cant', 'Imprenta_Precio']].copy()
            df_imprenta.columns = ['Mes', 'Cantidad', 'Precio']
            df_imprenta['Cantidad'] = pd.to_numeric(df_imprenta['Cantidad'], errors='coerce').fillna(0).astype(int)
            df_imprenta['Precio'] = df_imprenta['Precio'].apply(lambda x: f"${x:,.2f}" if pd.notna(x) and x != 0 else "")
            st.dataframe(df_imprenta, hide_index=True, width=600)
        
        st.markdown("---")
        last_update = st.session_state.last_update_time
        formatted_time = last_update.strftime("%H:%M:%S")
        st.caption(f"✅ Actualizado: {formatted_time} | Presiona 🔄 REFRESH si ves datos desactualizados")
    
    else:
        st.error("❌ Pestaña 'FC Proveedores' no encontrada")

# ============================================
# PANTALLA 5.5: COBRANZAS SYNA
# ============================================
elif pantalla_actual == "Cobranzas SYNA":
    if _SYNA_IMPORT_ERROR is not None:
        st.error(f"No se pudo cargar el módulo SYNA: {_SYNA_IMPORT_ERROR}")
    else:
        try:
            inicializar_db()
        except Exception as _e:
            st.error(f"No se pudo conectar a la base de datos de SYNA: {_e}")
        else:
            pantalla_syna_admin()

# ============================================
# PANTALLA 6: POST EMISIÓN
# ============================================
elif pantalla_actual == "Post Emisión":
    st.markdown("""
    <div class="hawk-header">
        <h1>Post Emisión</h1>
        <div class="hawk-header-subtitle">Detalle de facturación posterior a la emisión</div>
    </div>
    """, unsafe_allow_html=True)

    if "Post Emision" in datos and ultima_fila_datos is not None:
        # SECCIÓN SUPERIOR: ÚLTIMO MES CON DATOS
        if ultimo_mes:
            # Extraer datos directamente de la última fila
            datos_ultimo = {
                'GESA': {
                    'cant': pd.to_numeric(ultima_fila_datos.iloc[2], errors='coerce') if pd.notna(ultima_fila_datos.iloc[2]) else 0,
                    'premio': pd.to_numeric(ultima_fila_datos.iloc[3], errors='coerce') if pd.notna(ultima_fila_datos.iloc[3]) else 0,
                    'iva': pd.to_numeric(ultima_fila_datos.iloc[4], errors='coerce') if pd.notna(ultima_fila_datos.iloc[4]) else 0,
                    'sellos': pd.to_numeric(ultima_fila_datos.iloc[5], errors='coerce') if pd.notna(ultima_fila_datos.iloc[5]) else 0,
                },
                'BLISTER': {
                    'cant': pd.to_numeric(ultima_fila_datos.iloc[6], errors='coerce') if pd.notna(ultima_fila_datos.iloc[6]) else 0,
                    'premio': pd.to_numeric(ultima_fila_datos.iloc[7], errors='coerce') if pd.notna(ultima_fila_datos.iloc[7]) else 0,
                    'iva': pd.to_numeric(ultima_fila_datos.iloc[8], errors='coerce') if pd.notna(ultima_fila_datos.iloc[8]) else 0,
                    'sellos': pd.to_numeric(ultima_fila_datos.iloc[9], errors='coerce') if pd.notna(ultima_fila_datos.iloc[9]) else 0,
                },
                'TOTALES': {
                    'cant': pd.to_numeric(ultima_fila_datos.iloc[10], errors='coerce') if pd.notna(ultima_fila_datos.iloc[10]) else 0,
                    'total': pd.to_numeric(ultima_fila_datos.iloc[11], errors='coerce') if pd.notna(ultima_fila_datos.iloc[11]) else 0,
                    'ajuste': pd.to_numeric(ultima_fila_datos.iloc[12], errors='coerce') if pd.notna(ultima_fila_datos.iloc[12]) else 0,
                }
            }

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

        # TABLA HISTÓRICA - Mostrar todos los datos hasta la última fila
        st.write("### 📊 Histórico de Datos")

        # Construir tabla para visualización con estilos personalizados
        tabla_datos = []
        if "Post Emision" in datos:
            df_general = datos['Post Emision']
            # Encontrar el índice de la última fila con datos
            ultima_idx = None
            for idx in range(len(df_general) - 1, -1, -1):
                row = df_general.iloc[idx]
                total_value = pd.to_numeric(row.iloc[11], errors='coerce') if pd.notna(row.iloc[11]) else 0
                if total_value > 0:
                    ultima_idx = idx
                    break

            # Iterar desde el principio hasta la última fila con datos
            if ultima_idx is not None:
                for idx in range(len(df_general)):
                    if idx > ultima_idx:
                        break
                    row = df_general.iloc[idx]
                    mes = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""

                    if mes in meses_validos:
                        # Extraer valores de esta fila
                        gesa_cant = pd.to_numeric(row.iloc[2], errors='coerce') if pd.notna(row.iloc[2]) else 0
                        gesa_premio = pd.to_numeric(row.iloc[3], errors='coerce') if pd.notna(row.iloc[3]) else 0
                        gesa_iva = pd.to_numeric(row.iloc[4], errors='coerce') if pd.notna(row.iloc[4]) else 0
                        gesa_sellos = pd.to_numeric(row.iloc[5], errors='coerce') if pd.notna(row.iloc[5]) else 0

                        blister_cant = pd.to_numeric(row.iloc[6], errors='coerce') if pd.notna(row.iloc[6]) else 0
                        blister_premio = pd.to_numeric(row.iloc[7], errors='coerce') if pd.notna(row.iloc[7]) else 0
                        blister_iva = pd.to_numeric(row.iloc[8], errors='coerce') if pd.notna(row.iloc[8]) else 0
                        blister_sellos = pd.to_numeric(row.iloc[9], errors='coerce') if pd.notna(row.iloc[9]) else 0

                        total_cant = pd.to_numeric(row.iloc[10], errors='coerce') if pd.notna(row.iloc[10]) else 0
                        total_value = pd.to_numeric(row.iloc[11], errors='coerce') if pd.notna(row.iloc[11]) else 0
                        ajuste = pd.to_numeric(row.iloc[12], errors='coerce') if pd.notna(row.iloc[12]) else 0

                        tabla_datos.append({
                            'Mes': mes,
                            'Cant': int(gesa_cant) if gesa_cant > 0 else '',
                            'Premio': f"${gesa_premio:,.0f}" if gesa_premio > 0 else '',
                            'IVA': f"${gesa_iva:,.0f}" if gesa_iva > 0 else '',
                            'Sellos': f"${gesa_sellos:,.0f}" if gesa_sellos > 0 else '',
                            'Cant ': int(blister_cant) if blister_cant > 0 else '',
                            'Premio ': f"${blister_premio:,.0f}" if blister_premio > 0 else '',
                            'IVA ': f"${blister_iva:,.0f}" if blister_iva > 0 else '',
                            'Sellos ': f"${blister_sellos:,.0f}" if blister_sellos > 0 else '',
                            'Cant  ': int(total_cant) if total_cant > 0 else '',
                            'Total': f"${total_value:,.0f}" if total_value > 0 else '',
                            'Ajuste': f"${ajuste:,.0f}" if ajuste != 0 else '',
                        })

        if tabla_datos:
            df_historico = pd.DataFrame(tabla_datos)

            # Crear HTML personalizado con estilos de color mejorados
            html_tabla = '<style>'
            html_tabla += '.tabla-post-emision { width: 100%; border-collapse: collapse; font-size: 14px; }'
            html_tabla += '.tabla-post-emision th { padding: 12px; text-align: center; font-weight: 700; border-bottom: 2px solid #ddd; }'
            html_tabla += '.tabla-post-emision td { padding: 10px; text-align: right; border-bottom: 1px solid #ddd; }'
            html_tabla += '.tabla-post-emision td:first-child, .tabla-post-emision th:first-child { text-align: left; }'
            html_tabla += '.gesa-header { background-color: #FF6B6B; color: white; }'
            html_tabla += '.gesa-cell { background-color: #FFE0E0; }'
            html_tabla += '.blister-header { background-color: #4C7FD9; color: white; }'
            html_tabla += '.blister-cell { background-color: #E3ECFF; }'
            html_tabla += '.totales-header { background-color: #A9A9A9; color: white; }'
            html_tabla += '.totales-cell { background-color: #F0F0F0; }'
            html_tabla += '.mes-header { background-color: #1E3A8A; color: white; font-weight: 700; }'
            html_tabla += '.mes-cell { background-color: #FFFFFF; color: #1E3A8A; font-weight: 600; }'
            html_tabla += '.bold-value { font-weight: 700; }'
            html_tabla += '</style>'

            html_tabla += '<table class="tabla-post-emision"><thead>'
            html_tabla += '<tr>'
            html_tabla += '<th class="mes-header">Mes</th>'
            html_tabla += '<th colspan="4" class="gesa-header">GESA</th>'
            html_tabla += '<th colspan="4" class="blister-header">BLISTER</th>'
            html_tabla += '<th colspan="3" class="totales-header">TOTALES</th>'
            html_tabla += '</tr>'
            html_tabla += '<tr>'
            html_tabla += '<th class="mes-header"></th>'
            html_tabla += '<th class="gesa-header">Cant</th><th class="gesa-header">Premio</th><th class="gesa-header">IVA</th><th class="gesa-header">Sellos</th>'
            html_tabla += '<th class="blister-header">Cant</th><th class="blister-header">Premio</th><th class="blister-header">IVA</th><th class="blister-header">Sellos</th>'
            html_tabla += '<th class="totales-header">Cant</th><th class="totales-header">Total</th><th class="totales-header">Ajuste</th>'
            html_tabla += '</tr>'
            html_tabla += '</thead><tbody>'

            for _, row in df_historico.iterrows():
                html_tabla += '<tr>'
                html_tabla += f'<td class="mes-cell">{row["Mes"]}</td>'
                html_tabla += f'<td class="gesa-cell bold-value">{row["Cant"]:,}</td>'
                html_tabla += f'<td class="gesa-cell bold-value">{row["Premio"]}</td>'
                html_tabla += f'<td class="gesa-cell">{row["IVA"]}</td>'
                html_tabla += f'<td class="gesa-cell">{row["Sellos"]}</td>'
                html_tabla += f'<td class="blister-cell bold-value">{row["Cant "]:,}</td>'
                html_tabla += f'<td class="blister-cell bold-value">{row["Premio "]}</td>'
                html_tabla += f'<td class="blister-cell">{row["IVA "]}</td>'
                html_tabla += f'<td class="blister-cell">{row["Sellos "]}</td>'
                html_tabla += f'<td class="totales-cell bold-value">{row["Cant  "]:,}</td>'
                html_tabla += f'<td class="totales-cell bold-value">{row["Total"]}</td>'
                html_tabla += f'<td class="totales-cell">{row["Ajuste"]}</td>'
                html_tabla += '</tr>'

            html_tabla += '</tbody></table>'

            st.markdown(html_tabla, unsafe_allow_html=True)
        else:
            st.info("📭 No hay datos disponibles para mostrar")

        st.markdown("---")
        last_update = st.session_state.last_update_time
        formatted_time = last_update.strftime("%H:%M:%S")
        st.caption(f"✅ Actualizado: {formatted_time} | Se actualiza cada 5 minutos automáticamente")

    else:
        st.error("❌ No se encontraron datos en la pestaña 'Post Emision' o no hay información disponible")
