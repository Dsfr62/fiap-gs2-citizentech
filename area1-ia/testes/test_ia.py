"""Testes da IA do Sereno (unittest, biblioteca padrao). Rodar de dentro de area1-ia/:

    python -m unittest discover -s testes -v

Cada caso tem o codigo do plano de testes (docs/plano-de-testes.md).
"""
import http.client
import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["SERENO_SEM_PREVISAO"] = "1"   # os testes nao dependem da internet

import decisao  # noqa: E402
import mensagem  # noqa: E402
import risco  # noqa: E402
import servico  # noqa: E402
import treinar  # noqa: E402
from base import METRICAS  # noqa: E402

PEDIDO = {"canteiroId": 1, "cultura": "FOLHOSA", "areaM2": 120, "vazaoLitrosMin": 30, "latitude": -23.6566,
          "longitude": -47.2229, "umidadeSolo": 44.0, "temperaturaAr": 26.0, "luminosidade": 80.0, "umidadeMinima": 45}


def previsao(chuva, et0=4.0, dias=None):
    return {"proximas_24h": {"chuva_24h": chuva, "et0_24h": et0, "temp_max_24h": 28.0, "umidade_ar_24h": 70.0},
            "dias": dias or [], "fonte": "teste"}


class TesteIa(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.modelo = treinar.carregar()

    def test_ct28_seco_sem_chuva_rega(self):
        """CT28 - solo perto do minimo, dia de sol e sem chuva: a IA manda regar"""
        d = decisao.decidir(PEDIDO, previsao(chuva=0.0, et0=5.0), self.modelo)
        self.assertTrue(d["regar"])
        self.assertGreater(d["minutos"], 0)
        self.assertLess(d["umidade_prevista_24h"], PEDIDO["umidadeSolo"])

    def test_ct29_chuva_forte_segura_a_rega(self):
        """CT29 - solo abaixo do minimo, mas 30 mm de chuva prevista: a IA nao manda regar"""
        d = decisao.decidir({**PEDIDO, "umidadeSolo": 42.0}, previsao(chuva=30.0, et0=1.0), self.modelo)
        self.assertFalse(d["regar"])
        self.assertEqual(d["minutos"], 0)
        texto = mensagem.montar(d, [], date(2025, 9, 22))["explicacao"]
        self.assertIn("chuva prevista", texto)

    def test_ct30_sem_previsao_decide_pelo_sensor_e_avisa(self):
        """CT30 - sem previsao do tempo, a IA decide so pelo sensor (regra basica) e diz isso"""
        d = decisao.decidir({**PEDIDO, "umidadeSolo": 38.0}, None, self.modelo)
        self.assertTrue(d["regar"])
        self.assertFalse(d["com_previsao"])
        self.assertIn("sem a previsão", mensagem.montar(d, [], date(2025, 9, 1))["explicacao"])

    def test_ct31_riscos_de_doenca_geada_e_calor(self):
        """CT31 - riscos: 12 h de folha molhada = doenca alta; minima de 2 graus = geada alta; maxima de 33 = calor alto"""
        dias = [{"data": "2025-09-01", "horas_folha_molhada": 12, "temp_min": 14.0, "temp_max": 24.0, "chuva": 0},
                {"data": "2025-09-02", "horas_folha_molhada": 0, "temp_min": 2.0, "temp_max": 20.0, "chuva": 0},
                {"data": "2025-09-03", "horas_folha_molhada": 0, "temp_min": 18.0, "temp_max": 33.0, "chuva": 0}]
        niveis = {r["tipo"]: r["nivel"] for r in risco.avaliar(dias)}
        self.assertEqual(niveis, {"doenca": "alto", "geada": "alto", "calor": "alto"})
        self.assertEqual(risco.avaliar([{**dias[0], "horas_folha_molhada": 2}]), [])

    def test_ct32_mensagem_simples(self):
        """CT32 - mensagem: acao primeiro, sem palavra tecnica, curta e com o pedido "1 fiz / 2 nao fiz" """
        d = decisao.decidir(PEDIDO, previsao(chuva=0.0, et0=5.0), self.modelo)
        riscos = risco.avaliar([{"data": "2025-09-03", "horas_folha_molhada": 0, "temp_min": 2.0, "temp_max": 20.0, "chuva": 0}])
        textos = mensagem.montar(d, riscos, date(2025, 9, 1))
        self.assertTrue(textos["explicacao"].startswith("Regue"))
        self.assertIn("Geada prevista na quarta", textos["explicacao"])
        self.assertTrue(textos["whatsapp"].endswith("Responda 1 se fez ou 2 se não fez."))
        self.assertLessEqual(len(textos["whatsapp"]), 400)
        for palavra in ("evapotranspira", "modelo", "IA", "umidade relativa", "—", "·"):
            self.assertNotIn(palavra, textos["whatsapp"])

    def test_ct33_modelo_melhor_que_nada_mudar(self):
        """CT33 - no teste, o modelo erra menos da metade de "supor que nada muda" """
        metricas = json.loads(METRICAS.read_text(encoding="utf-8"))
        self.assertLess(metricas["erro_medio_modelo_pontos"], metricas["erro_medio_se_nada_mudasse_pontos"] / 2)


class TesteServico(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.servidor = servico.iniciar(0)          # porta livre qualquer
        cls.url = f"http://127.0.0.1:{cls.servidor.server_address[1]}"
        threading.Thread(target=cls.servidor.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.servidor.shutdown()

    def _post(self, corpo):
        pedido = urllib.request.Request(f"{self.url}/recomendar", data=json.dumps(corpo).encode(),
                                        headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(pedido, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as erro:
            return erro.code, json.loads(erro.read())

    def test_ct34_servico_responde_no_contrato_da_api(self):
        """CT34 - POST /recomendar devolve regar, minutos, explicacao e chuvaPrevistaMm (o contrato da API), tambem com o corpo em pedacos, como a API manda"""
        status, corpo = self._post(PEDIDO)
        self.assertEqual(status, 200)
        for campo in ("regar", "minutos", "explicacao", "chuvaPrevistaMm", "mensagemWhatsapp"):
            self.assertIn(campo, corpo)
        with urllib.request.urlopen(f"{self.url}/saude", timeout=5) as r:
            self.assertEqual(json.loads(r.read())["status"], "UP")
        # a API em Java (Spring 6) manda o corpo em pedacos, sem Content-Length: tem de funcionar igual
        conexao = http.client.HTTPConnection("127.0.0.1", self.servidor.server_address[1], timeout=10)
        pedacos = [json.dumps(PEDIDO).encode()[i:i + 50] for i in range(0, len(json.dumps(PEDIDO)), 50)]
        conexao.request("POST", "/recomendar", body=iter(pedacos), encode_chunked=True,
                        headers={"Content-Type": "application/json", "Transfer-Encoding": "chunked"})
        resposta = conexao.getresponse()
        self.assertEqual(resposta.status, 200)
        self.assertIn("explicacao", json.loads(resposta.read()))
        conexao.close()

    def test_ct35_servico_recusa_pedido_invalido(self):
        """CT35 - pedido com umidade 150% e cultura desconhecida volta 400, com os campos"""
        status, corpo = self._post({**PEDIDO, "umidadeSolo": 150, "cultura": "BANANA"})
        self.assertEqual(status, 400)
        self.assertIn("umidadeSolo", corpo["campos"])
        self.assertIn("cultura", corpo["campos"])


if __name__ == "__main__":
    unittest.main()
