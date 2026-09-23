"""
SYNA Tracking - Interfaz Streamlit v3 (Refinamientos Finales)
100% profesional, compacto, visual hierarchy clara
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from syna_db import (
    crear_invoice, obtener_invoices, calcular_saldo_factura,
    crear_payment, obtener_payments, obtener_payment,
    crear_mapping, obtener_mappings_por_payment,
    crear_credit, obtener_credits,
    calcular_balance_syna, obtener_proximos_vencimientos,
    obtener_audit_log
)


def estilos_globales_v3():
    """Paleta profesional con refinamientos finales."""
    st.markdown("""
    <style>
        /* Colores principales */
        :root {
            --primary: #1E3A8A;
            --bg-main: #FFFFFF;
            --bg-secondary: #F8FAFC;
            --text-primary: #1F2937;
            --text-secondary: #6B7280;
            --debe: #FEF5F5;
            --debe-text: #B91C1C;
            --haber: #F0FDF4;
            --haber-text: #15803D;
        }

        body {
            background-color: var(--bg-main);
            color: var(--text-primary);
        }

        h2, h3 {
            color: var(--text-primary) !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        h2 {
            font-size: 22px !important;
            font-weight: 600 !important;
            margin-bottom: 4px !important;
        }

        h3 {
            font-size: 12px !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary) !important;
            margin-bottom: 12px !important;
            margin-top: 16px !important;
        }

        /* Secciones compactas */
        .syna-section {
            background-color: var(--bg-secondary);
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 16px;
            border: 1px solid #E5E7EB;
        }

        .syna-section h3 {
            margin-top: 0 !important;
        }

        /* Tabla profesional */
        .syna-table {
            width: 100%;
            border-collapse: collapse;
            margin: 12px 0;
            font-size: 13px;
        }

        .syna-table th {
            background-color: var(--bg-secondary);
            color: var(--text-primary);
            padding: 10px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #D1D5DB;
            font-size: 12px;
        }

        .syna-table td {
            padding: 9px 10px;
            border-bottom: 1px solid #E5E7EB;
        }

        /* Debe/Haber SUTILES */
        .syna-debe {
            background-color: var(--debe);
            color: var(--debe-text);
            font-weight: 600;
        }

        .syna-haber {
            background-color: var(--haber);
            color: var(--haber-text);
            font-weight: 600;
        }

        .syna-saldo {
            background-color: var(--bg-secondary);
            color: var(--text-primary);
            font-weight: 600;
        }

        /* Estados */
        .syna-estado-pagada {
            background-color: #D1FAE5;
            color: #047857;
            padding: 3px 6px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }

        .syna-estado-impaga {
            background-color: #FECACA;
            color: #991B1B;
            padding: 3px 6px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }

        .syna-estado-parcial {
            background-color: #FEF08A;
            color: #854D0E;
            padding: 3px 6px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }

        /* Cards compactas */
        .syna-card {
            background-color: var(--bg-secondary);
            border: 1px solid #E5E7EB;
            border-radius: 8px;
            padding: 12px;
            text-align: center;
        }

        .syna-card-label {
            font-size: 11px;
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }

        .syna-card-value {
            font-size: 24px;
            font-weight: 700;
            color: var(--text-primary);
        }

        /* Botones toggle */
        .syna-toggle-button {
            padding: 10px 16px;
            border: 1px solid #E5E7EB;
            border-radius: 6px;
            background-color: #F3F4F6;
            color: var(--text-secondary);
            font-weight: 600;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
            flex: 1;
            text-align: center;
        }

        .syna-toggle-button:hover {
            background-color: #E5E7EB;
        }

        .syna-toggle-button.active {
            background-color: var(--primary);
            color: white;
            border-color: var(--primary);
        }

        /* Filtros sección */
        .syna-filters-section {
            background: linear-gradient(135deg, #1E3A8A 0%, #2E5AB5 100%);
            color: white;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 20px;
        }

        .syna-filters-section h3 {
            color: white !important;
            text-transform: none;
        }

        .syna-filters-section label {
            color: white;
            font-weight: 500;
            font-size: 12px;
        }

        /* Inputs compactos */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stDateInput > div > div > input,
        .stSelectbox > div > div > select {
            height: 36px !important;
            font-size: 12px !important;
        }

        /* Acceso Cintia */
        .syna-access-card {
            background-color: #DCFCE7;
            border: 1px solid #15803D;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 20px;
        }

        .syna-access-card h3 {
            color: #047857 !important;
        }

        .syna-access-link {
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            padding: 10px 12px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 11px;
            word-break: break-all;
            margin: 8px 0;
        }

        /* Grid compacto para formularios */
        .syna-form-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-bottom: 12px;
        }

        @media (max-width: 768px) {
            .syna-form-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
    """, unsafe_allow_html=True)


def pantalla_syna_admin_v3():
    """Pantalla principal SYNA v3 - 100% profesional."""
    estilos_globales_v3()

    # Header
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h2>Cobranzas SYNA</h2>
        <p style="color: #6B7280; font-size: 13px; margin: 0;">
            Gestión de comprobantes y pagos SYNA
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ACCESO CINTIA (Visible arriba)
    mostrar_acceso_cintia()

    st.markdown("---")

    # Tabs (sin Pagos)
    tab_comprobantes, tab_balance, tab_historico = st.tabs([
        "📋 Comprobantes",
        "📊 Balance",
        "🕐 Histórico"
    ])

    with tab_comprobantes:
        tab_comprobantes_v3()

    with tab_balance:
        tab_balance_v3()

    with tab_historico:
        tab_historico_v3()


def mostrar_acceso_cintia():
    """Muestra link y contraseña para Cintia."""

    # Generar token si no existe
    if "syna_access_token" not in st.session_state:
        st.session_state.syna_access_token = str(uuid.uuid4())[:12]

    if "syna_password" not in st.session_state:
        st.session_state.syna_password = "SYNA2024"

    token = st.session_state.syna_access_token
    password = st.session_state.syna_password

    # Construir URL
    url_base = st.request.base_url if hasattr(st, 'request') else "https://tu-app-url"
    link_cintia = f"{url_base}?role=viewer&token={token}"

    st.markdown(f"""
    <div class="syna-access-card">
        <h3>🔐 Acceso para Cobranzas (Cintia)</h3>
        <p style="color: #047857; font-size: 13px; margin: 8px 0;">
            Compartir este link y contraseña con el área de Cobranzas
        </p>

        <p style="color: #1F2937; font-weight: 600; font-size: 12px; margin-top: 12px;">Link:</p>
        <div class="syna-access-link">
            {link_cintia}
        </div>

        <p style="color: #1F2937; font-weight: 600; font-size: 12px; margin-top: 12px;">Contraseña:</p>
        <div class="syna-access-link">
            {password}
        </div>

        <p style="color: #6B7280; font-size: 11px; margin-top: 8px;">
            💡 Copia estos datos y comparte en Slack o correo
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Botones de copiar
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Copiar Link", use_container_width=True, key="copy_link"):
            st.info(f"Link copiado: {link_cintia}")

    with col2:
        if st.button("🔑 Copiar Contraseña", use_container_width=True, key="copy_pwd"):
            st.info(f"Contraseña copiada: {password}")


# ============================================
# TAB 1: COMPROBANTES (Unificado - SIN Tab Pagos)
# ============================================

def tab_comprobantes_v3():
    """Tab unificado para todos los comprobantes."""

    # Selector moderno (botones toggle)
    st.markdown("### Tipo de Comprobante")

    col1, col2, col3 = st.columns(3)
    with col1:
        btn_factura = st.button("📄 Factura Sancor", use_container_width=True,
                               key="type_factura")
    with col2:
        btn_nc = st.button("📝 Nota de Crédito", use_container_width=True,
                          key="type_nc")
    with col3:
        btn_odp = st.button("💰 Orden de Pago", use_container_width=True,
                           key="type_odp")

    # Determinar qué tipo está seleccionado
    if "comprobante_tipo" not in st.session_state:
        st.session_state.comprobante_tipo = "Factura"

    if btn_factura:
        st.session_state.comprobante_tipo = "Factura"
        st.rerun()
    elif btn_nc:
        st.session_state.comprobante_tipo = "NC"
        st.rerun()
    elif btn_odp:
        st.session_state.comprobante_tipo = "ODP"
        st.rerun()

    st.markdown("---")

    # Renderizar formulario según tipo
    tipo = st.session_state.comprobante_tipo

    if tipo == "Factura":
        form_factura_v3()
    elif tipo == "NC":
        form_nc_v3()
    else:
        form_odp_v3()

    # Tabla de últimos comprobantes
    st.markdown("---")
    st.markdown("### Últimos Comprobantes")

    invoices = obtener_invoices()
    credits = obtener_credits()
    payments = obtener_payments()

    if invoices or credits or payments:
        html = '<table class="syna-table"><thead><tr>'
        html += '<th>Comprobante</th><th>Tipo</th><th>Monto</th><th>Fecha</th><th>Estado</th>'
        html += '</tr></thead><tbody>'

        # Últimas 10 de cada tipo
        for inv in invoices[:10]:
            html += f'<tr><td><strong>{inv["invoice_number"]}</strong></td><td>FC</td>'
            html += f'<td>${inv["amount"]:,.2f}</td><td>{inv["invoice_date"] or "N/A"}</td>'
            if inv["estado"] == "Pagada":
                html += '<td><span class="syna-estado-pagada">Pagada</span></td></tr>'
            elif inv["estado"] == "Impaga":
                html += '<td><span class="syna-estado-impaga">Impaga</span></td></tr>'
            else:
                html += '<td><span class="syna-estado-parcial">Parcial</span></td></tr>'

        for cr in credits[:5]:
            html += f'<tr><td><strong>{cr["credit_number"]}</strong></td><td>NC</td>'
            html += f'<td>${cr["amount"]:,.2f}</td><td>{cr["credit_date"] or "N/A"}</td>'
            estado = "Utilizada" if cr["used"] else "Disponible"
            html += f'<td>{estado}</td></tr>'

        for pago in payments[:5]:
            html += f'<tr><td><strong>ODP-{pago["id"]}</strong></td><td>ODP</td>'
            html += f'<td>${pago["amount"]:,.2f}</td><td>{pago["payment_date"]}</td>'
            html += '<td>Registrada</td></tr>'

        html += '</tbody></table>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("📭 Sin comprobantes registrados")


def form_factura_v3():
    """Formulario factura - compacto."""

    with st.form("factura_v3", clear_on_submit=True):
        st.markdown("### Registrar Factura Sancor")

        # Grid 2 columnas
        st.markdown('<div class="syna-form-grid">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            numero_fc = st.text_input("Número FC", placeholder="FC-2026-001", key="fc_numero")
        with col2:
            fecha_factura = st.date_input("Fecha Factura", key="fc_fecha")

        st.markdown('</div><div class="syna-form-grid">', unsafe_allow_html=True)

        with col1:
            monto = st.number_input("Monto Total ($)", min_value=0.0, step=100.0,
                                   format="%.2f", key="fc_monto")
        with col2:
            fecha_vencimiento = st.date_input("Vencimiento", key="fc_venc")

        st.markdown('</div><div class="syna-form-grid">', unsafe_allow_html=True)

        with col1:
            sellados_fijos = st.number_input("Sellados Fijos", min_value=0.0,
                                            step=10.0, value=0.0, format="%.2f",
                                            key="fc_sf")
        with col2:
            sellados_var = st.number_input("Sellados Variables", min_value=0.0,
                                          step=10.0, value=0.0, format="%.2f",
                                          key="fc_sv")

        st.markdown('</div>')

        email_link = st.text_input("Link Correo (opcional)", key="fc_email")
        notas = st.text_area("Notas", height=40, key="fc_notas")

        if st.form_submit_button("✅ Registrar Factura", use_container_width=True):
            if not numero_fc or monto <= 0:
                st.error("❌ Número y monto obligatorios")
            else:
                try:
                    crear_invoice(
                        invoice_number=numero_fc,
                        amount=monto,
                        invoice_date=fecha_factura.isoformat(),
                        due_date=fecha_vencimiento.isoformat(),
                        fixed_stamps=sellados_fijos + sellados_var,
                        email_link=email_link,
                        notes=notas,
                        created_by="Dai"
                    )
                    st.success(f"✅ {numero_fc} registrada")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {str(e)}")


def form_nc_v3():
    """Formulario NC - compacto."""

    with st.form("nc_v3", clear_on_submit=True):
        st.markdown("### Registrar Nota de Crédito")

        st.markdown('<div class="syna-form-grid">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            numero_nc = st.text_input("Número NC", placeholder="NC-2026-001", key="nc_numero")
        with col2:
            fecha_nc = st.date_input("Fecha NC", key="nc_fecha")

        st.markdown('</div>')

        monto_nc = st.number_input("Monto ($)", min_value=0.0, step=100.0,
                                  format="%.2f", key="nc_monto")
        utilizada = st.checkbox("Ya fue utilizada", key="nc_usada")
        email_link = st.text_input("Link Correo (opcional)", key="nc_email")

        if st.form_submit_button("✅ Registrar NC", use_container_width=True):
            if not numero_nc or monto_nc <= 0:
                st.error("❌ Número y monto obligatorios")
            else:
                try:
                    crear_credit(
                        credit_number=numero_nc,
                        amount=monto_nc,
                        credit_date=fecha_nc.isoformat(),
                        used=utilizada,
                        created_by="Dai"
                    )
                    st.success(f"✅ {numero_nc} registrada")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ {str(e)}")


def form_odp_v3():
    """Formulario ODP - con matching compacto."""

    with st.form("odp_v3", clear_on_submit=True):
        st.markdown("### Registrar Orden de Pago")

        st.markdown('<div class="syna-form-grid">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            numero_odp = st.text_input("Número ODP", placeholder="ODP-2026-001", key="odp_numero")
        with col2:
            fecha_pago = st.date_input("Fecha Pago", key="odp_fecha")

        st.markdown('</div><div class="syna-form-grid">', unsafe_allow_html=True)

        with col1:
            monto_pago = st.number_input("Monto ($)", min_value=0.0, step=100.0,
                                        format="%.2f", key="odp_monto")
        with col2:
            pagador = st.selectbox("¿Quién pagó?", ["SYNA", "Blisterassist"], key="odp_pagador")

        st.markdown('</div>')

        descripcion = st.text_area("Descripción", height=40, key="odp_desc")

        if st.form_submit_button("✅ Registrar Orden de Pago", use_container_width=True):
            if monto_pago <= 0:
                st.error("❌ Monto debe ser > 0")
            else:
                try:
                    payment_id = crear_payment(
                        payment_date=fecha_pago.isoformat(),
                        amount=monto_pago,
                        payer=pagador,
                        description=descripcion,
                        created_by="Dai"
                    )
                    st.session_state.ultimo_pago_id = payment_id
                    st.session_state.monto_pago = monto_pago
                    st.success(f"✅ Orden registrada")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {str(e)}")

    # MATCHING (si hay pago pendiente)
    if "ultimo_pago_id" in st.session_state and st.session_state.get("monto_pago", 0) > 0:
        st.markdown("---")
        st.markdown("### Aplicar Pago a Facturas")

        payment = obtener_payment(st.session_state.ultimo_pago_id)
        if payment:
            monto_total = payment["amount"]
            st.info(f"💰 Pago de ${monto_total:,.2f} ({payment['payer']}) - Distribuir entre facturas")

            invoices = obtener_invoices()
            pendientes = [inv for inv in invoices if inv["saldo"] > 0]

            if pendientes:
                with st.form("matching_v3"):
                    mapeos = []
                    total_aplicado = 0

                    for inv in pendientes:
                        col1, col2, col3 = st.columns([2, 1.5, 1.5])

                        with col1:
                            sel = st.checkbox(inv["invoice_number"], key=f"sel_{inv['id']}")
                        with col2:
                            st.write(f"${inv['saldo']:,.0f}")
                        with col3:
                            if sel:
                                app = st.number_input("Aplicar", min_value=0.0,
                                                     max_value=inv["saldo"], step=100.0,
                                                     key=f"app_{inv['id']}", format="%.2f")
                                if app > 0:
                                    mapeos.append({"invoice_id": inv["id"], "amount": app})
                                    total_aplicado += app

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Monto Orden", f"${monto_total:,.0f}")
                    with col2:
                        st.metric("Aplicado", f"${total_aplicado:,.0f}")

                    if st.form_submit_button("✅ Confirmar", use_container_width=True):
                        if total_aplicado > monto_total:
                            st.error("❌ Excede monto")
                        elif total_aplicado == 0:
                            st.error("❌ Aplicar a algo")
                        else:
                            try:
                                for m in mapeos:
                                    crear_mapping(m["invoice_id"],
                                                st.session_state.ultimo_pago_id,
                                                m["amount"])
                                st.success(f"✅ ${total_aplicado:,.2f} aplicados")
                                del st.session_state.ultimo_pago_id
                                del st.session_state.monto_pago
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ {str(e)}")
            else:
                st.info("✅ Sin facturas pendientes")


# ============================================
# TAB 2: BALANCE (Libro Diario Refinado)
# ============================================

def tab_balance_v3():
    """Balance con filtros visuales."""

    # FILTROS SECCIÓN (con distintivo visual)
    st.markdown("""
    <div class="syna-filters-section">
        <h3>🔍 Filtros Avanzados</h3>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_desde = st.date_input("Desde", value=None, key="balance_desde")
    with col2:
        fecha_hasta = st.date_input("Hasta", value=None, key="balance_hasta")
    with col3:
        estado = st.selectbox("Estado", ["Todas", "Pagadas", "Impagas", "Parcialmente pagadas"],
                             key="balance_estado")

    st.markdown("---")

    # Datos
    balance = calcular_balance_syna()
    invoices = obtener_invoices()

    # Aplicar filtros
    inv_filtradas = invoices

    if fecha_desde:
        inv_filtradas = [i for i in inv_filtradas
                        if i["invoice_date"] and i["invoice_date"] >= fecha_desde.isoformat()]

    if fecha_hasta:
        inv_filtradas = [i for i in inv_filtradas
                        if i["invoice_date"] and i["invoice_date"] <= fecha_hasta.isoformat()]

    if estado != "Todas":
        estado_map = {"Pagadas": "Pagada", "Impagas": "Impaga",
                     "Parcialmente pagadas": "Parcialmente pagada"}
        inv_filtradas = [i for i in inv_filtradas if i["estado"] == estado_map[estado]]

    # Cards de resumen
    st.markdown("### Resumen")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""<div class="syna-card">
            <div class="syna-card-label">Total Facturado</div>
            <div class="syna-card-value">${balance['total_facturado']:,.0f}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""<div class="syna-card">
            <div class="syna-card-label">Total Pagado</div>
            <div class="syna-card-value" style="color: #15803D;">${balance['total_pagado']:,.0f}</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        color = "#B91C1C" if balance['saldo_pendiente'] > 0 else "#15803D"
        st.markdown(f"""<div class="syna-card">
            <div class="syna-card-label">Saldo Pendiente</div>
            <div class="syna-card-value" style="color: {color};">${balance['saldo_pendiente']:,.0f}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### Libro Diario")

    if inv_filtradas:
        html = '<table class="syna-table"><thead><tr>'
        html += '<th>Fecha</th><th>Comprobante</th><th>Debe ($)</th><th>Haber ($)</th><th>Saldo ($)</th>'
        html += '</tr></thead><tbody>'

        saldo = 0
        for inv in sorted(inv_filtradas, key=lambda x: x.get("invoice_date", "")):
            html += f'<tr><td>{inv["invoice_date"] or "N/A"}</td>'
            html += f'<td>{inv["invoice_number"]}</td>'
            html += f'<td class="syna-debe">${inv["amount"]:,.2f}</td><td></td>'
            saldo += inv["amount"]
            html += f'<td class="syna-saldo">${saldo:,.2f}</td></tr>'

        html += '</tbody></table>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("📭 Sin facturas")

    # Próximos vencimientos
    st.markdown("---")
    st.markdown("### 🕐 Próximos Vencimientos")

    vencimientos = obtener_proximos_vencimientos(30)

    if vencimientos:
        for v in vencimientos:
            st.markdown(f"**{v['invoice_number']}** • Venc: {v['due_date']} • Saldo: ${v['saldo']:,.2f}")
    else:
        st.success("✅ Sin vencimientos en 30 días")


# ============================================
# TAB 3: HISTÓRICO
# ============================================

def tab_historico_v3():
    """Histórico de auditoría."""

    st.markdown("### Histórico")

    logs = obtener_audit_log()

    if logs:
        html = '<table class="syna-table"><thead><tr>'
        html += '<th>Fecha/Hora</th><th>Usuario</th><th>Acción</th>'
        html += '</tr></thead><tbody>'

        for log in logs[:50]:
            html += f'<tr><td>{log["timestamp"][:16]}</td>'
            html += f'<td>{log["user"]}</td>'
            html += f'<td>{log["action"].replace("_", " ").title()}</td></tr>'

        html += '</tbody></table>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("📭 Sin registros")
