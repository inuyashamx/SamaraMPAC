# 🧠 Meta-Agente Orquestador de Samara

## 🎯 Descripción

El **Meta-Agente Orquestador** es el cerebro inteligente de Samara que decide dinámicamente qué modelo de IA usar según la tarea, complejidad, costo y disponibilidad. Es un sistema completo que orquesta múltiples LLMs y agentes especializados para ofrecer la mejor experiencia posible.

## 🚀 Características Principales

### 🤖 Enrutamiento Inteligente de Modelos
- **Detección automática** del tipo de tarea
- **Análisis de contexto** - considera el tamaño en tokens
- **Selección dinámica** del mejor modelo para cada situación
- **Sistema de fallback** robusto con múltiples proveedores
- **Optimización de costos** y velocidad basada en contexto

### 🧠 Agentes Especializados
- **ContextAgent**: Decide cuándo usar memoria
- **MemoryAgent**: Gestiona qué guardar en memoria
- **SamaraDevAgent**: Comandos especializados de desarrollo
- **ConversationManager**: Historial completo en Weaviate

### 📊 Estadísticas Avanzadas
- Uso por proveedor y tipo de tarea
- Ratios de eficiencia de memoria
- Fallbacks y errores
- Analytics por usuario

## 🛠️ Proveedores Soportados

| Proveedor | Modelos | Contexto | Costo | Velocidad | Calidad | Uso Recomendado |
|-----------|---------|----------|-------|-----------|---------|-----------------|
| **Ollama** | Llama3, Mistral, Phi3 | 8K tokens | Gratis | Rápido | Bueno | Conversación, tareas simples |
| **Claude** | Claude-3 Opus/Sonnet | 200K tokens | Alto | Medio | Excelente | Migración compleja, contextos grandes |
| **GPT-4** | GPT-4, GPT-4 Turbo | 128K tokens | Medio-Alto | Medio | Excelente | Debugging, arquitectura, contextos grandes |
| **Gemini** | Gemini Pro | 32K tokens | Bajo-Medio | Rápido | Muy Bueno | Documentación, contextos medianos |
| **Perplexity** | Llama-3 Sonar | 32K tokens | Bajo | Rápido | Bueno | Búsquedas, información actual |

## 📋 Tipos de Tareas Detectadas

### 🔄 Migración
- **Compleja**: Proyectos completos (300k+ líneas) → Claude/GPT-4
- **Sencilla**: Archivos individuales → Ollama/Gemini

### 🔍 Análisis y Desarrollo
- **Análisis de Código**: Estructura, dependencias → Claude/GPT-4
- **Debugging**: Errores, problemas → GPT-4/Claude
- **Refactoring**: Mejoras de código → Claude/Ollama
- **Arquitectura**: Diseño de sistemas → Claude/GPT-4

### 📚 Documentación y Consultas
- **Documentación**: Explicaciones, tutoriales → Gemini/Ollama
- **Consulta Simple**: Preguntas generales → Ollama/Perplexity
- **Conversación/Juego**: Modo game → Ollama/Gemini

## ⚙️ Configuración

### 1. Variables de Entorno

Copia `env_example.txt` a `.env` y configura tus API keys:

```bash
# Claude (Anthropic)
CLAUDE_API_KEY=tu_claude_api_key_aqui

# OpenAI (GPT-4)
OPENAI_API_KEY=tu_openai_api_key_aqui

# Google Gemini
GEMINI_API_KEY=tu_gemini_api_key_aqui

# Perplexity AI
PERPLEXITY_API_KEY=tu_perplexity_api_key_aqui

# Ollama (local)
OLLAMA_URL=http://localhost:11434
```

### 2. Instalar Ollama (Recomendado)

```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar modelos
ollama pull llama3:instruct
ollama pull mistral
ollama pull phi3
```

### 3. Dependencias Python

```bash
pip install requests weaviate-client python-dotenv
```

## 🎮 Uso

### Verificar Configuración (Recomendado primero)
```bash
python verificar_configuracion.py
```

### Modo Básico
```bash
python samara_chat.py dev
```

### Demo Completo
```bash
python demo_meta_agente.py
```

### Demo de Enrutamiento Inteligente
```bash
python demo_contexto_inteligente.py
```

### Comandos Especiales

#### 🔧 Configuración de Modelo
```
usar modelo ollama    # Fuerza Ollama para toda la sesión
usar modelo claude    # Fuerza Claude para toda la sesión
usar modelo gpt       # Fuerza GPT-4 para toda la sesión
```

#### 📊 Estadísticas
```
stats                 # Muestra estadísticas completas
estadísticas         # Alias en español
```

#### 🚀 Comandos de Desarrollo
```
migra el proyecto en /ruta de polymer a react
analiza el proyecto en /ruta
```

## 🧠 Lógica de Enrutamiento

### Detección Automática
El sistema analiza el prompt y detecta automáticamente:

1. **Palabras clave específicas**
2. **Tamaño del contexto** (estimación en tokens)
3. **Longitud y complejidad**
4. **Modo de operación** (dev/game)
5. **Contexto de conversación**

### 📏 Enrutamiento Basado en Contexto

#### Estimación de Tokens
- **Regla base**: ~4 caracteres = 1 token en español
- **Ajuste por código**: +20% para contenido técnico
- **Proyectos grandes**: Mínimo 50k tokens estimados

#### Estrategia de Selección por Tamaño

