"""Le os relatorios do JUnit (surefire) e escreve uma tabela em Markdown com cada caso de teste.

Uso: python3 area4-devops/resumo_testes.py [pasta-dos-relatorios] [pasta-dos-testes]
Padrao: area3-mvp/api/target/surefire-reports e area3-mvp/api/src/test/java.

No CI, a saida vai para o resumo da execucao (GITHUB_STEP_SUMMARY): e o print do plano de testes.
So biblioteca padrao do Python.
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RELATORIOS = Path(sys.argv[1] if len(sys.argv) > 1 else "area3-mvp/api/target/surefire-reports")
TESTES = Path(sys.argv[2] if len(sys.argv) > 2 else "area3-mvp/api/src/test/java")

# Nome do metodo -> texto do @DisplayName ("CT01 - ..."), lido do codigo dos testes.
PADRAO = re.compile(r'@DisplayName\("([^"]+)"\)\s*void\s+(\w+)\s*\(')
nomes = {}
for arquivo in TESTES.rglob("*.java"):
    for texto, metodo in PADRAO.findall(arquivo.read_text(encoding="utf-8")):
        nomes[metodo] = texto

linhas = []
for xml in sorted(RELATORIOS.glob("TEST-*.xml")):
    for caso in ET.parse(xml).getroot().iter("testcase"):
        falhou = caso.find("failure") is not None or caso.find("error") is not None
        pulou = caso.find("skipped") is not None
        estado = "falhou" if falhou else ("pulado" if pulou else "passou")
        metodo = caso.get("name", "").split("(")[0]
        linhas.append((nomes.get(metodo, metodo), estado, float(caso.get("time", 0))))

linhas.sort()
print("| Caso | Resultado | Tempo (s) |")
print("|---|---|---:|")
for nome, estado, tempo in linhas:
    marca = "✅" if estado == "passou" else ("⏭️" if estado == "pulado" else "❌")
    print(f"| {nome} | {marca} {estado} | {tempo:.2f} |")
passaram = sum(1 for _, e, _ in linhas if e == "passou")
print(f"\n**{passaram} de {len(linhas)} casos passaram.**")
sys.exit(0 if linhas and passaram == len(linhas) else 1)
