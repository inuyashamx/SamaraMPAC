#!/usr/bin/env python3
"""
Demo del Meta-Agente Orquestador de Samara
Muestra todas las capacidades del sistema inteligente de modelos
"""

import os
import sys
from samara.smart_conversational_agent import SmartConversationalAgent
from samara.model_router_agent import ModelProvider, TaskType

def print_header(title):
    """Imprime un header bonito"""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def print_section(title):
    """Imprime una sección"""
    print(f"\n📋 {title}")
    print("-" * 40)

def demo_basic_conversation():
    """Demo de conversación básica"""
    print_header("DEMO: Conversación Básica con Enrutamiento Inteligente")
    
    # Inicializar agente en modo dev
    agente = SmartConversationalAgent("profiles/dev.json")
    player_id = "DemoUser"
    
    # Ejemplos de diferentes tipos de consultas
    consultas = [
        "Hola, ¿cómo estás?",
        "Explícame qué es React",
        "Tengo un error en mi código Python, ¿me ayudas?",
        "Migra este archivo de JavaScript a TypeScript",
        "Analiza la arquitectura de mi proyecto",
        "¿Cuáles son las mejores prácticas para APIs REST?"
    ]
    
    for i, consulta in enumerate(consultas, 1):
        print(f"\n{i}. Usuario: {consulta}")
        respuesta = agente.interactuar(player_id, consulta)
        print(f"   Samara: {respuesta[:200]}...")
        
        # Mostrar qué modelo se usó
        print(f"   📊 Modelo detectado automáticamente")

def demo_model_selection():
    """Demo de selección manual de modelos"""
    print_header("DEMO: Selección Manual de Modelos")
    
    agente = SmartConversationalAgent("profiles/dev.json")
    player_id = "DemoUser"
    
    # Mostrar proveedores disponibles
    print("🤖 Proveedores disponibles:")
    available = agente.model_router.get_available_providers()
    for provider in available:
        print(f"   • {provider}")
    
    # Forzar uso de Ollama
    print("\n🔧 Configurando para usar solo Ollama...")
    respuesta = agente.interactuar(player_id, "usar modelo ollama")
    print(f"Samara: {respuesta}")
    
    # Hacer una consulta
    print("\n💬 Consulta con Ollama forzado:")
    respuesta = agente.interactuar(player_id, "Explícame los patrones de diseño")
    print(f"Samara: {respuesta[:200]}...")

def demo_dev_commands():
    """Demo de comandos de desarrollo"""
    print_header("DEMO: Comandos de Desarrollo Especializados")
    
    agente = SmartConversationalAgent("profiles/dev.json")
    player_id = "DemoUser"
    
    # Comando de migración
    print_section("Comando de Migración")
    respuesta = agente.interactuar(
        player_id, 
        "Migra el proyecto en /ruta/mi-proyecto de Polymer a React"
    )
    print(f"Samara: {respuesta[:300]}...")
    
    # Comando de análisis
    print_section("Comando de Análisis")
    respuesta = agente.interactuar(
        player_id, 
        "Analiza el proyecto en /ruta/mi-proyecto"
    )
    print(f"Samara: {respuesta[:300]}...")
    
    # Estadísticas
    print_section("Estadísticas del Sistema")
    respuesta = agente.interactuar(player_id, "stats")
    print(f"Samara: {respuesta}")

def demo_memory_intelligence():
    """Demo de memoria inteligente"""
    print_header("DEMO: Sistema de Memoria Inteligente")
    
    agente = SmartConversationalAgent("profiles/dev.json")
    player_id = "DemoUser"
    
    # Conversación que debería guardarse en memoria
    print_section("Información Técnica (se guarda en memoria)")
    respuesta = agente.interactuar(
        player_id, 
        "Estoy trabajando en un proyecto de e-commerce con Node.js, Express y MongoDB. Uso JWT para autenticación."
    )
    print(f"Samara: {respuesta[:200]}...")
    
    # Conversación simple que NO debería guardarse
    print_section("Saludo Simple (NO se guarda en memoria)")
    respuesta = agente.interactuar(player_id, "Hola")
    print(f"Samara: {respuesta[:200]}...")
    
    # Consulta que debería usar la memoria
    print_section("Consulta que Usa Memoria Previa")
    respuesta = agente.interactuar(
        player_id, 
        "¿Cómo puedo mejorar la seguridad de mi API?"
    )
    print(f"Samara: {respuesta[:200]}...")

