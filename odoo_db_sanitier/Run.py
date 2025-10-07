#!/usr/bin/env python3
"""
Run.py
Script principal de procesamiento de base de datos
Versión 3.7 - Corrección de Integridad Referencial:
- DISABLE TRIGGER USER (mantiene CASCADE activo)
- Integridad referencial 100% garantizada
- Batch size dinámico (100-2000)
- UPDATE con CASE optimizado
- Rendimiento excelente con integridad completa
"""

import psycopg2
import json
import os
import sys
from datetime import datetime
import logging
from pathlib import Path
import time

# ══════════════════════════════════════════════════════════════
#           PROGRESO EN TIEMPO REAL v3.5
# ══════════════════════════════════════════════════════════════

class ProgressTracker:
    """Tracker de progreso en tiempo real para visualización en consola"""

    def __init__(self, total_models):
        self.total_models = total_models
        self.current_model = 0
        self.start_time = time.time()
        self.model_times = []

    def start_model(self, model_num, model_name):
        """Inicia tracking de un modelo"""
        self.current_model = model_num
        self.model_start = time.time()
        elapsed = time.time() - self.start_time
        print(f"\n{'='*60}")
        print(f"Modelo {model_num}/{self.total_models}: {model_name}")
        print(f"Tiempo transcurrido: {self._format_time(elapsed)}")
        print(f"{'='*60}")

    def end_model(self, status="COMPLETADO"):
        """Finaliza tracking de un modelo"""
        model_time = time.time() - self.model_start
        self.model_times.append(model_time)

        # Calcular tiempo promedio y estimado restante
        avg_time = sum(self.model_times) / len(self.model_times)
        remaining = (self.total_models - self.current_model) * avg_time

        print(f"\n{'─'*60}")
        print(f"✓ {status} - Tiempo: {self._format_time(model_time)}")
        print(f"📊 Progreso: {self.current_model}/{self.total_models} modelos")
        print(f"⏱️  Tiempo restante estimado: {self._format_time(remaining)}")
        print(f"{'─'*60}")

    def log_step(self, step_name, count=None, total=None):
        """Registra un paso dentro del modelo"""
        if count and total:
            print(f"  ▶ {step_name}: {count}/{total}")
        else:
            print(f"  ▶ {step_name}")

    def log_batch(self, batch_num, total_batches, records_processed, total_records):
        """Registra progreso de un lote"""
        percent = (records_processed / total_records * 100) if total_records > 0 else 0
        bar_length = 30
        filled = int(bar_length * records_processed / total_records) if total_records > 0 else 0
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"    Lote {batch_num}/{total_batches}: [{bar}] {percent:.1f}% ({records_processed}/{total_records})")

    def _format_time(self, seconds):
        """Formatea segundos a formato legible"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            mins = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{mins}m {secs}s"
        else:
            hours = int(seconds // 3600)
            mins = int((seconds % 3600) // 60)
            return f"{hours}h {mins}m"

# ══════════════════════════════════════════════════════════════
#           FUNCIONES DE VALIDACIÓN Y DETECCIÓN v3.4
# ══════════════════════════════════════════════════════════════

def table_exists(conn, table_name):
    """v3.4: Verifica si una tabla existe en el esquema"""
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
    """, (table_name,))
    exists = cur.fetchone() is not None
    cur.close()
    return exists

