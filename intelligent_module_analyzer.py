#!/usr/bin/env python3
"""
Analizador Inteligente de Módulos - Sigue dependencias reales
"""

from samara.code_analysis_agent import CodeAnalysisAgent
import re
import os
from typing import Set, Dict, List

class IntelligentModuleAnalyzer:
    def __init__(self):
        self.agent = CodeAnalysisAgent()
        self.visited_files = set()  # Para evitar loops infinitos
        self.module_files = {}      # Cache de archivos encontrados
        self.dependency_graph = {}  # Grafo de dependencias
        
    def analyze_complete_module(self, module_name: str, project_name: str = "sacs3") -> Dict:
        """
        Analiza un módulo completo siguiendo todas sus dependencias
        """
        print(f"🧠 Analizando módulo completo: {module_name}")
        
        # PASO 1: Buscar archivo principal del módulo
        main_file = self._find_main_file(module_name, project_name)
        if not main_file:
            return {"error": f"No se encontró archivo principal para {module_name}"}
        
        print(f"🎯 Archivo principal encontrado: {main_file['fileName']}")
        
        # PASO 2: Construir grafo de dependencias completo
        self.visited_files.clear()
        self.module_files.clear()
        self.dependency_graph.clear()
        
        self._build_dependency_graph(main_file, project_name, level=0)
        
        # PASO 3: Organizar resultados
        result = self._organize_module_analysis()
        
        return result
    
    def _find_main_file(self, module_name: str, project_name: str) -> Dict:
        """
        Busca el archivo principal del módulo (index.html, main.js, etc.)
        """
        class_name = f"Project_{project_name}"
        
        # Buscar archivos principales típicos
        main_file_patterns = ["index.html", "main.js", "app.js", f"{module_name}.html"]
        
        for pattern in main_file_patterns:
            try:
                result = (
                    self.agent.weaviate_client.query
                    .get(class_name, [
                        "projectName", "filePath", "fileName", "content", 
                        "imports", "exports", "summary", "functions"
                    ])
                    .with_where({
                        "operator": "And",
                        "operands": [
                            {"path": ["filePath"], "operator": "Like", "valueString": f"*{module_name}*"},
                            {"path": ["fileName"], "operator": "Equal", "valueString": pattern}
                        ]
                    })
                    .with_limit(1)
                    .do()
                )
                
                if 'data' in result and 'Get' in result['data']:
                    files = result['data']['Get'].get(class_name, [])
                    if files:
                        return files[0]
            except Exception as e:
                print(f"⚠️ Error buscando {pattern}: {e}")
        
        # Si no encuentra archivo principal específico, buscar cualquier archivo del módulo
        try:
            result = (
                self.agent.weaviate_client.query
                .get(class_name, [
                    "projectName", "filePath", "fileName", "content", 
                    "imports", "exports", "summary", "functions"
                ])
                .with_where({
                    "path": ["filePath"], 
                    "operator": "Like", 
                    "valueString": f"*{module_name}*"
                })
                .with_limit(1)
                .do()
            )
            
            if 'data' in result and 'Get' in result['data']:
                files = result['data']['Get'].get(class_name, [])
                if files:
                    return files[0]
        except Exception as e:
            print(f"❌ Error en búsqueda general: {e}")
        
        return None
    
    def _build_dependency_graph(self, file_data: Dict, project_name: str, level: int = 0):
        """
        Construye recursivamente el grafo de dependencias
        """
        file_path = file_data.get('filePath', '')
        file_name = file_data.get('fileName', '')
        
        # Evitar loops infinitos
        if file_path in self.visited_files:
            return
        
        self.visited_files.add(file_path)
        self.module_files[file_path] = file_data
        
        indent = "  " * level
        print(f"{indent}📄 Analizando: {file_name}")
        
        # Extraer imports del archivo
        imports = self._extract_all_imports(file_data)
        self.dependency_graph[file_path] = imports
        
        if imports:
            print(f"{indent}📦 Dependencias encontradas: {len(imports)}")
            
            # Buscar cada dependencia en Weaviate
            for import_path in imports:
                dependency_file = self._find_file_by_import(import_path, project_name)
                if dependency_file:
                    print(f"{indent}  ↳ ✅ {dependency_file['fileName']}")
                    # Recursión para analizar dependencias de las dependencias
                    self._build_dependency_graph(dependency_file, project_name, level + 1)
                else:
                    print(f"{indent}  ↳ ❌ No encontrado: {import_path}")
        else:
            print(f"{indent}📦 Sin dependencias")
    
    def _extract_all_imports(self, file_data: Dict) -> List[str]:
        """
        Extrae TODOS los imports/referencias de un archivo
        """
        content = file_data.get('content', '')
        stored_imports = file_data.get('imports', [])
        
        all_imports = set(stored_imports) if stored_imports else set()
        
        # Patterns adicionales para extraer imports
        import_patterns = [
            # JavaScript/HTML imports
            r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
            r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)',
            # HTML links y scripts
            r'<link.*?href=[\'"]([^\'"]+)[\'"]',
            r'<script.*?src=[\'"]([^\'"]+)[\'"]',
            # Polymer specific
            r'<link.*?import.*?href=[\'"]([^\'"]+)[\'"]',
            # Relative file references
            r'[\'"](\./[^\'"]+\.(?:js|html|css))[\'"]',
            r'[\'"](\.\./[^\'"]+\.(?:js|html|css))[\'"]',
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            all_imports.update(matches)
        
        # Filtrar imports irrelevantes
        filtered_imports = []
        for imp in all_imports:
            if imp and not any(skip in imp.lower() for skip in [
                'http', 'https', 'node_modules', 'bower_components', 'cdn.',
                'googleapis.com', 'polymer-project.org'
            ]):
                # Normalizar rutas relativas
                normalized = self._normalize_import_path(imp)
                if normalized:
                    filtered_imports.append(normalized)
        
        return filtered_imports
    
    def _normalize_import_path(self, import_path: str) -> str:
        """
        Normaliza rutas de import para búsqueda
        """
        # Remover ./ y ../ del inicio
        normalized = import_path.replace('./', '').replace('../', '')
        
        # Si no tiene extensión, asumir .html para Polymer
        if not normalized.endswith(('.js', '.html', '.css')):
            if 'css' in normalized:
                normalized += '.css'
            elif 'js' in normalized:
                normalized += '.js'
            else:
                normalized += '.html'
        
        return normalized
    
    def _find_file_by_import(self, import_path: str, project_name: str) -> Dict:
        """
        Busca un archivo en Weaviate basado en el path de import
        """
        class_name = f"Project_{project_name}"
        
        # Buscar por path exacto primero
        search_patterns = [
            import_path,                                    # Exacto
            f"*{import_path}",                             # Contiene al final
            f"*{os.path.basename(import_path)}",           # Solo nombre archivo
            f"*{import_path.split('/')[-1]}",              # Último segmento
        ]
        
        for pattern in search_patterns:
            try:
                result = (
                    self.agent.weaviate_client.query
                    .get(class_name, [
                        "projectName", "filePath", "fileName", "content", 
                        "imports", "exports", "summary", "functions"
                    ])
                    .with_where({
                        "path": ["filePath"], 
                        "operator": "Like", 
                        "valueString": pattern
                    })
                    .with_limit(1)
                    .do()
                )
                
                if 'data' in result and 'Get' in result['data']:
                    files = result['data']['Get'].get(class_name, [])
                    if files:
                        return files[0]
            except Exception as e:
                continue
        
        return None
    
    def _organize_module_analysis(self) -> Dict:
        """
        Organiza los resultados del análisis en un formato útil
        """
        # Separar archivos por tipo
        html_files = []
        js_files = []
        css_files = []
        other_files = []
        
        for file_path, file_data in self.module_files.items():
            file_name = file_data.get('fileName', '')
            
            if file_name.endswith('.html'):
                html_files.append(file_data)
            elif file_name.endswith('.js'):
                js_files.append(file_data)
            elif file_name.endswith('.css'):
                css_files.append(file_data)
            else:
                other_files.append(file_data)
        
        # Extraer todas las funcionalidades
        all_functions = set()
        all_endpoints = set()
        all_styles = set()
        
        for file_data in self.module_files.values():
            functions = file_data.get('functions', [])
            endpoints = file_data.get('endpoints', [])
            styles = file_data.get('styles', [])
            
            if functions:
                all_functions.update(functions)
            if endpoints:
                all_endpoints.update(endpoints)
            if styles:
                all_styles.update(styles)
        
        return {
            "total_files": len(self.module_files),
            "files_by_type": {
                "html": len(html_files),
                "javascript": len(js_files),
                "css": len(css_files),
                "other": len(other_files)
            },
            "all_files": list(self.module_files.values()),
            "html_files": html_files,
            "js_files": js_files,
            "css_files": css_files,
            "other_files": other_files,
            "dependency_graph": self.dependency_graph,
            "all_functions": list(all_functions),
            "all_endpoints": list(all_endpoints),
            "all_styles": list(all_styles),
            "visited_paths": list(self.visited_files)
        }

