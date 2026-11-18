"""Previsao do tempo para a IA: o Open-Meteo (sem chave) ou um trecho do clima guardado (demonstracao e avaliacao).

Devolve um resumo:
- proximas_24h: chuva, evapotranspiracao (a agua que o sol e o vento tiram do solo), maxima e umidade do ar;
- dias: os proximos 3 dias, com horas de folha molhada, minima e maxima (para os riscos).
Sem internet ou com SERENO_SEM_PREVISAO=1, devolve None e a IA decide so pelo sensor.
"""
from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime

import pandas as pd

import base  # noqa: F401  (poe area2-dados no caminho)
from ouro import TEMP_DOENCA, UMIDADE_AR_DOENCA  # mesmos limites do painel da Area 2

URL = "https://api.open-meteo.com/v1/forecast"
VARIAVEIS = "temperature_2m,relative_humidity_2m,precipitation,et0_fao_evapotranspiration"
_CACHE: dict = {}
VALIDADE_DO_CACHE_S = 30 * 60


def _hora_a_hora(dados: dict) -> pd.DataFrame:
    df = pd.DataFrame(dados).rename(columns={
        "time": "hora", "temperature_2m": "temperatura", "relative_humidity_2m": "umidade_ar",
        "precipitation": "chuva", "et0_fao_evapotranspiration": "et0"})
    df["hora"] = pd.to_datetime(df["hora"])
    return df.dropna()


def resumir(hora_a_hora: pd.DataFrame, agora: datetime) -> dict | None:
    """Corta a partir da hora atual e resume as proximas 24 h e os proximos 3 dias."""
    inicio = pd.Timestamp(agora).floor("h")
    futuro = hora_a_hora[hora_a_hora["hora"] >= inicio]
    dia24 = futuro[futuro["hora"] < inicio + pd.to_timedelta(24, unit="h")]
    if len(dia24) < 20:
        return None
    futuro = futuro.assign(data=futuro["hora"].dt.normalize())
    futuro["folha_molhada"] = (futuro["umidade_ar"] >= UMIDADE_AR_DOENCA) & futuro["temperatura"].between(*TEMP_DOENCA)
    dias = futuro.groupby("data").agg(horas_folha_molhada=("folha_molhada", "sum"), temp_min=("temperatura", "min"),
                                      temp_max=("temperatura", "max"), chuva=("chuva", "sum")).head(3)
    return {
        "proximas_24h": {
            "chuva_24h": round(float(dia24["chuva"].sum()), 1),
            "et0_24h": round(float(dia24["et0"].sum()), 2),
            "temp_max_24h": round(float(dia24["temperatura"].max()), 1),
            "umidade_ar_24h": round(float(dia24["umidade_ar"].mean()), 1),
        },
        "dias": [{"data": d.date().isoformat(), "horas_folha_molhada": int(r.horas_folha_molhada),
                  "temp_min": round(float(r.temp_min), 1), "temp_max": round(float(r.temp_max), 1),
                  "chuva": round(float(r.chuva), 1)} for d, r in dias.iterrows()],
        "fonte": "",
    }


def do_open_meteo(latitude: float, longitude: float, timeout: float = 2.5) -> dict | None:
    """A API espera a IA por 5 s: a previsao tem 2,5 s para chegar, ou a IA decide so pelo sensor."""
    if os.environ.get("SERENO_SEM_PREVISAO") == "1":
        return None
    chave = (round(latitude, 2), round(longitude, 2))
    guardado = _CACHE.get(chave)
    if guardado and time.time() - guardado[0] < VALIDADE_DO_CACHE_S:
        dados = guardado[1]
    else:
        parametros = {"latitude": latitude, "longitude": longitude, "hourly": VARIAVEIS,
                      "timezone": "America/Sao_Paulo", "forecast_days": 4}
        pedido = urllib.request.Request(f"{URL}?{urllib.parse.urlencode(parametros)}",
                                        headers={"User-Agent": "sereno-ia-fiap"})
        try:
            with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
                dados = json.loads(resposta.read().decode("utf-8"))["hourly"]
        except (OSError, ValueError, KeyError):
            return None
        _CACHE[chave] = (time.time(), dados)
    agora = pd.Timestamp.now(tz="America/Sao_Paulo").tz_localize(None)
    resumo = resumir(_hora_a_hora(dados), agora)
    if resumo:
        resumo["fonte"] = "Open-Meteo (previsão)"
    return resumo


def de_clima_guardado(caminho, agora: datetime) -> dict | None:
    """Usa um arquivo do Open-Meteo ja baixado como se fosse a previsao (demonstracao e avaliacao)."""
    with open(caminho, encoding="utf-8") as arquivo:
        dados = json.load(arquivo)["hourly"]
    resumo = resumir(_hora_a_hora(dados), agora)
    if resumo:
        resumo["fonte"] = "clima guardado (o que de fato aconteceu)"
    return resumo
