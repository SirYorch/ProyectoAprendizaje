from sqlalchemy import create_engine, text, Column, String, Integer, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector
from sentence_transformers import SentenceTransformer
import json
from typing import List, Dict, Any

# ============================================
# 1. CONFIGURACIÓN DE BASE DE DATOS
# ============================================

DATABASE_URL = "postgresql://usuario1:password1@localhost:5432/aprendizaje"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================
# 2. MODELOS DE SQLALCHEMY
# ============================================

class FunctionDefinition(Base):
    """Tabla para definiciones de funciones"""
    __tablename__ = "function_definitions"
    
    id = Column(String, primary_key=True)
    nombre = Column(String, nullable=False, unique=True, index=True)
    descripcion = Column(String, nullable=False)
    parametros = Column(JSON, default=[])  # Lista de parámetros requeridos
    keywords = Column(JSON, default=[])  # Keywords adicionales
    activo = Column(Integer, default=1)  # 1 = activo, 0 = desactivado
    
    # Embedding de la descripción (dimensión 384 para MiniLM)
    embedding = Column(Vector(384))


class FunctionExample(Base):
    """Tabla para ejemplos de uso de funciones"""
    __tablename__ = "function_examples"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    function_id = Column(String, nullable=False, index=True)
    ejemplo = Column(String, nullable=False)
    
    # Embedding del ejemplo
    embedding = Column(Vector(384))


class FAQKnowledge(Base):
    """Tabla para base de conocimiento (FAQs)"""
    __tablename__ = "faq_knowledge"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pregunta = Column(String, nullable=False)
    respuesta = Column(String, nullable=False)
    categoria = Column(String, index=True)
    
    # Embedding de pregunta + respuesta
    embedding = Column(Vector(384))


class ConversationLog(Base):
    """Tabla para logging de conversaciones"""
    __tablename__ = "conversation_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(String, nullable=False, index=True)
    usuario_id = Column(String, index=True)
    mensaje = Column(String, nullable=False)
    tipo_respuesta = Column(String)  # saludo, function_call, rag, etc.
    funcion_ejecutada = Column(String)
    confianza = Column(Float)
    metada = Column(JSON)


# ============================================
# 3. DEFINICIONES DE FUNCIONES
# ============================================

