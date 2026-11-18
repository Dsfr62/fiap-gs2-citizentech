"""Roda o pipeline inteiro do Sereno (Area 2): bronze -> prata -> ouro -> CSV do Power BI.

    python pipeline.py              # clima real + historico simulado de 60 dias
    python pipeline.py --offline    # sem internet: usa a copia do clima guardada em amostra/
    python pipeline.py --api        # tambem puxa da API do Sereno (precisa da API rodando, Area 3)

Variaveis opcionais para --api: SERENO_API_URL (padrao http://localhost:8080),
SERENO_EMAIL (padrao ana@exemplo.com) e SERENO_SENHA (padrao: a senha de demonstracao do README da Area 3).
"""
import argparse
import os
import shutil
import time

import gerador
import ouro
import prata
from comum import DADOS
from ingestao import ingerir_api, ingerir_clima_historico, ingerir_clima_recente


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline de dados do Sereno (bronze, prata e ouro)")
    parser.add_argument("--offline", action="store_true", help="nao acessa a internet (clima da pasta amostra/)")
    parser.add_argument("--api", action="store_true", help="tambem exporta da API do Sereno, logado como tecnica")
    args = parser.parse_args()

    inicio = time.time()
    if DADOS.exists():
        shutil.rmtree(DADOS)   # cada rodada recria tudo do zero: o resultado nao depende da anterior

    print("1/4 bronze: ingestao")
    caminho_clima = ingerir_clima_historico(offline=args.offline)
    gerador.gerar(caminho_clima)
    if args.api:
        ingerir_clima_recente()
        ingerir_api(os.environ.get("SERENO_API_URL", "http://localhost:8080"),
                    os.environ.get("SERENO_EMAIL", "ana@exemplo.com"),
                    os.environ.get("SERENO_SENHA", "horta2026"))

    print("2/4 prata: limpeza e clima por hora")
    prata.rodar()

    print("3/4 ouro: resumo diario por canteiro")
    print("4/4 saida para o Power BI")
    ouro.rodar()

    print(f"\nPronto em {time.time() - inicio:.1f} s. Abra area2-dados/powerbi/ no Power BI (README, passo 4).")


if __name__ == "__main__":
    main()
