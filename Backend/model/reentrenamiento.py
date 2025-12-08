"""
Script de Reentrenamiento Automático del Modelo LSTM (MEJORADO)
================================================================
Actualiza el modelo con nuevos datos manteniendo consistencia temporal.
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
import os
import shutil

# Obtener el directorio base (BackendBD)
BASE_DIR = Path(__file__).resolve().parent.parent
FILES_DIR = BASE_DIR / "files"
MODEL_VERSIONS_DIR = FILES_DIR / "model_versions"

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

# Rutas de archivos (relativas a BackendBD)
# DATASET_FILE = FILES_DIR / "dataset_preparado.csv"
MODEL_FILE = FILES_DIR / "modelo.h5"
SCALER_FILE = FILES_DIR / "scaler.pkl"
BACKUP_DIR = MODEL_VERSIONS_DIR

# Logging
log_file = BASE_DIR / "retraining.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def validar_columnas_requeridas(df, requeridas):
    """Valida que el DataFrame tenga todas las columnas necesarias."""
    faltantes = set(requeridas) - set(df.columns)
    if faltantes:
        raise ValueError(f"Columnas faltantes en datos nuevos: {faltantes}")
    logger.info(f"✓ Todas las columnas requeridas presentes")


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


def preparar_datos_incremental(df_old, df_new, scaler, split_ratio=(0.7, 0.15, 0.15)):
    """
    Prepara datos RESPETANDO el orden temporal entre datasets antiguo y nuevo.
    
    Estrategia:
    - Train: Primeros 70% del dataset ANTIGUO
    - Val: Siguientes 15% del dataset ANTIGUO
    - Test: Últimos 15% del dataset ANTIGUO + TODO el dataset NUEVO
    
    Esto evita data leakage temporal.
    """
    df_old = df_old.sort_values(["product_id", "created_at"]).copy()
    df_new = df_new.sort_values(["product_id", "created_at"]).copy()
    
    # Split del dataset antiguo
    n_old = len(df_old)
    train_size = int(n_old * split_ratio[0])
    val_size = int(n_old * split_ratio[1])
    
    df_train = df_old.iloc[:train_size].copy()
    df_val = df_old.iloc[train_size:train_size + val_size].copy()
    df_test_old = df_old.iloc[train_size + val_size:].copy()
    
    # Test = últimos datos antiguos + todos los nuevos
    df_test = pd.concat([df_test_old, df_new], ignore_index=True)
    
    logger.info(f" División temporal:")
    logger.info(f"   Train: {df_train['created_at'].min().date()} → {df_train['created_at'].max().date()} | {len(df_train)} filas")
    logger.info(f"   Val:   {df_val['created_at'].min().date()} → {df_val['created_at'].max().date()} | {len(df_val)} filas")
    logger.info(f"   Test:  {df_test['created_at'].min().date()} → {df_test['created_at'].max().date()} | {len(df_test)} filas")
    logger.info(f"   (Test incluye {len(df_new)} filas nuevas)")
    
    # Escalado usando el scaler existente (NO refit)
    df_train_s = df_train.copy()
    df_val_s = df_val.copy()
    df_test_s = df_test.copy()
    
    df_train_s[FEATURES + [TARGET]] = scaler.transform(df_train_s[FEATURES + [TARGET]])
    df_val_s[FEATURES + [TARGET]] = scaler.transform(df_val_s[FEATURES + [TARGET]])
    df_test_s[FEATURES + [TARGET]] = scaler.transform(df_test_s[FEATURES + [TARGET]])
    
    return df_train_s, df_val_s, df_test_s


def crear_backup(version):
    """Crea backup del modelo y scaler actuales en files/model_versions/"""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    backup_model = BACKUP_DIR / f"model_{version}.h5"
    backup_scaler = BACKUP_DIR / f"scaler_{version}.pkl"

    
    if MODEL_FILE.exists():
        shutil.copy(MODEL_FILE, backup_model)
        logger.info(f"✓ Backup del modelo: {backup_model.name}")
    
    if SCALER_FILE.exists():
        shutil.copy(SCALER_FILE, backup_scaler)
        logger.info(f"✓ Backup del scaler: {backup_scaler.name}")
    
    
    return backup_model, backup_scaler


def restaurar_backup(backup_model, backup_scaler):
    """Restaura modelo, scaler y dataset desde backup."""
    if backup_model and backup_model.exists():
        shutil.copy(backup_model, MODEL_FILE)
    if backup_scaler and backup_scaler.exists():
        shutil.copy(backup_scaler, SCALER_FILE)
    logger.info("✓ Modelo y scaler restaurados desde backup")


def guardar_metadata_version(version, resultados, filepath):
    """Guarda metadatos de la versión del modelo."""
    metadata = {
        "version": version,
        "timestamp": datetime.now().isoformat(),
        "metricas": {
            "rmse_anterior": resultados.get("previous_rmse"),
            "rmse_nuevo": resultados.get("new_rmse"),
            "mae_anterior": resultados.get("previous_mae"),
            "mae_nuevo": resultados.get("new_mae"),
            "mejora_rmse_pct": resultados.get("mejora_rmse_pct"),
            "mejora_mae_pct": resultados.get("mejora_mae_pct")
        },
        "exito": resultados.get("exito"),
        "mensaje": resultados.get("mensaje")
    }
    
    with open(filepath, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.info(f"✓ Metadata guardada: {filepath.name}")


# ============================================================================
# FUNCIÓN PRINCIPAL DE REENTRENAMIENTO
# ============================================================================

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
    logger.info("=" * 70)
    logger.info(f"🚀 INICIO DE REENTRENAMIENTO - Versión {version}")
    logger.info("=" * 70)
    
    backup_model = backup_scaler = backup_dataset = None
    
    try:
                
        # 1. CARGAR DATASET PREPARADO DESDE BD
        logger.info("\n Paso 1: Cargando dataset preparado desde PostgreSQL...")

        from model.db_loader import load_inventory_dataset

        df_old = load_inventory_dataset()

        if df_old is None or len(df_old) == 0:
            raise ValueError("No se pudo cargar dataset desde la base de datos.")

        logger.info(f"   ✓ Dataset antiguo cargado desde BD: {len(df_old)} filas")
        logger.info(f"   ✓ Rango temporal: {df_old['created_at'].min().date()} → {df_old['created_at'].max().date()}")


    
        # 3. CARGAR SCALER Y MODELO
        logger.info("\n Paso 3: Cargando modelo y scaler actuales...")
        if not SCALER_FILE.exists():
            raise FileNotFoundError(f"No se encuentra {SCALER_FILE}")
        if not MODEL_FILE.exists():
            raise FileNotFoundError(f"No se encuentra {MODEL_FILE}")
        
        scaler = joblib.load(SCALER_FILE)
        
        # Cargar modelo con manejo de incompatibilidades de versión
        try:
            # Intento 1: Cargar normalmente
            old_model = tf.keras.models.load_model(str(MODEL_FILE))
            logger.info(f"   ✓ Modelo cargado correctamente")
        except (ValueError, ImportError) as e:
            logger.warning(f"    Error al cargar modelo compilado: {e}")
            logger.info("    Intentando cargar solo arquitectura y pesos...")
            
            # Intento 2: Cargar sin compilar y recompilar manualmente
            old_model = tf.keras.models.load_model(str(MODEL_FILE), compile=False)
            
            # Recompilar con configuración estándar
            old_model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                loss='mse',
                metrics=[tf.keras.metrics.RootMeanSquaredError(name="rmse")]
            )
            logger.info(f"   ✓ Modelo cargado y recompilado correctamente")
        
        # 4. CREAR BACKUP
        logger.info("\n Paso 4: Creando backup de seguridad...")
        backup_model, backup_scaler, backup_dataset = crear_backup(version)
        
        # 5. PREPARAR DATOS PARA ENTRENAMIENTO (RESPETANDO TEMPORALIDAD)
        logger.info("\n Paso 5: Dividiendo datos (estrategia incremental)...")
        df_train_s, df_val_s, df_test_s = preparar_datos_incremental(
            df_old, df_nuevo_prep, scaler
        )
        
        # Limpiar NaN en columnas usadas por el modelo
        cols_modelo = FEATURES + [TARGET]

        def _clean_nans(df_in, nombre):
            antes = len(df_in)
            df_out = df_in.dropna(subset=[c for c in cols_modelo if c in df_in.columns])
            despues = len(df_out)
            if antes != despues:
                logger.warning(
                    f"   ⚠ Se eliminaron {antes - despues} filas con NaN en {nombre} "
                    f"(columnas modelo: {cols_modelo})"
                )
            return df_out

        df_old = _clean_nans(df_old, "dataset antiguo")
        df_nuevo_prep = _clean_nans(df_nuevo_prep, "datos nuevos")

        # 6. CREAR SECUENCIAS
        logger.info("\n Paso 6: Creando secuencias temporales...")
        X_train, y_train = make_sequences(df_train_s, FEATURES, TARGET, N_STEPS)
        X_val, y_val = make_sequences(df_val_s, FEATURES, TARGET, N_STEPS)
        X_test, y_test = make_sequences(df_test_s, FEATURES, TARGET, N_STEPS)
        
        logger.info(f"   ✓ X_train: {X_train.shape}")
        logger.info(f"   ✓ X_val:   {X_val.shape}")
        logger.info(f"   ✓ X_test:  {X_test.shape}")
        
        # 7. EVALUAR MODELO ACTUAL (ANTES)
        logger.info("\nPaso 7: Evaluando modelo actual...")

        # Predicción del modelo actual
        y_old_pred = old_model.predict(X_test, verbose=0).reshape(-1)

        # Diagnóstico de NaN
        nan_y_test = np.isnan(y_test).sum()
        nan_y_pred = np.isnan(y_old_pred).sum()
        logger.info(f"   NaN en y_test: {nan_y_test} | NaN en y_old_pred: {nan_y_pred}")

        # Crear máscara para quedarnos solo con pares válidos (sin NaN)
        mask_valid = (~np.isnan(y_test)) & (~np.isnan(y_old_pred))
        y_test_valid = y_test[mask_valid]
        y_pred_valid = y_old_pred[mask_valid]

        if len(y_test_valid) == 0:
            raise ValueError("No hay muestras válidas (todas contienen NaN) para evaluar el modelo.")

        if len(y_test_valid) != len(y_pred_valid):
            raise ValueError("Dimensiones inconsistentes tras filtrar NaN en y_test / y_pred.")

        old_rmse = np.sqrt(mean_squared_error(y_test_valid, y_pred_valid))
        old_mae  = mean_absolute_error(y_test_valid, y_pred_valid)

        logger.info(f"    RMSE antes: {old_rmse:.4f}")
        logger.info(f"    MAE antes:  {old_mae:.4f}")
        
        # 8. REENTRENAR CON MLFLOW
        logger.info(f"\n Paso 8: Reentrenando modelo ({epochs} épocas max)...")
        
        with mlflow.start_run(run_name=f"retraining_{version}"):
            mlflow.log_params({
                "version": version,
                "epochs": epochs,
                "batch_size": batch_size,
                "n_steps": N_STEPS,
                "nuevas_filas": len(df_nuevo_prep),
                "total_filas_antiguas": len(df_old)
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
                logger.info(f"   ✓ Early stopping activado (patience={patience})")
            
            reduce_lr = tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.5,
                patience=3,
                verbose=1,
                min_lr=1e-7
            )
            callbacks.append(reduce_lr)
            
            # Entrenar (fine-tuning)
            history = old_model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                batch_size=batch_size,
                callbacks=callbacks,
                verbose=1
            )
            
            epochs_trained = len(history.history['loss'])
            logger.info(f"   ✓ Entrenamiento completado en {epochs_trained} épocas")
            
            # 9. EVALUAR MODELO REENTRENADO
            logger.info("\n Paso 9: Evaluando modelo reentrenado...")
            y_new_pred = old_model.predict(X_test, verbose=0).reshape(-1)

            nan_y_test_new = np.isnan(y_test).sum()
            nan_y_pred_new = np.isnan(y_new_pred).sum()
            logger.info(f"   NaN en y_test (reentrenado): {nan_y_test_new} | NaN en y_new_pred: {nan_y_pred_new}")

            mask_valid_new = (~np.isnan(y_test)) & (~np.isnan(y_new_pred))
            y_test_valid_new = y_test[mask_valid_new]
            y_pred_valid_new = y_new_pred[mask_valid_new]

            if len(y_test_valid_new) == 0:
                raise ValueError("No hay muestras válidas (todas contienen NaN) para evaluar el modelo reentrenado.")

            if len(y_test_valid_new) != len(y_pred_valid_new):
                raise ValueError("Dimensiones inconsistentes tras filtrar NaN en y_test / y_new_pred.")

            new_rmse = np.sqrt(mean_squared_error(y_test_valid_new, y_pred_valid_new))
            new_mae  = mean_absolute_error(y_test_valid_new, y_pred_valid_new)

            logger.info(f"    RMSE después: {new_rmse:.4f}")
            logger.info(f"    MAE después:  {new_mae:.4f}")
            
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
                "mejora_mae_pct": mejora_mae,
                "epochs_trained": epochs_trained
            })
            
            
            # 10. VALIDAR MEJORA DEL MODELO
            logger.info("\n Paso 11: Validando mejora del modelo...")
            
            degradacion_rmse = ((new_rmse - old_rmse) / old_rmse)
            
            if degradacion_rmse > umbral_degradacion:
                logger.warning(f"     MODELO EMPEORÓ > {umbral_degradacion*100}%")
                logger.warning(f"     Degradación RMSE: {degradacion_rmse*100:.2f}%")
                logger.warning("     Restaurando modelo anterior (solo modelo y scaler)...")
                
                # NO revertimos el CSV, solo modelo y scaler
                restaurar_backup(backup_model, backup_scaler, None)
                
                resultado = {
                    "exito": False,
                    "version": version,
                    "previous_rmse": float(old_rmse),
                    "new_rmse": float(new_rmse),
                    "previous_mae": float(old_mae),
                    "new_mae": float(new_mae),
                    "mejora_rmse_pct": float(mejora_rmse),
                    "mejora_mae_pct": float(mejora_mae),
                    "epochs_entrenadas": epochs_trained,
                    "mensaje": "Modelo rechazado por degradación. Se mantiene el modelo anterior, pero el dataset sí se actualizó."
                }
                
                mlflow.log_param("modelo_aceptado", False)
                logger.info("\n" + "=" * 70)
                logger.info(" REENTRENAMIENTO RECHAZADO")
                logger.info("=" * 70)
                
                return resultado
            
            # 12. GUARDAR MODELO MEJORADO
            logger.info("\n Paso 12: Guardando modelo mejorado...")
            
            # Guardar versión con timestamp en model_versions
            version_model = BACKUP_DIR / f"model_{version}.h5"
            version_scaler = BACKUP_DIR / f"scaler_{version}.pkl"
            metadata_file = BACKUP_DIR / f"metadata_{version}.json"
            
            old_model.save(str(version_model))
            joblib.dump(scaler, version_scaler)
            
            # Reemplazar modelo actual en producción
            old_model.save(str(MODEL_FILE))
            joblib.dump(scaler, SCALER_FILE)
            
            # Guardar metadata
            resultado = {
                "exito": True,
                "version": version,
                "previous_rmse": float(old_rmse),
                "new_rmse": float(new_rmse),
                "previous_mae": float(old_mae),
                "new_mae": float(new_mae),
                "mejora_rmse_pct": float(mejora_rmse),
                "mejora_mae_pct": float(mejora_mae),
                "epochs_entrenadas": epochs_trained,
                "mensaje": "Modelo reentrenado y guardado exitosamente."
            }
            
            guardar_metadata_version(version, resultado, metadata_file)
            
            # Log modelo en MLflow
            mlflow.keras.log_model(old_model, "modelo_reentrenado")
            mlflow.log_param("modelo_aceptado", True)
            
            logger.info(f"   ✓ Versión guardada: {version_model.name}")
            logger.info(f"   ✓ Scaler versión: {version_scaler.name}")
            logger.info(f"   ✓ Modelo actualizado: {MODEL_FILE.name}")
            logger.info(f"   ✓ Metadata: {metadata_file.name}")
            
            logger.info("\n" + "=" * 70)
            logger.info(" REENTRENAMIENTO COMPLETADO EXITOSAMENTE")
            logger.info("=" * 70)
            
            return resultado
    
    except Exception as e:
        logger.error(f"\n ERROR EN REENTRENAMIENTO: {str(e)}")
        logger.error(" Intentando restaurar backup...")
        
        try:
            if backup_model and backup_scaler and backup_dataset:
                restaurar_backup(backup_model, backup_scaler, backup_dataset)
                logger.info("✓ Backup restaurado correctamente")
        except Exception as restore_error:
            logger.error(f" No se pudo restaurar el backup: {restore_error}")
        
        raise


# ============================================================================
# EJEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    
    print("\n" + "=" * 70)
    print("🚀 SCRIPT DE REENTRENAMIENTO AUTOMÁTICO")
    print("=" * 70 + "\n")
    
    # Cargar nuevos datos
    nuevo_csv = FILES_DIR / "data20oct-2nov.csv"
    
    if not nuevo_csv.exists():
        logger.error(f" No se encuentra el archivo: {nuevo_csv}")
        logger.info("\n Tip: Coloca el CSV con nuevos datos en BackendBD/files/")
        exit(1)
    
    logger.info(f" Cargando datos desde: {nuevo_csv.name}")
    df_nuevo = pd.read_csv(nuevo_csv)
    logger.info(f"   ✓ {len(df_nuevo)} filas cargadas")
    logger.info(f"   ✓ Columnas disponibles: {len(df_nuevo.columns)}")
    
    # Reentrenar
    resultados = reentrenar_modelo(
        df_nuevo=df_nuevo,
        epochs=15,
        batch_size=128,
        umbral_degradacion=0.1,  # Permitir hasta 10% de degradación
        usar_early_stopping=True,
        patience=5
    )
    
    # Mostrar resumen
    print("\n" + "=" * 70)
    print(" RESUMEN DE REENTRENAMIENTO")
    print("=" * 70)
    print(f"Éxito:          {' SÍ' if resultados['exito'] else ' NO'}")
    print(f"Versión:        {resultados['version']}")
    print(f"RMSE antes:     {resultados['previous_rmse']:.4f}")
    print(f"RMSE después:   {resultados['new_rmse']:.4f}")
    print(f"Mejora RMSE:    {resultados['mejora_rmse_pct']:+.2f}%")
    print(f"MAE antes:      {resultados['previous_mae']:.4f}")
    print(f"MAE después:    {resultados['new_mae']:.4f}")
    print(f"Mejora MAE:     {resultados['mejora_mae_pct']:+.2f}%")
    print(f"Épocas:         {resultados['epochs_entrenadas']}")
    print(f"Mensaje:        {resultados['mensaje']}")
    print("=" * 70 + "\n")