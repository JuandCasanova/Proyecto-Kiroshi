"""Agente de escaneo: coordina el pipeline completo de Kiroshi Optics.

Pipeline: mark_parser -> target_classifier -> feature_extractor ->
specificity_enhancer -> scan_validator.

Su unica responsabilidad es delegar en las skills en el orden correcto y
propagar el resultado. No decide ni interpreta: eso es trabajo de las skills.
"""

from core.agent_base.base_agent import BaseAgent


class ScanAgent(BaseAgent):
    name = "scan_agent"

    PIPELINE = [
        "mark_parser",
        "target_classifier",
        "feature_extractor",
        "specificity_enhancer",
        "scan_validator",
    ]

    def run(self, task: dict) -> dict:
        raise NotImplementedError