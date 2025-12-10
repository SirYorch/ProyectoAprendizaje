"""
Script de Reentrenamiento con Aprobación Manual - VERSIÓN SIMPLIFICADA
========================================================================
Reentrena el modelo y retorna métricas MAE y RMSE para aprobación.

USO:
    reporte = reentrenar_y_evaluar(epochs=10)
    if reporte['recomendacion']['decision'] == 'APROBAR':
        aplicar_modelo_candidato(reporte['version'])
"""

import pandas as pd
import numpy as np
import tensorflow as tf
from datetime import datetime
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib
from pathlib import Path
import logging
import json
import shutil

# Configuración
BASE_DIR = Path(__file__).resolve().parent.parent
FILES_DIR = BASE_DIR / "files"
CANDIDATES_DIR = FILES_DIR / "candidates"
CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)

# Constantes
SEED = 42
tf.random.set_seed(SEED)
np.random.seed(SEED)

FEATURES = [
    "quantity_on_hand", "quantity_reserved", "reorder_point",
    "optimal_stock_level", "average_daily_usage", "stock_status",
    "dia_semana", "fin_de_semana", "category"
]
TARGET = "quantity_available"
N_STEPS = 7

MODEL_FILE = FILES_DIR / "modelo.h5"
SCALER_FILE = FILES_DIR / "scaler.pkl"

