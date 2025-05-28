#!/usr/bin/env python3
"""
CLI para el analizador de código con Weaviate
Uso: python cli_analizador.py <comando> [argumentos]
"""

import sys
import argparse
import json
import os
import psutil
from pathlib import Path
from code_analysis_agent import CodeAnalysisAgent

def detect_optimal_config():
    """Detecta la configuración óptima basada en el hardware"""
    cpu_count = os.cpu_count()
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    # Detectar si es un Ryzen 9 (aproximado basado en cores)
    if cpu_count >= 24:  # Ryzen 9 de alta gama (32 threads)
        recommended_workers = min(28, int(cpu_count * 0.85))
        recommended_ollama = min(8, max(4, cpu_count // 6))
    elif cpu_count >= 16:  # Ryzen 9 estándar (24 threads) 
        recommended_workers = min(22, int(cpu_count * 0.9))
        recommended_ollama = min(6, max(4, cpu_count // 4))
    elif cpu_count >= 12:  # Ryzen 7 o similar
        recommended_workers = min(16, int(cpu_count * 0.8))
        recommended_ollama = min(4, max(2, cpu_count // 4))
    else:  # CPUs menores
        recommended_workers = min(8, cpu_count)
        recommended_ollama = 2
    
    # Ajustar según RAM disponible
    if memory_gb < 16:
        recommended_workers = max(4, recommended_workers // 2)
        recommended_ollama = max(2, recommended_ollama // 2)
    
    return {
        "cpu_count": cpu_count,
        "memory_gb": round(memory_gb, 1),
        "recommended_workers": recommended_workers,
        "recommended_ollama": recommended_ollama,
        "conservative_workers": max(4, recommended_workers - 4),
        "aggressive_workers": min(32, recommended_workers + 4)
    }

def setup_agent(max_workers=None, ollama_max_concurrent=2, file_timeout=60, ollama_timeout=30):
    """Inicializa el agente de análisis con configuración personalizable"""
    try:
        agent = CodeAnalysisAgent(
            ollama_url="http://localhost:11434",
            weaviate_url="http://localhost:8080",
            max_workers=max_workers,
            ollama_max_concurrent=ollama_max_concurrent,
            file_timeout=file_timeout,
            ollama_timeout=ollama_timeout
        )
        return agent
    except Exception as e:
        print(f"❌ Error inicializando el agente: {e}")
        return None

def cmd_analizar(args):
    """Comando: analizar e indexar un proyecto"""
    agent = setup_agent(
        max_workers=getattr(args, 'workers', None),
        ollama_max_concurrent=getattr(args, 'ollama_concurrent', 2),
        file_timeout=getattr(args, 'file_timeout', 60),
        ollama_timeout=getattr(args, 'ollama_timeout', 30)
    )
    if not agent:
        return
    
    project_path = args.path
    project_name = args.name or Path(project_path).name
    
    print(f"🚀 Analizando proyecto: {project_name}")
    print(f"📁 Ruta: {project_path}")
    
    if not Path(project_path).exists():
        print(f"❌ Error: La ruta {project_path} no existe")
        return
    
    # Confirmación si ya existe el proyecto en Weaviate
    force_schema = True
    try:
        existing_classes = [cls['class'] for cls in agent.weaviate_client.schema.get().get('classes', [])]
        class_name = f"Project_{project_name}" if project_name.startswith("_") else f"Project_{project_name}"
        if class_name in existing_classes:
            response = input(f"⚠️ Ya existe un proyecto llamado '{project_name}'. ¿Quieres sobreescribirlo? (s/N): ")
            if response.strip().lower() in ['s', 'sí', 'si', 'y', 'yes']:
                force_schema = True
            else:
                print("🔄 Reanudando indexación: solo se agregarán archivos nuevos.")
                force_schema = False
    except Exception as e:
        print(f"⚠️ No se pudo verificar la existencia previa del proyecto: {e}")
    
    # Habilitar logging detallado si se especifica verbose
    if hasattr(args, 'verbose') and args.verbose:
        agent._verbose_mode = True
    
    # Configurar archivos de log si se especifica --logfile
    if hasattr(args, 'logfile') and args.logfile:
        agent._setup_log_files("logs", project_name, clear_existing=True)
    
    result = agent.analyze_and_index_project(project_path, project_name, force_schema=force_schema)
    
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

def cmd_detectar(args):
    """Comando: detectar configuración óptima del hardware"""
    config = detect_optimal_config()
    
    print("🔍 **DETECCIÓN DE HARDWARE Y CONFIGURACIÓN ÓPTIMA**")
    print("=" * 60)
    print(f"💻 CPU Threads detectados: {config['cpu_count']}")
    print(f"🧠 RAM disponible: {config['memory_gb']} GB")
    print()
    
    # Detectar tipo de procesador aproximado
    if config['cpu_count'] >= 24:
        cpu_type = "🚀 Ryzen 9 de alta gama (32 threads) o similar"
    elif config['cpu_count'] >= 16:
        cpu_type = "⚡ Ryzen 9 estándar (24 threads) o similar"
    elif config['cpu_count'] >= 12:
        cpu_type = "🔥 Ryzen 7 o similar"
    else:
        cpu_type = "💻 CPU estándar"
    
    print(f"🏷️  Tipo detectado: {cpu_type}")
    print()
    
    print("📊 **CONFIGURACIONES RECOMENDADAS:**")
    print()
    
    print(f"🟢 **CONSERVADORA** (empezar aquí):")
    print(f"   --workers {config['conservative_workers']} --ollama_concurrent {max(2, config['recommended_ollama']-1)}")
    print()
    
    print(f"🟡 **RECOMENDADA** (balance óptimo):")
    print(f"   --workers {config['recommended_workers']} --ollama_concurrent {config['recommended_ollama']}")
    print()
    
    print(f"🔴 **AGRESIVA** (máximo rendimiento):")
    print(f"   --workers {config['aggressive_workers']} --ollama_concurrent {min(8, config['recommended_ollama']+1)}")
    print()
    
    print("🔧 **COMANDOS LISTOS PARA USAR:**")
    print()
    print("# Configuración conservadora:")
    print(f"python cli_analizador.py analizar /ruta/proyecto --workers {config['conservative_workers']} --ollama_concurrent {max(2, config['recommended_ollama']-1)}")
    print()
    print("# Configuración recomendada:")
    print(f"python cli_analizador.py analizar /ruta/proyecto --workers {config['recommended_workers']} --ollama_concurrent {config['recommended_ollama']}")
    print()
    print("# Configuración agresiva:")
    print(f"python cli_analizador.py analizar /ruta/proyecto --workers {config['aggressive_workers']} --ollama_concurrent {min(8, config['recommended_ollama']+1)}")
    print()
    
    print("💡 **CONSEJOS:**")
    print("   • Empieza con la configuración conservadora")
    print("   • Si ves que tu CPU no está al 100%, prueba la recomendada")
    print("   • Solo usa la agresiva si tienes suficiente RAM y refrigeración")
    print("   • Monitorea la temperatura de tu CPU durante el procesamiento")

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

def cmd_verificar_indexado(args):
    """Comando: verificar archivos/módulos realmente indexados en el proyecto"""
    agent = setup_agent()
    if not agent:
        return
    print(f"🔍 Verificando archivos indexados en el proyecto: {args.project}")
    result = agent.list_project_modules(args.project)
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        mods = result.get('all_modules', [])
        print(f"\n📦 Total módulos indexados: {len(mods)}\n")
        for i, mod in enumerate(mods, 1):
            print(f"{i}. {mod.get('fileName', 'Sin nombre')} | {mod.get('filePath', 'N/A')} | Tipo: {mod.get('artifactType', 'N/A')} | Dominio: {mod.get('businessDomain', 'N/A')}")
        if not mods:
            print("No se encontraron módulos indexados en el proyecto.")

def main():
    parser = argparse.ArgumentParser(
        description="Analizador de código con Weaviate",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:

  # ¡NUEVO! Detectar configuración óptima para tu hardware
  python cli_analizador.py detectar

  # Analizar un proyecto (configuración por defecto)
  python cli_analizador.py analizar C:/MisProyectos/Polymer/MiApp --name MiApp

  # Analizar con configuración personalizada de multihilos
  python cli_analizador.py analizar C:/MisProyectos/Polymer/MiApp --name MiApp --workers 8 --ollama_concurrent 4

  # Analizar con timeouts personalizados
  python cli_analizador.py analizar C:/MisProyectos/Polymer/MiApp --name MiApp --file_timeout 120 --ollama_timeout 60

  # Analizar con logs detallados (archivos ignorados y chunks)
  python cli_analizador.py analizar C:/MisProyectos/Polymer/MiApp --name MiApp --verbose

  # Analizar generando archivos de log separados (en directorio "logs")
  python cli_analizador.py analizar C:/MisProyectos/Polymer/MiApp --name MiApp --logfile

  # Consultar información
  python cli_analizador.py consultar MiApp "dame un resumen del módulo login"

  # Listar módulos
  python cli_analizador.py listar MiApp

  # Eliminar proyecto
  python cli_analizador.py eliminar MiApp

Opciones de multihilos:
  --workers N              : Número de threads para procesar archivos (default: min(16, CPU_count))
  --ollama_concurrent N    : Conexiones simultáneas a Ollama (default: 2)
  --file_timeout N         : Timeout en segundos por archivo (default: 60)
  --ollama_timeout N       : Timeout en segundos para Ollama (default: 30)
        """
    )
    
    subparsers = parser.add_subparsers(dest='comando', help='Comandos disponibles')
    
    # Comando: analizar
    parser_analizar = subparsers.add_parser('analizar', help='Analizar e indexar un proyecto')
    parser_analizar.add_argument('path', help='Ruta del proyecto a analizar')
    parser_analizar.add_argument('--name', help='Nombre del proyecto (opcional)')
    parser_analizar.add_argument('--verbose', '-v', action='store_true', help='Mostrar información detallada y logs de archivos procesados')
    parser_analizar.add_argument('--logfile', action='store_true', help='Generar archivos de log en directorio "logs" (borra logs anteriores)')
    parser_analizar.add_argument('--workers', type=int, help='Número máximo de trabajadores')
    parser_analizar.add_argument('--ollama_concurrent', type=int, help='Número máximo de conexiones concurrentes con Ollama')
    parser_analizar.add_argument('--file_timeout', type=int, help='Tiempo de espera para archivos')
    parser_analizar.add_argument('--ollama_timeout', type=int, help='Tiempo de espera para Ollama')
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
    
    # Comando: detectar
    parser_detectar = subparsers.add_parser('detectar', help='Detectar configuración óptima del hardware')
    parser_detectar.set_defaults(func=cmd_detectar)
    
    # Comando: eliminar
    parser_eliminar = subparsers.add_parser('eliminar', help='Eliminar datos del proyecto')
    parser_eliminar.add_argument('project', help='Nombre del proyecto')
    parser_eliminar.add_argument('--confirmar', '-y', action='store_true', help='Confirmar sin preguntar')
    parser_eliminar.set_defaults(func=cmd_eliminar)
    
    # Comando: verificar_indexado
    parser_verificar = subparsers.add_parser('verificar_indexado', help='Verificar archivos/módulos realmente indexados en el proyecto')
    parser_verificar.add_argument('project', help='Nombre del proyecto')
    parser_verificar.set_defaults(func=cmd_verificar_indexado)
    
    args = parser.parse_args()
    
    if not args.comando:
        parser.print_help()
        return
    
    # Ejecutar el comando
    args.func(args)

if __name__ == "__main__":
    main() 