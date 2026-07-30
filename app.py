import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import json

st.set_page_config(page_title="Hawk - Exploración", layout="wide")
st.title("🦅 Hawk - Exploración de Datos")
st.markdown("---")

# Cargar datos
GOOGLE_DRIVE_ID = "1gZPD9XUspcN8e4FGrgdEl1AacDew68RU"
URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_DRIVE_ID}/export?format=xlsx"

with st.spinner("Cargando..."):
    response = requests.get(URL, timeout=10)
    archivo_excel = BytesIO(response.content)
    excel_file = pd.ExcelFile(archivo_excel)
    
    datos = {}
    for pestaña in excel_file.sheet_names:
        datos[pestaña] = pd.read_excel(archivo_excel, sheet_name=pestaña)

# ============================================
# BOTÓN PARA DESCARGAR ESTRUCTURA
# ============================================
col1, col2 = st.columns([3, 1])

with col2:
    # Crear resumen en JSON
    resumen = {}
    for pestaña, df in datos.items():
        resumen[pestaña] = {
            "columnas": list(df.columns),
            "filas": len(df),
            "primeras_5_filas": df.head(5).to_dict(orient='records')
        }
    
    json_str = json.dumps(resumen, indent=2, ensure_ascii=False)
    
    st.download_button(
        label="📥 Descargar estructura JSON",
        data=json_str,
        file_name="estructura_hawk.json",
        mime="application/json"
    )

st.markdown("---")

# Selector de pestaña
pestaña_seleccionada = st.selectbox(
    "Selecciona una pestaña para explorar:",
    list(datos.keys())
)

# Mostrar estructura
st.write(f"### 📊 Pestaña: `{pestaña_seleccionada}`")
st.write(f"**Tamaño:** {datos[pestaña_seleccionada].shape[0]} filas × {datos[pestaña_seleccionada].shape[1]} columnas")

st.write("**Columnas:**")
cols_text = ", ".join(list(datos[pestaña_seleccionada].columns))
st.code(cols_text, language="python")

st.write("**Vista previa (primeras 10 filas):**")
st.dataframe(datos[pestaña_seleccionada].head(10), use_container_width=True)
