#!/usr/bin/env python3
"""
Run.py
Script principal de procesamiento de base de datos
Basado en Plan de Desarrollo v3.2
"""

import psycopg2
import json
import os
import sys
from datetime import datetime
import logging
from pathlib import Path

# ══════════════════════════════════════════════════════════════
#                    CARGA DE CREDENCIALES
# ══════════════════════════════════════════════════════════════

def load_credentials():
    """Carga credenciales desde config/db_credentials.json"""
    cred_file = 'config/db_credentials.json'

    if not os.path.exists(cred_file):
        raise FileNotFoundError(f"❌ Credenciales no encontradas: {cred_file}")

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

        conn.autocommit = False  # Transacciones manuales
        logging.info(f"✓ Conectado a: {credentials['database']} @ {credentials['host']}")
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
        raise FileNotFoundError(f"❌ Configuración no encontrada: {config_file}")

    with open(config_file, 'r') as f:
        return json.load(f)

# ══════════════════════════════════════════════════════════════
#                    PASO 1: CASCADE
# ══════════════════════════════════════════════════════════════

def apply_cascade(conn, model_config, model_name):
    """Aplica CASCADE a foreign keys"""
    cur = conn.cursor()

    cascade_rules = model_config.get('cascade_rules', [])

    if not cascade_rules:
        logging.info(f"  ⊘ Sin CASCADE rules")
        return

    applied_count = 0

    for rule in cascade_rules:
        table = rule['table']
        constraint = rule['constraint']
        ref_table = rule['ref_table']
        on_delete = rule['on_delete']
        on_update = rule['on_update']

        try:
            # Verificar si el constraint existe
            cur.execute("""
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = %s AND table_name = %s
            """, (constraint, table))

            exists = cur.fetchone()

            if exists:
                # Drop constraint existente
                cur.execute(f'ALTER TABLE {table} DROP CONSTRAINT "{constraint}";')
                logging.debug(f"    - DROP constraint {constraint}")

            # Obtener información de la columna FK
            cur.execute(f"""
                SELECT kcu.column_name
                FROM information_schema.key_column_usage kcu
                WHERE kcu.constraint_name = %s
                LIMIT 1
            """, (constraint.replace('_fkey', ''),))

            result = cur.fetchone()

            # Si no encontramos la columna, extraerla del nombre del constraint
            if result:
                fk_column = result[0]
            else:
                # Intentar extraer del nombre: res_partner_parent_id_fkey -> parent_id
                parts = constraint.replace('_fkey', '').split('_')
                if len(parts) >= 2:
                    fk_column = '_'.join(parts[-2:]) if parts[-1] == 'id' else parts[-1]
                else:
                    logging.warning(f"    ⚠️  No se pudo determinar columna FK para {constraint}")
                    continue

            # Re-crear con CASCADE
            cur.execute(f"""
                ALTER TABLE {table}
                ADD CONSTRAINT "{constraint}"
                FOREIGN KEY ({fk_column})
                REFERENCES {ref_table}(id)
                ON DELETE {on_delete}
                ON UPDATE {on_update};
            """)

            applied_count += 1
            logging.debug(f"    + ADD constraint {constraint} (ON DELETE {on_delete})")

        except psycopg2.Error as e:
            logging.warning(f"    ⚠️  Error en CASCADE {constraint}: {e}")
            continue

    conn.commit()
    cur.close()

    logging.info(f"  ✓ CASCADE aplicado: {applied_count}/{len(cascade_rules)} reglas")

# ══════════════════════════════════════════════════════════════
#                    PASO 2: RESECUENCIAR IDs
# ══════════════════════════════════════════════════════════════

