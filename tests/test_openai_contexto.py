#!/usr/bin/env python3
"""
Script de prueba para verificar que OpenAI funciona con contextos largos
"""

from samara.smart_conversational_agent import SmartConversationalAgent

def test_contexto_largo():
    """Prueba con un contexto más largo que debería activar OpenAI"""
    print("🚀 Iniciando prueba de contexto largo con OpenAI...")
    
    # Inicializar con perfil de dev (sin recuerdos para contexto más limpio)
    agent = SmartConversationalAgent(profile_path="profiles/dev.json")
    
    # Mensaje que incluye mucho contexto
    mensaje_largo = """
    Necesito ayuda para analizar el módulo login del proyecto sacs3. 
    
    Este proyecto es muy complejo y tiene muchas dependencias. El módulo de login maneja:
    - Autenticación de usuarios
    - Validación de credenciales  
    - Gestión de sesiones
    - Integración con Firebase
    - Manejo de errores de autenticación
    - Redirección después del login
    - Tokens de seguridad
    - Encriptación de contraseñas
    
    También necesito entender cómo se integra con otros módulos del sistema,
    las dependencias que tiene, los endpoints que expone, y cualquier 
    patrón de diseño que esté utilizando.
    
    El sistema completo tiene más de 100 módulos y necesito una explicación
    detallada que me ayude a entender la arquitectura completa.
    
    ¿Puedes hacer un análisis completo del módulo login y su contexto?
    """
    
    print(f"📏 Mensaje de prueba: {len(mensaje_largo)} caracteres")
    print("="*50)
    
    # Hacer la consulta
    respuesta = agent.interactuar("test_user", mensaje_largo)
    
    print("="*50)
    print("📋 RESPUESTA:")
    print(respuesta)
    
    # Mostrar estadísticas
    print("\n📊 ESTADÍSTICAS DEL ROUTER:")
    stats = agent.model_router.get_stats()
    print(f"Total requests: {stats['total_requests']}")
    print(f"Por proveedor: {stats['by_provider']}")
    if 'by_context_size' in stats:
        print(f"Por tamaño de contexto: {stats['by_context_size']}")

def test_cambio_manual_openai():
    """Prueba forzando el uso de OpenAI"""
    print("\n🔄 Probando cambio manual a OpenAI...")
    
    agent = SmartConversationalAgent(profile_path="profiles/dev.json")
    
    # Forzar uso de OpenAI
    respuesta1 = agent.interactuar("test_user", "usar modelo gpt")
    print(f"Respuesta al cambio: {respuesta1}")
    
    # Hacer consulta simple
    respuesta2 = agent.interactuar("test_user", "¿Qué modelos tienes disponibles?")
    print(f"Respuesta: {respuesta2}")

def test_proveedores_disponibles():
    """Verificar qué proveedores están disponibles"""
    print("\n🔍 Verificando proveedores disponibles...")
    
    agent = SmartConversationalAgent(profile_path="profiles/dev.json")
    available = agent.model_router.get_available_providers()
    
    print(f"Proveedores disponibles: {available}")
    
    if 'gpt4' in available:
        print("✅ OpenAI/GPT-4 está disponible")
    else:
        print("❌ OpenAI/GPT-4 NO está disponible - verifica tu API key")
    
    if 'ollama' in available:
        print("✅ Ollama está disponible")
    else:
        print("❌ Ollama NO está disponible")

if __name__ == "__main__":
    print("🧪 PRUEBAS DE CONTEXTO LARGO Y OPENAI")
    print("="*60)
    
    # Verificar proveedores disponibles primero
    test_proveedores_disponibles()
    
    # Probar cambio manual
    test_cambio_manual_openai()
    
    # Probar contexto largo
    test_contexto_largo()
    
    print("\n✅ Pruebas completadas") 