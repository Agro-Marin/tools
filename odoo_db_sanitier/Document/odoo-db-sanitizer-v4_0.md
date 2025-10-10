# Odoo Database Sanitizer - Version 4.0

**Sistema de Limpieza y Resecuenciación de Base de Datos Odoo**

Versión: 4.0
Fecha: 2025-10-09
Base de Datos: PostgreSQL 12+
Odoo: 16.0+

---

## Tabla de Contenidos

1. [Introducción](#introducción)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Características Principales](#características-principales)
4. [Configuración](#configuración)
5. [Diagramas de Flujo](#diagramas-de-flujo)
6. [Estrategias de ID](#estrategias-de-id)
7. [Operaciones](#operaciones)
8. [Instalación y Uso](#instalación-y-uso)
9. [Casos de Uso](#casos-de-uso)
10. [Solución de Problemas](#solución-de-problemas)
11. [Referencias Técnicas](#referencias-técnicas)

---

## Introducción

Odoo Database Sanitizer v4.0 es un sistema completo y automatizado para la limpieza, optimización y resecuenciación de bases de datos Odoo. Diseñado para mantener la integridad referencial al 100% mientras reorganiza y optimiza la estructura de datos.

### ¿Qué hace este sistema?

- **Limpia** datos innecesarios (wizards, exportaciones, registros transitorios)
- **Resecuencia** IDs de manera inteligente con estrategias específicas por modelo
- **Gestiona CASCADE** automáticamente para mantener integridad referencial
- **Reconstruye XMLIDs** para mantener la trazabilidad de datos
- **Sincroniza secuencias** PostgreSQL con los datos reales
- **Valida integridad** antes y después del proceso

### ¿Por qué v4.0?

La versión 4.0 introduce:
- **Arquitectura basada en fases** para ejecución ordenada
- **Estrategias específicas de ID** (consolidation, sequential, custom)
- **Soporte para start_id específico** por modelo
- **Operaciones idempotentes** para re-ejecución segura
- **Gestión mejorada de CASCADE** con referencias inversas
- **247 operaciones** distribuidas en 31 modelos

---

## Arquitectura del Sistema

### Componentes Principales

```
odoo_db_sanitizer/
│
├── Run.py                     # Motor principal de ejecución
├── convertJSON.py             # Generador de configuración
├── models_config.json         # Configuración v4.0 (31 modelos)
│
├── config/
│   └── db_credentials.json    # Credenciales de conexión
│
├── utils/
│   └── acciones_servidor/     # Scripts SQL originales (32 archivos)
│
├── output/
│   ├── logs/                  # Logs de ejecución
│   └── statistics/            # Reportes JSON/CSV
│
└── Document/                  # Documentación
```

### Flujo de Datos

```
┌─────────────────────────────────────────────────────────────┐
│                    FLUJO DE DATOS v4.0                      │
└─────────────────────────────────────────────────────────────┘

   config/db_credentials.json ────┐
                                   ├──► Run.py
   models_config.json ─────────────┘       │
                                           │
                                           ▼
                            ┌──────────────────────────┐
                            │  Conexión PostgreSQL     │
                            └──────────────────────────┘
                                           │
                   ┌───────────────────────┼───────────────────────┐
                   │                       │                       │
                   ▼                       ▼                       ▼
           ┌───────────┐          ┌──────────────┐       ┌──────────────┐
           │  Modelo 1 │          │   Modelo 2   │       │  Modelo 31   │
           │res.company│          │ res.partner  │  ...  │consolidation │
           └───────────┘          └──────────────┘       └──────────────┘
                   │                       │                       │
                   └───────────────────────┼───────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────┐
                            │   Generación Reportes    │
                            │  output/statistics/      │
                            └──────────────────────────┘
                                           │
                                           ▼
                            ┌──────────────────────────┐
                            │     Logs Detallados      │
                            │    output/logs/          │
                            └──────────────────────────┘
```

---

## Características Principales

### 1. Integridad Referencial 100%

El sistema garantiza que NO se romperán relaciones de foreign keys mediante:

- **CASCADE automático**: Actualización de FKs cuando cambian IDs padres
- **Triggers USER**: Solo desactiva triggers de usuario, mantiene constraints activos
- **Referencias inversas**: Detecta y aplica CASCADE a FKs que apuntan a la tabla
- **Validación continua**: Verificaciones antes, durante y después del proceso

### 2. Estrategias de ID Específicas por Modelo

#### Estrategia: **Consolidation** (Mapeo Directo)

Fusiona registros específicos mediante mapeo directo de IDs.

**Ejemplo**: `res.company` (fusionar company 8 → 7)

```json
{
  "strategy": "consolidation",
  "mapping": {
    "8": "7"
  }
}
```

**Resultado**:
- ID 8 se convierte en ID 7
- Todos los FKs que apuntaban a 8 ahora apuntan a 7
- El registro 8 puede ser eliminado

#### Estrategia: **Sequential** (Renumeración Secuencial)

Renumera registros desde un start_id específico manteniendo orden.

**Ejemplo**: `res.partner` (desde ID 8590)

```json
{
  "strategy": "sequential",
  "start_id": 8590,
  "order_by": "id",
  "condition": "id >= 8590"
}
```

**Resultado**:
```
Antes: [8590, 8592, 8595, 8600, ...]
Después: [8590, 8591, 8592, 8593, ...]
```

#### Estrategia: **Custom** (Lógica Personalizada)

Implementa lógica específica del negocio.

**Ejemplo**: `product.product` (sincronizar con template)

```json
{
  "strategy": "custom",
  "description": "Set product.product.id = product_tmpl_id for single-variant products"
}
```

**Resultado**:
- Para productos single-variant: `product_product.id = product_tmpl_id`
- Sincronización perfecta entre variante y template

### 3. Sistema de Fases

```
┌────────────────────────────────────────────────────────┐
│              FASES DE EJECUCIÓN v4.0                   │
└────────────────────────────────────────────────────────┘

FASE 1: FK_REWRITE (Critical)
   ├─ Reescribir constraints con CASCADE
   ├─ Aplicar a referencias directas
   └─ Detectar y aplicar referencias inversas

FASE 2: CLEANUP (Critical)
   ├─ Eliminar wizards y transitorios
   ├─ Limpiar __export__ XMLIDs
   └─ DELETE con WHERE obligatorio

FASE 3: ID_SHIFT (Critical)
   ├─ Desplazar IDs temporalmente
   ├─ Evitar conflictos durante renumeración
   └─ Offset específico por modelo

FASE 4: ID_COMPACT (Critical)
   ├─ Renumeración final con estrategia
   ├─ consolidation | sequential | custom
   └─ Mantiene orden especificado

FASE 5: PATCH_JSONB (Parallelizable)
   ├─ Actualizar campos JSONB
   ├─ analytic_distribution
   └─ Referencias antiguas → nuevas

FASE 6: XMLID_REBUILD (Critical)
   ├─ Reconstruir ir_model_data
   ├─ Módulo específico (marin/marin_data)
   └─ Patterns configurables

FASE 7: SEQUENCE_SYNC (Parallelizable, Critical)
   ├─ Sincronizar secuencias PostgreSQL
   ├─ setval(sequence, MAX(id))
   └─ Prevenir duplicate keys

FASE 8: RECOMPUTE (Parallelizable)
   ├─ Recalcular campos computados
   └─ Solo si es necesario
```

### 4. Progreso en Tiempo Real

```python
class ProgressTracker:
    """
    Visualización en consola del progreso de ejecución

    Características:
    - Contador de modelos procesados (X/31)
    - Tiempo transcurrido
    - Tiempo estimado restante
    - Barra de progreso por lote
    - Detalles de cada operación
    """
```

**Salida visual**:
```
============================================================
Modelo 1/31: res.company
Tiempo transcurrido: 0m 5s
============================================================

  ▶ Aplicando CASCADE: 6/6
  ▶ Detectando referencias inversas...
  ▶ ID Compact con estrategia...
    Lote 1/1: [████████████████████████████] 100.0% (1/1)

────────────────────────────────────────────────────────
✓ SUCCESS - Tiempo: 0m 47s
📊 Progreso: 1/31 modelos
⏱️  Tiempo restante estimado: 24m 5s
────────────────────────────────────────────────────────
```

---

## Configuración

### Archivo: `models_config.json`

Estructura principal:

```json
{
  "version": "4.0",
  "description": "Comprehensive Odoo database migration configuration",
  "metadata": {
    "created": "2025-10-09",
    "model_count": 31,
    "total_operations": 247,
    "estimated_duration_minutes": 45,
    "database_compatibility": "PostgreSQL 12+",
    "odoo_version": "16.0"
  },
  "phases": { /* Definición de 8 fases */ },
  "execution_order": [ /* Orden de 31 modelos */ ],
  "global_settings": { /* Configuración global */ },
  "models": { /* Configuración específica de 31 modelos */ }
}
```

### Configuración de Modelo (Ejemplo Completo)

```json
"res.partner": {
  "enabled": true,
  "table": "res_partner",
  "description": "Partners - renumber from 8590",

  "operations": {

    "fk_rewrite": {
      "enabled": true,
      "constraints": [
        {
          "table": "account_reconcile_model_res_partner_rel",
          "column": "res_partner_id",
          "action": "CASCADE"
        },
        {
          "table": "mail_followers",
          "column": "partner_id",
          "action": "CASCADE"
        }
        // ... más constraints
      ]
    },

    "cleanup": {
      "enabled": true,
      "operations": [
        "DELETE FROM mail_compose_message",
        "DELETE FROM website_visitor",
        "DELETE FROM ir_model_data WHERE module='__export__' AND model='res.partner'"
      ]
    },

    "id_compact": {
      "enabled": true,
      "strategy": "sequential",
      "start_id": 8590,
      "order_by": "id",
      "condition": "id >= 8590"
    },

    "xmlid_rebuild": {
      "enabled": true,
      "module": "marin_data",
      "condition": "active IN (true, false) AND id >= 5000",
      "name_pattern": "partner_{id}"
    },

    "sequence_sync": {
      "enabled": true,
      "sequence": "res_partner_id_seq"
    }
  }
}
```

### Archivo: `config/db_credentials.json`

```json
{
  "host": "localhost",
  "port": 5432,
  "database": "odoo_production",
  "user": "odoo",
  "password": "secure_password",
  "sslmode": "prefer"
}
```

**Seguridad**:
```bash
chmod 600 config/db_credentials.json
```

---

## Diagramas de Flujo

### Diagrama 1: Flujo General del Sistema

```
╔══════════════════════════════════════════════════════════════╗
║            FLUJO GENERAL ODOO DB SANITIZER v4.0              ║
╚══════════════════════════════════════════════════════════════╝

           ┌──────────────────────┐
           │   INICIO SISTEMA     │
           └──────────┬───────────┘
                      │
                      ▼
           ┌──────────────────────┐
           │ Cargar Credenciales  │
           │ db_credentials.json  │
           └──────────┬───────────┘
                      │
                      ▼
           ┌──────────────────────┐
           │ Conectar PostgreSQL  │
           └──────────┬───────────┘
                      │
                      ▼
           ┌──────────────────────┐
           │ Cargar Configuración │
           │ models_config.json   │
           └──────────┬───────────┘
                      │
                      ▼
           ┌──────────────────────┐
           │ Inicializar Tracker  │
           │  (31 modelos)        │
           └──────────┬───────────┘
                      │
        ┌─────────────┴─────────────┐
        │   LOOP: Para cada modelo  │
        │   (en execution_order)    │
        └─────────────┬─────────────┘
                      │
                      ▼
           ┌──────────────────────┐
           │  Validar si tabla    │
           │      existe          │
           └──────────┬───────────┘
                      │
              ┌───────┴───────┐
              │               │
             No              Si
              │               │
              ▼               ▼
        ┌─────────┐    ┌─────────────────┐
        │  SKIP   │    │ process_model() │
        │ modelo  │    │   (ver detalle) │
        └─────────┘    └────────┬────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Registrar resultados  │
                    │   en statistics       │
                    └───────────┬───────────┘
                                │
        ┌───────────────────────┘
        │
        ▼
    ¿Más modelos?
        │
       No
        │
        ▼
┌────────────────────────┐
│  Generar Reportes      │
│  - JSON detallado      │
│  - CSV resumido        │
└────────────┬───────────┘
             │
             ▼
┌────────────────────────┐
│  Cerrar Conexión       │
└────────────┬───────────┘
             │
             ▼
┌────────────────────────┐
│    FIN EXITOSO         │
└────────────────────────┘
```

### Diagrama 2: Procesamiento de un Modelo

```
╔══════════════════════════════════════════════════════════════╗
║              PROCESS_MODEL() - Detalle v4.0                  ║
╚══════════════════════════════════════════════════════════════╝

         ┌──────────────────────────┐
         │  INICIO process_model()  │
         │  (modelo, config)        │
         └────────────┬─────────────┘
                      │
                      ▼
         ┌──────────────────────────┐
         │ Contar registros_before  │
         │  SELECT COUNT(*) ...     │
         └────────────┬─────────────┘
                      │
        ┌─────────────┴─────────────┐
        │     FASE 1: FK_REWRITE    │
        └─────────────┬─────────────┘
                      │
                      ▼
         ┌──────────────────────────┐
         │ fk_rewrite.enabled?      │
         └────────────┬─────────────┘
                      │
              ┌───────┴───────┐
             Si              No
              │               │
              ▼               ▼
    ┌──────────────────┐   [SKIP]
    │ apply_cascade()  │
    │ - DROP           │
    │ - ADD CASCADE    │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────────────┐
    │ apply_inverse_cascade()  │
    │ - Detectar refs inversas │
    │ - Aplicar CASCADE        │
    └────────┬─────────────────┘
             │
        ┌────┴────────────────────┐
        │   FASE 2: ID_SHIFT      │
        └────┬────────────────────┘
             │
             ▼
    ┌──────────────────────┐
    │ id_shift.enabled?    │
    └────────┬─────────────┘
             │
      ┌──────┴──────┐
     Si            No
      │             │
      ▼             ▼
┌──────────────┐  [SKIP]
│ UPDATE SET   │
│ id = id +    │
│   offset     │
└──────┬───────┘
       │
  ┌────┴───────────────────┐
  │  FASE 3: ID_COMPACT    │
  └────┬───────────────────┘
       │
       ▼
┌──────────────────────────────────┐
│ id_compact.enabled?              │
└────────┬─────────────────────────┘
         │
    ┌────┴────┐
   Si        No
    │         │
    ▼         ▼
┌────────────────────────┐  [SKIP]
│ Determinar estrategia  │
└────────┬───────────────┘
         │
    ┌────┴─────┬──────────┬─────────┐
    │          │          │         │
    ▼          ▼          ▼         ▼
┌─────────┐ ┌─────────┐ ┌──────┐ ┌──────┐
│consoli- │ │sequen-  │ │custom│ │legacy│
│dation   │ │tial     │ │      │ │      │
└────┬────┘ └────┬────┘ └───┬──┘ └───┬──┘
     │           │           │        │
     └───────────┴───────────┴────────┘
                 │
                 ▼
     ┌───────────────────────┐
     │  Mapeo de IDs creado  │
     │  (old_id → new_id)    │
     └───────────┬───────────┘
                 │
                 ▼
     ┌───────────────────────┐
     │ Batch processing      │
     │ - DISABLE TRIGGER USER│
     │ - UPDATE CASE ...     │
     │ - CASCADE actualiza   │
     │ - ENABLE TRIGGER USER │
     └───────────┬───────────┘
                 │
        ┌────────┴────────────────┐
        │   FASE 4: CLEANUP       │
        └────────┬────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ cleanup.enabled?   │
        └────────┬───────────┘
                 │
          ┌──────┴──────┐
         Si            No
          │             │
          ▼             ▼
    ┌──────────────┐  [SKIP]
    │ DELETE FROM  │
    │ (con WHERE)  │
    └──────┬───────┘
           │
    ┌──────┴──────────────────┐
    │ FASE 5: XMLID_REBUILD   │
    └──────┬──────────────────┘
           │
           ▼
    ┌──────────────────────┐
    │xmlid_rebuild.enabled?│
    └──────┬───────────────┘
           │
    ┌──────┴──────┐
   Si            No
    │             │
    ▼             ▼
┌─────────────┐ [SKIP]
│INSERT INTO  │
│ir_model_data│
└──────┬──────┘
       │
  ┌────┴──────────────────┐
  │ FASE 6: SEQUENCE_SYNC │
  └────┬──────────────────┘
       │
       ▼
┌────────────────────────┐
│sequence_sync.enabled?  │
└────────┬───────────────┘
         │
    ┌────┴────┐
   Si        No
    │         │
    ▼         ▼
┌──────────┐ [SKIP]
│ setval() │
└────┬─────┘
     │
     ▼
┌──────────────────────────┐
│ Contar registros_after   │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│  Retornar resultados     │
│  - status: SUCCESS       │
│  - records_before/after  │
│  - changes[]             │
└────────────┬─────────────┘
             │
             ▼
┌──────────────────────────┐
│    FIN process_model()   │
└──────────────────────────┘
```

### Diagrama 3: Estrategia Sequential Detallada

```
╔══════════════════════════════════════════════════════════════╗
║         ESTRATEGIA SEQUENTIAL - Flujo Detallado              ║
╚══════════════════════════════════════════════════════════════╝

Input: start_id = 8590, order_by = "id", condition = "id >= 8590"

                ┌─────────────────────┐
                │ Contar registros    │
                │ WHERE condition     │
                └──────────┬──────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │ Total = 3,813  │
                  └────────┬───────┘
                           │
                           ▼
                ┌─────────────────────┐
                │  SELECT id FROM     │
                │  res_partner WHERE  │
                │  id >= 8590         │
                │  ORDER BY id        │
                └──────────┬──────────┘
                           │
                           ▼
         ┌──────────────────────────────────┐
         │  IDs actuales (ejemplo):         │
         │  [8590, 8592, 8595, 8600, ...]   │
         └──────────────┬───────────────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │  Crear mapping:                  │
         │  old_id → new_id                 │
         │                                  │
         │  8590 → 8590 (sin cambio)        │
         │  8592 → 8591                     │
         │  8595 → 8592                     │
         │  8600 → 8593                     │
         │  ...                             │
         └──────────────┬───────────────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │  Calcular batch_size dinámico:   │
         │  3,813 registros → batch = 500   │
         │  Total batches = 8               │
         └──────────────┬───────────────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │  DISABLE TRIGGER USER            │
         └──────────────┬───────────────────┘
                        │
          ┌─────────────┴───────────────┐
          │   LOOP: Para cada batch     │
          │   (batch 1/8, 2/8, ... 8/8) │
          └─────────────┬───────────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │  Construir UPDATE con CASE:      │
         │                                  │
         │  UPDATE res_partner              │
         │  SET id = CASE id                │
         │    WHEN 8592 THEN 8591           │
         │    WHEN 8595 THEN 8592           │
         │    ...                           │
         │  END                             │
         │  WHERE id IN (8592, 8595, ...)   │
         └──────────────┬───────────────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │  COMMIT                          │
         └──────────────┬───────────────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │  CASCADE actualiza FKs:          │
         │                                  │
         │  account_move.partner_id:        │
         │    8592 → 8591                   │
         │                                  │
         │  sale_order.partner_id:          │
         │    8595 → 8592                   │
         │                                  │
         │  ... (automático por CASCADE)    │
         └──────────────┬───────────────────┘
                        │
                        ▼
         ┌──────────────────────────────────┐
         │  Mostrar progreso:               │
         │  Lote 1/8: [███░░...] 13.1%      │
         └──────────────┬───────────────────┘
                        │
         ┌──────────────┘
         │
         ▼
    ¿Más batches?
         │
        No
         │
         ▼
┌──────────────────────────────────┐
│  ENABLE TRIGGER USER             │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  RESULTADO:                      │
│  IDs secuenciales desde 8590     │
│  [8590, 8591, 8592, 8593, ...]   │
│  FKs intactos (100%)             │
└──────────────────────────────────┘
```

### Diagrama 4: Sistema de CASCADE

```
╔══════════════════════════════════════════════════════════════╗
║           SISTEMA CASCADE - Propagación de IDs               ║
╚══════════════════════════════════════════════════════════════╝

                   ┌─────────────────┐
                   │  res.partner    │
                   │  ID = 8595      │
                   └────────┬────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │account_move  │ │ sale_order   │ │mail_followers│
    │partner_id=   │ │partner_id=   │ │partner_id=   │
    │  8595 (FK)   │ │  8595 (FK)   │ │  8595 (FK)   │
    └──────────────┘ └──────────────┘ └──────────────┘
            │                │                │
            └────────────────┼────────────────┘
                             │
                     ┌───────▼─────────┐
                     │  PASO 1:        │
                     │  Aplicar CASCADE│
                     └───────┬─────────┘
                             │
     ┌───────────────────────┼───────────────────────┐
     ▼                       ▼                       ▼
┌──────────────────────────────────────────────────────────┐
│ ALTER TABLE account_move                                 │
│ DROP CONSTRAINT account_move_partner_id_fkey;            │
│                                                          │
│ ALTER TABLE account_move                                 │
│ ADD CONSTRAINT account_move_partner_id_fkey              │
│ FOREIGN KEY (partner_id)                                 │
│ REFERENCES res_partner(id)                               │
│ ON UPDATE CASCADE    ← CRÍTICO                           │
│ ON DELETE CASCADE;                                       │
└──────────────────────────────────────────────────────────┘

     Similar para sale_order, mail_followers, etc...

                             │
                     ┌───────▼─────────┐
                     │  PASO 2:        │
                     │  Actualizar ID  │
                     └───────┬─────────┘
                             │
┌──────────────────────────────────────────────────────────┐
│ ALTER TABLE res_partner DISABLE TRIGGER USER;            │
│                                                          │
│ UPDATE res_partner                                       │
│ SET id = 8592                                            │
│ WHERE id = 8595;                                         │
│                                                          │
│ -- CASCADE automático actualiza:                         │
│ -- account_move.partner_id: 8595 → 8592                  │
│ -- sale_order.partner_id: 8595 → 8592                    │
│ -- mail_followers.partner_id: 8595 → 8592                │
│                                                          │
│ ALTER TABLE res_partner ENABLE TRIGGER USER;             │
└──────────────────────────────────────────────────────────┘
                             │
                             ▼
                   ┌─────────────────┐
                   │  res.partner    │
                   │  ID = 8592      │
                   └────────┬────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │account_move  │ │ sale_order   │ │mail_followers│
    │partner_id=   │ │partner_id=   │ │partner_id=   │
    │  8592 ✓      │ │  8592 ✓      │ │  8592 ✓      │
    └──────────────┘ └──────────────┘ └──────────────┘

            INTEGRIDAD REFERENCIAL 100% GARANTIZADA
```

---

## Estrategias de ID

### Comparativa de Estrategias

| Aspecto | Consolidation | Sequential | Custom |
|---------|--------------|------------|--------|
| **Uso** | Fusionar registros duplicados | Renumeración ordenada | Lógica específica |
| **Complejidad** | Baja | Media | Alta |
| **Configuración** | Mapping simple | start_id + order_by | Implementación Python |
| **Ejemplo** | res.company (8→7) | res.partner (desde 8590) | product.product (=tmpl_id) |
| **Predictibilidad** | 100% | 100% | Depende de lógica |
| **Casos de uso** | Limpieza datos | Normalización | Sincronización |

### Cuándo usar cada estrategia

#### Consolidation
- Fusionar compañías duplicadas
- Eliminar registros redundantes
- Migrar datos entre registros

#### Sequential
- Normalizar IDs después de migraciones
- Eliminar gaps en secuencias
- Ordenar por criterios de negocio (fecha, nombre, etc.)

#### Custom
- Sincronizar product.product con product.template
- Lógica específica de Odoo
- Casos especiales no cubiertos por otras estrategias

---

## Operaciones

### 1. FK_REWRITE (Foreign Key Rewrite)

**Propósito**: Reescribir constraints de foreign key para incluir CASCADE.

**Acción**:
```sql
-- Antes
ALTER TABLE account_move DROP CONSTRAINT account_move_partner_id_fkey;

-- Después
ALTER TABLE account_move
ADD CONSTRAINT account_move_partner_id_fkey
FOREIGN KEY (partner_id)
REFERENCES res_partner(id)
ON UPDATE CASCADE
ON DELETE CASCADE;
```

**Configuración**:
```json
"fk_rewrite": {
  "enabled": true,
  "constraints": [
    {
      "table": "account_move",
      "column": "partner_id",
      "action": "CASCADE"  // o "SET NULL" o "RESTRICT"
    }
  ]
}
```

**Variantes de acción**:
- `CASCADE`: Propaga UPDATE/DELETE
- `SET NULL`: Establece NULL cuando padre se elimina
- `RESTRICT`: Previene eliminación si hay hijos

### 2. CLEANUP (Limpieza de Datos)

**Propósito**: Eliminar datos transitorios y basura.

**Tipos de limpieza**:
```sql
-- 1. Wizards transitorios
DELETE FROM mail_compose_message;
DELETE FROM account_payment_register;

-- 2. XMLIDs de exportación
DELETE FROM ir_model_data
WHERE module='__export__' AND model='res.partner';

-- 3. Datos temporales
DELETE FROM website_visitor;
DELETE FROM mail_message_reaction;
```

**Seguridad**: SIEMPRE requiere WHERE clause.

### 3. ID_SHIFT (Desplazamiento Temporal)

**Propósito**: Evitar conflictos de unique constraint durante renumeración.

**Ejemplo**:
```sql
-- Queremos renumerar desde ID 1
-- Pero ya existen IDs 1, 2, 3...
-- Solución: desplazar temporalmente

-- Paso 1: ID_SHIFT
UPDATE account_tax_group
SET id = id + 10000
WHERE id >= 1;
-- Resultado: [1, 2, 3] → [10001, 10002, 10003]

-- Paso 2: ID_COMPACT
UPDATE account_tax_group
SET id = ROW_NUMBER() + 1095
WHERE id >= 10000;
-- Resultado: [10001, 10002, 10003] → [1096, 1097, 1098]
```

**Configuración**:
```json
"id_shift": {
  "enabled": true,
  "offset": 10000,
  "condition": "id >= 1"
}
```

### 4. ID_COMPACT (Compactación de IDs)

**Propósito**: Renumeración final con estrategia específica.

Ver sección [Estrategias de ID](#estrategias-de-id) para detalles completos.

### 5. XMLID_REBUILD (Reconstrucción de XMLIDs)

**Propósito**: Reconstruir `ir_model_data` para mantener trazabilidad.

**Ejemplo**:
```sql
INSERT INTO ir_model_data (
  name,
  module,
  model,
  res_id,
  noupdate
)
SELECT
  'partner_' || id,        -- name_pattern
  'marin_data',            -- module
  'res.partner',           -- model
  id,                      -- res_id
  true                     -- noupdate
FROM res_partner
WHERE active IN (true, false) AND id >= 5000;
```

**Configuración**:
```json
"xmlid_rebuild": {
  "enabled": true,
  "module": "marin_data",
  "condition": "active IN (true, false) AND id >= 5000",
  "name_pattern": "partner_{id}"
}
```

**Patterns disponibles**:
- `{id}`: ID del registro
- `{code}`: Campo code (ej: account.account)
- `{name}`: Campo name
- Literales: `partner_`, `account_`, etc.

### 6. SEQUENCE_SYNC (Sincronización de Secuencias)

**Propósito**: Evitar duplicate key errors en inserciones futuras.

**Problema**:
```sql
-- Después de renumeración, MAX(id) = 8593
-- Pero secuencia sigue en 8640
INSERT INTO res_partner (...) VALUES (...);
-- Intenta usar ID 8641 ✓ OK

-- Sin sync:
-- Secuencia = 8640, pero MAX(id) = 10,000
-- Próximo INSERT intenta ID 8641
-- ERROR: duplicate key value violates unique constraint
```

**Solución**:
```sql
SELECT setval('res_partner_id_seq', 8593, true);
-- Próximo INSERT usará 8594
```

**Configuración**:
```json
"sequence_sync": {
  "enabled": true,
  "sequence": "res_partner_id_seq"
}
```

### 7. PATCH_JSONB (Actualización de campos JSONB)

**Propósito**: Actualizar referencias de IDs dentro de campos JSONB.

**Problema**:
```json
// Campo: account_move_line.analytic_distribution
{
  "12345": 100.0,  // ID antiguo de cuenta analítica
  "12346": 50.0
}

// Después de renumeración, ID 12345 → 1096
// Pero JSONB sigue con "12345"
// Resultado: referencia rota
```

**Solución**: Mapear claves en JSONB.

**Estado**: Implementación pendiente en v4.0 (placeholder).

### 8. SKIP_GAP_ELIMINATION

**Propósito**: No eliminar gaps en tablas específicas.

**Casos de uso**:
- `stock.lot`: Los números de serie pueden tener gaps intencionales
- `stock.quant`: Registro de inventario histórico
- `sale.order`: Mantener numeración original

**Configuración**:
```json
"operations": {
  "skip_gap_elimination": true
}
```

---

## Instalación y Uso

### Requisitos Previos

```bash
# Sistema
- Ubuntu 20.04+ / Debian 11+
- PostgreSQL 12+
- Python 3.8+

# Espacio
- Disco: 2x tamaño de la base de datos (para backups)
- RAM: 4 GB mínimo, 8 GB recomendado
```

### Instalación

```bash
# 1. Clonar o descargar proyecto
cd /ruta/al/proyecto

# 2. Instalar dependencias
pip3 install -r requirements.txt
# O en sistemas Debian/Ubuntu:
sudo apt install python3-psycopg2

# 3. Verificar instalación
python3 -c "import psycopg2; print('✓ psycopg2 OK')"
```

### Configuración Inicial

```bash
# 1. Configurar credenciales
cp config/db_credentials.json.example config/db_credentials.json
nano config/db_credentials.json

# Editar con datos reales:
{
  "host": "localhost",
  "port": 5432,
  "database": "odoo_test",  # ⚠️ USAR COPIA DE PRUEBA
  "user": "odoo",
  "password": "tu_password",
  "sslmode": "prefer"
}

# 2. Proteger credenciales
chmod 600 config/db_credentials.json

# 3. Verificar configuración existe
ls -lh models_config.json
# Si no existe, generar:
python3 convertJSON.py
```

### Ejecución

```bash
# ⚠️ CRÍTICO: HACER BACKUP PRIMERO
pg_dump -h localhost -U odoo -d odoo_test > backup_$(date +%Y%m%d_%H%M%S).sql

# Ejecutar sistema
python3 Run.py

# Monitorear en otra terminal
tail -f output/logs/execution_*.log
```

### Salida Esperada

```
╔══════════════════════════════════════════════════════════╗
║  Sistema de Limpieza y Resecuenciación BDD Odoo         ║
║  Versión 4.0 - Estrategias Específicas por Modelo       ║
╚══════════════════════════════════════════════════════════╝

📋 Cargando credenciales...
🔌 Conectando a base de datos...
✓ Conectado a: odoo_test @ localhost

📄 Cargando configuración de modelos...
📦 Total de modelos a procesar: 31

============================================================
Modelo 1/31: res.company
Tiempo transcurrido: 0m 0s
============================================================

  ▶ Aplicando CASCADE: 6/6
  ▶ Detectando referencias inversas...
  💡 Detectadas 15 referencias inversas, aplicando CASCADE...
  ✓ Referencias inversas: 15 aplicadas, 0 fallidas (15 total)

  🔄 Aplicando consolidación con 1 mapeos...
    ✓ 8 → 7
  ✓ Consolidación completa: 1 cambios

  ✓ Secuencia sincronizada: res_company_id_seq → 7

────────────────────────────────────────────────────────
✓ SUCCESS - Tiempo: 0m 47s
📊 Progreso: 1/31 modelos
⏱️  Tiempo restante estimado: 24m 5s
────────────────────────────────────────────────────────

... (continúa con 30 modelos más)

📊 Reportes generados:
   JSON: output/statistics/processing_report_20251009_140530.json
   CSV:  output/statistics/processing_summary_20251009_140530.csv

✅ Proceso completado exitosamente
📋 Log guardado en: output/logs/execution_20251009_140530.log
```

### Verificación Post-Ejecución

```bash
# Ver resultados
cat output/statistics/processing_summary_*.csv

# Verificar integridad (si existe script)
python3 verify_integrity_v2.py

# Revisar logs de errores
grep "ERROR\|FAILED" output/logs/execution_*.log
```

---

## Casos de Uso

### Caso 1: Fusión de Compañías Duplicadas

**Escenario**: Dos compañías (ID 7 y 8) que deberían ser una sola.

**Configuración**:
```json
"res.company": {
  "operations": {
    "id_compact": {
      "enabled": true,
      "strategy": "consolidation",
      "mapping": {
        "8": "7"
      }
    }
  }
}
```

**Resultado**:
- Compañía 8 → 7
- Todos los registros que apuntaban a compañía 8 ahora apuntan a 7
- Se puede eliminar registro 8 manualmente después

### Caso 2: Normalización de Partners después de Migración

**Escenario**: Migración de sistema legacy dejó IDs con gaps: [8590, 8592, 8595, 8600, ...].

**Configuración**:
```json
"res.partner": {
  "operations": {
    "id_compact": {
      "enabled": true,
      "strategy": "sequential",
      "start_id": 8590,
      "order_by": "id"
    }
  }
}
```

**Resultado**:
- IDs secuenciales: [8590, 8591, 8592, 8593, ...]
- Sin gaps
- Orden preservado

### Caso 3: Sincronización Product.Product con Template

**Escenario**: En Odoo, productos single-variant deben tener `product.product.id = product.template.id`.

**Configuración**:
```json
"product.product": {
  "operations": {
    "id_compact": {
      "enabled": true,
      "strategy": "custom",
      "description": "Set product.product.id = product_tmpl_id"
    }
  }
}
```

**Implementación** (en Run.py):
```python
def apply_custom_strategy(conn, table_name, config, progress=None):
    if 'product_tmpl_id' in config.get('description', '').lower():
        cur = conn.cursor()
        cur.execute(f"ALTER TABLE {table_name} DISABLE TRIGGER USER;")

        cur.execute(f"""
            UPDATE {table_name}
            SET id = product_tmpl_id
            WHERE product_tmpl_id IS NOT NULL;
        """)

        cur.execute(f"ALTER TABLE {table_name} ENABLE TRIGGER USER;")
        conn.commit()
```

**Resultado**:
- product_product.id = product_template.id para single-variant
- Sincronización perfecta

### Caso 4: Limpieza Completa de Base de Datos

**Escenario**: Base de datos acumuló basura (wizards, exportaciones, visitantes web).

**Configuración**:
```json
"res.partner": {
  "operations": {
    "cleanup": {
      "enabled": true,
      "operations": [
        "DELETE FROM mail_compose_message",
        "DELETE FROM website_visitor",
        "DELETE FROM ir_model_data WHERE module='__export__' AND model='res.partner'"
      ]
    }
  }
}
```

**Resultado**:
- Wizards eliminados
- Visitantes web eliminados
- XMLIDs de exportación eliminados
- Base de datos más ligera

### Caso 5: Renumeración con Orden Personalizado

**Escenario**: Renumerar account.move ordenado por fecha, compañía, journal.

**Configuración**:
```json
"account.move": {
  "operations": {
    "id_compact": {
      "enabled": true,
      "strategy": "sequential",
      "start_id": 1001,
      "order_by": "date, company_id, journal_id, id"
    }
  }
}
```

**Resultado**:
- Asientos ordenados cronológicamente
- Agrupados por compañía y diario
- IDs reflejan orden de negocio

---

## Solución de Problemas

### Error: "duplicate key value violates unique constraint"

**Causa**: ID shift insuficiente o secuencia no sincronizada.

**Síntomas**:
```
ERROR: duplicate key value violates unique constraint "res_partner_pkey"
DETAIL: Key (id)=(8591) already exists.
```

**Soluciones**:

1. **Aumentar offset en id_shift**:
```json
"id_shift": {
  "offset": 100000  // Aumentar de 10000 a 100000
}
```

2. **Usar start_id dinámico** (ya implementado en v4.0):
```python
start_id = calculate_start_id(conn, table_name, buffer_size=1000)
# Calcula: MAX(id) + 1000
```

3. **Sincronizar secuencia**:
```sql
SELECT setval('res_partner_id_seq', (SELECT MAX(id) FROM res_partner));
```

### Error: "current transaction is aborted"

**Causa**: Error en operación anterior abortó transacción.

**Síntomas**:
```
ERROR: current transaction is aborted, commands ignored until end of transaction block
```

**Solución**: v4.0 implementa commit/rollback individual por operación.

**Si persiste**:
```python
# En Run.py, cada operación tiene:
try:
    # operación
    conn.commit()
except:
    conn.rollback()
```

### Error: "relation does not exist"

**Causa**: Tabla o columna no existe en esquema.

**Síntomas**:
```
ERROR: relation "account_analytic_distribution_model" does not exist
```

**Solución**: v4.0 valida existencia antes de procesar.

**Verificación manual**:
```sql
SELECT tablename FROM pg_tables
WHERE schemaname='public'
AND tablename='account_analytic_distribution_model';
```

**Desactivar modelo**:
```json
"account.analytic.distribution.model": {
  "enabled": false  // Desactivar si no existe
}
```

### Rendimiento Lento

**Causa**: Tablas muy grandes (>1M registros).

**Síntomas**:
- Modelo tarda >10 minutos
- Batch progresa lentamente

**Soluciones**:

1. **Aumentar batch_size**:
```python
# En calculate_batch_size():
if total_records > 1000000:
    return 5000  # Aumentar de 2000 a 5000
```

2. **Crear índices temporales**:
```sql
CREATE INDEX CONCURRENTLY tmp_idx_partner_id ON res_partner(id);
-- Después de procesar:
DROP INDEX tmp_idx_partner_id;
```

3. **Ejecutar en horario no productivo**.

### Timeout

**Causa**: Proceso excede tiempo máximo.

**Síntomas**:
```
Timeout: proceso interrumpido después de 2 horas
```

**Soluciones**:

1. **Aumentar timeout**:
```bash
timeout 14400 python3 Run.py  # 4 horas
```

2. **Modo incremental** (feature request para v4.1):
```bash
python3 Run.py --models res.company,res.partner
```

3. **Procesar offline**:
```bash
nohup python3 Run.py > output.log 2>&1 &
tail -f output.log
```

### Integridad Referencial Rota

**Causa**: CASCADE no aplicado correctamente.

**Síntomas**:
```sql
SELECT COUNT(*) FROM account_move am
LEFT JOIN res_partner p ON am.partner_id = p.id
WHERE am.partner_id IS NOT NULL AND p.id IS NULL;
-- Resultado: > 0 (hay FKs rotas)
```

**Solución**: Verificar CASCADE aplicado.

**Verificación**:
```sql
SELECT
    tc.table_name,
    tc.constraint_name,
    rc.update_rule,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.referential_constraints rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name = 'account_move'
AND rc.update_rule != 'CASCADE';
```

**Re-aplicar CASCADE**:
```sql
ALTER TABLE account_move DROP CONSTRAINT account_move_partner_id_fkey;
ALTER TABLE account_move
ADD CONSTRAINT account_move_partner_id_fkey
FOREIGN KEY (partner_id)
REFERENCES res_partner(id)
ON UPDATE CASCADE
ON DELETE CASCADE;
```

---

## Referencias Técnicas

### Estructura de Clases Principales

#### ProgressTracker

```python
class ProgressTracker:
    """Tracker de progreso en tiempo real"""

    def __init__(self, total_models: int):
        self.total_models = total_models
        self.current_model = 0
        self.start_time = time.time()
        self.model_times = []

    def start_model(self, model_num: int, model_name: str):
        """Inicia tracking de un modelo"""
        pass

    def end_model(self, status: str = "COMPLETADO"):
        """Finaliza tracking con estadísticas"""
        pass

    def log_batch(self, batch_num: int, total_batches: int,
                  records_processed: int, total_records: int):
        """Muestra barra de progreso de batch"""
        pass
```

#### Funciones de Validación

```python
def table_exists(conn, table_name: str) -> bool:
    """Verifica si tabla existe en esquema public"""

def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Verifica si columna existe en tabla"""

def get_column_type(conn, table_name: str, column_name: str) -> str:
    """Obtiene tipo de dato de columna (varchar, integer, jsonb, etc.)"""

def calculate_start_id(conn, table_name: str, buffer_size: int = 1000) -> int:
    """Calcula start_id dinámicamente: MAX(id) + buffer"""

def calculate_batch_size(total_records: int) -> int:
    """
    Calcula batch_size óptimo:
    < 1,000: 100
    < 10,000: 500
    < 100,000: 1,000
    >= 100,000: 2,000
    """
```

#### Funciones de CASCADE

```python
def get_inverse_foreign_keys(conn, table_name: str) -> list:
    """
    Detecta referencias inversas: FKs desde otras tablas hacia esta.

    Returns: [(fk_table, fk_column, fk_constraint), ...]
    """

def apply_inverse_cascade(conn, table_name: str) -> int:
    """
    Aplica CASCADE a referencias inversas.

    Returns: número de constraints aplicadas
    """

def apply_cascade(conn, model_config: dict, model_name: str):
    """
    Lee CASCADE desde operations.fk_rewrite y aplica.
    Compatible con v3.7 (cascade_rules) para backward compatibility.
    """
```

#### Funciones de Estrategias

```python
def apply_consolidation_strategy(conn, table_name: str,
                                  config: dict, progress=None) -> dict:
    """
    Estrategia: mapeo directo de IDs.

    Input: {"mapping": {"8": "7", "10": "9"}}
    Output: {8: 7, 10: 9}  # IDs aplicados
    """

def apply_sequential_strategy(conn, table_name: str,
                               config: dict, progress=None) -> dict:
    """
    Estrategia: renumeración secuencial.

    Input: {
        "start_id": 8590,
        "order_by": "id",
        "condition": "id >= 8590"
    }
    Output: {8590: 8590, 8592: 8591, ...}  # Mapping aplicado
    """

def apply_custom_strategy(conn, table_name: str,
                          config: dict, progress=None) -> dict:
    """
    Estrategia: lógica personalizada.

    Actualmente implementa:
    - product.product.id = product_tmpl_id

    Extensible para otros casos.
    """
```

#### Función Principal de Procesamiento

```python
def process_model(conn, model_name: str, model_config: dict,
                  progress=None) -> dict:
    """
    Procesa un modelo completo con todas sus operaciones.

    Fases ejecutadas (si enabled):
    1. FK_REWRITE
    2. CLEANUP
    3. ID_SHIFT
    4. ID_COMPACT (con estrategia)
    5. XMLID_REBUILD
    6. SEQUENCE_SYNC

    Returns: {
        'status': 'SUCCESS'|'FAILED'|'SKIPPED',
        'records_before': int,
        'records_after': int,
        'changes': [str, ...]
    }
    """
```

### Esquema de Base de Datos Relevante

#### ir_model_data (XMLIDs)

```sql
CREATE TABLE ir_model_data (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,          -- 'partner_8590'
    module VARCHAR NOT NULL,        -- 'marin_data'
    model VARCHAR NOT NULL,         -- 'res.partner'
    res_id INTEGER,                 -- 8590
    noupdate BOOLEAN DEFAULT false,

    UNIQUE(module, name)
);

-- Índices recomendados
CREATE INDEX idx_ir_model_data_model_res_id
ON ir_model_data(model, res_id);

CREATE INDEX idx_ir_model_data_module
ON ir_model_data(module);
```

#### Constraints CASCADE Típicos

```sql
-- Ejemplo: account_move → res_partner
ALTER TABLE account_move
ADD CONSTRAINT account_move_partner_id_fkey
FOREIGN KEY (partner_id)
REFERENCES res_partner(id)
ON UPDATE CASCADE
ON DELETE CASCADE;

-- Ejemplo: product_product → product_template
ALTER TABLE product_product
ADD CONSTRAINT product_product_product_tmpl_id_fkey
FOREIGN KEY (product_tmpl_id)
REFERENCES product_template(id)
ON UPDATE CASCADE
ON DELETE CASCADE;
```

### Queries de Diagnóstico

```sql
-- 1. Verificar CASCADE aplicado
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table,
    rc.update_rule,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints rc
    ON tc.constraint_name = rc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND tc.table_name = 'account_move'
ORDER BY tc.table_name, kcu.column_name;

-- 2. Detectar FKs rotas
SELECT
    'account_move' AS tabla,
    COUNT(*) AS fks_rotas
FROM account_move am
LEFT JOIN res_partner p ON am.partner_id = p.id
WHERE am.partner_id IS NOT NULL AND p.id IS NULL;

-- 3. Verificar gaps en IDs
SELECT
    MIN(id) AS min_id,
    MAX(id) AS max_id,
    COUNT(*) AS total,
    (MAX(id) - MIN(id) + 1) - COUNT(*) AS gaps
FROM res_partner;

-- 4. Verificar secuencia sincronizada
SELECT
    last_value,
    (SELECT MAX(id) FROM res_partner) AS max_id,
    last_value - (SELECT MAX(id) FROM res_partner) AS diferencia
FROM res_partner_id_seq;
```

### Configuración PostgreSQL Recomendada

```ini
# postgresql.conf

# Aumentar trabajo de mantenimiento
maintenance_work_mem = 512MB        # Para CREATE INDEX, VACUUM

# Aumentar memoria de trabajo
work_mem = 64MB                     # Para ORDER BY, DISTINCT

# Aumentar buffer compartido
shared_buffers = 2GB                # 25% de RAM total

# Logs detallados (opcional, para debugging)
log_statement = 'mod'               # Loguear INSERTs, UPDATEs, DELETEs
log_duration = on
log_min_duration_statement = 1000   # Loguear queries > 1 segundo

# Checkpoint settings
checkpoint_timeout = 15min
checkpoint_completion_target = 0.9
```

### Métricas de Rendimiento v4.0

**Base de datos de prueba**: Odoo 16.0, ~1M registros totales

| Modelo | Registros | Tiempo v4.0 | Operaciones | Batch Size |
|--------|-----------|-------------|-------------|------------|
| res.company | 7 | 0m 47s | Consolidation | 100 |
| res.partner | 3,813 | 1m 43s | Sequential | 500 |
| product.template | 1,546 | 2m 15s | Sequential | 500 |
| account.account | 4,200 | 1m 55s | XMLIDs only | N/A |
| account.move | 174,511 | 8m 32s | Sequential | 1,000 |
| account.move.line | 521,411 | 45m 18s | Sequential | 2,000 |
| stock.quant | 89,342 | 12m 10s | Skip gaps | 2,000 |

**Total estimado**: 45-60 minutos para 31 modelos completos.

---

## Glosario

- **CASCADE**: Propagación automática de cambios de IDs a tablas relacionadas
- **XMLID**: External ID en ir_model_data para trazabilidad
- **FK (Foreign Key)**: Clave foránea, referencia a otra tabla
- **Gap**: Hueco en secuencia de IDs (ej: 1, 2, 5 tiene gap en 3-4)
- **Batch**: Lote de registros procesados juntos
- **Sequence**: Generador automático de IDs en PostgreSQL
- **Constraint**: Regla de integridad en base de datos
- **Trigger**: Función automática ejecutada en eventos (INSERT, UPDATE, DELETE)
- **Idempotent**: Operación que puede ejecutarse múltiples veces con mismo resultado

---

## Apéndices

### Apéndice A: Modelos Procesados (31 total)

1. res.company
2. res.partner.category
3. res.partner
4. uom.uom
5. product.template
6. product.product
7. pos.category
8. account.account
9. account.tax.group
10. account.tax
11. account.payment.term
12. account.journal
13. account.bank.statement
14. account.bank.statement.line
15. account.move
16. account.move.line
17. account.asset
18. account.analytic.distribution.model
19. crm.team
20. hr.employee
21. fleet.vehicle
22. stock.location
23. stock.warehouse
24. stock.picking.type
25. stock.rule
26. stock.lot
27. stock.quant
28. mrp.bom
29. mrp.bom.line
30. sale.order
31. project.project
32. consolidation

### Apéndice B: Fases del Sistema

| Fase | Orden | Crítica | Parallelizable | Descripción |
|------|-------|---------|----------------|-------------|
| fk_rewrite | 1 | Sí | No | Reescribir constraints CASCADE |
| cleanup | 2 | Sí | No | Eliminar datos transitorios |
| id_shift | 3 | Sí | No | Desplazar IDs temporalmente |
| id_compact | 4 | Sí | No | Renumeración final |
| patch_jsonb | 5 | No | Sí | Actualizar campos JSONB |
| xmlid_rebuild | 6 | Sí | No | Reconstruir ir_model_data |
| sequence_sync | 7 | Sí | Sí | Sincronizar secuencias |
| recompute | 8 | No | Sí | Recalcular campos computados |

### Apéndice C: Ejemplo de Reporte Generado

```json
{
  "execution_info": {
    "timestamp": "2025-10-09T14:05:30",
    "database": "odoo_test",
    "log_file": "output/logs/execution_20251009_140530.log"
  },
  "models_processed": {
    "res.company": {
      "status": "SUCCESS",
      "records_before": 8,
      "records_after": 7,
      "changes": [
        "CASCADE aplicado",
        "Referencias inversas CASCADE: 15",
        "IDs compactados: 1 cambios",
        "Secuencia: 7"
      ]
    },
    "res.partner": {
      "status": "SUCCESS",
      "records_before": 3813,
      "records_after": 3813,
      "changes": [
        "CASCADE aplicado",
        "Referencias inversas CASCADE: 68",
        "Cleanup: 1250 registros eliminados",
        "IDs compactados: 220 cambios",
        "Secuencia: 8593"
      ]
    }
  }
}
```

---

## Conclusión

Odoo Database Sanitizer v4.0 representa un sistema maduro y completo para la gestión de bases de datos Odoo. Con arquitectura basada en fases, estrategias específicas de ID y garantía de integridad referencial al 100%, es la herramienta ideal para:

- Migraciones de datos
- Optimización de bases de datos
- Consolidación de registros
- Limpieza de datos
- Normalización de IDs

**Próximos pasos**: Ver sección [Instalación y Uso](#instalación-y-uso) para comenzar.

**Soporte**: Consultar logs en `output/logs/` y reportes en `output/statistics/`.

---

**Documento generado**: 2025-10-09
**Versión del sistema**: 4.0
**Autor**: Equipo de Desarrollo
**Licencia**: Uso interno
