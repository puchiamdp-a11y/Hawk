"""
SYNA Tracking - Database Module
Gestión de base de datos SQLite para tracking de facturas y pagos SYNA
"""

import sqlite3
import json
import shutil
from datetime import datetime
from pathlib import Path
from io import BytesIO
import pandas as pd

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
        billing_month TEXT,
        category TEXT,
        UNIQUE(invoice_number)
    )
    """)

    # Migración: agregar billing_month/category si la tabla ya existía sin esas columnas
    cursor.execute("PRAGMA table_info(syna_invoices)")
    columnas_inv = [c[1] for c in cursor.fetchall()]
    if "billing_month" not in columnas_inv:
        cursor.execute("ALTER TABLE syna_invoices ADD COLUMN billing_month TEXT")
    if "category" not in columnas_inv:
        cursor.execute("ALTER TABLE syna_invoices ADD COLUMN category TEXT")

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

    # TABLA 3b: Mapping entre NC y pagos (separada de la de facturas
    # porque invoice_id sólo puede referenciar syna_invoices; aplicar un
    # pago a una NC usando la misma tabla causaba que se calculara el
    # saldo de una factura ajena con el mismo id numérico, o 0 si no
    # existía ninguna con ese id - de ahí el bug "excede saldo pendiente (0)"
    # al aplicar una ODP a una NC).
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS syna_credit_payment_mapping (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        credit_id INTEGER NOT NULL,
        payment_id INTEGER NOT NULL,
        amount_applied REAL NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (credit_id) REFERENCES syna_credits(id),
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
        billing_month TEXT,
        category TEXT,
        UNIQUE(credit_number)
    )
    """)

    # Migración: agregar billing_month/category si la tabla ya existía sin esas columnas
    cursor.execute("PRAGMA table_info(syna_credits)")
    columnas_cred = [c[1] for c in cursor.fetchall()]
    if "billing_month" not in columnas_cred:
        cursor.execute("ALTER TABLE syna_credits ADD COLUMN billing_month TEXT")
    if "category" not in columnas_cred:
        cursor.execute("ALTER TABLE syna_credits ADD COLUMN category TEXT")

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

def crear_invoice(invoice_number, amount, invoice_date, due_date, fixed_stamps=0, email_link="", notes="",
                   created_by="Dai", billing_month="", category=""):
    """Crea una nueva factura Sancor."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        now = datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO syna_invoices
        (invoice_number, amount, invoice_date, due_date, fixed_stamps, email_link, created_at, created_by, notes, billing_month, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (invoice_number, amount, invoice_date, due_date, fixed_stamps, email_link, now, created_by, notes, billing_month, category))

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
           i.fixed_stamps, i.email_link, i.created_at, i.created_by, i.notes,
           i.billing_month, i.category
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


def actualizar_invoice(invoice_id, invoice_number, amount, invoice_date, due_date,
                        fixed_stamps=0, email_link="", notes="", billing_month="", category=""):
    """Actualiza los datos de una factura existente."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        UPDATE syna_invoices
        SET invoice_number = ?, amount = ?, invoice_date = ?, due_date = ?,
            fixed_stamps = ?, email_link = ?, notes = ?, billing_month = ?, category = ?
        WHERE id = ?
        """, (invoice_number, amount, invoice_date, due_date, fixed_stamps, email_link, notes,
              billing_month, category, invoice_id))

        conn.commit()
        registrar_auditoria(conn, "Dai", "invoice_updated", {
            "invoice_id": invoice_id,
            "invoice_number": invoice_number,
            "amount": amount
        })
    except sqlite3.IntegrityError as e:
        conn.close()
        raise ValueError(f"Número de factura duplicado: {invoice_number}") from e
    finally:
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
    """Todos los pagos aplicados a facturas Y a NC, con la fecha y el
    número del pago y del comprobante correspondiente. Para el libro
    diario: sin esto, el saldo acumulado del libro diario no incluye las
    órdenes de pago y no coincide con el saldo pendiente real (que sí
    las resta). 'invoice_number' se reusa como nombre de columna para
    ambos casos (factura o NC) porque la UI del libro diario ya lo lee
    así, sin distinguir origen."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT m.id, m.amount_applied, p.payment_date, p.payment_number, p.id as payment_id,
           i.invoice_number
    FROM syna_invoice_payment_mapping m
    JOIN syna_payments p ON m.payment_id = p.id
    JOIN syna_invoices i ON m.invoice_id = i.id
    UNION ALL
    SELECT m.id, m.amount_applied, p.payment_date, p.payment_number, p.id as payment_id,
           c.credit_number as invoice_number
    FROM syna_credit_payment_mapping m
    JOIN syna_payments p ON m.payment_id = p.id
    JOIN syna_credits c ON m.credit_id = c.id
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


