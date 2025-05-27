#!/usr/bin/env python3
from samara.smart_conversational_agent import SmartConversationalAgent

def test_login_real():
    print("🧪 Test real: pregunta específica sobre módulo login de sacs3")
    
    # Inicializar agente en modo dev
    agente = SmartConversationalAgent(profile_path="profiles/dev.json")
    print("✅ Agente inicializado")
    
    # Usar la sintaxis exacta que activa el análisis específico
    player_id = "TestUser"
    mensaje = "analiza el módulo login de sacs3"
    
    print(f"\n🗣️ Pregunta (sintaxis especial): {mensaje}")
    print("⏳ Procesando...")
    
    try:
        respuesta = agente.interactuar(player_id, mensaje)
        print(f"\n🤖 Respuesta de Samara:\n{respuesta}")
        
        print(f"\n" + "="*60)
        
        # También probar con comparativo.js
        mensaje2 = "analiza el módulo comparativo de sacs3"
        print(f"🗣️ Segunda pregunta: {mensaje2}")
        respuesta2 = agente.interactuar(player_id, mensaje2)
        print(f"\n🤖 Segunda respuesta:\n{respuesta2}")
        
        print(f"\n" + "="*60)
        
        # Y probar con config
        mensaje3 = "describe el módulo config de sacs3"
        print(f"🗣️ Tercera pregunta: {mensaje3}")
        respuesta3 = agente.interactuar(player_id, mensaje3)
        print(f"\n🤖 Tercera respuesta:\n{respuesta3}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_login_real() 