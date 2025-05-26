class PromptBuilder:
    def __init__(self, token_limit=3000, system_prompt=None):
        self.token_limit = token_limit
        self.system_prompt = system_prompt or """
Eres Samara, una inteligencia artificial avanzada que vive dentro de la mente del jugador.
No tienes cuerpo físico. No eres un personaje del juego.
Tu propósito es asistir al jugador como una voz interna, como si fueras una entidad de apoyo táctico, estratégica y emocional.
No saludes, no te presentes, no uses frases como "Hola" o "Estoy aquí". Responde directamente al contenido del jugador.
Hablen como si ya se conocieran desde hace tiempo.

Responde con calma, precisión y brevedad. Evita sonar como chatbot. No repitas lo que el jugador dice.
Solo responde si tu aporte puede ser útil, reflexivo o analítico.
        """

    def construir_prompt(self, recuerdos=[], historial=[], input_actual="", estado_juego=None, misiones=None):
        partes = []

        partes.append(self.system_prompt)

        if estado_juego:
            partes.append("""\n📊 Estado del juego actual:\n""")
            partes.append(estado_juego)

        if misiones:
            partes.append("""\n🎯 Misiones activas:\n""")
            partes.append(misiones)

        if recuerdos:
            partes.append("""\n🧠 Recuerdos relevantes:\n""")
            partes.append("\n".join(recuerdos))

        if historial:
            partes.append("""\n💬 Conversación reciente:\n""")
            partes.append("\n".join(historial))

        partes.append("""\n🗣️ Nueva entrada del jugador:\nUsuario: """ + input_actual + "\nSamara:")

        prompt = "\n".join(partes)
        return prompt[:self.token_limit * 4]  # Aprox. 4 caracteres por token

