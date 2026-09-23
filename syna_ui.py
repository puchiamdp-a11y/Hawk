"""
SYNA Tracking - Interfaz Streamlit (módulo único, consolidado)

Todo el contenido de esta pantalla vive dentro de st.container(key="syna_root"),
que Streamlit renderiza como un <div class="... st-key-syna_root ...">
envolviendo realmente a los widgets hijos en el DOM. Todo el CSS de este
módulo está prefijado con ".st-key-syna_root" para que NUNCA se filtre
al sidebar ni al resto de la app Hawk. No definir aquí st.set_page_config()
(ya existe uno en app.py) ni CSS a nivel de módulo (fuera de una función):
eso se ejecuta en el import y contamina toda la app.
"""

import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
from syna_db import (
    crear_invoice, obtener_invoices,
    crear_payment, obtener_payments, obtener_payment,
    crear_mapping, obtener_mappings_aplicados,
    crear_credit, obtener_credits,
    calcular_balance_syna, obtener_proximos_vencimientos,
    obtener_audit_log
)

CONTAINER_KEY = "syna_root"


def _fmt_fecha(fecha_iso):
    """Convierte 'YYYY-MM-DD' (o un datetime ISO) a 'DD/MM/AAAA'."""
    if not fecha_iso:
        return "—"
    try:
        return datetime.fromisoformat(str(fecha_iso)[:10]).strftime("%d/%m/%Y")
    except ValueError:
        return str(fecha_iso)


def _fmt_fecha_hora(timestamp_iso):
    """Convierte un timestamp ISO completo a 'DD/MM/AAAA HH:MM'."""
    if not timestamp_iso:
        return "—"
    try:
        return datetime.fromisoformat(str(timestamp_iso)).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return str(timestamp_iso)
SCOPE = f".st-key-{CONTAINER_KEY}"


