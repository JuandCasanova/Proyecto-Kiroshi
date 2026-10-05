"""Skill: normaliza "lo marcado" en una estructura unica de entrada.

Es la unica skill que entiende formatos crudos de entrada. Todo lo demas
consume un Mark normalizado, lo que hace que el resto del pipeline sea
agnostico al modo de captura (region de imagen, texto, archivo, audio).
"""

from core.skill_base.base_skill import BaseSkill


class MarkParserSkill(BaseSkill):
    name = "mark_parser"

    def run(self, params: dict) -> dict:
        raise NotImplementedError