import requests
from typing import List, Dict, Optional
from conversation_manager import ConversationManager
from memory_manager import MemoryManager

class ContextAgent:
    """
    Agente especializado en determinar y formatear el contexto necesario
    para cada conversación de manera inteligente.
    """
    
    def __init__(self, weaviate_url: str = "http://localhost:8080"):
        self.ollama_url = "http://localhost:11434"
        self.embedding_model = "nomic-embed-text"
        
        # Palabras clave que indican necesidad de recuerdos
        self.memory_triggers = [
            "recuerda", "recordar", "antes", "anterior", "dijimos", "hablamos",
            "mencionaste", "conversación", "tema", "proyecto", "código",
            "problema", "error", "solución", "implementación"
        ]
        
        # Palabras que indican consultas simples (no necesitan recuerdos)
        self.simple_triggers = [
            "hola", "gracias", "adiós", "salir", "ok", "bien", "perfecto"
        ]

    def should_use_memories(self, user_input: str, conversation_context: List[Dict]) -> bool:
        """
        Determina inteligentemente si necesitamos consultar recuerdos
        """
        user_input_lower = user_input.lower()
        
        # 1. Consultas muy simples no necesitan recuerdos
        if any(trigger in user_input_lower for trigger in self.simple_triggers):
            if len(user_input.split()) <= 3:  # Mensajes muy cortos
                return False
        
        # 2. Referencias explícitas a memoria
        if any(trigger in user_input_lower for trigger in self.memory_triggers):
            return True
        
        # 3. Si no hay contexto reciente, usar recuerdos
        if len(conversation_context) < 2:
            return True
        
        # 4. Preguntas técnicas complejas
        if any(word in user_input_lower for word in ["cómo", "por qué", "implementar", "configurar", "error"]):
            return True
        
        # 5. Mensajes largos (probablemente complejos)
        if len(user_input.split()) > 10:
            return True
        
        return False

    def format_conversation_context(self, messages: List[Dict], max_messages: int = 6) -> List[str]:
        """
        Formatea el contexto de conversación de manera inteligente
        """
        if not messages:
            return []
        
        # Tomar los mensajes más recientes
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        formatted = []
        for msg in recent_messages:
            if msg["type"] == "human":
                formatted.append(f"Usuario: {msg['content']}")
            elif msg["type"] == "ai":
                formatted.append(f"Agente: {msg['content']}")
        
        return formatted

    def format_memory_context(self, memories: List[Dict], user_input: str, max_memories: int = 3) -> List[str]:
        """
        Formatea los recuerdos de manera más inteligente y relevante
        """
        if not memories:
            return []
        
        # Filtrar y rankear recuerdos por relevancia
        relevant_memories = self._rank_memories_by_relevance(memories, user_input)
        
        # Tomar solo los más relevantes
        top_memories = relevant_memories[:max_memories]
        
        formatted = []
        for memory in top_memories:
            # Extraer información clave del recuerdo
            content = memory.get('page_content', '')
            
            # Formatear de manera más natural
            if 'El jugador dijo:' in content and 'El agente respondió:' in content:
                # Extraer partes relevantes
                parts = content.split('El agente respondió:')
                if len(parts) == 2:
                    user_part = parts[0].replace('El jugador dijo:', '').strip()
                    agent_part = parts[1].strip()
                    
                    # Solo incluir si es relevante al contexto actual
                    if self._is_memory_relevant(user_part + ' ' + agent_part, user_input):
                        formatted.append(f"Contexto previo: {user_part} → {agent_part[:100]}...")
            else:
                # Formato simple para otros tipos de recuerdos
                formatted.append(f"Recuerdo: {content[:150]}...")
        
        return formatted

    def _rank_memories_by_relevance(self, memories: List[Dict], user_input: str) -> List[Dict]:
        """
        Rankea los recuerdos por relevancia al input actual
        """
        # Por ahora, mantener el orden de Weaviate (ya viene rankeado por similitud)
        # En el futuro se puede implementar ranking más sofisticado
        return memories

    def _is_memory_relevant(self, memory_content: str, user_input: str) -> bool:
        """
        Determina si un recuerdo es relevante al input actual
        """
        memory_lower = memory_content.lower()
        input_lower = user_input.lower()
        
        # Buscar palabras clave comunes
        memory_words = set(memory_lower.split())
        input_words = set(input_lower.split())
        
        # Si hay al menos 2 palabras en común (excluyendo palabras muy comunes)
        common_words = [
            "el", "la", "de", "que", "y", "a", "en", "un", "es", "se", "no", "te", "lo", "le", "da", "su", "por", "son", "con", "para", "al", "del", "los", "las", "una", "como", "pero", "sus", "me", "ya", "muy", "mi", "sin", "sobre", "este", "era", "entre", "cuando", "todo", "esta", "ser", "son", "dos", "también", "fue", "había", "si", "más", "hasta"
        ]
        
        memory_significant = memory_words - set(common_words)
        input_significant = input_words - set(common_words)
        
        overlap = memory_significant & input_significant
        
        return len(overlap) >= 2

    def get_smart_context(self, 
                         conversation_manager: ConversationManager,
                         memory_manager: MemoryManager,
                         user_id: str, 
                         mode: str, 
                         user_input: str,
                         namespace: str) -> Dict:
        """
        Método principal: obtiene contexto inteligente basado en la necesidad
        """
        # 1. Siempre obtener contexto de conversación reciente
        recent_conversation = conversation_manager.get_recent_conversation(user_id, mode, limit=12)
        conversation_context = self.format_conversation_context(recent_conversation)
        
        # 2. Determinar si necesitamos recuerdos
        needs_memories = self.should_use_memories(user_input, recent_conversation)
        
        memory_context = []
        if needs_memories:
            # 3. Obtener recuerdos relevantes
            player_id_with_mode = f"{user_id}_{mode}"
            memories = memory_manager.recuperar_recuerdos(
                query=user_input, 
                k=5, 
                metadatos={"player_id": player_id_with_mode}
            )
            memory_context = self.format_memory_context(memories, user_input)
        
        return {
            "conversation_context": conversation_context,
            "memory_context": memory_context,
            "used_memories": needs_memories,
            "context_summary": {
                "conversation_messages": len(conversation_context),
                "memory_items": len(memory_context),
                "total_context_size": len(conversation_context) + len(memory_context)
            }
        } 