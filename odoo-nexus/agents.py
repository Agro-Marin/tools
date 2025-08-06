# agents.py
"""
Módulo que define los agentes especializados del sistema.
Cada agente es una cadena de LangChain configurada para una tarea específica,
con su propia instancia del modelo de lenguaje.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import create_sql_query_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

import config
from database import get_db_connection, run_query


def create_sql_agent_chain(domain_config: dict, model_config: dict):
    """
    Crea una cadena de agente SQL genérica a partir de una configuración de dominio
    y una configuración de modelo específicas.
    """
    # Crea una instancia de LLM específica para este agente
    llm = ChatGoogleGenerativeAI(
        model=model_config["model"],
        temperature=model_config["temperature"],
        google_api_key=config.GEMINI_API_KEY
    )
    
    db = get_db_connection(tables=domain_config["tables"])
    
    # Log del table_info cuando DEBUG está activado
    if config.DEBUG:
        table_info = db.get_table_info()
        print(f"📊 Table Info para tablas {domain_config['tables']}:")
        print(f"{table_info[:500]}..." if len(table_info) > 500 else table_info)
        print("-" * 50)
    
    prompt_template = PromptTemplate.from_template(domain_config["prompt_template"])
    
    # Cadena para generar la consulta SQL
    sql_query_chain = create_sql_query_chain(llm, db, prompt=prompt_template)

    # Cadena para dar formato a la respuesta final en lenguaje natural
    answer_prompt = PromptTemplate.from_template(config.FINAL_RESPONSE_PROMPT)
    answer_chain = answer_prompt | llm | StrOutputParser()

    # Cadena completa que maneja el flujo de datos
    chain = (
        RunnablePassthrough.assign(question=lambda x: x["input"])
        .assign(sql_query=sql_query_chain)
        .assign(result=lambda x: run_query(x["sql_query"]))
        | answer_chain
    )
    return chain

def create_chat_agent_chain(model_config: dict):
    """
    Crea una cadena de agente para conversación general con su propia
    instancia de LLM.
    """
    # Crea una instancia de LLM específica para el chat
    llm = ChatGoogleGenerativeAI(
        model=model_config["model"],
        temperature=model_config["temperature"],
        google_api_key=config.GEMINI_API_KEY
    )
    
    prompt = PromptTemplate.from_template(config.CHAT_PROMPT)
    chain = prompt | llm | StrOutputParser()
    return chain

# --- Creación de los Agentes Específicos ---
# Cada agente se crea con su propia configuración de modelo desde config.py

inventory_agent_chain = create_sql_agent_chain(
    config.INVENTORY_DOMAIN,
    config.AGENT_MODELS["INVENTORY"]
)

sales_agent_chain = create_sql_agent_chain(
    config.SALES_DOMAIN,
    config.AGENT_MODELS["SALES"]
)

chat_agent_chain = create_chat_agent_chain(
    config.AGENT_MODELS["CHAT"]
)