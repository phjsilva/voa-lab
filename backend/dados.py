"""Lê, valida e salva os CSVs usados nas consultas."""

import csv
from io import StringIO
from pathlib import Path
import re
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from uuid import uuid4
import pandas as pd

from .consultas import COLUNAS, criar_termos, normalizar


def ler_csv(caminho, colunas, normalizar_dados=True):
    try:
        texto = caminho.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as erro:
        raise ValueError(f"{caminho.name}: salve o arquivo com codificação UTF-8.") from erro
    primeira_linha = texto.splitlines()[0] if texto.splitlines() else ""
    separador = ";" if ";" in primeira_linha and "," not in primeira_linha else ","
    validar_formato_csv(texto, separador, colunas, caminho.name)
    tabela = pd.read_csv(StringIO(texto), sep=separador, dtype=str, keep_default_na=False)
    if not normalizar_dados:
        return tabela  # Na página, preserva a escrita, a ordem e as linhas do arquivo.
    for coluna in colunas:
        tabela[coluna] = tabela[coluna].map(normalizar)
        if tabela[coluna].eq("").any():
            raise ValueError(f"{caminho.name}: há valores vazios em {coluna}.")
    return tabela.drop_duplicates()


def validar_formato_csv(texto, separador, colunas, nome_arquivo):
    try:
        linhas = [linha for linha in csv.reader(StringIO(texto), delimiter=separador, strict=True) if linha]
    except csv.Error as erro:
        raise ValueError(f"{nome_arquivo}: o conteúdo não é um CSV válido.") from erro
    if not linhas or linhas[0] != colunas:
        raise ValueError(f"{nome_arquivo}: cabeçalho esperado: {','.join(colunas)}.")
    if len(linhas) < 2:
        raise ValueError(f"{nome_arquivo}: inclua pelo menos uma linha de dados.")
    if any(len(linha) != len(colunas) for linha in linhas[1:]):
        raise ValueError(f"{nome_arquivo}: cada linha deve conter {len(colunas)} valores.")


def ler_base(pasta):
    pasta = Path(pasta)
    companhias = ler_csv(pasta / "companhias.csv", ["companhia", "cidade"])
    cidades = ler_csv(pasta / "cidades.csv", ["cidade", "turno"])
    if not cidades["turno"].isin(["manha", "tarde", "noite"]).all():
        raise ValueError("Os turnos do CSV devem ser manhã, tarde ou noite.")
    faltantes = companhias.loc[~companhias["cidade"].isin(cidades["cidade"]), "cidade"]
    if not faltantes.empty:
        raise ValueError("Cidades sem turno em cidades.csv: " + ", ".join(sorted(faltantes.unique())))
    # Junção: relaciona cada companhia aos turnos da mesma cidade.
    base = companhias.merge(cidades, on="cidade")[COLUNAS].drop_duplicates().reset_index(drop=True)
    criar_termos(base)  # Valida os nomes antes de permitir uma importação.
    return base


def pasta_ativa(pasta):
    pasta = Path(pasta)
    marcador = pasta / ".base_ativa"
    if not marcador.exists():
        return None
    identificador = marcador.read_text(encoding="ascii").strip()
    if not re.fullmatch(r"[a-f0-9]{32}", identificador):
        raise ValueError("Identificador de base importada inválido.")
    return pasta / ".importacoes" / identificador


def carregar_base(pasta):
    ativa = pasta_ativa(pasta)
    if ativa is None:
        return pd.DataFrame(columns=COLUNAS), False
    return ler_base(ativa), True


def carregar_csvs(pasta):
    """Retorna as linhas de cada CSV para exibir nas tabelas do site."""
    ativa = pasta_ativa(pasta)
    if ativa is None:
        return [], []
    companhias = ler_csv(ativa / "companhias.csv", ["companhia", "cidade"], normalizar_dados=False)
    cidades = ler_csv(ativa / "cidades.csv", ["cidade", "turno"], normalizar_dados=False)
    return companhias.to_dict(orient="records"), cidades.to_dict(orient="records")


def importar_csvs(pasta, companhias, cidades):
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".validacao-", dir=pasta) as temporaria:
        preparo = Path(temporaria)
        for stream, nome in [(companhias, "companhias.csv"), (cidades, "cidades.csv")]:
            with (preparo / nome).open("wb") as arquivo:
                copyfileobj(stream, arquivo)
        ler_base(preparo)  # Só salva a nova base quando os dois arquivos são válidos.
        identificador = uuid4().hex
        importacoes = pasta / ".importacoes"
        importacoes.mkdir(exist_ok=True)
        destino = importacoes / identificador
        preparo.rename(destino)
        try:
            marcador = pasta / f".base_ativa.{identificador}.tmp"
            marcador.write_text(identificador, encoding="ascii")
            marcador.replace(pasta / ".base_ativa")
        except OSError:
            for arquivo in destino.iterdir():
                arquivo.unlink()
            destino.rmdir()
            raise
