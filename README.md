# 🧠 Samara - Sistema de Análisis Inteligente de Código

Sistema avanzado de análisis de código que utiliza **fragmentos granulares** e **IA multi-modelo** para indexar, analizar y consultar proyectos de software de manera inteligente.

## 🚀 Características Principales

- **🔍 Análisis Granular**: Extrae fragmentos específicos (funciones, clases, componentes) en lugar de archivos completos
- **🧠 IA Multi-Modelo**: Enrutamiento inteligente entre Ollama (local) y modelos cloud (GPT-4, Claude, etc.)
- **⚡ Indexación Rápida**: Procesamiento paralelo optimizado para proyectos grandes
- **💬 Chat Inteligente**: Consulta natural sobre tu código con contexto semántico
- **🎯 Detección Automática**: Configuración óptima según tu hardware
- **🔄 Búsqueda Híbrida**: Combina búsqueda semántica con filtros exactos

## 📁 Estructura del Proyecto

```
📦 Samara/
├── 🤖 agentes/                      # Agentes de IA especializados
│   ├── indexador_fragmentos.py      # Indexación de código en fragmentos
│   ├── consultor_fragmentos.py      # Consultas inteligentes híbridas
│   ├── router_ia.py                 # Enrutamiento inteligente de modelos IA
│   └── __init__.py                  # Configuración del paquete
├── 🛠️ tools/                       # Herramientas auxiliares
│   └── clean_weaviate.py           # Limpieza y mantenimiento de BD
├── 📋 analizador_codigo.py          # CLI principal (ejecutar desde raíz)
├── 💬 samara_chat.py               # Chat interactivo con logging detallado
├── 📄 env_example.txt              # Plantilla de configuración API keys
├── 🐳 docker-compose.yml           # Configuración de Weaviate
├── 📦 requirements.txt             # Dependencias Python
└── 📖 README.md                    # Esta documentación
```

## ⚡ Inicio Rápido

### 1. **Detectar Configuración Óptima**
```bash
python analizador_codigo.py detectar
```
**¿Qué hace?** Analiza tu hardware (CPU, RAM) y recomienda la configuración óptima de workers y concurrencia para maximizar el rendimiento.

### 2. **Indexar Proyecto**
```bash
python analizador_codigo.py analizar /ruta/a/tu/proyecto --name MiProyecto
```
**¿Qué hace?** Escanea todo el proyecto, extrae fragmentos de código y los indexa en Weaviate con embeddings semánticos.

### 3. **Consultar con IA**
```bash
python samara_chat.py
```
**¿Qué hace?** Inicia un chat interactivo donde puedes hacer preguntas en lenguaje natural sobre tu código.

## 🔧 Instalación y Configuración Detallada

### Requisitos del Sistema
- **Python 3.8+** (recomendado 3.10+)
- **8GB RAM mínimo** (16GB+ recomendado para proyectos grandes)
- **Ollama** (para indexación local gratuita)
- **Weaviate** (base de datos vectorial)
- **Docker** (para Weaviate)

### Instalación Paso a Paso

#### 1. **Configurar el Entorno Python**
```bash
# Clonar repositorio
git clone <repo-url>
cd samara

# Crear entorno virtual (recomendado)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# o
.venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

#### 2. **Configurar Ollama (Local - Gratis)**
```bash
# Instalar Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Descargar modelos necesarios
ollama pull llama3:instruct      # Para descripciones de código
ollama pull nomic-embed-text     # Para embeddings semánticos

# Verificar instalación
ollama list
curl http://localhost:11434/api/tags
```

#### 3. **Configurar Weaviate (Base de Datos Vectorial)**
```bash
# Iniciar Weaviate con Docker
docker-compose up -d

# Verificar que está funcionando
curl http://localhost:8080/v1/meta
```

#### 4. **Configurar API Keys (Opcional pero Recomendado)**
```bash
# Copiar plantilla de configuración
cp env_example.txt .env

