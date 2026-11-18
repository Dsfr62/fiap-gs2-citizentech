# Área 1: IA e automação

A IA do Sereno responde todo dia, para cada canteiro: **regar hoje? quantos minutos? vem doença, geada ou calor?** E diz isso em linguagem simples, pronta para o WhatsApp, com o pedido "1 fiz / 2 não fiz".

| Item da nota | Onde está |
|---|---|
| IA aplicada | `treinar.py` (modelo de aprendizado de máquina) e `servico.py` (a IA no ar, ligada à API) |
| Prompts, agentes ou regras documentados | [`prompts/mensagem-ao-produtor.md`](prompts/mensagem-ao-produtor.md) e as regras de risco em `risco.py` |
| Demonstração com entrada e saída | `python demo.py` e os JSON em `exemplos/` |
| Lógica e ganho, com métrica antes e depois | `python avaliar.py` e [`resultados/antes_depois.md`](resultados/antes_depois.md) |

## Como a IA decide

1. **O modelo** (floresta aleatória do scikit-learn: várias árvores de decisão que votam) prevê **quanto a umidade do solo vai mudar nas próximas 24 h, se ninguém regar**. Ele olha o sensor agora (umidade e temperatura), a previsão do tempo das próximas 24 h (chuva, a água que o sol e o vento tiram do solo, máxima e umidade do ar) e a cultura.
2. **A decisão:** se a umidade prevista para amanhã fica abaixo do mínimo da cultura mais uma folga de 3 pontos, regar hoje. A quantidade leva o solo ao mínimo mais 10 pontos (0,4 mm por ponto, no máximo 8 mm, como a regra básica da API). Litros = mm × área; minutos = litros ÷ vazão.
3. **Os riscos** dos próximos 3 dias são regras agronômicas simples, com os mesmos limites do painel da Área 2:

| Risco | Regra | Médio | Alto |
|---|---|---|---|
| Doença nas folhas (ferrugem, míldio) | horas no dia com o ar a 95% ou mais e de 15 a 25 °C (folha molhada) | 6 h | 10 h |
| Geada | temperatura mínima | 6 °C ou menos | 3 °C ou menos |
| Calor | temperatura máxima | 30 °C ou mais | 32 °C ou mais |

4. **A mensagem** sai de `mensagem.py`, seguindo as regras do [prompt documentado](prompts/mensagem-ao-produtor.md): ação primeiro, o porquê com no máximo dois números, o risco mais grave com o que fazer, sem palavra técnica, e o pedido "Responda 1 se fez ou 2 se não fez".
5. **Sem previsão do tempo** (sem internet), a IA não chuta: decide só pelo sensor, com a regra básica, e diz isso na mensagem. **Se a IA cair**, a API usa a regra básica dela, e o produtor nunca fica sem resposta.

## O modelo, medido

Treinado com a **camada prata da Área 2**: as leituras limpas dos 7 canteiros, com o clima real de Ibiúna hora a hora. Cada exemplo é um canteiro às 6 h, nos dias sem rega (para aprender o solo sozinho). Teste honesto: treina nos primeiros 42 dias e mede nos 18 últimos, que ele nunca viu.

| Medida (nos 80 exemplos de teste) | Erro médio em 24 h (pontos de umidade) |
|---|---:|
| Supor que nada muda | 5,06 |
| **Modelo (floresta aleatória)** | **1,77** (R² 0,83) |
| Gabarito: a fórmula do próprio simulador | 1,17 |

O gabarito usa os números que nós mesmos pusemos no simulador da Área 2; no campo, ninguém sabe esses números para cada solo. O modelo chega perto dele **sem conhecê-los**, só olhando os dados. O que mais pesa: a chuva prevista (53%), a umidade de agora (34%) e a água que o sol tira (7%). Números em `modelo/metricas.json`, recriado a cada `python treinar.py`.

A folga de 3 pontos foi escolhida no **período de treino**, por uma regra fixada antes de olhar o teste: a menor folga que deixa o solo abaixo do mínimo em menos de 1% das horas (sem folga eram 2,5% das horas; com 3, 0,9%).

## Antes e depois

`python avaliar.py` roda os 7 canteiros por 60 dias com o **clima real de 01/09 a 30/10/2025**, que o modelo nunca viu, com a mesma física do solo do gerador da Área 2:

| Jeito de regar | Água (L) | Economia contra o calendário | Água perdida (L) | Horas com o solo abaixo do mínimo | Acerto do alerta |
|---|---:|---:|---:|---:|---:|
| Antes: calendário (30 min por dia) | 279.000 | 0,0% | 146.535 | 0 | |
| Regra básica (só o sensor) | 109.915 | 60,6% | 9.379 | 4.967 | 49,9% |
| **Depois: IA (sensor e previsão)** | **108.065** | **61,3%** | **3.413** | **581** | **98,3%** |

