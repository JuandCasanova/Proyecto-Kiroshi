"""Skill: extrae los atributos que distinguen un candidato de sus vecinos.

Este es el motor de especificidad. Cada taxonomia declara sus
discriminators (atributos que la separan de la clase hermana) y este modulo
solo extrae esos, ignorando cualquier atributo que no ayude a desambiguar.

Reglas para maxima discriminacion (botella vs vaso vs copa, telefono vs tablet):
- Prioriza rasgos estructurales medibles: forma, apertura, cuello, pie/stem, asas, proporciones, bezels.
- NO infiere funcion, uso o material si no es observable.
- Si un discriminador no es visible, marcarlo como ausente. Nunca adivinar.
- Usar terminologia descriptiva y concreta (cilindrico, tronco_conico, ensanchado_en_boca, etc.)
"""

from core.skill_base.base_skill import BaseSkill


class FeatureExtractorSkill(BaseSkill):
    name = "feature_extractor"

    def run(self, params: dict) -> dict:
        raise NotImplementedError