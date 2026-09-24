"""
SYNA Tracking - Database Module
Gestión de base de datos SQLite para tracking de facturas y pagos SYNA
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "syna_tracking.db"


def get_connection():
    """Obtiene conexión a la BD SQLite."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def inicializar_db():
    """Inicializa las 5 tablas de SYNA tracking."""
    conn = get_connection()
    cursor = conn.cursor()

    # TABLA 1: Facturas de Sancor
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS syna_invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_number TEXT UNIQUE NOT NULL,
        amount REAL NOT NULL,
        invoice_date TEXT,
        due_date TEXT,
        fixed_stamps REAL DEFAULT 0,
        email_link TEXT,
        created_at TEXT NOT NULL,
        created_by TEXT NOT NULL,
        notes TEXT,
        UNIQUE(invoice_number)
    )
    """)

    # TABLA 2: Órdenes de pago
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS syna_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_number TEXT,
        payment_date TEXT NOT NULL,
        amount REAL NOT NULL,
        payer TEXT NOT NULL,
        description TEXT,
        created_at TEXT NOT NULL,
        created_by TEXT NOT NULL
    )
    """)

    # Migración: agregar payment_number si la tabla ya existía sin esa columna
    cursor.execute("PRAGMA table_info(syna_payments)")
    columnas = [c[1] for c in cursor.fetchall()]
    if "payment_number" not in columnas:
        cursor.execute("ALTER TABLE syna_payments ADD COLUMN payment_number TEXT")

    # TABLA 3: Mapping entre facturas y pagos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS syna_invoice_payment_mapping (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        payment_id INTEGER NOT NULL,
        amount_applied REAL NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES syna_invoices(id),
        FOREIGN KEY (payment_id) REFERENCES syna_payments(id)
    )
    """)

    # TABLA 4: Notas de crédito
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS syna_credits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        credit_number TEXT UNIQUE NOT NULL,
        amount REAL NOT NULL,
        credit_date TEXT,
        used INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        created_by TEXT NOT NULL,
        UNIQUE(credit_number)
    )
    """)

    # TABLA 5: Auditoría
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS syna_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        user TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        details TEXT
    )
    """)

    conn.commit()
    conn.close()


# ============================================
# FUNCIONES PARA INVOICES
# ============================================

def crear_invoice(invoice_number, amount, invoice_date, due_date, fixed_stamps=0, email_link="", notes="", created_by="Dai"):
    """Crea una nueva factura Sancor."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        now = datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO syna_invoices
        (invoice_number, amount, invoice_date, due_date, fixed_stamps, email_link, created_at, created_by, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (invoice_number, amount, invoice_date, due_date, fixed_stamps, email_link, now, created_by, notes))

        conn.commit()
        invoice_id = cursor.lastrowid

        # Registrar en auditoría
        registrar_auditoria(conn, created_by, "invoice_added", {
            "invoice_number": invoice_number,
            "amount": amount,
            "due_date": due_date
        })

        return invoice_id
    except sqlite3.IntegrityError as e:
        conn.close()
        raise ValueError(f"Número de factura duplicado: {invoice_number}") from e
    finally:
        conn.close()


def obtener_invoices(filtro_estado=None):
    """Obtiene todas las facturas (con estado actualizado)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT i.id, i.invoice_number, i.amount, i.invoice_date, i.due_date,
           i.fixed_stamps, i.email_link, i.created_at, i.created_by, i.notes
    FROM syna_invoices i
    ORDER BY i.created_at DESC
    """)

    invoices = []
    for row in cursor.fetchall():
        invoice = dict(row)
        # Calcular saldo
        saldo = calcular_saldo_factura(invoice["id"])
        invoice["saldo"] = saldo
        invoice["estado"] = determinar_estado_factura(invoice["amount"], saldo)

        # Filtrar por estado si se especifica
        if filtro_estado is None or invoice["estado"] == filtro_estado:
            invoices.append(invoice)

    conn.close()
    return invoices


def calcular_saldo_factura(invoice_id):
    """Calcula el saldo pendiente de una factura."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COALESCE(SUM(amount_applied), 0) as total_applied
    FROM syna_invoice_payment_mapping
    WHERE invoice_id = ?
    """, (invoice_id,))

    result = cursor.fetchone()
    conn.close()

    total_applied = result["total_applied"] if result else 0

    # Obtener monto original
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT amount FROM syna_invoices WHERE id = ?", (invoice_id,))
    inv = cursor.fetchone()
    conn.close()

    if inv:
        return inv["amount"] - total_applied
    return 0


