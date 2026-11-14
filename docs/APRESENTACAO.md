# Guia para apresentar em Matemática para Computação

## Página no site

Abra **Códigos do projeto** no menu do site, ou acesse http://127.0.0.1:5000/apresentacao. O guia usa abas para mostrar uma etapa por vez. A explicação fica à esquerda; a função completa fica à direita, com numeração real e linhas destacadas. Você pode clicar nas abas, usar as setas do teclado ou os botões de anterior e próximo. O link de exemplo abre a busca em outra aba usando os CSVs já importados.

## Objetivo do programa

Buscar combinações de companhia aérea, cidade e turno usando operações de conjuntos. Os dados vêm de dois arquivos CSV, são lidos com Pandas e aparecem em um site feito com Flask, HTML e CSS.

## Os três arquivos do backend

| Arquivo | Explicação simples |
| --- | --- |
| `backend/dados.py` | Lê os dois CSVs e relaciona os dados pela cidade |
| `backend/consultas.py` | Filtra os dados e calcula interseção, união e diferença |
| `backend/app.py` | Recebe a busca do site e mostra a resposta |

Comece pelos dados e pelas três funções do início de `consultas.py`. Elas mostram diretamente o conteúdo matemático do trabalho.

## 1. Definir os elementos do conjunto

Cada elemento é uma tripla ordenada:

```text
(companhia, cidade, turno)
```

Por exemplo, `(latam, sjc, noite)` representa uma combinação da LATAM em São José dos Campos à noite.

As três colunas juntas identificam um elemento. Duas companhias na mesma cidade e no mesmo turno são elementos diferentes.

## 2. Mostrar como os CSVs se relacionam

No site, comece pelas duas tabelas de **Dados dos CSVs importados**. Elas mostram cada arquivo antes da junção. Depois mostre **Combinações usadas nas buscas**, que reúne companhia, cidade e turno.

Em `dados.py`, a função `ler_base` lê companhias e cidades. Esta linha relaciona as duas tabelas pela cidade:

```python
base = companhias.merge(cidades, on="cidade")[COLUNAS].drop_duplicates().reset_index(drop=True)
```

A companhia LATAM aparece em SJC. Como SJC tem os turnos tarde e noite, a junção gera duas combinações para essa companhia e cidade.

Essa operação é uma junção pela cidade: ela associa somente linhas com a mesma cidade nos dois arquivos. Não é o produto cartesiano irrestrito de todas as linhas.

## 3. Definir dois subconjuntos

Para explicar a matemática, suponha que seus CSVs importados produzam os conjuntos abaixo. Esses dados são apenas um exemplo na documentação:

```text
A = combinações da LATAM
  = {(latam, sjc, tarde), (latam, sjc, noite), (latam, bel, manhã)}

B = combinações noturnas
  = {(latam, sjc, noite), (azul, campinas, noite)}
```

No código, a função `filtrar` seleciona um subconjunto da tabela:

```python
def filtrar(base, coluna, valor):
    return base.loc[base[coluna] == valor]
```

## 4. Apresentar as três operações

### Interseção: A ∩ B

Mantém os elementos que pertencem aos dois conjuntos.

```python
def intersecao(a, b):
    return a.merge(b, on=COLUNAS, how="inner").drop_duplicates()
```

Busca: `voos latam e noite`

```text
A ∩ B = {(latam, sjc, noite)}
|A ∩ B| = 1
```

### União: A ∪ B

Reúne os elementos dos dois conjuntos e remove as repetições.

```python
def uniao(a, b):
    return pd.concat([a, b], ignore_index=True).drop_duplicates()
```

Busca: `voos latam ou noite`

```text
A ∪ B = {(latam, sjc, tarde), (latam, sjc, noite),
         (latam, bel, manhã), (azul, campinas, noite)}
|A ∪ B| = 4
```

O elemento `(latam, sjc, noite)` aparece nos dois conjuntos, mas entra uma única vez na união.

### Diferença: A − B

Mantém os elementos do primeiro conjunto que não aparecem no segundo.

```python
def diferenca(a, b):
    comparacao = a.merge(b, on=COLUNAS, how="left", indicator=True)
    return comparacao.loc[comparacao["_merge"] == "left_only", COLUNAS].drop_duplicates()
```

`left_only` significa que o elemento apareceu somente no conjunto da esquerda, isto é, em A.

Busca: `voos latam exceto noite`

```text
A − B = {(latam, sjc, tarde), (latam, bel, manhã)}
|A − B| = 2
```

A ordem importa: A − B pode ser diferente de B − A.

## 5. Mostrar a cardinalidade

Cardinalidade é a quantidade de elementos de um conjunto. A função `cardinalidade(conjunto)` devolve `len(conjunto)` e é chamada depois da busca para mostrar a quantidade de combinações.

Para o exemplo:

```text
|A| = 3
|B| = 2
|A ∩ B| = 1

|A ∪ B| = |A| + |B| − |A ∩ B|
        = 3 + 2 − 1
        = 4
```

A tabela da página agrupa os turnos por companhia e cidade. Portanto, a cardinalidade indicada em “combinações” pode ser maior que a quantidade de linhas visuais.

## 6. Demonstrar no site

Após importar seus arquivos, adapte os termos às companhias e aos turnos cadastrados. Se seus dados produzirem os conjuntos hipotéticos A e B acima, execute nesta ordem:

1. `voos latam` — mostra o conjunto A, com 3 elementos.
2. `voos noite` — mostra o conjunto B, com 2 elementos.
3. `voos latam e noite` — mostra a interseção, com 1 elemento.
4. `voos latam ou noite` — mostra a união, com 4 elementos.
5. `voos latam exceto noite` — mostra a diferença, com 2 elementos.

Use “Como a consulta foi resolvida” para mostrar os filtros e as operações. O site inicia sem dados: os resultados deste guia dependem dos CSVs que você importar.

## Funções auxiliares

`consultas.py` também tem as funções curtas `filtrar`, `cardinalidade` e `aplicar_operacao`. As funções auxiliares normalizam a escrita, reconhecem os termos, resolvem parênteses e respeitam a ordem das operações. Elas permitem escrever buscas em vez de selecionar conjuntos manualmente.

`dados.py` também valida o envio e guarda os arquivos. `app.py` conecta o formulário às funções. Para a explicação matemática, o ponto central é a relação entre filtros, conjuntos, operações e cardinalidade.

## Leitura do código simplificado

Comece por `filtrar`, depois mostre `intersecao`, `uniao` e `diferenca`. Em seguida, `aplicar_operacao` relaciona as três palavras da busca às funções, usando condições `if`. Por fim, `cardinalidade` conta os elementos. A função `buscar` organiza as etapas e deixa os parênteses para uma função auxiliar própria.
