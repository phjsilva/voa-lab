"""Flask recebe os formulários e entrega os dados para o HTML."""

from pathlib import Path
from flask import Flask, abort, redirect, render_template, request, url_for
from .consultas import buscar, cardinalidade
from .dados import carregar_base, importar_csvs


def create_app(pasta_dados=None):
    raiz = Path(__file__).resolve().parent.parent
    pasta = Path(pasta_dados) if pasta_dados is not None else raiz / "data"
    app = Flask(__name__, template_folder=str(raiz / "frontend/templates"),
                static_folder=str(raiz / "frontend/static"))
    app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

    @app.route("/", methods=["GET", "POST"])
    def index():
        erro_importacao = None
        if request.method == "POST":
            if request.headers.get("Origin") != request.host_url.rstrip("/"):
                abort(403)
            try:
                companhias = request.files.get("companhias")
                cidades = request.files.get("cidades")
                if not companhias or not cidades:
                    raise ValueError("Selecione os dois arquivos: companhias e cidades.")
                importar_csvs(pasta, companhias.stream, cidades.stream)
                return redirect(url_for("index", aviso="importado", _anchor="dados-csv"))
            except (ValueError, OSError) as problema:
                erro_importacao = str(problema)

        try:
            companhias, cidades, base = carregar_base(pasta)
        except (ValueError, OSError) as problema:
            return render_template(
                "index.html", consulta=request.args.get("q", ""), erro=None,
                erro_importacao=erro_importacao, erro_dados=str(problema),
                resultados=[], quantidade=0, base=[], companhias_csv=[], cidades_csv=[],
            ), 400
        consulta = request.args.get("q", "")
        resultado = base.iloc[0:0]
        erro = None
        if "q" in request.args:
            try:
                if base.empty:
                    raise ValueError("Importe os dois CSVs antes de fazer uma busca.")
                resultado = buscar(base, consulta)
            except ValueError as problema:
                erro = str(problema)
        return render_template(
            "index.html", consulta=consulta, erro=erro, erro_importacao=erro_importacao,
            resultados=resultado.to_dict("records"), quantidade=cardinalidade(resultado),
            base=base.to_dict("records"), companhias_csv=companhias.to_dict("records"),
            cidades_csv=cidades.to_dict("records"),
        ), 400 if erro or erro_importacao else 200

    @app.get("/apresentacao")
    def apresentacao():
        return render_template("apresentacao.html")

    @app.get("/teoria")
    def teoria():
        return render_template("teoria.html")

    @app.errorhandler(413)
    def tamanho_excedido(erro):
        return "O envio ultrapassou 2 MB. Escolha arquivos menores.", 413

    return app
