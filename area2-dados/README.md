# Área 2: Big Data e visualização

O caminho do dado no Sereno: a leitura do sensor e a resposta do produtor ("1 fiz / 2 não fiz") saem da API, juntam-se ao clima real de Ibiúna e viram, em três camadas, os indicadores do painel do técnico da Emater ou da cooperativa.

| Item da nota | Onde está |
|---|---|
| Modelo de dados em camadas | bronze, prata e ouro (abaixo) e o diagrama [`docs/camadas-de-dados.svg`](../docs/camadas-de-dados.svg) |
| Ingestão e processamento, da coleta ao dado tratado | `ingestao.py`, `gerador.py`, `prata.py` e `ouro.py`, rodados por `pipeline.py` |
| Dashboard com 3+ indicadores e filtros | os CSVs de `powerbi/` e o roteiro do painel (passo 4) |
| Funções analíticas | as medidas DAX (passo 5) |

## O que precisa estar instalado

Python 3.9 ou mais novo e o pandas (`requirements.txt`). Nada mais. A rede só é usada para o clima (Open-Meteo, sem chave) e, se você pedir, para a API.

## Como rodar

De dentro de `area2-dados/`:

```bash
python3 -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
python pipeline.py
```

A saída mostra as quatro etapas e termina com o resumo por comunidade. Leva cerca de 2 segundos.

| Comando | O que muda |
|---|---|
| `python pipeline.py` | baixa o clima real do Open-Meteo e gera o histórico de 60 dias |
| `python pipeline.py --offline` | sem internet: usa a cópia do clima que está em `amostra/` (a mesma resposta do Open-Meteo, guardada em 18/11/2026) |
| `python pipeline.py --api` | também exporta da API do Sereno, logado como a técnica Ana; precisa da API no ar (README da Área 3 ou `docker compose up -d`) |

Cada rodada apaga `dados/` e recria tudo, então o resultado não depende da anterior.

## As camadas

| Camada | Pasta | O que tem | Quem escreve |
|---|---|---|---|
| **Bronze** (crua) | `dados/bronze/` | a resposta do Open-Meteo e da API **como veio**, sem mexer; o histórico simulado no mesmo formato da API | `ingestao.py`, `gerador.py` |
| **Prata** (tratada) | `dados/prata/` | leituras limpas, em hora local, cada uma com o clima da mesma hora; alertas com a resposta; regas; e `qualidade.csv`, que conta o que foi tirado | `prata.py` |
| **Ouro** (analítica) | `dados/ouro/` e `powerbi/` | o resumo diário por canteiro, os alertas, a curva por hora e o resumo por comunidade | `ouro.py` |

### Da bronze à prata: o que a limpeza faz

| Problema no dado cru | Por que acontece | O que a prata faz | Na rodada padrão |
|---|---|---|---:|
| valor fora da faixa (umidade 150% ou -1%) | sensor com defeito | tira a leitura (mesmas faixas da API) | 39 |
| leitura repetida | o sensor reenvia quando o sinal volta | fica uma por canteiro e instante | 196 |
| dois fusos | a API manda em UTC (`Z`), o sensor às vezes em `-03:00`, o Open-Meteo em hora local | tudo vira hora local de São Paulo | todas |
| horário ilegível | dado corrompido | tira a leitura | 0 |

Depois da limpeza, cada leitura recebe o clima da mesma hora (chuva, umidade do ar, temperatura e evapotranspiração).

**A resposta "fiz / não fiz".** Hoje ela vem da rega registrada no app: se o alerta pediu para regar e o produtor regou seguindo a recomendação nas 24 h seguintes, é "fiz"; se o alerta disse que não precisava e ele regou mesmo assim, é "não fiz"; enquanto as 24 h não passam, é "aguardando". Quando a resposta pelo WhatsApp existir, ela entra como mais uma coluna do alerta.

### A ouro (modelo estrela)

| Tabela | Uma linha é | Colunas principais |
|---|---|---|
| `fato_diario_canteiro` | um dia de um canteiro | `umidade_media`, `umidade_minima_do_dia`, `horas_abaixo_do_minimo`, `litros_usados`, `litros_calendario`, `litros_economizados`, `chuva_mm`, `alertas_enviados`, `respostas_fiz`, `respostas_nao_fiz`, `risco_doenca`, `risco_geada`, `risco_calor` |
| `dim_canteiro` | um canteiro | `cultura`, `produtor`, `comunidade`, `area_m2`, `vazao_l_min`, `umidade_minima` |
| `alertas` | um alerta enviado | `data`, `hora`, `regar`, `minutos`, `litros`, `decidido_por` (IA ou regra básica), `resposta` |
| `leituras_por_hora` | uma hora de um canteiro | `umidade_solo`, `temperatura_ar`, `chuva_mm`, `abaixo_do_minimo` |
| `resumo_comunidade` | uma comunidade | `taxa_de_fiz_pct`, `agua_economizada_pct`, `horas_abaixo_do_minimo`, `dias_risco_doenca_alto` |

A chave que liga tudo é `canteiro_chave` (`sim-101` para o simulado, `api-1` para o que veio da API).

