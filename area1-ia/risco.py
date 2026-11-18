"""Riscos do clima para os proximos 3 dias: doenca nas folhas, geada e calor.

Sao regras agronomicas simples, documentadas (o enunciado aceita "regras" na Area 1), com os MESMOS limites
que o painel da Area 2 usa (area2-dados/ouro.py), para o aviso e o painel nunca discordarem:
- doenca (ferrugem, mildio): horas no dia com o ar a 95% ou mais e de 15 a 25 graus; 10 h = alto, 6 h = medio;
- geada: minima de 3 graus ou menos = alto; 6 graus ou menos = medio;
- calor: maxima de 32 graus ou mais = alto; 30 ou mais = medio.
"""
from __future__ import annotations

import base  # noqa: F401
from ouro import CALOR_ALTO, CALOR_MEDIO, GEADA_ALTO, GEADA_MEDIO, HORAS_DOENCA_ALTO, HORAS_DOENCA_MEDIO

ORDEM = {"alto": 2, "médio": 1}


def _nivel_doenca(horas):
    return "alto" if horas >= HORAS_DOENCA_ALTO else ("médio" if horas >= HORAS_DOENCA_MEDIO else None)


def _nivel_geada(minima):
    return "alto" if minima <= GEADA_ALTO else ("médio" if minima <= GEADA_MEDIO else None)


def _nivel_calor(maxima):
    return "alto" if maxima >= CALOR_ALTO else ("médio" if maxima >= CALOR_MEDIO else None)


def avaliar(dias: list[dict]) -> list[dict]:
    """Para cada tipo, o pior nivel dos proximos dias e o primeiro dia em que ele aparece."""
    regras = [("doenca", "horas_folha_molhada", _nivel_doenca), ("geada", "temp_min", _nivel_geada),
              ("calor", "temp_max", _nivel_calor)]
    riscos = []
    for tipo, campo, regra in regras:
        pior = None
        for dia in dias:
            nivel = regra(dia[campo])
            if nivel and (pior is None or ORDEM[nivel] > ORDEM[pior["nivel"]]):
                pior = {"tipo": tipo, "nivel": nivel, "data": dia["data"], "valor": dia[campo]}
        if pior:
            riscos.append(pior)
    return sorted(riscos, key=lambda r: -ORDEM[r["nivel"]])
