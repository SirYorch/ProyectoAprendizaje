from db.vector import add_batch_embeddings, create_vector_tables
from langchain_ollama import OllamaEmbeddings
emb = OllamaEmbeddings(model="nomic-embed-text")


items_intent_1 = [
    {"text": "cuánto stock tendrá producto X el 15 de mayo", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "stock de producto Y para el 2025-06-10", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cuántas unidades de producto Z habrá el próximo mes", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "predicción de stock de producto A en fecha específica", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "stock producto B para el día 20", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cantidad de producto C el 15 de marzo", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "unidades de producto D en una fecha", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "stock futuro de producto E", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cuánto quedará de producto F el día X", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "predicción producto G fecha Y", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cuánto stock tendrá el producto X en fecha Y", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cantidad prevista para producto X el día 15", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "qué unidades habrá del producto A el próximo viernes", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "proyección de stock de producto Z para junio", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cuántas existencias tendrá artículo B en fecha futura", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "stock esperado de producto C el día 10", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cuánto inventario habrá de item X el mes siguiente", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cuántas unidades quedarán de ese producto el 2025-01-01", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "predicción del stock para producto X", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "unidades futuras del artículo Y", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "proyección exacta del stock del producto A", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cuánto queda del producto Z en la fecha dada", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "previsión de existencias del producto C", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "qué cantidad habrá del artículo X en tal fecha", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "stock disponible para producto Y en fecha señalada", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cuánto inventario tendrá item F el día indicado", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cuántas unidades habrá del producto solicitado", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "proyección futura para referencia X", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cuál será el stock del producto en X fecha", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "unidades futuras estimadas del producto C", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "inventario proyectado de ese artículo", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cantidad futura del producto A", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "predicción del nivel de stock del producto B", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "unidades estimadas de referencia X para fecha Y", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cuánto stock habrá el próximo mes del producto Z", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "estimación de existencias futuras", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cuántos quedan en tal fecha", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "unidades del producto X en el día Y", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "inventario estimado para producto A", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cantidad disponible en el futuro para el producto B", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "proyección del inventario para una fecha concreta", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cuál será la cantidad disponible del artículo X", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "predicción de cuántas unidades quedarán", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "estimación futura de stock", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "cuánto quedará del producto en fecha futura", "group_name": "prediccion", "intent": "predict_product_stock"},
    {"text": "nivel de stock futuro del artículo", "group_name": "prediccion", "intent": "predict_product_stock"},
]

intent_2_items = [
    {"text": "cómo estará el inventario el 20 de junio", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "estado del inventario para el 2025-07-15", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "todos los productos en fecha X", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "inventario completo el próximo mes", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "qué productos y cantidades habrá el día 30", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "predicción de todo el stock para una fecha", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "estado general del inventario en fecha", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "todos los stocks en el futuro", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "inventario total el día X", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "predicción completa para fecha Y", "group_name": "prediccion", "intent": "predict_date"},

    {"text": "inventario total proyectado para fecha X", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "dime todo el inventario disponible el próximo lunes", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "qué habrá en todo el almacén en esa fecha", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "estado completo de existencias para futuro", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "inventario general para día especificado", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "stocks futuros de todos los productos", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "cómo estará todo el inventario en fecha determinada", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "cantidad total por producto en el futuro", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "listado de inventario futuro", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "predicción del inventario completo", "group_name": "prediccion", "intent": "predict_date"},

    {"text": "qué habrá en almacén para el mes siguiente", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "panorama del inventario en tal fecha", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "inventario proyectado del almacén", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "qué cantidades totales habrá en esa fecha", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "dame todos los productos y sus unidades futuras", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "inventario completo del día X", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "existencias totales en el futuro", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "stock global para fecha específica", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "estado del sistema de inventario futuro", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "total de existencias para un día", "group_name": "prediccion", "intent": "predict_date"},

    {"text": "cómo lucirá todo el inventario para mañana", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "predicción del inventario general", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "cuál será el inventario total en X fecha", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "lista completa de productos y existencias futuras", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "cuántas unidades habrá de cada artículo", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "inventario completo estimado", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "existencias proyectadas del almacén entero", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "visión completa del stock en fecha dada", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "disponibilidad total proyectada", "group_name": "prediccion", "intent": "predict_date"},
    {"text": "resumen de inventario para día X", "group_name": "prediccion", "intent": "predict_date"},
]


intent_3_items = [
    {"text": "¿cuándo se va a acabar el stock de este producto?", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "dime la fecha estimada de agotamiento del producto", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "¿para qué día ya no habrá unidades disponibles?", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "quiero saber cuándo se quedará sin existencias este artículo", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "fecha en la que el artículo llegará a cero inventario", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "¿cuándo se va a terminar este producto?", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "proyección de fecha de quiebre de stock para el producto", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "en qué día el sistema calcula que se agotará este ítem", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "quiero saber el día exacto en que se quedará sin inventario", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "estimación de agotamiento del stock del producto", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},

    {"text": "para cuándo se pronostica que este artículo se quede sin stock", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "muéstrame la fecha en la que ya no habrá existencias", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "según el modelo, ¿cuándo se agota este producto?", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "fecha prevista de agotamiento del inventario del artículo", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "hasta qué día alcanzan las existencias de este producto", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "cuándo quedará en cero el stock disponible", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "indicador de fecha de quiebre del inventario", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "necesito saber cuándo ya no habrá stock del producto", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "qué día dejará de estar disponible este producto", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "hasta cuándo durará el inventario actual de este producto", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},

    {"text": "para qué fecha exacta se espera el agotamiento del stock", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "¿cuándo se estima que este artículo llegue a inventario cero?", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "fecha proyectada de fin de inventario del producto seleccionado", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "quiero ver el día en que ya no quede nada en stock", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "predicción de agotamiento total de existencias", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "muéstrame el pronóstico de cuándo se quedará sin stock", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "en qué momento se terminarán las unidades disponibles", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "estimación de cuándo terminará el stock vigente", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "cuándo se proyecta que el artículo deje de estar disponible", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "dime la fecha límite del inventario de este producto", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},

    {"text": "¿hasta qué día tendremos stock para este ítem?", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "qué fecha marca el agotamiento según el modelo", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "cuándo se producirá el quiebre de stock de este producto", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "¿para qué día ya no habrá disponibilidad de este artículo?", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "proyección del día en que se agote el inventario", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "quiero saber cuándo llegará a cero la cantidad disponible", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "fecha en que este artículo dejará de estar en stock", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "para qué día exacto quedará sin inventario este producto", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "cantidad prevista hasta agotarse y fecha límite", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
    {"text": "cuándo estima el sistema que se terminará este producto", "group_name": "prediccion", "intent": "predict_out_of_stock_date"},
]

intent_4_items = [
    {"text": "¿cómo estará el stock total más adelante?", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "quiero saber la proyección general del inventario", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "dime el estado futuro de todo el stock", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "¿cómo se verá el inventario completo según la predicción?", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "proyección del stock total del almacén", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "estado global del inventario en el futuro", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "inventario total proyectado sin filtros", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "cómo estará todo el almacén más adelante", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "muéstrame una predicción de todo el stock", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "¿qué cantidades totales voy a tener en inventario?", "group_name": "prediccion", "intent": "predict_total_stock"},

    {"text": "proyección general del sistema de inventario", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "quiero ver el inventario completo en el futuro", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "¿cómo se distribuye el stock total próximamente?", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "estado global estimado del almacén", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "cuánto inventario habrá en general más adelante", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "resumen total del stock futuro", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "vista general del inventario estimado", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "proyección del inventario completo sin detalles", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "dime cómo se ve el stock general según el modelo", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "¿qué nivel de stock total tendré?", "group_name": "prediccion", "intent": "predict_total_stock"},

    {"text": "predicción del inventario general completo", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "inventario global futuro según el modelo", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "cuál será el total de existencias proyectadas", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "necesito ver el panorama completo del inventario", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "quiero el estado estimado del stock total", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "cómo estará la disponibilidad global en el futuro", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "cantidad total de inventario proyectado", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "dime el inventario total del almacén en general", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "inventario completo estimado sin filtros", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "cómo lucirá el inventario total próximamente", "group_name": "prediccion", "intent": "predict_total_stock"},

    {"text": "predicción de existencias totales del almacén", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "cuál será el inventario general disponible", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "dame un resumen del inventario proyectado", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "qué cantidades globales habrá en stock", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "inventario futuro en términos generales", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "panorama global del stock proyectado", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "cómo estará distribuido todo el inventario", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "cantidad general estimada del inventario", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "estado completo del inventario para más adelante", "group_name": "prediccion", "intent": "predict_total_stock"},
    {"text": "cómo estará el inventario total según las predicciones", "group_name": "prediccion", "intent": "predict_total_stock"},
]

saludo_general = [
    {"text": "hola", "group_name": "saludo", "intent": "saludo_general"},
    {"text": "hola amigo", "group_name": "saludo", "intent": "saludo_general"},
    {"text": "hola chatbot", "group_name": "saludo", "intent": "saludo_general"},
    {"text": "hola que tal", "group_name": "saludo", "intent": "saludo_general"},
    {"text": "buenas", "group_name": "saludo", "intent": "saludo_general"},
    {"text": "buenas que tal", "group_name": "saludo", "intent": "saludo_general"},
    {"text": "hey", "group_name": "saludo", "intent": "saludo_general"},
    {"text": "hey hola", "group_name": "saludo", "intent": "saludo_general"},
    {"text": "saludos", "group_name": "saludo", "intent": "saludo_general"},
    {"text": "qué tal", "group_name": "saludo", "intent": "saludo_general"},
]
saludo_buenos_dias = [
    {"text": "buenos días", "group_name": "saludo", "intent": "saludo_buenos_dias"},
    {"text": "buen día", "group_name": "saludo", "intent": "saludo_buenos_dias"},
    {"text": "muy buenos días", "group_name": "saludo", "intent": "saludo_buenos_dias"},
    {"text": "hola buenos días", "group_name": "saludo", "intent": "saludo_buenos_dias"},
    {"text": "qué tal buenos días", "group_name": "saludo", "intent": "saludo_buenos_dias"},
    {"text": "bendecido día", "group_name": "saludo", "intent": "saludo_buenos_dias"},
    {"text": "buen día cómo estás", "group_name": "saludo", "intent": "saludo_buenos_dias"},
]
saludo_buenas_tardes = [
    {"text": "buenas tardes", "group_name": "saludo", "intent": "saludo_buenas_tardes"},
    {"text": "muy buenas tardes", "group_name": "saludo", "intent": "saludo_buenas_tardes"},
    {"text": "hola buenas tardes", "group_name": "saludo", "intent": "saludo_buenas_tardes"},
    {"text": "qué tal buenas tardes", "group_name": "saludo", "intent": "saludo_buenas_tardes"},
    {"text": "buenas tardes cómo te va", "group_name": "saludo", "intent": "saludo_buenas_tardes"},
]
saludo_buenas_noches = [
    {"text": "buenas noches", "group_name": "saludo", "intent": "saludo_buenas_noches"},
    {"text": "muy buenas noches", "group_name": "saludo", "intent": "saludo_buenas_noches"},
    {"text": "hola buenas noches", "group_name": "saludo", "intent": "saludo_buenas_noches"},
    {"text": "qué tal buenas noches", "group_name": "saludo", "intent": "saludo_buenas_noches"},
    {"text": "buenas noches cómo estás", "group_name": "saludo", "intent": "saludo_buenas_noches"},
]
saludo_informal = [
    {"text": "holi", "group_name": "saludo", "intent": "saludo_informal"},
    {"text": "holis", "group_name": "saludo", "intent": "saludo_informal"},
    {"text": "que más", "group_name": "saludo", "intent": "saludo_informal"},
    {"text": "que más pues", "group_name": "saludo", "intent": "saludo_informal"},
    {"text": "qué onda", "group_name": "saludo", "intent": "saludo_informal"},
    {"text": "cómo va todo", "group_name": "saludo", "intent": "saludo_informal"},
    {"text": "cómo andas", "group_name": "saludo", "intent": "saludo_informal"},
    {"text": "qué haces", "group_name": "saludo", "intent": "saludo_informal"},
    {"text": "holaaa", "group_name": "saludo", "intent": "saludo_informal"},
    {"text": "holaaa qué tal", "group_name": "saludo", "intent": "saludo_informal"},
]
despedida = [
    {"text": "adiós", "group_name": "saludo", "intent": "despedida"},
    {"text": "chao", "group_name": "saludo", "intent": "despedida"},
    {"text": "hasta luego", "group_name": "saludo", "intent": "despedida"},
    {"text": "nos vemos", "group_name": "saludo", "intent": "despedida"},
    {"text": "gracias, eso es todo", "group_name": "saludo", "intent": "despedida"},
    {"text": "me voy", "group_name": "saludo", "intent": "despedida"},
    {"text": "hasta mañana", "group_name": "saludo", "intent": "despedida"},
    {"text": "bye", "group_name": "saludo", "intent": "despedida"},
    {"text": "thankius chauuu", "group_name": "saludo", "intent": "despedida"},
]


if __name__ == "__main__":
    print("=== Creando tablas si no existen ===")
    create_vector_tables()

    items = []

    print("=== Generando embeddings reales ===")
    for data in despedida:
        vector = emb.embed_query(data["text"])      

        items.append({
            "text": data["text"],
            "group_name": data["group_name"],
            "intent": data["intent"],
            "embedding": vector,
            "meta": {"tipo": "intent", "descripcion": "despedida"}
        })

    print("=== Insertando en base ===")
    added = add_batch_embeddings(items)
    print("✓ Insertados:", added)