import os
import ast
import json
import requests
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import re
import hashlib
import weaviate
from datetime import datetime, timezone
import uuid
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class CodeAnalysisAgent:
    """
    Agente especializado en análisis granular de código para indexación de fragmentos en Weaviate.
    Divide archivos en fragmentos útiles: funciones, clases, componentes, pantallas, endpoints, etc.
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434", weaviate_url: str = "http://localhost:8080", 
                 max_workers: int = None, ollama_max_concurrent: int = 2, 
                 file_timeout: int = 60, ollama_timeout: int = 30):
        self.ollama_url = ollama_url
        self.weaviate_url = weaviate_url
        self._verbose_mode = False
        self._log_files = {
            "ignored": None,
            "not_indexed": None,
            "enabled": False
        }
        
        # Configuración de threading personalizable
        cpu_count = os.cpu_count() or 4  # Fallback a 4 si os.cpu_count() devuelve None
        self.max_workers = max_workers or min(16, cpu_count)
        self.file_timeout = file_timeout
        self.ollama_timeout = ollama_timeout
        
        # Threading y sincronización
        self._log_lock = threading.Lock()
        self._counter_lock = threading.Lock()
        self._ollama_semaphore = threading.Semaphore(ollama_max_concurrent or 2)
        self._indexed_fragments_count = 0
        
        # Conectar a Weaviate
        try:
            self.weaviate_client = weaviate.Client(weaviate_url)
            print(f"✅ Conectado a Weaviate en {weaviate_url}")
        except Exception as e:
            print(f"❌ Error conectando a Weaviate: {e}")
            self.weaviate_client = None
        
        # Configuración para fragmentación
        self.max_function_lines = 100  # Funciones > 100 líneas se fragmentan
        self.fragment_chunk_size = 50  # Tamaño de chunks para funciones largas
        self.fragment_overlap = 10     # Líneas de solapamiento entre chunks

    def _get_embedding(self, text: str) -> List[float]:
        """Obtiene embedding usando Ollama con rate limiting"""
        with self._ollama_semaphore:
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/embeddings",
                    json={
                        "model": "nomic-embed-text",
                        "prompt": text
                    },
                    timeout=self.ollama_timeout
                )
                if response.status_code == 200:
                    return response.json()["embedding"]
                else:
                    print(f"Error al obtener embedding: {response.status_code}")
                    return []
            except Exception as e:
                print(f"Error conectando con Ollama: {e}")
                return []

    def create_weaviate_schema(self, project_name: str):
        """
        Crea el esquema de fragmentos de código en Weaviate
        """
        if not self.weaviate_client:
            return False
            
        class_name = f"CodeFragments_{self._sanitize_project_name(project_name)}"
        
        # Verificar si la clase ya existe
        try:
            existing_schema = self.weaviate_client.schema.get()
            existing_classes = [cls['class'] for cls in existing_schema.get('classes', [])]
            
            if class_name in existing_classes:
                print(f"⚠️  La clase {class_name} ya existe. Eliminándola para crear una nueva...")
                self.weaviate_client.schema.delete_class(class_name)
        except Exception as e:
            print(f"Error verificando esquema existente: {e}")
        
        # Esquema de Fragmentos de Código
        schema = {
            "class": class_name,
            "description": f"Fragmentos de código del proyecto {project_name}",
            "vectorizer": "none",
            "properties": [
                # IDENTIFICACIÓN DEL FRAGMENTO
                {"name": "projectName", "dataType": ["text"], "description": "Nombre del proyecto"},
                {"name": "fileName", "dataType": ["text"], "description": "Nombre del archivo"},
                {"name": "filePath", "dataType": ["text"], "description": "Ruta completa del archivo"},
                {"name": "type", "dataType": ["text"], "description": "Tipo de fragmento: function, class, component, screen, endpoint, import, comment"},
                {"name": "functionName", "dataType": ["text"], "description": "Nombre de la función/clase/componente"},
                {"name": "parentFunction", "dataType": ["text"], "description": "Función o clase padre (si aplica)"},
                {"name": "fragmentIndex", "dataType": ["int"], "description": "Índice del fragmento (para funciones largas divididas)"},
                {"name": "startLine", "dataType": ["int"], "description": "Línea de inicio del fragmento"},
                {"name": "endLine", "dataType": ["int"], "description": "Línea de fin del fragmento"},
                
                # CONTENIDO Y DESCRIPCIÓN
                {"name": "content", "dataType": ["text"], "description": "Contenido completo del fragmento"},
                {"name": "description", "dataType": ["text"], "description": "Descripción generada por IA del fragmento"},
                
                # CATEGORIZACIÓN
                {"name": "module", "dataType": ["text"], "description": "Módulo o carpeta lógica"},
                {"name": "language", "dataType": ["text"], "description": "Lenguaje de programación"},
                {"name": "framework", "dataType": ["text"], "description": "Framework detectado (React, Polymer, Vue, etc.)"},
                
                # METADATA ADICIONAL
                {"name": "complexity", "dataType": ["text"], "description": "Complejidad estimada: low, medium, high"},
                {"name": "dependencies", "dataType": ["text[]"], "description": "Dependencias detectadas en el fragmento"},
                {"name": "exports", "dataType": ["text[]"], "description": "Exports detectados"},
                {"name": "parameters", "dataType": ["text[]"], "description": "Parámetros de función (si aplica)"},
                {"name": "returnType", "dataType": ["text"], "description": "Tipo de retorno (si se puede detectar)"},
                
                # TIMESTAMPS
                {"name": "indexedAt", "dataType": ["date"], "description": "Fecha de indexación"}
            ]
        }
        
        try:
            self.weaviate_client.schema.create_class(schema)
            print(f"✅ Esquema de fragmentos creado para proyecto: {class_name}")
            return True
        except Exception as e:
            print(f"❌ Error creando esquema: {e}")
            return False

    def _sanitize_project_name(self, project_name: str) -> str:
        """Sanitiza el nombre del proyecto para usarlo como clase en Weaviate"""
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', project_name)
        if sanitized and not sanitized[0].isalpha():
            sanitized = f"Proj_{sanitized}"
        return sanitized or "UnknownProject"

    def _log(self, message: str, force: bool = False):
        """Log thread-safe con soporte para verbose mode"""
        important_prefixes = ['🚀', '✅', '❌', '📊', '🏁', '💾', '📦', '🔍']
        is_important = force or any(message.startswith(prefix) for prefix in important_prefixes)
        
        if is_important or self._verbose_mode:
            with self._log_lock:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def _should_index_file(self, file_path: str, relative_path: str, content: str) -> bool:
        """Decide si un archivo es relevante para indexar"""
        # Extensiones irrelevantes
        ignored_exts = [
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.bmp', '.tiff', '.webp',
            '.exe', '.dll', '.so', '.bin', '.obj', '.class', '.pyc', '.pyo', '.zip', '.tar', '.gz', '.rar', '.7z',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.mp3', '.mp4', '.avi', '.mov', '.mkv',
            '.log', '.tmp', '.bak', '.swp', '.lock', '.db', '.sqlite', '.woff', '.woff2', '.eot', '.ttf', '.otf',
            '.DS_Store', '.plist', '.sublime-workspace', '.sublime-project', '.iml', '.idea', '.vs', '.vscode', 
            '.env', '.sample', '.min.js', '.map'
        ]
        
        ext = Path(file_path).suffix.lower()
        if ext in ignored_exts:
            reason = f"Extensión irrelevante ({ext}): {relative_path}"
            self._log(f"[IGNORADO] {reason}")
            self._log_to_file("ignored", reason)
            return False
        
        # Archivos ocultos o de sistema
        if os.path.basename(file_path).startswith('.'):
            reason = f"Archivo oculto: {relative_path}"
            self._log(f"[IGNORADO] {reason}")
            self._log_to_file("ignored", reason)
            return False
        
        # Archivos muy pequeños o vacíos
        if len(content.strip()) < 10:
            reason = f"Archivo vacío o muy pequeño ({len(content)} bytes): {relative_path}"
            self._log(f"[IGNORADO] {reason}")
            self._log_to_file("ignored", reason)
            return False
        
        # Archivos binarios
        if '\x00' in content or not all(32 <= ord(c) <= 126 or c in '\n\r\t' for c in content[:100]):
            reason = f"Archivo binario o no texto: {relative_path}"
            self._log(f"[IGNORADO] {reason}")
            self._log_to_file("ignored", reason)
            return False
        
        # Carpetas irrelevantes
        ignored_dirs = ['node_modules', 'bower_components', '.git', 'dist', 'build', 'coverage', 'nbproject', '.idea', '.vscode', '__pycache__']
        if any(f"{os.sep}{d}{os.sep}" in file_path for d in ignored_dirs):
            reason = f"Carpeta irrelevante en ruta: {relative_path}"
            self._log(f"[IGNORADO] {reason}")
            self._log_to_file("ignored", reason)
            return False
        
        # Solo indexar archivos de código
        code_extensions = ['.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.cs', '.php', '.rb', '.go', '.rs', '.cpp', '.c', '.html', '.htm', '.vue', '.css', '.scss', '.sass']
        if ext not in code_extensions:
            reason = f"No es archivo de código ({ext}): {relative_path}"
            self._log(f"[IGNORADO] {reason}")
            self._log_to_file("ignored", reason)
            return False
        
        return True

    def _extract_code_fragments(self, file_path: str, content: str, language: str) -> List[Dict]:
        """
        Extrae fragmentos de código del archivo según el tipo de contenido
        """
        fragments = []
        lines = content.split('\n')
        
        # Detectar módulo basado en la ruta
        module = self._extract_module_from_path(file_path)
        
        # Detectar framework
        framework = self._detect_framework(content, language)
        
        if language in ['javascript', 'typescript']:
            fragments.extend(self._extract_js_fragments(lines, file_path, module, language, framework))
        elif language == 'python':
            fragments.extend(self._extract_python_fragments(lines, file_path, module, language, framework))
        elif language == 'html':
            fragments.extend(self._extract_html_fragments(lines, file_path, module, language, framework))
        elif language in ['css', 'scss', 'sass']:
            fragments.extend(self._extract_css_fragments(lines, file_path, module, language, framework))
        else:
            # Fragmentación genérica
            fragments.extend(self._extract_generic_fragments(lines, file_path, module, language, framework))
        
        return fragments

    def _extract_module_from_path(self, file_path: str) -> str:
        """Extrae el módulo basado en la estructura de carpetas"""
        path_parts = Path(file_path).parts
        
        # Buscar carpetas que indiquen módulos
        module_indicators = ['src', 'app', 'components', 'views', 'pages', 'modules', 'features']
        
        for i, part in enumerate(path_parts):
            if part.lower() in module_indicators and i + 1 < len(path_parts):
                return path_parts[i + 1]
        
        # Si no encuentra, usar la carpeta padre del archivo
        if len(path_parts) > 1:
            return path_parts[-2]
        
        return 'root'

    def _detect_framework(self, content: str, language: str) -> str:
        """Detecta el framework usado en el archivo"""
        content_lower = content.lower()
        
        # React
        if 'react' in content_lower or 'usestate' in content_lower or 'jsx' in content_lower:
            return 'react'
        
        # Vue
        if 'vue' in content_lower or '<template>' in content_lower:
            return 'vue'
        
        # Angular
        if '@component' in content_lower or 'angular' in content_lower:
            return 'angular'
        
        # Polymer
        if 'polymer' in content_lower or 'dom-module' in content_lower or 'iron-' in content_lower:
            return 'polymer'
        
        # Express/Node.js
        if 'express' in content_lower or 'app.get' in content_lower or 'router.' in content_lower:
            return 'express'
        
        # Django/Flask
        if 'django' in content_lower or 'flask' in content_lower:
            return 'django' if 'django' in content_lower else 'flask'
        
        return 'vanilla'

    def _extract_js_fragments(self, lines: List[str], file_path: str, module: str, language: str, framework: str) -> List[Dict]:
        """Extrae fragmentos específicos de JavaScript/TypeScript"""
        fragments = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Funciones
            if self._is_function_declaration(line):
                fragment = self._extract_function_fragment(lines, i, file_path, module, language, framework)
                if fragment:
                    fragments.append(fragment)
                    i = fragment['end_line']
                    continue
            
            # Clases
            elif self._is_class_declaration(line):
                fragment = self._extract_class_fragment(lines, i, file_path, module, language, framework)
                if fragment:
                    fragments.append(fragment)
                    i = fragment['end_line']
                    continue
            
            # Componentes React/Vue
            elif self._is_component_declaration(line, framework):
                fragment = self._extract_component_fragment(lines, i, file_path, module, language, framework)
                if fragment:
                    fragments.append(fragment)
                    i = fragment['end_line']
                    continue
            
            # Endpoints (Express, etc.)
            elif self._is_endpoint_declaration(line):
                fragment = self._extract_endpoint_fragment(lines, i, file_path, module, language, framework)
                if fragment:
                    fragments.append(fragment)
                    i = fragment['end_line']
                    continue
            
            # Imports/Exports importantes
            elif self._is_important_import_export(line):
                fragment = self._extract_import_export_fragment(lines, i, file_path, module, language, framework)
                if fragment:
                    fragments.append(fragment)
            
            i += 1
        
        return fragments

    def _is_function_declaration(self, line: str) -> bool:
        """Detecta declaraciones de función"""
        patterns = [
            r'function\s+\w+',
            r'const\s+\w+\s*=\s*\(',
            r'let\s+\w+\s*=\s*\(',
            r'var\s+\w+\s*=\s*\(',
            r'\w+\s*:\s*function',
            r'\w+\s*=>\s*{',
            r'async\s+function',
            r'export\s+function',
            r'export\s+const\s+\w+\s*='
        ]
        return any(re.search(pattern, line) for pattern in patterns)

    def _is_class_declaration(self, line: str) -> bool:
        """Detecta declaraciones de clase"""
        patterns = [
            r'class\s+\w+',
            r'export\s+class\s+\w+',
            r'export\s+default\s+class\s+\w+'
        ]
        return any(re.search(pattern, line) for pattern in patterns)

    def _is_component_declaration(self, line: str, framework: str) -> bool:
        """Detecta declaraciones de componente según el framework"""
        if framework == 'react':
            patterns = [
                r'const\s+\w+\s*=\s*\(\s*\)\s*=>\s*{',
                r'function\s+\w+\s*\(\s*\)\s*{.*return.*<',
                r'export\s+default\s+function\s+\w+'
            ]
        elif framework == 'vue':
            patterns = [
                r'export\s+default\s*{',
                r'Vue\.component\s*\(',
                r'<script.*setup'
            ]
        elif framework == 'polymer':
            patterns = [
                r'Polymer\s*\(',
                r'class\s+\w+\s+extends\s+PolymerElement'
            ]
        else:
            return False
        
        return any(re.search(pattern, line) for pattern in patterns)

    def _is_endpoint_declaration(self, line: str) -> bool:
        """Detecta declaraciones de endpoint"""
        patterns = [
            r'app\.(get|post|put|delete|patch)\s*\(',
            r'router\.(get|post|put|delete|patch)\s*\(',
            r'@(Get|Post|Put|Delete|Patch)\s*\(',
            r'@app\.route\s*\(',
            r'def\s+\w+.*@.*route'
        ]
        return any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns)

    def _is_important_import_export(self, line: str) -> bool:
        """Detecta imports/exports importantes"""
        if line.startswith('import ') or line.startswith('export ') or line.startswith('from '):
            # Ignorar imports de librerías muy comunes
            common_libs = ['react', 'lodash', 'moment', 'axios']
            return not any(lib in line.lower() for lib in common_libs)
        return False

    def _extract_function_fragment(self, lines: List[str], start_idx: int, file_path: str, module: str, language: str, framework: str) -> Dict:
        """Extrae un fragmento de función completo"""
        start_line = start_idx + 1  # 1-indexed
        function_name = self._extract_function_name(lines[start_idx])
        
        # Encontrar el final de la función
        end_idx = self._find_function_end(lines, start_idx)
        end_line = end_idx + 1
        
        # Extraer contenido
        content_lines = lines[start_idx:end_idx + 1]
        content = '\n'.join(content_lines)
        
        # Si la función es muy larga, fragmentarla
        if len(content_lines) > self.max_function_lines:
            # Para funciones largas, devolver el primer fragmento y agregar los demás a la lista
            large_fragments = self._fragment_large_function(content_lines, start_line, function_name, file_path, module, language, framework)
            return large_fragments[0] if large_fragments else None
        
        # Generar descripción
        description = self._generate_fragment_description(content, 'function', function_name)
        
        return {
            'file_name': os.path.basename(file_path),
            'file_path': file_path,
            'type': 'function',
            'function_name': function_name,
            'parent_function': None,
            'fragment_index': 0,
            'start_line': start_line,
            'end_line': end_line,
            'content': content,
            'description': description,
            'module': module,
            'language': language,
            'framework': framework,
            'complexity': self._estimate_complexity(content),
            'dependencies': self._extract_dependencies_from_content(content),
            'parameters': self._extract_function_parameters(lines[start_idx]),
            'return_type': self._extract_return_type(content)
        }

    def _find_function_end(self, lines: List[str], start_idx: int) -> int:
        """Encuentra el final de una función basado en llaves/indentación"""
        brace_count = 0
        in_function = False
        
        for i in range(start_idx, len(lines)):
            line = lines[i]
            
            # Contar llaves
            brace_count += line.count('{') - line.count('}')
            
            if '{' in line:
                in_function = True
            
            # Si estamos en la función y las llaves se balancean, hemos terminado
            if in_function and brace_count == 0:
                return i
        
        # Si no encontramos el final, devolver hasta el final del archivo
        return len(lines) - 1

    def _extract_function_name(self, line: str) -> str:
        """Extrae el nombre de la función de la línea de declaración"""
        # function nombre()
        match = re.search(r'function\s+(\w+)', line)
        if match:
            return match.group(1)
        
        # const nombre = () =>
        match = re.search(r'(?:const|let|var)\s+(\w+)\s*=', line)
        if match:
            return match.group(1)
        
        # nombre: function()
        match = re.search(r'(\w+)\s*:\s*function', line)
        if match:
            return match.group(1)
        
        # export function nombre()
        match = re.search(r'export\s+function\s+(\w+)', line)
        if match:
            return match.group(1)
        
        return 'anonymous'

    def _generate_fragment_description(self, content: str, fragment_type: str, name: str) -> str:
        """Genera descripción del fragmento usando IA"""
        prompt = f"""Analiza este fragmento de código {fragment_type} llamado '{name}' y describe en 1-2 líneas qué hace:

