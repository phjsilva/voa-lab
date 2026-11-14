from pathlib import Path
from io import BytesIO
from tempfile import TemporaryDirectory
import unittest

from backend.app import create_app
from backend.consultas import COLUNAS, apresentar, buscar, intersecao, uniao, diferenca
from backend.dados import carregar_base, ler_base
from tests.fixtures import COMPANHIAS, CIDADES, criar_csvs, importar_dados_teste


def tuplas(tabela):
    return set(tabela[COLUNAS].itertuples(index=False, name=None))


class TestConsultas(unittest.TestCase):
    def setUp(self):
        temporaria = TemporaryDirectory()
        self.addCleanup(temporaria.cleanup)
        self.pasta = Path(temporaria.name)
        criar_csvs(self.pasta)
        self.base = ler_base(self.pasta)

    def resultado(self, consulta):
        return tuplas(buscar(self.base, consulta)[0])

    def test_join(self):
        self.assertEqual(tuplas(self.base), {
            ("latam", "sjc", "tarde"), ("latam", "sjc", "noite"),
            ("latam", "bel", "manha"), ("gol", "bel", "manha"),
            ("azul", "campinas", "noite"),
        })

    def test_exemplo_latam(self):
        self.assertEqual(self.resultado("voos latam"), {
            ("latam", "sjc", "tarde"), ("latam", "sjc", "noite"),
            ("latam", "bel", "manha"),
        })

    def test_exemplo_intersecao(self):
        self.assertEqual(self.resultado("voos latam e manhã"), {("latam", "bel", "manha")})

    def test_exemplo_cidade_implicita(self):
        self.assertEqual(self.resultado("voos latam sjc"), {
            ("latam", "sjc", "tarde"), ("latam", "sjc", "noite"),
        })

    def test_exemplo_uniao_sem_duplicatas(self):
        self.assertEqual(self.resultado("voos latam ou noite"), {
            ("latam", "sjc", "tarde"), ("latam", "sjc", "noite"),
            ("latam", "bel", "manha"), ("azul", "campinas", "noite"),
        })

    def test_exemplo_exceto(self):
        self.assertEqual(self.resultado("voos gol exceto noturnos"), {("gol", "bel", "manha")})

    def test_exceto_remove_apenas_tupla_correspondente(self):
        self.assertEqual(self.resultado("latam exceto noite"), {
            ("latam", "sjc", "tarde"), ("latam", "bel", "manha"),
        })

    def test_maiusculas_acentos_e_apelidos(self):
        self.assertEqual(self.resultado("VOOS LATAM BELÉM"), {("latam", "bel", "manha")})
        self.assertEqual(self.resultado("latam São José dos Campos"), self.resultado("latam sjc"))
        self.assertEqual(self.resultado("voo LATAM E MANHA"), self.resultado("latam manhã"))

    def test_prioridade_do_e(self):
        self.assertEqual(self.resultado("latam ou azul e noite"), self.resultado("latam ou azul"))
        self.assertNotEqual(self.resultado("latam ou azul e noite"), self.resultado("(latam ou azul) e noite"))

    def test_parenteses(self):
        self.assertEqual(self.resultado("(latam ou azul) e noite"), {
            ("latam", "sjc", "noite"), ("azul", "campinas", "noite"),
        })

    def test_diferenca_associada_a_esquerda(self):
        self.assertEqual(self.resultado("latam exceto noite exceto tarde"), {("latam", "bel", "manha")})

    def test_parenteses_dentro_de_parenteses(self):
        self.assertEqual(self.resultado("((latam ou azul) e noite) exceto campinas"), {
            ("latam", "sjc", "noite"),
        })

    def test_diferenca_com_grupo_e_uniao(self):
        self.assertEqual(self.resultado("(latam exceto (noite ou tarde)) ou gol"), {
            ("latam", "bel", "manha"), ("gol", "bel", "manha"),
        })

    def test_resultado_vazio(self):
        self.assertEqual(self.resultado("gol e noite"), set())

    def test_identidades_de_conjuntos(self):
        a = self.base
        self.assertEqual(tuplas(intersecao(a, a)), tuplas(a))
        self.assertEqual(tuplas(uniao(a, a)), tuplas(a))
        self.assertTrue(diferenca(a, a).empty)

    def test_agrupamento_preserva_turnos(self):
        dados = apresentar(buscar(self.base, "latam")[0])
        self.assertEqual(dados, [
            {"companhia": "LATAM", "cidade": "Belém", "turnos": ["manhã"]},
            {"companhia": "LATAM", "cidade": "São José dos Campos", "turnos": ["tarde", "noite"]},
        ])

    def test_entradas_invalidas(self):
        for texto in ["", "voos", "latam e", "ou latam", "latam e ou noite", "()",
                      "(latam", "latam)", "latam banana", "latam;", "x" * 301]:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                buscar(self.base, texto)

    def test_csv_repetido_nao_duplica_resultados(self):
        with TemporaryDirectory() as pasta:
            pasta = Path(pasta)
            (pasta / "companhias.csv").write_text("companhia,cidade\nLATAM,sjc\nlatam,sjc\n", encoding="utf-8")
            (pasta / "cidades.csv").write_text("cidade,turno\nsjc,noite\nsjc,noite\n", encoding="utf-8")
            self.assertEqual(len(ler_base(pasta)), 1)

    def test_csv_com_cidade_sem_turno_falha(self):
        with TemporaryDirectory() as pasta:
            pasta = Path(pasta)
            (pasta / "companhias.csv").write_text("companhia,cidade\nlatam,sjc\n", encoding="utf-8")
            (pasta / "cidades.csv").write_text("cidade,turno\nbel,noite\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Cidades sem turno"):
                ler_base(pasta)

    def test_valor_com_varias_palavras_no_csv(self):
        with TemporaryDirectory() as pasta:
            pasta = Path(pasta)
            (pasta / "companhias.csv").write_text("companhia,cidade\nlatam,São Paulo\n", encoding="utf-8")
            (pasta / "cidades.csv").write_text("cidade,turno\nSão Paulo,manhã\n", encoding="utf-8")
            resultado, _ = buscar(ler_base(pasta), "voos latam são paulo")
            self.assertEqual(tuplas(resultado), {("latam", "sao paulo", "manha")})


