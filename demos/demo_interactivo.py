#!/usr/bin/env python3
"""
Demo Interactivo del Sistema de Enrutamiento Inteligente
Permite al usuario probar diferentes tipos de consultas y ver cómo se enrutan
"""

from samara.smart_conversational_agent import SmartConversationalAgent
import time

def print_header(title):
    """Imprime un header bonito"""
    print("\n" + "="*70)
    print(f"🧠 {title}")
    print("="*70)

def print_context_info(result):
    """Muestra información del contexto y enrutamiento"""
    if result and isinstance(result, str) and "🤖" in result:
        # Extraer información del modelo del resultado
        lines = result.split('\n')
        model_line = [line for line in lines if line.startswith('🤖')]
        if model_line:
            print(f"\n📊 {model_line[0]}")

def demo_interactivo():
    """Demo interactivo principal"""
    print_header("DEMO INTERACTIVO - ENRUTAMIENTO INTELIGENTE")
    
    print("🎯 Este demo te permite probar el sistema de enrutamiento basado en contexto")
    print("💡 Cada consulta será analizada y enrutada al modelo más apropiado")
    print("📊 En modo dev verás información detallada del enrutamiento")
    
    try:
        # Inicializar agente en modo dev
        agente = SmartConversationalAgent(profile_path="profiles/dev.json")
        player_id = "demo_user"
        
        print(f"\n✅ Sistema inicializado correctamente")
        print(f"📋 Proveedores disponibles: {agente.model_router.get_available_providers()}")
        
        # Ejemplos predefinidos
        ejemplos = [
            {
                "categoria": "Consulta Simple",
                "prompt": "Hola, ¿cómo estás?",
                "descripcion": "Saludo básico - debería usar Ollama local"
            },
            {
                "categoria": "Pregunta Técnica",
                "prompt": "¿Cuál es la diferencia entre async/await y Promises en JavaScript?",
                "descripcion": "Pregunta técnica mediana - Ollama puede manejarla"
            },
            {
                "categoria": "Análisis de Código",
                "prompt": "Analiza este código React y sugiere mejoras:\n\n" + """
import React, { useState, useEffect } from 'react';

const UserProfile = ({ userId }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then(response => response.json())
      .then(data => {
        setUser(data);
        setLoading(false);
      });
  }, [userId]);
  
  if (loading) return <div>Loading...</div>;
  
  return (
    <div>
      <h1>{user.name}</h1>
      <p>{user.email}</p>
    </div>
  );
};

export default UserProfile;
""" * 3,
                "descripcion": "Análisis de código mediano - contexto más grande"
            },
            {
                "categoria": "Comando de Migración",
                "prompt": "Migra el proyecto en C:\\MiProyecto de polymer a react",
                "descripcion": "Comando especializado - activará SamaraDevAgent"
            }
        ]
        
        while True:
            print_header("OPCIONES DISPONIBLES")
            print("1. 📝 Escribir consulta personalizada")
            print("2. 🧪 Probar ejemplos predefinidos")
            print("3. 📊 Ver estadísticas del sistema")
            print("4. 🔧 Cambiar modelo forzado")
            print("5. ❌ Salir")
            
            opcion = input("\n🎯 Elige una opción (1-5): ").strip()
            
            if opcion == "1":
                # Consulta personalizada
                print("\n📝 CONSULTA PERSONALIZADA")
                print("-" * 40)
                consulta = input("Escribe tu consulta: ").strip()
                
                if consulta:
                    print(f"\n🔄 Procesando: {consulta[:50]}{'...' if len(consulta) > 50 else ''}")
                    
                    start_time = time.time()
                    respuesta = agente.interactuar(player_id, consulta)
                    end_time = time.time()
                    
                    print(f"\n💬 RESPUESTA:")
                    print("-" * 40)
                    # Mostrar solo la respuesta principal (sin info del modelo)
                    respuesta_limpia = respuesta.split('\n\n🤖')[0] if '\n\n🤖' in respuesta else respuesta
                    print(respuesta_limpia)
                    
                    print_context_info(respuesta)
                    print(f"\n⏱️ Tiempo de respuesta: {end_time - start_time:.2f} segundos")
            
            elif opcion == "2":
                # Ejemplos predefinidos
                print("\n🧪 EJEMPLOS PREDEFINIDOS")
                print("-" * 40)
                
                for i, ejemplo in enumerate(ejemplos, 1):
                    print(f"{i}. {ejemplo['categoria']}")
                    print(f"   📝 {ejemplo['descripcion']}")
                
                ejemplo_num = input(f"\nElige un ejemplo (1-{len(ejemplos)}): ").strip()
                
                try:
                    idx = int(ejemplo_num) - 1
                    if 0 <= idx < len(ejemplos):
                        ejemplo = ejemplos[idx]
                        
                        print(f"\n🧪 PROBANDO: {ejemplo['categoria']}")
                        print(f"📝 Prompt: {ejemplo['prompt'][:100]}{'...' if len(ejemplo['prompt']) > 100 else ''}")
                        print(f"💡 Expectativa: {ejemplo['descripcion']}")
                        
                        start_time = time.time()
                        respuesta = agente.interactuar(player_id, ejemplo['prompt'])
                        end_time = time.time()
                        
                        print(f"\n💬 RESPUESTA:")
                        print("-" * 40)
                        respuesta_limpia = respuesta.split('\n\n🤖')[0] if '\n\n🤖' in respuesta else respuesta
                        print(respuesta_limpia[:300] + "..." if len(respuesta_limpia) > 300 else respuesta_limpia)
                        
                        print_context_info(respuesta)
                        print(f"\n⏱️ Tiempo de respuesta: {end_time - start_time:.2f} segundos")
                    else:
                        print("❌ Número de ejemplo inválido")
                except ValueError:
                    print("❌ Por favor ingresa un número válido")
            
            elif opcion == "3":
                # Estadísticas
                print("\n📊 ESTADÍSTICAS DEL SISTEMA")
                print("-" * 40)
                stats = agente._get_comprehensive_stats()
                print(stats)
            
            elif opcion == "4":
                # Cambiar modelo
                print("\n🔧 CONFIGURACIÓN DE MODELO")
                print("-" * 40)
                available = agente.model_router.get_available_providers()
                print(f"Proveedores disponibles: {', '.join(available)}")
                
                modelo = input("Forzar modelo (ollama/claude/gpt4/gemini) o 'auto' para automático: ").strip().lower()
                
                if modelo == "auto":
                    # Reinicializar para volver al modo automático
                    agente.model_router = agente.model_router.__class__()
                    print("✅ Modo automático activado")
                elif modelo in ["ollama", "claude", "gpt4", "gemini"]:
                    respuesta = agente._handle_model_command(f"usar modelo {modelo}")
                    print(respuesta)
                else:
                    print("❌ Modelo no válido")
            
            elif opcion == "5":
                print("\n👋 ¡Gracias por probar el sistema de enrutamiento inteligente!")
                print("💡 Para usar Samara en producción: python samara_chat.py dev")
                break
            
            else:
                print("❌ Opción no válida. Por favor elige 1-5.")
            
            input("\n⏸️ Presiona Enter para continuar...")
    
    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error en el demo: {e}")
        print("💡 Verifica que Ollama esté corriendo o que tengas API keys configuradas")

def mostrar_info_inicial():
    """Muestra información inicial del sistema"""
    print("🚀 SAMARA - META-AGENTE ORQUESTADOR")
    print("Sistema de Enrutamiento Inteligente Basado en Contexto")
    print()
    print("🎯 CARACTERÍSTICAS:")
    print("   • Análisis automático del tamaño de contexto")
    print("   • Selección inteligente del modelo óptimo")
    print("   • Optimización de costos (local vs cloud)")
    print("   • Fallback automático entre proveedores")
    print("   • Estadísticas detalladas de uso")
    print()
    print("📊 ESTRATEGIA DE ENRUTAMIENTO:")
    print("   • Contexto pequeño (<2K tokens) → Ollama (local, gratis)")
    print("   • Contexto mediano (2K-10K) → Según tarea y disponibilidad")
    print("   • Contexto grande (10K-30K) → Modelos cloud especializados")
    print("   • Contexto muy grande (>30K) → Claude/GPT-4 (máxima capacidad)")

if __name__ == "__main__":
    mostrar_info_inicial()
    demo_interactivo() 