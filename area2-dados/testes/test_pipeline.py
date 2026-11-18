"""Testes do pipeline da Area 2 (unittest, da biblioteca padrao do Python).

Rodar, de dentro de area2-dados/:  python -m unittest discover -s testes -v
Cada caso tem o codigo do plano de testes (docs/plano-de-testes.md).
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gerador  # noqa: E402
import ouro  # noqa: E402
import prata  # noqa: E402
from comum import AMOSTRA, PERIODO_SIMULADO  # noqa: E402


def _leitura(i, quando, umidade=50.0):
    return {"id": i, "canteiroId": 1, "umidadeSolo": umidade, "temperaturaAr": 22.0,
            "luminosidade": 60.0, "registradaEm": quando, "origem": "simulado"}


class TestePrata(unittest.TestCase):

    def test_ct20_limpeza_faixa_repetida_e_horario(self):
        """CT20 - prata tira leitura fora da faixa, repetida e com horario ilegivel"""
        bruto = pd.DataFrame([
            _leitura(1, "2026-09-01T09:00:00Z"),
            _leitura(2, "2026-09-01T06:00:00-03:00"),        # o mesmo instante, em hora local: repetida
            _leitura(3, "2026-09-01T10:00:00Z", umidade=150.0),  # sensor com defeito
            _leitura(4, "ontem de manha"),                     # horario ilegivel
            _leitura(5, "2026-09-01T11:00:00Z"),
        ])
        limpo, qualidade = prata.limpar_leituras(bruto)
        self.assertEqual(list(limpo["leitura_id"]), [1, 5])
        removidas = {q["etapa"]: q["removidas"] for q in qualidade}
        self.assertEqual(removidas["horario ilegivel"], 1)
        self.assertEqual(removidas["fora da faixa (sensor com defeito)"], 1)
        self.assertEqual(removidas["repetida (reenvio)"], 1)

    def test_ct21_fuso_vira_hora_local(self):
        """CT21 - 09:00 em UTC vira 06:00 de Sao Paulo, sem fuso no texto (igual ao Open-Meteo)"""
        hora = prata.para_hora_local(pd.Series(["2026-09-01T09:00:00Z", "2026-09-01T06:00:00-03:00"]))
        self.assertEqual(list(hora), [pd.Timestamp("2026-09-01 06:00:00")] * 2)
        self.assertIsNone(hora.dt.tz)

    def test_ct22_resposta_fiz_e_nao_fiz(self):
        """CT22 - resposta do alerta: regou como pedido = fiz; regou sem precisar = nao fiz; janela aberta = aguardando"""
        t = pd.Timestamp
        alertas = pd.DataFrame({
            "alerta_id": [1, 2, 3, 4],
            "canteiro_chave": ["sim-1", "sim-2", "sim-3", "sim-4"],
            "momento_local": [t("2026-09-01 06:00")] * 3 + [t("2026-09-02 06:00")],
            "regar": [True, False, True, False],
        })
        regas = pd.DataFrame({
            "canteiro_chave": ["sim-1", "sim-2"],
            "momento_local": [t("2026-09-01 17:10"), t("2026-09-01 17:20")],
            "seguiu_recomendacao": [True, False],
        })
        fim = pd.Series({"sim-1": t("2026-09-03"), "sim-2": t("2026-09-03"), "sim-3": t("2026-09-03"),
                         "sim-4": t("2026-09-02 12:00")})
        resposta = prata.resposta_dos_alertas(alertas, regas, fim)
        self.assertEqual(list(resposta), ["fiz", "não fiz", "não fiz", "aguardando"])


class TesteOuro(unittest.TestCase):

    def test_ct23_horas_abaixo_do_minimo_e_agua(self):
        """CT23 - ouro conta as horas abaixo do minimo e a agua economizada contra 30 min por dia"""
        t = pd.Timestamp
        canteiros = pd.DataFrame({"canteiro_chave": ["sim-1"], "umidade_minima": [45], "vazao_l_min": [30.0]})
        hora = pd.DataFrame({
            "canteiro_chave": ["sim-1"] * 3,
            "hora_local": [t("2026-09-01 06:00"), t("2026-09-01 07:00"), t("2026-09-01 08:00")],
            "umidade_solo": [44.0, 46.0, 40.0], "temperatura_ar": [20.0, 21.0, 22.0],
            "abaixo_do_minimo": [True, False, True], "data": [t("2026-09-01")] * 3,
        })
        alertas = pd.DataFrame({"canteiro_chave": ["sim-1"], "momento_local": [t("2026-09-01 06:00")],
                                "alerta_id": [1], "regar": [True], "resposta": ["fiz"]})
        regas = pd.DataFrame({"canteiro_chave": ["sim-1"], "momento_local": [t("2026-09-01 17:00")],
                              "rega_id": [1], "minutos": [10], "litros": [300.0]})
        clima_dia = pd.DataFrame({"data": [t("2026-09-01")], "chuva_mm": [0.0]})
        fato = ouro.fato_diario(hora, clima_dia, alertas, regas, canteiros)
        linha = fato.iloc[0]
        self.assertEqual(linha["horas_abaixo_do_minimo"], 2)
        self.assertEqual(linha["umidade_minima_do_dia"], 40.0)
        self.assertEqual(linha["litros_calendario"], 900.0)     # 30 min x 30 L/min
        self.assertEqual(linha["litros_economizados"], 600.0)   # 900 - 300
        self.assertEqual(linha["respostas_fiz"], 1)


class TesteGerador(unittest.TestCase):

    def test_ct24_semente_fixa_gera_sempre_igual(self):
        """CT24 - o gerador com a semente fixa produz o mesmo historico de 60 dias duas vezes"""
        inicio, fim = PERIODO_SIMULADO
        clima = AMOSTRA / f"clima_ibiuna_{inicio}_{fim}.json"
        resultados = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as pasta, mock.patch.object(gerador, "BRONZE", Path(pasta)):
                gerador.gerar(clima)
                resultados.append((Path(pasta) / "simulado" / "leituras.json").read_text(encoding="utf-8"))
        self.assertEqual(resultados[0], resultados[1])
        dias = {r["registradaEm"][:10] for r in json.loads(resultados[0])}
        self.assertGreaterEqual(len(dias), 60)


if __name__ == "__main__":
    unittest.main()
