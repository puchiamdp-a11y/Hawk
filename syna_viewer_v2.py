"""
SYNA Tracking - Interfaz Viewer v2 (Cintia - Read-Only)
Pantalla de lectura con autenticación segura
"""

import streamlit as st
from datetime import datetime
from syna_db import (
    obtener_invoices, calcular_balance_syna,
    obtener_proximos_vencimientos
)


def estilos_viewer():
    """Estilos para pantalla Cintia (read-only)."""
    st.markdown("""
    <style>
        /* Colores */
        :root {
            --bg-main: #FFFFFF;
            --bg-secondary: #F8FAFC;
            --text-primary: #1F2937;
            --text-secondary: #6B7280;
            --estado-pagada: #D1FAE5;
            --estado-pagada-text: #047857;
            --estado-impaga: #FECACA;
            --estado-impaga-text: #991B1B;
            --estado-parcial: #FEF08A;
            --estado-parcial-text: #854D0E;
        }

        h2, h3 {
            color: var(--text-primary) !important;
        }

        h2 {
            font-size: 22px !important;
            font-weight: 600 !important;
            margin: 20px 0 8px 0 !important;
        }

        h3 {
            font-size: 14px !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary) !important;
            margin: 16px 0 8px 0 !important;
        }

        /* Secciones */
        .syna-section {
            background-color: var(--bg-secondary);
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 16px;
            border: 1px solid #E5E7EB;
        }

        /* Tabla */
        .syna-table {
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
            font-size: 13px;
        }

        .syna-table th {
            background-color: var(--bg-secondary);
            color: var(--text-primary);
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #D1D5DB;
        }

        .syna-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #E5E7EB;
        }

        /* Estados */
        .syna-estado-pagada {
            background-color: var(--estado-pagada);
            color: var(--estado-pagada-text);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }

        .syna-estado-impaga {
            background-color: var(--estado-impaga);
            color: var(--estado-impaga-text);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }

        .syna-estado-parcial {
            background-color: var(--estado-parcial);
            color: var(--estado-parcial-text);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }

        /* Cards */
        .syna-card {
            background-color: var(--bg-secondary);
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }

        .syna-card-label {
            font-size: 12px;
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }

        .syna-card-value {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-primary);
        }

        /* Badge read-only */
        .syna-badge {
            background-color: #DCFCE7;
            color: #047857;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
            margin-top: 8px;
        }
    </style>
    """, unsafe_allow_html=True)


