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

    # TABLA 3b (DEPRECADA, se mantiene solo para no perder datos ya
    # guardados con este modelo): mapping directo NC-pago. Reemplazada
    # por syna_invoice_credit_mapping más abajo: aplicar una NC contra
    # una ODP sin vincularla a una factura específica hacía que el
    # sistema repartiera el monto de la ODP en partes iguales entre
    # TODAS las facturas y NC seleccionadas, en vez de usar la NC para
    # netear contra la factura primero - por eso una ODP que cubría el
    # neto exacto (facturas menos NC) dejaba las facturas en "Parcial"
    # en lugar de saldarlas del todo.
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

    # TABLA 3c: mapping NC-factura (reemplaza el uso de la 3b). Una NC
    # aplicada acá reduce directamente el saldo de esa factura, igual
    # que el efectivo de una ODP - así "facturado - NC aplicada -
    # efectivo aplicado = saldo" da 0 cuando corresponde, en vez de
    # tratar la NC como si "compitiera" por una porción del monto de la
    # ODP igual que una factura. payment_id es solo trazabilidad (en
    # qué ODP se hizo esta aplicación), el monto de la NC no sale del
    # monto de esa ODP.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS syna_invoice_credit_mapping (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER NOT NULL,
        credit_id INTEGER NOT NULL,
        payment_id INTEGER,
        amount_applied REAL NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (invoice_id) REFERENCES syna_invoices(id),
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
        efectivo_aplicado, nc_aplicada = calcular_aplicado_factura(invoice["id"])
        saldo = invoice["amount"] - efectivo_aplicado - nc_aplicada
        invoice["saldo"] = saldo
        invoice["efectivo_aplicado"] = efectivo_aplicado
        invoice["nc_aplicada"] = nc_aplicada
        invoice["estado"] = determinar_estado_factura(invoice["amount"], saldo)

        # Filtrar por estado si se especifica
        if filtro_estado is None or invoice["estado"] == filtro_estado:
            invoices.append(invoice)

    conn.close()
    return invoices


def calcular_aplicado_factura(invoice_id):
    """Devuelve (efectivo_aplicado, nc_aplicada) por separado para una
    factura. Separado de calcular_saldo_factura() porque el balance
    general ya resta el total de NC aparte (total_nc): sumar ahí
    también lo aplicado a facturas incluyendo NC duplicaría esa resta,
    por eso el balance necesita poder tomar solo la parte en efectivo."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COALESCE(SUM(amount_applied), 0) as total_applied
    FROM syna_invoice_payment_mapping
    WHERE invoice_id = ?
    """, (invoice_id,))
    total_efectivo = cursor.fetchone()["total_applied"]

    cursor.execute("""
    SELECT COALESCE(SUM(amount_applied), 0) as total_applied
    FROM syna_invoice_credit_mapping
    WHERE invoice_id = ?
    """, (invoice_id,))
    total_nc_aplicada = cursor.fetchone()["total_applied"]

    conn.close()
    return total_efectivo, total_nc_aplicada


def calcular_saldo_factura(invoice_id):
    """Calcula el saldo pendiente de una factura: monto menos efectivo
    aplicado (vía ODP) menos NC aplicada directamente a ella."""
    total_efectivo, total_nc_aplicada = calcular_aplicado_factura(invoice_id)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT amount FROM syna_invoices WHERE id = ?", (invoice_id,))
    inv = cursor.fetchone()
    conn.close()

    if inv:
        return inv["amount"] - total_efectivo - total_nc_aplicada
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
    """Elimina una factura (si no tiene pagos ni NC aplicados)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*) as count FROM syna_invoice_payment_mapping WHERE invoice_id = ?
    """, (invoice_id,))
    if cursor.fetchone()["count"] > 0:
        conn.close()
        raise ValueError("No se puede eliminar factura con pagos asociados")

    cursor.execute("""
    SELECT COUNT(*) as count FROM syna_invoice_credit_mapping WHERE invoice_id = ?
    """, (invoice_id,))
    if cursor.fetchone()["count"] > 0:
        conn.close()
        raise ValueError("No se puede eliminar factura con notas de crédito aplicadas")

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
    """Todos los pagos aplicados a FACTURAS (no a NC), con la fecha y el
    número del pago y de la factura correspondiente. Para el libro
    diario: sin esto, el saldo acumulado del libro diario no incluye las
    órdenes de pago y no coincide con el saldo pendiente real (que sí
    las resta).

    Deliberadamente NO incluye aplicaciones a NC (aunque existan en
    syna_credit_payment_mapping): una NC ya se resta al 100% en el libro
    diario en el momento en que se la registra (línea "Haber" propia).
    Si la aplicación a una ODP se sumara acá como otro "Haber", esa NC
    quedaría restada dos veces y el saldo del libro diario dejaría de
    coincidir con el saldo real (fue exactamente el bug reportado:
    el saldo del libro diario daba -0.00 en vez de coincidir con el
    saldo pendiente real). El mapping de NC sirve para trazabilidad
    (qué ODP cubre qué NC) y para no dejar aplicar la misma NC dos
    veces, no para generar un segundo movimiento contable."""
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


