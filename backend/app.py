"""Recebe os formulários do site e chama as funções do backend."""

from pathlib import Path
from inspect import getsourcelines, getsourcefile
from textwrap import dedent
import secrets
from flask import Flask, redirect, render_template, request, Response, session, url_for

from .consultas import apresentar, buscar
from . import consultas
from .dados import carregar_base, carregar_csvs, importar_csvs, ler_base, ler_csv


def create_app(pasta_dados=None):
    raiz = Path(__file__).resolve().parent.parent
    pasta = Path(pasta_dados) if pasta_dados else raiz / "data"
    app = Flask(__name__, template_folder=str(raiz / "frontend/templates"),
                static_folder=str(raiz / "frontend/static"), static_url_path="/static")
    app.config.update(SECRET_KEY=secrets.token_hex(32), MAX_CONTENT_LENGTH=2 * 1024 * 1024)

    def pagina(erro_importacao=None, status=200):
        session.setdefault("csrf", secrets.token_hex(32))
        base, importada = carregar_base(pasta)
        companhias_csv, cidades_csv = carregar_csvs(pasta)
        consulta = request.args.get("q", "")
        resultados = []
        etapas = []
        erro = None
        quantidade = 0
        if "q" in request.args:
            try:
                if base.empty:
                    raise ValueError("Importe os dois CSVs antes de fazer uma busca.")
                tabela, etapas = buscar(base, consulta)
                resultados = apresentar(tabela)
                quantidade = consultas.cardinalidade(tabela)
            except ValueError as problema:
                erro = str(problema)
                status = 400
        exemplos = []
        if not base.empty:
            primeira = base.iloc[0]
            empresa, cidade, turno = primeira["companhia"], primeira["cidade"], primeira["turno"]
            exemplos = [f"voos {empresa}", f"voos {empresa} e {turno}", f"voos {empresa} {cidade}",
                        f"voos {empresa} ou {turno}", f"voos {empresa} exceto {turno}"]
        avisos = {"importado": "CSV importados! Suas buscas já usam os novos dados."}
        return render_template("index.html", consulta=consulta, resultados=resultados, etapas=etapas,
                               erro=erro, pesquisou="q" in request.args, quantidade=quantidade,
                               base=apresentar(base), erro_importacao=erro_importacao, importada=importada,
                               companhias_csv=companhias_csv, cidades_csv=cidades_csv,
                               csrf=session["csrf"], exemplos=exemplos,
                               sucesso=avisos.get(request.args.get("aviso"))), status

    def formulario_valido():
        token = session.get("csrf", "")
        return bool(token) and secrets.compare_digest(token, request.form.get("csrf", ""))

    @app.get("/")
    def index():
        return pagina()

    @app.get("/apresentacao")
    def apresentacao():
        # Exibe cada função inteira, com os números reais das linhas do arquivo.
        def codigo(funcao, *destaques):
            linhas, inicio = getsourcelines(funcao)
            texto = dedent("".join(linhas)).splitlines()
            return {
                "arquivo": Path(getsourcefile(funcao)).relative_to(raiz).as_posix(),
                "funcao": funcao.__name__,
                "linhas": [{"numero": inicio + i, "texto": linha,
                            "destaque": any(marca in linha for marca in destaques)}
                           for i, linha in enumerate(texto)],
            }

        codigos = {
            "csv": codigo(ler_csv, "pd.read_csv(", "return tabela.drop_duplicates"),
            "juncao": codigo(ler_base, "ler_csv(", "merge("),
            "filtros": codigo(consultas.filtrar, "return base.loc"),
            "intersecao": codigo(consultas.intersecao, "return a.merge"),
            "uniao": codigo(consultas.uniao, "return pd.concat"),
            "diferenca": codigo(consultas.diferenca, "comparacao =", "left_only"),
            "prioridade": codigo(consultas.aplicar_operacao, 'operador ==', "return intersecao", "return uniao", "return diferenca"),
            "cardinalidade": codigo(consultas.cardinalidade, "return len"),
        }
        base, importada = carregar_base(pasta)
        exemplos = {}
        if importada:
            empresa, turno = base.iloc[0]["companhia"], base.iloc[0]["turno"]
            exemplos = {
                "csv": url_for("index", _anchor="dados-csv"),
                "juncao": url_for("index", _anchor="dados-csv"),
                "filtros": url_for("index", q=f"voos {empresa}"),
                "intersecao": url_for("index", q=f"voos {empresa} e {turno}"),
                "uniao": url_for("index", q=f"voos {empresa} ou {turno}"),
                "diferenca": url_for("index", q=f"voos {empresa} exceto {turno}"),
                "prioridade": url_for("index", q=f"voos ({empresa}) e ({turno})"),
                "cardinalidade": url_for("index", q=f"voos {empresa}"),
            }
        return render_template("apresentacao.html", codigos=codigos, exemplos=exemplos)

    @app.post("/importar")
    def importar():
        if not formulario_valido():
            return pagina("Atualize a página e tente enviar os arquivos novamente.", 400)
        companhias, cidades = request.files.get("companhias"), request.files.get("cidades")
        if not companhias or not cidades or not companhias.filename or not cidades.filename:
            return pagina("Selecione os dois arquivos: companhias e cidades.", 400)
        if not companhias.filename.lower().endswith(".csv") or not cidades.filename.lower().endswith(".csv"):
            return pagina("Os dois arquivos devem ter a extensão .csv.", 400)
        try:
            importar_csvs(pasta, companhias.stream, cidades.stream)
        except ValueError as erro:
            return pagina(str(erro), 400)
        except OSError:
            app.logger.exception("Não foi possível salvar os CSVs")
            return pagina("Não foi possível salvar os arquivos. Tente novamente.", 500)
        return redirect(url_for("index", aviso="importado", _anchor="dados-csv"), code=303)

    @app.get("/modelos/<tipo>")
    def modelo(tipo):
        cabecalhos = {"companhias": "companhia,cidade\n", "cidades": "cidade,turno\n"}
        if tipo not in cabecalhos:
            return "Modelo não encontrado.", 404
        return Response(cabecalhos[tipo], mimetype="text/csv",
                        headers={"Content-Disposition": f"attachment; filename={tipo}.csv"})

    @app.errorhandler(413)
    def tamanho_excedido(_erro):
        return pagina("O envio ultrapassou 2 MB. Escolha arquivos menores.", 413)

    return app
