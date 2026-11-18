"""Antes e depois: quanto a IA economiza de agua e se o alerta acerta.

Cenario: os 7 canteiros do gerador da Area 2, por 60 dias com o clima REAL de Ibiuna de 01/09 a 30/10/2025
(o modelo foi treinado com 2026: este periodo ele nunca viu). O solo segue a mesma fisica do gerador.
Tres jeitos de regar, com o mesmo sensor e o mesmo clima:
- ANTES, calendario: 30 minutos todo dia, faca chuva ou sol (o costume do Seu Jorge);
- regra basica: o plano B da API, que olha so o sensor;
- DEPOIS, IA: o modelo + a previsao. Aqui a "previsao" e o clima que de fato aconteceu; previsao de verdade
  erra, entao o ganho real tende a ser um pouco menor.

O acerto do alerta: um alerta acertou se, na manha seguinte, o solo estava acima do minimo e a rega do dia
nao se perdeu (no maximo 10% escorrendo porque o solo ja estava cheio ou porque choveu logo depois).
Depois, o mesmo cenario com as respostas "1 fiz / 2 nao fiz": cada produtor segue o alerta com a chance que
tem no gerador da Area 2, e o acerto e medido separado para quem fez e quem nao fez.

Rodar: python avaliar.py   (nao usa internet: o clima de 2025 esta em amostra/)
"""
from __future__ import annotations

import random

import pandas as pd

import decisao
import previsao
import treinar
from base import AMOSTRA, RESULTADOS, gerador
from comum import MINUTOS_CALENDARIO

CLIMA_2025 = AMOSTRA / "clima_ibiuna_2025-09-01_2025-10-30.json"
SEMENTE = 2025
PERDA_TOLERADA = 0.10


def carregar_clima() -> pd.DataFrame:
    clima = gerador.carregar_clima(CLIMA_2025)
    return clima


def simular(clima: pd.DataFrame, canteiro: tuple, politica: str, modelo, previsoes: dict, seguir_sempre: bool) -> dict:
    cid, nome, cultura, area, vazao, produtor, adesao = canteiro
    minimo = gerador.UMIDADE_MINIMA[cultura]
    sensor = random.Random(SEMENTE * 1000 + cid)        # o mesmo ruido do sensor nas tres politicas
    respostas = random.Random(SEMENTE * 7 + cid)        # a mesma sequencia de "fiz / nao fiz"
    umidade = random.Random(cid).uniform(48, 60)
    agua = perdida = 0.0
    horas_abaixo = 0
    rega_de_hoje, alertas, aberto = 0, [], None
    drenagem_apos_rega, rega_litros, rega_hora = 0.0, 0.0, None

    for hora_local, linha in clima.iterrows():
        hora = hora_local.hour
        # fecha o alerta de ontem as 6 h: o solo amanheceu no ponto?
        if hora == gerador.HORA_DO_ALERTA and aberto is not None:
            aberto["solo_amanheceu_ok"] = umidade >= minimo
            alertas.append(aberto)
            aberto = None

        umidade -= linha["et0_fao_evapotranspiration"] * gerador.COEF_CULTURA[cultura] * gerador.PONTOS_POR_MM
        umidade += linha["precipitation"] * gerador.EFICIENCIA_CHUVA * gerador.PONTOS_POR_MM
        if hora == gerador.HORA_DA_REGA and rega_de_hoje > 0:
            litros = rega_de_hoje * vazao
            agua += litros
            umidade += (litros / area) * gerador.EFICIENCIA_REGA * gerador.PONTOS_POR_MM
            drenagem_apos_rega, rega_litros, rega_hora = 0.0, litros, hora_local
        sobra = max(0.0, umidade - gerador.CAPACIDADE_DE_CAMPO)
        umidade = max(5.0, min(gerador.CAPACIDADE_DE_CAMPO, umidade))
        if rega_hora is not None:
            drenagem_apos_rega += sobra
            if hora_local - rega_hora >= pd.to_timedelta(23, unit="h"):   # 24 h depois da rega: fecha a conta
                litros_escorridos = drenagem_apos_rega / gerador.PONTOS_POR_MM / gerador.EFICIENCIA_REGA * area
                perda = min(rega_litros, litros_escorridos)
                perdida += perda
                if alertas and alertas[-1]["dia"] == rega_hora.normalize():
                    alertas[-1]["rega_perdida"] = perda > PERDA_TOLERADA * rega_litros
                rega_hora = None
        if umidade < minimo:
            horas_abaixo += 1

        leitura = umidade + sensor.gauss(0, 0.8)
        if hora == gerador.HORA_DO_ALERTA:
            fez = seguir_sempre or respostas.random() < adesao
            if politica == "calendario":
                rega_de_hoje = MINUTOS_CALENDARIO
                continue
            if politica == "regra_basica":
                regar, minutos, _, _ = gerador.regra_basica(cultura, area, vazao, leitura, linha["temperature_2m"], 0)
            else:
                pedido = {"cultura": cultura, "areaM2": area, "vazaoLitrosMin": vazao, "umidadeSolo": leitura,
                          "temperaturaAr": linha["temperature_2m"], "luminosidade": 0, "umidadeMinima": minimo}
                d = decisao.decidir(pedido, previsoes.get(hora_local), modelo)
                regar, minutos = d["regar"], d["minutos"]
            if regar:
                rega_de_hoje = minutos if fez else 0
            else:
                rega_de_hoje = 0 if fez else MINUTOS_CALENDARIO     # nao fez: regou no costume
            aberto = {"dia": hora_local.normalize(), "regar": regar, "fez": fez, "rega_perdida": False}

    for a in alertas:
        a["acertou"] = a["solo_amanheceu_ok"] and not a["rega_perdida"]
    return {"canteiro": nome, "politica": politica, "agua_l": agua, "agua_perdida_l": perdida,
            "horas_abaixo_do_minimo": horas_abaixo, "alertas": alertas}