def determinar_estado_factura(amount, saldo):
    """Determina estado: Pagada / Parcialmente pagada / Impaga."""
    if saldo <= 0:
        return "Pagada"
    elif saldo < amount:
        return "Parcialmente pagada"
    else:
        return "Impaga"


def eliminar_invoice(invoice_id):
    """Elimina una factura (si no tiene pagos aplicados)."""
    conn = get_connection()
    cursor = conn.cursor()

    # Verificar si hay pagos asociados
    cursor.execute("""
    SELECT COUNT(*) as count FROM syna_invoice_payment_mapping WHERE invoice_id = ?
    """, (invoice_id,))

    result = cursor.fetchone()
    if result["count"] > 0:
        conn.close()
        raise ValueError("No se puede eliminar factura con pagos asociados")

    cursor.execute("DELETE FROM syna_invoices WHERE id = ?", (invoice_id,))
    conn.commit()
    conn.close()


# ============================================
# FUNCIONES PARA PAYMENTS
# ============================================

def crear_payment(payment_date, amount, payer, description="", created_by="Dai", payment_number=""):
    """Crea una nueva orden de pago."""
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO syna_payments (payment_number, payment_date, amount, payer, description, created_at, created_by)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (payment_number, payment_date, amount, payer, description, now, created_by))

    conn.commit()
    payment_id = cursor.lastrowid

    # Registrar en auditoría
    registrar_auditoria(conn, created_by, "payment_registered", {
        "payment_number": payment_number,
        "amount": amount,
        "payer": payer,
        "payment_date": payment_date
    })

    conn.close()
    return payment_id


def obtener_payments():
    """Obtiene todos los pagos."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, payment_number, payment_date, amount, payer, description, created_at, created_by
    FROM syna_payments
    ORDER BY payment_date DESC, id DESC
    """)

    payments = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return payments


def obtener_payment(payment_id):
    """Obtiene un pago específico."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM syna_payments WHERE id = ?", (payment_id,))
    result = cursor.fetchone()
    conn.close()

    return dict(result) if result else None


# ============================================
# FUNCIONES PARA MAPPING (Matching)
# ============================================

def crear_mapping(invoice_id, payment_id, amount_applied):
    """Crea un mapping entre factura y pago (vinculación)."""
    conn = get_connection()
    cursor = conn.cursor()

    # Validar que el monto no sea mayor al saldo de la factura
    saldo = calcular_saldo_factura(invoice_id)
    if amount_applied > saldo:
        conn.close()
        raise ValueError(f"Monto a aplicar ({amount_applied}) excede saldo pendiente ({saldo})")

    now = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO syna_invoice_payment_mapping (invoice_id, payment_id, amount_applied, created_at)
    VALUES (?, ?, ?, ?)
    """, (invoice_id, payment_id, amount_applied, now))

    conn.commit()
    conn.close()


def obtener_mappings_por_payment(payment_id):
    """Obtiene todos los mappings de un pago específico."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT m.id, m.invoice_id, m.payment_id, m.amount_applied, i.invoice_number, i.amount
    FROM syna_invoice_payment_mapping m
    JOIN syna_invoices i ON m.invoice_id = i.id
    WHERE m.payment_id = ?
    """, (payment_id,))

    mappings = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return mappings


def obtener_mappings_aplicados():
    """Todos los pagos aplicados a facturas, con la fecha y el número del
    pago y de la factura correspondiente. Para el libro diario: sin esto,
    el saldo acumulado del libro diario no incluye las órdenes de pago y
    no coincide con el saldo pendiente real (que sí las resta)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT m.id, m.amount_applied, p.payment_date, p.payment_number, p.id as payment_id,
           i.invoice_number
    FROM syna_invoice_payment_mapping m
    JOIN syna_payments p ON m.payment_id = p.id
    JOIN syna_invoices i ON m.invoice_id = i.id
    """)

    aplicados = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return aplicados


def eliminar_mapping(mapping_id):
    """Elimina un mapping."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM syna_invoice_payment_mapping WHERE id = ?", (mapping_id,))
    conn.commit()
    conn.close()


# ============================================
# FUNCIONES PARA CREDITS
# ============================================

def crear_credit(credit_number, amount, credit_date, used=False, created_by="Dai"):
    """Crea una nota de crédito."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        now = datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO syna_credits (credit_number, amount, credit_date, used, created_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (credit_number, amount, credit_date, 1 if used else 0, now, created_by))

        conn.commit()
        credit_id = cursor.lastrowid

        registrar_auditoria(conn, created_by, "credit_added", {
            "credit_number": credit_number,
            "amount": amount
        })

        return credit_id
    except sqlite3.IntegrityError as e:
        conn.close()
        raise ValueError(f"Número de NC duplicado: {credit_number}") from e
    finally:
        conn.close()