FUNCTION_DEFINITIONS = [
    {
        "id": "func_001",
        "nombre": "predict_stock",
        "descripcion": "Obtiene la predicción de stock para todos los productos disponibles hasta que alguno se agote. Útil para consultas generales sobre el inventario completo.",
        "parametros": [],
        "keywords": ["stock general", "todo el inventario", "todos los productos", "stock completo", "inventario total"],
        "ejemplos": [
            "¿Cuál es el stock actual?",
            "Muéstrame todo el inventario",
            "Dame el stock de todos los productos",
            "Quiero ver el stock completo",
            "¿Cuánto stock tenemos en total?",
            "Predicción de stock general",
            "Inventario completo",
            "Ver todo el stock disponible"
        ]
    },
    {
        "id": "func_002",
        "nombre": "predict_product",
        "descripcion": "Obtiene la predicción de stock para un producto específico hasta que se agote. Requiere el nombre del producto.",
        "parametros": ["producto"],
        "keywords": ["stock de producto", "inventario de", "stock del", "cuánto hay de", "disponibilidad producto"],
        "ejemplos": [
            "¿Cuánto stock hay de Laptop HP?",
            "Muéstrame el inventario de Mouse Logitech",
            "Stock del producto Teclado Mecánico",
            "¿Cuándo se agota el Monitor Samsung?",
            "Predicción de stock para Auriculares Sony",
            "Disponibilidad de Tablet iPad",
            "¿Cuántas unidades hay de Smartphone Galaxy?",
            "Stock de Impresora HP"
        ]
    },
    {
        "id": "func_003",
        "nombre": "predict_date",
        "descripcion": "Obtiene la predicción de stock de todos los productos para una fecha específica futura. Requiere una fecha.",
        "parametros": ["fecha"],
        "keywords": ["stock para fecha", "habrá el", "disponible el", "inventario en fecha", "predicción fecha"],
        "ejemplos": [
            "¿Cuánto stock habrá el 2024-12-25?",
            "Predicción de inventario para el 31 de diciembre",
            "Stock disponible el 2025-01-15",
            "¿Qué productos tendré disponibles el 15 de enero?",
            "Muéstrame el stock para la fecha 2024-12-30",
            "Inventario para el 20 de diciembre",
            "¿Cómo estará el stock el próximo mes?"
        ]
    },
    {
        "id": "func_004",
        "nombre": "predict_product_fecha",
        "descripcion": "Obtiene la predicción de stock de un producto específico en una fecha específica. Requiere producto y fecha.",
        "parametros": ["producto", "fecha"],
        "keywords": ["stock de producto en fecha", "producto para fecha", "disponible el", "tendrá el"],
        "ejemplos": [
            "¿Cuánto stock de Laptop HP tendré el 2024-12-25?",
            "Mouse Logitech disponible para el 31 de diciembre",
            "Stock de Teclado Mecánico el 2025-01-15",
            "¿Tendré Monitor Samsung disponible el 20 de diciembre?",
            "Predicción de Auriculares Sony para el 2025-01-01",
            "¿Cuántas Tablets tendré el 15 de enero?",
            "Laptop HP para el día de navidad"
        ]
    },
    {
        "id": "func_005",
        "nombre": "top_selling",
        "descripcion": "Obtiene el ranking de los 5 productos más vendidos del último mes. No requiere parámetros.",
        "parametros": [],
        "keywords": ["más vendidos", "top ventas", "best sellers", "productos populares", "productos estrella", "mejor vendidos"],
        "ejemplos": [
            "¿Cuáles son los productos más vendidos?",
            "Top 5 de ventas",
            "Productos estrella del mes",
            "¿Qué productos se venden más?",
            "Mejores productos en ventas",
            "Artículos más populares",
            "Best sellers",
            "¿Qué se está vendiendo bien?"
        ]
    },
    {
        "id": "func_006",
        "nombre": "least_selling",
        "descripcion": "Obtiene los 5 productos con menor demanda del último mes. No requiere parámetros.",
        "parametros": [],
        "keywords": ["menos vendidos", "baja demanda", "pocas ventas", "peores ventas", "productos lentos"],
        "ejemplos": [
            "¿Cuáles son los productos menos vendidos?",
            "Productos con baja demanda",
            "¿Qué productos no se venden?",
            "Artículos con pocas ventas",
            "Peores productos en ventas",
            "Productos de movimiento lento",
            "¿Qué no está funcionando?"
        ]
    },
    {
        "id": "func_007",
        "nombre": "generate_csv",
        "descripcion": "Genera un archivo CSV con los registros del último mes o del mes especificado. Mes es opcional.",
        "parametros": ["mes"],
        "keywords": ["reporte csv", "archivo csv", "exportar csv", "descargar csv", "csv"],
        "ejemplos": [
            "Genera un reporte CSV",
            "Necesito un archivo CSV del mes actual",
            "Exportar datos a CSV",
            "Descargar reporte en CSV",
            "Quiero un CSV de noviembre 2024",
            "Dame un CSV del último mes",
            "Exporta los datos en formato CSV"
        ]
    },
    {
        "id": "func_008",
        "nombre": "generate_excel",
        "descripcion": "Genera un archivo Excel con los registros del último mes o del mes especificado. Mes es opcional.",
        "parametros": ["mes"],
        "keywords": ["reporte excel", "archivo excel", "exportar excel", "xlsx", "xls", "descargar excel"],
        "ejemplos": [
            "Genera un reporte Excel",
            "Necesito un archivo Excel del mes actual",
            "Exportar datos a Excel",
            "Descargar reporte en xlsx",
            "Quiero un Excel de diciembre 2024",
            "Dame un Excel del último mes",
            "Exporta los datos en formato Excel"
        ]
    }
]

# FAQs de ejemplo
FAQ_DATA = [
    {
        "pregunta": "¿Cuál es la política de garantía?",
        "respuesta": "Todos nuestros productos cuentan con garantía del fabricante. Las laptops y monitores tienen 2 años de garantía, mientras que accesorios como mouse y teclados tienen 1 año. La garantía cubre defectos de fábrica y no cubre daños por mal uso.",
        "categoria": "garantia"
    },
    {
        "pregunta": "¿Cómo funcionan los envíos?",
        "respuesta": "Realizamos envíos a todo el país. El tiempo de entrega es de 2-3 días hábiles en ciudades principales y 5-7 días en zonas rurales. El envío es gratuito para compras superiores a $100.",
        "categoria": "envios"
    },
    {
        "pregunta": "¿Puedo devolver un producto?",
        "respuesta": "Aceptamos devoluciones dentro de los primeros 30 días de compra, siempre que el producto esté en perfectas condiciones y con su empaque original. El costo de envío de devolución corre por cuenta del cliente.",
        "categoria": "devoluciones"
    },
    {
        "pregunta": "¿Qué métodos de pago aceptan?",
        "respuesta": "Aceptamos tarjetas de crédito y débito (Visa, Mastercard, American Express), transferencias bancarias y pagos en efectivo contra entrega en ciudades principales.",
        "categoria": "pagos"
    },
    {
        "pregunta": "¿Cuál es el horario de atención?",
        "respuesta": "Nuestro horario de atención al cliente es de lunes a viernes de 9:00 AM a 6:00 PM, y sábados de 9:00 AM a 1:00 PM. Estamos cerrados los domingos y días festivos.",
        "categoria": "horarios"
    }
]


