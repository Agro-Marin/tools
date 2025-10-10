#!/usr/bin/env python3
"""
verify_intervals_integrity.py
Script de verificación de integridad por intervalos para Odoo DB Sanitizer v4.0

Verifica:
- Secuencia de IDs (gaps, duplicados)
- Integridad referencial en intervalos
- Estadísticas por segmentos de la tabla
- Mínimo 2 intervalos por modelo

Autor: Sistema Odoo DB Sanitizer
Versión: 4.0
Fecha: 2025-10-09
"""

import psycopg2
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ══════════════════════════════════════════════════════════════
#                    CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════

def load_credentials():
    """Carga credenciales desde config/db_credentials.json"""
    cred_file = 'config/db_credentials.json'

    if not os.path.exists(cred_file):
        raise FileNotFoundError(f"❌ Credenciales no encontradas: {cred_file}")

    with open(cred_file, 'r') as f:
        return json.load(f)

def load_models_config():
    """Carga configuración de modelos"""
    config_file = 'models_config.json'

    if not os.path.exists(config_file):
        raise FileNotFoundError(f"❌ Configuración no encontrada: {config_file}")

    with open(config_file, 'r') as f:
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

        print(f"✓ Conectado a: {credentials['database']} @ {credentials['host']}")
        return conn

    except psycopg2.Error as e:
        print(f"✗ Error de conexión: {e}")
        raise

# ══════════════════════════════════════════════════════════════
#            FUNCIONES DE CÁLCULO DE INTERVALOS
# ══════════════════════════════════════════════════════════════

def calculate_intervals(conn, table_name, min_intervals=2):
    """
    Calcula intervalos inteligentes para verificación

    Estrategia:
    - Si tabla < 100 registros: 2 intervalos (mitad)
    - Si tabla < 1000: 2 intervalos (cuartiles)
    - Si tabla < 10000: 3 intervalos (terciles)
    - Si tabla >= 10000: 4 intervalos (cuartiles + extremos)

    Returns: List of (interval_name, min_id, max_id, description)
    """
    cur = conn.cursor()

    # Obtener estadísticas de la tabla
    cur.execute(f"""
        SELECT
            MIN(id) as min_id,
            MAX(id) as max_id,
            COUNT(*) as total,
            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY id) as q1,
            PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY id) as median,
            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY id) as q3
        FROM {table_name}
        WHERE id IS NOT NULL;
    """)

    stats = cur.fetchone()
    cur.close()

    if not stats or stats[0] is None:
        return []

    min_id, max_id, total, q1, median, q3 = stats

    intervals = []

    if total < 100:
        # Tablas muy pequeñas: 2 intervalos (inicio y fin)
        intervals = [
            ("Intervalo 1 (Inicio)", min_id, median, f"Primeros {int(total/2)} registros"),
            ("Intervalo 2 (Fin)", median + 1, max_id, f"Últimos {int(total/2)} registros"),
        ]

    elif total < 1000:
        # Tablas pequeñas: 2 intervalos (cuartiles)
        intervals = [
            ("Intervalo 1 (Q1-Q2)", min_id, median, "Primer 50%"),
            ("Intervalo 2 (Q2-Q4)", median + 1, max_id, "Segundo 50%"),
        ]

    elif total < 10000:
        # Tablas medianas: 3 intervalos (terciles)
        tercil_1 = min_id + (max_id - min_id) // 3
        tercil_2 = min_id + 2 * (max_id - min_id) // 3

        intervals = [
            ("Intervalo 1 (Inicio)", min_id, tercil_1, "Primer tercio"),
            ("Intervalo 2 (Medio)", tercil_1 + 1, tercil_2, "Segundo tercio"),
            ("Intervalo 3 (Fin)", tercil_2 + 1, max_id, "Tercer tercio"),
        ]

    else:
        # Tablas grandes: 4 intervalos (cuartiles + extremos)
        intervals = [
            ("Intervalo 1 (Q1)", min_id, q1, "Primer cuartil"),
            ("Intervalo 2 (Q2)", q1 + 1, median, "Segundo cuartil"),
            ("Intervalo 3 (Q3)", median + 1, q3, "Tercer cuartil"),
            ("Intervalo 4 (Q4)", q3 + 1, max_id, "Cuarto cuartil"),
        ]

    # Asegurar al menos min_intervals
    while len(intervals) < min_intervals:
        # Dividir el intervalo más grande
        largest_idx = max(range(len(intervals)),
                         key=lambda i: intervals[i][2] - intervals[i][1])

        name, start, end, desc = intervals[largest_idx]
        mid = start + (end - start) // 2

        intervals[largest_idx] = (f"{name} (a)", start, mid, f"{desc} (primera mitad)")
        intervals.insert(largest_idx + 1, (f"{name} (b)", mid + 1, end, f"{desc} (segunda mitad)"))

    return intervals

