from flask import Flask, request, jsonify, Response, stream_with_context
import requests
import json
from datetime import datetime, timedelta
import random

app = Flask(__name__)

# Configuración de DeepSeek R1 local (Ollama)
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "deepseek-r1:8b"

# ==================== MÉTODOS DE NEGOCIO ====================

def predict_stockout(fecha=None):
    """
    Predice qué elemento se agotará más pronto
    """
    if fecha is None:
        fecha = datetime.now()
    
    # Simulación de datos de inventario
    inventory = [
        {"producto": "Laptop Dell XPS", "stock_actual": 5, "consumo_diario": 2, "dias_restantes": 2.5},
        {"producto": "Mouse Logitech", "stock_actual": 45, "consumo_diario": 3, "dias_restantes": 15},
        {"producto": "Teclado Mecánico", "stock_actual": 8, "consumo_diario": 4, "dias_restantes": 2},
        {"producto": "Monitor 27 pulgadas", "stock_actual": 12, "consumo_diario": 1, "dias_restantes": 12},
        {"producto": "Cable HDMI", "stock_actual": 3, "consumo_diario": 2, "dias_restantes": 1.5},
    ]
    
    # Ordenar por días restantes
    inventory_sorted = sorted(inventory, key=lambda x: x['dias_restantes'])
    critico = inventory_sorted[0]
    
    fecha_agotamiento = fecha + timedelta(days=critico['dias_restantes'])
    
    return {
        "producto_critico": critico['producto'],
        "stock_actual": critico['stock_actual'],
        "consumo_diario": critico['consumo_diario'],
        "dias_restantes": critico['dias_restantes'],
        "fecha_agotamiento_estimada": fecha_agotamiento.strftime("%Y-%m-%d"),
        "todos_productos": inventory_sorted[:3],  # Top 3 críticos
        "fecha_consulta": fecha.strftime("%Y-%m-%d")
    }

def predict_sales(periodo="mes"):
    """
    Predice las ventas para el próximo período
    """
    # Simulación de datos históricos y predicción
    ventas_historicas = {
        "enero": 45000,
        "febrero": 52000,
        "marzo": 48000,
        "abril": 55000,
        "mayo": 62000
    }
    
    # Calcular tendencia
    valores = list(ventas_historicas.values())
    promedio = sum(valores) / len(valores)
    tendencia = (valores[-1] - valores[0]) / len(valores)
    
    prediccion_base = valores[-1] + tendencia
    margen_error = prediccion_base * 0.15
    
    return {
        "periodo_prediccion": f"Próximo {periodo}",
        "venta_predicha": round(prediccion_base, 2),
        "rango_minimo": round(prediccion_base - margen_error, 2),
        "rango_maximo": round(prediccion_base + margen_error, 2),
        "confianza": "85%",
        "tendencia": "creciente" if tendencia > 0 else "decreciente",
        "crecimiento_mensual": round(tendencia, 2),
        "ventas_historicas": ventas_historicas,
        "factores_clave": [
            "Temporada alta detectada",
            "Incremento en demanda online",
            "Nuevos productos lanzados"
        ]
    }

# Mapeo de intenciones a funciones
AVAILABLE_FUNCTIONS = {
    "predict_stockout": predict_stockout,
    "predict_sales": predict_sales
}

# ==================== ANÁLISIS DE INTENCIÓN ====================

def analyze_intent(user_message):
    """
    Usa DeepSeek R1 para analizar la intención y extraer parámetros
    """
    # Primero intenta con reglas simples (más rápido)
    message_lower = user_message.lower()
    
    # Reglas de detección rápida
    stockout_keywords = ['agotar', 'stock', 'inventario', 'falta', 'acaba', 'acabar', 'agota']
    sales_keywords = ['venta', 'vender', 'ingreso', 'proyección', 'comercial', 'ventas']
    
    if any(kw in message_lower for kw in stockout_keywords):
        return {
            "function": "predict_stockout",
            "params": {},
            "confidence": 0.90,
            "method": "rules"
        }
    
    if any(kw in message_lower for kw in sales_keywords):
        return {
            "function": "predict_sales",
            "params": {"periodo": "mes"},
            "confidence": 0.90,
            "method": "rules"
        }
    
    # Si no hay match con reglas, usa IA (más lento pero más preciso)
    prompt = f"""Analiza esta consulta y responde SOLO con JSON:

Consulta: "{user_message}"

Funciones:
- predict_stockout: agotamiento/stock/inventario
- predict_sales: ventas/ingresos

JSON:
{{
    "function": "predict_stockout",
    "params": {{}},
    "confidence": 0.95
}}"""

    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.1,
            "options": {
                "num_predict": 100  # Limitar tokens para respuesta más rápida
            }
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '').strip()
            
            # Limpiar respuesta (remover markdown si existe)
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            intent_data = json.loads(response_text)
            intent_data['method'] = 'ai'
            return intent_data
        else:
            return {"function": "none", "params": {}, "confidence": 0.0, "method": "error"}
            
    except Exception as e:
        print(f"Error analizando intención con IA: {e}")
        # Si falla la IA, devolver sin función
        return {"function": "none", "params": {}, "confidence": 0.0, "method": "error"}