- **Contra o calendário:** 61% menos água. Metade da água do calendário escorre sem a planta usar (solo já cheio ou chuva logo depois).
- **Contra a regra básica:** quase a mesma água, mas 88% menos horas com a planta sofrendo e 64% menos água perdida, porque a IA rega antes de secar e segura a rega quando vem chuva.
- **Acerto do alerta:** na manhã seguinte, o solo estava acima do mínimo e a rega do dia não se perdeu.

**Medido pelas respostas "1 fiz / 2 não fiz":** com cada produtor seguindo o alerta com a chance que tem no gerador da Área 2 (de 50% a 90%), a taxa de "fiz" foi 75,8%. Quando o produtor respondeu "fiz", o alerta acertou em **92,7%** das vezes; quando respondeu "não fiz", em **22,0%**. É a prova, pela resposta do próprio produtor, de que seguir o aviso funciona.

**Limites, ditos:** a planta e o solo são simulados (o clima é real); a "previsão" da avaliação é o clima que de fato aconteceu, e previsão de verdade erra, então o ganho real tende a ser um pouco menor.

## O que precisa estar instalado

Python 3.10 ou mais novo, com o pandas e o scikit-learn (`requirements.txt`).

## Como rodar

De dentro de `area1-ia/`:

```bash
python3 -m venv .venv
source .venv/bin/activate          # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
python treinar.py                  # treina o modelo (se a prata da Área 2 não existir, roda o pipeline antes)
python avaliar.py                  # antes e depois, sem internet
python demo.py                     # 3 exemplos de entrada e saída, sem internet
python servico.py                  # a IA no ar em http://localhost:8001
```

Com o serviço no ar, num outro terminal:

```bash
curl http://localhost:8001/saude
curl -X POST http://localhost:8001/recomendar -H 'Content-Type: application/json' -d '{
  "canteiroId": 1, "cultura": "FOLHOSA", "areaM2": 120, "vazaoLitrosMin": 30,
  "latitude": -23.6566, "longitude": -47.2229,
  "umidadeSolo": 41.5, "temperaturaAr": 24, "luminosidade": 70, "umidadeMinima": 45 }'
```

A resposta traz `regar`, `minutos`, `explicacao` e `chuvaPrevistaMm` (o que a API lê), mais `litros`, `umidadePrevista24h`, `riscos`, `mensagemWhatsapp` e de onde veio a previsão.

**Com a API e o app (Área 3):** com a IA no ar na porta 8001, a API já a chama sozinha (`IA_URL`, padrão `http://localhost:8001`). No app, "Pedir recomendação agora" mostra a mensagem da IA, e a tela diz que a decisão veio da IA. No Docker, `docker compose up -d --build` sobe a IA junto (README da Área 4).

## Exemplos de entrada e saída

`python demo.py` escolhe três manhãs reais de 2025 e mostra o que entra e o que sai; os JSON completos ficam em `exemplos/`.

| Situação | Entra | Sai |
|---|---|---|
| Dia seco e de sol (05/10/2025) | solo 46%, sem chuva, sol forte (5,4 mm de água tirada) | regar 32 min (960 L); solo previsto 35% |
| Chuva forte prevista (22/09/2025) | solo 42%, 22,7 mm de chuva | não regar; solo previsto 59%: "a chuva prevista dá conta" |
| Tempo abafado (16/10/2025) | solo 58%, sem chuva forte | regar 14 min; aviso de risco alto de doença nas folhas no sábado |

As mensagens completas estão no [prompt documentado](prompts/mensagem-ao-produtor.md).

## Segurança

- O serviço valida cada pedido (faixas iguais às da API, cultura conhecida, latitude e longitude válidas) e responde 400 com os campos errados (CT35); corpo acima de 10 KB é recusado.
- O log registra só a rota e o código de resposta, nunca os dados do canteiro.
- O modelo só é aberto do arquivo que o próprio `treinar.py` gerou (`modelo/`, fora do Git); no Docker, ele é treinado na montagem da imagem.
- No Docker, o serviço roda como usuário comum, não como root.

## Testes

```bash
python -m unittest discover -s testes -v
```

Oito casos (CT28 a CT35): regar no seco, segurar a rega com chuva, decidir sem previsão, os três riscos, a mensagem simples, o modelo contra "nada muda", o contrato da API e o pedido inválido. Os testes não usam a internet. O plano inteiro está em [`docs/plano-de-testes.md`](../docs/plano-de-testes.md).

## Ferramentas de IA usadas nesta área

O Claude Code (Anthropic, modelo Claude Opus 5.5) escreveu a primeira versão dos scripts, dos testes, do prompt e deste README, comparou modelos e explicou cada parte. Os testes, o erro medido no período de teste e a avaliação em 2025 conferem o resultado. A folga de segurança foi escolhida no período de treino, para o teste ficar limpo. Detalhe na seção "Uso de IA generativa" do README da raiz.
