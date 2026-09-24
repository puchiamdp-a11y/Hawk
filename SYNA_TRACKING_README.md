# 📊 SYNA Tracking - Sistema de Control de Facturas

Sistema integrado en **Hawk** para gestionar facturas Sancor, órdenes de pago y control de saldo SYNA en tiempo real.

## 🎯 Contexto del Negocio

La aseguradora **Sancor** factura directamente a **SYNA** (cliente VIP) por garantías extendidas. Estas facturas **NO entran en Zeus** (sistema ERP), causando pérdida de tracking. 

Este módulo resuelve el problema permitiendo:
- Registro manual de facturas Sancor
- Matching automático de órdenes de pago
- Cálculo de saldo en tiempo real
- Acceso restringido para cobranzas

---

## 🏗️ Arquitectura

### Stack Tecnológico
- **Frontend**: Streamlit (integrado en Hawk)
- **Backend**: Postgres externo (ej. Neon, tier gratuito) — ver "Persistencia y Backup" más abajo
- **Lenguaje**: Python 3.8+

### Módulos

| Archivo | Propósito |
|---------|-----------|
| `syna_db.py` | Lógica de BD + funciones CRUD |
| `syna_ui.py` | Interfaz Dai (admin) y Cintia (viewer) - 5 tabs |
| `app.py` (modificado) | Integración en Hawk |
| `test_syna_data.py` | Suite de testing con datos |
| `migrar_datos_existentes.py` | Migración única de datos viejos (SQLite o Excel) al Postgres externo |

---

## 💾 Persistencia y Backup

