"""
Script de Reentrenamiento Automático del Modelo LSTM
======================================================
Actualiza el modelo con nuevos datos manteniendo consistencia con el entrenamiento inicial.
Incluye validación de mejora, versionado y rollback automático.
"""

import pandas as pd
import numpy as np
import tensorflow as tf
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib
import mlflow
import mlflow.keras
from pathlib import Path
import logging
import json



SEED = 42
tf.random.set_seed(SEED)
np.random.seed(SEED)

# Features y target
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

DATASET_FILE = "dataset_preparado.csv"
MODEL_FILE = "model.keras"
SCALER_FILE = "scaler.pkl"
BACKUP_DIR = Path("model_backups")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('retraining.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FUNCIONES AUXILIARES

def preparar_csv_crudo(df):
    """
    Convierte un CSV crudo a dataset listo para el modelo.
    Debe ser idéntico al preprocesamiento del entrenamiento inicial.
    """
    df = df.copy()
    
    # Asegurar fechas
    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.sort_values(["product_id", "created_at"])
    
    # Asegurar categoría numérica
    if df["category"].dtype == 'object':
        df["category"] = df["category"].astype(int)
    
    # Variables temporales
    df["dia_semana"] = df["created_at"].dt.dayofweek
    df["fin_de_semana"] = (df["dia_semana"] >= 5).astype(int)
    
    # Reemplazar NaN
    df["average_daily_usage"] = df["average_daily_usage"].fillna(0)
    
    # Seleccionar columnas necesarias
    cols_necesarias = [
        "product_id", "created_at", "quantity_on_hand", "quantity_reserved",
        "quantity_available", "reorder_point", "optimal_stock_level",
        "average_daily_usage", "stock_status", "dia_semana", 
        "fin_de_semana", "category"
    ]
    
    return df[cols_necesarias]


def make_sequences(df_scaled, feat_cols, target_col, n_steps=N_STEPS):
    """
    Crea secuencias temporales para LSTM.
    Idéntico al entrenamiento inicial.
    """
    X, y = [], []
    for pid, g in df_scaled.groupby("product_id"):
        g = g.sort_values("created_at")
        vals = g[feat_cols + [target_col]].values
        
        for i in range(n_steps, len(g)):
            X.append(vals[i-n_steps:i, :-1])
            y.append(vals[i, -1])
    
    return np.array(X), np.array(y)


def preparar_datos(df, scaler=None):
    """
    Divide y escala datos para entrenamiento.
    Si se proporciona scaler, lo usa; sino, crea uno nuevo.
    """
    df = df.sort_values(["product_id", "created_at"])
    
    # Split temporal
    min_date = df["created_at"].min()
    max_date = df["created_at"].max()
    total_days = (max_date - min_date).days
    
    train_end = min_date + timedelta(days=int(total_days * 0.7))
    val_end   = min_date + timedelta(days=int(total_days * 0.85))
    
    df_train = df[df["created_at"] <= train_end].copy()
    df_val   = df[(df["created_at"] > train_end) & (df["created_at"] <= val_end)].copy()
    df_test  = df[df["created_at"] > val_end].copy()
    
    logger.info(f"Train: {df_train['created_at'].min().date()} → {df_train['created_at'].max().date()} | {len(df_train)} filas")
    logger.info(f"Val  : {df_val['created_at'].min().date()} → {df_val['created_at'].max().date()} | {len(df_val)} filas")
    logger.info(f"Test : {df_test['created_at'].min().date()} → {df_test['created_at'].max().date()} | {len(df_test)} filas")
    
    # Escalado
    if scaler is None:
        scaler = StandardScaler()
        scaler.fit(df_train[FEATURES + [TARGET]])
        logger.info("Nuevo scaler creado y ajustado")
    else:
        logger.info("Usando scaler existente")
    
    df_train_s = df_train.copy()
    df_val_s = df_val.copy()
    df_test_s = df_test.copy()
    
    df_train_s[FEATURES + [TARGET]] = scaler.transform(df_train_s[FEATURES + [TARGET]])
    df_val_s[FEATURES + [TARGET]]   = scaler.transform(df_val_s[FEATURES + [TARGET]])
    df_test_s[FEATURES + [TARGET]]  = scaler.transform(df_test_s[FEATURES + [TARGET]])
    
    return df_train_s, df_val_s, df_test_s, scaler


def crear_backup(version):
    """Crea backup del modelo y scaler actuales."""
    BACKUP_DIR.mkdir(exist_ok=True)
    
    backup_model = BACKUP_DIR / f"model_{version}.keras"
    backup_scaler = BACKUP_DIR / f"scaler_{version}.pkl"
    
    if Path(MODEL_FILE).exists():
        import shutil
        shutil.copy(MODEL_FILE, backup_model)
        logger.info(f"Backup del modelo guardado: {backup_model}")
    
    if Path(SCALER_FILE).exists():
        import shutil
        shutil.copy(SCALER_FILE, backup_scaler)
        logger.info(f"Backup del scaler guardado: {backup_scaler}")
    
    return backup_model, backup_scaler


def restaurar_backup(backup_model, backup_scaler):
    """Restaura modelo y scaler desde backup."""
    import shutil
    if backup_model.exists():
        shutil.copy(backup_model, MODEL_FILE)
    if backup_scaler.exists():
        shutil.copy(backup_scaler, SCALER_FILE)
    logger.info(" Modelo y scaler restaurados desde backup")


# FUNCIÓN PRINCIPAL DE REENTRENAMIENTO

def reentrenar_modelo(
    df_nuevo,
    epochs=10,
    batch_size=128,
    umbral_degradacion=0.1,
    usar_early_stopping=True,
    patience=5
):
    """
    Reentrena el modelo LSTM con nuevos datos.
    
    Parámetros:
    -----------
    df_nuevo : DataFrame
        Nuevos datos SIN PREPARAR (se procesarán automáticamente)
    epochs : int
        Número de épocas para reentrenamiento
    batch_size : int
        Tamaño del batch
    umbral_degradacion : float
        % permitido de degradación (0.1 = 10%)
    usar_early_stopping : bool
        Si usar early stopping
    patience : int
        Paciencia para early stopping
    
    Returns:
    --------
    dict : Resultados del reentrenamiento con métricas
    """
    
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info(f"\n{'='*60}")
    logger.info(f"INICIO DE REENTRENAMIENTO - Versión {version}")
    logger.info(f"{'='*60}\n")
    
    try:
        # 1. PREPARAR DATOS NUEVOS
        logger.info("Paso 1: Preparando datos nuevos...")
        df_nuevo_prep = preparar_csv_crudo(df_nuevo)
        logger.info(f" {len(df_nuevo_prep)} filas preparadas")
        
        # 2. CARGAR Y COMBINAR CON DATASET EXISTENTE
        logger.info("\nPaso 2: Cargando dataset existente...")
        if not Path(DATASET_FILE).exists():
            raise FileNotFoundError(f"No se encuentra {DATASET_FILE}")

        df_old = pd.read_csv(DATASET_FILE, parse_dates=["created_at"])
        logger.info(f"   Dataset antiguo: {len(df_old)} filas")
        
        # Combinar datasets
        df_total = pd.concat([df_old, df_nuevo_prep], ignore_index=True)
        df_total = df_total.drop_duplicates(
            subset=["product_id", "created_at"], 
            keep="last"
        ).sort_values(["product_id", "created_at"])
        
        logger.info(f"   Dataset combinado: {len(df_total)} filas")
        logger.info(f"   Nuevas filas agregadas: {len(df_total) - len(df_old)}")
        
        # 3. CARGAR SCALER Y MODELO EXISTENTES
        logger.info("\nPaso 3: Cargando modelo y scaler actuales...")
        
        if not Path(SCALER_FILE).exists():
            raise FileNotFoundError(f"No se encuentra {SCALER_FILE}")
        if not Path(MODEL_FILE).exists():
            raise FileNotFoundError(f"No se encuentra {MODEL_FILE}")
        
        scaler = joblib.load(SCALER_FILE)
        old_model = tf.keras.models.load_model(MODEL_FILE)
        logger.info(" Modelo y scaler cargados correctamente")
        
        # 4. CREAR BACKUP
        logger.info("\nPaso 4: Creando backup de seguridad...")
        backup_model, backup_scaler = crear_backup(version)
        
        # 5. PREPARAR DATOS PARA ENTRENAMIENTO
        logger.info("\nPaso 5: Dividiendo y escalando datos...")
        df_train_s, df_val_s, df_test_s, scaler = preparar_datos(df_total, scaler)
        
        # 6. CREAR SECUENCIAS
        logger.info("\nPaso 6: Creando secuencias temporales...")
        X_train, y_train = make_sequences(df_train_s, FEATURES, TARGET, N_STEPS)
        X_val, y_val     = make_sequences(df_val_s, FEATURES, TARGET, N_STEPS)
        X_test, y_test   = make_sequences(df_test_s, FEATURES, TARGET, N_STEPS)
        
        logger.info(f"   X_train: {X_train.shape} | X_val: {X_val.shape} | X_test: {X_test.shape}")
        
        # 7. EVALUAR MODELO ACTUAL (ANTES)
        logger.info("\nPaso 7: Evaluando modelo actual...")
        y_old_pred = old_model.predict(X_test, verbose=0).reshape(-1)
        old_rmse = np.sqrt(mean_squared_error(y_test, y_old_pred))
        old_mae  = mean_absolute_error(y_test, y_old_pred)
        
        logger.info(f"   RMSE antes: {old_rmse:.4f}")
        logger.info(f"   MAE antes:  {old_mae:.4f}")
        
        # 8. REENTRENAR CON MLFLOW
        logger.info(f"\nPaso 8: Reentrenando modelo ({epochs} épocas)...")
        
        with mlflow.start_run(run_name=f"retraining_{version}"):
            mlflow.log_params({
                "version": version,
                "epochs": epochs,
                "batch_size": batch_size,
                "n_steps": N_STEPS,
                "nuevas_filas": len(df_total) - len(df_old),
                "total_filas": len(df_total)
            })
            
            # Callbacks
            callbacks = []
            if usar_early_stopping:
                early_stop = tf.keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=patience,
                    restore_best_weights=True,
                    verbose=1
                )
                callbacks.append(early_stop)
                logger.info(f"   Early stopping activado (patience={patience})")
            
            reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=3,
                verbose=1
            )
            callbacks.append(reduce_lr)
            
            # Entrenar
            history = old_model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                batch_size=batch_size,
                callbacks=callbacks,
                verbose=1
            )
            
            # 9. EVALUAR MODELO REENTRENADO (DESPUÉS)
            logger.info("\nPaso 9: Evaluando modelo reentrenado...")
            y_new_pred = old_model.predict(X_test, verbose=0).reshape(-1)
            new_rmse = np.sqrt(mean_squared_error(y_test, y_new_pred))
            new_mae  = mean_absolute_error(y_test, y_new_pred)
            
            logger.info(f"  RMSE después: {new_rmse:.4f}")
            logger.info(f"  rMAE después:  {new_mae:.4f}")
            
            # Calcular mejora
            mejora_rmse = ((old_rmse - new_rmse) / old_rmse) * 100
            mejora_mae = ((old_mae - new_mae) / old_mae) * 100
            
            logger.info(f"    Mejora RMSE: {mejora_rmse:+.2f}%")
            logger.info(f"    Mejora MAE:  {mejora_mae:+.2f}%")
            
            # Log métricas
            mlflow.log_metrics({
                "rmse_antes": old_rmse,
                "rmse_despues": new_rmse,
                "mae_antes": old_mae,
                "mae_despues": new_mae,
                "mejora_rmse_pct": mejora_rmse,
                "mejora_mae_pct": mejora_mae
            })
            
            # 10. VALIDAR MEJORA
            logger.info("\nPaso 10: Validando mejora del modelo...")
            
            degradacion_rmse = ((new_rmse - old_rmse) / old_rmse)
            
            if degradacion_rmse > umbral_degradacion:
                logger.warning(f"   MODELO EMPEORÓ > {umbral_degradacion*100}%")
                logger.warning(f"   Degradación RMSE: {degradacion_rmse*100:.2f}%")
                logger.warning("   Restaurando modelo anterior...")
                
                restaurar_backup(backup_model, backup_scaler)
                
                resultado = {
                    "exito": False,
                    "version": version,
                    "old_rmse": old_rmse,
                    "new_rmse": new_rmse,
                    "old_mae": old_mae,
                    "new_mae": new_mae,
                    "mejora_rmse_pct": mejora_rmse,
                    "mejora_mae_pct": mejora_mae,
                    "mensaje": "Modelo rechazado por degradación. Backup restaurado."
                }
                
                mlflow.log_param("modelo_aceptado", False)
                logger.info("\nREENTRENAMIENTO RECHAZADO\n")
                
                return resultado
            
            # 11. GUARDAR MODELO MEJORADO
            logger.info("\nPaso 11: Guardando modelo mejorado...")
            
            old_model.save(MODEL_FILE)
            joblib.dump(scaler, SCALER_FILE)
            
            # Guardar versión con timestamp
            old_model.save(f"model_v{version}.keras")
            
            # Actualizar dataset
            df_total.to_csv(DATASET_FILE, index=False)
            
            # Log modelo en MLflow
            mlflow.keras.log_model(old_model, "modelo_reentrenado")
            mlflow.log_param("modelo_aceptado", True)
            
            logger.info(f"   Modelo guardado: {MODEL_FILE}")
            logger.info(f"   Versión guardada: model_v{version}.keras")
            logger.info(f"   Dataset actualizado: {DATASET_FILE}")
            
            resultado = {
                "exito": True,
                "version": version,
                "old_rmse": old_rmse,
                "new_rmse": new_rmse,
                "old_mae": old_mae,
                "new_mae": new_mae,
                "mejora_rmse_pct": mejora_rmse,
                "mejora_mae_pct": mejora_mae,
                "epochs_entrenadas": len(history.history['loss']),
                "mensaje": "Modelo reentrenado y guardado exitosamente."
            }
            
            # # Guardar resumen
            # with open(f"retraining_summary_{version}.json", "w") as f:
            #     json.dump(resultado, f, indent=2)
            
            logger.info(f"\n{'='*60}")
            logger.info("REENTRENAMIENTO COMPLETADO EXITOSAMENTE")
            logger.info(f"{'='*60}\n")
            
            return resultado
    
    except Exception as e:
        logger.error(f"\nERROR EN REENTRENAMIENTO: {str(e)}")
        logger.error("Intentando restaurar backup...")
        
        try:
            restaurar_backup(backup_model, backup_scaler)
            logger.info("Backup restaurado correctamente")
        except:
            logger.error("No se pudo restaurar el backup")
        
        raise


