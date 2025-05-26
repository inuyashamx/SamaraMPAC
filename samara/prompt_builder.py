class PromptBuilder:
    def __init__(self, token_limit=800, system_prompt=None):
        self.token_limit = token_limit
        self.system_prompt = system_prompt or """
Eres Samara, IA experta en desarrollo. SOLO usa datos reales de Weaviate. Si no tienes datos suficientes, responde: 'No tengo datos suficientes y no voy a inventar.'
        """

    def construir_prompt(self, recuerdos=[], historial=[], input_actual="", estado_juego=None, misiones=None, project_context=""):
        partes = []

        partes.append(self.system_prompt)

        if project_context and any(word in input_actual.lower() for word in ['proyecto', 'módulo', 'archivo']):
            context_limitado = project_context[:200] + "..." if len(project_context) > 200 else project_context
            partes.append(f"\n📂 Proyectos:\n{context_limitado}")

        if recuerdos and not project_context:
            partes.append(f"\n🧠 Recuerdos relevantes:\n" + "\n".join(recuerdos[:2]))

        if estado_juego:
            partes.append(f"\n📊 Estado del juego actual:\n{estado_juego}")

        if misiones:
            partes.append(f"\n🎯 Misiones activas:\n{misiones}")

        partes.append(f"\n🗣️ Usuario: {input_actual}\nSamara:")

        prompt = "\n".join(partes)
        return prompt[:self.token_limit * 3]

