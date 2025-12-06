from llm.agent import check_regex_response # Ajusta el import según tu carpeta

mensajes_prueba = [
    "Hola como estas",
    "buenos dias quiero saber el stock",
    "muchas gracias ñaño",
    "bueno chao me voy",
    "predecir stock de la laptop" # Este debería dar None
]

print("--- PROBANDO REGEX ---")
for msg in mensajes_prueba:
    respuesta = check_regex_response(msg)
    print(f"Usuario: '{msg}'")
    print(f"Bot: {respuesta if respuesta else '>> PASAR A LLM/RAG'}")
    print("-" * 20)