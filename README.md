# 🧠 Samara - Sistema de Análisis de Código con Fragmentos

Sistema inteligente de análisis de código que indexa **fragmentos específicos** (funciones, clases, componentes) en lugar de archivos completos, permitiendo consultas semánticas precisas y respuestas contextualizadas.

## 🚀 **Características Principales**

- **🔍 Indexación granular**: Fragmenta el código en funciones, clases, componentes específicos
- **🧠 Búsqueda semántica**: Consultas en lenguaje natural sobre fragmentos de código
- **⚡ Respuestas precisas**: IA contextualizada con código real específico
- **🏗️ Multi-proyecto**: Cada proyecto se indexa por separado
- **🔧 Multi-lenguaje**: Python, JavaScript, TypeScript, HTML, CSS y más

## 📋 **Requisitos**

1. **Weaviate** ejecutándose en `http://localhost:8080`
2. **Ollama** ejecutándose en `http://localhost:11434` con modelo `llama3:instruct` y `nomic-embed-text`
3. **Python 3.8+**

## 🛠️ **Instalación**

```bash
# Instalar dependencias
pip install -r requirements.txt

# Verificar servicios
# Weaviate: http://localhost:8080/v1/meta
# Ollama: http://localhost:11434/api/tags
```

## 📖 **Uso**

### 🖥️ **CLI (Recomendado)**

```bash
# 1. Detectar configuración óptima para tu hardware
python samara/cli_analizador.py detectar

# 2. Indexar proyecto con fragmentos
python samara/cli_analizador.py analizar /ruta/proyecto --name mi_proyecto

# 3. Consultar fragmentos
python samara/cli_analizador.py consultar mi_proyecto "funciones de autenticación"

# 4. Listar fragmentos indexados
python samara/cli_analizador.py listar mi_proyecto

# 5. Verificar fragmentos realmente indexados
python samara/cli_analizador.py verificar_indexado mi_proyecto
```

### 💬 **Chat Interactivo**

```bash
# Chat con fragmentos de código
python samara_chat.py
```

### 🐍 **API Python**

```python
from samara.code_analysis_agent import CodeAnalysisAgent
from samara.smart_conversational_agent import FragmentQueryAgent

# Indexar proyecto
agent = CodeAnalysisAgent()
result = agent.analyze_and_index_project("/ruta/proyecto", "mi_proyecto")

# Consultar fragmentos
query_agent = FragmentQueryAgent()
log = query_agent.consulta_inteligente("mi_proyecto", "funciones de login")
print(log['respuesta_final'])
```

## 🔍 **Tipos de Fragmentos Indexados**

### **JavaScript/TypeScript**
- ✅ Funciones (`function`, `const fn = ()`, `async function`)
- ✅ Clases (`class MyClass`)
- ✅ Componentes React/Vue (`const Component = () =>`)
- ✅ Endpoints (`app.get()`, `router.post()`)
- ✅ Imports/Exports importantes

### **Python**
- ✅ Funciones (`def function_name()`)
- ✅ Clases (`class ClassName`)
- ✅ Imports importantes
- ✅ Métodos de clase

### **HTML/CSS**
- ✅ Componentes HTML personalizados
- ✅ Clases CSS importantes
- ✅ Selectores específicos

## 📊 **Esquema de Fragmentos**

Cada fragmento se indexa con:

```json
{
  "file_name": "auth.js",
  "file_path": "src/services/auth.js", 
  "type": "function",
  "function_name": "authenticateUser",
  "parent_function": "AuthService",
  "fragment_index": 0,
  "start_line": 15,
  "end_line": 45,
  "description": "Función que autentica usuario con JWT",
  "module": "services",
  "language": "javascript",
  "content": "function authenticateUser(credentials) { ... }",
  "complexity": "medium",
  "dependencies": ["jwt", "bcrypt"],
  "parameters": ["credentials"],
  "return_type": "Promise"
}
```

## 🎯 **Flujo de Trabajo**

