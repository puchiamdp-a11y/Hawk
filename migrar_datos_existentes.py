"""
Migración única: lleva los datos de SYNA que ya existen (el
syna_tracking.db de producción, o un backup Excel descargado con el
botón "Descargar backup" de la app) hacia el Postgres externo nuevo.

Correr UNA sola vez, después de crear la base en Supabase (o el proveedor que
sea) y antes de que la app en producción empiece a escribir en ella, para
no pisar datos nuevos con datos viejos.

Uso:
    export SYNA_DATABASE_URL="postgresql://usuario:pass@host/dbname"

    # Si tenés el archivo syna_tracking.db original (por ejemplo, lo
    # bajaste del servidor antes de este cambio):
    python migrar_datos_existentes.py syna_tracking.db

    # Si en cambio solo tenés el Excel del botón "Descargar backup":
    python migrar_datos_existentes.py backup_syna.xlsx
"""

import sys
import sqlite3
from pathlib import Path

import pandas as pd

from syna_db import get_connection, inicializar_db


TABLAS = [
    "syna_invoices",
    "syna_payments",
    "syna_credits",
    "syna_invoice_payment_mapping",
    "syna_invoice_credit_mapping",
    "syna_credit_payment_mapping",
    "syna_audit_log",
]

# Nombre de hoja del Excel -> tabla real. Debe coincidir con
# exportar_backup_excel() en syna_db.py.
HOJA_A_TABLA = {
    "Facturas": "syna_invoices",
    "Notas de Credito": "syna_credits",
    "Ordenes de Pago": "syna_payments",
    "Aplicaciones (FC-OP)": "syna_invoice_payment_mapping",
    "Aplicaciones (NC-FC)": "syna_invoice_credit_mapping",
    "Aplicaciones (NC-OP legacy)": "syna_credit_payment_mapping",
    "Auditoria": "syna_audit_log",
}


def leer_tablas_desde_sqlite(path):
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    dataframes = {}
    for tabla in TABLAS:
        try:
            dataframes[tabla] = pd.read_sql_query(f"SELECT * FROM {tabla}", conn)
        except pd.errors.DatabaseError:
            dataframes[tabla] = pd.DataFrame()
    conn.close()
    return dataframes


def leer_tablas_desde_excel(path):
    dataframes = {}
    excel = pd.ExcelFile(path)
    for hoja, tabla in HOJA_A_TABLA.items():
        if hoja in excel.sheet_names:
            dataframes[tabla] = excel.parse(hoja)
        else:
            dataframes[tabla] = pd.DataFrame()
    return dataframes


def volcar_a_postgres(dataframes):
    conn = get_connection()
    cursor = conn.cursor()

    for tabla in TABLAS:
        df = dataframes.get(tabla)
        if df is None or df.empty:
            continue

        columnas = list(df.columns)
        columnas_sql = ", ".join(f'"{c}"' if c == "user" else c for c in columnas)
        placeholders = ", ".join(["%s"] * len(columnas))

        filas = [tuple(None if pd.isna(v) else v for v in row) for row in df.itertuples(index=False, name=None)]
        cursor.executemany(
            f"INSERT INTO {tabla} ({columnas_sql}) VALUES ({placeholders}) ON CONFLICT DO NOTHING",
            filas,
        )
        print(f"  {tabla}: {len(filas)} filas insertadas")

        # Reacomodar la secuencia SERIAL para que el próximo insert
        # automático (sin id explícito) no choque con los ids ya cargados.
        if "id" in columnas:
            cursor.execute(
                f"SELECT setval(pg_get_serial_sequence('{tabla}', 'id'), COALESCE((SELECT MAX(id) FROM {tabla}), 1))"
            )

    conn.commit()
    conn.close()


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    origen = Path(sys.argv[1])
    if not origen.exists():
        print(f"No existe el archivo: {origen}")
        sys.exit(1)

    print("Inicializando esquema en el Postgres de destino...")
    inicializar_db()

    if origen.suffix == ".db":
        print(f"Leyendo datos desde SQLite: {origen}")
        dataframes = leer_tablas_desde_sqlite(origen)
    elif origen.suffix in (".xlsx", ".xls"):
        print(f"Leyendo datos desde Excel: {origen}")
        dataframes = leer_tablas_desde_excel(origen)
    else:
        print("Formato no soportado. Usá un .db (SQLite) o un .xlsx (backup Excel).")
        sys.exit(1)

    print("Migrando a Postgres...")
    volcar_a_postgres(dataframes)
    print("✅ Migración completa.")


if __name__ == "__main__":
    main()