class TestInterface(unittest.TestCase):
    def setUp(self):
        temporaria = TemporaryDirectory()
        self.addCleanup(temporaria.cleanup)
        self.pasta = Path(temporaria.name)
        importar_dados_teste(self.pasta)
        self.client = create_app(self.pasta).test_client()

    def test_pagina_inicial(self):
        resposta = self.client.get("/")
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("O que você procura?", resposta.get_data(as_text=True))

    def test_busca_valida(self):
        resposta = self.client.get("/", query_string={"q": "latam e manhã"})
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("1 combinação(ões)", resposta.get_data(as_text=True))

    def test_tabelas_dos_csvs_independentes_da_busca(self):
        html = self.client.get("/?q=latam").get_data(as_text=True)
        companhias = html.split('id="csv-companhias"', 1)[1].split("</table>", 1)[0]
        cidades = html.split('id="csv-cidades"', 1)[1].split("</table>", 1)[0]
        self.assertEqual(companhias.count("<tr>"), 5)  # Cabeçalho e quatro linhas.
        self.assertEqual(cidades.count("<tr>"), 5)
        self.assertIn("gol", companhias)
        self.assertIn("campinas", cidades)

    def test_busca_invalida(self):
        resposta = self.client.get("/", query_string={"q": "companhia inexistente"})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Termo não reconhecido", resposta.get_data(as_text=True))

    def test_entrada_html_e_escapada(self):
        resposta = self.client.get("/", query_string={"q": '<script>alert("x")</script>'})
        self.assertEqual(resposta.status_code, 400)
        self.assertNotIn("<script>", resposta.get_data(as_text=True))

    def test_css_disponivel(self):
        with self.client.get("/static/style.css") as resposta:
            self.assertEqual(resposta.status_code, 200)


