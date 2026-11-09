# Área 3 · MVP, IoT e experiência digital

Três partes: a **API** (Java 17, Spring Boot), o **app** (Expo, roda no navegador e no celular) e o **IoT** (Arduino no TinkerCad e o simulador dos sensores em Python).

| Item da nota | Onde está |
|---|---|
| 4+ telas funcionais | `app/`: Entrar, Meus canteiros, Hoje, Histórico e Novo canteiro (5 telas) |
| 2+ sensores | `iot/sensor_canteiro.ino` (umidade do solo, temperatura TMP36 e luz) e `iot/simulador.py` (mock) |
| Fluxo completo | "Fluxo completo, passo a passo", abaixo |
| Arquitetura | `../docs/arquitetura.svg` |

## O que precisa estar instalado

| Ferramenta | Versão | Para quê |
|---|---|---|
| JDK | 17 ou mais novo | API |
| Node.js | 20 LTS ou mais novo | app |
| Python | 3.9 ou mais novo | simulador (só biblioteca padrão, nada para instalar) |

O Maven não precisa estar instalado: o projeto traz o Maven Wrapper (`mvnw`). O banco é o H2 em memória, que sobe junto com a API.

## Como rodar (3 terminais)

**Terminal 1, a API:**

```bash
cd area3-mvp/api
./mvnw spring-boot:run          # no Windows: mvnw.cmd spring-boot:run
```

Ela está pronta quando aparece `Started Gs2Application`. Para conferir:
- saúde: http://localhost:8080/actuator/health responde `{"status":"UP"}`;
- documentação: http://localhost:8080/swagger-ui.html.

**Terminal 2, os sensores (simulador):**

```bash
cd area3-mvp/iot
python3 simulador.py --cenario seco      # no Windows: python simulador.py --cenario seco
```

A cada 5 segundos ele manda uma leitura do canteiro de alface para a API. Os cenários são `normal`, `seco` e `chuva`. Para outro canteiro, use `--chave demo-sensor-tomate-0002`.

**Terminal 3, o app:**

```bash
cd area3-mvp/app
npm install
npx expo start --web
```

O app abre em http://localhost:8081. No celular, instale o Expo Go, ponha o celular na mesma rede e rode `EXPO_PUBLIC_API_URL=http://<IP-do-computador>:8080 npx expo start`. Depois é só ler o QR code.

### Usuários de demonstração

Senha de todos: `horta2026` (dados de exemplo, que nascem com a API).

| E-mail | Papel | O que vê |
|---|---|---|
| jorge@exemplo.com | produtor | os 2 canteiros dele (alface e tomate) |
| ana@exemplo.com | técnica da cooperativa | todos os canteiros |
| maria@exemplo.com | produtora | só o canteiro dela (prova de que um produtor não vê o do outro) |

## Fluxo completo, passo a passo

1. **Entrar** como `jorge@exemplo.com`.
2. Em **Meus canteiros**, o de alface aparece com "solo seco": a umidade está abaixo do mínimo de 45% para folhosas.
3. Toque no canteiro. A tela **Hoje** mostra o sensor ao vivo (umidade, temperatura, sol) e se atualiza sozinha a cada 5 s, com as leituras que o simulador manda.
4. **Pedir recomendação agora**: a API manda a última leitura para a IA (Área 1). Se a IA estiver desligada, usa a regra básica, e a tela diz qual das duas respondeu.
5. A recomendação aparece em linguagem simples, por exemplo "Regar 22 min, cerca de 648 litros", com o porquê.
6. **Reguei 22 min**: a rega fica registrada, em minutos e litros.
7. **Histórico**: o gráfico da umidade (barra laranja = abaixo do mínimo), a água gasta em 7 dias e quantas regas seguiram a recomendação.
8. (Opcional) **Novo canteiro**: cadastra um canteiro e mostra a chave que vai no sensor dele.

## IoT: o circuito no TinkerCad

Arquivo: `iot/sensor_canteiro.ino` (Arduino Uno). Ligações:

| Componente | Ligação |
|---|---|
| Sensor de umidade do solo | VCC no pino 7, GND no GND, SIG no A0 |
| TMP36 (temperatura) | pino esquerdo no 5V, meio no A1, direito no GND |
| Fotorresistor (luz) | uma perna no 5V; a outra no A2 e, por um resistor de 10 kΩ, no GND |
| LED vermelho (solo seco) | ânodo no pino 13 por um resistor de 220 Ω, cátodo no GND |

No TinkerCad, cole o código em "Código > Texto", inicie a simulação e abra o "Monitor serial". A cada 2 s sai uma linha JSON, no mesmo formato que a API recebe:

```json
{"umidadeSolo":41.2,"temperaturaAr":24.8,"luminosidade":63.0}
```

O TinkerCad não acessa a internet, por isso o simulador (`simulador.py`) faz a ponte até a API com o mesmo formato. O enunciado aceita "sensores reais ou mock". O LED acende no próprio canteiro quando o solo está abaixo do mínimo, mesmo sem conexão.

## Rotas principais da API

| Método | Rota | Quem usa |
|---|---|---|
| POST | `/api/auth/login` | app (devolve o token JWT) |
| POST | `/api/auth/cadastro` | app (cria sempre um produtor) |
| GET | `/api/canteiros` | app (o produtor vê os dele; o técnico, todos) |
| POST | `/api/canteiros` | app (devolve a chave do sensor) |
| GET | `/api/canteiros/{id}/leituras?limite=24` | app |
| POST | `/api/leituras` | sensor, com o cabeçalho `X-Chave-Dispositivo` |
| POST | `/api/canteiros/{id}/recomendacoes` | app ("pedir recomendação") |
| GET | `/api/canteiros/{id}/recomendacoes/ultima` | app |
| GET/POST | `/api/canteiros/{id}/regas` | app ("reguei" e histórico) |
| GET | `/api/dados/leituras?desde=...` | pipeline da Área 2 (só técnico) |
| GET | `/actuator/health` | monitoramento |

## Testes da API

```bash
cd area3-mvp/api
./mvnw test
```

São 14 casos (CT01 a CT14): login, rota sem token, chave de sensor inválida, validação, um produtor sem acesso ao canteiro do outro, fluxo completo, exportação só para o técnico, saúde e a regra básica. O plano completo fica na Área 4.

## Como as partes se ligam

Sensor (ou simulador) → `POST /api/leituras` → banco → app mostra ao vivo → app pede a recomendação → API chama a IA (`POST {IA_URL}/recomendar`, padrão `http://localhost:8001`) → resposta salva → produtor rega e registra → o pipeline da Área 2 lê `/api/dados/leituras`.
