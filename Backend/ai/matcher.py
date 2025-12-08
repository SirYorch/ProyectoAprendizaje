from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sentence_transformers import SentenceTransformer
from typing import Dict, Any, Optional
import re

# ============================================
# CONFIGURACIÓN
# ============================================

DATABASE_URL = "postgresql://usuario1:password1@localhost:5432/aprendizaje"


# ============================================
# CLASE PRINCIPAL - SOLO LO ESENCIAL
# ============================================

class FunctionCaller:
    """
    Clase minimalista para identificar funciones
    """
    
    def __init__(self, database_url: str = DATABASE_URL):
        """Inicializa conexión y modelo"""
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        # Carga modelo de embeddings (se hace solo una vez)
        print("Cargando modelo...")
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        print("✅ Listo")
    
    def identificar_funcion(self, mensaje: str) -> Dict[str, Any]:
        """
        MÉTODO PRINCIPAL - Identifica qué función ejecutar
        
        Args:
            mensaje: Texto del usuario
            
        Returns:
            {
                'funcion': 'nombre_de_la_funcion',
                'parametros': {'param1': 'valor1', ...},
                'confianza': 0.85
            }
        """
        session = self.SessionLocal()
        
        try:
            # 1. Genera embedding del mensaje
            embedding = self.model.encode([mensaje])[0].tolist()
            
            # 2. Busca la función más similar en la BD
            result = session.execute(text("""
                SELECT 
                    fe.function_id,
                    fd.nombre as funcion_nombre,
                    fd.parametros,
                    1 - (fe.embedding <=> :embedding) as similarity
                FROM function_examples fe
                JOIN function_definitions fd ON fe.function_id = fd.id
                WHERE fd.activo = 1
                ORDER BY fe.embedding <=> :embedding
                LIMIT 1
            """), {"embedding": str(embedding)}).fetchone()
            
            if not result or result[3] < 0.6:  # threshold = 0.6
                return {
                    'funcion': None,
                    'parametros': {},
                    'confianza': result[3] if result else 0.0,
                    'error': 'No se pudo identificar la función'
                }
            
            function_id, funcion_nombre, parametros_json, confianza = result
            
            # 3. Extrae parámetros del mensaje
            import json
            if isinstance(parametros_json, str):
                parametros_requeridos = json.loads(parametros_json)
            else:
                parametros_requeridos = parametros_json or []
            parametros_extraidos = self._extraer_parametros(
                mensaje, 
                parametros_requeridos, 
                session
            )
            
            return {
                'funcion': funcion_nombre,
                'parametros': parametros_extraidos,
                'confianza': confianza
            }
            
        finally:
            session.close()
    
    def _extraer_parametros(self, mensaje: str, params_requeridos: list, session) -> Dict[str, Any]:
        """Extrae parámetros del mensaje"""
        parametros = {}
        
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
        
        return parametros
    
    def _extraer_producto(self, texto: str, session) -> Optional[str]:
        """Extrae nombre de producto"""
        
        
        result = session.execute(text(
            "SELECT DISTINCT nombre FROM productos WHERE activo = true"
        ))
        
        productos = [row[0] for row in result]
        
        texto_lower = texto.lower()
        for producto in productos:
            if producto.lower() in texto_lower:
                return producto
        return None
    
    def _extraer_fecha(self, texto: str) -> Optional[str]:
        """Extrae fecha en formato YYYY-MM-DD"""
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
    
    def _extraer_mes(self, texto: str) -> Optional[str]:
        """Extrae mes en formato YYYY-MM"""
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
    
    def consultar_faq(self, mensaje: str) -> Dict[str, Any]:
        """
        Busca en la tabla FAQKnowledge
        """
        session = self.SessionLocal()
        try:
            # 1. Vectorizar pregunta
            embedding = self.model.encode([mensaje])[0].tolist()

            # 2. Buscar en la tabla de FAQs (NO en la de funciones)
            result = session.execute(text("""
                SELECT 
                    pregunta,
                    respuesta,
                    categoria,
                    1 - (embedding <=> :embedding) as similarity
                FROM faq_knowledge
                ORDER BY embedding <=> :embedding
                LIMIT 1
            """), {"embedding": str(embedding)}).fetchone()

            # 3. Umbral un poco más bajo para FAQs (0.5) para ser flexible
            if not result or result[3] < 0.5:
                return None

            return {
                "tipo": "faq",
                "pregunta": result[0],
                "respuesta": result[1],
                "confianza": result[3]
            }
        finally:
            session.close()

