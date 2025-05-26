import os
import json
import requests
from typing import List, Dict
from project_migration_agent import ProjectMigrationAgent
from code_analysis_agent import CodeAnalysisAgent

class SamaraDevAgent:
    """
    Versión especializada de Samara para desarrollo con capacidades avanzadas:
    - Migración masiva de proyectos (300k+ líneas)
    - Análisis profundo de código
    - Refactoring inteligente
    - Arquitectura y patrones
    """
    
    def __init__(self, ollama_url="http://localhost:11434"):
        
        self.ollama_url = ollama_url
        
        # Agentes especializados para desarrollo
        self.project_migration_agent = ProjectMigrationAgent(ollama_url)
        self.code_analysis_agent = CodeAnalysisAgent(ollama_url)
        
        # Comandos especiales que Samara puede reconocer
        self.dev_commands = {
            "migrar proyecto": self._handle_project_migration,
            "analizar proyecto": self._handle_project_analysis,
            "migrar archivo": self._handle_file_migration,
            "analizar archivo": self._handle_file_analysis,
            "generar reporte": self._handle_generate_report,
            "ayuda migración": self._handle_migration_help
        }

    def handle_dev_command(self, input_text: str) -> str:
        """
        Maneja comandos especiales de desarrollo
        """
        # Detectar si es un comando especial de desarrollo
        command_detected = self._detect_dev_command(input_text)
        
        if command_detected:
            return self._execute_dev_command("dev_user", input_text, command_detected)
        else:
            return None  # No es un comando especial

    def handle_migration_command(self, input_text: str) -> str:
        """
        Maneja específicamente comandos de migración
        """
        return self._handle_project_migration("dev_user", input_text)

    def handle_analysis_command(self, input_text: str) -> str:
        """
        Maneja específicamente comandos de análisis
        """
        return self._handle_project_analysis("dev_user", input_text)

    def _detect_dev_command(self, input_text: str) -> str:
        """
        Detecta si el input contiene un comando especial de desarrollo
        """
        input_lower = input_text.lower()
        
        for command, handler in self.dev_commands.items():
            if command in input_lower:
                return command
        
        # Detectar patrones de migración
        migration_patterns = [
            "migra este proyecto", "migrar de", "convertir a", "cambiar de",
            "polymer a react", "angular a vue", "vue a react"
        ]
        
        for pattern in migration_patterns:
            if pattern in input_lower:
                return "migrar proyecto"
        
        return None

    def _execute_dev_command(self, player_id: str, input_text: str, command: str) -> str:
        """
        Ejecuta un comando especial de desarrollo
        """
        try:
            handler = self.dev_commands[command]
            return handler(player_id, input_text)
        except Exception as e:
            return f"❌ Error ejecutando comando '{command}': {str(e)}"

    def _handle_project_migration(self, player_id: str, input_text: str) -> str:
        """
        Maneja comandos de migración de proyecto completo
        """
        # Extraer información del comando
        migration_info = self._parse_migration_command(input_text)
        
        if not migration_info["valid"]:
            return """
🤖 **Samara**: Para migrar un proyecto necesito más información. Usa este formato:

**Ejemplos:**
- "Migra el proyecto en /ruta/proyecto de polymer a react"
- "Migrar proyecto C:\\MiApp de angular a vue"
- "Convertir /home/user/app de polymer 1.0 a react con estrategia incremental"

**Parámetros:**
- **Ruta del proyecto**: Ruta completa al directorio
- **Tecnología origen**: polymer, angular, vue, etc.
- **Tecnología destino**: react, vue, angular, etc.
- **Estrategia** (opcional): incremental o completa

¿Podrías proporcionarme estos datos?
"""
        
        # Validar que el proyecto existe
        if not os.path.exists(migration_info["project_path"]):
            return f"❌ **Error**: No encontré el proyecto en la ruta: `{migration_info['project_path']}`\n\n¿Podrías verificar la ruta?"
        
        # Ejecutar migración
        try:
            print(f"\n🚀 Samara iniciando migración masiva...")
            
            result = self.project_migration_agent.migrate_project(
                project_path=migration_info["project_path"],
                source_tech=migration_info["source_tech"],
                target_tech=migration_info["target_tech"],
                strategy=migration_info["strategy"]
            )
            
            # Formatear respuesta
            summary = result["migration_summary"]
            
            response = f"""
✅ **Migración completada!**

📊 **Resumen:**
- **Proyecto**: {migration_info['source_tech']} → {migration_info['target_tech']}
- **Estrategia**: {summary['strategy']}
- **Tasa de éxito**: {summary['success_rate']}%
- **Archivos migrados**: {summary['files_migrated']}
- **Archivos fallidos**: {summary['files_failed']}
- **Tiempo**: {summary['execution_time_minutes']} minutos

📁 **Proyecto migrado**: `{result['execution_results']['phases_completed'][0]['saved_files'][0]['migrated'] if result['execution_results']['phases_completed'] else 'Ver reporte'}`

🔍 **Próximos pasos:**
{chr(10).join(f"- {step}" for step in result['next_steps'][:3])}

¿Quieres que revise algún archivo específico o necesitas ayuda con la configuración?
"""
            
            # Guardar contexto de la migración para futuras consultas
            self._save_migration_context(player_id, result)
            
            return response
            
        except Exception as e:
            return f"❌ **Error durante la migración**: {str(e)}\n\n¿Quieres que analice el proyecto primero para identificar posibles problemas?"

    def _handle_project_analysis(self, player_id: str, input_text: str) -> str:
        """
        Maneja comandos de análisis de proyecto
        """
        # Extraer ruta del proyecto
        project_path = self._extract_project_path(input_text)
        
        if not project_path or not os.path.exists(project_path):
            return """
🤖 **Samara**: Para analizar un proyecto necesito la ruta. Ejemplos:

- "Analiza el proyecto en /ruta/mi-proyecto"
- "Analizar proyecto C:\\MiApp"

¿Cuál es la ruta de tu proyecto?
"""
        
        try:
            analysis = self.code_analysis_agent.analyze_project_structure(project_path)
            
            response = f"""
📊 **Análisis del proyecto completado**

🏗️ **Estructura:**
- **Total archivos**: {analysis['total_files']:,}
- **Total líneas**: {analysis['total_lines']:,}
- **Tecnologías detectadas**: {', '.join(analysis['technologies_detected']) if analysis['technologies_detected'] else 'No detectadas'}
- **Patrones arquitectónicos**: {', '.join(analysis['architecture_patterns']) if analysis['architecture_patterns'] else 'No detectados'}

📁 **Tipos de archivo:**
{chr(10).join(f"- {ext}: {count} archivos" for ext, count in sorted(analysis['file_types'].items(), key=lambda x: x[1], reverse=True)[:5])}

🔧 **Archivos importantes:**
- **Entry points**: {len(analysis['entry_points'])}
- **Configuración**: {len(analysis['config_files'])}

💡 **Recomendaciones:**
- Proyecto {'grande' if analysis['total_files'] > 500 else 'mediano' if analysis['total_files'] > 100 else 'pequeño'} ({analysis['total_files']} archivos)
- Complejidad {'alta' if analysis['total_lines'] > 100000 else 'media' if analysis['total_lines'] > 10000 else 'baja'} ({analysis['total_lines']:,} líneas)

¿Quieres que genere un plan de migración o analice algún aspecto específico?
"""
            
            return response
            
        except Exception as e:
            return f"❌ **Error analizando proyecto**: {str(e)}"

    def _handle_migration_help(self, player_id: str, input_text: str) -> str:
        """
        Proporciona ayuda sobre migración de proyectos
        """
        return """
🧠 **Samara - Guía de Migración de Proyectos**

## 🚀 **Comandos disponibles:**

### **Migración completa:**
```
Migra el proyecto en /ruta/proyecto de polymer a react
```

### **Análisis previo:**
```
Analiza el proyecto en /ruta/proyecto
```

### **Migración de archivo:**
```
Migra el archivo /ruta/archivo.js de polymer a react
```

## 🎯 **Tecnologías soportadas:**
- **Origen**: Polymer 1.0/2.0/3.0, Angular, Vue 2/3
- **Destino**: React, Vue 3, Angular, Svelte

## ⚙️ **Estrategias:**
- **Incremental**: Migra por fases (recomendado para proyectos grandes)
- **Completa**: Migra todo de una vez (para proyectos pequeños)

## 📊 **Capacidades:**
- ✅ Proyectos hasta 300k+ líneas
- ✅ Análisis de dependencias
- ✅ Detección de patrones
- ✅ Migración inteligente con IA
- ✅ Reportes detallados

¿En qué proyecto estás trabajando? ¡Puedo ayudarte a migrarlo!
"""

    def _parse_migration_command(self, input_text: str) -> Dict:
        """
        Extrae información de un comando de migración
        """
        import re
        
        result = {
            "valid": False,
            "project_path": None,
            "source_tech": None,
            "target_tech": None,
            "strategy": "incremental"
        }
        
        # Extraer ruta del proyecto
        path_patterns = [
            r'proyecto en ([^\s]+)',
            r'proyecto ([C-Z]:[^\s]+)',
            r'proyecto (/[^\s]+)',
            r'en ([C-Z]:[^\s]+)',
            r'en (/[^\s]+)'
        ]
        
        for pattern in path_patterns:
            match = re.search(pattern, input_text, re.IGNORECASE)
            if match:
                result["project_path"] = match.group(1).strip('"\'')
                break
        
        # Extraer tecnologías
        tech_patterns = [
            r'de (\w+) a (\w+)',
            r'from (\w+) to (\w+)',
            r'(\w+) a (\w+)'
        ]
        
        for pattern in tech_patterns:
            match = re.search(pattern, input_text, re.IGNORECASE)
            if match:
                result["source_tech"] = match.group(1).lower()
                result["target_tech"] = match.group(2).lower()
                break
        
        # Extraer estrategia
        if "completa" in input_text.lower() or "complete" in input_text.lower():
            result["strategy"] = "complete"
        
        # Validar
        if result["project_path"] and result["source_tech"] and result["target_tech"]:
            result["valid"] = True
        
        return result

    def _extract_project_path(self, input_text: str) -> str:
        """
        Extrae la ruta del proyecto del texto
        """
        import re
        
        path_patterns = [
            r'proyecto en ([^\s]+)',
            r'proyecto ([C-Z]:[^\s]+)',
            r'proyecto (/[^\s]+)',
            r'en ([C-Z]:[^\s]+)',
            r'en (/[^\s]+)'
        ]
        
        for pattern in path_patterns:
            match = re.search(pattern, input_text, re.IGNORECASE)
            if match:
                return match.group(1).strip('"\'')
        
        return None

    def _save_migration_context(self, player_id: str, migration_result: Dict):
        """
        Guarda el contexto de migración para futuras consultas
        """
        # Guardar como recuerdo especial
        context_summary = f"""
Migración completada: {migration_result['migration_summary']['source_technology']} → {migration_result['migration_summary']['target_technology']}
- Archivos migrados: {migration_result['migration_summary']['files_migrated']}
- Tasa de éxito: {migration_result['migration_summary']['success_rate']}%
- Tiempo: {migration_result['migration_summary']['execution_time_minutes']} minutos
"""
        
        self.memory_agent.save_smart_memory(
            memory_manager=self.memory_manager,
            user_id=player_id,
            mode=self.mode,
            user_input="Migración de proyecto completada",
            agent_response=context_summary
        )

    def _handle_file_migration(self, player_id: str, input_text: str) -> str:
        """
        Maneja migración de archivos individuales
        """
        return "🚧 **Función en desarrollo**: Migración de archivos individuales estará disponible pronto."

    def _handle_file_analysis(self, player_id: str, input_text: str) -> str:
        """
        Maneja análisis de archivos individuales
        """
        return "🚧 **Función en desarrollo**: Análisis de archivos individuales estará disponible pronto."

    def _handle_generate_report(self, player_id: str, input_text: str) -> str:
        """
        Genera reportes de migración
        """
        return "🚧 **Función en desarrollo**: Generación de reportes personalizados estará disponible pronto." 