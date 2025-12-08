from fastapi import APIRouter, Body, UploadFile, File, Query, HTTPException

from typing import Any, Dict
from llm.llm import naturalize_response
from tts.textToSpeech import tts
import base64
import json
from lipsync.lipsyncgen import generate_lipsync
from ai.matcher import FunctionCaller
from db.functions import generate_csv , generate_excel, top_selling, least_selling


router = APIRouter()
caller = FunctionCaller()

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
async def predict_product_fecha(request: Dict[str, Any] = Body(...)):
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



# sin argumentos
# UPDATE function_definitions
# SET nombre = 'predict_stock'
# WHERE id = 'func_001';

# # con producto
# UPDATE function_definitions
# SET nombre = 'predict_product'
# WHERE id = 'func_002';


# # con fecha
# UPDATE function_definitions
# SET nombre = 'predict_date'
# WHERE id = 'func_003';

# # con fecha y producto
# UPDATE function_definitions
# SET nombre = 'predict_product_fecha'
# WHERE id = 'func_004';


# # get best sellers
# UPDATE function_definitions
# SET nombre = 'top_selling'
# WHERE id = 'func_005';

# # get worst Sellers
# UPDATE function_definitions
# SET nombre = 'least_selling'
# WHERE id = 'func_006';


# # generate csv
# UPDATE function_definitions
# SET nombre = 'generate_csv'
# WHERE id = 'func_007';

# # generate excel
# UPDATE function_definitions
# SET nombre = 'generate_excel'
# WHERE id = 'func_008';



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
    print("chat request")
    
    #Aqui tiene que pasar el primer filtro, expresiones regulares para, saludos, agradecimientos y despedidas karen, haz que solo se presente en saludos, 
    
    #Aqui tiene que pasar al segundo filtro, rag para detección de documentos, FAQ's y datos x
    
    #Aqui coloco el tercer filtro, function matcher
    pred = "Se Envió la solicitud"+query
    
    file = None
    
    try:
        resultado = caller.identificar_funcion(query)

        # print(resultado['funcion'])       #Resultados
        # print(resultado['parametros'])   
        # print(resultado['confianza'])    
        
        if(resultado['confianza'] > 0.9):
            if resultado['funcion'] == "predict_stock":
                predict_stock() # no necesita parametros
            if resultado['funcion'] == "predict_product":
                predict_product({ "name": resultado['parametros']['producto']})
            if resultado['funcion'] == "predict_date":
                # print(resultado['parametros']['fecha'])
                predict_date({ "date":resultado['parametros']['fecha']})
            if resultado['funcion'] == "predict_product_fecha":
                predict_product_fecha({ "name":resultado['parametros']['producto'],"date": resultado['parametros']['fecha']})
            if resultado['funcion'] == "top_selling":
                data = top_selling()
                pred = f"Los 5 productos más vendidos son: {data}"

            elif resultado['funcion'] == "least_selling":
                data = least_selling()
                pred = f"Los 5 productos menos vendidos son: {data}"

            elif resultado['funcion'] == "generate_csv":
                month = resultado["parametros"].get("mes")  # opcional
                file = generate_csv(month)
                pred = f"Se generó el CSV en: {file}"

            elif resultado['funcion'] == "generate_excel":
                month = resultado["parametros"].get("mes")  # opcional
                file = generate_excel(month)
                pred = f"Se generó el Excel en: {file}"
            

    except Exception as e:
        print("ERROR en identificar_funcion:", e)
        pred += "Lamentablemente no logré entender lo la solicitud, que haces, recuerda que puedo, hacer predicciónes tomando parametros como producto y fecha, y revisar productos más y menos vendidos, además de generar reportes en excel o csv."
    
    
    
    # #Valor en texto de las respuestas
    pred = naturalize_response(pred)
    
    # #Audio generado por gTTS
    tts(pred)
    
    # #Json generado por rhubarb
    generate_lipsync(pred)
    
    return {
            "messages": [
                {
                    "text": pred,
                    "audio": audio_to_base64("audios/audio.wav"),
                    "lipsync": read_json("audios/audio.json"),
                    "facialExpression": "smile",
                    "animation": "Standing",
                    "file": file
                }
            ]
        }




@router.post(
    "/upload/retrain",
    summary="Cargar CSV y reentrenar modelo",
    description="Sube un archivo CSV con datos nuevos para reentrenar el modelo"
)
async def upload_and_retrain(
    file: UploadFile = File(..., description="Archivo CSV con datos de entrenamiento"),
    epochs: int = Query(5, description="Número de épocas para reentrenamiento", ge=1, le=100),
    batch_size: int = Query(128, description="Tamaño del batch", ge=16, le=512),
    umbral_degradacion: float = Query(0.1, description="Porcentaje de degradación aceptable", ge=0.0, le=1.0)
) -> Dict[str, Any]:
    """
    Recibe un archivo CSV, lo procesa y reentrena el modelo.
    """

    # Validar tipo de archivo
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser un CSV (.csv)"
        )

    try:
        # Leer contenido
        contents = await file.read()

        if not contents or len(contents) == 0:
            raise HTTPException(
                status_code=400,
                detail="El archivo CSV está vacío"
            )

        
        # Este método debe ser reemplazado con la parte correcta
        resultado = {}
        # # Llamada a la función del modelo
        # resultado = retrain_from_csv(
        #     csv_content=contents,
        #     filename=file.filename,
        #     epochs=epochs,
        #     batch_size=batch_size,
        #     umbral_degradacion=umbral_degradacion
        # )
        
        

        # Validación del resultado
        if not isinstance(resultado, dict) or not resultado.get("success"):
            raise HTTPException(
                status_code=500,
                detail=resultado.get("message", "Error en el reentrenamiento")
            )

        return resultado

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando el archivo: {str(e)}"
        )