# Editar .env con tus API keys
nano .env  # o tu editor preferido
```

**Contenido del archivo .env:**
```bash
# Claude (excelente para análisis de código)
CLAUDE_API_KEY=tu_key_aqui

# OpenAI GPT-4 (recomendado para análisis avanzado)
OPENAI_API_KEY=tu_key_aqui

# Google Gemini (buena relación calidad/precio)
GEMINI_API_KEY=

# Perplexity (bueno para consultas con contexto web)
PERPLEXITY_API_KEY=

# Configuración local (no cambiar)
OLLAMA_URL=http://localhost:11434
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=
```

## 🧠 Cómo Funciona el Sistema

### 🔍 **1. Indexador de Fragmentos (`indexador_fragmentos.py`)**

**Propósito:** Analiza proyectos de código y extrae fragmentos granulares para indexación.

**Proceso Detallado:**
1. **Escaneo de Archivos**: Recorre recursivamente el proyecto ignorando carpetas irrelevantes
2. **Filtrado Inteligente**: Identifica archivos de código válidos (.py, .js, .ts, .jsx, etc.)
3. **Extracción de Fragmentos**: Divide cada archivo en fragmentos específicos:
   - **Funciones**: `function nombre()`, `const nombre = () =>`
   - **Clases**: `class NombreClase`
   - **Componentes**: React, Vue, Polymer
   - **Endpoints**: `app.get()`, `@route`
   - **Imports**: Dependencias importantes
4. **Generación de Embeddings**: Usa `nomic-embed-text` para crear vectores semánticos
5. **Descripción con IA**: Usa `llama3:instruct` para generar descripciones de cada fragmento
6. **Indexación en Weaviate**: Almacena fragmentos con metadatos estructurados

**Esquema de Fragmento:**
```json
{
  "fileName": "auth.js",
  "filePath": "src/services/auth.js",
  "type": "function",
  "functionName": "authenticateUser",
  "startLine": 15,
  "endLine": 45,
  "content": "function authenticateUser(credentials) { ... }",
  "description": "Función que autentica usuario con JWT y bcrypt",
  "module": "services",
  "language": "javascript",
  "framework": "express",
  "complexity": "medium",
  "dependencies": ["jwt", "bcrypt"],
  "parameters": ["credentials"],
  "returnType": "Promise"
}
```

### 🧠 **2. Router de IA (`router_ia.py`)**

**Propósito:** Enruta inteligentemente las consultas al mejor modelo de IA disponible.

**Lógica de Enrutamiento:**
1. **Detección de Tarea**: Analiza el prompt para identificar el tipo de consulta
2. **Estimación de Contexto**: Calcula el tamaño del contexto en tokens
3. **Selección de Proveedor**: Elige el mejor modelo según:
   - **Contexto pequeño** (<2k tokens) → **Ollama** (gratis, rápido)
   - **Contexto mediano** (2k-10k tokens) → **Gemini/GPT-4** (balance)
   - **Contexto grande** (>10k tokens) → **Claude/GPT-4** (mejor capacidad)
   - **Análisis complejo** → **GPT-4/Claude** (mejor calidad)

**Tipos de Tarea Detectados:**
- `ANALISIS_CODIGO`: Análisis técnico de fragmentos
- `MIGRACION_COMPLEJA`: Migración de proyectos grandes
- `DEBUGGING`: Búsqueda de errores
- `DOCUMENTACION`: Generación de documentación
- `CONSULTA_SIMPLE`: Preguntas básicas

**Sistema de Fallback:**
Si el proveedor principal falla, automáticamente prueba con otros disponibles.

### 💬 **3. Consultor de Fragmentos (`consultor_fragmentos.py`)**

**Propósito:** Realiza consultas inteligentes sobre los fragmentos indexados.

**Estrategia Híbrida de Búsqueda:**

#### **Estrategia 1: Búsqueda Semántica (Principal)**
1. **Generación de Embedding**: Convierte la pregunta en vector semántico
2. **Búsqueda Vectorial**: Encuentra fragmentos similares usando distancia coseno
3. **Preparación de Contexto**: Estructura los fragmentos encontrados
4. **Generación de Respuesta**: Usa IA para analizar y responder

#### **Estrategia 2: Búsqueda por Filtros (Fallback)**
1. **Extracción de Términos**: Usa IA para extraer palabras clave
2. **Filtros Exactos**: Busca en campos específicos (nombre, descripción, contenido)
3. **Combinación OR**: Une múltiples condiciones de búsqueda
4. **Respuesta Contextual**: Genera respuesta basada en coincidencias exactas

**Campos de Búsqueda:**
- `functionName`: Nombres de funciones/clases
- `description`: Descripciones generadas por IA
- `content`: Contenido del código
- `module`: Módulo/carpeta del fragmento
- `fileName`: Nombre del archivo

### 📋 **4. CLI Principal (`analizador_codigo.py`)**

**Comandos Disponibles:**

#### **`detectar`** - Optimización de Hardware
```bash
python analizador_codigo.py detectar
```
**Funcionalidad:**
- Detecta CPU cores y RAM disponible
- Calcula configuración óptima de workers
- Recomienda concurrencia de Ollama
- Proporciona comandos listos para usar

**Ejemplo de Salida:**
```
💻 CPU Threads detectados: 24
🧠 RAM disponible: 63.9 GB
🏷️ Tipo detectado: 🚀 Ryzen 9 de alta gama

