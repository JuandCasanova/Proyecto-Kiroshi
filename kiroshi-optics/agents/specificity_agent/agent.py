"""Agente de especificidad: eleva la granularidad de un resultado de escaneo.

No inventa informacion. Solo refina lo que ya esta respaldado por evidencia,
subiendo de "objeto" a "variante exacta" mediante los atributos disponibles.
Trabaja sobre el resultado del scan_agent, nunca sobre la marca cruda.
"""

from core.agent_base.base_agent import BaseAgent


class SpecificityAgent(BaseAgent):
    name = "specificity_agent"

    def run(self, task: dict) -> dict:
        raise NotImplementedError