# Plan de Desarrollo v3: Sistema de Limpieza y Resecuenciación de Base de Datos Odoo

**Fecha:** 2025-10-03
**Versión:** 3.0
**Enfoque:** Script Python único con procesamiento directo a base de datos

---

## 📋 ÍNDICE

1. [Arquitectura General](#arquitectura-general)
2. [Diagrama de Flujo Principal](#diagrama-de-flujo-principal)
3. [Diagrama de Navegación entre Componentes](#diagrama-de-navegación-entre-componentes)
4. [Flujo de Procesamiento por Modelo](#flujo-de-procesamiento-por-modelo)
5. [Estructura del Script Python](#estructura-del-script-python)
6. [Configuración JSON](#configuración-json)
7. [Reglas de Limpieza y Transformación](#reglas-de-limpieza-y-transformación)
8. [Manejo de Errores y Rollback](#manejo-de-errores-y-rollback)
9. [Archivo de Estadísticas](#archivo-de-estadísticas)
10. [Implementación y Ejecución](#implementación-y-ejecución)

---

## 🏗️ ARQUITECTURA GENERAL

```
╔══════════════════════════════════════════════════════════════════════╗
║                    ARQUITECTURA DEL SISTEMA v3                       ║
╚══════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────┐
│                         CAPA DE ENTRADA                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────┐      ┌──────────────────────────────┐   │
│  │  db_credentials.json │      │ models_processing_config.json│   │
│  │  ────────────────────│      │ ──────────────────────────────│   │
│  │  • host              │      │  • execution_order           │   │
│  │  • port              │      │  • models:                   │   │
│  │  • database          │      │    - res.partner             │   │
│  │  • user              │      │    - account.account         │   │
│  │  • password          │      │    - product.template        │   │
│  └──────────────────────┘      │    - (30+ modelos)           │   │
│                                 └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CAPA DE PROCESAMIENTO CENTRAL                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│                    ┌─────────────────────────┐                     │
│                    │   main_processor.py     │                     │
│                    │   ═══════════════════   │                     │
│                    │                         │                     │
│                    │  1. Conexión a BDD      │                     │
│                    │  2. Carga de JSON       │                     │
│                    │  3. Validaciones        │                     │
│                    │  4. Iteración Modelos   │                     │
│                    │  5. Limpieza de Data    │                     │
│                    │  6. Resecuenciación     │                     │
│                    │  7. Estadísticas        │                     │
│                    │                         │                     │
│                    └─────────────────────────┘                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CAPA DE BASE DE DATOS                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│              ┌──────────────────────────────────┐                  │
│              │   PostgreSQL - Odoo Database     │                  │
│              │   ══════════════════════════════ │                  │
│              │                                  │                  │
│              │  Operaciones:                    │                  │
│              │  • DELETE (wizards, modules)     │                  │
│              │  • UPDATE (gaps, IDs, nombres)   │                  │
│              │  • ALTER (foreign keys)          │                  │
│              │  • SELECT (validaciones)         │                  │
│              │                                  │                  │
│              │  Tablas afectadas:               │                  │
│              │  • res_partner                   │                  │
│              │  • account_account               │                  │
│              │  • product_template              │                  │
│              │  • ir_model_data                 │                  │
│              │  • (30+ tablas)                  │                  │
│              └──────────────────────────────────┘                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         CAPA DE SALIDA                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────────┐      ┌──────────────────────────────┐ │
│  │  processing_report.json│      │  processing_summary.csv      │ │
│  │  ───────────────────────│      │  ─────────────────────────── │ │
│  │  • execution_info      │      │  model,before,after,deleted  │ │
│  │  • validation_checks   │      │  res.partner,3761,3450,311   │ │
│  │  • models_processed    │      │  account.account,856,856,0   │ │
│  │  • summary             │      │  ...                         │ │
│  │  • errors/warnings     │      └──────────────────────────────┘ │
│  └────────────────────────┘                                        │
│                                                                     │
│  ┌────────────────────────┐                                        │
│  │  execution.log         │                                        │
│  │  ───────────────────────│                                        │
│  │  [INFO] Starting...    │                                        │
│  │  [DEBUG] Processing... │                                        │
│  │  [ERROR] Failed...     │                                        │
│  └────────────────────────┘                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 DIAGRAMA DE FLUJO PRINCIPAL

```
╔══════════════════════════════════════════════════════════════════════╗
║                     FLUJO PRINCIPAL DE EJECUCIÓN                     ║
╚══════════════════════════════════════════════════════════════════════╝

                            ┌─────────┐
                            │  INICIO │
                            └────┬────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ Cargar Credenciales    │
                    │ db_credentials.json    │
                    └────────┬───────────────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │ Conectar a Base Datos  │
                    │ psycopg2.connect()     │
                    └────────┬───────────────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │ ¿Conexión exitosa?     │
                    └────────┬───────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
                   SI                NO
                    │                 │
                    ▼                 ▼
          ┌─────────────────┐   ┌──────────────┐
          │ Cargar JSON     │   │ Log Error    │
          │ Config Modelos  │   │ EXIT(1)      │
          └────────┬────────┘   └──────────────┘
                   │
                   ▼
          ┌─────────────────────────────┐
          │ Validar Configuración JSON  │
          │ • execution_order           │
          │ • models                    │
          │ • global_settings           │
          └────────┬────────────────────┘
                   │
                   ▼
          ┌─────────────────────────────┐
          │ VALIDACIONES PREVIAS        │
          │ ═════════════════════       │
          │                             │
          │ ✓ Directorio salida existe? │
          │ ✓ Permisos escritura?       │
          │ ✓ Espacio en disco?         │
          │ ✓ Versión PostgreSQL?       │
          └────────┬────────────────────┘
                   │
                   ▼
          ┌─────────────────────────────┐
          │ ¿Todas validaciones OK?     │
          └────────┬────────────────────┘
                   │
          ┌────────┴────────┐
          │                 │
         SI                NO
          │                 │
          ▼                 ▼
┌──────────────────┐   ┌─────────────────┐
│ Crear Directorio │   │ Mostrar Errores │
│ de Salida        │   │ EXIT(1)         │
└────────┬─────────┘   └─────────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ INICIO ITERACIÓN POR MODELO              │
│ ════════════════════════════════════     │
│                                          │
│ FOR modelo IN execution_order:           │
└────────┬─────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Obtener Configuración del Modelo        │
│ config = models[modelo]                 │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ ¿Es modelo tipo Wizard?                 │
└────────┬────────────────────────────────┘
         │
    ┌────┴────┐
    │         │
   SI        NO
    │         │
    ▼         ▼
┌─────────┐  ┌──────────────────────────────┐
│ DELETE  │  │ ¿Es account.account?         │
│ ALL     │  └──────────┬───────────────────┘
│ RECORDS │             │
└────┬────┘        ┌────┴────┐
     │             │         │
     │            SI        NO
     │             │         │
     │             ▼         ▼
     │    ┌────────────┐  ┌──────────────────────┐
     │    │ Aplicar    │  │ Procesamiento        │
     │    │ Regla      │  │ Estándar             │
     │    │ Especial   │  │ ══════════════       │
     │    │ Account    │  │                      │
     │    └─────┬──────┘  │ 1. Contar registros  │
     │          │         │ 2. Eliminar módulos  │
     │          │         │ 3. Eliminar gaps     │
     │          │         │ 4. Normalizar nombres│
     │          │         │ 5. Resecuenciar IDs  │
     │          │         │ 6. Update FKs        │
     │          │         └──────┬───────────────┘
     │          │                │
     └──────────┴────────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ Registrar          │
        │ Estadísticas       │
        │ del Modelo         │
        └────────┬───────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ COMMIT             │
        │ Transacción        │
        └────────┬───────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ ¿Hay más modelos?  │
        └────────┬───────────┘
                 │
            ┌────┴────┐
            │         │
           SI        NO
            │         │
            │         ▼
            │    ┌────────────────────────┐
            │    │ Generar Estadísticas   │
            │    │ Finales                │
            │    └────────┬───────────────┘
            │             │
            │             ▼
            │    ┌────────────────────────┐
            │    │ Escribir JSON          │
            │    │ processing_report.json │
            │    └────────┬───────────────┘
            │             │
            │             ▼
            │    ┌────────────────────────┐
            │    │ Escribir CSV           │
            │    │ processing_summary.csv │
            │    └────────┬───────────────┘
            │             │
            │             ▼
            │    ┌────────────────────────┐
            │    │ Cerrar Conexión BDD    │
            │    └────────┬───────────────┘
            │             │
            │             ▼
            │         ┌───────┐
            │         │  FIN  │
            │         └───────┘
            │
            └──────► (Continuar con siguiente modelo)
```

---

## 🧭 DIAGRAMA DE NAVEGACIÓN ENTRE COMPONENTES

```
╔══════════════════════════════════════════════════════════════════════╗
║              NAVEGACIÓN Y DEPENDENCIAS ENTRE MÓDULOS                 ║
╚══════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────┐
│                        main_processor.py                            │
│                        ═════════════════                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  def main():                                                        │
│      │                                                              │
│      ├──► load_credentials()                                        │
│      │       └──► config/db_credentials.json                        │
│      │                                                              │
│      ├──► connect_database()                                        │
│      │       └──► psycopg2.connect()                                │
│      │                                                              │
│      ├──► load_processing_config()                                  │
│      │       └──► config/models_processing_config.json              │
│      │                                                              │
│      ├──► validate_environment()                                    │
│      │       ├──► check_db_connection()                             │
│      │       ├──► create_output_directory()                         │
│      │       └──► verify_permissions()                              │
│      │                                                              │
│      ├──► process_all_models()                                      │
│      │       │                                                      │
│      │       └──► for model in execution_order:                     │
│      │               │                                              │
│      │               ├──► identify_model_type()                     │
│      │               │       ├──► is_wizard_model()                 │
│      │               │       ├──► is_account_model()                │
│      │               │       └──► is_standard_model()               │
│      │               │                                              │
│      │               ├──► process_single_model()                    │
│      │               │       │                                      │
│      │               │       ├──► count_records()                   │
│      │               │       │                                      │
│      │               │       ├──► delete_by_modules()               │
│      │               │       │       └──► SQL: DELETE FROM...       │
│      │               │       │                                      │
│      │               │       ├──► eliminate_gaps()                  │
│      │               │       │       └──► SQL: UPDATE...WITH...     │
│      │               │       │                                      │
│      │               │       ├──► normalize_names()                 │
│      │               │       │       └──► apply_naming_standard()   │
│      │               │       │                                      │
│      │               │       ├──► resequence_ids()                  │
│      │               │       │       ├──► create_id_mapping()       │
│      │               │       │       ├──► update_primary_keys()     │
│      │               │       │       └──► update_foreign_keys()     │
│      │               │       │                                      │
│      │               │       └──► validate_integrity()              │
│      │               │               └──► check_fk_constraints()    │
│      │               │                                              │
│      │               └──► collect_statistics()                      │
│      │                                                              │
│      └──► generate_final_report()                                   │
│              ├──► write_json_report()                               │
│              ├──► write_csv_summary()                               │
│              └──► write_execution_log()                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                    MÓDULOS AUXILIARES                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  database_utils.py                                                  │
│  ├── connect_to_db()                                                │
│  ├── execute_query()                                                │
│  ├── execute_batch()                                                │
│  └── close_connection()                                             │
│                                                                     │
│  validation_utils.py                                                │
│  ├── validate_json_schema()                                         │
│  ├── check_table_exists()                                           │
│  ├── verify_column_exists()                                         │
│  └── validate_foreign_keys()                                        │
│                                                                     │
│  transformation_utils.py                                            │
│  ├── parse_model_name()                                             │
│  ├── generate_new_id()                                              │
│  ├── apply_naming_convention()                                      │
│  └── clean_string_value()                                           │
│                                                                     │
│  statistics_utils.py                                                │
│  ├── init_stats_tracker()                                           │
│  ├── record_model_stats()                                           │
│  ├── calculate_summary()                                            │
│  └── format_output()                                                │
│                                                                     │
│  logger_utils.py                                                    │
│  ├── setup_logger()                                                 │
│  ├── log_info()                                                     │
│  ├── log_error()                                                    │
│  └── log_debug()                                                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📦 FLUJO DE PROCESAMIENTO POR MODELO

```
╔══════════════════════════════════════════════════════════════════════╗
║            FLUJO DETALLADO: PROCESAMIENTO DE UN MODELO               ║
╚══════════════════════════════════════════════════════════════════════╝

                    ┌────────────────────────┐
                    │  Recibir Modelo        │
                    │  + Configuración       │
                    └──────────┬─────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ Extraer Datos Config:  │
                    │ • table_name           │
                    │ • cleanup_rules        │
                    │ • naming_standard      │
                    │ • foreign_keys         │
                    └──────────┬─────────────┘
                               │
                               ▼
                ┌──────────────────────────────────┐
                │ FASE 1: ANÁLISIS INICIAL         │
                └──────────────┬───────────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ SELECT COUNT(*)        │
                    │ FROM table_name        │
                    │                        │
                    │ records_before = N     │
                    └──────────┬─────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ Detectar Gaps:         │
                    │                        │
                    │ SELECT id,             │
                    │   LAG(id) OVER (...)   │
                    │ WHERE gap > 1          │
                    │                        │
                    │ gaps_found = M         │
                    └──────────┬─────────────┘
                               │
                               ▼
                ┌──────────────────────────────────┐
                │ FASE 2: LIMPIEZA DE REGISTROS    │
                └──────────────┬───────────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ ¿Eliminar módulos?     │
                    └──────────┬─────────────┘
                               │
                          ┌────┴────┐
                          │         │
                         SI        NO
                          │         │
                          ▼         │
            ┌──────────────────┐    │
            │ DELETE FROM      │    │
            │ ir_model_data    │    │
            │ WHERE module IN  │    │
            │ ('__export__',   │    │
            │  'marin')        │    │
            │                  │    │
            │ deleted_count=X  │    │
            └────────┬─────────┘    │
                     │              │
                     └──────┬───────┘
                            │
                            ▼
                ┌──────────────────────────────────┐
                │ FASE 3: ELIMINACIÓN DE GAPS      │
                └──────────────┬───────────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ WITH numbered AS (     │
                    │   SELECT id,           │
                    │   ROW_NUMBER() OVER    │
                    │   (ORDER BY id) as rn  │
                    │ )                      │
                    │                        │
                    │ UPDATE table_name      │
                    │ SET id = rn            │
                    └──────────┬─────────────┘
                               │
                               ▼
                ┌──────────────────────────────────┐
                │ FASE 4: NORMALIZACIÓN NOMBRES    │
                └──────────────┬───────────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ ¿Aplicar naming std?   │
                    └──────────┬─────────────┘
                               │
                          ┌────┴────┐
                          │         │
                         SI        NO (account.account)
                          │         │
                          ▼         ▼
          ┌────────────────────┐  ┌─────────────────┐
          │ UPDATE table_name  │  │ Usar código     │
          │ SET name =         │  │ contable como   │
          │ CONCAT(            │  │ identificador   │
          │   model_name,      │  │                 │
          │   '_',             │  │ Mantener puntos │
          │   id               │  └─────────────────┘
          │ )                  │
          │                    │
          │ Reemplazar . por _ │
          └──────────┬─────────┘
                     │
                     └──────┬───────┘
                            │
                            ▼
                ┌──────────────────────────────────┐
                │ FASE 5: RESECUENCIACIÓN IDs      │
                └──────────────┬───────────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ Crear Mapeo ID:        │
                    │                        │
                    │ old_id → new_id        │
                    │ 5017 → 8590            │
                    │ 5018 → 8591            │
                    │ ...                    │
                    └──────────┬─────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ Deshabilitar Triggers: │
                    │                        │
                    │ ALTER TABLE table_name │
                    │ DISABLE TRIGGER ALL;   │
                    └──────────┬─────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ Actualizar IDs:        │
                    │                        │
                    │ FOR old, new IN map:   │
                    │   UPDATE table_name    │
                    │   SET id = new         │
                    │   WHERE id = old       │
                    └──────────┬─────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ Actualizar FKs:        │
                    │                        │
                    │ FOR each FK_table:     │
                    │   UPDATE FK_table      │
                    │   SET fk_column = new  │
                    │   WHERE fk_column=old  │
                    └──────────┬─────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ Rehabilitar Triggers:  │
                    │                        │
                    │ ALTER TABLE table_name │
                    │ ENABLE TRIGGER ALL;    │
                    └──────────┬─────────────┘
                               │
                               ▼
                ┌──────────────────────────────────┐
                │ FASE 6: VALIDACIÓN FINAL         │
                └──────────────┬───────────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ Verificar FKs:         │
                    │                        │
                    │ SELECT constraint_name │
                    │ FROM pg_constraint     │
                    │ WHERE violated         │
                    └──────────┬─────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ ¿FKs válidas?          │
                    └──────────┬─────────────┘
                               │
                          ┌────┴────┐
                          │         │
                         SI        NO
                          │         │
                          ▼         ▼
              ┌────────────────┐  ┌──────────┐
              │ SELECT COUNT   │  │ ROLLBACK │
              │ records_after  │  │          │
              └────────┬───────┘  │ Lanzar   │
                       │          │ Error    │
                       │          └──────────┘
                       ▼
              ┌────────────────────┐
              │ COMMIT             │
              └────────┬───────────┘
                       │
                       ▼
              ┌────────────────────┐
              │ Registrar Stats:   │
              │ • records_before   │
              │ • records_after    │
              │ • deleted          │
              │ • gaps_eliminated  │
              │ • duration         │
              └────────┬───────────┘
                       │
                       ▼
                 ┌──────────┐
                 │ RETORNAR │
                 │ resultado│
                 └──────────┘
```

---

## 💻 ESTRUCTURA DEL SCRIPT PYTHON

```python
#!/usr/bin/env python3
"""
Sistema de Limpieza y Resecuenciación de Base de Datos Odoo
Versión: 3.0
"""

import psycopg2
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import logging

# ══════════════════════════════════════════════════════════════
#                    SECCIÓN 1: CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════

def load_credentials():
    """Carga credenciales de conexión desde archivo seguro"""
    cred_file = 'config/db_credentials.json'

    if not os.path.exists(cred_file):
        raise FileNotFoundError(f"Archivo de credenciales no encontrado: {cred_file}")

    with open(cred_file, 'r') as f:
        return json.load(f)

def load_processing_config():
    """Carga configuración de procesamiento de modelos"""
    config_file = 'config/models_processing_config.json'

    with open(config_file, 'r') as f:
        config = json.load(f)

    # Validar estructura
    required_keys = ['execution_order', 'models', 'global_settings']
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Clave requerida '{key}' no encontrada en configuración")

    return config

# ══════════════════════════════════════════════════════════════
#                   SECCIÓN 2: CONEXIÓN A BDD
# ══════════════════════════════════════════════════════════════

def connect_database(credentials):
    """Establece conexión a PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=credentials['host'],
            port=credentials['port'],
            database=credentials['database'],
            user=credentials['user'],
            password=credentials['password'],
            sslmode=credentials.get('sslmode', 'prefer')
        )

        logging.info(f"✓ Conexión exitosa a: {credentials['database']}")
        return conn

    except psycopg2.Error as e:
        logging.error(f"✗ Error de conexión: {e}")
        raise

# ══════════════════════════════════════════════════════════════
#                   SECCIÓN 3: VALIDACIONES
# ══════════════════════════════════════════════════════════════

def validate_environment(config):
    """Ejecuta validaciones previas al procesamiento"""
    validations = {}

    # 1. Conexión a BDD
    try:
        creds = load_credentials()
        conn = connect_database(creds)
        conn.close()
        validations['db_connection'] = 'OK'
    except Exception as e:
        validations['db_connection'] = f'FAIL: {str(e)}'
        return validations

    # 2. Directorio de salida
    output_dir = config['global_settings']['output_directory']
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        validations['output_directory'] = 'CREATED'
    else:
        validations['output_directory'] = 'OK'

    # 3. Permisos de escritura
    test_file = os.path.join(output_dir, '.test_write')
    try:
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        validations['permissions'] = 'OK'
    except Exception as e:
        validations['permissions'] = f'FAIL: {str(e)}'

    # 4. Verificar tablas existen
    validations['tables_verified'] = verify_tables_exist(config)

    return validations

def verify_tables_exist(config):
    """Verifica que las tablas de los modelos existan"""
    creds = load_credentials()
    conn = connect_database(creds)
    cur = conn.cursor()

    missing_tables = []

    for model_name in config['execution_order']:
        if model_name in config['models']:
            table_name = config['models'][model_name]['table_name']

            cur.execute(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '{table_name}'
                );
            """)

            exists = cur.fetchone()[0]
            if not exists:
                missing_tables.append(table_name)

    conn.close()

    if missing_tables:
        return f"MISSING: {', '.join(missing_tables)}"
    return 'OK'

# ══════════════════════════════════════════════════════════════
#            SECCIÓN 4: FUNCIONES DE LIMPIEZA
# ══════════════════════════════════════════════════════════════

def count_records(conn, table_name):
    """Cuenta registros en una tabla"""
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table_name};")
    count = cur.fetchone()[0]
    cur.close()
    return count

def delete_by_modules(conn, table_name, modules_to_delete):
    """Elimina registros basados en módulos en ir_model_data"""
    cur = conn.cursor()

    modules_str = "','".join(modules_to_delete)

    query = f"""
        DELETE FROM ir_model_data
        WHERE module IN ('{modules_str}')
        AND model = '{table_name.replace('_', '.')}';
    """

    cur.execute(query)
    deleted = cur.rowcount
    conn.commit()
    cur.close()

    return deleted

def eliminate_gaps(conn, table_name):
    """Elimina gaps en secuencia de IDs"""
    cur = conn.cursor()

    # Detectar gaps
    cur.execute(f"""
        WITH gaps AS (
            SELECT id,
                   id - LAG(id) OVER (ORDER BY id) - 1 as gap_size
            FROM {table_name}
        )
        SELECT COUNT(*) FROM gaps WHERE gap_size > 0;
    """)

    gaps_count = cur.fetchone()[0]

    if gaps_count > 0:
        # Renumerar para eliminar gaps
        cur.execute(f"""
            WITH numbered AS (
                SELECT id,
                       ROW_NUMBER() OVER (ORDER BY id) as new_id
                FROM {table_name}
            )
            UPDATE {table_name} t
            SET id = n.new_id
            FROM numbered n
            WHERE t.id = n.id;
        """)

        conn.commit()

    cur.close()
    return gaps_count

def normalize_names(conn, table_name, model_name):
    """Aplica normalización de nombres según estándar"""
    cur = conn.cursor()

    clean_model = model_name.replace('.', '_')

    cur.execute(f"""
        UPDATE {table_name}
        SET name = CONCAT('{clean_model}_', id)
        WHERE name IS NOT NULL;
    """)

    conn.commit()
    cur.close()

def resequence_model_ids(conn, model_config):
    """Resecuencia IDs de un modelo"""
    table_name = model_config['table_name']
    start_id = model_config['cleanup_rules'].get('resequence_start_id', 1000)

    cur = conn.cursor()

    # 1. Obtener registros ordenados
    cur.execute(f"""
        SELECT id FROM {table_name}
        ORDER BY id;
    """)

    records = cur.fetchall()

    # 2. Crear mapeo old_id -> new_id
    id_mapping = {}
    new_id = start_id

    for (old_id,) in records:
        id_mapping[old_id] = new_id
        new_id += 1

    # 3. Deshabilitar triggers
    cur.execute(f"ALTER TABLE {table_name} DISABLE TRIGGER ALL;")

    # 4. Actualizar IDs
    for old_id, new_id in id_mapping.items():
        cur.execute(f"""
            UPDATE {table_name}
            SET id = {new_id}
            WHERE id = {old_id};
        """)

    # 5. Actualizar foreign keys
    update_foreign_keys(conn, table_name, id_mapping, model_config)

    # 6. Rehabilitar triggers
    cur.execute(f"ALTER TABLE {table_name} ENABLE TRIGGER ALL;")

    conn.commit()
    cur.close()

    return id_mapping

def update_foreign_keys(conn, table_name, id_mapping, model_config):
    """Actualiza referencias de foreign keys"""
    cur = conn.cursor()

    if 'foreign_keys' in model_config:
        for fk in model_config['foreign_keys']:
            ref_table = fk['references'].replace('.', '_')

            # Encontrar tablas que referencian este modelo
            cur.execute(f"""
                SELECT DISTINCT tc.table_name, kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND kcu.table_name != '{table_name}';
            """)

            fk_tables = cur.fetchall()

            # Actualizar cada referencia
            for fk_table, fk_column in fk_tables:
                for old_id, new_id in id_mapping.items():
                    cur.execute(f"""
                        UPDATE {fk_table}
                        SET {fk_column} = {new_id}
                        WHERE {fk_column} = {old_id};
                    """)

    cur.close()

# ══════════════════════════════════════════════════════════════
#            SECCIÓN 5: PROCESAMIENTO POR MODELO
# ══════════════════════════════════════════════════════════════

def process_single_model(conn, model_name, model_config):
    """Procesa un modelo individual"""
    result = {
        'status': 'PROCESSING',
        'records_before': 0,
        'records_after': 0,
        'records_deleted': 0,
        'gaps_eliminated': 0,
        'changes': [],
        'duration_seconds': 0
    }

    start_time = datetime.now()
    table_name = model_config['table_name']

    # 1. Contar registros iniciales
    result['records_before'] = count_records(conn, table_name)

    # 2. Determinar tipo de procesamiento
    if 'wizard' in model_name.lower():
        # Eliminar todos los registros de wizard
        cur = conn.cursor()
        cur.execute(f"DELETE FROM {table_name};")
        result['records_deleted'] = cur.rowcount
        conn.commit()
        cur.close()
        result['changes'].append("Deleted all wizard records")

    elif model_name == 'account.account':
        # Aplicar regla especial para account.account
        apply_account_special_rule(conn, model_config)
        result['changes'].append("Applied special naming rule: account code as ID")

    else:
        # Procesamiento estándar

        # Eliminar módulos específicos
        if 'delete_modules' in model_config.get('cleanup_rules', {}):
            deleted = delete_by_modules(
                conn,
                table_name,
                model_config['cleanup_rules']['delete_modules']
            )
            result['records_deleted'] = deleted
            result['changes'].append(f"Deleted {deleted} records from specified modules")

        # Eliminar gaps
        if model_config.get('gap_elimination', False):
            gaps = eliminate_gaps(conn, table_name)
            result['gaps_eliminated'] = gaps
            result['changes'].append(f"Eliminated {gaps} gaps in ID sequence")

        # Normalizar nombres
        if model_config.get('replace_dots_with_underscore', False):
            normalize_names(conn, table_name, model_name)
            result['changes'].append("Normalized ID names (replaced dots with underscores)")

        # Resecuenciar IDs
        if 'resequence_start_id' in model_config.get('cleanup_rules', {}):
            id_mapping = resequence_model_ids(conn, model_config)
            result['ids_resequenced'] = True
            result['new_id_range'] = f"{min(id_mapping.values())}-{max(id_mapping.values())}"
            result['foreign_keys_updated'] = len(id_mapping)
            result['changes'].append(f"Resequenced IDs starting from {model_config['cleanup_rules']['resequence_start_id']}")

    # 3. Contar registros finales
    result['records_after'] = count_records(conn, table_name)

    # 4. Calcular duración
    end_time = datetime.now()
    result['duration_seconds'] = (end_time - start_time).total_seconds()

    result['status'] = 'SUCCESS'
    return result

def apply_account_special_rule(conn, model_config):
    """Aplica regla especial para account.account"""
    table_name = model_config['table_name']
    cur = conn.cursor()

    # Usar código de cuenta contable como identificador
    # No reemplazar puntos por guiones bajos
    cur.execute(f"""
        UPDATE {table_name}
        SET name = CONCAT(code, ' - ', name)
        WHERE code IS NOT NULL;
    """)

    conn.commit()
    cur.close()

def process_all_models(conn, config):
    """Procesa todos los modelos según orden de ejecución"""
    stats = {
        'execution_info': {
            'timestamp': datetime.now().isoformat(),
            'script_version': '3.0',
            'database': config['global_settings'].get('database_name', 'odoo')
        },
        'models_processed': {},
        'summary': {
            'total_models': 0,
            'successful': 0,
            'failed': 0,
            'total_records_processed': 0,
            'total_records_deleted': 0,
            'total_gaps_eliminated': 0
        },
        'errors': [],
        'warnings': []
    }

    for model_name in config['execution_order']:
        if model_name not in config['models']:
            logging.warning(f"⚠ Modelo {model_name} en execution_order pero no en models")
            continue

        model_config = config['models'][model_name]

        logging.info(f"\n▶ Procesando: {model_name}")

        try:
            result = process_single_model(conn, model_name, model_config)

            stats['models_processed'][model_name] = result
            stats['summary']['successful'] += 1
            stats['summary']['total_records_processed'] += result['records_before']
            stats['summary']['total_records_deleted'] += result.get('records_deleted', 0)
            stats['summary']['total_gaps_eliminated'] += result.get('gaps_eliminated', 0)

            logging.info(f"  ✓ Completado: {result['records_after']} registros finales")

        except Exception as e:
            logging.error(f"  ✗ Error: {str(e)}")

            stats['models_processed'][model_name] = {
                'status': 'FAILED',
                'error': str(e)
            }
            stats['summary']['failed'] += 1
            stats['errors'].append({
                'model': model_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

            # Rollback en caso de error
            conn.rollback()

        stats['summary']['total_models'] += 1

    return stats

# ══════════════════════════════════════════════════════════════
#              SECCIÓN 6: GENERACIÓN DE ESTADÍSTICAS
# ══════════════════════════════════════════════════════════════

def generate_statistics(stats, config):
    """Genera archivos de estadísticas"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = config['global_settings']['output_directory']

    # 1. Archivo JSON detallado
    json_file = os.path.join(output_dir, f'processing_report_{timestamp}.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    logging.info(f"\n📊 Estadísticas generadas:")
    logging.info(f"  - JSON: {json_file}")

    # 2. Archivo CSV resumido
    csv_file = os.path.join(output_dir, f'processing_summary_{timestamp}.csv')
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("model,records_before,records_after,deleted,gaps_eliminated,duration_sec,status\n")

        for model, data in stats['models_processed'].items():
            f.write(f"{model},")
            f.write(f"{data.get('records_before', 0)},")
            f.write(f"{data.get('records_after', 0)},")
            f.write(f"{data.get('records_deleted', 0)},")
            f.write(f"{data.get('gaps_eliminated', 0)},")
            f.write(f"{data.get('duration_seconds', 0):.2f},")
            f.write(f"{data['status']}\n")

    logging.info(f"  - CSV:  {csv_file}")

    # 3. Resumen en consola
    print("\n" + "="*60)
    print("                 RESUMEN DE EJECUCIÓN")
    print("="*60)
    print(f"Total modelos:          {stats['summary']['total_models']}")
    print(f"Exitosos:               {stats['summary']['successful']}")
    print(f"Fallidos:               {stats['summary']['failed']}")
    print(f"Registros procesados:   {stats['summary']['total_records_processed']}")
    print(f"Registros eliminados:   {stats['summary']['total_records_deleted']}")
    print(f"Gaps eliminados:        {stats['summary']['total_gaps_eliminated']}")
    print("="*60)

# ══════════════════════════════════════════════════════════════
#                    SECCIÓN 7: FUNCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════

def setup_logging(config):
    """Configura sistema de logging"""
    log_dir = config['global_settings'].get('log_directory', 'logs')
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'execution_{timestamp}.log')

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return log_file

def main():
    """Función principal de ejecución"""

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Sistema de Limpieza y Resecuenciación de BDD Odoo      ║")
    print("║  Versión 3.0                                             ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    try:
        # 1. Cargar configuración
        print("📋 Cargando configuración...")
        config = load_processing_config()

        # 2. Configurar logging
        log_file = setup_logging(config)
        logging.info(f"Log file: {log_file}")

        # 3. Validar entorno
        print("\n🔍 Validando entorno...")
        validations = validate_environment(config)

        for check, status in validations.items():
            if 'FAIL' in str(status):
                logging.error(f"✗ {check}: {status}")
                sys.exit(1)
            else:
                logging.info(f"✓ {check}: {status}")

        # 4. Conectar a base de datos
        print("\n🔌 Conectando a base de datos...")
        creds = load_credentials()
        conn = connect_database(creds)

        # 5. Procesar todos los modelos
        print(f"\n⚙️  Procesando {len(config['execution_order'])} modelos...\n")
        stats = process_all_models(conn, config)

        # 6. Generar estadísticas
        print("\n📊 Generando estadísticas finales...")
        generate_statistics(stats, config)

        # 7. Cerrar conexión
        conn.close()
        logging.info("\n✓ Proceso completado exitosamente")

        print("\n✅ Ejecución finalizada con éxito")

    except Exception as e:
        logging.error(f"\n❌ Error fatal: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## 🔧 CONFIGURACIÓN JSON

### Archivo: `config/models_processing_config.json`

```json
{
  "execution_order": [
    "res.company",
    "res.partner",
    "product.category",
    "product.template",
    "product.product",
    "account.account",
    "account.journal",
    "account.move",
    "stock.warehouse",
    "wizard.models"
  ],

  "models": {
    "res.partner": {
      "table_name": "res_partner",
      "id_naming_standard": "{model_name}_{id}",
      "replace_dots_with_underscore": true,
      "gap_elimination": true,
      "cleanup_rules": {
        "delete_modules": ["__export__", "marin"],
        "id_threshold": 5000,
        "resequence_start_id": 8590
      },
      "name_normalization": {
        "remove_special_chars": true,
        "trim_whitespace": true
      },
      "foreign_keys": [
        {
          "field": "parent_id",
          "references": "res.partner",
          "on_delete": "SET NULL"
        },
        {
          "field": "company_id",
          "references": "res.company",
          "on_delete": "RESTRICT"
        }
      ]
    },

    "account.account": {
      "table_name": "account_account",
      "id_naming_standard": "use_account_code",
      "special_naming_rule": true,
      "use_account_code_as_id": true,
      "replace_dots_with_underscore": false,
      "gap_elimination": true,
      "cleanup_rules": {
        "delete_modules": ["__export__"],
        "preserve_base_module": true
      }
    },

    "product.template": {
      "table_name": "product_template",
      "id_naming_standard": "{model_name}_{id}",
      "replace_dots_with_underscore": true,
      "gap_elimination": true,
      "cleanup_rules": {
        "delete_modules": ["__export__"],
        "resequence_start_id": 1000
      }
    },

    "wizard.models": {
      "action": "delete_all_records",
      "table_name": "wizard_*",
      "patterns": [
        "wizard.*",
        "*.wizard"
      ],
      "reason": "Transient models - no data persistence needed"
    }
  },

  "global_settings": {
    "output_directory": "/home/sistemas3/output/statistics",
    "log_directory": "/home/sistemas3/logs",
    "backup_before_changes": true,
    "transaction_mode": "per_model",
    "error_handling": "rollback_on_error",
    "logging_level": "INFO"
  }
}
```

---

## 🎯 REGLAS DE LIMPIEZA Y TRANSFORMACIÓN

### Regla 1: Eliminación de Gaps

**Objetivo:** Eliminar saltos en secuencia de IDs

**SQL:**
```sql
WITH numbered AS (
    SELECT id,
           ROW_NUMBER() OVER (ORDER BY id) as new_id
    FROM {table_name}
)
UPDATE {table_name} t
SET id = n.new_id
FROM numbered n
WHERE t.id = n.id;
```

### Regla 2: Normalización de Nombres

**Estándar General:**
```
Formato: {nombre_modelo}_{id}
Ejemplo: res_partner_8590

Transformación:
- res.partner ID 5017 → res_partner_8590
- product.template ID 1145 → product_template_1000
```

**Excepción - account.account:**
```
Formato: {codigo_cuenta} - {nombre}
Ejemplo: 1.1.01.001 - Caja General

NO aplicar reemplazo de puntos
Usar código contable como identificador
```

### Regla 3: Eliminación por Módulos

**Wizards:**
```sql
DELETE FROM {table_name}
WHERE {table_name} LIKE '%wizard%';
```

**ir.model.data:**
```sql
DELETE FROM ir_model_data
WHERE module IN ('__export__', 'marin')
  AND model != 'ir.module.module';
```

### Regla 4: Resecuenciación de IDs

**Proceso:**
1. Obtener IDs actuales ordenados
2. Crear mapeo: old_id → new_id
3. Deshabilitar triggers
4. Actualizar IDs primarios
5. Actualizar foreign keys
6. Habilitar triggers
7. Commit transacción

**Ejemplo:**
```
OLD IDs:  5017, 5018, 5020, 5025
NEW IDs:  8590, 8591, 8592, 8593
```

---

## ⚠️ MANEJO DE ERRORES Y ROLLBACK

```
╔══════════════════════════════════════════════════════════════════════╗
║                    DIAGRAMA DE MANEJO DE ERRORES                     ║
╚══════════════════════════════════════════════════════════════════════╝

                    ┌────────────────────────┐
                    │ Inicio Procesamiento   │
                    │ de Modelo              │
                    └──────────┬─────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ BEGIN TRANSACTION      │
                    └──────────┬─────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ try:                   │
                    │   Ejecutar Limpieza    │
                    │   Ejecutar Transform.  │
                    │   Validar Integridad   │
                    └──────────┬─────────────┘
                               │
                          ┌────┴────┐
                          │         │
                      ÉXITO      ERROR
                          │         │
                          ▼         ▼
              ┌────────────────┐  ┌──────────────────────┐
              │ COMMIT         │  │ except Exception:    │
              │                │  │   Log Error          │
              │ Registrar      │  │   ROLLBACK           │
              │ Estadísticas   │  │                      │
              └────────┬───────┘  │ Registrar en Errors  │
                       │          └──────────┬───────────┘
                       │                     │
                       ▼                     ▼
              ┌────────────────┐  ┌──────────────────────┐
              │ Status:        │  │ Status:              │
              │ SUCCESS        │  │ FAILED               │
              └────────┬───────┘  └──────────┬───────────┘
                       │                     │
                       └──────────┬──────────┘
                                  │
                                  ▼
                       ┌────────────────────┐
                       │ Continuar con      │
                       │ Siguiente Modelo   │
                       └────────────────────┘

ESTRATEGIAS DE RECUPERACIÓN:

1. Error de Conexión:
   → Reintentar 3 veces con backoff exponencial
   → Si falla: ABORT completo

2. Error de FK Constraint:
   → ROLLBACK transacción modelo actual
   → Registrar FK rota en warnings
   → Continuar con siguiente modelo

3. Error de Permisos:
   → Verificar rol de usuario
   → Sugerir GRANT necesario
   → ABORT si no se puede resolver

4. Error de Espacio en Disco:
   → Limpiar archivos temporales
   → Compactar tablas
   → Reintentar operación
```

---

## 📊 ARCHIVO DE ESTADÍSTICAS

### Estructura del JSON

```json
{
  "execution_info": {
    "timestamp": "2025-10-03T14:30:00",
    "script_version": "3.0",
    "database": "odoo_production",
    "total_duration_seconds": 1847.3,
    "host": "localhost",
    "user": "odoo_admin"
  },

  "validation_checks": {
    "db_connection": "OK",
    "output_directory": "CREATED",
    "permissions": "OK",
    "tables_verified": "OK",
    "json_config_loaded": "OK",
    "models_count": 30
  },

  "models_processed": {
    "res.partner": {
      "status": "SUCCESS",
      "table_name": "res_partner",
      "records_before": 3761,
      "records_after": 3450,
      "records_deleted": 311,
      "gaps_eliminated": 45,
      "ids_resequenced": true,
      "new_id_range": "8590-12039",
      "foreign_keys_updated": 1247,
      "duration_seconds": 12.5,
      "changes": [
        "Deleted 311 records from modules: __export__, marin",
        "Eliminated 45 gaps in ID sequence",
        "Normalized ID names (replaced dots with underscores)",
        "Resequenced IDs starting from 8590",
        "Updated 1247 foreign key references"
      ]
    },

    "account.account": {
      "status": "SUCCESS",
      "table_name": "account_account",
      "records_before": 856,
      "records_after": 856,
      "records_deleted": 0,
      "gaps_eliminated": 0,
      "special_rule_applied": "use_account_code_as_id",
      "ids_resequenced": false,
      "duration_seconds": 8.2,
      "changes": [
        "Applied special naming rule: account code as ID",
        "Preserved account code format (no dot replacement)",
        "No gaps detected in sequence"
      ]
    }
  },

  "summary": {
    "total_models": 30,
    "successful": 28,
    "failed": 2,
    "total_records_processed": 18945,
    "total_records_deleted": 5234,
    "total_gaps_eliminated": 203,
    "total_foreign_keys_updated": 3456,
    "total_duration_seconds": 1847.3
  },

  "errors": [
    {
      "model": "stock.move",
      "error": "Foreign key constraint violation on field 'location_id'",
      "details": "Cannot update ID due to pending references in stock_quant",
      "timestamp": "2025-10-03T14:35:22",
      "sql_state": "23503"
    }
  ],

  "warnings": [
    {
      "model": "product.template",
      "warning": "Large gap detected in ID sequence",
      "details": "Gap of 523 records between IDs 1500-2023",
      "recommendation": "Review data integrity and consider manual cleanup"
    }
  ]
}
```

---

## 🚀 IMPLEMENTACIÓN Y EJECUCIÓN

### Estructura de Directorios

```
/home/sistemas3/
│
├── main_processor.py              # Script principal
│
├── config/
│   ├── db_credentials.json       # Credenciales (chmod 600)
│   └── models_processing_config.json
│
├── output/
│   └── statistics/
│       ├── processing_report_20251003_143000.json
│       └── processing_summary_20251003_143000.csv
│
├── logs/
│   └── execution_20251003_143000.log
│
└── instancias/lib/Proyecto R/
    └── acciones_servidor 18.2/   # Referencia
```

### Pasos de Ejecución

```bash
# 1. Crear estructura de directorios
mkdir -p config output/statistics logs

# 2. Configurar credenciales
cat > config/db_credentials.json <<EOF
{
  "host": "localhost",
  "port": 5432,
  "database": "odoo_production",
  "user": "odoo_admin",
  "password": "your_password"
}
EOF

chmod 600 config/db_credentials.json

# 3. Crear JSON de configuración
# (Basado en los 30+ scripts de acciones_servidor 18.2/)
nano config/models_processing_config.json

# 4. Instalar dependencias
pip3 install psycopg2-binary

# 5. Ejecutar script
python3 main_processor.py

# 6. Revisar resultados
cat output/statistics/processing_report_*.json | jq '.summary'
cat logs/execution_*.log | grep ERROR
```

### Comandos de Validación

```bash
# Verificar conexión a BDD
psql -h localhost -U odoo_admin -d odoo_production -c "SELECT version();"

# Verificar tablas existen
psql -h localhost -U odoo_admin -d odoo_production -c "\dt res_partner"

# Verificar permisos
touch output/statistics/.test && rm output/statistics/.test

# Validar JSON
python3 -m json.tool config/models_processing_config.json > /dev/null
```

### Modo Dry-Run (Simulación)

Agregar al script principal:

```python
def main():
    # ... código existente ...

    # Verificar modo dry-run
    dry_run = '--dry-run' in sys.argv

    if dry_run:
        print("\n⚠️  MODO DRY-RUN: No se realizarán cambios reales\n")
        conn.set_session(readonly=True)

    # ... resto del código ...
```

Ejecutar:
```bash
python3 main_processor.py --dry-run
```

---

## 📝 RESUMEN EJECUTIVO

### Flujo Simplificado

```
1. Script carga credenciales seguras
   ↓
2. Conecta a PostgreSQL
   ↓
3. Carga JSON con configuración de 30+ modelos
   ↓
4. Valida entorno (conexión, permisos, directorios)
   ↓
5. Itera cada modelo según execution_order
   ↓
6. Para cada modelo:
   - Cuenta registros
   - Elimina módulos específicos
   - Elimina gaps en IDs
   - Normaliza nombres (excepto account.account)
   - Resecuencia IDs
   - Actualiza foreign keys
   - Valida integridad
   ↓
7. Genera estadísticas detalladas (JSON + CSV)
   ↓
8. Cierra conexión
```

### Ventajas del Enfoque v3

✅ **Un solo script Python** - No múltiples archivos
✅ **Modificación directa BDD** - Sin CSVs intermedios
✅ **Credenciales seguras** - Archivo separado con permisos restrictivos
✅ **JSON configurable** - Basado en lógica de acciones_servidor
✅ **Transaccional** - Rollback automático por modelo
✅ **Estadísticas completas** - JSON detallado + CSV resumido
✅ **Manejo de errores robusto** - Logs detallados y recuperación
✅ **Reglas especializadas** - account.account con lógica propia

---

**FIN DEL DOCUMENTO**
