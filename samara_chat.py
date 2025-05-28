#!/usr/bin/env python3
"""
Chat interactivo con Samara - Sistema de consulta de fragmentos de código
"""

import sys
import os
import json
from agentes.consultor_fragmentos import FragmentQueryAgent

# Determinar perfil (por argumento o default a 'dev')
modo = sys.argv[1] if len(sys.argv) > 1 else "dev"
profile_path = f"profiles/{modo}.json"

if not os.path.exists(profile_path):
    print(f"⚠️ El perfil '{modo}' no existe en {profile_path}")
    sys.exit(1)

semantic_agent = FragmentQueryAgent()

player_id = "InuYashaMX"

print(f"\n🧠 Samara está activa en modo '{modo}' con FRAGMENTOS DE CÓDIGO. Escribe algo para comenzar la conversación.\n(Escribe 'salir' para terminar)\n")

while True:
    entrada = input("Tú: ").strip()
    if entrada.lower() in ["salir", "exit", "bye"]:
        print("\n🧊 Samara: Hasta pronto...\n")
        break

    log = semantic_agent.consulta_inteligente("samara", entrada)
    print("\n--- LOG DE LA INTERACCIÓN (FRAGMENTOS) ---")
    print(f"Estrategia utilizada: {log.get('estrategia', 'desconocida')}")
    print(f"Estrategia exitosa: {log.get('estrategia_exitosa', 'ninguna')}")
    
    # Mostrar búsqueda semántica PRINCIPAL (fragmentos)
    if "busqueda_semantica_principal" in log:
        print("\n" + "="*60)
        print("--- BÚSQUEDA SEMÁNTICA EN FRAGMENTOS ---")
        semantica = log["busqueda_semantica_principal"]
        
        if "query_embedding_preview" in semantica:
            print(f"\nEmbedding de la pregunta (preview): {semantica['query_embedding_preview']}")
        
        if "respuesta_cruda" in semantica:
            print("\nRespuesta cruda de búsqueda semántica:")
            respuesta_cruda = semantica["respuesta_cruda"]
            if 'data' in respuesta_cruda and 'Get' in respuesta_cruda['data']:
                fragmentos = list(respuesta_cruda['data']['Get'].values())[0] if respuesta_cruda['data']['Get'] else []
                print(f"Fragmentos encontrados: {len(fragmentos)}")
                for i, fragmento in enumerate(fragmentos[:5], 1):  # Mostrar más fragmentos
                    function_name = fragmento.get('functionName', 'Sin nombre')
                    file_name = fragmento.get('fileName', 'N/A')
                    fragment_type = fragmento.get('type', 'N/A')
                    lines = f"{fragmento.get('startLine', 'N/A')}-{fragmento.get('endLine', 'N/A')}"
                    print(f"  {i}. {function_name} ({fragment_type}) en {file_name} (líneas {lines})")
                if len(fragmentos) > 5:
                    print(f"  ... y {len(fragmentos) - 5} fragmentos más")
            else:
                print("No se encontraron fragmentos relevantes")
        
        if "contexto_preparado" in semantica:
            print(f"\nContexto preparado (preview):\n{semantica['contexto_preparado']}")
        
        if "respuesta_final" in semantica:
            print(f"\nRespuesta de búsqueda semántica:\n{semantica['respuesta_final']}")
        
        if "error" in semantica:
            print(f"\nError en búsqueda semántica:\n{semantica['error']}")
    
    # Mostrar búsqueda por filtros (fallback)
    if "busqueda_filtros" in log:
        print("\n" + "="*60)
        print("--- BÚSQUEDA POR FILTROS (FALLBACK) ---")
        filtros = log["busqueda_filtros"]
        
        if "terminos_extraidos" in filtros:
            print(f"\nTérminos extraídos: {filtros['terminos_extraidos']}")
        
        if "respuesta_cruda" in filtros:
            print("\nRespuesta cruda de búsqueda por filtros:")
            respuesta_cruda = filtros["respuesta_cruda"]
            if 'data' in respuesta_cruda and 'Get' in respuesta_cruda['data']:
                fragmentos = list(respuesta_cruda['data']['Get'].values())[0] if respuesta_cruda['data']['Get'] else []
                print(f"Fragmentos encontrados: {len(fragmentos)}")
                for i, fragmento in enumerate(fragmentos[:3], 1):
                    function_name = fragmento.get('functionName', 'Sin nombre')
                    file_name = fragmento.get('fileName', 'N/A')
                    fragment_type = fragmento.get('type', 'N/A')
                    print(f"  {i}. {function_name} ({fragment_type}) en {file_name}")
                if len(fragmentos) > 3:
                    print(f"  ... y {len(fragmentos) - 3} fragmentos más")
            else:
                print("No se encontraron fragmentos relevantes")
        
        if "contexto_preparado" in filtros:
            print(f"\nContexto preparado (preview):\n{filtros['contexto_preparado']}")
        
        if "respuesta_final" in filtros:
            print(f"\nRespuesta final de búsqueda por filtros:\n{filtros['respuesta_final']}")
        
        if "error" in filtros:
            print(f"\nError en búsqueda por filtros:\n{filtros['error']}")
    
    # Mantener compatibilidad con el logging original (para proyectos que usen el esquema viejo)
    if "intentos" in log:
        print("\n" + "="*60)
        print("--- FILTROS EXACTOS (LEGACY) ---")
        for paso in log.get("intentos", []):
            print(f"\n--- Intento {paso.get('intento')} ---")
            print("Prompt enviado al LLM:")
            print(paso.get("prompt", "")[:1000], "..." if len(paso.get("prompt", "")) > 1000 else "")
            print("\nPlan generado por el LLM:")
            print(paso.get("plan_llm", "")[:1000], "..." if len(paso.get("plan_llm", "")) > 1000 else "")
            print("\nPlan parseado:")
            print(json.dumps(paso.get("plan_parseado", {}), indent=2, ensure_ascii=False))
            print("\nRespuesta cruda de Weaviate:")
            weaviate_resp = paso.get("respuesta_weaviate", {})
            print(json.dumps(weaviate_resp, indent=2, ensure_ascii=False)[:2000], "...")
            if "respuesta_final" in paso:
                print("\nRespuesta final de este intento:\n" + paso["respuesta_final"])
            if "error" in paso:
                print("\nError en este intento:\n" + paso["error"])
    
    # Mostrar error general si existe
    if "error" in log:
        print(f"\n❌ Error general: {log['error']}")
    
    print("\n🗣️ Samara (respuesta final):\n" + log.get("respuesta_final", "Sin respuesta") + "\n")

