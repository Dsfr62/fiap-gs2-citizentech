# O problema

> Global Solution 2026/2 · CitizenTech · tema "Campo · pequeno produtor". Este texto vai para o PDF da entrega.

## Quem é o cidadão

O agricultor familiar de hortaliças (alface, couve, tomate) tem de 1 a 5 hectares, irriga por aspersão ou gotejamento com bomba elétrica e não tem técnico por perto.

**Persona:** Seu Jorge, 54 anos, 2 ha de folhosas em Ibiúna (SP), celular Android e sinal fraco na roça. Ele rega todo dia no mesmo horário, 30 minutos, "porque sempre foi assim".

## A dor

Seu Jorge decide **quando e quanto irrigar** no hábito, sem saber a umidade do solo nem se vai chover. Em dia úmido, gasta água e energia à toa. No calor, a folhosa sofre (estresse hídrico), murcha e perde valor na venda.

Os números que sustentam o problema:

| Dado | Fonte |
|---|---|
| 77% dos estabelecimentos rurais do Brasil são de agricultura familiar (3.897.408) | IBGE, Censo Agropecuário 2017 |
| Só cerca de 20% dos estabelecimentos recebem orientação técnica | IBGE, Censo Agropecuário 2017 (Atlas do Espaço Rural) |
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

A medição é por simulação, com clima real (dados históricos do Open-Meteo para Ibiúna) e o mesmo canteiro nos dois casos:

| Métrica | Antes (rega por calendário: 30 min todo dia) | Depois (rega pela recomendação) |
|---|---|---|
| Água por m² em 60 dias | medida na Área 1 | medida na Área 1 |
| Dias com o solo abaixo do mínimo (planta sofrendo) | medida na Área 1 | medida na Área 1 |
| Acerto da decisão contra o balanço hídrico de referência (FAO-56) | não se aplica | medida na Área 1 |
| Tempo para decidir | depende do olho do produtor | 1 toque |

A hipótese, que ainda não é resultado, é gastar 25% menos água sem aumentar os dias de estresse. O número final é o da simulação, seja ele qual for.

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
