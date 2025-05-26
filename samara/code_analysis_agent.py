import os
import ast
import json
import requests
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import re

class CodeAnalysisAgent:
    """
    Agente especializado en análisis profundo de código para migración masiva.
    Analiza estructura, dependencias, patrones y arquitectura.
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        
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