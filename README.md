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
