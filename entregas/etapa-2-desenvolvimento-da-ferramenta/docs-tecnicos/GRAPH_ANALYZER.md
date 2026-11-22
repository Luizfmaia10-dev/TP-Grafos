# Análise topológica

`app.graph_analyzer.GraphAnalyzer(graph)` analisa estações reais do
`TransportGraph`, sem FastAPI, frontend ou NetworkX. Não há endpoint analítico.
Horários, durações e vértices temporários são ignorados; conectividade estrutural
não comprova uma viagem temporalmente viável.

| Método | Resultado |
|---|---|
| `find_articulation_points()` | `set[Station]` de cortes na projeção não direcionada simples |
| `find_strongly_connected_components()` | `list[set[Station]]` via Tarjan iterativo no grafo dirigido |
| `criticality_scores()` | `dict[Station, int]` com `max(0, componentes(G-v) - componentes(G))` |
| `get_critical_stations(top_n)` | Estações de score positivo, ordenadas por score decrescente, grau simples decrescente e ID crescente |

A projeção deduplica arestas paralelas e ignora autoarestas. As buscas usam
pilhas explícitas. Projeção, articulações e CFCs custam `O(V+E)` no tempo
esperado e até `O(V+E)` no espaço. Ordenar C estações críticas acrescenta
`O(C log(C+1))`. `top_n=0` retorna `[]`; valor negativo causa `ValueError`.

## CLI

Com os TXT GTFS completos via Git LFS, execute em `backend/`:

```sh
python -m app.analyze_topology ../data/gtfs --date 2026-11-17 --output ../docs/analysis/topology.json
```

Sem `--output`, o JSON vai para stdout; mensagens operacionais vão para stderr.
A data é obrigatória. A CLI registra os seis hashes presentes, serviços ativos,
contagens, articulações, tamanhos de CFCs e até vinte estações críticas.
Inclui todas as paradas aceitas, inclusive isoladas. A higienização e a quarentena
do `DataLoader` afetam a topologia analisada. Falha de carga/escrita retorna 1;
a saída em arquivo substitui o destino somente após escrita completa e rejeita
um destino que identifique uma entrada GTFS.

O [relatório versionado](analysis/topology.json) separa `metrics` dos resultados
determinísticos. Tempos de carga e análise excluem hash e serialização; RSS é
o pico do processo inteiro, não memória exclusiva do grafo. Zero indica medida
RSS indisponível. Scores não medem demanda, passageiros afetados ou isolamento
geográfico, nem representam outras datas de serviço.

Para validar com dados sintéticos em `backend/`:

```sh
python -m pytest tests/test_graph_analyzer.py tests/test_analyze_topology.py -q
```
