#!/usr/bin/env python3
"""
Ejemplo de uso del analizador de código con Weaviate
"""

from code_analysis_agent import CodeAnalysisAgent
import json

def main():
    # Inicializar el agente
    print("🚀 Iniciando analizador de código con Weaviate...")
    agent = CodeAnalysisAgent(
        ollama_url="http://localhost:11434",
        weaviate_url="http://localhost:8080"
    )
    
    # Ejemplo 1: Analizar e indexar un proyecto
    print("\n" + "="*60)
    print("1. ANÁLISIS E INDEXACIÓN DE PROYECTO")
    print("="*60)
    
    project_path = "C:/MisProyectos/Polymer/ProyectoEjemplo"
    project_name = "ProyectoEjemplo"
    
    print(f"Analizando proyecto: {project_name}")
    print(f"Ruta: {project_path}")
    
    # Nota: Cambiar la ruta por una que exista en tu sistema
    # result = agent.analyze_and_index_project(project_path, project_name)
    # print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Ejemplo 2: Consultar información del proyecto
    print("\n" + "="*60)
    print("2. CONSULTAS AL PROYECTO INDEXADO")
    print("="*60)
    
    # Consulta sobre un módulo específico
    consultas_ejemplo = [
        "dame un resumen del módulo login",
        "qué estilos usa el componente header",
        "qué endpoints consume la aplicación",
        "componentes que usan Polymer",
        "servicios de autenticación"
    ]
    
    for consulta in consultas_ejemplo:
        print(f"\n🔍 Consulta: {consulta}")
        # result = agent.query_project(project_name, consulta)
        # print(f"📄 Archivos encontrados: {result.get('files_found', 0)}")
        # print(f"🤖 Respuesta IA: {result.get('ai_response', 'No disponible')}")
    
    # Ejemplo 3: Listar módulos del proyecto
    print("\n" + "="*60)
    print("3. LISTADO DE MÓDULOS")
    print("="*60)
    
    # modules = agent.list_project_modules(project_name)
    # print(f"Total de módulos: {modules.get('total_modules', 0)}")
    # for module_type, files in modules.get('modules_by_type', {}).items():
    #     print(f"\n📁 {module_type.upper()}: {len(files)} archivos")
    #     for file in files[:3]:  # Mostrar solo los primeros 3
    #         print(f"   - {file.get('fileName')} ({file.get('complexity', 'unknown')})")
    
    # Ejemplo 4: Generar componente React
    print("\n" + "="*60)
    print("4. GENERACIÓN DE COMPONENTE REACT")
    print("="*60)
    
    module_name = "login"
    requirements = "usar hooks de React, incluir validación de formularios"
    
    print(f"Generando componente React basado en: {module_name}")
    # react_component = agent.generate_react_component(project_name, module_name, requirements)
    # print(react_component)

def ejemplo_flujo_completo():
    """
    Ejemplo del flujo completo que quieres lograr
    """
    print("\n" + "🎯" + "="*58)
    print("FLUJO COMPLETO: ANÁLISIS → CONSULTA → GENERACIÓN")
    print("="*60)
    
    agent = CodeAnalysisAgent()
    
    # Paso 1: Analizar proyecto
    print("📊 1. Analizando e indexando proyecto...")
    project_path = "C:/MisProyectos/Polymer/ProyectoNombre"
    result = agent.analyze_and_index_project(project_path)
    
    if "error" not in result:
        project_name = result["project_name"]
        print(f"✅ Proyecto '{project_name}' indexado correctamente")
        
        # Paso 2: Consultar módulo específico
        print("\n🔍 2. Consultando módulo login...")
        query_result = agent.query_project(project_name, "dame un resumen del módulo login")
        print(query_result.get("ai_response", "No encontrado"))
        
        # Paso 3: Generar componente React
        print("\n⚛️ 3. Generando componente React...")
        react_code = agent.generate_react_component(
            project_name, 
            "login", 
            "con validación, hooks modernos y estilos CSS modules"
        )
        print(react_code)
        
        # Paso 4: Limpiar datos (opcional)
        print("\n🗑️ 4. ¿Eliminar datos del proyecto? (opcional)")
        # agent.delete_project_data(project_name)
    
    else:
        print(f"❌ Error: {result['error']}")

def comandos_disponibles():
    """
    Muestra todos los comandos disponibles del analizador
    """
    print("\n📋 COMANDOS DISPONIBLES DEL ANALIZADOR:")
    print("="*50)
    
    comandos = {
        "Análisis": [
            "analyze_and_index_project(path, name) - Analizar e indexar proyecto completo",
            "analyze_project_structure(path) - Solo estructura del proyecto",
            "analyze_file_complexity(file_path) - Análisis de archivo individual"
        ],
        "Consultas": [
            "query_project(project, query) - Consulta semántica",
            "list_project_modules(project) - Listar módulos",
        ],
        "Generación": [
            "generate_react_component(project, module, requirements) - Generar React",
            "generate_migration_report(analysis) - Reporte de migración"
        ],
        "Gestión": [
            "create_weaviate_schema(project) - Crear esquema en Weaviate",
            "delete_project_data(project) - Eliminar datos del proyecto"
        ]
    }
    
    for categoria, metodos in comandos.items():
        print(f"\n🔧 {categoria}:")
        for metodo in metodos:
            print(f"   • {metodo}")

if __name__ == "__main__":
    main()
    comandos_disponibles()
    
    print("\n" + "🎉" + "="*58)
    print("¡ANALIZADOR LISTO PARA USAR!")
    print("="*60)
    print("Ahora puedes:")
    print("1. 📁 Analizar cualquier proyecto: agent.analyze_and_index_project(path)")
    print("2. 🔍 Hacer consultas: agent.query_project(project, 'dame resumen del módulo X')")
    print("3. ⚛️ Generar código: agent.generate_react_component(project, module)")
    print("4. 📊 Ver módulos: agent.list_project_modules(project)") 