"""Camada ouro: o resumo pronto para analise e a saida em CSV para o Power BI.

Tabelas (modelo estrela: uma tabela de fatos por dia e canteiro, ligada as dimensoes pela chave do canteiro):
- fato_diario_canteiro: um dia de um canteiro: umidade media e minima, horas abaixo do minimo,
  agua usada contra a rega por calendario, chuva, alertas enviados e respostas, e os indicadores de risco do clima;
- dim_canteiro: cultura, produtor e comunidade de cada canteiro (os filtros do painel);
- alertas: um alerta por linha, com a resposta "fiz", "nao fiz" ou "aguardando";
- leituras_por_hora: a curva da umidade do solo, hora a hora, com a chuva;
- resumo_comunidade: os indicadores por comunidade (o que o tecnico da Emater ou da cooperativa olha primeiro).
"""
from __future__ import annotations

import shutil

import pandas as pd

from comum import MINUTOS_CALENDARIO, OURO, POWERBI, PRATA, ler_csv, salvar_csv

# Indicadores de risco do clima, por regra simples (o modelo de risco de verdade e da Area 1).
# Horas de folha molhada no dia: ar com 95% ou mais de umidade e 15 a 25 graus, a faixa em que
# mildio e ferrugem se espalham. Calibrado no clima real de Ibiuna: com 90%, quase todo dia dava "alto".
UMIDADE_AR_DOENCA, TEMP_DOENCA = 95, (15, 25)
HORAS_DOENCA_ALTO, HORAS_DOENCA_MEDIO = 10, 6
GEADA_ALTO, GEADA_MEDIO = 3.0, 6.0                # temperatura minima do ar (graus)
CALOR_ALTO, CALOR_MEDIO = 32.0, 30.0              # temperatura maxima do ar (graus)


def _nivel(valor, alto, medio, maior_e_pior=True) -> str:
    if pd.isna(valor):
        return "sem dado"
    if maior_e_pior:
        return "alto" if valor >= alto else ("médio" if valor >= medio else "baixo")
    return "alto" if valor <= alto else ("médio" if valor <= medio else "baixo")


def carregar_prata() -> dict[str, pd.DataFrame]:
    datas = {"leituras": ["momento_local", "hora_local"], "clima_hora": ["hora_local"],
             "alertas": ["momento_local"], "regas": ["momento_local"]}
    tabelas = {"canteiros": ler_csv(PRATA / "canteiros.csv")}
    for nome, colunas in datas.items():
        tabelas[nome] = ler_csv(PRATA / f"{nome}.csv", parse_dates=colunas)
    return tabelas


def leituras_por_hora(leituras: pd.DataFrame, canteiros: pd.DataFrame) -> pd.DataFrame:
    hora = leituras.groupby(["canteiro_chave", "hora_local"], as_index=False).agg(
        umidade_solo=("umidade_solo", "mean"), temperatura_ar=("temperatura_ar", "mean"),
        luminosidade=("luminosidade", "mean"), chuva_mm=("chuva_mm", "first"), umidade_ar=("umidade_ar", "first"))
    hora = hora.merge(canteiros[["canteiro_chave", "umidade_minima"]], on="canteiro_chave", how="left")
    hora["abaixo_do_minimo"] = hora["umidade_solo"] < hora["umidade_minima"]
    hora["data"] = hora["hora_local"].dt.normalize()
    return hora


def clima_por_dia(clima: pd.DataFrame) -> pd.DataFrame:
    clima = clima.assign(data=clima["hora_local"].dt.normalize())
    clima["favoravel_doenca"] = (clima["umidade_ar"] >= UMIDADE_AR_DOENCA) & clima["temperatura_clima"].between(*TEMP_DOENCA)
    dia = clima.groupby("data", as_index=False).agg(
        chuva_mm=("chuva_mm", "sum"), et0_mm=("et0_mm", "sum"), umidade_ar_media=("umidade_ar", "mean"),
        temp_min_ar=("temperatura_clima", "min"), temp_max_ar=("temperatura_clima", "max"),
        horas_favoraveis_doenca=("favoravel_doenca", "sum"))
    dia["risco_doenca"] = dia["horas_favoraveis_doenca"].map(lambda h: _nivel(h, HORAS_DOENCA_ALTO, HORAS_DOENCA_MEDIO))
    dia["risco_geada"] = dia["temp_min_ar"].map(lambda t: _nivel(t, GEADA_ALTO, GEADA_MEDIO, maior_e_pior=False))
    dia["risco_calor"] = dia["temp_max_ar"].map(lambda t: _nivel(t, CALOR_ALTO, CALOR_MEDIO))
    return dia


