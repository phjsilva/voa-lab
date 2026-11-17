# Roteiro para apresentar em 19 de novembro de 2026

## 1. Objetivo

“Meu programa busca combinações de companhia aérea, cidade e turno. Eu uso dois
arquivos CSV e faço as consultas com Pandas. O Flask recebe a entrada e o HTML
mostra as informações.”

## 2. Mostrar os dados

Inicie o projeto e abra http://127.0.0.1:5000.
Importe seus dois CSVs e mostre as tabelas de companhias e cidades.

- Uma tabela tem companhia e cidade.
- A outra tem cidade e turno.
- A cidade relaciona as duas tabelas.

Em `backend/dados.py`, mostre `ler_csv` e depois `ler_base`.
A linha `companhias.merge(cidades, on="cidade")` junta as informações.
Cada linha gerada é um elemento: `(companhia, cidade, turno)`.

## 3. Explicar as operações

Abra **Códigos do projeto**. Use **Ampliar código** para mostrar cada função.

| Função | Explicação |
| --- | --- |
| `filtrar` | Seleciona as linhas que têm o valor informado |
| `intersecao` | Mantém as combinações presentes nos dois filtros |
| `uniao` | Reúne as combinações e remove as repetidas |
| `diferenca` | Mantém as combinações do primeiro filtro que não estão no segundo |
| `aplicar_operacao` | Usa `if` para escolher a função de “e”, “ou” ou “exceto” |
| `cardinalidade` | Usa `len` para contar as combinações |

Em `diferenca`, `indicator=True` cria a coluna `_merge`.
O valor `left_only` significa que a combinação está apenas no primeiro conjunto.
As operações comparam as três colunas, porque duas companhias na mesma cidade
continuam sendo elementos diferentes.

## 4. Demonstrar as buscas

Se seus CSVs tiverem os dados do exemplo do enunciado:

1. `voos latam`: três combinações.
2. `voos latam e manhã`: uma combinação.
3. `voos latam sjc`: duas combinações.
4. `voos latam ou noite`: quatro combinações, sem contar repetições.
5. `voos gol exceto noturnos`: uma combinação.

Se os seus CSVs forem diferentes, adapte os nomes e confira os resultados antes.
O site não inclui uma base inicial de exemplo.

## 5. Explicar o caminho da busca

Em `backend/consultas.py`:

- `normalizar` ignora acentos e maiúsculas.
- `criar_termos` relaciona os nomes dos CSVs às colunas.
- `separar_termos` reconhece um filtro ou dois filtros com um operador.
- `buscar` cria os subconjuntos e chama a operação escolhida.

Por exemplo, `latam sjc` vira `latam e sjc`.
A versão simples não interpreta parênteses nem várias operações na mesma busca.

## 6. Encerrar

“A lógica está no Python. O frontend mostra os formulários, as tabelas e as
explicações. A leitura usa `read_csv`, a junção e a interseção usam `merge`, a união
usa `concat` e a diferença seleciona as linhas marcadas como `left_only`.”

Antes do dia, reinicie o servidor e teste seus próprios CSVs.
Os cartões em `frontend/templates/codigos.html` são cópias do código desta versão;
atualize-os se mudar as funções depois.
