import os
import json
import requests
import re
from typing import List, Dict, Optional
from .model_router_agent import ModelRouterAgent, TaskType, ModelProvider
from datetime import datetime
from .code_analysis_agent import CodeAnalysisAgent
import time
import unicodedata

class FragmentQueryAgent:
    """
    Agente especializado en consultas sobre fragmentos de código.
    Funciona con el nuevo esquema CodeFragments_{proyecto}.
    """
    
    def __init__(self, weaviate_client=None):
        if weaviate_client is None:
            from .code_analysis_agent import CodeAnalysisAgent
            self.code_agent = CodeAnalysisAgent()
            self.weaviate_client = self.code_agent.weaviate_client
        else:
            self.weaviate_client = weaviate_client
        self._esquema_cache = None
        self.model_router = ModelRouterAgent()
        self.prompt_generator = PromptGenerator()

    def _get_schema(self):
        if self._esquema_cache is None:
            self._esquema_cache = self.weaviate_client.schema.get()
        return self._esquema_cache

    def _prompt_llm(self, prompt):
        result = self.model_router._call_gpt4(prompt, max_tokens=1024, temperature=0)
        if result["success"]:
            return result["response"]
        else:
            return f"[Error llamando a OpenAI: {result.get('error', '')}]"

    def consulta_inteligente(self, proyecto, pregunta, archivo=None):
        """
        Consulta inteligente usando fragmentos de código con búsqueda semántica híbrida
        """
        log = {"estrategia": "busqueda_fragmentos_hibrida", "intentos": []}
        class_name = f"CodeFragments_{proyecto}"
        
        # Verificar que la clase existe
        esquema = self._get_schema()
        clases_disponibles = [c['class'] for c in esquema.get('classes', [])]
        
        if class_name not in clases_disponibles:
            log["error"] = f"No se encontró el proyecto '{proyecto}' indexado con fragmentos. Clases disponibles: {clases_disponibles}"
            log["respuesta_final"] = f"El proyecto '{proyecto}' no está indexado con el nuevo sistema de fragmentos. Usa el CLI para indexarlo primero."
            return log

        # ESTRATEGIA 1: Búsqueda semántica principal
        try:
            log["busqueda_semantica_principal"] = self._busqueda_semantica_fragmentos(class_name, pregunta)
            
            if log["busqueda_semantica_principal"].get("respuesta_final"):
                log["respuesta_final"] = log["busqueda_semantica_principal"]["respuesta_final"]
                log["estrategia_exitosa"] = "busqueda_semantica_fragmentos"
                return log
        except Exception as e:
            log["busqueda_semantica_principal"] = {"error": f"Error en búsqueda semántica: {e}"}

        # ESTRATEGIA 2: Búsqueda por filtros exactos (fallback)
        try:
            log["busqueda_filtros"] = self._busqueda_filtros_fragmentos(class_name, pregunta)
            
            if log["busqueda_filtros"].get("respuesta_final"):
                log["respuesta_final"] = log["busqueda_filtros"]["respuesta_final"]
                log["estrategia_exitosa"] = "busqueda_filtros_fragmentos"
                return log
        except Exception as e:
            log["busqueda_filtros"] = {"error": f"Error en búsqueda por filtros: {e}"}

        # Si nada funcionó
        log["respuesta_final"] = f"No se encontraron fragmentos relevantes para '{pregunta}' en el proyecto {proyecto}."
        log["estrategia_exitosa"] = "ninguna"
        return log

    def _busqueda_semantica_fragmentos(self, class_name, pregunta):
        """Búsqueda semántica usando embeddings en fragmentos"""
        resultado = {}
        
        # Generar embedding de la pregunta
        query_embedding = self.code_agent._get_embedding(pregunta)
        if not query_embedding:
            resultado["error"] = "No se pudo generar embedding para la consulta"
            return resultado
        
        resultado["query_embedding_preview"] = query_embedding[:5]
        
        # Búsqueda semántica
        respuesta_cruda = (
            self.weaviate_client.query
            .get(class_name, [
                'fileName', 'filePath', 'type', 'functionName', 'startLine', 'endLine',
                'content', 'description', 'module', 'language', 'framework', 'complexity',
                'parameters', 'returnType'
            ])
            .with_near_vector({"vector": query_embedding})
            .with_limit(10)
            .do()
        )
        
        resultado["respuesta_cruda"] = respuesta_cruda
        
        # Extraer fragmentos
        fragmentos = []
        if 'data' in respuesta_cruda and 'Get' in respuesta_cruda['data'] and class_name in respuesta_cruda['data']['Get']:
            fragmentos = respuesta_cruda['data']['Get'][class_name]
        
        if not fragmentos:
            resultado["error"] = "No se encontraron fragmentos relevantes"
            return resultado
        
        # Preparar contexto
        contexto = self._preparar_contexto_fragmentos(fragmentos, pregunta)
        resultado["contexto_preparado"] = contexto[:500] + "..." if len(contexto) > 500 else contexto
        
        # Generar respuesta con IA
        prompt = f"""Eres un asistente experto en análisis de código. Un usuario ha hecho la siguiente consulta sobre un proyecto de software:

CONSULTA DEL USUARIO: "{pregunta}"

FRAGMENTOS DE CÓDIGO RELEVANTES ENCONTRADOS:
{contexto}

Tu tarea es:
1. Analizar los fragmentos de código encontrados
2. Responder la consulta del usuario de manera clara y estructurada
3. Proporcionar ejemplos específicos del código cuando sea relevante
4. Explicar cómo los fragmentos se relacionan con la consulta
5. Dar recomendaciones o insights útiles si es apropiado

Responde en español de manera técnica pero comprensible. Si no hay fragmentos relevantes, explica qué se podría buscar en su lugar.

RESPUESTA:"""

        respuesta_final = self._prompt_llm(prompt)
        resultado["respuesta_final"] = respuesta_final
        
        return resultado

    def _busqueda_filtros_fragmentos(self, class_name, pregunta):
        """Búsqueda usando filtros exactos en campos específicos"""
        resultado = {}
        
        # Extraer términos clave de la pregunta
        prompt_extraccion = f"""
Extrae SOLO los términos clave más importantes de esta pregunta para buscar en código:
"{pregunta}"

Responde solo con las palabras clave separadas por comas, sin explicaciones:
"""
        terminos_llm = self._prompt_llm(prompt_extraccion).strip()
        terminos = [t.strip().lower() for t in terminos_llm.split(',') if t.strip()]
        
        resultado["terminos_extraidos"] = terminos
        
        # Campos donde buscar
        campos_busqueda = ['functionName', 'description', 'content', 'module', 'fileName']
        
        # Construir consulta con filtros
        where_conditions = []
        for termino in terminos[:3]:  # Limitar a 3 términos para no saturar
            for campo in campos_busqueda:
                where_conditions.append({
                    "path": [campo],
                    "operator": "Like",
                    "valueString": f"*{termino}*"
                })
        
        if where_conditions:
            where_clause = {
                "operator": "Or",
                "operands": where_conditions
            }
            
            respuesta_cruda = (
                self.weaviate_client.query
                .get(class_name, [
                    'fileName', 'filePath', 'type', 'functionName', 'startLine', 'endLine',
                    'content', 'description', 'module', 'language', 'complexity'
                ])
                .with_where(where_clause)
                .with_limit(15)
                .do()
            )
            
            resultado["respuesta_cruda"] = respuesta_cruda
            
            # Extraer fragmentos
            fragmentos = []
            if 'data' in respuesta_cruda and 'Get' in respuesta_cruda['data'] and class_name in respuesta_cruda['data']['Get']:
                fragmentos = respuesta_cruda['data']['Get'][class_name]
            
            if fragmentos:
                # Preparar contexto y generar respuesta
                contexto = self._preparar_contexto_fragmentos(fragmentos, pregunta)
                resultado["contexto_preparado"] = contexto[:500] + "..." if len(contexto) > 500 else contexto
                
                prompt = f"""Analiza estos fragmentos de código y responde la pregunta del usuario:

PREGUNTA: "{pregunta}"

FRAGMENTOS ENCONTRADOS:
{contexto}

Responde de manera clara y técnica en español:"""

                respuesta_final = self._prompt_llm(prompt)
                resultado["respuesta_final"] = respuesta_final
            else:
                resultado["error"] = "No se encontraron fragmentos con los filtros aplicados"
        else:
            resultado["error"] = "No se pudieron extraer términos de búsqueda válidos"
        
        return resultado

    def _preparar_contexto_fragmentos(self, fragmentos, pregunta):
        """Prepara contexto estructurado con los fragmentos encontrados"""
        if not fragmentos:
            return "No se encontraron fragmentos relevantes."
        
        contexto = f"=== FRAGMENTOS RELEVANTES PARA: '{pregunta}' ===\n\n"
        
        for i, fragment in enumerate(fragmentos[:8], 1):  # Limitar a 8 para no saturar
            contexto += f"FRAGMENTO {i}:\n"
            contexto += f"  📁 Archivo: {fragment.get('fileName', 'N/A')}\n"
            contexto += f"  📍 Ubicación: {fragment.get('filePath', 'N/A')} (líneas {fragment.get('startLine', 'N/A')}-{fragment.get('endLine', 'N/A')})\n"
            contexto += f"  🏷️  Tipo: {fragment.get('type', 'N/A')}\n"
            contexto += f"  🔧 Función/Clase: {fragment.get('functionName', 'N/A')}\n"
            contexto += f"  📦 Módulo: {fragment.get('module', 'N/A')}\n"
            contexto += f"  💻 Lenguaje: {fragment.get('language', 'N/A')}\n"
            contexto += f"  📊 Complejidad: {fragment.get('complexity', 'N/A')}\n"
            contexto += f"  📝 Descripción: {fragment.get('description', 'N/A')}\n"
            
            # Mostrar contenido truncado
            content = fragment.get('content', '')
            if len(content) > 400:
                content = content[:400] + "..."
            contexto += f"  💾 Contenido:\n{content}\n"
            contexto += f"  {'-' * 50}\n\n"
        
        if len(fragmentos) > 8:
            contexto += f"... y {len(fragmentos) - 8} fragmentos más.\n"
        
        return contexto

class PromptGenerator:
    """Generador de prompts para diferentes tipos de consultas"""
    
    def __init__(self):
        pass
    
    def generar_prompt(self, pregunta_usuario, contexto, esquema):
        """Genera un prompt optimizado basado en el contexto y la pregunta"""
        return f"""Basándote en el siguiente contexto de fragmentos de código, responde la pregunta del usuario de manera clara y estructurada:

PREGUNTA: {pregunta_usuario}

CONTEXTO:
{contexto}

Responde en español de manera técnica pero comprensible.""" 