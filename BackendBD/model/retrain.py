"""
Wrapper para el reentrenamiento del modelo desde la API.
Simplificado: todo trabaja desde BackendBD/model/
"""

import pandas as pd
from pathlib import Path
from datetime import datetime
import time
import io

# Importar función de reentrenamiento desde el mismo módulo
from .reentrenamiento import reentrenar_modelo


def retrain_from_csv(
    csv_content: bytes,
    filename: str,
    epochs: int = 5,
    batch_size: int = 128,
    umbral_degradacion: float = 0.1
) -> dict:
    """
    Reentrena el modelo desde un CSV subido.
    
    Args:
        csv_content: Contenido del archivo CSV en bytes
        filename: Nombre del archivo original
        epochs: Número de épocas para reentrenamiento
        batch_size: Tamaño del batch
        umbral_degradacion: Porcentaje permitido de degradación (0.1 = 10%)
    
    Returns:
        Dict con resultados del reentrenamiento
    """
    start_time = time.time()
    
    try:
        # 1. Convertir bytes a DataFrame
        df_nuevo = pd.read_csv(io.BytesIO(csv_content))
        rows_processed = len(df_nuevo)
        
        # 2. Llamar directamente a la función de reentrenamiento
        # (ya está configurada para trabajar desde BackendBD)
        resultados = reentrenar_modelo(
            df_nuevo=df_nuevo,
            epochs=epochs,
            batch_size=batch_size,
            umbral_degradacion=umbral_degradacion,
            usar_early_stopping=True,
            patience=5
        )
        
        # 3. Calcular tiempo de entrenamiento
        training_time = time.time() - start_time
        
        # 4. Formatear respuesta para el schema
        return {
            "success": resultados.get("exito", False),
            "message": resultados.get("mensaje", "Reentrenamiento completado"),
            "filename": filename,
            "rows_processed": rows_processed,
            "model_retrained": resultados.get("exito", False),
            # "previous_accuracy": resultados.get("old_rmse"),  # Usando RMSE como métrica
            # "new_accuracy": resultados.get("new_rmse"),  # Usando RMSE como métrica
            "training_time_seconds": round(training_time, 2),
            # Datos adicionales
            "version": resultados.get("version"),
            "previous_rmse": resultados.get("previous_rmse"),
            "new_rmse": resultados.get("new_rmse"),
            "previous_mae": resultados.get("previous_mae"),
            "new_mae": resultados.get("new_mae"),
            "mejora_rmse_pct": resultados.get("mejora_rmse_pct"),
            "mejora_mae_pct": resultados.get("mejora_mae_pct"),
        }
    
    except Exception as e:
        training_time = time.time() - start_time
        return {
            "success": False,
            "message": f"Error en reentrenamiento: {str(e)}",
            "filename": filename,
            "rows_processed": 0,
            "rows_inserted": 0,
            "model_retrained": False,
            "previous_accuracy": None,
            "new_accuracy": None,
            "training_time_seconds": round(training_time, 2)
        }
