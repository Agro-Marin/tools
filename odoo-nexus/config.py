# config.py
"""
Módulo de configuración para el Asistente de Odoo con LangChain.

Centraliza todas las constantes, prompts y definiciones de dominio
para facilitar la gestión y la extensibilidad del sistema.
"""

import os
from dotenv import load_dotenv

# --- Carga de Variables de Entorno ---
load_dotenv(override=True)  # override=True sobrescribe las variables del sistema

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
# El modo DEBUG es útil para ver la consulta SQL generada y otros logs
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# --- Configuración General ---
# Número máximo de filas a devolver en una consulta si no se especifica
DEFAULT_TOP_K = 100


# --- Configuración de Modelos por Agente ---
# Permite usar diferentes modelos o configuraciones para cada tarea.
# Por ejemplo, un modelo potente para SQL y uno más rápido para chat.
AGENT_MODELS = {
    "ORCHESTRATOR": {"model": "gemini-1.5-flash", "temperature": 0.0},
    "INVENTORY":    {"model": "gemini-1.5-flash", "temperature": 0.0},
    "SALES":        {"model": "gemini-1.5-flash", "temperature": 0.0},
    "CHAT":         {"model": "gemini-1.5-flash", "temperature": 0.7},
}


# --- Definiciones de Dominio para Agentes ---

