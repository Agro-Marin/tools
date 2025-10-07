# Plan de Desarrollo: Sistema de Limpieza y Exportación de Datos Odoo

**Fecha:** 2025-10-01
**Versión:** 2.0 (Enfoque Revisado)
**Objetivo:** Sistema genérico controlado por JSON que ejecuta operaciones de limpieza en BD Odoo y exporta a CSV

---

## 📋 ÍNDICE

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Análisis de Patrones](#análisis-de-patrones)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Estructura JSON de Entrada](#estructura-json-de-entrada)
5. [Componentes del Sistema](#componentes-del-sistema)
6. [Flujo de Ejecución](#flujo-de-ejecución)
7. [Integración con Motor de Exportación Odoo](#integración-con-motor-de-exportación-odoo)
8. [Ejemplos de Código](#ejemplos-de-código)
9. [Consideraciones Técnicas](#consideraciones-técnicas)
10. [Fases de Implementación](#fases-de-implementación)

---

## 📊 RESUMEN EJECUTIVO

### Enfoque del Sistema

- **ENTRADA:** Archivo JSON con configuración de operaciones modelo por modelo
- **PROCESAMIENTO:** Ejecución de 6 tipos de operaciones usando API de Odoo
- **SALIDA:** Archivos CSV generados con motor nativo de exportación de Odoo

### Las 6 Operaciones Principales

1. **Redefinición de Foreign Keys** - ALTER TABLE con ON DELETE/UPDATE
2. **Limpieza de datos** - DELETE FROM tablas transaccionales y metadatos
3. **Re-secuenciación de IDs** - Eliminar huecos, ordenar consecutivamente
4. **Generación de metadatos** - Crear ir.model.data con External IDs
5. **Manejo de relaciones M2M** - Modificar tablas intermedias
6. **Actualización de secuencias PostgreSQL** - Sincronizar secuencias con MAX(id)

---

## 🔍 ANÁLISIS DE PATRONES

### Patrón Identificado en Scripts Existentes

Todos los scripts en `acciones_servidor 18.2/` siguen este patrón:

```python
# 1. Modificar FKs para controlar integridad referencial
env.cr.execute("ALTER TABLE ... DROP CONSTRAINT ...")
env.cr.execute("ALTER TABLE ... ADD CONSTRAINT ... ON DELETE CASCADE ...")

# 2. Limpiar datos transaccionales y metadatos
env.cr.execute("DELETE FROM website_track")
env.cr.execute("DELETE FROM ir_model_data WHERE module='__export__'")

# 3. Re-secuenciar IDs (eliminar huecos)
env.cr.execute("UPDATE res_partner SET id = id + 1000 WHERE id >= 8590")
# ... mapeo old_id -> new_id ...
env.cr.execute("UPDATE res_partner SET id = %s WHERE id = %s")

# 4. Generar metadatos (External IDs)
for record in env['res.partner'].search([('id', '>=', 5000)]):
    if not env['ir.model.data'].search([('model','=','res.partner'), ('res_id','=',record.id)]):
        env['ir.model.data'].create({
            'name': f'partner_{record.id}',
            'module': 'marin_data',
            'model': 'res.partner',
            'res_id': record.id
        })

# 5. Actualizar relaciones M2M
env.cr.execute("ALTER TABLE account_account_journal_rel ...")

# 6. Actualizar secuencia PostgreSQL
env.cr.execute("SELECT setval('res_partner_id_seq', (SELECT MAX(id) FROM res_partner))")
```

### Mapeo de Operaciones por Script

| Script | FK Redef | Limpieza | Re-seq | Metadata | M2M | Seq Update |
|--------|----------|----------|--------|----------|-----|------------|
| `res.parthner.py` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| `product.py` | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `stock_warehouse.py` | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| `account_journal.py` | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| `company.py` | ✅ | ✅ | ⚠️ (ID directo) | ✅ | ❌ | ✅ |

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### Diagrama de Componentes

```
┌─────────────────┐
│  config.json    │ (Entrada - Configuración)
└────────┬────────┘
         │
         v
┌────────────────────────────┐
│   ConfigLoader             │
│   - Validación JSON Schema │
│   - Parseo de config       │
└────────┬───────────────────┘
         │
         v
┌────────────────────────────┐
│   Orchestrator             │
│   - Control de flujo       │
│   - Gestión de errores     │
│   - Logging                │
└────────┬───────────────────┘
         │
         v
┌────────────────────────────┐      ┌──────────────────┐
│   OperationExecutor        │─────>│  Odoo ORM/CR     │
│   - FK redefinition        │      │  (env, env.cr)   │
│   - Data cleaning          │      └──────────────────┘
│   - ID resequencing        │
│   - Metadata generation    │      ┌──────────────────┐
│   - M2M handling           │─────>│  PostgreSQL      │
│   - Sequence update        │      │  (SQL directo)   │
└────────┬───────────────────┘      └──────────────────┘
         │
         v
┌────────────────────────────┐
│   CSVExporter              │
│   - Usa motor Odoo         │      ┌──────────────────┐
│   - records.export_data()  │─────>│  Archivos CSV    │
│   - Campos configurables   │      │  (Salida)        │
└────────────────────────────┘      └──────────────────┘
```

### Estructura de Directorios

```
odoo_data_cleaner/
├── models/
│   ├── __init__.py
│   ├── data_cleaner_orchestrator.py    # Orquestador principal
│   ├── operation_executor.py           # Ejecutor de operaciones
│   └── csv_exporter.py                 # Exportador CSV
├── config/
│   ├── config_schema.json              # JSON Schema para validación
│   └── models_config.json              # Configuración de modelos
├── data/
│   └── exports/                        # CSVs generados
├── logs/
│   └── cleaner.log                     # Logs de ejecución
├── tests/
│   ├── test_executor.py
│   └── test_exporter.py
└── __manifest__.py
```

---

## 📄 ESTRUCTURA JSON DE ENTRADA

### Schema Global

```json
{
  "global_settings": {
    "external_id_module": "marin_data",
    "log_level": "INFO",
    "stop_on_error": true,
    "output_directory": "/opt/odoo/exports"
  },
  "execution_plan": [
    { /* Configuración por modelo */ }
  ]
}
```

### Configuración por Modelo

```json
{
  "model_name": "res.partner",
  "description": "Limpieza y exportación de contactos",
  "enabled": true,
  "operations": {
    "foreign_key_redefinition": [ /* ... */ ],
    "data_cleaning": [ /* ... */ ],
    "resequence_ids": { /* ... */ },
    "generate_metadata": { /* ... */ },
    "m2m_relationships": [ /* ... */ ],
    "update_sequences": { /* ... */ }
  },
  "export": {
    "enabled": true,
    "output_filename": "res_partner.csv",
    "fields": ["id", "name", "email", "vat", "parent_id/id"]
  }
}
```

---

## 📝 EJEMPLOS COMPLETOS DE CONFIGURACIÓN

### Ejemplo 1: res.partner (Completo)

```json
{
  "model_name": "res.partner",
  "description": "Limpieza y exportación de contactos y empresas",
  "enabled": true,
  "operations": {
    "foreign_key_redefinition": [
      {
        "table": "res_partner",
        "column": "parent_id",
        "references_table": "res_partner",
        "references_column": "id",
        "on_delete": "SET NULL",
        "on_update": "CASCADE"
      },
      {
        "table": "account_analytic_account",
        "column": "partner_id",
        "references_table": "res_partner",
        "references_column": "id",
        "on_delete": "SET NULL",
        "on_update": "CASCADE"
      }
    ],
    "data_cleaning": [
      {
        "type": "orm",
        "model": "res.partner",
        "domain": "[('active', '=', False), ('create_date', '<', '2020-01-01')]",
        "description": "Eliminar contactos inactivos antiguos"
      },
      {
        "type": "sql",
        "table": "mail_compose_message",
        "where_clause": "1=1",
        "description": "Limpiar tabla de mensajes temporales"
      },
      {
        "type": "ir_model_data",
        "model": "res.partner",
        "module": "__export__",
        "description": "Limpiar metadatos de exportaciones previas"
      }
    ],
    "resequence_ids": {
      "enabled": true,
      "start_id": 8590,
      "domain": "[('id', '>=', 8590)]",
      "order_by": "id ASC",
      "temp_offset": 1000,
      "description": "Re-secuenciar desde ID 8590"
    },
    "generate_metadata": {
      "enabled": true,
      "module": "marin_data",
      "name_template": "partner_{id}",
      "domain": "[('id', '>=', 5000)]",
      "description": "Generar External IDs para partners >= 5000"
    },
    "m2m_relationships": [
      {
        "relation_table": "res_partner_res_partner_category_rel",
        "column1": "partner_id",
        "column2": "category_id",
        "references_table1": "res_partner",
        "references_table2": "res_partner_category",
        "on_delete": "CASCADE",
        "on_update": "CASCADE"
      }
    ],
    "update_sequences": {
      "enabled": true,
      "sequence_name": "res_partner_id_seq"
    }
  },
  "export": {
    "enabled": true,
    "output_filename": "res_partner.csv",
    "fields": [
      "id",
      "name",
      "ref",
      "email",
      "phone",
      "mobile",
      "vat",
      "street",
      "city",
      "zip",
      "country_id/id",
      "state_id/id",
      "parent_id/id",
      "category_id/id",
      "is_company",
      "active"
    ],
    "domain": "[]",
    "description": "Exportar todos los partners activos"
  }
}
```

### Ejemplo 2: product.template (Simplificado)

```json
{
  "model_name": "product.template",
  "description": "Limpieza y exportación de plantillas de productos",
  "enabled": true,
  "operations": {
    "data_cleaning": [
      {
        "type": "orm",
        "model": "product.template",
        "domain": "[('product_variant_count', '=', 0)]"
      },
      {
        "type": "sql",
        "table": "stock_valuation_layer",
        "where_clause": "1=1"
      }
    ],
    "resequence_ids": {
      "enabled": true,
      "start_id": 1000,
      "domain": "[('id', '>=', 1000)]",
      "order_by": "id ASC",
      "temp_offset": 10000
    },
    "generate_metadata": {
      "enabled": true,
      "module": "marin_data",
      "name_template": "product_template_{id}",
      "domain": "[]"
    },
    "update_sequences": {
      "enabled": true
    }
  },
  "export": {
    "enabled": true,
    "output_filename": "product_template.csv",
    "fields": [
      "id",
      "name",
      "default_code",
      "barcode",
      "list_price",
      "standard_price",
      "categ_id/id",
      "uom_id/id",
      "uom_po_id/id",
      "type",
      "active"
    ]
  }
}
```

### Ejemplo 3: stock.warehouse (Mínimo)

```json
{
  "model_name": "stock.warehouse",
  "description": "Limpieza y exportación de almacenes",
  "enabled": true,
  "operations": {
    "resequence_ids": {
      "enabled": true,
      "start_id": 1,
      "domain": "[]",
      "order_by": "id ASC",
      "temp_offset": 100
    },
    "generate_metadata": {
      "enabled": true,
      "module": "marin_data",
      "name_template": "warehouse_{id}",
      "domain": "[]"
    },
    "update_sequences": {
      "enabled": true
    }
  },
  "export": {
    "enabled": true,
    "output_filename": "stock_warehouse.csv",
    "fields": [
      "id",
      "name",
      "code",
      "company_id/id",
      "partner_id/id",
      "view_location_id/id",
      "lot_stock_id/id"
    ]
  }
}
```

---

## 🔧 COMPONENTES DEL SISTEMA

### 1. ConfigLoader

**Archivo:** `models/config_loader.py`

**Responsabilidad:** Cargar y validar el JSON de configuración

**Métodos:**
```python
class ConfigLoader:
    def load(self, config_path: str) -> dict:
        """Carga y valida el archivo JSON"""

    def validate_schema(self, config: dict) -> tuple[bool, list]:
        """Valida contra JSON Schema"""

    def get_enabled_models(self, config: dict) -> list:
        """Retorna solo modelos habilitados"""
```

---

### 2. Orchestrator (Modelo Odoo)

**Archivo:** `models/data_cleaner_orchestrator.py`

**Responsabilidad:** Coordinar la ejecución completa del proceso

**Métodos principales:**
```python
class DataCleanerOrchestrator(models.TransientModel):
    _name = 'data.cleaner.orchestrator'
    _description = 'Orquestador de Limpieza de Datos'

    config_file = fields.Char('Ruta Config JSON')

    def execute_cleaning_plan(self):
        """Ejecuta el plan completo de limpieza"""
        config = ConfigLoader().load(self.config_file)

        for model_config in config['execution_plan']:
            if not model_config['enabled']:
                continue

            try:
                with self.env.cr.savepoint():
                    self._process_model(model_config)
            except Exception as e:
                if config['global_settings']['stop_on_error']:
                    raise
                _logger.error(f"Error en {model_config['model_name']}: {e}")

    def _process_model(self, model_config: dict):
        """Procesa un modelo individual"""
        executor = self.env['data.cleaner.executor']
        exporter = self.env['data.cleaner.exporter']

        # Ejecutar operaciones en orden
        executor.execute_operations(model_config['model_name'], model_config['operations'])

        # Exportar si está habilitado
        if model_config['export']['enabled']:
            exporter.export_to_csv(
                model_config['model_name'],
                model_config['export']
            )
```

---

### 3. OperationExecutor (Modelo Odoo)

**Archivo:** `models/operation_executor.py`

**Responsabilidad:** Ejecutar las 6 operaciones de limpieza

```python
class DataCleanerExecutor(models.AbstractModel):
    _name = 'data.cleaner.executor'
    _description = 'Ejecutor de Operaciones de Limpieza'

    def execute_operations(self, model_name: str, operations: dict):
        """Ejecuta todas las operaciones configuradas"""
        if operations.get('foreign_key_redefinition'):
            self._execute_fk_redefinition(operations['foreign_key_redefinition'])

        if operations.get('data_cleaning'):
            self._execute_data_cleaning(operations['data_cleaning'])

        id_map = {}
        if operations.get('resequence_ids', {}).get('enabled'):
            id_map = self._execute_resequence_ids(model_name, operations['resequence_ids'])

        if operations.get('generate_metadata', {}).get('enabled'):
            self._execute_metadata_generation(model_name, operations['generate_metadata'], id_map)

        if operations.get('m2m_relationships'):
            self._execute_m2m_handling(operations['m2m_relationships'])

        if operations.get('update_sequences', {}).get('enabled'):
            self._execute_sequence_update(model_name, operations['update_sequences'])

    def _execute_fk_redefinition(self, fk_configs: list):
        """Redefinir Foreign Keys"""
        for fk in fk_configs:
            constraint_name = f"{fk['table']}_{fk['column']}_fkey"
            query = f"""
                ALTER TABLE {fk['table']}
                DROP CONSTRAINT IF EXISTS {constraint_name};

                ALTER TABLE {fk['table']}
                ADD CONSTRAINT {constraint_name}
                FOREIGN KEY ({fk['column']})
                REFERENCES {fk['references_table']}({fk.get('references_column', 'id')})
                ON DELETE {fk['on_delete']}
                ON UPDATE {fk['on_update']};
            """
            self.env.cr.execute(query)
            _logger.info(f"FK actualizada: {fk['table']}.{fk['column']}")

    def _execute_data_cleaning(self, cleaning_configs: list):
        """Limpieza de datos"""
        for config in cleaning_configs:
            if config['type'] == 'orm':
                domain = eval(config['domain'])
                records = self.env[config['model']].search(domain)
                count = len(records)
                records.unlink()
                _logger.info(f"Eliminados {count} registros de {config['model']}")

            elif config['type'] == 'sql':
                query = f"DELETE FROM {config['table']} WHERE {config['where_clause']}"
                self.env.cr.execute(query)
                _logger.info(f"DELETE ejecutado en {config['table']}")

            elif config['type'] == 'ir_model_data':
                self.env['ir.model.data'].search([
                    ('model', '=', config['model']),
                    ('module', '=', config['module'])
                ]).unlink()
                _logger.info(f"Metadatos eliminados: {config['model']}")

    def _execute_resequence_ids(self, model_name: str, config: dict) -> dict:
        """Re-secuenciar IDs"""
        table = self.env[model_name]._table
        start_id = config['start_id']
        temp_offset = config.get('temp_offset', 10000)

        # Obtener IDs actuales
        query = f"SELECT id FROM {table} ORDER BY {config.get('order_by', 'id ASC')}"
        self.env.cr.execute(query)
        old_ids = [r[0] for r in self.env.cr.fetchall()]

        # Crear mapeo
        id_map = {old_id: start_id + idx for idx, old_id in enumerate(old_ids)}

        # Mover a rango temporal
        self.env.cr.execute(f"UPDATE {table} SET id = id + {temp_offset}")

        # Actualizar a nuevos IDs
        for old_id, new_id in id_map.items():
            self.env.cr.execute(
                f"UPDATE {table} SET id = %s WHERE id = %s",
                (new_id, old_id + temp_offset)
            )

        _logger.info(f"Re-secuenciados {len(id_map)} registros de {model_name}")
        return id_map

    def _execute_metadata_generation(self, model_name: str, config: dict, id_map: dict):
        """Generar ir.model.data"""
        module = config['module']
        name_template = config['name_template']
        domain = eval(config.get('domain', '[]'))

        for record in self.env[model_name].search(domain):
            existing = self.env['ir.model.data'].search([
                ('model', '=', model_name),
                ('res_id', '=', record.id)
            ])

            if not existing:
                name = name_template.replace('{id}', str(record.id))
                self.env['ir.model.data'].create({
                    'name': name,
                    'module': module,
                    'model': model_name,
                    'res_id': record.id
                })

    def _execute_m2m_handling(self, m2m_configs: list):
        """Manejar relaciones M2M"""
        for m2m in m2m_configs:
            for idx, col in enumerate([m2m['column1'], m2m['column2']], 1):
                ref_table = m2m[f'references_table{idx}']
                constraint_name = f"{m2m['relation_table']}_{col}_fkey"

                query = f"""
                    ALTER TABLE {m2m['relation_table']}
                    DROP CONSTRAINT IF EXISTS {constraint_name};

                    ALTER TABLE {m2m['relation_table']}
                    ADD CONSTRAINT {constraint_name}
                    FOREIGN KEY ({col})
                    REFERENCES {ref_table}(id)
                    ON DELETE {m2m['on_delete']}
                    ON UPDATE {m2m['on_update']};
                """
                self.env.cr.execute(query)

    def _execute_sequence_update(self, model_name: str, config: dict):
        """Actualizar secuencias PostgreSQL"""
        table = self.env[model_name]._table
        sequence_name = config.get('sequence_name', f'{table}_id_seq')

        query = f"SELECT setval('{sequence_name}', (SELECT MAX(id) FROM {table}))"
        self.env.cr.execute(query)
        _logger.info(f"Secuencia {sequence_name} actualizada")
```

---

### 4. CSVExporter (Modelo Odoo)

**Archivo:** `models/csv_exporter.py`

**Responsabilidad:** Exportar datos a CSV usando motor nativo de Odoo

```python
class DataCleanerExporter(models.AbstractModel):
    _name = 'data.cleaner.exporter'
    _description = 'Exportador de Datos a CSV'

    def export_to_csv(self, model_name: str, export_config: dict):
        """Exporta modelo a CSV usando motor nativo de Odoo"""
        import csv

        output_file = export_config['output_filename']
        fields = export_config['fields']
        domain = eval(export_config.get('domain', '[]'))

        # Buscar registros
        Model = self.env[model_name]
        records = Model.search(domain)

        if not records:
            _logger.warning(f"No hay registros para exportar en {model_name}")
            return None

        _logger.info(f"Exportando {len(records)} registros de {model_name}")

        # Usar exportación nativa
        export_data = records.export_data(fields)

        # Escribir CSV
        output_path = self._get_output_path(output_file)

        with open(output_path, 'w', encoding='utf-8', newline='') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)

            # Headers
            writer.writerow(fields)

            # Data
            for row in export_data['datas']:
                writer.writerow(row)

        _logger.info(f"Exportación completada: {output_path}")
        return output_path

    def _get_output_path(self, filename: str) -> str:
        """Obtener ruta completa del archivo de salida"""
        import os
        config_param = self.env['ir.config_parameter'].sudo()
        output_dir = config_param.get_param('data_cleaner.output_directory', '/tmp')
        return os.path.join(output_dir, filename)
```

---

## 🔄 FLUJO DE EJECUCIÓN

### Diagrama de Secuencia

```
Usuario/Cron -> Orchestrator.execute_cleaning_plan()
                     |
                     v
              ConfigLoader.load(config.json)
                     |
                     v
         ┌───────────┴────────────┐
         │ Loop: Para cada modelo │
         └───────────┬────────────┘
                     |
                     v
            OperationExecutor.execute_operations()
                     |
         ┌───────────┴────────────────────────────┐
         │  1. FK Redefinition                    │
         │     - ALTER TABLE ... DROP CONSTRAINT  │
         │     - ALTER TABLE ... ADD CONSTRAINT   │
         └───────────┬────────────────────────────┘
                     v
         ┌───────────┴────────────────────────────┐
         │  2. Data Cleaning                      │
         │     - ORM: records.unlink()            │
         │     - SQL: DELETE FROM ...             │
         │     - Metadata: ir.model.data.unlink() │
         └───────────┬────────────────────────────┘
                     v
         ┌───────────┴────────────────────────────┐
         │  3. ID Resequencing                    │
         │     - UPDATE ... SET id = id + offset  │
         │     - Mapeo old_id -> new_id           │
         │     - UPDATE ... SET id = new_id       │
         └───────────┬────────────────────────────┘
                     v
         ┌───────────┴────────────────────────────┐
         │  4. Metadata Generation                │
         │     - Crear ir.model.data              │
         │     - External IDs únicos              │
         └───────────┬────────────────────────────┘
                     v
         ┌───────────┴────────────────────────────┐
         │  5. M2M Handling                       │
         │     - Actualizar tablas relacionales   │
         │     - Redefinir FKs en tablas M2M      │
         └───────────┬────────────────────────────┘
                     v
         ┌───────────┴────────────────────────────┐
         │  6. Sequence Update                    │
         │     - SELECT setval(...)               │
         └───────────┬────────────────────────────┘
                     v
              CSVExporter.export_to_csv()
                     |
         ┌───────────┴────────────────────────────┐
         │  - records.export_data(fields)         │
         │  - Escribir CSV                        │
         │  - Guardar en output_directory         │
         └───────────┬────────────────────────────┘
                     v
                 [CSV File]
```

---

## 📤 INTEGRACIÓN CON MOTOR DE EXPORTACIÓN ODOO

### Métodos Nativos de Exportación

Odoo proporciona el método `export_data()` para exportar registros:

```python
# Uso básico
records = env['res.partner'].search([])
fields_to_export = ['id', 'name', 'email', 'parent_id/id']

export_result = records.export_data(fields_to_export)
# Retorna: {
#   'datas': [['1', 'John Doe', 'john@example.com', '']],
#   ...
# }
```

### Características Soportadas

- **Campos relacionales:** `parent_id/id`, `country_id/name`
- **Campos many2many:** `category_id/id`
- **Campos computados:** Se exportan sus valores actuales
- **Formato compatible:** CSV listo para re-importación en Odoo

---

## 💻 EJEMPLOS DE CÓDIGO

### Ejemplo de Uso Completo

```python
# Desde Odoo Shell o acción de servidor
orchestrator = env['data.cleaner.orchestrator'].create({
    'config_file': '/opt/odoo/config/models_config.json'
})

orchestrator.execute_cleaning_plan()

# Output:
# [INFO] Cargando configuración...
# [INFO] Procesando modelo: res.partner
# [INFO] FK redefinition: 5 constraints actualizados
# [INFO] Data cleaning: 250 registros eliminados
# [INFO] ID resequencing: 1,250 IDs re-secuenciados
# [INFO] Metadata generation: 1,250 External IDs creados
# [INFO] Exportando 1,250 registros a res_partner.csv
# [INFO] Exportación completada: /opt/odoo/exports/res_partner.csv
```

### Ejemplo de Llamada por Acción de Servidor

```python
# Acción de servidor en Odoo
# Modelo: ir.actions.server
# Tipo: Código Python

config_path = '/opt/odoo/config/cleaning_config.json'

orchestrator = env['data.cleaner.orchestrator'].create({
    'config_file': config_path
})

try:
    orchestrator.execute_cleaning_plan()
    raise UserError("Limpieza completada exitosamente. Revisa los logs.")
except Exception as e:
    raise UserError(f"Error durante la limpieza: {str(e)}")
```

---

## ⚙️ CONSIDERACIONES TÉCNICAS

### Transacciones y Rollback

```python
# Usar savepoints para transacciones anidadas
with env.cr.savepoint():
    try:
        executor.execute_operations(model_name, operations)
        exporter.export_to_csv(model_name, export_config)
    except Exception as e:
        # Rollback automático al savepoint
        _logger.error(f"Error: {e}")
        if stop_on_error:
            raise
```

### Manejo de Re-secuenciación Segura

**Estrategia:**
1. Usar offset temporal grande (ej. 10000) para evitar colisiones
2. Crear mapeo completo old_id -> new_id
3. Actualizar tabla principal en orden
4. Confiar en ON UPDATE CASCADE para actualizar FKs automáticamente

### Validaciones Previas

- Verificar que tablas existan antes de ALTER TABLE
- Validar que start_id >= 1 en resequencing
- Confirmar que modelo existe en Odoo registry
- Validar sintaxis de domains antes de ejecutar

### Logging Detallado

```python
_logger.info(f"[{model_name}] Iniciando procesamiento")
_logger.info(f"[{model_name}] FK redefinition: {count} constraints")
_logger.info(f"[{model_name}] Data cleaning: {count} registros eliminados")
_logger.info(f"[{model_name}] Re-sequencing: {count} IDs actualizados")
_logger.info(f"[{model_name}] Metadata: {count} External IDs creados")
_logger.info(f"[{model_name}] Exportación: {output_path}")
```

---

## 🚀 FASES DE IMPLEMENTACIÓN

### Fase 1: Estructura Base (1 semana)
- ✅ Estructura de módulo Odoo
- ✅ ConfigLoader con validación JSON Schema
- ✅ Orchestrator básico
- ✅ Sistema de logging

**Entregable:** Módulo instalable que carga y valida JSON

---

### Fase 2: Operaciones Básicas (2 semanas)
- ✅ FK Redefinition
- ✅ Data Cleaning (ORM y SQL)
- ✅ Sequence Update
- ✅ Tests unitarios

**Entregable:** Ejecución de operaciones 1, 2 y 6

---

### Fase 3: Re-secuenciación (2 semanas)
- ✅ Algoritmo de re-secuenciación seguro
- ✅ Manejo de FKs durante re-sequencing
- ✅ Tests con datos reales

**Entregable:** Operación 3 funcionando correctamente

---

### Fase 4: Metadatos y M2M (1 semana)
- ✅ Metadata Generation
- ✅ M2M Handling
- ✅ Validaciones de integridad

**Entregable:** Operaciones 4 y 5 implementadas

---

### Fase 5: Exportación CSV (1 semana)
- ✅ Integración con motor de exportación Odoo
- ✅ Soporte para campos relacionales
- ✅ Formato CSV estándar
- ✅ Manejo de caracteres especiales

**Entregable:** CSVs generados correctamente

---

### Fase 6: Testing y Documentación (1 semana)
- ✅ Tests de integración completos
- ✅ Documentación de usuario
- ✅ Ejemplos de configuración
- ✅ Manejo de errores robusto

**Entregable:** Sistema completo y documentado

---

## 📊 MÉTRICAS DE ÉXITO

| Métrica | Objetivo |
|---------|----------|
| Modelos soportados | 100% de scripts en `acciones_servidor 18.2/` |
| Tasa de éxito | >99% de operaciones completadas |
| Tiempo de ejecución | <5 min para 50,000 registros |
| Tamaño de CSV | Formato compatible con importación Odoo |
| Integridad de datos | 0 errores de FK después de limpieza |

---

## 🎯 PRÓXIMOS PASOS

1. **Crear estructura de módulo Odoo** (`__manifest__.py`, `models/`, `config/`)
2. **Implementar ConfigLoader** con JSON Schema
3. **Desarrollar Orchestrator** con flujo básico
4. **Implementar OperationExecutor** operación por operación
5. **Integrar CSVExporter** con motor nativo
6. **Crear JSONs de configuración** para los 30 scripts existentes
7. **Testing exhaustivo** con base de datos de prueba

---

**Documento generado:** 2025-10-01
**Versión:** 2.0
**Estado:** Listo para implementación
