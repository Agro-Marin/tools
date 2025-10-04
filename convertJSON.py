#!/usr/bin/env python3
"""
convertJSON.py
Convierte archivos .py de acciones_servidor a configuración JSON
Basado en Plan de Desarrollo v3.2
"""

import os
import re
import json
from pathlib import Path
import ast

def parse_python_file(file_path):
    """Extrae patrones SQL y reglas de un archivo .py"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    model_config = {
        'foreign_keys': [],
        'cascade_rules': [],
        'cleanup_rules': {},
        'naming_rules': {},
        'resequence_rules': {}
    }

    # Extraer la lista queries usando ast
    try:
        tree = ast.parse(content)
        queries_list = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'queries':
                        if isinstance(node.value, ast.List):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant):
                                    queries_list.append(elt.value)

        # Procesar cada query
        for query in queries_list:
            if not query:
                continue

            # 1. Extraer CASCADE constraints
            # Patrón: ALTER TABLE res_partner ADD CONSTRAINT "res_partner_parent_id_fkey"
            #         FOREIGN KEY (parent_id) REFERENCES res_partner(id)
            #         ON DELETE CASCADE ON UPDATE CASCADE
            cascade_pattern = r'ALTER TABLE\s+(\w+)\s+ADD\s+CONSTRAINT\s+"([^"]+)"\s+FOREIGN KEY\s+\([^)]+\)\s+REFERENCES\s+"[^"]*"\."(\w+)"\s+\([^)]+\)\s+ON DELETE\s+(CASCADE|SET NULL|RESTRICT)\s+ON UPDATE\s+(CASCADE|RESTRICT)'

            match = re.search(cascade_pattern, query, re.IGNORECASE | re.DOTALL)

            if match:
                table_name = match.group(1)
                constraint_name = match.group(2)
                ref_table = match.group(3)
                on_delete = match.group(4)
                on_update = match.group(5)

                model_config['cascade_rules'].append({
                    'table': table_name,
                    'constraint': constraint_name,
                    'ref_table': ref_table,
                    'on_delete': on_delete,
                    'on_update': on_update
                })

            # 2. Extraer DELETE con WHERE
            delete_pattern = r'DELETE FROM\s+(\w+)\s+WHERE\s+(.+?);'
            delete_match = re.search(delete_pattern, query, re.IGNORECASE | re.DOTALL)

            if delete_match:
                table = delete_match.group(1)
                where_clause = delete_match.group(2).strip()

                if 'delete_conditions' not in model_config['cleanup_rules']:
                    model_config['cleanup_rules']['delete_conditions'] = []

                model_config['cleanup_rules']['delete_conditions'].append({
                    'table': table,
                    'where': where_clause
                })

            # 3. Extraer reglas de resecuenciación (UPDATE id =)
            reseq_pattern = r'UPDATE\s+(\w+)\s+SET\s+id\s*=\s*(\d+)'
            reseq_match = re.search(reseq_pattern, query, re.IGNORECASE)

            if reseq_match:
                start_id = int(reseq_match.group(2))
                if 'start_id' not in model_config['resequence_rules']:
                    model_config['resequence_rules']['start_id'] = start_id

            # 4. Extraer reglas de naming (UPDATE ... SET name/code = CONCAT)
            naming_pattern = r"UPDATE\s+(\w+)\s+SET\s+(name|code)\s*=\s*CONCAT\(['\"](.+?)['\"]\s*,\s*['\"](.+?)['\"]\)"
            naming_match = re.search(naming_pattern, query, re.IGNORECASE)

            if naming_match:
                field = naming_match.group(2)
                model_config['naming_rules']['field'] = field
                model_config['naming_rules']['pattern'] = naming_match.group(3) + naming_match.group(4)
                model_config['naming_rules']['replace_dots'] = True

    except Exception as e:
        print(f"   ⚠️  Error parseando {file_path.name}: {e}")

    return model_config


def determine_execution_order(models_data):
    """Determina orden de ejecución basado en dependencias FK"""

    # Orden predefinido basado en dependencias conocidas (líneas 463-480 del documento)
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
    print("║  Versión 3.2                                             ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    acciones_dir = Path('utils/acciones_servidor')

    if not acciones_dir.exists():
        print(f"❌ Directorio no encontrado: {acciones_dir}")
        return

    models_data = {}
    file_count = 0

    # Procesar cada archivo .py
    for py_file in sorted(acciones_dir.glob('*.py')):
        file_count += 1
        print(f"📄 Procesando [{file_count:02d}]: {py_file.name}")

        # Extraer nombre del modelo del nombre del archivo
        file_stem = py_file.stem

        # Mapeo especial de nombres (corregir typos y casos especiales)
        if file_stem == 'company':
            model_name = 'res.company'
        elif file_stem == 'res.parthner':  # typo en archivo original
            model_name = 'res.partner'
        elif file_stem == 'res.company':
            model_name = 'res.company'
        elif file_stem == 'product':
            model_name = 'product.template'
        elif file_stem == 'uom_uom':
            model_name = 'uom.uom'
        elif file_stem == 'res_partner_category':
            model_name = 'res.partner.category'
        elif file_stem.startswith('account_') and file_stem != 'account_account':
            # account_journal, account_move, etc.
            model_name = file_stem.replace('_', '.', 1)
        elif file_stem.startswith('stock_'):
            model_name = file_stem.replace('_', '.', 1)
        elif '.' in file_stem:
            model_name = file_stem  # ya tiene el formato correcto
        else:
            # Por defecto convertir _ a .
            model_name = file_stem.replace('_', '.')

        # Nombre de tabla (siempre con _)
        table_name = model_name.replace('.', '_')

        # Parsear archivo
        config = parse_python_file(py_file)

        # Construir configuración del modelo
        models_data[model_name] = {
            'table_name': table_name,
            **config
        }

        # Reglas especiales para account.account (líneas 516-518)
        if model_name == 'account.account':
            models_data[model_name]['naming_rules']['use_account_code'] = True
            models_data[model_name]['naming_rules']['replace_dots'] = True
            models_data[model_name]['naming_rules']['field'] = 'code'

        # Si no tiene start_id, asignar uno por defecto
        if 'start_id' not in models_data[model_name]['resequence_rules']:
            # IDs por defecto según el documento
            default_ids = {
                'res.company': 1,
                'res.partner': 8590,
                'product.category': 1000,
                'product.template': 2000,
                'product.product': 3000,
                'account.account': 4000,
                'account.journal': 5000,
                'stock.warehouse': 6000,
                'account.move': 10000,
                'account.move.line': 11000,
                'stock.location': 7000,
                'stock.picking.type': 8000
            }
            models_data[model_name]['resequence_rules']['start_id'] = default_ids.get(model_name, 1000)

        # Agregar naming_rules por defecto si no existe
        if not models_data[model_name]['naming_rules']:
            if model_name != 'account.account':
                models_data[model_name]['naming_rules'] = {
                    'pattern': f"{model_name}_{{id}}",
                    'replace_dots': True
                }

    # Determinar orden de ejecución
    execution_order = determine_execution_order(models_data)

    # Construir JSON final (estructura líneas 1110-1186)
    final_config = {
        'execution_order': execution_order,
        'models': models_data,
        'global_settings': {
            'output_directory': 'output/statistics',
            'log_directory': 'output/logs',
            'require_where_in_delete': True,
            'use_cascade': True,
            'disable_triggers': False,
            'batch_size': 1000,
            'transaction_per_model': True
        }
    }

    # Escribir JSON
    output_file = 'models_config.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_config, f, indent=2, ensure_ascii=False)

    print(f"\n✅ JSON generado: {output_file}")
    print(f"   📊 Modelos procesados: {len(models_data)}")
    print(f"   📋 Orden de ejecución: {len(execution_order)} modelos")
    print(f"\n   Orden: {' → '.join(execution_order[:5])}{'...' if len(execution_order) > 5 else ''}")

    # Mostrar estadísticas de reglas extraídas
    total_cascade = sum(len(m.get('cascade_rules', [])) for m in models_data.values())
    total_deletes = sum(len(m.get('cleanup_rules', {}).get('delete_conditions', [])) for m in models_data.values())

    print(f"\n   📌 CASCADE rules extraídas: {total_cascade}")
    print(f"   📌 DELETE rules extraídas: {total_deletes}")
    print(f"\n✓ Conversión completada exitosamente\n")


if __name__ == '__main__':
    convert_to_json()
