import streamlit as st
import pandas as pd
import requests
from io import BytesIO

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

# Selector de pestaña
pestaña_seleccionada = st.selectbox(
    "Selecciona una pestaña para explorar:",
    list(datos.keys())
)

# Mostrar estructura
st.write(f"### 📊 Pestaña: `{pestaña_seleccionada}`")
st.write(f"**Tamaño:** {datos[pestaña_seleccionada].shape[0]} filas × {datos[pestaña_seleccionada].shape[1]} columnas")

st.write("**Columnas:**")
for col in datos[pestaña_seleccionada].columns:
    st.write(f"  • `{col}`")

st.write("**Vista previa completa:**")
st.dataframe(datos[pestaña_seleccionada], use_container_width=True)