def test_conteo_fisico_intelligent():
    """
    Prueba el análisis inteligente del módulo conteoFisico
    """
    analyzer = IntelligentModuleAnalyzer()
    
    print("🧠 ANÁLISIS INTELIGENTE DEL MÓDULO CONTEO FÍSICO")
    print("=" * 60)
    
    result = analyzer.analyze_complete_module("conteoFisico")
    
    if "error" in result:
        print(f"❌ {result['error']}")
        return
    
    print(f"\n📊 RESUMEN COMPLETO:")
    print(f"   📦 Total archivos: {result['total_files']}")
    print(f"   🌐 HTML: {result['files_by_type']['html']}")
    print(f"   ⚙️  JavaScript: {result['files_by_type']['javascript']}")
    print(f"   🎨 CSS: {result['files_by_type']['css']}")
    print(f"   📄 Otros: {result['files_by_type']['other']}")
    
    print(f"\n🔧 FUNCIONALIDADES ({len(result['all_functions'])}):")
    for func in result['all_functions'][:10]:
        print(f"   • {func}")
    
    print(f"\n🌐 ENDPOINTS ({len(result['all_endpoints'])}):")
    for endpoint in result['all_endpoints'][:5]:
        print(f"   • {endpoint}")
    
    print(f"\n📋 ARCHIVOS PRINCIPALES:")
    for file_data in result['all_files'][:5]:
        print(f"   📄 {file_data.get('fileName')} - {file_data.get('filePath')}")
    
    print(f"\n🔗 GRAFO DE DEPENDENCIAS:")
    for file_path, deps in result['dependency_graph'].items():
        file_name = os.path.basename(file_path)
        print(f"   📄 {file_name}")
        for dep in deps[:3]:  # Solo primeras 3 dependencias
            print(f"      ↳ {dep}")
        if len(deps) > 3:
            print(f"      ↳ ... y {len(deps) - 3} más")
    
    return result

if __name__ == "__main__":
    test_conteo_fisico_intelligent() 