import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tensorflow as tf
import joblib
import os


os.environ["CUDA_VISIBLE_DEVICES"] = "-1"


df = pd.read_csv("dataset_preparado.csv", parse_dates=["created_at"])
df = df.sort_values(["product_id", "created_at"])
model = tf.keras.models.load_model("modelo.h5", compile=False)
scaler = joblib.load("scaler.pkl")


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

    if len(df_hist) < N_STEPS:
        raise ValueError(f"No hay suficientes datos para {product_id}. Se requieren {N_STEPS} días.")

    cols_scaler = FEATURES + [TARGET]

    scaled = scaler.transform(df_hist[cols_scaler])

    seq = scaled[:, :len(FEATURES)]

    return np.expand_dims(seq, axis=0)   # (1, 7, n_features)


def predict_stock(product_id: str, date: str):
    if isinstance(date, str):
        date = datetime.strptime(date, "%Y-%m-%d")
    
    X = build_sequence(product_id, date)
    
    pred_scaled = model.predict(X)[0][0]
    
    # Desescalar (invertir StandardScaler)
    target_idx = scaler.feature_names_in_.tolist().index(TARGET)
    mean = scaler.mean_[target_idx]
    std = np.sqrt(scaler.var_[target_idx])
    
    pred_real = pred_scaled * std + mean

    return {
        "product_id": product_id,
        "fecha_objetivo": date.strftime("%Y-%m-%d"),
        "prediccion_stock": round(float(pred_real), 2)
    }
