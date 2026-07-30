import streamlit as st
import pandas as pd
import requests
from io import BytesIO

# ============================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================
st.set_page_config(
    page_title="Hawk - Reportes",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .metric-card {
        background-color: #1E3A8A;
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# ENCABEZADO
# ============================================
st.title("🦅 Hawk - Reportes Internos")
st.markdown("---")

# ============================================
# CONEXIÓN A GOOGLE DRIVE
# ============================================
@st.cache_data
def cargar_excel_de_google_drive():
    """
    Descarga el Excel directamente desde Google Drive
    """
    # ID del archivo en Google Drive
    GOOGLE_DRIVE_ID = "1gZPD9XUspcN8e4FGrgdEl1AacDew68RU"
    
    # URL de exportación directa
    URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_DRIVE_ID}/export?format=xlsx"
    
    try:
        # Descargar el archivo
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        
        # Convertir a BytesIO para que pandas lo pueda leer
        archivo_excel = BytesIO(response.content)
        
        # Leer todas las pestañas
        excel_file = pd.ExcelFile(archivo_excel)
        
        return excel_file, None
    
    except Exception as e:
        return None, f"❌ Error al conectar con Google Drive: {str(e)}"

# ============================================
# CARGAR DATOS
# ============================================
st.write("### 📊 Estado de Conexión")

with st.spinner("⏳ Conectando con Google Drive..."):
    excel_file, error = cargar_excel_de_google_drive()

if error:
    st.error(error)
    st.stop()

# ============================================
# MOSTRAR PESTAÑAS DISPONIBLES
# ============================================
st.success("✅ Conexión exitosa con Google Drive")
st.write("### 📑 Pestañas Disponibles en el Excel:")

pestañas = excel_file.sheet_names
for pestaña in pestañas:
    st.write(f"✓ `{pestaña}`")

# ============================================
# PRUEBA: Leer la pestaña "resumen"
# ============================================
st.write("### 🔍 Vista Previa - Pestaña 'resumen':")

try:
    df_resumen = pd.read_excel(BytesIO(requests.get(
        f"https://docs.google.com/spreadsheets/d/1gZPD9XUspcN8e4FGrgdEl1AacDew68RU/export?format=xlsx"
    ).content), sheet_name="resumen")
    
    st.dataframe(df_resumen, use_container_width=True)
    st.success("✅ Pestaña 'resumen' cargada correctamente")
    
except Exception as e:
    st.warning(f"⚠️ No se pudo cargar 'resumen': {str(e)}")

# ============================================
# RESUMEN FINAL
# ============================================
st.markdown("---")
st.info("✅ **PASO 2 completado:** Google Drive conectado y Excel leyéndose en vivo")
