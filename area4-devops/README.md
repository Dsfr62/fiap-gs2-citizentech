# Área 4: DevOps, segurança e qualidade

O que esta área entrega, e onde está cada item da nota:

| Item da nota | Onde está |
|---|---|
| Código organizado por módulos e versionado em Git | o repositório, uma pasta por área (README da raiz) |
| Docker e CI funcionando | `area3-mvp/api/Dockerfile`, `docker-compose.yml` e `.github/workflows/ci.yml` |
| 2+ práticas de segurança | a tabela "Segurança", abaixo, com arquivo e linha |
| Plano com 5+ casos de teste e a execução | [`docs/plano-de-testes.md`](../docs/plano-de-testes.md) (27 casos) e "Evidência da execução", abaixo |

## O CI (GitHub Actions)

A cada push na `main` ou pull request, o arquivo `.github/workflows/ci.yml` roda quatro jobs:

| Job | O que faz | Casos |
|---|---|---|
| API Java | compila com o Maven Wrapper, roda o JUnit e escreve a tabela dos casos no resumo | CT01 a CT15 |
| App Expo | instala com `npm ci` e confere os tipos com o TypeScript | CT16 |
| Python | confere a sintaxe dos scripts, roda os testes do pipeline e o pipeline inteiro como o README manda | CT17, CT20 a CT25 |
| Docker | só roda se a API passou: monta a imagem, sobe o compose, espera o `/actuator/health`, faz a fumaça no PostgreSQL e o fluxo ponta a ponta | CT18, CT19, CT26, CT27 |

**Como ver:** no GitHub, aba **Actions**, workflow **CI**, a execução mais recente. Cada job mostra os passos; o **Summary** da execução traz as tabelas (casos da API, Docker, pipeline e fluxo). Os relatórios do JUnit ficam em **Artifacts** (`relatorios-testes-api`).

O Docker não roda na máquina de quem desenvolveu (um Mac com 8 GB). Por isso a prova do Docker é o próprio CI, que monta a imagem e sobe o compose num servidor do GitHub a cada push.

## Como rodar o compose na sua máquina

Precisa do Docker Desktop (ou do Docker Engine com o plugin `compose`).

```bash
cp .env.exemplo .env          # e troque os dois valores dentro do .env
docker compose up -d --build  # sobe o PostgreSQL e a API
curl http://localhost:8080/actuator/health    # {"status":"UP"}
```

- A primeira vez demora alguns minutos (baixa as imagens e as dependências do Maven).
- A API fica em http://localhost:8080 (Swagger em `/swagger-ui.html`), já com os usuários de demonstração do README da Área 3.
- O app e o simulador rodam fora do Docker, como no README da Área 3, apontando para a mesma porta 8080.
- Para o fluxo ponta a ponta (sensor, alerta, "fiz" e pipeline): `pip install -r area2-dados/requirements.txt` e depois `./area4-devops/fluxo_ponta_a_ponta.sh`.
- Para parar: `docker compose down` (com `-v`, apaga também o banco).

### O que tem em cada arquivo

- **`area3-mvp/api/Dockerfile`**, em duas etapas. A primeira usa o JDK 17 e o `mvnw` para gerar o `.jar`; a segunda parte de uma imagem só com o JRE 17 e copia apenas o `.jar`. A imagem final não leva código-fonte nem Maven, e a API roda com um usuário sem poder de administrador.
- **`docker-compose.yml`**: o `banco` (PostgreSQL 16) com teste de saúde (`pg_isready`); a `api`, que só sobe depois do banco saudável; e o lugar do serviço de IA (Área 1), comentado até ele existir. Sem a IA, a API usa a regra básica e diz isso na tela.
- **`.env.exemplo`**: o modelo dos segredos. O `.env` de verdade fica fora do Git.

## Segurança

| Prática | Onde | O que faz |
|---|---|---|
| Login com token JWT | `area3-mvp/api/src/main/java/br/com/fiap/gs2/security/TokenService.java:28`, `:37` e `:44` | assina com HMAC-256, expira em 8 h e confere a assinatura e o emissor a cada pedido |
| Senha com hash BCrypt | `.../security/SegurancaConfig.java:52-55` | a senha vira um hash com sal; nem quem lê o banco descobre a senha |
| Rotas fechadas por padrão e por papel | `.../security/SegurancaConfig.java:41-46` | só login, cadastro, sensor e saúde ficam abertos; `/api/dados/**` só para o técnico (CT09, CT15) |
| API sem sessão | `.../security/SegurancaConfig.java:39` | `STATELESS`: cada pedido se prova com o token |
| Validação de entrada | `.../dto/Dtos.java:24`, `:41`, `:67` e `:106` | faixa da umidade, e-mail, tamanho da senha e minutos da rega; dado inválido volta 400 antes do banco (CT05, CT10) |
| Dados do produtor protegidos | `.../service/CanteiroService.java:30-37` | um produtor não vê o canteiro do outro; responde 404, sem revelar que existe (CT06, CT07) |
| Sensor autenticado por chave | `.../service/LeituraService.java:25-30` e `CanteiroService.java:16` | cada canteiro tem uma chave aleatória (`SecureRandom`); sem ela, a leitura é recusada (CT04); a exportação não leva a chave (CT15) |
| Segredos fora do código | `area3-mvp/api/src/main/resources/application.properties:17`, `docker-compose.yml:29`, `.gitignore:22` | o segredo do JWT e a senha do banco vêm de variáveis de ambiente; o compose não sobe sem elas; o CI gera valores novos a cada execução |
| Contêiner sem root e banco fechado | `area3-mvp/api/Dockerfile:22-24`, `docker-compose.yml:18` | a API roda como usuário comum; o banco não expõe porta para fora do compose |
| CORS com lista de origens | `.../security/SegurancaConfig.java:65-69` | só o app conhecido chama a API pelo navegador |

(`...` = `area3-mvp/api/src/main/java/br/com/fiap/gs2`.)

## Monitoramento

- `GET /actuator/health` responde `{"status":"UP"}` sem login (CT11). O compose e o CI usam essa rota para saber se a API subiu (CT19).
- `GET /actuator/info` e `/actuator/metrics` existem, mas pedem login.

## Evidência da execução

- Execução verde na `main` (18/11/2026, os 4 jobs e os 27 casos): https://github.com/Dsfr62/fiap-gs2-citizentech/actions/runs/44239186747
- Todas as execuções: https://github.com/Dsfr62/fiap-gs2-citizentech/actions/workflows/ci.yml
- O que ela mostrou: 15 de 15 casos da API; imagem montada; API saudável em 14 s sobre o PostgreSQL; login da técnica, 3 canteiros exportados e 401 sem token; 5 testes do pipeline; pipeline pelo README; e o fluxo ponta a ponta (3 leituras secas, alerta de 22 min pela regra básica, rega, e o alerta chegando à prata como "fiz").
- Prints para o PDF: o **Summary** da execução (tabela dos 15 casos da API, Docker, pipeline e fluxo) e a lista dos quatro jobs verdes.

## Ferramentas de IA usadas nesta área

O Claude Code (Anthropic, modelo Claude Opus 5.5) escreveu a primeira versão do Dockerfile, do compose, do CI, do plano de testes e deste README, e explicou cada parte. O CI verde e o plano de testes conferem o resultado. Detalhe na seção "Uso de IA generativa" do README da raiz.