class TestImportacao(unittest.TestCase):
    def setUp(self):
        self.temporaria = TemporaryDirectory()
        self.addCleanup(self.temporaria.cleanup)
        self.pasta = Path(self.temporaria.name)
        importar_dados_teste(self.pasta)
        self.marcador_original = (self.pasta / ".base_ativa").read_text(encoding="ascii")
        self.originais = self.pasta / ".importacoes" / self.marcador_original
        self.app = create_app(self.pasta)
        self.client = self.app.test_client()
        self.client.get("/")
        with self.client.session_transaction() as sessao:
            self.token = sessao["csrf"]

    def enviar(self, companhias=b"companhia,cidade\navianca,recife\n", cidades=b"cidade,turno\nrecife,noite\n", nome_companhias="minhas_companhias.csv", **extras):
        dados = {"csrf": self.token,
                 "companhias": (BytesIO(companhias), nome_companhias),
                 "cidades": (BytesIO(cidades), "minhas_cidades.csv")}
        dados.update(extras)
        return self.client.post("/importar", data=dados, follow_redirects=True)

    def test_upload_atualiza_busca_e_persiste_apos_reinicio(self):
        resposta = self.enviar()
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("CSV importados!", resposta.get_data(as_text=True))
        self.assertIn("voos avianca", resposta.get_data(as_text=True))
        self.assertEqual(self.client.get("/?q=avianca").status_code, 200)
        self.assertEqual(self.client.get("/?q=latam").status_code, 400)
        novo_cliente = create_app(self.pasta).test_client()
        self.assertIn("Recife", novo_cliente.get("/?q=avianca").get_data(as_text=True))
        self.assertEqual((self.originais / "companhias.csv").read_bytes(), COMPANHIAS)

    def test_csv_invalido_preserva_base_ativa(self):
        resposta = self.enviar(companhias=b"errado,cidade\navianca,recife\n")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("cabeçalho esperado", resposta.get_data(as_text=True))
        self.assertEqual(self.client.get("/?q=latam").status_code, 200)
        self.assertEqual((self.pasta / ".base_ativa").read_text(encoding="ascii"), self.marcador_original)

    def test_cidade_sem_turno_preserva_ultima_importacao(self):
        self.enviar()
        resposta = self.enviar(cidades=b"cidade,turno\nfortaleza,noite\n")
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(self.client.get("/?q=avianca").status_code, 200)

    def test_tabelas_preservam_escrita_repeticoes_e_cidades_sem_companhia(self):
        resposta = self.enviar(
            companhias="companhia,cidade\nLATAM,São Paulo\nLATAM,São Paulo\n".encode("utf-8"),
            cidades="cidade,turno\nSão Paulo,MANHÃ\nCampinas,noite\n".encode("utf-8"),
        )
        self.assertEqual(resposta.status_code, 200)
        html = resposta.get_data(as_text=True)
        companhias = html.split('id="csv-companhias"', 1)[1].split("</table>", 1)[0]
        cidades = html.split('id="csv-cidades"', 1)[1].split("</table>", 1)[0]
        self.assertEqual(companhias.count("<tr>"), 3)
        self.assertEqual(companhias.count("São Paulo"), 2)
        self.assertIn("MANHÃ", cidades)
        self.assertIn("Campinas", cidades)

    def test_arquivo_ausente(self):
        resposta = self.client.post("/importar", data={"csrf": self.token})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Selecione os dois arquivos", resposta.get_data(as_text=True))

    def test_extensao_errada(self):
        resposta = self.enviar(nome_companhias="arquivo.txt")
        self.assertEqual(resposta.status_code, 400)

    def test_token_obrigatorio(self):
        resposta = self.enviar(csrf="invalido")
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual((self.pasta / ".base_ativa").read_text(encoding="ascii"), self.marcador_original)

    def test_csv_sem_dados(self):
        self.assertEqual(self.enviar(companhias=b"companhia,cidade\n").status_code, 400)

    def test_utf8_invalido(self):
        resposta = self.enviar(cidades=b"cidade,turno\nrecife,manh\xe3\n")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("UTF-8", resposta.get_data(as_text=True))

    def test_colunas_excedentes(self):
        self.assertEqual(self.enviar(companhias=b"companhia,cidade\navianca,recife,extra\n").status_code, 400)

    def test_ponto_e_virgula(self):
        resposta = self.enviar(companhias=b"companhia;cidade\navianca;recife\n", cidades=b"cidade;turno\nrecife;noite\n")
        self.assertEqual(resposta.status_code, 200)

    def test_limite_de_tamanho(self):
        resposta = self.client.post("/importar", data=b"a" * (2 * 1024 * 1024 + 1), content_type="application/octet-stream")
        self.assertEqual(resposta.status_code, 413)
        self.assertIn("2 MB", resposta.get_data(as_text=True))
        self.assertEqual((self.pasta / ".base_ativa").read_text(encoding="ascii"), self.marcador_original)

    def test_nao_existe_restauracao_de_exemplo(self):
        self.assertEqual(self.client.post("/restaurar", data={"csrf": self.token}).status_code, 404)
        self.assertNotIn("Voltar à base de exemplo", self.client.get("/").get_data(as_text=True))

    def test_download_modelos(self):
        for tipo, cabecalho in (("companhias", b"companhia,cidade"), ("cidades", b"cidade,turno")):
            with self.client.get(f"/modelos/{tipo}") as resposta:
                self.assertEqual(resposta.status_code, 200)
                self.assertIn(cabecalho, resposta.data)
                self.assertEqual(resposta.data.strip().splitlines(), [cabecalho])
                self.assertIn("attachment", resposta.headers["Content-Disposition"])
        self.assertEqual(self.client.get("/modelos/outro").status_code, 404)


