#!/usr/bin/env python3
"""
Test básico para el nuevo sistema de metadata universal
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Agregar samara al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from code_analysis_agent import CodeAnalysisAgent

def crear_proyecto_test():
    """
    Crea un proyecto de prueba con archivos variados
    """
    temp_dir = tempfile.mkdtemp(prefix="test_proyecto_")
    
    # Crear estructura de carpetas
    os.makedirs(os.path.join(temp_dir, "src", "components"))
    os.makedirs(os.path.join(temp_dir, "src", "services"))
    os.makedirs(os.path.join(temp_dir, "src", "styles"))
    
    # Archivo HTML Polymer
    html_content = """
<dom-module id="mi-componente">
  <template>
    <style>
      :host {
        display: block;
        padding: 16px;
      }
      .title {
        color: var(--primary-color);
        font-size: 24px;
      }
    </style>
    <div class="container">
      <h2 class="title">[[titulo]]</h2>
      <paper-button on-tap="handleClick">Hacer clic</paper-button>
      <iron-ajax
        auto
        url="/api/usuarios"
        handle-as="json"
        last-response="{{usuarios}}">
      </iron-ajax>
    </div>
  </template>
  <script>
    Polymer({
      is: 'mi-componente',
      properties: {
        titulo: String,
        usuarios: Array
      },
      handleClick: function() {
        this.fire('componente-clicked', {id: this.id});
        this.validateInput();
      },
      validateInput: function() {
        if (!this.titulo) {
          console.error('Título es requerido');
        }
      }
    });
  </script>
</dom-module>
"""
    
    # Archivo JavaScript de servicio
    js_content = """
import { ApiClient } from './api-client.js';

export class UserService {
  constructor() {
    this.apiClient = new ApiClient();
    this.cache = new Map();
  }
  
  async getUsers() {
    if (this.cache.has('users')) {
      return this.cache.get('users');
    }
    
    try {
      const response = await fetch('/api/usuarios');
      const users = await response.json();
      this.cache.set('users', users);
      return users;
    } catch (error) {
      console.error('Error loading users:', error);
      throw new Error('Failed to load users');
    }
  }
  
  async createUser(userData) {
    const response = await this.apiClient.post('/api/usuarios', userData);
    if (response.ok) {
      this.cache.delete('users'); // Invalidar cache
      return response.json();
    }
    throw new Error('Failed to create user');
  }
  
  validateUserData(data) {
    if (!data.email || !data.name) {
      throw new Error('Email y nombre son requeridos');
    }
    if (!this.isValidEmail(data.email)) {
      throw new Error('Email no válido');
    }
  }
  
  isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }
}

// Patrón Singleton
export const userService = new UserService();
"""

    # Archivo CSS
    css_content = """
:root {
  --primary-color: #1976d2;
  --secondary-color: #dc004e;
  --background-color: #fafafa;
  --text-color: #333;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 16px;
  background-color: var(--background-color);
}

.card {
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  padding: 24px;
  margin-bottom: 16px;
}

.button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.button:hover {
  background-color: #1565c0;
}

.form-field {
  margin-bottom: 16px;
}

.form-field label {
  display: block;
  margin-bottom: 4px;
  font-weight: 500;
  color: var(--text-color);
}

.form-field input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.error {
  color: var(--secondary-color);
  font-size: 12px;
  margin-top: 4px;
}

