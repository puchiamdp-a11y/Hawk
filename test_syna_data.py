"""
Script de testing SYNA Tracking
Carga datos de prueba para verificar funcionalidades
"""

from datetime import datetime, timedelta
from syna_db import (
    inicializar_db,
    crear_invoice,
    crear_payment,
    crear_mapping,
    crear_credit,
    calcular_balance_syna,
    obtener_invoices,
    obtener_payments,
    obtener_proximos_vencimientos,
    obtener_audit_log
)


def cargar_datos_prueba():
    """Carga datos de prueba en la BD."""

    print("=" * 60)
    print("TESTING SYNA TRACKING - Carga de Datos de Prueba")
    print("=" * 60)

    # Inicializar BD
    inicializar_db()
    print("✅ BD inicializada\n")

    # ============================================
    # CREAR FACTURAS DE PRUEBA
    # ============================================
    print("📄 CREANDO FACTURAS SANCOR...")

    facturas = [
        {
            "numero": "FC-2026-001",
            "monto": 10000.00,
            "fecha": datetime(2026, 9, 15).date().isoformat(),
            "vencimiento": datetime(2026, 10, 15).date().isoformat(),
            "sellados": 50.00,
            "descripcion": "Garantías extendidas - Septiembre"
        },
        {
            "numero": "FC-2026-002",
            "monto": 5000.00,
            "fecha": datetime(2026, 9, 20).date().isoformat(),
            "vencimiento": datetime(2026, 9, 30).date().isoformat(),  # Próximo a vencer
            "sellados": 25.00,
            "descripcion": "Garantías extendidas - Componentes"
        },
        {
            "numero": "FC-2026-003",
            "monto": 8000.00,
            "fecha": datetime(2026, 9, 22).date().isoformat(),
            "vencimiento": datetime(2026, 10, 22).date().isoformat(),
            "sellados": 40.00,
            "descripcion": "Garantías extendidas - General"
        }
    ]

    invoice_ids = []
    for fc in facturas:
        inv_id = crear_invoice(
            invoice_number=fc["numero"],
            amount=fc["monto"],
            invoice_date=fc["fecha"],
            due_date=fc["vencimiento"],
            fixed_stamps=fc["sellados"],
            notes=fc["descripcion"],
            created_by="Dai"
        )
        invoice_ids.append(inv_id)
        print(f"  ✅ {fc['numero']}: ${fc['monto']:,.2f} (Vencimiento: {fc['vencimiento']})")

    print()

    # ============================================
    # CREAR PAGOS Y HACER MATCHING
    # ============================================
    print("💳 CREANDO ÓRDENES DE PAGO...")

    # Pago 1: $10,000 para FC-001
    pago1_id = crear_payment(
        payment_date=datetime(2026, 9, 25).date().isoformat(),
        amount=10000.00,
        payer="SYNA",
        description="Orden de pago #OP-2026-001",
        created_by="Dai"
    )
    crear_mapping(invoice_ids[0], pago1_id, 10000.00)
    print(f"  ✅ Pago $10,000 - SYNA (Aplicado a FC-2026-001)")

    # Pago 2: $5,000 para FC-002
    pago2_id = crear_payment(
        payment_date=datetime(2026, 9, 26).date().isoformat(),
        amount=5000.00,
        payer="SYNA",
        description="Orden de pago #OP-2026-002",
        created_by="Dai"
    )
    crear_mapping(invoice_ids[1], pago2_id, 5000.00)
    print(f"  ✅ Pago $5,000 - SYNA (Aplicado a FC-2026-002)")

    # Pago 3: $4,000 parcial para FC-003
    pago3_id = crear_payment(
        payment_date=datetime(2026, 9, 27).date().isoformat(),
        amount=4000.00,
        payer="Blisterassist",
        description="Orden de pago #OP-2026-003",
        created_by="Dai"
    )
    crear_mapping(invoice_ids[2], pago3_id, 4000.00)
    print(f"  ✅ Pago $4,000 - Blisterassist (Aplicado parcialmente a FC-2026-003)")

    print()

    # ============================================
    # CREAR NOTAS DE CRÉDITO
    # ============================================
    print("🎫 CREANDO NOTAS DE CRÉDITO...")

    crear_credit(
        credit_number="NC-2026-001",
        amount=500.00,
        credit_date=datetime(2026, 9, 20).date().isoformat(),
        used=False,
        created_by="Dai"
    )
    print(f"  ✅ NC-2026-001: $500.00 (Disponible)")

    crear_credit(
        credit_number="NC-2026-002",
        amount=300.00,
        credit_date=datetime(2026, 9, 22).date().isoformat(),
        used=True,
        created_by="Dai"
    )
    print(f"  ✅ NC-2026-002: $300.00 (Utilizada)")

    print()

    # ============================================
    # VERIFICAR RESULTADOS
    # ============================================
    print("=" * 60)
    print("VERIFICACIÓN DE DATOS")
    print("=" * 60)
    print()

    # Balance
    balance = calcular_balance_syna()
    print("💰 BALANCE TOTAL:")
    print(f"  • Total Facturado: ${balance['total_facturado']:,.2f}")
    print(f"  • Total Pagado: ${balance['total_pagado']:,.2f}")
    print(f"  • Saldo Pendiente: ${balance['saldo_pendiente']:,.2f}")
    print()

    # Facturas
    invoices = obtener_invoices()
    print(f"📄 FACTURAS ({len(invoices)}):")
    for inv in invoices:
        print(f"  • {inv['invoice_number']}: ${inv['amount']:,.2f} | "
              f"Saldo: ${inv['saldo']:,.2f} | Estado: {inv['estado']}")
    print()

    # Próximos vencimientos
    vencimientos = obtener_proximos_vencimientos(dias=30)
    print(f"📅 PRÓXIMOS VENCIMIENTOS ({len(vencimientos)}):")
    if vencimientos:
        for venc in vencimientos:
            print(f"  • {venc['invoice_number']}: Vencimiento {venc['due_date']} | "
                  f"Saldo: ${venc['saldo']:,.2f}")
    else:
        print("  ✅ No hay facturas vencidas en los próximos 30 días")
    print()

    # Auditoría
    logs = obtener_audit_log()
    print(f"📋 AUDITORÍA ({len(logs)} registros):")
    for log in logs[:10]:  # Primeros 10
        print(f"  • {log['timestamp'][:16]} | {log['user']} | {log['action']}")
    if len(logs) > 10:
        print(f"  ... y {len(logs) - 10} más")
    print()

    # ============================================
    # CHECKLIST DE VALIDACIONES
    # ============================================
    print("=" * 60)
    print("CHECKLIST DE VALIDACIONES")
    print("=" * 60)
    print()

    checks = []

    # Check 1: Total facturado
    checks.append(("Total facturado ($23,000)", balance['total_facturado'] == 23000.00))

    # Check 2: Total pagado
    checks.append(("Total pagado ($19,000)", balance['total_pagado'] == 19000.00))

    # Check 3: Saldo pendiente
    checks.append(("Saldo pendiente ($4,000)", balance['saldo_pendiente'] == 4000.00))

    # Check 4: FC-001 pagada
    fc001 = [inv for inv in invoices if inv['invoice_number'] == 'FC-2026-001'][0]
    checks.append(("FC-001 está Pagada", fc001['estado'] == 'Pagada' and fc001['saldo'] == 0))

    # Check 5: FC-002 pagada
    fc002 = [inv for inv in invoices if inv['invoice_number'] == 'FC-2026-002'][0]
    checks.append(("FC-002 está Pagada", fc002['estado'] == 'Pagada' and fc002['saldo'] == 0))

    # Check 6: FC-003 parcialmente pagada
    fc003 = [inv for inv in invoices if inv['invoice_number'] == 'FC-2026-003'][0]
    checks.append(("FC-003 está Parcialmente pagada",
                   fc003['estado'] == 'Parcialmente pagada' and fc003['saldo'] == 4000.00))

    # Check 7: Próximos vencimientos
    checks.append(("Próximos vencimientos detectados", len(vencimientos) > 0))

    # Check 8: Auditoría registra acciones
    checks.append(("Auditoría registra acciones", len(logs) >= 6))  # 3 invoices + 3 pagos

    # Imprimir checks
    for desc, resultado in checks:
        estado = "✅" if resultado else "❌"
        print(f"{estado} {desc}")

    print()
    print("=" * 60)
    total_checks = len(checks)
    passed_checks = sum(1 for _, r in checks if r)
    print(f"RESULTADO: {passed_checks}/{total_checks} validaciones pasadas")
    print("=" * 60)

    if passed_checks == total_checks:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON! Sistema listo para usar")
    else:
        print(f"\n⚠️ {total_checks - passed_checks} validaciones fallaron")

    return passed_checks == total_checks


if __name__ == "__main__":
    exito = cargar_datos_prueba()
    exit(0 if exito else 1)
