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

class CodeAnalysisAgent:
    """
    Agente especializado en análisis profundo de código para migración masiva.
    Analiza estructura, dependencias, patrones y arquitectura.
    Ahora con integración a Weaviate para indexación semántica.
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434", weaviate_url: str = "http://localhost:8080"):
        self.ollama_url = ollama_url
        self.weaviate_url = weaviate_url
        self._verbose_mode = False  # Para logging detallado cuando se usa --verbose
        self._log_files = {
            "ignored": None,
            "not_indexed": None,
            "enabled": False
        }
        
        # Conectar a Weaviate
        try:
            self.weaviate_client = weaviate.Client(weaviate_url)
            print(f"✅ Conectado a Weaviate en {weaviate_url}")
        except Exception as e:
            print(f"❌ Error conectando a Weaviate: {e}")
            self.weaviate_client = None
        
        # Patrones de archivos por tecnología
        self.tech_patterns = {
            "polymer": {
                "extensions": [".html", ".js", ".css"],
                "keywords": ["Polymer", "polymer", "dom-module", "iron-", "paper-", "neon-"],
                "imports": ["polymer/polymer.html", "@polymer/"]
            },
            "react": {
                "extensions": [".jsx", ".tsx", ".js", ".ts"],
                "keywords": ["React", "Component", "useState", "useEffect", "JSX"],
                "imports": ["react", "react-dom"]
            },
            "angular": {
                "extensions": [".ts", ".html", ".scss", ".css"],
                "keywords": ["@Component", "@Injectable", "NgModule", "Angular"],
                "imports": ["@angular/"]
            },
            "vue": {
                "extensions": [".vue", ".js", ".ts"],
                "keywords": ["Vue", "template", "script", "style"],
                "imports": ["vue", "@vue/"]
            }
        }

    def _get_embedding(self, text: str) -> List[float]:
        """Obtiene embedding usando Ollama (igual que memory_manager)"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/embeddings",
                json={
                    "model": "nomic-embed-text",
                    "prompt": text
                }
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
        Crea el esquema en Weaviate para el proyecto específico (vectorizer: none)
        """
        if not self.weaviate_client:
            return False
            
        class_name = f"Project_{self._sanitize_project_name(project_name)}"
        
        # Verificar si la clase ya existe
        try:
            existing_schema = self.weaviate_client.schema.get()
            existing_classes = [cls['class'] for cls in existing_schema.get('classes', [])]
            
            if class_name in existing_classes:
                print(f"⚠️  La clase {class_name} ya existe. Eliminándola para crear una nueva...")
                self.weaviate_client.schema.delete_class(class_name)
        except Exception as e:
            print(f"Error verificando esquema existente: {e}")
        
        # Definir el esquema (vectorizer: none)
        schema = {
            "class": class_name,
            "description": f"Análisis de código del proyecto {project_name}",
            "vectorizer": "none",
            "properties": [
                {
                    "name": "projectName",
                    "dataType": ["text"],
                    "description": "Nombre del proyecto"
                },
                {
                    "name": "filePath",
                    "dataType": ["text"],
                    "description": "Ruta del archivo"
                },
                {
                    "name": "fileName",
                    "dataType": ["text"],
                    "description": "Nombre del archivo"
                },
                {
                    "name": "fileType",
                    "dataType": ["text"],
                    "description": "Tipo de archivo (extensión)"
                },
                {
                    "name": "moduleType",
                    "dataType": ["text"],
                    "description": "Tipo de módulo (component, service, model, etc.)"
                },
                {
                    "name": "technology",
                    "dataType": ["text"],
                    "description": "Tecnología utilizada (polymer, react, angular, etc.)"
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Contenido del archivo"
                },
                {
                    "name": "summary",
                    "dataType": ["text"],
                    "description": "Resumen generado por IA"
                },
                {
                    "name": "dependencies",
                    "dataType": ["text[]"],
                    "description": "Lista de dependencias"
                },
                {
                    "name": "exports",
                    "dataType": ["text[]"],
                    "description": "Lista de exports del archivo"
                },
                {
                    "name": "imports",
                    "dataType": ["text[]"],
                    "description": "Lista de imports del archivo"
                },
                {
                    "name": "functions",
                    "dataType": ["text[]"],
                    "description": "Lista de funciones encontradas"
                },
                {
                    "name": "classes",
                    "dataType": ["text[]"],
                    "description": "Lista de clases encontradas"
                },
                {
                    "name": "endpoints",
                    "dataType": ["text[]"],
                    "description": "Lista de endpoints/URLs encontrados"
                },
                {
                    "name": "styles",
                    "dataType": ["text[]"],
                    "description": "Lista de estilos CSS/SCSS utilizados"
                },
                {
                    "name": "events",
                    "dataType": ["text[]"],
                    "description": "Lista de eventos manejados"
                },
                {
                    "name": "variables",
                    "dataType": ["text[]"],
                    "description": "Lista de variables importantes"
                },
                {
                    "name": "comments",
                    "dataType": ["text[]"],
                    "description": "Comentarios importantes del código"
                },
                {
                    "name": "relatedFiles",
                    "dataType": ["text[]"],
                    "description": "Archivos relacionados"
                },
                {
                    "name": "contentChunks",
                    "dataType": ["text[]"],
                    "description": "Chunks principales del contenido"
                },
                {
                    "name": "complexity",
                    "dataType": ["text"],
                    "description": "Nivel de complejidad (low, medium, high)"
                },
                {
                    "name": "linesOfCode",
                    "dataType": ["int"],
                    "description": "Número de líneas de código"
                },
                {
                    "name": "analysisDate",
                    "dataType": ["date"],
                    "description": "Fecha del análisis"
                },
                {
                    "name": "tags",
                    "dataType": ["text[]"],
                    "description": "Tags adicionales para categorización"
                }
            ]
        }
        
        try:
            self.weaviate_client.schema.create_class(schema)
            print(f"✅ Esquema creado para proyecto: {class_name}")
            return True
        except Exception as e:
            print(f"❌ Error creando esquema: {e}")
            return False

    def _sanitize_project_name(self, project_name: str) -> str:
        """
        Sanitiza el nombre del proyecto para usarlo como clase en Weaviate
        """
        # Reemplazar caracteres especiales y espacios
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', project_name)
        # Asegurarse de que empiece con letra
        if sanitized and not sanitized[0].isalpha():
            sanitized = f"Proj_{sanitized}"
        return sanitized or "UnknownProject"

    def _log(self, message: str, force: bool = False):
        """
        Log con soporte para verbose mode
        force=True siempre muestra el mensaje
        force=False solo muestra si verbose_mode=True o si es un mensaje importante
        """
        # Mensajes importantes que siempre se muestran
        important_prefixes = ['🚀', '✅', '❌', '📊', '🏁', '💾', '📦']
        is_important = force or any(message.startswith(prefix) for prefix in important_prefixes)
        
        # Mostrar si es importante o si está en modo verbose
        if is_important or self._verbose_mode:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def _setup_log_files(self, base_path: str, project_name: str, clear_existing: bool = False):
        """
        Configura los archivos de log separados para ignorados y no indexados
        """
        from pathlib import Path
        import os
        import glob
        
        # Crear el directorio base si no existe
        log_dir = Path(base_path)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Borrar archivos anteriores si se especifica
        if clear_existing:
            self._clear_existing_logs(log_dir, project_name)
        
        # Crear nombres de archivo con timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        project_safe = re.sub(r'[^a-zA-Z0-9_]', '_', project_name)
        
        ignored_file = log_dir / f"{project_safe}_ignored_{timestamp}.log"
        not_indexed_file = log_dir / f"{project_safe}_not_indexed_{timestamp}.log"
        
        try:
            self._log_files["ignored"] = open(ignored_file, 'w', encoding='utf-8')
            self._log_files["not_indexed"] = open(not_indexed_file, 'w', encoding='utf-8')
            self._log_files["enabled"] = True
            
            # Escribir headers
            self._write_log_header(self._log_files["ignored"], "ARCHIVOS IGNORADOS", project_name)
            self._write_log_header(self._log_files["not_indexed"], "ARCHIVOS NO INDEXADOS", project_name)
            
            self._log(f"📝 Archivos de log configurados:", force=True)
            self._log(f"   🚫 Ignorados: {ignored_file}", force=True)
            self._log(f"   ❌ No indexados: {not_indexed_file}", force=True)
            
        except Exception as e:
            self._log(f"⚠️ Error configurando archivos de log: {e}", force=True)
            self._log_files["enabled"] = False

    def _write_log_header(self, file_handle, log_type: str, project_name: str):
        """
        Escribe el header del archivo de log
        """
        header = f"""
{'='*60}
{log_type} - PROYECTO: {project_name}
{'='*60}
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Descripción: {log_type.lower()} durante el análisis del proyecto

