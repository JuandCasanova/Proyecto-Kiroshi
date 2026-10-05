"""Agente de contexto: aporta variables de entorno que ayudan a desambiguar.

El contexto nunca reemplaza evidencia directa del objetivo: solo se usa para
romper empates cuando dos candidatos son igualmente compatibles con la marca.
"""

from core.agent_base.base_agent import BaseAgent


class ContextAgent(BaseAgent):
    name = "context_agent"

    def run(self, task: dict) -> dict:
        raise NotImplementedError