# Logging simple
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.FileHandler(BASE_DIR / "retraining.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


def make_sequences(df, feat_cols, target_col, n_steps=N_STEPS):
    """Crea secuencias temporales LSTM."""
    X, y = [], []
    for pid, g in df.groupby("product_id"):
        g = g.sort_values("created_at")
        vals = g[feat_cols + [target_col]].values
        for i in range(n_steps, len(g)):
            X.append(vals[i-n_steps:i, :-1])
            y.append(vals[i, -1])
    return np.array(X), np.array(y)


def cargar_modelo_robusto(ruta):
    """Carga modelo con múltiples intentos de compatibilidad."""
    rutas = [ruta, FILES_DIR / "modelo.h5"]
    
    for path in rutas:
        if not path.exists():
            logger.info(f"   ⚠ Ruta no existe: {path.name}")
            continue
        
        logger.info(f"   🔄 Intentando cargar desde: {path.name}")
        
        # Intento 1: Carga normal
        try:
            logger.info(f"      → Método 1: Carga estándar...")
            modelo = tf.keras.models.load_model(str(path))
            logger.info(f"      ✓ Cargado con método 1")
            return modelo
        except Exception as e1:
            logger.warning(f"      ✗ Método 1 falló: {str(e1)[:100]}")
        
        # Intento 2: Sin compilar
        try:
            logger.info(f"      → Método 2: Sin compilar...")
            modelo = tf.keras.models.load_model(str(path), compile=False)
            modelo.compile(optimizer='adam', loss='mse', metrics=['mae'])
            logger.info(f"      ✓ Cargado con método 2")
            return modelo
        except Exception as e2:
            logger.warning(f"      ✗ Método 2 falló: {str(e2)[:100]}")
        
        # Intento 3: Con custom_objects (batch_shape fix)
        try:
            logger.info(f"      → Método 3: Custom objects (batch_shape fix)...")
            
            class CompatibleInputLayer(tf.keras.layers.InputLayer):
                def __init__(self, *args, **kwargs):
                    if 'batch_shape' in kwargs:
                        batch_shape = kwargs.pop('batch_shape')
                        if batch_shape:
                            kwargs['input_shape'] = batch_shape[1:]
                    super().__init__(*args, **kwargs)
            
            custom_objects = {'InputLayer': CompatibleInputLayer}
            
            # Agregar DTypePolicy si existe
            try:
                from keras import DTypePolicy
                custom_objects['DTypePolicy'] = DTypePolicy
            except:
                class DummyDTypePolicy:
                    def __init__(self, *args, **kwargs):
                        pass
                custom_objects['DTypePolicy'] = DummyDTypePolicy
            
            with tf.keras.utils.custom_object_scope(custom_objects):
                modelo = tf.keras.models.load_model(str(path), compile=False)
            
            modelo.compile(optimizer='adam', loss='mse', metrics=['mae'])
            logger.info(f"      ✓ Cargado con método 3 (custom_objects)")
            return modelo
        except Exception as e3:
            logger.warning(f"      ✗ Método 3 falló: {str(e3)[:100]}")
    
    raise Exception(f"No se pudo cargar el modelo. Rutas intentadas: {[str(r) for r in rutas]}")


def evaluar_modelo(modelo, X_test, y_test):
    """Evalúa modelo - Solo MAE y RMSE."""
    y_pred = modelo.predict(X_test, verbose=0).flatten()
    
    # Filtrar NaN
    mask = (~np.isnan(y_test)) & (~np.isnan(y_pred))
    y_test_clean = y_test[mask]
    y_pred_clean = y_pred[mask]
    
    return {
        'rmse': float(np.sqrt(mean_squared_error(y_test_clean, y_pred_clean))),
        'mae': float(mean_absolute_error(y_test_clean, y_pred_clean))
    }


def reentrenar_y_evaluar(
    fecha_corte_val=None,  # Parámetro ignorado, por compatibilidad con wrapper
    fecha_corte_test=None,  # Parámetro ignorado, por compatibilidad con wrapper
    epochs=10, 
    batch_size=128,
    usar_early_stopping=True,  # Parámetro ignorado, por compatibilidad
    patience=5  # Parámetro ignorado, por compatibilidad
):
    """
    Reentrena modelo y retorna reporte simplificado.
    
    Returns:
        dict: {version, metricas_anterior, metricas_nuevo, comparacion, recomendacion}
    """
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.info("=" * 80)
    logger.info(f"🔬 REENTRENAMIENTO - Versión {version}")
    logger.info("=" * 80)
    
    try:
        # ====================================================================
        # PASO 1: CARGAR DATOS
        # ====================================================================
        logger.info("\n📥 Paso 1: Cargando datos desde PostgreSQL...")
        from model.db_loader import load_inventory_dataset
        df = load_inventory_dataset()
        if df is None or len(df) == 0:
            raise ValueError("No hay datos en la BD")
        
        df = df.dropna(subset=FEATURES + [TARGET])
        logger.info(f"   ✓ Dataset: {len(df):,} filas")
        logger.info(f"   ✓ Rango: {df['created_at'].min().date()} → {df['created_at'].max().date()}")
        
        # ====================================================================
        # PASO 2: CARGAR MODELO Y SCALER
        # ====================================================================
        logger.info("\n📦 Paso 2: Cargando modelo actual...")
        tf.keras.backend.clear_session()
        modelo_actual = cargar_modelo_robusto(MODEL_FILE)
        scaler = joblib.load(SCALER_FILE)
        logger.info(f"   ✓ Modelo cargado exitosamente")
        logger.info(f"   ✓ Input: {modelo_actual.input_shape}, Output: {modelo_actual.output_shape}")
        
        # ====================================================================
        # PASO 3: PREPARAR DATOS
        # ====================================================================
        logger.info("\n✂️  Paso 3: Preparando datos (split 70/15/15)...")
        df = df.sort_values(["product_id", "created_at"])
        n = len(df)
        train_end = int(n * 0.70)
        val_end = train_end + int(n * 0.15)
        
        df_train = df.iloc[:train_end].copy()
        df_val = df.iloc[train_end:val_end].copy()
        df_test = df.iloc[val_end:].copy()
        
        logger.info(f"   ✓ Train: {len(df_train):,} filas")
        logger.info(f"   ✓ Val:   {len(df_val):,} filas")
        logger.info(f"   ✓ Test:  {len(df_test):,} filas")
        
        # Escalar
        cols = FEATURES + [TARGET]
        for subset in [df_train, df_val, df_test]:
            subset[cols] = scaler.transform(subset[cols])
        
        # Secuencias
        X_train, y_train = make_sequences(df_train, FEATURES, TARGET)
        X_val, y_val = make_sequences(df_val, FEATURES, TARGET)
        X_test, y_test = make_sequences(df_test, FEATURES, TARGET)
        
        logger.info(f"   ✓ Secuencias: Train={X_train.shape[0]}, Val={X_val.shape[0]}, Test={X_test.shape[0]}")
        
        # ====================================================================
        # PASO 4: EVALUAR MODELO ACTUAL
        # ====================================================================
        logger.info("\n📊 Paso 4: Evaluando modelo actual...")
        metricas_anterior = evaluar_modelo(modelo_actual, X_test, y_test)
        logger.info(f"   📉 RMSE: {metricas_anterior['rmse']:.4f}")
        logger.info(f"   📉 MAE:  {metricas_anterior['mae']:.4f}")
        
        # ====================================================================
        # PASO 5: REENTRENAR MODELO
        # ====================================================================
        logger.info(f"\n🎯 Paso 5: Reentrenando modelo (máx {epochs} épocas)...")
        
        modelo_nuevo = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(N_STEPS, len(FEATURES))),
            tf.keras.layers.LSTM(64, return_sequences=True),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dropout(0.3),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(1)
        ])
        
        # Copiar pesos
        try:
            modelo_nuevo.set_weights(modelo_actual.get_weights())
            logger.info("   ✓ Pesos copiados del modelo actual")
        except:
            logger.warning("   ⚠ No se pudieron copiar pesos, entrenando desde cero")
        
        modelo_nuevo.compile(optimizer='adam', loss='mse', metrics=['mae'])
        
        # Entrenar
        history = modelo_nuevo.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[
                tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
                tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3)
            ],
            verbose=0
        )
        
        epochs_real = len(history.history['loss'])
        logger.info(f"   ✓ Entrenamiento completado en {epochs_real} épocas")
        
        # ====================================================================
        # PASO 6: EVALUAR MODELO NUEVO
        # ====================================================================
        logger.info("\n📊 Paso 6: Evaluando modelo candidato...")
        metricas_nuevo = evaluar_modelo(modelo_nuevo, X_test, y_test)
        logger.info(f"   📈 RMSE: {metricas_nuevo['rmse']:.4f}")
        logger.info(f"   📈 MAE:  {metricas_nuevo['mae']:.4f}")
        
        # ====================================================================
        # PASO 7: COMPARAR MÉTRICAS
        # ====================================================================
        logger.info("\n📊 Paso 7: Comparando métricas...")
        rmse_cambio = ((metricas_anterior['rmse'] - metricas_nuevo['rmse']) / metricas_anterior['rmse']) * 100
        mae_cambio = ((metricas_anterior['mae'] - metricas_nuevo['mae']) / metricas_anterior['mae']) * 100
        
        comparacion = {
            'rmse_cambio': float(rmse_cambio),
            'mae_cambio': float(mae_cambio)
        }
        
        logger.info(f"   {'📈' if rmse_cambio > 0 else '📉'} RMSE: {rmse_cambio:+.2f}%")
        logger.info(f"   {'📈' if mae_cambio > 0 else '📉'} MAE:  {mae_cambio:+.2f}%")
        
        # ====================================================================
        # PASO 8: GENERAR RECOMENDACIÓN
        # ====================================================================
        logger.info("\n🤔 Paso 8: Generando recomendación...")
        mejoras = sum([rmse_cambio > 0, mae_cambio > 0])
        
        if mejoras >= 1:  # Al menos 1 métrica mejoró
            decision = "APROBAR"
            confianza = "ALTA" if mejoras == 2 else "MEDIA"
        else:
            decision = "RECHAZAR"
            confianza = "ALTA"
        
        razones = [
            f"{'✓' if rmse_cambio > 0 else '✗'} RMSE: {rmse_cambio:+.2f}%",
            f"{'✓' if mae_cambio > 0 else '✗'} MAE: {mae_cambio:+.2f}%"
        ]
        
        logger.info(f"   🎯 Decisión: {decision} (Confianza: {confianza})")
        for razon in razones:
            logger.info(f"      {razon}")
        
        # ====================================================================
        # PASO 9: GUARDAR CANDIDATO
        # ====================================================================
        logger.info("\n💾 Paso 9: Guardando modelo candidato...")
        candidate_dir = CANDIDATES_DIR / version
        candidate_dir.mkdir(parents=True, exist_ok=True)
        
        modelo_nuevo.save(str(candidate_dir / "modelo_candidato.h5"))
        joblib.dump(scaler, candidate_dir / "scaler.pkl")
        
        with open(candidate_dir / "metadata.json", 'w') as f:
            json.dump({
                'version': version,
                'timestamp': datetime.now().isoformat(),
                'metricas_anterior': metricas_anterior,
                'metricas_nuevo': metricas_nuevo,
                'comparacion': comparacion,
                'recomendacion': {'decision': decision, 'confianza': confianza}
            }, f, indent=2)
        
        logger.info(f"   ✓ Modelo candidato guardado: {version}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ EVALUACIÓN COMPLETADA - ESPERANDO DECISIÓN")
        logger.info("=" * 80)
        
        # 10. Reporte
        return {
            'version': version,
            'metricas_anterior': metricas_anterior,
            'metricas_nuevo': metricas_nuevo,
            'comparacion': comparacion,
            'recomendacion': {
                'decision': decision,
                'confianza': confianza,
                'razones': razones
            },
            'datos': {
                'filas_totales': len(df),
                'productos_unicos': df['product_id'].nunique()
            }
        }
    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise


