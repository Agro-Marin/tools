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
        "product_product",
        "product_template",
    ],
    "prompt_template": """
Eres un experto en el módulo de Inventario de Odoo 18.0 para PostgreSQL.
Basado en el esquema de la base de datos a continuación, las reglas y la pregunta del usuario, genera una consulta SQL válida para PostgreSQL.

**Esquema de la Base de Datos:**
{table_info}

**Reglas Importantes:**
- Genera SOLO la consulta SQL, sin explicaciones, sin markdown, solo el código SQL.
- Limita tus resultados a {top_k} filas a menos que el usuario lo pida explícitamente.
- Las tablas y campos usan snake_case (ej: product_template, stock_quant).
- Los campos de texto traducibles (como 'name') son de tipo jsonb. Para obtener el nombre en español o inglés, usa:
  `COALESCE(name->>'es_ES', name->>'en_US')`
- Para búsquedas de texto no exactas en campos JSONB traducibles, usa: 
  `COALESCE(name->>'es_ES', name->>'en_US') ILIKE '%texto%'`

**Campos de precios:**
- `product_template.list_price` es NUMERIC - precio de venta
- `product_product.standard_price` es JSONB con estructura {{'company_id': precio}}. Para obtener el precio de costo usa:
  `CAST(pp.standard_price->>'2' AS NUMERIC)` donde '2' es el ID de la compañía
- Si necesitas convertir JSONB a número, usa CAST(campo->>'clave' AS NUMERIC)

**Sobre ubicaciones y almacenes:**
- `stock_quant` apunta a `stock_location` a través de `location_id`.
- `stock_location` es una estructura jerárquica. La jerarquía se representa en `parent_path`.
- `stock_warehouse` define su ubicación raíz con `lot_stock_id`.
- Para consultar el inventario dentro de un almacén (incluyendo sububicaciones), filtra `stock_location` cuyo `parent_path` contenga el `lot_stock_id` del almacén.
  Ejemplo de filtro: `sl.parent_path LIKE '%' || sw.lot_stock_id || '/%' OR sl.id = sw.lot_stock_id`

**Relaciones clave:**
- `stock_quant.product_id` → `product_product.id`
- `product_product.product_tmpl_id` → `product_template.id`
- `stock_quant.location_id` → `stock_location.id`
- `stock_warehouse.lot_stock_id` → `stock_location.id`

**Consideraciones sobre almacenes y ubicaciones:**
- `stock_warehouse.code` es el identificador técnico (ej: "CDG").
- `stock_warehouse.name` es el nombre descriptivo (ej: "CODAGEM").
- `stock_location.name` puede ser también descriptivo (ej: "CDG").
- Si el usuario menciona "codagem", busca por `stock_warehouse.name ILIKE '%codagem%'`.
- Si el usuario menciona "CDG", puede referirse tanto a `stock_warehouse.code = 'CDG'` como a ubicaciones con `stock_location.name ILIKE '%CDG%'`.
- Para mayor precisión, usa ambos criterios cuando sea apropiado.

**Ejemplo de consulta para buscar stock en almacén "codagem":**
```sql
WHERE (sw.name ILIKE '%codagem%' OR sw.code ILIKE '%codagem%')
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
        "crm_team", # Equipos de venta
        "product_product",
        "product_template",
    ],
    "prompt_template": """
Eres un experto en el módulo de Ventas de Odoo 18.0 para PostgreSQL.
Basado en el esquema de la base de datos, las reglas y la pregunta del usuario, genera una consulta SQL válida para PostgreSQL.

**Esquema de la Base de Datos:**
{table_info}

**Reglas Importantes:**
- Genera SOLO la consulta SQL, sin explicaciones, sin markdown, solo el código SQL.
- Limita tus resultados a {top_k} filas a menos que el usuario lo pida.
- Los campos de texto traducibles (como 'name') son de tipo jsonb. Usa `COALESCE(name->>'es_ES', name->>'en_US')` para obtener el nombre.
- Para búsquedas de texto no exactas en campos JSONB traducibles, usa: 
  `COALESCE(name->>'es_ES', name->>'en_US') ILIKE '%texto%'`
- Las fechas y horas están en UTC. Considera la zona horaria si es relevante.

**Relaciones clave:**
- `sale_order.partner_id` → `res_partner.id` (Cliente)
- `sale_order.team_id` → `crm_team.id` (Equipo de ventas)
- `sale_order_line.order_id` → `sale_order.id`
- `sale_order_line.product_id` → `product_product.id`
- `product_product.product_tmpl_id` → `product_template.id`

**Consideraciones sobre Ventas:**
- `sale_order.state` indica el estado del pedido: 'draft' (borrador), 'sent' (enviado), 'sale' (pedido de venta), 'done' (hecho), 'cancel' (cancelado).
- `sale_order.amount_total` es el importe total del pedido.
- `sale_order.date_order` es la fecha de confirmación del pedido.

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
Tu tarea es tomar la pregunta original del usuario y los resultados de la base de datos y formular una respuesta clara, concisa y en lenguaje natural.

- Resume los hallazgos de forma amable.
- Si los resultados son una lista, formatéalos de manera legible (por ejemplo, con viñetas o una tabla simple).
- Si no hay resultados (`result` está vacío o es `None`), informa al usuario educadamente que no encontraste información para su consulta.
- Responde siempre en el mismo idioma de la pregunta del usuario.

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
