# 🤖 Guía de OpenAI para Contextos Largos

## 🚀 Cómo usar

### Iniciar chat principal
```bash
python chat_openai.py
```

### Comandos especiales
- `usar modelo gpt` - Fuerza OpenAI/GPT-4 para toda la sesión
- `usar modelo ollama` - Cambia a Ollama local
- `usar modelo claude` - Cambia a Claude (si tienes API key)
- `salir` - Terminar el chat

## 🧠 Funcionamiento Inteligente

### Selección automática de modelo
El sistema elige automáticamente el mejor modelo según:

- **Contextos pequeños (<2k tokens)**: Ollama local (rápido y gratis)
- **Contextos medianos (2k-10k tokens)**: GPT-4 para análisis de código
- **Contextos grandes (>10k tokens)**: GPT-4 o Claude automáticamente
- **Contextos muy grandes (>30k tokens)**: Claude preferido

### Análisis de código
Para análisis de código específicamente, el sistema prefiere modelos cloud:

```
💬 Tú: analiza el módulo login del proyecto sacs3
🎯 Tarea detectada: analisis_codigo
🧠 Análisis de código (2,500 tokens) → GPT-4
🤖 Usado: gpt4
```

## 📊 Ventajas de OpenAI

### Para contextos largos:
- ✅ **128k tokens** de límite (vs 8k de Ollama)
- ✅ **Mejor comprensión** de contextos complejos
- ✅ **Análisis más profundo** de código
- ✅ **Respuestas más estructuradas**

### Ejemplos de uso ideal:
- Análisis de proyectos completos
- Migración de código masiva
- Documentación técnica extensa
- Debugging de sistemas complejos

## 🛠️ Configuración

### Variables de entorno necesarias:
```env
OPENAI_API_KEY=tu_api_key_aqui
```

### Verificar que funciona:
```bash
python test_openai_contexto.py
```

## 📝 Ejemplos prácticos

### Forzar OpenAI para una sesión:
```
💬 Tú: usar modelo gpt
🧠 Samara: 🤖 Configurado para usar GPT-4 para toda la sesión

💬 Tú: analiza el módulo login del proyecto sacs3
🤖 Usado: gpt4
```

### Contexto muy largo (activación automática):
```
💬 Tú: Necesito analizar todo el proyecto sacs3... [texto muy largo]
🎯 Tarea detectada: analisis_codigo  
📏 Tamaño de contexto: ~15,000 tokens
☁️ Contexto grande (15,000 tokens) → GPT-4
🤖 Usado: gpt4
```

## 🔧 Solución de problemas

### Si OpenAI no está disponible:
1. Verificar que tu API key está en `.env`
2. Verificar saldo de tu cuenta OpenAI
3. El sistema hará fallback a Ollama automáticamente

### Si ves "fallback desde gpt4":
- Problema temporal con la API de OpenAI
- Rate limiting (demasiadas consultas muy rápidas)
- El sistema usó Ollama como respaldo

### Para debug:
```bash
python test_openai_especifico.py  # Pruebas específicas
```

## 🎯 Casos de uso perfectos para OpenAI

1. **Análisis completo de proyectos grandes**
2. **Migración de código entre frameworks**
3. **Documentación técnica extensa**
4. **Debugging de sistemas complejos**
5. **Revisión de arquitectura de software**

El sistema es inteligente y elegirá el modelo óptimo para cada situación automáticamente. ¡Solo tienes que preguntar! 