"""
SYNA Tracking v5 - Fixes Críticos
1. Link Cintia funcional
2. Cintia solo ve Balance
3. Ancho máximo centrado (layout)
4. Balance conectado a tiempo real
5. Balance gráfico mejorado
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

# ============================================
# CONFIG: Ancho máximo centrado + Layout
# ============================================
st.set_page_config(
    page_title="Cobranzas SYNA",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS para limitar ancho
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        max-width: 1200px;
        margin: 0 auto;
    }

    [data-testid="stSidebar"] {
        max-width: 280px;
    }
</style>
""", unsafe_allow_html=True)


def estilos_v5():
    """Paleta profesional con colores reales y jerarquía clara."""
    st.markdown("""
    <style>
        /* Colores principales */
        :root {
            --primary: #1E40AF;
            --primary-dark: #1E3A8A;
            --accent: #DC2626;
            --success: #16A34A;
            --bg-page: #FFFFFF;
            --bg-section: #F0F4F8;
            --text-h1: #0F172A;
            --text-h2: #1E293B;
            --text-h3: #334155;
            --text-body: #475569;
            --text-light: #64748B;
            --border: #E2E8F0;
            --debe: #FEE2E2;
            --debe-text: #991B1B;
            --haber: #DCFCE7;
            --haber-text: #166534;
        }

        body {
            background-color: var(--bg-page);
        }

        /* Encabezados */
        h1 {
            color: var(--text-h1) !important;
            font-size: 32px !important;
            font-weight: 700 !important;
            margin: 0 0 8px 0 !important;
            letter-spacing: -0.5px;
        }

        h2 {
            color: var(--text-h2) !important;
            font-size: 24px !important;
            font-weight: 700 !important;
            margin: 24px 0 12px 0 !important;
            padding-bottom: 8px;
            border-bottom: 3px solid var(--primary);
            display: inline-block;
        }

        h3 {
            color: var(--text-h3) !important;
            font-size: 14px !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin: 16px 0 8px 0 !important;
            color: var(--primary) !important;
        }

        p {
            color: var(--text-body) !important;
            font-size: 14px !important;
            line-height: 1.5 !important;
        }

        .subtitle {
            color: var(--text-light);
            font-size: 15px;
            margin: 0 0 20px 0;
        }

        /* Secciones */
        .syna-section {
            background-color: var(--bg-section);
            border-left: 4px solid var(--primary);
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border: 1px solid var(--border);
        }

        /* Formularios */
        .stForm {
            background-color: var(--bg-section) !important;
            padding: 24px !important;
            border-radius: 8px !important;
            border: 1px solid var(--border) !important;
            margin-bottom: 20px !important;
        }

        /* Labels */
        label {
            color: var(--text-h3) !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        /* Inputs */
        input, select, textarea {
            background-color: #FFFFFF !important;
            border: 1.5px solid var(--border) !important;
            border-radius: 6px !important;
            padding: 10px 12px !important;
            font-size: 14px !important;
            color: var(--text-body) !important;
        }

        input:focus, select:focus, textarea:focus {
            border-color: var(--primary) !important;
            box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1) !important;
        }

        /* Botones */
        .stButton > button {
            background-color: var(--primary) !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 10px 24px !important;
            border-radius: 6px !important;
            border: none !important;
            font-size: 14px !important;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            transition: all 0.2s;
        }

        .stButton > button:hover {
            background-color: var(--primary-dark) !important;
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(30, 40, 175, 0.3);
        }

        /* Cards de resumen */
        .syna-card {
            background: linear-gradient(135deg, var(--bg-section) 0%, #FFFFFF 100%);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }

        .syna-card-label {
            font-size: 12px;
            color: var(--text-light);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 8px;
        }

        .syna-card-value {
            font-size: 28px;
            font-weight: 700;
            color: var(--text-h1);
        }

        .syna-card-value.positive {
            color: var(--success) !important;
        }

        .syna-card-value.negative {
            color: var(--accent) !important;
        }

        /* Tabla */
        .syna-table {
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
            font-size: 13px;
            background: white;
            border-radius: 6px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }

        .syna-table th {
            background-color: var(--primary);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 700;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .syna-table td {
            padding: 12px;
            border-bottom: 1px solid var(--border);
            color: var(--text-body);
        }

        .syna-table tr:hover {
            background-color: var(--bg-section);
        }

        /* Estados */
        .syna-estado-pagada {
            background-color: #D1FAE5;
            color: #047857;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
        }

        .syna-estado-impaga {
            background-color: #FEE2E2;
            color: var(--debe-text);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
        }

        .syna-estado-parcial {
            background-color: #FEF3C7;
            color: #92400E;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
        }

        /* Debe/Haber */
        .syna-debe {
            background-color: #FEE2E2;
            color: var(--debe-text);
            font-weight: 700;
        }

        .syna-haber {
            background-color: #DCFCE7;
            color: var(--haber-text);
            font-weight: 700;
        }

        .syna-saldo {
            background-color: #EFF6FF;
            color: var(--primary-dark);
            font-weight: 700;
        }

        /* Filtros */
        .syna-filters-section {
            background: linear-gradient(135deg, #60A5FA 0%, #3B82F6 100%);
            color: #1F2937;
            padding: 24px;
            border-radius: 8px;
            margin-bottom: 24px;
        }

        .syna-filters-section h3 {
            color: #1F2937 !important;
            text-transform: uppercase;
            margin-top: 0 !important;
        }

        .syna-filters-section label {
            color: #1F2937 !important;
            font-weight: 600;
        }

        .syna-filters-section input,
        .syna-filters-section select {
            background-color: rgba(255, 255, 255, 0.98) !important;
            color: var(--text-body) !important;
        }

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            padding: 12px 24px !important;
            font-weight: 600 !important;
            border-bottom: 3px solid transparent !important;
        }

        .stTabs [aria-selected="true"] {
            border-color: var(--primary) !important;
            color: var(--primary) !important;
        }
    </style>
    """, unsafe_allow_html=True)


