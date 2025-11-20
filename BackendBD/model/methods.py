import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tensorflow as tf
import joblib
import os
from pathlib import Path
from db.predictions_saved import *

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Obtener el directorio base (BackendBD)
BASE_DIR = Path(__file__).resolve().parent.parent
FILES_DIR = BASE_DIR / "files/"

# Rutas a los archivos necesarios
DATASET_PATH = FILES_DIR / "dataset_preparado.csv"
MODEL_PATH = FILES_DIR / "modelo.h5"
SCALER_PATH = FILES_DIR / "scaler.pkl"

# Cargar datos y modelo
df = pd.read_csv(DATASET_PATH, parse_dates=["created_at"])
df = df.sort_values(["product_id", "created_at"])
model = tf.keras.models.load_model("files/modelo.h5", compile=False)
scaler = joblib.load("files/scaler.pkl")


# Variables usadas en el modelo 
FEATURES = [
    "quantity_on_hand",
    "quantity_reserved",
    "reorder_point",
    "optimal_stock_level",
    "average_daily_usage",
    "stock_status",
    "dia_semana",
    "fin_de_semana",
    "category"
]

TARGET = "quantity_available"
N_STEPS = 7



def build_sequence(product_id, target_date):
    df_p = df[df["product_id"] == product_id].copy()
    df_p = df_p.sort_values("created_at")
    

    
    # Tomamos los últimos N_STEPS días previos
    df_hist = df_p[df_p["created_at"] < target_date].tail(N_STEPS)
    
    currentStock = df_hist["quantity_on_hand"].iloc[0]

    if len(df_hist) < N_STEPS:
        raise ValueError(f"No hay suficientes datos para {product_id}. Se requieren {N_STEPS} días.")

    cols_scaler = FEATURES + [TARGET]

    scaled = scaler.transform(df_hist[cols_scaler])

    seq = scaled[:, :len(FEATURES)]

    return np.expand_dims(seq, axis=0)  , currentStock # (1, 7, n_features)



def get_last_known_data(product_id: str, before_date: datetime) -> pd.DataFrame:
    """
    Obtiene los últimos N_STEPS días de datos (reales o predichos).
    
    Prioridad:
    1. Datos reales del CSV
    2. Datos predichos del caché
    
    Args:
        product_id: ID del producto
        before_date: Fecha límite
    
    Returns:
        DataFrame con los últimos N_STEPS registros
    
    Raises:
        ValueError: Si no hay suficientes datos
    """
    df_p = df[df["product_id"] == product_id].copy()
    df_p = df_p.sort_values("created_at")
    
    # Última fecha con datos reales
    ultima_fecha_real = df_p["created_at"].max()
    
    # Si tenemos suficientes datos reales antes de before_date
    df_real = df_p[df_p["created_at"] < before_date]
    
    if len(df_real) >= N_STEPS:
        return df_real.tail(N_STEPS)
    
    # Necesitamos combinar datos reales + predichos del caché
    df_cached = get_cached_predictions(
        product_id,
        ultima_fecha_real + timedelta(days=1),
        before_date - timedelta(days=1)
    )
    
    if df_cached is not None and len(df_cached) > 0:
        combined = pd.concat([df_real, df_cached], ignore_index=True)
        combined = combined.sort_values("created_at")
        return combined.tail(N_STEPS)
    
    # Solo datos reales disponibles
    if len(df_real) < N_STEPS:
        raise ValueError(
            f"No hay suficientes datos para {product_id}. "
            f"Se requieren {N_STEPS} días, solo hay {len(df_real)}."
        )
    
    return df_real.tail(N_STEPS)


def prepare_sequence(df_window: pd.DataFrame) -> np.ndarray:
    """
    Prepara una secuencia para el modelo.
    
    Args:
        df_window: DataFrame con N_STEPS registros
    
    Returns:
        Array con forma (1, N_STEPS, n_features)
    """
    cols_scaler = FEATURES + [TARGET]
    scaled = scaler.transform(df_window[cols_scaler])
    seq = scaled[:, :len(FEATURES)]
    return np.expand_dims(seq, axis=0)


