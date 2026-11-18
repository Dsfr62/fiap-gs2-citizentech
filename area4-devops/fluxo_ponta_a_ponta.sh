#!/usr/bin/env bash
# Fluxo ponta a ponta do Sereno, de verdade, contra a API rodando:
# sensor -> API -> IA -> alerta -> resposta "1 fiz" -> pipeline (bronze, prata e ouro).
# Com ESPERA_IA=1, confere que o alerta veio da IA (Area 1) e nao da regra basica.
# Precisa: a API no ar (docker compose up -d) e o pandas instalado (area2-dados/requirements.txt).
# O CI roda este mesmo script no job do Docker.
set -euo pipefail

API="${SERENO_API_URL:-http://localhost:8080}"
SENHA="${SERENO_SENHA:-horta2026}"
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
json() { python3 -c "import json,sys; d=json.load(sys.stdin); print($1)"; }

echo "1. sensor: 3 leituras de solo seco no canteiro de alface"
python3 "$RAIZ/area3-mvp/iot/simulador.py" --api "$API" --cenario seco --vezes 3 --intervalo 1

echo "2. produtor: login do Jorge"
TOKEN=$(curl -fsS -X POST "$API/api/auth/login" -H 'Content-Type: application/json' \
  -d "{\"email\":\"jorge@exemplo.com\",\"senha\":\"$SENHA\"}" | json 'd["token"]')
ALFACE=$(curl -fsS "$API/api/canteiros" -H "Authorization: Bearer $TOKEN" \
  | json '[c["id"] for c in d if "Alface" in c["nome"]][0]')

echo "3. alerta: recomendação para o canteiro $ALFACE"
REC=$(curl -fsS -X POST "$API/api/canteiros/$ALFACE/recomendacoes" -H "Authorization: Bearer $TOKEN")
echo "$REC" | json '"   regar=%s, %s min, decidido por %s" % (d["regar"], d["minutos"], d["origem"])'
REGAR=$(echo "$REC" | json 'str(d["regar"]).lower()')
MINUTOS=$(echo "$REC" | json 'd["minutos"]')

if [ "$REGAR" = "true" ]; then
  echo "4. resposta: o Jorge regou $MINUTOS min, como o alerta pediu (1 fiz)"
  curl -fsS -X POST "$API/api/canteiros/$ALFACE/regas" -H "Authorization: Bearer $TOKEN" \
    -H 'Content-Type: application/json' -d "{\"minutos\":$MINUTOS,\"seguiuRecomendacao\":true}" > /dev/null
else
  echo "4. resposta: o alerta disse para não regar; a resposta fica aguardando as 24 h"
fi

echo "5. pipeline: bronze, prata e ouro, com a API logada como técnica"
cd "$RAIZ/area2-dados"
python3 pipeline.py --api

echo "6. conferência: o alerta da API chegou à prata com a resposta"
REGAR="$REGAR" ESPERA_IA="${ESPERA_IA:-0}" python3 - <<'PY'
import os
import pandas as pd
a = pd.read_csv("dados/prata/alertas.csv", encoding="utf-8-sig")
api = a[a["canteiro_chave"].str.startswith("api-")]
print(api[["canteiro_chave", "momento_local", "regar", "minutos", "decidido_por", "resposta"]].to_string(index=False))
print("mensagem:", api["explicacao"].iloc[-1])
assert len(api) >= 1, "nenhum alerta da API chegou à prata"
if os.environ["REGAR"] == "true":
    assert (api["resposta"] == "fiz").any(), "a rega do Jorge não virou 'fiz' na prata"
if os.environ["ESPERA_IA"] == "1":
    assert (api["decidido_por"] == "IA").all(), "o alerta não veio da IA (a API caiu na regra básica)"
print("OK: sensor -> API -> IA -> alerta -> resposta -> pipeline")
PY