def naturalize_response(function_name, function_result, user_message):
    """
    Convierte el resultado estructurado a lenguaje natural usando SIEMPRE IA
    """
    prompt = f"""Eres un asistente empresarial que analiza datos y responde de forma natural y conversacional.

Pregunta del usuario: "{user_message}"

Análisis ejecutado: {function_name}

Datos obtenidos:
{json.dumps(function_result, indent=2, ensure_ascii=False)}

INSTRUCCIONES:
- Responde en español de forma natural y conversacional
- NO uses templates ni estructuras fijas
- NO uses emojis ni formato markdown excesivo
- Explica los datos de forma clara pero variada
- Adapta tu estilo a la pregunta específica
- Sé directo y útil
- Incluye insights y recomendaciones cuando sea relevante

Genera una respuesta única y natural:"""

    try:
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.8  # Mayor creatividad
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=90)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('response', '').strip()
        else:
            return "Lo siento, no pude procesar la respuesta correctamente."
            
    except Exception as e:
        return f"Error generando respuesta: {str(e)}"

# ==================== ENDPOINTS ====================

@app.route('/predict', methods=['POST'])
def predict():
    """
    Endpoint inteligente que analiza, ejecuta y responde en lenguaje natural
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "error": "Debe proporcionar un 'message' en el JSON"
            }), 400
        
        user_message = data['message']
        
        # Paso 1: Analizar intención
        print(f"📝 Analizando: {user_message}")
        intent = analyze_intent(user_message)
        print(f"🎯 Intención detectada: {intent}")
        
        # Si NO detecta función específica, responde normalmente con IA
        if intent['function'] == 'none' or intent['confidence'] < 0.5:
            print(f"💬 Sin función específica, respondiendo con chat normal...")
            
            payload = {
                "model": MODEL_NAME,
                "prompt": user_message,
                "stream": False
            }
            
            response = requests.post(OLLAMA_URL, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                return jsonify({
                    "success": True,
                    "response": result.get('response', ''),
                    "metadata": {
                        "function_executed": "chat",
                        "intent_detection": intent
                    }
                })
            else:
                return jsonify({
                    "error": "Error al generar respuesta"
                }), 500
        
        # Paso 2: Ejecutar función
        function_name = intent['function']
        function_params = intent.get('params', {})
        
        if function_name not in AVAILABLE_FUNCTIONS:
            return jsonify({
                "success": False,
                "message": f"Función '{function_name}' no disponible"
            })
        
        print(f"⚙️  Ejecutando: {function_name}({function_params})")
        function_result = AVAILABLE_FUNCTIONS[function_name](**function_params)
        print(f"✅ Resultado: {function_result}")
        
        # Paso 3: Naturalizar respuesta con IA (siempre)
        print(f"💬 Generando respuesta natural con IA...")
        natural_response = naturalize_response(function_name, function_result, user_message)
        
        return jsonify({
            "success": True,
            "response": natural_response,
            "metadata": {
                "function_executed": function_name,
                "parameters": function_params,
                "raw_data": function_result,
                "confidence": intent['confidence']
            }
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Error: {str(e)}"
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Endpoint simple sin predicción"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "error": "Debe proporcionar un 'message' en el JSON"
            }), 400
        
        user_message = data['message']
        
        payload = {
            "model": MODEL_NAME,
            "prompt": user_message,
            "stream": False
        }
        
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                "success": True,
                "response": result.get('response', ''),
                "model": MODEL_NAME
            })
        else:
            return jsonify({
                "error": f"Error del modelo: {response.status_code}"
            }), 500
            
    except Exception as e:
        return jsonify({
            "error": f"Error: {str(e)}"
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Verificar estado del servidor"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        ollama_status = "running" if response.status_code == 200 else "error"
    except:
        ollama_status = "not_available"
    
    return jsonify({
        "status": "running",
        "ollama": ollama_status,
        "model": MODEL_NAME,
        "available_functions": list(AVAILABLE_FUNCTIONS.keys())
    })

@app.route('/', methods=['GET'])
def home():
    """Página de documentación"""
    return """<!DOCTYPE html>
