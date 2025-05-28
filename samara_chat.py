import sys
import os
import json
from samara.smart_conversational_agent import SemanticQueryAgent

# Determinar perfil (por argumento o default a 'dev')
modo = sys.argv[1] if len(sys.argv) > 1 else "dev"
profile_path = f"profiles/{modo}.json"

if not os.path.exists(profile_path):
    print(f"⚠️ El perfil '{modo}' no existe en {profile_path}")
    sys.exit(1)

semantic_agent = SemanticQueryAgent()

player_id = "InuYashaMX"

print(f"\n🧠 Samara está activa en modo '{modo}'. Escribe algo para comenzar la conversación.\n(Escribe 'salir' para terminar)\n")

while True:
    entrada = input("Tú: ").strip()
    if entrada.lower() in ["salir", "exit", "bye"]:
        print("\n🧊 Samara: Hasta pronto...\n")
        break

    log = semantic_agent.consulta_inteligente("sacs3", entrada)
    print("\n--- LOG DE LA INTERACCIÓN (LLM-driven) ---")
    print(f"Estrategia utilizada: {log.get('estrategia', 'desconocida')}")
    print(f"Estrategia exitosa: {log.get('estrategia_exitosa', 'ninguna')}")
    
    # Mostrar búsqueda semántica PRINCIPAL (la nueva)
    if "busqueda_semantica_principal" in log:
        print("\n" + "="*60)
        print("--- BÚSQUEDA SEMÁNTICA PRINCIPAL ---")
        semantica = log["busqueda_semantica_principal"]
        
        if "query_embedding_preview" in semantica:
            print(f"\nEmbedding de la pregunta (preview): {semantica['query_embedding_preview']}")
        
        if "respuesta_cruda" in semantica:
            print("\nRespuesta cruda de búsqueda semántica:")
            respuesta_cruda = semantica["respuesta_cruda"]
            if 'data' in respuesta_cruda and 'Get' in respuesta_cruda['data']:
                archivos = list(respuesta_cruda['data']['Get'].values())[0] if respuesta_cruda['data']['Get'] else []
                print(f"Archivos encontrados: {len(archivos)}")
                for i, archivo in enumerate(archivos[:5], 1):  # Mostrar más archivos
                    print(f"  {i}. {archivo.get('fileName', 'Sin nombre')} - {archivo.get('filePath', 'N/A')} ({archivo.get('moduleType', 'N/A')})")
                if len(archivos) > 5:
                    print(f"  ... y {len(archivos) - 5} archivos más")
            else:
                print("No se encontraron archivos relevantes")
        
        if "contexto_preparado" in semantica:
            print(f"\nContexto preparado (preview):\n{semantica['contexto_preparado']}")
        
        if "respuesta_final" in semantica:
            print(f"\nRespuesta de búsqueda semántica principal:\n{semantica['respuesta_final']}")
        
        if "error" in semantica:
            print(f"\nError en búsqueda semántica principal:\n{semantica['error']}")
    
    # Mostrar intentos con filtros exactos (fallback)
    if log.get("intentos"):
        print("\n" + "="*60)
        print("--- FILTROS EXACTOS (FALLBACK) ---")
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
    
    # Mostrar búsqueda semántica antigua (si existe, para compatibilidad)
    if "busqueda_semantica" in log:
        print("\n" + "="*60)
        print("--- BÚSQUEDA SEMÁNTICA (LEGACY) ---")
        semantica = log["busqueda_semantica"]
        
        if "query_embedding_preview" in semantica:
            print(f"\nEmbedding de la pregunta (preview): {semantica['query_embedding_preview']}")
        
        if "respuesta_cruda" in semantica:
            print("\nRespuesta cruda de búsqueda semántica:")
            respuesta_cruda = semantica["respuesta_cruda"]
            if 'data' in respuesta_cruda and 'Get' in respuesta_cruda['data']:
                archivos = list(respuesta_cruda['data']['Get'].values())[0] if respuesta_cruda['data']['Get'] else []
                print(f"Archivos encontrados: {len(archivos)}")
                for i, archivo in enumerate(archivos[:3], 1):
                    print(f"  {i}. {archivo.get('fileName', 'Sin nombre')} ({archivo.get('moduleType', 'N/A')})")
                if len(archivos) > 3:
                    print(f"  ... y {len(archivos) - 3} archivos más")
            else:
                print("No se encontraron archivos relevantes")
        
        if "contexto_preparado" in semantica:
            print(f"\nContexto preparado (preview):\n{semantica['contexto_preparado']}")
        
        print("\nProcesamiento: PromptGeneratorAgent analizó directamente el contexto")
        
        if "respuesta_final" in semantica:
            print(f"\nRespuesta final de búsqueda semántica:\n{semantica['respuesta_final']}")
        
        if "error" in semantica:
            print(f"\nError en búsqueda semántica:\n{semantica['error']}")
    
    print("\n🗣️ Samara (respuesta final):\n" + log.get("respuesta_final", "Sin respuesta") + "\n")