def demo_task_detection():
    """Demo de detección automática de tareas"""
    print_header("DEMO: Detección Automática de Tipos de Tarea")
    
    from samara.model_router_agent import ModelRouterAgent
    
    router = ModelRouterAgent()
    
    # Ejemplos de diferentes tipos de tareas
    ejemplos = [
        ("Migra el proyecto completo de 300k líneas", TaskType.MIGRACION_COMPLEJA),
        ("Convierte este archivo a TypeScript", TaskType.MIGRACION_SENCILLA),
        ("Analiza la estructura del proyecto", TaskType.ANALISIS_CODIGO),
        ("Tengo un bug en mi código", TaskType.DEBUGGING),
        ("Documenta esta función", TaskType.DOCUMENTACION),
        ("¿Cómo estás?", TaskType.CONSULTA_SIMPLE),
        ("Diseña la arquitectura del sistema", TaskType.ARQUITECTURA)
    ]
    
    for prompt, expected_type in ejemplos:
        detected = router._detect_task_type(prompt, "dev")
        status = "✅" if detected == expected_type else "❌"
        print(f"{status} '{prompt}' → {detected.value}")

def demo_fallback_system():
    """Demo del sistema de fallback"""
    print_header("DEMO: Sistema de Fallback")
    
    from samara.model_router_agent import ModelRouterAgent, ModelProvider
    
    router = ModelRouterAgent()
    
    print("🔧 Simulando falla de proveedor principal...")
    
    # Simular que Claude no está disponible
    original_claude_key = router.model_config[ModelProvider.CLAUDE]["api_key"]
    router.model_config[ModelProvider.CLAUDE]["api_key"] = None
    
    print("❌ Claude deshabilitado temporalmente")
    print("🔄 El sistema debería usar fallback automáticamente...")
    
    # Hacer una consulta que normalmente usaría Claude
    result = router.route_and_query(
        "Migra este proyecto complejo de 300k líneas",
        TaskType.MIGRACION_COMPLEJA
    )
    
    if result["success"]:
        provider_used = result.get("provider", "unknown")
        used_fallback = result.get("used_fallback", False)
        
        if used_fallback:
            original = result.get("original_provider", "unknown")
            print(f"✅ Fallback exitoso: {original} → {provider_used}")
        else:
            print(f"✅ Usó directamente: {provider_used}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Restaurar configuración
    router.model_config[ModelProvider.CLAUDE]["api_key"] = original_claude_key

def demo_statistics():
    """Demo de estadísticas completas"""
    print_header("DEMO: Sistema de Estadísticas")
    
    agente = SmartConversationalAgent("profiles/dev.json")
    player_id = "DemoUser"
    
    # Hacer varias consultas para generar estadísticas
    consultas = [
        "Hola",
        "Migra este archivo",
        "Analiza el código",
        "Tengo un error",
        "stats"
    ]
    
    for consulta in consultas[:-1]:  # Todas excepto 'stats'
        agente.interactuar(player_id, consulta)
    
    # Mostrar estadísticas
    print_section("Estadísticas Generadas")
    respuesta = agente.interactuar(player_id, "stats")
    print(respuesta)

def main():
    """Función principal del demo"""
    print("🎯 DEMO COMPLETO DEL META-AGENTE ORQUESTADOR DE SAMARA")
    print("=" * 60)
    print("Este demo muestra todas las capacidades del sistema:")
    print("• Enrutamiento inteligente de modelos")
    print("• Detección automática de tipos de tarea")
    print("• Sistema de fallback robusto")
    print("• Memoria inteligente selectiva")
    print("• Comandos especializados de desarrollo")
    print("• Estadísticas completas")
    
    # Verificar dependencias
    print("\n🔍 Verificando dependencias...")
    
    try:
        # Verificar si Ollama está disponible
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print("✅ Ollama disponible")
        else:
            print("❌ Ollama no disponible")
    except:
        print("❌ Ollama no disponible")
    
    # Verificar API keys
    api_keys = ["CLAUDE_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "PERPLEXITY_API_KEY"]
    for key in api_keys:
        if os.getenv(key):
            print(f"✅ {key} configurada")
        else:
            print(f"❌ {key} no configurada")
    
    print("\n" + "="*60)
    
    # Ejecutar demos
    try:
        demo_task_detection()
        demo_basic_conversation()
        demo_model_selection()
        demo_memory_intelligence()
        demo_dev_commands()
        demo_fallback_system()
        demo_statistics()
        
        print_header("DEMO COMPLETADO")
        print("🎉 Todas las funcionalidades han sido demostradas")
        print("💡 Para usar el sistema completo, ejecuta: python samara_chat.py dev")
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante el demo: {e}")
        print("💡 Asegúrate de tener todas las dependencias instaladas")

if __name__ == "__main__":
    main() 