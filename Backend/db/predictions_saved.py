import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column, String, Float, DateTime, Integer,
    create_engine
)
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import insert




DATABASE_URL = "postgresql://usuario1:password1@localhost:5432/aprendizaje"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


def get_session_local():
    """Devuelve una sesión lista para usarse."""
    return SessionLocal

# ==================== MODELO ORM ====================

class StockPrediction(Base):
    """
    Modelo ORM para cachear predicciones de stock.
    
    Attributes:
        product_id: ID del producto
        prediction_date: Fecha de la predicción
        predicted_stock: Stock predicho para esa fecha
        predicted_demand: Demanda predicha para esa fecha
        quantity_on_hand: Cantidad disponible
        quantity_reserved: Cantidad reservada
        reorder_point: Punto de reorden
        optimal_stock_level: Nivel óptimo de stock
        average_daily_usage: Uso diario promedio
        stock_status: Estado del stock
        dia_semana: Día de la semana (0-6)
        fin_de_semana: Si es fin de semana (0-1)
        category: Categoría del producto
        created_at: Timestamp de creación del registro
    """
    __tablename__ = 'stock_predictions_cache'
    
    product_id = Column(String, primary_key=True, index=True)
    prediction_date = Column(DateTime, primary_key=True, index=True)
    predicted_stock = Column(Float, nullable=False)
    predicted_demand = Column(Float, nullable=False)
    quantity_on_hand = Column(Float, nullable=False)
    quantity_reserved = Column(Float, nullable=False)
    reorder_point = Column(Float, nullable=False)
    optimal_stock_level = Column(Float, nullable=False)
    average_daily_usage = Column(Float, nullable=False)
    stock_status = Column(Integer, nullable=False)
    dia_semana = Column(Integer, nullable=False)
    fin_de_semana = Column(Integer, nullable=False)
    category = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<StockPrediction(product={self.product_id}, date={self.prediction_date}, stock={self.predicted_stock})>"


# ==================== FUNCIONES DE CACHÉ ====================

def get_cached_predictions(
    product_id: str, 
    start_date: datetime, 
    end_date: datetime
) -> Optional[pd.DataFrame]:
    """
    Obtiene predicciones cacheadas para un producto en un rango de fechas.
    
    Args:
        product_id: ID del producto
        start_date: Fecha inicial del rango
        end_date: Fecha final del rango
    
    Returns:
        DataFrame con las predicciones encontradas o None si no hay datos
    """
    SessionLocal = get_session_local()
    session = SessionLocal()
    
    try:
        predictions = session.query(StockPrediction).filter(
            StockPrediction.product_id == product_id,
            StockPrediction.prediction_date >= start_date,
            StockPrediction.prediction_date <= end_date
        ).order_by(StockPrediction.prediction_date).all()
        
        if not predictions:
            return None
        
        # Convertir a DataFrame con el formato esperado por el modelo
        data = [{
            'created_at': p.prediction_date,
            'quantity_on_hand': p.quantity_on_hand,
            'quantity_reserved': p.quantity_reserved,
            'reorder_point': p.reorder_point,
            'optimal_stock_level': p.optimal_stock_level,
            'average_daily_usage': p.average_daily_usage,
            'stock_status': p.stock_status,
            'dia_semana': p.dia_semana,
            'fin_de_semana': p.fin_de_semana,
            'category': p.category,
            'quantity_available': p.predicted_stock  # Para compatibilidad
        } for p in predictions]
        
        return pd.DataFrame(data)
        
    except Exception as e:
        print(f"Error obteniendo predicciones del caché: {e}")
        return None
    finally:
        session.close()


