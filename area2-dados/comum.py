"""Constantes e funcoes usadas por todas as etapas do pipeline do Sereno (Area 2)."""
import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent
DADOS = RAIZ / "dados"            # gerado pelo pipeline (fora do Git)
BRONZE = DADOS / "bronze"         # o dado cru, como veio
PRATA = DADOS / "prata"           # o dado limpo
OURO = DADOS / "ouro"             # o resumo para analise
POWERBI = RAIZ / "powerbi"        # a saida em CSV para o Power BI (vai para o Git)
AMOSTRA = RAIZ / "amostra"        # copia do clima real, para rodar sem internet
REFERENCIAS = RAIZ / "referencias"

FUSO = "America/Sao_Paulo"
IBIUNA = (-23.6566, -47.2229)     # latitude e longitude
PERIODO_SIMULADO = ("2026-09-01", "2026-10-30")   # 60 dias
SEMENTE = 2026                    # semente fixa: o historico simulado sai sempre igual

# O costume do Seu Jorge (persona em docs/problema.md): 30 minutos de rega todo dia.
MINUTOS_CALENDARIO = 30

# Faixas validas: as mesmas que a API usa para recusar leitura (area3-mvp/api/.../dto/Dtos.java).
FAIXAS = {"umidade_solo": (0, 100), "temperatura_ar": (-10, 60), "luminosidade": (0, 100)}

# Umidade minima por cultura: a mesma da API (area3-mvp/api/.../model/Cultura.java).
UMIDADE_MINIMA = {"FOLHOSA": 45, "FRUTO": 38, "RAIZ": 32}

VARIAVEIS_CLIMA = "temperature_2m,relative_humidity_2m,precipitation,et0_fao_evapotranspiration"


def salvar_texto(caminho: Path, texto: str) -> Path:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(texto, encoding="utf-8")
    return caminho


def salvar_json(caminho: Path, dados) -> Path:
    return salvar_texto(caminho, json.dumps(dados, ensure_ascii=False, indent=1))


def ler_json(caminho: Path):
    return json.loads(Path(caminho).read_text(encoding="utf-8"))


def salvar_csv(df: pd.DataFrame, caminho: Path) -> Path:
    """CSV com virgula entre colunas, ponto nos decimais e UTF-8 com BOM (o Power BI le os acentos)."""
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, index=False, encoding="utf-8-sig", float_format="%.2f")
    return caminho


def ler_csv(caminho: Path, **kwargs) -> pd.DataFrame:
    return pd.read_csv(caminho, encoding="utf-8-sig", **kwargs)
