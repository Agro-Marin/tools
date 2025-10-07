#!/usr/bin/env python3
"""
convertJSON.py - Versión 3.3
Generador mejorado de configuración para resecuenciación con CASCADE
Extrae todas las reglas de las acciones de servidor
"""

import os
import re
import json
from pathlib import Path
import ast

def parse_python_file(file_path):
    """
    Extrae patrones SQL y reglas de un archivo .py
    Versión mejorada: captura DELETE sin WHERE, resecuenciación custom, etc.
    """

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    model_config = {
        'cascade_rules': [],
        'cleanup_rules': {
            'delete_with_where': [],
            'delete_unsafe': []  # DELETE sin WHERE
        },
        'naming_rules': {},
        'resequence_rules': {},
        'custom_operations': []  # Para lógica Python personalizada
    }

    # Extraer la lista de queries usando AST
    # Intentar múltiples nombres de variables: queries, query, lista
    try:
        tree = ast.parse(content)
        queries_list = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    # Buscar variables: queries, query, lista
                    if isinstance(target, ast.Name) and target.id in ['queries', 'query', 'lista']:
                        if isinstance(node.value, ast.List):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant):
                                    queries_list.append(elt.value)

        # Procesar cada query
        for query in queries_list:
            if not query:
                continue

            # ══════════════════════════════════════════════════════════
            # 1. EXTRAER CASCADE CONSTRAINTS
            # ══════════════════════════════════════════════════════════
            # Patrón: ALTER TABLE table ADD CONSTRAINT "name"
            #         FOREIGN KEY (col) REFERENCES "schema"."ref_table" (id)
            #         ON DELETE [CASCADE|SET NULL|RESTRICT] ON UPDATE CASCADE

            cascade_pattern = r'ALTER TABLE\s+(\w+)\s+ADD\s+CONSTRAINT\s+"([^"]+)"\s+FOREIGN KEY\s+\(([^)]+)\)\s+REFERENCES\s+"[^"]*"\."?(\w+)"?\s+\([^)]+\)\s+ON DELETE\s+(CASCADE|SET NULL|RESTRICT)\s+ON UPDATE\s+(CASCADE|RESTRICT)'

            match = re.search(cascade_pattern, query, re.IGNORECASE | re.DOTALL)

            if match:
                table_name = match.group(1)
                constraint_name = match.group(2)
                fk_column = match.group(3).strip('"')  # Capturar la columna FK
                ref_table = match.group(4)
                on_delete = match.group(5)
                on_update = match.group(6)

                model_config['cascade_rules'].append({
                    'table': table_name,
                    'constraint': constraint_name,
                    'fk_column': fk_column,  # NUEVO: columna FK explícita
                    'ref_table': ref_table,
                    'on_delete': on_delete,
                    'on_update': on_update
                })

            # ══════════════════════════════════════════════════════════
            # 2. EXTRAER DELETE CON WHERE
            # ══════════════════════════════════════════════════════════
            delete_where_pattern = r'DELETE FROM\s+(\w+)\s+WHERE\s+(.+?)(?:;|$)'
            delete_where_match = re.search(delete_where_pattern, query, re.IGNORECASE | re.DOTALL)

            if delete_where_match:
                table = delete_where_match.group(1)
                where_clause = delete_where_match.group(2).strip()

                model_config['cleanup_rules']['delete_with_where'].append({
                    'table': table,
                    'where': where_clause
                })

            # ══════════════════════════════════════════════════════════
            # 3. EXTRAER DELETE SIN WHERE (UNSAFE)
            # ══════════════════════════════════════════════════════════
            # Patrón: DELETE FROM tabla (sin WHERE)
            delete_unsafe_pattern = r'DELETE FROM\s+(\w+)\s*(?:;|$)'

            # Solo si NO tiene WHERE
            if 'WHERE' not in query.upper() and re.search(delete_unsafe_pattern, query, re.IGNORECASE):
                delete_unsafe_match = re.search(delete_unsafe_pattern, query, re.IGNORECASE)
                if delete_unsafe_match:
                    table = delete_unsafe_match.group(1)

                    model_config['cleanup_rules']['delete_unsafe'].append({
                        'table': table,
                        'warning': 'DELETE sin WHERE - limpia toda la tabla'
                    })

            # ══════════════════════════════════════════════════════════
            # 4. EXTRAER RESECUENCIACIÓN (UPDATE id = valor)
            # ══════════════════════════════════════════════════════════
            # Patrón: UPDATE tabla SET id=valor WHERE id=otro_valor
            reseq_pattern = r'UPDATE\s+(\w+)\s+SET\s+id\s*=\s*(\d+)\s+WHERE\s+id\s*=\s*(\d+)'
            reseq_match = re.search(reseq_pattern, query, re.IGNORECASE)

            if reseq_match:
                table = reseq_match.group(1)
                new_id = int(reseq_match.group(2))
                old_id = int(reseq_match.group(3))

                if 'id_mappings' not in model_config['resequence_rules']:
                    model_config['resequence_rules']['id_mappings'] = []

                model_config['resequence_rules']['id_mappings'].append({
                    'old_id': old_id,
                    'new_id': new_id
                })

            # ══════════════════════════════════════════════════════════
            # 5. EXTRAER NAMING RULES (UPDATE SET name/code = CONCAT)
            # ══════════════════════════════════════════════════════════
            naming_pattern = r"UPDATE\s+(\w+)\s+SET\s+(name|code)\s*=\s*CONCAT\(['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\)"
            naming_match = re.search(naming_pattern, query, re.IGNORECASE)

            if naming_match:
                field = naming_match.group(2)
                model_config['naming_rules']['field'] = field
                model_config['naming_rules']['pattern'] = naming_match.group(3) + naming_match.group(4)
                model_config['naming_rules']['replace_dots'] = True

        # ══════════════════════════════════════════════════════════
        # 6. DETECTAR LÓGICA PYTHON PERSONALIZADA
        # ══════════════════════════════════════════════════════════
        # Buscar patrones como: fix_id = 2453, bucles FOR, etc.

        # Patrón: fix_id = número
        fix_id_pattern = r'fix_id\s*=\s*(\d+)'
        fix_id_match = re.search(fix_id_pattern, content)

        if fix_id_match:
            fix_id = int(fix_id_match.group(1))
            model_config['resequence_rules']['start_id'] = fix_id
            model_config['custom_operations'].append({
                'type': 'resequence_from_id',
                'start_id': fix_id,
                'description': 'Resecuenciación secuencial desde start_id'
            })

        # Detectar si usa env.cr.execute con bucles FOR
        if 'for r in records:' in content and 'UPDATE' in content and 'SET id=' in content:
            model_config['custom_operations'].append({
                'type': 'python_loop_resequencing',
                'description': 'Resecuenciación con bucle Python'
            })

        # Detectar creación de ir.model.data
        if 'ir.model.data' in content and 'create' in content:
            model_config['custom_operations'].append({
                'type': 'create_model_data',
                'description': 'Crear registros en ir_model_data'
            })

        # Detectar setval de secuencias
        if 'setval' in content:
            model_config['custom_operations'].append({
                'type': 'reset_sequence',
                'description': 'Resetear secuencia PostgreSQL'
            })

    except SyntaxError as e:
        print(f"   ⚠️  Error de sintaxis en {file_path.name}: línea {e.lineno}")
        return model_config
    except Exception as e:
        print(f"   ⚠️  Error parseando {file_path.name}: {e}")
        return model_config

    return model_config


