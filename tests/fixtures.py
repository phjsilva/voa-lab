"""Dados usados somente pelos testes, sem carregar uma base no site."""

from io import BytesIO
from backend.dados import importar_csvs

COMPANHIAS = b"companhia,cidade\nlatam,sjc\nlatam,bel\ngol,bel\nazul,campinas\n"
CIDADES = "cidade,turno\nsjc,tarde\nsjc,noite\nbel,manhã\ncampinas,noite\n".encode("utf-8")


def importar_dados_teste(pasta):
    importar_csvs(pasta, BytesIO(COMPANHIAS), BytesIO(CIDADES))
