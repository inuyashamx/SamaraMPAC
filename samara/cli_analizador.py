#!/usr/bin/env python3
"""
CLI para el analizador de código con Weaviate
Uso: python cli_analizador.py <comando> [argumentos]
"""

import sys
import argparse
import json
from pathlib import Path
from code_analysis_agent import CodeAnalysisAgent

def setup_agent():
    """Inicializa el agente de análisis"""
    try:
        agent = CodeAnalysisAgent(
            ollama_url="http://localhost:11434",
            weaviate_url="http://localhost:8080"
        )
        return agent
    except Exception as e:
        print(f"❌ Error inicializando el agente: {e}")
        return None

def cmd_analizar(args):
    """Comando: analizar e indexar un proyecto"""
    agent = setup_agent()
    if not agent:
        return
    
    project_path = args.path
    project_name = args.name or Path(project_path).name
    
    print(f"🚀 Analizando proyecto: {project_name}")
    print(f"📁 Ruta: {project_path}")
    
    if not Path(project_path).exists():
        print(f"❌ Error: La ruta {project_path} no existe")
        return
    
    result = agent.analyze_and_index_project(project_path, project_name)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"\n✅ Análisis completado:")
        print(f"   📊 {result['indexed_files']} archivos indexados")
        print(f"   🔧 Tecnologías: {', '.join(result['technologies'])}")
        print(f"   🏗️  Patrones: {', '.join(result['architecture_patterns'])}")
        
        if args.verbose:
            print(f"\n📋 Resumen del proyecto:")
            print(result.get('project_summary', 'No disponible'))

def cmd_consultar(args):
    """Comando: consultar información del proyecto"""
    agent = setup_agent()
    if not agent:
        return
    
    print(f"🔍 Consultando: '{args.query}' en proyecto '{args.project}'")
    
    result = agent.query_project(args.project, args.query, limit=args.limit)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"\n📄 Archivos encontrados: {result['files_found']}")
        print(f"\n🤖 Respuesta:")
        print(result.get('ai_response', 'No disponible'))
        
        if args.verbose and result.get('results'):
            print(f"\n📋 Detalles de archivos encontrados:")
            for i, file_data in enumerate(result['results'], 1):
                print(f"\n{i}. {file_data.get('fileName', 'Sin nombre')}")
                print(f"   📁 Ruta: {file_data.get('filePath', 'N/A')}")
                print(f"   🏷️  Tipo: {file_data.get('moduleType', 'N/A')}")
                print(f"   🔧 Tecnología: {file_data.get('technology', 'N/A')}")
                print(f"   📊 Complejidad: {file_data.get('complexity', 'N/A')}")

def cmd_listar(args):
    """Comando: listar módulos del proyecto"""
    agent = setup_agent()
    if not agent:
        return
    
    print(f"📋 Listando módulos del proyecto: {args.project}")
    
    result = agent.list_project_modules(args.project)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"\n📊 Total de módulos: {result['total_modules']}")
        
        for module_type, files in result.get('modules_by_type', {}).items():
            print(f"\n📁 {module_type.upper()}: {len(files)} archivos")
            
            for file_data in files[:args.limit]:
                complexity = file_data.get('complexity', 'unknown')
                emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(complexity, "⚪")
                print(f"   {emoji} {file_data.get('fileName', 'Sin nombre')} ({complexity})")
                
                if args.verbose:
                    print(f"      📁 {file_data.get('filePath', 'N/A')}")
                    print(f"      🔧 {file_data.get('technology', 'N/A')}")

def cmd_generar(args):
    """Comando: generar componente React"""
    agent = setup_agent()
    if not agent:
        return
    
    print(f"⚛️ Generando componente React para módulo: {args.modulo}")
    print(f"📁 Proyecto: {args.project}")
    
    if args.requisitos:
        print(f"📋 Requisitos adicionales: {args.requisitos}")
    
    result = agent.generate_react_component(
        args.project, 
        args.modulo, 
        args.requisitos or ""
    )
    
    print(f"\n📄 Componente React generado:")
    print("=" * 60)
    print(result)
    print("=" * 60)
    
    # Guardar en archivo si se especifica
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)
        
        print(f"\n💾 Componente guardado en: {output_path}")

def cmd_migrar(args):
    """Comando: migrar módulo a nueva tecnología"""
    agent = setup_agent()
    if not agent:
        return
    
    print(f"🚀 Migrando módulo '{args.modulo}' del proyecto '{args.project}' a {args.tecnologia}")
    
    if args.requisitos:
        print(f"📋 Requisitos adicionales: {args.requisitos}")
    
    result = agent.migrate_module_to_technology(
        args.project, 
        args.modulo, 
        args.tecnologia,
        args.requisitos or ""
    )
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        if "suggestions" in result:
            print("\n💡 Sugerencias:")
            for suggestion in result["suggestions"]:
                print(f"   • {suggestion}")
    else:
        print(f"\n✅ Migración completada:")
        print(f"   📄 Módulo: {result['module_name']}")
        print(f"   🔄 De: {result['original_technology']} → A: {result['target_technology']}")
        print(f"   📊 Complejidad: {result['complexity']}")
        print(f"   📁 Archivos analizados: {result['files_analyzed']}")
        print(f"   🧩 Chunks analizados: {result['chunks_analyzed']}")
        
        print(f"\n📋 Análisis del módulo original:")
        print(result.get('analysis_summary', 'No disponible'))
        
        print(f"\n📄 Código migrado:")
        print("=" * 80)
        print(result['migrated_code'])
        print("=" * 80)
        
        print(f"\n📊 Reporte de migración:")
        print(result.get('migration_report', 'No disponible'))
        
        if result.get('recommendations'):
            print(f"\n💡 Recomendaciones:")
            for rec in result['recommendations']:
                print(f"   • {rec}")
        
        # Guardar en archivo si se especifica
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Crear un reporte completo
            full_report = f"""
# Migración de {result['module_name']}

## Información general
- **Módulo original**: {result['module_name']}
- **Tecnología original**: {result['original_technology']}
- **Tecnología destino**: {result['target_technology']}
- **Complejidad**: {result['complexity']}

## Análisis del módulo original
{result.get('analysis_summary', 'No disponible')}

## Código migrado
```{args.tecnologia.lower()}
{result['migrated_code']}
```

## Reporte de migración
{result.get('migration_report', 'No disponible')}

## Recomendaciones
{chr(10).join([f"- {rec}" for rec in result.get('recommendations', [])])}
"""
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_report)
            
            print(f"\n💾 Reporte completo guardado en: {output_path}")

