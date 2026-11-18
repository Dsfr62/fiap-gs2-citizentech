"""Servico da IA do Sereno: POST /recomendar e GET /saude, com http.server da biblioteca padrao.

A API (Area 3) chama POST {IA_URL}/recomendar com o PedidoIa (area3-mvp/api/.../dto/Dtos.java) e le
{regar, minutos, explicacao, chuvaPrevistaMm}. Os campos a mais (mensagemWhatsapp, riscos, umidadePrevista24h...)
a API ignora; servem para a demonstracao e para o aviso por WhatsApp.

Rodar: python servico.py   (porta 8001; outra com PORTA=8002)
"""
from __future__ import annotations

import json
import os
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import decisao
import mensagem
import previsao
import risco
import treinar
from base import METRICAS

CULTURAS = {"FOLHOSA", "FRUTO", "RAIZ"}
TAMANHO_MAXIMO = 10_000   # bytes: pedido maior que isso nao e um pedido de canteiro
FAIXAS = {   # as mesmas da API: dado fora da faixa volta 400
    "umidadeSolo": (0, 100), "temperaturaAr": (-10, 60), "luminosidade": (0, 100), "umidadeMinima": (0, 100),
    "areaM2": (0.01, 100000), "vazaoLitrosMin": (0.01, 1000),
}

MODELO = None


def validar(pedido) -> dict:
    """Devolve os campos com problema (vazio = pedido valido)."""
    if not isinstance(pedido, dict):
        return {"corpo": "precisa ser um objeto JSON"}
    erros = {}
    for campo, (minimo, maximo) in FAIXAS.items():
        valor = pedido.get(campo)
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            erros[campo] = "obrigatório e numérico"
        elif not minimo <= valor <= maximo:
            erros[campo] = f"precisa estar entre {minimo} e {maximo}"
    if pedido.get("cultura") not in CULTURAS:
        erros["cultura"] = f"precisa ser uma de {sorted(CULTURAS)}"
    for campo, (minimo, maximo) in {"latitude": (-90, 90), "longitude": (-180, 180)}.items():
        valor = pedido.get(campo)
        if valor is not None and (isinstance(valor, bool) or not isinstance(valor, (int, float)) or not minimo <= valor <= maximo):
            erros[campo] = f"precisa estar entre {minimo} e {maximo}"
    return erros


def recomendar(pedido: dict, prev: dict | None = None, hoje: date | None = None) -> dict:
    """O caminho inteiro: previsao, decisao, riscos e mensagem."""
    if prev is None and pedido.get("latitude") is not None and pedido.get("longitude") is not None:
        prev = previsao.do_open_meteo(pedido["latitude"], pedido["longitude"])
    d = decisao.decidir(pedido, prev, MODELO)
    riscos = risco.avaliar(prev["dias"]) if prev else []
    textos = mensagem.montar(d, riscos, hoje or date.today())
    return {
        "regar": d["regar"],
        "minutos": d["minutos"],
        "explicacao": textos["explicacao"],
        "chuvaPrevistaMm": d["chuva_prevista_mm"],
        # a partir daqui, a API ignora:
        "litros": d["litros"],
        "umidadePrevista24h": d["umidade_prevista_24h"],
        "riscos": riscos,
        "mensagemWhatsapp": textos["whatsapp"],
        "previsao": prev["fonte"] if prev else "sem previsão (decidi só pelo sensor)",
    }


class Tratador(BaseHTTPRequestHandler):
    server_version = "SerenoIA/1.0"

    def _responder(self, status: int, corpo: dict) -> None:
        dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):  # noqa: N802 (nome exigido pelo http.server)
        if self.path == "/saude":
            metricas = json.loads(METRICAS.read_text(encoding="utf-8")) if METRICAS.exists() else {}
            self._responder(200, {"status": "UP", "modelo": "floresta aleatória (scikit-learn)",
                                  "erroMedioNoTestePontos": metricas.get("erro_medio_modelo_pontos")})
        else:
            self._responder(404, {"erro": "rota não encontrada"})

    def do_POST(self):  # noqa: N802
        if self.path != "/recomendar":
            self._responder(404, {"erro": "rota não encontrada"})
            return
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho <= 0 or tamanho > TAMANHO_MAXIMO:
            self._responder(413 if tamanho > TAMANHO_MAXIMO else 400, {"erro": "corpo vazio ou grande demais"})
            return
        try:
            pedido = json.loads(self.rfile.read(tamanho).decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            self._responder(400, {"erro": "JSON inválido"})
            return
        erros = validar(pedido)
        if erros:
            self._responder(400, {"erro": "pedido inválido", "campos": erros})
            return
        self._responder(200, recomendar(pedido))

    def log_message(self, formato, *args):  # um log curto por pedido, sem o corpo (dado do produtor)
        print(f"{self.address_string()} {self.command} {self.path} -> {args[1] if len(args) > 1 else ''}", flush=True)


def iniciar(porta: int) -> ThreadingHTTPServer:
    global MODELO
    MODELO = treinar.carregar()
    return ThreadingHTTPServer(("0.0.0.0", porta), Tratador)


if __name__ == "__main__":
    porta = int(os.environ.get("PORTA", "8001"))
    servidor = iniciar(porta)
    print(f"IA do Sereno no ar em http://localhost:{porta} (POST /recomendar, GET /saude)", flush=True)
    servidor.serve_forever()
