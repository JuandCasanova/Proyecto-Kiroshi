"""Skill: valida que un escaneo cumple el contrato de especificidad de Kiroshi.

Es la unica skill autorizada para aprobar o rechazar un escaneo. Verifica
coherencia interna contra la taxonomia y calcula la especificidad efectiva,
de modo que "especifico" sea una cifra reproducible y no una sensacion.
"""

from core.skill_base.base_skill import BaseSkill


class ScanValidatorSkill(BaseSkill):
    name = "scan_validator"

    MIN_ACCEPTABLE = 0.55

    def run(self, params: dict) -> dict:
        raise NotImplementedError