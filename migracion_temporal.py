"""
Migración temporal y de un solo uso: Neon -> Supabase.

Se activa visitando la app con ?migrar_syna=<TOKEN> en la URL, donde
TOKEN tiene que matchear el secreto SYNA_MIGRATION_TOKEN (nunca un valor
fijo en el código - un token hardcodeado en una función que ejecuta SQL
arbitrario contra la base quedaría para siempre en el historial de git,
aunque después se borre el archivo). Lee la base ORIGEN de
SYNA_DATABASE_URL (la actual, Neon) y la base DESTINO de
SYNA_MIGRATION_TARGET_URL (la nueva, Supabase) y copia todo preservando
ids. Pensado para borrarse del repo apenas se usa una vez.
"""
import streamlit as st
import psycopg2
import psycopg2.extras


def token_valido(token_recibido):
    """Compara contra el secreto SYNA_MIGRATION_TOKEN, nunca contra un
    valor fijo en el código."""
    token_esperado = st.secrets.get("SYNA_MIGRATION_TOKEN")
    return bool(token_esperado) and token_recibido == token_esperado


TABLAS_EN_ORDEN = [
    "syna_invoices",
    "syna_payments",
    "syna_credits",
    "syna_invoice_payment_mapping",
    "syna_credit_payment_mapping",
    "syna_invoice_credit_mapping",
    "syna_audit_log",
]

DDL = """
CREATE TABLE IF NOT EXISTS syna_invoices (
    id SERIAL PRIMARY KEY,
    invoice_number TEXT UNIQUE NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    invoice_date TEXT,
    due_date TEXT,
    fixed_stamps DOUBLE PRECISION DEFAULT 0,
    email_link TEXT,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    notes TEXT,
    billing_month TEXT,
    category TEXT
);
CREATE TABLE IF NOT EXISTS syna_payments (
    id SERIAL PRIMARY KEY,
    payment_number TEXT,
    payment_date TEXT NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    payer TEXT NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS syna_credits (
    id SERIAL PRIMARY KEY,
    credit_number TEXT UNIQUE NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    credit_date TEXT,
    used INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    created_by TEXT NOT NULL,
    billing_month TEXT,
    category TEXT,
    due_date TEXT
);
CREATE TABLE IF NOT EXISTS syna_invoice_payment_mapping (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL,
    payment_id INTEGER NOT NULL,
    amount_applied DOUBLE PRECISION NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES syna_invoices(id),
    FOREIGN KEY (payment_id) REFERENCES syna_payments(id)
);
CREATE TABLE IF NOT EXISTS syna_credit_payment_mapping (
    id SERIAL PRIMARY KEY,
    credit_id INTEGER NOT NULL,
    payment_id INTEGER NOT NULL,
    amount_applied DOUBLE PRECISION NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (credit_id) REFERENCES syna_credits(id),
    FOREIGN KEY (payment_id) REFERENCES syna_payments(id)
);
CREATE TABLE IF NOT EXISTS syna_invoice_credit_mapping (
    id SERIAL PRIMARY KEY,
    invoice_id INTEGER NOT NULL,
    credit_id INTEGER NOT NULL,
    payment_id INTEGER,
    amount_applied DOUBLE PRECISION NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES syna_invoices(id),
    FOREIGN KEY (credit_id) REFERENCES syna_credits(id),
    FOREIGN KEY (payment_id) REFERENCES syna_payments(id)
);
CREATE TABLE IF NOT EXISTS syna_audit_log (
    id SERIAL PRIMARY KEY,
    action TEXT NOT NULL,
    "user" TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    details TEXT
);
"""


def pantalla_migracion():
    st.title("Migración SYNA: Neon → Supabase")
    st.caption("Pantalla temporal de un solo uso. Se borra del código después de migrar.")

    origen_url = st.secrets.get("SYNA_DATABASE_URL")
    destino_url = st.secrets.get("SYNA_MIGRATION_TARGET_URL")

    if not origen_url:
        st.error("Falta SYNA_DATABASE_URL en los Secrets (debería ya estar, es la base actual).")
        return
    if not destino_url:
        st.error(
            "Falta SYNA_MIGRATION_TARGET_URL en los Secrets. Agregalo con la "
            "connection string de Supabase y volvé a cargar esta página."
        )
        return

    st.write("✅ Origen (Neon, actual): configurado")
    st.write("✅ Destino (Supabase, nuevo): configurado")

    if st.button("Migrar ahora", type="primary"):
        with st.spinner("Migrando..."):
            try:
                origen = psycopg2.connect(origen_url, cursor_factory=psycopg2.extras.RealDictCursor)
                destino = psycopg2.connect(destino_url, cursor_factory=psycopg2.extras.RealDictCursor)
                dcur = destino.cursor()
                dcur.execute(DDL)
                destino.commit()

                resultados = []
                for tabla in TABLAS_EN_ORDEN:
                    ocur = origen.cursor()
                    ocur.execute(f"SELECT * FROM {tabla} ORDER BY id")
                    filas = ocur.fetchall()

                    if filas:
                        columnas = list(filas[0].keys())
                        columnas_sql = ", ".join(f'"{c}"' if c == "user" else c for c in columnas)
                        placeholders = ", ".join(["%s"] * len(columnas))
                        valores = [tuple(row[c] for c in columnas) for row in filas]
                        dcur.executemany(
                            f"INSERT INTO {tabla} ({columnas_sql}) VALUES ({placeholders}) "
                            f"ON CONFLICT DO NOTHING",
                            valores,
                        )
                        destino.commit()
                        dcur.execute(
                            f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), "
                            f"COALESCE((SELECT MAX(id) FROM {tabla}), 1))"
                        )
                        destino.commit()

                    dcur.execute(f"SELECT COUNT(*) as c FROM {tabla}")
                    conteo_destino = dcur.fetchone()["c"]
                    resultados.append((tabla, len(filas), conteo_destino))

                origen.close()
                destino.close()

                st.success("Migración completa.")
                todo_ok = True
                for tabla, n_origen, n_destino in resultados:
                    ok = n_origen == n_destino
                    todo_ok = todo_ok and ok
                    icono = "✅" if ok else "⚠️"
                    st.write(f"{icono} {tabla}: Neon={n_origen} / Supabase={n_destino}")

                if todo_ok:
                    st.info(
                        "Todo coincide. Ahora reemplazá SYNA_DATABASE_URL en Secrets por la "
                        "connection string de Supabase, borrá SYNA_MIGRATION_TARGET_URL, y "
                        "avisale a Claude para que quite esta pantalla temporal del código."
                    )
                else:
                    st.warning("Hay tablas con conteos distintos - revisar antes de cortar a Supabase.")

            except Exception as e:
                st.error(f"Error durante la migración: {e}")
