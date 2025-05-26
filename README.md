# 🧠 Samara: Meta-Agente Orquestador de IA para Migración y Conversación

## 🚀 ¿Qué es Samara?
Samara es una plataforma de IA conversacional y de migración de código **multi-agente** y **multi-modelo**. Orquesta varios LLMs (Ollama, Claude, GPT-4, Gemini, Perplexity) para tareas como:
- Migración masiva de proyectos frontend (ej: Polymer → React)
- Análisis y refactorización de código
- Conversación inteligente con memoria semántica
- Asistente de desarrollo y juego

Samara es escalable, modular y lista para miles de usuarios y proyectos reales.

---

## 🧩 **Arquitectura Lógica**

### 1. **Agentes Especializados**
- **SmartConversationalAgent**: Orquesta la conversación, decide cuándo usar memoria, selecciona el modelo óptimo.
- **ContextAgent**: Decide cuándo y qué contexto/memoria es relevante para cada consulta.
- **MemoryAgent**: Decide qué recuerdos guardar, filtra información trivial y prioriza lo importante.
- **ProjectMigrationAgent**: Orquesta la migración masiva de proyectos, gestiona chunking, fases y reportes.
- **CodeAnalysisAgent**: Analiza la estructura, dependencias, tecnologías y patrones del código.
- **CodeMigrationAgent**: Migra archivos individuales usando reglas y LLMs.
- **SamaraDevAgent**: Interfaz conversacional para comandos naturales de migración y análisis.

### 2. **Meta-Agente Orquestador (ModelRouterAgent)**
- Detecta el tipo de tarea (migración, análisis, conversación, debugging, etc.)
- Estima el tamaño de contexto (tokens) y selecciona el modelo más adecuado según:
  - Capacidad de contexto (tokens)
  - Costo y velocidad
  - Disponibilidad (API keys, Ollama local)
  - Complejidad de la tarea
- Implementa fallback automático entre proveedores
- Lleva estadísticas detalladas de uso y eficiencia

### 3. **Memoria y Contexto Inteligente**
- **Weaviate** almacena:
  - Historial de conversaciones (por usuario, modo, sesión)
  - Recuerdos relevantes (fragmentos, resúmenes, decisiones técnicas)
  - Metadatos de migraciones y análisis
- Búsqueda semántica para recuperar contexto relevante
- Separación total por usuario y modo (dev/game)

### 4. **Migración Masiva e Incremental**
- Chunking automático de archivos grandes (por líneas, bloques lógicos, tokens)
- Procesamiento incremental y ensamblado de resultados
- Análisis previo de dependencias, endpoints, lógica de negocio y estilos
- Propuestas de re-arquitectura y limpieza de código
- Reportes detallados de migración (archivos migrados, fallidos, próximos pasos)

---

## ⚙️ **Capacidades Técnicas**

### 1. **Estructura del Proyecto**
```
/samara/           # Código principal de agentes y lógica
/demos/            # Scripts de demo, inicio rápido, verificación
/tests/            # Pruebas unitarias y de integración
/profiles/         # Perfiles de configuración (dev, game)
samara_chat.py     # Entrada principal modo conversación
requirements.txt   # Dependencias
.docker-compose.yml# Orquestación de servicios (Weaviate, etc)
```

### 2. **Enrutamiento Inteligente de Modelos**
- Soporta Ollama (local), Claude, GPT-4, Gemini, Perplexity
- Selección dinámica según:
  - Tipo de tarea (migración, análisis, conversación, etc.)
  - Tamaño de contexto (tokens)
  - Costo y velocidad
  - Disponibilidad real (API keys, Ollama corriendo)
- Chunking automático para archivos grandes
- Fallback robusto si un proveedor falla

### 3. **Chunking y Procesamiento Incremental**
- Divide archivos grandes en fragmentos manejables
- Procesa cada chunk por separado y ensambla el resultado
- Soporta chunking semántico (por funciones, clases, componentes)
- Resúmenes intermedios y ventanas deslizantes para mantener contexto

### 4. **Integración con Weaviate**
- Guarda historial de conversaciones y recuerdos como objetos en Weaviate
- Namespaces separados por usuario y modo
- Búsqueda semántica para contexto relevante
- No almacena archivos de código completos, solo metadatos y fragmentos clave