# ══════════════════════════════════════════════════════════════
#              VERIFICACIÓN DE INTEGRIDAD
# ══════════════════════════════════════════════════════════════

def verify_sequence_integrity(conn, table_name, interval_name, min_id, max_id):
    """
    Verifica integridad de secuencia en un intervalo

    Checks:
    - Gaps en secuencia
    - Duplicados
    - Registros en intervalo
    - Densidad (registros / rango)
    """
    cur = conn.cursor()

    result = {
        'interval': interval_name,
        'range': f"{min_id} - {max_id}",
        'min_id': int(min_id),
        'max_id': int(max_id),
        'checks': {}
    }

    # 1. Contar registros en intervalo
    cur.execute(f"""
        SELECT COUNT(*)
        FROM {table_name}
        WHERE id >= {min_id} AND id <= {max_id};
    """)
    records_count = cur.fetchone()[0]
    result['checks']['records_count'] = records_count

    # 2. Detectar gaps
    cur.execute(f"""
        WITH gaps AS (
            SELECT
                id,
                id - LAG(id) OVER (ORDER BY id) - 1 as gap_size
            FROM {table_name}
            WHERE id >= {min_id} AND id <= {max_id}
        )
        SELECT COUNT(*) as gaps_count, COALESCE(SUM(gap_size), 0) as total_gap_size
        FROM gaps
        WHERE gap_size > 0;
    """)

    gaps_data = cur.fetchone()
    result['checks']['gaps_count'] = gaps_data[0] if gaps_data else 0
    result['checks']['total_gap_size'] = int(gaps_data[1]) if gaps_data else 0

    # 3. Detectar duplicados
    cur.execute(f"""
        SELECT COUNT(*)
        FROM (
            SELECT id, COUNT(*)
            FROM {table_name}
            WHERE id >= {min_id} AND id <= {max_id}
            GROUP BY id
            HAVING COUNT(*) > 1
        ) duplicates;
    """)
    duplicates_count = cur.fetchone()[0]
    result['checks']['duplicates'] = duplicates_count

    # 4. Calcular densidad
    range_size = max_id - min_id + 1
    density = (records_count / range_size * 100) if range_size > 0 else 0
    result['checks']['density_percent'] = round(density, 2)

    # 5. Primer y último ID real
    cur.execute(f"""
        SELECT MIN(id), MAX(id)
        FROM {table_name}
        WHERE id >= {min_id} AND id <= {max_id};
    """)
    actual_range = cur.fetchone()
    result['checks']['actual_min_id'] = int(actual_range[0]) if actual_range[0] else None
    result['checks']['actual_max_id'] = int(actual_range[1]) if actual_range[1] else None

    # 6. Estado general
    if duplicates_count > 0:
        result['status'] = 'ERROR'
        result['message'] = f"❌ {duplicates_count} IDs duplicados detectados"
    elif gaps_data[0] > 0 and gaps_data[0] > records_count * 0.1:
        result['status'] = 'WARNING'
        result['message'] = f"⚠️  {gaps_data[0]} gaps detectados (>10% de registros)"
    elif density < 50:
        result['status'] = 'WARNING'
        result['message'] = f"⚠️  Baja densidad: {density:.1f}%"
    else:
        result['status'] = 'OK'
        result['message'] = f"✓ Secuencia OK ({records_count} registros, densidad {density:.1f}%)"

    cur.close()
    return result

