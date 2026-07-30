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
</style>
""", unsafe_allow_html=True)

# ============================================
# ENCABEZADO
# ============================================
st.title("🦅 Hawk - Reportes Internos")
st.markdown("---")

# ============================================
# CONEXIÓN A GOOGLE DRIVE (SIN CACHE PROBLEMÁTICO)
# ============================================
def cargar_excel_de_google_drive():
    """
    Descarga el Excel directamente desde Google Drive
    Retorna un diccionario con todas las pestañas
    """
    GOOGLE_DRIVE_ID = "1gZPD9XUspcN8e4FGrgdEl1AacDew68RU"
    URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_DRIVE_ID}/export?format=xlsx"
    
    try:
        # Descargar el archivo
        response = requests.get(URL, timeout=10)
        response.raise_for_status()
        
        # Leer todas las pestañas en un diccionario
        archivo_excel = BytesIO(response.content)
        excel_file = pd.ExcelFile(archivo_excel)
        
        # Crear diccionario con todas las pestañas
        datos = {}
        for pestaña in excel_file.sheet_names:
            datos[pestaña] = pd.read_excel(archivo_excel, sheet_name=pestaña)
        
        return datos, None
    
    except Exception as e:
        return None, f"❌ Error al conectar con Google Drive: {str(e)}"

# ============================================
# CARGAR DATOS
# ============================================
st.write("### 📊 Estado de Conexión")

with st.spinner("⏳ Conectando con Google Drive..."):
    datos, error = cargar_excel_de_google_drive()

if error:
    st.error(error)
    st.stop()

# ============================================
# MOSTRAR PESTAÑAS DISPONIBLES
# ============================================
st.success("✅ Conexión exitosa con Google Drive")
st.write("### 📑 Pestañas Disponibles en el Excel:")

for pestaña in datos.keys():
    st.write(f"✓ `{pestaña}`")

# ============================================
# PRUEBA: Leer la pestaña "resumen"
# ============================================
st.write("### 🔍 Vista Previa - Pestaña 'resumen':")

try:
    if "resumen" in datos:
        df_resumen = datos["resumen"]
        st.dataframe(df_resumen, use_container_width=True)
        st.success(f"✅ Pestaña 'resumen' cargada correctamente ({len(df_resumen)} filas)")
    else:
        st.warning("⚠️ Pestaña 'resumen' no encontrada")
except Exception as e:
    st.warning(f"⚠️ Error al mostrar 'resumen': {str(e)}")

# ============================================
# INFORMACIÓN DEBUG
# ============================================
st.markdown("---")
with st.expander("🔧 Información Debug"):
    st.write(f"**Pestañas encontradas:** {list(datos.keys())}")
    st.write(f"**Número de pestañas:** {len(datos)}")

st.info("✅ **PASO 2 completado:** Google Drive conectado y Excel leyéndose en vivo")
