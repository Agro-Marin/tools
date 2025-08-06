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


def validate_sql(sql: str) -> bool:
    """Valida que la consulta sea un SELECT seguro."""
    sql_clean = sql.strip().lower()
    if not sql_clean.startswith("select"):
        print("🚨 Fallo de validación: La consulta no comienza con SELECT.")
        return False

    forbidden_keywords = [
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "create",
        "truncate",
        "grant",
        "revoke",
        "commit",
        "rollback",
    ]
    # Usamos split() para evitar falsos positivos en nombres de tablas/columnas
    if any(kw in sql_clean.split() for kw in forbidden_keywords):
        print(
            f"🚨 Fallo de validación: La consulta contiene una palabra clave prohibida."
        )
        return False

    return True


def run_query(sql_query: str):
    """
    Ejecuta una consulta SQL validada y devuelve los resultados.
    """
    if not engine:
        raise ConnectionError("La conexión a la base de datos no está disponible.")

    clean_sql = extract_sql_from_markdown(sql_query)

    if not validate_sql(clean_sql):
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
