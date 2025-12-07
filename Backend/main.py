import uvicorn
from fastapi import FastAPI
# from endpoint.routes import router as http_router
from endpoint.routes import router as http_router
from datetime import date
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Agente de predicción de stock",
    description="API para predicción de stock y manejo de agentes",
    version="1.0.0"
)

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(http_router, prefix="/api", tags=["predicciones"])


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    