# EJEMPLO DE USO

if __name__ == "__main__":
    
    # Ejemplo: Cargar nuevos datos mensuales
    print("\n" + "="*60)
    print("SCRIPT DE REENTRENAMIENTO AUTOMÁTICO")
    print("="*60 + "\n")
    
    # Cargar nuevos datos
    nuevo_csv = "data20oct-2nov.csv"
    
    if not Path(nuevo_csv).exists():
        logger.error(f"No se encuentra el archivo: {nuevo_csv}")
        logger.info("\nTip: Coloca el CSV con nuevos datos en el directorio actual")
        exit(1)
    
    logger.info(f"Cargando datos desde: {nuevo_csv}")
    df_nuevo = pd.read_csv(nuevo_csv)
    
    logger.info(f"   {len(df_nuevo)} filas cargadas")
    logger.info(f"   Columnas: {list(df_nuevo.columns)}")
    
    # Reentrenar
    resultados = reentrenar_modelo(
        df_nuevo=df_nuevo,
        epochs=5,
        batch_size=128,
        umbral_degradacion=0.1,  # Permitir hasta 10% de degradación
        usar_early_stopping=True,
        patience=5
    )
    
    # Mostrar resumen
    print("\n" + "="*60)
    print("RESUMEN DE REENTRENAMIENTO")
    print("="*60)
    print(f"Éxito: {'SÍ' if resultados['exito'] else 'NO'}")
    print(f"Versión: {resultados['version']}")
    print(f"RMSE antes: {resultados['old_rmse']:.4f}")
    print(f"RMSE después: {resultados['new_rmse']:.4f}")
    print(f"Mejora: {resultados['mejora_rmse_pct']:+.2f}%")
    print(f"Mensaje: {resultados['mensaje']}")
    print("="*60 + "\n")