# ============================================
# 4. FUNCIÓN DE SETUP
# ============================================

def setup_database():
    """
    Configura la base de datos: crea extensión, tablas e índices
    Ejecuta esto UNA VEZ al iniciar la aplicación
    """
    print("🔧 Configurando base de datos...")
    
    # Crear extensión pgvector
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    print("✅ Extensión pgvector habilitada")
    
    # Crear todas las tablas - ¡CORREGIDO EL TYPO!
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas")
    
    # Crear índices para búsqueda vectorial (HNSW es más rápido que IVFFlat)
    with engine.connect() as conn:
        # Índice para function_definitions
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_function_definitions_embedding 
            ON function_definitions 
            USING hnsw (embedding vector_cosine_ops)
        """))
        
        # Índice para function_examples
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_function_examples_embedding 
            ON function_examples 
            USING hnsw (embedding vector_cosine_ops)
        """))
        
        # Índice para faq_knowledge
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_faq_knowledge_embedding 
            ON faq_knowledge 
            USING hnsw (embedding vector_cosine_ops)
        """))
        
        conn.commit()
    print("✅ Índices vectoriales creados")


def indexar_funciones():
    """
    Indexa las definiciones de funciones y sus ejemplos
    Ejecuta esto al iniciar o cuando agregues nuevas funciones
    """
    print("\n🔄 Indexando funciones...")
    
    # Carga el modelo de embeddings
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    
    session = SessionLocal()
    
    try:
        # Limpia datos existentes (opcional, solo en desarrollo)
        # session.query(FunctionDefinition).delete()
        # session.query(FunctionExample).delete()
        
        for func_def in FUNCTION_DEFINITIONS:
            # Verifica si ya existe
            existing = session.query(FunctionDefinition).filter_by(
                id=func_def['id']
            ).first()
            
            if existing:
                print(f"⏭  Función {func_def['nombre']} ya existe, saltando...")
                continue
            
            # Genera embedding de la descripción completa
            texto_completo = f"{func_def['descripcion']} {' '.join(func_def['keywords'])}"
            embedding = model.encode([texto_completo])[0].tolist()
            
            # Inserta definición de función
            func_db = FunctionDefinition(
                id=func_def['id'],
                nombre=func_def['nombre'],
                descripcion=func_def['descripcion'],
                parametros=func_def['parametros'],
                keywords=func_def['keywords'],
                embedding=embedding
            )
            session.add(func_db)
            
            # Inserta ejemplos
            ejemplos_embeddings = model.encode(func_def['ejemplos']).tolist()
            for ejemplo, emb in zip(func_def['ejemplos'], ejemplos_embeddings):
                ejemplo_db = FunctionExample(
                    function_id=func_def['id'],
                    ejemplo=ejemplo,
                    embedding=emb
                )
                session.add(ejemplo_db)
            
            print(f"✅ Indexada función: {func_def['nombre']} con {len(func_def['ejemplos'])} ejemplos")
        
        session.commit()
        print(f"\n✅ Total de {len(FUNCTION_DEFINITIONS)} funciones indexadas")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error al indexar funciones: {e}")
        raise
    finally:
        session.close()


def indexar_faqs():
    """
    Indexa la base de conocimiento (FAQs)
    """
    print("\n🔄 Indexando FAQs...")
    
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    session = SessionLocal()
    
    try:
        # Limpia datos existentes (opcional)
        # session.query(FAQKnowledge).delete()
        
        for faq in FAQ_DATA:
            # Verifica si ya existe
            existing = session.query(FAQKnowledge).filter_by(
                pregunta=faq['pregunta']
            ).first()
            
            if existing:
                continue
            
            # Genera embedding de pregunta + respuesta
            texto_completo = f"{faq['pregunta']} {faq['respuesta']}"
            embedding = model.encode([texto_completo])[0].tolist()
            
            faq_db = FAQKnowledge(
                pregunta=faq['pregunta'],
                respuesta=faq['respuesta'],
                categoria=faq['categoria'],
                embedding=embedding
            )
            session.add(faq_db)
        
        session.commit()
        print(f"✅ {len(FAQ_DATA)} FAQs indexadas")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error al indexar FAQs: {e}")
        raise
    finally:
        session.close()


# ============================================
# 5. FUNCIÓN PRINCIPAL DE INICIALIZACIÓN
# ============================================

def initialize_chatbot_db(force_reindex: bool = False):
    """
    Función principal para inicializar todo el sistema
    
    Args:
        force_reindex: Si True, re-indexa todo (útil después de cambios)
    """
    print("\n" + "="*70)
    print("INICIALIZANDO SISTEMA DE CHATBOT EN POSTGRESQL")
    print("="*70 + "\n")
    
    try:
        # Paso 1: Setup de base de datos
        setup_database()
        
        # Paso 2: Indexar funciones
        if force_reindex:
            session = SessionLocal()
            session.query(FunctionDefinition).delete()
            session.query(FunctionExample).delete()
            session.commit()
            session.close()
            print("🗑️  Datos anteriores eliminados")
        
        indexar_funciones()
        
        # Paso 3: Indexar FAQs
        if force_reindex:
            session = SessionLocal()
            session.query(FAQKnowledge).delete()
            session.commit()
            session.close()
        
        indexar_faqs()
        
        print("\n" + "="*70)
        print("✅ INICIALIZACIÓN COMPLETA")
        print("="*70)
        print("\n📊 Estadísticas:")
        
        session = SessionLocal()
        n_functions = session.query(FunctionDefinition).count()
        n_examples = session.query(FunctionExample).count()
        n_faqs = session.query(FAQKnowledge).count()
        session.close()
        
        print(f"   • Funciones: {n_functions}")
        print(f"   • Ejemplos: {n_examples}")
        print(f"   • FAQs: {n_faqs}")
        print("\n✨ El sistema está listo para usar\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error durante la inicialización: {e}")
        import traceback
        traceback.print_exc()
        return False


# ============================================
# 6. VERIFICACIÓN Y TESTS
# ============================================

def verificar_setup():
    """Verifica que todo esté correctamente configurado"""
    print("\n🔍 Verificando configuración...")
    
    session = SessionLocal()
    
    try:
        # Test 1: Verificar extensión pgvector
        result = session.execute(text(
            "SELECT * FROM pg_extension WHERE extname = 'vector'"
        )).fetchone()
        assert result is not None, "Extensión pgvector no instalada"
        print("✅ pgvector está instalado")
        
        # Test 2: Verificar tablas
        for table in ['function_definitions', 'function_examples', 'faq_knowledge']:
            result = session.execute(text(
                f"SELECT COUNT(*) FROM {table}"
            )).scalar()
            print(f"✅ Tabla {table}: {result} registros")
        
        # Test 3: Verificar índices
        result = session.execute(text("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename IN ('function_definitions', 'function_examples', 'faq_knowledge')
            AND indexname LIKE 'idx_%'
        """)).fetchall()
        print(f"✅ {len(result)} índices vectoriales creados")
        
        # Test 4: Test de búsqueda vectorial simple
        test_query = "¿Cuánto stock hay?"
        model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        query_embedding = model.encode([test_query])[0].tolist()
        
        result = session.execute(text("""
            SELECT nombre, 1 - (embedding <=> :query_embedding) as similarity
            FROM function_definitions
            ORDER BY embedding <=> :query_embedding
            LIMIT 1
        """), {"query_embedding": str(query_embedding)}).fetchone()
        
        print(f"✅ Test de búsqueda: '{test_query}' → {result[0]} (similitud: {result[1]:.2%})")
        
        print("\n✨ Todas las verificaciones pasaron correctamente\n")
        return True
        
    except Exception as e:
        print(f"\n❌ Error en verificación: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


# ============================================
# 7. SCRIPT PRINCIPAL
# ============================================

if __name__ == "__main__":
    import sys
    
    # Argumento para forzar re-indexación
    force_reindex = "--force" in sys.argv
    
    # Inicializa todo
    success = initialize_chatbot_db(force_reindex=force_reindex)
    
    if success:
        # Verifica que todo funcione
        verificar_setup()
    else:
        print("\n❌ La inicialización falló. Revisa los errores anteriores.")
        sys.exit(1)