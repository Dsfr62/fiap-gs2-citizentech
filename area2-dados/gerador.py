"""Gerador do historico SIMULADO de 60 dias (camada bronze, fonte "simulado").

Por que simular: o Sereno ainda nao tem estacao no campo. Para o painel ter 60 dias de historia,
este script imita 7 canteiros em 3 comunidades de Ibiuna, usando o CLIMA REAL do Open-Meteo
(chuva, temperatura, umidade do ar e evapotranspiracao hora a hora). Tudo o que e da planta,
do sensor e do produtor e simulado, e o arquivo _LEIA.txt da pasta diz isso.

Semente fixa (SEMENTE em comum.py): rodar duas vezes da exatamente o mesmo resultado.

O que sai e no MESMO formato JSON que a API exporta (/api/dados/...), para o resto do pipeline
tratar as duas fontes do mesmo jeito. O sensor simulado tambem erra como um sensor de verdade:
leitura fora da faixa, leitura repetida (reenvio quando o sinal volta), hora faltando e
horario em dois formatos (UTC e hora local com -03:00). A camada prata limpa isso.
"""
import math
import random
from datetime import timedelta

import pandas as pd

from comum import BRONZE, FUSO, MINUTOS_CALENDARIO, SEMENTE, UMIDADE_MINIMA, ler_json, salvar_json, salvar_texto

# ---- os canteiros simulados (ids a partir de 101 para nao confundir com os da API) ----
CANTEIROS = [
    # id, nome, cultura, area m2, vazao L/min, produtor, chance de seguir o alerta
    (101, "Canteiro 1 - Alface", "FOLHOSA", 120, 30, "Jorge Almeida", 0.85),
    (102, "Canteiro 2 - Tomate", "FRUTO", 80, 20, "Jorge Almeida", 0.85),
    (103, "Horta do Antônio - Alface", "FOLHOSA", 100, 25, "Antônio Ribeiro", 0.60),
    (104, "Horta da Maria - Couve", "FOLHOSA", 60, 15, "Maria Lima", 0.90),
    (105, "Sítio da Cida - Couve", "FOLHOSA", 90, 20, "Cida Moraes", 0.75),
    (106, "Sítio do Tadeu - Tomate", "FRUTO", 150, 30, "Tadeu Campos", 0.50),
    (107, "Horta da Rosa - Cenoura", "RAIZ", 70, 15, "Rosa Nunes", 0.80),
]

# ---- o solo, em pontos de umidade do sensor (0 a 100) ----
PONTOS_POR_MM = 2.5          # 1 mm de agua = 2,5 pontos (o inverso dos 0,4 mm por ponto da RegraBasica)
CAPACIDADE_DE_CAMPO = 70.0   # acima disso a agua escorre ou infiltra fundo
COEF_CULTURA = {"FOLHOSA": 1.0, "FRUTO": 1.1, "RAIZ": 0.9}   # Kc simplificado (FAO-56)
EFICIENCIA_CHUVA = 0.8
EFICIENCIA_REGA = 0.9

# ---- os defeitos do sensor (para a camada prata ter o que limpar) ----
CHANCE_FORA_DA_FAIXA = 0.004
CHANCE_REPETIDA = 0.02
CHANCE_FALTANDO = 0.015
CHANCE_HORA_LOCAL = 0.2

HORA_DO_ALERTA = 6       # o alerta sai as 6h
HORA_DA_REGA = 17        # a RegraBasica sugere regar no fim da tarde


def regra_basica(cultura: str, area: float, vazao: float, umidade: float, temperatura: float, luz: float):
    """Copia, em Python, da RegraBasica da API (area3-mvp/api/.../service/RegraBasica.java)."""
    minimo = UMIDADE_MINIMA[cultura]
    if umidade >= minimo:
        return False, 0, 0.0, f"Solo com {umidade:.0f}% de umidade, acima do mínimo de {minimo}%. Hoje não precisa regar."
    lamina = (minimo + 10 - umidade) * 0.4
    if temperatura >= 30 and luz >= 70:
        lamina += 1.0
    lamina = min(lamina, 8.0)
    litros = float(round(lamina * area))
    minutos = math.ceil(litros / vazao)
    return True, minutos, litros, (f"Solo com {umidade:.0f}% de umidade, abaixo do mínimo de {minimo}%. "
                                   f"Regue {minutos} minutos (cerca de {litros:.0f} litros), de preferência no fim da tarde.")


def carregar_clima(caminho) -> pd.DataFrame:
    bruto = ler_json(caminho)["hourly"]
    clima = pd.DataFrame(bruto)
    clima["hora_local"] = pd.to_datetime(clima["time"])
    return clima.set_index("hora_local")


def _instante(hora_local: pd.Timestamp, sorte: random.Random) -> str:
    """Hora local -> texto ISO, como o sensor manda: quase sempre em UTC, as vezes em hora local."""
    local = hora_local.tz_localize(FUSO) + timedelta(seconds=sorte.randint(0, 50))
    if sorte.random() < CHANCE_HORA_LOCAL:
        return local.isoformat()                                   # 2026-09-01T06:00:12-03:00
    return local.tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")  # 2026-09-01T09:00:12Z


