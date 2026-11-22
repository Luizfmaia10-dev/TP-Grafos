# TP-Grafos

Trabalho pratico desenvolvido para a disciplina de Teoria dos Grafos e Computabilidade do curso de Engenharia de Software da PUC Minas.

Objetivo: desenvolver uma ferramenta computacional para resolucao de problemas aplicados por meio de modelagem, implementacao e analise de grafos.

## Linguagem

Python

## Tema

Analise de redes de transporte publico: construcao de grafos baseados em linhas de onibus, metro ou trem, com simulacao de trajetos, tempo de espera e eficiencia.

## Autores e Disciplina

- Alunos: Caio Cesar Falinacio dos Santos, Gabriel Aredes, Joaquim Antonio, Luiz Fernando Cunha Maia, Pedro Henrique Nogueira e Wanessa Oliveira Marcos.
- Disciplina: Teoria dos Grafos e Computabilidade.
- Professor Responsavel: Leonardo Vilela Cardoso.

## Como rodar

Requisitos: Python 3.12+, Git LFS (para os dados reais) e, apenas para recompilar o CSS, Node.js 20+.

O backend (FastAPI) tambem serve o frontend, entao basta um servidor.
Execute todos os comandos a partir da raiz do repositorio.

### 1. Baixar os dados GTFS

Necessario apenas para calcular rotas com os dados reais de BH. Os testes nao
dependem deste passo.

```sh
git lfs install
git lfs pull
```

### 2. Instalar as dependencias

```sh
python3.12 -m venv .venv         # ou: uv venv --python 3.12 .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

Se o sistema so tiver Python 3.11, use a opcao com `uv`, que baixa o 3.12.

### 3. Iniciar o servidor

```sh
export GTFS_SERVICE_DATE=2026-11-17   # Windows (PowerShell): $env:GTFS_SERVICE_DATE = "2026-11-17"
python -m uvicorn app.main:app --app-dir backend --port 8000
```

Abra http://127.0.0.1:8000/. A carga da rede leva cerca de 1 minuto.

`GTFS_SERVICE_DATE` exige os dados do passo 1. Para abrir so a interface, sem
os dados, nao defina essa variavel: a pagina abre, mas as buscas ficam
indisponiveis.

### Frontend (opcional)

O CSS compilado ja esta no repositorio. So e preciso recompilar ao editar estilos:

```sh
cd frontend
npm ci
npm run build
```

### Testes

```sh
python -m pytest -c backend/pytest.ini backend/tests   # backend
cd frontend && npm test                                 # frontend
```

Mais detalhes: [frontend/README.md](frontend/README.md) e [docs/FRONTEND_INTEGRATION.md](docs/FRONTEND_INTEGRATION.md).
