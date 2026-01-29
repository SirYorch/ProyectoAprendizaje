"""
Wrapper simplificado para reentrenamiento desde la API.
Compatible con sistema refactorizado que carga datos desde PostgreSQL.
"""

import pandas as pd
import time
import io
import tempfile

from model.reentrenamiento import (
    reentrenar_y_evaluar, 
    aplicar_modelo_candidato,
    descartar_modelo_candidato,
    listar_modelos_candidatos
)

try:
    from . import methods as model_methods
    from db.predictions_saved import clear_all_cache
    from db.Tables import cargarnuevosRegistros
except ImportError:
    import model.methods as model_methods
    from db.predictions_saved import clear_all_cache
    from db.Tables import cargarnuevosRegistros


def retrain_manual_evaluate(csv_content: bytes = None, filename: str = None, 
                           epochs: int = 15, batch_size: int = 128, 
                           cargar_a_bd: bool = False) -> dict:
    """
    Reentrena el modelo y retorna métricas para APROBACIÓN MANUAL.
    
    Returns:
        dict: Respuesta simplificada con métricas y recomendación
    """
    start_time = time.time()
    
    try:
        # Cargar CSV a BD si se especifica
        rows_inserted = 0
        if cargar_a_bd and csv_content:
            df_nuevo = pd.read_csv(io.BytesIO(csv_content))
            rows_inserted = len(df_nuevo)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                tmp.write(csv_content)
                cargarnuevosRegistros(tmp.name)
        
        # Reentrenar
        reporte = reentrenar_y_evaluar(epochs=epochs, batch_size=batch_size)
        training_time = time.time() - start_time
        
        # Respuesta limpia
        return {
            "success": True,
            "message": "Reentrenamiento completado. Esperando aprobación.",
            "training_time_seconds": round(training_time, 2),
            "version": reporte['version'],
            "metricas_anterior": reporte['metricas_anterior'],
            "metricas_nuevo": reporte['metricas_nuevo'],
            "comparacion": reporte['comparacion'],
            "recomendacion": reporte['recomendacion'],
            "datos": reporte['datos']
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "training_time_seconds": round(time.time() - start_time, 2)
        }


def retrain_manual_approve(version: str) -> dict:
    """Aplica modelo candidato en producción."""
    try:
        resultado = aplicar_modelo_candidato(version)
        
        # Recargar modelo en memoria
        try:
            model_methods.reload_model()
            clear_all_cache()
            reload_ok = True
        except:
            reload_ok = False
        
        return {
            "success": True,
            "message": "Modelo aplicado exitosamente",
            "version": version,
            "model_reloaded": reload_ok
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "version": version
        }


def retrain_manual_reject(version: str) -> dict:
    """Rechaza modelo candidato."""
    try:
        descartar_modelo_candidato(version)
        return {
            "success": True,
            "message": "Modelo descartado",
            "version": version
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}"
        }


def retrain_manual_list_candidates() -> dict:
    """Lista modelos candidatos pendientes."""
    try:
        candidatos = listar_modelos_candidatos()
        return {
            "success": True,
            "candidatos": candidatos,
            "count": len(candidatos)
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "candidatos": []
        }


# Alias para compatibilidad con endpoints existentes
def retrain_from_csv(csv_content: bytes, filename: str, epochs: int = 15, 
                     batch_size: int = 128, modo: str = "manual", 
                     cargar_a_bd: bool = False, **kwargs) -> dict:
    """
    Función principal compatible con endpoints existentes.
    Solo soporta modo manual.
    """
    if modo != "manual":
        return {
            "success": False,
            "message": "Solo se soporta modo 'manual'"
        }
    
    return retrain_manual_evaluate(
        csv_content=csv_content,
        filename=filename,
        epochs=epochs,
        batch_size=batch_size,
        cargar_a_bd=cargar_a_bd
    )


def retrain_from_database(epochs: int = 15, batch_size: int = 128, **kwargs) -> dict:
    """Reentrena solo desde datos en PostgreSQL (sin CSV)."""
    return retrain_manual_evaluate(
        csv_content=None,
        filename=None,
        epochs=epochs,
        batch_size=batch_size,
        cargar_a_bd=False
    )