def verify_foreign_key_integrity(conn, table_name, fk_constraints, interval_name, min_id, max_id):
    """
    Verifica integridad referencial en un intervalo

    Verifica que todos los FKs apunten a registros existentes
    """
    cur = conn.cursor()

    result = {
        'interval': interval_name,
        'range': f"{min_id} - {max_id}",
        'fk_checks': []
    }

    if not fk_constraints:
        result['status'] = 'SKIP'
        result['message'] = 'Sin FK constraints configuradas'
        return result

    total_broken = 0

    for fk in fk_constraints:
        fk_table = fk.get('table')
        fk_column = fk.get('column')

        if not fk_table or not fk_column:
            continue

        # Verificar que tabla FK existe
        cur.execute("""
            SELECT 1 FROM information_schema.tables
            WHERE table_schema='public' AND table_name=%s;
        """, (fk_table,))

        if not cur.fetchone():
            continue

        # Verificar que columna FK existe
        cur.execute("""
            SELECT 1 FROM information_schema.columns
            WHERE table_schema='public' AND table_name=%s AND column_name=%s;
        """, (fk_table, fk_column))

        if not cur.fetchone():
            continue

        # Verificar integridad FK
        cur.execute(f"""
            SELECT COUNT(*) as broken_fks
            FROM {fk_table} fk
            LEFT JOIN {table_name} t ON fk.{fk_column} = t.id
            WHERE fk.{fk_column} IS NOT NULL
              AND fk.{fk_column} >= {min_id}
              AND fk.{fk_column} <= {max_id}
              AND t.id IS NULL;
        """)

        broken_fks = cur.fetchone()[0]
        total_broken += broken_fks

        fk_result = {
            'fk_table': fk_table,
            'fk_column': fk_column,
            'broken_count': broken_fks,
            'status': 'ERROR' if broken_fks > 0 else 'OK'
        }

        result['fk_checks'].append(fk_result)

    # Estado general
    if total_broken > 0:
        result['status'] = 'ERROR'
        result['message'] = f"❌ {total_broken} FKs rotas detectadas"
    else:
        result['status'] = 'OK'
        result['message'] = f"✓ Todas las FKs intactas ({len(result['fk_checks'])} verificadas)"

    cur.close()
    return result

# ══════════════════════════════════════════════════════════════
#              VERIFICACIÓN POR MODELO
# ══════════════════════════════════════════════════════════════

def verify_model(conn, model_name, model_config):
    """
    Verifica un modelo completo por intervalos
    """
    table_name = model_config.get('table', model_config.get('table_name'))

    if not table_name:
        return None

    print(f"\n{'='*70}")
    print(f"Modelo: {model_name} ({table_name})")
    print(f"{'='*70}")

    # Verificar que tabla existe
    cur = conn.cursor()
    cur.execute("""
        SELECT 1 FROM information_schema.tables
        WHERE table_schema='public' AND table_name=%s;
    """, (table_name,))

    if not cur.fetchone():
        print(f"  ⊘ Tabla '{table_name}' no existe - SKIP")
        cur.close()
        return None

    # Contar registros totales
    cur.execute(f"SELECT COUNT(*) FROM {table_name};")
    total_records = cur.fetchone()[0]
    cur.close()

    if total_records == 0:
        print(f"  ⊘ Tabla vacía - SKIP")
        return None

    print(f"  📊 Total registros: {total_records:,}")

    # Calcular intervalos
    intervals = calculate_intervals(conn, table_name, min_intervals=2)

    if not intervals:
        print(f"  ⊘ No se pudieron calcular intervalos - SKIP")
        return None

    print(f"  📐 Intervalos a verificar: {len(intervals)}")

    model_result = {
        'model': model_name,
        'table': table_name,
        'total_records': total_records,
        'intervals': []
    }

    # Obtener FK constraints
    fk_constraints = []
    operations = model_config.get('operations', {})
    fk_rewrite = operations.get('fk_rewrite', {})
    if fk_rewrite.get('enabled'):
        fk_constraints = fk_rewrite.get('constraints', [])

    # Verificar cada intervalo
    for idx, (interval_name, min_id, max_id, description) in enumerate(intervals, 1):
        print(f"\n  ▶ {interval_name}: {description}")
        print(f"    Rango: ID {int(min_id)} - {int(max_id)}")

        # 1. Verificar secuencia
        sequence_result = verify_sequence_integrity(conn, table_name, interval_name,
                                                    min_id, max_id)

        print(f"    {sequence_result['message']}")

        # 2. Verificar FKs
        fk_result = verify_foreign_key_integrity(conn, table_name, fk_constraints,
                                                 interval_name, min_id, max_id)

        if fk_result['status'] != 'SKIP':
            print(f"    {fk_result['message']}")

        # Agregar al resultado
        model_result['intervals'].append({
            'sequence': sequence_result,
            'foreign_keys': fk_result
        })

    # Resumen del modelo
    errors = sum(1 for i in model_result['intervals']
                 if i['sequence']['status'] == 'ERROR' or
                    i['foreign_keys']['status'] == 'ERROR')
    warnings = sum(1 for i in model_result['intervals']
                   if i['sequence']['status'] == 'WARNING' or
                      i['foreign_keys']['status'] == 'WARNING')

    print(f"\n  {'─'*66}")
    if errors > 0:
        print(f"  ❌ ERRORES: {errors} intervalos con errores críticos")
        model_result['overall_status'] = 'ERROR'
    elif warnings > 0:
        print(f"  ⚠️  ADVERTENCIAS: {warnings} intervalos con advertencias")
        model_result['overall_status'] = 'WARNING'
    else:
        print(f"  ✅ OK: Todos los intervalos verificados exitosamente")
        model_result['overall_status'] = 'OK'

    return model_result

