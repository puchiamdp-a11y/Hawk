"""
SYNA Tracking - Interfaz Streamlit v2 (Rediseño UX/UI Profesional)
Módulo de UI completamente rediseñado para Dai (admin)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from syna_db import (
    crear_invoice, obtener_invoices, calcular_saldo_factura,
    crear_payment, obtener_payments, obtener_payment,
    crear_mapping, obtener_mappings_por_payment,
    crear_credit, obtener_credits,
    calcular_balance_syna, obtener_proximos_vencimientos,
    obtener_audit_log
)


def estilos_globales():
    """Paleta de colores y estilos profesionales."""
    st.markdown("""
    <style>
        /* Colores principales */
        :root {
            --primary: #1E3A8A;
            --bg-main: #FFFFFF;
            --bg-secondary: #F8FAFC;
            --text-primary: #1F2937;
            --text-secondary: #6B7280;
            --debe: #FEE2E2;
            --debe-text: #DC2626;
            --haber: #DCFCE7;
            --haber-text: #16A34A;
            --estado-pagada: #D1FAE5;
            --estado-pagada-text: #047857;
            --estado-impaga: #FECACA;
            --estado-impaga-text: #991B1B;
            --estado-parcial: #FEF08A;
            --estado-parcial-text: #854D0E;
        }

        body {
            background-color: var(--bg-main);
            color: var(--text-primary);
        }

        h1, h2, h3 {
            color: var(--text-primary) !important;
            margin: 20px 0 8px 0 !important;
            padding: 0 !important;
        }

        h2 {
            font-size: 22px !important;
            font-weight: 600 !important;
        }

        h3 {
            font-size: 14px !important;
            font-weight: 600 !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-secondary) !important;
        }

        /* Secciones */
        .syna-section {
            background-color: var(--bg-secondary);
            padding: 16px;
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
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #D1D5DB;
        }

        .syna-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #E5E7EB;
        }

        /* Debe/Haber */
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

        /* Estados de comprobante */
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

        /* Cards de resumen */
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

        /* Botones */
        .stButton > button {
            background-color: var(--primary) !important;
            color: white !important;
            font-weight: 600 !important;
            border: none !important;
        }

        .stButton > button:hover {
            background-color: #0F2460 !important;
        }

        /* Radio buttons personalizados */
        .stRadio {
            margin-bottom: 16px;
        }

        /* Inputs */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stDateInput > div > div > input,
        .stSelectbox > div > div > select {
            border: 1px solid #D1D5DB !important;
            border-radius: 6px !important;
            padding: 8px 12px !important;
            font-size: 13px !important;
        }

        /* Checkboxes */
        .stCheckbox {
            margin: 8px 0;
        }
    </style>
    """, unsafe_allow_html=True)


def pantalla_syna_admin_v2():
    """Pantalla principal SYNA rediseñada para Dai (admin)."""
    estilos_globales()

    # Header pequeño
    st.markdown("""
    <div style="margin-bottom: 24px;">
        <h2 style="margin-bottom: 4px;">Cobranzas SYNA</h2>
        <p style="color: #6B7280; font-size: 14px; margin: 0;">
            Gestión de comprobantes y pagos SYNA
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Tabs
    tab_comprobantes, tab_pagos, tab_balance, tab_historico = st.tabs([
        "📋 Comprobantes",
        "💰 Pagos",
        "📊 Balance",
        "🕐 Histórico"
    ])

    with tab_comprobantes:
        tab_comprobantes_v2()

    with tab_pagos:
        tab_pagos_v2()

    with tab_balance:
        tab_balance_v2()

    with tab_historico:
        tab_historico_v2()


# ============================================
# TAB 1: COMPROBANTES (Rediseñado)
# ============================================

