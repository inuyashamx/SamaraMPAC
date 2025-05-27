#!/usr/bin/env python3
"""
Script específico para probar OpenAI con contextos largos
"""

from samara.smart_conversational_agent import SmartConversationalAgent

def test_openai_contexto_muy_largo():
    """Prueba con contexto muy largo que active automáticamente OpenAI"""
    print("🚀 PRUEBA: Contexto muy largo para activar OpenAI automáticamente")
    
    agent = SmartConversationalAgent(profile_path="profiles/dev.json")
    
    # Crear un contexto muy largo que supere los límites de Ollama
    contexto_base = """
    Necesito un análisis completo del proyecto sacs3. Este es un sistema muy complejo con múltiples capas:
    
    ARQUITECTURA GENERAL:
    - Frontend: Polymer 3.0 con componentes modulares
    - Backend: Node.js con Express y APIs REST
    - Base de datos: PostgreSQL con Redis para cache
    - Autenticación: Firebase Authentication + JWT
    - Deploy: Docker containers en AWS
    
    MÓDULOS PRINCIPALES:
    1. Autenticación y autorización
    2. Gestión de usuarios y perfiles
    3. Sistema de notificaciones
    4. Procesamiento de archivos
    5. APIs de integración externa
    6. Sistema de reportes y analytics
    7. Gestión de configuraciones
    8. Logs y monitoreo
    9. Sistema de backup automático
    10. Gestión de permisos granulares
    
    DEPENDENCIAS TÉCNICAS:
    - Librerías frontend: Polymer, LitElement, Firebase SDK
    - Librerías backend: Express, Sequelize, Passport, Multer
    - Testing: Jest, Cypress, Mocha
    - Build tools: Webpack, Babel, ESLint
    - CI/CD: GitHub Actions, Docker, AWS CodeDeploy
    
    PATRONES DE DISEÑO IMPLEMENTADOS:
    - MVC en el backend
    - Component pattern en el frontend
    - Repository pattern para acceso a datos
    - Factory pattern para creación de objetos
    - Observer pattern para eventos
    - Singleton para configuraciones globales
    
    CONSIDERACIONES DE SEGURIDAD:
    - Validación de entrada en todos los endpoints
    - Sanitización de datos antes de almacenar
    - HTTPS obligatorio en producción
    - Rate limiting en APIs públicas
    - Logs de auditoría para acciones críticas
    - Encriptación de datos sensibles
    
    PERFORMANCE Y ESCALABILIDAD:
    - Cache Redis para consultas frecuentes
    - CDN para assets estáticos
    - Database indexing optimizado
    - Lazy loading en componentes frontend
    - Connection pooling en base de datos
    - Load balancer para múltiples instancias
    """
    
    # Repetir el contexto varias veces para hacer el prompt muy largo
    mensaje_muy_largo = contexto_base * 3
    
    mensaje_final = f"""
    {mensaje_muy_largo}
    
    Con toda esta información de contexto, necesito que analices específicamente el módulo de login
    y me proporciones recomendaciones técnicas detalladas para optimizar:
    1. La seguridad del proceso de autenticación
    2. La experiencia de usuario en el login
    3. La integración con el resto del sistema
    4. Las posibles mejoras de performance
    5. Estrategias de testing para este módulo crítico
    
    Por favor, proporciona un análisis técnico profundo basado en los datos reales de Weaviate.
    """
    
    print(f"📏 Tamaño del mensaje: {len(mensaje_final):,} caracteres")
    print(f"📏 Tokens estimados: ~{len(mensaje_final)//4:,}")
    print("="*60)
    
    respuesta = agent.interactuar("test_openai", mensaje_final)
    
    print("="*60)
    print("📋 RESPUESTA:")
    print(respuesta)
    
    # Mostrar estadísticas detalladas
    print("\n📊 ESTADÍSTICAS:")
    stats = agent.model_router.get_stats()
    print(f"Total requests: {stats['total_requests']}")
    print(f"Por proveedor: {stats['by_provider']}")
    print(f"Por contexto: {stats.get('by_context_size', {})}")

def test_forzar_openai():
    """Prueba forzando específicamente OpenAI"""
    print("\n🎯 PRUEBA: Forzar uso específico de OpenAI")
    
    agent = SmartConversationalAgent(profile_path="profiles/dev.json")
    
    # Cambiar a OpenAI
    respuesta_cambio = agent.interactuar("test_openai", "usar modelo gpt")
    print(f"Cambio a OpenAI: {respuesta_cambio}")
    
    # Ahora hacer una consulta que use OpenAI
    consulta = """
    Analiza el módulo login del proyecto sacs3 con OpenAI. 
    Necesito un análisis técnico detallado que incluya:
    - Arquitectura del módulo
    - Patrones de seguridad implementados
    - Puntos de mejora específicos
    - Recomendaciones de optimización
    
    Esta consulta debería usar OpenAI ya que lo configuré específicamente.
    """
    
    respuesta = agent.interactuar("test_openai", consulta)
    
    print("\n📋 RESPUESTA CON OPENAI:")
    print(respuesta)
    
    # Estadísticas
    stats = agent.model_router.get_stats()
    print(f"\n📊 Último proveedor usado: {stats['by_provider']}")

if __name__ == "__main__":
    print("🧪 PRUEBAS ESPECÍFICAS DE OPENAI")
    print("="*70)
    
    # Primero forzar OpenAI específicamente
    test_forzar_openai()
    
    # Luego probar con contexto muy largo
    test_openai_contexto_muy_largo()
    
    print("\n✅ Pruebas de OpenAI completadas") 