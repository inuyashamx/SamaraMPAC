#!/usr/bin/env python3
from samara.smart_conversational_agent import SmartConversationalAgent

def test_samara_dev():
    print("🧪 Iniciando test de Samara en modo dev...")
    
    # Inicializar agente en modo dev
    agente = SmartConversationalAgent(profile_path="profiles/dev.json")
    print("✅ Agente inicializado")
    
    # Hacer una pregunta simple
    player_id = "TestUser"
    mensaje = "¿qué proyectos tienes?"
    
    print(f"\n🗣️ Pregunta: {mensaje}")
    print("⏳ Procesando...")
    
    try:
        respuesta = agente.interactuar(player_id, mensaje)
        print(f"\n🤖 Respuesta de Samara:\n{respuesta}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_samara_dev() 