#!/usr/bin/env python3
from samara.smart_conversational_agent import SmartConversationalAgent

def test_samara_especifico():
    print("🧪 Test específico: preguntando por módulo login de sacs3...")
    
    # Inicializar agente en modo dev
    agente = SmartConversationalAgent(profile_path="profiles/dev.json")
    print("✅ Agente inicializado")
    
    # Preguntar específicamente por el módulo login
    player_id = "TestUser"
    mensaje = "explícame el módulo login de sacs3"
    
    print(f"\n🗣️ Pregunta: {mensaje}")
    print("⏳ Procesando...")
    
    try:
        respuesta = agente.interactuar(player_id, mensaje)
        print(f"\n🤖 Respuesta de Samara:\n{respuesta}")
        
        # También probar con otra consulta
        print(f"\n" + "="*50)
        mensaje2 = "¿qué hace el archivo comparativo.js en sacs3?"
        print(f"🗣️ Segunda pregunta: {mensaje2}")
        respuesta2 = agente.interactuar(player_id, mensaje2)
        print(f"\n🤖 Segunda respuesta:\n{respuesta2}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_samara_especifico() 