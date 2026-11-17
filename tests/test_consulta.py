"""Testes dos requisitos da versão simples para apresentação."""

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from backend.app import create_app
from backend.consultas import buscar, intersecao, uniao, diferenca, COLUNAS
from backend.dados import carregar_base
from tests.fixtures import COMPANHIAS, CIDADES, importar_dados_teste


def tuplas(tabela):
    return set(tabela[COLUNAS].itertuples(index=False, name=None))


class TestProjeto(unittest.TestCase):
    def setUp(self):
        temporaria = TemporaryDirectory()
        self.addCleanup(temporaria.cleanup)
        self.pasta = Path(temporaria.name)
        importar_dados_teste(self.pasta)
        self.base = carregar_base(self.pasta)[2]
        self.client = create_app(self.pasta).test_client()

    def enviar(self, companhias=COMPANHIAS, cidades=CIDADES):
        return self.client.post('/', headers={'Origin': 'http://localhost'}, data={
            'companhias': (BytesIO(companhias), 'companhias.csv'),
            'cidades': (BytesIO(cidades), 'cidades.csv'),
        }, follow_redirects=True)

    def resultado(self, texto):
        return tuplas(buscar(self.base, texto))

    def test_juncao(self):
        self.assertEqual(tuplas(self.base), {
            ('latam', 'sjc', 'tarde'), ('latam', 'sjc', 'noite'),
            ('latam', 'bel', 'manha'), ('gol', 'bel', 'manha'),
            ('azul', 'campinas', 'noite'),
        })

    def test_cinco_exemplos_do_enunciado(self):
        exemplos = {
            'voos latam': {('latam', 'sjc', 'tarde'), ('latam', 'sjc', 'noite'), ('latam', 'bel', 'manha')},
            'voos latam e manhã': {('latam', 'bel', 'manha')},
            'voos latam sjc': {('latam', 'sjc', 'tarde'), ('latam', 'sjc', 'noite')},
            'voos latam ou noite': {('latam', 'sjc', 'tarde'), ('latam', 'sjc', 'noite'), ('latam', 'bel', 'manha'), ('azul', 'campinas', 'noite')},
            'voos gol exceto noturnos': {('gol', 'bel', 'manha')},
        }
        for texto, esperado in exemplos.items():
            with self.subTest(texto=texto):
                self.assertEqual(self.resultado(texto), esperado)

    def test_diferenca_compara_as_tres_colunas(self):
        self.assertEqual(self.resultado('latam exceto noite'), {
            ('latam', 'sjc', 'tarde'), ('latam', 'bel', 'manha'),
        })

    def test_identidades(self):
        self.assertEqual(tuplas(intersecao(self.base, self.base)), tuplas(self.base))
        self.assertEqual(tuplas(uniao(self.base, self.base)), tuplas(self.base))
        self.assertTrue(diferenca(self.base, self.base).empty)

    def test_acentos_e_apelidos(self):
        self.assertEqual(self.resultado('VOOS LATAM BELÉM'), {('latam', 'bel', 'manha')})
        self.assertEqual(self.resultado('latam São José dos Campos'), self.resultado('latam sjc'))
        self.assertEqual(self.resultado('voo latam noturno'), self.resultado('latam e noite'))

    def test_nomes_com_varias_palavras(self):
        self.enviar('companhia,cidade\nLatam,São Paulo\n'.encode(), 'cidade,turno\nSão Paulo,MANHÃ\n'.encode())
        base = carregar_base(self.pasta)[2]
        self.assertEqual(tuplas(buscar(base, 'latam são paulo')), {('latam', 'sao paulo', 'manha')})

    def test_busca_vazia_e_formato_fora_do_escopo(self):
        for texto in ['', 'voos', 'latam e', 'ou latam', 'latam e ou noite', 'banana',
                      'latam ou azul e noite', '(latam ou azul) e noite', '<script>alert(1)</script>']:
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                buscar(self.base, texto)

    def test_busca_sem_correspondencias(self):
        self.assertEqual(self.resultado('gol e noite'), set())
        self.assertEqual(self.client.get('/?q=gol+e+noite').status_code, 200)

    def test_pagina_de_busca(self):
        resposta = self.client.get('/?q=latam+e+manhã')
        self.assertEqual(resposta.status_code, 200)
        self.assertIn('1 combinação(ões)', resposta.get_data(as_text=True))
        self.assertIn('LATAM', resposta.get_data(as_text=True))

    def test_busca_invalida_tem_mensagem(self):
        resposta = self.client.get('/?q=banana')
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('Termo não reconhecido', resposta.get_data(as_text=True))

    def test_importacao_persiste_apos_reinicio(self):
        resposta = self.enviar(b'companhia,cidade\navianca,recife\n', b'cidade,turno\nrecife,noite\n')
        self.assertEqual(resposta.status_code, 200)
        novo_cliente = create_app(self.pasta).test_client()
        self.assertIn('AVIANCA', novo_cliente.get('/?q=avianca').get_data(as_text=True))
        self.assertEqual(self.client.get('/?q=latam').status_code, 400)

    def test_csv_invalido_preserva_dados(self):
        casos = [
            (b'errado,cidade\nlatam,sjc\n', CIDADES),
            (b'companhia,cidade\n', CIDADES),
            (b'companhia,cidade\nlatam,sjc,extra\n', CIDADES),
            (b'companhia,cidade\nlatam\n', CIDADES),
            (b'companhia,cidade\nlatam,\n', CIDADES),
            (COMPANHIAS, b'cidade,turno\nsjc,manh\xe3\n'),
            (COMPANHIAS, b'cidade,turno\nbel,noite\n'),
            (COMPANHIAS, b'cidade,turno\nsjc,madrugada\nbel,noite\n'),
            (b'companhia,cidade\ne,sjc\n', CIDADES),
            (b'companhia,cidade\nsjc,sjc\n', CIDADES),
        ]
        original = (self.pasta / 'companhias.csv').read_bytes()
        for companhias, cidades in casos:
            with self.subTest(companhias=companhias, cidades=cidades):
                self.assertEqual(self.enviar(companhias, cidades).status_code, 400)
                self.assertEqual((self.pasta / 'companhias.csv').read_bytes(), original)
                self.assertEqual(self.client.get('/?q=latam').status_code, 200)

    def test_csv_com_ponto_e_virgula(self):
        resposta = self.enviar(b'companhia;cidade\navianca;recife\n', b'cidade;turno\nrecife;noite\n')
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.client.get('/?q=avianca').status_code, 200)

    def test_repeticoes_nao_duplicam_resultados(self):
        resposta = self.enviar(b'companhia,cidade\nLATAM,sjc\nlatam,sjc\n', b'cidade,turno\nsjc,noite\nsjc,noite\n')
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(carregar_base(self.pasta)[2]), 1)

    def test_tabelas_preservam_conteudo_original(self):
        self.enviar('companhia,cidade\nLATAM,São Paulo\nLATAM,São Paulo\n'.encode(),
                    'cidade,turno\nSão Paulo,MANHÃ\nCampinas,noite\n'.encode())
        html = self.client.get('/?q=latam').get_data(as_text=True)
        companhias = html.split('id="csv-companhias"', 1)[1].split('</table>', 1)[0]
        cidades = html.split('id="csv-cidades"', 1)[1].split('</table>', 1)[0]
        self.assertEqual(companhias.count('São Paulo'), 2)
        self.assertIn('MANHÃ', cidades)
        self.assertIn('Campinas', cidades)

    def test_envio_exige_os_dois_arquivos(self):
        resposta = self.client.post('/', headers={'Origin': 'http://localhost'}, data={})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('Selecione os dois arquivos', resposta.get_data(as_text=True))

    def test_envio_de_outro_site_e_recusado(self):
        self.assertEqual(self.client.post('/', headers={'Origin': 'http://outro-site'}).status_code, 403)

    def test_limite_do_envio(self):
        resposta = self.client.post('/', data=b'a' * (2 * 1024 * 1024 + 1), headers={'Origin': 'http://localhost'})
        self.assertEqual(resposta.status_code, 413)

    def test_modelos_e_estilos_sao_arquivos_do_frontend(self):
        for nome, conteudo in [('companhias', b'companhia,cidade'), ('cidades', b'cidade,turno')]:
            with self.client.get(f'/static/modelos/{nome}.csv') as resposta:
                self.assertEqual(resposta.data.strip(), conteudo)
        with self.client.get('/static/apresentacao.css') as resposta:
            self.assertEqual(resposta.status_code, 200)

    def test_inicio_e_apresentacao_sem_csvs(self):
        with TemporaryDirectory() as pasta:
            cliente = create_app(pasta).test_client()
            resposta = cliente.get('/')
            self.assertEqual(resposta.status_code, 200)
            self.assertIn('Nenhum CSV importado', resposta.get_data(as_text=True))
            self.assertEqual(cliente.get('/?q=latam').status_code, 400)
            html = cliente.get('/apresentacao').get_data(as_text=True)
            for nome in ['intersecao', 'uniao', 'diferenca']:
                self.assertIn(f'def {nome}(a, b):', html)
            self.assertIn('Ampliar código', html)
            self.assertNotIn('Não foi possível', html)

    def test_primeira_importacao_cria_pasta(self):
        pasta = self.pasta / 'nova'
        importar_dados_teste(pasta)
        self.assertEqual(len(carregar_base(pasta)[2]), 5)


if __name__ == '__main__':
    unittest.main()
