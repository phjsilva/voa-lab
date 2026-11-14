"""Parte matemática: filtros, interseção, união e diferença com Pandas."""

import re
import unicodedata
import pandas as pd

COLUNAS = ["companhia", "cidade", "turno"]


def intersecao(a, b):
    """A ∩ B: combinações presentes nos dois conjuntos."""
    return a.merge(b, on=COLUNAS, how="inner").drop_duplicates()


def uniao(a, b):
    """A ∪ B: combinações de A ou B, sem repetir."""
    return pd.concat([a, b], ignore_index=True).drop_duplicates()


def diferenca(a, b):
    """A − B: combinações de A que não estão em B."""
    comparacao = a.merge(b, on=COLUNAS, how="left", indicator=True)
    return comparacao.loc[comparacao["_merge"] == "left_only", COLUNAS].drop_duplicates()


def filtrar(base, coluna, valor):
    """Seleciona o subconjunto que atende a uma condição."""
    return base.loc[base[coluna] == valor]


def cardinalidade(conjunto):
    """|A|: quantidade de elementos do conjunto."""
    return len(conjunto)


OPERADORES = ("e", "ou", "exceto")


def aplicar_operacao(a, b, operador):
    """Escolhe a operação correspondente à palavra digitada."""
    if operador == "e":
        return intersecao(a, b)
    if operador == "ou":
        return uniao(a, b)
    if operador == "exceto":
        return diferenca(a, b)
    raise ValueError("Operador desconhecido.")


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto).lower())
    texto = "".join(letra for letra in texto if not unicodedata.combining(letra))
    return " ".join(texto.split())


def criar_termos(base):
    """Relaciona cada palavra de busca à coluna e ao valor do CSV."""
    termos = {}
    for coluna in COLUNAS:
        for valor in base[coluna].unique():
            if valor in {"e", "ou", "exceto", "voo", "voos"} or re.search(r"[^\w\s-]", valor):
                raise ValueError(f"Valor não suportado no CSV: {valor!r}.")
            if valor in termos and termos[valor] != (coluna, valor):
                raise ValueError(f"Termo ambíguo entre colunas: {valor!r}.")
            termos[valor] = (coluna, valor)
    apelidos = {
        "sao jose dos campos": ("cidade", "sjc"), "belem": ("cidade", "bel"),
        "matutino": ("turno", "manha"), "matutinos": ("turno", "manha"),
        "vespertino": ("turno", "tarde"), "vespertinos": ("turno", "tarde"),
        "noturno": ("turno", "noite"), "noturnos": ("turno", "noite"),
    }
    for apelido, (coluna, valor) in apelidos.items():
        if valor in base[coluna].values and apelido not in termos:
            termos[apelido] = (coluna, valor)
    return termos


def separar_termos(texto, termos):
    """Transforma 'voos latam e noite' em ['latam', 'e', 'noite']."""
    texto = re.sub(r"^voos?\b\s*", "", normalizar(texto))
    if not texto:
        raise ValueError("Digite uma companhia, cidade ou turno.")
    if len(texto) > 300:
        raise ValueError("Use uma busca com até 300 caracteres.")
    nomes = sorted(termos, key=len, reverse=True)
    tokens = []
    while texto:
        token = None
        operador = re.match(r"(?:exceto|ou|e)\b|[()]", texto)
        if operador:
            token = operador.group()
        else:
            for nome in nomes:
                if texto.startswith(nome) and (len(texto) == len(nome) or texto[len(nome)] in " ()"):
                    token = nome
                    break
        if token is None:
            raise ValueError(f"Termo não reconhecido: {texto.split()[0]!r}. Consulte a base abaixo.")
        # Dois termos juntos indicam interseção: 'latam sjc' = 'latam e sjc'.
        if tokens:
            anterior = tokens[-1]
            anterior_e_conjunto = anterior in termos or anterior == ")"
            atual_e_conjunto = token in termos or token == "("
            if anterior_e_conjunto and atual_e_conjunto:
                tokens.append("e")
        tokens.append(token)
        texto = texto[len(token):].lstrip()
    return tokens


def resolver(tokens, filtros, etapas):
    """Primeiro calcula interseções; depois, uniões e diferenças."""
    if not tokens or len(tokens) % 2 == 0:
        raise ValueError("A busca precisa alternar termos e operadores.")

    for posicao in range(0, len(tokens), 2):
        if tokens[posicao] not in filtros:
            raise ValueError("Confira os termos e parênteses da busca.")
    for posicao in range(1, len(tokens), 2):
        if tokens[posicao] not in OPERADORES:
            raise ValueError("Confira os operadores da busca.")

    # 1. Calcula os grupos ligados por 'e'.
    atual = filtros[tokens[0]]
    grupos = []
    operadores = []
    for posicao in range(1, len(tokens), 2):
        operador = tokens[posicao]
        proximo = filtros[tokens[posicao + 1]]
        if operador == "e":
            atual = intersecao(atual, proximo)
            etapas.append(f"Interseção: {len(atual)} combinação(ões).")
        else:
            grupos.append(atual)
            operadores.append(operador)
            atual = proximo
    grupos.append(atual)

    # 2. Resolve 'ou' e 'exceto' da esquerda para a direita.
    resultado = grupos[0]
    for posicao in range(len(operadores)):
        proximo = grupos[posicao + 1]
        resultado = aplicar_operacao(resultado, proximo, operadores[posicao])
        etapas.append(f"Operação '{operadores[posicao]}': {len(resultado)} combinação(ões).")
    return resultado


def resolver_parenteses(tokens, filtros, etapas):
    """Calcula um grupo interno e o substitui pelo conjunto resultante."""
    while "(" in tokens:
        # O último '(' indica o grupo mais interno ainda não resolvido.
        inicio = 0
        for posicao in range(len(tokens)):
            if tokens[posicao] == "(":
                inicio = posicao
        if ")" not in tokens[inicio + 1:]:
            raise ValueError("Falta fechar um parêntese.")
        fim = tokens.index(")", inicio + 1)
        nome_grupo = f"#grupo{inicio}"
        filtros[nome_grupo] = resolver(tokens[inicio + 1:fim], filtros, etapas)
        tokens[inicio:fim + 1] = [nome_grupo]
    return tokens


def buscar(base, texto):
    """Reconhece os termos, forma os conjuntos e calcula a resposta."""
    termos = criar_termos(base)
    tokens = separar_termos(texto, termos)
    filtros = {}
    etapas = []
    for token in tokens:
        if token in termos:
            coluna, valor = termos[token]
            filtros[token] = filtrar(base, coluna, valor)
            etapas.append(f"Filtro {coluna} = {valor}: {len(filtros[token])} combinação(ões).")
    tokens = resolver_parenteses(tokens, filtros, etapas)
    resultado = resolver(tokens, filtros, etapas)
    return resultado.sort_values(COLUNAS).reset_index(drop=True), etapas


def apresentar(tabela):
    """Agrupa os turnos apenas para exibir a resposta na página."""
    cidades = {"sjc": "São José dos Campos", "bel": "Belém"}
    linhas = []
    for (companhia, cidade), grupo in tabela.groupby(["companhia", "cidade"], sort=True):
        turnos = [turno for turno in ["manha", "tarde", "noite"] if turno in grupo["turno"].values]
        linhas.append({"companhia": companhia.upper(), "cidade": cidades.get(cidade, cidade.title()),
                       "turnos": ["manhã" if turno == "manha" else turno for turno in turnos]})
    return linhas
