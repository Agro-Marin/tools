# database.py
"""
Módulo para la gestión de la conexión y ejecución de consultas a la base de datos.
"""

import re
import warnings
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SAWarning
from langchain_community.utilities import SQLDatabase

import config

# Ignorar advertencias de SQLAlchemy que no son críticas
warnings.filterwarnings("ignore", category=SAWarning)

# --- Conexión a la Base de Datos ---
try:
    engine = create_engine(config.DATABASE_URL)
    # Probar la conexión
    with engine.connect() as connection:
        if config.DEBUG:
            print("✅ Conexión a la base de datos establecida correctamente.")
except Exception as e:
    print(f"🚨 Error al conectar con la base de datos: {e}")
    engine = None


def get_db_connection(tables: list[str]) -> SQLDatabase:
    """
    Obtiene una instancia de SQLDatabase para las tablas especificadas.
    """
    if not engine:
        raise ConnectionError("No se pudo establecer la conexión con la base de datos.")
    return SQLDatabase(engine, include_tables=tables)


# --- Utilidades y Seguridad ---


def extract_sql_from_markdown(text: str) -> str:
    """Extrae el código SQL de un bloque de markdown si está presente."""
    match = re.search(r"```(?:sql)?\n(.*?)\n```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Valida que la consulta sea un SELECT seguro.
    
    Returns:
        tuple[bool, str]: (es_válida, mensaje_error)
    """
    sql_clean = sql.strip().lower()
    
    # Verificar que comience con SELECT o WITH (para CTEs)
    if not (sql_clean.startswith("select") or sql_clean.startswith("with")):
        return False, "🚨 Fallo de validación: La consulta debe comenzar con SELECT o WITH."

    forbidden_keywords = [
        "insert", "update", "delete", "drop", "alter", "create", "truncate",
        "grant", "revoke", "commit", "rollback", "execute", "call"
    ]
    
    # Verificar palabras clave prohibidas
    sql_words = sql_clean.split()
    for keyword in forbidden_keywords:
        if keyword in sql_words:
            return False, f"🚨 Fallo de validación: La consulta contiene '{keyword}' que está prohibido."
    
    # Verificar uso correcto de operadores JSONB
    if "->>" in sql and "jsonb" not in sql_clean:
        # Buscar patrones potencialmente problemáticos
        import re
        jsonb_pattern = r"(\w+)\s*->>\s*'[^']+'"
        matches = re.findall(jsonb_pattern, sql)
        
        warning_tables = ["stock_warehouse", "stock_location"]
        for match in matches:
            table_hint = match.lower()
            if any(wt in table_hint for wt in warning_tables):
                return False, f"🚨 Posible error: Campo '{match}' puede no ser JSONB. Usa el campo directamente."
    
    # Verificar columnas ambiguas en JOINs
    if " join " in sql_clean and "select " in sql_clean:
        import re
        # Buscar SELECT seguido de nombres de columna sin alias
        select_pattern = r"select\s+([^from]+)"
        select_match = re.search(select_pattern, sql_clean)
        if select_match:
            select_fields = select_match.group(1)
            # Buscar campos comunes que suelen ser ambiguos
            common_fields = ["name", "id", "active", "create_date", "write_date"]
            for field in common_fields:
                if f" {field} " in f" {select_fields} " or select_fields.strip() == field:
                    return False, f"🚨 Columna ambigua: '{field}' necesita alias de tabla (ej: sl.{field}, sw.{field})"
    
    # Validación adicional: límite de filas si no está especificado
    if "limit" not in sql_clean and "count(" not in sql_clean:
        if config.DEBUG:
            print("⚠️  Advertencia: La consulta no tiene LIMIT. Se aplicará el límite por defecto.")
    
    return True, "✅ Consulta válida"


def get_column_type(table_name: str, column_name: str) -> str:
    """
    Obtiene el tipo de datos de una columna específica.
    Útil para determinar si un campo es JSONB o VARCHAR.
    """
    if not engine:
        return "unknown"
    
    query = """
    SELECT data_type 
    FROM information_schema.columns 
    WHERE table_name = %s AND column_name = %s
    """
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), (table_name, column_name))
            row = result.fetchone()
            return row[0] if row else "unknown"
    except:
        return "unknown"


def run_query(sql_query: str):
    """
    Ejecuta una consulta SQL validada y devuelve los resultados.
    """
    if not engine:
        raise ConnectionError("La conexión a la base de datos no está disponible.")

    clean_sql = extract_sql_from_markdown(sql_query)

    # Usar la nueva validación que devuelve tuple
    is_valid, validation_message = validate_sql(clean_sql)
    if not is_valid:
        print(validation_message)
        raise ValueError("Consulta SQL no válida o insegura.")

    if config.DEBUG:
        print(f"⚙️ SQL Ejecutando:\n{clean_sql}\n")

    try:
        with engine.connect() as connection:
            result = connection.execute(text(clean_sql))
            return result.fetchall()
    except Exception as e:
        print(f"💥 Error al ejecutar la consulta: {e}")
        # Devolvemos un mensaje de error amigable que el LLM pueda interpretar
        return f"Error al procesar la consulta. Detalles: {str(e)}"
