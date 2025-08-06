# main.py
"""
Punto de entrada principal para la aplicación de consola del Asistente de Odoo.
"""

import config
from orchestrator import route_request

def main_console():
    """
    Inicia el bucle principal de la aplicación de consola.
    """
    # Validar configuración antes de iniciar
    if not config.GEMINI_API_KEY or not config.DATABASE_URL:
        print(
            "🚨 Error: Asegúrate de que las variables de entorno GEMINI_API_KEY y "
            "DATABASE_URL están definidas en tu archivo .env"
        )
        return

    print("--- 🤖 Asistente Multi-Agente para Odoo ---")
    print("Puedes hacer preguntas sobre inventario, ventas, o simplemente conversar.")
    print("Escribe 'salir' para terminar.\n")

    chat_history = []

    while True:
        user_input = input("💬 Tú: ")
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("👋 ¡Adiós!")
            break
        
        if not user_input.strip():
            continue

        try:
            # El orquestador se encarga de todo el trabajo pesado
            final_answer = route_request(user_input, chat_history)
            
            print(f"\n🤖 Asistente:\n{final_answer}\n")
            
            # Actualizar historial para el contexto del chat
            chat_history.append(f"Usuario: {user_input}")
            chat_history.append(f"Asistente: {final_answer}")
            # Limitar el historial para no exceder el límite de tokens
            chat_history = chat_history[-6:]

        except Exception as e:
            print(f"💥 Ha ocurrido un error inesperado: {e}\n")
            if config.DEBUG:
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    main_console()