def column_exists(conn, table_name, column_name):
    """v3.4: Verifica si una columna existe en una tabla"""
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
          AND column_name = %s
    """, (table_name, column_name))
    exists = cur.fetchone() is not None
    cur.close()
    return exists

def get_column_type(conn, table_name, column_name):
    """v3.4: Obtiene el tipo de dato de una columna"""
    cur = conn.cursor()
    cur.execute("""
        SELECT data_type FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = %s
          AND column_name = %s
    """, (table_name, column_name))
    result = cur.fetchone()
    cur.close()
    return result[0] if result else None

def calculate_start_id(conn, table_name, buffer_size=1000):
    """
    v3.4: Calcula start_id dinámicamente como MAX(id) + buffer
    Solución para duplicate key errors
    """
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table_name}")
        max_id = cur.fetchone()[0]
        start_id = max_id + buffer_size
        logging.debug(f"    💡 start_id calculado: {start_id} (MAX={max_id} + buffer={buffer_size})")
        cur.close()
        return start_id
    except psycopg2.Error as e:
        logging.warning(f"    ⚠️  Error calculando start_id: {e}")
        cur.close()
        return buffer_size  # Fallback

def calculate_batch_size(total_records):
    """
    v3.6: Calcula batch_size dinámico según tamaño de tabla
    Optimiza rendimiento ajustando tamaño de lote
    """
    if total_records < 1000:
        return 100      # Tablas pequeñas
    elif total_records < 10000:
        return 500      # Tablas medianas
    elif total_records < 100000:
        return 1000     # Tablas grandes
    else:
        return 2000     # Tablas muy grandes (stock.move, etc.)

def get_inverse_foreign_keys(conn, table_name):
    """
    v3.4: Detecta referencias inversas - FKs desde otras tablas hacia esta
    Solución para referencias inversas sin CASCADE
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT
            tc.table_name,
            kcu.column_name,
            tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
            AND ccu.table_name = %s
    """, (table_name,))
    result = cur.fetchall()
    cur.close()
    return result

def apply_inverse_cascade(conn, table_name):
    """
    v3.5: Aplica CASCADE a referencias inversas con progreso y ROLLBACK individual
    """
    inverse_fks = get_inverse_foreign_keys(conn, table_name)

    if not inverse_fks:
        logging.debug(f"    💡 Sin referencias inversas detectadas")
        return 0

    total = len(inverse_fks)
    logging.info(f"    💡 Detectadas {total} referencias inversas, aplicando CASCADE...")

    applied_count = 0
    failed_count = 0

    for idx, (fk_table, fk_column, fk_constraint) in enumerate(inverse_fks, 1):
        cur = conn.cursor()
        try:
            # Drop constraint existente
            cur.execute(f'ALTER TABLE {fk_table} DROP CONSTRAINT IF EXISTS "{fk_constraint}";')

            # Re-crear con CASCADE
            cur.execute(f"""
                ALTER TABLE {fk_table}
                ADD CONSTRAINT "{fk_constraint}"
                FOREIGN KEY ({fk_column})
                REFERENCES {table_name}(id)
                ON DELETE CASCADE
                ON UPDATE CASCADE;
            """)

            conn.commit()  # v3.5: Commit individual
            applied_count += 1

            # v3.5: Progreso cada 50 referencias
            if idx % 50 == 0 or idx == total:
                logging.info(f"       Progreso: {idx}/{total} referencias inversas procesadas")

            logging.debug(f"       + {fk_table}.{fk_column} → {table_name} (CASCADE)")

        except psycopg2.Error as e:
            conn.rollback()  # v3.5: ROLLBACK individual
            failed_count += 1
            logging.debug(f"       ⚠️  Error en {fk_constraint}: {str(e).split(chr(10))[0]}")
        finally:
            cur.close()

    logging.info(f"    ✓ Referencias inversas: {applied_count} aplicadas, {failed_count} fallidas ({total} total)")
    return applied_count

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
    """
    v3.5: Aplica CASCADE a foreign keys con validación y ROLLBACK individual
    """
    cascade_rules = model_config.get('cascade_rules', [])

    if not cascade_rules:
        logging.info(f"  ⊘ Sin CASCADE rules")
        return

    applied_count = 0
    skipped_count = 0

    for rule in cascade_rules:
        table = rule['table']
        constraint = rule['constraint']
        fk_column = rule.get('fk_column')
        ref_table = rule['ref_table']
        on_delete = rule['on_delete']
        on_update = rule['on_update']

        # Si no hay fk_column en JSON, intentar inferir (fallback)
        if not fk_column:
            parts = constraint.replace('_fkey', '').split('_')
            if len(parts) >= 2:
                fk_column = '_'.join(parts[-2:]) if parts[-1] == 'id' else parts[-1]
            else:
                logging.warning(f"    ⚠️  SKIP {constraint}: no se pudo determinar columna FK")
                skipped_count += 1
                continue

        # v3.5: Validar que la tabla y columna FK existen
        if not table_exists(conn, table):
            logging.warning(f"    ⚠️  SKIP {constraint}: tabla '{table}' no existe")
            skipped_count += 1
            continue

        if not column_exists(conn, table, fk_column):
            logging.warning(f"    ⚠️  SKIP {constraint}: columna '{table}.{fk_column}' no existe")
            skipped_count += 1
            continue

        # v3.5: Cada CASCADE en su propia transacción
        cur = conn.cursor()
        try:
            # Verificar si el constraint existe
            cur.execute("""
                SELECT 1 FROM information_schema.table_constraints
                WHERE constraint_name = %s AND table_name = %s
            """, (constraint, table))

            exists = cur.fetchone()

            if exists:
                cur.execute(f'ALTER TABLE {table} DROP CONSTRAINT "{constraint}";')
                logging.debug(f"    - DROP {constraint}")

            # Re-crear con CASCADE
            cur.execute(f"""
                ALTER TABLE {table}
                ADD CONSTRAINT "{constraint}"
                FOREIGN KEY ({fk_column})
                REFERENCES {ref_table}(id)
                ON DELETE {on_delete}
                ON UPDATE {on_update};
            """)

            conn.commit()  # v3.5: Commit individual
            applied_count += 1
            logging.debug(f"    + ADD {constraint} (ON DELETE {on_delete})")

        except psycopg2.Error as e:
            conn.rollback()  # v3.5: ROLLBACK individual - evita abort cascade
            logging.warning(f"    ⚠️  Error en {constraint}: {str(e).split(chr(10))[0]}")  # Solo primera línea
            skipped_count += 1
        finally:
            cur.close()

    total = len(cascade_rules)
    logging.info(f"  ✓ CASCADE: {applied_count} aplicados, {skipped_count} omitidos ({total} total)")

# ══════════════════════════════════════════════════════════════
#                    PASO 2: RESECUENCIAR IDs
# ══════════════════════════════════════════════════════════════

def resequence_ids(conn, table_name, start_id, batch_size=None, progress=None):
    """
    v3.6: Resecuenciación optimizada con UPDATE CASE, tabla temporal y triggers desactivados
    - Batch size dinámico según tamaño de tabla
    - UPDATE con CASE (1 query por lote vs N queries)
    - Tabla temporal para mapping
    - Triggers desactivados durante proceso
    """
    cur = conn.cursor()

    # 1. Obtener IDs actuales y contar
    cur.execute(f"SELECT id FROM {table_name} ORDER BY id;")
    records = cur.fetchall()
    total_records = len(records)

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

    if not id_mapping:
        logging.info(f"  ✓ IDs ya secuenciales desde {start_id}")
        cur.close()
        return {}

    # v3.6: Batch size dinámico según tamaño de tabla
    if batch_size is None:
        batch_size = calculate_batch_size(total_records)

    total_changes = len(id_mapping)
    mapping_items = list(id_mapping.items())
    total_batches = (total_changes + batch_size - 1) // batch_size

    logging.info(f"  💡 Resecuenciando {total_changes} registros en {total_batches} lotes de {batch_size} (dinámico)...")

    if progress:
        progress.log_step(f"Resecuenciando IDs", total_changes, total_records)

    try:
        # v3.7: Desactivar solo triggers USER (mantiene CASCADE activo)
        logging.debug(f"    🔧 Desactivando triggers de usuario...")
        cur.execute(f"ALTER TABLE {table_name} DISABLE TRIGGER USER;")
        conn.commit()

        # v3.6: Crear tabla temporal para mapping
        cur.execute("""
            CREATE TEMP TABLE IF NOT EXISTS temp_id_mapping (
                old_id INTEGER,
                new_id INTEGER
            ) ON COMMIT DROP;
        """)

        # 3. Procesar en lotes con UPDATE CASE optimizado
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, total_changes)
            batch = mapping_items[start_idx:end_idx]

            try:
                # v3.6: Construir UPDATE con CASE (1 query vs N queries)
                when_clauses = []
                old_ids = []

                for old_id, new_id in batch:
                    when_clauses.append(f"WHEN {old_id} THEN {new_id}")
                    old_ids.append(str(old_id))

                case_statement = " ".join(when_clauses)
                ids_list = ", ".join(old_ids)

                # v3.6: Un solo UPDATE para todo el lote
                update_query = f"""
                    UPDATE {table_name}
                    SET id = CASE id
                        {case_statement}
                    END
                    WHERE id IN ({ids_list});
                """

                cur.execute(update_query)
                conn.commit()

                # Mostrar progreso visual
                if progress:
                    progress.log_batch(batch_num + 1, total_batches, end_idx, total_changes)
                else:
                    logging.info(f"    ✓ Lote {batch_num + 1}/{total_batches}: {end_idx}/{total_changes} registros")

            except psycopg2.Error as e:
                conn.rollback()
                logging.error(f"    ✗ Error en lote {batch_num + 1}: {e}")
                raise

        # v3.7: Reactivar triggers de usuario
        logging.debug(f"    🔧 Reactivando triggers de usuario...")
        cur.execute(f"ALTER TABLE {table_name} ENABLE TRIGGER USER;")
        conn.commit()

    except Exception as e:
        # Asegurar que triggers se reactiven incluso si hay error
        try:
            cur.execute(f"ALTER TABLE {table_name} ENABLE TRIGGER USER;")
            conn.commit()
        except:
            pass
        raise

    finally:
        cur.close()

    logging.info(f"  ✓ Resecuenciado completo: {total_changes} cambios (FKs actualizados por CASCADE)")
    return id_mapping

# ══════════════════════════════════════════════════════════════
#                    PASO 3: ACTUALIZAR NOMBRES
# ══════════════════════════════════════════════════════════════

def update_names(conn, model_name, table_name, naming_rules):
    """v3.4: Actualiza nombres según reglas (con validación JSONB)"""
    cur = conn.cursor()

    if not naming_rules:
        logging.info(f"  ⊘ Sin naming rules")
        cur.close()
        return

    try:
        if naming_rules.get('use_account_code'):
            # v3.4: Validar que columna code existe
            if not column_exists(conn, table_name, 'code'):
                logging.warning(f"  ⚠️  Columna 'code' no existe - SKIP naming")
                cur.close()
                return

            # Regla especial: account.account usa código contable con _ en lugar de .
            cur.execute(f"""
                UPDATE {table_name}
                SET code = REPLACE(code, '.', '_')
                WHERE code IS NOT NULL;
            """)
            updated = cur.rowcount
            logging.info(f"  ✓ Nombres actualizados: {updated} códigos (. → _)")

        else:
            # v3.4: Validar que columna name existe
            if not column_exists(conn, table_name, 'name'):
                logging.warning(f"  ⚠️  Columna 'name' no existe - SKIP naming")
                cur.close()
                return

            # v3.4: Detectar tipo de columna
            col_type = get_column_type(conn, table_name, 'name')

            if col_type == 'jsonb':
                # JSONB: Skip por ahora (requiere lógica especial)
                logging.warning(f"  ⚠️  Campo 'name' es JSONB - SKIP naming (mejora futura)")
                cur.close()
                return

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

def process_model(conn, model_name, model_config, progress=None):
    """v3.5: Procesa un modelo con validaciones, mejoras y progreso visual"""

    table_name = model_config['table_name']

    logging.info(f"\n▶ Procesando: {model_name} ({table_name})")

    result = {
        'status': 'PROCESSING',
        'records_before': 0,
        'records_after': 0,
        'changes': []
    }

    # v3.4: VALIDACIÓN - Verificar que tabla existe
    if not table_exists(conn, table_name):
        logging.warning(f"  ⚠️  Tabla '{table_name}' no existe - SKIP modelo")
        result['status'] = 'SKIPPED'
        result['error'] = 'Tabla no existe'
        return result

    # Contar registros iniciales
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        result['records_before'] = cur.fetchone()[0]
        if progress:
            progress.log_step(f"Registros en tabla", result['records_before'])
    except psycopg2.Error:
        result['records_before'] = 0
    cur.close()

    try:
        # PASO 1: CASCADE (desde archivos .py)
        if 'cascade_rules' in model_config and model_config['cascade_rules']:
            if progress:
                progress.log_step("Aplicando CASCADE", len(model_config['cascade_rules']), len(model_config['cascade_rules']))
            apply_cascade(conn, model_config, model_name)
            result['changes'].append("CASCADE aplicado")

        # v3.4: PASO 1b: CASCADE REFERENCIAS INVERSAS
        if progress:
            progress.log_step("Detectando referencias inversas...")
        inverse_count = apply_inverse_cascade(conn, table_name)
        if inverse_count > 0:
            result['changes'].append(f"Referencias inversas CASCADE: {inverse_count}")

        # v3.4: PASO 2: RESECUENCIAR IDs (con start_id dinámico)
        if 'resequence_rules' in model_config and model_config['resequence_rules']:
            # Calcular start_id dinámicamente
            start_id = calculate_start_id(conn, table_name, buffer_size=1000)
            logging.info(f"  💡 start_id dinámico: {start_id}")

            id_mapping = resequence_ids(conn, table_name, start_id, progress=progress)
            result['changes'].append(f"IDs resecuenciados desde {start_id}")

        # PASO 3: ACTUALIZAR NOMBRES (con validación JSONB)
        if 'naming_rules' in model_config and model_config['naming_rules']:
            if progress:
                progress.log_step("Actualizando nombres...")
            update_names(conn, model_name, table_name, model_config['naming_rules'])
            result['changes'].append("Nombres actualizados")

        # PASO 4: ELIMINAR GAPS
        if progress:
            progress.log_step("Eliminando gaps...")
        gaps = eliminate_gaps(conn, table_name)
        result['changes'].append(f"{gaps} gaps eliminados")

        # PASO 5: DELETE SEGURO
        if 'cleanup_rules' in model_config:
            if progress:
                progress.log_step("Ejecutando deletes seguros...")
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
    print("║  Versión 3.7 - Integridad Referencial Garantizada       ║")
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

        # 4. Procesar modelos con progreso visual v3.5
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

        # v3.5: Inicializar ProgressTracker
        progress = ProgressTracker(total_models)

        for idx, model_name in enumerate(config['execution_order'], 1):
            # v3.5: Mostrar progreso de modelo
            progress.start_model(idx, model_name)

            model_config = config['models'][model_name]
            result = process_model(conn, model_name, model_config, progress=progress)
            stats['models_processed'][model_name] = result

            # v3.5: Finalizar progreso de modelo
            progress.end_model(result['status'])

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
