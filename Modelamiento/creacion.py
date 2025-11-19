# ======================================================
# 💼 DATASET SECUENCIAL REALISTA DE INVENTARIO RETAIL 
# (ajustado: menor stock y rotación en alta gama, sin floats indeseados)
# ======================================================

import pandas as pd
import numpy as np
import uuid
import random
from datetime import datetime, timedelta

# --------------------------------------
# CONFIGURACIÓN GLOBAL
# --------------------------------------
np.random.seed(42)
random.seed(42)

dias_totales = 14  # días simulados
fecha_inicio = datetime(2025, 10, 20)

# Productos y proveedores
productos = [
    {"name": "Laptop Dell Inspiron 15", "sku": "LAP-DELL-001", "cost": 650.00},
    {"name": "Mouse Logitech MX Master 3", "sku": "MOU-LOG-003", "cost": 99.99},
    {"name": "Teclado Mecánico Corsair K70", "sku": "TEC-COR-005", "cost": 149.99},
    {"name": "Monitor LG UltraWide 34''", "sku": "MON-LG-002", "cost": 480.00},
    {"name": "Auriculares Sony WH-1000XM5", "sku": "AUR-SON-008", "cost": 349.99},
    {"name": "Webcam Logitech C920", "sku": "WEB-LOG-011", "cost": 79.99},
    {"name": "Hub USB-C Anker 7 en 1", "sku": "HUB-ANK-015", "cost": 59.99},
    {"name": "Disco SSD Samsung 1TB", "sku": "SSD-SAM-020", "cost": 89.99},
    {"name": "Memoria RAM Corsair 16GB", "sku": "RAM-COR-025", "cost": 74.99},
    {"name": "Router WiFi 6 TP-Link", "sku": "ROU-TPL-030", "cost": 129.99},
    {"name": "Impresora HP LaserJet Pro", "sku": "IMP-HP-035", "cost": 299.99},
    {"name": "Tablet Samsung Galaxy Tab S8", "sku": "TAB-SAM-040", "cost": 549.99},
    {"name": "Cámara Web Razer Kiyo", "sku": "CAM-RAZ-045", "cost": 99.99},
    {"name": "Micrófono Blue Yeti", "sku": "MIC-BLU-050", "cost": 129.99},
    {"name": "Switch de Red Cisco 8 Puertos", "sku": "SWI-CIS-055", "cost": 189.99},
    {"name": "Cargador Multipuerto Anker", "sku": "CAR-ANK-060", "cost": 39.99},
    {"name": "Cable HDMI 4K Premium 2m", "sku": "CAB-HDM-065", "cost": 19.99},
    {"name": "Soporte para Laptop Ajustable", "sku": "SOP-LAP-070", "cost": 34.99},
    {"name": "Mochila para Laptop Targus", "sku": "MOC-TAR-075", "cost": 59.99},
    {"name": "Protector de Pantalla Universal", "sku": "PRO-PAN-080", "cost": 12.99}
]

proveedores = [
    {"id": "PROV-001", "name": "TechDistributor SA"},
    {"id": "PROV-002", "name": "ElectroSupply Corp"},
    {"id": "PROV-003", "name": "GlobalTech Imports"},
    {"id": "PROV-004", "name": "CompuWholesale Ltd"}
]

almacenes = ["Warehouse A", "Warehouse B", "Warehouse C"]
pasillos = ["A1", "A2", "B1", "B2", "C1", "C2", "D1", "D2"]
usuarios_sistema = [str(uuid.uuid4()) for _ in range(5)]

notas_opciones = [
    None, "Recepción de mercancía del proveedor", "Ajuste manual de inventario",
    "Conteo físico realizado", "Revisar próximamente", "Stock óptimo",
    "Pendiente auditoría", "Producto en promoción",
]

categorias = {
    "alta_gama": ["Laptop", "Tablet", "Monitor", "Impresora"],
    "media": ["Auriculares", "Micrófono", "Router", "Switch", "SSD", "RAM"],
    "accesorios": ["Mouse", "Teclado", "Cable", "Hub", "Soporte", "Mochila", "Protector", "Cargador", "Webcam", "Cámara"]
}