def crear_credit_mapping(credit_id, payment_id, amount_applied):
    """DEPRECADA: mapping directo NC-pago sin pasar por una factura. Se
    mantiene solo por compatibilidad con datos ya guardados; el flujo
    de ODP actual usa crear_invoice_credit_mapping()."""
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


def crear_invoice_credit_mapping(invoice_id, credit_id, amount_applied, payment_id=None):
    """Aplica una NC directamente contra una factura: reduce el saldo de
    esa factura igual que el efectivo de una ODP (ver calcular_saldo_factura).
    payment_id es opcional y solo sirve de trazabilidad (en qué ODP se
    hizo esta aplicación); el monto de la NC no sale del monto de esa ODP."""
    conn = get_connection()
    cursor = conn.cursor()

    saldo_factura = calcular_saldo_factura(invoice_id)
    if amount_applied > saldo_factura:
        conn.close()
        raise ValueError(f"Monto a aplicar ({amount_applied}) excede saldo de la factura ({saldo_factura})")

    saldo_credit = calcular_saldo_credit(credit_id)
    if amount_applied > saldo_credit:
        conn.close()
        raise ValueError(f"Monto a aplicar ({amount_applied}) excede saldo de la NC ({saldo_credit})")

    now = datetime.now().isoformat()
    cursor.execute("""
    INSERT INTO syna_invoice_credit_mapping (invoice_id, credit_id, payment_id, amount_applied, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (invoice_id, credit_id, payment_id, amount_applied, now))

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
    """Calcula el saldo disponible de una NC: monto menos lo ya aplicado
    directamente a facturas (syna_invoice_credit_mapping, el modelo
    actual) menos lo aplicado con el modelo viejo (syna_credit_payment_mapping,
    deprecado pero sumado acá para no ignorar aplicaciones ya guardadas
    con él). Reemplaza el cálculo original 'amount - used', que restaba
    0 o 1 (el booleano 'used') en vez de un monto real."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COALESCE(SUM(amount_applied), 0) as total_applied
    FROM syna_invoice_credit_mapping
    WHERE credit_id = ?
    """, (credit_id,))
    total_nueva = cursor.fetchone()["total_applied"]

    cursor.execute("""
    SELECT COALESCE(SUM(amount_applied), 0) as total_applied
    FROM syna_credit_payment_mapping
    WHERE credit_id = ?
    """, (credit_id,))
    total_vieja = cursor.fetchone()["total_applied"]

    cursor.execute("SELECT amount FROM syna_credits WHERE id = ?", (credit_id,))
    cr = cursor.fetchone()
    conn.close()

    if cr:
        return cr["amount"] - total_nueva - total_vieja
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
    """Elimina una NC (si no tiene aplicaciones a facturas, ni legacy)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*) as count FROM syna_invoice_credit_mapping WHERE credit_id = ?
    """, (credit_id,))
    if cursor.fetchone()["count"] > 0:
        conn.close()
        raise ValueError("No se puede eliminar una NC aplicada a una factura")

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
    """Elimina una orden de pago y todo lo que se aplicó en su contexto:
    efectivo a facturas, NC a facturas (modelo actual), y NC a la ODP
    directamente (modelo legacy)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM syna_invoice_payment_mapping WHERE payment_id = ?", (payment_id,))
    cursor.execute("DELETE FROM syna_invoice_credit_mapping WHERE payment_id = ?", (payment_id,))
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

    # Total EFECTIVAMENTE aplicado a facturas (HABER real). Este es el que
    # se usa para saldo_pendiente: las NC ya se restan enteras arriba
    # (total_nc), así que sumar también lo aplicado a NC acá duplicaría
    # esa resta.
    cursor.execute("SELECT COALESCE(SUM(amount_applied), 0) as total FROM syna_invoice_payment_mapping")
    total_pagado_facturas = cursor.fetchone()["total"]

    # Compatibilidad con datos guardados con el modelo viejo (NC aplicada
    # directo contra una ODP, sin pasar por una factura - ver comentario
    # en syna_credit_payment_mapping). El flujo actual ya no escribe acá,
    # esto da 0 salvo que existan aplicaciones previas hechas así.
    cursor.execute("SELECT COALESCE(SUM(amount_applied), 0) as total FROM syna_credit_payment_mapping")
    total_pagado_nc_legacy = cursor.fetchone()["total"]

    conn.close()

    saldo_pendiente = total_facturado - total_nc - total_pagado_facturas

    return {
        "total_facturado": total_facturado,
        "total_nc": total_nc,
        "total_ordenes_pago": total_ordenes_pago,
        "total_pagado": total_pagado_facturas,
        "pagos_sin_aplicar": total_ordenes_pago - total_pagado_facturas - total_pagado_nc_legacy,
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
        "Aplicaciones (NC-FC)": "SELECT * FROM syna_invoice_credit_mapping ORDER BY id",
        "Aplicaciones (NC-OP legacy)": "SELECT * FROM syna_credit_payment_mapping ORDER BY id",
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
