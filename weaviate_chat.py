import weaviate
import requests
import json

# Configuración
OLLAMA_URL = "http://localhost:11434"
WEAVIATE_URL = "http://localhost:8080"


def obtener_embedding(texto):
    """Obtiene el embedding usando Ollama (nomic-embed-text)"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": texto},
            timeout=30
        )
        if response.status_code == 200:
            return response.json()["embedding"]
        else:
            print(f"Error al obtener embedding: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error conectando con Ollama: {e}")
        return []


def listar_proyectos(client):
    """Lista los proyectos (clases que empiezan por Project_) en Weaviate"""
    try:
        schema = client.schema.get()
        clases = [c['class'] for c in schema.get('classes', [])]
        proyectos = [c for c in clases if c.startswith('Project_') and not c.endswith('_Chunks')]
        if not proyectos:
            print("No hay proyectos indexados en Weaviate.")
        else:
            print("Proyectos disponibles en Weaviate:")
            for c in proyectos:
                print(f"  - {c[8:]}")  # Mostrar solo el nombre después de 'Project_'
        print()
    except Exception as e:
        print(f"Error al listar proyectos: {e}")
        print()


def main():
    print("\n=== Chat semántico con Weaviate ===\n")
    # Conectar a Weaviate
    try:
        client = weaviate.Client(WEAVIATE_URL)
        print(f"Conectado a Weaviate en {WEAVIATE_URL}\n")
    except Exception as e:
        print(f"No se pudo conectar a Weaviate: {e}")
        return

    # Listar proyectos disponibles
    listar_proyectos(client)

    proyecto = input("Nombre del proyecto (como lo indexaste): ").strip()
    if not proyecto:
        print("Debes indicar un nombre de proyecto.")
        return
    clase = f"Project_{''.join([c if c.isalnum() or c == '_' else '_' for c in proyecto])}"

    print("Escribe tu pregunta (o 'salir' para terminar):\n")
    while True:
        pregunta = input("> ").strip()
        if pregunta.lower() in ("salir", "exit", "quit"):
            print("Adiós!")
            break
        if not pregunta:
            continue
        embedding = obtener_embedding(pregunta)
        if not embedding:
            print("No se pudo obtener el embedding de la pregunta.")
            continue
        try:
            result = (
                client.query
                .get(clase, [
                    "filePath", "fileName", "moduleType", "technology", "summary", "content"
                ])
                .with_near_vector({"vector": embedding})
                .with_limit(5)
                .do()
            )
            archivos = result.get('data', {}).get('Get', {}).get(clase, [])
            if not archivos:
                print("No se encontraron resultados relevantes.\n")
                continue
            print(f"\nResultados relevantes para: '{pregunta}'\n")
            for i, archivo in enumerate(archivos, 1):
                print(f"[{i}] {archivo.get('fileName')} ({archivo.get('filePath')})")
                print(f"    Tipo: {archivo.get('moduleType')} | Tecnología: {archivo.get('technology')}")
                print(f"    Resumen: {archivo.get('summary')[:300]}")
                print("-")
            print()
        except Exception as e:
            print(f"Error consultando Weaviate: {e}\n")

if __name__ == "__main__":
    main()