def gerar(caminho_clima) -> dict:
    sorte = random.Random(SEMENTE)
    clima = carregar_clima(caminho_clima)
    canteiros, leituras, alertas, regas = [], [], [], []

    for cid, nome, cultura, area, vazao, produtor, adesao in CANTEIROS:
        canteiros.append({"id": cid, "nome": nome, "cultura": cultura, "areaM2": area, "vazaoLitrosMin": vazao,
                          "latitude": -23.6566, "longitude": -47.2229, "umidadeMinima": UMIDADE_MINIMA[cultura],
                          "produtor": produtor, "ultimaLeitura": None})
        umidade = sorte.uniform(48, 60)
        desvio_temp = sorte.uniform(-0.8, 0.8)    # cada canteiro tem o seu microclima
        rega_de_hoje = 0                          # minutos que o produtor vai regar as 17h

        for hora_local, linha in clima.iterrows():
            hora = hora_local.hour
            # 1. o solo: perde agua para o ar e ganha com chuva e rega
            umidade -= linha["et0_fao_evapotranspiration"] * COEF_CULTURA[cultura] * PONTOS_POR_MM
            umidade += linha["precipitation"] * EFICIENCIA_CHUVA * PONTOS_POR_MM
            if hora == HORA_DA_REGA and rega_de_hoje > 0:
                umidade += (rega_de_hoje * vazao / area) * EFICIENCIA_REGA * PONTOS_POR_MM
            umidade = max(5.0, min(CAPACIDADE_DE_CAMPO, umidade))

            # 2. o sensor mede (com ruido)
            sol = max(0.0, math.sin(math.pi * (hora - 6) / 12))
            nublado = 0.4 if linha["precipitation"] > 0 else 1.0
            leitura = {
                "umidadeSolo": round(umidade + sorte.gauss(0, 0.8), 1),
                "temperaturaAr": round(linha["temperature_2m"] + desvio_temp + sorte.gauss(0, 0.3), 1),
                "luminosidade": round(min(100, max(0, 95 * sol * nublado + sorte.gauss(0, 3))), 1),
            }
            if sorte.random() >= CHANCE_FALTANDO:                    # sinal fraco: as vezes a hora se perde
                if sorte.random() < CHANCE_FORA_DA_FAIXA:            # defeito do sensor
                    leitura["umidadeSolo"] = sorte.choice([150.0, -1.0])
                registro = {"id": len(leituras) + 1, "canteiroId": cid, **leitura,
                            "registradaEm": _instante(hora_local, sorte)}
                leituras.append(registro)
                if sorte.random() < CHANCE_REPETIDA:                 # reenvio quando o sinal volta
                    leituras.append({**registro, "id": len(leituras) + 1})

            # 3. as 6h sai o alerta do dia; o produtor responde regando (ou nao) as 17h
            if hora == HORA_DO_ALERTA:
                regar, minutos, litros, texto = regra_basica(cultura, area, vazao, leitura["umidadeSolo"],
                                                             leitura["temperaturaAr"], leitura["luminosidade"])
                alertas.append({"id": len(alertas) + 1, "canteiroId": cid, "criadaEm": _instante(hora_local, sorte),
                                "regar": regar, "minutos": minutos, "litros": litros, "explicacao": texto,
                                "origem": "REGRA_BASICA", "umidadeSoloUsada": leitura["umidadeSolo"],
                                "chuvaPrevistaMm": None})
                seguiu = sorte.random() < adesao
                if regar:
                    rega_de_hoje = minutos if seguiu else 0
                else:
                    rega_de_hoje = 0 if seguiu else MINUTOS_CALENDARIO   # nao seguiu: regou no costume
                if rega_de_hoje > 0:
                    quando = hora_local.replace(hour=HORA_DA_REGA) + timedelta(minutes=sorte.randint(0, 50))
                    regas.append({"id": len(regas) + 1, "canteiroId": cid,
                                  "feitaEm": quando.tz_localize(FUSO).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
                                  "minutos": rega_de_hoje, "litros": float(rega_de_hoje * vazao),
                                  "seguiuRecomendacao": regar and seguiu})

    pasta = BRONZE / "simulado"
    salvar_json(pasta / "canteiros.json", canteiros)
    salvar_json(pasta / "leituras.json", leituras)
    salvar_json(pasta / "recomendacoes.json", alertas)
    salvar_json(pasta / "regas.json", regas)
    salvar_texto(pasta / "_LEIA.txt",
                 "DADOS SIMULADOS. Clima real de Ibiúna (Open-Meteo); canteiros, sensores, alertas e regas\n"
                 f"gerados por gerador.py com a semente {SEMENTE}. Mesmo formato da API do Sereno.\n")
    contagem = {"canteiros": len(canteiros), "leituras": len(leituras), "recomendacoes": len(alertas), "regas": len(regas)}
    print(f"  simulado: {contagem} -> {pasta.relative_to(BRONZE.parent)}")
    return contagem


if __name__ == "__main__":
    from ingestao import ingerir_clima_historico
    gerar(ingerir_clima_historico())
