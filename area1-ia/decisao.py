"""A decisao de rega da IA do Sereno.

1. O modelo (treinar.py) preve quanto a umidade do solo vai mudar nas proximas 24 h, sem rega,
   olhando o sensor agora e a previsao do tempo.
2. Se a umidade prevista fica abaixo do minimo da cultura mais uma folga de seguranca de 3 pontos, regar hoje;
   a quantidade leva o solo ao minimo + 10 pontos (0,4 mm por ponto, no maximo 8 mm, como a regra basica da API).
   A folga foi escolhida no periodo de TREINO (2026), por uma regra fixada antes: a menor folga que deixa o solo
   abaixo do minimo em menos de 1% das horas. Com 0 eram 2,5% das horas; com 3, 0,9%.
3. Sem previsao do tempo, a IA nao chuta: decide so pelo sensor, com a regra basica, e diz isso.
"""
from __future__ import annotations

import math

import pandas as pd

from base import COLUNAS, LAMINA_MAXIMA_MM, MM_POR_PONTO, PONTOS_ACIMA_DO_MINIMO, gerador, linha

FOLGA_DE_SEGURANCA = 3   # pontos de umidade acima do minimo


def decidir(pedido: dict, previsao: dict | None, modelo) -> dict:
    cultura = pedido["cultura"]
    umidade = float(pedido["umidadeSolo"])
    minimo = int(pedido["umidadeMinima"])
    area, vazao = float(pedido["areaM2"]), float(pedido["vazaoLitrosMin"])

    if previsao is None:
        regar, minutos, litros, _ = gerador.regra_basica(cultura, area, vazao, umidade,
                                                         float(pedido["temperaturaAr"]), float(pedido["luminosidade"]))
        return {"regar": regar, "minutos": minutos, "litros": litros, "umidade_agora": umidade,
                "umidade_prevista_24h": None, "minimo": minimo, "cultura": cultura,
                "chuva_prevista_mm": None, "com_previsao": False}

    entrada = pd.DataFrame([linha(umidade, float(pedido["temperaturaAr"]), cultura, previsao["proximas_24h"])])[COLUNAS]
    variacao = float(modelo.predict(entrada)[0])
    prevista = max(0.0, min(100.0, umidade + variacao))
    regar = prevista < minimo + FOLGA_DE_SEGURANCA
    minutos, litros = 0, 0.0
    if regar:
        lamina = min((minimo + PONTOS_ACIMA_DO_MINIMO - prevista) * MM_POR_PONTO, LAMINA_MAXIMA_MM)
        litros = float(round(lamina * area))
        minutos = math.ceil(litros / vazao)
    return {"regar": regar, "minutos": minutos, "litros": litros, "umidade_agora": umidade,
            "umidade_prevista_24h": round(prevista, 1), "minimo": minimo, "cultura": cultura,
            "chuva_prevista_mm": previsao["proximas_24h"]["chuva_24h"], "com_previsao": True}