def resequence_ids(conn, table_name, start_id):
    """Resecuencia IDs de una tabla (CASCADE actualiza FKs automáticamente)"""
    cur = conn.cursor()

    # 1. Obtener IDs actuales
    cur.execute(f"SELECT id FROM {table_name} ORDER BY id;")
    records = cur.fetchall()

    if not records:
        logging.info(f"  ⊘ Tabla vacía, sin IDs para resecuenciar")
        cur.close()
        return {}

    # 2. Crear mapeo
    id_mapping = {}
    new_id = start_id

    for (old_id,) in records:
        if old_id != new_id:
            id_mapping[old_id] = new_id
        new_id += 1

    # 3. Actualizar IDs
    # CASCADE (ON UPDATE CASCADE) actualiza automáticamente los foreign keys
    for old_id, new_id in id_mapping.items():
        try:
            cur.execute(f"""
                UPDATE {table_name}
                SET id = {new_id}
                WHERE id = {old_id};
            """)
        except psycopg2.Error as e:
            logging.error(f"    ✗ Error actualizando ID {old_id} → {new_id}: {e}")
            raise

    conn.commit()
    cur.close()

    logging.info(f"  ✓ Resecuenciado: {len(id_mapping)} cambios (FKs actualizados por CASCADE)")
    return id_mapping

# ══════════════════════════════════════════════════════════════
#                    PASO 3: ACTUALIZAR NOMBRES
# ══════════════════════════════════════════════════════════════

def update_names(conn, model_name, table_name, naming_rules):
    """Actualiza nombres según reglas"""
    cur = conn.cursor()

    if not naming_rules:
        logging.info(f"  ⊘ Sin naming rules")
        cur.close()
        return

    try:
        if naming_rules.get('use_account_code'):
            # Regla especial: account.account usa código contable con _ en lugar de .
            cur.execute(f"""
                UPDATE {table_name}
                SET code = REPLACE(code, '.', '_')
                WHERE code IS NOT NULL;
            """)
            updated = cur.rowcount
            logging.info(f"  ✓ Nombres actualizados: {updated} códigos (. → _)")

        else:
            # Regla estándar: modelo_id con . → _
            model_clean = model_name.replace('.', '_')

            cur.execute(f"""
                UPDATE {table_name}
                SET name = REPLACE(
                    CONCAT('{model_clean}_', id::text),
                    '.',
                    '_'
                )
                WHERE name IS NOT NULL;
            """)
            updated = cur.rowcount
            logging.info(f"  ✓ Nombres actualizados: {updated} registros ({model_clean}_id)")

        conn.commit()

    except psycopg2.Error as e:
        logging.error(f"  ✗ Error actualizando nombres: {e}")
        conn.rollback()
        raise

    cur.close()

# ══════════════════════════════════════════════════════════════
#                    PASO 4: ELIMINAR GAPS
# ══════════════════════════════════════════════════════════════

def eliminate_gaps(conn, table_name):
    """Elimina gaps en secuencia de IDs"""
    cur = conn.cursor()

    try:
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
            # Renumerar para eliminar gaps (mantiene orden, elimina huecos)
            cur.execute(f"""
                WITH numbered AS (
                    SELECT id,
                           ROW_NUMBER() OVER (ORDER BY id) as new_id
                    FROM {table_name}
                )
                UPDATE {table_name} t
                SET id = n.new_id
                FROM numbered n
                WHERE t.id = n.id AND t.id != n.new_id;
            """)

            conn.commit()
            logging.info(f"  ✓ Gaps eliminados: {gaps_count} huecos corregidos")
        else:
            logging.info(f"  ✓ Sin gaps detectados")

    except psycopg2.Error as e:
        logging.error(f"  ✗ Error eliminando gaps: {e}")
        conn.rollback()
        raise

    cur.close()
    return gaps_count

# ══════════════════════════════════════════════════════════════
#                    PASO 5: DELETE SEGURO
# ══════════════════════════════════════════════════════════════

