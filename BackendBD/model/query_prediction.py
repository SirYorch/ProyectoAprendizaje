import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier
from typing import Dict, Any, Tuple
from datetime import datetime
import re

class IntentClassifier:
    """
    Clasificador de intenciones usando KNN para determinar qué endpoint usar.
    """
    
    # def __init__(self):
    #     self.vectorizer = TfidfVectorizer(
    #         max_features=100,
    #         ngram_range=(1, 3),
    #         stop_words=None
    #     )
    #     self.knn = KNeighborsClassifier(
    #         n_neighbors=3,
    #         weights='distance',
    #         metric='cosine'
    #     )
    #     self.intent_labels = {
    #         0: "predict_out_of_stock",
    #         1: "predict_product_stock",
    #         2: "predict_date",
    #         3: "predict_product_out_of_stock"
    #     }
    #     self.is_trained = False    
    #     texts = [example[0] for example in training_examples]
    #     labels = [example[1] for example in training_examples]
        
    #     return texts, labels

    
    def predict_intent(self, query: str) -> Tuple[str, float, int]:
        """
        Predice la intención del usuario a partir de su consulta.
        """
        if not self.is_trained:
            raise Exception("El modelo no ha sido entrenado. Llama a train() primero.")
        
        query_clean = query.lower().strip()
        X = self.vectorizer.transform([query_clean])
        prediction = self.knn.predict(X)[0]
        distances, _ = self.knn.kneighbors(X)
        confidence = 1 - (distances.mean() / 2)
        endpoint = self.intent_labels[prediction]
        
        return endpoint, confidence, prediction
    
    def extract_parameters(self, query: str, intent: str) -> Dict[str, Any]:
        """
        Extrae parámetros de la consulta según la intención detectada.
        """
        query_lower = query.lower()
        params = {}
        
        MONTHS = {
            "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5,
            "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9,
            "octubre": 10, "noviembre": 11, "diciembre": 12
        }

        today = datetime.now()
        year = today.year
        month = today.month
        
        # Extraer nombre de producto
        product_patterns = [
            r'producto\s+([a-zA-Z0-9\-_]+)',
            r'del?\s+([a-z0-9_áéíóúñ]+)',
            r'de\s+([a-z0-9_áéíóúñ]+)',
        ]
        
        for pattern in product_patterns:
            match = re.search(pattern, query_lower)
            if match:
                params['product_name'] = match.group(1).strip()
                break
        
        # Extraer fecha
        # -----------------------------
        # 1) Formato completo YYYY-MM-DD
        # -----------------------------
        match = re.search(r'(\d{4})-(\d{2})-(\d{2})', query_lower)
        if match:
            y, m, d = match.groups()
            params["prediction_date"] = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
            return params

        # -----------------------------
        # 2) Formato "15 de mayo"
        # -----------------------------
        match = re.search(
            r'(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)',
            query_lower
        )
        if match:
            day = int(match.group(1))
            month = MONTHS[match.group(2)]
            params["prediction_date"] = f"{year:04d}-{month:02d}-{day:02d}"
            return params

        # -----------------------------
        # 3) Formato "mayo 15"
        # -----------------------------
        match = re.search(
            r'(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+(\d{1,2})',
            query_lower
        )
        if match:
            month = MONTHS[match.group(1)]
            day = int(match.group(2))
            params["prediction_date"] = f"{year}-{month:02d}-{day:02d}"
            return params

        # -----------------------------
        # 4) Día aislado ("el día 10", "el 5", "para el 12")
        # -----------------------------
        match = re.search(r'(?:el\s+día\s+|el\s+|para\s+el\s+)(\d{1,2})', query_lower)
        if match:
            day = int(match.group(1))
            params["prediction_date"] = f"{year}-{month:02d}-{day:02d}"
            return params

        # -----------------------------
        # 5) Mes aislado ("en mayo", "para junio")
        # -----------------------------
        match = re.search(r'en\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)', query_lower)
        if match:
            month = MONTHS[match.group(1)]
            params["prediction_date"] = f"{year}-{month:02d}-01"
            return params

        # -----------------------------
        # 6) Año aislado ("en 2026")
        # -----------------------------
        match = re.search(r'en\s+(20\d{2})', query_lower)
        if match:
            params["prediction_date"] = f"{int(match.group(1))}-01-01"
            return params

        return params
        
    
    def save_model(self, path: str = "intent_classifier.pkl"):
        """
        Guarda el modelo entrenado en disco.
        """
        with open(path, 'wb') as f:
            pickle.dump({
                'vectorizer': self.vectorizer,
                'knn': self.knn,
                'intent_labels': self.intent_labels,
                'is_trained': self.is_trained
            }, f)
    
    def load_model(self, path: str = "files/intent_classifier.pkl"):
        """
        Carga un modelo previamente entrenado.
        """
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.vectorizer = data['vectorizer']
            self.knn = data['knn']
            self.intent_labels = data['intent_labels']
            self.is_trained = data['is_trained']
        