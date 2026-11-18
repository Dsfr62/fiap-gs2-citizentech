# O problema

> Sereno, Global Solution 2026/2 (CitizenTech), tema "Campo: pequeno produtor". Este texto vai para o PDF da entrega.

## O Sereno, em uma frase

O clima da roça em aviso simples: sensores no canteiro (e, no futuro, uma estação comunitária dividida entre vizinhos), o clima e uma IA viram avisos curtos para o produtor ("não precisa irrigar até quinta", "risco alto de ferrugem: olhe as folhas de baixo", "geada nesta madrugada: cubra as mudas"). Ele responde "1 fiz / 2 não fiz", e a Emater ou a cooperativa acompanha num painel por comunidade. Nome e recorte escolhidos pelo grupo em 18/11/2026.

| Parte | Estado hoje |
|---|---|
| Aviso de irrigação (regar ou não, quantos minutos e o porquê) | **pronto**: a IA da Área 1 decide com o sensor e a previsão; sem ela, a API usa a regra básica |
| Resposta "fiz / não fiz" | hoje é o "Reguei" do app; o pipeline transforma em fiz, não fiz ou aguardando |
| Painel por comunidade (taxa de "fiz", água economizada, alertas, risco) | dados prontos na Área 2; o painel em Power BI está em montagem |
| Risco de doença, geada e calor | **pronto**: regras da Área 1 sobre a previsão de 3 dias, com os mesmos limites do painel da Área 2 |
| Aviso por WhatsApp, SMS e áudio | a IA já devolve o texto pronto para o WhatsApp (`mensagemWhatsapp`); no MVP, o aviso aparece no app |

## Quem é o cidadão

O agricultor familiar de hortaliças (alface, couve, tomate) tem de 1 a 5 hectares, irriga por aspersão ou gotejamento com bomba elétrica e não tem técnico por perto.

**Persona:** Seu Jorge, 54 anos, 2 ha de folhosas em Ibiúna (SP), celular Android e sinal fraco na roça. Ele rega todo dia no mesmo horário, 30 minutos, "porque sempre foi assim".

## A dor

Seu Jorge decide **quando e quanto irrigar** no hábito, sem saber a umidade do solo nem se vai chover. Em dia úmido, gasta água e energia à toa. No calor, a folhosa sofre (estresse hídrico), murcha e perde valor na venda.

Os números que sustentam o problema:

| Dado | Fonte |
|---|---|
| 77% dos estabelecimentos rurais do Brasil são de agricultura familiar (3.897.408) | IBGE, Censo Agropecuário 2017 |
| Só cerca de 20% dos estabelecimentos recebem orientação técnica, um índice parado há mais de 20 anos: 19,5% no Censo 1995/96, 22,1% em 2006 e 20,2% em 2017 | IBGE, Atlas do Espaço Rural Brasileiro (texto sobre assistência técnica, com os Censos Agropecuários) |
| A irrigação responde por 50,5% da água retirada no Brasil | ANA, Conjuntura dos Recursos Hídricos 2023 |

Quem mais precisaria de orientação para usar água é quem menos recebe.

## A solução

Dois sensores no canteiro (umidade do solo e temperatura do ar, mais um sensor de luz) e a previsão do tempo alimentam uma IA. Uma vez por dia, ela responde **"regar hoje? quantos minutos?"** e explica o porquê em linguagem simples. O produtor rega e toca em "reguei". O técnico da cooperativa vê num painel quem gasta água demais e quem tem planta em risco.

## Ecossistema

| Quem | O que ganha |
|---|---|
| Produtor | Decisão diária pronta, menos água e luz, menos perda de folhosa |
| Técnico da cooperativa ou da assistência técnica (ATER) | Painel com todos os produtores: onde visitar primeiro |
| Cooperativa ou associação | Indicador de uso de água para projetos, crédito e outorga |
| Prefeitura (Secretaria de Agricultura) | Dado para programas de estiagem e assistência técnica |

## ODS

