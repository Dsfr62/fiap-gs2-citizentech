"""Ingestao (camada bronze): busca o dado e guarda do jeito que veio, sem mexer.

Duas fontes:
1. Clima real de Ibiuna (SP) no Open-Meteo, sem chave de API.
   Sem internet, usa a copia guardada em amostra/ (o mesmo arquivo que a API devolveu em 18/11/2026).
2. A API do Sereno (Area 3): canteiros, leituras dos sensores, alertas e regas,
   com o login da tecnica Ana (so o papel TECNICO pode exportar).

So biblioteca padrao (urllib) para a rede; nada a instalar alem do pandas do pipeline.
"""
from __future__ import annotations

import json
import shutil
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from comum import AMOSTRA, BRONZE, IBIUNA, PERIODO_SIMULADO, VARIAVEIS_CLIMA, FUSO, salvar_json, salvar_texto

URL_ARQUIVO = "https://archive-api.open-meteo.com/v1/archive"
URL_PREVISAO = "https://api.open-meteo.com/v1/forecast"


def _baixar(url: str, corpo: dict | None = None, token: str | None = None, timeout: int = 30) -> str:
    """GET (ou POST com JSON) e devolve o texto da resposta como veio."""
    cabecalhos = {"Accept": "application/json", "User-Agent": "sereno-pipeline-fiap"}
    dados = None
    if corpo is not None:
        dados = json.dumps(corpo).encode("utf-8")
        cabecalhos["Content-Type"] = "application/json"
    if token:
        cabecalhos["Authorization"] = f"Bearer {token}"
    pedido = urllib.request.Request(url, data=dados, headers=cabecalhos)
    for tentativa in (1, 2):   # a rede do campo cai: tenta de novo uma vez antes de desistir
        try:
            with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
                return resposta.read().decode("utf-8")
        except urllib.error.HTTPError:
            raise   # resposta de erro da API (401, 403...): tentar de novo nao adianta
        except (urllib.error.URLError, TimeoutError, OSError):
            if tentativa == 2:
                raise
    raise RuntimeError("inalcancavel")


def _url_clima(base: str, **extra) -> str:
    parametros = {
        "latitude": IBIUNA[0],
        "longitude": IBIUNA[1],
        "hourly": VARIAVEIS_CLIMA,
        "timezone": FUSO,
        **extra,
    }
    return f"{base}?{urllib.parse.urlencode(parametros)}"


def ingerir_clima_historico(offline: bool = False) -> Path:
    """Clima hora a hora dos 60 dias do historico simulado (Open-Meteo, arquivo historico)."""
    inicio, fim = PERIODO_SIMULADO
    destino = BRONZE / "clima" / f"historico_{inicio}_{fim}.json"
    amostra = AMOSTRA / f"clima_ibiuna_{inicio}_{fim}.json"
    if not offline:
        try:
            texto = _baixar(_url_clima(URL_ARQUIVO, start_date=inicio, end_date=fim))
            salvar_texto(destino, texto)
            print(f"  clima: Open-Meteo respondeu ({len(texto) // 1024} KB) -> {destino.relative_to(BRONZE.parent)}")
            return destino
        except (urllib.error.URLError, TimeoutError, OSError) as erro:
            print(f"  clima: Open-Meteo fora do alcance ({erro}); usando a copia guardada em amostra/")
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(amostra, destino)
    print(f"  clima: copia de amostra/ -> {destino.relative_to(BRONZE.parent)}")
    return destino


def ingerir_clima_recente() -> Path | None:
    """Clima das ultimas 2 semanas (e dos proximos 2 dias), para juntar com as leituras que vem da API."""
    hoje = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    destino = BRONZE / "clima" / f"recente_{hoje}.json"
    try:
        texto = _baixar(_url_clima(URL_PREVISAO, past_days=14, forecast_days=2))
    except (urllib.error.URLError, TimeoutError, OSError) as erro:
        print(f"  clima recente: Open-Meteo fora do alcance ({erro}); as leituras da API ficam sem clima")
        return None
    salvar_texto(destino, texto)
    print(f"  clima recente: {destino.relative_to(BRONZE.parent)}")
    return destino


def ingerir_api(url_api: str, email: str, senha: str, dias: int = 60) -> Path:
    """Exporta da API do Sereno, logada como tecnica, e guarda cada resposta crua."""
    url_api = url_api.rstrip("/")
    login = json.loads(_baixar(f"{url_api}/api/auth/login", corpo={"email": email, "senha": senha}))
    token = login["token"]
    carimbo = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    pasta = BRONZE / "api" / carimbo
    desde = (datetime.now(timezone.utc) - timedelta(days=dias)).strftime("%Y-%m-%dT%H:%M:%SZ")
    contagem = {}
    for entidade in ("canteiros", "leituras", "recomendacoes", "regas"):
        url = f"{url_api}/api/dados/{entidade}"
        if entidade != "canteiros":
            url += "?" + urllib.parse.urlencode({"desde": desde})
        texto = _baixar(url, token=token)
        salvar_texto(pasta / f"{entidade}.json", texto)
        contagem[entidade] = len(json.loads(texto))
    salvar_json(pasta / "_sobre.json", {"origem": "api", "url": url_api, "usuario": email,
                                        "exportado_em": carimbo, "desde": desde, "registros": contagem})
    print(f"  api: {contagem} -> {pasta.relative_to(BRONZE.parent)}")
    return pasta
