# Diagrama de Componentes - MVP RotasGraph

Componentes disponíveis e dependências.

```mermaid
flowchart TB
    subgraph UI[Apresentação]
        Front[HTML, Tailwind local e JavaScript nativo]
        Map[Mapa SVG e timeline]
        Front --> Map
    end
    subgraph API[FastAPI]
        App[app.main: ciclo de vida e GET /health]
        Network[RouteNetwork: grafo e índice compartilhados]
        Stations[GET /stations]
        Routes[POST /routes/search]
        App --> Network
        App --> Stations
        App --> Routes
        Stations --> Network
        Routes --> Network
    end
    subgraph Core[Domínio em memória]
        Simulator[RouteSimulator: A* temporal, bisect e heapq]
        Graph[TransportGraph: listas de adjacência]
        Itinerary[Itinerary: totais, passos e instruções]
        Snap[snap_to_network: capacidade interna]
        Analyzer[GraphAnalyzer: DFS e Tarjan iterativos]
        Time[TimeUtils]
        Simulator --> Graph
        Simulator --> Snap
        Snap --> Graph
        Analyzer --> Graph
        Itinerary --> Time
    end
    subgraph Data[Ingestão]
        Loader[DataLoader: leitura e higienização]
        Calendar[get_active_service_ids]
        Files[Seis TXT GTFS locais via Git LFS]
        Loader --> Files
        Loader --> Calendar
        Calendar --> Files
        Loader --> Time
        Loader --> Graph
    end
    subgraph CLI[Ferramentas por linha de comando]
        Topology[app.analyze_topology]
        Validation[app.validate_gtfs]
        Benchmark[benchmarks.run e referência NetworkX]
        Report[Relatórios JSON e CSV]
        Topology --> Loader
        Topology --> Analyzer
        Topology --> Report
        Validation --> Loader
        Validation --> Report
        Benchmark --> Loader
        Benchmark --> Simulator
        Benchmark --> Report
    end
    Front -->|Fetch HTTP e JSON| Stations
    Front -->|origin_id, destination_id, departure_time| Routes
    Network -->|carga na inicialização| Loader
    Network --> Graph
    Routes --> Simulator
    Routes -->|cria após receber o caminho| Itinerary
```

O domínio não importa FastAPI, frontend ou NetworkX. A API reutiliza um grafo
por data de serviço; o roteador retorna um caminho e a API cria `Itinerary`.
O encaixe de coordenadas é interno e não participa do contrato REST.

A [CLI topológica](../../docs/GRAPH_ANALYZER.md) usa `GraphAnalyzer` sem
endpoint analítico. Articulações usam projeção não direcionada simples; CFCs
usam Tarjan iterativo. A análise ignora horários e vértices temporários.
NetworkX fica somente no benchmark.

Recuperar vizinhos custa `O(1)` médio; inserir uma conexão ordenada custa
`O(K)` no pior caso. O `bisect` localiza a primeira partida em `O(log K)`,
seguido da varredura do sufixo relevante. O grafo permanece na RAM.
