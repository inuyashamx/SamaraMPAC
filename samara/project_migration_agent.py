import os
import json
import time
from typing import List, Dict, Optional
from pathlib import Path
from code_analysis_agent import CodeAnalysisAgent
from code_migration_agent import CodeMigrationAgent

class ProjectMigrationAgent:
    """
    Agente principal que orquesta la migración completa de proyectos masivos.
    Coordina análisis, planificación y ejecución de migración.
    """
    
    def __init__(self, ollama_url: str = "http://localhost:11434"):
        self.ollama_url = ollama_url
        self.analysis_agent = CodeAnalysisAgent(ollama_url)
        self.migration_agent = CodeMigrationAgent(ollama_url)
        
        # Configuración de migración
        self.migration_config = {
            "batch_size": 10,  # Archivos por lote
            "max_file_size": 50000,  # Tamaño máximo de archivo en caracteres
            "priority_extensions": [".js", ".ts", ".jsx", ".tsx", ".html", ".vue"],
            "ignore_patterns": [
                "node_modules", ".git", "dist", "build", ".cache",
                "coverage", "*.min.js", "*.bundle.js"
            ]
        }

    def migrate_project(self, 
                       project_path: str, 
                       source_tech: str, 
                       target_tech: str,
                       output_path: str = None,
                       strategy: str = "incremental") -> Dict:
        """
        Migra un proyecto completo de una tecnología a otra
        """
        print(f"🚀 Iniciando migración de proyecto: {source_tech} → {target_tech}")
        print(f"📁 Proyecto: {project_path}")
        
        # 1. Análisis inicial del proyecto
        print("\n📊 FASE 1: Análisis del proyecto")
        project_analysis = self.analysis_agent.analyze_project_structure(project_path)
        
        # 2. Generar plan de migración
        print("\n📋 FASE 2: Generación del plan de migración")
        migration_plan = self._generate_migration_plan(project_analysis, source_tech, target_tech, strategy)
        
        # 3. Preparar directorio de salida
        if not output_path:
            output_path = f"{project_path}_migrated_to_{target_tech}"
        
        os.makedirs(output_path, exist_ok=True)
        
        # 4. Ejecutar migración por fases
        print("\n🔄 FASE 3: Ejecución de la migración")
        migration_results = self._execute_migration_plan(
            migration_plan, 
            project_path, 
            output_path, 
            project_analysis
        )
        
        # 5. Generar reporte final
        print("\n📄 FASE 4: Generación de reporte")
        final_report = self._generate_final_report(
            project_analysis, 
            migration_plan, 
            migration_results,
            source_tech,
            target_tech
        )
        
        # 6. Guardar reporte
        report_path = os.path.join(output_path, "migration_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Migración completada!")
        print(f"📁 Proyecto migrado: {output_path}")
        print(f"📄 Reporte: {report_path}")
        
        return final_report

    def _generate_migration_plan(self, 
                                project_analysis: Dict, 
                                source_tech: str, 
                                target_tech: str,
                                strategy: str) -> Dict:
        """
        Genera un plan detallado de migración
        """
        plan = {
            "strategy": strategy,
            "source_tech": source_tech,
            "target_tech": target_tech,
            "phases": [],
            "file_priorities": {},
            "estimated_duration": 0,
            "risks": []
        }
        
        # Clasificar archivos por prioridad
        all_files = self._get_all_project_files(project_analysis)
        prioritized_files = self._prioritize_files(all_files, project_analysis)
        
        plan["file_priorities"] = prioritized_files
        
        # Crear fases de migración
        if strategy == "incremental":
            plan["phases"] = self._create_incremental_phases(prioritized_files)
        else:  # strategy == "complete"
            plan["phases"] = self._create_complete_phases(prioritized_files)
        
        # Estimar duración
        plan["estimated_duration"] = self._estimate_migration_duration(prioritized_files)
        
        # Identificar riesgos
        plan["risks"] = self._identify_migration_risks(project_analysis, prioritized_files)
        
        return plan

    def _get_all_project_files(self, project_analysis: Dict) -> List[str]:
        """
        Obtiene todos los archivos del proyecto que deben ser migrados
        """
        files = []
        
        for directory in project_analysis["directories"]:
            if any(ignore in directory for ignore in self.migration_config["ignore_patterns"]):
                continue
            
            try:
                for root, dirs, filenames in os.walk(directory):
                    # Filtrar directorios ignorados
                    dirs[:] = [d for d in dirs if not any(ignore in d for ignore in self.migration_config["ignore_patterns"])]
                    
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        file_ext = Path(filename).suffix.lower()
                        
                        # Solo incluir archivos relevantes
                        if file_ext in self.migration_config["priority_extensions"]:
                            files.append(file_path)
            except:
                continue
        
        return files

    def _prioritize_files(self, files: List[str], project_analysis: Dict) -> Dict:
        """
        Prioriza archivos para migración
        """
        priorities = {
            "critical": [],    # Archivos de configuración y entry points
            "high": [],        # Componentes principales
            "medium": [],      # Componentes secundarios
            "low": []          # Archivos de soporte
        }
        
        for file_path in files:
            file_name = Path(file_path).name.lower()
            file_ext = Path(file_path).suffix.lower()
            
            # Archivos críticos
            if (file_path in project_analysis.get("entry_points", []) or
                file_path in project_analysis.get("config_files", []) or
                file_name in ["app.js", "main.js", "index.js", "app.component.ts"]):
                priorities["critical"].append(file_path)
            
            # Archivos de alta prioridad
            elif ("component" in file_name or "service" in file_name or 
                  file_ext in [".jsx", ".tsx", ".vue"]):
                priorities["high"].append(file_path)
            
            # Archivos de media prioridad
            elif file_ext in [".js", ".ts"]:
                priorities["medium"].append(file_path)
            
            # Archivos de baja prioridad
            else:
                priorities["low"].append(file_path)
        
        return priorities

    def _create_incremental_phases(self, prioritized_files: Dict) -> List[Dict]:
        """
        Crea fases incrementales de migración
        """
        phases = []
        
        # Fase 1: Archivos críticos
        if prioritized_files["critical"]:
            phases.append({
                "name": "Configuración y Entry Points",
                "description": "Migración de archivos críticos del proyecto",
                "files": prioritized_files["critical"],
                "order": 1,
                "can_run_parallel": False
            })
        
        # Fase 2: Componentes principales (en lotes)
        high_priority_batches = self._create_batches(prioritized_files["high"])
        for i, batch in enumerate(high_priority_batches):
            phases.append({
                "name": f"Componentes Principales - Lote {i+1}",
                "description": "Migración de componentes de alta prioridad",
                "files": batch,
                "order": 2,
                "can_run_parallel": True
            })
        
        # Fase 3: Componentes secundarios (en lotes)
        medium_priority_batches = self._create_batches(prioritized_files["medium"])
        for i, batch in enumerate(medium_priority_batches):
            phases.append({
                "name": f"Componentes Secundarios - Lote {i+1}",
                "description": "Migración de componentes de media prioridad",
                "files": batch,
                "order": 3,
                "can_run_parallel": True
            })
        
        # Fase 4: Archivos de soporte
        if prioritized_files["low"]:
            low_priority_batches = self._create_batches(prioritized_files["low"])
            for i, batch in enumerate(low_priority_batches):
                phases.append({
                    "name": f"Archivos de Soporte - Lote {i+1}",
                    "description": "Migración de archivos de baja prioridad",
                    "files": batch,
                    "order": 4,
                    "can_run_parallel": True
                })
        
        return phases

    def _create_complete_phases(self, prioritized_files: Dict) -> List[Dict]:
        """
        Crea fases para migración completa
        """
        all_files = []
        for priority_files in prioritized_files.values():
            all_files.extend(priority_files)
        
        batches = self._create_batches(all_files)
        phases = []
        
        for i, batch in enumerate(batches):
            phases.append({
                "name": f"Migración Completa - Lote {i+1}",
                "description": f"Migración de archivos del lote {i+1}",
                "files": batch,
                "order": 1,
                "can_run_parallel": True
            })
        
        return phases

    def _create_batches(self, files: List[str]) -> List[List[str]]:
        """
        Divide archivos en lotes para procesamiento
        """
        batch_size = self.migration_config["batch_size"]
        batches = []
        
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            batches.append(batch)
        
        return batches

    def _execute_migration_plan(self, 
                               migration_plan: Dict, 
                               project_path: str, 
                               output_path: str,
                               project_analysis: Dict) -> Dict:
        """
        Ejecuta el plan de migración
        """
        results = {
            "phases_completed": [],
            "total_files_migrated": 0,
            "total_files_failed": 0,
            "execution_time": 0,
            "errors": []
        }
        
        start_time = time.time()
        
        for phase in migration_plan["phases"]:
            print(f"\n🔄 Ejecutando: {phase['name']}")
            print(f"   📁 Archivos: {len(phase['files'])}")
            
            phase_start = time.time()
            
            # Migrar archivos de la fase
            migration_result = self.migration_agent.migrate_batch(
                phase["files"],
                migration_plan["source_tech"],
                migration_plan["target_tech"],
                context=project_analysis
            )
            
            # Guardar archivos migrados
            if migration_result["successful_migrations"]:
                save_result = self.migration_agent.save_migrated_files(
                    migration_result["successful_migrations"],
                    output_path
                )
                
                phase_result = {
                    "phase_name": phase["name"],
                    "files_processed": len(phase["files"]),
                    "files_migrated": migration_result["summary"]["successful"],
                    "files_failed": migration_result["summary"]["failed"],
                    "execution_time": time.time() - phase_start,
                    "saved_files": save_result["saved_files"],
                    "errors": migration_result["failed_migrations"] + save_result["errors"]
                }
                
                results["phases_completed"].append(phase_result)
                results["total_files_migrated"] += migration_result["summary"]["successful"]
                results["total_files_failed"] += migration_result["summary"]["failed"]
                results["errors"].extend(phase_result["errors"])
                
                print(f"   ✅ Completado: {migration_result['summary']['successful']} archivos")
                if migration_result["summary"]["failed"] > 0:
                    print(f"   ❌ Fallidos: {migration_result['summary']['failed']} archivos")
        
        results["execution_time"] = time.time() - start_time
        
        return results

    def _estimate_migration_duration(self, prioritized_files: Dict) -> int:
        """
        Estima la duración de migración en minutos
        """
        total_files = sum(len(files) for files in prioritized_files.values())
        
        # Estimación: 30 segundos por archivo en promedio
        estimated_seconds = total_files * 30
        estimated_minutes = estimated_seconds / 60
        
        return int(estimated_minutes)

    def _identify_migration_risks(self, project_analysis: Dict, prioritized_files: Dict) -> List[str]:
        """
        Identifica riesgos potenciales en la migración
        """
        risks = []
        
        total_files = sum(len(files) for files in prioritized_files.values())
        
        if total_files > 1000:
            risks.append("Proyecto muy grande (>1000 archivos) - considerar migración por módulos")
        
        if project_analysis["total_lines"] > 500000:
            risks.append("Código base muy extenso (>500k líneas) - tiempo de migración prolongado")
        
        if len(project_analysis["technologies_detected"]) > 2:
            risks.append("Múltiples tecnologías detectadas - posibles conflictos de migración")
        
        if not project_analysis["config_files"]:
            risks.append("No se detectaron archivos de configuración - estructura del proyecto incierta")
        
        return risks

    def _generate_final_report(self, 
                              project_analysis: Dict,
                              migration_plan: Dict,
                              migration_results: Dict,
                              source_tech: str,
                              target_tech: str) -> Dict:
        """
        Genera el reporte final de migración
        """
        success_rate = (migration_results["total_files_migrated"] / 
                       (migration_results["total_files_migrated"] + migration_results["total_files_failed"]) * 100
                       if (migration_results["total_files_migrated"] + migration_results["total_files_failed"]) > 0 else 0)
        
        return {
            "migration_summary": {
                "source_technology": source_tech,
                "target_technology": target_tech,
                "strategy": migration_plan["strategy"],
                "success_rate": round(success_rate, 2),
                "total_files_processed": migration_results["total_files_migrated"] + migration_results["total_files_failed"],
                "files_migrated": migration_results["total_files_migrated"],
                "files_failed": migration_results["total_files_failed"],
                "execution_time_minutes": round(migration_results["execution_time"] / 60, 2)
            },
            "project_analysis": project_analysis,
            "migration_plan": migration_plan,
            "execution_results": migration_results,
            "recommendations": self._generate_recommendations(migration_results, project_analysis),
            "next_steps": self._generate_next_steps(migration_results, target_tech)
        }

    def _generate_recommendations(self, migration_results: Dict, project_analysis: Dict) -> List[str]:
        """
        Genera recomendaciones basadas en los resultados
        """
        recommendations = []
        
        if migration_results["total_files_failed"] > 0:
            recommendations.append("Revisar archivos fallidos manualmente")
            recommendations.append("Considerar migración manual para archivos complejos")
        
        if migration_results["total_files_migrated"] > 100:
            recommendations.append("Ejecutar pruebas exhaustivas del código migrado")
            recommendations.append("Revisar dependencias y configuraciones")
        
        recommendations.append("Actualizar documentación del proyecto")
        recommendations.append("Configurar herramientas de desarrollo para la nueva tecnología")
        
        return recommendations

    def _generate_next_steps(self, migration_results: Dict, target_tech: str) -> List[str]:
        """
        Genera pasos siguientes recomendados
        """
        steps = [
            f"1. Instalar dependencias de {target_tech}",
            "2. Configurar herramientas de build",
            "3. Ejecutar pruebas unitarias",
            "4. Revisar y corregir errores de compilación",
            "5. Actualizar scripts de deployment",
            "6. Entrenar al equipo en la nueva tecnología"
        ]
        
        if migration_results["total_files_failed"] > 0:
            steps.insert(1, "1.5. Migrar manualmente archivos fallidos")
        
        return steps 