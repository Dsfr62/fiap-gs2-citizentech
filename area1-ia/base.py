"""O que as partes da IA do Sereno (Area 1) dividem: caminhos, as colunas do modelo e a fisica do solo.

A fisica do solo (quanto a umidade cai com o sol e sobe com chuva e rega) e a MESMA do gerador da Area 2:
importamos de area2-dados/gerador.py para nao ter duas versoes da mesma conta.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
AREA2 = RAIZ.parent / "area2-dados"
if str(AREA2) not in sys.path:
    sys.path.insert(0, str(AREA2))

import gerador  # noqa: E402  (area2-dados/gerador.py)

MODELO = RAIZ / "modelo" / "modelo.pkl"
METRICAS = RAIZ / "modelo" / "metricas.json"
AMOSTRA = RAIZ / "amostra"
RESULTADOS = RAIZ / "resultados"
EXEMPLOS = RAIZ / "exemplos"

# Entradas do modelo: o sensor agora + a previsao das proximas 24 h + a cultura.
COLUNAS = ["umidade_solo", "temperatura_ar", "chuva_24h", "et0_24h", "temp_max_24h", "umidade_ar_24h",
           "folhosa", "fruto", "raiz"]

MM_POR_PONTO = 0.4          # como a RegraBasica da API: 1 ponto de umidade = 0,4 mm de agua
LAMINA_MAXIMA_MM = 8.0
PONTOS_ACIMA_DO_MINIMO = 10  # alvo da rega = minimo da cultura + 10 pontos

NOME_DA_CULTURA = {"FOLHOSA": "folhosas", "FRUTO": "plantas de fruto", "RAIZ": "raízes"}


def linha(umidade_solo: float, temperatura_ar: float, cultura: str, previsao_24h: dict) -> dict:
    """Monta uma linha de entrada do modelo."""
    return {
        "umidade_solo": umidade_solo,
        "temperatura_ar": temperatura_ar,
        "chuva_24h": previsao_24h["chuva_24h"],
        "et0_24h": previsao_24h["et0_24h"],
        "temp_max_24h": previsao_24h["temp_max_24h"],
        "umidade_ar_24h": previsao_24h["umidade_ar_24h"],
        "folhosa": int(cultura == "FOLHOSA"),
        "fruto": int(cultura == "FRUTO"),
        "raiz": int(cultura == "RAIZ"),
    }
