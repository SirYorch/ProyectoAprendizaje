"""
Manejo de conexiones a PostgreSQL usando SQLAlchemy.
"""

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import Generator
from .config import db_config


# Base para los modelos ORM
Base = declarative_base()

# Engine global
_engine: Engine = None
_SessionLocal: sessionmaker = None


def get_engine() -> Engine:
    """
    Obtiene o crea el engine de SQLAlchemy.
    
    Returns:
        Engine de SQLAlchemy
    """
    global _engine
    
    if _engine is None:
        _engine = create_engine(
            db_config.get_database_url(),
            echo=db_config.echo,
            pool_pre_ping=True,  # Verifica conexiones antes de usarlas
            pool_size=10,  # Tamaño del pool
            max_overflow=20  # Conexiones adicionales permitidas
        )
        print("✓ Engine de SQLAlchemy creado")
    
    return _engine


def get_session_local() -> sessionmaker:
    """
    Obtiene o crea el sessionmaker.
    
    Returns:
        SessionLocal factory
    """
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        print("✓ SessionLocal creado")
    
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para FastAPI que proporciona una sesión de base de datos.
    
    Uso en FastAPI:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    
    Yields:
        Sesión de SQLAlchemy
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Inicializa la base de datos creando todas las tablas.
    Se debe llamar una vez al inicio de la aplicación.
    """
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas de base de datos creadas/verificadas")


def close_db():
    """Cierra el engine y todas las conexiones."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
        print("✓ Engine de SQLAlchemy cerrado")