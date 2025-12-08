from datetime import datetime, timedelta
from sqlalchemy import func, create_engine, Column, String, Integer, Float, DateTime, Boolean, Text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import pandas as pd
import uuid

# ============================================
# CONFIGURACIÓN DE BASE DE DATOS
# ============================================

DATABASE_URL = "postgresql://usuario1:password1@localhost:5432/aprendizaje"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================
# MODELOS DE SQLALCHEMY
# ============================================

class Producto(Base):
    """Modelo para la tabla productos"""
    __tablename__ = "productos"
    
    product_id = Column(String(50), primary_key=True)
    product_name = Column(String(255), nullable=False)
    product_sku = Column(String(100), unique=True, nullable=False)
    supplier_id = Column(String(50))
    supplier_name = Column(String(255))
    warehouse_location = Column(String(100))
    shelf_location = Column(String(50))
    minimum_stock_level = Column(Integer)
    reorder_point = Column(Integer)
    optimal_stock_level = Column(Integer)
    reorder_quantity = Column(Integer)
    average_daily_usage = Column(Float)
    unit_cost = Column(Float)
    stock_status = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RegistroInventario(Base):
    """Modelo para la tabla registros_inventario"""
    __tablename__ = "registros_inventario"
    
    id = Column(String, primary_key=True)  # UUID como string
    product_id = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False)
    quantity_on_hand = Column(Integer)
    quantity_reserved = Column(Integer)
    quantity_available = Column(Integer)
    ventas_diarias = Column(Integer)
    total_value = Column(Float)
    last_order_date = Column(DateTime)
    last_stock_count_date = Column(DateTime)
    batch_number = Column(String(100))
    last_updated_at = Column(DateTime)
    notes = Column(Text)
    created_by_id = Column(String)  # UUID como string


# ============================================
# FUNCIONES DE NEGOCIO
# ============================================

def top_selling():
    """
    Obtiene los 5 productos más vendidos del último mes.
    Retorna una lista de diccionarios.
    """
    session = SessionLocal()
    try:
        hace_un_mes = datetime.now() - timedelta(days=30)

        # Agrupamos ventas por producto usando registros del último mes
        resultados = (
            session.query(
                Producto.product_name,
                func.sum(RegistroInventario.ventas_diarias).label("ventas")
            )
            .join(RegistroInventario, Producto.product_id == RegistroInventario.product_id)
            .filter(RegistroInventario.created_at >= hace_un_mes)
            .group_by(Producto.product_name)
            .order_by(func.sum(RegistroInventario.ventas_diarias).desc())
            .limit(5)
            .all()
        )

        data = [
            {"product": r.product_name, "ventas": int(r.ventas or 0)}
            for r in resultados
        ]

        print(f"✓ Top 5 productos más vendidos obtenidos: {len(data)} productos")
        return data

    except Exception as e:
        print(f"✗ Error en top_selling: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        session.close()


def least_selling():
    """
    Obtiene los 5 productos con menor venta en el último mes.
    Retorna una lista de diccionarios.
    """
    session = SessionLocal()
    try:
        hace_un_mes = datetime.now() - timedelta(days=30)

        resultados = (
            session.query(
                Producto.product_name,
                func.sum(RegistroInventario.ventas_diarias).label("ventas")
            )
            .join(RegistroInventario, Producto.product_id == RegistroInventario.product_id)
            .filter(RegistroInventario.created_at >= hace_un_mes)
            .group_by(Producto.product_name)
            .order_by(func.sum(RegistroInventario.ventas_diarias).asc())
            .limit(5)
            .all()
        )

        data = [
            {"product": r.product_name, "ventas": int(r.ventas or 0)}
            for r in resultados
        ]

        print(f"✓ Top 5 productos menos vendidos obtenidos: {len(data)} productos")
        return data

    except Exception as e:
        print(f"✗ Error en least_selling: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        session.close()


def generate_excel(month=None):
    """
    Genera un archivo Excel con los registros del último mes o un mes indicado.
    Retorna la ruta del archivo generado.
    
    Args:
        month: String en formato "YYYY-MM" (ej: "2024-12") o None para último mes
    """
    session = SessionLocal()
    try:
        if month:
            año, mes = map(int, month.split("-"))
            inicio = datetime(año, mes, 1)
            if mes == 12:
                fin = datetime(año + 1, 1, 1)
            else:
                fin = datetime(año, mes + 1, 1)
        else:
            fin = datetime.now()
            inicio = fin - timedelta(days=30)

        query = (
            session.query(
                RegistroInventario.id,
                RegistroInventario.product_id,
                RegistroInventario.created_at,
                RegistroInventario.quantity_available,
                RegistroInventario.ventas_diarias,
                RegistroInventario.total_value
            )
            .filter(RegistroInventario.created_at >= inicio)
            .filter(RegistroInventario.created_at < fin)
        )

        df = pd.read_sql(query.statement, session.bind)

        # Crear directorio si no existe
        import os
        os.makedirs("reportes", exist_ok=True)
        
        file_path = f"reportes/reporte_{inicio.date()}_{fin.date()}.xlsx"
        df.to_excel(file_path, index=False)

        print(f"✓ Excel generado: {file_path}")
        return file_path

    except Exception as e:
        print(f"✗ Error en generate_excel: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        session.close()


def generate_csv(month=None):
    """
    Genera un archivo CSV con los registros del último mes o del mes especificado.
    Retorna la ruta del archivo generado.
    
    Args:
        month: String en formato "YYYY-MM" (ej: "2024-12") o None para último mes
    """
    session = SessionLocal()
    try:
        if month:
            # formato esperado: "2025-01"
            año, mes = map(int, month.split("-"))
            inicio = datetime(año, mes, 1)
            if mes == 12:
                fin = datetime(año + 1, 1, 1)
            else:
                fin = datetime(año, mes + 1, 1)
        else:
            fin = datetime.now()
            inicio = fin - timedelta(days=30)

        query = (
            session.query(
                RegistroInventario.id,
                RegistroInventario.product_id,
                RegistroInventario.created_at,
                RegistroInventario.quantity_available,
                RegistroInventario.ventas_diarias,
                RegistroInventario.total_value
            )
            .filter(RegistroInventario.created_at >= inicio)
            .filter(RegistroInventario.created_at < fin)
        )

        df = pd.read_sql(query.statement, session.bind)

        # Crear directorio si no existe
        import os
        os.makedirs("reportes", exist_ok=True)
        
        file_path = f"reportes/reporte_{inicio.date()}_{fin.date()}.csv"
        df.to_csv(file_path, index=False)

        print(f"✓ CSV generado: {file_path}")
        return file_path

    except Exception as e:
        print(f"✗ Error en generate_csv: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        session.close()
