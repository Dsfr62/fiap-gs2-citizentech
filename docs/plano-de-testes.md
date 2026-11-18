# Plano de testes do Sereno

> Área 4: DevOps, segurança e qualidade. 27 casos, todos automáticos, rodando no GitHub Actions a cada push (`.github/workflows/ci.yml`). Este texto vai para o PDF da entrega.

## Como o plano está montado

| Nível | Ferramenta | Onde está | Quantos |
|---|---|---|---:|
| Unidade e integração da API | JUnit 5 + Spring MockMvc | `area3-mvp/api/src/test/java/` | 15 |
| Unidade do pipeline de dados | `unittest` (biblioteca padrão do Python) | `area2-dados/testes/test_pipeline.py` | 5 |
| Build e conferência estática | TypeScript (`tsc`), `py_compile`, Docker | `.github/workflows/ci.yml` | 4 |
| Sistema (ponta a ponta) | `curl`, simulador e pipeline contra a API no Docker | `area4-devops/fluxo_ponta_a_ponta.sh` e o CI | 3 |

Cada caso tem um código (CT01 a CT27). O mesmo código aparece no nome do teste, no resumo do CI e aqui.

## Casos de teste

| CT | O que confere | Tipo | Entrada | Resultado esperado | Job do CI |
|---|---|---|---|---|---|
| CT01 | Login com a senha certa | integração | `jorge@exemplo.com` e a senha certa | 200 e um token JWT | API |
| CT02 | Login com a senha errada | segurança | senha errada | 401, sem token | API |
| CT03 | Rota protegida sem token | segurança | `GET /api/canteiros` sem `Authorization` | 401 | API |
| CT04 | Sensor com chave inválida | segurança | `POST /api/leituras` com chave falsa | 401, leitura não gravada | API |
| CT05 | Leitura fora da faixa | validação | umidade do solo 150% | 400, com o campo que falhou | API |
| CT06 | Produtor não vê o canteiro do outro | segurança (dados do produtor) | Maria pede o canteiro do Jorge | 404 | API |
| CT07 | Lista só os próprios canteiros | segurança (dados do produtor) | Jorge lista canteiros | só os 2 dele, com o nome dele | API |
| CT08 | Fluxo completo na API | integração | leitura seca, recomendação, rega | rega de 32 min e 960 L registrada | API |
| CT09 | Exportação de leituras só para o técnico | segurança (papel) | Ana e Jorge pedem `/api/dados/leituras` | Ana 200, Jorge 403 | API |
| CT10 | Cadastro com senha curta | validação | senha de 3 caracteres | 400 no campo `senha` | API |
| CT11 | Monitoramento sem login | monitoramento | `GET /actuator/health` | 200 e `UP` | API |
| CT12 | Regra básica: solo úmido | unidade | umidade acima do mínimo | não rega | API |
| CT13 | Regra básica: solo seco | unidade | 120 m², 30 L/min, solo seco | 32 min, 960 L | API |
| CT14 | Regra básica: dia quente e de sol | unidade | 30 °C ou mais e sol forte | soma 1 mm, sem passar do teto | API |
| CT15 | Exportação de canteiros, alertas e regas | segurança e integração | Ana e Jorge pedem `/api/dados/...` | Ana 200 sem a chave do sensor; Jorge 403 | API |
| CT16 | Tipos do app | estático | `npx tsc --noEmit` | nenhum erro de TypeScript | App |
| CT17 | Sintaxe dos scripts Python | estático | `py_compile` no simulador, no pipeline e no resumo | nenhum erro | Python |
| CT18 | Imagem Docker da API | build | `docker compose build api` (duas etapas) | imagem montada, só com o JRE | Docker |
| CT19 | Compose sobe e fica saudável | sistema / monitoramento | `docker compose up -d` (PostgreSQL + API) | `/actuator/health` = `UP` em até 120 s | Docker |
| CT20 | Limpeza da prata | unidade | leitura repetida, fora da faixa e com horário ilegível | as 3 saem, e cada uma é contada | Python |
| CT21 | Fuso horário | unidade | `09:00Z` e `06:00-03:00` | os dois viram 06:00 de São Paulo | Python |
| CT22 | Resposta "fiz / não fiz" | unidade | alerta com e sem rega nas 24 h | fiz, não fiz e aguardando nos casos certos | Python |
| CT23 | Horas abaixo do mínimo e água | unidade | 3 horas, 2 abaixo de 45%; rega de 300 L | 2 horas; 900 L no calendário, 600 L economizados | Python |
| CT24 | Semente fixa | unidade | gerador rodado duas vezes | o mesmo histórico, com 60 dias | Python |
| CT25 | Pipeline pelo README | sistema | `python pipeline.py --offline` | CSVs da ouro em `powerbi/` | Python |
| CT26 | Fumaça no PostgreSQL | sistema / segurança | login da Ana, exportação, rota sem token | token, 3 canteiros, 401 | Docker |
| CT27 | Ponta a ponta | sistema | simulador seco → alerta → rega → pipeline `--api` | o alerta da API chega à prata como "fiz" | Docker |

## Como rodar

- Tudo de uma vez: cada push na `main` dispara o CI. Ver em **Actions** no GitHub (o caminho está em `area4-devops/README.md`).
- Só a API: `cd area3-mvp/api && ./mvnw test` (CT01 a CT15).
- Só o pipeline: `cd area2-dados && python -m unittest discover -s testes -v` (CT20 a CT24).
- Ponta a ponta na máquina: `docker compose up -d` e depois `./area4-devops/fluxo_ponta_a_ponta.sh` (CT27).

## Evidência da execução

A execução que vale para a entrega é a última verde na `main`. O link e os prints ficam em [`area4-devops/README.md`](../area4-devops/README.md#evidência-da-execução). O resumo de cada execução lista os 15 casos da API com o resultado, o resultado do Docker, a saída do pipeline e a do fluxo ponta a ponta.