def crear_credit_mapping(credit_id, payment_id, amount_applied):
    """Crea un mapping entre NC y pago. Equivalente a crear_mapping() pero
    para syna_credit_payment_mapping - ver el comentario en esa tabla
    dentro de inicializar_db() para el porqué de la separación."""
    conn = get_connection()
    cursor = conn.cursor()

    saldo = calcular_saldo_credit(credit_id)
    if amount_applied > saldo:
        conn.close()
        raise ValueError(f"Monto a aplicar ({amount_applied}) excede saldo pendiente ({saldo})")

    now = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO syna_credit_payment_mapping (credit_id, payment_id, amount_applied, created_at)
    VALUES (?, ?, ?, ?)
    """, (credit_id, payment_id, amount_applied, now))

    conn.commit()
    conn.close()


def eliminar_credit_mapping(mapping_id):
    """Elimina un mapping de NC."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM syna_credit_payment_mapping WHERE id = ?", (mapping_id,))
    conn.commit()
    conn.close()


# ============================================
# FUNCIONES PARA CREDITS
# ============================================

def crear_credit(credit_number, amount, credit_date, used=False, created_by="Dai", billing_month="", category=""):
    """Crea una nota de crédito."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        now = datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO syna_credits (credit_number, amount, credit_date, used, created_at, created_by, billing_month, category)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (credit_number, amount, credit_date, 1 if used else 0, now, created_by, billing_month, category))

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


def calcular_saldo_credit(credit_id):
    """Calcula el saldo disponible de una NC (monto menos lo ya aplicado
    a órdenes de pago). Reemplaza el cálculo viejo 'amount - used', que
    restaba 0 o 1 (el booleano 'used') en vez del monto real aplicado."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COALESCE(SUM(amount_applied), 0) as total_applied
    FROM syna_credit_payment_mapping
    WHERE credit_id = ?
    """, (credit_id,))
    total_applied = cursor.fetchone()["total_applied"]

    cursor.execute("SELECT amount FROM syna_credits WHERE id = ?", (credit_id,))
    cr = cursor.fetchone()
    conn.close()

    if cr:
        return cr["amount"] - total_applied
    return 0


def obtener_credits():
    """Obtiene todas las notas de crédito (con saldo real disponible)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, credit_number, amount, credit_date, used, created_at, created_by, billing_month, category
    FROM syna_credits
    ORDER BY created_at DESC
    """)

    credits = [dict(row) for row in cursor.fetchall()]
    conn.close()

    for cr in credits:
        cr["saldo"] = calcular_saldo_credit(cr["id"])

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
    """Elimina una NC (si no tiene pagos aplicados)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*) as count FROM syna_credit_payment_mapping WHERE credit_id = ?
    """, (credit_id,))
    if cursor.fetchone()["count"] > 0:
        conn.close()
        raise ValueError("No se puede eliminar una NC con pagos aplicados")

    cursor.execute("DELETE FROM syna_credits WHERE id = ?", (credit_id,))
    conn.commit()
    conn.close()


def actualizar_credit(credit_id, credit_number, amount, credit_date, used=False, billing_month="", category=""):
    """Actualiza los datos de una NC existente."""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
        UPDATE syna_credits
        SET credit_number = ?, amount = ?, credit_date = ?, used = ?, billing_month = ?, category = ?
        WHERE id = ?
        """, (credit_number, amount, credit_date, 1 if used else 0, billing_month, category, credit_id))

        conn.commit()
        registrar_auditoria(conn, "Dai", "credit_updated", {
            "credit_id": credit_id,
            "credit_number": credit_number,
            "amount": amount
        })
    except sqlite3.IntegrityError as e:
        conn.close()
        raise ValueError(f"Número de NC duplicado: {credit_number}") from e
    finally:
        conn.close()


