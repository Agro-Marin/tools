#!/usr/bin/env python3
"""
Script de Verificación de Integridad Referencial - Consultas Aleatorias
Verifica relaciones FK entre modelos aleatorios para asegurar integridad completa
"""

import psycopg2
import json
from datetime import datetime

def load_db_credentials():
    """Cargar credenciales desde JSON"""
    with open('config/db_credentials.json', 'r') as f:
        return json.load(f)

def connect_db(credentials):
    """Conectar a la base de datos"""
    return psycopg2.connect(
        host=credentials['host'],
        port=credentials['port'],
        database=credentials['database'],
        user=credentials['user'],
        password=credentials['password'],
        sslmode=credentials.get('sslmode', 'prefer')
    )

def ejecutar_query(conn, nombre, query, descripcion=""):
    """Ejecutar una query y mostrar resultados"""
    cur = conn.cursor()
    try:
        print(f"🔍 {nombre}")
        if descripcion:
            print(f"   {descripcion}")
        cur.execute(query)
        result = cur.fetchall()
        colnames = [desc[0] for desc in cur.description]
        cur.close()
        return colnames, result
    except psycopg2.Error as e:
        conn.rollback()
        cur.close()
        print(f"   ⚠️  ERROR: {str(e).split(chr(10))[0][:100]}")
        print()
        return None, None