def fato_diario(hora: pd.DataFrame, clima_dia: pd.DataFrame, alertas: pd.DataFrame, regas: pd.DataFrame,
                canteiros: pd.DataFrame) -> pd.DataFrame:
    fato = hora.groupby(["canteiro_chave", "data"], as_index=False).agg(
        umidade_media=("umidade_solo", "mean"), umidade_minima_do_dia=("umidade_solo", "min"),
        horas_com_leitura=("umidade_solo", "size"), horas_abaixo_do_minimo=("abaixo_do_minimo", "sum"),
        temp_max_sensor=("temperatura_ar", "max"), temp_min_sensor=("temperatura_ar", "min"))

    a = alertas.assign(data=alertas["momento_local"].dt.normalize())
    a_dia = a.groupby(["canteiro_chave", "data"], as_index=False).agg(
        alertas_enviados=("alerta_id", "size"), alertas_para_regar=("regar", "sum"),
        respostas_fiz=("resposta", lambda r: (r == "fiz").sum()),
        respostas_nao_fiz=("resposta", lambda r: (r == "não fiz").sum()),
        respostas_aguardando=("resposta", lambda r: (r == "aguardando").sum()))

    r = regas.assign(data=regas["momento_local"].dt.normalize())
    r_dia = r.groupby(["canteiro_chave", "data"], as_index=False).agg(
        regas=("rega_id", "size"), minutos_regados=("minutos", "sum"), litros_usados=("litros", "sum"))

    fato = (fato.merge(a_dia, on=["canteiro_chave", "data"], how="left")
                .merge(r_dia, on=["canteiro_chave", "data"], how="left")
                .merge(clima_dia, on="data", how="left")
                .merge(canteiros[["canteiro_chave", "vazao_l_min"]], on="canteiro_chave", how="left"))
    contagens = ["alertas_enviados", "alertas_para_regar", "respostas_fiz", "respostas_nao_fiz",
                 "respostas_aguardando", "regas", "minutos_regados", "litros_usados"]
    fato[contagens] = fato[contagens].fillna(0)
    fato[[c for c in contagens if c != "litros_usados"]] = fato[[c for c in contagens if c != "litros_usados"]].astype(int)
    # "antes": o costume de regar 30 minutos todo dia; "depois": o que o produtor regou com o Sereno
    fato["litros_calendario"] = MINUTOS_CALENDARIO * fato["vazao_l_min"]
    fato["litros_economizados"] = fato["litros_calendario"] - fato["litros_usados"]
    return fato.drop(columns=["vazao_l_min"]).sort_values(["canteiro_chave", "data"]).reset_index(drop=True)


def resumo_comunidade(fato: pd.DataFrame, canteiros: pd.DataFrame) -> pd.DataFrame:
    f = fato.merge(canteiros[["canteiro_chave", "comunidade"]], on="canteiro_chave")
    resumo = f.groupby("comunidade", as_index=False).agg(
        canteiros=("canteiro_chave", "nunique"), dias=("data", "nunique"),
        alertas_enviados=("alertas_enviados", "sum"), respostas_fiz=("respostas_fiz", "sum"),
        respostas_nao_fiz=("respostas_nao_fiz", "sum"), litros_usados=("litros_usados", "sum"),
        litros_calendario=("litros_calendario", "sum"), horas_abaixo_do_minimo=("horas_abaixo_do_minimo", "sum"))
    # dias distintos com risco alto de doenca na comunidade (nao dia x canteiro)
    risco = f[f["risco_doenca"] == "alto"].groupby("comunidade")["data"].nunique()
    resumo["dias_risco_doenca_alto"] = resumo["comunidade"].map(risco).fillna(0).astype(int)
    respondidas = resumo["respostas_fiz"] + resumo["respostas_nao_fiz"]
    resumo["taxa_de_fiz_pct"] = (100 * resumo["respostas_fiz"] / respondidas).round(1)
    resumo["agua_economizada_pct"] = (100 * (1 - resumo["litros_usados"] / resumo["litros_calendario"])).round(1)
    return resumo


def rodar() -> dict[str, int]:
    p = carregar_prata()
    hora = leituras_por_hora(p["leituras"], p["canteiros"])
    fato = fato_diario(hora, clima_por_dia(p["clima_hora"]), p["alertas"], p["regas"], p["canteiros"])
    alertas = p["alertas"].assign(data=p["alertas"]["momento_local"].dt.normalize(),
                                  hora=p["alertas"]["momento_local"].dt.strftime("%H:%M"))
    alertas = alertas[["alerta_id", "canteiro_chave", "data", "hora", "regar", "minutos", "litros",
                       "chuva_prevista_mm", "umidade_solo_usada", "decidido_por", "resposta", "explicacao"]]
    resumo = resumo_comunidade(fato, p["canteiros"])

    saidas = {"fato_diario_canteiro": fato, "dim_canteiro": p["canteiros"], "alertas": alertas,
              "leituras_por_hora": hora, "resumo_comunidade": resumo}
    for nome, df in saidas.items():
        salvar_csv(df, OURO / f"{nome}.csv")
    # saida para o Power BI: a mesma ouro, numa pasta que vai para o Git (da para montar o painel sem rodar nada)
    POWERBI.mkdir(exist_ok=True)
    for nome in saidas:
        shutil.copyfile(OURO / f"{nome}.csv", POWERBI / f"{nome}.csv")

    contagem = {nome: len(df) for nome, df in saidas.items()}
    print(f"  ouro: {contagem} -> dados/ouro/ e powerbi/")
    print("\n  Resumo por comunidade:")
    colunas = ["comunidade", "canteiros", "dias", "alertas_enviados", "taxa_de_fiz_pct", "agua_economizada_pct",
               "horas_abaixo_do_minimo", "dias_risco_doenca_alto"]
    print(resumo[colunas].to_string(index=False))
    return contagem


if __name__ == "__main__":
    rodar()