class TestSemDados(unittest.TestCase):
    def setUp(self):
        temporaria = TemporaryDirectory()
        self.addCleanup(temporaria.cleanup)
        self.pasta = Path(temporaria.name)
        self.client = create_app(self.pasta).test_client()
        self.client.get("/")
        with self.client.session_transaction() as sessao:
            self.token = sessao["csrf"]

    def enviar(self, companhias=COMPANHIAS):
        return self.client.post("/importar", data={
            "csrf": self.token,
            "companhias": (BytesIO(companhias), "companhias.csv"),
            "cidades": (BytesIO(CIDADES), "cidades.csv"),
        }, follow_redirects=True)

    def test_pagina_inicial_sem_dados(self):
        resposta = self.client.get("/")
        html = resposta.get_data(as_text=True)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Nenhum CSV importado", html)
        self.assertNotIn('id="q"', html)
        self.assertNotIn("Conheça os dados", html)
        self.assertNotIn('id="dados-csv"', html)
        self.assertNotIn("LATAM", html)

    def test_busca_sem_importar(self):
        resposta = self.client.get("/?q=latam")
        self.assertEqual(resposta.status_code, 400)
        self.assertIn("Importe os dois CSVs antes", resposta.get_data(as_text=True))

    def test_pagina_de_codigos_funciona_sem_csvs(self):
        resposta = self.client.get("/apresentacao")
        html = resposta.get_data(as_text=True)
        self.assertEqual(resposta.status_code, 200)
        self.assertIn("Códigos do projeto", html)
        self.assertIn("def intersecao(a, b):", html)
        self.assertIn("def uniao(a, b):", html)
        self.assertIn("def diferenca(a, b):", html)
        self.assertIn("Cardinalidade", html)
        self.assertIn('href="/apresentacao"', self.client.get("/").get_data(as_text=True))

    def test_primeira_importacao_e_persistencia(self):
        self.assertEqual(self.enviar().status_code, 200)
        self.assertEqual(self.client.get("/?q=latam").status_code, 200)
        self.assertNotIn("Nenhum CSV importado", self.client.get("/").get_data(as_text=True))
        self.assertFalse((self.pasta / "companhias.csv").exists())
        self.assertEqual(create_app(self.pasta).test_client().get("/?q=latam").status_code, 200)

    def test_primeira_importacao_invalida_continua_sem_dados(self):
        self.assertEqual(self.enviar(b"errado,cidade\nlatam,sjc\n").status_code, 400)
        self.assertFalse((self.pasta / ".base_ativa").exists())
        self.assertIn("Nenhum CSV importado", self.client.get("/").get_data(as_text=True))

    def test_csvs_soltos_nao_sao_carregados_automaticamente(self):
        criar_csvs(self.pasta)
        base, importada = carregar_base(self.pasta)
        self.assertTrue(base.empty)
        self.assertFalse(importada)

    def test_primeira_importacao_cria_pasta_de_dados(self):
        destino = self.pasta / "nova_pasta"
        importar_dados_teste(destino)
        base, importada = carregar_base(destino)
        self.assertTrue(importada)
        self.assertEqual(len(base), 5)


if __name__ == "__main__":
    unittest.main()