def get_single_cached_prediction(
    product_id: str, 
    prediction_date: datetime
) -> Optional[Dict[str, Any]]:
    """
    Obtiene una predicción específica del caché.
    
    Args:
        product_id: ID del producto
        prediction_date: Fecha específica de la predicción
    
    Returns:
        Diccionario con los datos de la predicción o None si no existe
    """
    SessionLocal = get_session_local()
    session = SessionLocal()
    
    try:
        prediction = session.query(StockPrediction).filter(
            StockPrediction.product_id == product_id,
            StockPrediction.prediction_date == prediction_date
        ).first()
        
        if not prediction:
            return None
        
        return {
            'predicted_stock': prediction.predicted_stock,
            'predicted_demand': prediction.predicted_demand,
            'quantity_on_hand': prediction.quantity_on_hand,
            'created_at': prediction.created_at
        }
        
    except Exception as e:
        print(f"Error obteniendo predicción del caché: {e}")
        return None
    finally:
        session.close()


def save_prediction_to_cache(
    product_id: str, 
    prediction_date: datetime,
    predicted_stock: float, 
    predicted_demand: float,
    features_dict: Dict[str, Any]
) -> bool:
    """
    Guarda una predicción en el caché usando UPSERT (insert or update).
    
    Args:
        product_id: ID del producto
        prediction_date: Fecha de la predicción
        predicted_stock: Stock predicho
        predicted_demand: Demanda predicha
        features_dict: Diccionario con todos los features del modelo
            - quantity_on_hand
            - quantity_reserved
            - reorder_point
            - optimal_stock_level
            - average_daily_usage
            - stock_status
            - dia_semana
            - fin_de_semana
            - category
    
    Returns:
        True si se guardó correctamente, False en caso de error
    """
    SessionLocal = get_session_local()
    session = SessionLocal()
    
    try:
        stmt = insert(StockPrediction).values(
            product_id=product_id,
            prediction_date=prediction_date,
            predicted_stock=predicted_stock,
            predicted_demand=predicted_demand,
            **features_dict
        )
        
        # UPSERT: actualiza si ya existe (basado en PK: product_id + prediction_date)
        stmt = stmt.on_conflict_do_update(
            index_elements=['product_id', 'prediction_date'],
            set_=dict(
                predicted_stock=predicted_stock,
                predicted_demand=predicted_demand,
                **features_dict,
                created_at=datetime.utcnow()
            )
        )
        
        session.execute(stmt)
        session.commit()
        return True
        
    except Exception as e:
        session.rollback()
        print(f"Error guardando predicción en caché: {e}")
        return False
    finally:
        session.close()


def save_multiple_predictions(predictions_list: list) -> int:
    """
    Guarda múltiples predicciones en una sola transacción (más eficiente).
    
    Args:
        predictions_list: Lista de diccionarios con las predicciones.
            Cada diccionario debe contener:
            - product_id
            - prediction_date
            - predicted_stock
            - predicted_demand
            - [todos los features]
    
    Returns:
        Número de predicciones guardadas exitosamente
    """
    if not predictions_list:
        return 0
    
    SessionLocal = get_session_local()
    session = SessionLocal()
    
    try:
        # Usar bulk insert para mejor performance
        for pred_data in predictions_list:
            stmt = insert(StockPrediction).values(**pred_data)
            stmt = stmt.on_conflict_do_update(
                index_elements=['product_id', 'prediction_date'],
                set_=pred_data
            )
            session.execute(stmt)
        
        session.commit()
        return len(predictions_list)
        
    except Exception as e:
        session.rollback()
        print(f"Error guardando múltiples predicciones: {e}")
        return 0
    finally:
        session.close()


def clear_cache_for_product(
    product_id: str, 
    after_date: Optional[datetime] = None
) -> int:
    """
    Limpia el caché de predicciones para un producto.
    Útil cuando se actualizan datos reales y las predicciones ya no son válidas.
    
    Args:
        product_id: ID del producto
        after_date: Si se especifica, solo borra predicciones después de esta fecha
    
    Returns:
        Número de registros eliminados
    """
    SessionLocal = get_session_local()
    session = SessionLocal()
    
    try:
        query = session.query(StockPrediction).filter(
            StockPrediction.product_id == product_id
        )
        
        if after_date:
            query = query.filter(StockPrediction.prediction_date >= after_date)
        
        deleted_count = query.delete()
        session.commit()
        
        print(f"✓ Eliminadas {deleted_count} predicciones del caché para {product_id}")
        return deleted_count
        
    except Exception as e:
        session.rollback()
        print(f"Error limpiando caché: {e}")
        return 0
    finally:
        session.close()


