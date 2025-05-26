# 📊 Analizador de Código con Weaviate

Este analizador de código permite indexar proyectos completos en Weaviate para realizar consultas semánticas inteligentes y generar código basado en el contexto del proyecto.

## 🚀 Características

- **📁 Análisis completo de proyectos**: Detecta tecnologías, patrones arquitectónicos, dependencias
- **🔍 Búsqueda semántica**: Consultas en lenguaje natural sobre el código
- **⚛️ Generación de código**: Crea componentes React basados en análisis previo
- **🏗️ Separación por proyecto**: Cada proyecto se indexa por separado
- **🔧 Soporte múltiples tecnologías**: Polymer, React, Angular, Vue y más

## 📋 Requisitos

1. **Weaviate** ejecutándose en `http://localhost:8080`
2. **Ollama** ejecutándose en `http://localhost:11434` con modelo `llama3:instruct`
3. **Python 3.8+**

## 🛠️ Instalación

```bash
# Instalar dependencias
pip install -r requirements_analizador.txt

# Verificar que Weaviate y Ollama estén ejecutándose
# Weaviate: http://localhost:8080/v1/meta
# Ollama: http://localhost:11434/api/tags
```

## 📖 Uso

### 1. CLI (Interfaz de línea de comandos)

```bash
# Analizar e indexar un proyecto
python cli_analizador.py analizar "C:/MisProyectos/Polymer/ProyectoNombre" --name ProyectoNombre

# Consultar información del proyecto
python cli_analizador.py consultar ProyectoNombre "dame un resumen del módulo login"

# Listar módulos del proyecto
python cli_analizador.py listar ProyectoNombre

# Generar componente React
python cli_analizador.py generar ProyectoNombre login --requisitos "con hooks y validación" --output ./LoginComponent.jsx

# Eliminar datos del proyecto
python cli_analizador.py eliminar ProyectoNombre
```

### 2. API Python

```python
from code_analysis_agent import CodeAnalysisAgent

# Inicializar agente
agent = CodeAnalysisAgent(
    ollama_url="http://localhost:11434",
    weaviate_url="http://localhost:8080"
)

# Analizar proyecto
result = agent.analyze_and_index_project(
    "C:/MisProyectos/Polymer/ProyectoNombre", 
    "ProyectoNombre"
)

# Consultar información
query_result = agent.query_project(
    "ProyectoNombre", 
    "dame un resumen del módulo login"
)

# Generar componente React
react_component = agent.generate_react_component(
    "ProyectoNombre", 
    "login", 
    "con validación y hooks modernos"
)
```

## 🎯 Flujo de trabajo típico

1. **Analizar**: `python cli_analizador.py analizar C:/MisProyectos/Polymer/MiApp --name MiApp`
2. **Explorar**: `python cli_analizador.py listar MiApp`
3. **Consultar**: `python cli_analizador.py consultar MiApp "qué estilos usa el header"`
4. **Generar**: `python cli_analizador.py generar MiApp header --requisitos "responsivo con flexbox"`

## 🔍 Tipos de consultas soportadas

### Consultas generales
- "dame un resumen del módulo login"
- "qué componentes usan Polymer"
- "lista los servicios de autenticación"

### Consultas técnicas específicas
- "qué estilos usa el componente header"
- "qué endpoints consume la aplicación"
- "componentes con alta complejidad"
- "archivos que importan biblioteca X"

### Consultas de arquitectura
- "patrones arquitectónicos utilizados"
- "dependencias principales del proyecto"
- "componentes reutilizables"

## 📊 Información extraída por archivo

Para cada archivo, el analizador extrae:

- **📄 Metadatos**: Nombre, ruta, tipo, tamaño
- **🔧 Tecnología**: Framework/librería principal
- **🏷️ Tipo de módulo**: component, service, model, utility, etc.
- **📦 Dependencias**: Imports y exports
- **⚙️ Funciones y clases**: Listado completo
- **🌐 Endpoints**: URLs y llamadas a APIs
- **🎨 Estilos**: Clases CSS y variables
- **📊 Complejidad**: Nivel de dificultad de migración
- **🤖 Resumen IA**: Descripción generada automáticamente

## 🏗️ Estructura de datos en Weaviate

Cada proyecto se almacena en una clase separada (`Project_NombreProyecto`) con las siguientes propiedades:

```
- projectName: string
- filePath: string
- fileName: string
- fileType: string
- moduleType: string
- technology: string
- content: string (limitado a 10K caracteres)
- summary: string (generado por IA)
- dependencies: string[]
- exports: string[]
- imports: string[]
- functions: string[]
- classes: string[]
- endpoints: string[]
- styles: string[]
- complexity: string (low/medium/high)
- linesOfCode: int
- analysisDate: date
- tags: string[]
```

## ⚡ Comandos CLI completos

### `analizar`
```bash
python cli_analizador.py analizar <ruta> [--name <nombre>] [--verbose]
```

### `consultar`
```bash
python cli_analizador.py consultar <proyecto> "<consulta>" [--limit <n>] [--verbose]
```

### `listar`
```bash
python cli_analizador.py listar <proyecto> [--limit <n>] [--verbose]
```

### `generar`
```bash
python cli_analizador.py generar <proyecto> <modulo> [--requisitos "<req>"] [--output <archivo>]
```

### `eliminar`
```bash
python cli_analizador.py eliminar <proyecto> [--confirmar]
```

## 🔧 API Python completa

### Métodos principales

- `analyze_and_index_project(path, name)` - Analizar e indexar proyecto
- `query_project(project, query, limit)` - Consulta semántica
- `list_project_modules(project)` - Listar módulos
- `generate_react_component(project, module, requirements)` - Generar React
- `delete_project_data(project)` - Eliminar datos

### Métodos de análisis
- `analyze_project_structure(path)` - Solo estructura
- `analyze_file_complexity(file_path)` - Archivo individual
- `generate_migration_report(analysis)` - Reporte de migración

### Métodos de gestión
- `create_weaviate_schema(project)` - Crear esquema
- `_extract_imports/exports/functions/etc.` - Extractores específicos

## 🐛 Troubleshooting

### Error de conexión a Weaviate
```
❌ Error conectando a Weaviate: ...
```
**Solución**: Verificar que Weaviate esté ejecutándose en `http://localhost:8080`

### Error de conexión a Ollama
```
[Error al conectar con Ollama: ...]
```
**Solución**: Verificar que Ollama esté ejecutándose en `http://localhost:11434`

### "No se encontraron resultados"
**Solución**: Verificar que el proyecto haya sido indexado correctamente

### Archivo no encontrado
**Solución**: Verificar que la ruta del proyecto sea correcta y accesible

## 📈 Optimizaciones futuras

- ✅ Soporte para más lenguajes (Python, Java, C#)
- ✅ Análisis de performance y calidad de código
- ✅ Integración con Git para análisis de cambios
- ✅ Exportación de reportes en diferentes formatos
- ✅ API REST para integración con otras herramientas

## 📝 Ejemplos de uso completos

Ver `ejemplo_uso_analizador.py` para ejemplos detallados de todas las funcionalidades.

---

¡Ahora puedes analizar cualquier proyecto y generar código inteligente basado en su contexto! 🚀 