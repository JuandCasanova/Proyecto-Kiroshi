"""Skill: sube la especificidad del resultado hasta donde la evidencia permita.

Funcionamiento: recibe los discriminadores faltantes, los ordena por impacto en
la especificidad (pesos de taxonomia) y solicita evidencia directa para
resolverlos. Acepta solo valores verificables. Criterio de parada:
- alcanza target_specificity
- ganancia por pasada < MIN_GAIN_PER_PASS
- supera MAX_PASSES

Reglas para maxima especificidad (diferenciacion fina):
- Ordenar faltantes por ganancia esperada (prioriza los que desbloquean nivel mas alto).
- Para cada faltante: ¿existe evidencia medible en mark? Si NO -> ausente.
- Requiere alta confianza (>= 0.7) para aceptar un valor.
- Nunca mezclar contexto con atributos del objeto.
- En recipientes: dar prioridad a apertura, cuello, hombros, pie, tallo/stem, asas.
- En electronicos: dar prioridad a proporciones pantalla/cuerpo, bezels, orientacion visible.
- Si despues de evaluar TODOS los faltantes medibles no hay ganancia -> detenerse.
"""

from core.skill_base.base_skill import BaseSkill


class SpecificityEnhancerSkill(BaseSkill):
    name = "specificity_enhancer"

    MAX_PASSES = 3
    MIN_GAIN_PER_PASS = 0.02

    def run(self, params: dict) -> dict:
        raise NotImplementedError