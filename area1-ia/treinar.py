"""Treina o modelo de irrigacao do Sereno com a camada prata da Area 2.

A pergunta que o modelo responde: "se ninguem regar, quanto a umidade do solo vai mudar nas proximas 24 horas?"
Com essa resposta, a IA sabe se o canteiro vai secar (regar hoje) ou se a chuva da conta (nao regar).

Dados: as leituras limpas da prata (sensor + clima real hora a hora). Cada exemplo e um canteiro as 6 h:
- entradas: umidade do solo e temperatura agora, chuva, evapotranspiracao (a agua que o sol e o vento tiram),
  temperatura maxima e umidade do ar das 24 h seguintes, e a cultura;
- resposta certa: a umidade 24 h depois menos a de agora, so nos dias SEM rega (para medir o solo sozinho).

Modelo: floresta aleatoria de regressao (scikit-learn, capitulo "IA - Machine Learning"), semente fixa.
Teste honesto: treina nos primeiros 42 dias e mede nos 18 ultimos, que o modelo nunca viu.

Rodar: python treinar.py   (se a prata nao existir, roda antes o pipeline da Area 2 sem internet)
"""
from __future__ import annotations

import json
import pickle
import subprocess
import sys

import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

from base import AREA2, COLUNAS, METRICAS, MODELO

PRATA = AREA2 / "dados" / "prata"
SEMENTE = 2026
CORTE_TREINO_TESTE = pd.Timestamp("2026-10-13")   # treino antes, teste a partir desta data
HORA_DA_DECISAO = 6


def garantir_prata() -> None:
    if not (PRATA / "leituras.csv").exists():
        print("  a prata da Area 2 nao existe ainda: rodando python area2-dados/pipeline.py --offline")
        subprocess.run([sys.executable, str(AREA2 / "pipeline.py"), "--offline"], check=True, cwd=AREA2)


def montar_exemplos() -> pd.DataFrame:
    """Um exemplo por canteiro e por dia, as 6 h, so dos canteiros simulados e sem rega nas 24 h seguintes."""
    ler = lambda nome, datas: pd.read_csv(PRATA / f"{nome}.csv", encoding="utf-8-sig", parse_dates=datas)  # noqa: E731
    leituras = ler("leituras", ["hora_local"])
    clima = ler("clima_hora", ["hora_local"]).set_index("hora_local").sort_index()
    canteiros = ler("canteiros", None)
    regas = ler("regas", ["momento_local"])

    leituras = leituras[leituras["canteiro_chave"].str.startswith("sim-")]
    hora = leituras.groupby(["canteiro_chave", "hora_local"], as_index=False).agg(
        umidade_solo=("umidade_solo", "mean"), temperatura_ar=("temperatura_ar", "mean"))
    agora = hora[hora["hora_local"].dt.hour == HORA_DA_DECISAO]
    depois = hora.assign(hora_local=hora["hora_local"] - pd.to_timedelta(24, unit="h"))[
        ["canteiro_chave", "hora_local", "umidade_solo"]].rename(columns={"umidade_solo": "umidade_24h"})
    ex = agora.merge(depois, on=["canteiro_chave", "hora_local"], how="inner")

    # a "previsao": o clima real das 24 h seguintes (no servico, vem da previsao do Open-Meteo)
    janela = clima.rolling("24h").agg({"chuva_mm": "sum", "et0_mm": "sum", "temperatura_clima": "max", "umidade_ar": "mean"})
    janela.index = janela.index.shift(-23, freq="h")              # rolling olha para tras: vira "das proximas 24 h"
    janela = janela.rename(columns={"chuva_mm": "chuva_24h", "et0_mm": "et0_24h",
                                    "temperatura_clima": "temp_max_24h", "umidade_ar": "umidade_ar_24h"})
    ex = ex.merge(janela, left_on="hora_local", right_index=True, how="inner")

    # tira os dias com rega na janela: o modelo aprende o solo sozinho
    r = regas[regas["canteiro_chave"].str.startswith("sim-")]
    com_rega = set()
    for _, rega in r.iterrows():
        inicio = rega["momento_local"].replace(hour=HORA_DA_DECISAO, minute=0, second=0, microsecond=0)
        if rega["momento_local"] < inicio:
            inicio = inicio - pd.to_timedelta(1, unit="D")
        com_rega.add((rega["canteiro_chave"], inicio))
    ex = ex[[(c, h) not in com_rega for c, h in zip(ex["canteiro_chave"], ex["hora_local"])]]

    cultura = canteiros.set_index("canteiro_chave")["cultura"]
    ex["cultura"] = ex["canteiro_chave"].map(cultura)
    for nome in ("FOLHOSA", "FRUTO", "RAIZ"):
        ex[nome.lower()] = (ex["cultura"] == nome).astype(int)
    ex["variacao_24h"] = ex["umidade_24h"] - ex["umidade_solo"]
    ex = ex.dropna(subset=COLUNAS + ["variacao_24h"])
    return ex.sort_values(["hora_local", "canteiro_chave"]).reset_index(drop=True)