def pantalla_syna_viewer_v2():
    """Pantalla read-only para Cintia (cobranzas)."""

    estilos_viewer()

    # Header
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h2 style="margin-bottom: 4px;">Seguimiento Cobranzas SYNA</h2>
        <p style="color: #6B7280; font-size: 14px; margin: 0;">
            Consulta de estado de facturas y balance pendiente
        </p>
        <div class="syna-badge">🔒 Modo Lectura - Acceso Restringido</div>
    </div>
    """, unsafe_allow_html=True)

    # Obtener datos
    balance = calcular_balance_syna()
    invoices = obtener_invoices()
    vencimientos = obtener_proximos_vencimientos(dias=30)

    # Cards de resumen
    st.markdown("### Resumen")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="syna-card">
            <div class="syna-card-label">Total Facturado</div>
            <div class="syna-card-value">${balance['total_facturado']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="syna-card">
            <div class="syna-card-label">Total Pagado</div>
            <div class="syna-card-value" style="color: #16A34A;">${balance['total_pagado']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        color = "#DC2626" if balance['saldo_pendiente'] > 0 else "#16A34A"
        st.markdown(f"""
        <div class="syna-card">
            <div class="syna-card-label">Saldo Pendiente</div>
            <div class="syna-card-value" style="color: {color};">${balance['saldo_pendiente']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Filtros
    st.markdown("### Filtros")

    col1, col2, col3 = st.columns(3)

    with col1:
        fecha_desde = st.date_input("Desde", value=None, key="viewer_desde")

    with col2:
        fecha_hasta = st.date_input("Hasta", value=None, key="viewer_hasta")

    with col3:
        estado_filtro = st.selectbox(
            "Estado",
            ["Todas", "Pagadas", "Impagas", "Parcialmente pagadas"],
            key="viewer_estado"
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

    st.markdown("---")

    # Tabla de facturas
    st.markdown("### Detalle de Facturas")

    if invoices_filtradas:
        html_tabla = '<table class="syna-table"><thead><tr>'
        html_tabla += '<th>Comprobante</th><th>Monto</th><th>Vencimiento</th><th>Pagado</th><th>Saldo</th><th>Estado</th>'
        html_tabla += '</tr></thead><tbody>'

        for inv in invoices_filtradas:
            html_tabla += '<tr>'
            html_tabla += f'<td><strong>{inv["invoice_number"]}</strong></td>'
            html_tabla += f'<td>${inv["amount"]:,.2f}</td>'
            html_tabla += f'<td>{inv["due_date"] if inv["due_date"] else "N/A"}</td>'
            html_tabla += f'<td>${inv["amount"] - inv["saldo"]:,.2f}</td>'
            html_tabla += f'<td>${inv["saldo"]:,.2f}</td>'

            # Estado
            if inv["estado"] == "Pagada":
                html_tabla += '<td><span class="syna-estado-pagada">Pagada</span></td>'
            elif inv["estado"] == "Impaga":
                html_tabla += '<td><span class="syna-estado-impaga">Impaga</span></td>'
            else:
                html_tabla += '<td><span class="syna-estado-parcial">Parcial</span></td>'

            html_tabla += '</tr>'

        html_tabla += '</tbody></table>'
        st.markdown(html_tabla, unsafe_allow_html=True)

        # Botón de exportar
        if st.button("📥 Exportar a Excel", use_container_width=True):
            try:
                import pandas as pd
                from io import BytesIO

                df_export = []
                for inv in invoices_filtradas:
                    df_export.append({
                        "Comprobante": inv["invoice_number"],
                        "Monto": f"${inv['amount']:,.2f}",
                        "Vencimiento": inv["due_date"] if inv["due_date"] else "N/A",
                        "Pagado": f"${inv['amount'] - inv['saldo']:,.2f}",
                        "Saldo": f"${inv['saldo']:,.2f}",
                        "Estado": inv["estado"]
                    })

                df = pd.DataFrame(df_export)

                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Cobranzas', index=False)

                buffer.seek(0)

                st.download_button(
                    label="💾 Descargar Excel",
                    data=buffer,
                    file_name=f"SYNA_Cobranzas_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"❌ Error al exportar: {str(e)}")
    else:
        st.info("📭 No hay facturas con los filtros especificados")

    st.markdown("---")

    # Próximos vencimientos
    st.markdown("### 🕐 Próximos Vencimientos (30 días)")

    if vencimientos:
        for venc in vencimientos:
            st.markdown(f"""
            <div class="syna-section">
                <strong>{venc['invoice_number']}</strong>
                <br>
                Vencimiento: {venc['due_date']} | Saldo: ${venc['saldo']:,.2f}
                <br>
                <span style="color: #6B7280; font-size: 12px;">Estado: {venc['estado']}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ No hay facturas vencidas en los próximos 30 días")

    st.markdown("---")
    st.caption(f"✅ Actualizado: {datetime.now().strftime('%H:%M:%S')} | Acceso restringido")


def pantalla_syna_con_autenticacion_v2():
    """Pantalla de autenticación para Cintia."""

    estilos_viewer()

    st.markdown("""
    <div style="max-width: 400px; margin: 80px auto; text-align: center;">
        <h2 style="margin-bottom: 8px;">🔐 Acceso a Cobranzas SYNA</h2>
        <p style="color: #6B7280; font-size: 14px;">
            Ingresa la contraseña para acceder
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Obtener contraseña
    try:
        contraseña_correcta = st.secrets.get("syna_password", "SYNA2024")
    except:
        contraseña_correcta = "SYNA2024"

    # Formulario
    st.markdown('<div style="max-width: 400px; margin: 20px auto;">', unsafe_allow_html=True)

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

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.caption("Este panel es solo para consulta de estado de cobranzas SYNA")