def _estilos():
    """CSS scoped exclusivamente al contenedor SYNA. Nunca selectores desnudos."""
    st.markdown(f"""
    <style>
        {SCOPE} {{
            --primary: #2563EB;
            --primary-dark: #1E3A8A;
            --accent: #DC2626;
            --success: #16A34A;
            --bg-section: #F8FAFC;
            --text-h1: #0F172A;
            --text-h2: #1E293B;
            --text-h3: #334155;
            --text-body: #475569;
            --text-light: #64748B;
            --border: #E2E8F0;
            --debe-bg: #FEF2F2;
            --debe-text: #B91C1C;
            --haber-bg: #F0FDF4;
            --haber-text: #15803D;
            max-width: 1100px;
            margin: 0 auto;
        }}

        {SCOPE} h1 {{
            color: var(--text-h1) !important;
            font-size: 28px !important;
            font-weight: 700 !important;
            margin: 0 0 4px 0 !important;
        }}

        {SCOPE} h2 {{
            color: var(--text-h2) !important;
            font-size: 20px !important;
            font-weight: 700 !important;
            margin: 4px 0 12px 0 !important;
        }}

        {SCOPE} h3 {{
            color: var(--text-h3) !important;
            font-size: 13px !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            margin: 4px 0 10px 0 !important;
        }}

        {SCOPE} p {{
            color: var(--text-body) !important;
            font-size: 14px !important;
        }}

        {SCOPE} .syna-banner {{
            background: linear-gradient(120deg, #1E3A8A 0%, #2563EB 60%, #3B82F6 100%);
            border-radius: 14px;
            padding: 22px 26px;
            margin-bottom: 20px;
            color: white;
        }}

        {SCOPE} .syna-banner h1 {{
            color: white !important;
        }}

        {SCOPE} .syna-banner p {{
            color: #DBEAFE !important;
            margin: 0 !important;
        }}

        {SCOPE} .syna-form-box {{
            background-color: var(--bg-section);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 18px 20px;
            margin-bottom: 16px;
        }}

        {SCOPE} label {{
            color: var(--text-h3) !important;
            font-weight: 600 !important;
            font-size: 12px !important;
        }}

        {SCOPE} .stButton > button {{
            background-color: var(--primary) !important;
            color: white !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 8px 18px !important;
        }}

        {SCOPE} .stButton > button * {{
            color: white !important;
        }}

        {SCOPE} .stButton > button:hover {{
            background-color: var(--primary-dark) !important;
        }}

        {SCOPE} .stButton > button:hover * {{
            color: white !important;
        }}

        {SCOPE} .syna-card {{
            background: #FFFFFF;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px 18px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
        }}

        {SCOPE} .syna-card-label {{
            font-size: 11px;
            color: var(--text-light);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            margin-bottom: 6px;
        }}

        {SCOPE} .syna-card-value {{
            font-size: 24px;
            font-weight: 700;
            color: var(--text-h1);
        }}

        {SCOPE} .syna-card-value.positive {{ color: var(--accent) !important; }}
        {SCOPE} .syna-card-value.negative {{ color: var(--success) !important; }}

        {SCOPE} .syna-card-total {{
            text-align: center;
            padding: 24px;
            margin-bottom: 12px;
            border-width: 2px;
        }}

        {SCOPE} .syna-card-value-big {{
            font-size: 42px;
            font-weight: 800;
            color: var(--text-h1);
        }}

        {SCOPE} .syna-card-value-big.positive {{ color: var(--accent) !important; }}
        {SCOPE} .syna-card-value-big.negative {{ color: var(--success) !important; }}
        {SCOPE} .syna-card-value.neutral  {{ color: var(--primary) !important; }}

        {SCOPE} .syna-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0 16px 0;
            font-size: 13px;
            background: white;
            border: 1px solid var(--border);
            border-radius: 10px;
            overflow: hidden;
        }}

        {SCOPE} .syna-table th {{
            background-color: var(--bg-section);
            color: var(--text-h3);
            padding: 10px 12px;
            text-align: left;
            font-weight: 700;
            font-size: 11px;
            text-transform: uppercase;
            border-bottom: 1px solid var(--border);
        }}

        {SCOPE} .syna-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
            color: var(--text-body);
        }}

        {SCOPE} .syna-badge {{
            padding: 3px 9px;
            border-radius: 999px;
            font-size: 11px;
            font-weight: 700;
            display: inline-block;
        }}

        {SCOPE} .syna-badge-verde {{ background: #DCFCE7; color: #15803D; }}
        {SCOPE} .syna-badge-rojo  {{ background: #FEE2E2; color: #B91C1C; }}
        {SCOPE} .syna-badge-ambar {{ background: #FEF3C7; color: #92400E; }}

        {SCOPE} .syna-debe  {{ background: var(--haber-bg); color: var(--haber-text); font-weight: 700; }}
        {SCOPE} .syna-haber {{ background: var(--debe-bg);  color: var(--debe-text);  font-weight: 700; }}

        {SCOPE} .syna-filters {{
            background: #EFF6FF;
            border: 1px solid #BFDBFE;
            border-radius: 12px;
            padding: 16px 18px;
            margin-bottom: 18px;
        }}

        {SCOPE} .syna-filters h3 {{
            color: var(--primary-dark) !important;
            margin-top: 0 !important;
        }}

        {SCOPE} .syna-alert {{
            background: #FFFBEB;
            border: 1px solid #FDE68A;
            border-left: 4px solid #F59E0B;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 13px;
            color: #92400E;
            margin-bottom: 14px;
        }}

        {SCOPE} .stTabs [data-baseweb="tab"] {{
            font-weight: 600 !important;
        }}
    </style>
    """, unsafe_allow_html=True)


def _link_cintia():
    """Construye el link real de acceso viewer, usando la URL real del servidor."""
    if "syna_access_token" not in st.session_state:
        st.session_state.syna_access_token = str(uuid.uuid4())[:12]
    if "syna_password" not in st.session_state:
        st.session_state.syna_password = "SYNA2024"

    try:
        parts = urlsplit(st.context.url)
        base = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    except Exception:
        base = ""

    token = st.session_state.syna_access_token
    password = st.session_state.syna_password
    link = f"{base}?role=viewer&token={token}" if base else f"?role=viewer&token={token}"
    return link, password, base


