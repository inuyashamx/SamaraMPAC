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
    print("\n🗣️ Samara (respuesta final):\n" + log.get("respuesta_final", "Sin respuesta") + "\n")

