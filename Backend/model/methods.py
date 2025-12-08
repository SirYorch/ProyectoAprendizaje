import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tensorflow as tf
import joblib
import os
from pathlib import Path
from db.predictions_saved import *
import threading

# Cargar data from database
from model.db_loader import load_inventory_dataset

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# Obtener el directorio base (BackendBD)
BASE_DIR = Path(__file__).resolve().parent.parent
FILES_DIR = BASE_DIR / "files/"

# Rutas a los archivos necesarios
DATASET_PATH = FILES_DIR / "dataset_preparado.csv"
MODEL_PATH = FILES_DIR / "modelo.h5"
SCALER_PATH = FILES_DIR / "scaler.pkl"


# Cargar datos y modelo al inicio
df = load_inventory_dataset()
df = df.sort_values(["product_id", "created_at"])
# Cargar modelo y scaler con rutas centralizadas
def _load_model_and_scaler(model_path=MODEL_PATH, scaler_path=SCALER_PATH):
    m = tf.keras.models.load_model(str(model_path), compile=False)
    s = joblib.load(str(scaler_path))
    return m, s

# Variables globales y lock para recarga segura
_model_lock = threading.Lock()
model, scaler = _load_model_and_scaler()


def reload_model(model_path: Path = MODEL_PATH, scaler_path: Path = SCALER_PATH) -> bool:
    """Recarga el modelo y el scaler en memoria desde los ficheros dados.

    Retorna True si la recarga fue exitosa, lanza excepción en caso contrario.
    """
    global model, scaler
    try:
        with _model_lock:
            print(f"→ Recargando modelo desde {model_path} y scaler desde {scaler_path}")
            m, s = _load_model_and_scaler(model_path, scaler_path)
            model = m
            scaler = s
        print("✓ Modelo recargado en memoria")
        return True
    except Exception as e:
        print("✗ Error recargando modelo:", e)
        raise


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
    use_cache: bool = False   
) -> Dict[str, Any]:
    """
    Predice el stock de un producto de forma recursiva, día a día,
    usando siempre ventanas de longitud N_STEPS.

    - Si la fecha objetivo está dentro de los datos reales -> devuelve dato real.
    - Si es futura -> parte de los últimos N_STEPS días reales y
      va generando días sintéticos usando el modelo, actualizando la ventana.
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
    current_stock_real = float(df_p["quantity_on_hand"].iloc[-1])
    
    # CASO 1: La fecha objetivo está en los datos reales -> dato real
    if target_date <= ultima_fecha_real:
        actual_data = df_p[df_p["created_at"] == target_date]
        if len(actual_data) > 0:
            return {
                "product_name": product_id,
                "predicted_stock": round(float(actual_data["quantity_on_hand"].iloc[0]), 2),
                "current_stock": round(current_stock_real, 2),
                "dias_predichos": 0,
                "fecha_inicial": ultima_fecha_real.strftime("%Y-%m-%d"),
                "fecha_objetivo": target_date.strftime("%Y-%m-%d"),
                "tipo": "datos_reales"
            }
    
    # CASO 2: Predicción futura recursiva 
    # Tomamos los últimos N_STEPS días reales como ventana inicial
    df_hist = df_p[df_p["created_at"] <= ultima_fecha_real].tail(N_STEPS).copy()
    if len(df_hist) < N_STEPS:
        return {
            "error": f"No hay suficientes datos para {product_id}. "
                     f"Se requieren {N_STEPS} días, solo hay {len(df_hist)}.",
            "product_name": product_id
        }
    
    # Vamos a ir generando días sintéticos desde el día siguiente al último real
    fecha_actual = ultima_fecha_real + timedelta(days=1)
    dias_predichos = 0
    predicted_stock = current_stock_real  # valor que iremos actualizando
    
    # Para copiar features estáticos del último registro real
    ultimo_real = df_hist.iloc[-1]
    
    while fecha_actual <= target_date:
        # Construir ventana escalada a partir de df_hist (últimos N_STEPS registros, reales + sintéticos)
        cols_scaler = FEATURES + [TARGET]
        window_scaled = scaler.transform(df_hist[cols_scaler])
        X_input = np.expand_dims(window_scaled[:, :len(FEATURES)], axis=0)  # (1, N_STEPS, n_features)
        
        # Predecir quantity_available del nuevo día (en espacio original)
        pred_scaled = model.predict(X_input, verbose=0)[0][0]
        predicted_quantity = inverse_scale_prediction(pred_scaled)
        
        # Crear un nuevo registro sintético para fecha_actual
        new_row = {
            "product_id": product_id,
            "created_at": fecha_actual,
            "quantity_available": float(predicted_quantity),
            # Para simplificar, tomamos quantity_on_hand como quantity_available predicho
            "quantity_on_hand": float(predicted_quantity),
            "quantity_reserved": float(ultimo_real["quantity_reserved"]),
            "reorder_point": float(ultimo_real["reorder_point"]),
            "optimal_stock_level": float(ultimo_real["optimal_stock_level"]),
            "average_daily_usage": float(ultimo_real["average_daily_usage"]),
            "stock_status": int(ultimo_real["stock_status"]),
            "anio": fecha_actual.year,
            "mes": fecha_actual.month,
            "dia_semana": fecha_actual.dayofweek,
            "fin_de_semana": 1 if fecha_actual.dayofweek >= 5 else 0,
            "category": int(ultimo_real.get("category", 0)),
        }
        
        # Añadir este nuevo día a la ventana y quedarnos con los últimos N_STEPS
        df_hist = pd.concat([df_hist, pd.DataFrame([new_row])], ignore_index=True)
        df_hist = df_hist.sort_values("created_at").tail(N_STEPS).copy()
        
        predicted_stock = float(predicted_quantity)
        dias_predichos += 1
        fecha_actual += timedelta(days=1)
    
    return {
        "product_name": product_id,
        "predicted_stock": round(predicted_stock, 2),
        "current_stock": round(current_stock_real, 2),
        "dias_predichos": dias_predichos,
        "predicciones_generadas": dias_predichos,
        "predicciones_desde_cache": 0,
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
    # Desactivar caché
    use_cache = False

    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    # Calcular predicciones día a día 
    daily_predictions = []
    current = start
    final_result = None

    while current <= end:
        res = predict_stock(
            product_id=product_id,
            date=current.strftime("%Y-%m-%d"),
            use_cache=False
        )
        if "error" in res:
            return res

        daily_predictions.append({
            "date": current.strftime("%Y-%m-%d"),
            "predicted_stock": res["predicted_stock"],
        })
        final_result = res
        current += timedelta(days=1)

    if final_result is None:
        return {
            "error": "Rango de fechas vacío",
            "product_name": product_id
        }

    return {
        "product_name": product_id,
        "start_date": start_date,
        "end_date": end_date,
        "total_days": len(daily_predictions),
        "daily_predictions": daily_predictions,
        "final_stock": final_result["predicted_stock"],
        "current_stock": final_result["current_stock"],
    }


def clean_numpy(value):
    """Convierte numpy types a tipos nativos de Python."""
    import numpy as np

    if isinstance(value, (np.floating, np.float32, np.float64)):
        return float(value)
    if isinstance(value, (np.integer, np.int32, np.int64)):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return value

def reload_dataset(dataset_path: Path = DATASET_PATH) -> bool:
    """Recarga el dataset de inventario en memoria"""
    global df
    try:
        df = load_inventory_dataset()
        print(f"✓ Dataset recargado en memoria")
        return True
    except Exception as e:
        print("✗ Error recargando dataset:", e)
        raise