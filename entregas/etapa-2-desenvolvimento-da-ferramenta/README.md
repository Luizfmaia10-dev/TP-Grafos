# Etapa 2 – Desenvolvimento da Ferramenta

## 1. Escopo da Etapa Conforme o Enunciado (TP.pdf)
> "Implementacao da estrutura de grafos, aplicacao dos algoritmos e construcao de uma interface minima de uso. Procure em sites como o Kaggle bases de dados para a execucao do seu sistema e testes. Apresente uma interface grafica com os resultados (sem limitacao de framework para frontend).  
> **Entregavel**: Prototipo funcional com codigo versionado no Git."

---

## 2. Conteudo Deste Diretorio

1. **`backend/`**:
   - `app/domain.py`: Entidades centrais `Station`, `Connection` e `VehicleType` otimizadas com `__slots__`.
   - `app/graph.py`: Estrutura de Lista de Adjacencia nativa em memoria com dicionarios (`dict[Station, list[Connection]]`) com consultas em $O(1)$ e conexoes ordenadas por horario de partida.
   - `app/route_simulator.py`: Motor de roteamento A* dependente do tempo com busca binaria (`bisect`) para consulta de partidas em $O(\log K)$ e heuristica admissivel de Haversine.
   - `app/graph_analyzer.py`: Algoritmo DFS com `lowpt` para identificacao de Pontos de Articulacao e algoritmo de Tarjan para Componentes Fortemente Conexos (CFC).
   - `app/data_loader.py`: Parser e higienizador GTFS em streaming via `itertools.groupby`.
   - `app/time_utils.py`: Conversoes de horarios de servico para minutos fracionarios.
   - `app/main.py` e `app/api/`: Camada controladora REST em FastAPI (`GET /stations` e `POST /routes/search`).
   - `tests/`: 362 testes unitarios automatizados sob metodologia TDD (cobertura de 96,17%).

2. **`frontend/`**:
   - Interface web interativa em HTML5, Tailwind CSS e Vanilla JavaScript.
   - Mapa vetorial interativo em SVG para selecao visual de estacoes e renderizacao do trajeto com coloracoes padronizadas (Metro em Blue `#209dd7`, Onibus em Red `#e11d48`, Acoes em Purple `#753991`, Caminhada em Gray `#888888`).
   - Timeline lateral com exibicao passo a passo do itinerario retornado.

3. **`data/`**:
   - Estrutura de dados de transporte publico da BHTRANS (GTFS).
   - `data/gtfs/README.md`: Instrucoes para restauracao dos arquivos completos via Git LFS.

4. **`docs-tecnicos/`**:
   - Documentacao completa de contratos de API, modulos de calculo e relatorios de benchmark:
     `API.md`, `DATA_LOADER.md`, `ROUTE_SIMULATOR.md`, `GRAPH_ANALYZER.md`, `ITINERARY.md`, `FRONTEND_INTEGRATION.md`, `GTFS_VALIDATION.md`, `TIME_UTILS.md`, `BENCHMARK.md`.

5. **`README_PROJETO.md`**:
   - Guia de instalacao e inicializacao rapida do projeto.

---

## 3. Instrucoes Rapidas de Execucao

### Backend (FastAPI):
```bash
# A partir do diretorio do projeto
python -m venv venv
venv\Scripts\activate   # No Windows
pip install -r backend/requirements.txt
pytest backend/tests    # Executar a bateria de testes unitarios
uvicorn backend.app.main:app --reload --port 8000
```

### Frontend:
Acesse no navegador:
`http://localhost:8000` (servido estaticamente pelo FastAPI) ou abra diretamente `frontend/index.html`.

---

## 4. Avaliacao de Completude
- [x] Estrutura de grafos em memoria implementada (sem bibliotecas prontas como NetworkX no core).
- [x] Algoritmos implementados: A* com heuristica admissivel, busca binaria temporal, Pontos de Articulacao e CFCs.
- [x] Base de dados real de transporte publico (BHTRANS / GTFS).
- [x] Interface grafica interativa com mapa SVG e itinerario detalhado.
- [x] Suite de testes unitarios em TDD com 100% de aprovacao.
- **Status**: **100% Concluido**. Nenhum item de codigo em falta nesta etapa.
