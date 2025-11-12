from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
import uuid

# Importar desde models.py
from models import (
    Producto,
    RegistroInventario,
    SessionLocal,
    listar_productos,
    obtener_producto,
    agregar_producto,
    actualizar_producto,
    eliminar_producto,
    listar_registros,
    obtener_registros_por_producto,
    agregar_registro,
    actualizar_registro,
    eliminar_registro,
    consultar_bajo_stock,
    estadisticas_inventario
)

# Inicializar FastAPI
app = FastAPI(
    title="API de Inventario",
    description="API para gestión de productos y registros de inventario con PostgreSQL",
    version="2.0.0"
)

# ==================== MODELOS PYDANTIC ====================

class MensajeRequest(BaseModel):
    mensaje: str

class MensajeResponse(BaseModel):
    recibido: str
    timestamp: str

# Modelos para Producto
class ProductoCreate(BaseModel):
    product_id: str
    product_name: str
    product_sku: str
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    warehouse_location: Optional[str] = None
    shelf_location: Optional[str] = None
    minimum_stock_level: Optional[int] = None
    reorder_point: Optional[int] = None
    optimal_stock_level: Optional[int] = None
    reorder_quantity: Optional[int] = None
    average_daily_usage: Optional[Decimal] = None
    unit_cost: Optional[Decimal] = None
    stock_status: Optional[int] = None
    is_active: bool = True

class ProductoUpdate(BaseModel):
    product_name: Optional[str] = None
    supplier_id: Optional[str] = None
    supplier_name: Optional[str] = None
    warehouse_location: Optional[str] = None
    shelf_location: Optional[str] = None
    minimum_stock_level: Optional[int] = None
    reorder_point: Optional[int] = None
    optimal_stock_level: Optional[int] = None
    reorder_quantity: Optional[int] = None
    average_daily_usage: Optional[Decimal] = None
    unit_cost: Optional[Decimal] = None
    stock_status: Optional[int] = None
    is_active: Optional[bool] = None

class ProductoResponse(BaseModel):
    product_id: str
    product_name: str
    product_sku: str
    warehouse_location: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True

# Modelos para Registro de Inventario
class RegistroCreate(BaseModel):
    product_id: str
    quantity_on_hand: Optional[int] = 0
    quantity_reserved: Optional[int] = 0
    quantity_available: Optional[int] = 0
    ventas_diarias: Optional[int] = None
    total_value: Optional[Decimal] = None
    last_order_date: Optional[date] = None
    last_stock_count_date: Optional[date] = None
    batch_number: Optional[str] = None
    notes: Optional[str] = None

class RegistroUpdate(BaseModel):
    quantity_on_hand: Optional[int] = None
    quantity_reserved: Optional[int] = None
    quantity_available: Optional[int] = None
    ventas_diarias: Optional[int] = None
    total_value: Optional[Decimal] = None
    notes: Optional[str] = None

class RegistroResponse(BaseModel):
    id: str
    product_id: str
    created_at: datetime
    quantity_available: Optional[int]
    quantity_on_hand: Optional[int]
    total_value: Optional[Decimal]
    
    class Config:
        from_attributes = True

# Modelo para predicción
class PrediccionRequest(BaseModel):
    producto: str
    fecha: str  # Formato: "DD/MM/YYYY" o "MM/DD/YYYY"

class PrediccionResponse(BaseModel):
    producto: str
    fecha: str
    prediccion: int
    mensaje: Optional[str] = None

# ==================== DEPENDENCIAS ====================