📊 CONFIGURACIONES RECOMENDADAS:
🟢 CONSERVADORA: --workers 16 --ollama_concurrent 3
🟡 RECOMENDADA: --workers 20 --ollama_concurrent 4
🔴 AGRESIVA: --workers 24 --ollama_concurrent 5
```

#### **`analizar`** - Indexación de Proyectos
```bash
python analizador_codigo.py analizar /ruta/proyecto --name MiApp [opciones]
```
**Opciones Avanzadas:**
- `--workers N`: Número de threads paralelos
- `--ollama_concurrent N`: Conexiones simultáneas a Ollama
- `--verbose`: Logs detallados en tiempo real
- `--log_files`: Genera archivos de log separados
- `--file_timeout N`: Timeout por archivo (segundos)
- `--ollama_timeout N`: Timeout para Ollama (segundos)

**Proceso Interno:**
1. Verificación de servicios (Weaviate, Ollama)
2. Creación/actualización de esquema
3. Escaneo paralelo de archivos
4. Extracción y análisis de fragmentos
5. Generación de embeddings y descripciones
6. Indexación en base de datos vectorial

#### **`consultar`** - Búsqueda Directa
```bash
python analizador_codigo.py consultar MiApp "funciones de autenticación" --limit 10
```

#### **`listar`** - Inventario de Fragmentos
```bash
python analizador_codigo.py listar MiApp --verbose
```

#### **`eliminar`** - Limpieza de Datos
```bash
python analizador_codigo.py eliminar MiApp --confirmar
```

### 💬 **5. Chat Interactivo (`samara_chat.py`)**

**Funcionalidad:**
- Chat en tiempo real con logging detallado
- Muestra el proceso completo de búsqueda
- Estrategias de fallback transparentes
- Información de fragmentos encontrados

**Ejemplo de Interacción:**
```
Tú: ¿Qué funciones manejan autenticación?

--- BÚSQUEDA SEMÁNTICA EN FRAGMENTOS ---
Fragmentos encontrados: 5
  1. authenticateUser (function) en auth.js (líneas 15-45)
  2. validateToken (function) en middleware.js (líneas 8-25)
  3. loginUser (function) en controllers/auth.js (líneas 30-60)

🗣️ Samara: Encontré 5 funciones relacionadas con autenticación:

