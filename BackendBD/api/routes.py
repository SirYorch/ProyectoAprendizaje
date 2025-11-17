"""
Rutas HTTP para las predicciones de inventario.
Define los endpoints de la API REST.
"""

from fastapi import APIRouter, Query, HTTPException, File, UploadFile
from datetime import date
from typing import Dict, Any
from model.methods import predict_stock

from .schemas import *

router = APIRouter()


@router.get(
    "/predict/out-of-stock",
    response_model=OutOfStockResponse,
    summary="Predecir productos fuera de stock",
    description="Predice qué productos se quedarán sin stock próximamente"
)
async def predict_out_of_stock() -> Dict[str, Any]:
    """
    Predice los productos que se quedarán sin stock.
    
    Returns:
        Dict con la lista de productos y probabilidades de quedarse sin stock
    """
    
    
    PRODUCTS = ["Laptop HP", "Monitor Samsung", "Mouse Logitech"]

    today = date.today()
    results = []

    for product in PRODUCTS:
        pred = predict_stock(
            product_id=product,
            date=today.strftime("%Y-%m-%d")
        )

        if pred["prediccion_stock"] <= 0:
            results.append({
                "product_name": product,
                "predicted_stock": pred["prediccion_stock"]
            })

    return {"out_of_stock_products": results}


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
    pred = predict_stock(
        product_id=request.product_name,
        date=request.prediction_date.strftime("%Y-%m-%d")
    )

    return {
        "product_name": request.product_name,
        "prediction_date": request.prediction_date,
        "predicted_stock": pred["prediccion_stock"]
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
    PRODUCTS = ["Laptop HP", "Monitor Samsung", "Mouse Logitech"]

    results = []

    for product in PRODUCTS:
        pred = predict_stock(
            product_id=product,
            date=request.prediction_date.strftime("%Y-%m-%d")
        )

        results.append({
            "product_name": product,
            "prediction_date": request.prediction_date,
            "predicted_stock": pred["prediccion_stock"]
        })

    return {
        "prediction_date": request.prediction_date,
        "inventory_predictions": results
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
    today = date.today()

    # Buscar hasta 365 días hacia adelante
    for offset in range(0, 365):
        check_date = today + timedelta(days=offset)
        pred = predict_stock(
            product_id=product,
            date=check_date.strftime("%Y-%m-%d")
        )

        if pred["prediccion_stock"] <= 0:
            return {
                "product_name": product,
                "out_of_stock_date": check_date
            }

    # Si nunca se agota en 1 año
    return {
        "product_name": product,
        "out_of_stock_date": None
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
    # TODO: Implementar integración con Deepseek-r1:8b
    return {
        "success": True,
        "message": request.message,
        "agent_response": "Hola mundo"
    }


@router.post(
    "/upload/retrain",
    response_model=RetrainResponse,
    summary="Cargar CSV y reentrenar modelo",
    description="Sube un archivo CSV con nuevos datos para reentrenar el modelo de predicción"
)
async def upload_and_retrain(
    file: UploadFile = File(..., description="Archivo CSV con datos de entrenamiento")
) -> Dict[str, Any]:
    """
    Recibe un archivo CSV, lo procesa y reentrena el modelo.
    
    Args:
        file: Archivo CSV con columnas: fecha, producto, stock, ventas, etc.
        
    Returns:
        Dict con información del proceso de reentrenamiento
    """
    # TODO: Implementar validación del CSV
    # TODO: Implementar inserción en base de datos
    # TODO: Implementar reentrenamiento del modelo
    pass