import requests
from typing import List, Dict, Optional
from memory_manager import MemoryManager
from datetime import datetime

class MemoryAgent:
    """
    Agente especializado en gestionar recuerdos de manera inteligente.
    Decide qué guardar, cómo formatear y cuándo limpiar.
    """
    
    def __init__(self, weaviate_url: str = "http://localhost:8080"):
        self.ollama_url = "http://localhost:11434"
        
        # Palabras clave que indican información importante para recordar
        self.important_keywords = [
            "proyecto", "código", "implementar", "configurar", "error", "problema",
            "solución", "arquitectura", "base de datos", "api", "endpoint",
            "componente", "servicio", "clase", "función", "método", "variable",
            "bug", "fix", "refactor", "optimizar", "performance", "seguridad"
        ]
        
        # Palabras que indican información no importante
        self.unimportant_keywords = [
            "hola", "gracias", "adiós", "ok", "bien", "perfecto", "claro",
            "entiendo", "sí", "no", "tal vez", "quizás"
        ]

    def should_save_memory(self, user_input: str, agent_response: str) -> bool:
        """
        Determina si una interacción debe guardarse como recuerdo
        """
        combined_text = (user_input + " " + agent_response).lower()
        
        # 1. No guardar saludos simples
        if any(word in user_input.lower() for word in self.unimportant_keywords):
            if len(user_input.split()) <= 3:
                return False
        
        # 2. Guardar si contiene información técnica importante
        if any(keyword in combined_text for keyword in self.important_keywords):
            return True
        
        # 3. Guardar preguntas complejas
        if any(word in user_input.lower() for word in ["cómo", "por qué", "cuál", "dónde", "cuándo"]):
            if len(user_input.split()) > 5:
                return True
        
        # 4. Guardar respuestas largas (probablemente informativas)
        if len(agent_response.split()) > 20:
            return True
        
        # 5. Guardar si menciona código, archivos, o implementaciones
        code_indicators = ["código", "archivo", "función", "clase", "método", "variable", "import", "export"]
        if any(indicator in combined_text for indicator in code_indicators):
            return True
        
        return False

    def format_memory_content(self, user_input: str, agent_response: str, context_type: str = "conversation") -> str:
        """
        Formatea el contenido del recuerdo de manera más estructurada
        """
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        # Extraer información clave
        key_info = self._extract_key_information(user_input, agent_response)
        
        if context_type == "technical":
            return f"[{timestamp}] Consulta técnica: {user_input} | Solución: {key_info}"
        elif context_type == "problem":
            return f"[{timestamp}] Problema: {user_input} | Resolución: {key_info}"
        else:
            return f"[{timestamp}] {user_input} | Respuesta: {key_info}"

    def _extract_key_information(self, user_input: str, agent_response: str) -> str:
        """
        Extrae la información clave de la respuesta del agente
        """
        # Tomar los primeros 200 caracteres de la respuesta
        # En el futuro se puede implementar extracción más sofisticada
        key_info = agent_response[:200]
        if len(agent_response) > 200:
            key_info += "..."
        
        return key_info

    def clean_old_memories(self, memory_manager: MemoryManager, namespace: str, days_old: int = 30):
        """
        Limpia recuerdos antiguos o irrelevantes
        """
        # Esta funcionalidad requeriría implementar filtros por fecha en Weaviate
        # Por ahora, solo es un placeholder para funcionalidad futura
        pass

    def save_smart_memory(self, 
                         memory_manager: MemoryManager,
                         user_id: str, 
                         mode: str,
                         user_input: str, 
                         agent_response: str) -> bool:
        """
        Guarda un recuerdo de manera inteligente si es necesario
        """
        if not self.should_save_memory(user_input, agent_response):
            return False
        
        # Determinar el tipo de contexto
        context_type = self._determine_context_type(user_input, agent_response)
        
        # Formatear el contenido
        memory_content = self.format_memory_content(user_input, agent_response, context_type)
        
        # Guardar el recuerdo
        player_id_with_mode = f"{user_id}_{mode}"
        memory_manager.guardar_recuerdo(
            memory_content,
            {"player_id": player_id_with_mode}
        )
        
        return True

    def _determine_context_type(self, user_input: str, agent_response: str) -> str:
        """
        Determina el tipo de contexto para mejor categorización
        """
        combined_text = (user_input + " " + agent_response).lower()
        
        if any(word in combined_text for word in ["error", "problema", "bug", "falla"]):
            return "problem"
        elif any(word in combined_text for word in ["implementar", "código", "función", "clase", "método"]):
            return "technical"
        else:
            return "conversation"

    def get_memory_stats(self, memory_manager: MemoryManager, user_id: str, mode: str) -> Dict:
        """
        Obtiene estadísticas de memoria para un usuario
        """
        player_id_with_mode = f"{user_id}_{mode}"
        
        # Obtener algunos recuerdos para análisis
        recent_memories = memory_manager.recuperar_recuerdos(
            query="", 
            k=10, 
            metadatos={"player_id": player_id_with_mode}
        )
        
        return {
            "total_memories": len(recent_memories),
            "user_id": user_id,
            "mode": mode,
            "last_memory_date": datetime.now().isoformat() if recent_memories else None
        } 