1. **authenticateUser()** en `auth.js`: Función principal que valida credenciales usando JWT y bcrypt...
```

## 📊 Comandos y Casos de Uso Detallados

### 🔍 **Análisis de Proyectos**

#### **Proyecto Pequeño (< 1k archivos)**
```bash
python analizador_codigo.py detectar
python analizador_codigo.py analizar /mi/proyecto --name MiApp
```

#### **Proyecto Mediano (1k-10k archivos)**
```bash
python analizador_codigo.py analizar /mi/proyecto --name MiApp \
  --workers 12 --ollama_concurrent 4 --verbose
```

#### **Proyecto Grande (10k+ archivos)**
```bash
python analizador_codigo.py analizar /mi/proyecto --name MiApp \
  --workers 20 --ollama_concurrent 6 --verbose --log_files \
  --file_timeout 120 --ollama_timeout 60
```

### 💬 **Consultas Inteligentes**

#### **Búsqueda de Funcionalidad**
```
"¿Qué funciones manejan autenticación?"
"Muéstrame los componentes de React"
"¿Dónde se definen las rutas de la API?"
"Funciones que usan base de datos"
```

#### **Análisis Arquitectónico**
```
"¿Cómo está estructurado el proyecto?"
"¿Qué patrones de diseño se usan?"
"Dependencias entre módulos"
"Componentes con alta complejidad"
```

#### **Debugging y Optimización**
```
"Funciones que pueden tener bugs"
"Código duplicado o similar"
"Funciones que necesitan refactoring"
"Endpoints sin validación"
```

#### **Migración y Modernización**
```
"¿Qué funciones usan jQuery?"
"Componentes que pueden convertirse a React"
"Código legacy que necesita actualización"
"APIs que usan métodos deprecados"
```

### 🛠️ **Herramientas de Mantenimiento**

#### **Limpieza de Base de Datos**
```bash
python tools/clean_weaviate.py
```
**Opciones:**
1. Limpiar todo Weaviate
2. Eliminar proyecto específico
3. Solo ver estado actual

#### **Verificación de Estado**
```bash
python analizador_codigo.py listar MiApp --verbose
python analizador_codigo.py verificar_indexado MiApp
```

## 🎯 Optimización de Rendimiento

### **Configuración por Hardware**

#### **CPU de 4-8 núcleos (Desarrollo)**
```bash
python analizador_codigo.py analizar /proyecto \
  --workers 4 --ollama_concurrent 2
```

#### **CPU de 12-16 núcleos (Workstation)**
```bash
python analizador_codigo.py analizar /proyecto \
  --workers 12 --ollama_concurrent 4
```

#### **CPU de 24+ núcleos (Servidor)**
```bash
python analizador_codigo.py analizar /proyecto \
  --workers 20 --ollama_concurrent 6
```

### **Optimización por Tipo de Proyecto**

#### **Proyectos JavaScript/TypeScript**
- **Frameworks detectados**: React, Vue, Angular, Express
- **Fragmentos especiales**: Componentes, hooks, endpoints
- **Configuración recomendada**: Workers altos, concurrencia media

#### **Proyectos Python**
- **Frameworks detectados**: Django, Flask, FastAPI
- **Fragmentos especiales**: Clases, decoradores, APIs
- **Configuración recomendada**: Workers medios, concurrencia alta

#### **Proyectos Mixtos**
- **Detección automática** de múltiples lenguajes
- **Fragmentación adaptativa** según tipo de archivo
- **Configuración balanceada**

## 🔧 Configuración Avanzada

### **Variables de Entorno**
```bash
# API Keys (opcional - solo configura las que tengas)
OPENAI_API_KEY=sk-...                    # GPT-4 para análisis complejos
CLAUDE_API_KEY=sk-ant-...               # Claude para contextos grandes
GEMINI_API_KEY=...                      # Gemini para balance calidad/precio
PERPLEXITY_API_KEY=...                  # Perplexity para consultas web