# --------------------------------------
# FUNCIÓN DE SIMULACIÓN REALISTA
# --------------------------------------
def generar_secuencia_realista(prod, idx):
    fechas = [fecha_inicio + timedelta(days=i) for i in range(dias_totales)]
    proveedor = proveedores[idx % len(proveedores)]
    warehouse = random.choice(almacenes)
    shelf = random.choice(pasillos)

    # 🔹 Configuración según categoría
    if any(k in prod["name"] for k in categorias["alta_gama"]):
        stock_inicial = random.randint(10, 20)
        max_venta = random.randint(1, 2)
        prob_venta = random.uniform(0.05, 0.15)
        prod["category"] = 2
    elif any(k in prod["name"] for k in categorias["media"]):
        stock_inicial = random.randint(30, 80)
        max_venta = random.randint(2, 4)
        prob_venta = random.uniform(0.25, 0.45)
        prod["category"] = 1    
    else:
        stock_inicial = random.randint(100, 400)
        max_venta = random.randint(4, 10)
        prob_venta = random.uniform(0.6, 0.9)
        prod["category"] = 0
    stock = [stock_inicial]
    notas, batch_numbers, last_order_dates, last_stock_counts, last_updates = [], [], [], [], []
    ultima_reposicion = fechas[0] - timedelta(days=random.randint(10, 60))

    for d in range(1, dias_totales):
        fecha_actual = fechas[d]
        base_salida = np.random.poisson(lam=random.uniform(1, max_venta))
        if fecha_actual.weekday() >= 5:
            base_salida = int(base_salida * 1.8)

        mes = fecha_actual.month
        if mes == 11 and 25 <= fecha_actual.day <= 30:
            base_salida *= 2.5
        elif mes == 12:
            base_salida *= 2.0
        elif mes in [1, 2]:
            base_salida *= 0.6
        elif mes == 9:
            base_salida *= 1.8

        salida = int(round(base_salida)) if random.random() < prob_venta else 0
        reposicion = 0
        nota = None

        if any(k in prod["name"] for k in categorias["alta_gama"]):
            if stock[-1] < 5 and random.random() < 0.1:
                reposicion = random.randint(5, 15)
                nota = "Reabastecimiento limitado (alta gama)"
        else:
            if stock[-1] < 50 and random.random() < 0.25:
                reposicion = random.randint(40, 150)
                nota = "Reabastecimiento urgente"

        nuevo_stock = max(0, stock[-1] - salida + reposicion)
        stock.append(int(round(nuevo_stock)))
        notas.append(nota)

        batch = (
            f"BATCH-{fecha_actual.year}{fecha_actual.month:02d}-{random.randint(1000,9999)}"
            if reposicion > 0 else batch_numbers[-1] if batch_numbers else f"BATCH-{fecha_inicio.year}{fecha_inicio.month:02d}-{random.randint(1000,9999)}"
        )
        batch_numbers.append(batch)
        last_order_dates.append(ultima_reposicion)
        last_stock_counts.append(fecha_actual - timedelta(days=random.choice([7, 14, 30])))
        last_updates.append(fecha_actual + timedelta(minutes=random.randint(1, 120)))

    notas.insert(0, None)
    batch_numbers.insert(0, batch_numbers[0])
    last_order_dates.insert(0, ultima_reposicion)
    last_stock_counts.insert(0, fechas[0] - timedelta(days=7))
    last_updates.insert(0, fechas[0] + timedelta(minutes=5))

    quantity_reserved = [random.randint(0, q // 3) for q in stock]
    quantity_available = [max(0, q - r) for q, r in zip(stock, quantity_reserved)]
    minimum_stock_level = [random.randint(5, 30) for _ in fechas]
    reorder_point = [m + random.randint(5, 20) for m in minimum_stock_level]
    optimal_stock_level = [r + random.randint(5, 40) for r in reorder_point]
    reorder_quantity = [max(0, o - q) for o, q in zip(optimal_stock_level, stock)]
    average_daily_usage = (
        pd.Series(stock).diff().abs().rolling(window=7, min_periods=1).mean().round(2)
    )
    total_value = [round(q * prod["cost"], 2) for q in stock]

    stock_status = []
    for q, m, r in zip(stock, minimum_stock_level, reorder_point):
        if q == 0:
            stock_status.append(2) # agotado
        elif q < m:
            stock_status.append(3) # bajo
        elif q < r:
            stock_status.append(4) # por debajo del punto de reorden
        else:
            stock_status.append(1) # normal

    df = pd.DataFrame({
        "id": [str(uuid.uuid4()) for _ in fechas],
        "created_at": fechas,
        "product_id": f"PROD-{idx+1:03d}",
        "product_name": prod["name"],
        "product_sku": prod["sku"],
        "category": prod["category"],
        "supplier_id": proveedor["id"],
        "supplier_name": proveedor["name"],
        "warehouse_location": warehouse,
        "shelf_location": shelf,
        "quantity_on_hand": stock,
        "quantity_reserved": quantity_reserved,
        "quantity_available": quantity_available,
        "minimum_stock_level": minimum_stock_level,
        "reorder_point": reorder_point,
        "optimal_stock_level": optimal_stock_level,
        "reorder_quantity": reorder_quantity,
        "average_daily_usage": average_daily_usage,
        "unit_cost": prod["cost"],
        "total_value": total_value,
        "stock_status": stock_status,
        "last_order_date": last_order_dates,
        "last_stock_count_date": last_stock_counts,
        "batch_number": batch_numbers,
        "last_updated_at": last_updates,
        "notes": notas,
        "is_active": [True] * len(fechas),
        "created_by_id": [random.choice(usuarios_sistema) for _ in fechas],
    })

    # 🔧 LIMPIEZA FINAL: eliminar floats indeseados
    cols_enteras = [
        "quantity_on_hand", "quantity_reserved", "quantity_available",
        "minimum_stock_level", "reorder_point", "optimal_stock_level",
        "reorder_quantity", "stock_status"
    ]
    for c in cols_enteras:
        df[c] = df[c].astype(int)

    df["average_daily_usage"] = df["average_daily_usage"].round(2)
    df["total_value"] = df["total_value"].round(2)

    return df

# --------------------------------------
# CREAR DATASET COMPLETO
# --------------------------------------
df_total = pd.concat(
    [generar_secuencia_realista(prod, i) for i, prod in enumerate(productos)],
    ignore_index=True
)

# --------------------------------------
# GUARDAR RESULTADO
# --------------------------------------
df_total.to_csv("data20oct-2nov.csv", index=False)
print(f"✅ Dataset generado con {len(df_total):,} filas ({len(productos)} productos × {dias_totales} días)")
print(df_total.head(10))
