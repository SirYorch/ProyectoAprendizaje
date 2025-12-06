from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage
import re
import random

llm = ChatOllama(
    model="deepseek-r1:8b",  # o "mistral", "gemma2", "qwen2.5"
)

def naturalize_response(prediction_data: dict, language: str = "es") -> dict:
    """
    Usa Ollama local para convertir los datos técnicos en un mensaje natural.
    """
    
    mensaje = (
        f"Eres un agente de predicción de stock, debes presentar este texto al cliente, de forma que sea comprensible y adaptado, puedes usar tablas signos como negrita y cursita para presentar el texto, escribelo en formato markdown "
        f"La data es: {prediction_data}"
    )

    resp = llm.invoke([HumanMessage(content=mensaje)])
    return resp.content




def check_regex_response(user_text: str) -> str | None:
    """
    Analiza el texto buscando patrones simples de saludo, despedida o agradecimiento.
    Retorna una respuesta inmediata si encuentra coincidencia, o None si no encuentra nada.
    """

    text = user_text.lower()

    # --- GRUPO A: SALUDOS ---
    patron_saludos = r"\b(hola|oli|buenos d[íi]as|buenas tardes|buenas noches|que tal|hello)\b"
    
    if re.search(patron_saludos, text):
        respuestas = [
            "¡Hola! Bienvenido a Nombre. ¿En qué puedo ayudarte hoy?",
            "¡Buenas! Soy tu asistente virtual. ¿Buscas stock o información?",
            "¡Hola! Estoy listo para ayudarte con el inventario."
        ]
        return random.choice(respuestas)

    # --- GRUPO B: DESPEDIDAS ---
    patron_despedidas = r"\b(chao|adi[óo]s|hasta luego|nos vemos|bye|cu[íi]date)\b"
    
    if re.search(patron_despedidas, text):
        respuestas = [
            "¡Hasta luego! Gracias por visitar Nombre.",
            "¡Chao! Vuelve pronto.",
            "Nos vemos. Espero haberte ayudado."
        ]
        return random.choice(respuestas)

    # --- GRUPO C: AGRADECIMIENTOS ---
    patron_agradecimientos = r"\b(gracias|te agradezco|muy amable|thx)\b"
    
    if re.search(patron_agradecimientos, text):
        respuestas = [
            "¡De nada! Es un placer ayudarte.",
            "¡Para eso estamos!",
            "Con gusto. ¿Necesitas algo más?"
        ]
        return random.choice(respuestas)

    # Si no coincidió con nada, devolvemos None para que pase al siguiente filtro (RAG o LLM)
    return None