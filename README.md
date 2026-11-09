# GS2 CitizenTech · irrigação na medida para o agricultor familiar

**Global Solution 2026/2 · FIAP · Engenharia de Software · turma 4ESOA**

O pequeno produtor de hortaliças decide quando e quanto regar no hábito, sem saber a umidade do solo nem se vai chover. Esta solução põe dois sensores no canteiro, junta a previsão do tempo e uma IA, e responde todo dia: **"regar hoje? quantos minutos?"**, com o porquê em linguagem simples. O técnico da cooperativa acompanha todos os produtores num painel.

- Problema, persona, ODS (2, 13 e 10) e a métrica de antes e depois: [`docs/problema.md`](docs/problema.md)
- Arquitetura geral, com as 4 áreas e como se ligam: [`docs/arquitetura.svg`](docs/arquitetura.svg)

> O nome final da solução ainda vai ser escolhido. Hoje ele está numa constante só: `area3-mvp/app/src/config.ts`.

## Estrutura

| Pasta | Área | O que tem | Estado |
|---|---|---|---|
| [`area1-ia/`](area1-ia/) | 1 · IA e automação | serviço de IA (Python): modelo, previsão e explicação | a fazer |
| [`area2-dados/`](area2-dados/) | 2 · Big Data e visualização | pipeline bronze, prata e ouro, mais o painel Power BI | a fazer |
| [`area3-mvp/`](area3-mvp/) | 3 · MVP, IoT e experiência digital | API Spring Boot, app Expo, Arduino e simulador | **rodando** |
| [`area4-devops/`](area4-devops/) | 4 · DevOps, segurança e qualidade | Docker, CI, plano de testes e segurança | a fazer |
| [`docs/`](docs/) | todas | problema, arquitetura e evidências para o PDF | em andamento |

Cada área tem o próprio README, com o passo a passo para rodar.

## Como rodar

- **Área 3:** [`area3-mvp/README.md`](area3-mvp/README.md). Em resumo: `./mvnw spring-boot:run` na API, `python3 simulador.py` nos sensores e `npx expo start --web` no app.
- Áreas 1, 2 e 4: em construção.

## Vídeo pitch

Link: _a incluir_ (YouTube, Google Drive ou Vimeo, público).

## Uso de IA generativa no desenvolvimento

A regra da GS2 permite usar IA para pesquisar, revisar e explicar, desde que o grupo entenda e revise tudo o que entrega. Esta seção diz o que foi usado e para quê. Ela não fala da IA que faz parte do produto: essa é a Área 1.

| Ferramenta | Para quê | Onde | Revisado por |
|---|---|---|---|
| Claude Code (Anthropic, modelo Claude Opus 5.5), no terminal | propor a arquitetura; escrever a primeira versão da API, do app, do sketch do Arduino, do simulador e dos testes; explicar cada parte; procurar fontes dos dados do problema | áreas 3 e `docs/` | _a preencher após a revisão_ |

Como foi feito:
- Os testes automáticos (14 casos na API) e a execução pelo README conferem o que o código gerado faz.
- Os números do problema têm fonte pública citada em `docs/problema.md`; nenhum dado de mercado foi inventado.
- As respostas de usuários e os dados dos sensores são de demonstração, e o texto diz isso onde aparecem.

## Créditos e reaproveitamento

- A estrutura (API Spring Boot com app Expo) segue a da GS1 do grupo, AgroSat (2026/1), como referência. Nenhum arquivo foi copiado; o código desta GS2 foi escrito do zero.
- Bibliotecas de terceiros: as listadas em `area3-mvp/api/pom.xml` e `area3-mvp/app/package.json`, cada uma com a própria licença.

## Grupo

Nome do grupo, nomes e RM: no `.txt` da entrega (a incluir).
