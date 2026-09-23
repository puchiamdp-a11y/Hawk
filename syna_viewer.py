"""
SYNA Tracking - Interfaz Viewer (Cintia)
Pantalla read-only para consulta de balance SYNA
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from syna_db import (
    obtener_invoices, calcular_balance_syna,
    obtener_proximos_vencimientos
)


def pantalla_syna_viewer():
    """Pantalla read-only SYNA para Cintia (cobranzas)."""

    # Estilos CSS
    st.markdown("""
    <style>
        .syna-viewer-header {
            background: linear-gradient(135deg, #1E3A8A 0%, #2E5AB5 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }

        .syna-viewer-header h2 {
            color: white !important;
            margin: 0 !important;
        }

        .syna-viewer-badge {
            background-color: #dcfce7;
            color: #166534;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: bold;
            display: inline-block;
            margin-top: 10px;
        }

        .syna-balance-card {
            background-color: #f9fafb;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #1E3A8A;
            margin: 10px 0;
        }

        .syna-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }

        .syna-table th {
            background-color: #1E3A8A;
            color: white;
            padding: 12px;
            text-align: left;
            font-size: 13px;
        }

        .syna-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #e5e7eb;
            font-size: 12px;
        }

        .syna-estado-pagada {
            background-color: #dcfce7;
            color: #166534;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }

        .syna-estado-impaga {
            background-color: #fee2e2;
            color: #991b1b;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }

        .syna-estado-parcial {
            background-color: #fef3c7;
            color: #92400e;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="syna-viewer-header">
        <h2>📊 Seguimiento Cobranzas SYNA</h2>
        <p>Consulta de estado de facturas y balance pendiente</p>
        <div class="syna-viewer-badge">🔒 Modo Lectura - Acceso Restringido</div>
    </div>
    """, unsafe_allow_html=True)

    # Obtener datos
    balance = calcular_balance_syna()
    invoices = obtener_invoices()
    vencimientos = obtener_proximos_vencimientos(dias=30)

    # Resumen de balance
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="syna-balance-card">
            <div style="font-size: 12px; opacity: 0.7;">Total Facturado</div>
            <div style="font-size: 24px; font-weight: bold; color: #1E3A8A;">
                ${balance['total_facturado']:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="syna-balance-card">
            <div style="font-size: 12px; opacity: 0.7;">Total Pagado</div>
            <div style="font-size: 24px; font-weight: bold; color: #16a34a;">
                ${balance['total_pagado']:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        color = "#dc2626" if balance['saldo_pendiente'] > 0 else "#16a34a"
        st.markdown(f"""
        <div class="syna-balance-card">
            <div style="font-size: 12px; opacity: 0.7;">Saldo Pendiente</div>
            <div style="font-size: 24px; font-weight: bold; color: {color};">
                ${balance['saldo_pendiente']:,.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Filtros
    st.markdown("---")
    st.subheader("🔍 Filtrar y Exportar")

    col1, col2, col3 = st.columns(3)

    with col1:
        fecha_desde = st.date_input("Desde", value=None)

    with col2:
        fecha_hasta = st.date_input("Hasta", value=None)

    with col3:
        estado_filtro = st.selectbox(
            "Estado",
            ["Todas", "Pagadas", "Impagas", "Parcialmente pagadas"]
        )

    # Aplicar filtros
    invoices_filtradas = invoices

    if fecha_desde:
        invoices_filtradas = [
            inv for inv in invoices_filtradas
            if inv["invoice_date"] and inv["invoice_date"] >= fecha_desde.isoformat()
        ]

    if fecha_hasta:
        invoices_filtradas = [
            inv for inv in invoices_filtradas
            if inv["invoice_date"] and inv["invoice_date"] <= fecha_hasta.isoformat()
        ]

    if estado_filtro != "Todas":
        estado_map = {
            "Pagadas": "Pagada",
            "Impagas": "Impaga",
            "Parcialmente pagadas": "Parcialmente pagada"
        }
        invoices_filtradas = [
            inv for inv in invoices_filtradas
            if inv["estado"] == estado_map[estado_filtro]
        ]

    # Tabla de facturas
    st.markdown("---")
    st.subheader("📋 Detalle de Facturas")

    if invoices_filtradas:
        df_display = []
        for inv in invoices_filtradas:
            df_display.append({
                "Número": inv["invoice_number"],
                "Monto": f"${inv['amount']:,.2f}",
                "Fecha": inv["invoice_date"] if inv["invoice_date"] else "N/A",
                "Vencimiento": inv["due_date"] if inv["due_date"] else "N/A",
                "Pagado": f"${inv['amount'] - inv['saldo']:,.2f}",
                "Saldo": f"${inv['saldo']:,.2f}",
                "Estado": inv["estado"]
            })

        df = pd.DataFrame(df_display)

        # Mostrar con HTML para colores en estado
        html_tabla = '<table class="syna-table"><thead><tr>'
        for col in df.columns:
            html_tabla += f'<th>{col}</th>'
        html_tabla += '</tr></thead><tbody>'

        for _, row in df.iterrows():
            html_tabla += '<tr>'
            for col in df.columns:
                valor = row[col]
                if col == "Estado":
                    if valor == "Pagada":
                        html_tabla += f'<td><span class="syna-estado-pagada">{valor}</span></td>'
                    elif valor == "Impaga":
                        html_tabla += f'<td><span class="syna-estado-impaga">{valor}</span></td>'
                    else:
                        html_tabla += f'<td><span class="syna-estado-parcial">{valor}</span></td>'
                else:
                    html_tabla += f'<td>{valor}</td>'
            html_tabla += '</tr>'

        html_tabla += '</tbody></table>'
        st.markdown(html_tabla, unsafe_allow_html=True)

        # Botón de exportar
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("📥 Exportar a Excel", use_container_width=True):
                try:
                    # Crear DataFrame para export
                    df_export = df.copy()

                    # Generar nombre de archivo
                    filename = f"SYNA_Cobranzas_{datetime.now().strftime('%Y%m%d')}.xlsx"

                    # Usar BytesIO para generar Excel en memoria
                    from io import BytesIO
                    buffer = BytesIO()

                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_export.to_excel(writer, sheet_name='Cobranzas', index=False)

                    buffer.seek(0)

                    st.download_button(
                        label="💾 Descargar Excel",
                        data=buffer,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"❌ Error al exportar: {str(e)}")
    else:
        st.info("📭 No hay facturas con los filtros especificados")

    # Próximos vencimientos
    st.markdown("---")
    st.subheader("📅 Próximos Vencimientos (30 días)")

    if vencimientos:
        df_venc = []
        for venc in vencimientos:
            df_venc.append({
                "Factura": venc["invoice_number"],
                "Vencimiento": venc["due_date"],
                "Saldo": f"${venc['saldo']:,.2f}",
                "Estado": venc["estado"]
            })

        df = pd.DataFrame(df_venc)

        # Mostrar con HTML para colores
        html_tabla = '<table class="syna-table"><thead><tr>'
        for col in df.columns:
            html_tabla += f'<th>{col}</th>'
        html_tabla += '</tr></thead><tbody>'

        for _, row in df.iterrows():
            html_tabla += '<tr>'
            for col in df.columns:
                valor = row[col]
                if col == "Estado":
                    if valor == "Pagada":
                        html_tabla += f'<td><span class="syna-estado-pagada">{valor}</span></td>'
                    elif valor == "Impaga":
                        html_tabla += f'<td><span class="syna-estado-impaga">{valor}</span></td>'
                    else:
                        html_tabla += f'<td><span class="syna-estado-parcial">{valor}</span></td>'
                else:
                    html_tabla += f'<td>{valor}</td>'
            html_tabla += '</tr>'

        html_tabla += '</tbody></table>'
        st.markdown(html_tabla, unsafe_allow_html=True)
    else:
        st.success("✅ No hay facturas vencidas en los próximos 30 días")

    # Footer
    st.markdown("---")
    st.caption(f"✅ Actualizado: {datetime.now().strftime('%H:%M:%S')} | Acceso restringido a Cintia")


def pantalla_syna_con_autenticacion():
    """Pantalla con autenticación para Cintia."""

    st.markdown("""
    <div style="text-align: center; padding: 40px;">
        <h2>🔐 Acceso a Cobranzas SYNA</h2>
        <p>Ingresa la contraseña para acceder</p>
    </div>
    """, unsafe_allow_html=True)

    # Obtener contraseña del archivo .streamlit/secrets.toml o usar default
    try:
        contraseña_correcta = st.secrets.get("syna_password", "SYNA2024")
    except:
        contraseña_correcta = "SYNA2024"

    contraseña_ingresada = st.text_input(
        "Contraseña",
        type="password",
        placeholder="Ingresa la contraseña"
    )

    if st.button("Acceder", use_container_width=True):
        if contraseña_ingresada == contraseña_correcta:
            st.session_state.syna_authenticated = True
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta")

    # Info footer
    st.markdown("---")
    st.caption("Este panel es solo para consulta de estado de cobranzas SYNA")