FORMATO: [TIMESTAMP] RAZÓN: ruta_del_archivo
{'='*60}

"""
        file_handle.write(header)
        file_handle.flush()

    def _log_to_file(self, log_type: str, message: str):
        """
        Escribe un mensaje al archivo de log correspondiente
        log_type: 'ignored' o 'not_indexed'
        """
        if not self._log_files["enabled"] or log_type not in self._log_files:
            return
        
        file_handle = self._log_files[log_type]
        if file_handle:
            timestamp = datetime.now().strftime('%H:%M:%S')
            file_handle.write(f"[{timestamp}] {message}\n")
            file_handle.flush()

    def __del__(self):
        """
        Cerrar archivos de log al destruir el objeto
        """
        if hasattr(self, '_log_files') and self._log_files["enabled"]:
            for file_handle in [self._log_files["ignored"], self._log_files["not_indexed"]]:
                if file_handle:
                    try:
                        file_handle.close()
                    except:
                        pass

    def _clear_existing_logs(self, log_dir: Path, project_name: str):
        """
        Borra los archivos de log anteriores del proyecto
        """
        import glob
        
        project_safe = re.sub(r'[^a-zA-Z0-9_]', '_', project_name)
        
        # Patrones para buscar archivos del proyecto
        patterns = [
            f"{project_safe}_ignored_*.log",
            f"{project_safe}_not_indexed_*.log"
        ]
        
        deleted_count = 0
        for pattern in patterns:
            full_pattern = log_dir / pattern
            for file_path in glob.glob(str(full_pattern)):
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    self._log(f"🗑️  Eliminado log anterior: {os.path.basename(file_path)}")
                except Exception as e:
                    self._log(f"⚠️ No se pudo eliminar {file_path}: {e}")
        
        if deleted_count > 0:
            self._log(f"🧹 Eliminados {deleted_count} archivos de log anteriores", force=True)
        else:
            self._log(f"📝 No hay logs anteriores para eliminar", force=True)

    def _finalize_log_files(self):
        """
        Finaliza los archivos de log y muestra un resumen
        """
        if not self._log_files["enabled"]:
            return
        
        # Contar líneas en cada archivo
        ignored_count = 0
        not_indexed_count = 0
        
        # Escribir footer y contar líneas
        for log_type in ["ignored", "not_indexed"]:
            if self._log_files[log_type]:
                # Escribir footer
                footer = f"""
{'='*60}
RESUMEN FINAL
{'='*60}
Análisis completado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Para revisar este archivo:
- Busca patrones específicos de archivos que no esperabas ver aquí
- Verifica que los filtros estén funcionando correctamente
- Considera ajustar los criterios de filtrado si es necesario

