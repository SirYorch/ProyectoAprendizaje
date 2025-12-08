import pandas as pd
import uuid
import psycopg2
from psycopg2 import sql
from datetime import datetime
import os

class InventoryDataLoader:
    def __init__(self, db_config):
        """
        Inicializar el cargador de datos
        
        db_config debe contener: host, database, user, password, port
        """
        self.db_config = db_config
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Conectar a la base de datos PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            print("✓ Conexión exitosa a PostgreSQL")
        except Exception as e:
            print(f"✗ Error al conectar a PostgreSQL: {e}")
            raise
    
    def create_tables(self):
        """Crear las tablas productos y registros_inventario"""
        
        # Tabla de productos (datos maestros)
        create_productos_table = """
        CREATE TABLE IF NOT EXISTS productos (
            product_id VARCHAR(50) PRIMARY KEY,
            product_name VARCHAR(255) NOT NULL,
            product_sku VARCHAR(100) UNIQUE NOT NULL,
            category INTEGER,
            supplier_id VARCHAR(50),
            supplier_name VARCHAR(255),
            warehouse_location VARCHAR(100),
            shelf_location VARCHAR(50),
            minimum_stock_level INTEGER,
            reorder_point INTEGER,
            optimal_stock_level INTEGER,
            reorder_quantity INTEGER,
            average_daily_usage DECIMAL(10, 2),
            unit_cost DECIMAL(10, 2),
            stock_status INTEGER,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Tabla de registros de inventario (datos históricos)
        create_registros_table = """
        CREATE TABLE IF NOT EXISTS registros_inventario (
            id UUID PRIMARY KEY,
            product_id VARCHAR(50) NOT NULL,
            created_at TIMESTAMP NOT NULL,
            quantity_on_hand INTEGER,
            quantity_reserved INTEGER,
            quantity_available INTEGER,
            ventas_diarias INTEGER,
            total_value DECIMAL(12, 2),
            last_order_date DATE,
            last_stock_count_date DATE,
            batch_number VARCHAR(100),
            last_updated_at TIMESTAMP,
            notes TEXT,
            created_by_id UUID,
            FOREIGN KEY (product_id) REFERENCES productos(product_id) ON DELETE CASCADE
        );
        """
        
        # Índices para mejorar el rendimiento
        create_indexes = """
        CREATE INDEX IF NOT EXISTS idx_registros_product_id ON registros_inventario(product_id);
        CREATE INDEX IF NOT EXISTS idx_registros_created_at ON registros_inventario(created_at);
        CREATE INDEX IF NOT EXISTS idx_productos_sku ON productos(product_sku);
        """
        
        try:
            self.cursor.execute(create_productos_table)
            print("✓ Tabla 'productos' creada/verificada")
            
            self.cursor.execute(create_registros_table)
            print("✓ Tabla 'registros_inventario' creada/verificada")
            
            self.cursor.execute(create_indexes)
            print("✓ Índices creados/verificados")
            
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"✗ Error al crear tablas: {e}")
            raise
    
    def parse_date(self, date_str):
        """Parsear fechas en formato M/D/YYYY"""
        if pd.isna(date_str) or date_str == '':
            return None
        try:
            return datetime.strptime(str(date_str), '%m/%d/%Y').date()
        except:
            return None
    
    def parse_datetime(self, datetime_str):
        """Parsear datetime en formato M/D/YYYY H:MM"""
        if pd.isna(datetime_str) or datetime_str == '':
            return None
        try:
            return datetime.strptime(str(datetime_str), '%m/%d/%Y %H:%M')
        except:
            try:
                return datetime.strptime(str(datetime_str), '%m/%d/%Y')
            except:
                return None
    
    def load_from_csv(self, csv_file_path):
        """Cargar datos desde CSV y poblar las tablas"""
        
        # Leer el CSV
        print(f"\n Leyendo archivo CSV: {csv_file_path}")
        df = pd.read_csv(csv_file_path)
        print(f" {len(df)} registros encontrados en el CSV")
        
        # Extraer productos únicos
        productos_cols = [
            'product_id', 'product_name', 'product_sku', 'supplier_id',
            'supplier_name', 'warehouse_location', 'shelf_location',
            'minimum_stock_level', 'reorder_point', 'optimal_stock_level',
            'reorder_quantity', 'average_daily_usage', 'unit_cost',
            'stock_status', 'is_active'
        ]
        
        productos_df = df[productos_cols].drop_duplicates(subset=['product_id'])
        print(f"\n📦 {len(productos_df)} productos únicos encontrados")
        
        # Insertar productos
        insert_producto_query = """
        INSERT INTO productos (
            product_id, product_name, product_sku, supplier_id, supplier_name,
            warehouse_location, shelf_location, minimum_stock_level, reorder_point,
            optimal_stock_level, reorder_quantity, average_daily_usage, unit_cost,
            stock_status, is_active
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (product_id) DO UPDATE SET
            product_name = EXCLUDED.product_name,
            supplier_id = EXCLUDED.supplier_id,
            supplier_name = EXCLUDED.supplier_name,
            warehouse_location = EXCLUDED.warehouse_location,
            shelf_location = EXCLUDED.shelf_location,
            minimum_stock_level = EXCLUDED.minimum_stock_level,
            reorder_point = EXCLUDED.reorder_point,
            optimal_stock_level = EXCLUDED.optimal_stock_level,
            reorder_quantity = EXCLUDED.reorder_quantity,
            average_daily_usage = EXCLUDED.average_daily_usage,
            unit_cost = EXCLUDED.unit_cost,
            stock_status = EXCLUDED.stock_status,
            is_active = EXCLUDED.is_active,
            updated_at = CURRENT_TIMESTAMP;
        """
        
        productos_insertados = 0
        for _, row in productos_df.iterrows():
            try:
                self.cursor.execute(insert_producto_query, (
                    row['product_id'],
                    row['product_name'],
                    row['product_sku'],
                    row['supplier_id'],
                    row['supplier_name'],
                    row['warehouse_location'],
                    row['shelf_location'],
                    row['minimum_stock_level'],
                    row['reorder_point'],
                    row['optimal_stock_level'],
                    row['reorder_quantity'],
                    row['average_daily_usage'],
                    row['unit_cost'],
                    row['stock_status'],
                    row['is_active'] == True or row['is_active'] == 'True'
                ))
                productos_insertados += 1
            except Exception as e:
                print(f"✗ Error insertando producto {row['product_id']}: {e}")
        
        self.conn.commit()
        print(f"✓ {productos_insertados} productos insertados/actualizados")
        
        # Insertar registros de inventario
        insert_registro_query = """
        INSERT INTO registros_inventario (
            id, product_id, created_at, quantity_on_hand, quantity_reserved,
            quantity_available, ventas_diarias, total_value, last_order_date,
            last_stock_count_date, batch_number, last_updated_at, notes, created_by_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        """
        
        registros_insertados = 0
        for _, row in df.iterrows():
            try:
                self.cursor.execute(insert_registro_query, (
                    row['id'],
                    row['product_id'],
                    self.parse_datetime(row['created_at']),
                    row['quantity_on_hand'],
                    row['quantity_reserved'],
                    row['quantity_available'],
                    row['ventas_diarias'],
                    row['total_value'],
                    self.parse_date(row['last_order_date']),
                    self.parse_date(row['last_stock_count_date']),
                    row['batch_number'],
                    self.parse_datetime(row['last_updated_at']),
                    row['notes'] if pd.notna(row['notes']) else None,
                    row['created_by_id'] if pd.notna(row['created_by_id']) else None
                ))
                registros_insertados += 1
            except Exception as e:
                print(f"✗ Error insertando registro {row['id']}: {e}")
        
        self.conn.commit()
        print(f"✓ {registros_insertados} registros de inventario insertados")
        
        return productos_insertados, registros_insertados
    
    def agregar_registros_inventario(self, csv_file_path):
        """
        Método para SOLO agregar nuevos registros de inventario desde un CSV.
        No modifica ni inserta productos.
        
        Args:
            csv_file_path: Ruta al archivo CSV con los registros
            
        Returns:
            int: Número de registros insertados exitosamente
        """
        print(f"\nAgregando registros de inventario desde: {csv_file_path}")
        
        # Leer el CSV
        df = pd.read_csv(csv_file_path)
        print(f"{len(df)} registros encontrados en el CSV")
        
        # Query de inserción
        insert_registro_query = """
        INSERT INTO registros_inventario (
            id, product_id, created_at, quantity_on_hand, quantity_reserved,
            quantity_available, ventas_diarias, total_value, last_order_date,
            last_stock_count_date, batch_number, last_updated_at, notes, created_by_id
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        """
        
        registros_insertados = 0
        registros_duplicados = 0
        registros_error = 0
        
        for _, row in df.iterrows():
            try:
                self.cursor.execute(insert_registro_query, (
                    row['id'],
                    row['product_id'],
                    self.parse_datetime(row['created_at']),
                    row['quantity_on_hand'],
                    row['quantity_reserved'],
                    row['quantity_available'],
                    row['ventas_diarias'],
                    row['total_value'],
                    self.parse_date(row['last_order_date']),
                    self.parse_date(row['last_stock_count_date']),
                    row['batch_number'],
                    self.parse_datetime(row['last_updated_at']),
                    row['notes'] if pd.notna(row['notes']) else None,
                    row['created_by_id'] if pd.notna(row['created_by_id']) else None
                ))
                
                # Verificar si realmente se insertó (rowcount > 0)
                if self.cursor.rowcount > 0:
                    registros_insertados += 1
                else:
                    registros_duplicados += 1
                    
            except Exception as e:
                registros_error += 1
                print(f"✗ Error insertando registro {row['id']}: {e}")
        
        self.conn.commit()
        
        # Reporte de resultados
        print("\n" + "=" * 60)
        print("   RESUMEN DE CARGA DE REGISTROS")
        print("=" * 60)
        print(f"✓ Registros nuevos insertados: {registros_insertados}")
        print(f"⊘ Registros duplicados (omitidos): {registros_duplicados}")
        print(f"✗ Registros con error: {registros_error}")
        print("=" * 60)
        
        return registros_insertados
    
    def verify_data(self):
        """Verificar los datos cargados"""
        print("\n🔍 Verificación de datos:")
        
        self.cursor.execute("SELECT COUNT(*) FROM productos;")
        productos_count = self.cursor.fetchone()[0]
        print(f"  • Productos en BD: {productos_count}")
        
        self.cursor.execute("SELECT COUNT(*) FROM registros_inventario;")
        registros_count = self.cursor.fetchone()[0]
        print(f"  • Registros de inventario en BD: {registros_count}")
        
        self.cursor.execute("""
            SELECT p.product_name, COUNT(r.id) as num_registros
            FROM productos p
            LEFT JOIN registros_inventario r ON p.product_id = r.product_id
            GROUP BY p.product_id, p.product_name
            ORDER BY num_registros DESC
            LIMIT 5;
        """)
        
        print("\n  Top 5 productos con más registros:")
        for row in self.cursor.fetchall():
            print(f"    - {row[0]}: {row[1]} registros")
    
    def close(self):
        """Cerrar la conexión"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("\n✓ Conexión cerrada")

        
def agregar_nuevos_registros(csv_file):
    """
    Función independiente para agregar SOLO registros de inventario.
    Puede ser llamada desde cualquier otro script.
    
    Args:
        csv_file: Ruta al archivo CSV con los nuevos registros
        
    Returns:
        int: Número de registros insertados exitosamente
    """
    # Configuración de la base de datos
    db_config = {
        'host': 'localhost',
        'database': 'aprendizaje',
        'user': 'usuario1',
        'password': 'password1',
        'port': 5432
    }
    
    loader = InventoryDataLoader(db_config)
    
    try:
        print("\n" + "=" * 60)
        print("   AGREGAR NUEVOS REGISTROS DE INVENTARIO")
        print("=" * 60)
        
        # Conectar a la base de datos
        loader.connect()
        
        # Agregar solo registros
        registros = loader.agregar_registros_inventario(csv_file)
        
        print("\n✓ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 60 + "\n")
        
        return registros
        
    except Exception as e:
        print(f"\n✗ Error en el proceso: {e}")
        return 0
    finally:
        loader.close()


def cargarnuevosRegistros(csv_file):
    """Función para cargar nuevos registros desde un CSV dado (mantiene compatibilidad)"""
    return agregar_nuevos_registros(csv_file)
    

def main():
    """Función principal"""
    
    # Configuración de la base de datos
    db_config = {
        'host': 'localhost',
        'database': 'aprendizaje',
        'user': 'usuario1',
        'password': 'password1',
        'port': 5432
    }
    
    # Ruta al archivo CSV
    csv_file = 'files/dataset_inventario.csv'
    print("=" * 60)
    print("   CARGA DE DATOS DE INVENTARIO A POSTGRESQL")
    print("=" * 60)
    
    loader = InventoryDataLoader(db_config)
    
    try:
        # Conectar a la base de datos
        loader.connect()
        
        # Crear las tablas
        loader.create_tables()
        
        # Cargar datos desde CSV
        productos, registros = loader.load_from_csv(csv_file)
        
        # Verificar los datos
        loader.verify_data()
        
        print("\n" + "=" * 60)
        print("   ✓ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error en el proceso: {e}")
    finally:
        loader.close()


if __name__ == "__main__":
    main()