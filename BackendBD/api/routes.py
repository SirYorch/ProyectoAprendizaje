"""
Rutas HTTP para las predicciones de inventario.
Define los endpoints de la API REST.
"""

from fastapi import APIRouter, Query, HTTPException, File, UploadFile
from datetime import date , timedelta
from typing import Dict, Any
from model.methods import predict_stock
from agent.agent import naturalize_response
from db.getters import get_products
from model.query_prediction import *
from model.retrain import retrain_from_csv
import pandas as pd

from .schemas import *

router = APIRouter()


@router.get(
    "/predict/out-of-stock",
    response_model=OutOfStockResponse,
    summary="Predecir productos fuera de stock",
    description="Predice qué productos se quedarán sin stock próximamente"
)
async def predict_out_of_stock() -> Dict[List, Any]:
    """
    Predice los productos hasta que uno se ŕediga sin stock
    Returns:
        Dict con la lista de productos y probabilidades de quedarse sin stock
    """
    
    PRODUCTS = get_products()
    

    day = date.today()
    results = []

    for i in range (30):
        zero = False
        for product in PRODUCTS:
            pred = predict_stock(
                product_id=product,
                date=day)
            day = day+ timedelta(days=1)
            
            results.append({
                    "product_name": product,
                    "predicted_stock": int(pred["predicted_stock"]),
                    "current_stock": pred["current_stock"],
                })
            if(int(pred["predicted_stock"]) <= 0):
                zero = True
                break
        if zero == True:
            break
        
    
    
    return {
        "success": True,
        "message": "Predicción completada exitosamente",
        "total_products": 3,
        "risk_date": pd.to_datetime("2025-04-12"),
        "products_at_risk": results}


@router.post(
    "/predict/product-stock",
    response_model=ProductStockResponse,
    summary="Predecir stock de producto específico",
    description="Predice el stock de un producto en una fecha determinada"
)
async def predict_product_stock(request: PredictProductStockRequest) -> Dict[str, Any]:
    """
    Predice el stock de un producto específico en una fecha.
    
    Args:
        request: Contiene product_name (str) y prediction_date (date)
        
    Returns:
        Dict con predicción de stock para el producto y fecha especificados
    """
    
    producto = request.product_name
    
    fecha = request.predict_date
    
    print("Hola mundo")
    pred = predict_stock(
        product_id=producto,
        date=fecha )
    
        
        
        
    return {
                "success": True,
                "message": "Predicción completada",
                "product_name": producto,
                "prediction_date": fecha,
                "predicted_stock": int(pred["predicted_stock"]),
                "current_stock": pred["current_stock"],
            }


@router.post(
    "/predict/date",
    response_model=DatePredictionResponse,
    summary="Predecir inventario para una fecha",
    description="Predice el estado del inventario completo para una fecha específica"
)
async def predict_date(request: PredictDateRequest) -> Dict[str, Any]:
    """
    Predice el estado del inventario para una fecha específica.
    
    Args:
        request: Contiene prediction_date (date)
        
    Returns:
        Dict con predicciones de todos los productos para la fecha especificada
    """
    PRODUCTS = get_products()
    
    results = []

    for product in PRODUCTS:
        pred = predict_stock(
            product_id=product,
            date=request.prediction_date.strftime("%Y-%m-%d")
        )

        results.append({
            "product_name": product,
            "predicted_stock": int(pred["predicted_stock"])
        })

    return {
                "success": True,
                "message": "Predicción completada",
                "prediction_date": str(request.prediction_date),
                "total_products": len(results),
                "predictions": results
            }







