"""A mensagem ao produtor, em linguagem simples.

Segue as regras do prompt documentado em prompts/mensagem-ao-produtor.md, sem chamar um modelo de linguagem:
sem chave, sem custo e com a mesma saida para a mesma entrada (da para testar). As regras:
1. a primeira frase e a acao (regar quantos minutos, ou nao regar);
2. a segunda diz o porque, com no maximo dois numeros, arredondados;
3. se houver risco medio ou alto (doenca, geada, calor), uma frase com o que fazer;
4. sem palavra tecnica (nada de "evapotranspiracao", "modelo", "IA", "umidade relativa");
5. no WhatsApp, termina pedindo a resposta "1 fiz / 2 nao fiz";
6. no maximo 3 frases antes do pedido de resposta.
"""
from __future__ import annotations

from datetime import date

from base import NOME_DA_CULTURA

DIAS_DA_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
PEDIDO_DE_RESPOSTA = "Responda 1 se fez ou 2 se não fez."


def nome_do_dia(dia_iso: str, hoje: date) -> str:
    dia = date.fromisoformat(dia_iso)
    diferenca = (dia - hoje).days
    if diferenca <= 0:
        return "hoje"
    if diferenca == 1:
        return "amanhã"
    return f"na {DIAS_DA_SEMANA[dia.weekday()]}" if dia.weekday() < 5 else f"no {DIAS_DA_SEMANA[dia.weekday()]}"


def frase_do_risco(risco: dict, hoje: date) -> str:
    dia = nome_do_dia(risco["data"], hoje)
    if risco["tipo"] == "doenca":
        if risco["nivel"] == "alto":
            return (f"Tempo úmido {dia}, com risco alto de doença nas folhas (ferrugem e míldio): "
                    "olhe as folhas de baixo e regue no pé, sem molhar as folhas.")
        return f"Tempo úmido {dia}: fique de olho nas folhas de baixo."
    if risco["tipo"] == "geada":
        if risco["nivel"] == "alto":
            return f"Geada prevista {dia} de madrugada ({risco['valor']:.0f} °C): cubra as mudas no fim da tarde."
        return f"Madrugada fria {dia} ({risco['valor']:.0f} °C): se puder, cubra as mudas mais novas."
    if risco["nivel"] == "alto":
        return f"Calor forte {dia} ({risco['valor']:.0f} °C): regue no fim da tarde, nunca no sol do meio-dia."
    return f"Dia quente {dia} ({risco['valor']:.0f} °C): confira o solo no fim da tarde."


def montar(decisao: dict, riscos: list[dict], hoje: date) -> dict:
    cultura = NOME_DA_CULTURA.get(decisao["cultura"], "a sua cultura")
    agora, minimo = decisao["umidade_agora"], decisao["minimo"]
    prevista, chuva = decisao["umidade_prevista_24h"], decisao["chuva_prevista_mm"]

    if decisao["regar"]:
        acao = f"Regue {decisao['minutos']} minutos hoje, no fim da tarde (cerca de {decisao['litros']:.0f} litros)."
    elif chuva is not None and chuva >= 2 and agora < minimo + 5:
        acao = f"Não precisa regar hoje: a chuva prevista até amanhã ({chuva:.0f} mm) dá conta."
    else:
        acao = "Não precisa regar hoje."

    if prevista is None:
        porque = (f"O solo está com {agora:.0f}% de umidade, e o mínimo para {cultura} é {minimo}%. "
                  "Estou sem a previsão do tempo agora, então decidi só pelo sensor.")
    else:
        if prevista < agora - 1:
            rumo = f"deve cair para {prevista:.0f}%"
        elif prevista > agora + 1:
            rumo = f"deve subir para {prevista:.0f}%"
        else:
            rumo = f"deve continuar perto de {prevista:.0f}%"
        if decisao["regar"]:
            perto = "perto do" if prevista >= minimo else "abaixo do"
            porque = f"O solo está com {agora:.0f}% de umidade e {rumo} até amanhã, {perto} mínimo de {minimo}% para {cultura}."
        else:
            porque = f"O solo está com {agora:.0f}% de umidade e {rumo} até amanhã, acima do mínimo de {minimo}% para {cultura}."

    frases = [acao, porque]
    if riscos:
        frases.append(frase_do_risco(riscos[0], hoje))
    texto = " ".join(frases)
    return {"explicacao": texto, "whatsapp": f"{texto} {PEDIDO_DE_RESPOSTA}"}