Los datos de SYNA **NO** viven en un archivo junto al código. Viven en una
base Postgres externa (recomendado: [Neon](https://neon.tech), tier
gratuito permanente, no pide tarjeta). Esto es intencional: antes se usaba
un archivo SQLite (`syna_tracking.db`) en el disco del propio contenedor
de la app, que se perdía sin aviso ante cualquier redeploy o cambio de
código. Con una base externa, el código se puede modificar, redeployar o
recrear el contenedor sin que la información cargada corra riesgo.

### Configuración (una sola vez)

1. Crear una cuenta gratuita en [neon.tech](https://neon.tech) y un
   proyecto/base nueva.
2. Copiar la **connection string** (formato
   `postgresql://usuario:password@host/dbname?sslmode=require`).
3. Configurarla como secreto, **nunca** en el código ni en git:
   - **Local**: crear `.streamlit/secrets.toml` (ya está en `.gitignore`) con:
     ```toml
     SYNA_DATABASE_URL = "postgresql://usuario:password@host/dbname?sslmode=require"
     ```
   - **Producción (Streamlit Cloud)**: en la configuración de la app,
     sección "Secrets", agregar la misma clave `SYNA_DATABASE_URL`.
4. Al iniciar, la app llama a `inicializar_db()` (`syna_db.py`), que crea
   las tablas si no existen — no hace falta ningún paso manual extra en
   una base nueva.

### Migrar datos que ya existían en el SQLite viejo

Si ya había datos cargados en el `syna_tracking.db` de producción antes de
este cambio, migrarlos una sola vez con `migrar_datos_existentes.py` (ver
el docstring del archivo para el paso a paso), a partir del `.db` original
o de un backup Excel descargado con el botón "💾 Descargar backup".

### Backup adicional

El botón "💾 Descargar backup" (Excel, una hoja por tabla) sigue
disponible como resguardo manual extra, pero ya no es la única red de
seguridad: la base Postgres externa es la fuente de verdad y sobrevive
por sí sola a cambios de código.

---

## 👥 Roles & Acceso

### 1. **Dai** (Administrativo)
- Acceso: Botón "📊 Cobranzas SYNA" en sidebar de Hawk
- Permisos: Full access (crear, editar, consultar)
- URL: `http://hawk-url` (ingresa por sidebar)

**Funcionalidades**:
- ✅ Registrar facturas (número, monto, vencimiento, sellados)
- ✅ Registrar órdenes de pago
- ✅ Hacer matching (vincular pago → factura)
- ✅ Registrar notas de crédito
- ✅ Ver balance y próximos vencimientos
- ✅ Consultar histórico de auditoría

### 2. **Cintia** (Cobranzas)
- Acceso: Link especial con parámetro `?role=viewer`
- Permisos: Read-only (solo lectura)
- URL: `http://hawk-url?role=viewer`
- Autenticación: Contraseña (default: `SYNA2024`)

**Funcionalidades**:
- ✅ Ver balance SYNA
- ✅ Filtrar facturas por fecha/estado
- ✅ Consultar próximos vencimientos
- ✅ Exportar a Excel
- ❌ No puede editar nada

---

## 📊 Estructura de Datos

### Tablas SQLite

#### 1. `syna_invoices` - Facturas Sancor
```sql
id              INTEGER (PK)
invoice_number  TEXT UNIQUE   -- ej: FC-001
amount          REAL          -- monto total
invoice_date    TEXT          -- fecha factura
due_date        TEXT          -- fecha vencimiento
fixed_stamps    REAL          -- sellados fijos
email_link      TEXT          -- link a correo
created_at      TEXT          -- timestamp
created_by      TEXT          -- "Dai"
notes           TEXT          -- observaciones
```

#### 2. `syna_payments` - Órdenes de Pago
```sql
id              INTEGER (PK)
payment_date    TEXT          -- fecha pago
amount          REAL          -- monto total
payer           TEXT          -- "SYNA" o "Blisterassist"
description     TEXT          -- descripción
created_at      TEXT          -- timestamp
created_by      TEXT          -- "Dai"
```

#### 3. `syna_invoice_payment_mapping` - Matching
```sql
id              INTEGER (PK)
invoice_id      INTEGER (FK)  -- referencia a factura
payment_id      INTEGER (FK)  -- referencia a pago
amount_applied  REAL          -- cuánto se aplica
created_at      TEXT          -- timestamp
```

#### 4. `syna_credits` - Notas de Crédito
```sql
id              INTEGER (PK)
credit_number   TEXT UNIQUE   -- ej: NC-001
amount          REAL
credit_date     TEXT
used            INTEGER       -- 0=disponible, 1=utilizada
created_at      TEXT
created_by      TEXT
```

#### 5. `syna_audit_log` - Histórico
```sql
id              INTEGER (PK)
action          TEXT          -- ej: "invoice_added"
user            TEXT          -- "Dai" o "Cintia"
timestamp       TEXT
details         TEXT          -- JSON con cambios
```

---

## 🚀 Cómo Usar

### PASO 1: Registrar Factura (Dai)
1. Abre Hawk → Sidebar: "📊 Cobranzas SYNA"
2. Tab "📄 Facturas"
3. Completa el formulario:
   - Número FC: `FC-001`
   - Monto: `10000`
   - Fecha factura: selecciona
   - Vencimiento: selecciona
   - Sellados fijos: `50` (opcional)
   - Link correo: pega URL (opcional)
4. Botón "✅ Registrar Factura"

### PASO 2: Registrar Pago (Dai)
1. Tab "💳 Pagos"
2. Completa formulario:
   - Fecha pago: selecciona
   - Monto: `10000`
   - ¿Quién pagó?: SYNA / Blisterassist
   - Descripción: ej "Orden OP-2026-001"
3. Botón "✅ Registrar Pago"
4. **Automáticamente** aparece matching:
   - Lista de facturas pendientes
   - Input "Aplicar" para cada factura
   - Validación: suma ≤ monto del pago
5. Botón "✅ Confirmar Matching"

### PASO 3: Consultar Balance (Dai o Cintia)
1. Tab "📊 Balance" (Dai) o directamente en viewer (Cintia)
2. Ve:
   - Total facturado
   - Total pagado
   - Saldo pendiente
   - Tabla de facturas (con colores por estado)
   - Próximos vencimientos (30 días)

### PASO 4: Exportar Excel (Cintia)
1. En tab "Balance" (viewer)
2. Aplica filtros (fecha, estado)
3. Botón "📥 Exportar a Excel"
4. Se descarga archivo `SYNA_Cobranzas_YYYYMMDD.xlsx`

---

## 🔒 Configuración de Seguridad

### Contraseña para Cintia
Editar `.streamlit/secrets.toml`:
```toml
syna_password = "tu_contraseña_secreta"
```

Si no existe, usa default: `SYNA2024`

### URL para Cintia
```
https://tu-dominio-hawk.com?role=viewer
```

Compartir este link + contraseña con Cintia

---

## 📈 Casos de Uso Real

### Escenario 1: Factura Pagada
```
1. Dai registra FC-001: $10,000 (vencimiento 2026-10-15)
   → Balance: Facturado=$10,000, Pagado=$0, Saldo=$10,000

2. Dai registra pago SYNA: $10,000 (2026-09-25)
   → Matching: Aplica $10,000 a FC-001
   
3. Balance actualizado:
   → FC-001 está "Pagada" ✅
   → Saldo total = $0
```

### Escenario 2: Factura Parcialmente Pagada
```
1. Dai registra FC-002: $8,000 (vencimiento 2026-10-22)
   → Balance: Facturado=$8,000, Saldo=$8,000

2. Dai registra pago Blisterassist: $4,000
   → Matching: Aplica $4,000 a FC-002
   
3. Balance parcial:
   → FC-002 está "Parcialmente pagada" ⚠️
   → Saldo = $4,000
   → Próximos vencimientos: Muestra FC-002 con $4,000
```

### Escenario 3: Múltiples Pagos en Una Factura
```
1. Dai registra FC-003: $10,000

2. Dai registra pago #1: $6,000
   → Aplica $6,000 a FC-003
   → Saldo de FC-003 = $4,000

3. Dai registra pago #2: $5,000
   → Aplica $4,000 a FC-003 (solo lo que falta)
   → Aplica $1,000 a otra factura
   → FC-003 está "Pagada" ✅
```

---

## 🔍 Monitoreo & Auditoría

Toda acción se registra automáticamente en `syna_audit_log`:

```
Timestamp          | Usuario | Acción              | Detalles
2026-09-23 15:54   | Dai     | invoice_added       | FC-001, $10,000
2026-09-23 15:55   | Dai     | payment_registered  | Pago $10,000
2026-09-23 15:55   | Dai     | mapping_created     | FC-001 ← Pago
2026-09-23 16:00   | Cintia  | (lectura)           | Balance consultado
```

Ver histórico: Tab "📋 Histórico" (solo Dai)

---

## 📋 Checklist de Validaciones

- ✅ No permite números de factura duplicados
- ✅ Montos > 0 obligatorios
- ✅ Matching: suma aplicada ≤ monto del pago
- ✅ Saldos calculados dinámicamente
- ✅ Estados automáticos (Pagada/Impaga/Parcial)
- ✅ Próximos vencimientos (30 días)
- ✅ Auditoría completa con timestamps
- ✅ Cintia no ve botones de edición
- ✅ Export Excel con datos filtrados

---

## 🧪 Testing

Cargar datos de prueba:
```bash
python test_syna_data.py
```

Genera:
- 3 facturas ($23,000 total)
- 3 pagos ($19,000 total)
- 2 notas de crédito
- Verifica 8 validaciones automáticas

---

## 🛠️ Troubleshooting

### BD corrupta
```bash
# Eliminar e inicializar
rm syna_tracking.db
python -c "from syna_db import inicializar_db; inicializar_db()"
```

### Cambiar contraseña Cintia
Editar `.streamlit/secrets.toml`:
```toml
syna_password = "nueva_contraseña"
```

### Limpiar datos de prueba
```bash
rm syna_tracking.db
python test_syna_data.py  # o ejecutar operaciones manuales
```

---

## 📞 Contacto & Soporte

**Desarrollado por**: Claude Code
**Fecha**: Septiembre 2026
**Status**: Producción lista ✅

Para issues o mejoras, contactar equipo de sistemas.

---

## 📝 Historial de Cambios

### v1.0 - Lanzamiento Inicial (2026-09-23)
- ✅ BD con 5 tablas
- ✅ Interfaz Dai con 5 tabs
- ✅ Interfaz Cintia read-only
- ✅ Sistema completo de auditoría
- ✅ Testing con datos reales
- ✅ Documentación completa

---

**🎯 Objetivo Cumplido**: Reemplazar funcionalidad Zeus para SYNA con sistema independiente, interactivo y 100% trazable.
