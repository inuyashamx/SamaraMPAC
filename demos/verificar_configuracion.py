#!/usr/bin/env python3
"""
Script de verificación de configuración para Samara
Verifica qué proveedores de IA están disponibles y configurados
"""

import os
import requests
from samara.model_router_agent import ModelRouterAgent, ModelProvider

def print_header(title):
    """Imprime un header bonito"""
    print("\n" + "="*60)
    print(f"🔍 {title}")
    print("="*60)

def print_status(provider, status, details=""):
    """Imprime el estado de un proveedor"""
    icon = "✅" if status else "❌"
    print(f"{icon} {provider:<12} {'DISPONIBLE' if status else 'NO DISPONIBLE':<15} {details}")

def verificar_ollama():
    """Verifica si Ollama está disponible"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model.get("name", "unknown") for model in models]
            return True, f"Modelos: {', '.join(model_names[:3])}" + ("..." if len(model_names) > 3 else "")
        else:
            return False, f"Error HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "No se puede conectar (¿está corriendo?)"
    except Exception as e:
        return False, f"Error: {str(e)[:30]}..."

def verificar_api_key(provider_name, env_var):
    """Verifica si una API key está configurada"""
    api_key = os.getenv(env_var)
    if api_key:
        # Ocultar la mayor parte de la key por seguridad
        masked_key = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        return True, f"Configurada ({masked_key})"
    else:
        return False, f"Variable {env_var} no encontrada"

def verificar_configuracion_completa():
    """Verifica toda la configuración del sistema"""
    print_header("VERIFICACIÓN DE CONFIGURACIÓN DE SAMARA")
    
    print("\n📋 Estado de Proveedores de IA:")
    print("-" * 60)
    
    # Verificar Ollama
    ollama_ok, ollama_details = verificar_ollama()
    print_status("Ollama", ollama_ok, ollama_details)
    
    # Verificar API keys
    api_providers = [
        ("Claude", "CLAUDE_API_KEY"),
        ("GPT-4", "OPENAI_API_KEY"),
        ("Gemini", "GEMINI_API_KEY"),
        ("Perplexity", "PERPLEXITY_API_KEY")
    ]
    
    available_count = 1 if ollama_ok else 0
    
    for provider_name, env_var in api_providers:
        api_ok, api_details = verificar_api_key(provider_name, env_var)
        print_status(provider_name, api_ok, api_details)
        if api_ok:
            available_count += 1
    
    # Resumen
    print("\n" + "="*60)
    print(f"📊 RESUMEN: {available_count}/5 proveedores disponibles")
    
    if available_count == 0:
        print("\n❌ PROBLEMA CRÍTICO: No hay proveedores disponibles")
        print("\n💡 SOLUCIONES:")
        print("   1. Instalar Ollama (recomendado para empezar):")
        print("      curl -fsSL https://ollama.ai/install.sh | sh")
        print("      ollama pull llama3:instruct")
        print("\n   2. O configurar API keys:")
        print("      cp env_example.txt .env")
        print("      # Editar .env con tus claves")
        
    elif available_count == 1 and ollama_ok:
        print("\n⚠️  Solo Ollama disponible (modo básico)")
        print("💡 Para funcionalidad completa, considera agregar API keys cloud")
        
    else:
        print(f"\n✅ Configuración excelente con {available_count} proveedores")
        if ollama_ok:
            print("🏠 Ollama local para tareas rápidas y gratuitas")
        
        cloud_count = available_count - (1 if ollama_ok else 0)
        if cloud_count > 0:
            print(f"☁️  {cloud_count} proveedor(es) cloud para tareas complejas")

def probar_router():
    """Prueba el ModelRouterAgent con la configuración actual"""
    print_header("PRUEBA DEL ROUTER DE MODELOS")
    
    try:
        router = ModelRouterAgent()
        available = router.get_available_providers()
        
        if not available:
            print("❌ No se pudo inicializar el router - no hay proveedores disponibles")
            return
        
        print(f"\n✅ Router inicializado correctamente")
        print(f"📋 Proveedores configurados: {', '.join(available)}")
        
        # Probar una consulta simple
        print("\n🧪 Probando consulta simple...")
        result = router.route_and_query(
            prompt="Hola, ¿puedes responder con 'Sistema funcionando correctamente'?",
            max_tokens=50,
            temperature=0.1
        )
        
        if result["success"]:
            print(f"✅ Prueba exitosa con {result.get('provider', 'unknown')}")
            print(f"📝 Respuesta: {result.get('response', '')[:100]}...")
        else:
            print(f"❌ Prueba falló: {result.get('error', 'Error desconocido')}")
            
    except Exception as e:
        print(f"❌ Error al probar router: {e}")

def mostrar_recomendaciones():
    """Muestra recomendaciones basadas en la configuración"""
    print_header("RECOMENDACIONES")
    
    router = ModelRouterAgent()
    available = router.get_available_providers()
    
    if "ollama" in available:
        print("🏠 OLLAMA DISPONIBLE:")
        print("   • Perfecto para desarrollo y pruebas")
        print("   • Gratis y privado (local)")
        print("   • Bueno para conversación y tareas simples")
    
    if "claude" in available:
        print("\n🧠 CLAUDE DISPONIBLE:")
        print("   • Excelente para migración de código compleja")
        print("   • Muy bueno para análisis de arquitectura")
        print("   • Recomendado para proyectos grandes")
    
    if "gpt4" in available:
        print("\n🤖 GPT-4 DISPONIBLE:")
        print("   • Excelente para debugging y resolución de problemas")
        print("   • Muy bueno para diseño de arquitectura")
        print("   • Amplio conocimiento general")
    
    if "gemini" in available:
        print("\n💎 GEMINI DISPONIBLE:")
        print("   • Bueno para documentación y explicaciones")
        print("   • Rápido y económico")
        print("   • Excelente relación calidad-precio")
    
    if "perplexity" in available:
        print("\n🔍 PERPLEXITY DISPONIBLE:")
        print("   • Perfecto para búsquedas e información actual")
        print("   • Acceso a internet en tiempo real")
        print("   • Bueno para investigación")
    
    print(f"\n🎯 CONFIGURACIÓN RECOMENDADA:")
    if len(available) >= 3:
        print("   • Tu configuración es excelente para uso profesional")
        print("   • Tienes redundancia y opciones para diferentes tareas")
    elif len(available) == 2:
        print("   • Configuración sólida para la mayoría de casos")
        print("   • Considera agregar un proveedor más para redundancia")
    elif len(available) == 1:
        if "ollama" in available:
            print("   • Configuración básica funcional")
            print("   • Considera agregar Claude o GPT-4 para tareas complejas")
        else:
            print("   • Solo un proveedor cloud disponible")
            print("   • Instala Ollama como backup local gratuito")

def main():
    """Función principal"""
    print("🎯 VERIFICADOR DE CONFIGURACIÓN DE SAMARA")
    print("Este script verifica qué proveedores de IA están disponibles")
    
    # Verificar configuración básica
    verificar_configuracion_completa()
    
    # Probar el router si hay proveedores disponibles
    try:
        router = ModelRouterAgent()
        if router.get_available_providers():
            probar_router()
            mostrar_recomendaciones()
    except Exception as e:
        print(f"\n❌ No se pudo inicializar el sistema: {e}")
    
    print("\n" + "="*60)
    print("🚀 Para usar Samara: python samara_chat.py dev")
    print("📖 Para ver el demo: python demo_meta_agente.py")
    print("="*60)

if __name__ == "__main__":
    main() 