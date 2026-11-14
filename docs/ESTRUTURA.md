# Estrutura simples do backend

O backend tem três arquivos principais, com funções em vez de classes:

| Arquivo | Responsabilidade |
| --- | --- |
| `backend/app.py` | Receber os formulários e renderizar a página com Flask |
| `backend/consultas.py` | Filtrar a tabela e calcular interseção, união e diferença |
| `backend/dados.py` | Ler, validar e salvar os CSVs |

O `app.py` da raiz apenas inicia o site. `backend/__init__.py` identifica a pasta como um pacote Python; não contém regras do projeto.

## Fluxo de uma busca

1. O formulário envia o texto para a rota `/`.
2. `carregar_base`, em `dados.py`, lê a versão ativa dos CSVs. Se ainda não houve importação, devolve uma tabela vazia e a página orienta o envio dos arquivos.
3. `ler_base` relaciona companhias e turnos pela cidade com `merge`.
4. `buscar`, em `consultas.py`, aplica os filtros e as operações de conjuntos.
5. `app.py` envia o resultado para `frontend/templates/index.html`.

A base é lida a cada requisição. Isso dispensa objetos de serviço, estado em memória e gerenciamento de versões em uma classe. O arquivo `.base_ativa` continua identificando os CSVs importados; a escolha persiste após reiniciar o servidor.

## Onde está a matemática

As três funções no início de `consultas.py` representam diretamente A ∩ B, A ∪ B e A − B. Cada elemento é uma tripla `(companhia, cidade, turno)`. `drop_duplicates` garante que um elemento não apareça repetido.

`cardinalidade(resultado)` calcula a quantidade de elementos com `len`. A função `filtrar` seleciona os subconjuntos, e `aplicar_operacao` escolhe a operação com condições `if`. O arquivo `docs/APRESENTACAO.md` mostra os exemplos completos.

## Outras pastas

- `frontend/`: HTML e CSS, servidos pelo Flask.
- `data/`: CSVs importados e identificação da base ativa.
- `tests/`: testes do cálculo, buscas, arquivos e páginas.
- `docs/`: explicações e verificações.

## Executar

Na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe app.py
```

Abra http://127.0.0.1:5000. Para encerrar, pressione Ctrl+C.

## Testar

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os modelos para download contêm somente os cabeçalhos. Não há CSV preenchido incluído como base inicial, nem botão de restauração de exemplo.

A interpretação da busca usa duas etapas explícitas: primeiro resolve os grupos de interseção; depois aplica união e diferença da esquerda para a direita. Os parênteses são tratados por `resolver_parenteses`. A validação do formato CSV fica em uma função separada da leitura.
