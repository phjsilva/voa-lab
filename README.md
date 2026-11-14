# PRJ.10 — Busca de voos com CSV e Pandas

Aplicação didática com Python, Flask, HTML, CSS e Pandas. A pessoa escreve uma busca e recebe as combinações de companhia, cidade e turno que atendem aos filtros.

## Interpretação do enunciado

Na página 22 de `set_theory.pdf`, a PRJ.10 pede para repetir a PRJ.8, mas descreve arquivos de companhias aéreas e cidades. Esse assunto é o da **PRJ.9**; a PRJ.8 é sobre similaridade de Jaccard. Este projeto assume que a referência pretendida é a PRJ.9, adaptada para CSV e Pandas.

O projeto inicia sem dados cadastrados. As buscas ficam disponíveis depois que você importa seus dois CSVs pelo site. Não há consulta a horários ou disponibilidade de voos reais.

## Como executar

Requer Python 3.10 ou superior. Abra um terminal na pasta do projeto que contém `app.py`.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Abra http://127.0.0.1:5000 no navegador. Para encerrar, pressione Ctrl+C no terminal. Os comandos acima funcionam no Windows sem precisar ativar o ambiente virtual.

No Linux/macOS, use `.venv/bin/python` no lugar de `.\.venv\Scripts\python.exe`.

## Importar os CSVs pelo site

1. Abra a página e clique em **Usar meus próprios CSVs**, ou role até **Importar seus CSVs**.
2. No primeiro campo, escolha o CSV com cabeçalho `companhia,cidade`.
3. No segundo, escolha o CSV com cabeçalho `cidade,turno`.
4. Clique em **Importar e usar nas buscas**.

O envio aceita até 2 MB no total, codificação UTF-8 e separador vírgula ou ponto e vírgula. Os nomes dos arquivos podem ser quaisquer, desde que terminem em `.csv`. Cada arquivo precisa ter pelo menos uma linha de dados e duas colunas. Cidades das companhias devem ter turnos no outro CSV; turnos permitidos: manhã, tarde e noite.

Sem arquivos importados, a página mostra uma orientação para enviar os dois CSVs. Depois do envio válido, a busca e os exemplos clicáveis ficam disponíveis imediatamente, sem reiniciar o servidor. Se um arquivo for inválido, a página explica o erro e mantém a base anterior, se houver. Os dois arquivos validados são guardados juntos em `data/.importacoes/`, e `data/.base_ativa` identifica a versão em uso. Essa seleção continua ativa após reiniciar o servidor. Versões importadas anteriores permanecem guardadas nessa pasta.

Os links **Baixar modelo vazio** fornecem somente os cabeçalhos `companhia,cidade` e `cidade,turno`. Preencha as linhas com seus dados antes de importar. A aplicação não carrega automaticamente CSVs soltos em `data/` e não possui uma base de exemplo para restaurar. Esta aplicação local compartilha uma única base entre as abas abertas.

## Visualizar os arquivos importados

Depois da importação, a seção **Dados dos CSVs importados** mostra duas tabelas: **Companhias aéreas** e **Cidades e turnos**. Elas exibem as linhas de cada arquivo, preservando a escrita, a ordem e as repetições. As tabelas continuam completas durante as buscas. Mais abaixo, **Combinações usadas nas buscas** mostra o relacionamento dos dados pela cidade.

## Exemplos hipotéticos de busca

Os resultados abaixo pressupõem arquivos com os dados do exemplo matemático desta documentação. Esses dados não são carregados pelo site; use suas companhias, cidades e turnos nas buscas.

| Busca                      | Resultado                                                 |
| -------------------------- | --------------------------------------------------------- |
| `voos latam`               | LATAM: SJC à tarde e à noite; Belém de manhã              |
| `voos latam e manhã`       | LATAM: Belém de manhã                                     |
| `voos latam sjc`           | LATAM: SJC à tarde e à noite                              |
| `voos latam ou noite`      | Todas as combinações LATAM, mais AZUL em Campinas à noite |
| `voos gol exceto noturnos` | GOL: Belém de manhã                                       |
| `voos latam exceto noite`  | LATAM: SJC à tarde e Belém de manhã                       |
| `voos gol e noite`         | Nenhum resultado                                          |
| `(latam ou azul) e noite`  | LATAM em SJC e AZUL em Campinas, ambas à noite            |

SJC significa São José dos Campos; BEL significa Belém. A busca aceita os códigos ou os nomes completos. Acentuação e maiúsculas são ignoradas. `voo`/`voos` são opcionais no início; termos adjacentes, como `latam sjc`, equivalem a `latam e sjc`.

## Como os conjuntos são usados

O universo é formado por tuplas **(companhia, cidade, turno)**. Primeiro, `pd.read_csv()` lê os dois arquivos. Depois, `merge(..., on="cidade")` relaciona as companhias com os turnos das cidades onde operam. No exemplo hipotético abaixo, as duas linhas LATAM geram três combinações, pois SJC tem dois turnos.

Cada termo produz um subconjunto desse universo. Por exemplo:

```text
A = combinações da LATAM
  = {(latam, sjc, tarde), (latam, sjc, noite), (latam, bel, manhã)}

B = combinações noturnas
  = {(latam, sjc, noite), (azul, campinas, noite)}

A ∩ B = {(latam, sjc, noite)}
A ∪ B = {(latam, sjc, tarde), (latam, sjc, noite),
         (latam, bel, manhã), (azul, campinas, noite)}
A − B = {(latam, sjc, tarde), (latam, bel, manhã)}
```

