import requests
import weaviate
import json
from typing import List, Dict, Optional
from datetime import datetime

class ConversationManager:
    def __init__(self, weaviate_url: str = "http://localhost:8080", namespace: str = "Conversations"):
        self.ollama_url = "http://localhost:11434"
        self.embedding_model = "nomic-embed-text"
        self.namespace = namespace
        
        # Conectar a Weaviate v3
        self.client = weaviate.Client(weaviate_url)
        
        # Crear la clase si no existe
        self._ensure_class_exists()

    def _ensure_class_exists(self):
        """Asegura que la clase de conversaciones existe en Weaviate"""
        try:
            if not self.client.schema.exists(self.namespace):
                schema = {
                    "class": self.namespace,
                    "description": "Historial completo de conversaciones por usuario y modo",
                    "vectorizer": "none",
                    "properties": [
                        {
                            "name": "content",
                            "dataType": ["text"],
                            "description": "Contenido del mensaje"
                        },
                        {
                            "name": "message_type",
                            "dataType": ["string"],
                            "description": "Tipo: human o ai"
                        },
                        {
                            "name": "user_id",
                            "dataType": ["string"],
                            "description": "ID del usuario"
                        },
                        {
                            "name": "mode",
                            "dataType": ["string"],
                            "description": "Modo: dev, game, etc"
                        },
                        {
                            "name": "timestamp",
                            "dataType": ["string"],
                            "description": "Timestamp ISO del mensaje"
                        },
                        {
                            "name": "session_id",
                            "dataType": ["string"],
                            "description": "ID de sesión para agrupar conversaciones"
                        }
                    ]
                }
                self.client.schema.create_class(schema)
                print(f"✅ Clase {self.namespace} creada en Weaviate.")
        except Exception as e:
            print(f"⚠️ Error al crear clase de conversaciones: {e}")

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
                return []
        except Exception as e:
            print(f"Error obteniendo embedding: {e}")
            return []

    def save_message(self, user_id: str, mode: str, content: str, message_type: str, session_id: str = None):
        """Guarda un mensaje individual en Weaviate"""
        try:
            embedding = self._get_embedding(content)
            if not embedding:
                print("⚠️ No se pudo obtener embedding para el mensaje")
                return
            
            timestamp = datetime.now().isoformat()
            if not session_id:
                session_id = f"{user_id}_{mode}_{datetime.now().strftime('%Y%m%d')}"
            
            data_object = {
                "content": content,
                "message_type": message_type,
                "user_id": user_id,
                "mode": mode,
                "timestamp": timestamp,
                "session_id": session_id
            }
            
            self.client.data_object.create(
                data_object=data_object,
                class_name=self.namespace,
                vector=embedding
            )
            
        except Exception as e:
            print(f"Error guardando mensaje: {e}")

    def get_recent_conversation(self, user_id: str, mode: str, limit: int = 12) -> List[Dict]:
        """Recupera la conversación reciente de un usuario en un modo específico"""
        try:
            where_filter = {
                "operator": "And",
                "operands": [
                    {
                        "path": ["user_id"],
                        "operator": "Equal",
                        "valueString": user_id
                    },
                    {
                        "path": ["mode"],
                        "operator": "Equal",
                        "valueString": mode
                    }
                ]
            }
            
            # Ordenar por timestamp descendente y limitar
            query_result = self.client.query.get(
                self.namespace, 
                ["content", "message_type", "timestamp", "session_id"]
            ).with_where(where_filter).with_limit(limit)
            
            result = query_result.do()
            
            messages = []
            if "data" in result and "Get" in result["data"] and self.namespace in result["data"]["Get"]:
                # Ordenar por timestamp (más recientes primero, luego invertir)
                raw_messages = result["data"]["Get"][self.namespace]
                sorted_messages = sorted(raw_messages, key=lambda x: x["timestamp"])
                
                # Tomar los últimos N mensajes y mantener el orden cronológico
                recent_messages = sorted_messages[-limit:] if len(sorted_messages) > limit else sorted_messages
                
                for msg in recent_messages:
                    messages.append({
                        "type": msg["message_type"],
                        "content": msg["content"],
                        "timestamp": msg["timestamp"]
                    })
            
            return messages
            
        except Exception as e:
            print(f"Error recuperando conversación: {e}")
            return []

    def search_conversation_history(self, user_id: str, mode: str, query: str, limit: int = 10) -> List[Dict]:
        """Busca en el historial de conversaciones usando embeddings semánticos"""
        try:
            query_embedding = self._get_embedding(query)
            if not query_embedding:
                return []
            
            where_filter = {
                "operator": "And",
                "operands": [
                    {
                        "path": ["user_id"],
                        "operator": "Equal",
                        "valueString": user_id
                    },
                    {
                        "path": ["mode"],
                        "operator": "Equal",
                        "valueString": mode
                    }
                ]
            }
            
            near_vector = {"vector": query_embedding}
            
            query_result = self.client.query.get(
                self.namespace, 
                ["content", "message_type", "timestamp"]
            ).with_near_vector(near_vector).with_where(where_filter).with_limit(limit)
            
            result = query_result.do()
            
            messages = []
            if "data" in result and "Get" in result["data"] and self.namespace in result["data"]["Get"]:
                for msg in result["data"]["Get"][self.namespace]:
                    messages.append({
                        "type": msg["message_type"],
                        "content": msg["content"],
                        "timestamp": msg["timestamp"]
                    })
            
            return messages
            
        except Exception as e:
            print(f"Error buscando en historial: {e}")
            return []

    def get_conversation_stats(self, user_id: str, mode: str) -> Dict:
        """Obtiene estadísticas de conversación para un usuario"""
        try:
            where_filter = {
                "operator": "And",
                "operands": [
                    {
                        "path": ["user_id"],
                        "operator": "Equal",
                        "valueString": user_id
                    },
                    {
                        "path": ["mode"],
                        "operator": "Equal",
                        "valueString": mode
                    }
                ]
            }
            
            # Contar mensajes totales
            query_result = self.client.query.aggregate(self.namespace).with_where(where_filter).with_meta_count()
            result = query_result.do()
            
            total_messages = 0
            if "data" in result and "Aggregate" in result["data"]:
                total_messages = result["data"]["Aggregate"][self.namespace][0]["meta"]["count"]
            
            return {
                "total_messages": total_messages,
                "user_id": user_id,
                "mode": mode
            }
            
        except Exception as e:
            print(f"Error obteniendo estadísticas: {e}")
            return {"total_messages": 0, "user_id": user_id, "mode": mode} 