import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://usuario1:password1@localhost:5432/aprendizaje"

engine = create_engine(DATABASE_URL)

def load_inventory_from_db():
    query = """
        SELECT
                r.product_id,
                r.created_at,
                r.quantity_on_hand,
                r.quantity_reserved,
                reorder_point,
                optimal_stock_level,
                average_daily_usage,
                stock_status,
                p.category,
                r.quantity_available
            FROM registros_inventario r
            INNER JOIN productos p
                ON r.product_id = p.product_id
            ORDER BY r.product_id, r.created_at;
    """

    df = pd.read_sql(query, engine, parse_dates=["created_at"])
    return df


def load_inventory_dataset():

    df = load_inventory_from_db()
    
    # Asegurarse de que las columnas de fecha estén en formato datetime
    df['created_at'] = pd.to_datetime(df['created_at'])
    df = df.sort_values(["product_id", "created_at"])
    
    # Variables temporales
    df["anio"] = df["created_at"].dt.year
    df["mes"] = df["created_at"].dt.month
    df["dia_semana"] = df["created_at"].dt.dayofweek
    df["fin_de_semana"] = (df["dia_semana"] >= 5).astype(int)

    # Asegurar category
    if "category" not in df.columns:
        df["category"] = 0

    # Reemplazar NaN en columnas clave
    for col in ["quantity_available", "quantity_on_hand", "quantity_reserved",
                "reorder_point", "optimal_stock_level", "average_daily_usage",
                "stock_status", "category"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)
    
    cols_necesarias = [
        "product_id", "created_at", "category", "quantity_available", "quantity_on_hand", 
        "quantity_reserved", "reorder_point", "optimal_stock_level",
        "average_daily_usage", "stock_status", "anio", "mes", 
        "dia_semana", "fin_de_semana"
    ]

    cols_existentes = [col for col in cols_necesarias if col in df.columns]
    
    return df[cols_existentes]
