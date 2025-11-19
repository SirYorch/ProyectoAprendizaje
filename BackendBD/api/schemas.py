"""
Esquemas Pydantic para validación de requests y responses.
Define la estructura de datos de entrada y salida de la API.
"""

from pydantic import BaseModel, Field
from datetime import date
from typing import List, Optional, Dict, Any
import pandas as pd




# ============ REQUEST SCHEMAS ============

class PredictProductStockRequest(BaseModel):
    """Request para predecir stock de un producto específico, en una fecha específica."""
    product_name: str
    predict_date: str
    
    class Config:
        json_schema_extra ={
            "example": {
                "product_name": "Laptop HP",
                "predict_date": "2025-04-01",
            }
        }


class PredictDateRequest(BaseModel):
    """Request para predecir inventario en una fecha."""
    prediction_date: date = Field(..., description="Fecha para la predicción")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prediction_date": "2025-12-31"
            }
        }


class PredictProductOutOfStockRequest(BaseModel):
    """Request para predecir cuándo se agotará un producto."""
    product_name: str = Field(..., description="Nombre del producto", min_length=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "Laptop HP"
            }
        }

class ChatRequest(BaseModel):
    """Request para chat con el agente LLM."""
    message: str = Field(..., description="Mensaje del usuario", min_length=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "¿Qué productos se agotarán esta semana?"
            }
        }



# ============ RESPONSE SCHEMAS ============

class ProductOutOfStockInfo(BaseModel):
    """Información de un producto que se quedará sin stock."""
    product_name: str
    predicted_stock:int 
    current_stock: int


class OutOfStockResponse(BaseModel):
    """Response con productos que se quedarán sin stock."""
    success: bool
    message: str
    total_products: int
    risk_date: date
    products_at_risk: List[ProductOutOfStockInfo]
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Predicción completada exitosamente",
                "total_products": 3,
                "risk_date": pd.to_datetime("2025-04-12"),
                "products_at_risk": [
                    {
                 
                        "product_name": "Laptop HP",
                        "current_stock": 5,
                        "predicted_out_date": "2025-12-15",
                        "days_until_out": 28,
                 
                    }
                ]
            }
        }


class ProductStockResponse(BaseModel):
    """Response con predicción de stock de un producto."""
    success: bool
    message: str
    product_name: str
    prediction_date: date
    predicted_stock: int
    current_stock: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Predicción completada",
                "product_name": "Laptop HP",
                "prediction_date": "2025-12-31",
                "predicted_stock": 8,
                "current_stock": 12,
            }
        }



class ProductPrediction(BaseModel):
    """Predicción individual de un producto."""
    product_name: str
    predicted_stock: int


class DatePredictionResponse(BaseModel):
    """Response con predicción de inventario para una fecha."""
    success: bool
    message: str
    prediction_date: str
    total_products: int
    predictions: List[ProductPrediction]
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Predicción completada",
                "prediction_date": "2025-12-31",
                "total_products": 2,
                "predictions": [
                    {
                      
                        "product_name": "Laptop HP",
                        "predicted_stock": 8,
                        
                    }
                ]
            }
        }
        

class ProductOutOfStockResponse(BaseModel):
    """Response con predicción de cuándo se agotará un producto."""
    success: bool
    message: str
    product_name: str
    predicted_out_date: str
    predictions: List[ProductPrediction]

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Predicción completada",
                "product_name": "Laptop HP",
                "predicted_out_date": "2025-12-15",
                "predictions": [
                    {
                      
                        "product_name": "Laptop HP",
                        "predicted_stock": 8,
                        
                    }
                ]
            }
        }
        
class ChatResponse(BaseModel):
    """Response del agente LLM."""
    success: bool
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Respuesta generada por el agente",
            }
        }


class RetrainResponse(BaseModel):
    """Response del proceso de reentrenamiento."""
    success: bool
    message: str
    filename: str
    rows_processed: int
    rows_inserted: int
    model_retrained: bool
    previous_accuracy: Optional[float] = Field(None, description="Precisión del modelo anterior")
    new_accuracy: Optional[float] = Field(None, description="Precisión del modelo nuevo")
    training_time_seconds: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Modelo reentrenado exitosamente",
                "filename": "nuevos_datos.csv",
                "rows_processed": 1500,
                "rows_inserted": 1500,
                "model_retrained": True,
                "previous_accuracy": 0.87,
                "new_accuracy": 0.91,
                "training_time_seconds": 45.3
            }
        }