1. **Detectar hardware**: `python samara/cli_analizador.py detectar`
2. **Indexar**: `python samara/cli_analizador.py analizar /mi/proyecto --name proyecto`
3. **Consultar**: `python samara_chat.py` o usar CLI
4. **Iterar**: Hacer preguntas específicas sobre el código

## 🔧 **Comandos CLI Completos**

### **Análisis**
```bash
# Básico
python samara/cli_analizador.py analizar /ruta --name proyecto

# Con configuración personalizada
python samara/cli_analizador.py analizar /ruta --name proyecto --workers 16 --ollama_concurrent 4

# Con logs detallados
python samara/cli_analizador.py analizar /ruta --name proyecto --verbose --logfile
```

### **Consultas**
```bash
# Consulta básica
python samara/cli_analizador.py consultar proyecto "funciones de login"

# Con más resultados
python samara/cli_analizador.py consultar proyecto "componentes React" --limit 10 --verbose
```

### **Gestión**
```bash
# Listar fragmentos
python samara/cli_analizador.py listar proyecto --limit 20

# Verificar indexación
python samara/cli_analizador.py verificar_indexado proyecto

# Eliminar proyecto
python samara/cli_analizador.py eliminar proyecto --confirmar
```

## 🛠️ **Herramientas Adicionales**

### **Limpiar Weaviate**
```bash
python tools/clean_weaviate.py
```

Opciones:
- Limpiar todo Weaviate
- Eliminar proyecto específico  
- Ver estado actual

## 🔍 **Ejemplos de Consultas**

### **Consultas Funcionales**
- "funciones de autenticación"
- "componentes que usan hooks"
- "endpoints de la API"
- "clases con alta complejidad"

### **Consultas Arquitectónicas**
- "módulos del sistema de login"
- "dependencias entre componentes"
- "funciones que manejan errores"

### **Consultas Específicas**
- "función que valida passwords"
- "componente de navegación principal"
- "servicios que consumen APIs externas"

## 📈 **Ventajas del Sistema de Fragmentos**

### **vs. Indexación de Archivos Completos**
- ✅ **Precisión**: Encuentra funciones específicas, no archivos enteros
- ✅ **Contexto**: Respuestas con código real relevante
- ✅ **Escalabilidad**: Maneja proyectos grandes eficientemente
- ✅ **Granularidad**: Búsqueda a nivel de función/clase

### **vs. Búsqueda de Texto Simple**
- ✅ **Semántica**: Entiende intención, no solo palabras clave
- ✅ **Inteligencia**: IA contextualizada con código real
- ✅ **Estructura**: Respeta la estructura del código

## 🐛 **Troubleshooting**

### **Error de conexión a Weaviate**
```
❌ Error conectando a Weaviate
```
**Solución**: Verificar que Weaviate esté en `http://localhost:8080`

### **Error de conexión a Ollama**
```
❌ Error conectando con Ollama
```
**Solución**: Verificar que Ollama esté en `http://localhost:11434` con modelos instalados

### **No se indexan fragmentos**
```
📊 0 fragmentos indexados
```
**Solución**: Verificar que el proyecto tenga archivos de código válidos (.py, .js, .ts, etc.)

### **Consultas sin resultados**
```
No se encontraron fragmentos relevantes
```
**Solución**: Usar términos más específicos o verificar que el proyecto esté indexado

## 🏗️ **Arquitectura**

```
samara/
├── code_analysis_agent.py      # 🔧 Indexador de fragmentos
├── smart_conversational_agent.py # 🧠 Agente de consultas
├── cli_analizador.py           # 🖥️ Interfaz CLI
└── model_router_agent.py       # 🤖 Router de modelos IA

samara_chat.py                  # 💬 Chat interactivo
tools/clean_weaviate.py         # 🧹 Herramienta de limpieza
```

## 📝 **Licencia**

MIT License - Ver archivo LICENSE para detalles.

---

**🚀 ¡Empieza analizando tu primer proyecto con fragmentos!**

```bash
python samara/cli_analizador.py detectar
python samara/cli_analizador.py analizar /tu/proyecto --name mi_proyecto
python samara_chat.py
``` 