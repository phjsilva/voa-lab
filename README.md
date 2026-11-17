# Busca de voos — versão simples para apresentação

Aplicação de Matemática para Computação com Python, Flask, CSV e Pandas.

O programa lê dois CSVs, relaciona os dados pela cidade e aplica filtros com
interseção, união ou diferença. O frontend recebe os formulários e exibe os dados;
toda a consulta é calculada no backend.

## Executar

Na pasta do projeto:

```powershell
.\.venv\Scripts\python.exe app.py
```

Se ainda não houver ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Abra http://127.0.0.1:5000. Para encerrar, pressione Ctrl+C.
Depois de alterar o Python, encerre o servidor e execute novamente.

## CSVs

Importe os dois arquivos pelo site. Os cabeçalhos são:

- Companhias: `companhia,cidade`.
- Cidades: `cidade,turno`.

Use a mesma cidade nos dois arquivos e os turnos manhã, tarde ou noite.
Os CSVs precisam de linhas de dados, codificação UTF-8 e separador vírgula ou
ponto e vírgula. Os modelos vazios estão disponíveis no formulário.
O envio aceita até 2 MB. Um CSV inválido é recusado antes de substituir os dados.

Os arquivos importados ficam em `data/companhias.csv` e `data/cidades.csv`.
O projeto não inclui dados de exemplo como base inicial. As importações que já
existiam foram preservadas. A aplicação é local e usa uma única base de dados.

## Buscas do enunciado

Após importar seus CSVs, use os nomes que estiverem nos dados:

| Busca | Operação |
| --- | --- |
| `voos latam` | Filtro de companhia |
| `voos latam e manhã` | Interseção |
| `voos latam sjc` | Interseção implícita |
| `voos latam ou noite` | União |
| `voos gol exceto noturnos` | Diferença |

Acentos e maiúsculas são ignorados. Cidades com várias palavras são aceitas.
Cada consulta aceita um filtro ou dois filtros com um operador. Parênteses e
cadeias com várias operações foram retirados para simplificar a apresentação.
Cada linha do resultado é uma tripla `(companhia, cidade, turno)`.

## Código para estudar

- `backend/dados.py`: leitura, junção e salvamento dos CSVs.
- `backend/consultas.py`: filtros, operações e interpretação da busca simples.
- `backend/app.py`: duas páginas e recebimento do formulário com Flask.
- `frontend/`: HTML, CSS e JavaScript de exibição.

O `app.py` da raiz apenas inicia o Flask. Não há classes de serviço, sessões,
histórico de importações nem leitura do código-fonte pelo servidor.

A página http://127.0.0.1:5000/apresentacao mostra cartões no estilo CodeSnap.
Os trechos de código ficam em `frontend/templates/codigos.html`, como material de
apresentação. Se alterar uma função depois, atualize também esse material.
O roteiro está em `docs/APRESENTACAO.md`.

## Testes

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes cobrem os cinco exemplos do enunciado, conjuntos, CSVs, importação,
persistência, erros e páginas.

## Observação sobre o enunciado

A página 22 de `set_theory.pdf` menciona repetir a PRJ.8, mas também fala em CSVs
de companhias aéreas e cidades, assunto da PRJ.9. Este projeto mantém a opção de
busca de voos com CSV e Pandas já escolhida para este exemplo.