| Operação                   | Pandas                                  | Efeito                                         |
| -------------------------- | --------------------------------------- | ---------------------------------------------- |
| Relacionamento das tabelas | `merge` pela cidade                     | Associa companhia aos turnos                   |
| Interseção (`e`)           | `merge` interno pelas três colunas      | Mantém tuplas presentes nos dois resultados    |
| União (`ou`)               | `concat` e `drop_duplicates`            | Reúne as tuplas sem repetir                    |
| Diferença (`exceto`)       | `merge` à esquerda com `indicator=True` | Mantém apenas tuplas marcadas como `left_only` |

As operações usam as três colunas para evitar misturar companhias que operam na mesma cidade. A exibição agrupa os turnos por companhia e cidade depois que a consulta termina.

## Regras da linguagem de busca

1. Parênteses são resolvidos primeiro.
2. `e`, incluindo a interseção implícita, tem prioridade sobre os demais operadores.
3. `ou` e `exceto` têm a mesma prioridade e são associados à esquerda.
4. Termos reconhecidos são companhias e cidades cadastradas, turnos e os apelidos definidos em `backend/consultas.py`.
5. `noturno(s)`, `vespertino(s)` e `matutino(s)` equivalem a noite, tarde e manhã.
6. Termos desconhecidos, parênteses incorretos e operadores sem termo geram uma mensagem de erro. Uma busca válida sem correspondências mostra um resultado vazio.

Exemplo: `latam ou azul e noite` significa `latam ou (azul e noite)`. Para limitar as duas companhias à noite, escreva `(latam ou azul) e noite`.

É uma linguagem de filtros controlada. Não é um interpretador de português livre: frases como “passagens baratas para amanhã” não são reconhecidas. Não se usa `eval`, SQL ou `DataFrame.query` com a entrada do usuário.

## Arquivos

```text
prj10_busca_voos/
├── app.py                     # Inicia o site
├── backend/
│   ├── __init__.py            # Identifica a pasta como pacote Python
│   ├── app.py                 # Recebe os formulários e mostra as respostas
│   ├── consultas.py           # Filtros e operações de conjuntos com Pandas
│   └── dados.py               # Leitura, validação e gravação dos CSVs
├── frontend/
│   ├── templates/            # Páginas de busca e apresentação
│   └── static/               # CSS do site e da página de códigos
├── data/                      # CSVs enviados pelo usuário
├── tests/test_consulta.py     # Testes automatizados
├── docs/
│   ├── APRESENTACAO.md        # Explicação matemática e demonstração
│   ├── ESTRUTURA.md           # Responsabilidade de cada arquivo
│   └── VERIFICACAO.txt        # Verificações realizadas
└── requirements.txt           # Dependências Python
```

O frontend é servido pelo Flask. Inicie a aplicação pela raiz com `python app.py`; as rotas encontram o HTML e o CSS em `frontend/`. A lógica Python fica em `backend/`, e os CSVs continuam em `data/`.

Veja o [guia da estrutura](docs/ESTRUTURA.md) para entender a responsabilidade de cada arquivo e o caminho de uma consulta.

Os CSVs usam vírgula ou ponto e vírgula como separador e codificação UTF-8. Para expandir a base, mantenha os cabeçalhos e envie os dois arquivos pela página. Os termos novos são carregados automaticamente. Use o mesmo identificador de cidade nos dois arquivos; toda cidade de uma companhia deve possuir pelo menos um turno em `cidades.csv`. Turnos permitidos: manhã, tarde e noite. Linhas repetidas são removidas e valores vazios são rejeitados. Identificadores iguais em colunas diferentes e palavras reservadas da busca são rejeitados para evitar ambiguidade. Para atualizar os dados, envie novamente os dois CSVs pelo site.

## Testes

Na mesma pasta, após instalar as dependências:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os 47 testes verificam os exemplos adaptados do enunciado, operações e identidades de conjuntos, remoção de duplicatas, nomes com várias palavras, acentos, precedência, parênteses, entradas inválidas, agrupamento e respostas HTTP. Também verificam upload, persistência após reinício, preservação da base anterior, início sem dados, modelos vazios para download, codificação, separadores, cabeçalhos e limite de tamanho.

## Página de códigos

No menu do site, abra **Códigos do projeto**, em http://127.0.0.1:5000/apresentacao. A página funciona mesmo antes de importar CSVs e usa abas: CSV, junção, subconjuntos, interseção, união, diferença, operadores e cardinalidade. Cada etapa tem uma explicação à esquerda e a função Python completa à direita, com números de linha do arquivo e destaques nas partes relacionadas ao conceito. Os botões de anterior e próximo percorrem as etapas. Quando há CSVs importados, um link abre um exemplo de busca em outra aba.

## Explicação para apresentar

Veja o [guia de apresentação de Matemática para Computação](docs/APRESENTACAO.md). Comece pelas funções curtas `filtrar`, `intersecao`, `uniao`, `diferenca` e `cardinalidade`, em `backend/consultas.py`. A função `aplicar_operacao` liga cada palavra da busca à operação usando condições simples.

“O projeto representa os dados como conjuntos. Eu leio dois arquivos CSV com Pandas e faço uma junção pela cidade. Cada busca filtra conjuntos de combinações de companhia, cidade e turno. O operador ‘e’ calcula a interseção; ‘ou’ calcula a união sem repetir elementos; e ‘exceto’ calcula a diferença. O Flask recebe o texto, chama o mecanismo de consulta e devolve uma página HTML com os resultados e as etapas da operação.”

## Referências técnicas

- [Pandas: read_csv](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)
- [Pandas: DataFrame.merge](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.merge.html)
- [Flask: Quickstart](https://flask.palletsprojects.com/en/stable/quickstart/)