# Configuración de servicios (no cambiar)
OLLAMA_URL=http://localhost:11434       # Ollama local
WEAVIATE_URL=http://localhost:8080      # Weaviate local
WEAVIATE_API_KEY=                       # Solo si usas Weaviate Cloud
```

### **Configuración de Docker (Weaviate)**
```yaml
# docker-compose.yml
version: '3.4'
services:
  weaviate:
    image: semitechnologies/weaviate:1.22.4
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      CLUSTER_HOSTNAME: 'node1'
    volumes:
      - weaviate_data:/var/lib/weaviate
```

## 🛠️ Solución de Problemas

### **Problemas Comunes**

#### **Ollama no responde**
```bash
# Verificar estado
curl http://localhost:11434/api/tags

# Reiniciar servicio
ollama serve

# Verificar modelos
ollama list
```

#### **Weaviate no conecta**
```bash
# Verificar Docker
docker-compose ps

# Ver logs
docker-compose logs weaviate

# Reiniciar
docker-compose restart weaviate
```

#### **Problemas de memoria**
```bash
# Reducir workers
python analizador_codigo.py analizar /proyecto \
  --workers 2 --ollama_concurrent 1

# Verificar uso de memoria
htop  # o Task Manager en Windows
```

#### **Timeouts en proyectos grandes**
```bash
# Aumentar timeouts
python analizador_codigo.py analizar /proyecto \
  --file_timeout 180 --ollama_timeout 90
```

### **Logs y Debugging**

#### **Logs Detallados**
```bash
# Verbose mode
python analizador_codigo.py analizar /proyecto --verbose

# Archivos de log separados
python analizador_codigo.py analizar /proyecto --log_files
```

#### **Verificación de Fragmentos**
```bash
# Ver fragmentos indexados
python analizador_codigo.py verificar_indexado MiApp

# Estadísticas del proyecto
python analizador_codigo.py listar MiApp --verbose
```

## 📝 Notas Técnicas Avanzadas

### **Arquitectura del Sistema**
- **Base de datos**: Weaviate (vectorial) para búsqueda semántica
- **Embeddings**: `nomic-embed-text` (384 dimensiones)
- **Descripciones**: `llama3:instruct` (local, 8B parámetros)
- **Análisis avanzado**: GPT-4/Claude según contexto
- **Paralelización**: ThreadPoolExecutor con semáforos
- **Sincronización**: Thread-safe con locks para contadores

### **Algoritmos de Fragmentación**
- **JavaScript/TypeScript**: AST parsing para funciones, clases, componentes
- **Python**: Análisis de indentación para funciones y clases
- **Fragmentación de funciones largas**: Chunks de 50 líneas con overlap de 10
- **Detección de frameworks**: Patrones específicos (React, Vue, Express, Django)

### **Optimizaciones de Rendimiento**
- **Pooling de conexiones**: Reutilización de conexiones HTTP
- **Rate limiting**: Semáforos para controlar concurrencia
- **Caching**: Schema y configuración en memoria
- **Batch processing**: Procesamiento por lotes de embeddings

### **Esquema de Base de Datos**
```
CodeFragments_{proyecto}:
├── Identificación: fileName, filePath, type, functionName
├── Ubicación: startLine, endLine, fragmentIndex
├── Contenido: content, description
├── Metadatos: module, language, framework, complexity
├── Análisis: dependencies, parameters, returnType
└── Timestamps: indexedAt
```

---

## 🚀 **¡Empieza Ahora!**

```bash
# 1. Detectar tu configuración óptima
python analizador_codigo.py detectar

# 2. Indexar tu primer proyecto
python analizador_codigo.py analizar /ruta/a/tu/proyecto --name MiProyecto

# 3. Comenzar a consultar
python samara_chat.py
```

**🧠 ¡Samara hace que analizar código sea tan fácil como conversar!**

---

*Desarrollado con ❤️ para hacer el análisis de código más inteligente y accesible.* 