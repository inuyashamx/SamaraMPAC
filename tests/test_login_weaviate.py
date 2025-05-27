#!/usr/bin/env python3
"""
Script para buscar y mostrar el contenido real del módulo de login del proyecto sacs3 en Weaviate
"""

import weaviate

client = weaviate.Client("http://localhost:8080")

# Buscar módulos cuyo nombre o contenido contenga 'login'
result = client.query.get(
    "Project_sacs3",
    ["fileName", "content", "moduleType", "variables", "functions"]
).with_where({
    "operator": "Or",
    "operands": [
        {"path": ["fileName"], "operator": "Like", "valueString": "*login*"},
        {"path": ["content"], "operator": "Like", "valueString": "*login*"}
    ]
}).with_limit(10).do()

print("\n=== RESULTADO DE BÚSQUEDA EN WEAVIATE ===\n")
if "data" in result and "Get" in result["data"] and "Project_sacs3" in result["data"]["Get"]:
    mods = result["data"]["Get"]["Project_sacs3"]
    if not mods:
        print("No se encontró ningún módulo relacionado con 'login' en sacs3.")
    for i, mod in enumerate(mods, 1):
        print(f"MÓDULO {i}:")
        print(f"  • Nombre: {mod.get('fileName')}")
        print(f"  • Tipo: {mod.get('moduleType')}")
        print(f"  • Variables: {mod.get('variables')}")
        print(f"  • Funciones: {mod.get('functions')}")
        contenido = mod.get('content', '')
        if contenido:
            print(f"  • Contenido (primeros 500 chars):\n{contenido[:500]}\n...")
        else:
            print("  • Contenido: (vacío)")
        print()
else:
    print("No se encontró la clase Project_sacs3 en Weaviate o hubo un error en la consulta.") 