# ══════════════════════════════════════════════════════════════
#                    GENERACIÓN DE REPORTES
# ══════════════════════════════════════════════════════════════

def generate_report(results, execution_time):
    """Genera reporte detallado en JSON y resumen en consola"""

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Crear directorios
    os.makedirs('output/integrity', exist_ok=True)

    # Reporte JSON detallado
    report_data = {
        'execution_info': {
            'timestamp': datetime.now().isoformat(),
            'execution_time_seconds': round(execution_time, 2),
            'script': 'verify_intervals_integrity.py',
            'version': '4.0'
        },
        'summary': {
            'total_models': len(results),
            'models_ok': sum(1 for r in results if r['overall_status'] == 'OK'),
            'models_warning': sum(1 for r in results if r['overall_status'] == 'WARNING'),
            'models_error': sum(1 for r in results if r['overall_status'] == 'ERROR'),
            'total_records_verified': sum(r['total_records'] for r in results),
            'total_intervals': sum(len(r['intervals']) for r in results)
        },
        'models': results
    }

    json_file = f'output/integrity/intervals_verification_{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    # Reporte CSV resumido
    csv_file = f'output/integrity/intervals_summary_{timestamp}.csv'
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("model,table,total_records,intervals,status\n")
        for r in results:
            f.write(f"{r['model']},{r['table']},{r['total_records']},{len(r['intervals'])},{r['overall_status']}\n")

    # Reporte TXT detallado
    txt_file = f'output/integrity/intervals_detail_{timestamp}.txt'
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("REPORTE DE VERIFICACIÓN DE INTEGRIDAD POR INTERVALOS\n")
        f.write(f"Odoo DB Sanitizer v4.0\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")

        f.write(f"📊 RESUMEN GENERAL\n")
        f.write(f"{'─'*80}\n")
        f.write(f"  Modelos verificados: {report_data['summary']['total_models']}\n")
        f.write(f"  ✅ OK: {report_data['summary']['models_ok']}\n")
        f.write(f"  ⚠️  Advertencias: {report_data['summary']['models_warning']}\n")
        f.write(f"  ❌ Errores: {report_data['summary']['models_error']}\n")
        f.write(f"  Total registros verificados: {report_data['summary']['total_records_verified']:,}\n")
        f.write(f"  Total intervalos: {report_data['summary']['total_intervals']}\n")
        f.write(f"  Tiempo de ejecución: {execution_time:.2f}s\n\n")

        for model_result in results:
            f.write(f"\n{'='*80}\n")
            f.write(f"Modelo: {model_result['model']} ({model_result['table']})\n")
            f.write(f"Estado: {model_result['overall_status']} | Registros: {model_result['total_records']:,}\n")
            f.write(f"{'='*80}\n")

            for idx, interval_data in enumerate(model_result['intervals'], 1):
                seq = interval_data['sequence']
                fk = interval_data['foreign_keys']

                f.write(f"\n  Intervalo {idx}: {seq['interval']}\n")
                f.write(f"  Rango: {seq['range']}\n")
                f.write(f"  Registros: {seq['checks']['records_count']:,}\n")
                f.write(f"  Gaps: {seq['checks']['gaps_count']}\n")
                f.write(f"  Duplicados: {seq['checks']['duplicates']}\n")
                f.write(f"  Densidad: {seq['checks']['density_percent']}%\n")
                f.write(f"  Estado secuencia: {seq['status']} - {seq['message']}\n")

                if fk['status'] != 'SKIP':
                    f.write(f"  Estado FKs: {fk['status']} - {fk['message']}\n")
                    if fk.get('fk_checks'):
                        for fk_check in fk['fk_checks']:
                            if fk_check['broken_count'] > 0:
                                f.write(f"    ❌ {fk_check['fk_table']}.{fk_check['fk_column']}: {fk_check['broken_count']} rotas\n")

    print(f"\n{'='*70}")
    print(f"📊 REPORTES GENERADOS:")
    print(f"  JSON detallado: {json_file}")
    print(f"  CSV resumido:   {csv_file}")
    print(f"  TXT detallado:  {txt_file}")

    return report_data