def generar_link_cintia():
    """Genera link funcional de Cintia con URL hardcodeada."""
    if "syna_access_token" not in st.session_state:
        st.session_state.syna_access_token = str(uuid.uuid4())[:12]

    if "syna_password" not in st.session_state:
        st.session_state.syna_password = "SYNA2024"

    # URL hardcodeada (cambiar según tu dominio)
    url_base = "https://hawk-app.example.com"  # CAMBIAR A URL REAL

    token = st.session_state.syna_access_token
    password = st.session_state.syna_password
    link = f"{url_base}?role=viewer&token={token}"

    return link, password


def pantalla_syna_admin_v5():
    """Pantalla principal - Admin con acceso total."""
    estilos_v5()

    st.markdown("""
    <h1>💼 Cobranzas SYNA</h1>
    <p class="subtitle">
        Gestión integral de comprobantes, pagos y balance •
        <span style="color: #10B981;">Sistema de control para cliente VIP</span>
    </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Tabs: Comprobantes, Balance, Histórico
    tab_comprobantes, tab_balance, tab_historico = st.tabs([
        "📋 Comprobantes",
        "📊 Balance",
        "🕐 Histórico"
    ])

    with tab_comprobantes:
        tab_comprobantes_v5()

    with tab_balance:
        tab_balance_v5()

    with tab_historico:
        tab_historico_v5()

    # Acceso Cintia al final
    st.markdown("---")
    st.markdown("### Acceso Cobranzas (Cintia)")

    link, password = generar_link_cintia()

    col1, col2 = st.columns([1, 1])
    with col1:
        st.write("**Link Acceso:**")
        st.code(link, language="text")

    with col2:
        st.write("**Contraseña:**")
        st.code(password, language="text")


def pantalla_syna_viewer_v5():
    """Pantalla SOLO para Cintia - SOLO BALANCE."""
    estilos_v5()

    st.markdown("""
    <h1>📊 Balance Cobranzas SYNA</h1>
    <p class="subtitle">
        Consulta de estado de facturas y balance pendiente (Lectura solo)
    </p>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # SOLO TAB DE BALANCE
    tab_balance_v5()


def pantalla_syna_con_autenticacion_v5():
    """Autenticación para Cintia."""
    estilos_v5()

    st.markdown("""
    <div style="max-width: 400px; margin: 80px auto; text-align: center;">
        <h2 style="border: none; display: block;">🔐 Acceso Cobranzas SYNA</h2>
        <p style="color: #6B7280; font-size: 14px; margin: 12px 0;">
            Ingresa la contraseña para acceder al balance
        </p>
    </div>
    """, unsafe_allow_html=True)

    contraseña_correcta = "SYNA2024"  # Cambiable

    st.markdown('<div style="max-width: 400px; margin: 20px auto;">', unsafe_allow_html=True)

    contraseña_ingresada = st.text_input("Contraseña", type="password", placeholder="Ingresa la contraseña")

    if st.button("Acceder", use_container_width=True):
        if contraseña_ingresada == contraseña_correcta:
            st.session_state.syna_authenticated = True
            st.rerun()
        else:
            st.error("❌ Contraseña incorrecta")

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================
# TAB 1: COMPROBANTES
# ============================================

def tab_comprobantes_v5():
    """Tab comprobantes - carga de facturas, NCs, ODPs."""

    st.markdown("### Tipo de Comprobante")

    col1, col2, col3 = st.columns(3)
    with col1:
        btn_factura = st.button("📄 Factura Sancor", use_container_width=True, key="type_factura")
    with col2:
        btn_nc = st.button("📝 Nota de Crédito", use_container_width=True, key="type_nc")
    with col3:
        btn_odp = st.button("💰 Orden de Pago", use_container_width=True, key="type_odp")

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

    tipo = st.session_state.comprobante_tipo

    if tipo == "Factura":
        form_factura_v5()
    elif tipo == "NC":
        form_nc_v5()
    else:
        form_odp_v5()

    st.markdown("---")
    st.markdown("### Últimos Comprobantes Registrados")

    invoices = obtener_invoices()
    credits = obtener_credits()
    payments = obtener_payments()

    if invoices or credits or payments:
        html = '<table class="syna-table"><thead><tr>'
        html += '<th>Comprobante</th><th>Tipo</th><th>Monto</th><th>Fecha</th><th>Estado</th>'
        html += '</tr></thead><tbody>'

        for inv in invoices[:10]:
            html += f'<tr><td><strong>{inv["invoice_number"]}</strong></td><td>FC</td>'
            html += f'<td>${inv["amount"]:,.2f}</td><td>{inv["invoice_date"] or "—"}</td>'
            if inv["estado"] == "Pagada":
                html += '<td><span class="syna-estado-pagada">Pagada</span></td></tr>'
            elif inv["estado"] == "Impaga":
                html += '<td><span class="syna-estado-impaga">Impaga</span></td></tr>'
            else:
                html += '<td><span class="syna-estado-parcial">Parcial</span></td></tr>'

        for cr in credits[:5]:
            html += f'<tr><td><strong>{cr["credit_number"]}</strong></td><td>NC</td>'
            html += f'<td>${cr["amount"]:,.2f}</td><td>{cr["credit_date"] or "—"}</td>'
            html += f'<td>{"Utilizada" if cr["used"] else "Disponible"}</td></tr>'

        for pago in payments[:5]:
            html += f'<tr><td><strong>ODP-{pago["id"]}</strong></td><td>ODP</td>'
            html += f'<td>${pago["amount"]:,.2f}</td><td>{pago["payment_date"]}</td>'
            html += '<td>Registrada</td></tr>'

        html += '</tbody></table>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("📭 Sin comprobantes registrados")


def form_factura_v5():
    """Formulario factura."""

    with st.form("factura_v5", clear_on_submit=True):
        st.markdown("### Registrar Factura")

        col1, col2 = st.columns(2)
        with col1:
            numero_fc = st.text_input("Número FC", placeholder="FC-2026-001", key="fc_numero")
        with col2:
            fecha_factura = st.date_input("Fecha", key="fc_fecha")

        col1, col2 = st.columns(2)
        with col1:
            monto = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f", key="fc_monto")
        with col2:
            fecha_vencimiento = st.date_input("Vencimiento", key="fc_venc")

        col1, col2 = st.columns(2)
        with col1:
            sf = st.number_input("Sellados Fijos ($)", min_value=0.0, step=10.0, value=0.0, format="%.2f", key="fc_sf")
        with col2:
            sv = st.number_input("Sellados Variables ($)", min_value=0.0, step=10.0, value=0.0, format="%.2f", key="fc_sv")

        email = st.text_input("Link Correo (opcional)", key="fc_email")
        notas = st.text_area("Notas", height=50, key="fc_notas")

        if st.form_submit_button("✅ Registrar", use_container_width=True):
            if not numero_fc or monto <= 0:
                st.error("❌ Número y monto obligatorios")
            else:
                try:
                    crear_invoice(
                        invoice_number=numero_fc,
                        amount=monto,
                        invoice_date=fecha_factura.isoformat(),
                        due_date=fecha_vencimiento.isoformat(),
                        fixed_stamps=sf + sv,
                        email_link=email,
                        notes=notas,
                        created_by="Dai"
                    )
                    st.success(f"✅ {numero_fc} registrada")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ Error: {str(e)}")


def form_nc_v5():
    """Formulario NC."""

    with st.form("nc_v5", clear_on_submit=True):
        st.markdown("### Registrar Nota de Crédito")

        col1, col2 = st.columns(2)
        with col1:
            numero_nc = st.text_input("Número NC", placeholder="NC-2026-001", key="nc_numero")
        with col2:
            fecha_nc = st.date_input("Fecha", key="nc_fecha")

        monto_nc = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f", key="nc_monto")
        utilizada = st.checkbox("Marcada como utilizada", key="nc_usada")

        if st.form_submit_button("✅ Registrar", use_container_width=True):
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
                    st.error(f"❌ Error: {str(e)}")


def form_odp_v5():
    """Formulario ODP."""

    with st.form("odp_v5", clear_on_submit=True):
        st.markdown("### Registrar Orden de Pago")

        col1, col2 = st.columns(2)
        with col1:
            numero_odp = st.text_input("Número ODP", placeholder="ODP-2026-001", key="odp_numero")
        with col2:
            fecha_pago = st.date_input("Fecha", key="odp_fecha")

        col1, col2 = st.columns(2)
        with col1:
            monto_pago = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f", key="odp_monto")
        with col2:
            pagador = st.selectbox("Pagador", ["SYNA", "Blisterassist"], key="odp_pagador")

        descripcion = st.text_area("Descripción", height=50, key="odp_desc")

        if st.form_submit_button("✅ Registrar", use_container_width=True):
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
                    st.error(f"❌ Error: {str(e)}")

    if "ultimo_pago_id" in st.session_state and st.session_state.get("monto_pago", 0) > 0:
        st.markdown("---")
        st.markdown("### Aplicar Pago a Facturas")

        payment = obtener_payment(st.session_state.ultimo_pago_id)
        if payment:
            monto_total = payment["amount"]
            st.info(f"💰 Distribuyendo pago de ${monto_total:,.2f}")

            invoices = obtener_invoices()
            pendientes = [inv for inv in invoices if inv["saldo"] > 0]

            if pendientes:
                with st.form("matching_v5"):
                    mapeos = []
                    total_aplicado = 0

                    for inv in pendientes:
                        col1, col2, col3 = st.columns([2, 1.5, 1.5])

                        with col1:
                            sel = st.checkbox(inv["invoice_number"], key=f"sel_{inv['id']}")
                        with col2:
                            st.write(f"**${inv['saldo']:,.0f}**")
                        with col3:
                            if sel:
                                app = st.number_input("Aplicar", min_value=0.0, max_value=inv["saldo"], step=100.0, key=f"app_{inv['id']}", format="%.2f")
                                if app > 0:
                                    mapeos.append({"invoice_id": inv["id"], "amount": app})
                                    total_aplicado += app

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Orden", f"${monto_total:,.0f}")
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
                                    crear_mapping(m["invoice_id"], st.session_state.ultimo_pago_id, m["amount"])
                                st.success(f"✅ ${total_aplicado:,.2f} aplicados")
                                del st.session_state.ultimo_pago_id
                                del st.session_state.monto_pago
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")


# ============================================
# TAB 2: BALANCE (TIEMPO REAL + GRÁFICO)
# ============================================

def tab_balance_v5():
    """Balance en tiempo real - conectado a comprobantes."""

    # FILTROS
    st.markdown("""
    <div class="syna-filters-section">
        <h3>🔍 Filtros</h3>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_desde = st.date_input("Desde", value=None, key="balance_desde")
    with col2:
        fecha_hasta = st.date_input("Hasta", value=None, key="balance_hasta")
    with col3:
        estado = st.selectbox("Estado", ["Todas", "Pagadas", "Impagas", "Parciales"], key="balance_estado")

    st.markdown("---")

    # OBTENER DATOS EN TIEMPO REAL
    balance = calcular_balance_syna()
    invoices = obtener_invoices()

    inv_filtradas = invoices

    if fecha_desde:
        inv_filtradas = [i for i in inv_filtradas if i["invoice_date"] and i["invoice_date"] >= fecha_desde.isoformat()]

    if fecha_hasta:
        inv_filtradas = [i for i in inv_filtradas if i["invoice_date"] and i["invoice_date"] <= fecha_hasta.isoformat()]

    if estado != "Todas":
        estado_map = {"Pagadas": "Pagada", "Impagas": "Impaga", "Parciales": "Parcialmente pagada"}
        inv_filtradas = [i for i in inv_filtradas if i["estado"] == estado_map.get(estado, "")]

    # RESUMEN - CARDS GRÁFICAS
    st.markdown("### Estado General de Cuenta")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""<div class="syna-card">
            <div class="syna-card-label">Facturas</div>
            <div class="syna-card-value">{len(invoices)}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""<div class="syna-card">
            <div class="syna-card-label">Total Facturado</div>
            <div class="syna-card-value">${balance['total_facturado']:,.0f}</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""<div class="syna-card">
            <div class="syna-card-label">Total Pagado</div>
            <div class="syna-card-value positive">${balance['total_pagado']:,.0f}</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        color_class = "negative" if balance['saldo_pendiente'] > 0 else "positive"
        st.markdown(f"""<div class="syna-card">
            <div class="syna-card-label">Saldo Pendiente</div>
            <div class="syna-card-value {color_class}">${balance['saldo_pendiente']:,.0f}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # DETALLES - Mostrar qué resta y qué suma
    st.markdown("### Libro Diario (Restas y Sumas)")

    if inv_filtradas:
        html = '<table class="syna-table"><thead><tr>'
        html += '<th>Fecha</th><th>Comprobante</th><th>Debe (Resta)</th><th>Haber (Suma)</th><th>Saldo Acum.</th>'
        html += '</tr></thead><tbody>'

        saldo = 0
        for inv in sorted(inv_filtradas, key=lambda x: x.get("invoice_date", "")):
            html += f'<tr><td>{inv["invoice_date"] or "—"}</td>'
            html += f'<td><strong>{inv["invoice_number"]}</strong></td>'
            html += f'<td class="syna-debe">${inv["amount"]:,.2f}</td>'
            html += f'<td></td>'
            saldo += inv["amount"]
            html += f'<td class="syna-saldo">${saldo:,.2f}</td></tr>'

        html += '</tbody></table>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.info("📭 Sin comprobantes")

    st.markdown("---")
    st.markdown("### Próximos Vencimientos (30 días)")

    vencimientos = obtener_proximos_vencimientos(30)

    if vencimientos:
        for v in vencimientos[:5]:
            st.markdown(f"""
            <div class="syna-section">
                <strong style="color: #DC2626;">{v['invoice_number']}</strong>
                <br>
                <span style="color: #334155;">Vence: {v['due_date']} • Saldo: ${v['saldo']:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ Sin vencimientos próximos")


# ============================================
# TAB 3: HISTÓRICO
# ============================================

def tab_historico_v5():
    """Histórico de auditoría."""

    st.markdown("### Registro de Auditoría")

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
