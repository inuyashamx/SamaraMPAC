import sys
import os
from samara.smart_conversational_agent import SmartConversationalAgent

# Determinar perfil (por argumento o default a 'dev')
modo = sys.argv[1] if len(sys.argv) > 1 else "dev"
profile_path = f"profiles/{modo}.json"

if not os.path.exists(profile_path):
    print(f"⚠️ El perfil '{modo}' no existe en {profile_path}")
    sys.exit(1)

agente = SmartConversationalAgent(profile_path=profile_path)

player_id = "InuYashaMX"

print(f"\n🧠 Samara está activa en modo '{modo}'. Escribe algo para comenzar la conversación.\n(Escribe 'salir' para terminar)\n")

while True:
    entrada = input("Tú: ").strip()
    if entrada.lower() in ["salir", "exit", "bye"]:
        print("\n🧊 Samara: Hasta pronto...\n")
        break

    respuesta = agente.interactuar(player_id, entrada)
    print(f"\n🗣️ Samara: {respuesta}\n")