def safe_delete(conn, table_name, cleanup_rules):
    """Ejecuta DELETE con validación de WHERE"""
    cur = conn.cursor()

    delete_conditions = cleanup_rules.get('delete_conditions', [])

    if not delete_conditions:
        logging.info(f"  ⊘ Sin DELETE rules")
        cur.close()
        return 0

    deleted_total = 0

    for condition in delete_conditions:
        where_clause = condition['where']

        # SEGURIDAD: Validar que tenga WHERE
        if not where_clause or where_clause.strip() == '':
            raise SecurityError(f"❌ DELETE sin WHERE no permitido en {table_name}")

        try:
            # Ejecutar DELETE seguro
            query = f"DELETE FROM {table_name} WHERE {where_clause};"

            cur.execute(query)
            deleted_count = cur.rowcount
            deleted_total += deleted_count

            logging.info(f"    DELETE: {deleted_count} registros ({where_clause[:60]}...)")

        except psycopg2.Error as e:
            logging.warning(f"    ⚠️  Error en DELETE: {e}")
            continue

    conn.commit()
    cur.close()

    logging.info(f"  ✓ DELETE completado: {deleted_total} registros eliminados")
    return deleted_total

# ══════════════════════════════════════════════════════════════
#                    PROCESAMIENTO POR MODELO
# ══════════════════════════════════════════════════════════════

def process_model(conn, model_name, model_config):
    """Procesa un modelo con orden específico"""

    table_name = model_config['table_name']

    logging.info(f"\n▶ Procesando: {model_name} ({table_name})")

    result = {
        'status': 'PROCESSING',
        'records_before': 0,
        'records_after': 0,
        'changes': []
    }

    # Contar registros iniciales
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        result['records_before'] = cur.fetchone()[0]
    except psycopg2.Error:
        result['records_before'] = 0
    cur.close()

    try:
        # PASO 1: CASCADE
        if 'cascade_rules' in model_config and model_config['cascade_rules']:
            apply_cascade(conn, model_config, model_name)
            result['changes'].append("CASCADE aplicado")

        # PASO 2: RESECUENCIAR IDs
        if 'resequence_rules' in model_config and model_config['resequence_rules']:
            start_id = model_config['resequence_rules'].get('start_id', 1000)
            id_mapping = resequence_ids(conn, table_name, start_id)
            result['changes'].append(f"IDs resecuenciados desde {start_id}")

        # PASO 3: ACTUALIZAR NOMBRES
        if 'naming_rules' in model_config and model_config['naming_rules']:
            update_names(conn, model_name, table_name, model_config['naming_rules'])
            result['changes'].append("Nombres actualizados")

        # PASO 4: ELIMINAR GAPS
        gaps = eliminate_gaps(conn, table_name)
        result['changes'].append(f"{gaps} gaps eliminados")

        # PASO 5: DELETE SEGURO
        if 'cleanup_rules' in model_config:
            deleted = safe_delete(conn, table_name, model_config['cleanup_rules'])
            result['changes'].append(f"{deleted} registros eliminados")

        # Contar registros finales
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        result['records_after'] = cur.fetchone()[0]
        cur.close()

        result['status'] = 'SUCCESS'
        logging.info(f"  ✓ Completado: {result['records_after']} registros finales")

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

    # Crear directorios si no existen
    os.makedirs('output/statistics', exist_ok=True)
    os.makedirs('output/logs', exist_ok=True)

    # JSON detallado
    json_file = f'output/statistics/processing_report_{timestamp}.json'

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
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'output/logs/execution_{timestamp}.log'
    os.makedirs('output/logs', exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Sistema de Limpieza y Resecuenciación BDD Odoo         ║")
    print("║  Versión 3.2                                             ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    try:
        # 1. Cargar credenciales
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
                'database': credentials['database'],
                'log_file': log_file
            },
            'models_processed': {}
        }

        total_models = len(config['execution_order'])
        logging.info(f"📦 Total de modelos a procesar: {total_models}\n")

        for idx, model_name in enumerate(config['execution_order'], 1):
            logging.info(f"{'='*60}")
            logging.info(f"Modelo {idx}/{total_models}: {model_name}")
            logging.info(f"{'='*60}")

            model_config = config['models'][model_name]
            result = process_model(conn, model_name, model_config)
            stats['models_processed'][model_name] = result

        # 5. Generar reportes
        generate_report(stats)

        # 6. Cerrar conexión
        conn.close()
        logging.info("\n🔌 Conexión cerrada")

        print("\n✅ Proceso completado exitosamente")
        print(f"📋 Log guardado en: {log_file}")

    except Exception as e:
        logging.error(f"\n❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