- **ODS 2, Fome zero e agricultura sustentável.** A meta 2.3 trata da produtividade e da renda do pequeno produtor; a 2.4, de sistemas de produção sustentáveis e adaptados ao clima.
- **ODS 13, Ação contra a mudança do clima.** A meta 13.1 trata da resiliência a eventos climáticos: decidir a rega pela previsão ajuda a atravessar a estiagem.
- **ODS 10, Redução das desigualdades.** Leva orientação técnica de irrigação a quem está nos 80% que não recebem.

## Como medimos o antes e o depois

A medição é por simulação, com clima real: os 7 canteiros do histórico da Área 2 (670 m² no total), por 60 dias com o clima de Ibiúna de 01/09 a 30/10/2025 (Open-Meteo), período que o modelo da IA nunca viu. Mesmo solo, mesmo sensor e mesmo clima nos três casos. Detalhe e código em `area1-ia/` (`python avaliar.py`).

| Métrica | Antes: calendário (30 min todo dia) | Regra básica (só o sensor) | Depois: IA (sensor e previsão) |
|---|---:|---:|---:|
| Água em 60 dias | 279.000 L (416 L/m²) | 109.915 L | **108.065 L (161 L/m²), 61% menos** |
| Água perdida (escorreu com o solo cheio ou com chuva logo depois) | 146.535 L | 9.379 L | **3.413 L** |
| Horas com o solo abaixo do mínimo (planta sofrendo) | 0 (o calendário encharca) | 4.967 (49% das horas) | **581 (5,8% das horas)** |
| Acerto do alerta (na manhã seguinte, solo no ponto e rega sem perda) | não se aplica | 49,9% | **98,3%** |
| Tempo para decidir | depende do olho do produtor | 1 toque | 1 toque |

A hipótese era gastar 25% menos água sem deixar a planta sofrer. O resultado: **61% menos água** que o calendário. A planta passa 5,8% das horas um pouco abaixo do mínimo, contra 0% no calendário, que nunca deixa secar porque encharca e perde metade da água. Contra a regra básica, que também economiza, a IA corta as horas de sofrimento em 88%. Pelas respostas "1 fiz / 2 não fiz": quando o produtor seguiu o aviso, ele acertou em 92,7% das vezes; quando não seguiu, em 22,0%.

Limites: a planta e o solo são simulados (o clima é real), e a avaliação usa como "previsão" o clima que de fato aconteceu; previsão de verdade erra, então o ganho real tende a ser um pouco menor.

## Fora do cenário ideal

- **Sem internet:** o LED do sensor acende quando o solo está seco, e o produtor vê o aviso no próprio canteiro. O simulador e o nó guardam as leituras e reenviam quando a conexão volta.
- **Sem previsão do tempo:** a IA decide só pelos sensores e diz isso na explicação.
- **IA fora do ar:** a API usa uma regra básica, e o produtor nunca fica sem resposta.

## Fontes

- IBGE. Censo Agropecuário 2017, resultados definitivos, agricultura familiar. https://ftp.ibge.gov.br/Censo_Agropecuario/Censo_Agropecuario_2017/Resultados_Definitivos/agricultura_familiar/
- IBGE. Atlas do Espaço Rural Brasileiro, assistência técnica. https://www.ibge.gov.br/apps/atlasrural/pdfs/05_00_Texto.pdf
- ANA. Conjuntura dos Recursos Hídricos no Brasil 2023 (notícia oficial, 02/2024). https://agenciagov.ebc.com.br/noticias/202402/relatorio-conjuntura-dos-recursos-hidricos-no-brasil-atualiza-informacoes-sobre-aguas-do-pais
- FAO. Crop evapotranspiration, Irrigation and Drainage Paper 56 (Allen et al., 1998). https://www.fao.org/4/x0490e/x0490e00.htm
- Open-Meteo. API de clima histórico e previsão, sem chave. https://open-meteo.com/
- ONU. Objetivos de Desenvolvimento Sustentável. https://brasil.un.org/pt-br/sdgs