### 5. **Memoria Inteligente y Estadísticas**
- Decide qué guardar y qué descartar
- Lleva estadísticas por proveedor, tipo de tarea, tamaño de contexto
- Muestra información de contexto y modelo usado en modo dev

### 6. **Comandos Naturales y Flexibilidad**
- Soporta comandos como:
  - `migra el proyecto en /ruta de polymer a react`
  - `analiza el proyecto en /ruta`
  - `usar modelo ollama`
  - `stats`
- Interfaz conversacional amigable y adaptable

### 7. **Escalabilidad y Buenas Prácticas**
- Estructura modular y profesional
- `.gitignore` robusto para entornos virtuales, cachés y archivos temporales
- Soporte para Docker y despliegue en producción
- Tests automáticos con `pytest`

---

## 🧠 **Casos de Uso y Ejemplos**

### 1. **Migración Masiva de Polymer a React**
- Analiza el proyecto, detecta componentes, endpoints, estilos
- Divide archivos grandes, migra cada fragmento y ensambla
- Propone estructura moderna en React, con mejores prácticas
- Genera reporte de migración y próximos pasos

### 2. **Análisis Profundo de Código**
- Detecta tecnologías, dependencias, patrones arquitectónicos
- Calcula complejidad, identifica entry points y archivos críticos
- Sugiere refactorizaciones y mejoras

### 3. **Conversación Inteligente con Memoria**
- Recuerda decisiones técnicas, preferencias y migraciones previas
- Usa contexto relevante para cada respuesta
- Separa contextos por usuario y modo

### 4. **Orquestación Multi-Modelo**
- Usa modelos locales para tareas simples (Ollama)
- Usa modelos cloud para tareas complejas o contextos grandes (Claude, GPT-4)
- Optimiza costos y velocidad automáticamente

---

## 🛠️ **Cómo usar Samara**

1. **Configura tu entorno**
   - Instala dependencias: `pip install -r requirements.txt`
   - (Opcional) Instala y ejecuta Weaviate y Ollama (ver `demos/inicio_rapido.py`)
   - Configura tus API keys en `.env` si quieres usar modelos cloud

2. **Ejecuta el chat principal**
   ```bash
   python samara_chat.py dev
   ```

3. **Prueba los demos y tests**
   ```bash
   python demos/demo_interactivo.py
   python demos/demo_meta_agente.py
   .venv/Scripts/python -m pytest
   ```

4. **Migra un proyecto real**
   - Usa el comando: `Migra el proyecto en /ruta de polymer a react`
   - Sigue las instrucciones y revisa el reporte generado

---

## 📊 **Estadísticas y Transparencia**
- Muestra qué modelo se usó, tamaño de contexto, si hubo fallback, etc.
- Lleva métricas de eficiencia, uso de memoria, y éxito por proveedor

---

## 📝 **Notas Técnicas y Consejos**
- **No subas tu entorno virtual ni archivos de caché a Git** (`.gitignore` ya lo cubre)
- **No almacenes código fuente completo en Weaviate**: solo metadatos y fragmentos relevantes
- **Chunking**: Si un archivo es muy grande, Samara lo dividirá automáticamente
- **Puedes personalizar los agentes** para nuevas tecnologías o flujos

---

## 💡 **¿Dudas o quieres contribuir?**
- El código está documentado y modular
- Puedes crear nuevos agentes, comandos o integraciones fácilmente
- ¡Abre un issue o PR si tienes ideas o mejoras!

---

## ❓ FAQ - Preguntas Frecuentes

### 1. ¿Samara puede migrar proyectos gigantes (100k+ líneas)?
Sí. Utiliza chunking automático para dividir archivos grandes y migrar por partes, ensamblando el resultado final. Además, analiza dependencias y lógica de negocio para mantener la coherencia.

### 2. ¿Qué pasa si un archivo es más grande que el límite de tokens del modelo?
Samara lo detecta y lo divide en fragmentos (chunks) que sí caben en el contexto del modelo. Cada fragmento se procesa por separado y luego se ensamblan los resultados.

### 3. ¿Dónde se guarda el código migrado?
El código migrado se guarda en tu sistema de archivos, en una carpeta de salida. **Weaviate solo almacena metadatos, resúmenes y contexto relevante, nunca el código fuente completo.**

