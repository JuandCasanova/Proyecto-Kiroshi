"""Skill: clasifica el objetivo marcado en una jerarquia de clases.

La granularidad de la taxonomia es parametrizable: el mismo target puede
devolverse como "recipiente" o como "copa_de_vino".

Enfoque para diferenciacion fina:
- Usa SOLO rasgos visibles en mark (no conoce uso intencional).
- Cuando varias clases hermanas comparten rasgos, devolver CANDIDATOS MULTIPLES con ambiguity>0.
- Reporta discriminadores requeridos para CADA candidato (feature_extractor los usara).
- Prioriza discriminadores medibles estructuralmente.
"""

from core.skill_base.base_skill import BaseSkill


class TargetClassifierSkill(BaseSkill):
    name = "target_classifier"

    TAXONOMY_PATH = "config/taxonomy.yaml"

    def run(self, params: dict) -> dict:
        raise NotImplementedError