from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    String, DateTime, Float, Integer, Boolean
)
from sqlalchemy.exc import SQLAlchemyError

# -------------------------------------------------------------------
# CONFIGURA TU BASE
# -------------------------------------------------------------------
DATABASE_URL = "postgresql+psycopg2://usuario1:password1@localhost:5432/aprendizaje"

engine = create_engine(DATABASE_URL)

# Cambia "public" si tu tabla está en otro schema
metadata = MetaData(schema="public")

# -------------------------------------------------------------------
# DEFINICIÓN DE LA TABLA
# -------------------------------------------------------------------
stock_predictions_cache = Table(
    "stock_predictions_cache",
    metadata,

    # PRIMARY KEY COMPUESTA (NECESARIA PARA ON CONFLICT)
    Column("product_id", String, primary_key=True),
    Column("prediction_date", DateTime, primary_key=True),

    # CAMPOS NUMÉRICOS
    Column("predicted_stock", Float),
    Column("predicted_demand", Float),
    Column("quantity_on_hand", Float),
    Column("quantity_reserved", Float),
    Column("reorder_point", Float),
    Column("optimal_stock_level", Float),
    Column("average_daily_usage", Float),

    # CAMPOS CATEGÓRICOS
    Column("stock_status", Integer),   # Cambia a String si quieres texto
    Column("dia_semana", Integer),
    Column("fin_de_semana", Integer),
    Column("category", String),        # pon String si es texto, Integer si son códigos

    # TIMESTAMP
    Column("created_at", DateTime),
)

# -------------------------------------------------------------------
# CREAR LA TABLA
# -------------------------------------------------------------------
try:
    print("Creando tabla stock_predictions_cache si no existe...")
    metadata.create_all(engine)
    print("✔ Tabla creada correctamente.")
except SQLAlchemyError as e:
    print("❌ Error al crear la tabla:", e)
