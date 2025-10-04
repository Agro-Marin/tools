# Plan de Desarrollo 1: Sistema de Procesamiento de Data Maestra

**Fecha:** 2025-10-01
**Versión:** 1.0
**Premisa:** La data sucia **ya está extraída en archivos CSV** listos para procesar
**Objetivo:** Procesar, limpiar y validar data maestra lista para importar a BD Odoo

---

## 📋 ÍNDICE

1. [Premisa y Contexto](#premisa-y-contexto)
2. [Diagrama de Flujo Lógico Completo](#diagrama-de-flujo-lógico-completo)
3. [Estructura de Directorios](#estructura-de-directorios)
4. [Estructura JSON de Configuración](#estructura-json-de-configuración)
5. [Componentes del Sistema](#componentes-del-sistema)
6. [Descripción de las 6 Operaciones](#descripción-de-las-6-operaciones)
7. [Ejemplo de Ejecución](#ejemplo-de-ejecución)
8. [Plan de Implementación](#plan-de-implementación)

---

## 🎯 PREMISA Y CONTEXTO

### Punto de Partida

```
┌─────────────────────────────────────────────────────┐
│          DIRECTORIO CON DATA EXTRAÍDA               │
│       =========================================      │
│                                                     │
│  data/input/                                        │
│  ├─ res_partner.csv (8,590 registros)              │
│  │   └─ IDs: 1, 5, 27, 103, 8590, 8591...         │
│  │   └─ Sin External IDs                           │
│  │   └─ Puede tener registros duplicados           │
│  │                                                  │
│  ├─ product_template.csv (3,200 registros)          │
│  │   └─ IDs dispersos                              │
│  │   └─ Relaciones con categorías                  │
│  │                                                  │
│  ├─ stock_warehouse.csv (15 registros)              │
│  │   └─ IDs: 1, 2, 5, 101, 102...                 │
│  │                                                  │
│  └─ account_move.csv (12,000 registros)            │
│      └─ Datos transaccionales                      │
│                                                     │
│  Problemas:                                         │
│  ├─ IDs con huecos y desordenados                  │
│  ├─ Sin External IDs (ir.model.data)               │
│  ├─ Registros potencialmente duplicados            │
│  ├─ Relaciones pueden estar rotas                  │
│  └─ Datos sin validar                              │
└─────────────────────────────────────────────────────┘
```

### Objetivo Final

```
┌─────────────────────────────────────────────────────┐
│         DIRECTORIO CON DATA MAESTRA LIMPIA          │
│       =========================================      │
│                                                     │
│  data/output/                                       │
│  ├─ res_partner_clean.csv                           │
│  │   └─ IDs: 1, 2, 3, 4, 5... (consecutivos)       │
│  │   └─ Todos con External ID                      │
│  │   └─ Sin duplicados                             │
│  │   └─ Validados y limpios                        │
│  │                                                  │
│  ├─ product_template_clean.csv                      │
│  │   └─ IDs: 1000, 1001, 1002... (consecutivos)    │
│  │   └─ Con External IDs                           │
│  │   └─ Relaciones verificadas                     │
│  │                                                  │
│  ├─ stock_warehouse_clean.csv                       │
│  │   └─ IDs: 1, 2, 3... (consecutivos)             │
│  │   └─ Data validada                              │
│  │                                                  │
│  └─ metadata/                                       │
│      ├─ ir_model_data.csv  ← External IDs          │
│      └─ processing_report.json                     │
│                                                     │
│  ✓ Listos para importar en Odoo                    │
│  ✓ IDs consecutivos y ordenados                    │
│  ✓ External IDs generados                          │
│  ✓ Relaciones correctas                            │
│  ✓ Datos validados                                 │
└─────────────────────────────────────────────────────┘
```

---

## 📊 DIAGRAMA DE FLUJO LÓGICO COMPLETO

```
═══════════════════════════════════════════════════════════════════
                            INICIO
═══════════════════════════════════════════════════════════════════
                              │
                              │ Usuario ejecuta: python run_processor.py
                              v
┌──────────────────────────────────────────────────────────────────┐
│  FASE 1: CARGA DE CONFIGURACIÓN                                 │
│  ═══════════════════════════════                                 │
│                                                                  │
│  ┌────────────────────────────────────────────┐                 │
│  │  config/models_config.json                 │                 │
│  │  {                                         │                 │
│  │    "global_settings": {                    │                 │
│  │      "input_directory": "data/input",      │                 │
│  │      "output_directory": "data/output",    │                 │
│  │      "external_id_module": "marin_data",   │                 │
│  │      "stop_on_error": true                 │                 │
│  │    },                                      │                 │
│  │    "execution_plan": [                     │                 │
│  │      {                                     │                 │
│  │        "model_name": "res.partner",        │                 │
│  │        "input_file": "res_partner.csv",    │                 │
│  │        "operations": {                     │                 │
│  │          "data_cleaning": [...],           │                 │
│  │          "resequence_ids": {...},          │                 │
│  │          "generate_metadata": {...}        │                 │
│  │        },                                  │                 │
│  │        "export": {                         │                 │
│  │          "output_file": "res_partner_clean.csv",             │
│  │          "fields": ["id", "name", ...]     │                 │
│  │        }                                   │                 │
│  │      }                                     │                 │
│  │    ]                                       │                 │
│  │  }                                         │                 │
│  └────────────┬─────────────────────────────────┘                 │
│               │                                                  │
│               v                                                  │
│  ┌────────────────────────────────────────────┐                 │
│  │     ConfigLoader                           │                 │
│  │  ────────────────────────────────────────  │                 │
│  │  • Cargar JSON                             │                 │
│  │  • Validar schema                          │                 │
│  │  • Verificar archivos de entrada existen   │                 │
│  │  • Preparar plan de ejecución              │                 │
│  └────────────┬─────────────────────────────────┘                 │
│               │                                                  │
│               v                                                  │
│  ┌────────────────────────────────────────────┐                 │
│  │  Validación exitosa                        │                 │
│  │  • 15 modelos configurados                 │                 │
│  │  • Archivos de entrada verificados         │                 │
│  │  • Directorio de salida preparado          │                 │
│  └────────────┬─────────────────────────────────┘                 │
└───────────────┼──────────────────────────────────────────────────┘
                │
                │ Config validada, iniciar procesamiento
                v
┌──────────────────────────────────────────────────────────────────┐
│  FASE 2: ORQUESTACIÓN - LOOP POR MODELO                         │
│  ═══════════════════════════════════════════                     │
│                                                                  │
│  ┌────────────────────────────────────────────┐                 │
│  │     Orchestrator                           │                 │
│  │  ────────────────────────────────────────  │                 │
│  │                                            │                 │
│  │  for model_config in execution_plan:       │                 │
│  │      if not model_config['enabled']:       │                 │
│  │          continue                          │                 │
│  │                                            │                 │
│  │      logger.info(f"Procesando {model}")    │                 │
│  │      process_model(model_config)           │                 │
│  └────────────┬─────────────────────────────────┘                 │
│               │                                                  │
│               │ Modelo actual: res.partner                       │
│               v                                                  │
│  ┌────────────────────────────────────────────┐                 │
│  │  1. Cargar CSV de entrada                  │                 │
│  │     └─ data/input/res_partner.csv          │                 │
│  └────────────┬─────────────────────────────────┘                 │
└───────────────┼──────────────────────────────────────────────────┘
                │
                v
┌──────────────────────────────────────────────────────────────────┐
│  FASE 3: CARGA DE DATA SUCIA                                    │
│  ═══════════════════════════                                     │
│                                                                  │
│  ┌────────────────────────────────────────────┐                 │
│  │     CSVReader                              │                 │
│  │  ────────────────────────────────────────  │                 │
│  │  • Leer res_partner.csv                    │                 │
│  │  • Parsear columnas                        │                 │
│  │  • Validar tipos de datos básicos          │                 │
│  │  • Cargar en memoria (o chunks)            │                 │
│  └────────────┬─────────────────────────────────┘                 │
│               │                                                  │
│               v                                                  │
│  ┌────────────────────────────────────────────┐                 │
│  │  DataFrame / Lista de registros            │                 │
│  │  [                                         │                 │
│  │    {id: 1, name: "John", email: "..."},    │                 │
│  │    {id: 5, name: "Jane", email: "..."},    │                 │
│  │    {id: 27, name: "Acme", email: "..."},   │                 │
│  │    ...                                     │                 │
│  │  ]                                         │                 │
│  │  Total: 8,590 registros cargados           │                 │
│  └────────────┬─────────────────────────────────┘                 │
└───────────────┼──────────────────────────────────────────────────┘
                │
                │ Data cargada en memoria
                v
┌──────────────────────────────────────────────────────────────────┐
│  FASE 4: EJECUCIÓN DE 6 OPERACIONES                             │
│  ═══════════════════════════════════                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  OPERACIÓN 1: FK REDEFINITION (Opcional/Skip en CSV)       │ │
│  │  ════════════════════════════════════════════════════════  │ │
│  │                                                            │ │
│  │  ⚠️ Esta operación es principalmente para BD              │ │
│  │  En procesamiento CSV: SKIP o validar integridad          │ │
│  │                                                            │ │
│  │  Alternativa: Validar que las relaciones existan          │ │
│  │  • Verificar parent_id existe en registros                 │ │
│  │  • Marcar registros con FK rotas                           │ │
│  │                                                            │ │
│  │  Resultado: Validación de integridad referencial           │ │
│  └────────────────────────┬───────────────────────────────────┘ │
│                           │                                      │
│                           v                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  OPERACIÓN 2: DATA CLEANING                                │ │
│  │  ════════════════════════════════════════════════════════  │ │
│  │                                                            │ │
│  │  A. Limpieza por condiciones                               │ │
│  │     config = {                                             │ │
│  │       "type": "filter",                                    │ │
│  │       "conditions": [                                      │ │
│  │         "active == True",                                  │ │
│  │         "email is not null"                                │ │
│  │       ]                                                    │ │
│  │     }                                                      │ │
│  │                                                            │ │
│  │     # Filtrar registros                                    │ │
│  │     registros_limpios = [                                  │ │
│  │       r for r in registros                                 │ │
│  │       if r['active'] == True and r['email']                │ │
│  │     ]                                                      │ │
│  │     # Antes: 8,590 → Después: 8,340 registros              │ │
│  │                                                            │ │
│  │  B. Eliminar duplicados                                    │ │
│  │     config = {                                             │ │
│  │       "type": "deduplicate",                               │ │
│  │       "key_fields": ["email", "vat"]                       │ │
│  │     }                                                      │ │
│  │                                                            │ │
│  │     # Detectar y eliminar duplicados                       │ │
│  │     registros_unicos = remove_duplicates(                  │ │
│  │       registros_limpios,                                   │ │
│  │       keys=['email', 'vat']                                │ │
│  │     )                                                      │ │
│  │     # 8,340 → 8,325 registros (15 duplicados eliminados)   │ │
│  │                                                            │ │
│  │  C. Normalizar datos                                       │ │
│  │     • Limpiar espacios en blanco                           │ │
│  │     • Normalizar emails (lowercase)                        │ │
│  │     • Formatear teléfonos                                  │ │
│  │                                                            │ │
│  │  Resultado: 8,325 registros limpios y validados            │ │
│  └────────────────────────┬───────────────────────────────────┘ │
│                           │                                      │
│                           v                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  OPERACIÓN 3: ID RESEQUENCING                              │ │
│  │  ════════════════════════════════════════════════════════  │ │
│  │                                                            │ │
│  │  Entrada: IDs dispersos [1, 5, 27, 103, 8590, 8591...]    │ │
│  │  Salida:  IDs consecutivos [1, 2, 3, 4, 5, 6, 7...]       │ │
│  │                                                            │ │
│  │  config = {                                                │ │
│  │    "enabled": true,                                        │ │
│  │    "start_id": 1,                                          │ │
│  │    "order_by": ["id"]                                      │ │
│  │  }                                                         │ │
│  │                                                            │ │
│  │  1. Ordenar registros                                      │ │
│  │     registros_ordenados = sorted(                          │ │
│  │       registros_limpios,                                   │ │
│  │       key=lambda x: x['id']                                │ │
│  │     )                                                      │ │
│  │                                                            │ │
│  │  2. Crear mapeo old_id → new_id                            │ │
│  │     id_map = {}                                            │ │
│  │     new_id = 1  # start_id                                 │ │
│  │     for registro in registros_ordenados:                   │ │
│  │       id_map[registro['id']] = new_id                      │ │
│  │       registro['id_original'] = registro['id']             │ │
│  │       registro['id'] = new_id                              │ │
│  │       new_id += 1                                          │ │
│  │                                                            │ │
│  │     # Mapeo creado:                                        │ │
│  │     # {1: 1, 5: 2, 27: 3, 103: 4, 8590: 5, 8591: 6, ...}  │ │
│  │                                                            │ │
│  │  3. Actualizar FKs en registros                            │ │
│  │     for registro in registros_ordenados:                   │ │
│  │       if registro.get('parent_id'):                        │ │
│  │         old_parent = registro['parent_id']                 │ │
│  │         registro['parent_id'] = id_map.get(old_parent)     │ │
│  │                                                            │ │
│  │  Resultado: 8,325 registros con IDs consecutivos [1-8325]  │ │
│  └────────────────────────┬───────────────────────────────────┘ │
│                           │                                      │
│                           v                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  OPERACIÓN 4: METADATA GENERATION                          │ │
│  │  ════════════════════════════════════════════════════════  │ │
│  │                                                            │ │
│  │  Generar External IDs para todos los registros             │ │
│  │                                                            │ │
│  │  config = {                                                │ │
│  │    "enabled": true,                                        │ │
│  │    "module": "marin_data",                                 │ │
│  │    "name_template": "partner_{id}"                         │ │
│  │  }                                                         │ │
│  │                                                            │ │
│  │  metadata_records = []                                     │ │
│  │  for registro in registros_ordenados:                      │ │
│  │    external_id = f"marin_data.partner_{registro['id']}"    │ │
│  │    registro['external_id'] = external_id                   │ │
│  │                                                            │ │
│  │    # Crear registro para ir.model.data                     │ │
│  │    metadata_records.append({                               │ │
│  │      'module': 'marin_data',                               │ │
│  │      'name': f"partner_{registro['id']}",                  │ │
│  │      'model': 'res.partner',                               │ │
│  │      'res_id': registro['id']                              │ │
│  │    })                                                      │ │
│  │                                                            │ │
│  │  Resultado:                                                │ │
│  │  • 8,325 registros con External ID                         │ │
│  │  • Archivo metadata/ir_model_data.csv generado             │ │
│  └────────────────────────┬───────────────────────────────────┘ │
│                           │                                      │
│                           v                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  OPERACIÓN 5: M2M HANDLING                                 │ │
│  │  ════════════════════════════════════════════════════════  │ │
│  │                                                            │ │
│  │  Procesar relaciones Many2Many                             │ │
│  │                                                            │ │
│  │  Si hay archivo: res_partner_category_rel.csv              │ │
│  │                                                            │ │
│  │  1. Cargar archivo de relación M2M                         │ │
│  │     m2m_records = CSVReader.read(                          │ │
│  │       'res_partner_category_rel.csv'                       │ │
│  │     )                                                      │ │
│  │                                                            │ │
│  │  2. Actualizar IDs con mapeo                               │ │
│  │     for rel in m2m_records:                                │ │
│  │       rel['partner_id'] = id_map[rel['partner_id']]        │ │
│  │       rel['category_id'] = cat_id_map[rel['category_id']]  │ │
│  │                                                            │ │
│  │  3. Exportar relación actualizada                          │ │
│  │     CSVWriter.write(                                       │ │
│  │       m2m_records,                                         │ │
│  │       'res_partner_category_rel_clean.csv'                 │ │
│  │     )                                                      │ │
│  │                                                            │ │
│  │  Resultado: Archivos M2M actualizados con nuevos IDs       │ │
│  └────────────────────────┬───────────────────────────────────┘ │
│                           │                                      │
│                           v                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  OPERACIÓN 6: SEQUENCE UPDATE (Skip en CSV)               │ │
│  │  ════════════════════════════════════════════════════════  │ │
│  │                                                            │ │
│  │  ⚠️ Esta operación es para BD PostgreSQL                   │ │
│  │  En procesamiento CSV: SKIP                                │ │
│  │                                                            │ │
│  │  Alternativa: Generar archivo de secuencias                │ │
│  │  sequences.json:                                           │ │
│  │  {                                                         │ │
│  │    "res_partner_id_seq": 8326,                             │ │
│  │    "product_template_id_seq": 3201,                        │ │
│  │    ...                                                     │ │
│  │  }                                                         │ │
│  │                                                            │ │
│  │  Resultado: Archivo con valores para setval()              │ │
│  └────────────────────────┬───────────────────────────────────┘ │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                            │ Operaciones completadas
                            v
┌──────────────────────────────────────────────────────────────────┐
│  FASE 5: EXPORTACIÓN DE DATA LIMPIA                             │
│  ═══════════════════════════════════                             │
│                                                                  │
│  ┌────────────────────────────────────────────┐                 │
│  │     CSVExporter                            │                 │
│  │  ────────────────────────────────────────  │                 │
│  │                                            │                 │
│  │  config = {                                │                 │
│  │    "output_file": "res_partner_clean.csv", │                 │
│  │    "fields": [                             │                 │
│  │      "id",                                 │                 │
│  │      "external_id",                        │                 │
│  │      "id_original",                        │                 │
│  │      "name",                               │                 │
│  │      "email",                              │                 │
│  │      "parent_id",                          │                 │
│  │      "category_id"                         │                 │
│  │    ]                                       │                 │
│  │  }                                         │                 │
│  │                                            │                 │
│  │  1. Seleccionar campos                     │                 │
│  │  2. Formatear datos                        │                 │
│  │  3. Escribir CSV                           │                 │
│  └────────────┬───────────────────────────────┘                 │
│               │                                                  │
│               v                                                  │
│  ┌────────────────────────────────────────────┐                 │
│  │  data/output/res_partner_clean.csv         │                 │
│  │  ─────────────────────────────────────     │                 │
│  │  id,external_id,id_original,name,email,... │                 │
│  │  1,marin_data.partner_1,1,John,john@...,   │                 │
│  │  2,marin_data.partner_2,5,Jane,jane@...,   │                 │
│  │  3,marin_data.partner_3,27,Acme,acme@...,  │                 │
│  │  ...                                       │                 │
│  │                                            │                 │
│  │  ✓ 8,325 registros exportados              │                 │
│  │  ✓ IDs consecutivos [1-8325]               │                 │
│  │  ✓ Con External IDs                        │                 │
│  │  ✓ Relaciones actualizadas                 │                 │
│  └────────────┬───────────────────────────────┘                 │
└───────────────┼──────────────────────────────────────────────────┘
                │
                │ CSV limpio guardado
                v
┌──────────────────────────────────────────────────────────────────┐
│  FASE 6: GENERACIÓN DE REPORTES                                 │
│  ═══════════════════════════                                     │
│                                                                  │
│  ┌────────────────────────────────────────────┐                 │
│  │  Generar estadísticas y logs               │                 │
│  │                                            │                 │
│  │  processing_report.json:                   │                 │
│  │  {                                         │                 │
│  │    "model": "res.partner",                 │                 │
│  │    "input_file": "res_partner.csv",        │                 │
│  │    "output_file": "res_partner_clean.csv", │                 │
│  │    "statistics": {                         │                 │
│  │      "records_input": 8590,                │                 │
│  │      "records_cleaned": 8340,              │                 │
│  │      "records_duplicates": 15,             │                 │
│  │      "records_output": 8325,               │                 │
│  │      "ids_resequenced": 8325,              │                 │
│  │      "external_ids_created": 8325          │                 │
│  │    },                                      │                 │
│  │    "operations_executed": [                │                 │
│  │      "data_cleaning",                      │                 │
│  │      "id_resequencing",                    │                 │
│  │      "metadata_generation"                 │                 │
│  │    ],                                      │                 │
│  │    "errors": [],                           │                 │
│  │    "warnings": [                           │                 │
│  │      "15 registros duplicados eliminados"  │                 │
│  │    ]                                       │                 │
│  │  }                                         │                 │
│  └────────────┬───────────────────────────────┘                 │
└───────────────┼──────────────────────────────────────────────────┘
                │
                │ Loop continúa con siguiente modelo
                │ (product.template, stock.warehouse, etc)
                v
┌──────────────────────────────────────────────────────────────────┐
│  FASE 7: FINALIZACIÓN                                            │
│  ═══════════════════                                             │
│                                                                  │
│  • Generar resumen global                                        │
│  • Consolidar logs                                               │
│  • Generar archivo de importación para Odoo                      │
│                                                                  │
│  ┌────────────────────────────────────────────┐                 │
│  │  Resumen Global                            │                 │
│  │  ════════════════════════════════════════  │                 │
│  │                                            │                 │
│  │  Modelos procesados: 15 / 15               │                 │
│  │  ├─ res.partner: 8,325 registros           │                 │
│  │  ├─ product.template: 3,180 registros      │                 │
│  │  ├─ stock.warehouse: 15 registros          │                 │
│  │  └─ ...                                    │                 │
│  │                                            │                 │
│  │  Operaciones totales:                      │                 │
│  │  ├─ Registros procesados: 45,230           │                 │
│  │  ├─ Registros limpiados: 44,100            │                 │
│  │  ├─ Duplicados eliminados: 1,130           │                 │
│  │  ├─ IDs re-secuenciados: 44,100            │                 │
│  │  └─ External IDs creados: 44,100           │                 │
│  │                                            │                 │
│  │  Archivos generados:                       │                 │
│  │  ├─ 15 CSVs limpios en data/output/       │                 │
│  │  ├─ 1 archivo ir_model_data.csv            │                 │
│  │  ├─ 15 reportes JSON                       │                 │
│  │  └─ 1 resumen global                       │                 │
│  │                                            │                 │
│  │  Tiempo total: 2m 15s                      │                 │
│  │  Estado: ✓ EXITOSO                         │                 │
│  └────────────────────────────────────────────┘                 │
└──────────────────────────────────────────────────────────────────┘
                              │
                              v
═══════════════════════════════════════════════════════════════════
                            FIN
═══════════════════════════════════════════════════════════════════
```

---

## 📁 ESTRUCTURA DE DIRECTORIOS

```
proyecto_limpieza_data_maestra/
│
├── README.md                          # Documentación del proyecto
├── requirements.txt                   # Dependencias Python
├── setup.py                          # Instalación del paquete
├── .gitignore                        # Archivos a ignorar
│
├── config/                           # Configuraciones
│   ├── models_config.json            # ← CONFIGURACIÓN PRINCIPAL
│   ├── config_schema.json            # JSON Schema para validación
│   │
│   └── models/                       # Configs individuales por modelo
│       ├── res_partner.json
│       ├── product_template.json
│       └── stock_warehouse.json
│
├── data/                             # Datos de entrada/salida
│   ├── input/                        # ← DATA SUCIA (ya extraída)
│   │   ├── res_partner.csv
│   │   ├── product_template.csv
│   │   ├── stock_warehouse.csv
│   │   ├── account_move.csv
│   │   └── ...
│   │
│   └── output/                       # ← DATA LIMPIA (resultado)
│       ├── res_partner_clean.csv
│       ├── product_template_clean.csv
│       ├── stock_warehouse_clean.csv
│       │
│       ├── metadata/                 # Archivos de metadata
│       │   ├── ir_model_data.csv    # External IDs
│       │   └── sequences.json       # Valores de secuencias
│       │
│       └── reports/                  # Reportes por modelo
│           ├── res_partner_report.json
│           ├── product_template_report.json
│           └── global_summary.json
│
├── logs/                             # Logs de ejecución
│   ├── processor_20251001_143000.log
│   ├── errors.log
│   └── debug.log
│
├── src/                              # Código fuente
│   ├── __init__.py
│   │
│   ├── core/                         # Componentes núcleo
│   │   ├── __init__.py
│   │   ├── orchestrator.py           # ← ORQUESTADOR PRINCIPAL
│   │   │   # Métodos:
│   │   │   # - load_config()
│   │   │   # - execute_plan()
│   │   │   # - process_model()
│   │   │   # - generate_summary()
│   │   │
│   │   └── config_loader.py          # Carga y valida JSON
│   │       # - load()
│   │       # - validate_schema()
│   │       # - verify_input_files()
│   │
│   ├── readers/                      # Lectores de datos
│   │   ├── __init__.py
│   │   ├── csv_reader.py             # Lee CSVs
│   │   │   # - read()
│   │   │   # - read_in_chunks()
│   │   │   # - validate_columns()
│   │   │
│   │   └── json_reader.py            # Lee JSONs
│   │
│   ├── operations/                   # ← EJECUTORES DE OPERACIONES
│   │   ├── __init__.py
│   │   │
│   │   ├── operation_executor.py     # Ejecutor principal
│   │   │   # - execute_all_operations()
│   │   │
│   │   ├── op2_data_cleaning.py      # Operación 2
│   │   │   # - filter_records()
│   │   │   # - remove_duplicates()
│   │   │   # - normalize_data()
│   │   │
│   │   ├── op3_id_resequencing.py    # Operación 3
│   │   │   # - resequence_ids()
│   │   │   # - create_id_mapping()
│   │   │   # - update_foreign_keys()
│   │   │
│   │   ├── op4_metadata_generator.py # Operación 4
│   │   │   # - generate_external_ids()
│   │   │   # - create_metadata_file()
│   │   │
│   │   └── op5_m2m_handler.py        # Operación 5
│   │       # - process_m2m_relations()
│   │       # - update_relation_ids()
│   │
│   ├── exporters/                    # Exportadores
│   │   ├── __init__.py
│   │   ├── csv_exporter.py           # Exporta CSVs limpios
│   │   │   # - export_to_csv()
│   │   │   # - format_fields()
│   │   │
│   │   └── report_generator.py       # Genera reportes
│   │       # - generate_model_report()
│   │       # - generate_global_summary()
│   │
│   ├── validators/                   # Validadores
│   │   ├── __init__.py
│   │   ├── data_validator.py         # Valida datos
│   │   │   # - validate_record()
│   │   │   # - validate_foreign_keys()
│   │   │   # - validate_data_types()
│   │   │
│   │   └── integrity_checker.py      # Verifica integridad
│   │       # - check_referential_integrity()
│   │       # - check_duplicates()
│   │
│   └── utils/                        # Utilidades
│       ├── __init__.py
│       ├── logger.py                 # Sistema de logging
│       ├── helpers.py                # Funciones auxiliares
│       └── progress_tracker.py       # Seguimiento de progreso
│
├── scripts/                          # Scripts de ejecución
│   ├── run_processor.py              # ← SCRIPT PRINCIPAL
│   │   # Uso:
│   │   # python scripts/run_processor.py --config config/models_config.json
│   │
│   ├── validate_config.py            # Valida configuración
│   ├── validate_input_files.py       # Valida archivos de entrada
│   ├── generate_config_template.py   # Genera template de config
│   └── compare_before_after.py       # Compara input vs output
│
├── tests/                            # Tests
│   ├── __init__.py
│   │
│   ├── unit/                         # Tests unitarios
│   │   ├── test_config_loader.py
│   │   ├── test_csv_reader.py
│   │   ├── test_id_resequencer.py
│   │   ├── test_data_cleaning.py
│   │   └── test_csv_exporter.py
│   │
│   ├── integration/                  # Tests de integración
│   │   ├── test_full_pipeline.py
│   │   └── test_orchestrator.py
│   │
│   └── fixtures/                     # Datos de prueba
│       ├── sample_input.csv
│       ├── sample_config.json
│       └── expected_output.csv
│
└── docs/                             # Documentación
    ├── architecture.md               # Arquitectura del sistema
    ├── configuration_guide.md        # Guía de configuración
    ├── operations_reference.md       # Referencia de operaciones
    ├── user_guide.md                 # Guía de usuario
    │
    └── examples/                     # Ejemplos
        ├── example_basic.md
        └── example_advanced.md
```

---

## 📄 ESTRUCTURA JSON DE CONFIGURACIÓN

### Archivo: `config/models_config.json`

```json
{
  "global_settings": {
    "input_directory": "data/input",
    "output_directory": "data/output",
    "external_id_module": "marin_data",
    "log_level": "INFO",
    "stop_on_error": true,
    "generate_reports": true
  },

  "execution_plan": [
    {
      "model_name": "res.partner",
      "description": "Procesamiento de contactos y empresas",
      "enabled": true,
      "priority": 1,

      "input": {
        "file": "res_partner.csv",
        "encoding": "utf-8",
        "delimiter": ",",
        "has_header": true
      },

      "operations": {
        "data_cleaning": {
          "enabled": true,
          "filters": [
            {
              "type": "condition",
              "field": "active",
              "operator": "==",
              "value": true
            },
            {
              "type": "not_null",
              "fields": ["name", "email"]
            }
          ],
          "deduplicate": {
            "enabled": true,
            "key_fields": ["email", "vat"],
            "keep": "first"
          },
          "normalize": {
            "email": "lowercase",
            "name": "title_case",
            "phone": "format_phone"
          }
        },

        "resequence_ids": {
          "enabled": true,
          "start_id": 1,
          "order_by": ["id"],
          "keep_original_id": true
        },

        "generate_metadata": {
          "enabled": true,
          "module": "marin_data",
          "name_template": "partner_{id}",
          "include_all": true
        },

        "m2m_relationships": [
          {
            "relation_file": "res_partner_category_rel.csv",
            "column1": "partner_id",
            "column2": "category_id",
            "output_file": "res_partner_category_rel_clean.csv"
          }
        ]
      },

      "export": {
        "enabled": true,
        "output_file": "res_partner_clean.csv",
        "fields": [
          "id",
          "external_id",
          "id_original",
          "name",
          "ref",
          "email",
          "phone",
          "mobile",
          "vat",
          "street",
          "city",
          "zip",
          "country_id",
          "state_id",
          "parent_id",
          "category_id",
          "is_company",
          "active"
        ],
        "include_metadata": true
      }
    },

    {
      "model_name": "product.template",
      "description": "Procesamiento de plantillas de productos",
      "enabled": true,
      "priority": 2,

      "input": {
        "file": "product_template.csv",
        "encoding": "utf-8"
      },

      "operations": {
        "data_cleaning": {
          "enabled": true,
          "filters": [
            {
              "type": "not_null",
              "fields": ["name", "default_code"]
            }
          ],
          "deduplicate": {
            "enabled": true,
            "key_fields": ["default_code"],
            "keep": "first"
          }
        },

        "resequence_ids": {
          "enabled": true,
          "start_id": 1000,
          "order_by": ["id"]
        },

        "generate_metadata": {
          "enabled": true,
          "module": "marin_data",
          "name_template": "product_template_{id}"
        }
      },

      "export": {
        "enabled": true,
        "output_file": "product_template_clean.csv",
        "fields": [
          "id",
          "external_id",
          "name",
          "default_code",
          "barcode",
          "list_price",
          "standard_price",
          "categ_id",
          "uom_id",
          "uom_po_id",
          "type",
          "active"
        ]
      }
    },

    {
      "model_name": "stock.warehouse",
      "description": "Procesamiento de almacenes",
      "enabled": true,
      "priority": 3,

      "input": {
        "file": "stock_warehouse.csv"
      },

      "operations": {
        "resequence_ids": {
          "enabled": true,
          "start_id": 1,
          "order_by": ["id"]
        },

        "generate_metadata": {
          "enabled": true,
          "module": "marin_data",
          "name_template": "warehouse_{id}"
        }
      },

      "export": {
        "enabled": true,
        "output_file": "stock_warehouse_clean.csv",
        "fields": [
          "id",
          "external_id",
          "name",
          "code",
          "company_id",
          "partner_id"
        ]
      }
    }
  ]
}
```

---

## 🔧 COMPONENTES DEL SISTEMA

### 1. Orchestrator (`src/core/orchestrator.py`)

**Responsabilidad:** Coordinar todo el flujo de procesamiento

```python
class DataMasterProcessor:
    def __init__(self, config_path: str):
        self.config = ConfigLoader().load(config_path)
        self.stats = {}

    def execute_plan(self):
        """Ejecuta el plan completo de procesamiento"""
        logger.info("Iniciando procesamiento de data maestra...")

        for model_config in self.config['execution_plan']:
            if not model_config['enabled']:
                continue

            try:
                self._process_model(model_config)
            except Exception as e:
                logger.error(f"Error en {model_config['model_name']}: {e}")
                if self.config['global_settings']['stop_on_error']:
                    raise

        self._generate_global_summary()

    def _process_model(self, model_config: dict):
        """Procesa un modelo individual"""
        model_name = model_config['model_name']
        logger.info(f"Procesando modelo: {model_name}")

        # 1. Cargar data sucia
        input_file = os.path.join(
            self.config['global_settings']['input_directory'],
            model_config['input']['file']
        )
        registros = CSVReader().read(input_file)
        logger.info(f"Cargados {len(registros)} registros de {input_file}")

        # 2. Ejecutar operaciones
        executor = OperationExecutor()
        registros_limpios, id_map = executor.execute_all_operations(
            registros,
            model_config['operations']
        )
        logger.info(f"Procesados {len(registros_limpios)} registros limpios")

        # 3. Exportar data limpia
        if model_config['export']['enabled']:
            output_file = os.path.join(
                self.config['global_settings']['output_directory'],
                model_config['export']['output_file']
            )
            CSVExporter().export_to_csv(
                registros_limpios,
                output_file,
                model_config['export']['fields']
            )
            logger.info(f"Exportado a {output_file}")

        # 4. Generar reporte del modelo
        if self.config['global_settings']['generate_reports']:
            self._generate_model_report(model_name, registros, registros_limpios)
```

### 2. OperationExecutor (`src/operations/operation_executor.py`)

**Responsabilidad:** Ejecutar las operaciones de limpieza

```python
class OperationExecutor:
    def execute_all_operations(self, registros: list, operations: dict) -> tuple:
        """Ejecuta todas las operaciones configuradas"""

        # Op 2: Data Cleaning
        if operations.get('data_cleaning', {}).get('enabled'):
            registros = DataCleaner().clean(
                registros,
                operations['data_cleaning']
            )

        # Op 3: ID Resequencing
        id_map = {}
        if operations.get('resequence_ids', {}).get('enabled'):
            registros, id_map = IDResequencer().resequence(
                registros,
                operations['resequence_ids']
            )

        # Op 4: Metadata Generation
        if operations.get('generate_metadata', {}).get('enabled'):
            registros = MetadataGenerator().generate(
                registros,
                operations['generate_metadata']
            )

        # Op 5: M2M Handling
        if operations.get('m2m_relationships'):
            M2MHandler().process_relations(
                operations['m2m_relationships'],
                id_map
            )

        return registros, id_map
```

### 3. CSVReader (`src/readers/csv_reader.py`)

```python
class CSVReader:
    def read(self, file_path: str, encoding='utf-8') -> list:
        """Lee un archivo CSV y retorna lista de diccionarios"""
        import csv

        records = []
        with open(file_path, 'r', encoding=encoding) as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)

        logger.info(f"Leídos {len(records)} registros de {file_path}")
        return records
```

### 4. CSVExporter (`src/exporters/csv_exporter.py`)

```python
class CSVExporter:
    def export_to_csv(self, records: list, output_file: str, fields: list):
        """Exporta registros a CSV"""
        import csv

        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()

            for record in records:
                # Filtrar solo campos configurados
                row = {k: record.get(k, '') for k in fields}
                writer.writerow(row)

        logger.info(f"Exportados {len(records)} registros a {output_file}")
```

---

## 📝 DESCRIPCIÓN DE LAS 6 OPERACIONES

### Operación 1: FK Redefinition
**Estado:** SKIP en procesamiento CSV (aplicable solo en BD)
**Alternativa:** Validar integridad referencial

### Operación 2: Data Cleaning ✅
- Filtrado de registros por condiciones
- Eliminación de duplicados
- Normalización de datos
- Limpieza de campos

### Operación 3: ID Resequencing ✅
- Ordenamiento de registros
- Creación de mapeo old_id → new_id
- Asignación de IDs consecutivos
- Actualización de FKs

### Operación 4: Metadata Generation ✅
- Generación de External IDs
- Creación de archivo ir_model_data.csv
- Formato: module.model_id

### Operación 5: M2M Handling ✅
- Procesamiento de archivos de relación M2M
- Actualización de IDs con mapeo
- Exportación de relaciones limpias

### Operación 6: Sequence Update
**Estado:** SKIP en procesamiento CSV (aplicable solo en BD)
**Alternativa:** Generar archivo sequences.json

---

## 🚀 EJEMPLO DE EJECUCIÓN

### Comando Principal

```bash
# Ejecución completa
python scripts/run_processor.py \
  --config config/models_config.json

# Con opciones
python scripts/run_processor.py \
  --config config/models_config.json \
  --log-level DEBUG \
  --verbose

# Validar configuración antes
python scripts/validate_config.py \
  --config config/models_config.json

# Validar archivos de entrada
python scripts/validate_input_files.py \
  --config config/models_config.json
```

### Salida Esperada

```
============================================================
INICIANDO PROCESAMIENTO DE DATA MAESTRA
============================================================
[14:30:00] [INFO] Cargando configuración...
[14:30:01] [INFO] Modelos a procesar: 15

─────────────────────────────────────────────────────────
Procesando modelo 1/15: res.partner
─────────────────────────────────────────────────────────
[14:30:02] [INFO] Cargados 8,590 registros
[14:30:03] [INFO] Operación 2: Data Cleaning
[14:30:05] [INFO]   ✓ 250 registros filtrados
[14:30:05] [INFO]   ✓ 15 duplicados eliminados
[14:30:05] [INFO]   ✓ Datos normalizados
[14:30:06] [INFO] Operación 3: ID Resequencing
[14:30:08] [INFO]   ✓ 8,325 IDs re-secuenciados
[14:30:08] [INFO] Operación 4: Metadata Generation
[14:30:10] [INFO]   ✓ 8,325 External IDs generados
[14:30:10] [INFO] Exportando a CSV...
[14:30:12] [INFO]   ✓ Exportado: data/output/res_partner_clean.csv
[14:30:12] [INFO] Modelo res.partner completado ✓

============================================================
RESUMEN GLOBAL
============================================================
Modelos procesados: 15 / 15
Registros totales: 45,230
Registros limpios: 44,100
External IDs creados: 44,100

Tiempo total: 2m 15s
Estado: ✓ EXITOSO
============================================================
```

---

## 📅 PLAN DE IMPLEMENTACIÓN

### Fase 1: Setup Inicial (3 días)
- ✅ Crear estructura de directorios
- ✅ Configurar entorno virtual
- ✅ Instalar dependencias
- ✅ Crear ConfigLoader básico
- ✅ Crear sistema de logging

### Fase 2: Lectores y Exportadores (3 días)
- ✅ CSVReader completo
- ✅ CSVExporter completo
- ✅ Validadores básicos
- ✅ Tests unitarios

### Fase 3: Operaciones Básicas (5 días)
- ✅ Operación 2: Data Cleaning
- ✅ Operación 3: ID Resequencing
- ✅ Tests con datos reales

### Fase 4: Metadata y M2M (3 días)
- ✅ Operación 4: Metadata Generation
- ✅ Operación 5: M2M Handling
- ✅ Tests de integración

### Fase 5: Orchestrator y Reporting (3 días)
- ✅ Orchestrator completo
- ✅ Sistema de reportes
- ✅ Generación de resumen global

### Fase 6: Testing y Documentación (3 días)
- ✅ Tests de integración completos
- ✅ Documentación de usuario
- ✅ Ejemplos de uso

**Duración total: 20 días (4 semanas)**

---

**Versión:** 1.0
**Fecha:** 2025-10-01
**Estado:** ✅ Listo para desarrollo
**Output Final:** Data maestra validada, limpia y lista para importar a BD Odoo