def inverse_scale_prediction(pred_scaled: float) -> float:
    """
    Desescala una predicción del modelo.
    
    Args:
        pred_scaled: Valor escalado predicho por el modelo
    
    Returns:
        Valor real desescalado
    """
    target_idx = scaler.feature_names_in_.tolist().index(TARGET)
    mean = scaler.mean_[target_idx]
    std = np.sqrt(scaler.var_[target_idx])
    return pred_scaled * std + mean


def create_features_dict(
    current_stock: float,
    ultimo_registro: pd.Series,
    fecha: datetime
) -> Dict[str, Any]:
    """
    Crea un diccionario con todos los features para guardar en caché.
    
    Args:
        current_stock: Stock actualizado
        ultimo_registro: Último registro conocido (para copiar features estáticos)
        fecha: Fecha de la predicción
    
    Returns:
        Diccionario con todos los features
    """
    return {
        'quantity_on_hand': float(current_stock),
        'quantity_reserved': float(ultimo_registro['quantity_reserved']),
        'reorder_point': float(ultimo_registro['reorder_point']),
        'optimal_stock_level': float(ultimo_registro['optimal_stock_level']),
        'average_daily_usage': float(ultimo_registro['average_daily_usage']),
        'stock_status': int(ultimo_registro['stock_status']),
        'dia_semana': int(fecha.dayofweek),
        'fin_de_semana': 1 if fecha.dayofweek >= 5 else 0,
        'category': int(ultimo_registro['category'])
    }


# ==================== FUNCIÓN PRINCIPAL ====================

