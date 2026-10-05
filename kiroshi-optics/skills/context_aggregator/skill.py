"""Skill: agrega contexto para desambiguar candidatos empatados.

El contexto se usa solo cuando la evidencia directa del objetivo no alcanza
para elegir entre candidatos. Nunca se agrega al resultado final como si fuera
un atributo del objetivo: se registra aparte para no contaminar la especificidad.
"""

from core.skill_base.base_skill import BaseSkill


class ContextAggregatorSkill(BaseSkill):
    name = "context_aggregator"

    def run(self, params: dict) -> dict:
        raise NotImplementedError