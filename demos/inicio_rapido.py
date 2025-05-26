#!/usr/bin/env python3
"""
Script de Inicio Rápido para Samara
Guía al usuario paso a paso para configurar y usar el sistema
"""

import os
import sys
import subprocess
from demos.verificar_configuracion import verificar_configuracion_completa

def print_header(title):
    """Imprime un header bonito"""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def print_step(step, title):
    """Imprime un paso numerado"""
    print(f"\n📋 PASO {step}: {title}")
    print("-" * 40)

def esperar_usuario():
    """Espera que el usuario presione Enter"""
    input("\n⏸️  Presiona Enter para continuar...")

def ejecutar_comando(comando, descripcion):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n🔧 Ejecutando: {descripcion}")
    print(f"💻 Comando: {comando}")
    
    respuesta = input("¿Ejecutar este comando? (s/n): ").lower().strip()
    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        try:
            result = subprocess.run(comando, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Comando ejecutado exitosamente")
                if result.stdout:
                    print(f"📝 Salida: {result.stdout[:200]}...")
            else:
                print(f"❌ Error: {result.stderr}")
        except Exception as e:
            print(f"❌ Error ejecutando comando: {e}")
    else:
        print("⏭️  Comando omitido")

def configurar_ollama():
    """Guía para configurar Ollama"""
    print_step(1, "Configurar Ollama (Recomendado)")
    
    print("🏠 Ollama es un proveedor local gratuito que funciona sin API keys")
    print("💡 Es perfecto para empezar y como backup siempre disponible")
    
    # Verificar si ya está instalado
    try:
        result = subprocess.run("ollama --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama ya está instalado")
            print(f"📝 Versión: {result.stdout.strip()}")
            
            # Verificar si está corriendo
            import requests
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    print("✅ Ollama está corriendo")
                    models = response.json().get("models", [])
                    if models:
                        print(f"📦 Modelos instalados: {len(models)}")
                    else:
                        print("⚠️  No hay modelos instalados")
                        ejecutar_comando("ollama pull llama3:instruct", "Descargar modelo Llama3")
                else:
                    print("❌ Ollama no está corriendo")
                    ejecutar_comando("ollama serve", "Iniciar Ollama")
            except:
                print("❌ Ollama no está corriendo")
                ejecutar_comando("ollama serve", "Iniciar Ollama")
        else:
            print("❌ Ollama no está instalado")
            print("\n💡 Opciones de instalación:")
            print("   1. Linux/Mac: curl -fsSL https://ollama.ai/install.sh | sh")
            print("   2. Windows: Descargar desde https://ollama.ai/download")
            
            if sys.platform.startswith('linux') or sys.platform == 'darwin':
                ejecutar_comando("curl -fsSL https://ollama.ai/install.sh | sh", "Instalar Ollama")
                ejecutar_comando("ollama pull llama3:instruct", "Descargar modelo Llama3")
            else:
                print("🪟 En Windows, descarga el instalador desde https://ollama.ai/download")
                esperar_usuario()
    except Exception as e:
        print(f"❌ Error verificando Ollama: {e}")

def configurar_api_keys():
    """Guía para configurar API keys"""
    print_step(2, "Configurar API Keys (Opcional pero Recomendado)")
    
    print("☁️  Las API keys te dan acceso a modelos más potentes para tareas complejas")
    print("💰 Cada proveedor tiene diferentes precios y capacidades")
    
    # Verificar si existe .env
    if os.path.exists(".env"):
        print("✅ Archivo .env encontrado")
    else:
        print("❌ Archivo .env no encontrado")
        if os.path.exists("env_example.txt"):
            ejecutar_comando("cp env_example.txt .env", "Crear archivo .env desde ejemplo")
        else:
            print("❌ Archivo env_example.txt no encontrado")
            return
    
    print("\n🔑 Proveedores disponibles:")
    print("   • Claude (Anthropic): Excelente para código complejo")
    print("   • GPT-4 (OpenAI): Muy bueno para debugging y arquitectura")
    print("   • Gemini (Google): Rápido y económico")
    print("   • Perplexity: Acceso a internet en tiempo real")
    
    print(f"\n📝 Para configurar, edita el archivo .env:")
    print(f"   nano .env  # o tu editor favorito")
    
    respuesta = input("\n¿Quieres abrir el archivo .env ahora? (s/n): ").lower().strip()
    if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
        # Intentar abrir con diferentes editores
        editores = ['code', 'nano', 'vim', 'notepad']
        for editor in editores:
            try:
                subprocess.run([editor, '.env'])
                break
            except:
                continue
        else:
            print("💡 Abre manualmente el archivo .env con tu editor favorito")

def verificar_sistema():
    """Verifica que todo esté configurado correctamente"""
    print_step(3, "Verificar Configuración")
    
    print("🔍 Verificando qué proveedores están disponibles...")
    
    try:
        from samara.model_router_agent import ModelRouterAgent
        router = ModelRouterAgent()
        available = router.get_available_providers()
        
        if available:
            print(f"✅ Sistema configurado correctamente")
            print(f"📋 Proveedores disponibles: {', '.join(available)}")
        else:
            print("❌ No hay proveedores disponibles")
            print("💡 Revisa la configuración de Ollama o las API keys")
            
    except Exception as e:
        print(f"❌ Error verificando sistema: {e}")

def mostrar_opciones_uso():
    """Muestra las opciones de uso del sistema"""
    print_step(4, "¡Listo para Usar!")
    
    print("🎯 Opciones disponibles:")
    print("\n1. 🔍 Verificar configuración detallada:")
    print("   python verificar_configuracion.py")
    
    print("\n2. 🚀 Usar Samara en modo desarrollo:")
    print("   python samara_chat.py dev")
    
    print("\n3. 🎮 Usar Samara en modo juego:")
    print("   python samara_chat.py game")
    
    print("\n4. 🧪 Ver demo completo:")
    print("   python demo_meta_agente.py")
    
    print("\n💡 Comandos especiales en Samara:")
    print("   • 'stats' - Ver estadísticas del sistema")
    print("   • 'usar modelo ollama' - Forzar un modelo específico")
    print("   • 'migra el proyecto en /ruta de polymer a react' - Migración")
    print("   • 'analiza el proyecto en /ruta' - Análisis de código")

def main():
    """Función principal del script de inicio rápido"""
    print("🎯 INICIO RÁPIDO DE SAMARA")
    print("Meta-Agente Orquestador de Modelos de IA")
    print("="*60)
    
    print("\n🎉 ¡Bienvenido a Samara!")
    print("Este script te ayudará a configurar el sistema paso a paso")
    
    esperar_usuario()
    
    try:
        # Paso 1: Configurar Ollama
        configurar_ollama()
        esperar_usuario()
        
        # Paso 2: Configurar API keys
        configurar_api_keys()
        esperar_usuario()
        
        # Paso 3: Verificar sistema
        verificar_sistema()
        esperar_usuario()
        
        # Paso 4: Mostrar opciones de uso
        mostrar_opciones_uso()
        
        print("\n" + "="*60)
        print("🎉 ¡Configuración completada!")
        print("🚀 Ya puedes usar Samara con: python samara_chat.py dev")
        print("="*60)
        
        # Preguntar si quiere ejecutar algo ahora
        print("\n¿Qué te gustaría hacer ahora?")
        print("1. Verificar configuración detallada")
        print("2. Iniciar Samara en modo dev")
        print("3. Ver demo completo")
        print("4. Salir")
        
        opcion = input("\nElige una opción (1-4): ").strip()
        
        if opcion == "1":
            subprocess.run([sys.executable, "verificar_configuracion.py"])
        elif opcion == "2":
            subprocess.run([sys.executable, "samara_chat.py", "dev"])
        elif opcion == "3":
            subprocess.run([sys.executable, "demo_meta_agente.py"])
        else:
            print("👋 ¡Hasta luego! Usa 'python samara_chat.py dev' cuando quieras empezar")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Configuración interrumpida por el usuario")
        print("💡 Puedes ejecutar este script de nuevo cuando quieras")
    except Exception as e:
        print(f"\n❌ Error durante la configuración: {e}")
        print("💡 Puedes intentar configurar manualmente o pedir ayuda")

if __name__ == "__main__":
    main() 