{content[:500]}...

Responde solo con la descripción, sin explicaciones adicionales."""
        
        return self._consultar_ollama(prompt) or f"{fragment_type.title()} {name}"

    def _estimate_complexity(self, content: str) -> str:
        """Estima la complejidad del fragmento"""
        lines = len(content.split('\n'))
        
        # Contar estructuras de control
        control_structures = len(re.findall(r'\b(if|for|while|switch|try|catch)\b', content))
        
        # Contar funciones anidadas
        nested_functions = len(re.findall(r'function\s+\w+|=>\s*{', content))
        
        complexity_score = lines + (control_structures * 3) + (nested_functions * 2)
        
        if complexity_score < 20:
            return 'low'
        elif complexity_score < 50:
            return 'medium'
        else:
            return 'high'

    def _extract_dependencies_from_content(self, content: str) -> List[str]:
        """Extrae dependencias del contenido del fragmento"""
        dependencies = []
        
        # Imports
        imports = re.findall(r'import.*?from\s+[\'"]([^\'"]+)[\'"]', content)
        dependencies.extend(imports)
        
        # Requires
        requires = re.findall(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content)
        dependencies.extend(requires)
        
        return list(set(dependencies))

    def _extract_function_parameters(self, line: str) -> List[str]:
        """Extrae parámetros de la función"""
        # Buscar parámetros entre paréntesis
        match = re.search(r'\(([^)]*)\)', line)
        if match:
            params_str = match.group(1).strip()
            if params_str:
                # Dividir por comas y limpiar
                params = [p.strip().split('=')[0].strip() for p in params_str.split(',')]
                return [p for p in params if p and p != '...']
        return []

    def _extract_return_type(self, content: str) -> str:
        """Intenta detectar el tipo de retorno"""
        # Buscar return statements
        returns = re.findall(r'return\s+([^;]+)', content)
        if returns:
            first_return = returns[0].strip()
            if first_return.startswith('{'):
                return 'object'
            elif first_return.startswith('['):
                return 'array'
            elif first_return.startswith('"') or first_return.startswith("'"):
                return 'string'
            elif first_return.isdigit():
                return 'number'
            elif first_return in ['true', 'false']:
                return 'boolean'
        return 'unknown'

    # Implementaciones básicas para otros tipos de fragmentos
    def _extract_class_fragment(self, lines: List[str], start_idx: int, file_path: str, module: str, language: str, framework: str) -> Dict:
        """Extrae fragmento de clase (implementación básica)"""
        # Similar a _extract_function_fragment pero para clases
        return None  # Implementar según necesidades

    def _extract_component_fragment(self, lines: List[str], start_idx: int, file_path: str, module: str, language: str, framework: str) -> Dict:
        """Extrae fragmento de componente (implementación básica)"""
        # Implementar para React, Vue, Polymer, etc.
        return None

    def _extract_endpoint_fragment(self, lines: List[str], start_idx: int, file_path: str, module: str, language: str, framework: str) -> Dict:
        """Extrae fragmento de endpoint (implementación básica)"""
        # Implementar para Express, Flask, etc.
        return None

    def _extract_import_export_fragment(self, lines: List[str], start_idx: int, file_path: str, module: str, language: str, framework: str) -> Dict:
        """Extrae fragmento de import/export (implementación básica)"""
        # Implementar para imports/exports importantes
        return None

    def _extract_python_fragments(self, lines: List[str], file_path: str, module: str, language: str, framework: str) -> List[Dict]:
        """Extrae fragmentos de Python: funciones, clases, imports"""
        fragments = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Funciones
            if self._is_python_function_declaration(line):
                fragment = self._extract_python_function_fragment(lines, i, file_path, module, language, framework)
                if fragment:
                    fragments.append(fragment)
                    i = fragment['end_line']
                    continue
            
            # Clases
            elif self._is_python_class_declaration(line):
                fragment = self._extract_python_class_fragment(lines, i, file_path, module, language, framework)
                if fragment:
                    fragments.append(fragment)
                    i = fragment['end_line']
                    continue
            
            # Imports importantes
            elif self._is_python_important_import(line):
                fragment = self._extract_python_import_fragment(lines, i, file_path, module, language, framework)
                if fragment:
                    fragments.append(fragment)
            
            i += 1
        
        return fragments

    def _is_python_function_declaration(self, line: str) -> bool:
        """Detecta declaraciones de función en Python"""
        return re.match(r'^\s*def\s+\w+\s*\(', line) is not None

    def _is_python_class_declaration(self, line: str) -> bool:
        """Detecta declaraciones de clase en Python"""
        return re.match(r'^\s*class\s+\w+', line) is not None

    def _is_python_important_import(self, line: str) -> bool:
        """Detecta imports importantes en Python"""
        if line.startswith('import ') or line.startswith('from '):
            # Ignorar imports de librerías muy comunes
            common_libs = ['os', 'sys', 'json', 're', 'time', 'datetime']
            return not any(lib in line.lower() for lib in common_libs)
        return False

    def _extract_python_function_fragment(self, lines: List[str], start_idx: int, file_path: str, module: str, language: str, framework: str) -> Dict:
        """Extrae un fragmento de función Python"""
        start_line = start_idx + 1  # 1-indexed
        function_name = self._extract_python_function_name(lines[start_idx])
        
        # Encontrar el final de la función basado en indentación
        end_idx = self._find_python_function_end(lines, start_idx)
        end_line = end_idx + 1
        
        # Extraer contenido
        content_lines = lines[start_idx:end_idx + 1]
        content = '\n'.join(content_lines)
        
        # Si la función es muy larga, fragmentarla
        if len(content_lines) > self.max_function_lines:
            # Para funciones largas, devolver el primer fragmento y agregar los demás a la lista
            large_fragments = self._fragment_large_function(content_lines, start_line, function_name, file_path, module, language, framework)
            return large_fragments[0] if large_fragments else None
        
        # Generar descripción
        description = self._generate_fragment_description(content, 'function', function_name)
        
        return {
            'file_name': os.path.basename(file_path),
            'file_path': file_path,
            'type': 'function',
            'function_name': function_name,
            'parent_function': None,
            'fragment_index': 0,
            'start_line': start_line,
            'end_line': end_line,
            'content': content,
            'description': description,
            'module': module,
            'language': language,
            'framework': framework,
            'complexity': self._estimate_complexity(content),
            'dependencies': self._extract_dependencies_from_content(content),
            'parameters': self._extract_python_function_parameters(lines[start_idx]),
            'return_type': self._extract_python_return_type(content)
        }

    def _extract_python_class_fragment(self, lines: List[str], start_idx: int, file_path: str, module: str, language: str, framework: str) -> Dict:
        """Extrae un fragmento de clase Python"""
        start_line = start_idx + 1  # 1-indexed
        class_name = self._extract_python_class_name(lines[start_idx])
        
        # Encontrar el final de la clase basado en indentación
        end_idx = self._find_python_class_end(lines, start_idx)
        end_line = end_idx + 1
        
        # Extraer contenido
        content_lines = lines[start_idx:end_idx + 1]
        content = '\n'.join(content_lines)
        
        # Generar descripción
        description = self._generate_fragment_description(content, 'class', class_name)
        
        return {
            'file_name': os.path.basename(file_path),
            'file_path': file_path,
            'type': 'class',
            'function_name': class_name,
            'parent_function': None,
            'fragment_index': 0,
            'start_line': start_line,
            'end_line': end_line,
            'content': content,
            'description': description,
            'module': module,
            'language': language,
            'framework': framework,
            'complexity': self._estimate_complexity(content),
            'dependencies': self._extract_dependencies_from_content(content),
            'parameters': [],
            'return_type': 'class'
        }

    def _extract_python_import_fragment(self, lines: List[str], start_idx: int, file_path: str, module: str, language: str, framework: str) -> Dict:
        """Extrae un fragmento de import Python"""
        line = lines[start_idx]
        
        return {
            'file_name': os.path.basename(file_path),
            'file_path': file_path,
            'type': 'import',
            'function_name': 'imports',
            'parent_function': None,
            'fragment_index': 0,
            'start_line': start_idx + 1,
            'end_line': start_idx + 1,
            'content': line,
            'description': f"Import statement: {line.strip()}",
            'module': module,
            'language': language,
            'framework': framework,
            'complexity': 'low',
            'dependencies': [line.strip()],
            'parameters': [],
            'return_type': 'import'
        }

    def _find_python_function_end(self, lines: List[str], start_idx: int) -> int:
        """Encuentra el final de una función Python basado en indentación"""
        if start_idx >= len(lines):
            return start_idx
        
        # Obtener la indentación base de la función
        base_indent = len(lines[start_idx]) - len(lines[start_idx].lstrip())
        
        # Buscar el final basado en indentación
        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            
            # Líneas vacías o solo comentarios se ignoran
            if not line.strip() or line.strip().startswith('#'):
                continue
            
            # Si encontramos una línea con indentación igual o menor, hemos terminado
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent:
                return i - 1
        
        # Si llegamos al final del archivo
        return len(lines) - 1

    def _find_python_class_end(self, lines: List[str], start_idx: int) -> int:
        """Encuentra el final de una clase Python basado en indentación"""
        return self._find_python_function_end(lines, start_idx)

    def _extract_python_function_name(self, line: str) -> str:
        """Extrae el nombre de la función de la línea de declaración Python"""
        match = re.search(r'def\s+(\w+)', line)
        return match.group(1) if match else 'unknown_function'

    def _extract_python_class_name(self, line: str) -> str:
        """Extrae el nombre de la clase de la línea de declaración Python"""
        match = re.search(r'class\s+(\w+)', line)
        return match.group(1) if match else 'unknown_class'

    def _extract_python_function_parameters(self, line: str) -> List[str]:
        """Extrae parámetros de la función Python"""
        match = re.search(r'def\s+\w+\s*\(([^)]*)\)', line)
        if match:
            params_str = match.group(1).strip()
            if params_str:
                # Dividir por comas y limpiar
                params = [p.strip().split('=')[0].strip().split(':')[0].strip() for p in params_str.split(',')]
                return [p for p in params if p and p != 'self']
        return []

    def _extract_python_return_type(self, content: str) -> str:
        """Intenta detectar el tipo de retorno en Python"""
        # Buscar return statements
        returns = re.findall(r'return\s+([^#\n]+)', content)
        if returns:
            first_return = returns[0].strip()
            if first_return.startswith('{') or 'dict(' in first_return:
                return 'dict'
            elif first_return.startswith('[') or 'list(' in first_return:
                return 'list'
            elif first_return.startswith('"') or first_return.startswith("'"):
                return 'str'
            elif first_return.isdigit():
                return 'int'
            elif first_return in ['True', 'False']:
                return 'bool'
            elif first_return == 'None':
                return 'None'
        return 'unknown'

    def _extract_html_fragments(self, lines: List[str], file_path: str, module: str, language: str, framework: str) -> List[Dict]:
        """Extrae fragmentos de HTML (implementación básica)"""
        return []

    def _extract_css_fragments(self, lines: List[str], file_path: str, module: str, language: str, framework: str) -> List[Dict]:
        """Extrae fragmentos de CSS (implementación básica)"""
        return []

    def _extract_generic_fragments(self, lines: List[str], file_path: str, module: str, language: str, framework: str) -> List[Dict]:
        """Extrae fragmentos genéricos (implementación básica)"""
        return []

    def _fragment_large_function(self, content_lines: List[str], start_line: int, function_name: str, file_path: str, module: str, language: str, framework: str) -> List[Dict]:
        """Fragmenta funciones muy largas en chunks más pequeños"""
        fragments = []
        
        for i in range(0, len(content_lines), self.fragment_chunk_size - self.fragment_overlap):
            end_idx = min(i + self.fragment_chunk_size, len(content_lines))
            
            chunk_content = '\n'.join(content_lines[i:end_idx])
            chunk_start_line = start_line + i
            chunk_end_line = start_line + end_idx - 1
            
            description = self._generate_fragment_description(chunk_content, 'function_chunk', f"{function_name}_part_{len(fragments)}")
            
            fragment = {
                'file_name': os.path.basename(file_path),
                'file_path': file_path,
                'type': 'function',
                'function_name': function_name,
                'parent_function': function_name,
                'fragment_index': len(fragments),
                'start_line': chunk_start_line,
                'end_line': chunk_end_line,
                'content': chunk_content,
                'description': description,
                'module': module,
                'language': language,
                'framework': framework,
                'complexity': self._estimate_complexity(chunk_content),
                'dependencies': self._extract_dependencies_from_content(chunk_content),
                'parameters': [],
                'return_type': 'unknown'
            }
            
            fragments.append(fragment)
        
        return fragments

    def _detect_language(self, file_path: str) -> str:
        """Detecta el lenguaje basado en la extensión"""
        ext = Path(file_path).suffix.lower()
        lang_map = {
            '.js': 'javascript', '.ts': 'typescript', '.jsx': 'javascript', '.tsx': 'typescript',
            '.html': 'html', '.htm': 'html', '.css': 'css', '.scss': 'scss', '.sass': 'sass',
            '.py': 'python', '.java': 'java', '.cs': 'csharp', '.php': 'php', '.rb': 'ruby',
            '.go': 'go', '.rs': 'rust', '.cpp': 'cpp', '.c': 'c', '.vue': 'vue'
        }
        return lang_map.get(ext, 'unknown')

    def _process_file_thread_safe(self, file_data: tuple, project_name: str, project_analysis: Dict, file_index: int, total_files: int) -> Dict:
        """Procesa un archivo en un thread separado de forma segura"""
        file_path, relative_path = file_data
        result = {
            "success": False,
            "indexed": False,
            "error": None,
            "file_path": relative_path,
            "fragments_count": 0
        }
        
        try:
            # Leer archivo
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                reason = f"Error leyendo archivo: {relative_path} - {e}"
                self._log(f"⚠️  No se pudo leer: {relative_path}")
                self._log_to_file("not_indexed", reason)
                result["error"] = reason
                return result
            
            # Verificar si debe indexar
            if not self._should_index_file(file_path, relative_path, content):
                result["success"] = True
                return result
            
            self._log(f"🔍 Analizando archivo: {relative_path} ({file_index}/{total_files})")
            
            # Detectar lenguaje
            language = self._detect_language(file_path)
            
            # Extraer fragmentos
            fragments = self._extract_code_fragments(file_path, content, language)
            
            if fragments:
                # Indexar cada fragmento
                indexed_count = 0
                for fragment in fragments:
                    if self._index_fragment(fragment, project_name):
                        indexed_count += 1
                
                with self._counter_lock:
                    self._indexed_fragments_count += indexed_count
                
                self._log(f"✅ Indexado: {relative_path} ({indexed_count} fragmentos)")
                result["success"] = True
                result["indexed"] = True
                result["fragments_count"] = indexed_count
            else:
                reason = f"No se encontraron fragmentos relevantes: {relative_path}"
                self._log(f"⚠️  Sin fragmentos: {relative_path}")
                self._log_to_file("not_indexed", reason)
                result["error"] = reason
                
        except Exception as e:
            error_msg = f"❌ Error en: {relative_path} - {e}"
            reason = f"Error durante indexación: {relative_path} - {e}"
            self._log(error_msg)
            self._log_to_file("not_indexed", reason)
            result["error"] = reason
        
        return result

    def _index_fragment(self, fragment: Dict, project_name: str) -> bool:
        """Indexa un fragmento individual en Weaviate"""
        class_name = f"CodeFragments_{self._sanitize_project_name(project_name)}"
        
        # Preparar datos para Weaviate
        weaviate_data = {
            "projectName": project_name,
            "fileName": fragment['file_name'],
            "filePath": fragment['file_path'].replace('\\', '/'),
            "type": fragment['type'],
            "functionName": fragment['function_name'],
            "parentFunction": fragment.get('parent_function'),
            "fragmentIndex": fragment['fragment_index'],
            "startLine": fragment['start_line'],
            "endLine": fragment['end_line'],
            "content": fragment['content'],
            "description": fragment['description'],
            "module": fragment['module'],
            "language": fragment['language'],
            "framework": fragment.get('framework', 'unknown'),
            "complexity": fragment.get('complexity', 'unknown'),
            "dependencies": fragment.get('dependencies', []),
            "exports": fragment.get('exports', []),
            "parameters": fragment.get('parameters', []),
            "returnType": fragment.get('return_type', 'unknown'),
            "indexedAt": datetime.now(timezone.utc).isoformat()
        }
        
        # Crear embedding del contenido + descripción
        embedding_text = f"{fragment['description']} {fragment['content'][:500]}"
        embedding = self._get_embedding(embedding_text)
        
        try:
            self.weaviate_client.data_object.create(
                data_object=weaviate_data,
                class_name=class_name,
                vector=embedding
            )
            return True
        except Exception as e:
            print(f"Error indexando fragmento {fragment['function_name']}: {e}")
            return False

    def analyze_and_index_project(self, project_path: str, project_name: str = None, force_schema: bool = True) -> Dict:
        """Analiza e indexa un proyecto completo extrayendo fragmentos de código"""
        if project_name is None:
            project_name = os.path.basename(project_path)
        
        self._log(f"🚀 Iniciando análisis e indexación de fragmentos del proyecto: {project_name}", force=True)
        self._log(f"📁 Ruta: {project_path}", force=True)
        
        if force_schema:
            if not self.create_weaviate_schema(project_name):
                return {"error": "No se pudo crear el esquema en Weaviate"}
        
        # Análisis básico del proyecto
        project_analysis = self.analyze_project_structure(project_path)
        project_analysis["project_name"] = project_name
        project_analysis["analysis_date"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        
        # Resetear contador
        with self._counter_lock:
            self._indexed_fragments_count = 0
        
        errors = []
        start_time = time.time()
        ignore_dirs = ['node_modules', 'bower_components', '.git', 'dist', 'build', 'coverage', 'nbproject']
        all_files = []
        
        # Recopilar todos los archivos
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ignore_dirs]
            for file in files:
                if file.startswith('.'):
                    continue
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, project_path).replace('\\', '/')
                all_files.append((file_path, relative_path))
        
        total_files = len(all_files)
        self._log(f"📁 Total de archivos encontrados: {total_files}", force=True)
        
        # Configurar paralelización
        max_workers = self.max_workers
        self._log(f"🚀 Procesando con {max_workers} threads paralelos", force=True)
        
        completed_files = 0
        last_progress_time = time.time()
        
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Enviar tareas al pool
                future_to_file = {
                    executor.submit(
                        self._process_file_thread_safe, 
                        file_data, 
                        project_name, 
                        project_analysis, 
                        idx, 
                        total_files
                    ): (idx, file_data) for idx, file_data in enumerate(all_files, 1)
                }
                
                # Procesar resultados conforme se completan
                for future in as_completed(future_to_file):
                    idx, file_data = future_to_file[future]
                    completed_files += 1
                    
                    try:
                        result = future.result(timeout=self.file_timeout)
                        
                        if result["error"]:
                            errors.append(result["error"])
                            
                    except Exception as e:
                        error_msg = f"❌ Error procesando {file_data[1]}: {e}"
                        self._log(error_msg)
                        errors.append(error_msg)
                    
                    # Mostrar progreso cada 10 archivos o cada 30 segundos
                    current_time = time.time()
                    if completed_files % 10 == 0 or (current_time - last_progress_time) > 30:
                        elapsed = current_time - start_time
                        if completed_files > 0:
                            avg_time = elapsed / completed_files
                            remaining = total_files - completed_files
                            est_seconds = int(avg_time * remaining)
                            est_min, est_sec = divmod(est_seconds, 60)
                            
                            with self._counter_lock:
                                indexed_count = self._indexed_fragments_count
                            
                            self._log(f"⏳ Progreso: {completed_files}/{total_files} procesados, {indexed_count} fragmentos indexados. Tiempo estimado: {est_min}m {est_sec}s", force=True)
                        last_progress_time = current_time
                        
        except KeyboardInterrupt:
            self._log("⏹️  Interrupción del usuario. Cerrando threads...", force=True)
            executor.shutdown(wait=False)
            raise
        
        # Obtener resultado final
        with self._counter_lock:
            indexed_fragments = self._indexed_fragments_count
            
        total_time = int(time.time() - start_time)
        min_total, sec_total = divmod(total_time, 60)
        self._log(f"🏁 Análisis completado en {min_total}m {sec_total}s. Fragmentos indexados: {indexed_fragments}", force=True)
        
        if errors:
            self._log(f"❗ Errores encontrados: {len(errors)}", force=True)
        
        # Finalizar archivos de log y mostrar resumen
        if self._log_files["enabled"]:
            self._finalize_log_files()
        
        result = {
            "project_name": project_name,
            "project_path": project_path,
            "indexed_fragments": indexed_fragments,
            "total_files": total_files,
            "technologies": project_analysis.get('technologies_detected', []),
            "architecture_patterns": project_analysis.get('architecture_patterns', []),
            "errors": errors,
            "analysis_date": project_analysis["analysis_date"]
        }
        return result

    # Métodos auxiliares que necesitan implementación básica
    def _setup_log_files(self, base_path: str, project_name: str, clear_existing: bool = False):
        """Configuración básica de archivos de log"""
        pass

    def _log_to_file(self, log_type: str, message: str):
        """Log básico a archivo"""
        pass

    def _finalize_log_files(self):
        """Finalización básica de logs"""
        pass

    def analyze_project_structure(self, project_path: str) -> Dict:
        """Análisis básico de estructura del proyecto"""
        return {
            "total_files": 0,
            "technologies_detected": [],
            "architecture_patterns": []
        }

    def _consultar_ollama(self, prompt: str) -> str:
        """Consulta a Ollama para generar descripciones"""
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

    # Métodos de consulta (implementación básica)
    def query_project(self, project_name: str, query: str, limit: int = 20) -> Dict:
        """Consulta fragmentos del proyecto usando búsqueda semántica"""
        if not self.weaviate_client:
            return {"error": "Cliente Weaviate no disponible"}
        
        class_name = f"CodeFragments_{self._sanitize_project_name(project_name)}"
        
        try:
            # Generar embedding de la consulta
            query_embedding = self._get_embedding(query)
            if not query_embedding:
                return {"error": "No se pudo generar embedding para la consulta"}
            
            # Búsqueda semántica en fragmentos
            result = (
                self.weaviate_client.query
                .get(class_name, [
                    'fileName', 'filePath', 'type', 'functionName', 'startLine', 'endLine',
                    'content', 'description', 'module', 'language', 'framework', 'complexity'
                ])
                .with_near_vector({"vector": query_embedding})
                .with_limit(limit)
                .do()
            )
            
            if 'data' in result and 'Get' in result['data'] and class_name in result['data']['Get']:
                fragments = result['data']['Get'][class_name]
                
                # Preparar contexto para IA
                context = self._prepare_fragments_context(fragments, query)
                
                # Generar respuesta usando IA
                ai_response = self._generate_ai_response(query, context)
                
                return {
                    "success": True,
                    "query": query,
                    "fragments_found": len(fragments),
                    "fragments": fragments,
                    "ai_response": ai_response,
                    "context": context
                }
            else:
                return {
                    "success": True,
                    "query": query,
                    "fragments_found": 0,
                    "fragments": [],
                    "ai_response": f"No se encontraron fragmentos relevantes para '{query}' en el proyecto {project_name}."
                }
                
        except Exception as e:
            return {"error": f"Error en consulta: {e}"}

    def list_project_modules(self, project_name: str) -> Dict:
        """Lista módulos del proyecto agrupados por tipo"""
        if not self.weaviate_client:
            return {"error": "Cliente Weaviate no disponible"}
        
        class_name = f"CodeFragments_{self._sanitize_project_name(project_name)}"
        
        try:
            # Obtener todos los fragmentos
            result = (
                self.weaviate_client.query
                .get(class_name, [
                    'fileName', 'filePath', 'type', 'functionName', 'module', 
                    'language', 'complexity', 'startLine', 'endLine'
                ])
                .with_limit(1000)  # Límite alto para obtener todos
                .do()
            )
            
            if 'data' in result and 'Get' in result['data'] and class_name in result['data']['Get']:
                fragments = result['data']['Get'][class_name]
                
                # Agrupar por tipo
                modules_by_type = {}
                for fragment in fragments:
                    ftype = fragment.get('type', 'unknown')
                    if ftype not in modules_by_type:
                        modules_by_type[ftype] = []
                    modules_by_type[ftype].append(fragment)
                
                # Estadísticas
                total_fragments = len(fragments)
                languages = set(f.get('language', 'unknown') for f in fragments)
                modules = set(f.get('module', 'unknown') for f in fragments)
                
                return {
                    "success": True,
                    "project_name": project_name,
                    "total_fragments": total_fragments,
                    "modules_by_type": modules_by_type,
                    "languages": list(languages),
                    "modules": list(modules),
                    "all_modules": fragments  # Para compatibilidad
                }
            else:
                return {
                    "success": True,
                    "project_name": project_name,
                    "total_fragments": 0,
                    "modules_by_type": {},
                    "languages": [],
                    "modules": [],
                    "all_modules": []
                }
                
        except Exception as e:
            return {"error": f"Error listando módulos: {e}"}

    def _prepare_fragments_context(self, fragments: List[Dict], query: str) -> str:
        """Prepara contexto estructurado con los fragmentos encontrados"""
        if not fragments:
            return "No se encontraron fragmentos relevantes."
        
        context = f"=== FRAGMENTOS RELEVANTES PARA: '{query}' ===\n\n"
        
        for i, fragment in enumerate(fragments[:10], 1):  # Limitar a 10 para no saturar
            context += f"FRAGMENTO {i}:\n"
            context += f"  📁 Archivo: {fragment.get('fileName', 'N/A')}\n"
            context += f"  📍 Ubicación: {fragment.get('filePath', 'N/A')} (líneas {fragment.get('startLine', 'N/A')}-{fragment.get('endLine', 'N/A')})\n"
            context += f"  🏷️  Tipo: {fragment.get('type', 'N/A')}\n"
            context += f"  🔧 Función/Clase: {fragment.get('functionName', 'N/A')}\n"
            context += f"  📦 Módulo: {fragment.get('module', 'N/A')}\n"
            context += f"  💻 Lenguaje: {fragment.get('language', 'N/A')}\n"
            context += f"  📊 Complejidad: {fragment.get('complexity', 'N/A')}\n"
            context += f"  📝 Descripción: {fragment.get('description', 'N/A')}\n"
            
            # Mostrar contenido truncado
            content = fragment.get('content', '')
            if len(content) > 300:
                content = content[:300] + "..."
            context += f"  💾 Contenido:\n{content}\n"
            context += f"  {'-' * 50}\n\n"
        
        if len(fragments) > 10:
            context += f"... y {len(fragments) - 10} fragmentos más.\n"
        
        return context

    def _generate_ai_response(self, query: str, context: str) -> str:
        """Genera respuesta usando IA basada en el contexto de fragmentos"""
        prompt = f"""Eres un asistente experto en análisis de código. Un usuario ha hecho la siguiente consulta sobre un proyecto de software:

CONSULTA DEL USUARIO: "{query}"

FRAGMENTOS DE CÓDIGO RELEVANTES ENCONTRADOS:
{context}

Tu tarea es:
1. Analizar los fragmentos de código encontrados
2. Responder la consulta del usuario de manera clara y estructurada
3. Proporcionar ejemplos específicos del código cuando sea relevante
4. Explicar cómo los fragmentos se relacionan con la consulta
5. Dar recomendaciones o insights útiles si es apropiado

Responde en español de manera técnica pero comprensible. Si no hay fragmentos relevantes, explica qué se podría buscar en su lugar.

RESPUESTA:"""

        return self._consultar_ollama(prompt)

    def delete_project_data(self, project_name: str) -> bool:
        """Elimina datos del proyecto"""
        if not self.weaviate_client:
            return False
        
        class_name = f"CodeFragments_{self._sanitize_project_name(project_name)}"
        
        try:
            self.weaviate_client.schema.delete_class(class_name)
            print(f"✅ Fragmentos del proyecto '{project_name}' eliminados de Weaviate")
            return True
        except Exception as e:
            print(f"❌ Error eliminando proyecto: {e}")
            return False