# orchestrator.py
"""
Módulo del orquestador.
Clasifica la intención del usuario usando su propia instancia de LLM
y enruta la solicitud al agente adecuado.
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

import config
from agents import inventory_agent_chain, sales_agent_chain, chat_agent_chain

def classify_intent(user_input: str) -> str:
    """
    Clasifica la intención del usuario usando una instancia de LLM dedicada.
    """
    # Crea una instancia de LLM específica para la tarea de orquestación
    orchestrator_llm = ChatGoogleGenerativeAI(
        model=config.AGENT_MODELS["ORCHESTRATOR"]["model"],
        temperature=config.AGENT_MODELS["ORCHESTRATOR"]["temperature"],
        google_api_key=config.GEMINI_API_KEY
    )
    
    prompt = PromptTemplate.from_template(config.ORCHESTRATOR_PROMPT)
    chain = prompt | orchestrator_llm | StrOutputParser()
    
    if config.DEBUG:
        print(f"🧠 Clasificando intención para: '{user_input}'")
        
    intent = chain.invoke({"user_input": user_input}).strip()
    
    if config.DEBUG:
        print(f"✅ Intención clasificada como: {intent}")
        
    return intent

def route_request(user_input: str, chat_history: list):
    """
    Enruta la solicitud del usuario al agente correcto y obtiene una respuesta.
    """
    intent = classify_intent(user_input)

    if intent == "INVENTORY_QUERY":
        print("➡️  Enrutando a Agente de Inventario...")
        response = inventory_agent_chain.invoke({
            "input": user_input,
            "top_k": config.DEFAULT_TOP_K
        })
    elif intent == "SALES_QUERY":
        print("➡️  Enrutando a Agente de Ventas...")
        response = sales_agent_chain.invoke({
            "input": user_input,
            "top_k": config.DEFAULT_TOP_K
        })
    elif intent == "CHAT":
        print("➡️  Enrutando a Agente de Chat...")
        response = chat_agent_chain.invoke({
            "user_input": user_input,
            "history": chat_history
        })
    else:
        print(f"⚠️  Intención desconocida: '{intent}'. Usando agente de chat por defecto.")
        response = chat_agent_chain.invoke({
            "user_input": user_input,
            "history": chat_history
        })
        
    return response