def get_db():
    """Obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== ENDPOINTS BÁSICOS ====================

@app.get("/")
async def root():
    """Endpoint raíz - Health check"""
    return {
        "status": "online",
        "mensaje": "API de Inventario funcionando correctamente",
        "version": "2.0.0",
        "base_de_datos": "PostgreSQL",
        "tablas": ["productos", "registros_inventario"]
    }

@app.get("/saludo")
async def obtener_saludo():
    """GET - Obtiene un saludo"""
    return {
        "mensaje": "¡Hola! Bienvenido a la API de inventario",
        "fecha": datetime.now().isoformat(),
        "endpoints": {
            "productos": ["/productos", "/productos/{product_id}"],
            "registros": ["/registros-inventario", "/registros-inventario/{registro_id}"],
            "estadisticas": ["/estadisticas", "/bajo-stock"]
        }
    }

@app.post("/mensaje", response_model=MensajeResponse)
async def recibir_mensaje(data: MensajeRequest):
    """POST - Recibe un mensaje string"""
    return {
        "recibido": data.mensaje,
        "timestamp": datetime.now().isoformat()
    }

@app.put("/actualizar/{item_id}")
async def actualizar_item_simple(item_id: str):
    """PUT - Endpoint de prueba que devuelve saludo"""
    return {
        "mensaje": f"¡Hola! Solicitud PUT recibida para el item {item_id}",
        "accion": "actualizar",
        "item_id": item_id,
        "nota": "Usa /productos/{product_id} o /registros-inventario/{registro_id} para actualizar datos reales"
    }

@app.delete("/eliminar/{item_id}")
async def eliminar_item_simple(item_id: str):
    """DELETE - Endpoint de prueba que devuelve saludo"""
    return {
        "mensaje": f"¡Hola! Solicitud DELETE recibida para el item {item_id}",
        "accion": "eliminar",
        "item_id": item_id,
        "nota": "Usa /productos/{product_id} o /registros-inventario/{registro_id} para eliminar datos reales"
    }

# ==================== ENDPOINTS DE PRODUCTOS ====================

@app.get("/productos", response_model=List[ProductoResponse])
async def listar_productos_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    activos_solo: bool = Query(False),
    db: Session = Depends(get_db)
):
    """GET - Lista todos los productos"""
    query = db.query(Producto)
    
    if activos_solo:
        query = query.filter(Producto.is_active == True)
    
    productos = query.offset(skip).limit(limit).all()
    return productos

@app.get("/productos/{product_id}")
async def obtener_producto_endpoint(product_id: str, db: Session = Depends(get_db)):
    """GET - Obtiene un producto específico por ID"""
    producto = db.query(Producto).filter(Producto.product_id == product_id).first()
    
    if not producto:
        raise HTTPException(status_code=404, detail=f"Producto {product_id} no encontrado")
    
    return producto

@app.post("/productos", status_code=201)
async def crear_producto_endpoint(producto: ProductoCreate, db: Session = Depends(get_db)):
    """POST - Crea un nuevo producto"""
    # Verificar si ya existe
    existe = db.query(Producto).filter(Producto.product_id == producto.product_id).first()
    if existe:
        raise HTTPException(status_code=400, detail=f"El producto {producto.product_id} ya existe")
    
    try:
        nuevo_producto = Producto(**producto.model_dump())
        nuevo_producto.created_at = datetime.now()
        nuevo_producto.updated_at = datetime.now()
        
        db.add(nuevo_producto)
        db.commit()
        db.refresh(nuevo_producto)
        
        return {
            "mensaje": "Producto creado exitosamente",
            "producto": nuevo_producto
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al crear producto: {str(e)}")

@app.put("/productos/{product_id}")
async def actualizar_producto_endpoint(
    product_id: str,
    producto_update: ProductoUpdate,
    db: Session = Depends(get_db)
):
    """PUT - Actualiza un producto"""
    producto = db.query(Producto).filter(Producto.product_id == product_id).first()
    
    if not producto:
        raise HTTPException(status_code=404, detail=f"Producto {product_id} no encontrado")
    
    try:
        update_data = producto_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(producto, key, value)
        
        producto.updated_at = datetime.now()
        db.commit()
        db.refresh(producto)
        
        return {
            "mensaje": "Producto actualizado exitosamente",
            "producto": producto
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al actualizar: {str(e)}")

@app.delete("/productos/{product_id}")
async def eliminar_producto_endpoint(product_id: str, db: Session = Depends(get_db)):
    """DELETE - Elimina un producto (y sus registros asociados)"""
    producto = db.query(Producto).filter(Producto.product_id == product_id).first()
    
    if not producto:
        raise HTTPException(status_code=404, detail=f"Producto {product_id} no encontrado")
    
    try:
        product_name = producto.product_name
        db.delete(producto)
        db.commit()
        
        return {
            "mensaje": f"Producto '{product_name}' eliminado exitosamente",
            "product_id": product_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al eliminar: {str(e)}")

# ==================== ENDPOINTS DE REGISTROS DE INVENTARIO ====================

@app.get("/registros-inventario", response_model=List[RegistroResponse])
async def listar_registros_endpoint(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    product_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """GET - Lista registros de inventario"""
    query = db.query(RegistroInventario)
    
    if product_id:
        query = query.filter(RegistroInventario.product_id == product_id)
    
    registros = query.order_by(RegistroInventario.created_at.desc()).offset(skip).limit(limit).all()
    return registros

@app.get("/registros-inventario/{registro_id}")
async def obtener_registro_endpoint(registro_id: str, db: Session = Depends(get_db)):
    """GET - Obtiene un registro específico por ID"""
    registro = db.query(RegistroInventario).filter(RegistroInventario.id == registro_id).first()
    
    if not registro:
        raise HTTPException(status_code=404, detail=f"Registro {registro_id} no encontrado")
    
    return registro

@app.get("/productos/{product_id}/registros")
async def obtener_registros_de_producto(
    product_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """GET - Obtiene todos los registros de un producto específico"""
    # Verificar que el producto existe
    producto = db.query(Producto).filter(Producto.product_id == product_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail=f"Producto {product_id} no encontrado")
    
    registros = db.query(RegistroInventario).filter(
        RegistroInventario.product_id == product_id
    ).order_by(RegistroInventario.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "producto": producto,
        "total_registros": len(registros),
        "registros": registros
    }

@app.post("/registros-inventario", status_code=201)
async def crear_registro_endpoint(registro: RegistroCreate, db: Session = Depends(get_db)):
    """POST - Crea un nuevo registro de inventario"""
    # Verificar que el producto existe
    producto = db.query(Producto).filter(Producto.product_id == registro.product_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail=f"Producto {registro.product_id} no encontrado")
    
    try:
        registro_data = registro.model_dump()
        registro_data['id'] = str(uuid.uuid4())
        registro_data['created_at'] = datetime.now()
        registro_data['last_updated_at'] = datetime.now()
        
        nuevo_registro = RegistroInventario(**registro_data)
        db.add(nuevo_registro)
        db.commit()
        db.refresh(nuevo_registro)
        
        return {
            "mensaje": "Registro de inventario creado exitosamente",
            "registro": nuevo_registro
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al crear registro: {str(e)}")

@app.put("/registros-inventario/{registro_id}")
async def actualizar_registro_endpoint(
    registro_id: str,
    registro_update: RegistroUpdate,
    db: Session = Depends(get_db)
):
    """PUT - Actualiza un registro de inventario"""
    registro = db.query(RegistroInventario).filter(RegistroInventario.id == registro_id).first()
    
    if not registro:
        raise HTTPException(status_code=404, detail=f"Registro {registro_id} no encontrado")
    
    try:
        update_data = registro_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(registro, key, value)
        
        registro.last_updated_at = datetime.now()
        db.commit()
        db.refresh(registro)
        
        return {
            "mensaje": "Registro actualizado exitosamente",
            "registro": registro
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al actualizar: {str(e)}")

@app.delete("/registros-inventario/{registro_id}")
async def eliminar_registro_endpoint(registro_id: str, db: Session = Depends(get_db)):
    """DELETE - Elimina un registro de inventario"""
    registro = db.query(RegistroInventario).filter(RegistroInventario.id == registro_id).first()
    
    if not registro:
        raise HTTPException(status_code=404, detail=f"Registro {registro_id} no encontrado")
    
    try:
        db.delete(registro)
        db.commit()
        
        return {
            "mensaje": "Registro eliminado exitosamente",
            "registro_id": registro_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al eliminar: {str(e)}")

# ==================== ENDPOINTS DE ESTADÍSTICAS ====================

@app.get("/estadisticas")
async def obtener_estadisticas_endpoint(db: Session = Depends(get_db)):
    """GET - Obtiene estadísticas generales del inventario"""
    
    # Total de productos
    total_productos = db.query(func.count(Producto.product_id)).scalar()
    
    # Productos activos
    productos_activos = db.query(Producto).filter(Producto.is_active == True).count()
    
    # Total de registros
    total_registros = db.query(func.count(RegistroInventario.id)).scalar()
    
    # Últimos registros por producto para calcular valor total
    subquery = db.query(
        RegistroInventario.product_id,
        func.max(RegistroInventario.created_at).label('max_created_at')
    ).group_by(RegistroInventario.product_id).subquery()
    
    valor_total = db.query(func.sum(RegistroInventario.total_value)).join(
        subquery,
        (RegistroInventario.product_id == subquery.c.product_id) &
        (RegistroInventario.created_at == subquery.c.max_created_at)
    ).scalar() or 0
    
    # Productos por almacén
    por_almacen = db.query(
        Producto.warehouse_location,
        func.count(Producto.product_id)
    ).group_by(Producto.warehouse_location).all()
    
    return {
        "total_productos": total_productos,
        "productos_activos": productos_activos,
        "productos_inactivos": total_productos - productos_activos,
        "total_registros": total_registros,
        "valor_total_inventario": float(valor_total),
        "productos_por_almacen": [
            {"almacen": almacen or "Sin asignar", "cantidad": cantidad}
            for almacen, cantidad in por_almacen
        ]
    }

@app.get("/bajo-stock")
async def productos_bajo_stock_endpoint(db: Session = Depends(get_db)):
    """GET - Lista productos con stock bajo"""
    # Obtener últimos registros de cada producto
    subquery = db.query(
        RegistroInventario.product_id,
        func.max(RegistroInventario.created_at).label('max_created_at')
    ).group_by(RegistroInventario.product_id).subquery()
    
    registros = db.query(RegistroInventario).join(
        subquery,
        (RegistroInventario.product_id == subquery.c.product_id) &
        (RegistroInventario.created_at == subquery.c.max_created_at)
    ).join(Producto).filter(
        RegistroInventario.quantity_available < Producto.reorder_point
    ).all()
    
    return {
        "total": len(registros),
        "productos_bajo_stock": [
            {
                "product_id": r.product_id,
                "product_name": r.producto.product_name,
                "quantity_available": r.quantity_available,
                "reorder_point": r.producto.reorder_point,
                "diferencia": r.producto.reorder_point - r.quantity_available
            }
            for r in registros
        ]
    }

@app.get("/almacenes")
async def listar_almacenes_endpoint(db: Session = Depends(get_db)):
    """GET - Lista todos los almacenes y su información"""
    almacenes = db.query(
        Producto.warehouse_location,
        func.count(Producto.product_id).label('total_productos')
    ).group_by(Producto.warehouse_location).all()
    
    return [
        {
            "almacen": a.warehouse_location or "Sin asignar",
            "total_productos": a.total_productos
        }
        for a in almacenes
    ]

# ==================== ENDPOINT DE PREDICCIÓN ====================

@app.post("/predict", status_code=201, response_model=PrediccionResponse)
async def predecir_inventario(request: PrediccionRequest, db: Session = Depends(get_db)):
    """POST - Realiza predicción de inventario para un producto y fecha"""
    
    # Verificar que el producto existe
    producto = db.query(Producto).filter(Producto.product_id == request.producto).first()
    if not producto:
        raise HTTPException(status_code=404, detail=f"Producto {request.producto} no encontrado")
    
    # TODO: Implementar lógica de predicción aquí
    # Por ahora retorna un valor de prueba
    prediccion = 9
    
    return {
        "producto": request.producto,
        "fecha": request.fecha,
        "prediccion": prediccion,
        "mensaje": f"Predicción de stock para {producto.product_name}"
    }

# ==================== EJECUTAR ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("Backend:app", host="0.0.0.0", port=8000, reload=True)