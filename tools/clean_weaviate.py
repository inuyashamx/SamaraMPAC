#!/usr/bin/env python3
"""
Herramienta para limpiar datos de Weaviate
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentes.indexador_fragmentos import CodeAnalysisAgent

def clean_weaviate_completely():
    """
    Borra TODAS las clases y datos de Weaviate
    """
    print("🧹 LIMPIEZA COMPLETA DE WEAVIATE")
    print("=" * 50)
    
    # Conectar a Weaviate
    try:
        client = weaviate.Client("http://localhost:8080")
        print("✅ Conectado a Weaviate")
    except Exception as e:
        print(f"❌ Error conectando a Weaviate: {e}")
        return False
    
    try:
        # Obtener esquema actual
        schema = client.schema.get()
        classes = schema.get('classes', [])
        
        if not classes:
            print("ℹ️  Weaviate ya está vacío - no hay clases para eliminar")
            return True
        
        print(f"🔍 Encontradas {len(classes)} clases:")
        for cls in classes:
            class_name = cls.get('class', 'Unknown')
            class_type = "Fragmentos" if class_name.startswith('CodeFragments_') else "Otro"
            print(f"   📦 {class_name} ({class_type})")
        
        # Confirmar eliminación
        print(f"\n⚠️  ¿Estás seguro de que quieres ELIMINAR TODAS las {len(classes)} clases?")
        print("   Esto borrará TODOS los datos indexados permanentemente.")
        
        confirm = input("   Escribe 'SI' para confirmar: ").strip()
        
        if confirm.upper() != 'SI':
            print("❌ Operación cancelada")
            return False
        
        # Eliminar cada clase
        print(f"\n🗑️  Eliminando clases...")
        deleted_count = 0
        
        for cls in classes:
            class_name = cls.get('class', 'Unknown')
            try:
                client.schema.delete_class(class_name)
                print(f"   ✅ Eliminada: {class_name}")
                deleted_count += 1
            except Exception as e:
                print(f"   ❌ Error eliminando {class_name}: {e}")
        
        print(f"\n🎉 Limpieza completada:")
        print(f"   ✅ {deleted_count} clases eliminadas")
        print(f"   ❌ {len(classes) - deleted_count} errores")
        
        # Verificar que está vacío
        final_schema = client.schema.get()
        final_classes = final_schema.get('classes', [])
        
        if not final_classes:
            print(f"\n✨ ¡Weaviate está completamente limpio!")
            print(f"   📊 Clases restantes: 0")
            print(f"   💾 Memoria liberada")
            print(f"\n🚀 Listo para re-indexar proyectos con fragmentos")
        else:
            print(f"\n⚠️  Aún quedan {len(final_classes)} clases:")
            for cls in final_classes:
                print(f"   - {cls.get('class', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error durante la limpieza: {e}")
        return False

def clean_specific_project(project_name):
    """
    Elimina solo un proyecto específico
    """
    print(f"🗑️  ELIMINANDO PROYECTO: {project_name}")
    print("=" * 50)
    
    try:
        agent = CodeAnalysisAgent()
        success = agent.delete_project_data(project_name)
        
        if success:
            print(f"✅ Proyecto '{project_name}' eliminado correctamente")
        else:
            print(f"❌ Error eliminando proyecto '{project_name}'")
        
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def show_weaviate_status():
    """
    Muestra el estado actual de Weaviate con información de fragmentos
    """
    print("📊 ESTADO ACTUAL DE WEAVIATE")
    print("=" * 40)
    
    try:
        client = weaviate.Client("http://localhost:8080")
        schema = client.schema.get()
        classes = schema.get('classes', [])
        
        if not classes:
            print("✨ Weaviate está vacío")
        else:
            print(f"📦 {len(classes)} clases encontradas:")
            
            fragment_classes = []
            other_classes = []
            
            for cls in classes:
                class_name = cls.get('class', 'Unknown')
                
                if class_name.startswith('CodeFragments_'):
                    fragment_classes.append(class_name)
                else:
                    other_classes.append(class_name)
            
            # Mostrar proyectos de fragmentos
            if fragment_classes:
                print(f"\n🔧 PROYECTOS CON FRAGMENTOS ({len(fragment_classes)}):")
                for class_name in fragment_classes:
                    project_name = class_name.replace('CodeFragments_', '')
                    
                    # Contar fragmentos
                    try:
                        result = (
                            client.query
                            .aggregate(class_name)
                            .with_meta_count()
                            .do()
                        )
                        
                        if 'data' in result and 'Aggregate' in result['data']:
                            agg_data = result['data']['Aggregate'].get(class_name, [])
                            if agg_data and 'meta' in agg_data[0]:
                                count = agg_data[0]['meta']['count']
                                print(f"   📄 {project_name}: {count} fragmentos")
                            else:
                                print(f"   📄 {project_name}: ? fragmentos")
                        else:
                            print(f"   📄 {project_name}: ? fragmentos")
                            
                    except Exception as e:
                        print(f"   📄 {project_name}: Error contando ({e})")
            
            # Mostrar otras clases
            if other_classes:
                print(f"\n📋 OTRAS CLASES ({len(other_classes)}):")
                for class_name in other_classes:
                    try:
                        result = (
                            client.query
                            .aggregate(class_name)
                            .with_meta_count()
                            .do()
                        )
                        
                        if 'data' in result and 'Aggregate' in result['data']:
                            agg_data = result['data']['Aggregate'].get(class_name, [])
                            if agg_data and 'meta' in agg_data[0]:
                                count = agg_data[0]['meta']['count']
                                print(f"   📄 {class_name}: {count} objetos")
                            else:
                                print(f"   📄 {class_name}: ? objetos")
                        else:
                            print(f"   📄 {class_name}: ? objetos")
                            
                    except Exception as e:
                        print(f"   📄 {class_name}: Error contando ({e})")
        
    except Exception as e:
        print(f"❌ Error obteniendo estado: {e}")

if __name__ == "__main__":
    print("🔧 HERRAMIENTA DE LIMPIEZA DE WEAVIATE")
    print("   Compatible con sistema de fragmentos")
    print("=" * 50)
    
    # Mostrar estado actual
    show_weaviate_status()
    
    print("\n" + "=" * 50)
    
    # Opciones
    print("\n¿Qué quieres hacer?")
    print("  1. Limpiar todo Weaviate")
    print("  2. Eliminar proyecto específico")
    print("  3. Solo ver estado")
    
    action = input("\nElige (1/2/3): ").strip()
    
    if action == "1":
        success = clean_weaviate_completely()
        if success:
            print("\n" + "=" * 50)
            show_weaviate_status()
    elif action == "2":
        project_name = input("\nNombre del proyecto a eliminar: ").strip()
        if project_name:
            success = clean_specific_project(project_name)
            if success:
                print("\n" + "=" * 50)
                show_weaviate_status()
        else:
            print("❌ Nombre de proyecto no válido")
    elif action == "3":
        print("\n✅ Solo mostrando estado - no se hicieron cambios")
    else:
        print("❌ Opción no válida") 