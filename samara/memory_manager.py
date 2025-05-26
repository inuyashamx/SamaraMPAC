import requests
import weaviate
import json
from typing import List, Dict

class MemoryManager:
    def __init__(self, weaviate_url: str = "http://localhost:8080", namespace: str = "PlayerMemories"):
        self.ollama_url = "http://localhost:11434"
        self.embedding_model = "nomic-embed-text"
        self.namespace = namespace
        
        # Conectar a Weaviate v3
        self.client = weaviate.Client(weaviate_url)
        
        # Crear la clase si no existe
        self._ensure_class_exists()

    def _ensure_class_exists(self):
        """Asegura que la clase existe en Weaviate"""
        try:
            if not self.client.schema.exists(self.namespace):
                schema = {
                    "class": self.namespace,
                    "description": "Recuerdos narrativos por jugador",
                    "vectorizer": "none",
                    "properties": [
                        {
                            "name": "contenido",
                            "dataType": ["text"]
                        },
                        {
                            "name": "player_id",
                            "dataType": ["string"]
                        }
                    ]
                }
                self.client.schema.create_class(schema)
                print(f"✅ Clase {self.namespace} creada en Weaviate.")
        except Exception as e:
            print(f"⚠️ Error al crear clase: {e}")

    def _get_embedding(self, text: str) -> List[float]:
        """Obtiene embedding usando Ollama directamente"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                }
            )
            if response.status_code == 200:
                return response.json()["embedding"]
            else:
                print(f"Error al obtener embedding: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error conectando con Ollama: {e}")
            return []

    def guardar_recuerdo(self, contenido: str, metadatos: Dict[str, str]):
        """Guarda un recuerdo con metadatos (ej: player_id)"""
        try:
            embedding = self._get_embedding(contenido)
            if not embedding:
                print("⚠️ No se pudo obtener embedding, guardando sin vector")
                return
            
            data_object = {
                "contenido": contenido,
                "player_id": metadatos.get("player_id", "unknown")
            }
            
            self.client.data_object.create(
                data_object=data_object,
                class_name=self.namespace,
                vector=embedding
            )
            print(f"✅ Recuerdo guardado para {metadatos.get('player_id', 'unknown')}")
        except Exception as e:
            print(f"Error guardando recuerdo: {e}")

    def recuperar_recuerdos(self, query: str, k: int = 5, metadatos: Dict[str, str] = None) -> List[Dict]:
        """Busca recuerdos similares usando embeddings"""
        try:
            query_embedding = self._get_embedding(query)
            if not query_embedding:
                print("⚠️ No se pudo obtener embedding para la consulta")
                return []
            
            # Construir consulta GraphQL
            near_vector = {
                "vector": query_embedding
            }
            
            where_filter = None
            if metadatos and "player_id" in metadatos:
                where_filter = {
                    "path": ["player_id"],
                    "operator": "Equal",
                    "valueString": metadatos["player_id"]
                }
            
            query_result = self.client.query.get(
                self.namespace, ["contenido", "player_id"]
            ).with_near_vector(near_vector).with_limit(k)
            
            if where_filter:
                query_result = query_result.with_where(where_filter)
            
            result = query_result.do()
            
            # Convertir resultados a formato compatible
            results = []
            if "data" in result and "Get" in result["data"] and self.namespace in result["data"]["Get"]:
                for obj in result["data"]["Get"][self.namespace]:
                    results.append({
                        "page_content": obj["contenido"],
                        "metadata": {
                            "player_id": obj["player_id"]
                        }
                    })
            
            return results
            
        except Exception as e:
            print(f"Error recuperando recuerdos: {e}")
            return []

    def __del__(self):
        """Cerrar la conexión al destruir el objeto"""
        # Weaviate v3 no requiere cerrar explícitamente
        pass


