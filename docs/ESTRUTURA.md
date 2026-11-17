# Estrutura do projeto

O backend tem três arquivos e usa funções simples.

| Arquivo | Responsabilidade |
| --- | --- |
| `backend/dados.py` | Ler os CSVs com Pandas, conferir os dados e fazer a junção pela cidade |
| `backend/consultas.py` | Selecionar os filtros e calcular interseção, união e diferença |
| `backend/app.py` | Receber os formulários e entregar os resultados ao HTML |

O `app.py` da raiz apenas inicia o servidor.

## Caminho dos dados

1. O formulário envia dois CSVs para `/` com POST.
2. `importar_csvs` lê e confere os dois arquivos antes de salvar em `data/`.
3. A página carrega os arquivos com `carregar_base`.
4. `ler_base` relaciona companhias e turnos com `merge` pela cidade.
5. A busca chega como texto para `/` com GET.
6. `buscar` encontra um ou dois filtros e aplica a operação.
7. O HTML mostra as tabelas e a quantidade de combinações.

## Apresentação

`/apresentacao` apenas abre o HTML com os cartões de código. As explicações e os
trechos ficam no frontend. O JavaScript controla as abas, as cores e a cópia do
texto; não lê CSVs nem calcula resultados de buscas.

Os modelos vazios também são arquivos estáticos do frontend. Os dados importados
ficam nos dois CSVs de `data/`. As antigas pastas `.importacoes` foram preservadas,
mas o programa simplificado não depende delas.