def pantalla_syna_admin():
    """Pantalla principal SYNA para Dai (acceso completo)."""
    with st.container(key=CONTAINER_KEY):
        _estilos()

        st.markdown("""
        <div class="syna-banner">
            <h1>Cobranzas SYNA</h1>
            <p>Gestión de comprobantes, pagos y balance del cliente VIP</p>
        </div>
        """, unsafe_allow_html=True)

        tab_comprobantes, tab_balance, tab_historico = st.tabs([
            "Comprobantes", "Balance", "Histórico"
        ])

        with tab_comprobantes:
            _tab_comprobantes()

        with tab_balance:
            _tab_balance()

        with tab_historico:
            _tab_historico()

        st.markdown("---")
        st.markdown("### Acceso Cobranzas (Cintia)")

        link, password, base = _link_cintia()

        if not base:
            st.warning("No se pudo detectar la URL del servidor automáticamente. Copiá la URL de la barra del navegador y agregá manualmente: `?role=viewer&token=...`")

        col1, col2 = st.columns([1, 1])
        with col1:
            st.write("**Link de acceso:**")
            st.code(link, language="text")
        with col2:
            st.write("**Contraseña:**")
            st.code(password, language="text")


def _ocultar_chrome_streamlit():
    """Oculta el menú hamburguesa, toolbar y footer nativos de Streamlit.

    Esto es lo único alcanzable por CSS desde acá: son elementos que viven
    en el mismo documento que la app. El "ícono de cuenta" que Streamlit
    Community Cloud puede superponer para el dueño del deployment (el
    selector rápido entre apps del mismo workspace) es un widget inyectado
    por la PLATAFORMA de hosting, fuera de este documento — ningún CSS o
    JS de la app puede alcanzarlo ni ocultarlo. Ese widget solo aparece
    cuando el navegador tiene una sesión iniciada en streamlit.io con la
    cuenta dueña del deployment; un visitante sin esa sesión (el caso
    normal de Cintia) no debería verlo nunca.
    """
    st.markdown("""
    <style>
        #MainMenu, header, footer,
        [data-testid="stToolbar"], [data-testid="stStatusWidget"],
        [data-testid="stDecoration"] {
            visibility: hidden !important;
            height: 0 !important;
        }
    </style>
    """, unsafe_allow_html=True)


def pantalla_syna_viewer():
    """Pantalla SOLO lectura para Cintia - únicamente Balance."""
    _ocultar_chrome_streamlit()
    with st.container(key=CONTAINER_KEY):
        _estilos()

        st.markdown("""
        <div class="syna-banner">
            <h1>Balance Cobranzas SYNA</h1>
            <p>Consulta de estado de cuenta (solo lectura)</p>
        </div>
        """, unsafe_allow_html=True)

        _tab_balance()


