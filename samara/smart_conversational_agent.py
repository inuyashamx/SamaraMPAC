import os
import json
import requests
import re
from typing import List, Dict, Optional
from .conversation_manager import ConversationManager
from .memory_manager import MemoryManager
from .context_agent import ContextAgent
from .memory_agent import MemoryAgent
from .prompt_builder import PromptBuilder
from .model_router_agent import ModelRouterAgent, TaskType, ModelProvider
# from .samara_dev_agent import SamaraDevAgent  # Importación movida para evitar circular
from datetime import datetime
from .code_analysis_agent import CodeAnalysisAgent

class SmartConversationalAgent:
    """
    Agente conversacional inteligente que orquesta múltiples agentes especializados:
    - ContextAgent: Gestiona contexto de manera inteligente
    - MemoryAgent: Gestiona recuerdos de manera selectiva
    - ConversationManager: Maneja conversaciones en Weaviate
    - MemoryManager: Maneja recuerdos en Weaviate
    """
    
    def __init__(self, profile_path="profiles/game.json", ollama_url="http://localhost:11434", token_limit=3000):
        # Cargar perfil JSON
        with open(profile_path, "r", encoding="utf-8") as f:
            self.profile = json.load(f)

        # Inicializar componentes con valores del perfil
        self.namespace = self.profile.get("namespace", "samara-default")
        self.mode = self.profile.get("mode", "default")
        self.system_prompt = self.profile.get("system_prompt", "")
        self.ollama_url = ollama_url
        self.token_limit = token_limit

        # Inicializar agentes especializados
        self.model_router = ModelRouterAgent()
        self.conversation_manager = ConversationManager("http://localhost:8080", namespace=f"{self.namespace}Conversations")
        self.memory_manager = MemoryManager("http://localhost:8080", namespace=self.namespace)
        use_memories = self.profile.get("use_memories", True)
        self.context_agent = ContextAgent("http://localhost:8080", use_memories=use_memories, mode=self.mode)
        self.memory_agent = MemoryAgent("http://localhost:8080")
        self.prompt_builder = PromptBuilder(token_limit=token_limit, system_prompt=self.system_prompt)

        # Estadísticas de sesión
        self.session_stats = {
            "messages_processed": 0,
            "memories_used": 0,
            "memories_saved": 0,
            "context_optimizations": 0
        }

        # Agente especializado para modo dev (importación lazy para evitar circular)
        self.dev_agent = None
        if self.mode == "dev":
            try:
                from .samara_dev_agent import SamaraDevAgent
                self.dev_agent = SamaraDevAgent()
            except ImportError as e:
                print(f"⚠️ No se pudo cargar SamaraDevAgent: {e}")
                print("💡 Funcionalidad básica disponible sin comandos especializados")

        # Estadísticas de eficiencia
        self.efficiency_stats = {
            "total_interactions": 0,
            "memory_queries": 0,
            "memory_saves": 0,
            "model_switches": 0,
            "fallbacks_used": 0,
            "dev_commands": 0,
            "session_start": datetime.now().isoformat()
        }

        print(f"🧠 SmartConversationalAgent inicializado en modo '{self.mode}'")
        print(f"📊 Proveedores disponibles: {self.model_router.get_available_providers()}")

    def interactuar(self, player_id: str, mensaje: str) -> str:
        """
        Método principal de interacción: SOLO consulta directa a Weaviate (sacs3_Chunks), muestra debug crudo y responde 'No hay datos.' si no hay chunks relevantes. Nunca pasa a LLM ni genera análisis.
        """
        self.efficiency_stats["total_interactions"] += 1

        # Comando especial: debug de Weaviate
        if mensaje.lower().strip() in ["debug weaviate", "debug weaviate data", "debug weaviate datos"]:
            print("\n=== DEBUG SOLICITADO POR USUARIO ===\n")
            self.debug_weaviate_data()
            return "🛠️ Debug de Weaviate ejecutado. Revisa la consola para ver los datos reales indexados."

        # SOLO consulta a Weaviate (sacs3_Chunks), sin pasar nunca a LLM
        try:
            code_agent = CodeAnalysisAgent()
            proyecto_default = "sacs3"
            chunks_class_name = f"Project_{proyecto_default}_Chunks"
            query_embedding = code_agent._get_embedding(mensaje)
            result = (
                code_agent.weaviate_client.query
                .get(chunks_class_name, [
                    "parentFile", "chunkContent", "chunkType", "moduleType", "technology"
                ])
                .with_near_vector({"vector": query_embedding})
                .with_limit(10)
                .do()
            )
            print("\n=== DEBUG: RESULTADOS DE WEAVIATE (sacs3_Chunks) ===\n")
            if "data" in result and "Get" in result["data"] and chunks_class_name in result["data"]["Get"]:
                chunks = result["data"]["Get"][chunks_class_name]
                if not chunks:
                    print("No se encontraron chunks relevantes en Weaviate.")
                    return "No hay datos."
                for i, chunk in enumerate(chunks, 1):
                    print(f"CHUNK {i}:")
                    print(f"  • Archivo: {chunk.get('parentFile')}")
                    print(f"  • Tipo: {chunk.get('chunkType')}")
                    print(f"  • Tecnología: {chunk.get('technology')}")
                    contenido = chunk.get('chunkContent', '')
                    print(f"  • Contenido (primeros 500 chars):\n{contenido[:500]}\n...")
                    print()
                # Mostrar el contenido más relevante como respuesta (sin pasar a LLM)
                chunk = chunks[0]
                contenido = chunk.get('chunkContent', '').strip()
                if contenido:
                    return f"🔍 Fragmento relevante encontrado en Weaviate:\n\n{contenido[:1200]}\n..."
                else:
                    return "No hay datos."
            else:
                print("No se encontró la clase de chunks en Weaviate o hubo un error en la consulta.")
                return "No hay datos."
        except Exception as e:
            print(f"❌ Error consultando Weaviate: {e}")
            return f"❌ Error consultando Weaviate: {e}"

    def _handle_dev_command(self, player_id: str, mensaje: str) -> Optional[str]:
        """
        Maneja comandos específicos de desarrollo
        """
        # Comandos de migración
        if any(keyword in mensaje.lower() for keyword in [
            "migra el proyecto", "migrar proyecto", "convertir proyecto"
        ]):
            return self.dev_agent.handle_migration_command(mensaje)
        
        # Comandos de análisis
        if any(keyword in mensaje.lower() for keyword in [
            "analiza el proyecto", "analizar proyecto", "estructura del proyecto"
        ]):
            return self.dev_agent.handle_analysis_command(mensaje)
        
        # Comandos de estadísticas
        if mensaje.lower() in ["stats", "estadísticas", "estadisticas"]:
            return self._get_comprehensive_stats()
        
        # Comandos de configuración de modelo
        if mensaje.lower().startswith("usar modelo"):
            return self._handle_model_command(mensaje)
        
        return None

    def _get_memory_context(self, player_id: str, mensaje: str) -> str:
        """
        Obtiene contexto relevante de la memoria
        """
        try:
            # Buscar recuerdos relevantes
            recuerdos = self.memory_agent.buscar_recuerdos_relevantes(
                player_id=player_id,
                consulta=mensaje,
                namespace=self.namespace,
                limite=3
            )
            
            if recuerdos:
                contexto = "📚 Información relevante de conversaciones anteriores:\n"
                for i, recuerdo in enumerate(recuerdos, 1):
                    contexto += f"{i}. {recuerdo}\n"
                return contexto + "\n"
            
            return ""
            
        except Exception as e:
            print(f"⚠️ Error obteniendo contexto de memoria: {e}")
            return ""

    def _build_complete_prompt(self, mensaje: str, contexto_memoria: str, 
                              player_id: str, context_decision: Dict) -> str:
        """
        Construye el prompt completo con toda la información necesaria
        """
        # Información del perfil
        personalidad = self.profile.get("personality", "Asistente útil")
        instrucciones = self.profile.get("instructions", "")
        
        prompt = f"""Eres {personalidad}.

{instrucciones}

{contexto_memoria}

Razón para usar memoria: {context_decision.get('reason', 'No especificada')}

Usuario ({player_id}): {mensaje}

Responde de manera natural y útil:"""
        
        return prompt

    def _detect_enhanced_task_type(self, mensaje: str) -> Optional[TaskType]:
        """
        Detecta el tipo de tarea con lógica mejorada
        """
        mensaje_lower = mensaje.lower()
        
        # Detección específica para migración
        if any(keyword in mensaje_lower for keyword in [
            "migra el proyecto", "migrar proyecto completo", "300k líneas"
        ]):
            return TaskType.MIGRACION_COMPLEJA
        
        if any(keyword in mensaje_lower for keyword in [
            "migra este archivo", "convertir archivo", "refactorizar"
        ]):
            return TaskType.MIGRACION_SENCILLA
        
        # Detección para análisis
        if any(keyword in mensaje_lower for keyword in [
            "analiza", "estructura", "dependencias", "arquitectura"
        ]):
            return TaskType.ANALISIS_CODIGO
        
        # Detección para debugging
        if any(keyword in mensaje_lower for keyword in [
            "error", "bug", "problema", "no funciona", "falla"
        ]):
            return TaskType.DEBUGGING
        
        # Detección por modo
        if self.mode == "game":
            return TaskType.CONVERSACION_JUEGO
        
        # Default para modo dev
        return TaskType.CONSULTA_SIMPLE

    def _save_to_memory(self, player_id: str, mensaje: str, respuesta: str, 
                       memory_decision: Dict):
        """
        Guarda información relevante en memoria
        """
        try:
            recuerdo_formateado = self.memory_agent.format_memory(
                user_input=mensaje,
                assistant_response=respuesta,
                category=memory_decision.get("category", "general")
            )
            
            self.memory_agent.guardar_recuerdo(
                player_id=player_id,
                recuerdo=recuerdo_formateado,
                namespace=self.namespace
            )
            
        except Exception as e:
            print(f"⚠️ Error guardando en memoria: {e}")

    def _handle_model_command(self, mensaje: str) -> str:
        """
        Maneja comandos de configuración de modelo
        """
        try:
            # Extraer el modelo solicitado
            if "ollama" in mensaje.lower():
                self.model_router.force_provider_for_session(ModelProvider.OLLAMA)
                return "🤖 Configurado para usar Ollama para toda la sesión"
            elif "claude" in mensaje.lower():
                self.model_router.force_provider_for_session(ModelProvider.CLAUDE)
                return "🤖 Configurado para usar Claude para toda la sesión"
            elif "gpt" in mensaje.lower():
                self.model_router.force_provider_for_session(ModelProvider.GPT4)
                return "🤖 Configurado para usar GPT-4 para toda la sesión"
            elif "gemini" in mensaje.lower():
                self.model_router.force_provider_for_session(ModelProvider.GEMINI)
                return "🤖 Configurado para usar Gemini para toda la sesión"
            else:
                available = self.model_router.get_available_providers()
                return f"🤖 Modelos disponibles: {', '.join(available)}\nUso: 'usar modelo [nombre]'"
                
        except Exception as e:
            return f"❌ Error configurando modelo: {e}"

    def _get_comprehensive_stats(self) -> str:
        """
        Obtiene estadísticas completas del sistema
        """
        try:
            # Stats del router de modelos
            router_stats = self.model_router.get_stats()
            
            # Stats de eficiencia
            efficiency = self.efficiency_stats
            
            # Calcular ratios
            total = efficiency["total_interactions"]
            memory_usage_ratio = (efficiency["memory_queries"] / total * 100) if total > 0 else 0
            memory_save_ratio = (efficiency["memory_saves"] / total * 100) if total > 0 else 0
            
            stats = f"""📊 **Estadísticas Completas de Samara**

🎯 **Eficiencia del Sistema:**
• Total de interacciones: {total}
• Consultas a memoria: {efficiency['memory_queries']} ({memory_usage_ratio:.1f}%)
• Guardados en memoria: {efficiency['memory_saves']} ({memory_save_ratio:.1f}%)
• Comandos de desarrollo: {efficiency['dev_commands']}
• Fallbacks usados: {efficiency['fallbacks_used']}

🤖 **Uso de Modelos:**
• Total de consultas: {router_stats['total_requests']}
• Fallbacks: {router_stats['fallbacks']}
• Errores: {router_stats['errors']}

📈 **Por Proveedor:**"""
            
            for provider, stats_data in router_stats.get('by_provider', {}).items():
                success = stats_data.get('success', 0)
                failed = stats_data.get('failed', 0)
                total_provider = success + failed
                success_rate = (success / total_provider * 100) if total_provider > 0 else 0
                stats += f"\n• {provider}: {success}/{total_provider} ({success_rate:.1f}% éxito)"
            
            stats += f"\n\n📏 **Por Tamaño de Contexto:**"
            
            # Agregar estadísticas de contexto si están disponibles
            context_stats = router_stats.get('by_context_size', {})
            if context_stats:
                for size_category, data in context_stats.items():
                    count = data.get('count', 0)
                    avg_tokens = data.get('avg_tokens', 0)
                    top_provider = max(data.get('providers', {}).items(), key=lambda x: x[1], default=('N/A', 0))[0]
                    stats += f"\n• {size_category}: {count} consultas (promedio: {avg_tokens:,} tokens, proveedor principal: {top_provider})"
            else:
                stats += "\n• (Estadísticas de contexto no disponibles aún)"
            
            stats += f"\n\n🕒 **Sesión iniciada:** {efficiency['session_start']}"
            
            return stats
            
        except Exception as e:
            return f"❌ Error obteniendo estadísticas: {e}"

    def get_conversation_history(self, player_id: str, limit: int = 10) -> List[Dict]:
        """
        Obtiene historial de conversaciones
        """
        try:
            return self.conversation_manager.get_conversation_history(
                user_id=player_id,
                mode=self.mode,
                limit=limit
            )
        except Exception as e:
            print(f"❌ Error obteniendo historial: {e}")
            return []

    def search_conversations(self, player_id: str, query: str, limit: int = 5) -> List[Dict]:
        """
        Busca en el historial de conversaciones
        """
        try:
            return self.conversation_manager.search_conversations(
                user_id=player_id,
                mode=self.mode,
                query=query,
                limit=limit
            )
        except Exception as e:
            print(f"❌ Error buscando conversaciones: {e}")
            return []

    def get_user_stats(self, player_id: str) -> Dict:
        """
        Obtiene estadísticas del usuario
        """
        try:
            return self.conversation_manager.get_user_stats(player_id, self.mode)
        except Exception as e:
            print(f"❌ Error obteniendo stats del usuario: {e}")
            return {}

    def cleanup_old_data(self, days: int = 30):
        """
        Limpia datos antiguos
        """
        try:
            # Limpiar conversaciones antiguas
            deleted_conversations = self.conversation_manager.cleanup_old_conversations(days)
            
            # Limpiar recuerdos antiguos (implementar en MemoryAgent si es necesario)
            # deleted_memories = self.memory_agent.cleanup_old_memories(days)
            
            return f"🧹 Limpieza completada: {deleted_conversations} conversaciones eliminadas"
            
        except Exception as e:
            return f"❌ Error en limpieza: {e}"

    def buscar_en_historial(self, player_id: str, query: str, limit: int = 5) -> List[Dict]:
        """
        Busca en el historial de conversaciones
        """
        try:
            return self.conversation_manager.search_conversation_history(player_id, self.mode, query, limit)
        except Exception as e:
            print(f"❌ Error buscando conversaciones: {e}")
            return []

    def buscar_en_memoria(self, player_id: str, query: str, limit: int = 5) -> List[Dict]:
        """
        Busca en los recuerdos semánticos
        """
        player_id_with_mode = f"{player_id}_{self.mode}"
        return self.memory_manager.recuperar_recuerdos(
            query=query, 
            k=limit, 
            metadatos={"player_id": player_id_with_mode}
        )

    def obtener_estadisticas_completas(self, player_id: str) -> Dict:
        """
        Obtiene estadísticas completas del usuario y la sesión
        """
        # Estadísticas de conversación
        conversation_stats = self.conversation_manager.get_conversation_stats(player_id, self.mode)
        
        # Estadísticas de memoria
        memory_stats = self.memory_agent.get_memory_stats(self.memory_manager, player_id, self.mode)
        
        return {
            "user_id": player_id,
            "mode": self.mode,
            "conversation": conversation_stats,
            "memory": memory_stats,
            "session": self.session_stats,
            "efficiency": {
                "memory_usage_rate": self.session_stats["memories_used"] / max(1, self.session_stats["messages_processed"]),
                "memory_save_rate": self.session_stats["memories_saved"] / max(1, self.session_stats["messages_processed"]),
                "context_optimization_rate": self.session_stats["context_optimizations"] / max(1, self.session_stats["messages_processed"])
            }
        }

    def obtener_contexto_debug(self, player_id: str, input_actual: str) -> Dict:
        """
        Método de debug para ver qué contexto se está usando
        """
        return self.context_agent.get_smart_context(
            conversation_manager=self.conversation_manager,
            memory_manager=self.memory_manager,
            user_id=player_id,
            mode=self.mode,
            user_input=input_actual,
            namespace=self.namespace
        )

    def limpiar_memoria_antigua(self, days_old: int = 30):
        """
        Limpia recuerdos antiguos (funcionalidad futura)
        """
        self.memory_agent.clean_old_memories(self.memory_manager, self.namespace, days_old)

    def _consultar_ollama(self, prompt: str) -> str:
        payload = {
            "model": "llama3:instruct",
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(f"{self.ollama_url}/api/generate", json=payload)
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            else:
                return f"[Error {response.status_code} al consultar Ollama]"
        except Exception as e:
            return f"[Error al conectar con Ollama: {e}]"

    def test_listar_proyectos(self):
        """Método de prueba para listar proyectos reales en Weaviate"""
        try:
            code_agent = CodeAnalysisAgent()
            weaviate_client = code_agent.weaviate_client
            clases = weaviate_client.schema.get().get('classes', [])
            proyectos = [cls['class'] for cls in clases if cls['class'].startswith('Project_')]
            if proyectos:
                proyectos_limpios = [p.replace('Project_', '') for p in proyectos]
                print("\n📂 Proyectos encontrados en Weaviate:")
                for p in proyectos_limpios:
                    print(f"- {p}")
            else:
                print("No se encontraron proyectos en Weaviate.")
        except Exception as e:
            print(f"❌ Error consultando proyectos en Weaviate: {e}")

    def test_listar_modulos_sacs3(self):
        """Muestra los primeros 5 módulos del proyecto 'sacs3'"""
        try:
            agent = CodeAnalysisAgent()
            result = agent.list_project_modules('sacs3')
            if 'error' in result:
                print(f"Error: {result['error']}")
            else:
                mods = result.get('all_modules', [])
                print(f"\nPrimeros 5 módulos de 'sacs3':")
                for i, mod in enumerate(mods[:5]):
                    nombre = mod.get('fileName', 'Sin nombre')
                    tipo = mod.get('moduleType', 'N/A')
                    print(f"{i+1}. {nombre} ({tipo})")
                if not mods:
                    print("No se encontraron módulos en 'sacs3'.")
        except Exception as e:
            print(f"❌ Error consultando módulos de 'sacs3': {e}")

    def test_analiza_modulo_login_sacs3(self):
        """Consulta y muestra el análisis del módulo 'login' del proyecto 'sacs3'"""
        try:
            code_agent = CodeAnalysisAgent()
            result = code_agent.query_project('sacs3', 'módulo login', limit=5)
            if 'error' in result:
                print(f"Error: {result['error']}")
            else:
                print("\nAnálisis IA del módulo 'login' en 'sacs3':\n")
                print(result.get('ai_response', 'No se encontró información relevante.'))
        except Exception as e:
            print(f"❌ Error consultando el módulo: {e}")

    def borrar_conversaciones_recientes(self, player_id: str):
        """Elimina todas las conversaciones recientes del usuario y modo actual en Weaviate."""
        try:
            # Usar el namespace y modo actual
            weaviate_client = self.conversation_manager.client
            where_filter = {
                "operator": "And",
                "operands": [
                    {"path": ["user_id"], "operator": "Equal", "valueString": player_id},
                    {"path": ["mode"], "operator": "Equal", "valueString": self.mode}
                ]
            }
            # Buscar los objetos a eliminar
            result = weaviate_client.query.get(
                self.conversation_manager.namespace,
                ["_additional { id }"]
            ).with_where(where_filter).with_limit(1000).do()
            if "data" in result and "Get" in result["data"] and self.conversation_manager.namespace in result["data"]["Get"]:
                objs = result["data"]["Get"][self.conversation_manager.namespace]
                for obj in objs:
                    obj_id = obj["_additional"]["id"]
                    weaviate_client.data_object.delete(obj_id, self.conversation_manager.namespace)
                print(f"✅ Conversaciones recientes eliminadas para {player_id} en modo {self.mode}.")
            else:
                print("No se encontraron conversaciones para eliminar.")
        except Exception as e:
            print(f"❌ Error eliminando conversaciones: {e}")

    def debug_weaviate_data(self):
        """Método de debug para mostrar exactamente qué datos hay en Weaviate"""
        try:
            code_agent = CodeAnalysisAgent()
            weaviate_client = code_agent.weaviate_client
            
            print("=== DEBUG: DATOS EN WEAVIATE ===\n")
            
            # Obtener clases de proyectos
            clases = weaviate_client.schema.get().get('classes', [])
            proyectos = [cls['class'] for cls in clases if cls['class'].startswith('Project_')]
            
            if not proyectos:
                print("❌ No hay proyectos indexados en Weaviate.")
                return
            
            for proyecto_clase in proyectos:
                proyecto_nombre = proyecto_clase.replace('Project_', '')
                print(f"\n📂 PROYECTO: {proyecto_nombre}")
                print(f"   Clase en Weaviate: {proyecto_clase}")
                
                # Obtener módulos detallados del proyecto
                try:
                    result = code_agent.list_project_modules(proyecto_nombre)
                    if 'error' in result:
                        print(f"   ❌ Error: {result['error']}")
                        continue
                    
                    if 'all_modules' in result:
                        modulos = result['all_modules']
                        print(f"   📊 Total módulos: {len(modulos)}")
                        
                        # Mostrar primeros 3 módulos con detalles
                        for i, mod in enumerate(modulos[:3]):
                            print(f"\n   MÓDULO {i+1}:")
                            print(f"     • Nombre: {mod.get('fileName', 'Sin nombre')}")
                            print(f"     • Tipo: {mod.get('moduleType', 'N/A')}")
                            print(f"     • Contenido: {mod.get('content', 'Sin contenido')[:100]}...")
                            print(f"     • Variables: {mod.get('variables', [])}")
                            print(f"     • Funciones: {mod.get('functions', [])}")
                        
                        if len(modulos) > 3:
                            print(f"   ... y {len(modulos) - 3} módulos más")
                    else:
                        print("   ❌ No se encontraron módulos")
                        
                    # Probar consulta específica
                    print(f"\n   🔍 PRUEBA DE CONSULTA ESPECÍFICA:")
                    query_result = code_agent.query_project(proyecto_nombre, "login", limit=3)
                    if 'error' in query_result:
                        print(f"     ❌ Error en consulta: {query_result['error']}")
                    else:
                        print(f"     ✅ Respuesta IA: {query_result.get('ai_response', 'Sin respuesta')[:200]}...")
                        
                except Exception as e:
                    print(f"   ❌ Error obteniendo módulos: {e}")
                    
        except Exception as e:
            print(f"❌ Error general: {e}")
        
        print("\n=== FIN DEBUG ===") 