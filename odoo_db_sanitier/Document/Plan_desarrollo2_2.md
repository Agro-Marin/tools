# Script de Depuración y Preparación de Datos - Proyecto R 18.2

## Índice
1. [Descripción General](#descripción-general)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Diagrama Lógico Integrado](#diagrama-lógico-integrado)
4. [Especificación JSON](#especificación-json)
5. [Estandarización de IDs Externos](#estandarización-de-ids-externos)
6. [Operaciones Principales](#operaciones-principales)
7. [Script Principal](#script-principal)
8. [Guía de Ejecución](#guía-de-ejecución)

---

## Descripción General

Script Python automatizado para depurar y preparar la base de datos del Proyecto R 18.2, dejándola lista para ser descargada.

### Objetivos

1. **Validar y preparar el entorno** (directorios, JSON, permisos)
2. **Depurar datos temporales**: Eliminar data de Wizard y referencias de usuario en ir.model.data
3. **Conservar data original** de módulos `marin_data` y `marin`
4. **Eliminar espacios en blanco** entre registros (gaps de ID)
5. **Normalizar IDs** de forma secuencial
6. **Estandarizar IDs externos** (ir.model.data) con patrones específicos
7. **Actualizar constraints de FK** a CASCADE
8. **Dejar la BDD lista para descarga**

### Alcance

- **Script Python único** con conexión directa a PostgreSQL
- **44 modelos de Odoo** a procesar
- **Operaciones de depuración** basadas en configuración JSON
- **Base de datos lista** para ser exportada/descargada

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA DEL SISTEMA                  │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Config     │         │   Script     │         │  PostgreSQL  │
│   JSON       │────────▶│   Python     │────────▶│  Database    │
│              │  Read   │  cleanup.py  │  Query  │              │
└──────────────┘         └──────┬───────┘         └──────────────┘
                                │
                                ▼
                   ┌────────────────────────┐
                   │   Operaciones:         │
                   │  ┌──────────────────┐  │
                   │  │ 1. VALIDAR       │  │
                   │  │ 2. ALTER FK      │  │
                   │  │ 3. DELETE WIZARD │  │
                   │  │ 4. RENUMBER IDs  │  │
                   │  │ 5. STANDARDIZE   │  │
                   │  │    XMLIDS        │  │
                   │  │ 6. RESET SEQ     │  │
                   │  │ 7. UPDATE FIELDS │  │
                   │  └──────────────────┘  │
                   └────────────┬───────────┘
                                │
                                ▼
                   ┌────────────────────────┐
                   │   BDD Lista para       │
                   │   Descarga             │
                   └────────────────────────┘
```

### Estructura de Directorios

```
/home/sistemas3/instancias/lib/Proyecto R/acciones_servidor 18.2/
│
├── acciones_servidor/                      # Archivos Python originales
│   ├── account_account.py
│   ├── product.py
│   ├── res_partner.py
│   └── ... (30 archivos)
│
├── config/                                 # Configuración
│   └── cleanup_config.json                # Configuración maestra
│
├── scripts/                                # Scripts
│   └── cleanup_script.py                  # Script principal
│
└── logs/                                   # Logs de ejecución
    ├── cleanup_YYYYMMDD_HHMMSS.log
    └── errors_YYYYMMDD_HHMMSS.log
```

---

## Diagrama Lógico Integrado

```
┌───────────────────────────────────────────────────────────────────────────────────┐
│                    DIAGRAMA LÓGICO INTEGRADO DEL SISTEMA                          │
└───────────────────────────────────────────────────────────────────────────────────┘

                                    ╔═══════════════════╗
                                    ║    INICIO DEL     ║
                                    ║     SCRIPT        ║
                                    ╚═════════╤═════════╝
                                              │
                                              ▼
                    ┌─────────────────────────────────────────────┐
                    │  FASE 1: VALIDACIONES INICIALES             │
                    ├─────────────────────────────────────────────┤
                    │  ✓ Validar BASE_DIR existe                  │
                    │  ✓ Validar CONFIG_DIR existe                │
                    │  ✓ Validar cleanup_config.json existe       │
                    │  ✓ Validar JSON es válido                   │
                    │  ✓ Crear directorios faltantes (logs/)      │
                    │  ✓ Validar permisos de escritura            │
                    └────────────────────┬────────────────────────┘
                                         │
                                         ▼
                    ┌─────────────────────────────────────────────┐
                    │  FASE 2: INICIALIZACIÓN                     │
                    ├─────────────────────────────────────────────┤
                    │  • Cargar cleanup_config.json               │
                    │  • Conectar a PostgreSQL                    │
                    │  • Configurar logging                       │
                    └────────────────────┬────────────────────────┘
                                         │
                                         ▼
        ╔═══════════════════════════════════════════════════════════════╗
        ║         CONEXIÓN A BASE DE DATOS POSTGRESQL                   ║
        ╠═══════════════════════════════════════════════════════════════╣
        ║  Database: proyecto_r_18_2                                    ║
        ║  ┌─────────────────────────────────────────────────────┐     ║
        ║  │  MODELOS DE ODOO (44 tablas)                        │     ║
        ║  │  ┌──────────────┬──────────────┬──────────────┐     │     ║
        ║  │  │ account.*    │ product.*    │ res.*        │     │     ║
        ║  │  │ stock.*      │ sale.*       │ purchase.*   │     │     ║
        ║  │  │ mrp.*        │ fleet.*      │ hr.*         │     │     ║
        ║  │  └──────────────┴──────────────┴──────────────┘     │     ║
        ║  │                                                      │     ║
        ║  │  TABLAS DE SISTEMA                                  │     ║
        ║  │  ┌──────────────────────────────────────────┐       │     ║
        ║  │  │ ir_model_data (Referencias XMLIDs)       │       │     ║
        ║  │  │ wizard_* (Tablas temporales)             │       │     ║
        ║  │  └──────────────────────────────────────────┘       │     ║
        ║  └─────────────────────────────────────────────────────┘     ║
        ╚═════════════════════════════╤═════════════════════════════════╝
                                      │
                                      ▼
        ╔═══════════════════════════════════════════════════════════════╗
        ║  FASE 3: ITERACIÓN POR CADA MODELO (44 modelos)              ║
        ╚═════════════════════════════╤═════════════════════════════════╝
                                      │
                                      ▼
        ┌─────────────────────────────────────────────────────────────┐
        │  PARA CADA MODELO (ejemplo: product.template)               │
        └──────────────────────┬──────────────────────────────────────┘
                               │
        ┌──────────────────────┴──────────────────────┐
        │                                              │
        ▼                                              ▼
    ┌───────────────────────────┐         ┌───────────────────────────┐
    │  LEER CONFIGURACIÓN       │         │  OBTENER DATOS MODELO     │
    │  DEL MODELO               │         │  DESDE POSTGRESQL         │
    ├───────────────────────────┤         ├───────────────────────────┤
    │  • file: "product.py"     │         │  • Tabla: product_template│
    │  • model: product.template│         │  • Registros actuales     │
    │  • operations: [...]      │         │  • IDs existentes         │
    └──────────┬────────────────┘         │  • Referencias FK         │
               │                          └──────────┬────────────────┘
               │                                     │
               └──────────────┬──────────────────────┘
                              │
                              ▼
        ╔═══════════════════════════════════════════════════════════════╗
        ║              EJECUCIÓN DE OPERACIONES                         ║
        ╚═══════════════════════════════════════════════════════════════╝
                              │
        ┌─────────────────────┴─────────────────────┐
        │                                            │
        ▼                                            ▼
    ┌─────────────────────────────────┐    ┌─────────────────────────────────┐
    │  OPERACIÓN 1:                   │    │  OPERACIÓN 2:                   │
    │  ALTER FOREIGN KEYS             │    │  DELETE WIZARD DATA             │
    ├─────────────────────────────────┤    ├─────────────────────────────────┤
    │  • Identificar FKs relacionados │    │  • Buscar tablas wizard_*       │
    │  • DROP CONSTRAINT              │    │  • DELETE FROM wizard_*         │
    │  • ADD CONSTRAINT CASCADE       │    │  • DELETE FROM ir_model_data    │
    │                                 │    │    WHERE module='__export__'    │
    │  Ejemplo:                       │    │  • DELETE FROM ir_model_data    │
    │  ALTER TABLE product_product    │    │    WHERE create_uid IS NOT NULL │
    │  ADD CONSTRAINT                 │    │    AND module NOT IN            │
    │  product_product_tmpl_id_fkey   │    │    ('marin_data', 'marin')      │
    │  FOREIGN KEY (product_tmpl_id)  │    │                                 │
    │  REFERENCES product_template(id)│    │  Resultado:                     │
    │  ON DELETE CASCADE              │    │  • Wizard limpiado              │
    │  ON UPDATE CASCADE              │    │  • Refs usuario eliminadas      │
    └────────────┬────────────────────┘    └────────────┬────────────────────┘
                 │                                      │
                 └──────────────┬───────────────────────┘
                                │
                                ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  OPERACIÓN 3: RENUMBER IDs                                          │
    ├─────────────────────────────────────────────────────────────────────┤
    │                                                                      │
    │  ESTADO INICIAL:    IDs: 1, 2, 5, 8, 150, 151, 300 (con gaps)      │
    │                                                                      │
    │  Paso 1: OFFSET TEMPORAL                                            │
    │  ┌────────────────────────────────────────────────────────────┐    │
    │  │ UPDATE product_template SET id = id + 10000                │    │
    │  │ IDs: 10001, 10002, 10005, 10008, 10150, 10151, 10300      │    │
    │  └────────────────────────────────────────────────────────────┘    │
    │                                                                      │
    │  Paso 2: OBTENER ORDEN CORRECTO                                     │
    │  ┌────────────────────────────────────────────────────────────┐    │
    │  │ SELECT id FROM product_template ORDER BY id                │    │
    │  │ Orden: [10001, 10002, 10005, 10008, 10150, 10151, 10300]  │    │
    │  └────────────────────────────────────────────────────────────┘    │
    │                                                                      │
    │  Paso 3: RENUMERAR SECUENCIALMENTE                                  │
    │  ┌────────────────────────────────────────────────────────────┐    │
    │  │ UPDATE product_template SET id = 1 WHERE id = 10001        │    │
    │  │ UPDATE product_template SET id = 2 WHERE id = 10002        │    │
    │  │ UPDATE product_template SET id = 3 WHERE id = 10005        │    │
    │  │ UPDATE product_template SET id = 4 WHERE id = 10008        │    │
    │  │ UPDATE product_template SET id = 5 WHERE id = 10150        │    │
    │  │ UPDATE product_template SET id = 6 WHERE id = 10151        │    │
    │  │ UPDATE product_template SET id = 7 WHERE id = 10300        │    │
    │  └────────────────────────────────────────────────────────────┘    │
    │                                                                      │
    │  ESTADO FINAL:      IDs: 1, 2, 3, 4, 5, 6, 7 (sin gaps)            │
    │                                                                      │
    └────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  OPERACIÓN 4: STANDARDIZE XMLIDS                                    │
    ├─────────────────────────────────────────────────────────────────────┤
    │                                                                      │
    │  CASO GENERAL (product.template):                                   │
    │  ┌────────────────────────────────────────────────────────────┐    │
    │  │ Patrón: {tabla}_{id}                                       │    │
    │  │                                                            │    │
    │  │ ID 1 → product_template_1                                  │    │
    │  │ ID 2 → product_template_2                                  │    │
    │  │ ID 3 → product_template_3                                  │    │
    │  │ ...                                                        │    │
    │  │ ID 7 → product_template_7                                  │    │
    │  │                                                            │    │
    │  │ INSERT/UPDATE ir_model_data:                               │    │
    │  │   module: 'marin_data'                                     │    │
    │  │   model: 'product.template'                                │    │
    │  │   name: 'product_template_1'                               │    │
    │  │   res_id: 1                                                │    │
    │  └────────────────────────────────────────────────────────────┘    │
    │                                                                      │
    │  CASO ESPECIAL (account.account):                                   │
    │  ┌────────────────────────────────────────────────────────────┐    │
    │  │ Patrón: account_account_{code}                             │    │
    │  │ (puntos reemplazados por guiones bajos)                    │    │
    │  │                                                            │    │
    │  │ Code "102.01"    → account_account_102_01                  │    │
    │  │ Code "510.03"    → account_account_510_03                  │    │
    │  │ Code "102.01.001" → account_account_102_01_001             │    │
    │  │                                                            │    │
    │  │ INSERT/UPDATE ir_model_data:                               │    │
    │  │   module: 'marin_data'                                     │    │
    │  │   model: 'account.account'                                 │    │
    │  │   name: 'account_account_102_01'                           │    │
    │  │   res_id: 42                                               │    │
    │  └────────────────────────────────────────────────────────────┘    │
    │                                                                      │
    └────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  OPERACIÓN 5: RESET SEQUENCE                                        │
    ├─────────────────────────────────────────────────────────────────────┤
    │  • Obtener MAX(id) de la tabla                                      │
    │  • Resetear secuencia PostgreSQL                                    │
    │                                                                      │
    │  SELECT MAX(id) FROM product_template;  -- Resultado: 7             │
    │  SELECT setval('product_template_id_seq', 7, true);                 │
    │                                                                      │
    │  Resultado: Secuencia sincronizada con último ID                    │
    └────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │  OPERACIÓN 6: UPDATE FIELDS (opcional)                              │
    ├─────────────────────────────────────────────────────────────────────┤
    │  • Actualizaciones específicas por modelo                           │
    │  • Cálculos de campos                                               │
    │  • Correcciones de datos                                            │
    └────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │  MODELO PROCESADO EXITOSAMENTE                         │
        │  ✓ FKs actualizados a CASCADE                          │
        │  ✓ Wizard eliminado                                    │
        │  ✓ IDs normalizados (sin gaps)                         │
        │  ✓ XMLIDs estandarizados                               │
        │  ✓ Secuencia sincronizada                              │
        └──────────────────────┬─────────────────────────────────┘
                               │
                               ▼
        ┌────────────────────────────────────────────────────────┐
        │  ¿HAY MÁS MODELOS POR PROCESAR?                        │
        └────────┬───────────────────────────────────┬───────────┘
                 │ SÍ                                │ NO
                 │                                   │
                 ▼                                   ▼
        ┌────────────────────┐         ┌────────────────────────────────┐
        │  SIGUIENTE MODELO  │         │  TODOS LOS MODELOS PROCESADOS  │
        │  (repetir ciclo)   │         │  (44 modelos completados)      │
        └────────────────────┘         └────────────┬───────────────────┘
                                                    │
                                                    ▼
                                ┌───────────────────────────────────────┐
                                │  FASE 4: VALIDACIÓN DE INTEGRIDAD    │
                                ├───────────────────────────────────────┤
                                │  Para cada modelo:                    │
                                │  ✓ Verificar gaps en IDs              │
                                │  ✓ Verificar secuencias               │
                                │  ✓ Verificar FKs válidos              │
                                │  ✓ Verificar XMLIDs correctos         │
                                └─────────────┬─────────────────────────┘
                                              │
                                              ▼
                                ┌───────────────────────────────────────┐
                                │  FASE 5: REPORTE FINAL                │
                                ├───────────────────────────────────────┤
                                │  • Modelos procesados: 44             │
                                │  • Operaciones ejecutadas: 264        │
                                │  • Registros afectados: 15,432        │
                                │  • Tablas wizard eliminadas: 23       │
                                │  • XMLIDs estandarizados: 8,741       │
                                │  • Errores: 0                         │
                                │  • Tiempo ejecución: 12m 34s          │
                                └─────────────┬─────────────────────────┘
                                              │
                                              ▼
                        ╔═══════════════════════════════════════════════╗
                        ║  BASE DE DATOS LISTA PARA DESCARGA           ║
                        ╠═══════════════════════════════════════════════╣
                        ║  ✓ Data depurada                              ║
                        ║  ✓ IDs normalizados sin gaps                  ║
                        ║  ✓ XMLIDs estandarizados                      ║
                        ║  ✓ Secuencias sincronizadas                   ║
                        ║  ✓ Integridad referencial garantizada         ║
                        ║  ✓ Lista para pg_dump                         ║
                        ╚═══════════════════════════════════════════════╝
                                              │
                                              ▼
                                    ╔═══════════════════╗
                                    ║    FIN DEL        ║
                                    ║     SCRIPT        ║
                                    ╚═══════════════════╝
```

---

## Especificación JSON

### Estructura del archivo `cleanup_config.json`

```json
{
  "metadata": {
    "description": "Configuración de depuración de base de datos",
    "version": "2.0",
    "generated_date": "2025-10-02",
    "target_module": "marin_data",
    "database": "Proyecto R 18.2"
  },

  "cleanup_operations": [
    {
      "file": "account_account.py",
      "model": "account.account",
      "operations": [
        {
          "type": "alter_foreign_keys",
          "description": "Actualizar FKs a CASCADE",
          "tables": ["account_move_line", "account_analytic_line"]
        },
        {
          "type": "delete_wizard_data",
          "description": "Eliminar data temporal de wizard"
        },
        {
          "type": "renumber_ids",
          "description": "Renumerar IDs sin gaps",
          "start_id": 1,
          "order": "code",
          "temp_offset": 10000
        },
        {
          "type": "standardize_xmlids",
          "description": "Estandarizar xmlids con código de cuenta",
          "pattern": "account_account_{code}",
          "special_rules": {
            "replace_dots": true
          }
        },
        {
          "type": "reset_sequence",
          "description": "Resetear secuencia"
        }
      ]
    },
    {
      "file": "product.py",
      "model": "product.template",
      "operations": [
        {
          "type": "alter_foreign_keys",
          "description": "Actualizar FKs a CASCADE"
        },
        {
          "type": "delete_wizard_data",
          "description": "Limpiar referencias usuario"
        },
        {
          "type": "renumber_ids",
          "description": "Normalizar IDs",
          "start_id": 1,
          "order": "id",
          "temp_offset": 10000
        },
        {
          "type": "standardize_xmlids",
          "description": "Estandarizar xmlids",
          "pattern": "product_template_{id}"
        },
        {
          "type": "reset_sequence",
          "description": "Resetear secuencia"
        }
      ]
    }
  ],

  "cleanup_patterns": {
    "preserve_modules": ["marin_data", "marin"],
    "delete_wizard_tables": ["wizard_%"],
    "delete_ir_model_data_modules": ["__export__"],
    "xmlid_standardization": {
      "general_pattern": "{table}_{id}",
      "special_cases": {
        "account.account": {
          "pattern": "account_account_{code}",
          "replace_dots": true
        }
      }
    }
  },

  "execution_order": [
    "1. VALIDATE ENVIRONMENT",
    "2. ALTER FOREIGN KEYS",
    "3. DELETE WIZARD DATA",
    "4. RENUMBER IDS",
    "5. STANDARDIZE XMLIDS",
    "6. RESET SEQUENCES",
    "7. UPDATE FIELDS"
  ]
}
```

### Tipos de Operaciones

| Tipo | Descripción | Parámetros |
|------|-------------|------------|
| `alter_foreign_keys` | Modificar constraints FK a CASCADE | `tables[]` |
| `delete_wizard_data` | Eliminar wizard y refs usuario | - |
| `renumber_ids` | Renumerar IDs secuenciales | `start_id`, `order`, `temp_offset` |
| `standardize_xmlids` | Estandarizar xmlids | `pattern`, `special_rules` |
| `reset_sequence` | Sincronizar secuencias | - |
| `update_fields` | Actualizar campos | `fields[]` |

---

## Estandarización de IDs Externos

### Patrón General

Para todos los modelos **excepto** `account.account`:

```
{tabla_underscore}_{id_database}
```

**Ejemplos:**
```
product.template (ID 150)  → product_template_150
res.partner (ID 42)        → res_partner_42
stock.location (ID 7)      → stock_location_7
```

### Caso Especial: account.account

Para el modelo `account.account`:

```
account_account_{code_sin_puntos}
```

**Reglas:**
1. Se usa el **código de cuenta** en lugar del ID
2. Los puntos (`.`) se reemplazan por guiones bajos (`_`)
3. Se mantiene la estructura del código

**Ejemplos:**
```
Cuenta 102.01      → account_account_102_01
Cuenta 510.03      → account_account_510_03
Cuenta 102.01.001  → account_account_102_01_001
```

### Implementación

```python
def standardize_xmlids(self, model: str, operation: Dict) -> int:
    """
    Estandariza XMLIDs según patrón
    """
    if model == "account.account":
        # Usar código de cuenta
        query = "SELECT id, code FROM account_account"
        for record_id, code in records:
            code_clean = code.replace(".", "_")
            xmlid_name = f"account_account_{code_clean}"
            self._upsert_xmlid(model, record_id, xmlid_name)
    else:
        # Usar ID de base de datos
        query = f"SELECT id FROM {table}"
        for record_id in records:
            xmlid_name = f"{table}_{record_id}"
            self._upsert_xmlid(model, record_id, xmlid_name)
```

### Tabla de Ejemplos

| Modelo | ID/Code | XMLID Generado |
|--------|---------|----------------|
| product.template | 150 | product_template_150 |
| product.product | 300 | product_product_300 |
| res.partner | 42 | res_partner_42 |
| account.account | 102.01 | account_account_102_01 |
| account.account | 510.03 | account_account_510_03 |
| stock.location | 7 | stock_location_7 |
| account.move | 1234 | account_move_1234 |

---

## Operaciones Principales

### 1. ALTER FOREIGN KEYS

**Objetivo:** Actualizar constraints de FK a CASCADE

**Proceso:**
1. Identificar tablas con FK hacia el modelo
2. Para cada constraint:
   - DROP CONSTRAINT
   - ADD CONSTRAINT con ON DELETE CASCADE

**SQL Ejemplo:**
```sql
ALTER TABLE account_move_line
DROP CONSTRAINT IF EXISTS account_move_line_account_id_fkey;

ALTER TABLE account_move_line
ADD CONSTRAINT account_move_line_account_id_fkey
FOREIGN KEY (account_id)
REFERENCES account_account (id)
ON DELETE CASCADE
ON UPDATE CASCADE;
```

### 2. DELETE WIZARD DATA

**Objetivo:** Eliminar data temporal y referencias de usuario

**Proceso:**
1. Eliminar todas las tablas `wizard_*`
2. Eliminar referencias en `ir_model_data` con:
   - `module = '__export__'`
   - `create_uid != NULL AND module NOT IN ('marin_data', 'marin')`

**SQL Ejemplo:**
```sql
-- Eliminar tablas wizard
DELETE FROM wizard_product_import;
DELETE FROM wizard_account_reconcile;

-- Eliminar referencias __export__
DELETE FROM ir_model_data WHERE module = '__export__';

-- Eliminar referencias de usuario no originales
DELETE FROM ir_model_data
WHERE create_uid IS NOT NULL
  AND module NOT IN ('marin_data', 'marin');
```

**Importante:** NO se elimina data transaccional de negocio (account.move, sale.order, etc.)

### 3. RENUMBER IDS

**Objetivo:** Eliminar gaps y renumerar secuencialmente

**Proceso:**
1. Aplicar offset temporal (+10000)
2. Obtener registros en orden correcto
3. Renumerar desde 1 secuencialmente

**SQL Ejemplo:**
```sql
-- Paso 1: Offset
UPDATE product_template SET id = id + 10000;

-- Paso 2: Obtener orden
SELECT id FROM product_template ORDER BY id;

-- Paso 3: Renumerar
UPDATE product_template SET id = 1 WHERE id = 10150;
UPDATE product_template SET id = 2 WHERE id = 10151;
...
```

### 4. STANDARDIZE XMLIDS

**Objetivo:** Estandarizar nombres de XMLIDs

**Proceso:**
1. Para cada registro del modelo
2. Generar nombre según patrón
3. UPDATE o INSERT en `ir_model_data`

**SQL Ejemplo:**
```sql
-- Caso general
UPDATE ir_model_data
SET name = 'product_template_150'
WHERE model = 'product.template' AND res_id = 150;

-- Caso especial account.account
UPDATE ir_model_data
SET name = 'account_account_102_01'
WHERE model = 'account.account' AND res_id = 42;
```

### 5. RESET SEQUENCE

**Objetivo:** Sincronizar secuencias de PostgreSQL

**Proceso:**
1. Obtener MAX(id) de la tabla
2. Resetear secuencia con setval

**SQL Ejemplo:**
```sql
SELECT MAX(id) FROM product_template;  -- Resultado: 150

SELECT setval('public.product_template_id_seq', 150, true);
```

---

## Script Principal

### Estructura del Script

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de Depuración y Preparación de Datos - Proyecto R 18.2

Funcionalidad:
- Valida entorno antes de procesar
- Elimina data temporal de Wizard
- Elimina referencias de usuario en ir.model.data
- Normaliza IDs eliminando gaps
- Estandariza XMLIDs con patrones específicos
- Actualiza constraints FK a CASCADE
- Deja BDD lista para descarga
"""

import os
import sys
import json
import logging
import psycopg2
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configuración
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_FILE = CONFIG_DIR / "cleanup_config.json"

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "proyecto_r_18_2",
    "user": "odoo",
    "password": "odoo"
}

class CleanupScript:
    """
    Clase principal para depuración de base de datos
    """

    def __init__(self, config_path: Path):
        self.logger = setup_logging()
        self.config_path = config_path
        self.config = {}
        self.conn = None
        self.cursor = None
        self.stats = {
            "models_processed": 0,
            "operations_executed": 0,
            "records_affected": 0,
            "wizard_tables_deleted": 0,
            "xmlids_standardized": 0,
            "errors": 0
        }

    # Métodos de validación
    def validate_environment(self) -> bool:
        """Valida el entorno antes de inicializar"""
        pass

    def create_directories(self) -> bool:
        """Crea directorios necesarios"""
        pass

    def load_config(self) -> bool:
        """Carga configuración desde JSON"""
        pass

    def connect_database(self) -> bool:
        """Conecta a PostgreSQL"""
        pass

    # Métodos de operaciones
    def alter_foreign_keys(self, model: str, operation: Dict) -> int:
        """Modifica constraints FK a CASCADE"""
        pass

    def delete_wizard_data(self, model: str, operation: Dict) -> int:
        """Elimina wizard y referencias usuario"""
        pass

    def renumber_ids(self, model: str, operation: Dict) -> int:
        """Renumera IDs secuencialmente"""
        pass

    def standardize_xmlids(self, model: str, operation: Dict) -> int:
        """Estandariza XMLIDs"""
        pass

    def reset_sequence(self, model: str, operation: Dict) -> bool:
        """Resetea secuencias"""
        pass

    # Método principal
    def run(self) -> bool:
        """Ejecuta el proceso completo"""
        if not self.validate_environment():
            return False
        if not self.create_directories():
            return False
        if not self.load_config():
            return False
        if not self.connect_database():
            return False

        # Procesar cada modelo
        for model_config in self.config["cleanup_operations"]:
            self.process_model(model_config)

        # Validar integridad
        self.validate_data_integrity()

        # Reporte final
        self.generate_summary_report()

        return True

def main():
    script = CleanupScript(CONFIG_FILE)
    success = script.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
```

**Nota:** El código completo del script está disponible en el archivo `cleanup_script.py` en el directorio `scripts/`.

---

## Guía de Ejecución

### Requisitos Previos

1. **Python 3.8+** instalado
2. **PostgreSQL** con acceso a la base de datos
3. **psycopg2** instalado:
   ```bash
   pip install psycopg2-binary
   ```
4. **Backup de la base de datos** (CRÍTICO)

### Pasos de Ejecución

#### 1. Backup OBLIGATORIO

```bash
# CRÍTICO: Hacer backup antes de ejecutar
pg_dump -U odoo -d proyecto_r_18_2 -F c -f backup_pre_depuracion.dump
```

#### 2. Configurar Parámetros

Editar `scripts/cleanup_script.py`:

```python
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "proyecto_r_18_2",  # ← Ajustar
    "user": "odoo",                   # ← Ajustar
    "password": "odoo"                # ← Ajustar
}
```

#### 3. Validar JSON de Configuración

```bash
# Validar que el JSON existe y es válido
cat config/cleanup_config.json | python -m json.tool
```

#### 4. Ejecutar Script

```bash
cd "/home/sistemas3/instancias/lib/Proyecto R/acciones_servidor 18.2/scripts"
python3 cleanup_script.py
```

#### 5. Monitorear Ejecución

```bash
# En otra terminal, seguir el log en tiempo real
tail -f ../logs/cleanup_*.log
```

#### 6. Validar Resultados

```bash
# Conectar a la base de datos
psql -U odoo -d proyecto_r_18_2

-- Verificar gaps en IDs
SELECT COUNT(*) as gaps
FROM (
    SELECT id, id - LAG(id) OVER (ORDER BY id) as gap
    FROM product_template
) sub
WHERE gap > 1;

-- Verificar XMLIDs estandarizados
SELECT name FROM ir_model_data
WHERE model = 'product.template'
LIMIT 10;

-- Verificar secuencias
SELECT last_value FROM product_template_id_seq;
SELECT MAX(id) FROM product_template;

-- Verificar wizard eliminado
SELECT tablename FROM pg_tables
WHERE tablename LIKE 'wizard_%';

-- Verificar ir_model_data limpio
SELECT COUNT(*) FROM ir_model_data
WHERE module = '__export__';
```

#### 7. Descargar Base de Datos

```bash
# Una vez validado, descargar la BDD lista
pg_dump -U odoo -d proyecto_r_18_2 -F c -f proyecto_r_18_2_depurado.dump

# Verificar tamaño
ls -lh proyecto_r_18_2_depurado.dump
```

### Manejo de Errores

Si el script falla:

1. **Revisar logs:**
   ```bash
   cat logs/errors_*.log
   ```

2. **Restaurar backup:**
   ```bash
   pg_restore -U odoo -d proyecto_r_18_2 -c backup_pre_depuracion.dump
   ```

3. **Corregir problema** y reintentar

### Estructura de Logs

**cleanup_YYYYMMDD_HHMMSS.log:**
- Todas las operaciones ejecutadas
- Progreso de cada modelo
- Estadísticas detalladas

**errors_YYYYMMDD_HHMMSS.log:**
- Únicamente errores
- Stack traces
- Queries fallidos

---

## Ejemplo de Ejecución Completa

```
┌─────────────────────────────────────────────────────────────────┐
│         EJEMPLO: PROCESAMIENTO DE product.template              │
└─────────────────────────────────────────────────────────────────┘

ESTADO INICIAL:
  IDs: 1, 2, 5, 8, 150, 151, 300
  Wizard: 10 tablas con data
  ir_model_data: 50 refs __export__, 30 refs usuario

OPERACIÓN 1: ALTER FOREIGN KEYS
  ✓ product_product.product_tmpl_id → CASCADE
  ✓ stock_quant.product_tmpl_id → CASCADE

OPERACIÓN 2: DELETE WIZARD DATA
  ✓ 10 tablas wizard eliminadas (500 registros)
  ✓ 50 refs __export__ eliminadas
  ✓ 30 refs usuario eliminadas

OPERACIÓN 3: RENUMBER IDS
  Before: 1, 2, 5, 8, 150, 151, 300
  After:  1, 2, 3, 4, 5, 6, 7

OPERACIÓN 4: STANDARDIZE XMLIDS
  ID 1 → product_template_1
  ID 2 → product_template_2
  ID 3 → product_template_3
  ID 4 → product_template_4
  ID 5 → product_template_5
  ID 6 → product_template_6
  ID 7 → product_template_7

OPERACIÓN 5: RESET SEQUENCE
  product_template_id_seq → 7

ESTADO FINAL:
  ✓ IDs: 1-7 (sin gaps)
  ✓ XMLIDs estandarizados
  ✓ Wizard eliminado
  ✓ Secuencia sincronizada
  ✓ BDD lista para descarga
```

---

## Resultado Final

### Base de Datos Depurada

Al finalizar la ejecución del script, la base de datos estará:

✅ **Depurada**
- Sin tablas wizard temporales
- Sin referencias de usuario no originales
- Sin referencias __export__

✅ **Normalizada**
- IDs secuenciales sin gaps
- Secuencias sincronizadas
- Integridad referencial garantizada

✅ **Estandarizada**
- XMLIDs con patrones consistentes
- Foreign Keys con CASCADE
- Data organizada y limpia

✅ **Lista para Descarga**
- Puede ser exportada con pg_dump
- Puede ser restaurada en otro ambiente
- Puede ser migrada a otra versión
- Puede ser distribuida como módulo

---

**Documento generado:** 2025-10-02
**Versión:** 2.0
**Proyecto:** Proyecto R 18.2