@router.post(
    "/predict/product-out-of-stock",
    response_model=ProductOutOfStockResponse,
    summary="Predecir cuándo se agotará un producto",
    description="Predice la fecha en que un producto específico se quedará sin stock"
)
async def predict_product_out_of_stock(
    request: PredictProductOutOfStockRequest
) -> Dict[str, Any]:
    """
    Predice cuándo un producto específico se quedará sin stock.
    
    Args:
        request: Contiene product_name (str)
        
    Returns:
        Dict con la fecha estimada de agotamiento del producto
    """
    product = request.product_name
    day = date.today()

    predictions = []
    # Buscar hasta 365 días hacia adelante
    for i in range (30):
        day = day+timedelta(days=1)
        print(day)
        pred = predict_stock(
            product_id=product,
            date=day
        )

        predictions.append(
            {
                      
                        "product_name": product,
                        "predicted_stock": int(pred["predicted_stock"]),
                        
                    }
        )
        if pred["predicted_stock"] <= 0:
            break

    # Si nunca se agota en 1 año
    return  {
                "success": True,
                "message": "Predicción completada",
                "product_name": product,
                "predicted_out_date": str(day),
                "predictions": predictions
            }
    
    
    
    
    
        

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Interactuar con el agente LLM",
    description="Envía un mensaje al agente LLM para consultas en lenguaje natural"
)
async def chat_with_agent(request: ChatRequest) -> Dict[str, Any]:
    """
    Procesa un mensaje en lenguaje natural usando el agente LLM.
    
    Args:
        request: Contiene message (str) con la consulta del usuario
        
    Returns:
        Dict con la respuesta del agente LLM
    """
    
    
    classifier = IntentClassifier()
    
    # Cargar o entrenar modelo
    model_path = "files/intent_classifier.pkl"
    classifier.load_model(model_path)
    
    endpoint, confidence, label = classifier.predict_intent(request.message)
    params = classifier.extract_parameters(request.message, endpoint)
    
    # print(f"  → Endpoint: {endpoint}")
    # print(f"  → Confianza: {confidence:.2%}")
    # print(f"  → Parámetros: {params}")
    res = {}
    
    if(confidence > 80):    
        if(endpoint == predict_out_of_stock):
            res = predict_out_of_stock()
        elif(endpoint == predict_product_stock):
            res = predict_product_stock(params["product_name"],params["prediction_date"])
        elif(endpoint == predict_date):
            res = predict_date(params["prediction_date"])
        elif(endpoint == predict_product_out_of_stock):
            res = predict_product_out_of_stock(params["product_name"])
    else:
        res = f"no logré encontrar un resultado para la busqueda: {request.message}"    
    
    
    # ans = predict_intent(request.message)
    req = naturalize_response(res)
    
    return {
        "success": True,
        "message": req
    }













@router.post(
    "/upload/retrain",
    response_model=RetrainResponse,
    summary="Cargar CSV y reentrenar modelo",
    description="Sube un archivo CSV con nuevos datos para reentrenar el modelo de predicción"
)
async def upload_and_retrain(
    file: UploadFile = File(..., description="Archivo CSV con datos de entrenamiento"),
    epochs: int = Query(5, description="Número de épocas para reentrenamiento", ge=1, le=100),
    batch_size: int = Query(128, description="Tamaño del batch", ge=16, le=512),
    umbral_degradacion: float = Query(0.1, description="Porcentaje permitido de degradación (0.1 = 10%)", ge=0.0, le=1.0)
) -> Dict[str, Any]:
    """
    Recibe un archivo CSV, lo procesa y reentrena el modelo.
    
    Args:
        file: Archivo CSV con columnas: fecha, producto, stock, ventas, etc.
        epochs: Número de épocas para reentrenamiento (default: 15)
        batch_size: Tamaño del batch (default: 128)
        umbral_degradacion: Porcentaje permitido de degradación (default: 0.1 = 10%)
        
    Returns:
        Dict con información del proceso de reentrenamiento
    """
    # Validar que sea un archivo CSV
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="El archivo debe ser un CSV (.csv)"
        )
    
    try:
        # Leer el contenido del archivo
        contents = await file.read()
        
        # Validar que no esté vacío
        if len(contents) == 0:
            raise HTTPException(
                status_code=400,
                detail="El archivo CSV está vacío"
            )
        
        # Llamar a la función de reentrenamiento
        resultado = retrain_from_csv(
            csv_content=contents,
            filename=file.filename,
            epochs=epochs,
            batch_size=batch_size,
            umbral_degradacion=umbral_degradacion
        )
        
        # Si falló, devolver error
        if not resultado.get("success", False):
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