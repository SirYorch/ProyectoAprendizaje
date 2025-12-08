from sqlalchemy import create_engine, Column, String, Integer, Numeric, Boolean, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import LargeBinary
from datetime import datetime

import pandas as pd

# Base para los modelos
Base = declarative_base()


# Modelo de la tabla productos
class Producto(Base):
    __tablename__ = 'productos'
    
    product_id = Column(String(50), primary_key=True)
    product_name = Column(String(255), nullable=False)
    product_sku = Column(String(100), unique=True, nullable=False)
    category = Column(Integer)
    supplier_id = Column(String(50))
    supplier_name = Column(String(255))
    warehouse_location = Column(String(100))
    shelf_location = Column(String(50))
    minimum_stock_level = Column(Integer)
    reorder_point = Column(Integer)
    optimal_stock_level = Column(Integer)
    reorder_quantity = Column(Integer)
    average_daily_usage = Column(Numeric(10, 2))
    unit_cost = Column(Numeric(10, 2))
    stock_status = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relación con registros de inventario
    registros = relationship("RegistroInventario", back_populates="producto", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Producto(product_id='{self.product_id}', product_name='{self.product_name}')>"


# Modelo de la tabla registros_inventario
class RegistroInventario(Base):
    __tablename__ = 'registros_inventario'
    
    id = Column(String(36), primary_key=True)
    product_id = Column(String(50), ForeignKey('productos.product_id', ondelete='CASCADE'), nullable=False)
    created_at = Column(DateTime, nullable=False)
    quantity_on_hand = Column(Integer)
    quantity_reserved = Column(Integer)
    quantity_available = Column(Integer)
    ventas_diarias = Column(Integer)
    total_value = Column(Numeric(12, 2))
    last_order_date = Column(Date)
    last_stock_count_date = Column(Date)
    batch_number = Column(String(100))
    last_updated_at = Column(DateTime)
    notes = Column(Text)
    created_by_id = Column(String(36))
    
    # Relación con producto
    producto = relationship("Producto", back_populates="registros")
    
    def __repr__(self):
        return f"<RegistroInventario(id='{self.id}', product_id='{self.product_id}', quantity_available={self.quantity_available})>"
    
class Document(Base):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text, nullable=False)
    meta = Column(JSON)

    # Relación con embeddings
    embeddings = relationship("Embedding", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id})>"


class Embedding(Base):
    __tablename__ = 'embeddings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id', ondelete='CASCADE'), nullable=False)
    
    vector = Column(LargeBinary, nullable=False)

    document = relationship("Document", back_populates="embeddings")

    def __repr__(self):
        return f"<Embedding(id={self.id}, document_id={self.document_id})>"


# Configuración de la conexión
DATABASE_URL = "postgresql://usuario1:password1@localhost:5432/aprendizaje"

# Crear engine
engine = create_engine(DATABASE_URL, echo=False)

# Crear Session
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


# ==================== FUNCIONES DE PRODUCTOS ====================

def crear_tablas():
    """Crea todas las tablas definidas en Base"""
    Base.metadata.create_all(engine)
    print("✓ Tablas creadas")


def listar_productos():
    """Lista todos los productos"""
    session = SessionLocal()
    try:
        productos = session.query(Producto).all()
        products_ids = []
        print(f"\n=== Total de productos: {len(productos)} ===")
        for producto in productos:
            products_ids.append(producto.product_id)
        return products_ids
    finally:
        session.close()


def obtener_producto(product_id):
    """Obtiene un producto por su ID"""
    session = SessionLocal()
    try:
        producto = session.query(Producto).filter(
            Producto.product_id == product_id
        ).first()
        if producto:
            print(f"\n✓ Producto encontrado: {producto.product_name}")
        else:
            print(f"\n✗ Producto {product_id} no encontrado")
        return producto
    finally:
        session.close()