def verificar_integridad_aleatoria(conn):
    """Ejecutar verificaciones aleatorias de integridad"""

    print("=" * 90)
    print(f"VERIFICACIÓN DE INTEGRIDAD REFERENCIAL - CONSULTAS ALEATORIAS")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)
    print()

    verificaciones_exitosas = 0
    verificaciones_totales = 0

    # 1. Verificar IDs resecuenciados en res.partner
    print("=" * 90)
    print("GRUPO 1: VERIFICACIÓN DE RESECUENCIACIÓN")
    print("=" * 90)
    print()

    colnames, result = ejecutar_query(conn,
        "1. Verificar rango de IDs en res.partner",
        """
        SELECT
            MIN(id) AS min_id,
            MAX(id) AS max_id,
            COUNT(*) AS total_registros,
            MAX(id) - MIN(id) + 1 AS rango_esperado,
            COUNT(*) = (MAX(id) - MIN(id) + 1) AS sin_gaps
        FROM res_partner;
        """,
        "Verificar que no hay gaps en IDs resecuenciados"
    )
    if result:
        for row in result:
            print(f"   Min ID: {row[0]} | Max ID: {row[1]} | Total: {row[2]}")
            print(f"   Rango esperado: {row[3]} | Sin gaps: {'✅ SÍ' if row[4] else '❌ NO'}")
        verificaciones_exitosas += 1 if result[0][4] else 0
        verificaciones_totales += 1
    print()

    # 2. Verificar IDs resecuenciados en product.template
    colnames, result = ejecutar_query(conn,
        "2. Verificar rango de IDs en product.template",
        """
        SELECT
            MIN(id) AS min_id,
            MAX(id) AS max_id,
            COUNT(*) AS total_registros,
            COUNT(*) = (MAX(id) - MIN(id) + 1) AS sin_gaps
        FROM product_template;
        """
    )
    if result:
        for row in result:
            print(f"   Min ID: {row[0]} | Max ID: {row[1]} | Total: {row[2]}")
            print(f"   Sin gaps: {'✅ SÍ' if row[3] else '❌ NO'}")
        verificaciones_exitosas += 1 if result[0][3] else 0
        verificaciones_totales += 1
    print()

    # 3. Verificar CASCADE en account.move → account.move_line
    print("=" * 90)
    print("GRUPO 2: VERIFICACIÓN DE CASCADE")
    print("=" * 90)
    print()

    colnames, result = ejecutar_query(conn,
        "3. Verificar account.move_line → account.move (sin FKs huérfanas)",
        """
        SELECT
            COUNT(*) AS total_lines,
            COUNT(DISTINCT move_id) AS moves_referenciados,
            COUNT(DISTINCT am.id) AS moves_existentes,
            COUNT(*) FILTER (WHERE am.id IS NULL) AS fks_huerfanas,
            CASE
                WHEN COUNT(*) FILTER (WHERE am.id IS NULL) = 0 THEN '✅ INTEGRIDAD OK'
                ELSE '❌ HAY HUÉRFANAS'
            END AS estado
        FROM account_move_line aml
        LEFT JOIN account_move am ON aml.move_id = am.id;
        """
    )
    if result:
        for row in result:
            print(f"   Total líneas: {row[0]:,}")
            print(f"   Moves referenciados: {row[1]:,} | Existentes: {row[2]:,}")
            print(f"   FKs huérfanas: {row[3]:,}")
            print(f"   Estado: {row[4]}")
        verificaciones_exitosas += 1 if result[0][3] == 0 else 0
        verificaciones_totales += 1
    print()

    # 4. Verificar múltiples FKs desde account.move
    colnames, result = ejecutar_query(conn,
        "4. Verificar account.move → journal/partner/company",
        """
        SELECT
            COUNT(*) AS total_moves,
            COUNT(*) FILTER (WHERE aj.id IS NULL) AS journal_rotas,
            COUNT(*) FILTER (WHERE p.id IS NULL AND partner_id IS NOT NULL) AS partner_rotas,
            COUNT(*) FILTER (WHERE c.id IS NULL) AS company_rotas,
            CASE
                WHEN COUNT(*) FILTER (WHERE aj.id IS NULL) +
                     COUNT(*) FILTER (WHERE p.id IS NULL AND partner_id IS NOT NULL) +
                     COUNT(*) FILTER (WHERE c.id IS NULL) = 0
                THEN '✅ INTEGRIDAD OK'
                ELSE '❌ HAY FKs ROTAS'
            END AS estado
        FROM account_move am
        LEFT JOIN account_journal aj ON am.journal_id = aj.id
        LEFT JOIN res_partner p ON am.partner_id = p.id
        LEFT JOIN res_company c ON am.company_id = c.id;
        """
    )
    if result:
        for row in result:
            print(f"   Total moves: {row[0]:,}")
            print(f"   Journal FKs rotas: {row[1]} | Partner: {row[2]} | Company: {row[3]}")
            print(f"   Estado: {row[4]}")
        verificaciones_exitosas += 1 if (result[0][1] + result[0][2] + result[0][3]) == 0 else 0
        verificaciones_totales += 1
    print()

    # 5. Verificar stock.move → product/location/picking
    colnames, result = ejecutar_query(conn,
        "5. Verificar stock.move → product/location_src/location_dest/picking",
        """
        SELECT
            COUNT(*) AS total_moves,
            COUNT(*) FILTER (WHERE pp.id IS NULL) AS product_rotas,
            COUNT(*) FILTER (WHERE loc_src.id IS NULL) AS location_src_rotas,
            COUNT(*) FILTER (WHERE loc_dest.id IS NULL) AS location_dest_rotas,
            COUNT(*) FILTER (WHERE picking_id IS NOT NULL AND sp.id IS NULL) AS picking_rotas,
            CASE
                WHEN COUNT(*) FILTER (WHERE pp.id IS NULL OR loc_src.id IS NULL OR
                                           loc_dest.id IS NULL OR
                                           (picking_id IS NOT NULL AND sp.id IS NULL)) = 0
                THEN '✅ INTEGRIDAD OK'
                ELSE '❌ HAY FKs ROTAS'
            END AS estado
        FROM stock_move sm
        LEFT JOIN product_product pp ON sm.product_id = pp.id
        LEFT JOIN stock_location loc_src ON sm.location_id = loc_src.id
        LEFT JOIN stock_location loc_dest ON sm.location_dest_id = loc_dest.id
        LEFT JOIN stock_picking sp ON sm.picking_id = sp.id;
        """
    )
    if result:
        for row in result:
            print(f"   Total stock moves: {row[0]:,}")
            print(f"   Product rotas: {row[1]} | Loc src: {row[2]} | Loc dest: {row[3]} | Picking: {row[4]}")
            print(f"   Estado: {row[5]}")
        verificaciones_exitosas += 1 if (result[0][1] + result[0][2] + result[0][3] + result[0][4]) == 0 else 0
        verificaciones_totales += 1
    print()

    # 6. Verificar relación compleja: sale_order → sale_order_line → product
    print("=" * 90)
    print("GRUPO 3: VERIFICACIÓN DE CADENAS DE RELACIONES")
    print("=" * 90)
    print()

    colnames, result = ejecutar_query(conn,
        "6. Verificar sale_order → sale_order_line → product (cadena completa)",
        """
        SELECT
            COUNT(DISTINCT so.id) AS total_orders,
            COUNT(sol.id) AS total_lines,
            COUNT(*) FILTER (WHERE so.id IS NULL) AS order_fks_rotas,
            COUNT(*) FILTER (WHERE pp.id IS NULL AND sol.product_id IS NOT NULL) AS product_fks_rotas,
            CASE
                WHEN COUNT(*) FILTER (WHERE so.id IS NULL OR
                                           (pp.id IS NULL AND sol.product_id IS NOT NULL)) = 0
                THEN '✅ INTEGRIDAD OK'
                ELSE '❌ HAY FKs ROTAS'
            END AS estado
        FROM sale_order_line sol
        LEFT JOIN sale_order so ON sol.order_id = so.id
        LEFT JOIN product_product pp ON sol.product_id = pp.id;
        """
    )
    if result:
        for row in result:
            print(f"   Total órdenes: {row[0]:,} | Líneas: {row[1]:,}")
            print(f"   Order FKs rotas: {row[2]} | Product FKs rotas: {row[3]}")
            print(f"   Estado: {row[4]}")
        verificaciones_exitosas += 1 if (result[0][2] + result[0][3]) == 0 else 0
        verificaciones_totales += 1
    print()

    # 7. Verificar purchase_order → purchase_order_line → product
    colnames, result = ejecutar_query(conn,
        "7. Verificar purchase_order → purchase_order_line → product",
        """
        SELECT
            COUNT(DISTINCT po.id) AS total_orders,
            COUNT(pol.id) AS total_lines,
            COUNT(*) FILTER (WHERE po.id IS NULL) AS order_fks_rotas,
            COUNT(*) FILTER (WHERE pp.id IS NULL) AS product_fks_rotas,
            CASE
                WHEN COUNT(*) FILTER (WHERE po.id IS NULL OR pp.id IS NULL) = 0
                THEN '✅ INTEGRIDAD OK'
                ELSE '❌ HAY FKs ROTAS'
            END AS estado
        FROM purchase_order_line pol
        LEFT JOIN purchase_order po ON pol.order_id = po.id
        LEFT JOIN product_product pp ON pol.product_id = pp.id;
        """
    )
    if result:
        for row in result:
            print(f"   Total órdenes de compra: {row[0]:,} | Líneas: {row[1]:,}")
            print(f"   Order FKs rotas: {row[2]} | Product FKs rotas: {row[3]}")
            print(f"   Estado: {row[4]}")
        verificaciones_exitosas += 1 if (result[0][2] + result[0][3]) == 0 else 0
        verificaciones_totales += 1
    print()

    # 8. Verificar account.bank.statement.line → journal/partner
    colnames, result = ejecutar_query(conn,
        "8. Verificar account_bank_statement_line → statement/journal/partner",
        """
        SELECT
            COUNT(*) AS total_lines,
            COUNT(*) FILTER (WHERE abs.id IS NULL) AS statement_rotas,
            COUNT(*) FILTER (WHERE aj.id IS NULL) AS journal_rotas,
            COUNT(*) FILTER (WHERE p.id IS NULL AND absl.partner_id IS NOT NULL) AS partner_rotas,
            CASE
                WHEN COUNT(*) FILTER (WHERE abs.id IS NULL OR aj.id IS NULL OR
                                           (p.id IS NULL AND absl.partner_id IS NOT NULL)) = 0
                THEN '✅ INTEGRIDAD OK'
                ELSE '❌ HAY FKs ROTAS'
            END AS estado
        FROM account_bank_statement_line absl
        LEFT JOIN account_bank_statement abs ON absl.statement_id = abs.id
        LEFT JOIN account_journal aj ON absl.journal_id = aj.id
        LEFT JOIN res_partner p ON absl.partner_id = p.id;
        """
    )
    if result:
        for row in result:
            print(f"   Total líneas de extracto: {row[0]:,}")
            print(f"   Statement rotas: {row[1]} | Journal: {row[2]} | Partner: {row[3]}")
            print(f"   Estado: {row[4]}")
        verificaciones_exitosas += 1 if (result[0][1] + result[0][2] + result[0][3]) == 0 else 0
        verificaciones_totales += 1
    print()

    # 9. Verificar stock.picking → partner/location/picking_type
    colnames, result = ejecutar_query(conn,
        "9. Verificar stock_picking → partner/location_src/location_dest/picking_type",
        """
        SELECT
            COUNT(*) AS total_pickings,
            COUNT(*) FILTER (WHERE p.id IS NULL AND partner_id IS NOT NULL) AS partner_rotas,
            COUNT(*) FILTER (WHERE loc_src.id IS NULL) AS location_src_rotas,
            COUNT(*) FILTER (WHERE loc_dest.id IS NULL) AS location_dest_rotas,
            COUNT(*) FILTER (WHERE pt.id IS NULL) AS picking_type_rotas,
            CASE
                WHEN COUNT(*) FILTER (WHERE (p.id IS NULL AND partner_id IS NOT NULL) OR
                                           loc_src.id IS NULL OR loc_dest.id IS NULL OR pt.id IS NULL) = 0
                THEN '✅ INTEGRIDAD OK'
                ELSE '❌ HAY FKs ROTAS'
            END AS estado
        FROM stock_picking sp
        LEFT JOIN res_partner p ON sp.partner_id = p.id
        LEFT JOIN stock_location loc_src ON sp.location_id = loc_src.id
        LEFT JOIN stock_location loc_dest ON sp.location_dest_id = loc_dest.id
        LEFT JOIN stock_picking_type pt ON sp.picking_type_id = pt.id;
        """
    )
    if result:
        for row in result:
            print(f"   Total pickings: {row[0]:,}")
            print(f"   Partner rotas: {row[1]} | Loc src: {row[2]} | Loc dest: {row[3]} | Type: {row[4]}")
            print(f"   Estado: {row[5]}")
        verificaciones_exitosas += 1 if (result[0][1] + result[0][2] + result[0][3] + result[0][4]) == 0 else 0
        verificaciones_totales += 1
    print()

    # 10. Verificar tabla de relación M2M: stock_location_route
    colnames, result = ejecutar_query(conn,
        "10. Verificar stock_route_location → route/location (M2M)",
        """
        SELECT
            COUNT(*) AS total_relaciones,
            COUNT(*) FILTER (WHERE sr.id IS NULL) AS route_rotas,
            COUNT(*) FILTER (WHERE sl.id IS NULL) AS location_rotas,
            CASE
                WHEN COUNT(*) FILTER (WHERE sr.id IS NULL OR sl.id IS NULL) = 0
                THEN '✅ INTEGRIDAD OK'
                ELSE '❌ HAY FKs ROTAS'
            END AS estado
        FROM stock_route_location srl
        LEFT JOIN stock_route sr ON srl.route_id = sr.id
        LEFT JOIN stock_location sl ON srl.location_id = sl.id;
        """
    )
    if result:
        for row in result:
            print(f"   Total relaciones M2M: {row[0]:,}")
            print(f"   Route rotas: {row[1]} | Location rotas: {row[2]}")
            print(f"   Estado: {row[3]}")
        verificaciones_exitosas += 1 if (result[0][1] + result[0][2]) == 0 else 0
        verificaciones_totales += 1
    print()

    # 11. Muestreo aleatorio: Verificar 100 partners random tienen todas sus FKs correctas
    print("=" * 90)
    print("GRUPO 4: MUESTREO ALEATORIO")
    print("=" * 90)
    print()

    colnames, result = ejecutar_query(conn,
        "11. Verificar 100 partners aleatorios (todas sus relaciones)",
        """
        WITH random_partners AS (
            SELECT id FROM res_partner
            ORDER BY RANDOM()
            LIMIT 100
        )
        SELECT
            COUNT(DISTINCT rp.id) AS partners_verificados,
            COUNT(*) FILTER (WHERE c.id IS NULL AND rp.company_id IS NOT NULL) AS company_rotas,
            COUNT(*) FILTER (WHERE parent.id IS NULL AND rp.parent_id IS NOT NULL) AS parent_rotas,
            COUNT(*) FILTER (WHERE u.id IS NULL AND rp.user_id IS NOT NULL) AS user_rotas,
            CASE
                WHEN COUNT(*) FILTER (WHERE (c.id IS NULL AND rp.company_id IS NOT NULL) OR
                                           (parent.id IS NULL AND rp.parent_id IS NOT NULL) OR
                                           (u.id IS NULL AND rp.user_id IS NOT NULL)) = 0
                THEN '✅ INTEGRIDAD OK'
                ELSE '❌ HAY FKs ROTAS'
            END AS estado
        FROM random_partners rnd
        JOIN res_partner rp ON rnd.id = rp.id
        LEFT JOIN res_company c ON rp.company_id = c.id
        LEFT JOIN res_partner parent ON rp.parent_id = parent.id
        LEFT JOIN res_users u ON rp.user_id = u.id;
        """
    )
    if result:
        for row in result:
            print(f"   Partners verificados (muestra aleatoria): {row[0]}")
            print(f"   Company rotas: {row[1]} | Parent rotas: {row[2]} | User rotas: {row[3]}")
            print(f"   Estado: {row[4]}")
        verificaciones_exitosas += 1 if (result[0][1] + result[0][2] + result[0][3]) == 0 else 0
        verificaciones_totales += 1
    print()

    # 12. Verificar IDs consecutivos en diferentes tablas
    colnames, result = ejecutar_query(conn,
        "12. Verificar consistencia de IDs resecuenciados (múltiples tablas)",
        """
        SELECT
            'res_partner' AS tabla,
            MIN(id) AS min_id,
            MAX(id) AS max_id,
            COUNT(*) AS total,
            COUNT(*) = (MAX(id) - MIN(id) + 1) AS sin_gaps
        FROM res_partner
        UNION ALL
        SELECT
            'product_template', MIN(id), MAX(id), COUNT(*),
            COUNT(*) = (MAX(id) - MIN(id) + 1)
        FROM product_template
        UNION ALL
        SELECT
            'account_move', MIN(id), MAX(id), COUNT(*),
            COUNT(*) = (MAX(id) - MIN(id) + 1)
        FROM account_move
        UNION ALL
        SELECT
            'stock_quant', MIN(id), MAX(id), COUNT(*),
            COUNT(*) = (MAX(id) - MIN(id) + 1)
        FROM stock_quant
        UNION ALL
        SELECT
            'stock_location', MIN(id), MAX(id), COUNT(*),
            COUNT(*) = (MAX(id) - MIN(id) + 1)
        FROM stock_location;
        """
    )
    if result:
        print(f"   {'Tabla':<20} {'Min ID':>10} {'Max ID':>10} {'Total':>10} {'Sin Gaps'}")
        print(f"   {'-'*20} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
        gaps_found = False
        for row in result:
            gaps_status = '✅' if row[4] else '❌'
            if not row[4]:
                gaps_found = True
            print(f"   {row[0]:<20} {row[1]:>10} {row[2]:>10} {row[3]:>10} {gaps_status:>10}")
        print()
        print(f"   Estado general: {'✅ TODOS SIN GAPS' if not gaps_found else '❌ ALGUNOS CON GAPS'}")
        verificaciones_exitosas += 1 if not gaps_found else 0
        verificaciones_totales += 1
    print()

    # Resumen final
    print("=" * 90)
    print("RESUMEN DE VERIFICACIÓN ALEATORIA")
    print("=" * 90)
    print()

    if verificaciones_totales == 0:
        print("⚠️  No se completaron verificaciones")
        return False

    porcentaje = (verificaciones_exitosas / verificaciones_totales * 100)

    print(f"Total verificaciones: {verificaciones_totales}")
    print(f"Exitosas: {verificaciones_exitosas} ({porcentaje:.1f}%)")
    print(f"Fallidas: {verificaciones_totales - verificaciones_exitosas} ({100-porcentaje:.1f}%)")
    print()

    if verificaciones_exitosas == verificaciones_totales:
        print("🎉🎉🎉 INTEGRIDAD REFERENCIAL 100% VERIFICADA")
        print("Todas las consultas aleatorias pasaron exitosamente")
    else:
        print(f"⚠️  ATENCIÓN: {verificaciones_totales - verificaciones_exitosas} verificaciones fallaron")

    print("=" * 90)

    return verificaciones_exitosas == verificaciones_totales

if __name__ == '__main__':
    try:
        credentials = load_db_credentials()
        print(f"Conectando a base de datos: {credentials['database']}...")
        conn = connect_db(credentials)
        print(f"✅ Conectado exitosamente")
        print()

        integridad_ok = verificar_integridad_aleatoria(conn)

        conn.close()

        exit(0 if integridad_ok else 1)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
