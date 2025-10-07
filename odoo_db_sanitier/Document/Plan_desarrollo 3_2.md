# Plan de Desarrollo v3.2: Sistema de Limpieza y Resecuenciación de Base de Datos Odoo

**Fecha:** 2025-10-03
**Versión:** 3.2
**Enfoque:** Procesamiento directo a base de datos con arquitectura modular

---

## 📋 ÍNDICE

1. [Arquitectura del Sistema](#arquitectura-del-sistema)
2. [Estructura de Directorios](#estructura-de-directorios)
3. [Flujo Principal de Ejecución](#flujo-principal-de-ejecución)
4. [Componente: convertJSON.py](#componente-convertjsonpy)
5. [Componente: Run.py](#componente-runpy)
6. [Configuración JSON Generada](#configuración-json-generada)
7. [Reglas de Procesamiento](#reglas-de-procesamiento)
8. [Orden de Operaciones por Modelo](#orden-de-operaciones-por-modelo)
9. [Reglas de Seguridad](#reglas-de-seguridad)
10. [Manejo de Errores](#manejo-de-errores)
11. [Archivo de Estadísticas](#archivo-de-estadísticas)
12. [Implementación](#implementación)

---

## 🏗️ ARQUITECTURA DEL SISTEMA

```
╔══════════════════════════════════════════════════════════════════════╗
║                    ARQUITECTURA COMPLETA v3.2                        ║
╚══════════════════════════════════════════════════════════════════════╝

                           ┌─────────────────┐
                           │   INICIO        │
                           └────────┬────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────────┐
        │           FASE 1: PREPARACIÓN                     │
        │   ──────────────────────────────────────────      │
        │                                                   │
        │   config/db_credentials.json                      │
        │   └─► Credenciales de acceso a BDD               │
        │                                                   │
        │   utils/acciones_servidor/*.py                    │
        │   └─► 30+ archivos con lógica de negocio         │
        └───────────────────────┬───────────────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────────────┐
        │      FASE 2: CONVERSIÓN A JSON                    │
        │   ──────────────────────────────────────────      │
        │                                                   │
        │   convertJSON.py                                  │
        │   ────────────────                                │
        │                                                   │
        │   • Lee archivos .py de acciones_servidor        │
        │   • Identifica patrones:                          │
        │     - ALTER TABLE ... CASCADE                     │
        │     - DELETE FROM ... WHERE ...                   │
        │     - UPDATE ... SET ...                          │
        │     - Reglas de naming                            │
        │                                                   │
        │   • Extrae metadata:                              │
        │     - table_name                                  │
        │     - foreign_keys con CASCADE                    │
        │     - cleanup_rules                               │
        │     - naming_rules                                │
        │                                                   │
        │   Genera ▼                                        │
        │   models_config.json                              │
        └───────────────────────┬───────────────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────────────┐
        │        FASE 3: EJECUCIÓN PRINCIPAL                │
        │   ──────────────────────────────────────────      │
        │                                                   │
        │   Run.py                                          │
        │   ──────                                          │
        │                                                   │
        │   1. Cargar config/db_credentials.json           │
        │   2. Conectar a PostgreSQL                        │
        │   3. Cargar models_config.json                    │
        │   4. Validar entorno                              │
        │                                                   │
        │   5. FOR each modelo IN execution_order:          │
        │                                                   │
        │      a) Aplicar CASCADE constraints               │
        │      b) Resecuenciar IDs                          │
        │      c) Actualizar nombres                        │
        │      d) Eliminar gaps                             │
        │      e) DELETE con WHERE (seguro)                 │
        │                                                   │
        │   6. Generar estadísticas                         │
        │   7. Cerrar conexión                              │
        └───────────────────────┬───────────────────────────┘
                                │
                                ▼
        ┌───────────────────────────────────────────────────┐
        │           FASE 4: RESULTADOS                      │
        │   ──────────────────────────────────────────      │
        │                                                   │
        │   output/                                         │
        │   ├── processing_report.json                      │
        │   ├── processing_summary.csv                      │
        │   └── execution.log                               │
        └───────────────────────────────────────────────────┘
```

---

## 📁 ESTRUCTURA DE DIRECTORIOS

```
proyectoR/
│
├── config/
│   └── db_credentials.json          # Credenciales BDD (chmod 600)
│
├── utils/
│   └── acciones_servidor/
│       ├── account_account.py       # Reglas de account.account
│       ├── res_partner.py           # Reglas de res.partner
│       ├── product_template.py      # Reglas de product.*
│       ├── stock_warehouse.py       # Reglas de stock.*
│       ├── account_move.py
│       ├── account_journal.py
│       └── ... (30+ archivos .py)
│
├── convertJSON.py                   # Convierte .py → JSON
├── Run.py                           # Script principal de ejecución
│
├── models_config.json               # JSON generado (auto)
│
├── output/
│   ├── statistics/
│   │   ├── processing_report_YYYYMMDD_HHMMSS.json
│   │   └── processing_summary_YYYYMMDD_HHMMSS.csv
│   └── logs/
│       └── execution_YYYYMMDD_HHMMSS.log
│
└── README.md
```

### Detalle de Archivos

**config/db_credentials.json**
```json
{
  "host": "localhost",
  "port": 5432,
  "database": "odoo_production",
  "user": "odoo_admin",
  "password": "secure_password",
  "sslmode": "require"
}
```

**utils/acciones_servidor/\*.py**
- Contienen queries SQL de acciones de servidor
- Definen lógica de limpieza por modelo
- Incluyen CASCADE constraints
- Especifican reglas de DELETE con WHERE

---

## 🔄 FLUJO PRINCIPAL DE EJECUCIÓN

```
╔══════════════════════════════════════════════════════════════════════╗
║                  FLUJO COMPLETO DE EJECUCIÓN                         ║
╚══════════════════════════════════════════════════════════════════════╝

                            ┌─────────┐
                            │  START  │
                            └────┬────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ 1. CARGAR CREDENCIALES │
                    │    desde config/       │
                    └────────┬───────────────┘
                             │
                             ▼
                    ┌────────────────────────┐
                    │ 2. CONECTAR A BDD      │
                    │    PostgreSQL          │
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
          ┌─────────────────┐   ┌──────────┐
          │ 3. CARGAR JSON  │   │ EXIT(1)  │
          │ models_config   │   └──────────┘
          └────────┬────────┘
                   │
                   ▼
          ┌──────────────────────────┐
          │ 4. VALIDACIONES PREVIAS  │
          │                          │
          │ • Directorio salida      │
          │ • Permisos               │
          │ • Tablas existen         │
          └────────┬─────────────────┘
                   │
                   ▼
          ┌──────────────────────────┐
          │ 5. ITERACIÓN MODELOS     │
          │                          │
          │ FOR modelo IN order:     │
          └────────┬─────────────────┘
                   │
                   ▼
          ┌──────────────────────────────────────┐
          │ 6. PROCESAR MODELO                   │
          │    (Orden específico)                │
          │                                      │
          │ ┌──────────────────────────────────┐│
          │ │ PASO 1: CASCADE                  ││
          │ │ ─────────────────                ││
          │ │ ALTER TABLE ... CASCADE          ││
          │ │ Configurar FKs para propagación  ││
          │ └──────────────────────────────────┘│
          │                                      │
          │ ┌──────────────────────────────────┐│
          │ │ PASO 2: RESECUENCIAR IDs         ││
          │ │ ──────────────────────           ││
          │ │ • Crear mapeo old→new            ││
          │ │ • UPDATE tabla SET id = new      ││
          │ │ • CASCADE actualiza FKs auto     ││
          │ └──────────────────────────────────┘│
          │                                      │
          │ ┌──────────────────────────────────┐│
          │ │ PASO 3: ACTUALIZAR NOMBRES       ││
          │ │ ────────────────────────         ││
          │ │ • Aplicar naming standard        ││
          │ │ • Reemplazar . por _             ││
          │ │ • Excepción: account.account     ││
          │ └──────────────────────────────────┘│
          │                                      │
          │ ┌──────────────────────────────────┐│
          │ │ PASO 4: ELIMINAR GAPS            ││
          │ │ ───────────────────              ││
          │ │ • Detectar saltos en IDs         ││
          │ │ • Renumerar consecutivos         ││
          │ └──────────────────────────────────┘│
          │                                      │
          │ ┌──────────────────────────────────┐│
          │ │ PASO 5: DELETE SEGURO            ││
          │ │ ───────────────────              ││
          │ │ DELETE FROM tabla                ││
          │ │ WHERE condicion                  ││
          │ │ (SIEMPRE con WHERE)              ││
          │ └──────────────────────────────────┘│
          │                                      │
          └────────┬─────────────────────────────┘
                   │
                   ▼
          ┌──────────────────────────┐
          │ 7. REGISTRAR STATS       │
          │    por modelo            │
          └────────┬─────────────────┘
                   │
                   ▼
          ┌──────────────────────────┐
          │ 8. ¿Más modelos?         │
          └────────┬─────────────────┘
                   │
              ┌────┴────┐
              │         │
             SI        NO
              │         │
              │         ▼
              │    ┌─────────────────────┐
              │    │ 9. GENERAR REPORTES │
              │    │    • JSON           │
              │    │    • CSV            │
              │    │    • LOG            │
              │    └─────────┬───────────┘
              │              │
              │              ▼
              │         ┌─────────┐
              │         │   END   │
              │         └─────────┘
              │
              └──► (Siguiente modelo)
```

---

## 🔧 COMPONENTE: convertJSON.py

### Propósito
Transformar archivos Python de acciones de servidor en configuración JSON estructurada.

### Diagrama de Funcionamiento

```
╔══════════════════════════════════════════════════════════════════════╗
║                      convertJSON.py - FLUJO                          ║
╚══════════════════════════════════════════════════════════════════════╝

                    ┌────────────────────────┐
                    │ Escanear directorio    │
                    │ utils/acciones_servidor│
                    └──────────┬─────────────┘
                               │
                               ▼
                    ┌────────────────────────┐
                    │ FOR each archivo.py    │
                    └──────────┬─────────────┘
                               │
                               ▼
            ┌──────────────────────────────────────┐
            │ Parsear contenido Python             │
            │                                      │
            │ Buscar patrones:                     │
            │ ─────────────────                    │
            │                                      │
            │ 1. ALTER TABLE ... CASCADE           │
            │    → Extraer foreign_keys            │
            │                                      │
            │ 2. DELETE FROM ... WHERE ...         │
            │    → Extraer cleanup_rules           │
            │                                      │
            │ 3. UPDATE ... SET id = ...           │
            │    → Extraer resequence_rules        │
            │                                      │
            │ 4. CONCAT() o string manipulation    │
            │    → Extraer naming_rules            │
            └──────────────┬───────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────────────┐
            │ Construir objeto JSON por modelo:    │
            │                                      │
            │ {                                    │
            │   "model_name": "res.partner",       │
            │   "table_name": "res_partner",       │
            │   "foreign_keys": [...],             │
            │   "cascade_rules": [...],            │
            │   "cleanup_rules": {...},            │
            │   "naming_rules": {...},             │
            │   "resequence_rules": {...}          │
            │ }                                    │
            └──────────────┬───────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────────────┐
            │ Determinar execution_order           │
            │                                      │
            │ Basado en dependencias FK:           │
            │ • res.company (primero)              │
            │ • res.partner                        │
            │ • product.category                   │
            │ • ...                                │
            │ • wizards (último)                   │
            └──────────────┬───────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────────────┐
            │ Generar models_config.json           │
            │                                      │
            │ {                                    │
            │   "execution_order": [...],          │
            │   "models": {                        │
            │     "res.partner": {...},            │
            │     "account.account": {...},        │
            │     ...                              │
            │   },                                 │
            │   "global_settings": {...}           │
            │ }                                    │
            └──────────────┬───────────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ Escribir JSON│
                    │ a disco      │
                    └──────────────┘
```

### Código de convertJSON.py

```python
#!/usr/bin/env python3
"""
convertJSON.py
Convierte archivos .py de acciones_servidor a configuración JSON
"""

import os
import re
import json
from pathlib import Path

def parse_python_file(file_path):
    """Extrae patrones SQL y reglas de un archivo .py"""

    with open(file_path, 'r') as f:
        content = f.read()

    model_config = {
        'foreign_keys': [],
        'cascade_rules': [],
        'cleanup_rules': {},
        'naming_rules': {},
        'resequence_rules': {}
    }

    # 1. Extraer CASCADE constraints
    cascade_pattern = r'ALTER TABLE (\w+) ADD CONSTRAINT.*?ON DELETE (CASCADE|SET NULL|RESTRICT)'
    cascades = re.findall(cascade_pattern, content, re.IGNORECASE)

    for table, action in cascades:
        model_config['cascade_rules'].append({
            'table': table,
            'on_delete': action
        })

    # 2. Extraer DELETE con WHERE
    delete_pattern = r'DELETE FROM (\w+)\s+WHERE (.+?);'
    deletes = re.findall(delete_pattern, content, re.IGNORECASE | re.DOTALL)

    for table, where_clause in deletes:
        if 'delete_conditions' not in model_config['cleanup_rules']:
            model_config['cleanup_rules']['delete_conditions'] = []

        model_config['cleanup_rules']['delete_conditions'].append({
            'table': table,
            'where': where_clause.strip()
        })

    # 3. Extraer reglas de resecuenciación
    reseq_pattern = r'UPDATE (\w+) SET id = (\d+)'
    reseqs = re.findall(reseq_pattern, content, re.IGNORECASE)

    if reseqs:
        model_config['resequence_rules']['start_id'] = int(reseqs[0][1])

    # 4. Extraer reglas de naming
    naming_pattern = r"CONCAT\(['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\)"
    namings = re.findall(naming_pattern, content)

    if namings:
        model_config['naming_rules']['pattern'] = namings[0]
        model_config['naming_rules']['replace_dots'] = True

    return model_config

def determine_execution_order(models_data):
    """Determina orden de ejecución basado en dependencias FK"""

    # Orden predefinido basado en dependencias conocidas
    base_order = [
        'res.company',
        'res.partner',
        'product.category',
        'product.template',
        'product.product',
        'account.account',
        'account.journal',
        'account.tax',
        'account.move',
        'account.move.line',
        'stock.location',
        'stock.warehouse',
        'stock.picking.type',
        'stock.picking',
        'stock.move',
        'wizard.models'
    ]

    # Filtrar solo modelos que existen en models_data
    execution_order = [m for m in base_order if m in models_data]

    return execution_order

def convert_to_json():
    """Función principal de conversión"""

    acciones_dir = Path('utils/acciones_servidor')

    if not acciones_dir.exists():
        print(f"❌ Directorio no encontrado: {acciones_dir}")
        return

    models_data = {}

    # Procesar cada archivo .py
    for py_file in acciones_dir.glob('*.py'):
        print(f"📄 Procesando: {py_file.name}")

        # Extraer nombre del modelo del nombre del archivo
        model_name = py_file.stem.replace('_', '.')
        table_name = py_file.stem

        # Parsear archivo
        config = parse_python_file(py_file)

        # Construir configuración del modelo
        models_data[model_name] = {
            'table_name': table_name,
            **config
        }

        # Regla especial para account.account
        if model_name == 'account.account':
            models_data[model_name]['naming_rules']['use_account_code'] = True
            models_data[model_name]['naming_rules']['replace_dots'] = True  # Sí reemplaza puntos

    # Determinar orden de ejecución
    execution_order = determine_execution_order(models_data)

    # Construir JSON final
    final_config = {
        'execution_order': execution_order,
        'models': models_data,
        'global_settings': {
            'output_directory': 'output/statistics',
            'log_directory': 'output/logs',
            'require_where_in_delete': True,
            'use_cascade': True,
            'disable_triggers': False
        }
    }

    # Escribir JSON
    output_file = 'models_config.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_config, f, indent=2, ensure_ascii=False)

    print(f"\n✅ JSON generado: {output_file}")
    print(f"   Modelos procesados: {len(models_data)}")
    print(f"   Orden de ejecución: {len(execution_order)} modelos")

if __name__ == '__main__':
    convert_to_json()
```

---

## ⚙️ COMPONENTE: Run.py

### Propósito
Script principal que ejecuta el procesamiento de la base de datos.

### Diagrama de Funcionamiento

```
╔══════════════════════════════════════════════════════════════════════╗
║                        Run.py - FLUJO DETALLADO                      ║
╚══════════════════════════════════════════════════════════════════════╝

                    ┌────────────────────────┐
                    │ main()                 │
                    └──────────┬─────────────┘
                               │
                               ▼
            ┌──────────────────────────────────────┐
            │ 1. load_credentials()                │
            │    config/db_credentials.json        │
            └──────────────┬───────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────────────┐
            │ 2. connect_database(credentials)     │
            │    psycopg2.connect()                │
            └──────────────┬───────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────────────┐
            │ 3. load_models_config()              │
            │    models_config.json                │
            └──────────────┬───────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────────────┐
            │ 4. validate_environment()            │
            └──────────────┬───────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────────────┐
            │ 5. FOR modelo IN execution_order:    │
            │                                      │
            │    process_model(modelo, config)     │
            └──────────────┬───────────────────────┘
                           │
                           ▼
    ┌──────────────────────────────────────────────────────┐
    │         process_model() - ORDEN ESPECÍFICO           │
    ├──────────────────────────────────────────────────────┤
    │                                                      │
    │  ┌────────────────────────────────────────────────┐ │
    │  │ PASO 1: apply_cascade()                        │ │
    │  │ ─────────────────────                          │ │
    │  │                                                │ │
    │  │ FOR each FK in cascade_rules:                 │ │
    │  │   ALTER TABLE {table}                         │ │
    │  │   DROP CONSTRAINT {constraint};               │ │
    │  │                                                │ │
    │  │   ALTER TABLE {table}                         │ │
    │  │   ADD CONSTRAINT {constraint}                 │ │
    │  │   FOREIGN KEY (col)                           │ │
    │  │   REFERENCES {ref_table}(id)                  │ │
    │  │   ON DELETE CASCADE;                          │ │
    │  └────────────────────────────────────────────────┘ │
    │                                                      │
    │  ┌────────────────────────────────────────────────┐ │
    │  │ PASO 2: resequence_ids()                       │ │
    │  │ ──────────────────────                         │ │
    │  │                                                │ │
    │  │ 1. SELECT id FROM {table} ORDER BY id          │ │
    │  │                                                │ │
    │  │ 2. Crear mapeo: old_id → new_id               │ │
    │  │    new_id = start_id + index                  │ │
    │  │                                                │ │
    │  │ 3. FOR old, new IN mapping:                   │ │
    │  │      UPDATE {table}                           │ │
    │  │      SET id = {new}                           │ │
    │  │      WHERE id = {old};                        │ │
    │  │                                                │ │
    │  │    ✅ CASCADE actualiza FKs automáticamente    │ │
    │  └────────────────────────────────────────────────┘ │
    │                                                      │
    │  ┌────────────────────────────────────────────────┐ │
    │  │ PASO 3: update_names()                         │ │
    │  │ ────────────────────                           │ │
    │  │                                                │ │
    │  │ IF modelo != 'account.account':               │ │
    │  │   UPDATE {table}                              │ │
    │  │   SET name = REPLACE(                         │ │
    │  │     CONCAT('{model}_', id),                   │ │
    │  │     '.',                                      │ │
    │  │     '_'                                       │ │
    │  │   );                                          │ │
    │  │                                                │ │
    │  │ ELSE:  # account.account                      │ │
    │  │   UPDATE account_account                      │ │
    │  │   SET code = REPLACE(code, '.', '_')          │ │
    │  │   WHERE code IS NOT NULL;                     │ │
    │  └────────────────────────────────────────────────┘ │
    │                                                      │
    │  ┌────────────────────────────────────────────────┐ │
    │  │ PASO 4: eliminate_gaps()                       │ │
    │  │ ──────────────────────                         │ │
    │  │                                                │ │
    │  │ WITH numbered AS (                            │ │
    │  │   SELECT id,                                  │ │
    │  │   ROW_NUMBER() OVER (ORDER BY id) as new_id   │ │
    │  │   FROM {table}                                │ │
    │  │ )                                             │ │
    │  │ UPDATE {table} t                              │ │
    │  │ SET id = n.new_id                             │ │
    │  │ FROM numbered n                               │ │
    │  │ WHERE t.id = n.id;                            │ │
    │  └────────────────────────────────────────────────┘ │
    │                                                      │
    │  ┌────────────────────────────────────────────────┐ │
    │  │ PASO 5: safe_delete()                          │ │
    │  │ ───────────────────                            │ │
    │  │                                                │ │
    │  │ FOR each condition IN delete_conditions:      │ │
    │  │                                                │ │
    │  │   IF NOT has_where_clause(condition):         │ │
    │  │     RAISE SecurityError                       │ │
    │  │                                                │ │
    │  │   DELETE FROM {table}                         │ │
    │  │   WHERE {condition};                          │ │
    │  └────────────────────────────────────────────────┘ │
    │                                                      │
    └──────────────────────────────────────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────────────┐
            │ 6. collect_statistics()              │
            └──────────────┬───────────────────────┘
                           │
                           ▼
            ┌──────────────────────────────────────┐
            │ 7. generate_report()                 │
            │    • JSON                            │
            │    • CSV                             │
            │    • LOG                             │
            └──────────────────────────────────────┘
```

### Código de Run.py

```python
#!/usr/bin/env python3
"""
Run.py
Script principal de procesamiento de base de datos
"""

import psycopg2
import json
import os
import sys
from datetime import datetime
import logging

# ══════════════════════════════════════════════════════════════
#                    CARGA DE CREDENCIALES
# ══════════════════════════════════════════════════════════════

def load_credentials():
    """Carga credenciales desde config/db_credentials.json"""
    cred_file = 'config/db_credentials.json'

    if not os.path.exists(cred_file):
        raise FileNotFoundError(f"Credenciales no encontradas: {cred_file}")

    with open(cred_file, 'r') as f:
        return json.load(f)

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

        logging.info(f"✓ Conectado a: {credentials['database']}")
        return conn

    except psycopg2.Error as e:
        logging.error(f"✗ Error de conexión: {e}")
        raise

# ══════════════════════════════════════════════════════════════
#                    CARGA DE CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════

def load_models_config():
    """Carga configuración de modelos desde JSON"""
    config_file = 'models_config.json'

    if not os.path.exists(config_file):
        raise FileNotFoundError(f"Configuración no encontrada: {config_file}")

    with open(config_file, 'r') as f:
        return json.load(f)

# ══════════════════════════════════════════════════════════════
#                    PASO 1: CASCADE
# ══════════════════════════════════════════════════════════════

def apply_cascade(conn, model_config):
    """Aplica CASCADE a foreign keys"""
    cur = conn.cursor()

    cascade_rules = model_config.get('cascade_rules', [])

    for rule in cascade_rules:
        table = rule['table']
        on_delete = rule['on_delete']

        # Obtener constraints existentes
        cur.execute(f"""
            SELECT constraint_name, table_name
            FROM information_schema.table_constraints
            WHERE table_name = '{table}'
            AND constraint_type = 'FOREIGN KEY';
        """)

        constraints = cur.fetchall()

        for constraint_name, table_name in constraints:
            # Drop constraint existente
            cur.execute(f"""
                ALTER TABLE {table_name}
                DROP CONSTRAINT {constraint_name};
            """)

            # Re-crear con CASCADE
            cur.execute(f"""
                ALTER TABLE {table_name}
                ADD CONSTRAINT {constraint_name}
                FOREIGN KEY ...
                ON DELETE {on_delete}
                ON UPDATE CASCADE;
            """)

    conn.commit()
    cur.close()

    logging.info(f"  ✓ CASCADE aplicado: {len(cascade_rules)} reglas")

# ══════════════════════════════════════════════════════════════
#                    PASO 2: RESECUENCIAR IDs
# ══════════════════════════════════════════════════════════════

def resequence_ids(conn, table_name, start_id):
    """Resecuencia IDs de una tabla (CASCADE actualiza FKs automáticamente)"""
    cur = conn.cursor()

    # 1. Obtener IDs actuales
    cur.execute(f"SELECT id FROM {table_name} ORDER BY id;")
    records = cur.fetchall()

    # 2. Crear mapeo
    id_mapping = {}
    new_id = start_id

    for (old_id,) in records:
        id_mapping[old_id] = new_id
        new_id += 1

    # 3. Actualizar IDs
    # CASCADE (ON UPDATE CASCADE) actualiza automáticamente los foreign keys
    for old_id, new_id in id_mapping.items():
        cur.execute(f"""
            UPDATE {table_name}
            SET id = {new_id}
            WHERE id = {old_id};
        """)

    conn.commit()
    cur.close()

    logging.info(f"  ✓ Resecuenciado: {len(id_mapping)} registros (FKs actualizados por CASCADE)")
    return id_mapping

# ══════════════════════════════════════════════════════════════
#                    PASO 3: ACTUALIZAR NOMBRES
# ══════════════════════════════════════════════════════════════

def update_names(conn, model_name, table_name):
    """Actualiza nombres según reglas"""
    cur = conn.cursor()

    if model_name == 'account.account':
        # Regla especial: usar código contable con _ en lugar de .
        cur.execute(f"""
            UPDATE {table_name}
            SET code = REPLACE(code, '.', '_')
            WHERE code IS NOT NULL;
        """)
    else:
        # Regla estándar: modelo_id con . → _
        model_clean = model_name.replace('.', '_')

        cur.execute(f"""
            UPDATE {table_name}
            SET name = REPLACE(
                CONCAT('{model_clean}_', id),
                '.',
                '_'
            )
            WHERE name IS NOT NULL;
        """)

    conn.commit()
    cur.close()

    logging.info(f"  ✓ Nombres actualizados")

# ══════════════════════════════════════════════════════════════
#                    PASO 4: ELIMINAR GAPS
# ══════════════════════════════════════════════════════════════

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

    logging.info(f"  ✓ Gaps eliminados: {gaps_count}")
    return gaps_count

# ══════════════════════════════════════════════════════════════
#                    PASO 5: DELETE SEGURO
# ══════════════════════════════════════════════════════════════

def safe_delete(conn, table_name, delete_conditions):
    """Ejecuta DELETE con validación de WHERE"""
    cur = conn.cursor()

    deleted_total = 0

    for condition in delete_conditions:
        where_clause = condition['where']

        # SEGURIDAD: Validar que tenga WHERE
        if not where_clause or where_clause.strip() == '':
            raise SecurityError(f"DELETE sin WHERE no permitido en {table_name}")

        # Ejecutar DELETE seguro
        query = f"DELETE FROM {table_name} WHERE {where_clause};"

        cur.execute(query)
        deleted_total += cur.rowcount

        logging.info(f"    DELETE: {cur.rowcount} registros ({where_clause[:50]}...)")

    conn.commit()
    cur.close()

    return deleted_total

# ══════════════════════════════════════════════════════════════
#                    PROCESAMIENTO POR MODELO
# ══════════════════════════════════════════════════════════════

def process_model(conn, model_name, model_config):
    """Procesa un modelo con orden específico"""

    table_name = model_config['table_name']

    logging.info(f"\n▶ Procesando: {model_name}")

    result = {
        'status': 'PROCESSING',
        'records_before': 0,
        'records_after': 0,
        'changes': []
    }

    # Contar registros iniciales
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table_name};")
    result['records_before'] = cur.fetchone()[0]
    cur.close()

    try:
        # PASO 1: CASCADE
        if 'cascade_rules' in model_config:
            apply_cascade(conn, model_config)
            result['changes'].append("CASCADE aplicado")

        # PASO 2: RESECUENCIAR IDs
        if 'resequence_rules' in model_config:
            start_id = model_config['resequence_rules'].get('start_id', 1000)
            id_mapping = resequence_ids(conn, table_name, start_id)
            result['changes'].append(f"IDs resecuenciados desde {start_id}")

        # PASO 3: ACTUALIZAR NOMBRES
        if 'naming_rules' in model_config:
            update_names(conn, model_name, table_name)
            result['changes'].append("Nombres actualizados")

        # PASO 4: ELIMINAR GAPS
        gaps = eliminate_gaps(conn, table_name)
        result['changes'].append(f"{gaps} gaps eliminados")

        # PASO 5: DELETE SEGURO
        if 'cleanup_rules' in model_config:
            conditions = model_config['cleanup_rules'].get('delete_conditions', [])
            deleted = safe_delete(conn, table_name, conditions)
            result['changes'].append(f"{deleted} registros eliminados")

        # Contar registros finales
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        result['records_after'] = cur.fetchone()[0]
        cur.close()

        result['status'] = 'SUCCESS'

        logging.info(f"  ✓ Completado: {result['records_after']} registros")

    except Exception as e:
        result['status'] = 'FAILED'
        result['error'] = str(e)
        logging.error(f"  ✗ Error: {e}")
        conn.rollback()

    return result

# ══════════════════════════════════════════════════════════════
#                    GENERACIÓN DE REPORTES
# ══════════════════════════════════════════════════════════════

def generate_report(stats):
    """Genera archivos de reporte"""

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # JSON detallado
    json_file = f'output/statistics/processing_report_{timestamp}.json'
    os.makedirs(os.path.dirname(json_file), exist_ok=True)

    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    # CSV resumido
    csv_file = f'output/statistics/processing_summary_{timestamp}.csv'

    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("model,records_before,records_after,status\n")

        for model, data in stats['models_processed'].items():
            f.write(f"{model},{data['records_before']},{data['records_after']},{data['status']}\n")

    logging.info(f"\n📊 Reportes generados:")
    logging.info(f"   JSON: {json_file}")
    logging.info(f"   CSV:  {csv_file}")

# ══════════════════════════════════════════════════════════════
#                    FUNCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════

def main():
    """Función principal"""

    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Sistema de Limpieza y Resecuenciación BDD Odoo         ║")
    print("║  Versión 3.2                                             ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    try:
        # 1. Cargar credenciales PRIMERO
        logging.info("📋 Cargando credenciales...")
        credentials = load_credentials()

        # 2. Conectar a BDD
        logging.info("🔌 Conectando a base de datos...")
        conn = connect_database(credentials)

        # 3. Cargar configuración de modelos
        logging.info("📄 Cargando configuración de modelos...")
        config = load_models_config()

        # 4. Procesar modelos
        stats = {
            'execution_info': {
                'timestamp': datetime.now().isoformat(),
                'database': credentials['database']
            },
            'models_processed': {}
        }

        for model_name in config['execution_order']:
            model_config = config['models'][model_name]
            result = process_model(conn, model_name, model_config)
            stats['models_processed'][model_name] = result

        # 5. Generar reportes
        generate_report(stats)

        # 6. Cerrar conexión
        conn.close()

        print("\n✅ Proceso completado exitosamente")

    except Exception as e:
        logging.error(f"\n❌ Error fatal: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

---

## 📋 CONFIGURACIÓN JSON GENERADA

### Estructura de models_config.json

```json
{
  "execution_order": [
    "res.company",
    "res.partner",
    "product.category",
    "product.template",
    "account.account",
    "account.move",
    "stock.warehouse",
    "wizard.models"
  ],

  "models": {
    "res.partner": {
      "table_name": "res_partner",

      "cascade_rules": [
        {
          "table": "res_partner",
          "on_delete": "CASCADE"
        }
      ],

      "resequence_rules": {
        "start_id": 8590
      },

      "naming_rules": {
        "pattern": "{model}_{id}",
        "replace_dots": true
      },

      "cleanup_rules": {
        "delete_conditions": [
          {
            "table": "res_partner",
            "where": "id IN (SELECT res_id FROM ir_model_data WHERE module IN ('__export__', 'marin'))"
          }
        ]
      }
    },

    "account.account": {
      "table_name": "account_account",

      "cascade_rules": [
        {
          "table": "account_account",
          "on_delete": "RESTRICT"
        }
      ],

      "naming_rules": {
        "use_account_code": true,
        "replace_dots": true
      },

      "cleanup_rules": {
        "delete_conditions": [
          {
            "table": "account_account",
            "where": "company_id NOT IN (SELECT id FROM res_company)"
          }
        ]
      }
    }
  },

  "global_settings": {
    "output_directory": "output/statistics",
    "log_directory": "output/logs",
    "require_where_in_delete": true,
    "use_cascade": true,
    "disable_triggers": false
  }
}
```

---

## 🎯 REGLAS DE PROCESAMIENTO

### Regla 1: Nombres (Todos los modelos)

**Estándar General:**
- Formato: `{modelo_nombre}_{id}`
- **SIEMPRE** reemplazar `.` por `_`
- Ejemplo: `res.partner` → `res_partner_8590`

**Excepción account.account:**
- NO usar ID en el nombre
- Usar código contable
- **SÍ** reemplazar `.` por `_` en el código
- Ejemplo: `1.1.01.001` → `1_1_01_001`

### Regla 2: Orden de Operaciones

**Secuencia OBLIGATORIA:**
1. **CASCADE** - Configurar foreign keys con ON UPDATE CASCADE
2. **Resecuenciar IDs** - Cambiar IDs (CASCADE actualiza FKs automáticamente)
3. **Actualizar nombres** - Después de tener IDs nuevos
4. **Eliminar gaps** - Compactar secuencia (CASCADE actualiza FKs)
5. **DELETE seguro** - Limpieza final con WHERE

**⚠️ IMPORTANTE:** Este orden evita errores de referencia. CASCADE maneja automáticamente la actualización de foreign keys.

### Regla 3: Eliminación de Gaps

**ANTES de eliminar gaps:**
- Aplicar CASCADE en foreign keys (ON UPDATE CASCADE)
- Asegurar que las referencias se propaguen automáticamente

**Proceso:**
```sql
-- Con CASCADE (ON UPDATE CASCADE) ya aplicado
-- Los foreign keys se actualizan automáticamente
WITH numbered AS (
    SELECT id,
           ROW_NUMBER() OVER (ORDER BY id) as new_id
    FROM {table_name}
)
UPDATE {table_name} t
SET id = n.new_id
FROM numbered n
WHERE t.id = n.id;

-- ✅ PostgreSQL actualiza automáticamente todas las tablas
-- que referencian esta tabla vía ON UPDATE CASCADE
```

---

## 🔒 REGLAS DE SEGURIDAD

### 1. DELETE siempre con WHERE

**❌ PROHIBIDO:**
```sql
DELETE FROM res_partner;
```

**✅ CORRECTO:**
```sql
DELETE FROM res_partner
WHERE id IN (
    SELECT res_id FROM ir_model_data
    WHERE module = '__export__'
);
```

**Validación en código:**
```python
def safe_delete(conn, table_name, delete_conditions):
    for condition in delete_conditions:
        where_clause = condition['where']

        # Validar WHERE obligatorio
        if not where_clause or where_clause.strip() == '':
            raise SecurityError(
                f"DELETE sin WHERE no permitido en {table_name}"
            )

        query = f"DELETE FROM {table_name} WHERE {where_clause};"
        cur.execute(query)
```

### 2. NO usar DISABLE TRIGGER

**❌ NO HACER:**
```sql
ALTER TABLE res_partner DISABLE TRIGGER ALL;
-- operaciones
ALTER TABLE res_partner ENABLE TRIGGER ALL;
```

**✅ USAR CASCADE:**
```sql
ALTER TABLE res_partner
ADD CONSTRAINT fk_parent
FOREIGN KEY (parent_id)
REFERENCES res_partner(id)
ON DELETE CASCADE
ON UPDATE CASCADE;
```

### 3. Transacciones por Modelo

Cada modelo se procesa en su propia transacción:
- `BEGIN` al inicio
- Procesar todas las operaciones
- `COMMIT` si todo OK
- `ROLLBACK` si hay error

---

## 📊 ORDEN DE OPERACIONES POR MODELO

```
╔══════════════════════════════════════════════════════════════════════╗
║              ORDEN ESPECÍFICO DE OPERACIONES                         ║
╚══════════════════════════════════════════════════════════════════════╝

Para cada modelo en execution_order:

┌─────────────────────────────────────────────────────────────────┐
│ MODELO: res.partner                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1️⃣ CASCADE (Primero - Configurar FKs)                          │
│    ────────────────────────────────────                         │
│    ALTER TABLE res_partner                                      │
│    DROP CONSTRAINT res_partner_parent_id_fkey;                  │
│                                                                 │
│    ALTER TABLE res_partner                                      │
│    ADD CONSTRAINT res_partner_parent_id_fkey                    │
│    FOREIGN KEY (parent_id)                                      │
│    REFERENCES res_partner(id)                                   │
│    ON DELETE CASCADE                                            │
│    ON UPDATE CASCADE;                                           │
│                                                                 │
│ 2️⃣ RESECUENCIAR IDs (Segundo - Cambiar IDs)                    │
│    ───────────────────────────────────────                      │
│    -- Crear mapeo: old → new                                    │
│    5017 → 8590                                                  │
│    5018 → 8591                                                  │
│    5020 → 8592                                                  │
│                                                                 │
│    UPDATE res_partner SET id = 8590 WHERE id = 5017;           │
│    UPDATE res_partner SET id = 8591 WHERE id = 5018;           │
│    UPDATE res_partner SET id = 8592 WHERE id = 5020;           │
│                                                                 │
│    ✅ FKs se actualizan AUTOMÁTICAMENTE por ON UPDATE CASCADE   │
│    No se requiere UPDATE manual de foreign keys                │
│                                                                 │
│ 3️⃣ ACTUALIZAR NOMBRES (Tercero - Después de IDs nuevos)        │
│    ─────────────────────────────────────────────                │
│    UPDATE res_partner                                           │
│    SET name = REPLACE(                                          │
│        CONCAT('res_partner_', id),                             │
│        '.',                                                     │
│        '_'                                                      │
│    );                                                           │
│                                                                 │
│    -- Resultado: res_partner_8590, res_partner_8591, ...       │
│                                                                 │
│ 4️⃣ ELIMINAR GAPS (Cuarto - Con CASCADE ya aplicado)            │
│    ──────────────────────────────────────────                   │
│    WITH numbered AS (                                           │
│        SELECT id,                                               │
│               ROW_NUMBER() OVER (ORDER BY id) as new_id         │
│        FROM res_partner                                         │
│    )                                                            │
│    UPDATE res_partner t                                         │
│    SET id = n.new_id                                            │
│    FROM numbered n                                              │
│    WHERE t.id = n.id;                                           │
│                                                                 │
│    ✅ FKs se actualizan AUTOMÁTICAMENTE por ON UPDATE CASCADE   │
│                                                                 │
│ 5️⃣ DELETE SEGURO (Quinto - Limpieza final)                     │
│    ────────────────────────────────────                         │
│    DELETE FROM res_partner                                      │
│    WHERE id IN (                                                │
│        SELECT res_id FROM ir_model_data                         │
│        WHERE module IN ('__export__', 'marin')                  │
│    );                                                           │
│                                                                 │
│    -- SIEMPRE con WHERE (seguridad)                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ MODELO: account.account (Caso especial)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1️⃣ CASCADE                                                      │
│    Similar al estándar                                          │
│                                                                 │
│ 2️⃣ RESECUENCIAR IDs                                            │
│    Similar al estándar                                          │
│                                                                 │
│ 3️⃣ ACTUALIZAR NOMBRES (DIFERENTE)                              │
│    ─────────────────────────────                                │
│    UPDATE account_account                                       │
│    SET code = REPLACE(code, '.', '_')                           │
│    WHERE code IS NOT NULL;                                      │
│                                                                 │
│    -- Usa código contable, NO id                               │
│    -- SÍ reemplaza puntos por guiones bajos                    │
│    -- Ejemplo: 1.1.01.001 → 1_1_01_001                         │
│                                                                 │
│ 4️⃣ ELIMINAR GAPS                                               │
│    Similar al estándar                                          │
│                                                                 │
│ 5️⃣ DELETE SEGURO                                               │
│    Similar al estándar                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## ⚠️ MANEJO DE ERRORES

```
╔══════════════════════════════════════════════════════════════════════╗
║                    ESTRATEGIA DE MANEJO DE ERRORES                   ║
╚══════════════════════════════════════════════════════════════════════╝

                    ┌────────────────────────┐
                    │ Iniciar Modelo         │
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
                    │   1. CASCADE           │
                    │   2. Resecuenciar      │
                    │   3. Nombres           │
                    │   4. Gaps              │
                    │   5. DELETE            │
                    └──────────┬─────────────┘
                               │
                          ┌────┴────┐
                          │         │
                      ÉXITO      ERROR
                          │         │
                          ▼         ▼
              ┌────────────────┐  ┌──────────────────┐
              │ COMMIT         │  │ except:          │
              │                │  │   ROLLBACK       │
              │ Status: OK     │  │   Log Error      │
              └────────────────┘  │   Status: FAIL   │
                                  └──────────────────┘
                                           │
                                           ▼
                                  ┌──────────────────┐
                                  │ Continuar con    │
                                  │ siguiente modelo │
                                  └──────────────────┘

TIPOS DE ERROR:

1. Error de CASCADE:
   → Verificar que FK existe
   → Validar que tabla referenciada existe
   → ROLLBACK y continuar

2. Error de Resecuenciación:
   → Verificar IDs únicos
   → Validar rango de IDs
   → ROLLBACK y continuar

3. Error de DELETE sin WHERE:
   → SecurityError inmediato
   → NO ejecutar DELETE
   → ROLLBACK y ABORT completo

4. Error de FK Constraint:
   → Verificar CASCADE aplicado
   → Revisar orden de ejecución
   → ROLLBACK y continuar
```

---

## 📊 ARCHIVO DE ESTADÍSTICAS

### JSON: processing_report_{timestamp}.json

```json
{
  "execution_info": {
    "timestamp": "2025-10-03T15:30:00",
    "database": "odoo_production",
    "script_version": "3.2",
    "duration_seconds": 245.7
  },

  "models_processed": {
    "res.partner": {
      "status": "SUCCESS",
      "records_before": 3761,
      "records_after": 3450,
      "changes": [
        "CASCADE aplicado",
        "IDs resecuenciados desde 8590",
        "Nombres actualizados",
        "45 gaps eliminados",
        "311 registros eliminados"
      ],
      "duration_seconds": 12.3
    },

    "account.account": {
      "status": "SUCCESS",
      "records_before": 856,
      "records_after": 856,
      "changes": [
        "CASCADE aplicado",
        "Nombres actualizados (código contable con _)",
        "0 gaps eliminados",
        "0 registros eliminados"
      ],
      "duration_seconds": 5.1
    }
  },

  "summary": {
    "total_models": 30,
    "successful": 28,
    "failed": 2,
    "total_duration_seconds": 245.7
  },

  "errors": [
    {
      "model": "stock.move",
      "error": "FK constraint violation",
      "timestamp": "2025-10-03T15:32:15"
    }
  ]
}
```

### CSV: processing_summary_{timestamp}.csv

```csv
model,records_before,records_after,status
res.partner,3761,3450,SUCCESS
account.account,856,856,SUCCESS
product.template,900,850,SUCCESS
stock.move,5234,0,FAILED
```

---

## 🚀 IMPLEMENTACIÓN

### Paso 1: Estructura Inicial

```bash
# Crear estructura de directorios
mkdir -p proyectoR/{config,utils/acciones_servidor,output/{statistics,logs}}

# Copiar archivos de acciones de servidor
cp /home/sistemas3/instancias/lib/Proyecto\ R/acciones_servidor\ 18.2/*.py \
   proyectoR/utils/acciones_servidor/
```

### Paso 2: Configurar Credenciales

```bash
# Crear archivo de credenciales
cat > proyectoR/config/db_credentials.json <<EOF
{
  "host": "localhost",
  "port": 5432,
  "database": "odoo_production",
  "user": "odoo_admin",
  "password": "your_secure_password",
  "sslmode": "require"
}
EOF

# Asegurar permisos
chmod 600 proyectoR/config/db_credentials.json
```

### Paso 3: Generar JSON de Configuración

```bash
cd proyectoR

# Ejecutar convertJSON.py
python3 convertJSON.py

# Verificar JSON generado
cat models_config.json | jq '.execution_order'
```

### Paso 4: Ejecutar Procesamiento

```bash
# Ejecutar Run.py
python3 Run.py

# Monitorear logs
tail -f output/logs/execution_*.log
```

### Paso 5: Revisar Resultados

```bash
# Ver resumen JSON
cat output/statistics/processing_report_*.json | jq '.summary'

# Ver CSV
cat output/statistics/processing_summary_*.csv

# Buscar errores
grep ERROR output/logs/execution_*.log
```

---

## 📝 RESUMEN EJECUTIVO

### Flujo Completo

```
1. convertJSON.py lee acciones_servidor/*.py
   ↓
2. Identifica patrones: CASCADE, DELETE WHERE, nombres
   ↓
3. Genera models_config.json
   ↓
4. Run.py carga credenciales desde config/
   ↓
5. Conecta a PostgreSQL
   ↓
6. Carga models_config.json
   ↓
7. Para cada modelo (en orden):
   a. Aplicar CASCADE
   b. Resecuenciar IDs
   c. Actualizar nombres
   d. Eliminar gaps
   e. DELETE con WHERE
   ↓
8. Genera reportes (JSON, CSV, LOG)
```

### Principios Clave

✅ **Credenciales primero** - Desde config/ al inicio
✅ **Orden correcto** - CASCADE → IDs → Nombres → Gaps → DELETE
✅ **Seguridad** - DELETE siempre con WHERE
✅ **CASCADE automático** - ON UPDATE CASCADE actualiza FKs automáticamente
✅ **No triggers** - No usar DISABLE/ENABLE TRIGGER
✅ **No UPDATE manual de FKs** - CASCADE lo hace automáticamente
✅ **Nombres con _** - Reemplazar . por _ en todos (incluso account.account usa _ en código)
✅ **Excepción account.account** - Código contable, no ID
✅ **Transaccional** - ROLLBACK por modelo si falla

---

**FIN DEL DOCUMENTO**
