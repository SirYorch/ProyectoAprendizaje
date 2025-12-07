from fastapi import APIRouter, Body
from typing import Any, Dict
from llm.llm import naturalize_response
from tts.textToSpeech import tts
import base64
import json
from lipsync.lipsyncgen import generate_lipsync


router = APIRouter()

#Funciones auxiliares de transformacion
# --- Funciones auxiliares ---
def audio_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def read_json(path):
    with open(path, "r") as f:
        return json.load(f)
    
    

#Todas las solicitudes deben mantener el retorno de un msg
#Todas las solicitudes reciben un valor llm true or false, para saber si la respuesta se naturaliza o no



@router.post(
    "/predict/product-date",
    summary="Predecir stock de producto específico en una fecha específica",
    description="Predice el stock de un producto en una fecha determinada"
)
async def predict_product_fecha_stock(request: Dict[str, Any] = Body(...)):
    """
    Predice el stock de un producto específico en una fecha.
    """
    print("prediccion con producto y fecha")
    product = request.get("name")
    date = request.get("date")

    if not product or not date:
        return "Faltan campos obligatorios: name o date"
        
        
    llm = request.get("llm")
    
    if(llm):
        pred = naturalize_response("Se envió una solicitud en donde se intenta predecir el stock de un producto específico en una fecha los datos son los siguientes"+pred)
    
    return pred



@router.post(
    "/predict/product",
    summary="Predecir stock de producto en el tiempo hasta que se agote.",
    description="Predice el stock de un producto hasta que se agote"
)
async def predict_product(request: Dict[str, Any] = Body(...)):
    """
    Predice el stock de un producto específico hasta que se acabe
    """
    print("prediccion con producto")
    product = request.get("name")

    if not product:
        return "Faltan campos obligatorios: name"
        
    pred = "" ## mensaje de respuesta
    
    
    llm = request.get("llm")
    
    if(llm):
        pred = naturalize_response("Se envió una solicitud en donde se intenta predecir stock de producto en el tiempo hasta que se agote los datos son los siguientes"+pred)
    return pred


@router.post(
    "/predict/date",
    summary="Predecir stock de todos los productos hasta que alguno se agote totalmente",
    description="Predice el stock de todos los productos hasta que alguno se agote totalmente"
)
async def predict_date(request: Dict[str, Any] = Body(...)):
    """
    Predice el stock de todos los productos específico hasta que se acabe
    """
    print("prediccion con fecha")
    date = request.get("date")

    if not date:
        return  "Faltan campos obligatorios: date"
        
        
    pred = "" ## mensaje de respuesta
    
    
    llm = request.get("llm")
    
    if(llm):
        pred = naturalize_response("Se envió una solicitud en donde se intenta predecir stock de todos los productos en cierta fecha los datos son los siguientes"+pred)
        
    return pred

@router.post(
    "/predict/all",
    summary="Predecir stock de todos los productos hasta que alguno se agote",
    description="Predice el stock de todos los productos hasta que alguno se agote"
)
async def predict_stock(request: Dict[str, Any] = Body(...)):
    """
    Predice el stock de un producto específico hasta que se acabe
    """
    print("prediccion sin argumentos")
    pred = "" ## mensaje de respuesta
    
    llm = request.get("llm")
    
    if(llm):
        pred = naturalize_response("Se envió una solicitud en donde se intenta predecir stock de todos los productos hasta que alguno se agote los datos son los siguientes"+pred)
    
    return pred



@router.post(
    "/chat",
    summary="Envía mensajes directamente al chat, para que este procese la información, y sean presentadas utilizando un agente avatar con inteligencia artificial",
    description="Envía y procesa imagenes con un avatar e inteligencia artificial"
)
async def chat(request: Dict[str, Any] = Body(...)):
    """
    Recibe la información en forma de query, la procesa, y la presenta a los usuarios naturalizados.
    """
    
    query = request.get("message")
    print("prediccion sin argumentos")
    
    pred = "" ## mensaje de respuesta
    
    
    #Valor en texto de las respuestas
    # pred = naturalize_response("Se Envió la solicitud"+query+"el resultado obtenido a la solicitud es el siguiente"+pred)
    pred = "¡Hola! Soy tu asistente de ventas de Arc, la tienda de electrónicos avanzada. Estoy aquí para ayudarte de la manera más cómoda posible.\n\nRecibí tu solicitud para conocer los productos en riesgo. Hemos revisado los datos y, ¡ups!, parece que en este momento no hay información disponible sobre esos productos.\n\nNo te preocupes, esto solo significa que no encontramos resultados en este instante. Si tienes otra pregunta o quieres que busquemos algo más, ¡aquí estoy para ayudarte!"
    
    #Audio generado por gTTS
    tts(pred)
    
    #Json generado por rhubarb
    generate_lipsync(pred)
    
    return {
            "messages": [
                {
                    "text": pred,
                    "audio": audio_to_base64("audios/audio.wav"),
                    "lipsync": read_json("audios/audio.json"),
                    "facialExpression": "smile",
                    "animation": "Standing"
                }
            ]
        }