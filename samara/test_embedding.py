import requests
import weaviate
import time

# Conexiones
weaviate_url = 'http://localhost:8080'
ollama_url = 'http://localhost:11434'

client = weaviate.Client(weaviate_url)

# 1. Crear clase de prueba
schema = {
    'class': 'TestEmbeddings',
    'vectorizer': 'none',
    'properties': [
        {'name': 'contenido', 'dataType': ['text']}
    ]
}
try:
    if not client.schema.exists('TestEmbeddings'):
        client.schema.create_class(schema)
        print('✅ Clase TestEmbeddings creada')
except Exception as e:
    print(f'⚠️  Error creando clase: {e}')

# 2. Guardar objeto de prueba
texto = 'esto es una prueba de embedding'
embedding = requests.post(f'{ollama_url}/api/embeddings', json={'model': 'nomic-embed-text', 'prompt': texto}).json()['embedding']

obj = client.data_object.create({'contenido': texto}, 'TestEmbeddings', vector=embedding)
print('✅ Objeto guardado con embedding')

# Esperar a que Weaviate indexe
time.sleep(2)

# 3. Buscar por embedding similar
consulta = 'prueba de vector semántico'
consulta_emb = requests.post(f'{ollama_url}/api/embeddings', json={'model': 'nomic-embed-text', 'prompt': consulta}).json()['embedding']

result = client.query.get('TestEmbeddings', ['contenido']).with_near_vector({'vector': consulta_emb}).with_limit(2).do()

print('\n🔎 Resultado de búsqueda:')
if 'data' in result and 'Get' in result['data'] and 'TestEmbeddings' in result['data']['Get']:
    for obj in result['data']['Get']['TestEmbeddings']:
        print('   ➡️', obj['contenido'])
else:
    print('   ❌ No se encontró ningún resultado') 