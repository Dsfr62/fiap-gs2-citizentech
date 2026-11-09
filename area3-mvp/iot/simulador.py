"""
Simulador dos sensores do canteiro (mock da Area 3).

Faz o papel do Arduino: gera leituras de umidade do solo, temperatura do ar e luz no mesmo
formato JSON que o sketch sensor_canteiro.ino imprime, e envia cada uma para a API
(POST /api/leituras, com a chave do canteiro no cabecalho X-Chave-Dispositivo).

So usa a biblioteca padrao do Python (nada para instalar).

Exemplos:
    python3 simulador.py                       # canteiro de alface, 1 leitura a cada 5 s, sem parar
    python3 simulador.py --vezes 10            # manda 10 leituras e para
    python3 simulador.py --cenario seco        # solo secando rapido (para ver a recomendacao de regar)
    python3 simulador.py --cenario chuva       # solo encharcado (recomendacao: nao regar)
    python3 simulador.py --chave demo-sensor-tomate-0002
"""

import argparse
import json
import math
import random
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

CENARIOS = {
    # umidade inicial do solo (%) e quanto ela cai a cada leitura
    "normal": (52.0, 0.4),
    "seco": (44.0, 1.2),
    "chuva": (78.0, 0.1),
}


def gerar_leitura(umidade: float, agora: datetime, sorte: random.Random) -> dict:
    """Temperatura e luz seguem a hora do dia; a umidade vem do estado do canteiro."""
    sol = max(0.0, math.sin(math.pi * (agora.hour + agora.minute / 60 - 6) / 12))
    temperatura = 16 + 13 * sol + sorte.gauss(0, 0.5)
    luz = min(100.0, max(0.0, 95 * sol + sorte.gauss(0, 3)))
    return {
        "umidadeSolo": round(max(0.0, min(100.0, umidade + sorte.gauss(0, 0.3))), 1),
        "temperaturaAr": round(temperatura, 1),
        "luminosidade": round(luz, 1),
    }


def enviar(api: str, chave: str, leitura: dict) -> int:
    pedido = urllib.request.Request(
        f"{api}/api/leituras",
        data=json.dumps(leitura).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-Chave-Dispositivo": chave},
        method="POST",
    )
    with urllib.request.urlopen(pedido, timeout=5) as resposta:
        return resposta.status


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulador dos sensores do canteiro")
    parser.add_argument("--api", default="http://localhost:8080", help="endereco da API")
    parser.add_argument("--chave", default="demo-sensor-alface-0001", help="chave do sensor do canteiro")
    parser.add_argument("--cenario", choices=CENARIOS.keys(), default="normal")
    parser.add_argument("--intervalo", type=float, default=5.0, help="segundos entre leituras")
    parser.add_argument("--vezes", type=int, default=0, help="quantas leituras (0 = sem parar)")
    parser.add_argument("--semente", type=int, default=42)
    args = parser.parse_args()

    umidade, queda = CENARIOS[args.cenario]
    sorte = random.Random(args.semente)
    guardadas: list[dict] = []  # sem conexao, guarda e reenvia depois
    enviadas = 0

    print(f"Simulador ligado: cenario={args.cenario}, api={args.api}. Ctrl+C para parar.")
    try:
        while args.vezes == 0 or enviadas < args.vezes:
            leitura = gerar_leitura(umidade, datetime.now(), sorte)
            guardadas.append(leitura)
            try:
                while guardadas:
                    status = enviar(args.api, args.chave, guardadas[0])
                    print(f"enviado {status}: {json.dumps(guardadas[0])}")
                    guardadas.pop(0)
                    enviadas += 1
            except urllib.error.HTTPError as erro:
                print(f"API recusou ({erro.code}): {erro.read().decode('utf-8', 'replace')}")
                return 1
            except (urllib.error.URLError, TimeoutError) as erro:
                print(f"sem conexao ({erro}); {len(guardadas)} leitura(s) guardada(s) para reenviar")
            umidade = max(5.0, umidade - queda)
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        print("\nSimulador parado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