### 4. ¿Qué modelos de IA soporta Samara?
- **Ollama** (local, gratis)
- **Claude** (Anthropic, 200k tokens)
- **GPT-4** (OpenAI, 128k tokens)
- **Gemini** (Google)
- **Perplexity** (búsqueda en tiempo real)

Puedes usar solo Ollama (local) o agregar API keys para los modelos cloud.

### 5. ¿Cómo decide Samara qué modelo usar?
- Analiza el tipo de tarea (migración, análisis, conversación, etc.)
- Estima el tamaño del contexto (tokens)
- Considera disponibilidad, costo y velocidad
- Usa fallback automático si un proveedor falla

### 6. ¿Puedo personalizar los agentes o agregar nuevos modelos?
Sí. La arquitectura es modular. Puedes crear nuevos agentes, comandos, o integrar más modelos editando los archivos en `samara/`.

### 7. ¿Qué tan segura es la información?
- El código fuente nunca se sube a la nube (a menos que tú lo decidas)
- Weaviate puede correr localmente o en la nube
- Las API keys se gestionan por `.env` y nunca se suben a Git

### 8. ¿Qué hago si algo no funciona o hay errores?
- Ejecuta `python demos/verificar_configuracion.py` para diagnosticar problemas
- Revisa que Ollama esté corriendo y/o tus API keys estén bien configuradas
- Consulta los logs y las estadísticas para más detalles

### 9. ¿Puedo usar Samara solo como asistente conversacional?
¡Sí! Puedes usarlo solo para conversación, memoria y contexto, sin migrar código.

### 10. ¿Samara soporta otros lenguajes además de JS/TS?
La arquitectura es extensible. Puedes agregar reglas y prompts para migrar o analizar otros lenguajes (Python, Java, etc.)

---

**Samara es la plataforma definitiva para migración, análisis y conversación inteligente sobre código real.**

¡Listo para la era de la IA aplicada al desarrollo profesional! 🚀 

---

## 🚀 Uso Avanzado

### 1. **Prompts avanzados para migración y análisis**

- **Migración con estrategia personalizada:**
  ```
  Migra el proyecto en /ruta/mi-app de polymer a react usando estrategia incremental y separa los servicios en hooks.
  ```
- **Análisis de dependencias y riesgos:**
  ```
  Analiza el proyecto en /ruta/mi-app y genera un reporte de dependencias, endpoints y posibles riesgos de migración.
  ```
- **Refactorización y modernización:**
  ```
  Refactoriza este archivo para usar React hooks modernos y elimina código legacy:
  [pega aquí el código]
  ```
- **Re-arquitectura completa:**
  ```
  Propón una nueva estructura de carpetas y componentes para este proyecto migrado a React, siguiendo mejores prácticas.
  ```
- **Migración multi-lenguaje:**
  ```
  Migra este backend de Python Flask a FastAPI y documenta los endpoints.
  ```

### 2. **Flujos avanzados**
- **Migración masiva + análisis + refactor:**
  1. Analiza el proyecto completo.
  2. Migra por chunks cada archivo grande.
  3. Refactoriza los resultados y genera un reporte final.
- **Conversación con memoria técnica:**
  1. Explica una decisión técnica.
  2. Consulta después: "¿Por qué elegimos esa arquitectura?"
  3. Samara recuerda y responde con contexto real.

---

## 📊 Tabla Comparativa de Modelos Soportados

| Proveedor    | Modelos principales         | Tokens máx. | Costo*   | Velocidad | Casos de uso recomendados                |
|--------------|----------------------------|-------------|----------|-----------|------------------------------------------|
| **Ollama**   | llama3, mistral, phi3      | 8,192       | Gratis   | Rápido    | Conversación, tareas simples, local      |
| **Claude**   | Claude 3 Opus/Sonnet       | 200,000     | Alto     | Medio     | Migración compleja, análisis profundo    |
| **GPT-4**    | GPT-4, GPT-4 Turbo         | 128,000     | Medio    | Medio     | Debugging, arquitectura, refactor        |
| **Gemini**   | Gemini Pro                 | 32,768      | Bajo     | Rápido    | Documentación, consultas, análisis medio |
| **Perplexity**| Llama-3 Sonar              | 32,768      | Bajo     | Rápido    | Búsqueda, información actual, soporte    |

*El costo depende del proveedor y uso cloud. Ollama es siempre local y gratis.

--- 