def obtener_credits():
    """Obtiene todas las notas de crédito."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, credit_number, amount, credit_date, used, created_at, created_by
    FROM syna_credits
    ORDER BY created_at DESC
    """)

    credits = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return credits


def marcar_credit_usado(credit_id, usado=True):
    """Marca una NC como utilizada o no."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE syna_credits SET used = ? WHERE id = ?
    """, (1 if usado else 0, credit_id))

    conn.commit()
    conn.close()


def eliminar_credit(credit_id):
    """Elimina una NC."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM syna_credits WHERE id = ?", (credit_id,))
    conn.commit()
    conn.close()


def eliminar_payment(payment_id):
    """Elimina una orden de pago (y sus mappings asociados)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM syna_invoice_payment_mapping WHERE payment_id = ?", (payment_id,))
    cursor.execute("DELETE FROM syna_payments WHERE id = ?", (payment_id,))
    conn.commit()
    conn.close()


# ============================================
# FUNCIONES PARA CÁLCULOS GENERALES
# ============================================

def calcular_balance_syna():
    """Calcula balance total SYNA: Facturas (debe) contra NC + pagos aplicados (haber).

    total_pagado usa el monto efectivamente APLICADO (matched) a facturas,
    no el bruto de syna_payments, para que el saldo general sea coherente
    con calcular_saldo_factura() de cada factura individual. Un pago
    registrado pero sin aplicar (matching pendiente) no reduce el saldo.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Total facturado (DEBE)
    cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM syna_invoices")
    total_facturado = cursor.fetchone()["total"]

    # Total notas de crédito (HABER) - reducen lo que SYNA debe
    cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM syna_credits")
    total_nc = cursor.fetchone()["total"]

    # Total bruto de órdenes de pago registradas (informativo)
    cursor.execute("SELECT COALESCE(SUM(amount), 0) as total FROM syna_payments")
    total_ordenes_pago = cursor.fetchone()["total"]

    # Total EFECTIVAMENTE aplicado a facturas (HABER real)
    cursor.execute("SELECT COALESCE(SUM(amount_applied), 0) as total FROM syna_invoice_payment_mapping")
    total_pagado_aplicado = cursor.fetchone()["total"]

    conn.close()

    saldo_pendiente = total_facturado - total_nc - total_pagado_aplicado

    return {
        "total_facturado": total_facturado,
        "total_nc": total_nc,
        "total_ordenes_pago": total_ordenes_pago,
        "total_pagado": total_pagado_aplicado,
        "pagos_sin_aplicar": total_ordenes_pago - total_pagado_aplicado,
        "saldo_pendiente": saldo_pendiente
    }


def obtener_proximos_vencimientos(dias=30):
    """Obtiene facturas que vencen en los próximos N días."""
    from datetime import datetime, timedelta

    conn = get_connection()
    cursor = conn.cursor()

    hoy = datetime.now().date().isoformat()
    futura = (datetime.now().date() + timedelta(days=dias)).isoformat()

    cursor.execute("""
    SELECT i.id, i.invoice_number, i.amount, i.due_date, i.created_at
    FROM syna_invoices i
    WHERE i.due_date BETWEEN ? AND ?
    ORDER BY i.due_date ASC
    """, (hoy, futura))

    vencimientos = []
    for row in cursor.fetchall():
        inv = dict(row)
        saldo = calcular_saldo_factura(inv["id"])
        inv["saldo"] = saldo
        inv["estado"] = determinar_estado_factura(inv["amount"], saldo)
        if saldo > 0:  # Solo mostrar si hay saldo pendiente
            vencimientos.append(inv)

    conn.close()
    return vencimientos


# ============================================
# FUNCIONES PARA AUDITORÍA
# ============================================

def registrar_auditoria(conn, user, action, details):
    """Registra una acción en el log de auditoría."""
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    cursor.execute("""
    INSERT INTO syna_audit_log (action, user, timestamp, details)
    VALUES (?, ?, ?, ?)
    """, (action, user, now, json.dumps(details)))

    conn.commit()


def obtener_audit_log():
    """Obtiene el histórico de auditoría."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, action, user, timestamp, details
    FROM syna_audit_log
    ORDER BY timestamp DESC
    """)

    logs = []
    for row in cursor.fetchall():
        log = dict(row)
        log["details"] = json.loads(log["details"]) if log["details"] else {}
        logs.append(log)

    conn.close()
    return logs


# ============================================
# INICIALIZACIÓN
# ============================================

if __name__ == "__main__":
    inicializar_db()
    print(f"✅ Base de datos SYNA creada en: {DB_PATH}")