| Tamaño de Contexto | Estrategia | Modelos Preferidos |
|-------------------|------------|-------------------|
| **Muy Pequeño** (<1K tokens) | Local rápido | Ollama |
| **Pequeño** (1K-5K tokens) | Local si es simple | Ollama → Gemini |
| **Mediano** (5K-20K tokens) | Modelo óptimo | Según tarea y capacidad |
| **Grande** (20K-50K tokens) | Cloud especializado | Gemini → GPT-4 → Claude |
| **Muy Grande** (>50K tokens) | Máxima capacidad | Claude → GPT-4 |

### Selección de Proveedor
```python
# Ejemplo de lógica de decisión mejorada
if contexto > 50000:  # Contexto muy grande
    preferir: Claude (200K) > GPT-4 (128K)
elif contexto > 20000:  # Contexto grande
    if tarea == MIGRACION_COMPLEJA:
        preferir: Claude > GPT-4 > Gemini
    elif tarea == DEBUGGING:
        preferir: GPT-4 > Claude > Gemini
elif contexto < 5000:  # Contexto pequeño
    preferir: Ollama (local, gratis)
else:  # Contexto mediano
    aplicar_logica_de_tarea()
```

### Sistema de Fallback
Si el proveedor principal falla:
1. Intenta con el siguiente en la lista de prioridad
2. Registra el fallback en estadísticas
3. Informa al usuario (solo en modo dev)

## 📈 Memoria Inteligente

### Cuándo SE GUARDA en memoria:
- ✅ Información técnica importante
- ✅ Configuraciones de proyecto
- ✅ Errores y soluciones
- ✅ Preferencias del usuario

### Cuándo NO se guarda:
- ❌ Saludos simples ("Hola", "Gracias")
- ❌ Confirmaciones básicas ("Ok", "Sí")
- ❌ Consultas muy generales
- ❌ Información temporal

### Cuándo SE USA memoria:
- 🔍 Consultas técnicas complejas
- 🔍 Referencias a conversaciones previas
- 🔍 Mensajes largos (>50 caracteres)
- 🔍 Palabras clave técnicas

## 📊 Estadísticas del Sistema

### Métricas de Eficiencia
- **Ratio de uso de memoria**: % de consultas que usan memoria
- **Ratio de guardado**: % de respuestas guardadas
- **Tasa de fallback**: % de consultas que usaron fallback
- **Distribución por proveedor**: Uso de cada modelo

### Ejemplo de Salida
```
📊 Estadísticas Completas de Samara

🎯 Eficiencia del Sistema:
• Total de interacciones: 25
• Consultas a memoria: 8 (32.0%)
• Guardados en memoria: 5 (20.0%)
• Comandos de desarrollo: 3
• Fallbacks usados: 1

🤖 Uso de Modelos:
• Total de consultas: 25
• Fallbacks: 1
• Errores: 0

📈 Por Proveedor:
• ollama: 15/20 (75.0% éxito)
• claude: 3/3 (100.0% éxito)
• gpt4: 2/2 (100.0% éxito)
```

## 🔧 Arquitectura del Sistema

```
SmartConversationalAgent
├── ModelRouterAgent (Orquestador principal)
├── ContextAgent (Decisiones de memoria)
├── MemoryAgent (Gestión de recuerdos)
├── ConversationManager (Historial completo)
├── SamaraDevAgent (Comandos especializados)
└── Proveedores:
    ├── Ollama (Local)
    ├── Claude (API)
    ├── GPT-4 (API)
    ├── Gemini (API)
    └── Perplexity (API)
```

## 🎯 Casos de Uso

### 1. Desarrollador Individual
- **Migración de proyectos**: Polymer → React
- **Debugging**: Análisis de errores
- **Consultas rápidas**: Ollama local
- **Tareas complejas**: Claude/GPT-4 automático

### 2. Equipo de Desarrollo
- **Análisis de arquitectura**: GPT-4 para diseño
- **Documentación**: Gemini para explicaciones
- **Code reviews**: Claude para análisis profundo
- **Consultas diarias**: Ollama para velocidad

### 3. Empresa/Startup
- **Migración masiva**: 300k líneas con Claude
- **Optimización de costos**: Ollama para tareas simples
- **Fallback garantizado**: Múltiples proveedores
- **Analytics detallados**: Métricas de uso

## 🚨 Manejo de Errores

### Errores Comunes
1. **API Key no configurada**: Fallback automático a Ollama
2. **Ollama no disponible**: Mensaje de error claro
3. **Rate limiting**: Espera automática y reintento
4. **Timeout**: Fallback a proveedor más rápido

### Logs y Debugging
- Errores registrados en estadísticas
- Información de fallback en modo dev
- Timeouts configurables por proveedor

## 🔮 Roadmap Futuro

### Próximas Características
- [ ] **Auto-scaling**: Ajuste dinámico según carga
- [ ] **Caching inteligente**: Respuestas similares
- [ ] **Fine-tuning**: Modelos personalizados
- [ ] **Multi-modal**: Soporte para imágenes/audio
- [ ] **Collaborative filtering**: Recomendaciones basadas en uso

### Optimizaciones Planeadas
- [ ] **Predicción de costos**: Estimación antes de ejecutar
- [ ] **Load balancing**: Distribución inteligente de carga
- [ ] **A/B testing**: Comparación automática de modelos
- [ ] **Feedback loop**: Mejora continua basada en resultados

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature
3. Implementa mejoras en el router o agentes
4. Agrega tests para nuevas funcionalidades
5. Envía un pull request

## 📄 Licencia

MIT License - Úsalo libremente en tus proyectos.

---

**¡El Meta-Agente Orquestador de Samara está listo para revolucionar tu flujo de trabajo de desarrollo!** 🚀 