def cmd_eliminar(args):
    """Comando: eliminar datos del proyecto"""
    if not args.confirmar:
        response = input(f"⚠️  ¿Estás seguro de eliminar los datos del proyecto '{args.project}'? (s/N): ")
        if response.lower() not in ['s', 'si', 'sí', 'yes', 'y']:
            print("❌ Operación cancelada")
            return
    
    agent = setup_agent()
    if not agent:
        return
    
    if agent.delete_project_data(args.project):
        print(f"✅ Datos del proyecto '{args.project}' eliminados correctamente")
    else:
        print(f"❌ Error eliminando datos del proyecto '{args.project}'")

def main():
    parser = argparse.ArgumentParser(
        description="Analizador de código con Weaviate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # Analizar un proyecto
  python cli_analizador.py analizar C:/MisProyectos/Polymer/MiApp --name MiApp

  # Consultar información
  python cli_analizador.py consultar MiApp "dame un resumen del módulo login"

  # Listar módulos
  python cli_analizador.py listar MiApp

  # Generar componente React
  python cli_analizador.py generar MiApp login --requisitos "con hooks y validación"

  # Migrar módulo a nueva tecnología
  python cli_analizador.py migrar MiApp login react --requisitos "con hooks y validación"

  # Eliminar proyecto
  python cli_analizador.py eliminar MiApp
        """
    )
    
    subparsers = parser.add_subparsers(dest='comando', help='Comandos disponibles')
    
    # Comando: analizar
    parser_analizar = subparsers.add_parser('analizar', help='Analizar e indexar un proyecto')
    parser_analizar.add_argument('path', help='Ruta del proyecto a analizar')
    parser_analizar.add_argument('--name', help='Nombre del proyecto (opcional)')
    parser_analizar.add_argument('--verbose', '-v', action='store_true', help='Mostrar información detallada')
    parser_analizar.set_defaults(func=cmd_analizar)
    
    # Comando: consultar
    parser_consultar = subparsers.add_parser('consultar', help='Consultar información del proyecto')
    parser_consultar.add_argument('project', help='Nombre del proyecto')
    parser_consultar.add_argument('query', help='Consulta a realizar')
    parser_consultar.add_argument('--limit', type=int, default=5, help='Límite de resultados (default: 5)')
    parser_consultar.add_argument('--verbose', '-v', action='store_true', help='Mostrar información detallada')
    parser_consultar.set_defaults(func=cmd_consultar)
    
    # Comando: listar
    parser_listar = subparsers.add_parser('listar', help='Listar módulos del proyecto')
    parser_listar.add_argument('project', help='Nombre del proyecto')
    parser_listar.add_argument('--limit', type=int, default=10, help='Límite de archivos por tipo (default: 10)')
    parser_listar.add_argument('--verbose', '-v', action='store_true', help='Mostrar información detallada')
    parser_listar.set_defaults(func=cmd_listar)
    
    # Comando: generar
    parser_generar = subparsers.add_parser('generar', help='Generar componente React')
    parser_generar.add_argument('project', help='Nombre del proyecto')
    parser_generar.add_argument('modulo', help='Nombre del módulo a convertir')
    parser_generar.add_argument('--requisitos', help='Requisitos adicionales')
    parser_generar.add_argument('--output', '-o', help='Archivo de salida para guardar el componente')
    parser_generar.set_defaults(func=cmd_generar)
    
    # Comando: migrar
    parser_migrar = subparsers.add_parser('migrar', help='Migrar módulo a nueva tecnología')
    parser_migrar.add_argument('project', help='Nombre del proyecto')
    parser_migrar.add_argument('modulo', help='Nombre del módulo a migrar')
    parser_migrar.add_argument('tecnologia', choices=['react', 'vue', 'angular', 'svelte'], help='Tecnología destino')
    parser_migrar.add_argument('--requisitos', help='Requisitos adicionales')
    parser_migrar.add_argument('--output', '-o', help='Archivo de salida para guardar el reporte completo')
    parser_migrar.set_defaults(func=cmd_migrar)
    
    # Comando: eliminar
    parser_eliminar = subparsers.add_parser('eliminar', help='Eliminar datos del proyecto')
    parser_eliminar.add_argument('project', help='Nombre del proyecto')
    parser_eliminar.add_argument('--confirmar', '-y', action='store_true', help='Confirmar sin preguntar')
    parser_eliminar.set_defaults(func=cmd_eliminar)
    
    args = parser.parse_args()
    
    if not args.comando:
        parser.print_help()
        return
    
    # Ejecutar el comando
    args.func(args)

if __name__ == "__main__":
    main() 