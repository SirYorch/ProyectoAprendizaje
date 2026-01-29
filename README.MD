# Aplicación - Backend

$Karen$ en  cuenta esto routes.py ln 140 && 142
revisa esto en el matcher ln 126
        result = session.execute(text(
            "SELECT DISTINCT nombre FROM productos WHERE activo = true"
        ))
ahi le colocas con la base de datos lo que tengas para extraer parametros, es la unicaque no le estoy haciendo

los métodos ya están funcionando, o bueno igual con todo que les revisen, y faltaría que modifiquen el routes, metiendole lo de predicciones

en retrain que le metan tambien le método de reentrenamiento

no supe cómo hacer que funcione su base de datos, pero bueno en todo caso, en matcher tienen que revisar una tabla de products, porque estoy leyendo produc_id y no me acuerdo qué era realmente. y lo de las funciones ya está ahi más o menos, si quieren hacer pruebas con el chat, hay un README.mc dentro de functionMatcher, que tiene algunos ejemplos que si funcionan, igual con todo lean todo este documento antes de empezar

porque tienen que ejecutar el initializer, individualmente antes de iniciar la aplicación para que les funcione la parte de function_matcher

al final, igual se están haciendo embeddings, y palabras clave y con los ejemplos que les doy en el readme, la confianza el super alta y le coloqué un treshold de 90%


## Inicialización

Este proyecto fue hecho con una base de datos de vectores de postgresql, para su uso, necesitamos inicializar tanto la base de datos con docker en este nivel del proyecto el backend y frontend


**Backend**
ejecutar
docker compose
Backend/ai/functionMatcher/Initializer.py  **Para inicializar el matcher de funciones**
Backend/db/models.py **Para inicializar las tables de faqs**
Backend/db/Tables.py **Para rellenar las tablas**  se puede hacer nuevamente el models.py
Generar y colocar el api de google `GOOGLE_GEMINI_API_KEY={api_key}`
main.py para la aplicación
**Frontend**
cd Frontend
npm install || yarn
npm run dev || yarn dev


### Extras

Antes de iniciar ejecutar el archivo initializer.py para crear la abse de datos de function matcher

## TODO: 

--------
 
 ## Partially done 

maneje los métodos de predicción
    - Predicción stock 
    - Predicción stock con producto
    - Predicción stock con fecha
    - Predicción stock con fecha y producto

Agregar nuevos registros productos
    - en formato csv
    - Actualizar el modelo


--------



## DONE: 


función de cargar_csv



functiones a definir
    - Productos más vendidos (query)
    - Productos menos vendido (query)
    - generar reportes (csv)
    - generar reportes (excel)



function Matcher:
    - expresiones regulares para obtener los parametros
    - similaridad de coseno en funciones
    - llamado de funciones


Langchain

    - Preguntas frecuentes
    - embeddings
    - documentos


FRONTEND

    - REACT para ventanas


fastapi - conexión

    - predict all ( useLlm)
    
    - predict by product (Product, useLlm)
    
    - predict by date (Date, useLlm)
    
    - preduct by date and product (Date, product, useLlm)
    
    - chat (texto)

Conexión llm - gemini

    - naturalize (texto) -> texto

Rhubarb - gestos faciales

    - tts( audio )-> json

api tts - gratuita

    getAudio


Expresiones regulares

    - para saludos, agradecimientos y despedidas

RAG retrieval data augmentation para faqs

    - da información sobre la empresa 

        - Preguntas frecuentes

Docker

    - Base de datos