def predict_stock(
    product_id: str, 
    date: str, 
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Predice el stock de un producto de forma recursiva con caché inteligente.
    
    Proceso:
    1. Verifica si la fecha está en datos reales → retorna datos reales
    2. Verifica si está completamente en caché → retorna del caché
    3. Predice recursivamente día por día:
       - Reutiliza días ya cacheados
       - Calcula y cachea días faltantes
       - Actualiza stock acumulativamente
    
    Args:
        product_id: ID del producto (ej. 'PROD-005')
        date: Fecha objetivo (str 'YYYY-MM-DD' o datetime)
        use_cache: Si True, usa y guarda predicciones en caché
    
    Returns:
        Diccionario con:
        - product_name: ID del producto
        - predicted_stock: Stock predicho para la fecha objetivo
        - current_stock: Stock actual (último dato real)
        - dias_predichos: Días entre última fecha real y objetivo
        - predicciones_generadas: Días calculados (no estaban en caché)
        - predicciones_desde_cache: Días obtenidos del caché
        - fecha_inicial: Última fecha con datos reales
        - fecha_objetivo: Fecha solicitada
        - tipo: Tipo de resultado ('datos_reales', 'cache', 'prediccion_recursiva')
    
    Raises:
        ValueError: Si no hay suficientes datos históricos
    """
    # Convertir fecha objetivo a datetime
    if isinstance(date, str):
        target_date = pd.to_datetime(date)
    else:
        target_date = pd.to_datetime(date)
    
    # Obtener datos históricos del producto
    df_p = df[df["product_id"] == product_id].copy()
    
    if len(df_p) == 0:
        return {
            "error": f"No se encontraron datos para el producto {product_id}",
            "product_name": product_id
        }
    
    df_p = df_p.sort_values("created_at")
    
    # Última fecha con datos reales
    ultima_fecha_real = df_p["created_at"].max()
    current_stock_real = df_p["quantity_on_hand"].iloc[-1]
    
    # CASO 1: La fecha objetivo ya pasó - retornar datos reales
    if target_date <= ultima_fecha_real:
        actual_data = df_p[df_p["created_at"] == target_date]
        if len(actual_data) > 0:
            return {
                "product_name": product_id,
                "predicted_stock": round(float(actual_data["quantity_on_hand"].iloc[0]), 2),
                "current_stock": round(float(current_stock_real), 2),
                "dias_predichos": 0,
                "fecha_objetivo": target_date.strftime("%Y-%m-%d"),
                "tipo": "datos_reales"
            }
    
    # CASO 2: Verificar si tenemos la predicción completa en caché
    if use_cache:
        cached = get_single_cached_prediction(product_id, target_date)
        if cached is not None:
            return {
                "product_name": product_id,
                "predicted_stock": round(float(cached['predicted_stock']), 2),
                "current_stock": round(float(current_stock_real), 2),
                "dias_predichos": (target_date - ultima_fecha_real).days,
                "predicciones_generadas": 0,
                "predicciones_desde_cache": (target_date - ultima_fecha_real).days,
                "fecha_inicial": ultima_fecha_real.strftime("%Y-%m-%d"),
                "fecha_objetivo": target_date.strftime("%Y-%m-%d"),
                "tipo": "cache"
            }
    
    # CASO 3: PREDICCIÓN RECURSIVA con caché incremental
    fecha_actual = ultima_fecha_real + timedelta(days=1)
    current_stock = current_stock_real
    dias_predichos = 0
    predicciones_generadas = 0
    
    while fecha_actual <= target_date:
        # Intentar obtener del caché primero
        if use_cache:
            cached_day = get_single_cached_prediction(product_id, fecha_actual)
            if cached_day is not None:
                current_stock = cached_day['predicted_stock']
                fecha_actual += timedelta(days=1)
                dias_predichos += 1
                continue
        
        # No está en caché, necesitamos predecir
        try:
            df_window = get_last_known_data(product_id, fecha_actual)
        except ValueError as e:
            return {
                "error": str(e),
                "product_name": product_id
            }
        
        # Preparar secuencia y predecir
        X_input = prepare_sequence(df_window)
        pred_scaled = model.predict(X_input, verbose=0)[0][0]
        pred_demanda = inverse_scale_prediction(pred_scaled)
        
        # Actualizar stock: stock actual - demanda predicha
        current_stock = max(0, current_stock - pred_demanda)
        
        # Preparar features para guardar en caché
        ultimo_registro = df_window.iloc[-1]
        features_dict = create_features_dict(
            current_stock, 
            ultimo_registro, 
            fecha_actual
        )
        
        # Guardar en caché
        if use_cache:
            save_prediction_to_cache(
                product_id,
                fecha_actual,
                current_stock,
                pred_demanda,
                features_dict
            )
            predicciones_generadas += 1
        
        fecha_actual += timedelta(days=1)
        dias_predichos += 1
    
    return {
        "product_name": product_id,
        "predicted_stock": round(float(current_stock), 2),
        "current_stock": round(float(current_stock_real), 2),
        "dias_predichos": dias_predichos,
        "predicciones_generadas": predicciones_generadas,
        "predicciones_desde_cache": dias_predichos - predicciones_generadas,
        "fecha_inicial": ultima_fecha_real.strftime("%Y-%m-%d"),
        "fecha_objetivo": target_date.strftime("%Y-%m-%d"),
        "tipo": "prediccion_recursiva"
    }


def predict_stock_range(
    product_id: str,
    start_date: str,
    end_date: str,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    Predice el stock para un rango de fechas.
    
    Args:
        product_id: ID del producto
        start_date: Fecha inicial
        end_date: Fecha final
        use_cache: Si usa caché
    
    Returns:
        Diccionario con predicciones diarias y estadísticas
    """
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    
    # Primero predecir hasta la fecha final (esto cachea todos los días)
    result = predict_stock(product_id, end_date, use_cache)
    
    if "error" in result:
        return result
    
    # Obtener todas las predicciones del rango desde el caché
    predictions = get_cached_predictions(product_id, start, end)
    
    if predictions is None or len(predictions) == 0:
        return {
            "error": "No se pudieron obtener las predicciones del rango",
            "product_name": product_id
        }
    
    # Formatear para respuesta
    daily_predictions = []
    for _, row in predictions.iterrows():
        daily_predictions.append({
            "date": row['created_at'].strftime("%Y-%m-%d"),
            "predicted_stock": round(float(row['quantity_available']), 2)
        })
    
    return {
        "product_name": product_id,
        "start_date": start_date,
        "end_date": end_date,
        "total_days": len(daily_predictions),
        "daily_predictions": daily_predictions,
        "final_stock": result["predicted_stock"],
        "current_stock": result["current_stock"]
    }