def agregar_producto(data):
    """Agrega un nuevo producto"""
    session = SessionLocal()
    try:
        nuevo_producto = Producto(**data)
        session.add(nuevo_producto)
        session.commit()
        print(f"✓ Producto agregado: {nuevo_producto.product_name}")
        return nuevo_producto
    except Exception as e:
        session.rollback()
        print(f"✗ Error al agregar producto: {e}")
        return None
    finally:
        session.close()


def actualizar_producto(product_id, data):
    """Actualiza un producto existente"""
    session = SessionLocal()
    try:
        producto = session.query(Producto).filter(
            Producto.product_id == product_id
        ).first()
        if producto:
            for key, value in data.items():
                setattr(producto, key, value)
            producto.updated_at = datetime.now()
            session.commit()
            print(f"✓ Producto actualizado: {producto.product_name}")
            return producto
        else:
            print(f"✗ Producto {product_id} no encontrado")
            return None
    except Exception as e:
        session.rollback()
        print(f"✗ Error al actualizar producto: {e}")
        return None
    finally:
        session.close()


def eliminar_producto(product_id):
    """Elimina un producto"""
    session = SessionLocal()
    try:
        producto = session.query(Producto).filter(
            Producto.product_id == product_id
        ).first()
        if producto:
            product_name = producto.product_name
            session.delete(producto)
            session.commit()
            print(f"✓ Producto eliminado: {product_name}")
            return True
        else:
            print(f"✗ Producto {product_id} no encontrado")
            return False
    except Exception as e:
        session.rollback()
        print(f"✗ Error al eliminar producto: {e}")
        return False
    finally:
        session.close()


# ==================== FUNCIONES DE REGISTROS DE INVENTARIO ====================

def listar_registros(limit=100):
    """Lista registros de inventario"""
    session = SessionLocal()
    try:
        registros = session.query(RegistroInventario).limit(limit).all()
        print(f"\n=== Registros de inventario: {len(registros)} ===")
        for registro in registros[:5]:
            print(f"  • {registro.id} - Producto: {registro.product_id} - Disponible: {registro.quantity_available}")
        if len(registros) > 5:
            print(f"  ... y {len(registros) - 5} más")
        return registros
    finally:
        session.close()


def obtener_registros_por_producto(product_id):
    """Obtiene todos los registros de un producto específico"""
    session = SessionLocal()
    try:
        registros = session.query(RegistroInventario).filter(
            RegistroInventario.product_id == product_id
        ).all()
        print(f"\n=== Registros del producto {product_id}: {len(registros)} ===")
        for registro in registros[:5]:
            print(f"  • Creado: {registro.created_at} - Disponible: {registro.quantity_available}")
        return registros
    finally:
        session.close()


def agregar_registro(data):
    """Agrega un nuevo registro de inventario"""
    session = SessionLocal()
    try:
        nuevo_registro = RegistroInventario(**data)
        session.add(nuevo_registro)
        session.commit()
        print(f"✓ Registro agregado: {nuevo_registro.id}")
        return nuevo_registro
    except Exception as e:
        session.rollback()
        print(f"✗ Error al agregar registro: {e}")
        return None
    finally:
        session.close()


def actualizar_registro(registro_id, data):
    """Actualiza un registro de inventario"""
    session = SessionLocal()
    try:
        registro = session.query(RegistroInventario).filter(
            RegistroInventario.id == registro_id
        ).first()
        if registro:
            for key, value in data.items():
                setattr(registro, key, value)
            registro.last_updated_at = datetime.now()
            session.commit()
            print(f"✓ Registro actualizado: {registro.id}")
            return registro
        else:
            print(f"✗ Registro {registro_id} no encontrado")
            return None
    except Exception as e:
        session.rollback()
        print(f"✗ Error al actualizar registro: {e}")
        return None
    finally:
        session.close()


