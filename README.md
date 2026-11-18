# Sereno: o clima da roça em aviso simples

**Global Solution 2026/2 (CitizenTech), FIAP, Engenharia de Software, turma 4ESOA**

O agricultor familiar decide quando irrigar e como se proteger do clima no olho: rega demais, descobre a doença tarde e perde a safra em geada ou calor que ninguém avisou. Só 1 em cada 5 estabelecimentos rurais recebe orientação técnica (IBGE, Censo Agro 2017). O Sereno junta sensores no canteiro, o clima e uma IA, e devolve ao produtor um aviso simples ("não precisa irrigar hoje", "regue 22 minutos", "risco de doença: olhe as folhas de baixo"). O produtor responde "1 fiz / 2 não fiz", e o técnico da Emater ou da cooperativa acompanha tudo num painel por comunidade.

- Problema, persona, ODS (2, 13 e 10) e a métrica de antes e depois: [`docs/problema.md`](docs/problema.md)
- Arquitetura geral, com as 4 áreas e como se ligam: [`docs/arquitetura.svg`](docs/arquitetura.svg)
- Camadas de dados: [`docs/camadas-de-dados.svg`](docs/camadas-de-dados.svg)
- Plano de testes: [`docs/plano-de-testes.md`](docs/plano-de-testes.md)

## Estrutura

| Pasta | Área | O que tem | Estado |
|---|---|---|---|
| [`area1-ia/`](area1-ia/) | 1: IA e automação | modelo de irrigação (scikit-learn), riscos de doença, geada e calor, mensagem em linguagem simples e o antes e depois | **roda pelo README e no CI** |
| [`area2-dados/`](area2-dados/) | 2: Big Data e visualização | pipeline bronze, prata e ouro com o clima real; CSVs e medidas DAX para o Power BI | **roda pelo README**; painel em montagem |
| [`area3-mvp/`](area3-mvp/) | 3: MVP, IoT e experiência digital | API Spring Boot, app Expo (5 telas), Arduino no TinkerCad e simulador | **roda pelo README** |
| [`area4-devops/`](area4-devops/) | 4: DevOps, segurança e qualidade | Docker, docker-compose, GitHub Actions, segurança e o fluxo ponta a ponta | **roda pelo README e no CI** |
| [`docs/`](docs/) | todas | problema, arquitetura, camadas de dados e plano de testes | em andamento |

Cada área tem o próprio README, com o passo a passo para rodar.

## Como rodar

- **Área 3 (app, API e sensores):** [`area3-mvp/README.md`](area3-mvp/README.md). Em resumo: `./mvnw spring-boot:run` na API, `python3 simulador.py` nos sensores e `npx expo start --web` no app.
- **Área 2 (dados):** [`area2-dados/README.md`](area2-dados/README.md). Em resumo: `pip install -r requirements.txt` e `python pipeline.py`.
- **Área 4 (Docker e CI):** [`area4-devops/README.md`](area4-devops/README.md). Em resumo: `cp .env.exemplo .env` e `docker compose up -d --build`. O CI roda a cada push (aba Actions do GitHub).
- **Área 1 (IA):** [`area1-ia/README.md`](area1-ia/README.md). Em resumo: `pip install -r requirements.txt`, `python treinar.py`, `python avaliar.py` e `python servico.py`.

## Vídeo pitch

Link: _a incluir_ (YouTube, Google Drive ou Vimeo, público).

## Uso de IA generativa no desenvolvimento

A regra da GS2 permite usar IA para pesquisar, revisar e explicar, desde que o grupo entenda e revise tudo o que entrega. Esta seção diz o que foi usado e para quê. Ela não fala da IA que faz parte do produto: essa é a Área 1.

| Ferramenta | Para quê | Onde | Revisado por |
|---|---|---|---|
| Claude Code (Anthropic, modelo Claude Opus 5.5), no terminal | propor a arquitetura; escrever a primeira versão da API, do app, do sketch do Arduino, do simulador e dos testes; explicar cada parte; procurar fontes dos dados do problema | áreas 3 e `docs/` | _a preencher após a revisão_ |
| Claude Code (Anthropic, modelo Claude Opus 5.5), no terminal | escrever a primeira versão do Dockerfile, do docker-compose, do CI, do plano de testes, do pipeline de dados (bronze, prata e ouro), dos testes do pipeline e das medidas DAX; calibrar o indicador de risco de doença no clima real; explicar cada parte | áreas 2 e 4 e `docs/` | _a preencher após a revisão_ |
| Claude Code (Anthropic, modelo Claude Opus 5.5), no terminal | escrever a primeira versão do treino, da decisão, dos riscos, da mensagem, do serviço, da avaliação de antes e depois, dos testes e do prompt; comparar modelos; explicar cada parte | área 1 | _a preencher após a revisão_ |

Como foi feito:
- Os testes automáticos (37 casos, rodando no GitHub Actions a cada push) e a execução pelo README conferem o que o código gerado faz.
- Os números do problema têm fonte pública citada em `docs/problema.md`; nenhum dado de mercado foi inventado.
- As respostas de usuários e os dados dos sensores são de demonstração, e o texto diz isso onde aparecem. O histórico de 60 dias da Área 2 é simulado sobre o clima real de Ibiúna (Open-Meteo), e o README da área explica o que é real e o que é simulado.

## Créditos e reaproveitamento

- A estrutura (API Spring Boot com app Expo) segue a da GS1 do grupo, AgroSat (2026/1), como referência. Nenhum arquivo foi copiado; o código desta GS2 foi escrito do zero.
- Bibliotecas de terceiros: as listadas em `area3-mvp/api/pom.xml`, `area3-mvp/app/package.json` e `area2-dados/requirements.txt`, cada uma com a própria licença.
- Clima: Open-Meteo (https://open-meteo.com/), dados abertos sob CC BY 4.0.

## Grupo

Nome do grupo, nomes e RM: no `.txt` da entrega (a incluir).