# ══════════════════════════════════════════════════════════════
#                    FUNCIÓN PRINCIPAL
# ══════════════════════════════════════════════════════════════

def main():
    """Función principal"""

    import time
    start_time = time.time()

    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Verificación de Integridad por Intervalos v4.0         ║")
    print("║  Odoo Database Sanitizer                                 ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    try:
        # 1. Cargar credenciales
        print("📋 Cargando credenciales...")
        credentials = load_credentials()

        # 2. Conectar a base de datos
        print("🔌 Conectando a base de datos...")
        conn = connect_database(credentials)

        # 3. Cargar configuración de modelos
        print("📄 Cargando configuración de modelos...")
        config = load_models_config()

        # 4. Verificar modelos
        results = []
        execution_order = config.get('execution_order', [])
        models_config = config.get('models', {})

        total_models = len(execution_order)
        print(f"📦 Total de modelos a verificar: {total_models}\n")

        for idx, model_name in enumerate(execution_order, 1):
            if model_name not in models_config:
                continue

            model_config = models_config[model_name]

            # Skip si no está enabled
            if not model_config.get('enabled', True):
                print(f"[{idx}/{total_models}] {model_name} - DESHABILITADO - SKIP")
                continue

            print(f"[{idx}/{total_models}] Verificando {model_name}...")

            result = verify_model(conn, model_name, model_config)

            if result:
                results.append(result)

        # 5. Generar reportes
        execution_time = time.time() - start_time

        print(f"\n{'='*70}")
        print("📊 Generando reportes...")

        report_data = generate_report(results, execution_time)

        # 6. Resumen final en consola
        print(f"\n{'='*70}")
        print("📊 RESUMEN FINAL:")
        print(f"{'─'*70}")
        print(f"  ✅ Modelos OK:        {report_data['summary']['models_ok']}")
        print(f"  ⚠️  Advertencias:      {report_data['summary']['models_warning']}")
        print(f"  ❌ Errores:           {report_data['summary']['models_error']}")
        print(f"  📊 Total verificados: {report_data['summary']['total_models']}")
        print(f"  ⏱️  Tiempo total:      {execution_time:.2f}s")
        print(f"{'='*70}")

        # 7. Cerrar conexión
        conn.close()

        # 8. Exit code según resultados
        if report_data['summary']['models_error'] > 0:
            print("\n❌ Verificación completada con ERRORES")
            sys.exit(1)
        elif report_data['summary']['models_warning'] > 0:
            print("\n⚠️  Verificación completada con ADVERTENCIAS")
            sys.exit(0)
        else:
            print("\n✅ Verificación completada EXITOSAMENTE")
            sys.exit(0)

    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
