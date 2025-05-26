#!/usr/bin/env python3
"""
Prueba rápida del sistema de enrutamiento basado en contexto
"""

from samara.model_router_agent import ModelRouterAgent, TaskType

def test_context_routing():
    """Prueba el enrutamiento basado en contexto"""
    print("🧠 PRUEBA: Sistema de Enrutamiento Basado en Contexto")
    print("="*60)
    
    try:
        router = ModelRouterAgent()
        available = router.get_available_providers()
        
        if not available:
            print("❌ No hay proveedores disponibles")
            return
        
        print(f"✅ Proveedores disponibles: {', '.join(available)}")
        print()
        
        # Casos de prueba
        test_cases = [
            {
                "name": "Consulta muy pequeña",
                "prompt": "Hola",
                "expected_context": "muy_pequeño"
            },
            {
                "name": "Consulta pequeña",
                "prompt": "¿Cómo hacer un loop en Python?" * 10,
                "expected_context": "pequeño"
            },
            {
                "name": "Análisis mediano",
                "prompt": "Analiza este código:\n\n" + "def function():\n    pass\n" * 100,
                "expected_context": "mediano"
            },
            {
                "name": "Migración grande",
                "prompt": "Migra este proyecto completo:\n\n" + "// Código muy largo\n" * 1000,
                "expected_context": "grande"
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            print(f"🧪 PRUEBA {i}: {test['name']}")
            print(f"📏 Tamaño: {len(test['prompt']):,} caracteres")
            
            # Estimar contexto
            context_size = router._estimate_context_size(test['prompt'])
            context_category = router._categorize_context_size(context_size)
            
            # Detectar tarea
            task_type = router._detect_task_type(test['prompt'], "dev")
            
            # Seleccionar proveedor
            selected_provider = router._select_best_provider(task_type, test['prompt'], context_size)
            
            print(f"   • Contexto estimado: {context_size:,} tokens ({context_category})")
            print(f"   • Tarea detectada: {task_type.value}")
            print(f"   • Proveedor seleccionado: {selected_provider.value}")
            
            # Verificar si coincide con lo esperado
            if context_category == test['expected_context']:
                print(f"   ✅ Categorización correcta")
            else:
                print(f"   ⚠️  Esperado: {test['expected_context']}, obtenido: {context_category}")
            
            print()
        
        # Mostrar capacidades de modelos
        print("📊 CAPACIDADES DE MODELOS:")
        print("-" * 40)
        for provider_enum in router.model_config:
            if router._is_provider_available(provider_enum):
                config = router.model_config[provider_enum]
                print(f"{provider_enum.value:<12} | {config['context_limit']:>8,} tokens | {config['optimal_context']:>8,} óptimo")
        
        print("\n🎯 ESTRATEGIA DE ENRUTAMIENTO:")
        print("   • Contexto muy pequeño → Ollama (local)")
        print("   • Contexto pequeño → Ollama o Gemini")
        print("   • Contexto mediano → Según tarea")
        print("   • Contexto grande → Modelos cloud")
        print("   • Contexto muy grande → Claude/GPT-4")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_real_query():
    """Prueba con una consulta real"""
    print("\n" + "="*60)
    print("🚀 PRUEBA REAL: Consulta con Contexto")
    print("="*60)
    
    try:
        router = ModelRouterAgent()
        
        # Consulta de ejemplo
        prompt = """
Hola Samara, necesito ayuda con un proyecto de migración.

Tengo un proyecto en Polymer 1.0 con aproximadamente 50 archivos JavaScript,
15 componentes personalizados, y uso Bower para dependencias.

¿Podrías ayudarme a planificar la migración a React?
Específicamente necesito saber:
1. Qué archivos migrar primero
2. Cómo manejar los componentes personalizados
3. Estrategia para las dependencias

El proyecto está en C:\\MiProyecto\\polymer-app
"""
        
        print(f"📝 Consulta: {prompt[:100]}...")
        print(f"📏 Tamaño: {len(prompt):,} caracteres")
        
        # Procesar con el router
        result = router.route_and_query(
            prompt=prompt,
            mode="dev",
            max_tokens=1024,
            temperature=0.7
        )
        
        if result["success"]:
            print(f"\n✅ RESULTADO:")
            print(f"   • Proveedor usado: {result.get('provider', 'unknown')}")
            print(f"   • Modelo: {result.get('model', 'unknown')}")
            print(f"   • Contexto: {result.get('context_category', 'unknown')} ({result.get('context_size', 0):,} tokens)")
            print(f"   • Respuesta: {result.get('response', '')[:200]}...")
            
            if result.get('used_fallback'):
                print(f"   • Fallback desde: {result.get('original_provider')}")
        else:
            print(f"❌ Error: {result.get('error', 'Desconocido')}")
            
    except Exception as e:
        print(f"❌ Error en prueba real: {e}")

if __name__ == "__main__":
    test_context_routing()
    test_real_query()
    
    print("\n" + "="*60)
    print("🎉 PRUEBAS COMPLETADAS")
    print("💡 Para usar en vivo: python samara_chat.py dev")
    print("="*60) 