def determine_execution_order(models_data):
    """
    Determina orden de ejecución basado en dependencias FK
    ORDEN CRÍTICO: Tablas padre primero, hijos después
    """

    # Orden predefinido basado en análisis de dependencias
    # Este orden garantiza que CASCADE funcione correctamente
    base_order = [
        # NIVEL 1: Sin dependencias (raíz)
        'res.company',

        # NIVEL 2: Dependen de company
        'res.partner',
        'product.category',

        # NIVEL 3: Dependen de partner/category
        'product.template',
        'product.product',
        'account.account',
        'account.journal',
        'stock.location',
        'stock.warehouse',

        # NIVEL 4: Contabilidad
        'account.tax',
        'account.payment.term',
        'account.analytic',
        'account.asset',

        # NIVEL 5: Movimientos
        'account.move',
        'account.move.line',
        'account.bank_statement',
        'account.bank_statement_line',

        # NIVEL 6: Stock
        'stock.picking.type',
        'stock.picking',
        'stock.move',
        'stock.lot',
        'stock.quant',
        'stock.route_rule',

        # NIVEL 7: Ventas/CRM/Fleet
        'sale',
        'crm',
        'fleet',
        'hr',
        'mrp.bom',
        'pos',

        # NIVEL 8: Consolidación y otros
        'consolidation',
        'res.partner.category',
        'uom.uom',

        # ÚLTIMO: Modelos sin dependencias claras
        'wizard.models'
    ]

    # Filtrar solo modelos que existen
    execution_order = []

    for model in base_order:
        if model in models_data:
            execution_order.append(model)

    # Agregar modelos no listados al final
    for model in sorted(models_data.keys()):
        if model not in execution_order:
            execution_order.append(model)

    return execution_order