@media (max-width: 768px) {
  .container {
    padding: 8px;
  }
  
  .card {
    padding: 16px;
  }
}
"""

    # Archivo de configuración JSON
    config_content = """
{
  "name": "mi-app-polymer",
  "version": "1.0.0",
  "description": "Aplicación de prueba Polymer",
  "main": "index.html",
  "dependencies": {
    "polymer": "^1.11.3",
    "iron-ajax": "^1.4.3",
    "paper-button": "^1.0.14",
    "paper-input": "^1.1.24"
  },
  "devDependencies": {
    "web-component-tester": "^6.0.0",
    "polyserve": "^0.17.19"
  },
  "scripts": {
    "start": "polyserve",
    "test": "wct"
  },
  "keywords": ["polymer", "web-components", "frontend"],
  "author": "Test Developer",
  "license": "MIT"
}
"""

    # Escribir archivos
    with open(os.path.join(temp_dir, "src", "components", "mi-componente.html"), "w", encoding='utf-8') as f:
        f.write(html_content)
    
    with open(os.path.join(temp_dir, "src", "services", "user-service.js"), "w", encoding='utf-8') as f:
        f.write(js_content)
    
    with open(os.path.join(temp_dir, "src", "styles", "main.css"), "w", encoding='utf-8') as f:
        f.write(css_content)
    
    with open(os.path.join(temp_dir, "package.json"), "w", encoding='utf-8') as f:
        f.write(config_content)
    
    # Archivo README
    with open(os.path.join(temp_dir, "README.md"), "w", encoding='utf-8') as f:
        f.write("# Mi App Polymer\n\nAplicación de prueba para testing del sistema de metadata.")
    
    return temp_dir

def test_sistema_metadata():
    """
    Test principal del sistema de metadata
    """
    print("🧪 INICIANDO TESTS DEL SISTEMA DE METADATA")
    print("=" * 60)
    
    # Crear proyecto de prueba
    print("📁 Creando proyecto de prueba...")
    proyecto_path = crear_proyecto_test()
    print(f"   Proyecto creado en: {proyecto_path}")
    
    try:
        # Inicializar agente
        print("\n🔧 Inicializando CodeAnalysisAgent...")
        agent = CodeAnalysisAgent(
            ollama_url="http://localhost:11434",
            weaviate_url="http://localhost:8080",
            max_workers=2  # Menos workers para testing
        )
        print("   ✅ Agente inicializado")
        
        # Test 1: Crear esquema
        print("\n📋 TEST 1: Creando esquema de metadata...")
        esquema_ok = agent.create_weaviate_schema("test_proyecto")
        if esquema_ok:
            print("   ✅ Esquema creado exitosamente")
        else:
            print("   ❌ Error creando esquema")
            return False
        
        # Test 2: Analizar proyecto
        print("\n🔍 TEST 2: Analizando estructura del proyecto...")
        estructura = agent.analyze_project_structure(proyecto_path)
        print(f"   📊 Archivos encontrados: {estructura['total_files']}")
        print(f"   🔧 Tecnologías detectadas: {estructura['technologies_detected']}")
        print(f"   🏗️ Patrones arquitectónicos: {estructura['architecture_patterns']}")
        
        # Test 3: Indexar proyecto
        print("\n💾 TEST 3: Indexando proyecto completo...")
        resultado = agent.analyze_and_index_project(proyecto_path, "test_proyecto")
        
        if resultado.get('indexed_files', 0) > 0:
            print(f"   ✅ Archivos indexados: {resultado['indexed_files']}")
            print(f"   📝 Total archivos: {resultado['total_files']}")
        else:
            print("   ❌ No se indexaron archivos")
            return False
        
        # Test 4: Consultas de metadata
        print("\n🔎 TEST 4: Probando consultas de metadata...")
        
        # Consulta 1: Componentes
        print("   🔍 Buscando componentes...")
        consulta1 = agent.query_project("test_proyecto", "componentes polymer", limit=5)
        print(f"      Archivos encontrados: {consulta1.get('files_found', 0)}")
        
        # Consulta 2: Servicios
        print("   🔍 Buscando servicios...")
        consulta2 = agent.query_project("test_proyecto", "servicios usuarios api", limit=5)
        print(f"      Archivos encontrados: {consulta2.get('files_found', 0)}")
        
        # Consulta 3: Estilos
        print("   🔍 Buscando estilos...")
        consulta3 = agent.query_project("test_proyecto", "css estilos variables", limit=5)
        print(f"      Archivos encontrados: {consulta3.get('files_found', 0)}")
        
        # Test 5: Listar módulos
        print("\n📋 TEST 5: Listando módulos del proyecto...")
        modulos = agent.list_project_modules("test_proyecto")
        if modulos.get('total_modules', 0) > 0:
            print(f"   ✅ Total módulos: {modulos['total_modules']}")
            print("   📊 Por tipo:", modulos.get('modules_by_type', {}).keys())
            print("   🏢 Por dominio:", modulos.get('modules_by_domain', {}).keys())
        else:
            print("   ❌ No se encontraron módulos")
        
        print("\n🎉 TODOS LOS TESTS COMPLETADOS EXITOSAMENTE!")
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR EN TEST: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Limpiar
        print(f"\n🧹 Limpiando proyecto temporal: {proyecto_path}")
        try:
            shutil.rmtree(proyecto_path)
            # También limpiar datos de Weaviate
            agent.delete_project_data("test_proyecto")
            print("   ✅ Limpieza completada")
        except Exception as e:
            print(f"   ⚠️ Error en limpieza: {e}")

if __name__ == "__main__":
    print("🧪 SISTEMA DE TESTING - METADATA UNIVERSAL")
    print("=" * 60)
    
    # Verificar servicios
    print("🔍 Verificando servicios requeridos...")
    
    # TODO: Aquí se pueden agregar checks de Weaviate y Ollama
    print("   ℹ️ Asumiendo que Weaviate está en localhost:8080")
    print("   ℹ️ Asumiendo que Ollama está en localhost:11434")
    
    # Ejecutar tests
    exito = test_sistema_metadata()
    
    if exito:
        print("\n✅ TODOS LOS TESTS PASARON!")
        sys.exit(0)
    else:
        print("\n❌ ALGUNOS TESTS FALLARON!")
        sys.exit(1) 