def tab_comprobantes_v2():
    """Tab para registrar comprobantes (FC + NC + ODP)."""

    st.markdown("### Registrar Comprobante")

    # Selector de tipo
    col1, col2, col3 = st.columns(3)
    with col1:
        es_factura = st.radio(
            "Tipo de comprobante",
            ["Factura Sancor", "Nota de Crédito", "Orden de Pago"],
            horizontal=False,
            label_visibility="collapsed"
        )

    st.markdown("---")

    # Formulario dinámico según tipo
    if es_factura == "Factura Sancor":
        form_factura_v2()
    elif es_factura == "Nota de Crédito":
        form_credito_v2()
    else:
        form_orden_pago_v2()

    # Tabla de últimos comprobantes
    st.markdown("---")
    st.markdown("### Últimos Comprobantes Registrados")

    invoices = obtener_invoices()
    credits = obtener_credits()
    payments = obtener_payments()

    # Combinar todos en una lista
    comprobantes = []

    for inv in invoices[:10]:
        comprobantes.append({
            "tipo": "FC",
            "numero": inv["invoice_number"],
            "monto": inv["amount"],
            "fecha": inv["invoice_date"],
            "estado": inv["estado"]
        })

    for cr in credits[:10]:
        comprobantes.append({
            "tipo": "NC",
            "numero": cr["credit_number"],
            "monto": cr["amount"],
            "fecha": cr["credit_date"],
            "estado": "Utilizada" if cr["used"] else "Disponible"
        })

    for pago in payments[:10]:
        comprobantes.append({
            "tipo": "ODP",
            "numero": f"ODP-{pago['id']}",
            "monto": pago["amount"],
            "fecha": pago["payment_date"],
            "estado": "Registrada"
        })

    if comprobantes:
        comprobantes.sort(key=lambda x: x.get("fecha", ""), reverse=True)

        html_tabla = '<table class="syna-table"><thead><tr>'
        html_tabla += '<th>Comprobante</th><th>Tipo</th><th>Monto</th><th>Fecha</th><th>Estado</th>'
        html_tabla += '</tr></thead><tbody>'

        for comp in comprobantes[:15]:
            html_tabla += '<tr>'
            html_tabla += f'<td style="font-weight: 600;">{comp["numero"]}</td>'
            html_tabla += f'<td>{comp["tipo"]}</td>'
            html_tabla += f'<td>${comp["monto"]:,.2f}</td>'
            html_tabla += f'<td>{comp["fecha"] if comp["fecha"] else "N/A"}</td>'

            # Estado con colores
            if comp["estado"] == "Pagada":
                html_tabla += '<td><span class="syna-estado-pagada">Pagada</span></td>'
            elif comp["estado"] == "Impaga":
                html_tabla += '<td><span class="syna-estado-impaga">Impaga</span></td>'
            elif comp["estado"] == "Parcialmente pagada":
                html_tabla += '<td><span class="syna-estado-parcial">Parcial</span></td>'
            else:
                html_tabla += f'<td>{comp["estado"]}</td>'

            html_tabla += '</tr>'

        html_tabla += '</tbody></table>'
        st.markdown(html_tabla, unsafe_allow_html=True)
    else:
        st.info("📭 No hay comprobantes registrados aún")


