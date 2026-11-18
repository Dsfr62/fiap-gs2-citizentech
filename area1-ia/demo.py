"""Exemplos de entrada e saida da IA, em dias reais de 2025 (sem internet).

Escolhe tres manhas do clima guardado de Ibiuna (01/09 a 30/10/2025):
1. o dia mais seco e de mais sol, com o solo perto do minimo: a IA manda regar;
2. o dia de mais chuva prevista, com o solo abaixo do minimo: a IA segura a rega, porque a chuva da conta;
3. o dia mais abafado sem chuva forte: alem da rega, vem o aviso de doenca nas folhas.
Cada exemplo vai para exemplos/ (entrada, previsao e saida em JSON) e aparece na tela.

Rodar: python demo.py
"""
from __future__ import annotations

import json

import previsao
import servico
import treinar
from avaliar import CLIMA_2025
from base import EXEMPLOS, gerador

CANTEIRO = {"canteiroId": 1, "cultura": "FOLHOSA", "areaM2": 120, "vazaoLitrosMin": 30,
            "latitude": -23.6566, "longitude": -47.2229, "luminosidade": 0, "umidadeMinima": 45}


def escolher_manhas():
    clima = gerador.carregar_clima(CLIMA_2025)
    manhas = [h for h in clima.index if h.hour == 6][:-1]
    resumos = {h: previsao.de_clima_guardado(CLIMA_2025, h) for h in manhas}
    resumos = {h: r for h, r in resumos.items() if r}
    seco = max((h for h, r in resumos.items() if r["proximas_24h"]["chuva_24h"] == 0),
               key=lambda h: resumos[h]["proximas_24h"]["et0_24h"])
    chuvoso = max(resumos, key=lambda h: resumos[h]["proximas_24h"]["chuva_24h"])
    umido = max((h for h, r in resumos.items() if r["proximas_24h"]["chuva_24h"] < 1),
                key=lambda h: max(d["horas_folha_molhada"] for d in resumos[h]["dias"]))
    return clima, resumos, [
        ("Dia seco e de sol, solo perto do mínimo", seco, 46.0),
        ("Solo abaixo do mínimo, mas com chuva forte prevista", chuvoso, 42.0),
        ("Tempo abafado, com risco de doença nas folhas", umido, 58.0),
    ]


def rodar() -> list[dict]:
    servico.MODELO = treinar.carregar()
    clima, resumos, casos = escolher_manhas()
    EXEMPLOS.mkdir(exist_ok=True)
    exemplos = []
    for numero, (situacao, manha, umidade) in enumerate(casos, start=1):
        entrada = {**CANTEIRO, "umidadeSolo": umidade, "temperaturaAr": float(clima.loc[manha, "temperature_2m"])}
        prev = resumos[manha]
        saida = servico.recomendar(entrada, prev=prev, hoje=manha.date())
        exemplo = {"situacao": situacao, "manha": manha.isoformat(), "entrada": entrada,
                   "previsao_24h": prev["proximas_24h"], "saida": saida}
        (EXEMPLOS / f"exemplo-{numero}.json").write_text(json.dumps(exemplo, ensure_ascii=False, indent=2),
                                                          encoding="utf-8")
        exemplos.append(exemplo)
        p = prev["proximas_24h"]
        print(f"\n{numero}. {situacao} ({manha:%d/%m/%Y}, 6 h)")
        print(f"   entrada: solo {umidade:.0f}%, {entrada['temperaturaAr']:.0f} °C; previsão 24 h: chuva {p['chuva_24h']} mm, "
              f"evapotranspiração {p['et0_24h']} mm, máxima {p['temp_max_24h']} °C")
        print(f"   saída: regar={saida['regar']}, {saida['minutos']} min, solo previsto {saida['umidadePrevista24h']}%")
        print(f"   WhatsApp: {saida['mensagemWhatsapp']}")
    return exemplos


if __name__ == "__main__":
    rodar()
