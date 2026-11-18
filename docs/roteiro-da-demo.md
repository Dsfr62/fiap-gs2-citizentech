# Roteiro do vídeo pitch do Sereno

Até 3 minutos, mostrando o sistema funcionando (a FIAP não aceita só slide nem leitura de texto). O roteiro segue os tempos que a FIAP sugere. Os números são os medidos no projeto, com a fonte ao lado.

## Fala e tela, por tempo

| Tempo | O que aparece na tela | O que falar (resumo) |
|---|---|---|
| 0:00 a 0:30, o problema | foto ou vídeo de uma horta; depois, o app aberto | O agricultor familiar é 77% dos estabelecimentos rurais do Brasil, e só 1 em cada 5 recebe orientação técnica, um índice parado há mais de 20 anos (IBGE). Ele rega no olho: 30 minutos todo dia, chova ou faça sol. E a irrigação já é metade da água retirada no país (ANA). |
| 0:30 a 0:50, a solução | o diagrama `docs/arquitetura.svg` por 3 segundos e o app | O Sereno junta o sensor no canteiro, a previsão do tempo e uma IA, e manda um aviso simples: regar ou não, quantos minutos, e se vem doença, geada ou calor. O produtor responde "1 fiz" ou "2 não fiz", e a Emater acompanha tudo num painel por comunidade. |
| 0:50 a 1:20, o sensor | o circuito no TinkerCad rodando, com o monitor serial; depois o simulador mandando leituras | Dois sensores no canteiro: umidade do solo e temperatura, mais luz. O LED acende quando o solo seca, mesmo sem internet. |
| 1:20 a 1:50, a IA | no app: Meus canteiros, a alface com "solo seco", a tela Hoje ao vivo, o toque em "Pedir recomendação agora" e a mensagem da IA; depois "Reguei" | A IA olha o solo agora e a chuva das próximas 24 horas. Se vai chover, ela segura a rega; se vai secar, manda regar antes. Tudo em português simples. |
| 1:50 a 2:10, o painel | o Power BI: taxa de "fiz" por comunidade, água economizada, alertas, risco; mexer num filtro | O técnico vê, por comunidade, quem segue os avisos, quanta água foi economizada e onde tem risco de doença. |
| 2:10 a 2:40, impacto e ODS | o painel ou a tela de antes e depois (`area1-ia/resultados/antes_depois.md`) | Em 60 dias com o clima real de Ibiúna, a IA gastou 61% menos água que a rega por calendário e acertou 98% dos alertas. Quem seguiu o aviso acertou em 93% das vezes; quem não seguiu, em 22%. ODS 2 (agricultura sustentável), 13 (clima) e 10 (desigualdades). |
| 2:40 a 3:00, fecho | o app com o nome Sereno | O clima da roça em aviso simples, para quem nunca teve técnico por perto. |

## Fontes dos números

- 77% dos estabelecimentos são agricultura familiar: IBGE, Censo Agropecuário 2017.
- Orientação técnica: 19,5% (1995/96), 22,1% (2006) e 20,2% (2017): IBGE, Atlas do Espaço Rural Brasileiro.
- Irrigação = 50,5% da água retirada: ANA, Conjuntura dos Recursos Hídricos 2023.
- 61% menos água, 98% de acerto, 93% contra 22%: `area1-ia/resultados/antes_depois.md` (simulação com clima real de 2025; planta e solo simulados).

## Como pôr o sistema de pé para gravar

**Com Docker** (qualquer computador com Docker Desktop):

```bash
cp .env.exemplo .env                 # e troque os dois valores
docker compose up -d --build         # banco, IA e API
cd area3-mvp/app && npm install && npx expo start --web     # o app em http://localhost:8081
python3 area3-mvp/iot/simulador.py --cenario seco            # noutro terminal: o sensor
```

**Sem Docker:** siga os READMEs, na ordem: a IA (`area1-ia`, `python servico.py`), a API (`area3-mvp/api`, `./mvnw spring-boot:run`), o simulador e o app.

Entrar como `jorge@exemplo.com`, senha `horta2026`. O painel do técnico é o Power BI da Área 2 (CSVs em `area2-dados/powerbi/`).

## Antes de enviar o link

- Duração de até 3 minutos.
- Link público (YouTube não listado, Google Drive ou Vimeo), testado numa aba anônima.
- O link vai no `.txt` da entrega e no README da raiz.
