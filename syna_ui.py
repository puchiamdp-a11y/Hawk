"""
SYNA Tracking - Interfaz Streamlit
Módulo de UI para entrada de datos por Dai (admin)
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


def estilos_syna():
    """Aplica estilos CSS personalizados para SYNA."""
    st.markdown("""
    <style>
        .syna-header {
            background: linear-gradient(135deg, #1E3A8A 0%, #2E5AB5 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }

        .syna-header h2 {
            color: white !important;
            margin: 0 !important;
        }

        .syna-debe {
            color: #dc2626;
            opacity: 0.9;
            font-weight: bold;
        }

        .syna-haber {
            color: #16a34a;
            opacity: 0.9;
            font-weight: bold;
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


def pantalla_syna_admin():
    """Pantalla principal SYNA para Dai (admin)."""
    estilos_syna()

    st.markdown("""
    <div class="syna-header">
        <h2>📊 Cobranzas SYNA - Panel Administrativo</h2>
        <p>Gestión de facturas Sancor, órdenes de pago y notas de crédito</p>
    </div>
    """, unsafe_allow_html=True)

    # Inicializar session state para tabs
    if "syna_tab" not in st.session_state:
        st.session_state.syna_tab = "Facturas"

    # Tabs de navegación
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Facturas",
        "💳 Pagos",
        "🎫 Notas de Crédito",
        "📊 Balance",
        "📋 Histórico"
    ])

    with tab1:
        tab_facturas()

    with tab2:
        tab_pagos()

    with tab3:
        tab_creditos()

    with tab4:
        tab_balance()

    with tab5:
        tab_historico()


# ============================================
# TAB 1: FACTURAS
# ============================================

def tab_facturas():
    """Tab para registrar facturas Sancor."""
    st.subheader("Registrar Factura Sancor")

    with st.form("form_factura", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            numero_fc = st.text_input(
                "Número de Factura",
                placeholder="FC-001",
                help="Ej: FC-001, FC-002, etc."
            )
            monto = st.number_input(
                "Monto Total ($)",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )
            sellados = st.number_input(
                "Sellados Fijos ($)",
                min_value=0.0,
                step=10.0,
                value=0.0,
                format="%.2f"
            )

        with col2:
            fecha_factura = st.date_input("Fecha de Factura")
            fecha_vencimiento = st.date_input("Fecha de Vencimiento")
            email_link = st.text_input(
                "Link a Correo",
                placeholder="outlook.live.com/mail/...",
                help="Opcional: link al correo de Sancor"
            )

        notas = st.text_area(
            "Notas",
            placeholder="Observaciones adicionales...",
            height=60
        )

        submitted = st.form_submit_button("✅ Registrar Factura", use_container_width=True)

        if submitted:
            if not numero_fc or monto <= 0:
                st.error("❌ Número de factura y monto son obligatorios")
            else:
                try:
                    crear_invoice(
                        invoice_number=numero_fc,
                        amount=monto,
                        invoice_date=fecha_factura.isoformat(),
                        due_date=fecha_vencimiento.isoformat(),
                        fixed_stamps=sellados,
                        email_link=email_link,
                        notes=notas,
                        created_by="Dai"
                    )
                    st.success(f"✅ Factura {numero_fc} registrada correctamente")
                except ValueError as e:
                    st.error(f"❌ Error: {str(e)}")

    # Mostrar últimas facturas
    st.markdown("---")
    st.subheader("Últimas Facturas Registradas")

    invoices = obtener_invoices()

    if invoices:
        # Limitar a últimas 5
        invoices_display = invoices[:5]

        df_display = []
        for inv in invoices_display:
            df_display.append({
                "Número": inv["invoice_number"],
                "Monto": f"${inv['amount']:,.2f}",
                "Vencimiento": inv["due_date"] if inv["due_date"] else "N/A",
                "Saldo": f"${inv['saldo']:,.2f}",
                "Estado": inv["estado"]
            })

        df = pd.DataFrame(df_display)

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
        st.info("📭 No hay facturas registradas aún")


# ============================================
# TAB 2: PAGOS
# ============================================

def tab_pagos():
    """Tab para registrar pagos y hacer matching."""
    st.subheader("Registrar Orden de Pago")

    with st.form("form_pago", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            fecha_pago = st.date_input("Fecha de Pago")

        with col2:
            monto_pago = st.number_input(
                "Monto Pago ($)",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )

        with col3:
            pagador = st.selectbox(
                "¿Quién pagó?",
                ["SYNA", "Blisterassist"]
            )

        descripcion = st.text_area(
            "Descripción",
            placeholder="Ej: Orden de pago por garantías extendidas",
            height=60
        )

        submitted = st.form_submit_button("✅ Registrar Pago", use_container_width=True)

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
                    st.success(f"✅ Pago registrado (ID: {payment_id})")
                    st.session_state.ultimo_pago_id = payment_id
                    st.session_state.monto_pago_pendiente = monto_pago
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # Matching de pagos a facturas
    st.markdown("---")
    st.subheader("Aplicar Pago a Facturas")

    if "ultimo_pago_id" in st.session_state and st.session_state.get("monto_pago_pendiente", 0) > 0:
        payment = obtener_payment(st.session_state.ultimo_pago_id)
        if payment:
            monto_total = payment["amount"]
            st.info(f"💰 Pago de ${monto_total:,.2f} registrado - Aplicar a facturas:")

            # Obtener facturas impagadas o parcialmente pagadas
            invoices = obtener_invoices()
            facturas_pendientes = [inv for inv in invoices if inv["saldo"] > 0]

            if facturas_pendientes:
                with st.form("form_matching"):
                    mappings = []
                    monto_aplicado_total = 0

                    for inv in facturas_pendientes:
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.write(f"**{inv['invoice_number']}** - Saldo: ${inv['saldo']:,.2f}")

                        with col2:
                            cantidad = st.number_input(
                                "Aplicar",
                                min_value=0.0,
                                max_value=inv["saldo"],
                                step=100.0,
                                value=0.0,
                                key=f"matching_{inv['id']}",
                                format="%.2f"
                            )
                            if cantidad > 0:
                                mappings.append({
                                    "invoice_id": inv["id"],
                                    "amount": cantidad
                                })
                                monto_aplicado_total += cantidad

                    st.markdown("---")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Monto a aplicar:** ${monto_aplicado_total:,.2f}")

                    with col2:
                        if monto_aplicado_total > monto_total:
                            st.error(f"⚠️ Excede monto del pago (${monto_total:,.2f})")
                        else:
                            st.write(f"**Diferencia:** ${monto_total - monto_aplicado_total:,.2f}")

                    if st.form_submit_button("✅ Confirmar Matching", use_container_width=True):
                        if monto_aplicado_total > monto_total:
                            st.error(f"❌ Suma de aplicaciones excede monto del pago")
                        elif monto_aplicado_total == 0:
                            st.error("❌ Debe aplicar al menos a una factura")
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
                st.info("✅ No hay facturas pendientes")

    # Mostrar pagos recientes
    st.markdown("---")
    st.subheader("Pagos Registrados")

    payments = obtener_payments()
    if payments:
        payments_display = payments[:5]

        df_display = []
        for pago in payments_display:
            mappings = obtener_mappings_por_payment(pago["id"])
            monto_aplicado = sum(m["amount_applied"] for m in mappings)
            saldo_pago = pago["amount"] - monto_aplicado

            df_display.append({
                "Fecha": pago["payment_date"],
                "Monto": f"${pago['amount']:,.2f}",
                "Pagador": pago["payer"],
                "Aplicado": f"${monto_aplicado:,.2f}",
                "Saldo": f"${saldo_pago:,.2f}"
            })

        df = pd.DataFrame(df_display)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No hay pagos registrados aún")


# ============================================
# TAB 3: NOTAS DE CRÉDITO
# ============================================

def tab_creditos():
    """Tab para registrar notas de crédito."""
    st.subheader("Registrar Nota de Crédito")

    with st.form("form_credito", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            numero_nc = st.text_input(
                "Número NC",
                placeholder="NC-001"
            )

        with col2:
            monto_nc = st.number_input(
                "Monto ($)",
                min_value=0.0,
                step=100.0,
                format="%.2f"
            )

        with col3:
            fecha_nc = st.date_input("Fecha de NC")

        utilizada = st.checkbox("Ya está utilizada")

        submitted = st.form_submit_button("✅ Registrar NC", use_container_width=True)

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
                except ValueError as e:
                    st.error(f"❌ Error: {str(e)}")

    # Mostrar NCs registradas
    st.markdown("---")
    st.subheader("Notas de Crédito Registradas")

    credits = obtener_credits()

    if credits:
        df_display = []
        for nc in credits:
            estado = "Utilizada" if nc["used"] else "Disponible"
            df_display.append({
                "Número": nc["credit_number"],
                "Monto": f"${nc['amount']:,.2f}",
                "Fecha": nc["credit_date"] if nc["credit_date"] else "N/A",
                "Estado": estado
            })

        df = pd.DataFrame(df_display)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No hay notas de crédito registradas")


# ============================================
# TAB 4: BALANCE
# ============================================

def tab_balance():
    """Tab con visualización del balance."""
    st.subheader("Balance SYNA")

    # Obtener datos
    balance = calcular_balance_syna()
    vencimientos = obtener_proximos_vencimientos(dias=30)
    invoices = obtener_invoices()

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

    # Tabla de facturas
    st.markdown("---")
    st.subheader("Detalle de Facturas")

    if invoices:
        df_display = []
        for inv in invoices:
            df_display.append({
                "Número": inv["invoice_number"],
                "Monto": f"${inv['amount']:,.2f}",
                "Vencimiento": inv["due_date"] if inv["due_date"] else "N/A",
                "Pagado": f"${inv['amount'] - inv['saldo']:,.2f}",
                "Saldo": f"${inv['saldo']:,.2f}",
                "Estado": inv["estado"]
            })

        df = pd.DataFrame(df_display)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No hay facturas registradas")

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
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.success("✅ No hay facturas vencidas en los próximos 30 días")


# ============================================
# TAB 5: HISTÓRICO
# ============================================

def tab_historico():
    """Tab con histórico de auditoría."""
    st.subheader("Histórico de Auditoría")

    logs = obtener_audit_log()

    if logs:
        df_display = []
        for log in logs[:50]:  # Últimos 50 registros
            df_display.append({
                "Fecha/Hora": log["timestamp"][:16],
                "Usuario": log["user"],
                "Acción": log["action"],
                "Detalles": str(log["details"])
            })

        df = pd.DataFrame(df_display)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("📭 No hay registros de auditoría")