def clear_all_cache() -> int:
    """
    Limpia TODO el caché de predicciones.
    ⚠️ Usar con precaución.
    
    Returns:
        Número de registros eliminados
    """
    SessionLocal = get_session_local()
    session = SessionLocal()
    
    try:
        deleted_count = session.query(StockPrediction).delete()
        session.commit()
        
        print(f"⚠️ Eliminadas TODAS las predicciones del caché ({deleted_count} registros)")
        return deleted_count
        
    except Exception as e:
        session.rollback()
        print(f"Error limpiando caché completo: {e}")
        return 0
    finally:
        session.close()


def get_cache_stats(product_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Obtiene estadísticas del caché de predicciones.
    
    Args:
        product_id: Si se especifica, solo estadísticas de ese producto
    
    Returns:
        Diccionario con estadísticas del caché
    """
    SessionLocal = get_session_local()
    session = SessionLocal()
    
    try:
        query = session.query(StockPrediction)
        
        if product_id:
            query = query.filter(StockPrediction.product_id == product_id)
        
        total_predictions = query.count()
        
        if total_predictions == 0:
            return {
                "total_predictions": 0,
                "products_count": 0,
                "date_range": None
            }
        
        # Obtener rango de fechas
        from sqlalchemy import func
        date_stats = session.query(
            func.min(StockPrediction.prediction_date).label('min_date'),
            func.max(StockPrediction.prediction_date).label('max_date'),
            func.count(func.distinct(StockPrediction.product_id)).label('products_count')
        ).filter(
            StockPrediction.product_id == product_id if product_id else True
        ).first()
        
        return {
            "total_predictions": total_predictions,
            "products_count": date_stats.products_count,
            "date_range": {
                "start": date_stats.min_date.strftime("%Y-%m-%d") if date_stats.min_date else None,
                "end": date_stats.max_date.strftime("%Y-%m-%d") if date_stats.max_date else None
            }
        }
        
    except Exception as e:
        print(f"Error obteniendo estadísticas del caché: {e}")
        return {"error": str(e)}
    finally:
        session.close()


def check_cache_coverage(
    product_id: str, 
    start_date: datetime, 
    end_date: datetime
) -> Dict[str, Any]:
    """
    Verifica qué días están en caché y cuáles faltan en un rango.
    
    Args:
        product_id: ID del producto
        start_date: Fecha inicial
        end_date: Fecha final
    
    Returns:
        Diccionario con días en caché, días faltantes y porcentaje de cobertura
    """
    cached = get_cached_predictions(product_id, start_date, end_date)
    
    # Generar todos los días en el rango
    total_days = (end_date - start_date).days + 1
    all_dates = {start_date + timedelta(days=i) for i in range(total_days)}
    
    if cached is None or len(cached) == 0:
        return {
            "total_days": total_days,
            "cached_days": 0,
            "missing_days": total_days,
            "coverage_percentage": 0.0,
            "missing_dates": sorted([d.strftime("%Y-%m-%d") for d in all_dates])
        }
    
    # Fechas en caché (normalizar a solo fecha, sin hora)
    cached_dates = {pd.to_datetime(d).date() for d in cached['created_at']}
    all_dates_normalized = {d.date() for d in all_dates}
    
    missing_dates = all_dates_normalized - cached_dates
    
    return {
        "total_days": total_days,
        "cached_days": len(cached_dates),
        "missing_days": len(missing_dates),
        "coverage_percentage": round((len(cached_dates) / total_days) * 100, 2),
        "missing_dates": sorted([d.strftime("%Y-%m-%d") for d in missing_dates])
    }