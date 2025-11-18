from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage


llm = ChatOllama(
    model="deepseek-r1:8b",  # o "mistral", "gemma2", "qwen2.5"
)

def naturalize_response(prediction_data: dict, language: str = "es") -> dict:
    """
    Usa Ollama local para convertir los datos técnicos en un mensaje natural.
    """
    
    mensaje = (
        f"Presenta este texto simulando ser un agente de predicción de stock: "
        f"{prediction_data}"
    )

    resp = llm.invoke([HumanMessage(content=mensaje)])
    return resp.content