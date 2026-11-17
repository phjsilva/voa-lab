"""Filtros e operações de conjuntos com Pandas."""

import unicodedata
import pandas as pd

COLUNAS = ["companhia", "cidade", "turno"]
OPERADORES = ["e", "ou", "exceto"]


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto).lower())
    resultado = ""
    for letra in texto:
        if not unicodedata.combining(letra):
            resultado += letra
    return " ".join(resultado.split())


def filtrar(base, coluna, valor):
    return base[base[coluna] == valor]


def intersecao(a, b):
    resultado = a.merge(b, on=COLUNAS)
    return resultado.drop_duplicates()


def uniao(a, b):
    resultado = pd.concat([a, b])
    return resultado.drop_duplicates()


def diferenca(a, b):
    comparacao = a.merge(b, on=COLUNAS, how="left", indicator=True)
    resultado = comparacao[comparacao["_merge"] == "left_only"]
    return resultado[COLUNAS].drop_duplicates()


def aplicar_operacao(a, b, operador):
    if operador == "e":
        return intersecao(a, b)
    if operador == "ou":
        return uniao(a, b)
    if operador == "exceto":
        return diferenca(a, b)
    raise ValueError("Use e, ou ou exceto.")


def cardinalidade(conjunto):
    return len(conjunto)


def criar_termos(base):
    termos = {}
    for coluna in COLUNAS:
        for valor in base[coluna].unique():
            if valor in OPERADORES + ["voo", "voos"] or "(" in valor or ")" in valor:
                raise ValueError(f"Nome reservado no CSV: {valor}.")
            if valor in termos and termos[valor][0] != coluna:
                raise ValueError(f"Nome repetido em colunas diferentes: {valor}.")
            termos[valor] = (coluna, valor)
    apelidos = {
        "sao jose dos campos": "sjc", "belem": "bel",
        "matutino": "manha", "matutinos": "manha",
        "vespertino": "tarde", "vespertinos": "tarde",
        "noturno": "noite", "noturnos": "noite",
    }
    for apelido, valor in apelidos.items():
        if valor in termos and apelido not in termos:
            termos[apelido] = termos[valor]
    return termos


def separar_termos(texto, termos):
    palavras = normalizar(texto).split()
    if palavras and palavras[0] in ["voo", "voos"]:
        palavras.pop(0)
    tokens = []
    while palavras:
        if palavras[0] in OPERADORES:
            tokens.append(palavras.pop(0))
            continue
        # Procura o nome completo, incluindo cidades com mais de uma palavra.
        encontrou = False
        for tamanho in range(len(palavras), 0, -1):
            nome = " ".join(palavras[:tamanho])
            if nome in termos:
                tokens.append(nome)
                palavras = palavras[tamanho:]
                encontrou = True
                break
        if not encontrou:
            raise ValueError("Termo não reconhecido. Consulte os dados importados.")
    if len(tokens) == 2 and tokens[0] in termos and tokens[1] in termos:
        tokens.insert(1, "e")
    if len(tokens) == 1 and tokens[0] in termos:
        return tokens
    if len(tokens) == 3 and tokens[0] in termos and tokens[1] in OPERADORES and tokens[2] in termos:
        return tokens
    raise ValueError("Use um filtro ou dois filtros ligados por e, ou ou exceto.")


def buscar(base, texto):
    termos = criar_termos(base)
    tokens = separar_termos(texto, termos)
    coluna, valor = termos[tokens[0]]
    resultado = filtrar(base, coluna, valor)
    if len(tokens) == 3:
        coluna, valor = termos[tokens[2]]
        segundo = filtrar(base, coluna, valor)
        resultado = aplicar_operacao(resultado, segundo, tokens[1])
    return resultado.sort_values(COLUNAS)
