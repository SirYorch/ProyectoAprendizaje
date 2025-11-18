## Aplicación de servicio
# UPS-Cuenca-Ecuador
# Cueva-Jorge Quito-Karen Barzallo-Mateo

# Práctica 2 y 3 Servicio e integración de agentes LLM

# Herramientas utilizadas FastAPI, SQLAlchemy ORM, LLM Deepseek-r1:8b

import uvicorn
from fastapi import FastAPI
from datetime import date
from api.routes import router as http_router

# Inicializar aplicación FastAPI
app = FastAPI(
    title="Agente de predicción de stock",
    description="API para predicción de stock y manejo de agentes",
    version="1.0.0"
)

# Registrar rutas HTTP
app.include_router(http_router, prefix="/api", tags=["predicciones"])

        
        
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    
    