def convert_to_json():
    """Función principal de conversión"""

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  convertJSON.py - Generador de Configuración            ║")
    print("║  Versión 3.3 - Mejorado para CASCADE + Resecuenciación  ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    acciones_dir = Path('utils/acciones_servidor')

    if not acciones_dir.exists():
        print(f"❌ Directorio no encontrado: {acciones_dir}")
        return

    models_data = {}
    file_count = 0
    syntax_errors = []

    # Procesar cada archivo .py
    for py_file in sorted(acciones_dir.glob('*.py')):
        file_count += 1
        print(f"📄 Procesando [{file_count:02d}]: {py_file.name}")

        # ══════════════════════════════════════════════════════════
        # MAPEO DE NOMBRES DE ARCHIVO → MODELO
        # ══════════════════════════════════════════════════════════
        file_stem = py_file.stem

        # Ignorar archivos especiales
        if file_stem.startswith('Set ') or file_stem.startswith('_'):
            print(f"   ⊘ Ignorando archivo especial: {py_file.name}")
            continue

        # Mapeo de nombres
        model_mapping = {
            'company': 'res.company',
            'res.parthner': 'res.partner',  # typo en archivo
            'res.company': 'res.company',
            'product': 'product.template',
            'uom_uom': 'uom.uom',
            'res_partner_category': 'res.partner.category',
            'mrp_bom': 'mrp.bom',
        }

        # Aplicar mapeo
        if file_stem in model_mapping:
            model_name = model_mapping[file_stem]
        elif file_stem.startswith('account_') and file_stem != 'account_account':
            # account_journal → account.journal
            model_name = file_stem.replace('_', '.', 1)
        elif file_stem.startswith('stock_'):
            # stock_location → stock.location
            model_name = file_stem.replace('_', '.', 1)
        elif '.' in file_stem:
            model_name = file_stem
        else:
            # Conversión por defecto: _ → .
            model_name = file_stem.replace('_', '.')

        # Nombre de tabla (siempre con _)
        table_name = model_name.replace('.', '_')

        # ══════════════════════════════════════════════════════════
        # PARSEAR ARCHIVO
        # ══════════════════════════════════════════════════════════
        config = parse_python_file(py_file)

        # Construir configuración del modelo
        models_data[model_name] = {
            'table_name': table_name,
            'source_file': py_file.name,  # NUEVO: tracking del archivo origen
            **config
        }

        # ══════════════════════════════════════════════════════════
        # REGLAS ESPECIALES POR MODELO
        # ══════════════════════════════════════════════════════════

        # account.account: usa código contable, no ID
        if model_name == 'account.account':
            models_data[model_name]['naming_rules'] = {
                'use_account_code': True,
                'replace_dots': True,
                'field': 'code'
            }

        # ══════════════════════════════════════════════════════════
        # ASIGNAR start_id POR DEFECTO
        # ══════════════════════════════════════════════════════════
        if 'start_id' not in models_data[model_name]['resequence_rules']:
            # IDs por defecto basados en análisis de las acciones
            default_ids = {
                'res.company': 1,
                'res.partner': 8590,
                'product.category': 1000,
                'product.template': 2000,
                'product.product': 3000,
                'account.account': 4000,
                'account.journal': 5000,
                'account.move': 10000,
                'account.move.line': 11000,
                'stock.warehouse': 6000,
                'stock.location': 7000,
                'stock.picking.type': 8000,
            }
            models_data[model_name]['resequence_rules']['start_id'] = default_ids.get(model_name, 1000)

        # ══════════════════════════════════════════════════════════
        # NAMING RULES POR DEFECTO
        # ══════════════════════════════════════════════════════════
        if not models_data[model_name]['naming_rules']:
            if model_name != 'account.account':
                models_data[model_name]['naming_rules'] = {
                    'pattern': f"{model_name}_{{id}}",
                    'replace_dots': True,
                    'field': 'name'
                }

    # ══════════════════════════════════════════════════════════
    # DETERMINAR ORDEN DE EJECUCIÓN
    # ══════════════════════════════════════════════════════════
    execution_order = determine_execution_order(models_data)

    # ══════════════════════════════════════════════════════════
    # CONSTRUIR JSON FINAL
    # ══════════════════════════════════════════════════════════
    final_config = {
        'version': '3.3',
        'description': 'Configuración para resecuenciación con CASCADE',
        'execution_order': execution_order,
        'models': models_data,
        'global_settings': {
            'output_directory': 'output/statistics',
            'log_directory': 'output/logs',
            'require_where_in_delete': True,  # Validar WHERE en DELETE
            'use_cascade': True,  # Usar CASCADE para propagar cambios
            'disable_triggers': False,  # NUNCA deshabilitar triggers
            'batch_size': 1000,
            'transaction_per_model': True,  # Una transacción por modelo
            'validate_fk_integrity': True  # Validar integridad FK después
        }
    }

    # ══════════════════════════════════════════════════════════
    # ESCRIBIR JSON
    # ══════════════════════════════════════════════════════════
    output_file = 'models_config.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_config, f, indent=2, ensure_ascii=False)

    # ══════════════════════════════════════════════════════════
    # ESTADÍSTICAS
    # ══════════════════════════════════════════════════════════
    print(f"\n✅ JSON generado: {output_file}")
    print(f"   📊 Modelos procesados: {len(models_data)}")
    print(f"   📋 Orden de ejecución: {len(execution_order)} modelos")
    print(f"\n   Orden: {' → '.join(execution_order[:5])}{'...' if len(execution_order) > 5 else ''}")

    # Estadísticas de reglas extraídas
    total_cascade = sum(len(m.get('cascade_rules', [])) for m in models_data.values())
    total_delete_safe = sum(len(m.get('cleanup_rules', {}).get('delete_with_where', [])) for m in models_data.values())
    total_delete_unsafe = sum(len(m.get('cleanup_rules', {}).get('delete_unsafe', [])) for m in models_data.values())
    total_custom_ops = sum(len(m.get('custom_operations', [])) for m in models_data.values())

    print(f"\n   📌 CASCADE rules: {total_cascade}")
    print(f"   📌 DELETE con WHERE: {total_delete_safe}")
    print(f"   ⚠️  DELETE sin WHERE: {total_delete_unsafe}")
    print(f"   🔧 Operaciones custom: {total_custom_ops}")

    # Modelos con operaciones custom
    models_with_custom = [name for name, data in models_data.items() if data.get('custom_operations')]
    if models_with_custom:
        print(f"\n   🔍 Modelos con lógica personalizada:")
        for model in models_with_custom[:5]:
            ops = models_data[model]['custom_operations']
            print(f"      • {model}: {len(ops)} operaciones")

    print(f"\n✓ Conversión completada exitosamente\n")


if __name__ == '__main__':
    convert_to_json()
