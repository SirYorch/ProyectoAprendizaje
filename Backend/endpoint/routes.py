from fastapi import APIRouter, Body, UploadFile, File, Query, HTTPException

from typing import Any, Dict
from llm.llm import naturalize_response
from datetime import date , timedelta
from tts.textToSpeech import tts
import base64
import json
from lipsync.lipsyncgen import generate_lipsync
from ai.matcher import FunctionCaller
from db.functions import generate_csv , generate_excel, top_selling, least_selling
from llm.agent import check_regex_response
from model.methods import predict_stock_product_date
from db.models import listar_productos

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
    
    pred = predict_stock_product_date(
        product_id=product,
        date=date)
    
    if(llm):
        pred = naturalize_response("Se envió una solicitud en donde se intenta predecir el stock de un producto específico en una fecha los datos son los siguientes"+str(pred))
    
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
        
    day = date.today()

    result = []
    # Buscar hasta 365 días hacia adelante
    for i in range (30):
        day = day+timedelta(days=1)
        pred = predict_stock_product_date(
            product_id=product,
            date=day
        )

        result.append(
            {
                      
                "product_name": product,
                "predicted_stock": int(pred["predicted_stock"]),
                "date": day
                
        }
        )
        print({
                      
            "product_name": product,
            "predicted_stock": int(pred["predicted_stock"]),
            "date": day
            
        })
        if pred["predicted_stock"] <= 0:
            break
    
    
    pred = result
    
    llm = request.get("llm")
    
    if(llm):
        pred = naturalize_response("Se envió una solicitud en donde se intenta predecir stock de producto en el tiempo hasta que se agote los datos son los siguientes"+str(pred))
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
    PRODUCTS = listar_productos()
    date = request.get("date")

    if not date:
        return  "Faltan campos obligatorios: date"
        
        
    results = []

    for product in PRODUCTS:
        predi = predict_stock_product_date(
            product_id=product,
            date=date
        )

        results.append({
            "product_name": product,
            "predicted_stock": int(predi["predicted_stock"]),
            "date":date
        })
        print({
            "product_name": product,
            "predicted_stock": int(predi["predicted_stock"]),
            "date":date
        })
    
    pred = results
    
    llm = request.get("llm")
    
    if(llm):
        pred = naturalize_response("Se envió una solicitud en donde se intenta predecir stock de todos los productos en cierta fecha los datos son los siguientes"+str(pred))
        
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
    
    PRODUCTS = listar_productos()
    
    pred = "" ## mensaje de respuesta
    
    day = date.today()
    results = []
    
    
    for i in range (30):
        zero = False
        for product in PRODUCTS:
            pred = predict_stock_product_date(
                product_id=product,
                date=day)
            day = day+ timedelta(days=1)
            
            results.append({
                    "product_name": product,
                    "predicted_stock": int(pred["predicted_stock"]),
                    "current_stock": pred["current_stock"],
                })
            print(str({
                    "product_name": product,
                    "predicted_stock": int(pred["predicted_stock"]),
                    "current_stock": pred["current_stock"],
                }))
            if(int(pred["predicted_stock"]) <= 0):
                zero = True
            
        if zero == True:
            break
        
    pred = results
    
    llm = request.get("llm")
    
    if(llm):
        pred = naturalize_response("Se envió una solicitud en donde se intenta predecir stock de todos los productos hasta que alguno se agote los datos son los siguientes"+str(pred))
    
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

    pred = "Se Envió la solicitud "+ query
    file = None
    

    #Aqui tiene que pasar el primer filtro, expresiones regulares para, saludos, agradecimientos y despedidas karen, haz que solo se presente en saludos, 
    regex_resp = check_regex_response(query)
    
    if regex_resp:
        print(" Respondido por Regex")
        pred = regex_resp
    else:
        #Aqui tiene que pasar al segundo filtro, rag para detección de documentos, FAQ's y datos x
        faq_resp = caller.consultar_faq(query)

        if faq_resp:
            print(f" Respondido por RAG (Confianza: {faq_resp['confianza']:.2f})")
            # Aquí obtenemos la respuesta directa de la base de datos
            pred = faq_resp['respuesta'] 
        else:
         #Aqui coloco el tercer filtro, function matcher
            
            resultado = caller.identificar_funcion(query)

            # print(resultado['funcion'])       #Resultados
            # print(resultado['parametros'])   
            # print(resultado['confianza'])    
            
            if(resultado['confianza'] > 0.8):
                pred = "La función con mayor probabilidad es " + resultado['funcion'] + "los resultados de la función son"
                print("Funcion:" + resultado['funcion'] )
                print("Confianza:" + str(resultado['confianza']) )
                print("Confianza:" + str(resultado['confianza']) )
                
                if str(resultado['funcion']) == "predict_stock":
                    pred += await str(predict_stock()) # no necesita parametros
                elif str(resultado['funcion']) == "predict_product":
                    pred += await str(predict_product({ "name": resultado['parametros']['producto']}))
                elif str(resultado['funcion']) == "predict_date":
                    # print(resultado['parametros']['fecha'])
                    
                    data = await predict_date({ "date":resultado['parametros']['fecha']})
                    print(data)
                    pred += str(data)
                elif str(resultado['funcion']) == "predict_product_fecha":
                    pred += await str(predict_product_fecha({ "name":resultado['parametros']['producto'],"date": resultado['parametros']['fecha']}))
                elif str(resultado['funcion']) == "top_selling":
                    data = await top_selling()
                    pred += f"Los 5 productos más vendidos son: {str(data)}"

                elif str(resultado['funcion']) == "least_selling":
                    data = await least_selling()
                    print(data)
                    pred += f"Los 5 productos menos vendidos son: {str(data)}"

                elif str(resultado['funcion']) == "generate_csv":
                    month = resultado["parametros"].get("mes")  # opcional
                    file = await generate_csv(month)
                    pred = +f"Se generó el CSV en: {str(file)}"

                elif str(resultado['funcion']) == "generate_excel":
                    month = resultado["parametros"].get("mes")  # opcional
                    file = await generate_excel(month)
                    pred = +f"Se generó el Excel en: {str(file)}"
            else:
                pred += "Lamentablemente no logré entender lo la solicitud, que haces, recuerda que puedo, hacer predicciónes tomando parametros como producto y fecha, y revisar productos más y menos vendidos, además de generar reportes en excel o csv."

    
    # #Valor en texto de las respuestas
    pred = naturalize_response(pred)
    
    # #Audio generado por gTTS
    # tts(pred)
    
    # #Json generado por rhubarb
    # generate_lipsync(pred)
    
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