def eliminar_registro(registro_id):
    """Elimina un registro de inventario"""
    session = SessionLocal()
    try:
        registro = session.query(RegistroInventario).filter(
            RegistroInventario.id == registro_id
        ).first()
        if registro:
            session.delete(registro)
            session.commit()
            print(f"✓ Registro eliminado: {registro_id}")
            return True
        else:
            print(f"✗ Registro {registro_id} no encontrado")
            return False
    except Exception as e:
        session.rollback()
        print(f"✗ Error al eliminar registro: {e}")
        return False
    finally:
        session.close()


def consultar_bajo_stock():
    """Consulta productos con stock bajo"""
    session = SessionLocal()
    try:
        # Obtener el último registro de cada producto
        from sqlalchemy import func
        
        subquery = session.query(
            RegistroInventario.product_id,
            func.max(RegistroInventario.created_at).label('max_created_at')
        ).group_by(RegistroInventario.product_id).subquery()
        
        registros = session.query(RegistroInventario).join(
            subquery,
            (RegistroInventario.product_id == subquery.c.product_id) &
            (RegistroInventario.created_at == subquery.c.max_created_at)
        ).join(Producto).filter(
            RegistroInventario.quantity_available < Producto.reorder_point
        ).all()
        
        print(f"\n=== Productos con stock bajo: {len(registros)} ===")
        for registro in registros:
            producto = registro.producto
            print(f"  • {producto.product_name} - Disponible: {registro.quantity_available} / Reorden: {producto.reorder_point}")
        
        return registros
    finally:
        session.close()


def estadisticas_inventario():
    """Muestra estadísticas del inventario"""
    session = SessionLocal()
    try:
        from sqlalchemy import func
        
        # Total de productos
        total_productos = session.query(func.count(Producto.product_id)).scalar()
        
        # Total de registros
        total_registros = session.query(func.count(RegistroInventario.id)).scalar()
        
        # Valor total (último registro de cada producto)
        subquery = session.query(
            RegistroInventario.product_id,
            func.max(RegistroInventario.created_at).label('max_created_at')
        ).group_by(RegistroInventario.product_id).subquery()
        
        valor_total = session.query(func.sum(RegistroInventario.total_value)).join(
            subquery,
            (RegistroInventario.product_id == subquery.c.product_id) &
            (RegistroInventario.created_at == subquery.c.max_created_at)
        ).scalar() or 0
        
        # Productos por almacén
        por_almacen = session.query(
            Producto.warehouse_location,
            func.count(Producto.product_id)
        ).group_by(Producto.warehouse_location).all()
        
        print("\n=== ESTADÍSTICAS DEL INVENTARIO ===")
        print(f"Total de productos: {total_productos}")
        print(f"Total de registros: {total_registros}")
        print(f"Valor total inventario: ${valor_total:,.2f}")
        print("\nProductos por almacén:")
        for almacen, cantidad in por_almacen:
            print(f"  • {almacen}: {cantidad} productos")
        
        return {
            "total_productos": total_productos,
            "total_registros": total_registros,
            "valor_total": float(valor_total),
            "por_almacen": por_almacen
        }
    finally:
        session.close()


def consultar_con_pandas():
    """Consulta productos con pandas"""
    query = "SELECT * FROM productos"
    df = pd.read_sql(query, engine)
    print(f"\n=== DataFrame con {len(df)} productos ===")
    print(df.head())
    return df


# ==================== EJEMPLO DE USO ====================

if __name__ == "__main__":
    print("=" * 50)
    print("  SQLAlchemy - Gestión de Inventario")
    print("=" * 50)
    
    # 1. Crear tablas (si no existen)
    crear_tablas()
    
    # 2. Consultas
    print("\n[1] Listar productos:")
    listar_productos()
    
    print("\n[2] Listar registros de inventario:")
    listar_registros(10)
    
    print("\n[3] Productos con stock bajo:")
    consultar_bajo_stock()
    
    print("\n[4] Estadísticas:")
    estadisticas_inventario()
    
    # 5. Usar pandas
    print("\n[5] Consulta con Pandas:")
    df = consultar_con_pandas()