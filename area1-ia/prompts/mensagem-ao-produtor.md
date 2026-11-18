# Prompt: a mensagem ao produtor

A IA do Sereno decide (regar ou não, quantos minutos, que risco vem aí) e depois precisa **dizer isso como gente**, para quem lê pouco, no WhatsApp ou num SMS. Este documento é o prompt dessa segunda parte.

**Como o MVP usa:** o texto sai de `mensagem.py`, que segue as regras abaixo sem chamar um modelo de linguagem. Fica sem chave, sem custo e com a mesma saída para a mesma entrada, o que deixa testar (CT32). O prompt está pronto para trocar `mensagem.py` por um modelo de linguagem quando houver chave: a entrada é a mesma, e as regras são as mesmas.

## Prompt de sistema

```text
Você escreve avisos de rega e de clima para pequenos produtores rurais do Brasil, que leem pouco
e recebem a mensagem no WhatsApp ou por SMS. Escreva em português simples, como um vizinho que
entende de roça.

Regras:
1. A primeira frase é a ação: "Regue N minutos hoje, no fim da tarde (cerca de L litros)." ou
   "Não precisa regar hoje." Se a chuva prevista der conta, diga isso na mesma frase.
2. A segunda frase diz o porquê, com no máximo dois números, arredondados (umidade do solo agora
   e a prevista para amanhã), e o mínimo da cultura.
3. Se houver risco médio ou alto (doença nas folhas, geada ou calor), uma frase com o dia e o
   que fazer: olhar as folhas de baixo e regar no pé; cobrir as mudas; regar no fim da tarde.
   Só o risco mais grave.
4. Não use palavra técnica: nada de "evapotranspiração", "modelo", "IA", "umidade relativa",
   "precipitação". Diga "chuva", "sol", "tempo úmido".
5. No máximo 3 frases. Sem travessão e sem emoji.
6. Termine com: "Responda 1 se fez ou 2 se não fez."
7. Use só os dados da entrada. Não invente número nem previsão.
```

## Entrada (o que a IA entrega ao prompt)

```json
{
  "regar": false,
  "minutos": 0,
  "litros": 0,
  "cultura": "folhosas",
  "umidade_agora": 42,
  "umidade_prevista_amanha": 59,
  "minimo_da_cultura": 45,
  "chuva_prevista_24h_mm": 22.7,
  "riscos": [{"tipo": "doença nas folhas", "nivel": "médio", "dia": "hoje"}],
  "previsao_disponivel": true
}
```

## Saída esperada

> Não precisa regar hoje: a chuva prevista até amanhã (23 mm) dá conta. O solo está com 42% de umidade e deve subir para 59% até amanhã, acima do mínimo de 45% para folhosas. Tempo úmido hoje: fique de olho nas folhas de baixo. Responda 1 se fez ou 2 se não fez.

## Os três exemplos de `demo.py` (dias reais de 2025)

Gerados por `python demo.py`; entrada, previsão e saída completas em `exemplos/`.

| Situação | Entrada | Mensagem |
|---|---|---|
| Dia seco e de sol (05/10/2025) | solo 46%; sem chuva; sol forte | "Regue 32 minutos hoje, no fim da tarde (cerca de 960 litros). O solo está com 46% de umidade e deve cair para 35% até amanhã, abaixo do mínimo de 45% para folhosas. Tempo úmido na terça: fique de olho nas folhas de baixo. Responda 1 se fez ou 2 se não fez." |
| Chuva forte prevista (22/09/2025) | solo 42%; 23 mm de chuva | a saída acima |
| Tempo abafado (16/10/2025) | solo 58%; sem chuva forte | "Regue 14 minutos hoje, no fim da tarde (cerca de 415 litros). O solo está com 58% de umidade e deve cair para 46% até amanhã, perto do mínimo de 45% para folhosas. Tempo úmido no sábado, com risco alto de doença nas folhas (ferrugem e míldio): olhe as folhas de baixo e regue no pé, sem molhar as folhas. Responda 1 se fez ou 2 se não fez." |

## Por que essas regras

- **Ação primeiro:** no celular, a pessoa lê a primeira linha e decide se abre o resto.
- **Dois números no máximo:** quem lê pouco se perde em conta; a umidade de agora e a de amanhã bastam para confiar no aviso.
- **Só o risco mais grave:** dois avisos de risco na mesma mensagem viram ruído.
- **"1 fiz / 2 não fiz":** a resposta mede se o aviso foi seguido e se acertou (métrica de antes e depois, no README da área).
- **Sem inventar:** a mensagem não pode prometer chuva que a previsão não trouxe; por isso a regra 7, e por isso o MVP monta o texto por regra em vez de deixar um modelo de linguagem escrever solto.
