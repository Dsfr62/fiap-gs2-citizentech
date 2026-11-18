"""Camada prata: o dado limpo e padronizado.

Le tudo o que esta na bronze (simulado e API), e:
1. padroniza os nomes das colunas e cria a chave do canteiro ("sim-101", "api-1");
2. limpa as leituras: horario ilegivel, valor fora da faixa e leitura repetida;
3. acerta o fuso: a API e o sensor mandam em UTC (ou com -03:00), o Open-Meteo manda em hora local.
   Tudo vira hora local de Sao Paulo, sem fuso no texto, para o Power BI;
4. junta o clima hora a hora em cada leitura;
5. descobre a resposta de cada alerta ("fiz", "nao fiz" ou "aguardando") pelas regas registradas.
Cada limpeza fica contada em prata/qualidade.csv (vai para o PDF como evidencia).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from comum import BRONZE, FAIXAS, FUSO, PRATA, REFERENCIAS, ler_csv, ler_json, salvar_csv

JANELA_DA_RESPOSTA = pd.Timedelta(hours=24)


# ---------------------------------------------------------------- leitura da bronze

def _fontes() -> list[tuple[str, Path]]:
    fontes = []
    if (BRONZE / "simulado").exists():
        fontes.append(("simulado", BRONZE / "simulado"))
    if (BRONZE / "api").exists():
        fontes += [("api", pasta) for pasta in sorted((BRONZE / "api").iterdir()) if pasta.is_dir()]
    return fontes


def carregar_bronze() -> dict[str, pd.DataFrame]:
    """Junta as fontes da bronze por entidade, com a coluna "origem"."""
    partes: dict[str, list[pd.DataFrame]] = {"canteiros": [], "leituras": [], "recomendacoes": [], "regas": []}
    for origem, pasta in _fontes():
        for entidade in partes:
            arquivo = pasta / f"{entidade}.json"
            if arquivo.exists():
                df = pd.DataFrame(ler_json(arquivo))
                if not df.empty:
                    # o alerta ja tem um campo "origem" (IA ou REGRA_BASICA): guarda antes de marcar a fonte
                    df = df.rename(columns={"origem": "origem_registro"})
                    partes[entidade].append(df.assign(origem=origem))
    tabelas = {}
    for entidade, lista in partes.items():
        df = pd.concat(lista, ignore_index=True) if lista else pd.DataFrame()
        if not df.empty:
            # a mesma exportacao da API pode vir mais de uma vez: fica a mais recente de cada id
            df = df.drop_duplicates(subset=["origem", "id"], keep="last")
        tabelas[entidade] = df
    return tabelas


def chave(origem: pd.Series, canteiro_id: pd.Series) -> pd.Series:
    return origem.str[:3] + "-" + canteiro_id.astype(int).astype(str)


def para_hora_local(texto: pd.Series) -> pd.Series:
    """Texto ISO (com Z ou com -03:00) -> hora local de Sao Paulo, sem fuso. Ilegivel vira NaT."""
    momento = pd.to_datetime(texto, utc=True, format="ISO8601", errors="coerce")
    return momento.dt.tz_convert(FUSO).dt.tz_localize(None)


# ---------------------------------------------------------------- limpeza

def limpar_leituras(bruto: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
    qualidade = []
    df = bruto.rename(columns={"id": "leitura_id", "canteiroId": "canteiro_id", "umidadeSolo": "umidade_solo",
                               "temperaturaAr": "temperatura_ar", "registradaEm": "registrada_em"})
    df["canteiro_chave"] = chave(df["origem"], df["canteiro_id"])
    entrada = len(df)
    qualidade.append({"tabela": "leituras", "etapa": "entrada (bronze)", "linhas": entrada, "removidas": 0})

    df["momento_local"] = para_hora_local(df["registrada_em"])
    ilegivel = df["momento_local"].isna()
    qualidade.append({"tabela": "leituras", "etapa": "horario ilegivel", "linhas": int((~ilegivel).sum()),
                      "removidas": int(ilegivel.sum())})
    df = df[~ilegivel]

    dentro = pd.Series(True, index=df.index)
    for coluna, (minimo, maximo) in FAIXAS.items():
        dentro &= df[coluna].between(minimo, maximo)
    qualidade.append({"tabela": "leituras", "etapa": "fora da faixa (sensor com defeito)",
                      "linhas": int(dentro.sum()), "removidas": int((~dentro).sum())})
    df = df[dentro]

    antes = len(df)
    # a mesma leitura no mesmo instante, mesmo que uma venha em UTC e a outra em -03:00
    df = df.sort_values("leitura_id").drop_duplicates(subset=["canteiro_chave", "momento_local"], keep="first")
    qualidade.append({"tabela": "leituras", "etapa": "repetida (reenvio)", "linhas": len(df),
                      "removidas": antes - len(df)})

    df["hora_local"] = df["momento_local"].dt.floor("h")
    colunas = ["canteiro_chave", "leitura_id", "origem", "momento_local", "hora_local",
               "umidade_solo", "temperatura_ar", "luminosidade"]
    return df[colunas].sort_values(["canteiro_chave", "momento_local"]).reset_index(drop=True), qualidade


def preparar_clima() -> tuple[pd.DataFrame, list[dict]]:
    """Todos os arquivos de clima da bronze -> uma linha por hora local."""
    arquivos = sorted((BRONZE / "clima").glob("historico_*.json")) + sorted((BRONZE / "clima").glob("recente_*.json"))
    partes = []
    for arquivo in arquivos:
        hora = pd.DataFrame(ler_json(arquivo)["hourly"])
        partes.append(hora.assign(fonte=arquivo.stem.split("_")[0]))
    if not partes:
        return pd.DataFrame(columns=["hora_local", "temperatura_clima", "umidade_ar", "chuva_mm", "et0_mm"]), []
    df = pd.concat(partes, ignore_index=True).rename(columns={
        "temperature_2m": "temperatura_clima", "relative_humidity_2m": "umidade_ar",
        "precipitation": "chuva_mm", "et0_fao_evapotranspiration": "et0_mm"})
    df["hora_local"] = pd.to_datetime(df["time"])     # o Open-Meteo ja manda em hora local (timezone=America/Sao_Paulo)
    entrada = len(df)
    df = df.dropna(subset=["temperatura_clima", "umidade_ar", "chuva_mm"])
    df = df[df["umidade_ar"].between(0, 100) & (df["chuva_mm"] >= 0)]
    validas = len(df)
    df = df.drop_duplicates(subset=["hora_local"], keep="first")   # o historico vem antes do recente
    qualidade = [{"tabela": "clima", "etapa": "entrada (bronze)", "linhas": entrada, "removidas": 0},
                 {"tabela": "clima", "etapa": "sem valor ou fora da faixa", "linhas": validas, "removidas": entrada - validas},
                 {"tabela": "clima", "etapa": "hora repetida entre arquivos", "linhas": len(df), "removidas": validas - len(df)}]
    colunas = ["hora_local", "temperatura_clima", "umidade_ar", "chuva_mm", "et0_mm", "fonte"]
    return df[colunas].sort_values("hora_local").reset_index(drop=True), qualidade


def preparar_canteiros(bruto: pd.DataFrame) -> pd.DataFrame:
    df = bruto.rename(columns={"id": "canteiro_id", "areaM2": "area_m2", "vazaoLitrosMin": "vazao_l_min",
                               "umidadeMinima": "umidade_minima"})
    df["canteiro_chave"] = chave(df["origem"], df["canteiro_id"])
    comunidades = ler_csv(REFERENCIAS / "comunidades.csv")
    df = df.merge(comunidades, on="produtor", how="left")
    df["comunidade"] = df["comunidade"].fillna("Sem comunidade")
    colunas = ["canteiro_chave", "canteiro_id", "origem", "nome", "cultura", "produtor", "comunidade",
               "area_m2", "vazao_l_min", "umidade_minima"]
    return df[colunas].sort_values("canteiro_chave").reset_index(drop=True)


def preparar_regas(bruto: pd.DataFrame) -> pd.DataFrame:
    if bruto.empty:
        return pd.DataFrame(columns=["rega_id", "canteiro_chave", "momento_local", "minutos", "litros", "seguiu_recomendacao"])
    df = bruto.rename(columns={"id": "rega_id", "canteiroId": "canteiro_id", "seguiuRecomendacao": "seguiu_recomendacao"})
    df["canteiro_chave"] = chave(df["origem"], df["canteiro_id"])
    df["momento_local"] = para_hora_local(df["feitaEm"])
    return df[["rega_id", "canteiro_chave", "momento_local", "minutos", "litros", "seguiu_recomendacao"]].dropna(
        subset=["momento_local"]).sort_values(["canteiro_chave", "momento_local"]).reset_index(drop=True)


def preparar_alertas(bruto: pd.DataFrame) -> pd.DataFrame:
    df = bruto.rename(columns={"id": "alerta_id", "canteiroId": "canteiro_id", "chuvaPrevistaMm": "chuva_prevista_mm",
                               "umidadeSoloUsada": "umidade_solo_usada"})
    df["canteiro_chave"] = chave(df["origem"], df["canteiro_id"])
    df["momento_local"] = para_hora_local(df["criadaEm"])
    # quem decidiu o alerta: a IA (Area 1) ou a regra basica, quando a IA nao respondeu
    df["decidido_por"] = df["origem_registro"].fillna("REGRA_BASICA")
    colunas = ["alerta_id", "canteiro_chave", "momento_local", "regar", "minutos", "litros",
               "chuva_prevista_mm", "umidade_solo_usada", "decidido_por", "explicacao"]
    return df[colunas].dropna(subset=["momento_local"]).sort_values(["canteiro_chave", "momento_local"]).reset_index(drop=True)


def resposta_dos_alertas(alertas: pd.DataFrame, regas: pd.DataFrame, fim_por_canteiro: pd.Series) -> pd.Series:
    """'1 fiz / 2 nao fiz': hoje a resposta vem da rega registrada nas 24 h depois do alerta.

    - alerta "regar": fiz = houve rega marcada como "seguiu a recomendacao";
    - alerta "nao precisa regar": fiz = nao houve rega nenhuma;
    - se as 24 h ainda nao passaram e nada confirmou: aguardando.
    """
    pares = alertas[["alerta_id", "canteiro_chave", "momento_local"]].merge(
        regas[["canteiro_chave", "momento_local", "seguiu_recomendacao"]].rename(columns={"momento_local": "rega_em"}),
        on="canteiro_chave", how="left")
    na_janela = (pares["rega_em"] > pares["momento_local"]) & (pares["rega_em"] <= pares["momento_local"] + JANELA_DA_RESPOSTA)
    pares = pares[na_janela]
    houve_rega = pares.groupby("alerta_id").size().reindex(alertas["alerta_id"], fill_value=0).to_numpy() > 0
    seguiu = pares[pares["seguiu_recomendacao"].astype(bool)].groupby("alerta_id").size().reindex(
        alertas["alerta_id"], fill_value=0).to_numpy() > 0

    fim = alertas["canteiro_chave"].map(fim_por_canteiro)
    janela_aberta = (alertas["momento_local"] + JANELA_DA_RESPOSTA > fim).to_numpy()
    regar = alertas["regar"].astype(bool).to_numpy()

    fiz = (regar & seguiu) | (~regar & ~houve_rega)
    # com a janela aberta, so fica certo o que ja aconteceu: a rega seguida (fiz) ou a rega sem precisar (nao fiz)
    ainda_pode_mudar = janela_aberta & ((regar & ~seguiu) | (~regar & ~houve_rega))
    resposta = pd.Series(["fiz" if f else "não fiz" for f in fiz], index=alertas.index)
    resposta[ainda_pode_mudar] = "aguardando"
    return resposta


# ---------------------------------------------------------------- etapa

def rodar() -> dict[str, int]:
    bronze = carregar_bronze()
    if bronze["leituras"].empty:
        raise SystemExit("A bronze esta vazia: rode a ingestao ou o gerador antes (python pipeline.py).")

    leituras, q_leituras = limpar_leituras(bronze["leituras"])
    clima, q_clima = preparar_clima()
    leituras = leituras.merge(clima.drop(columns=["fonte"]), on="hora_local", how="left")
    sem_clima = int(leituras["chuva_mm"].isna().sum())
    q_leituras.append({"tabela": "leituras", "etapa": "juntadas ao clima da mesma hora",
                       "linhas": len(leituras) - sem_clima, "removidas": 0})

    canteiros = preparar_canteiros(bronze["canteiros"])
    regas = preparar_regas(bronze["regas"])
    alertas = preparar_alertas(bronze["recomendacoes"])
    fim = leituras.groupby("canteiro_chave")["momento_local"].max()
    alertas["resposta"] = resposta_dos_alertas(alertas, regas, fim)

    saidas = {"canteiros": canteiros, "leituras": leituras, "clima_hora": clima, "alertas": alertas, "regas": regas,
              "qualidade": pd.DataFrame(q_leituras + q_clima)}
    for nome, df in saidas.items():
        salvar_csv(df, PRATA / f"{nome}.csv")
    contagem = {nome: len(df) for nome, df in saidas.items() if nome != "qualidade"}
    removidas = sum(q["removidas"] for q in q_leituras)
    print(f"  prata: {contagem}; leituras removidas na limpeza: {removidas}")
    return contagem


if __name__ == "__main__":
    rodar()
