import weaviate

client = weaviate.Client("http://localhost:8080")

schema = {
    "class": "PlayerMemories",
    "description": "Recuerdos narrativos por jugador",
    "vectorizer": "none",
    "properties": [
        {
            "name": "contenido",
            "dataType": ["text"]
        },
        {
            "name": "player_id",
            "dataType": ["string"]
        }
    ]
}

# Limpia si ya existe
if client.schema.exists("PlayerMemories"):
    client.schema.delete_class("PlayerMemories")

client.schema.create_class(schema)
print("✅ Clase PlayerMemories creada en Weaviate.")

