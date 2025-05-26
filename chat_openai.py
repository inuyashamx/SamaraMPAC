#!/usr/bin/env python3
"""
Chat principal de Samara con soporte inteligente para OpenAI en contextos largos
"""

from samara.smart_conversational_agent import SmartConversationalAgent
import sys

def main():
    print("🤖 SAMARA - ASISTENTE DE DESARROLLO CON OPENAI")
    print("=" * 60)
    print("✨ OpenAI se activará automáticamente para contextos largos")
    print("💡 Comandos especiales:")
    print("   • 'usar modelo gpt' - Forzar OpenAI para toda la sesión")
    print("   • 'usar modelo ollama' - Usar Ollama local")
    print("   • 'salir' - Terminar")
    print("=" * 60)
    
    # Inicializar con perfil developer (sin recuerdos para contexto limpio)
    agent = SmartConversationalAgent(profile_path="profiles/dev.json")
    
    # Mostrar proveedores disponibles
    available = agent.model_router.get_available_providers()
    print(f"🔧 Proveedores disponibles: {', '.join(available)}")
    
    if 'gpt4' in available:
        print("✅ OpenAI/GPT-4 listo para contextos largos")
    else:
        print("⚠️ OpenAI no disponible - usando solo Ollama")
    
    print("\n🚀 ¡Samara lista! Empieza a preguntar...")
    print("-" * 60)
    
    user_id = "paul"
    
    while True:
        try:
            # Leer input del usuario
            mensaje = input("\n💬 Tú: ").strip()
            
            # Comando de salida
            if mensaje.lower() in ['salir', 'exit', 'quit']:
                print("\n👋 ¡Hasta luego!")
                
                # Mostrar estadísticas finales
                stats = agent.model_router.get_stats()
                if stats['total_requests'] > 0:
                    print(f"\n📊 Resumen de la sesión:")
                    print(f"   Total consultas: {stats['total_requests']}")
                    for provider, data in stats['by_provider'].items():
                        total = data['success'] + data['failed']
                        if total > 0:
                            success_rate = (data['success'] / total) * 100
                            print(f"   {provider}: {data['success']}/{total} ({success_rate:.1f}% éxito)")
                
                break
            
            # Saltar si está vacío
            if not mensaje:
                continue
            
            # Procesar mensaje
            print("\n🧠 Samara:", end=" ")
            respuesta = agent.interactuar(user_id, mensaje)
            print(respuesta)
            
            # Separador visual
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 ¡Interrumpido por el usuario! Hasta luego.")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("🔄 Intentando continuar...")

if __name__ == "__main__":
    main() 