{'='*60}
"""
                self._log_files[log_type].write(footer)
                self._log_files[log_type].close()
                
                # Contar líneas (aproximado)
                try:
                    if log_type == "ignored":
                        ignored_count = self._count_log_entries(self._log_files[log_type].name)
                    else:
                        not_indexed_count = self._count_log_entries(self._log_files[log_type].name)
                except:
                    pass
        
        # Mostrar resumen
        self._log(f"📝 Archivos de log finalizados:", force=True)
        self._log(f"   🚫 {ignored_count} archivos ignorados registrados", force=True)
        self._log(f"   ❌ {not_indexed_count} archivos no indexados registrados", force=True)
        
        self._log_files["enabled"] = False

    def _count_log_entries(self, file_path: str) -> int:
        """
        Cuenta las entradas de log (líneas que empiezan con [timestamp])
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                count = 0
                for line in f:
                    if line.strip().startswith('[') and ']' in line:
                        count += 1
                return count
        except:
            return 0

    def _should_index_file(self, file_path: str, relative_path: str, content: str) -> bool:
        """
        Decide si un archivo es relevante para indexar usando heurísticas inteligentes.
        """
        # Extensiones irrelevantes
        ignored_exts = [
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.bmp', '.tiff', '.webp',
            '.exe', '.dll', '.so', '.bin', '.obj', '.class', '.pyc', '.pyo', '.zip', '.tar', '.gz', '.rar', '.7z',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.mp3', '.mp4', '.avi', '.mov', '.mkv',
            '.log', '.tmp', '.bak', '.swp', '.lock', '.db', '.sqlite', '.woff', '.woff2', '.eot', '.ttf', '.otf',
            '.DS_Store', '.plist', '.sublime-workspace', '.sublime-project', '.iml', '.idea', '.vs', '.vscode', '.env', '.sample', '.test', '.spec'
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
        if len(content.strip()) < 5:
            reason = f"Archivo vacío o muy pequeño ({len(content)} bytes): {relative_path}"
            self._log(f"[IGNORADO] {reason}")
            self._log_to_file("ignored", reason)
            return False
        # Archivos binarios (contienen bytes no imprimibles)
        if '\x00' in content or not all(32 <= ord(c) <= 126 or c in '\n\r\t' for c in content[:100]):
            reason = f"Archivo binario o no texto: {relative_path}"
            self._log(f"[IGNORADO] {reason}")
            self._log_to_file("ignored", reason)
            return False
        # Archivos de backup o temporales
        if any(s in file_path.lower() for s in ['backup', 'bak', 'temp', 'tmp', '~', '#']):
            reason = f"Archivo temporal o backup: {relative_path}"
            self._log(f"[IGNORADO] {reason}")
            self._log_to_file("ignored", reason)
            return False
        # Carpetas irrelevantes en la ruta
        ignored_dirs = ['node_modules', 'bower_components', '.git', 'dist', 'build', 'coverage', 'nbproject', '.idea', '.vscode', '__pycache__']
        if any(f"{os.sep}{d}{os.sep}" in file_path for d in ignored_dirs):
            reason = f"Carpeta irrelevante en ruta: {relative_path}"
            self._log(f"[IGNORADO] {reason}")
            self._log_to_file("ignored", reason)
            return False
        # Si no contiene palabras clave de código fuente
        code_keywords = ['function', 'class', 'import', 'export', 'def ', 'var ', 'let ', 'const ', 'public ', 'private ', 'return', 'if ', 'else', 'for ', 'while ', '=>', 'template', 'script', 'style']
        if not any(kw in content for kw in code_keywords):
            reason = f"No parece código fuente: {relative_path}"
            self._log(f"[IGNORADO] {reason}")
            self._log_to_file("ignored", reason)
            return False
        return True

    def analyze_and_index_project(self, project_path: str, project_name: str = None, force_schema: bool = True) -> Dict:
        if project_name is None:
            project_name = os.path.basename(project_path)
        self._log(f"🚀 Iniciando análisis e indexación del proyecto: {project_name}", force=True)
        self._log(f"📁 Ruta: {project_path}", force=True)
        if force_schema:
            if not self.create_weaviate_schema(project_name):
                return {"error": "No se pudo crear el esquema en Weaviate"}
        project_analysis = self.analyze_project_structure(project_path)
        project_analysis["project_name"] = project_name
        project_analysis["analysis_date"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        indexed_files = 0
        errors = []
        start_time = time.time()
        file_times = []
        ignore_dirs = ['node_modules', 'bower_components', '.git', 'dist', 'build', 'coverage', 'nbproject']
        all_files = []
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ignore_dirs]
            for file in files:
                if file.startswith('.'):
                    continue
                file_path = os.path.join(root, file)
                # Normalizar rutas para usar siempre '/' como separador
                relative_path = os.path.relpath(file_path, project_path).replace('\\', '/')
                all_files.append((file_path, relative_path))
        total_files = len(all_files)
        for idx, (file_path, relative_path) in enumerate(all_files, 1):
            t0 = time.time()
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                reason = f"Error leyendo archivo: {relative_path} - {e}"
                self._log(f"⚠️  No se pudo leer: {relative_path}")
                self._log_to_file("not_indexed", reason)
                continue
            if not self._should_index_file(file_path, relative_path, content):
                continue
            self._log(f"🔍 Analizando archivo: {relative_path} ({idx}/{total_files})")
            try:
                ok = self._index_file(file_path, relative_path, project_name, project_analysis)
                if ok:
                    indexed_files += 1
                    self._log(f"✅ Indexado: {relative_path}")
                else:
                    reason = f"Archivo vacío o sin contenido relevante: {relative_path}"
                    self._log(f"⚠️  Archivo ignorado o vacío: {relative_path}")
                    self._log_to_file("not_indexed", reason)
            except Exception as e:
                error_msg = f"❌ Error en: {relative_path} - {e}"
                reason = f"Error durante indexación: {relative_path} - {e}"
                self._log(error_msg)
                self._log_to_file("not_indexed", reason)
                errors.append(error_msg)
            t1 = time.time()
            file_times.append(t1 - t0)
            avg_time = sum(file_times) / len(file_times)
            remaining = total_files - idx
            est_seconds = int(avg_time * remaining)
            est_min, est_sec = divmod(est_seconds, 60)
            self._log(f"⏳ Tiempo estimado restante: {est_min}m {est_sec}s")
        total_time = int(time.time() - start_time)
        min_total, sec_total = divmod(total_time, 60)
        self._log(f"🏁 Análisis completado en {min_total}m {sec_total}s. Archivos indexados: {indexed_files}/{total_files}", force=True)
        if errors:
            self._log(f"❗ Errores encontrados: {len(errors)}", force=True)
        
        # Finalizar archivos de log y mostrar resumen
        if self._log_files["enabled"]:
            self._finalize_log_files()
        project_summary = self._generate_project_summary(project_analysis)
        result = {
            "project_name": project_name,
            "project_path": project_path,
            "indexed_files": indexed_files,
            "total_files": project_analysis["total_files"],
            "technologies": project_analysis["technologies_detected"],
            "architecture_patterns": project_analysis["architecture_patterns"],
            "project_summary": project_summary,
            "errors": errors,
            "analysis_date": project_analysis["analysis_date"]
        }
        return result

    def _clean_list_field(self, field, field_name):
        cleaned = []
        for i, v in enumerate(field):
            try:
                s = str(v)
                if s and len(s) < 500:
                    cleaned.append(s)
                elif len(s) >= 500:
                    # En lugar de ignorar, dividir en chunks más pequeños
                    if field_name in ['relatedFiles', 'comments', 'functions', 'classes']:
                        # Para estos campos, crear resumen o truncar inteligentemente
                        if field_name == 'relatedFiles':
                            # Extraer solo nombres de archivos/rutas, ignorar contenido embebido
                            lines = s.split('\n')
                            file_refs = []
                            for line in lines:
                                if any(ext in line for ext in ['.js', '.ts', '.html', '.css', '.json', '.vue', '.jsx', '.tsx']):
                                    # Extraer referencias a archivos
                                    matches = re.findall(r'[\'"\'](.*?\.(?:js|ts|html|css|json|vue|jsx|tsx))[\'"\']', line)
                                    file_refs.extend(matches)
                            if file_refs:
                                cleaned.extend(file_refs[:10])  # Limitar a 10 referencias
                            else:
                                # Si no hay referencias de archivos, tomar un resumen
                                cleaned.append(s[:300] + "...")
                        elif field_name in ['comments']:
                            # Para comentarios, tomar los primeros 200 caracteres
                            cleaned.append(s[:200] + "...")
                        else:
                            # Para funciones y clases, dividir en chunks de 400 caracteres
                            for chunk_start in range(0, len(s), 400):
                                chunk = s[chunk_start:chunk_start+400]
                                if chunk.strip():
                                    cleaned.append(chunk)
                    else:
                        # Para otros campos, truncar con resumen
                        cleaned.append(s[:300] + "... [truncado]")
                    
                    self._log(f"[INFO] Valor largo en '{field_name}' procesado en chunks/resumen (era {len(s)} chars)")
            except Exception as e:
                self._log(f"[WARN] Valor no convertible a string en '{field_name}' (ignorado): {v} - {e}")
        return cleaned

    def _index_file(self, file_path: str, relative_path: str, project_name: str, project_context: Dict) -> bool:
        class_name = f"Project_{self._sanitize_project_name(project_name)}"
        # Normalizar ruta para consulta (asegurar que use '/' como separador)
        normalized_path = relative_path.replace('\\', '/')
        # Verificar si ya existe el archivo en Weaviate
        try:
            result = (
                self.weaviate_client.query
                .get(class_name, ["filePath", "projectName"])
                .with_where({
                    "operator": "And",
                    "operands": [
                        {"path": ["filePath"], "operator": "Equal", "valueString": normalized_path},
                        {"path": ["projectName"], "operator": "Equal", "valueString": project_name}
                    ]
                })
                .with_limit(1)
                .do()
            )
            if (
                "data" in result and "Get" in result["data"] and
                class_name in result["data"]["Get"] and
                len(result["data"]["Get"][class_name]) > 0
            ):
                self._log(f"indexacion ya existe, saltando... [{normalized_path}]")
                self._log_to_file("not_indexed", f"indexacion ya existe, saltando...: {normalized_path}")
                return True
        except Exception as e:
            self._log(f"[WARN] No se pudo verificar existencia previa en Weaviate para {normalized_path}: {e}")
        # ... existente ...
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            return False
        if len(content.strip()) == 0:
            return False
        file_analysis = self.analyze_file_complexity(file_path)
        file_ext = Path(file_path).suffix.lower()
        imports = self._extract_imports(content, file_ext)
        exports = self._extract_exports(content, file_ext)
        functions = self._extract_functions(content, file_ext)
        classes = self._extract_classes(content, file_ext)
        endpoints = self._extract_endpoints(content)
        styles = self._extract_styles(content, file_ext)
        events = self._extract_events(content, file_ext)
        variables = self._extract_variables(content, file_ext)
        comments = self._extract_comments(content, file_ext)
        summary = self._generate_file_summary(content, file_analysis, relative_path)
        module_type = self._determine_module_type(relative_path, content, file_analysis)
        technology = self._determine_file_technology(content, file_ext, project_context)
        # Crear chunks del contenido
        content_chunks = self._create_content_chunks(content, file_path)
        if len(content_chunks) > 5:
            self._log(f"📦 Archivo largo detectado, dividiéndolo en {len(content_chunks)} chunks")
        
        related_files = self._find_related_files(content, imports, exports)
        embedding = self._get_embedding(content[:15000])
        # Limpiar todos los campos tipo lista
        imports = self._clean_list_field(imports, 'imports')
        exports = self._clean_list_field(exports, 'exports')
        functions = self._clean_list_field(functions, 'functions')
        classes = self._clean_list_field(classes, 'classes')
        endpoints = self._clean_list_field(endpoints, 'endpoints')
        styles = self._clean_list_field(styles, 'styles')
        events = self._clean_list_field(events, 'events')
        variables = self._clean_list_field(variables, 'variables')
        comments = self._clean_list_field(comments, 'comments')
        related_files = self._clean_list_field(related_files, 'relatedFiles')
        data_object = {
            "projectName": project_name,
            "filePath": normalized_path,
            "fileName": os.path.basename(file_path),
            "fileType": file_ext,
            "moduleType": module_type,
            "technology": technology,
            "content": content[:15000],
            "summary": summary,
            "dependencies": imports,
            "exports": exports,
            "imports": imports,
            "functions": functions,
            "classes": classes,
            "endpoints": endpoints,
            "styles": styles,
            "events": events,
            "variables": variables,
            "comments": comments,
            "relatedFiles": related_files,
            "complexity": file_analysis.get("migration_difficulty", "unknown"),
            "linesOfCode": file_analysis.get("lines_of_code", 0),
            "analysisDate": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
            "tags": self._generate_tags(relative_path, file_analysis, module_type),
            "contentChunks": content_chunks[:5]
        }
        try:
            self.weaviate_client.data_object.create(
                data_object=data_object,
                class_name=class_name,
                vector=embedding
            )
            # Indexar chunks adicionales si existen
            additional_chunks = content_chunks[5:]
            if additional_chunks:
                self._log(f"💾 Guardando {len(additional_chunks)} chunks adicionales")
                self._index_file_chunks(additional_chunks, normalized_path, project_name, module_type, technology)
            
            return True
        except Exception as e:
            print(f"Error indexando {normalized_path}: {e}")
            return False

    def _create_content_chunks(self, content: str, file_path: str) -> List[str]:
        """
        Crea chunks inteligentes del contenido para análisis granular
        """
        chunks = []
        lines = content.split('\n')
        
        # Chunk 1: Imports y configuración inicial
        import_lines = [line for line in lines if any(keyword in line for keyword in ['import', 'require', 'from', 'link', 'script'])]
        if import_lines:
            chunks.append('\n'.join(import_lines))
        
        # Chunk 2: Definiciones de clases/componentes
        class_content = []
        in_class = False
        for line in lines:
            if any(keyword in line for keyword in ['class ', 'Component', 'dom-module', 'Polymer(']):
                in_class = True
                class_content.append(line)
            elif in_class and line.strip():
                class_content.append(line)
            elif in_class and not line.strip():
                break
        if class_content:
            chunks.append('\n'.join(class_content))
        
        # Chunk 3: Funciones principales
        function_content = []
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ['function ', 'const ', 'let ', 'var ', '=>']):
                # Tomar la función y algunas líneas de contexto
                start = max(0, i-1)
                end = min(len(lines), i+10)
                function_content.extend(lines[start:end])
        if function_content:
            chunks.append('\n'.join(function_content))
        
        # Chunk 4: Estilos y CSS
        style_content = []
        in_style = False
        for line in lines:
            if '<style>' in line or 'style=' in line:
                in_style = True
            elif '</style>' in line:
                in_style = False
            elif in_style or line.strip().startswith('.') or line.strip().startswith('#'):
                style_content.append(line)
        if style_content:
            chunks.append('\n'.join(style_content))
        
        # Chunk 5: HTML/Template
        template_content = []
        in_template = False
        for line in lines:
            if '<template>' in line or '<div' in line or '<dom-module' in line:
                in_template = True
                template_content.append(line)
            elif '</template>' in line or '</dom-module>' in line:
                template_content.append(line)
                in_template = False
            elif in_template:
                template_content.append(line)
        if template_content:
            chunks.append('\n'.join(template_content))
        
        # Chunk 6: Resto del contenido en bloques de 500 líneas
        remaining_content = content
        for chunk in chunks:
            remaining_content = remaining_content.replace(chunk, '')
        
        if remaining_content.strip():
            remaining_lines = remaining_content.split('\n')
            for i in range(0, len(remaining_lines), 500):
                chunk = '\n'.join(remaining_lines[i:i+500])
                if chunk.strip():
                    chunks.append(chunk)
        
        return chunks

    def _extract_events(self, content: str, file_ext: str) -> List[str]:
        """
        Extrae eventos del archivo
        """
        events = []
        
        if file_ext in ['.js', '.ts', '.jsx', '.tsx']:
            # Event listeners
            events.extend(re.findall(r'addEventListener\s*\(\s*[\'"]([^\'"]+)[\'"]', content))
            events.extend(re.findall(r'on(\w+)\s*=', content))
        elif file_ext == '.html':
            # HTML events
            events.extend(re.findall(r'on(\w+)=[\'"]([^\'"]+)[\'"]', content))
        
        return list(set(events))

    def _extract_variables(self, content: str, file_ext: str) -> List[str]:
        """
        Extrae variables importantes del archivo
        """
        variables = []
        
        if file_ext in ['.js', '.ts', '.jsx', '.tsx']:
            # Variables y constantes
            variables.extend(re.findall(r'(?:const|let|var)\s+(\w+)', content))
            # Propiedades de objetos
            variables.extend(re.findall(r'(\w+)\s*:', content))
        
        return list(set(variables))

    def _extract_comments(self, content: str, file_ext: str) -> List[str]:
        """
        Extrae comentarios importantes del archivo
        """
        comments = []
        
        # Comentarios de una línea
        comments.extend(re.findall(r'//\s*(.+)', content))
        # Comentarios de múltiples líneas
        comments.extend(re.findall(r'/\*\s*(.*?)\s*\*/', content, re.DOTALL))
        # Comentarios HTML
        if file_ext == '.html':
            comments.extend(re.findall(r'<!--\s*(.*?)\s*-->', content, re.DOTALL))
        
        # Filtrar comentarios importantes (más de 5 caracteres)
        important_comments = [comment.strip() for comment in comments if len(comment.strip()) > 5]
        
        return important_comments[:10]  # Solo los primeros 10 comentarios importantes

    def _find_related_files(self, content: str, imports: List[str], exports: List[str]) -> List[str]:
        """
        Encuentra archivos relacionados basándose en imports y referencias
        """
        related = []
        
        # Archivos importados
        for imp in imports:
            if not imp.startswith(('http', 'https', 'node_modules')):
                related.append(imp)
        
        # Referencias a otros archivos en comentarios o strings
        file_refs = re.findall(r'[\'"]([^\'\"]*\.(?:js|ts|html|css|scss)[^\'\"]*)[\'"]', content)
        related.extend([ref for ref in file_refs if not ref.startswith(('http', 'https'))])
        
        return list(set(related))

    def _index_file_chunks(self, chunks: List[str], file_path: str, project_name: str, module_type: str, technology: str):
        """
        Indexa chunks adicionales del archivo para análisis granular
        """
        class_name = f"Project_{self._sanitize_project_name(project_name)}_Chunks"
        
        # Crear esquema para chunks si no existe
        try:
            existing_schema = self.weaviate_client.schema.get()
            existing_classes = [cls['class'] for cls in existing_schema.get('classes', [])]
            
            if class_name not in existing_classes:
                chunk_schema = {
                    "class": class_name,
                    "description": f"Chunks detallados del proyecto {project_name}",
                    "vectorizer": "none",
                    "properties": [
                        {"name": "parentFile", "dataType": ["text"], "description": "Archivo padre"},
                        {"name": "chunkContent", "dataType": ["text"], "description": "Contenido del chunk"},
                        {"name": "chunkType", "dataType": ["text"], "description": "Tipo de chunk"},
                        {"name": "moduleType", "dataType": ["text"], "description": "Tipo de módulo"},
                        {"name": "technology", "dataType": ["text"], "description": "Tecnología"},
                        {"name": "projectName", "dataType": ["text"], "description": "Nombre del proyecto"}
                    ]
                }
                self.weaviate_client.schema.create_class(chunk_schema)
        except:
            pass  # Continuar si hay error en chunks adicionales
        
        # Indexar cada chunk con logging detallado
        for i, chunk in enumerate(chunks):
            if chunk.strip():
                chunk_number = i + 6  # Chunks adicionales empiezan en 6
                self._log(f"   📦 Guardando chunk {chunk_number} ({len(chunk)} caracteres)")
                
                chunk_data = {
                    "parentFile": file_path,
                    "chunkContent": chunk[:5000],  # Limitar tamaño del chunk
                    "chunkType": f"chunk_{chunk_number}",
                    "moduleType": module_type,
                    "technology": technology,
                    "projectName": project_name
                }
                embedding = self._get_embedding(chunk[:5000])
                try:
                    self.weaviate_client.data_object.create(
                        data_object=chunk_data,
                        class_name=class_name,
                        vector=embedding
                    )
                except Exception as e:
                    self._log(f"   ⚠️ Error guardando chunk {chunk_number}: {e}")
                    continue

    def _extract_imports(self, content: str, file_ext: str) -> List[str]:
        """
        Extrae los imports del archivo
        """
        imports = []
        
        if file_ext in ['.js', '.ts', '.jsx', '.tsx']:
            # ES6 imports
            imports.extend(re.findall(r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]', content))
            # CommonJS requires
            imports.extend(re.findall(r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)', content))
        elif file_ext == '.html':
            # HTML imports/links
            imports.extend(re.findall(r'<link.*?href=[\'"]([^\'"]+)[\'"]', content))
            imports.extend(re.findall(r'<script.*?src=[\'"]([^\'"]+)[\'"]', content))
        
        return list(set(imports))  # Eliminar duplicados

    def _extract_exports(self, content: str, file_ext: str) -> List[str]:
        """
        Extrae los exports del archivo
        """
        exports = []
        
        if file_ext in ['.js', '.ts', '.jsx', '.tsx']:
            # Export default
            exports.extend(re.findall(r'export\s+default\s+(\w+)', content))
            # Named exports
            exports.extend(re.findall(r'export\s+(?:const|let|var|function|class)\s+(\w+)', content))
            # Export destructuring
            matches = re.findall(r'export\s*\{\s*([^}]+)\s*\}', content)
            for match in matches:
                exports.extend([name.strip() for name in match.split(',')])
        
        return list(set(exports))

    def _extract_functions(self, content: str, file_ext: str) -> List[str]:
        """
        Extrae las funciones del archivo
        """
        functions = []
        
        if file_ext in ['.js', '.ts', '.jsx', '.tsx']:
            # Funciones normales
            functions.extend(re.findall(r'function\s+(\w+)', content))
            # Arrow functions asignadas a variables
            functions.extend(re.findall(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:\([^)]*\)|[^=])\s*=>', content))
            # Métodos de clase
            functions.extend(re.findall(r'(\w+)\s*\([^)]*\)\s*\{', content))
        
        return list(set(functions))

    def _extract_classes(self, content: str, file_ext: str) -> List[str]:
        """
        Extrae las clases del archivo
        """
        classes = []
        
        if file_ext in ['.js', '.ts', '.jsx', '.tsx']:
            classes.extend(re.findall(r'class\s+(\w+)', content))
        elif file_ext == '.html':
            # CSS classes
            classes.extend(re.findall(r'class=[\'"]([^\'"]+)[\'"]', content))
        
        return list(set(classes))

    def _extract_endpoints(self, content: str) -> List[str]:
        """
        Extrae endpoints/URLs del archivo
        """
        endpoints = []
        
        # URLs HTTP
        endpoints.extend(re.findall(r'https?://[^\s\'"]+', content))
        # Rutas de API
        endpoints.extend(re.findall(r'[\'"](?:/api/[^\'"]*|/[a-zA-Z][^\'"]*)[\'"]', content))
        # Llamadas a fetch/axios
        endpoints.extend(re.findall(r'(?:fetch|axios\.(?:get|post|put|delete))\s*\(\s*[\'"]([^\'"]+)[\'"]', content))
        
        return list(set(endpoints))

    def _extract_styles(self, content: str, file_ext: str) -> List[str]:
        """
        Extrae información de estilos del archivo
        """
        styles = []
        
        if file_ext in ['.css', '.scss', '.sass']:
            # Selectores CSS
            styles.extend(re.findall(r'\.([a-zA-Z][a-zA-Z0-9_-]*)\s*\{', content))
            # Variables CSS
            styles.extend(re.findall(r'--([a-zA-Z][a-zA-Z0-9_-]*)', content))
        elif file_ext == '.html':
            # Clases inline
            styles.extend(re.findall(r'class=[\'"]([^\'"]+)[\'"]', content))
        
        return list(set(styles))

    def _determine_module_type(self, file_path: str, content: str, analysis: Dict) -> str:
        """
        Determina el tipo de módulo basado en el análisis
        """
        path_lower = file_path.lower()
        
        # Basado en la ruta
        if 'component' in path_lower:
            return 'component'
        elif 'service' in path_lower:
            return 'service'
        elif 'model' in path_lower or 'entity' in path_lower:
            return 'model'
        elif 'util' in path_lower or 'helper' in path_lower:
            return 'utility'
        elif 'config' in path_lower:
            return 'configuration'
        elif 'test' in path_lower or 'spec' in path_lower:
            return 'test'
        elif 'style' in path_lower or file_path.endswith(('.css', '.scss')):
            return 'stylesheet'
        
        # Basado en el contenido
        if 'Component' in content or 'dom-module' in content:
            return 'component'
        elif 'service' in content.lower() or 'Service' in content:
            return 'service'
        elif 'router' in content.lower() or 'Router' in content:
            return 'router'
        
        return 'module'

    def _determine_file_technology(self, content: str, file_ext: str, project_context: Dict) -> str:
        """
        Determina la tecnología principal del archivo
        """
        # Buscar indicadores específicos en el contenido
        if 'Polymer' in content or 'dom-module' in content:
            return 'polymer'
        elif 'React' in content or 'useState' in content or 'JSX' in content:
            return 'react'
        elif '@Component' in content or 'Angular' in content:
            return 'angular'
        elif 'Vue' in content or file_ext == '.vue':
            return 'vue'
        
        # Usar la tecnología principal del proyecto
        technologies = project_context.get('technologies_detected', [])
        if technologies:
            return technologies[0]
        
        return 'unknown'

    def _generate_tags(self, file_path: str, analysis: Dict, module_type: str) -> List[str]:
        """
        Genera tags adicionales para el archivo
        """
        tags = [module_type]
        
        # Tags basados en la ruta
        path_parts = file_path.split(os.sep)
        tags.extend([part for part in path_parts if part not in ['.', '..']])
        
        # Tags basados en análisis
        if analysis.get('migration_difficulty') == 'high':
            tags.append('complex')
        elif analysis.get('migration_difficulty') == 'low':
            tags.append('simple')
        
        if analysis.get('lines_of_code', 0) > 500:
            tags.append('large')
        elif analysis.get('lines_of_code', 0) < 50:
            tags.append('small')
        
        return list(set(tags))

    def _generate_file_summary(self, content: str, analysis: Dict, file_path: str) -> str:
        """
        Genera un resumen del archivo usando IA
        """
        # Limitar el contenido para el análisis
        content_preview = content[:2000] if len(content) > 2000 else content
        
        prompt = f"""
Analiza este archivo de código y genera un resumen conciso:

ARCHIVO: {file_path}
ANÁLISIS: {json.dumps(analysis, indent=2)}

CONTENIDO:
{content_preview}

Genera un resumen que incluya:
1. Qué hace este archivo/módulo
2. Principales funcionalidades
3. Dependencias importantes
4. Complejidad y características técnicas

Responde en español y máximo 200 palabras.
"""
        
        summary = self._consultar_ollama(prompt)
        return summary if summary and not summary.startswith('[Error') else f"Archivo {os.path.basename(file_path)} - {analysis.get('lines_of_code', 0)} líneas"

    def _generate_project_summary(self, project_analysis: Dict) -> str:
        """
        Genera un resumen general del proyecto
        """
        prompt = f"""
Genera un resumen ejecutivo de este proyecto basado en el análisis:

{json.dumps(project_analysis, indent=2)}

El resumen debe incluir:
1. Descripción general del proyecto
2. Tecnologías principales utilizadas
3. Arquitectura y patrones detectados
4. Complejidad general
5. Recomendaciones para migración

Responde en español y máximo 300 palabras.
"""
        
        return self._consultar_ollama(prompt)

    def query_project(self, project_name: str, query: str, limit: int = 20) -> Dict:
        """
        Realiza una consulta semántica COMPLETA sobre un proyecto específico
        """
        if not self.weaviate_client:
            return {"error": "Weaviate no está disponible"}
        
        class_name = f"Project_{self._sanitize_project_name(project_name)}"
        chunks_class_name = f"Project_{self._sanitize_project_name(project_name)}_Chunks"
        
        try:
            # Consulta principal
            query_embedding = self._get_embedding(query)
            result = (
                self.weaviate_client.query
                .get(class_name, [
                    "projectName", "filePath", "fileName", "moduleType", 
                    "technology", "summary", "functions", "classes", 
                    "endpoints", "styles", "events", "variables", "comments",
                    "relatedFiles", "contentChunks", "complexity", "tags", "content"
                ])
                .with_near_vector({"vector": query_embedding})
                .with_limit(limit)
                .do()
            )
            
            files_found = []
            if 'data' in result and 'Get' in result['data']:
                files_found = result['data']['Get'].get(class_name, [])
            
            # Consulta en chunks para obtener más contexto
            chunks_found = []
            try:
                chunks_result = (
                    self.weaviate_client.query
                    .get(chunks_class_name, [
                        "parentFile", "chunkContent", "chunkType", 
                        "moduleType", "technology"
                    ])
                    .with_near_vector({"vector": query_embedding})
                    .with_limit(15)
                    .do()
                )
                
                if 'data' in chunks_result and 'Get' in chunks_result['data']:
                    chunks_found = chunks_result['data']['Get'].get(chunks_class_name, [])
            except:
                pass  # Continuar sin chunks si hay error
            
            # Combinar información para análisis completo
            complete_context = self._build_complete_context(files_found, chunks_found, query)
            
            # Generar respuesta usando TODO el contexto
            ai_response = self._generate_comprehensive_response(query, complete_context, project_name)
            
            return {
                "query": query,
                "project": project_name,
                "files_found": len(files_found),
                "chunks_found": len(chunks_found),
                "results": files_found,
                "chunks": chunks_found,
                "complete_context": complete_context,
                "ai_response": ai_response
            }
                
        except Exception as e:
            return {"error": f"Error en consulta: {e}"}

    def _build_complete_context(self, files_found: List[Dict], chunks_found: List[Dict], query: str) -> Dict:
        """
        Construye un contexto completo combinando archivos y chunks
        """
        context = {
            "main_files": [],
            "related_content": [],
            "all_functions": set(),
            "all_classes": set(),
            "all_endpoints": set(),
            "all_styles": set(),
            "all_events": set(),
            "all_variables": set(),
            "technologies": set(),
            "module_types": set(),
            "comments": [],
            "related_files": set()
        }
        
        # Procesar archivos principales
        for file_data in files_found:
            context["main_files"].append({
                "file": file_data.get("fileName", ""),
                "path": file_data.get("filePath", ""),
                "type": file_data.get("moduleType", ""),
                "technology": file_data.get("technology", ""),
                "summary": file_data.get("summary", ""),
                "complexity": file_data.get("complexity", "")
            })
            
            # Agregar todos los elementos encontrados
            context["all_functions"].update(file_data.get("functions", []))
            context["all_classes"].update(file_data.get("classes", []))
            context["all_endpoints"].update(file_data.get("endpoints", []))
            context["all_styles"].update(file_data.get("styles", []))
            context["all_events"].update(file_data.get("events", []))
            context["all_variables"].update(file_data.get("variables", []))
            context["technologies"].add(file_data.get("technology", ""))
            context["module_types"].add(file_data.get("moduleType", ""))
            context["comments"].extend(file_data.get("comments", []))
            context["related_files"].update(file_data.get("relatedFiles", []))
        
        # Procesar chunks adicionales
        for chunk in chunks_found:
            context["related_content"].append({
                "file": chunk.get("parentFile", ""),
                "type": chunk.get("chunkType", ""),
                "content": chunk.get("chunkContent", "")[:500]  # Primeros 500 chars
            })
        
        # Convertir sets a listas para JSON
        for key in ["all_functions", "all_classes", "all_endpoints", "all_styles", 
                    "all_events", "all_variables", "technologies", "module_types", "related_files"]:
            context[key] = list(context[key])
        
        return context

    def _generate_comprehensive_response(self, query: str, complete_context: Dict, project_name: str) -> str:
        """
        Genera una respuesta comprehensiva usando TODO el contexto disponible
        """
        context_summary = f"""
PROYECTO: {project_name}
CONSULTA: {query}

ARCHIVOS PRINCIPALES ENCONTRADOS:
{json.dumps(complete_context['main_files'], indent=2, ensure_ascii=False)}

FUNCIONES IDENTIFICADAS: {', '.join(complete_context['all_functions'][:20])}
CLASES IDENTIFICADAS: {', '.join(complete_context['all_classes'][:20])}
ENDPOINTS/APIs: {', '.join(complete_context['all_endpoints'][:20])}
ESTILOS CSS: {', '.join(complete_context['all_styles'][:20])}
EVENTOS: {', '.join(complete_context['all_events'][:20])}
VARIABLES IMPORTANTES: {', '.join(complete_context['all_variables'][:20])}

TECNOLOGÍAS UTILIZADAS: {', '.join(complete_context['technologies'])}
TIPOS DE MÓDULO: {', '.join(complete_context['module_types'])}

ARCHIVOS RELACIONADOS: {', '.join(complete_context['related_files'][:10])}

CONTENIDO ADICIONAL RELEVANTE:
{json.dumps(complete_context['related_content'][:5], indent=2, ensure_ascii=False)}

COMENTARIOS IMPORTANTES:
{'; '.join(complete_context['comments'][:10])}
"""
        
        prompt = f"""
Analiza COMPLETAMENTE este módulo/componente basándote en TODO el contexto disponible:

{context_summary}

Proporciona un análisis COMPLETO que incluya:

1. **RESUMEN GENERAL**: Qué hace este módulo/componente
2. **FUNCIONALIDAD PRINCIPAL**: Características y comportamiento clave
3. **ARQUITECTURA**: Cómo está estructurado el código
4. **DEPENDENCIAS**: Qué librerías, módulos o archivos necesita
5. **TECNOLOGÍA**: Framework/librería principal y versión si es posible
6. **ESTILOS**: Clases CSS, variables, y enfoque de estilizado
7. **EVENTOS Y INTERACCIONES**: Cómo maneja la interacción del usuario
8. **APIS Y ENDPOINTS**: Qué servicios consume o expone
9. **ESTADO Y DATOS**: Cómo maneja el estado interno y datos
10. **COMPLEJIDAD**: Nivel de dificultad para migrar/replicar
11. **ARCHIVOS RELACIONADOS**: Otros módulos que interactúan con este
12. **RECOMENDACIONES**: Cómo abordar una migración o creación similar

Responde en español de manera estructurada, técnica y COMPLETA. No omitas detalles importantes.
"""
        
        return self._consultar_ollama(prompt)

    def list_project_modules(self, project_name: str) -> Dict:
        """
        Lista todos los módulos/componentes de un proyecto
        """
        if not self.weaviate_client:
            return {"error": "Weaviate no está disponible"}
        
        class_name = f"Project_{self._sanitize_project_name(project_name)}"
        
        try:
            result = (
                self.weaviate_client.query
                .get(class_name, ["filePath", "fileName", "moduleType", "technology", "summary", "complexity"])
                .with_limit(100)
                .do()
            )
            
            if 'data' in result and 'Get' in result['data']:
                modules = result['data']['Get'].get(class_name, [])
                
                # Agrupar por tipo de módulo
                grouped = {}
                for module in modules:
                    module_type = module.get('moduleType', 'unknown')
                    if module_type not in grouped:
                        grouped[module_type] = []
                    grouped[module_type].append(module)
                
                return {
                    "project": project_name,
                    "total_modules": len(modules),
                    "modules_by_type": grouped,
                    "all_modules": modules
                }
            else:
                return {"error": "No se encontraron módulos"}
                
        except Exception as e:
            return {"error": f"Error listando módulos: {e}"}

    def generate_react_component(self, project_name: str, module_name: str, additional_requirements: str = "") -> str:
        """
        Genera un componente React basado en el análisis COMPLETO de un módulo existente
        """
        # Buscar información COMPLETA del módulo
        search_result = self.query_project(project_name, f"módulo {module_name} componente", limit=20)
        
        if 'complete_context' in search_result and search_result['complete_context']:
            complete_context = search_result['complete_context']
            
            # Construir contexto específico para generación de código
            code_context = self._build_code_generation_context(complete_context, search_result.get('results', []))
            
            prompt = f"""
Vas a generar un componente React COMPLETO basándote en el análisis exhaustivo del módulo "{module_name}" del proyecto "{project_name}".

CONTEXTO COMPLETO DEL MÓDULO ORIGINAL:
{json.dumps(code_context, indent=2, ensure_ascii=False)}

REQUISITOS ADICIONALES: {additional_requirements}

INSTRUCCIONES PARA LA GENERACIÓN:

1. **ANÁLISIS DEL MÓDULO ORIGINAL**: 
   - Tecnología original: {', '.join(complete_context.get('technologies', []))}
   - Tipos de módulo: {', '.join(complete_context.get('module_types', []))}
   - Funciones principales: {', '.join(complete_context.get('all_functions', [])[:10])}

2. **COMPONENTE REACT A GENERAR**:
   - Usar React moderno con hooks
   - Replicar TODA la funcionalidad identificada
   - Mantener la misma estructura lógica
   - Adaptar los estilos a CSS modules o styled-components
   - Convertir eventos y manejo de estado a React

3. **ESTRUCTURA REQUERIDA**:
   ```jsx
   import React, {{ useState, useEffect }} from 'react';
   // [otros imports necesarios]
   
   const ComponenteName = (props) => {{
     // [estado usando hooks]
     // [efectos si son necesarios]
     // [funciones del componente]
     // [manejo de eventos]
     
     return (
       // [JSX que replique la funcionalidad original]
     );
   }};
   
   export default ComponenteName;
   ```

4. **DEBE INCLUIR**:
   - ✅ Hooks de React (useState, useEffect, etc.)
   - ✅ PropTypes o interfaces TypeScript
   - ✅ Manejo de estado equivalente al original
   - ✅ Eventos convertidos a React (onClick, onChange, etc.)
   - ✅ Estilos CSS modernos
   - ✅ Llamadas a APIs si las había
   - ✅ Validaciones y lógica de negocio
   - ✅ Comentarios explicativos
   - ✅ Código completamente funcional

GENERA EL COMPONENTE REACT COMPLETO que replique TODA la funcionalidad encontrada en el módulo original. No omitas ninguna característica importante.
"""
            
            return self._consultar_ollama(prompt)
        else:
            return f"No se encontró información suficiente sobre el módulo '{module_name}' en el proyecto '{project_name}'"

    def _build_code_generation_context(self, complete_context: Dict, main_files: List[Dict]) -> Dict:
        """
        Construye un contexto específico optimizado para generación de código
        """
        code_context = {
            "original_technology": complete_context.get('technologies', []),
            "module_types": complete_context.get('module_types', []),
            "main_functionality": {
                "functions": complete_context.get('all_functions', []),
                "classes": complete_context.get('all_classes', []),
                "events": complete_context.get('all_events', []),
                "variables": complete_context.get('all_variables', [])
            },
            "ui_elements": {
                "styles": complete_context.get('all_styles', []),
                "related_files": complete_context.get('related_files', [])
            },
            "api_integration": {
                "endpoints": complete_context.get('all_endpoints', [])
            },
            "file_details": [],
            "code_samples": []
        }
        
        # Agregar detalles específicos de archivos
        for file_data in main_files:
            file_detail = {
                "file": file_data.get("fileName", ""),
                "path": file_data.get("filePath", ""),
                "type": file_data.get("moduleType", ""),
                "technology": file_data.get("technology", ""),
                "summary": file_data.get("summary", ""),
                "complexity": file_data.get("complexity", ""),
                "content_preview": file_data.get("content", "")[:1000] if file_data.get("content") else ""
            }
            code_context["file_details"].append(file_detail)
        
        # Agregar samples de código relevante
        for content_item in complete_context.get('related_content', []):
            if content_item.get('content'):
                code_context["code_samples"].append({
                    "file": content_item.get('file', ''),
                    "type": content_item.get('type', ''),
                    "code": content_item.get('content', '')
                })
        
        return code_context

    def migrate_module_to_technology(self, project_name: str, module_name: str, target_technology: str, additional_requirements: str = "") -> Dict:
        """
        Migra un módulo específico a una nueva tecnología con análisis completo
        """
        print(f"🚀 Iniciando migración del módulo '{module_name}' a {target_technology}...")
        
        # Paso 1: Obtener análisis completo del módulo original
        print("📊 1. Analizando módulo original...")
        analysis_result = self.query_project(project_name, f"módulo {module_name}", limit=30)
        
        if 'complete_context' not in analysis_result or not analysis_result['complete_context']:
            return {
                "error": f"No se encontró información suficiente sobre el módulo '{module_name}'",
                "suggestions": [
                    f"Verifica que el proyecto '{project_name}' esté indexado",
                    f"Prueba con términos de búsqueda alternativos como 'componente {module_name}' o '{module_name} component'"
                ]
            }
        
        # Paso 2: Generar código en la nueva tecnología
        print(f"⚛️ 2. Generando código en {target_technology}...")
        
        if target_technology.lower() == 'react':
            migrated_code = self.generate_react_component(project_name, module_name, additional_requirements)
        elif target_technology.lower() == 'vue':
            migrated_code = self._generate_vue_component(project_name, module_name, additional_requirements, analysis_result)
        elif target_technology.lower() == 'angular':
            migrated_code = self._generate_angular_component(project_name, module_name, additional_requirements, analysis_result)
        else:
            migrated_code = self._generate_generic_component(project_name, module_name, target_technology, additional_requirements, analysis_result)
        
        # Paso 3: Generar reporte de migración
        print("📋 3. Generando reporte de migración...")
        migration_report = self._generate_migration_report(analysis_result, target_technology, module_name)
        
        return {
            "module_name": module_name,
            "original_technology": ', '.join(analysis_result['complete_context'].get('technologies', [])),
            "target_technology": target_technology,
            "analysis_summary": analysis_result.get('ai_response', ''),
            "migrated_code": migrated_code,
            "migration_report": migration_report,
            "files_analyzed": analysis_result.get('files_found', 0),
            "chunks_analyzed": analysis_result.get('chunks_found', 0),
            "complexity": self._assess_migration_complexity(analysis_result),
            "recommendations": self._generate_migration_recommendations(analysis_result, target_technology)
        }

    def _generate_vue_component(self, project_name: str, module_name: str, requirements: str, analysis_result: Dict) -> str:
        """Genera un componente Vue basado en el análisis"""
        context = analysis_result.get('complete_context', {})
        
        prompt = f"""
Genera un componente Vue 3 COMPLETO basándote en el análisis del módulo "{module_name}":

CONTEXTO ORIGINAL:
{json.dumps(context, indent=2, ensure_ascii=False)}

REQUISITOS: {requirements}

El componente Vue debe incluir:
1. <template> con la estructura HTML
2. <script setup> con lógica de Vue 3
3. <style scoped> con estilos
4. Reactive data con ref/reactive
5. Computed properties si es necesario
6. Methods para funcionalidad
7. Lifecycle hooks si es necesario

Genera el componente Vue completo y funcional.
"""
        return self._consultar_ollama(prompt)

    def _generate_angular_component(self, project_name: str, module_name: str, requirements: str, analysis_result: Dict) -> str:
        """Genera un componente Angular basado en el análisis"""
        context = analysis_result.get('complete_context', {})
        
        prompt = f"""
Genera un componente Angular COMPLETO basándote en el análisis del módulo "{module_name}":

CONTEXTO ORIGINAL:
{json.dumps(context, indent=2, ensure_ascii=False)}

REQUISITOS: {requirements}

El componente Angular debe incluir:
1. @Component decorator con selector, template y styles
2. Class con propiedades y métodos
3. Lifecycle hooks (ngOnInit, etc.)
4. Data binding y event handling
5. Services injection si es necesario
6. Interfaces TypeScript
7. Template HTML separado
8. CSS separado

Genera el componente Angular completo (.ts, .html, .css).
"""
        return self._consultar_ollama(prompt)

    def _generate_generic_component(self, project_name: str, module_name: str, target_tech: str, requirements: str, analysis_result: Dict) -> str:
        """Genera un componente en cualquier tecnología"""
        context = analysis_result.get('complete_context', {})
        
        prompt = f"""
Genera un componente en {target_tech} basándote en el análisis del módulo "{module_name}":

CONTEXTO ORIGINAL:
{json.dumps(context, indent=2, ensure_ascii=False)}

REQUISITOS: {requirements}

Adapta toda la funcionalidad encontrada a {target_tech} siguiendo las mejores prácticas de esta tecnología.
"""
        return self._consultar_ollama(prompt)

    def _generate_migration_report(self, analysis_result: Dict, target_tech: str, module_name: str) -> str:
        """Genera un reporte detallado de la migración"""
        context = analysis_result.get('complete_context', {})
        
        prompt = f"""
Genera un REPORTE DE MIGRACIÓN detallado para el módulo "{module_name}" hacia {target_tech}:

ANÁLISIS ORIGINAL:
{json.dumps(context, indent=2, ensure_ascii=False)}

El reporte debe incluir:
1. **RESUMEN DE MIGRACIÓN**: Qué se está migrando y hacia dónde
2. **CAMBIOS PRINCIPALES**: Diferencias clave entre tecnologías
3. **FUNCIONALIDADES MIGRADAS**: Lista de características transferidas
4. **DEPENDENCIAS NECESARIAS**: Qué librerías instalar
5. **CONFIGURACIÓN REQUERIDA**: Setup del entorno
6. **PRUEBAS RECOMENDADAS**: Cómo verificar que funciona
7. **POSIBLES PROBLEMAS**: Qué vigilar durante la migración
8. **PASOS SIGUIENTES**: Qué hacer después de implementar

Responde en español de manera estructurada y técnica.
"""
        return self._consultar_ollama(prompt)

    def _assess_migration_complexity(self, analysis_result: Dict) -> str:
        """Evalúa la complejidad de la migración"""
        context = analysis_result.get('complete_context', {})
        
        # Factores de complejidad
        functions_count = len(context.get('all_functions', []))
        endpoints_count = len(context.get('all_endpoints', []))
        styles_count = len(context.get('all_styles', []))
        events_count = len(context.get('all_events', []))
        files_count = analysis_result.get('files_found', 0)
        
        complexity_score = (
            functions_count * 2 +
            endpoints_count * 3 +
            styles_count * 1 +
            events_count * 2 +
            files_count * 1
        )
        
        if complexity_score < 10:
            return "Baja - Migración directa"
        elif complexity_score < 30:
            return "Media - Requiere atención en algunos aspectos"
        else:
            return "Alta - Migración compleja, revisar paso a paso"

    def _generate_migration_recommendations(self, analysis_result: Dict, target_tech: str) -> List[str]:
        """Genera recomendaciones específicas para la migración"""
        context = analysis_result.get('complete_context', {})
        recommendations = []
        
        # Recomendaciones basadas en tecnología destino
        if target_tech.lower() == 'react':
            recommendations.extend([
                "Convertir eventos DOM a eventos React (onClick, onChange, etc.)",
                "Migrar estado local a useState hooks",
                "Convertir lifecycle methods a useEffect",
                "Adaptar estilos a CSS modules o styled-components"
            ])
        elif target_tech.lower() == 'vue':
            recommendations.extend([
                "Usar Vue 3 Composition API para mejor organización",
                "Convertir eventos a @click, @change syntax",
                "Migrar estado a reactive/ref",
                "Usar scoped styles en el componente"
            ])
        elif target_tech.lower() == 'angular':
            recommendations.extend([
                "Implementar interfaces TypeScript para type safety",
                "Usar servicios para lógica de negocio compartida",
                "Implementar lifecycle hooks apropiados",
                "Seguir Angular style guide para naming conventions"
            ])
        
        # Recomendaciones basadas en funcionalidades encontradas
        if context.get('all_endpoints'):
            recommendations.append("Implementar manejo de APIs con la librería HTTP de la nueva tecnología")
        
        if context.get('all_styles'):
            recommendations.append("Revisar y adaptar todos los estilos CSS al nuevo framework")
        
        if len(context.get('all_functions', [])) > 10:
            recommendations.append("Considerar dividir funcionalidades en múltiples componentes")
        
        return recommendations

    def delete_project_data(self, project_name: str) -> bool:
        """
        Elimina todos los datos de un proyecto de Weaviate
        """
        if not self.weaviate_client:
            return False
        
        class_name = f"Project_{self._sanitize_project_name(project_name)}"
        
        try:
            self.weaviate_client.schema.delete_class(class_name)
            print(f"✅ Datos del proyecto '{project_name}' eliminados de Weaviate")
            return True
        except Exception as e:
            print(f"❌ Error eliminando proyecto: {e}")
            return False

    def analyze_project_structure(self, project_path: str) -> Dict:
        """
        Analiza la estructura completa del proyecto
        """
        print(f"🔍 Analizando estructura del proyecto: {project_path}")
        
        structure = {
            "total_files": 0,
            "total_lines": 0,
            "file_types": {},
            "directories": [],
            "technologies_detected": [],
            "entry_points": [],
            "config_files": [],
            "dependencies": {},
            "architecture_patterns": []
        }
        
        # Recorrer todos los archivos
        for root, dirs, files in os.walk(project_path):
            # Ignorar node_modules, .git, etc.
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', 'dist', 'build']]
            
            structure["directories"].append(root)
            
            for file in files:
                if file.startswith('.'):
                    continue
                    
                file_path = os.path.join(root, file)
                file_ext = Path(file).suffix.lower()
                
                structure["total_files"] += 1
                structure["file_types"][file_ext] = structure["file_types"].get(file_ext, 0) + 1
                
                # Contar líneas
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len(f.readlines())
                        structure["total_lines"] += lines
                except:
                    continue
                
                # Detectar archivos importantes
                if file in ['package.json', 'bower.json', 'angular.json', 'tsconfig.json', 'webpack.config.js']:
                    structure["config_files"].append(file_path)
                
                if file in ['index.html', 'main.js', 'app.js', 'index.js']:
                    structure["entry_points"].append(file_path)
        
        # Detectar tecnologías
        structure["technologies_detected"] = self._detect_technologies(project_path)
        
        # Analizar dependencias
        structure["dependencies"] = self._analyze_dependencies(project_path)
        
        # Detectar patrones arquitectónicos
        structure["architecture_patterns"] = self._detect_architecture_patterns(project_path)
        
        return structure

    def _detect_technologies(self, project_path: str) -> List[str]:
        """
        Detecta qué tecnologías se están usando en el proyecto
        """
        detected = []
        
        for tech, patterns in self.tech_patterns.items():
            score = 0
            
            # Buscar por extensiones de archivo
            for root, dirs, files in os.walk(project_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules']]
                
                for file in files:
                    if Path(file).suffix.lower() in patterns["extensions"]:
                        score += 1
                    
                    # Buscar keywords en el contenido
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            for keyword in patterns["keywords"]:
                                score += content.count(keyword)
                    except:
                        continue
            
            if score > 10:  # Umbral para considerar que la tecnología está presente
                detected.append(tech)
        
        return detected

    def _analyze_dependencies(self, project_path: str) -> Dict:
        """
        Analiza las dependencias del proyecto
        """
        dependencies = {
            "package_json": {},
            "bower_json": {},
            "requirements_txt": [],
            "other": []
        }
        
        # Analizar package.json
        package_json_path = os.path.join(project_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    dependencies["package_json"] = {
                        "dependencies": package_data.get("dependencies", {}),
                        "devDependencies": package_data.get("devDependencies", {})
                    }
            except:
                pass
        
        # Analizar bower.json
        bower_json_path = os.path.join(project_path, "bower.json")
        if os.path.exists(bower_json_path):
            try:
                with open(bower_json_path, 'r', encoding='utf-8') as f:
                    bower_data = json.load(f)
                    dependencies["bower_json"] = bower_data.get("dependencies", {})
            except:
                pass
        
        return dependencies

    def _detect_architecture_patterns(self, project_path: str) -> List[str]:
        """
        Detecta patrones arquitectónicos en el proyecto
        """
        patterns = []
        
        # Buscar patrones comunes
        pattern_indicators = {
            "MVC": ["models", "views", "controllers"],
            "Component-Based": ["components", "widgets", "elements"],
            "Modular": ["modules", "libs", "packages"],
            "Layered": ["services", "repositories", "entities"],
            "Micro-Frontend": ["apps", "microfrontends", "federation"]
        }
        
        dir_names = []
        for root, dirs, files in os.walk(project_path):
            dir_names.extend([d.lower() for d in dirs])
        
        for pattern, indicators in pattern_indicators.items():
            if any(indicator in dir_names for indicator in indicators):
                patterns.append(pattern)
        
        return patterns

    def analyze_file_complexity(self, file_path: str) -> Dict:
        """
        Analiza la complejidad de un archivo específico
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            analysis = {
                "file_path": file_path,
                "lines_of_code": len(content.splitlines()),
                "functions_count": 0,
                "classes_count": 0,
                "imports_count": 0,
                "complexity_score": 0,
                "migration_difficulty": "low",
                "key_patterns": []
            }
            
            # Análisis básico por extensión
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in ['.js', '.ts']:
                analysis.update(self._analyze_javascript_file(content))
            elif file_ext in ['.html']:
                analysis.update(self._analyze_html_file(content))
            elif file_ext in ['.css', '.scss']:
                analysis.update(self._analyze_css_file(content))
            
            # Calcular dificultad de migración
            analysis["migration_difficulty"] = self._calculate_migration_difficulty(analysis)
            
            return analysis
            
        except Exception as e:
            return {"error": str(e), "file_path": file_path}

    def _analyze_javascript_file(self, content: str) -> Dict:
        """
        Análisis específico para archivos JavaScript/TypeScript
        """
        analysis = {
            "functions_count": len(re.findall(r'function\s+\w+|=>\s*{|\w+\s*:\s*function', content)),
            "classes_count": len(re.findall(r'class\s+\w+', content)),
            "imports_count": len(re.findall(r'import\s+.*from|require\s*\(', content)),
            "key_patterns": []
        }
        
        # Detectar patrones específicos
        if 'Polymer(' in content or 'PolymerElement' in content:
            analysis["key_patterns"].append("Polymer Component")
        
        if 'React.Component' in content or 'useState' in content:
            analysis["key_patterns"].append("React Component")
        
        if '@Component' in content:
            analysis["key_patterns"].append("Angular Component")
        
        return analysis

    def _analyze_html_file(self, content: str) -> Dict:
        """
        Análisis específico para archivos HTML
        """
        analysis = {
            "dom_modules": len(re.findall(r'<dom-module', content)),
            "custom_elements": len(re.findall(r'<\w+-\w+', content)),
            "polymer_elements": len(re.findall(r'<(iron-|paper-|neon-|gold-)', content)),
            "key_patterns": []
        }
        
        if analysis["dom_modules"] > 0:
            analysis["key_patterns"].append("Polymer DOM Module")
        
        if analysis["polymer_elements"] > 0:
            analysis["key_patterns"].append("Polymer Elements")
        
        return analysis

    def _analyze_css_file(self, content: str) -> Dict:
        """
        Análisis específico para archivos CSS/SCSS
        """
        analysis = {
            "css_rules": len(re.findall(r'[^{}]+\s*{', content)),
            "css_variables": len(re.findall(r'--\w+:', content)),
            "mixins": len(re.findall(r'@mixin|@include', content)),
            "key_patterns": []
        }
        
        if analysis["css_variables"] > 0:
            analysis["key_patterns"].append("CSS Variables")
        
        if analysis["mixins"] > 0:
            analysis["key_patterns"].append("SCSS Mixins")
        
        return analysis

    def _calculate_migration_difficulty(self, analysis: Dict) -> str:
        """
        Calcula la dificultad de migración basada en el análisis
        """
        score = 0
        
        # Factores que aumentan la dificultad
        score += analysis.get("lines_of_code", 0) / 100
        score += analysis.get("functions_count", 0) * 2
        score += analysis.get("classes_count", 0) * 3
        score += len(analysis.get("key_patterns", [])) * 5
        
        if score < 10:
            return "low"
        elif score < 30:
            return "medium"
        else:
            return "high"

    def generate_migration_report(self, project_analysis: Dict) -> str:
        """
        Genera un reporte de migración usando Ollama
        """
        prompt = f"""
Analiza este proyecto y genera un plan de migración detallado:

ESTRUCTURA DEL PROYECTO:
- Total de archivos: {project_analysis['total_files']}
- Total de líneas: {project_analysis['total_lines']}
- Tecnologías detectadas: {', '.join(project_analysis['technologies_detected'])}
- Patrones arquitectónicos: {', '.join(project_analysis['architecture_patterns'])}
- Tipos de archivo: {json.dumps(project_analysis['file_types'], indent=2)}

DEPENDENCIAS:
{json.dumps(project_analysis['dependencies'], indent=2)}

Genera un plan de migración que incluya:
1. Estrategia de migración (incremental vs completa)
2. Orden de migración de componentes
3. Mapeo de dependencias
4. Riesgos identificados
5. Estimación de tiempo
6. Pasos específicos

Responde en español y sé específico y técnico.
"""
        
        return self._consultar_ollama(prompt)

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