def aplicar_modelo_candidato(version):
    """Aplica modelo candidato a producción."""
    logger.info(f"✅ Aplicando modelo {version}...")
    
    candidate_dir = CANDIDATES_DIR / version
    if not candidate_dir.exists():
        raise FileNotFoundError(f"Candidato {version} no encontrado")
    
    # Backup
    backup_dir = FILES_DIR / "model_versions" / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    if MODEL_FILE.exists():
        shutil.copy(MODEL_FILE, backup_dir / "modelo_anterior.keras")
    if SCALER_FILE.exists():
        shutil.copy(SCALER_FILE, backup_dir / "scaler_anterior.pkl")
    
    # Aplicar
    shutil.copy(candidate_dir / "modelo_candidato.h5", MODEL_FILE)
    shutil.copy(candidate_dir / "scaler.pkl", SCALER_FILE)
    
    logger.info(f"✓ Modelo aplicado (backup: {backup_dir.name})")
    
    return {'exito': True, 'version': version, 'mensaje': 'Modelo aplicado exitosamente'}


def descartar_modelo_candidato(version):
    """Descarta modelo candidato."""
    candidate_dir = CANDIDATES_DIR / version
    if not candidate_dir.exists():
        raise FileNotFoundError(f"Candidato {version} no encontrado")
    
    discarded_dir = CANDIDATES_DIR / "discarded"
    discarded_dir.mkdir(exist_ok=True)
    shutil.move(str(candidate_dir), str(discarded_dir / version))
    
    logger.info(f"🗑️ Modelo {version} descartado")
    return {'exito': True, 'version': version, 'mensaje': 'Modelo descartado'}


