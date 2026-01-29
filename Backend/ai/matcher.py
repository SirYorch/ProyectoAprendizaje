from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sentence_transformers import SentenceTransformer
from typing import Dict, Any, Optional
import re
import json

# ============================================
# CONFIGURACIÓN
# ============================================

DATABASE_URL = "postgresql://usuario1:password1@localhost:5432/aprendizaje"


# ============================================
# CLASE PRINCIPAL - CON PRINTS DETALLADOS
# ============================================

class FunctionCaller:
    """
    Clase minimalista para identificar funciones con prints detallados
    """
    
    def __init__(self, database_url: str = DATABASE_URL):
        """Inicializa conexión y modelo"""
        
        
        try:
            print(f"🔗 Conectando a base de datos...")
            self.engine = create_engine(database_url)
            self.SessionLocal = sessionmaker(bind=self.engine)
        
            
            # Carga modelo de embeddings
            print("📦 Cargando modelo de embeddings...")
            self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
            
            print("="*70 + "\n")
            
        except Exception as e:
        
            raise
    
    def _get_session(self) -> Session:
        """Crea y retorna una nueva sesión de base de datos"""
        return self.SessionLocal()
    
    def identificar_funcion(self, mensaje: str) -> Dict[str, Any]:
        """
        MÉTODO PRINCIPAL - Identifica qué función ejecutar
        """
        
        print("IDENTIFICAR FUNCIÓN")
        
        print(f" Mensaje: '{mensaje}'")
        print(f" Longitud: {len(mensaje)} caracteres")
        
        session = None
        
        try:
            session = self._get_session()
            
            
            # 1. Genera embedding del mensaje
            
            embedding = self.model.encode([mensaje])[0].tolist()
            print(f" Embedding generado - Dimensiones: {len(embedding)}")
            print(f"   Primeros 5 valores: {[round(v, 4) for v in embedding[:5]]}")
            
            # 2. Busca las top 3 funciones más similares
            
            results = session.execute(text("""
                SELECT 
                    fe.function_id,
                    fd.nombre as funcion_nombre,
                    fd.parametros,
                    1 - (fe.embedding <=> :embedding) as similarity
                FROM function_examples fe
                JOIN function_definitions fd ON fe.function_id = fd.id
                WHERE fd.activo = 1
                ORDER BY fe.embedding <=> :embedding
                LIMIT 3
            """), {"embedding": str(embedding)}).fetchall()
            
            print(f"Resultados encontrados: {len(results)}")
            
            # Mostrar top 3 funciones candidatas
            if results:
                print("\nTOP 3 FUNCIONES CANDIDATAS:")
                print("-" * 70)
                for idx, row in enumerate(results, 1):
                    confianza = row[3]
                    
                    print(f"{idx}. {row[1]:<35} Confianza: {confianza:.4f}")
                print("-" * 70)
            
            # Validar resultado
            if not results or results[0][3] < 0.6:
                confianza_mejor = results[0][3] if results else 0.0
                print(f"\n FUNCIÓN NO IDENTIFICADA")
                print(f"   Umbral mínimo requerido: 0.6000")
                print(f"   Mejor confianza obtenida: {confianza_mejor:.4f}")
                
                return {
                    'funcion': None,
                    'parametros': {},
                    'confianza': confianza_mejor,
                    'error': 'No se pudo identificar la función'
                }
            
            function_id, funcion_nombre, parametros_json, confianza = results[0]
                       
            # 3. Extrae parámetros del mensaje
            if isinstance(parametros_json, str):
                parametros_requeridos = json.loads(parametros_json)
            else:
                parametros_requeridos = parametros_json or []
            
            print(f"Parámetros requeridos: {parametros_requeridos}")
            
            print("\n Extrayendo parámetros del mensaje...")
            parametros_extraidos = self._extraer_parametros(
                mensaje, 
                parametros_requeridos, 
                session
            )
            
            resultado_final = {
                'funcion': funcion_nombre,
                'parametros': parametros_extraidos,
                'confianza': confianza
            }
            return resultado_final
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'funcion': None,
                'parametros': {},
                'confianza': 0.0,
                'error': f'Error al identificar función: {str(e)}'
            }
        
        finally:
            if session:
                session.close()
    
    def _extraer_parametros(self, mensaje: str, params_requeridos: list, session: Session) -> Dict[str, Any]:
        """Extrae parámetros del mensaje"""
        parametros = {}
        
        try:
            # Extrae producto si es necesario
            if 'producto' in params_requeridos:
                
                producto = self._extraer_producto(mensaje, session)
                if producto:
                    parametros['producto'] = producto
                    
                
            
            # Extrae fecha si es necesario
            if 'fecha' in params_requeridos:
                
                fecha = self._extraer_fecha(mensaje)
                if fecha:
                    parametros['fecha'] = fecha
                
            # Extrae mes si es necesario
            if 'mes' in params_requeridos:
                
                mes = self._extraer_mes(mensaje)
                if mes:
                    parametros['mes'] = mes
                    
                
            
            print(f"   Parámetros extraídos: {parametros}")
        
        except Exception as e:
            print(f"Error al extraer parámetros: {e}")
        
        return parametros
    
    def _extraer_producto(self, texto: str, session: Session) -> Optional[str]:
        """Extrae nombre de producto usando la sesión pasada como parámetro"""
        try:
            result = session.execute(text(
                "SELECT DISTINCT nombre FROM productos WHERE activo = true"
            ))
            
            productos = [row[0] for row in result]
            print(f"         Productos en BD: {len(productos)}")
            
            texto_lower = texto.lower()
            for producto in productos:
                if producto.lower() in texto_lower:
                    return producto
            return None
        except Exception as e:
            print(f"          Error: {e}")
            return None
    
    def _extraer_fecha(self, texto: str) -> Optional[str]:
        """Extrae fecha en formato YYYY-MM-DD"""
        try:
            # Formato ISO: 2024-12-25
            match = re.search(r'\b(\d{4})-(\d{2})-(\d{2})\b', texto)
            if match:
                return match.group(0)
            
            # Formato: 25/12/2024
            match = re.search(r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b', texto)
            if match:
                dia, mes, año = match.groups()
                return f"{año}-{mes.zfill(2)}-{dia.zfill(2)}"
            
            return None
        except Exception as e:
            print(f"         ❌ Error: {e}")
            return None
    
    def _extraer_mes(self, texto: str) -> Optional[str]:
        """Extrae mes en formato YYYY-MM"""
        try:
            meses = {
                'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
                'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
                'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
            }
            
            for mes_nombre, mes_num in meses.items():
                pattern = rf'\b{mes_nombre}\s+(?:de\s+)?(\d{{4}})\b'
                match = re.search(pattern, texto.lower())
                if match:
                    año = match.group(1)
                    return f"{año}-{mes_num}"
            
            return None
        except Exception as e:
            print(f"         ❌ Error: {e}")
            return None
    
    def consultar_faq(self, mensaje: str) -> Optional[Dict[str, Any]]:
        """
        Busca en la tabla FAQKnowledge y muestra top 3 resultados
        """
        
        session = None
        
        try:
            session = self._get_session()
        
            
            # 1. Vectorizar pregunta
            embedding = self.model.encode([mensaje])[0].tolist()
            # 2. Buscar TOP 3 en la tabla de FAQs
        
            results = session.execute(text("""
                SELECT 
                    pregunta,
                    respuesta,
                    categoria,
                    1 - (embedding <=> :embedding) as similarity
                FROM faq_knowledge
                ORDER BY embedding <=> :embedding
                LIMIT 3
            """), {"embedding": str(embedding)}).fetchall()


            
            # Mostrar top 3 FAQs con detalles
            if results:
                print("\nTOP 3 FAQs MÁS SIMILARES:")
                print("-" * 70)
                for idx, row in enumerate(results, 1):
                    confianza = row[3]
                    print(f"\n FAQ #{idx} - Confianza: {confianza:.4f}")
                    print(f"   Categoría: {row[2]}")
                    print(f"   Pregunta: {row[0][:100]}{'...' if len(row[0]) > 100 else ''}")
                    print(f"   Respuesta: {row[1][:100]}{'...' if len(row[1]) > 100 else ''}")
                print("-" * 70)

            # 3. Validar mejor resultado con umbral
            if not results or results[0][3] < 0.5:
                confianza_mejor = results[0][3] if results else 0.0
                print(f"\n FAQ NO ENCONTRADO")
                print(f"   Umbral mínimo requerido: 0.5000")
                print(f"   Mejor confianza obtenida: {confianza_mejor:.4f}")
                print("="*70 + "\n")
                return None

            resultado = {
                "tipo": "faq",
                "pregunta": results[0][0],
                "respuesta": results[0][1],
                "categoria": results[0][2],
                "confianza": results[0][3]
            }
            
            print(f"\n FAQ SELECCIONADO (Mayor confianza)")
            print(f"   Categoría: {resultado['categoria']}")
            print(f"   Confianza: {resultado['confianza']:.4f}")
            
            print("\n" + "="*70)
            print("RESULTADO FINAL:")
            print(json.dumps(resultado, indent=2, ensure_ascii=False))
            print("="*70 + "\n")
            
            return resultado
        
        except Exception as e:
            print(f"\n ERROR en consultar_faq: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        finally:
            if session:
                session.close()