def eliminar_payment(payment_id):
    """Elimina una orden de pago (y sus mappings asociados, tanto a facturas como a NC)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM syna_invoice_payment_mapping WHERE payment_id = ?", (payment_id,))
    cursor.execute("DELETE FROM syna_credit_payment_mapping WHERE payment_id = ?", (payment_id,))
    cursor.execute("DELETE FROM syna_payments WHERE id = ?", (payment_id,))
    conn.commit()
    conn.close()


def actualizar_payment(payment_id, payment_number, payment_date, amount, payer, description=""):
    """Actualiza los datos de una orden de pago existente.

    No toca los mappings (aplicaciones a facturas/NC) ya registrados; si
    el usuario cambió el monto de forma que ya no cubre lo aplicado, eso
    queda igual que si lo hubiera aplicado él mismo - no se revierte nada
    automáticamente para no perder el historial de aplicaciones."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE syna_payments
    SET payment_number = ?, payment_date = ?, amount = ?, payer = ?, description = ?
    WHERE id = ?
    """, (payment_number, payment_date, amount, payer, description, payment_id))

    conn.commit()
    registrar_auditoria(conn, "Dai", "payment_updated", {
        "payment_id": payment_id,
        "payment_number": payment_number,
        "amount": amount
    })
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
# BACKUP / EXPORTACIÓN
# ============================================

def exportar_backup_excel():
    """Genera un backup completo en Excel (todas las tablas, una hoja por
    tabla) en memoria, para descargar desde la UI. No depende del estado
    del servidor: el usuario se lleva una copia propia de los datos."""
    conn = get_connection()

    hojas = {
        "Facturas": "SELECT * FROM syna_invoices ORDER BY id",
        "Notas de Credito": "SELECT * FROM syna_credits ORDER BY id",
        "Ordenes de Pago": "SELECT * FROM syna_payments ORDER BY id",
        "Aplicaciones (FC-OP)": "SELECT * FROM syna_invoice_payment_mapping ORDER BY id",
        "Aplicaciones (NC-OP)": "SELECT * FROM syna_credit_payment_mapping ORDER BY id",
        "Auditoria": "SELECT * FROM syna_audit_log ORDER BY id",
    }

    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for nombre_hoja, query in hojas.items():
            df = pd.read_sql_query(query, conn)
            df.to_excel(writer, sheet_name=nombre_hoja, index=False)

    conn.close()
    buffer.seek(0)
    return buffer.getvalue()


def crear_backup_archivo(destino_dir=None):
    """Copia el archivo .db completo a una carpeta de backups locales con
    timestamp en el nombre. Complementa exportar_backup_excel(): esta
    copia preserva el formato SQLite tal cual para una restauración 1:1."""
    if destino_dir is None:
        destino_dir = DB_PATH.parent / "backups"
    destino_dir = Path(destino_dir)
    destino_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destino = destino_dir / f"syna_tracking_{timestamp}.db"
    shutil.copy2(DB_PATH, destino)
    return destino


# ============================================
# INICIALIZACIÓN
# ============================================

if __name__ == "__main__":
    inicializar_db()
    print(f"✅ Base de datos SYNA creada en: {DB_PATH}")