def pantalla_syna_con_autenticacion():
    """Autenticación simple para el acceso de Cintia."""
    _ocultar_chrome_streamlit()
    with st.container(key=CONTAINER_KEY):
        _estilos()

        st.markdown("""
        <div style="max-width:380px;margin:60px auto 0 auto;text-align:center;">
            <h1 style="font-size:22px !important;">Acceso Cobranzas SYNA</h1>
            <p>Ingresá la contraseña para ver el balance</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div style="max-width:380px;margin:16px auto 0 auto;">', unsafe_allow_html=True)
        contraseña_correcta = st.session_state.get("syna_password", "SYNA2024")
        ingresada = st.text_input("Contraseña", type="password", label_visibility="collapsed", placeholder="Contraseña")

        if st.button("Acceder", use_container_width=True):
            if ingresada == contraseña_correcta:
                st.session_state.syna_authenticated = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================
# TAB: COMPROBANTES
# ============================================

def _tab_comprobantes():
    st.markdown("#### Tipo de comprobante")

    if "comprobante_tipo" not in st.session_state:
        st.session_state.comprobante_tipo = "Factura"

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Factura Sancor", use_container_width=True, key="type_factura"):
            st.session_state.comprobante_tipo = "Factura"
            st.rerun()
    with col2:
        if st.button("Nota de Crédito", use_container_width=True, key="type_nc"):
            st.session_state.comprobante_tipo = "NC"
            st.rerun()
    with col3:
        if st.button("Orden de Pago", use_container_width=True, key="type_odp"):
            st.session_state.comprobante_tipo = "ODP"
            st.rerun()

    tipo = st.session_state.comprobante_tipo
    st.markdown(f'<div class="syna-badge syna-badge-ambar">Cargando: {tipo}</div>', unsafe_allow_html=True)
    st.write("")

    if tipo == "Factura":
        _form_factura()
    elif tipo == "NC":
        _form_nc()
    else:
        _form_odp()

    st.markdown("---")
    st.markdown("#### Últimos comprobantes registrados")

    invoices = obtener_invoices()
    credits = obtener_credits()
    payments = obtener_payments()

    if not (invoices or credits or payments):
        st.info("Todavía no hay comprobantes registrados.")
        return

    html = '<table class="syna-table"><thead><tr>'
    html += '<th>Comprobante</th><th>Tipo</th><th>Monto</th><th>Fecha</th><th>Estado</th></tr></thead><tbody>'

    badge_por_estado = {
        "Pagada": ("syna-badge-verde", "Pagada"),
        "Impaga": ("syna-badge-rojo", "Impaga"),
        "Parcialmente pagada": ("syna-badge-ambar", "Parcial"),
    }

    for inv in invoices[:10]:
        clase, texto = badge_por_estado.get(inv["estado"], ("syna-badge-ambar", inv["estado"]))
        html += f'<tr><td><strong>{inv["invoice_number"]}</strong></td><td>Factura</td>'
        html += f'<td>${inv["amount"]:,.2f}</td><td>{_fmt_fecha(inv["invoice_date"])}</td>'
        html += f'<td><span class="syna-badge {clase}">{texto}</span></td></tr>'

    for cr in credits[:5]:
        estado = "Utilizada" if cr["used"] else "Disponible"
        clase = "syna-badge-verde" if not cr["used"] else "syna-badge-ambar"
        html += f'<tr><td><strong>{cr["credit_number"]}</strong></td><td>Nota de Crédito</td>'
        html += f'<td>${cr["amount"]:,.2f}</td><td>{_fmt_fecha(cr["credit_date"])}</td>'
        html += f'<td><span class="syna-badge {clase}">{estado}</span></td></tr>'

    for pago in payments[:5]:
        numero_visible = pago.get("payment_number") or f"ODP-{pago['id']}"
        html += f'<tr><td><strong>{numero_visible}</strong></td><td>Orden de Pago</td>'
        html += f'<td>${pago["amount"]:,.2f}</td><td>{_fmt_fecha(pago["payment_date"])}</td>'
        html += '<td><span class="syna-badge syna-badge-verde">Registrada</span></td></tr>'

    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)


def _form_factura():
    with st.container():
        st.markdown('<div class="syna-form-box">', unsafe_allow_html=True)
        with st.form("factura_form", clear_on_submit=True):
            st.markdown("**Registrar factura**")
            col1, col2 = st.columns(2)
            with col1:
                numero_fc = st.text_input("Número FC", placeholder="FC-2026-001")
            with col2:
                fecha_factura = st.date_input("Fecha")

            col1, col2 = st.columns(2)
            with col1:
                monto = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f")
            with col2:
                fecha_vencimiento = st.date_input("Vencimiento")

            col1, col2 = st.columns(2)
            with col1:
                sf = st.number_input("Sellados fijos ($)", min_value=0.0, step=10.0, value=0.0, format="%.2f")
            with col2:
                sv = st.number_input("Sellados variables ($)", min_value=0.0, step=10.0, value=0.0, format="%.2f")

            email = st.text_input("Link correo (opcional)")
            notas = st.text_area("Notas", height=60)

            if st.form_submit_button("Registrar factura", use_container_width=True):
                if not numero_fc or monto <= 0:
                    st.error("Número y monto son obligatorios")
                else:
                    try:
                        crear_invoice(
                            invoice_number=numero_fc, amount=monto,
                            invoice_date=fecha_factura.isoformat(),
                            due_date=fecha_vencimiento.isoformat(),
                            fixed_stamps=sf + sv, email_link=email,
                            notes=notas, created_by="Dai"
                        )
                        st.success(f"{numero_fc} registrada. Ya está sumada en Balance.")
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
        st.markdown('</div>', unsafe_allow_html=True)


def _form_nc():
    st.markdown('<div class="syna-form-box">', unsafe_allow_html=True)
    with st.form("nc_form", clear_on_submit=True):
        st.markdown("**Registrar nota de crédito**")
        col1, col2 = st.columns(2)
        with col1:
            numero_nc = st.text_input("Número NC", placeholder="NC-2026-001")
        with col2:
            fecha_nc = st.date_input("Fecha")

        monto_nc = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f")
        utilizada = st.checkbox("Marcar como utilizada (informativo)")

        if st.form_submit_button("Registrar NC", use_container_width=True):
            if not numero_nc or monto_nc <= 0:
                st.error("Número y monto son obligatorios")
            else:
                try:
                    crear_credit(
                        credit_number=numero_nc, amount=monto_nc,
                        credit_date=fecha_nc.isoformat(), used=utilizada,
                        created_by="Dai"
                    )
                    st.success(f"{numero_nc} registrada. Ya está restando en Balance.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)


def _form_odp():
    st.markdown('<div class="syna-form-box">', unsafe_allow_html=True)
    st.markdown("**Registrar orden de pago + Aplicar a facturas/NC**")

    # Datos de la ODP
    col1, col2 = st.columns(2)
    with col1:
        numero_odp = st.text_input("Número ODP", placeholder="ODP-2026-001", key="numero_odp_input")
    with col2:
        fecha_pago = st.date_input("Fecha", key="fecha_pago_input")

    col1, col2 = st.columns(2)
    with col1:
        monto_pago = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f", key="monto_pago_input")
    with col2:
        pagador = st.selectbox("Pagador", ["SYNA", "Blisterassist"], key="pagador_input")

    descripcion = st.text_area("Descripción", height=60, key="descripcion_input")

    st.markdown("---")

    # Recopilar facturas y NC con saldo pendiente
    invoices = obtener_invoices()
    credits = obtener_credits()

    pendientes_fc = [inv for inv in invoices if inv["saldo"] > 0]
    pendientes_nc = [cred for cred in credits if cred["amount"] - cred.get("used", 0) > 0]

    # Combinar en lista única con tipo para identificarlos
    todos_pendientes = []
    for inv in pendientes_fc:
        todos_pendientes.append({
            "tipo": "FC",
            "id": inv["id"],
            "numero": inv["invoice_number"],
            "saldo": inv["saldo"],
            "data": inv
        })
    for cred in pendientes_nc:
        saldo_nc = cred["amount"] - cred.get("used", 0)
        todos_pendientes.append({
            "tipo": "NC",
            "id": cred["id"],
            "numero": cred["credit_number"],
            "saldo": saldo_nc,
            "data": cred
        })

    if todos_pendientes:
        st.markdown("##### Seleccionar documentos a pagar")

        # Multiselect con tipo + número + saldo
        opciones_display = [
            f"[{doc['tipo']}] {doc['numero']} - Saldo: ${doc['saldo']:,.0f}"
            for doc in todos_pendientes
        ]
        opciones_map = {display: doc for display, doc in zip(opciones_display, todos_pendientes)}

        seleccionadas_display = st.multiselect(
            "Documentos a pagar",
            opciones_display,
            key="odp_multiselect_docs"
        )

        if seleccionadas_display and monto_pago > 0:
            seleccionados = [opciones_map[d] for d in seleccionadas_display]

            # Calcular saldo total de documentos seleccionados
            saldo_total_docs = sum(doc["saldo"] for doc in seleccionados)

            # Calcular distribución proporcional del monto de la ODP
            st.write("")
            st.markdown("**Distribución automática del pago:**")

            mapeos = []
            for doc in seleccionados:
                # Calcular proporción: (saldo doc / saldo total) * monto ODP
                proporcion = doc["saldo"] / saldo_total_docs if saldo_total_docs > 0 else 0
                monto_asignado = min(proporcion * monto_pago, doc["saldo"])

                col1, col2, col3 = st.columns([2, 1.2, 1.2])
                with col1:
                    st.write(f"**{doc['numero']}**")
                with col2:
                    st.write(f"Saldo: ${doc['saldo']:,.0f}")
                with col3:
                    st.write(f"**${monto_asignado:,.0f}**")

                mapeos.append({
                    "tipo": doc["tipo"],
                    "id": doc["id"],
                    "amount": monto_asignado
                })

            total_aplicado = sum(m["amount"] for m in mapeos)

            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Monto de ODP", f"${monto_pago:,.0f}")
            with c2:
                st.metric("Total a aplicar", f"${total_aplicado:,.0f}")
            with c3:
                diferencia = monto_pago - total_aplicado
                st.metric("Sin aplicar", f"${diferencia:,.0f}")

            if st.button("Registrar y aplicar", use_container_width=True, key="registrar_y_aplicar"):
                if monto_pago <= 0:
                    st.error("El monto debe ser mayor a 0")
                elif total_aplicado == 0:
                    st.error("Selecciona al menos un documento para aplicar el pago")
                else:
                    try:
                        payment_id = crear_payment(
                            payment_date=fecha_pago.isoformat(), amount=monto_pago,
                            payer=pagador, description=descripcion, created_by="Dai",
                            payment_number=numero_odp
                        )
                        for m in mapeos:
                            crear_mapping(m["id"], payment_id, m["amount"])
                        st.success(f"Orden registrada y ${total_aplicado:,.2f} aplicados. Balance actualizado.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        elif not todos_pendientes:
            st.info("No hay documentos con saldo pendiente")
        else:
            st.info("Selecciona al menos un documento para ver la distribución")
    else:
        st.info("No hay facturas ni NC con saldo pendiente")

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================
# TAB: BALANCE
# ============================================

def _tab_balance():
    st.markdown("""
    <div class="syna-filters">
        <h3>Filtros</h3>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        fecha_desde = st.date_input("Desde", value=None, key="balance_desde")
    with col2:
        fecha_hasta = st.date_input("Hasta", value=None, key="balance_hasta")
    with col3:
        estado = st.selectbox("Estado", ["Todas", "Pagadas", "Impagas", "Parciales"], key="balance_estado")

    balance = calcular_balance_syna()
    # Defensivo: si alguna vez el dict viniera incompleto (versión vieja de
    # syna_db.py en un proceso que no se reinició tras un deploy, por
    # ejemplo), no tumbar toda la pantalla SYNA por un KeyError.
    for _clave, _default in [
        ("total_facturado", 0), ("total_nc", 0), ("total_pagado", 0),
        ("total_ordenes_pago", 0), ("pagos_sin_aplicar", 0), ("saldo_pendiente", 0),
    ]:
        balance.setdefault(_clave, _default)
    invoices = obtener_invoices()
    credits = obtener_credits()

    inv_filtradas = invoices
    if fecha_desde:
        inv_filtradas = [i for i in inv_filtradas if i["invoice_date"] and i["invoice_date"] >= fecha_desde.isoformat()]
    if fecha_hasta:
        inv_filtradas = [i for i in inv_filtradas if i["invoice_date"] and i["invoice_date"] <= fecha_hasta.isoformat()]
    if estado != "Todas":
        estado_map = {"Pagadas": "Pagada", "Impagas": "Impaga", "Parciales": "Parcialmente pagada"}
        inv_filtradas = [i for i in inv_filtradas if i["estado"] == estado_map.get(estado, "")]

    # Las NC se filtran solo por fecha (no tienen "estado" de factura):
    # así el filtro de período afecta a todo el libro diario por igual.
    credits_filtrados = credits
    if fecha_desde:
        credits_filtrados = [c for c in credits_filtrados if c["credit_date"] and c["credit_date"] >= fecha_desde.isoformat()]
    if fecha_hasta:
        credits_filtrados = [c for c in credits_filtrados if c["credit_date"] and c["credit_date"] <= fecha_hasta.isoformat()]

    hay_filtro_activo = bool(fecha_desde or fecha_hasta or estado != "Todas")

    # Las tarjetas de resumen reflejan lo que está filtrado, no el total
    # general: si hay un filtro activo, se recalculan sobre inv_filtradas
    # / credits_filtrados en vez de usar el balance global.
    total_facturado_view = sum(i["amount"] for i in inv_filtradas)
    total_pagado_view = sum(i["amount"] - i["saldo"] for i in inv_filtradas)
    total_nc_view = sum(c["amount"] for c in credits_filtrados)
    saldo_view = total_facturado_view - total_nc_view - total_pagado_view

    st.markdown("#### Estado general de cuenta")
    if hay_filtro_activo:
        st.caption("Mostrando el resultado con los filtros aplicados arriba.")

    # Tarjeta única y destacada: el número que importa (lo que SYNA debe
    # pagar realmente, ya con NC y pagos aplicados descontados). Todo lo
    # demás es el detalle de cómo se compone ese número.
    color_class = "negative" if saldo_view > 0 else "positive"
    st.markdown(f"""<div class="syna-card syna-card-total">
        <div class="syna-card-label">Total a pagar por SYNA (facturado − NC − pagado)</div>
        <div class="syna-card-value-big {color_class}">${saldo_view:,.0f}</div>
    </div>""", unsafe_allow_html=True)

    st.caption("Detalle de cómo se compone ese número:")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""<div class="syna-card">
            <div class="syna-card-label">Total facturado (bruto)</div>
            <div class="syna-card-value neutral">${total_facturado_view:,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="syna-card">
            <div class="syna-card-label">Menos: notas de crédito</div>
            <div class="syna-card-value positive">-${total_nc_view:,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="syna-card">
            <div class="syna-card-label">Menos: pagado (aplicado)</div>
            <div class="syna-card-value positive">-${total_pagado_view:,.0f}</div>
        </div>""", unsafe_allow_html=True)

    if balance["pagos_sin_aplicar"] > 0:
        st.markdown(f'<div class="syna-alert">Hay ${balance["pagos_sin_aplicar"]:,.2f} en órdenes de pago registradas que todavía no fueron aplicadas a ninguna factura (no impactan el saldo hasta aplicarlas en la pestaña Comprobantes).</div>', unsafe_allow_html=True)

    # Pagos aplicados a facturas, filtrados por la misma fecha que el
    # resto (fecha del pago, no de la factura): sin esto el libro diario
    # no restaba los pagos y su saldo final no coincidía con el de las
    # tarjetas de arriba (que sí los restan).
    aplicados_filtrados = obtener_mappings_aplicados()
    if fecha_desde:
        aplicados_filtrados = [a for a in aplicados_filtrados if a["payment_date"] and a["payment_date"] >= fecha_desde.isoformat()]
    if fecha_hasta:
        aplicados_filtrados = [a for a in aplicados_filtrados if a["payment_date"] and a["payment_date"] <= fecha_hasta.isoformat()]

    st.markdown("---")
    st.markdown("#### Libro diario")

    if inv_filtradas or credits_filtrados or aplicados_filtrados:
        movimientos = []
        for inv in inv_filtradas:
            movimientos.append((inv.get("invoice_date") or "", "debe", inv["invoice_number"], inv["amount"]))
        for cr in credits_filtrados:
            movimientos.append((cr.get("credit_date") or "", "haber", cr["credit_number"], cr["amount"]))
        for ap in aplicados_filtrados:
            numero_pago = ap.get("payment_number") or f"ODP-{ap['payment_id']}"
            etiqueta = f"{numero_pago} → {ap['invoice_number']}"
            movimientos.append((ap.get("payment_date") or "", "haber", etiqueta, ap["amount_applied"]))

        # El saldo acumulado se calcula UNA VEZ en orden cronológico real
        # (así tiene sentido contable) y queda fijo en cada fila; el
        # usuario puede después ordenar la tabla por cualquier columna
        # (clickeando el encabezado) sin que ese valor se recalcule.
        movimientos.sort(key=lambda m: m[0])

        filas = []
        saldo = 0
        for fecha, tipo, numero, monto in movimientos:
            # 0.0 en vez de NaN a propósito: en esta versión de Streamlit,
            # st.dataframe muestra el texto literal "None" para celdas NaN
            # sin importar el format (probado con y sin Styler, con varios
            # formatos incluyendo el default) - es una limitación del
            # componente, no de este código. Con 0.0 + estilo "color:
            # white" para esas celdas, la celda vacía queda visualmente en
            # blanco en vez de mostrar "None".
            if tipo == "debe":
                saldo += monto
                debe, haber = monto, 0.0
            else:
                saldo -= monto
                debe, haber = 0.0, monto
            filas.append({
                "Fecha": datetime.fromisoformat(fecha[:10]).date() if fecha else None,
                "Comprobante": numero,
                "Debe": debe,
                "Haber": haber,
                "Saldo acumulado": saldo,
            })

        df_libro = pd.DataFrame(filas)

        def _colorear_debe_haber(row):
            estilos = [""] * len(row)
            idx_debe = row.index.get_loc("Debe")
            idx_haber = row.index.get_loc("Haber")
            if row["Debe"] != 0:
                estilos[idx_debe] = "background-color: #F0FDF4; color: #15803D; font-weight: 700;"
            else:
                estilos[idx_debe] = "color: white;"
            if row["Haber"] != 0:
                estilos[idx_haber] = "background-color: #FEF2F2; color: #B91C1C; font-weight: 700;"
            else:
                estilos[idx_haber] = "color: white;"
            return estilos

        st.dataframe(
            df_libro.style.apply(_colorear_debe_haber, axis=1),
            column_config={
                "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                "Debe": st.column_config.NumberColumn("Debe", format="$ %,.2f"),
                "Haber": st.column_config.NumberColumn("Haber", format="$ %,.2f"),
                "Saldo acumulado": st.column_config.NumberColumn("Saldo acumulado", format="$ %,.2f"),
            },
            hide_index=True,
            use_container_width=True,
        )
        st.caption("Hacé click en el encabezado de una columna para ordenar la tabla por ella.")

        if abs(saldo - saldo_view) > 0.01:
            st.warning(f"El saldo acumulado del libro diario (${saldo:,.2f}) no coincide con el total a pagar de arriba (${saldo_view:,.2f}). Puede deberse a un pago aplicado fuera del rango de fechas filtrado.")
    else:
        st.info("Sin comprobantes para los filtros seleccionados.")

    st.markdown("---")
    st.markdown("#### Próximos vencimientos (30 días)")

    vencimientos = obtener_proximos_vencimientos(30)
    if vencimientos:
        for v in vencimientos[:5]:
            st.markdown(f"""
            <div class="syna-card" style="margin-bottom:8px;">
                <strong style="color:#B91C1C;">{v['invoice_number']}</strong>
                <span style="color:var(--text-body);"> · vence {_fmt_fecha(v['due_date'])} · saldo ${v['saldo']:,.2f}</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("Sin vencimientos próximos.")


# ============================================
# TAB: HISTÓRICO
# ============================================

def _tab_historico():
    st.markdown("#### Registro de auditoría")

    logs = obtener_audit_log()
    if not logs:
        st.info("Sin registros de auditoría.")
        return

    html = '<table class="syna-table"><thead><tr><th>Fecha/Hora</th><th>Usuario</th><th>Acción</th></tr></thead><tbody>'
    for log in logs[:50]:
        html += f'<tr><td>{_fmt_fecha_hora(log["timestamp"])}</td><td>{log["user"]}</td>'
        html += f'<td>{log["action"].replace("_", " ").title()}</td></tr>'
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)
