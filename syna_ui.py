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
import uuid
from urllib.parse import urlsplit, urlunsplit
from syna_db import (
    crear_invoice, obtener_invoices,
    crear_payment, obtener_payments, obtener_payment,
    crear_mapping,
    crear_credit, obtener_credits,
    calcular_balance_syna, obtener_proximos_vencimientos,
    obtener_audit_log
)

CONTAINER_KEY = "syna_root"
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

        {SCOPE} .stButton > button:hover {{
            background-color: var(--primary-dark) !important;
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

        {SCOPE} .syna-card-value.positive {{ color: var(--success) !important; }}
        {SCOPE} .syna-card-value.negative {{ color: var(--accent) !important; }}
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

        {SCOPE} .syna-debe  {{ background: var(--debe-bg);  color: var(--debe-text);  font-weight: 700; }}
        {SCOPE} .syna-haber {{ background: var(--haber-bg); color: var(--haber-text); font-weight: 700; }}

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


def pantalla_syna_viewer():
    """Pantalla SOLO lectura para Cintia - únicamente Balance."""
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
        html += f'<td>${inv["amount"]:,.2f}</td><td>{inv["invoice_date"] or "—"}</td>'
        html += f'<td><span class="syna-badge {clase}">{texto}</span></td></tr>'

    for cr in credits[:5]:
        estado = "Utilizada" if cr["used"] else "Disponible"
        clase = "syna-badge-verde" if not cr["used"] else "syna-badge-ambar"
        html += f'<tr><td><strong>{cr["credit_number"]}</strong></td><td>Nota de Crédito</td>'
        html += f'<td>${cr["amount"]:,.2f}</td><td>{cr["credit_date"] or "—"}</td>'
        html += f'<td><span class="syna-badge {clase}">{estado}</span></td></tr>'

    for pago in payments[:5]:
        numero_visible = pago.get("payment_number") or f"ODP-{pago['id']}"
        html += f'<tr><td><strong>{numero_visible}</strong></td><td>Orden de Pago</td>'
        html += f'<td>${pago["amount"]:,.2f}</td><td>{pago["payment_date"]}</td>'
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
    with st.form("odp_form", clear_on_submit=True):
        st.markdown("**Registrar orden de pago**")
        col1, col2 = st.columns(2)
        with col1:
            numero_odp = st.text_input("Número ODP", placeholder="ODP-2026-001")
        with col2:
            fecha_pago = st.date_input("Fecha")

        col1, col2 = st.columns(2)
        with col1:
            monto_pago = st.number_input("Monto ($)", min_value=0.0, step=100.0, format="%.2f")
        with col2:
            pagador = st.selectbox("Pagador", ["SYNA", "Blisterassist"])

        descripcion = st.text_area("Descripción", height=60)

        if st.form_submit_button("Registrar orden de pago", use_container_width=True):
            if monto_pago <= 0:
                st.error("El monto debe ser mayor a 0")
            else:
                try:
                    payment_id = crear_payment(
                        payment_date=fecha_pago.isoformat(), amount=monto_pago,
                        payer=pagador, description=descripcion, created_by="Dai",
                        payment_number=numero_odp
                    )
                    st.session_state.ultimo_pago_id = payment_id
                    st.session_state.monto_pago = monto_pago
                    st.success("Orden registrada. Aplicala a una o más facturas abajo para que impacte en Balance.")
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.get("ultimo_pago_id") and st.session_state.get("monto_pago", 0) > 0:
        st.markdown("##### Aplicar pago a facturas")

        payment = obtener_payment(st.session_state.ultimo_pago_id)
        if payment:
            monto_total = payment["amount"]
            st.markdown(f'<div class="syna-alert">Este pago (${monto_total:,.2f}) todavía NO afecta el saldo hasta que lo apliques a una factura.</div>', unsafe_allow_html=True)

            invoices = obtener_invoices()
            pendientes = [inv for inv in invoices if inv["saldo"] > 0]

            if pendientes:
                # IMPORTANTE: estos widgets van FUERA de un st.form a propósito.
                # Streamlit no re-renderiza el contenido de un form hasta el
                # submit, así que un checkbox dentro de un form nunca revela
                # un campo condicional (if sel: ...) en el mismo click: queda
                # marcado pero el campo "Aplicar" no aparece hasta el próximo
                # rerun. Con widgets sueltos, cada click sí dispara rerun.
                mapeos = []
                total_aplicado = 0
                for inv in pendientes:
                    c1, c2, c3 = st.columns([2, 1.3, 1.3])
                    with c1:
                        sel = st.checkbox(inv["invoice_number"], key=f"sel_{inv['id']}")
                    with c2:
                        st.write(f"Saldo: **${inv['saldo']:,.0f}**")
                    with c3:
                        if sel:
                            app = st.number_input("Aplicar", min_value=0.0, max_value=inv["saldo"],
                                                   step=100.0, key=f"app_{inv['id']}", format="%.2f")
                            if app > 0:
                                mapeos.append({"invoice_id": inv["id"], "amount": app})
                                total_aplicado += app

                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Monto de la orden", f"${monto_total:,.0f}")
                with c2:
                    st.metric("Total a aplicar", f"${total_aplicado:,.0f}")

                if st.button("Confirmar aplicación", use_container_width=True, key="confirmar_matching"):
                    if total_aplicado > monto_total:
                        st.error("El total aplicado excede el monto de la orden")
                    elif total_aplicado == 0:
                        st.error("Aplicá el pago a al menos una factura")
                    else:
                        for m in mapeos:
                            crear_mapping(m["invoice_id"], st.session_state.ultimo_pago_id, m["amount"])
                        st.success(f"${total_aplicado:,.2f} aplicados. Balance actualizado.")
                        del st.session_state.ultimo_pago_id
                        del st.session_state.monto_pago
                        for inv in pendientes:
                            st.session_state.pop(f"sel_{inv['id']}", None)
                            st.session_state.pop(f"app_{inv['id']}", None)
                        st.rerun()
            else:
                st.info("No hay facturas con saldo pendiente para aplicar este pago.")


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

    st.markdown("#### Estado general de cuenta")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""<div class="syna-card">
            <div class="syna-card-label">Total facturado</div>
            <div class="syna-card-value neutral">${balance['total_facturado']:,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="syna-card">
            <div class="syna-card-label">Notas de crédito</div>
            <div class="syna-card-value positive">-${balance['total_nc']:,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="syna-card">
            <div class="syna-card-label">Pagado (aplicado)</div>
            <div class="syna-card-value positive">-${balance['total_pagado']:,.0f}</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        color_class = "negative" if balance['saldo_pendiente'] > 0 else "positive"
        st.markdown(f"""<div class="syna-card">
            <div class="syna-card-label">Saldo pendiente</div>
            <div class="syna-card-value {color_class}">${balance['saldo_pendiente']:,.0f}</div>
        </div>""", unsafe_allow_html=True)

    if balance["pagos_sin_aplicar"] > 0:
        st.markdown(f'<div class="syna-alert">Hay ${balance["pagos_sin_aplicar"]:,.2f} en órdenes de pago registradas que todavía no fueron aplicadas a ninguna factura (no impactan el saldo hasta aplicarlas en la pestaña Comprobantes).</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Libro diario")

    if inv_filtradas or credits:
        html = '<table class="syna-table"><thead><tr>'
        html += '<th>Fecha</th><th>Comprobante</th><th>Debe</th><th>Haber</th><th>Saldo acumulado</th>'
        html += '</tr></thead><tbody>'

        movimientos = []
        for inv in inv_filtradas:
            movimientos.append((inv.get("invoice_date") or "", "debe", inv["invoice_number"], inv["amount"]))
        for cr in credits:
            movimientos.append((cr.get("credit_date") or "", "haber", cr["credit_number"], cr["amount"]))

        movimientos.sort(key=lambda m: m[0])

        saldo = 0
        for fecha, tipo, numero, monto in movimientos:
            html += f'<tr><td>{fecha or "—"}</td><td><strong>{numero}</strong></td>'
            if tipo == "debe":
                html += f'<td class="syna-debe">${monto:,.2f}</td><td></td>'
                saldo += monto
            else:
                html += f'<td></td><td class="syna-haber">${monto:,.2f}</td>'
                saldo -= monto
            html += f'<td>${saldo:,.2f}</td></tr>'

        html += '</tbody></table>'
        st.markdown(html, unsafe_allow_html=True)
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
                <span style="color:var(--text-body);"> · vence {v['due_date']} · saldo ${v['saldo']:,.2f}</span>
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
        html += f'<tr><td>{log["timestamp"][:16]}</td><td>{log["user"]}</td>'
        html += f'<td>{log["action"].replace("_", " ").title()}</td></tr>'
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)