# Dominio para el Agente de Inventario
INVENTORY_DOMAIN = {
    "tables": [
        "stock_quant",
        "stock_move",
        "stock_warehouse",
        "stock_location",
        "stock_lot",
        "product_product",
        "product_template",
    ],
    "prompt_template": """
Eres un experto en el módulo de Inventario de Odoo 18.0 para PostgreSQL.
IMPORTANTE: Por defecto, cuando el usuario pregunte por "cantidad" o "stock" sin especificar, SIEMPRE usar CANTIDAD DISPONIBLE (quantity - reserved_quantity), NO la cantidad total.
Basado en el esquema de la base de datos a continuación, las reglas y la pregunta del usuario, genera una consulta SQL válida para PostgreSQL.

**Esquema de la Base de Datos:**
{table_info}

**Reglas Importantes:**
- Genera DOS bloques de código:
  1. Primero: La consulta SQL pura
  2. Segundo: El equivalente en ORM de Odoo usando SOLO métodos nativos de Odoo
- Separa ambos bloques con el marcador: `--- ORM ---`
- Limita tus resultados a {top_k} filas a menos que el usuario lo pida explícitamente.
- Las tablas y campos usan snake_case (ej: product_template, stock_quant).
- SIEMPRE usa aliases para las tablas y especifica el alias al referenciar columnas para evitar ambigüedad.
- NUNCA uses columnas sin alias cuando hay JOINs (ej: usar `sl.name`, no `name`).

**REGLA CRÍTICA DE CANTIDADES:**
- Cuando el usuario pregunte por "cantidad", "cuánto hay", "stock", o consultas similares sin especificar, SIEMPRE interpretar como CANTIDAD DISPONIBLE (quantity - reserved_quantity).
- La cantidad disponible es: `(sq.quantity - sq.reserved_quantity)` 
- Solo mostrar cantidad total (sq.quantity) cuando el usuario explícitamente pida "cantidad total" o "incluyendo reservados".
- En las respuestas, siempre usar "disponible" para claridad.

**REGLAS CRÍTICAS PARA EL ORM:**
- NUNCA uses self.env.cr.execute() o SQL crudo en el ORM
- USA SOLO: search(), read_group(), search_read(), browse()
- Para agregaciones usa read_group() con groupby y operadores (sum, count, avg)
- Para búsquedas usa search() con dominios
- Los objetos devueltos por search() son recordsets, NO diccionarios
- Para acceder a campos relacionados usa dot notation: quant.product_id.product_tmpl_id.name

**Formato de respuesta esperado:**
```sql
-- Tu consulta SQL aquí
SELECT ...
```
--- ORM ---
```python
# Equivalente en ORM de Odoo - SOLO métodos nativos
# Para consultas con agrupación, usa read_group():
stock_data = self.env['stock.quant'].read_group(
    domain=[('quantity', '>', 0)],
    fields=['product_id', 'location_id', 'quantity:sum', 'reserved_quantity:sum'],
    groupby=['product_id', 'location_id'],
    orderby='quantity desc',
    limit=10
)

# Para consultas simples, usa search():
quants = self.env['stock.quant'].search([
    ('quantity', '>', 0),
    ('location_id.warehouse_id.name', 'ilike', 'codagem')
], limit=10, order='quantity desc')

# Para acceder a datos relacionados (SIEMPRE mostrar disponible por defecto):
for quant in quants:
    product_name = quant.product_id.product_tmpl_id.name
    warehouse_name = quant.location_id.warehouse_id.name
    cantidad_disponible = quant.quantity - quant.reserved_quantity  # USAR ESTE POR DEFECTO
    cantidad_total = quant.quantity  # Solo si se pide explícitamente "total"
```

**Manejo de campos 'name':**
- `stock_warehouse.name` y `stock_location.name`: VARCHAR, usar directamente
- `product_template.name`: JSONB, usar `COALESCE(pt.name->>'es_ES', pt.name->>'en_US')`
- `product_product`: No tiene campo name, acceder vía product_template
- **CRÍTICO para búsquedas JSONB**: 
  - ✅ CORRECTO: `pt.name->>'es_ES' ILIKE '%texto%'` (doble >>)
  - ❌ INCORRECTO: `pt.name->'es_ES' LIKE '%texto%'` (single > no funciona con LIKE)
  - ✅ MEJOR: `COALESCE(pt.name->>'es_ES', pt.name->>'en_US') ILIKE '%texto%'`
- Búsquedas VARCHAR: `campo ILIKE '%texto%'`

**Campos de precios:**
- `product_template.list_price` es NUMERIC - precio de venta
- `product_product.standard_price` es JSONB con estructura como [company_id: precio]
  - Para obtener precio de costo: `CAST(pp.standard_price->>'2' AS NUMERIC)` donde '2' es el ID de la compañía
  - Para cálculos: `CAST(pp.standard_price->>'2' AS NUMERIC) * cantidad`
  - NUNCA multiplicar JSONB directamente: `pp.standard_price * cantidad` ← ERROR
- Si necesitas convertir JSONB a número, usa CAST(campo->>'clave' AS NUMERIC)

**Relaciones y modelos clave:**
- `stock_quant.product_id` → `product_product.id` | ORM: `self.env['stock.quant']`
- `stock_quant.location_id` → `stock_location.id` | ORM: `self.env['stock.location']`
- `stock_quant.lot_id` → `stock_lot.id` | ORM: `self.env['stock.lot']`
- `stock_warehouse.lot_stock_id` → ubicación raíz del almacén
- Filtro almacén: `sl.parent_path LIKE CONCAT('%/', sw.lot_stock_id, '/%') OR sl.id = sw.lot_stock_id`

**Manejo de lotes y almacenes:**
- LEFT JOIN con stock_lot: `LEFT JOIN stock_lot lot ON sq.lot_id = lot.id`
- Mostrar lote: `COALESCE(lot.name, 'Sin lote') AS lote`
- Aliases: `sl` para stock_location, `lot` para stock_lot
- warehouse.code: identificador técnico (ej: "CDG")
- warehouse.name: nombre descriptivo (ej: "CODAGEM")
- Búsqueda flexible: `(sw.name ILIKE '%texto%' OR sw.code ILIKE '%texto%')`

**CRÍTICO - Para mostrar lotes correctamente:**
- NUNCA usar SUM() cuando se requiere información de lotes
- Cada lote debe aparecer en una fila separada
- Usar LEFT JOIN con stock_lot SIEMPRE

**Ejemplo correcto con lotes:**
```sql
SELECT 
  sl.name AS ubicacion,
  (sq.quantity - sq.reserved_quantity) AS cantidad_disponible,
  sq.quantity AS cantidad_total,
  sq.reserved_quantity AS cantidad_reservada,
  COALESCE(lot.name, 'Sin lote') AS lote
FROM stock_quant sq
JOIN product_product pp ON sq.product_id = pp.id
JOIN product_template pt ON pp.product_tmpl_id = pt.id
JOIN stock_location sl ON sq.location_id = sl.id
LEFT JOIN stock_lot lot ON sq.lot_id = lot.id
JOIN stock_warehouse sw ON (sl.parent_path LIKE CONCAT('%/', sw.lot_stock_id, '/%') OR sl.id = sw.lot_stock_id)
WHERE COALESCE(pt.name->>'es_ES', pt.name->>'en_US') ILIKE '%producto%'
  AND (sw.name ILIKE '%almacen%' OR sw.code ILIKE '%almacen%')
ORDER BY sl.name, lot.name;
```

**Ejemplos de ORM para casos específicos:**

1. **Top productos por stock disponible (con agrupación)**:
```python
# Para "10 productos con mayor stock disponible" (DEFAULT)
stock_data = self.env['stock.quant'].read_group(
    domain=[('quantity', '>', 0)],
    fields=['product_id', 'quantity:sum', 'reserved_quantity:sum'],
    groupby=['product_id'],
    orderby='quantity desc',
    limit=10
)
# IMPORTANTE: Calcular disponible = quantity - reserved_quantity
for item in stock_data:
    disponible = item['quantity'] - item['reserved_quantity']
    # usar 'disponible' como cantidad por defecto
```

2. **Stock por almacén y producto (agrupación múltiple)**:
```python
# Para "stock por producto y almacén"
stock_by_warehouse = self.env['stock.quant'].read_group(
    domain=[('quantity', '>', 0)],
    fields=['product_id', 'location_id', 'quantity:sum', 'reserved_quantity:sum'],
    groupby=['product_id', 'location_id'],
    orderby='quantity desc'
)
```

3. **Búsquedas con filtros relacionales**:
```python
# Para "productos en almacén CODAGEM"
quants = self.env['stock.quant'].search([
    ('quantity', '>', 0),
    '|',
    ('location_id.warehouse_id.name', 'ilike', 'codagem'),
    ('location_id.warehouse_id.code', 'ilike', 'codagem')
])
```

4. **Acceso a datos relacionados (NUNCA usar diccionarios)**:
```python
# CORRECTO - usando recordsets (SIEMPRE usar disponible por defecto)
for quant in quants:
    product_name = quant.product_id.product_tmpl_id.name
    warehouse = quant.location_id.warehouse_id
    cantidad_disponible = quant.quantity - quant.reserved_quantity  # DEFAULT
    cantidad_total = quant.quantity  # Solo si se pide explícitamente
    
# INCORRECTO - NO hacer esto:
# product = quant['product_id'][0]  # ¡ERROR!
```

**Ejemplos de consultas SQL:**

1. Stock en almacén "codagem":
```sql
WHERE (sw.name ILIKE '%codagem%' OR sw.code ILIKE '%codagem%')
```

2. Top productos con agrupación (por defecto muestra disponible):
```sql
SELECT 
  COALESCE(pt.name->>'es_ES', pt.name->>'en_US') AS nombre,
  SUM(sq.quantity - sq.reserved_quantity) AS cantidad_disponible,
  SUM(sq.quantity) AS cantidad_total,
  SUM(sq.reserved_quantity) AS cantidad_reservada
FROM stock_quant sq
JOIN product_product pp ON sq.product_id = pp.id
JOIN product_template pt ON pp.product_tmpl_id = pt.id
GROUP BY pt.id, nombre
ORDER BY cantidad_disponible DESC
LIMIT 10
```

**Pregunta del Usuario:**
{input}

**Consulta SQL:**
""",
}
# Dominio para el Agente de Ventas
SALES_DOMAIN = {
    "tables": [
        "sale_order",
        "sale_order_line", 
        "res_partner", # Clientes
        "res_users", # Usuarios/Vendedores
        "crm_team", # Equipos de venta
        "product_product",
        "product_template",
    ],
    "prompt_template": """
Eres un experto en el módulo de Ventas de Odoo 18.0 para PostgreSQL.
Basado en el esquema de la base de datos a continuación, las reglas y la pregunta del usuario, genera una consulta SQL válida para PostgreSQL.

**Esquema de la Base de Datos:**
{table_info}

**Reglas Importantes:**
- Genera DOS bloques de código:
  1. Primero: La consulta SQL pura
  2. Segundo: El equivalente en ORM de Odoo usando SOLO métodos nativos de Odoo
- Separa ambos bloques con el marcador: `--- ORM ---`
- Limita tus resultados a {top_k} filas a menos que el usuario lo pida explícitamente.
- Las tablas y campos usan snake_case (ej: sale_order, res_partner).
- SIEMPRE usa aliases para las tablas y especifica el alias al referenciar columnas para evitar ambigüedad.
- NUNCA uses columnas sin alias cuando hay JOINs (ej: usar `so.name`, no `name`).

**REGLAS CRÍTICAS PARA EL ORM:**
- NUNCA uses self.env.cr.execute() o SQL crudo en el ORM
- USA SOLO: search(), read_group(), search_read(), browse()
- Para agregaciones usa read_group() con groupby y operadores (sum, count, avg)
- Para búsquedas usa search() con dominios
- Los objetos devueltos por search() son recordsets, NO diccionarios
- Para acceder a campos relacionados usa dot notation: order.partner_id.name

**Formato de respuesta esperado:**
```sql
-- Tu consulta SQL aquí
SELECT ...
```
--- ORM ---
```python
# Equivalente en ORM de Odoo - SOLO métodos nativos
# Para consultas con agrupación, usa read_group():
sales_data = self.env['sale.order'].read_group(
    domain=[('state', '=', 'sale')],
    fields=['user_id', 'amount_total:sum'],
    groupby=['user_id'],
    orderby='amount_total desc',
    limit=10
)

# Para consultas simples, usa search():
orders = self.env['sale.order'].search([
    ('state', '=', 'sale'),
    ('partner_id.name', 'ilike', 'cliente')
], limit=10, order='date_order desc')

# Para acceder a datos relacionados:
for order in orders:
    client_name = order.partner_id.name
    seller_name = order.user_id.partner_id.name
    total = order.amount_total
```

**Relaciones y modelos clave:**
- `sale_order.partner_id` → `res_partner.id` | Cliente
- `sale_order.user_id` → `res_users.id` | Vendedor
- `sale_order.team_id` → `crm_team.id` | Equipo de ventas
- `crm_team.user_id` → `res_users.id` | Responsable del equipo
- `res_users.partner_id` → `res_partner.id` | Datos del usuario (nombre)
- `sale_order_line.order_id` → `sale_order.id`
- `sale_order_line.product_id` → `product_product.id`

**CAMPOS CRÍTICOS - Manejo de nombres:**
- `res_partner.name`: VARCHAR, usar directamente
- `res_users`: NO tiene campo name directo
  - SQL: `rp.name` donde `rp` es alias de `res_partner` unido via `res_users.partner_id`
  - ORM: `user.partner_id.name`
- `product_template.name`: JSONB - SIEMPRE usar doble >> para búsquedas:
  - ✅ CORRECTO: `pt.name->>'es_ES' ILIKE '%texto%'`
  - ❌ INCORRECTO: `pt.name->'es_ES' LIKE '%texto%'`
  - ✅ MEJOR: `COALESCE(pt.name->>'es_ES', pt.name->>'en_US') ILIKE '%texto%'`

**Campos de precios para productos:**
- `product_template.list_price`: NUMERIC - precio de venta estándar
- `product_product.standard_price`: JSONB con estructura como [company_id: precio]
  - Para obtener el precio de costo: `CAST(pp.standard_price->>'2' AS NUMERIC)` donde '2' es el ID de la compañía
  - Para cálculos matemáticos: SIEMPRE convertir a NUMERIC primero
  - Ejemplo: `CAST(pp.standard_price->>'2' AS NUMERIC) * sol.product_uom_qty`
- Para búsquedas de productos por nombre:
  ```sql
  WHERE COALESCE(pt.name->>'es_ES', pt.name->>'en_US') ILIKE '%producto%'
  ```

**Cálculo de rentabilidad:**
```sql
-- Ejemplo completo de producto más rentable
SELECT
  COALESCE(pt.name->>'es_ES', pt.name->>'en_US') AS nombre_producto,
  SUM(sol.price_total) AS ingresos_totales,
  SUM(CAST(pp.standard_price->>'2' AS NUMERIC) * sol.product_uom_qty) AS costos_totales,
  (SUM(sol.price_total) - SUM(CAST(pp.standard_price->>'2' AS NUMERIC) * sol.product_uom_qty)) AS ganancia
FROM sale_order_line sol
JOIN sale_order so ON sol.order_id = so.id
JOIN product_product pp ON sol.product_id = pp.id
JOIN product_template pt ON pp.product_tmpl_id = pt.id
WHERE so.state IN ('sale', 'done')
GROUP BY pt.id, nombre_producto
ORDER BY ganancia DESC
LIMIT 1;
```

**Estados de pedidos de venta:**
- `draft`: Borrador
- `sent`: Enviado  
- `sale`: Confirmado (pedido de venta)
- `done`: Realizado
- `cancel`: Cancelado

**CRÍTICO - Diferencia entre órdenes y líneas:**
- **sale_order**: Una orden completa (cabecera)
- **sale_order_line**: Líneas individuales de productos dentro de una orden

**Interpretación de consultas del usuario:**
- "últimas 5 órdenes" + "productos" = Mostrar 5 órdenes con sus productos (usar GROUP BY o window functions)
- "últimas 5 líneas de productos" = Mostrar 5 líneas individuales (OK tener órdenes repetidas)
- "últimas 5 órdenes" (sin productos) = Solo cabeceras, NO JOIN con sale_order_line

**REGLA:** Si usuario pide "órdenes + productos", agregar window functions para mostrar máximo X órdenes

**Para mostrar últimas órdenes SIN productos:**
```sql
SELECT 
  so.name, rp.name AS cliente, rp2.name AS vendedor, so.amount_total
FROM sale_order so
JOIN res_partner rp ON so.partner_id = rp.id
JOIN res_users ru ON so.user_id = ru.id  
JOIN res_partner rp2 ON ru.partner_id = rp2.id
WHERE so.state IN ('sale', 'done')
ORDER BY so.date_order DESC
LIMIT 5;
```

**Para mostrar órdenes CON productos detallados (máximo X órdenes):**
```sql
WITH top_orders AS (
  SELECT so.id, so.name, so.date_order, so.amount_total,
         rp.name AS cliente, rp2.name AS vendedor
  FROM sale_order so
  JOIN res_partner rp ON so.partner_id = rp.id
  JOIN res_users ru ON so.user_id = ru.id  
  JOIN res_partner rp2 ON ru.partner_id = rp2.id
  WHERE so.state IN ('sale', 'done')
  ORDER BY so.date_order DESC
  LIMIT 5
)
SELECT 
  to.name AS orden,
  to.cliente,
  to.vendedor,
  COALESCE(pt.name->>'es_ES', pt.name->>'en_US') AS producto,
  sol.price_unit AS precio_unitario,
  sol.price_total AS precio_linea
FROM top_orders to
JOIN sale_order_line sol ON to.id = sol.order_id
JOIN product_product pp ON sol.product_id = pp.id
JOIN product_template pt ON pp.product_tmpl_id = pt.id
ORDER BY to.date_order DESC, sol.id;
```

**Para mostrar órdenes CON productos consolidados (una fila por orden):**
```sql
WITH recent_orders AS (
  SELECT so.id, so.name, so.date_order, so.amount_total,
         rp.name AS cliente, rp2.name AS vendedor
  FROM sale_order so
  JOIN res_partner rp ON so.partner_id = rp.id
  JOIN res_users ru ON so.user_id = ru.id  
  JOIN res_partner rp2 ON ru.partner_id = rp2.id
  WHERE so.state IN ('sale', 'done')
  ORDER BY so.date_order DESC
  LIMIT 5
)
SELECT 
  ro.name AS orden,
  ro.cliente,
  ro.vendedor,
  ro.amount_total AS total_orden,
  STRING_AGG(COALESCE(pt.name->>'es_ES', pt.name->>'en_US'), ', ') AS productos
FROM recent_orders ro
JOIN sale_order_line sol ON ro.id = sol.order_id
JOIN product_product pp ON sol.product_id = pp.id
JOIN product_template pt ON pp.product_tmpl_id = pt.id
GROUP BY ro.id, ro.name, ro.cliente, ro.vendedor, ro.amount_total, ro.date_order
ORDER BY ro.date_order DESC;
```

**REGLAS CRÍTICAS para filtros de fecha:**
- Cuando el usuario no especifica año, detectar automáticamente el año con más datos
- NUNCA hacer hardcode de años específicos
- Usar subconsulta para encontrar el año más relevante dinámicamente
- Para "mes actual" usar año actual, para "meses pasados" buscar en años con datos

**Ejemplos específicos para ventas:**

1. **Mejor vendedor por número de pedidos (detección automática de año)**:
```sql
-- Para un mes específico sin año (ej: "julio"), detectar año con más datos
WITH recent_year AS (
  SELECT EXTRACT(YEAR FROM date_order) as year
  FROM sale_order 
  WHERE state IN ('sale', 'done') AND date_order IS NOT NULL
  GROUP BY EXTRACT(YEAR FROM date_order)
  ORDER BY COUNT(*) DESC, EXTRACT(YEAR FROM date_order) DESC
  LIMIT 1
)
SELECT 
  ru.id AS user_id,
  rp.name AS vendedor,
  COUNT(so.id) AS total_pedidos,
  SUM(so.amount_total) AS total_ventas
FROM sale_order so
JOIN res_users ru ON so.user_id = ru.id  
JOIN res_partner rp ON ru.partner_id = rp.id
CROSS JOIN recent_year ry
WHERE so.state IN ('sale', 'done') 
  AND so.user_id IS NOT NULL
  AND EXTRACT(MONTH FROM so.date_order) = 7  -- julio
  AND EXTRACT(YEAR FROM so.date_order) = ry.year  -- año detectado
GROUP BY ru.id, rp.name
ORDER BY total_pedidos DESC
LIMIT 3
```

2. **Ventas por equipo**:
```sql
SELECT 
  ct.name AS equipo,
  COUNT(so.id) AS pedidos,
  SUM(so.amount_total) AS total
FROM sale_order so
JOIN crm_team ct ON so.team_id = ct.id
WHERE so.state = 'sale'
GROUP BY ct.name
ORDER BY total DESC
```

**ORM CORRECTO para mejor vendedor:**
```python
# Para mejor vendedor por monto total - EVITAR user_id = False
best_seller = self.env['sale.order'].read_group(
    domain=[
        ('state', 'in', ['sale', 'done']),
        ('user_id', '!=', False)  # ← CRÍTICO: excluir pedidos sin vendedor
    ],
    fields=['user_id', 'amount_total:sum'],
    groupby=['user_id'],
    orderby='amount_total desc',
    limit=1
)

# Para top vendedores por número de pedidos:
top_sellers = self.env['sale.order'].read_group(
    domain=[
        ('state', 'in', ['sale', 'done']),
        ('user_id', '!=', False)
    ],
    fields=['user_id', 'id:count'],  # ← CORRECTO: usar id:count para contar registros
    groupby=['user_id'],
    orderby='id desc',  # ← CORRECTO: ordenar por el conteo
    limit=3
)

# Para filtros de fecha específicos - DETECCIÓN AUTOMÁTICA DE AÑO:
# Encontrar año con más datos, luego filtrar por ese año
year_data = self.env['sale.order'].read_group(
    domain=[('state', 'in', ['sale', 'done'])],
    fields=['date_order:year', 'id:count'],
    groupby=['date_order:year'],
    orderby='id desc',
    limit=1
)

if year_data:
    target_year = year_data[0]['date_order:year']
    start_date = str(target_year) + '-07-01'
    end_date = str(target_year) + '-08-01'
    
    july_sellers = self.env['sale.order'].read_group(
        domain=[
            ('state', 'in', ['sale', 'done']),
            ('user_id', '!=', False),
            ('date_order', '>=', start_date),
            ('date_order', '<', end_date)
        ],
        fields=['user_id', 'amount_total:sum'],
        groupby=['user_id'],
        orderby='amount_total desc',
        limit=1
    )
    # Resultado: july_sellers contiene el mejor vendedor de julio

# Para análisis de rentabilidad - ORM simplificado:
profitable_products = self.env['sale.order.line'].read_group(
    domain=[('order_id.state', 'in', ['sale', 'done'])],
    fields=['product_id', 'price_total:sum'],
    groupby=['product_id'],
    orderby='price_total desc',
    limit=10
)
# Nota: El cálculo de costo requiere lógica adicional debido a JSONB

# Para últimas órdenes SIN duplicados:
recent_orders = self.env['sale.order'].search([
    ('state', 'in', ['sale', 'done'])
], limit=5, order='date_order desc')

# Para acceder a productos de cada orden:
for order in recent_orders:
    products = order.order_line.mapped('product_id.product_tmpl_id.name')
    product_list = ', '.join(products) if products else 'Sin productos'

# MANEJO CORRECTO de resultados:
for seller_data in top_sellers:
    if isinstance(seller_data['user_id'], tuple):
        # Caso normal: user_id es tupla [id, nombre]
        user_id = seller_data['user_id'][0]
        user_name = seller_data['user_id'][1]
    else:
        # Caso especial: user_id es solo el ID
        user_id = seller_data['user_id']
        user = self.env['res.users'].browse(user_id)
        user_name = user.partner_id.name
    
    pedidos_count = seller_data['id']  # Número de pedidos
    # Usar: user_name, pedidos_count
```

**REGLAS CRÍTICAS - Manejo de read_group():**
- Para contar registros usa `'id:count'` en fields, NO `'campo:count_distinct'`
- Campos Many2one pueden devolver tupla `[id, nombre]` O solo el ID (entero)
- SIEMPRE verificar tipo con `isinstance(result['user_id'], tuple)`
- Si el campo puede ser `False`, SIEMPRE filtrar con `('campo', '!=', False)` en el dominio
- Para ordenar por conteos usa el nombre del campo sin operador: `orderby='id desc'`

**Operadores válidos en read_group():**
- `'campo:sum'` - suma
- `'campo:count'` - contar valores no nulos  
- `'campo:avg'` - promedio
- `'campo:max'` - máximo
- `'campo:min'` - mínimo
- `'id:count'` - contar registros (más común)

**Pregunta del Usuario:**
{input}

**Consulta SQL:**
""",
}