def form_factura_v2():
    """Formulario para registrar factura Sancor."""

    with st.form("form_factura_v2", clear_on_submit=True):
        # Datos básicos
        st.markdown("#### Datos Básicos")

        col1, col2 = st.columns(2)
        with col1:
            numero_fc = st.text_input(
                "Número FC",
                placeholder="FC-2026-001"
            )
        with col2:
            fecha_factura = st.date_input("Fecha de Factura")

        col3, col4 = st.columns(2)
        with col3:
            monto = st.number_input(
                "Monto Total ($)",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )
        with col4:
            fecha_vencimiento = st.date_input("Vencimiento (opcional)")

        # Detalles fiscales
        st.markdown("#### Detalles Fiscales")

        col5, col6 = st.columns(2)
        with col5:
            sellados_fijos = st.number_input(
                "Sellados Fijos (Sancor abona)",
                min_value=0.0,
                step=10.0,
                value=0.0,
                format="%.2f",
                help="Ej: $150"
            )
        with col6:
            sellados_variables = st.number_input(
                "Sellados Variables (Sancor abona)",
                min_value=0.0,
                step=10.0,
                value=0.0,
                format="%.2f",
                help="Ej: $80"
            )

        # Referencias
        st.markdown("#### Referencias")

        email_link = st.text_input(
            "Link a correo Sancor",
            placeholder="outlook.live.com/mail/...",
            help="Opcional"
        )

        notas = st.text_area(
            "Notas",
            placeholder="Ej: Garantía extendida modelo XYZ",
            height=60
        )

        submitted = st.form_submit_button("Registrar Factura", use_container_width=True)

        if submitted:
            if not numero_fc or monto <= 0:
                st.error("❌ Número de factura y monto son obligatorios")
            else:
                try:
                    crear_invoice(
                        invoice_number=numero_fc,
                        amount=monto,
                        invoice_date=fecha_factura.isoformat(),
                        due_date=fecha_vencimiento.isoformat() if fecha_vencimiento else None,
                        fixed_stamps=sellados_fijos + sellados_variables,
                        email_link=email_link,
                        notes=notas,
                        created_by="Dai"
                    )
                    st.success(f"✅ Factura {numero_fc} registrada correctamente")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ Error: {str(e)}")


def form_credito_v2():
    """Formulario para registrar nota de crédito."""

    with st.form("form_credito_v2", clear_on_submit=True):
        st.markdown("#### Datos Básicos")

        col1, col2 = st.columns(2)
        with col1:
            numero_nc = st.text_input(
                "Número NC",
                placeholder="NC-2026-001"
            )
        with col2:
            fecha_nc = st.date_input("Fecha de NC")

        monto_nc = st.number_input(
            "Monto ($)",
            min_value=0.0,
            step=100.0,
            format="%.2f"
        )

        st.markdown("#### Estado")
        utilizada = st.checkbox("Ya fue utilizada / aplicada")

        st.markdown("#### Referencias")
        email_link = st.text_input(
            "Link a correo Sancor",
            placeholder="outlook.live.com/mail/...",
            help="Opcional"
        )

        submitted = st.form_submit_button("Registrar NC", use_container_width=True)

        if submitted:
            if not numero_nc or monto_nc <= 0:
                st.error("❌ Número y monto son obligatorios")
            else:
                try:
                    crear_credit(
                        credit_number=numero_nc,
                        amount=monto_nc,
                        credit_date=fecha_nc.isoformat(),
                        used=utilizada,
                        created_by="Dai"
                    )
                    st.success(f"✅ Nota de Crédito {numero_nc} registrada")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ Error: {str(e)}")


def form_orden_pago_v2():
    """Formulario para registrar orden de pago."""

    with st.form("form_orden_pago_v2", clear_on_submit=True):
        st.markdown("#### Datos Básicos")

        col1, col2 = st.columns(2)
        with col1:
            numero_odp = st.text_input(
                "Número Comprobante",
                placeholder="ODP-2026-001"
            )
        with col2:
            fecha_pago = st.date_input("Fecha de Pago")

        col3, col4 = st.columns(2)
        with col3:
            monto_pago = st.number_input(
                "Monto Total ($)",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )
        with col4:
            pagador = st.selectbox(
                "¿Quién pagó?",
                ["SYNA", "Blisterassist"]
            )

        st.markdown("#### Referencias")
        link_comprobante = st.text_input(
            "Link a comprobante bancario",
            placeholder="link a PDF o transferencia",
            help="Opcional"
        )

        descripcion = st.text_area(
            "Descripción/Notas",
            placeholder="Ej: Transferencia banco X",
            height=60
        )

        submitted = st.form_submit_button("Registrar Orden de Pago", use_container_width=True)

        if submitted:
            if monto_pago <= 0:
                st.error("❌ Monto debe ser mayor a 0")
            else:
                try:
                    payment_id = crear_payment(
                        payment_date=fecha_pago.isoformat(),
                        amount=monto_pago,
                        payer=pagador,
                        description=descripcion,
                        created_by="Dai"
                    )
                    st.success(f"✅ Orden de Pago registrada (ID: {payment_id})")
                    st.session_state.ultimo_pago_id = payment_id
                    st.session_state.monto_pago_pendiente = monto_pago
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