**Água economizada** = o que o produtor gastaria no costume (30 minutos por dia, como o Seu Jorge de `docs/problema.md`) menos o que ele regou com o Sereno. A medição completa de antes e depois, com o solo simulado nos dois casos, é da Área 1.

**Riscos do clima** são indicadores por regra simples, calibrados no clima real de Ibiúna: doença = horas no dia com o ar a 95% ou mais e de 15 a 25 °C (folha molhada, onde míldio e ferrugem se espalham), alto com 10 h e médio com 6 h; geada = mínima de 3 °C (alto) ou 6 °C (médio); calor = máxima de 32 °C (alto) ou 30 °C (médio). O modelo de risco de verdade é da Área 1.

## O histórico simulado (declarado)

O Sereno ainda não tem estação no campo. Para o painel ter 60 dias de história, `gerador.py` imita **7 canteiros em 3 comunidades** de Ibiúna (Água Limpa, Pinhal e Ponte Alta) de **01/09 a 30/10/2026**:

- **real:** o clima, hora a hora, do Open-Meteo para Ibiúna (-23.6566, -47.2229);
- **simulado:** a umidade do solo (balanço simples de água: perde pela evapotranspiração, ganha com chuva e rega), o ruído e os defeitos do sensor, os alertas (a mesma regra básica da API) e a resposta de cada produtor (cada um segue o alerta com uma chance diferente);
- **semente fixa** (`2026`): rodar duas vezes dá o mesmo resultado (CT24).

O arquivo `dados/bronze/simulado/_LEIA.txt` repete isso. Pessoas, canteiros e comunidades são fictícios.

## Passo 4: o painel no Power BI

Os CSVs prontos estão em `powerbi/` (vírgula entre colunas, ponto nos decimais, UTF-8). Dá para montar o painel sem rodar o Python.

1. No Power BI (Desktop ou pela web), **Obter dados > Texto/CSV** e carregue os cinco arquivos de `powerbi/`. Se os números vierem errados (ponto lido como milhar), em **Transformar dados**, troque a localidade da coluna para "Inglês (Estados Unidos)".
2. **Relacionamentos:** `dim_canteiro[canteiro_chave]` 1:N com `fato_diario_canteiro`, `alertas` e `leituras_por_hora`.
3. Indicadores sugeridos (o grupo pediu estes quatro):

| Indicador | Visual | De onde vem |
|---|---|---|
| Taxa de "fiz" por comunidade | cartão e barras | `alertas[resposta]` |
| Água economizada | cartão (litros e %) e linha por dia | `fato_diario_canteiro[litros_economizados]` |
| Alertas enviados | colunas por dia, cor por `regar` | `alertas` |
| Risco por comunidade | matriz comunidade × dia, cor pelo risco | `fato_diario_canteiro[risco_doenca]` |
| (extra) Umidade do solo e chuva | linha por hora, com a linha do mínimo | `leituras_por_hora` |

4. Filtros (segmentações): `comunidade`, `cultura`, `produtor` e o período (`data`).

## Passo 5: medidas DAX

```DAX
Alertas enviados = COUNTROWS ( alertas )

Respostas fiz = CALCULATE ( COUNTROWS ( alertas ), alertas[resposta] = "fiz" )

Taxa de fiz =
DIVIDE (
    [Respostas fiz],
    CALCULATE ( COUNTROWS ( alertas ), alertas[resposta] IN { "fiz", "não fiz" } )
)

Água economizada (L) = SUM ( fato_diario_canteiro[litros_economizados] )

Água economizada (%) =
DIVIDE ( [Água economizada (L)], SUM ( fato_diario_canteiro[litros_calendario] ) )

Horas abaixo do mínimo = SUM ( fato_diario_canteiro[horas_abaixo_do_minimo] )

Dias com risco alto de doença =
CALCULATE ( DISTINCTCOUNT ( fato_diario_canteiro[data] ), fato_diario_canteiro[risco_doenca] = "alto" )
```

Na rodada padrão, o resumo por comunidade (`powerbi/resumo_comunidade.csv`) dá a referência para conferir as medidas: taxa de "fiz" de 65% a 81% e água economizada de 60% a 74% contra a rega por calendário, num período chuvoso (491 mm em 60 dias).

## Testes

```bash
python -m unittest discover -s testes -v
```

Cinco casos (CT20 a CT24): limpeza, fuso, resposta "fiz / não fiz", horas abaixo do mínimo e água, e a semente fixa. O plano inteiro está em [`docs/plano-de-testes.md`](../docs/plano-de-testes.md); o CI roda estes testes e o pipeline a cada push.

## Ferramentas de IA usadas nesta área

O Claude Code (Anthropic, modelo Claude Opus 5.5) escreveu a primeira versão dos scripts, dos testes e deste README e explicou cada parte. Os testes, a contagem de `qualidade.csv` e o resumo por comunidade conferem o resultado. A calibração do risco de doença foi feita olhando o clima real (com 90% de umidade do ar, quase todo dia dava risco alto). Detalhe na seção "Uso de IA generativa" do README da raiz.
