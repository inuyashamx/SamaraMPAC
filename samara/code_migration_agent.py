import os
import json
import requests
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import re

class CodeMigrationAgent:
    """
    Agente especializado en migración de código entre tecnologías.
    Transforma archivos individuales y mantiene la funcionalidad.
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        
        # Plantillas de migración por tecnología
        self.migration_templates = {
            "polymer_to_react": {
                "file_mapping": {
                    ".html": ".jsx",
                    ".js": ".js"
                },
                "patterns": {
                    "component_definition": {
                        "from": r"Polymer\(\{[\s\S]*?\}\);",
                        "to": "class {component_name} extends React.Component {{\n  {content}\n}}"
                    },
                    "properties": {
                        "from": r"properties:\s*\{[\s\S]*?\}",
                        "to": "// Props: {properties}"
                    },
                    "lifecycle": {
                        "ready": "componentDidMount",
                        "attached": "componentDidMount",
                        "detached": "componentWillUnmount"
                    }
                }
            },
            "polymer_to_vue": {
                "file_mapping": {
                    ".html": ".vue",
                    ".js": ".vue"
                }
            },
            "angular_to_react": {
                "file_mapping": {
                    ".ts": ".tsx",
                    ".html": ".tsx"
                }
            }
        }

    def migrate_file(self, file_path: str, source_tech: str, target_tech: str, context: Dict = None) -> Dict:
        """
        Migra un archivo individual de una tecnología a otra
        """
        migration_key = f"{source_tech}_to_{target_tech}"
        
        if migration_key not in self.migration_templates:
            return self._migrate_with_ai(file_path, source_tech, target_tech, context)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            # Determinar el nuevo nombre de archivo
            original_path = Path(file_path)
            template = self.migration_templates[migration_key]
            
            new_extension = template["file_mapping"].get(original_path.suffix, original_path.suffix)
            new_file_path = str(original_path.with_suffix(new_extension))
            
            # Migrar contenido
            migrated_content = self._apply_migration_patterns(
                original_content, 
                template, 
                original_path.stem,
                context
            )
            
            return {
                "success": True,
                "original_file": file_path,
                "new_file": new_file_path,
                "original_content": original_content,
                "migrated_content": migrated_content,
                "migration_type": migration_key,
                "changes_summary": self._generate_changes_summary(original_content, migrated_content)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "original_file": file_path
            }

    def _migrate_with_ai(self, file_path: str, source_tech: str, target_tech: str, context: Dict = None) -> Dict:
        """
        Usa IA para migrar cuando no hay plantillas predefinidas
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()
            
            # Construir prompt para migración
            prompt = self._build_migration_prompt(
                original_content, 
                file_path, 
                source_tech, 
                target_tech, 
                context
            )
            
            # Obtener código migrado de Ollama
            migrated_content = self._consultar_ollama(prompt)
            
            # Limpiar la respuesta (remover explicaciones, solo código)
            migrated_content = self._extract_code_from_response(migrated_content)
            
            # Determinar nuevo nombre de archivo
            new_file_path = self._determine_new_file_path(file_path, source_tech, target_tech)
            
            return {
                "success": True,
                "original_file": file_path,
                "new_file": new_file_path,
                "original_content": original_content,
                "migrated_content": migrated_content,
                "migration_type": f"{source_tech}_to_{target_tech}_ai",
                "changes_summary": self._generate_changes_summary(original_content, migrated_content)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "original_file": file_path
            }

    def _build_migration_prompt(self, content: str, file_path: str, source_tech: str, target_tech: str, context: Dict = None) -> str:
        """
        Construye el prompt para migración con IA
        """
        file_name = Path(file_path).name
        context_info = ""
        
        if context:
            context_info = f"""
CONTEXTO DEL PROYECTO:
- Arquitectura: {context.get('architecture_patterns', [])}
- Dependencias: {context.get('dependencies', {})}
- Patrones detectados: {context.get('patterns', [])}
"""
        
        prompt = f"""
Eres un experto en migración de código. Migra este archivo de {source_tech} a {target_tech}.

ARCHIVO: {file_name}
TECNOLOGÍA ORIGEN: {source_tech}
TECNOLOGÍA DESTINO: {target_tech}

{context_info}

CÓDIGO ORIGINAL:
```
{content}
```

INSTRUCCIONES:
1. Mantén la funcionalidad exacta del código original
2. Usa las mejores prácticas de {target_tech}
3. Convierte patrones específicos de {source_tech} a equivalentes en {target_tech}
4. Mantén la estructura y lógica de negocio
5. Agrega comentarios donde sea necesario para explicar cambios importantes
6. Asegúrate de que el código sea funcional y siga convenciones modernas

RESPONDE SOLO CON EL CÓDIGO MIGRADO, SIN EXPLICACIONES ADICIONALES:
"""
        
        return prompt

    def _apply_migration_patterns(self, content: str, template: Dict, component_name: str, context: Dict = None) -> str:
        """
        Aplica patrones de migración predefinidos
        """
        migrated = content
        
        if "patterns" in template:
            patterns = template["patterns"]
            
            # Aplicar transformaciones de patrones
            for pattern_name, pattern_config in patterns.items():
                if isinstance(pattern_config, dict) and "from" in pattern_config and "to" in pattern_config:
                    from_pattern = pattern_config["from"]
                    to_pattern = pattern_config["to"]
                    
                    # Reemplazar placeholders
                    to_pattern = to_pattern.replace("{component_name}", component_name)
                    
                    migrated = re.sub(from_pattern, to_pattern, migrated, flags=re.MULTILINE | re.DOTALL)
        
        return migrated

    def _extract_code_from_response(self, response: str) -> str:
        """
        Extrae solo el código de la respuesta de Ollama
        """
        # Buscar bloques de código
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', response, re.DOTALL)
        
        if code_blocks:
            return code_blocks[0].strip()
        
        # Si no hay bloques de código, intentar limpiar la respuesta
        lines = response.split('\n')
        code_lines = []
        
        for line in lines:
            # Filtrar líneas que parecen explicaciones
            if not line.strip().startswith(('Aquí', 'Este', 'El código', 'La migración', 'He migrado')):
                code_lines.append(line)
        
        return '\n'.join(code_lines).strip()

    def _determine_new_file_path(self, original_path: str, source_tech: str, target_tech: str) -> str:
        """
        Determina el nuevo nombre de archivo basado en las tecnologías
        """
        path = Path(original_path)
        
        # Mapeos comunes de extensiones
        extension_mappings = {
            ("polymer", "react"): {".html": ".jsx", ".js": ".js"},
            ("polymer", "vue"): {".html": ".vue", ".js": ".vue"},
            ("angular", "react"): {".ts": ".tsx", ".html": ".tsx"},
            ("vue", "react"): {".vue": ".jsx"}
        }
        
        mapping_key = (source_tech, target_tech)
        if mapping_key in extension_mappings:
            new_ext = extension_mappings[mapping_key].get(path.suffix, path.suffix)
            return str(path.with_suffix(new_ext))
        
        return original_path

    def _generate_changes_summary(self, original: str, migrated: str) -> Dict:
        """
        Genera un resumen de los cambios realizados
        """
        return {
            "original_lines": len(original.splitlines()),
            "migrated_lines": len(migrated.splitlines()),
            "size_change": len(migrated) - len(original),
            "major_changes": self._detect_major_changes(original, migrated)
        }

    def _detect_major_changes(self, original: str, migrated: str) -> List[str]:
        """
        Detecta cambios importantes en la migración
        """
        changes = []
        
        # Detectar cambios en imports
        original_imports = re.findall(r'import.*|require.*', original)
        migrated_imports = re.findall(r'import.*|require.*', migrated)
        
        if len(original_imports) != len(migrated_imports):
            changes.append("Imports modificados")
        
        # Detectar cambios en estructura de componentes
        if 'class ' in migrated and 'class ' not in original:
            changes.append("Convertido a clase")
        
        if 'function ' in migrated and 'function ' not in original:
            changes.append("Convertido a función")
        
        # Detectar cambios en lifecycle methods
        lifecycle_patterns = ['componentDidMount', 'componentWillUnmount', 'useEffect', 'mounted', 'destroyed']
        for pattern in lifecycle_patterns:
            if pattern in migrated and pattern not in original:
                changes.append(f"Agregado {pattern}")
        
        return changes

    def migrate_batch(self, file_paths: List[str], source_tech: str, target_tech: str, context: Dict = None) -> Dict:
        """
        Migra múltiples archivos en lote
        """
        results = {
            "successful_migrations": [],
            "failed_migrations": [],
            "summary": {
                "total_files": len(file_paths),
                "successful": 0,
                "failed": 0
            }
        }
        
        for file_path in file_paths:
            print(f"🔄 Migrando: {file_path}")
            
            migration_result = self.migrate_file(file_path, source_tech, target_tech, context)
            
            if migration_result["success"]:
                results["successful_migrations"].append(migration_result)
                results["summary"]["successful"] += 1
            else:
                results["failed_migrations"].append(migration_result)
                results["summary"]["failed"] += 1
        
        return results

    def save_migrated_files(self, migration_results: List[Dict], output_dir: str) -> Dict:
        """
        Guarda los archivos migrados en el directorio de salida
        """
        saved_files = []
        errors = []
        
        os.makedirs(output_dir, exist_ok=True)
        
        for result in migration_results:
            if not result["success"]:
                continue
            
            try:
                # Determinar ruta de salida
                original_path = Path(result["original_file"])
                new_filename = Path(result["new_file"]).name
                output_path = os.path.join(output_dir, new_filename)
                
                # Guardar archivo migrado
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result["migrated_content"])
                
                saved_files.append({
                    "original": result["original_file"],
                    "migrated": output_path,
                    "changes": result["changes_summary"]
                })
                
            except Exception as e:
                errors.append({
                    "file": result["original_file"],
                    "error": str(e)
                })
        
        return {
            "saved_files": saved_files,
            "errors": errors,
            "total_saved": len(saved_files)
        }

    def _consultar_ollama(self, prompt: str) -> str:
        payload = {
            "model": "llama3:instruct",
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(f"{self.ollama_url}/api/generate", json=payload)
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            else:
                return f"[Error {response.status_code} al consultar Ollama]"
        except Exception as e:
            return f"[Error al conectar con Ollama: {e}]" 