def tabela(resultados: list[dict]) -> pd.DataFrame:
    linhas = []
    for politica in ("calendario", "regra_basica", "ia"):
        rs = [r for r in resultados if r["politica"] == politica]
        alertas = [a for r in rs for a in r["alertas"]]
        linhas.append({
            "politica": {"calendario": "Antes: calendário (30 min/dia)", "regra_basica": "Regra básica (só sensor)",
                         "ia": "Depois: IA (sensor + previsão)"}[politica],
            "agua_l": round(sum(r["agua_l"] for r in rs)),
            "agua_perdida_l": round(sum(r["agua_perdida_l"] for r in rs)),
            "horas_abaixo_do_minimo": sum(r["horas_abaixo_do_minimo"] for r in rs),
            "alertas": len(alertas),
            "acerto_pct": round(100 * sum(a["acertou"] for a in alertas) / len(alertas), 1) if alertas else None,
        })
    df = pd.DataFrame(linhas)
    base_agua = df.loc[0, "agua_l"]
    df["economia_vs_calendario_pct"] = (100 * (1 - df["agua_l"] / base_agua)).round(1)
    return df


def br(numero: float, casas: int = 0) -> str:
    """279000 -> 279.000; 61.4 -> 61,4 (como se escreve no Brasil)."""
    texto = f"{numero:,.{casas}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def rodar() -> dict:
    clima = carregar_clima()
    modelo = treinar.carregar()
    # a previsao de cada manha (6 h): o clima das 24 h e dos 3 dias seguintes
    previsoes = {h: previsao.de_clima_guardado(CLIMA_2025, h) for h in clima.index if h.hour == gerador.HORA_DO_ALERTA}

    sempre = [simular(clima, c, p, modelo, previsoes, seguir_sempre=True)
              for c in gerador.CANTEIROS for p in ("calendario", "regra_basica", "ia")]
    comparacao = tabela(sempre)

    com_respostas = [simular(clima, c, "ia", modelo, previsoes, seguir_sempre=False) for c in gerador.CANTEIROS]
    alertas = [a for r in com_respostas for a in r["alertas"]]
    fez = [a for a in alertas if a["fez"]]
    nao_fez = [a for a in alertas if not a["fez"]]
    respostas = {
        "alertas": len(alertas),
        "taxa_de_fiz_pct": round(100 * len(fez) / len(alertas), 1),
        "acerto_quando_fez_pct": round(100 * sum(a["acertou"] for a in fez) / len(fez), 1),
        "acerto_quando_nao_fez_pct": round(100 * sum(a["acertou"] for a in nao_fez) / len(nao_fez), 1),
        "agua_l": round(sum(r["agua_l"] for r in com_respostas)),
        "horas_abaixo_do_minimo": sum(r["horas_abaixo_do_minimo"] for r in com_respostas),
    }

    RESULTADOS.mkdir(exist_ok=True)
    comparacao.to_csv(RESULTADOS / "antes_depois.csv", index=False, encoding="utf-8-sig")
    chuva = clima["precipitation"].sum()
    md = ["# Antes e depois da IA do Sereno", "",
          f"7 canteiros, 60 dias com o clima real de Ibiúna de 01/09 a 30/10/2025 ({chuva:.0f} mm de chuva), "
          "período que o modelo nunca viu. Gerado por `python avaliar.py`.", "",
          "## Seguindo sempre o alerta", "",
          "| Jeito de regar | Água (L) | Economia contra o calendário | Água perdida (L) | Horas com o solo abaixo do mínimo | Alertas | Acerto do alerta |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    for _, r in comparacao.iterrows():
        acerto = "" if pd.isna(r["acerto_pct"]) else f"{br(r['acerto_pct'], 1)}%"
        md.append(f"| {r['politica']} | {br(r['agua_l'])} | {br(r['economia_vs_calendario_pct'], 1)}% | "
                  f"{br(r['agua_perdida_l'])} | {br(r['horas_abaixo_do_minimo'])} | {r['alertas'] or ''} | {acerto} |")
    md += ["", "## Com as respostas \"1 fiz / 2 não fiz\"", "",
           "Cada produtor segue o alerta da IA com a chance que tem no gerador da Área 2 (de 50% a 90%).", "",
           "| Medida | Valor |", "|---|---:|",
           f"| Alertas enviados | {respostas['alertas']} |",
           f"| Taxa de \"fiz\" | {br(respostas['taxa_de_fiz_pct'], 1)}% |",
           f"| Acerto quando o produtor respondeu \"fiz\" | {br(respostas['acerto_quando_fez_pct'], 1)}% |",
           f"| Acerto quando respondeu \"não fiz\" | {br(respostas['acerto_quando_nao_fez_pct'], 1)}% |",
           f"| Água usada (L) | {br(respostas['agua_l'])} |",
           f"| Horas com o solo abaixo do mínimo | {br(respostas['horas_abaixo_do_minimo'])} |", "",
           "Acerto: na manhã seguinte o solo estava acima do mínimo e a rega do dia não se perdeu "
           "(no máximo 10% escorrendo). A \"previsão\" usada é o clima que de fato aconteceu: previsão de verdade erra, "
           "então o ganho real tende a ser um pouco menor."]
    texto = "\n".join(md)
    (RESULTADOS / "antes_depois.md").write_text(texto + "\n", encoding="utf-8")
    print(texto)
    return {"comparacao": comparacao, "respostas": respostas}


if __name__ == "__main__":
    rodar()