def listar_modelos_candidatos():
    """Lista modelos candidatos pendientes."""
    candidatos = []
    for d in CANDIDATES_DIR.iterdir():
        if d.is_dir() and d.name not in ['discarded']:
            meta_path = d / "metadata.json"
            if meta_path.exists():
                with open(meta_path) as f:
                    meta = json.load(f)
                candidatos.append({
                    'version': d.name,
                    'timestamp': meta.get('timestamp'),
                    'recomendacion': meta.get('recomendacion', {}).get('decision'),
                    'rmse_cambio': meta.get('comparacion', {}).get('rmse_cambio'),
                    'mae_cambio': meta.get('comparacion', {}).get('mae_cambio')
                })
    return sorted(candidatos, key=lambda x: x['version'], reverse=True)


if __name__ == "__main__":
    print("\n🔬 Reentrenamiento con Aprobación Manual\n")
    
    reporte = reentrenar_y_evaluar(epochs=10)
    
    print(f"\n📊 REPORTE - Versión {reporte['version']}")
    print("=" * 60)
    print(f"Modelo Actual:    RMSE={reporte['metricas_anterior']['rmse']:.4f}, MAE={reporte['metricas_anterior']['mae']:.4f}")
    print(f"Modelo Candidato: RMSE={reporte['metricas_nuevo']['rmse']:.4f}, MAE={reporte['metricas_nuevo']['mae']:.4f}")
    print(f"\nCambios: RMSE {reporte['comparacion']['rmse_cambio']:+.2f}%, MAE {reporte['comparacion']['mae_cambio']:+.2f}%")
    print(f"\nRecomendación: {reporte['recomendacion']['decision']} ({reporte['recomendacion']['confianza']})")
    print("=" * 60)
    
    if reporte['recomendacion']['decision'] == 'APROBAR':
        resp = input("\n¿Aplicar modelo? (s/n): ")
        if resp.lower() == 's':
            aplicar_modelo_candidato(reporte['version'])
            print("✅ Modelo aplicado")