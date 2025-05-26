import sys
import os
from samara.samara_dev_agent import SamaraDevAgent

def main():
    print("🧠 Samara Dev - Asistente de Desarrollo Avanzado")
    print("=" * 60)
    print("Capacidades especiales:")
    print("• Migración masiva de proyectos (300k+ líneas)")
    print("• Análisis profundo de código")
    print("• Soporte para Polymer → React, Angular → Vue, etc.")
    print("• Estrategias incrementales y completas")
    print("=" * 60)
    
    # Inicializar Samara Dev
    try:
        agente = SamaraDevAgent(profile_path="profiles/dev.json")
        print("✅ Samara Dev inicializada correctamente")
    except Exception as e:
        print(f"❌ Error inicializando Samara Dev: {e}")
        return
    
    player_id = "InuYashaMX"
    
    print(f"\n🤖 Samara Dev está lista. Escribe 'ayuda migración' para ver comandos especiales.")
    print("(Escribe 'salir' para terminar)\n")
    
    # Mostrar ejemplos de uso
    print("💡 Ejemplos de comandos:")
    print("• 'Migra el proyecto en C:\\MiApp de polymer a react'")
    print("• 'Analiza el proyecto en /home/user/mi-proyecto'")
    print("• 'ayuda migración' - Ver guía completa")
    print("• Conversación normal también funciona\n")
    
    while True:
        try:
            entrada = input("Tú: ").strip()
            
            if entrada.lower() in ["salir", "exit", "bye"]:
                print("\n🧊 Samara Dev: Hasta pronto. ¡Que tengas un excelente desarrollo!\n")
                break
            
            if not entrada:
                continue
            
            # Procesar entrada
            print("\n🤖 Samara Dev está procesando...")
            respuesta = agente.interactuar(player_id, entrada)
            print(f"\n🗣️ Samara Dev:\n{respuesta}\n")
            
        except KeyboardInterrupt:
            print("\n\n🧊 Samara Dev: Sesión interrumpida. ¡Hasta pronto!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    main() 