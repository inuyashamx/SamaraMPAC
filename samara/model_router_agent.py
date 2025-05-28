import os
import json
import requests
from typing import Dict, List, Optional, Tuple
from enum import Enum
import time
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class TaskType(Enum):
    """Tipos de tareas para el enrutamiento de modelos"""
    MIGRACION_COMPLEJA = "migracion_compleja"
    MIGRACION_SENCILLA = "migracion_sencilla"
    ANALISIS_CODIGO = "analisis_codigo"
    CONVERSACION_JUEGO = "conversacion_juego"
    REFACTORING = "refactoring"
    DEBUGGING = "debugging"
    DOCUMENTACION = "documentacion"
    CONSULTA_SIMPLE = "consulta_simple"
    ARQUITECTURA = "arquitectura"

class ModelProvider(Enum):
    """Proveedores de modelos disponibles"""
    OLLAMA = "ollama"
    CLAUDE = "claude"
    GPT4 = "gpt4"
    GEMINI = "gemini"
    PERPLEXITY = "perplexity"

class ModelRouterAgent:
    """
    Meta-agente que orquesta múltiples LLMs y decide dinámicamente
    cuál usar según la tarea, complejidad, costo y disponibilidad.
    """
    
    def __init__(self):
        # Configuración de modelos con límites de contexto reales
        self.model_config = {
            ModelProvider.OLLAMA: {
                "url": "http://localhost:11434",
                "models": ["llama3:instruct", "mistral", "phi3", "codellama"],
                "cost": 0,  # Gratis (local)
                "speed": "fast",
                "quality": "good",
                "context_limit": 8192,  # Llama3 típico
                "optimal_context": 4096  # Funciona mejor con contextos menores
            },
            ModelProvider.CLAUDE: {
                "api_key": os.getenv("CLAUDE_API_KEY"),
                "url": "https://api.anthropic.com/v1/messages",
                "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
                "cost": 3,  # Alto
                "speed": "medium",
                "quality": "excellent",
                "context_limit": 200000,  # Claude 3 - 200k tokens
                "optimal_context": 100000  # Funciona excelente con contextos grandes
            },
            ModelProvider.GPT4: {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "url": "https://api.openai.com/v1/chat/completions",
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "cost": 2,  # Medio-Alto
                "speed": "medium",
                "quality": "excellent",
                "context_limit": 128000,  # GPT-4 Turbo - 128k tokens
                "optimal_context": 64000  # Funciona muy bien con contextos grandes
            },
            ModelProvider.GEMINI: {
                "api_key": os.getenv("GEMINI_API_KEY"),
                "url": "https://generativelanguage.googleapis.com/v1beta/models",
                "models": ["gemini-pro", "gemini-pro-vision"],
                "cost": 1,  # Bajo-Medio
                "speed": "fast",
                "quality": "very_good",
                "context_limit": 32768,  # Gemini Pro - 32k tokens
                "optimal_context": 16384  # Funciona bien con contextos medianos
            },
            ModelProvider.PERPLEXITY: {
                "api_key": os.getenv("PERPLEXITY_API_KEY"),
                "url": "https://api.perplexity.ai/chat/completions",
                "models": ["llama-3-sonar-large-32k-online", "llama-3-sonar-small-32k-online"],
                "cost": 1,  # Bajo
                "speed": "fast",
                "quality": "good",
                "context_limit": 32768,  # Sonar 32k
                "optimal_context": 16384  # Funciona bien con contextos medianos
            }
        }
        
        # Reglas de enrutamiento por tipo de tarea
        self.routing_rules = {
            TaskType.MIGRACION_COMPLEJA: [
                ModelProvider.CLAUDE,
                ModelProvider.GPT4,
                ModelProvider.GEMINI,
                ModelProvider.OLLAMA  # Fallback
            ],
            TaskType.MIGRACION_SENCILLA: [
                ModelProvider.OLLAMA,
                ModelProvider.GEMINI,
                ModelProvider.GPT4
            ],
            TaskType.ANALISIS_CODIGO: [
                ModelProvider.CLAUDE,
                ModelProvider.GPT4,
                ModelProvider.OLLAMA
            ],
            TaskType.CONVERSACION_JUEGO: [
                ModelProvider.OLLAMA,
                ModelProvider.GEMINI,
                ModelProvider.PERPLEXITY
            ],
            TaskType.REFACTORING: [
                ModelProvider.CLAUDE,
                ModelProvider.OLLAMA,
                ModelProvider.GPT4
            ],
            TaskType.DEBUGGING: [
                ModelProvider.GPT4,
                ModelProvider.CLAUDE,
                ModelProvider.OLLAMA
            ],
            TaskType.DOCUMENTACION: [
                ModelProvider.GEMINI,
                ModelProvider.OLLAMA,
                ModelProvider.CLAUDE
            ],
            TaskType.CONSULTA_SIMPLE: [
                ModelProvider.OLLAMA,
                ModelProvider.PERPLEXITY,
                ModelProvider.GEMINI
            ],
            TaskType.ARQUITECTURA: [
                ModelProvider.CLAUDE,
                ModelProvider.GPT4,
                ModelProvider.GEMINI
            ]
        }
        
        # Estadísticas de uso
        self.usage_stats = {
            "total_requests": 0,
            "by_provider": {},
            "by_task_type": {},
            "by_context_size": {},
            "fallbacks": 0,
            "errors": 0
        }

        # Filtrar solo proveedores disponibles al inicializar (después de definir routing_rules)
        self._filter_available_providers()

    def _filter_available_providers(self):
        """
        Filtra las reglas de enrutamiento para incluir solo proveedores disponibles
        """
        available_providers = []
        unavailable_providers = []
        
        # Verificar qué proveedores están realmente disponibles
        for provider in ModelProvider:
            if self._is_provider_available(provider):
                available_providers.append(provider)
            else:
                unavailable_providers.append(provider)
        
        print(f"🔍 Verificando proveedores de IA...")
        
        # Mostrar proveedores disponibles
        if available_providers:
            print(f"✅ Proveedores disponibles: {[p.value for p in available_providers]}")
            
            if ModelProvider.OLLAMA in available_providers:
                print("🏠 Ollama local disponible (gratis) - usado para indexación")
            
            cloud_providers = [p for p in available_providers if p != ModelProvider.OLLAMA]
            if cloud_providers:
                print(f"☁️ Proveedores cloud disponibles: {[p.value for p in cloud_providers]}")
        
        # Mostrar proveedores no disponibles
        if unavailable_providers:
            print(f"⚠️ Proveedores sin configurar: {[p.value for p in unavailable_providers]}")
            
            missing_keys = []
            for provider in unavailable_providers:
                if provider == ModelProvider.OLLAMA:
                    print("   • Ollama: No está ejecutándose en http://localhost:11434")
                else:
                    key_name = f"{provider.value.upper()}_API_KEY"
                    missing_keys.append(key_name)
            
            if missing_keys:
                print(f"   • API keys faltantes: {', '.join(missing_keys)}")
                print("   • Configúralas en el archivo .env para habilitar más opciones")
        
        # Si no hay proveedores disponibles, mostrar error
        if not available_providers:
            print("❌ ERROR: No hay proveedores de IA disponibles!")
            print("💡 Soluciones:")
            print("   • Instala y ejecuta Ollama: curl -fsSL https://ollama.ai/install.sh | sh")
            print("   • O configura API keys en el archivo .env")
            return
        
        # Actualizar reglas de enrutamiento con solo proveedores disponibles
        for task_type in self.routing_rules:
            # Filtrar la lista para incluir solo proveedores disponibles
            filtered_providers = [p for p in self.routing_rules[task_type] if p in available_providers]
            
            # Si no queda ningún proveedor para esta tarea, usar el primero disponible
            if not filtered_providers:
                filtered_providers = [available_providers[0]]
            
            self.routing_rules[task_type] = filtered_providers
        
        # Mostrar configuración final
        print(f"✅ Sistema configurado con {len(available_providers)} proveedor(es)")
        
        if len(available_providers) == 1 and ModelProvider.OLLAMA in available_providers:
            print("💡 Solo Ollama disponible - perfecto para indexación, considera agregar API keys para análisis avanzado")

    def route_and_query(self, prompt: str, task_type: Optional[TaskType] = None, mode: str = "default", context_size: int = 0, max_tokens: int = 1024, temperature: float = 0.7) -> Dict:
        """
        Enruta inteligentemente la consulta al mejor proveedor disponible según la tarea, contexto y disponibilidad.
        """
        # Actualizar estadísticas totales
        self.usage_stats["total_requests"] += 1
        
        try:
            # 1. DETECTAR TIPO DE TAREA SI NO SE ESPECIFICA
            if task_type is None:
                task_type = self._detect_task_type(prompt, mode)
            
            # 2. ESTIMAR TAMAÑO DE CONTEXTO SI NO SE ESPECIFICA
            if context_size == 0:
                context_size = self._estimate_context_size(prompt)
            
            # 3. SELECCIONAR MEJOR PROVEEDOR
            selected_provider = self._select_best_provider(task_type, prompt, context_size)
            
            # 4. EJECUTAR CON SISTEMA DE FALLBACK
            result = self._execute_with_fallback(
                provider=selected_provider,
                prompt=prompt,
                task_type=task_type,
                max_tokens=max_tokens,
                temperature=temperature,
                context_size=context_size
            )
            
            # 5. ACTUALIZAR ESTADÍSTICAS
            self._update_stats(selected_provider, task_type, result["success"], context_size)
            
            # 6. AGREGAR METADATA AL RESULTADO
            result.update({
                "task_type": task_type.value,
                "context_size": context_size,
                "selected_provider": selected_provider.value
            })
            
            return result
            
        except Exception as e:
            # Error en el enrutamiento
            self.usage_stats["errors"] += 1
            return {
                "success": False,
                "error": f"Error en enrutamiento: {str(e)}",
                "provider": "none",
                "task_type": task_type.value if task_type else "unknown",
                "context_size": context_size
            }

    def _categorize_context_size(self, context_size: int) -> str:
        """Categoriza el tamaño del contexto"""
        if context_size < 500:
            return "muy_pequeño"
        elif context_size < 2000:
            return "pequeño"
        elif context_size < 10000:
            return "mediano"
        elif context_size < 30000:
            return "grande"
        else:
            return "muy_grande"

    def _detect_task_type(self, prompt: str, mode: str) -> TaskType:
        """
        Detecta automáticamente el tipo de tarea basado en el prompt y modo
        """
        prompt_lower = prompt.lower()
        
        # Palabras clave para cada tipo de tarea
        keywords = {
            TaskType.MIGRACION_COMPLEJA: [
                "migra el proyecto", "migrar proyecto", "convertir proyecto",
                "300k líneas", "proyecto completo", "migración masiva"
            ],
            TaskType.MIGRACION_SENCILLA: [
                "migra este archivo", "convertir archivo", "cambiar de",
                "refactorizar", "actualizar código"
            ],
            TaskType.ANALISIS_CODIGO: [
                "analiza el proyecto", "analizar código", "estructura del proyecto",
                "dependencias", "patrones", "arquitectura", "fragmentos",
                "funciones", "clases", "componentes", "módulos", "que hace",
                "cómo funciona", "explicar código", "revisar código"
            ],
            TaskType.CONVERSACION_JUEGO: [
                "puntaje", "nivel", "juego", "personaje", "historia",
                "aventura", "quest", "misión"
            ],
            TaskType.DEBUGGING: [
                "error", "bug", "problema", "no funciona", "falla",
                "excepción", "debug", "arreglar", "solucionar"
            ],
            TaskType.DOCUMENTACION: [
                "documenta", "explicar", "cómo funciona", "tutorial",
                "guía", "readme", "comentarios", "documentación"
            ],
            TaskType.ARQUITECTURA: [
                "diseño", "arquitectura", "patrones", "estructura",
                "escalabilidad", "performance", "organización"
            ],
            TaskType.CONSULTA_SIMPLE: [
                "qué es", "cuál es", "dónde está", "cuándo", "por qué",
                "buscar", "encontrar", "mostrar", "listar"
            ]
        }
        
        # Detectar por palabras clave
        for task_type, words in keywords.items():
            if any(word in prompt_lower for word in words):
                return task_type
        
        # Detectar por modo
        if mode == "game":
            return TaskType.CONVERSACION_JUEGO
        elif mode == "dev":
            # Si es dev pero no detectamos nada específico, asumir análisis de código
            return TaskType.ANALISIS_CODIGO
        
        return TaskType.CONSULTA_SIMPLE

    def _estimate_context_size(self, prompt: str) -> int:
        """
        Estima el tamaño del contexto en tokens (aproximado)
        Regla general: ~4 caracteres = 1 token en español
        """
        # Estimación básica: 4 caracteres por token
        estimated_tokens = len(prompt) // 4
        
        # Ajustes por tipo de contenido
        if any(keyword in prompt.lower() for keyword in ["código", "code", "función", "class", "import", "fragmentos"]):
            # El código tiende a tener más tokens por carácter
            estimated_tokens = int(estimated_tokens * 1.2)
        
        if any(keyword in prompt.lower() for keyword in ["proyecto completo", "migración masiva", "300k líneas"]):
            # Proyectos grandes probablemente necesitarán mucho contexto
            estimated_tokens = max(estimated_tokens, 50000)
        
        return estimated_tokens

    def _select_best_provider(self, task_type: TaskType, prompt: str, context_size: int) -> ModelProvider:
        """
        Selecciona el mejor proveedor considerando tarea y tamaño de contexto
        """
        # Obtener proveedores ordenados por prioridad para esta tarea (ya filtrados)
        preferred_providers = self.routing_rules.get(task_type, [])
        
        # Si no hay proveedores para esta tarea, obtener cualquier disponible
        if not preferred_providers:
            available = self.get_available_providers()
            if not available:
                raise Exception("No hay proveedores de IA disponibles")
            return ModelProvider(available[0])
        
        # 1. FILTRAR POR CAPACIDAD DE CONTEXTO
        context_capable_providers = []
        for provider in preferred_providers:
            config = self.model_config[provider]
            if context_size <= config["context_limit"]:
                context_capable_providers.append(provider)
        
        # Si ningún proveedor puede manejar el contexto, usar el de mayor capacidad
        if not context_capable_providers:
            print(f"⚠️ Contexto grande ({context_size} tokens) - usando proveedor de mayor capacidad")
            max_context_provider = max(preferred_providers, 
                                     key=lambda p: self.model_config[p]["context_limit"])
            return max_context_provider
        
        # 2. SELECCIÓN INTELIGENTE BASADA EN CONTEXTO Y TAREA
        
        # Para contextos muy grandes (>30k tokens), preferir Claude o GPT-4
        if context_size > 30000:
            for provider in [ModelProvider.CLAUDE, ModelProvider.GPT4]:
                if provider in context_capable_providers:
                    print(f"🧠 Contexto muy grande ({context_size:,} tokens) → {provider.value}")
                    return provider
        
        # Para contextos grandes (>10k tokens), preferir modelos cloud
        elif context_size > 10000:
            cloud_providers = [p for p in context_capable_providers 
                             if p != ModelProvider.OLLAMA]
            if cloud_providers:
                # Ordenar por capacidad de contexto óptimo
                best_cloud = max(cloud_providers, 
                               key=lambda p: self.model_config[p]["optimal_context"])
                print(f"☁️ Contexto grande ({context_size:,} tokens) → {best_cloud.value}")
                return best_cloud
        
        # Para contextos medianos (2k-10k tokens), considerar todos
        elif context_size > 2000:
            # Para análisis de código, preferir modelos cloud sobre Ollama
            if task_type == TaskType.ANALISIS_CODIGO:
                cloud_providers = [p for p in context_capable_providers 
                                 if p != ModelProvider.OLLAMA]
                if cloud_providers:
                    # Preferir GPT-4 para análisis de código
                    if ModelProvider.GPT4 in cloud_providers:
                        print(f"🧠 Análisis de código ({context_size:,} tokens) → GPT-4")
                        return ModelProvider.GPT4
                    # Fallback a Claude
                    elif ModelProvider.CLAUDE in cloud_providers:
                        print(f"🧠 Análisis de código ({context_size:,} tokens) → Claude")
                        return ModelProvider.CLAUDE
            
            # Preferir proveedores que manejen bien este tamaño
            optimal_providers = [p for p in context_capable_providers 
                               if context_size <= self.model_config[p]["optimal_context"]]
            if optimal_providers:
                # Aplicar lógica de tarea dentro de los óptimos
                return self._apply_task_logic(optimal_providers, task_type, prompt)
        
        # Para contextos pequeños (<2k tokens), preferir Ollama si está disponible
        else:
            if ModelProvider.OLLAMA in context_capable_providers:
                print(f"🏠 Contexto pequeño ({context_size:,} tokens) → Ollama (local)")
                return ModelProvider.OLLAMA
        
        # 3. APLICAR LÓGICA DE TAREA COMO FALLBACK
        return self._apply_task_logic(context_capable_providers, task_type, prompt)

    def _apply_task_logic(self, available_providers: List[ModelProvider], 
                         task_type: TaskType, prompt: str) -> ModelProvider:
        """
        Aplica lógica específica de tarea entre proveedores disponibles
        """
        prompt_lower = prompt.lower()
        is_complex = len(prompt) > 1000 or "complejo" in prompt_lower
        
        # Para tareas complejas, preferir modelos cloud
        if is_complex and task_type in [TaskType.MIGRACION_COMPLEJA, TaskType.ARQUITECTURA]:
            for provider in [ModelProvider.CLAUDE, ModelProvider.GPT4]:
                if provider in available_providers:
                    return provider
        
        # Para debugging, preferir GPT-4
        if task_type == TaskType.DEBUGGING:
            if ModelProvider.GPT4 in available_providers:
                return ModelProvider.GPT4
        
        # Para documentación, preferir Gemini
        if task_type == TaskType.DOCUMENTACION:
            if ModelProvider.GEMINI in available_providers:
                return ModelProvider.GEMINI
        
        # Para tareas simples, preferir Ollama
        if task_type in [TaskType.CONSULTA_SIMPLE, TaskType.CONVERSACION_JUEGO]:
            if ModelProvider.OLLAMA in available_providers:
                return ModelProvider.OLLAMA
        
        # Fallback: usar el primero disponible
        return available_providers[0]

    def _is_provider_available(self, provider: ModelProvider) -> bool:
        """
        Verifica si un proveedor está disponible
        """
        config = self.model_config[provider]
        
        if provider == ModelProvider.OLLAMA:
            # Verificar si Ollama está corriendo
            try:
                response = requests.get(f"{config['url']}/api/tags", timeout=2)
                return response.status_code == 200
            except:
                return False
        else:
            # Para proveedores cloud, verificar si hay API key configurada
            api_key = config.get("api_key")
            if api_key is None or api_key.strip() == "":
                return False
            return True

    def _execute_with_fallback(self, 
                              provider: ModelProvider, 
                              prompt: str, 
                              task_type: TaskType,
                              max_tokens: int,
                              temperature: float,
                              context_size: int) -> Dict:
        """
        Ejecuta la consulta con sistema de fallback (solo proveedores disponibles)
        """
        # Intentar con el proveedor seleccionado
        result = self._call_provider(provider, prompt, max_tokens, temperature)
        
        if result["success"]:
            return result
        
        # Si falla, intentar fallbacks (solo de la lista ya filtrada)
        self.usage_stats["fallbacks"] += 1
        fallback_providers = self.routing_rules.get(task_type, [])
        
        for fallback_provider in fallback_providers:
            if fallback_provider != provider:
                result = self._call_provider(fallback_provider, prompt, max_tokens, temperature)
                if result["success"]:
                    result["used_fallback"] = True
                    result["original_provider"] = provider.value
                    return result
        
        # Si los fallbacks de la tarea fallan, intentar con cualquier proveedor disponible
        all_available = self.get_available_providers()
        for provider_name in all_available:
            fallback_provider = ModelProvider(provider_name)
            if fallback_provider != provider and fallback_provider not in fallback_providers:
                result = self._call_provider(fallback_provider, prompt, max_tokens, temperature)
                if result["success"]:
                    result["used_fallback"] = True
                    result["original_provider"] = provider.value
                    return result
        
        # Si todo falla
        self.usage_stats["errors"] += 1
        return {
            "success": False,
            "response": "❌ Error: No se pudo conectar con ningún modelo disponible. Verifica tu configuración.",
            "provider": provider.value,
            "error": "All available providers failed"
        }

    def _call_provider(self, 
                      provider: ModelProvider, 
                      prompt: str,
                      max_tokens: int,
                      temperature: float) -> Dict:
        """
        Llama al proveedor específico
        """
        try:
            if provider == ModelProvider.OLLAMA:
                return self._call_ollama(prompt, max_tokens, temperature)
            elif provider == ModelProvider.CLAUDE:
                return self._call_claude(prompt, max_tokens, temperature)
            elif provider == ModelProvider.GPT4:
                return self._call_gpt4(prompt, max_tokens, temperature)
            elif provider == ModelProvider.GEMINI:
                return self._call_gemini(prompt, max_tokens, temperature)
            elif provider == ModelProvider.PERPLEXITY:
                return self._call_perplexity(prompt, max_tokens, temperature)
            else:
                return {"success": False, "error": f"Provider {provider} not implemented"}
        except Exception as e:
            return {"success": False, "error": str(e), "provider": provider.value}

    def _call_ollama(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Llama a Ollama local"""
        config = self.model_config[ModelProvider.OLLAMA]
        
        payload = {
            "model": "llama3:instruct",
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        response = requests.post(f"{config['url']}/api/generate", json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result.get("response", "").strip(),
                "provider": ModelProvider.OLLAMA.value,
                "model": "llama3:instruct"
            }
        else:
            return {"success": False, "error": f"Ollama error: {response.status_code}"}

    def _call_claude(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Llama a Claude API"""
        config = self.model_config[ModelProvider.CLAUDE]
        
        if not config.get("api_key"):
            return {"success": False, "error": "Claude API key not configured"}
        
        headers = {
            "x-api-key": config["api_key"],
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": "claude-3-sonnet-20240229",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post(config["url"], headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result["content"][0]["text"],
                "provider": ModelProvider.CLAUDE.value,
                "model": "claude-3-sonnet"
            }
        else:
            return {"success": False, "error": f"Claude error: {response.status_code}"}

    def _call_gpt4(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Llama a GPT-4 API"""
        config = self.model_config[ModelProvider.GPT4]
        
        if not config.get("api_key"):
            return {"success": False, "error": "OpenAI API key not configured"}
        
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(config["url"], headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result["choices"][0]["message"]["content"],
                "provider": ModelProvider.GPT4.value,
                "model": "gpt-4"
            }
        else:
            return {"success": False, "error": f"GPT-4 error: {response.status_code}"}

    def _call_gemini(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Llama a Gemini API"""
        config = self.model_config[ModelProvider.GEMINI]
        
        if not config.get("api_key"):
            return {"success": False, "error": "Gemini API key not configured"}
        
        url = f"{config['url']}/gemini-pro:generateContent?key={config['api_key']}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result["candidates"][0]["content"]["parts"][0]["text"],
                "provider": ModelProvider.GEMINI.value,
                "model": "gemini-pro"
            }
        else:
            return {"success": False, "error": f"Gemini error: {response.status_code}"}

    def _call_perplexity(self, prompt: str, max_tokens: int, temperature: float) -> Dict:
        """Llama a Perplexity API"""
        config = self.model_config[ModelProvider.PERPLEXITY]
        
        if not config.get("api_key"):
            return {"success": False, "error": "Perplexity API key not configured"}
        
        headers = {
            "Authorization": f"Bearer {config['api_key']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3-sonar-small-32k-online",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(config["url"], headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "response": result["choices"][0]["message"]["content"],
                "provider": ModelProvider.PERPLEXITY.value,
                "model": "llama-3-sonar"
            }
        else:
            return {"success": False, "error": f"Perplexity error: {response.status_code}"}

    def _update_stats(self, provider: ModelProvider, task_type: TaskType, success: bool, context_size: int):
        """Actualiza estadísticas de uso incluyendo contexto"""
        provider_name = provider.value
        task_name = task_type.value
        context_category = self._categorize_context_size(context_size)
        
        # Estadísticas por proveedor
        if provider_name not in self.usage_stats["by_provider"]:
            self.usage_stats["by_provider"][provider_name] = {"success": 0, "failed": 0}
        
        # Estadísticas por tipo de tarea
        if task_name not in self.usage_stats["by_task_type"]:
            self.usage_stats["by_task_type"][task_name] = {"success": 0, "failed": 0}
        
        # Estadísticas por tamaño de contexto
        if context_category not in self.usage_stats["by_context_size"]:
            self.usage_stats["by_context_size"][context_category] = {"count": 0, "avg_tokens": 0, "providers": {}}
        
        # Actualizar contadores
        if success:
            self.usage_stats["by_provider"][provider_name]["success"] += 1
            self.usage_stats["by_task_type"][task_name]["success"] += 1
        else:
            self.usage_stats["by_provider"][provider_name]["failed"] += 1
            self.usage_stats["by_task_type"][task_name]["failed"] += 1
        
        # Actualizar estadísticas de contexto
        context_stats = self.usage_stats["by_context_size"][context_category]
        old_count = context_stats["count"]
        old_avg = context_stats["avg_tokens"]
        
        # Calcular nuevo promedio de tokens
        context_stats["count"] = old_count + 1
        context_stats["avg_tokens"] = ((old_avg * old_count) + context_size) // context_stats["count"]
        
        # Contar uso por proveedor en esta categoría de contexto
        if provider_name not in context_stats["providers"]:
            context_stats["providers"][provider_name] = 0
        context_stats["providers"][provider_name] += 1

    def get_stats(self) -> Dict:
        """Obtiene estadísticas de uso"""
        return self.usage_stats

    def get_available_providers(self) -> List[str]:
        """Lista proveedores disponibles"""
        available = []
        for provider in ModelProvider:
            if self._is_provider_available(provider):
                available.append(provider.value)
        return available

    def force_provider_for_session(self, provider: ModelProvider):
        """Fuerza un proveedor específico para toda la sesión"""
        # Modificar todas las reglas para usar solo este proveedor
        for task_type in self.routing_rules:
            self.routing_rules[task_type] = [provider] 

    # Métodos de conveniencia para casos comunes
    def query_code_analysis(self, prompt: str, context_size: int = 0) -> Dict:
        """Método de conveniencia para análisis de código"""
        return self.route_and_query(
            prompt=prompt,
            task_type=TaskType.ANALISIS_CODIGO,
            mode="dev",
            context_size=context_size,
            temperature=0.3  # Más determinístico para código
        )
    
    def query_simple(self, prompt: str) -> Dict:
        """Método de conveniencia para consultas simples"""
        return self.route_and_query(
            prompt=prompt,
            task_type=TaskType.CONSULTA_SIMPLE,
            temperature=0.7
        )
    
    def query_documentation(self, prompt: str, context_size: int = 0) -> Dict:
        """Método de conveniencia para documentación"""
        return self.route_and_query(
            prompt=prompt,
            task_type=TaskType.DOCUMENTACION,
            context_size=context_size,
            temperature=0.5
        ) 