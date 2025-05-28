"""
Agentes de IA para análisis y consulta de código

Este paquete contiene los agentes especializados para:
- Indexación de fragmentos de código (indexador_fragmentos.py)
- Consulta inteligente de fragmentos (consultor_fragmentos.py) 
- Enrutamiento de modelos de IA (router_ia.py)
"""

from .indexador_fragmentos import CodeAnalysisAgent
from .consultor_fragmentos import FragmentQueryAgent, PromptGenerator
from .router_ia import ModelRouterAgent, TaskType, ModelProvider

__all__ = [
    'CodeAnalysisAgent',
    'FragmentQueryAgent', 
    'PromptGenerator',
    'ModelRouterAgent',
    'TaskType',
    'ModelProvider'
] 