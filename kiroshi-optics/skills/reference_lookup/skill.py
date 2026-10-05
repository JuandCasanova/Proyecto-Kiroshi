"""Skill: consulta referencias externas para confirmar candidatos o resolver gaps.

Es la unica skill con permiso de red en el pipeline de escaneo. Existe para
que el agente de especificidad pueda exigir verificacion antes de aceptar un
atributo en modo estricto, en lugar de confiar en el modelo.
"""

from core.skill_base.base_skill import BaseSkill


class ReferenceLookupSkill(BaseSkill):
    name = "reference_lookup"

    def run(self, params: dict) -> dict:
        raise NotImplementedError