<html>
<head>
    <title>DeepSeek R1 - Predicción Inteligente</title>
    <style>
        body { font-family: Arial; max-width: 900px; margin: 50px auto; padding: 20px; }
        .endpoint { background: #f4f4f4; padding: 15px; margin: 10px 0; border-radius: 5px; }
        code { background: #e8e8e8; padding: 2px 6px; border-radius: 3px; }
        .example { background: #e3f2fd; padding: 10px; margin: 10px 0; border-left: 4px solid #2196F3; }
        button { padding: 10px 20px; background: #4CAF50; color: white; 
                border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #45a049; }
        #response { background: #f9f9f9; padding: 15px; border: 1px solid #ddd; 
                   min-height: 100px; white-space: pre-wrap; margin-top: 10px; }
        h1 { color: #333; }
        h2 { color: #555; margin-top: 30px; }
    </style>
</head>
<body>
    <h1>🤖 API de Predicción Inteligente con DeepSeek R1</h1>
    
    <h2>📡 Endpoint Principal</h2>
    <div class="endpoint">
        <h3>POST /predict</h3>
        <p><strong>Análisis inteligente + Ejecución + Respuesta natural</strong></p>
        <code>{"message": "tu consulta en lenguaje natural"}</code>
    </div>

    <h2>📋 Funciones Disponibles</h2>
    
    <div class="example">
        <h4>1. predict_stockout(fecha)</h4>
        <p><strong>Preguntas que funcionan:</strong></p>
        <ul>
            <li>"¿Qué producto se va a agotar primero?"</li>
            <li>"¿Cuál elemento falta pronto?"</li>
            <li>"¿Qué se acaba en inventario?"</li>
        </ul>
    </div>

    <div class="example">
        <h4>2. predict_sales(periodo)</h4>
        <p><strong>Preguntas que funcionan:</strong></p>
        <ul>
            <li>"¿Cuánto vamos a vender el próximo mes?"</li>
            <li>"Proyección de ventas"</li>
            <li>"¿Cuáles son las ventas estimadas?"</li>
        </ul>
    </div>

    <h2>🧪 Pruebas Rápidas</h2>
    <button onclick="test1()">Test: Stockout</button>
    <button onclick="test2()">Test: Ventas</button>
    <button onclick="test3()">Test: Chat General</button>
    <button onclick="testStream()">Test: Streaming</button>
    
    <div id="response"></div>

    <script>
        function showResponse(data) {
            const div = document.getElementById('response');
            div.textContent = JSON.stringify(data, null, 2);
        }

        function test1() {
            fetch('/predict', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: 'que elemento se va a agotar mas pronto'})
            })
            .then(r => r.json())
            .then(showResponse);
        }

        function test2() {
            fetch('/predict', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: 'cuanto venderemos el proximo mes'})
            })
            .then(r => r.json())
            .then(showResponse);
        }

        function test3() {
            fetch('/predict', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: 'quien fue Albert Einstein'})
            })
            .then(r => r.json())
            .then(showResponse);
        }

        function testStream() {
            const div = document.getElementById('response');
            div.textContent = 'Generando respuesta en streaming...\\n\\n';
            
            fetch('/chat/stream', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: 'que producto se agota primero'})
            }).then(response => {
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                function read() {
                    reader.read().then(({done, value}) => {
                        if (done) {
                            div.textContent += '\\n\\n[Completado]';
                            return;
                        }
                        
                        const chunk = decoder.decode(value);
                        const lines = chunk.split('\\n');
                        
                        lines.forEach(line => {
                            if (line.startsWith('data: ')) {
                                try {
                                    const data = JSON.parse(line.slice(6));
                                    if (data.token) {
                                        div.textContent += data.token;
                                    }
                                } catch(e) {}
                            }
                        });
                        
                        read();
                    });
                }
                
                read();
            });
        }
    </script>
</body>
</html>"""

if __name__ == '__main__':
    print("🚀 Iniciando API de Predicción Inteligente...")
    print("📡 Asegúrate de que Ollama esté ejecutándose: ollama serve")
    print("📦 Y que tengas el modelo: ollama pull deepseek-r1")
    print("\n🎯 Funciones disponibles:")
    print("   - predict_stockout: Predice agotamiento de productos")
    print("   - predict_sales: Predice ventas futuras")
    print("\n🔗 Servidor corriendo en: http://localhost:5000")
    print("🌐 Abre http://localhost:5000 para ver la documentación")
    
    app.run(host='0.0.0.0', port=5000, debug=True)