def treinar() -> dict:
    garantir_prata()
    ex = montar_exemplos()
    treino = ex[ex["hora_local"] < CORTE_TREINO_TESTE]
    teste = ex[ex["hora_local"] >= CORTE_TREINO_TESTE]

    modelo = RandomForestRegressor(n_estimators=150, max_depth=8, min_samples_leaf=3, random_state=SEMENTE)
    modelo.fit(treino[COLUNAS], treino["variacao_24h"])
    previsto = modelo.predict(teste[COLUNAS])

    # duas referencias: "nada muda" (o piso) e a formula do proprio simulador (o gabarito, que usa os numeros
    # que nos pusemos no gerador da Area 2; no campo ninguem sabe esses numeros para cada solo)
    parado = [0.0] * len(teste)
    gabarito = (-2.5 * teste["et0_24h"] + 2.0 * teste["chuva_24h"]).clip(upper=70 - teste["umidade_solo"])
    metricas = {
        "exemplos_treino": int(len(treino)),
        "exemplos_teste": int(len(teste)),
        "periodo_treino": f"{treino['hora_local'].min():%d/%m} a {treino['hora_local'].max():%d/%m/%Y}",
        "periodo_teste": f"{teste['hora_local'].min():%d/%m} a {teste['hora_local'].max():%d/%m/%Y}",
        "erro_medio_modelo_pontos": round(mean_absolute_error(teste["variacao_24h"], previsto), 2),
        "erro_medio_se_nada_mudasse_pontos": round(mean_absolute_error(teste["variacao_24h"], parado), 2),
        "erro_medio_gabarito_do_simulador_pontos": round(mean_absolute_error(teste["variacao_24h"], gabarito), 2),
        "r2_modelo": round(r2_score(teste["variacao_24h"], previsto), 3),
        "importancia": {c: round(float(v), 3) for c, v in sorted(
            zip(COLUNAS, modelo.feature_importances_), key=lambda x: -x[1])},
        "semente": SEMENTE,
    }
    # o modelo final usa todos os dias (treino + teste): mais exemplo, mesma receita
    modelo.fit(ex[COLUNAS], ex["variacao_24h"])
    MODELO.parent.mkdir(parents=True, exist_ok=True)
    with open(MODELO, "wb") as arquivo:
        pickle.dump(modelo, arquivo)
    METRICAS.write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  exemplos: {metricas['exemplos_treino']} de treino ({metricas['periodo_treino']}), "
          f"{metricas['exemplos_teste']} de teste ({metricas['periodo_teste']})")
    print(f"  erro medio no teste (pontos de umidade em 24 h): modelo {metricas['erro_medio_modelo_pontos']}, "
          f"gabarito do simulador {metricas['erro_medio_gabarito_do_simulador_pontos']}, "
          f"se nada mudasse {metricas['erro_medio_se_nada_mudasse_pontos']}; R2 do modelo {metricas['r2_modelo']}")
    print(f"  o que mais pesa: {list(metricas['importancia'])[:3]}")
    print(f"  modelo salvo em {MODELO.relative_to(MODELO.parents[1])}")
    return metricas


def carregar():
    """Abre o modelo salvo (so o arquivo que o treinar.py gerou nesta maquina); treina se nao existir."""
    if not MODELO.exists():
        treinar()
    with open(MODELO, "rb") as arquivo:
        return pickle.load(arquivo)


if __name__ == "__main__":
    treinar()