# ============================================
# TAB 2: PAGOS (Rediseñado - Matching Interactivo)
# ============================================

def tab_pagos_v2():
    """Tab para matching de pagos a comprobantes."""

    if "ultimo_pago_id" in st.session_state and st.session_state.get("monto_pago_pendiente", 0) > 0:
        st.markdown("### Aplicar Pago a Comprobantes")

        payment = obtener_payment(st.session_state.ultimo_pago_id)
        if payment:
            monto_total = payment["amount"]

            st.markdown(f"""
            <div class="syna-section">
                <strong>Pago de ${monto_total:,.2f}</strong> registrado por {payment['payer']}
                <br>
                <span style="color: #6B7280; font-size: 13px;">Distribúyelo entre comprobantes</span>
            </div>
            """, unsafe_allow_html=True)

            # Obtener comprobantes pendientes
            invoices = obtener_invoices()
            facturas_pendientes = [inv for inv in invoices if inv["saldo"] > 0]

            if facturas_pendientes:
                with st.form("form_matching_v2"):
                    st.markdown("#### Selecciona y distribuye")

                    mappings = []
                    monto_aplicado_total = 0

                    # Tabla interactiva
                    col1, col2, col3, col4 = st.columns([1, 2, 1.5, 1.5])

                    with col1:
                        st.markdown("**☑**")
                    with col2:
                        st.markdown("**Comprobante**")
                    with col3:
                        st.markdown("**Saldo**")
                    with col4:
                        st.markdown("**Aplicar**")

                    st.markdown("---")

                    for inv in facturas_pendientes:
                        col1, col2, col3, col4 = st.columns([1, 2, 1.5, 1.5])

                        with col1:
                            seleccionar = st.checkbox(
                                "sel",
                                key=f"sel_{inv['id']}",
                                label_visibility="collapsed"
                            )

                        with col2:
                            st.markdown(f"**{inv['invoice_number']}**")

                        with col3:
                            st.markdown(f"${inv['saldo']:,.2f}")

                        with col4:
                            if seleccionar:
                                cantidad = st.number_input(
                                    "aplicar",
                                    min_value=0.0,
                                    max_value=inv["saldo"],
                                    step=100.0,
                                    value=0.0,
                                    key=f"aplicar_{inv['id']}",
                                    label_visibility="collapsed",
                                    format="%.2f"
                                )
                                if cantidad > 0:
                                    mappings.append({
                                        "invoice_id": inv["id"],
                                        "amount": cantidad
                                    })
                                    monto_aplicado_total += cantidad

                    st.markdown("---")

                    # Resumen
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown(f"""
                        <div class="syna-card">
                            <div class="syna-card-label">Monto Orden</div>
                            <div class="syna-card-value">${monto_total:,.0f}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.markdown(f"""
                        <div class="syna-card">
                            <div class="syna-card-label">Aplicado</div>
                            <div class="syna-card-value">${monto_aplicado_total:,.0f}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    with col3:
                        diferencia = monto_total - monto_aplicado_total
                        color = "#DC2626" if diferencia > 0 else "#16A34A"
                        st.markdown(f"""
                        <div class="syna-card">
                            <div class="syna-card-label">Pendiente</div>
                            <div class="syna-card-value" style="color: {color};">
                                ${diferencia:,.0f}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("---")

                    if st.form_submit_button("Confirmar Aplicación", use_container_width=True):
                        if monto_aplicado_total > monto_total:
                            st.error(f"❌ Suma de aplicaciones excede monto del pago")
                        elif monto_aplicado_total == 0:
                            st.error("❌ Debe aplicar al menos a un comprobante")
                        else:
                            try:
                                for mapping in mappings:
                                    crear_mapping(
                                        invoice_id=mapping["invoice_id"],
                                        payment_id=st.session_state.ultimo_pago_id,
                                        amount_applied=mapping["amount"]
                                    )

                                st.success(f"✅ Matching completado - ${monto_aplicado_total:,.2f} aplicados")
                                st.session_state.ultimo_pago_id = None
                                st.session_state.monto_pago_pendiente = 0
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
            else:
                st.info("✅ No hay comprobantes pendientes")
    else:
        st.info("📭 Registra una orden de pago en la tab 'Comprobantes' para hacer matching")


# ============================================
# TAB 3: BALANCE (Libro Diario Rediseñado)
# ============================================

def tab_balance_v2():
    """Tab con balance y libro diario profesional."""

    st.markdown("### Filtros")

    col1, col2, col3 = st.columns(3)

    with col1:
        fecha_desde = st.date_input("Desde", value=None, key="balance_desde")

    with col2:
        fecha_hasta = st.date_input("Hasta", value=None, key="balance_hasta")

    with col3:
        estado_filtro = st.selectbox(
            "Estado",
            ["Todas", "Pagadas", "Impagas", "Parcialmente pagadas"],
            key="balance_estado"
        )

    st.markdown("---")

    # Obtener datos
    balance = calcular_balance_syna()
    invoices = obtener_invoices()

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
    st.markdown("### Libro Diario")

    if invoices_filtradas:
        # Tabla libro diario
        html_tabla = '<table class="syna-table"><thead><tr>'
        html_tabla += '<th>Fecha</th><th>Comprobante</th><th>Debe ($)</th><th>Haber ($)</th><th>Saldo ($)</th>'
        html_tabla += '</tr></thead><tbody>'

        saldo_acum = 0
        for inv in sorted(invoices_filtradas, key=lambda x: x.get("invoice_date", "")):
            html_tabla += '<tr>'
            html_tabla += f'<td>{inv["invoice_date"] if inv["invoice_date"] else "N/A"}</td>'
            html_tabla += f'<td>{inv["invoice_number"]}</td>'

            # Debe (factura = aumento de deuda)
            html_tabla += f'<td class="syna-debe">${inv["amount"]:,.2f}</td>'
            html_tabla += f'<td></td>'

            saldo_acum += inv["amount"]
            html_tabla += f'<td class="syna-saldo">${saldo_acum:,.2f}</td>'
            html_tabla += '</tr>'

        # Totales
        html_tabla += '<tr style="background-color: #F3F4F6; font-weight: 700;">'
        html_tabla += '<td colspan="2">TOTALES</td>'
        html_tabla += f'<td class="syna-debe">${sum(inv["amount"] for inv in invoices_filtradas):,.2f}</td>'
        html_tabla += f'<td></td>'
        html_tabla += f'<td class="syna-saldo">${saldo_acum:,.2f}</td>'
        html_tabla += '</tr>'

        html_tabla += '</tbody></table>'
        st.markdown(html_tabla, unsafe_allow_html=True)
    else:
        st.info("📭 No hay facturas con los filtros especificados")

    # Próximos vencimientos
    st.markdown("---")
    st.markdown("### 🕐 Próximos Vencimientos (30 días)")

    vencimientos = obtener_proximos_vencimientos(dias=30)

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


# ============================================
# TAB 4: HISTÓRICO (Igual pero mejorado)
# ============================================

def tab_historico_v2():
    """Tab con histórico de auditoría."""

    st.markdown("### Histórico de Auditoría")

    logs = obtener_audit_log()

    if logs:
        html_tabla = '<table class="syna-table"><thead><tr>'
        html_tabla += '<th>Fecha/Hora</th><th>Usuario</th><th>Acción</th>'
        html_tabla += '</tr></thead><tbody>'

        for log in logs[:50]:
            html_tabla += '<tr>'
            html_tabla += f'<td>{log["timestamp"][:16]}</td>'
            html_tabla += f'<td>{log["user"]}</td>'
            html_tabla += f'<td>{log["action"].replace("_", " ").title()}</td>'
            html_tabla += '</tr>'

        html_tabla += '</tbody></table>'
        st.markdown(html_tabla, unsafe_allow_html=True)
    else:
        st.info("📭 No hay registros de auditoría")