# --- Prompts para el Orquestador y Post-procesamiento ---

# Prompt para que el orquestador clasifique la intención del usuario
ORCHESTRATOR_PROMPT = """
Tu tarea es clasificar la pregunta de un usuario en una de las siguientes categorías: 'INVENTORY_QUERY', 'SALES_QUERY' o 'CHAT'.
Responde únicamente con la categoría, sin explicaciones.

- 'INVENTORY_QUERY': Preguntas sobre stock, existencias, productos en almacenes, cantidades, etc.
  Ejemplos: "¿cuánto stock hay de la silla?", "muéstrame los productos del almacén principal", "listar inventario".
- 'SALES_QUERY': Preguntas sobre pedidos de venta, clientes, facturación, ingresos, equipos de venta.
  Ejemplos: "¿cuáles fueron las ventas del mes pasado?", "dame los pedidos del cliente 'Juan Pérez'", "total de ventas por equipo".
- 'CHAT': Saludos, despedidas, preguntas generales o conversaciones que no encajan en las otras categorías.
  Ejemplos: "hola", "¿cómo estás?", "gracias", "¿qué puedes hacer?".

**Pregunta del usuario:**
{user_input}

**Categoría:**
"""

# Prompt para formatear la respuesta final al usuario
FINAL_RESPONSE_PROMPT = """
Eres un asistente de Odoo amigable y servicial.
Tu tarea es tomar la pregunta original del usuario y los resultados de la base de datos y formular una respuesta clara usando un formato visual atractivo.

**IMPORTANTE**: Cuando el usuario pregunte por "cantidad" sin especificar, SIEMPRE mostrar la cantidad DISPONIBLE (no reservada), no la cantidad total.

**Reglas de formato para datos de inventario:**

1. **Título con emoji**: 🧪 *Inventario: [Nombre del Producto]* 🧪

2. **Total disponible**: ✅ *Total Disponible: [suma de cantidades disponibles] unidades*

3. **Separador**: ---

4. **Desglose**: *Desglose por ubicación:*

5. **Por cada ubicación**:
   - 📍 [Ubicación]
   - *Disponibles:* *[cantidad_disponible]* (si es diferente de cantidad total: *[disponible]* de [total])
   - *Lote:* [nombre_lote]

6. **Ubicaciones agotadas** (si las hay):
   - ---
   - ❌ *Agotado en:* [lista de ubicaciones]

**Ejemplo de formato:**
```
🧪 *Inventario: Malphos 1000 CE 0.950L* 🧪

✅ *Total Disponible: 3,232 unidades*

---

*Desglose por ubicación:*

📍 R4F21N3
*Disponibles:* *936*
*Lote:* 2211|1777

📍 R4F22N3
*Disponibles:* *528* de 936
*Lote:* 2211|1777

---
❌ *Agotado en:* R4F23N3 y R4F24N3
```

**Para otros tipos de consultas** (no inventario), usa formato de lista con viñetas y emojis apropiados.

Si no hay resultados, informa educadamente que no se encontró información.

**Pregunta Original del Usuario:**
{question}

**Resultados de la Base de Datos:**
{result}

**Respuesta Final:**
"""

# Prompt para el modo de chat general
CHAT_PROMPT = """
Eres un asistente conversacional amigable. Tu propósito es saludar, conversar y responder preguntas generales.
Puedes tener conversaciones sobre cualquier tema, pero no debes realizar consultas SQL ni acceder a la base de datos.

**Conversación hasta ahora:**
{history}

**Pregunta del Usuario:**
{user_input}

**Respuesta:**
"""
