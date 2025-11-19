## Aplicación de servicio
# UPS-Cuenca-Ecuador
# Cueva-Jorge Quito-Karen Barzallo-Mateo

# Práctica 2 y 3 Servicio e integración de agentes LLM

# Herramientas utilizadas FastAPI, SQLAlchemy ORM, LLM Deepseek-r1:8b

import uvicorn
from fastapi import FastAPI
from datetime import date
from api.routes import router as http_router
from model.query_prediction import *

from fastapi.middleware.cors import CORSMiddleware

# Inicializar aplicación FastAPI
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
    
    
    # classifier = IntentClassifier()
    
    # # Cargar o entrenar modelo
    # model_path = "intent_classifier.pkl"
    # classifier.load_model(model_path)
    
    # # Probar con diferentes consultas
    # test_queries = [
    #     "cual producto se va a agotar más pronto?",
    #     "cuánto stock tendrá producto A el 15 de mayo",
    #     "cómo estará el inventario el 20 de junio",
    #     "cuándo se agotará el producto PROD-002",
    #     "cuándo se agotará el producto PROD-001",
    #     "cuándo se agotará el producto PROD-003",
    # ]
    
    # print("\n" + "="*60)
    # print("Probando clasificador KNN:")
    # print("="*60)
    
    # for query in test_queries:
    #     endpoint, confidence, label = classifier.predict_intent(query)
    #     params = classifier.extract_parameters(query, endpoint)
        
    #     print(f"\nConsulta: '{query}'")
    #     print(f"  → Endpoint: {endpoint}")
    #     print(f"  → Confianza: {confidence:.2%}")
    #     print(f"  → Parámetros: {params}")
    
    # print("\n" + "="*60 + "\n")

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    
    
    