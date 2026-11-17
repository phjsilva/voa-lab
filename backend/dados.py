"""Leitura dos CSVs, junção pela cidade e salvamento dos dados importados."""

from pathlib import Path
import csv
import pandas as pd
from .consultas import COLUNAS, criar_termos, normalizar


def ler_csv(arquivo, colunas):
    try:
        tabela = pd.read_csv(arquivo, sep=None, engine="python", dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except (ValueError, UnicodeError, csv.Error) as erro:
        raise ValueError("Envie um CSV válido, em UTF-8, com vírgula ou ponto e vírgula.") from erro
    if list(tabela.columns) != colunas:
        raise ValueError("Cabeçalho esperado: " + ",".join(colunas) + ".")
    if tabela.empty or not isinstance(tabela.index, pd.RangeIndex):
        raise ValueError("Inclua linhas de dados com duas colunas.")
    for coluna in colunas:
        if tabela[coluna].isna().any() or tabela[coluna].map(normalizar).eq("").any():
            raise ValueError("Preencha todos os valores do CSV.")
    return tabela


def ler_base(companhias, cidades):
    companhias = companhias.copy()
    cidades = cidades.copy()
    for tabela in [companhias, cidades]:
        for coluna in tabela.columns:
            tabela[coluna] = tabela[coluna].map(normalizar)
    for turno in cidades["turno"]:
        if turno not in ["manha", "tarde", "noite"]:
            raise ValueError("Use os turnos manhã, tarde ou noite.")
    for cidade in companhias["cidade"]:
        if cidade not in cidades["cidade"].values:
            raise ValueError(f"Cidade sem turno em cidades.csv: {cidade}.")
    base = companhias.merge(cidades, on="cidade")
    base = base[COLUNAS].drop_duplicates()
    criar_termos(base)
    return base


def carregar_base(pasta):
    pasta = Path(pasta)
    companhias = pd.DataFrame(columns=["companhia", "cidade"])
    cidades = pd.DataFrame(columns=["cidade", "turno"])
    if (pasta / "companhias.csv").exists() and (pasta / "cidades.csv").exists():
        companhias = ler_csv(pasta / "companhias.csv", ["companhia", "cidade"])
        cidades = ler_csv(pasta / "cidades.csv", ["cidade", "turno"])
    return companhias, cidades, ler_base(companhias, cidades)


def importar_csvs(pasta, companhias, cidades):
    companhias = ler_csv(companhias, ["companhia", "cidade"])
    cidades = ler_csv(cidades, ["cidade", "turno"])
    ler_base(companhias, cidades)  # Confere os dois CSVs antes de substituir os dados.
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    companhias.to_csv(pasta / "companhias.csv", index=False)
    cidades.to_csv(pasta / "cidades.csv", index=False)
