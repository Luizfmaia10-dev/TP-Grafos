# Diagrama de Componentes - MVP RotasGraph

Componentes disponíveis e dependências.

```mermaid
flowchart TB
    Geocoder[Geoapify / OpenStreetMap]
    subgraph UI[Apresentação]
        Front[HTML, Tailwind local e JavaScript nativo]
        Address[Autocomplete e seleção de endereços]
        Limits[Preferências A e B de 100 m a 2 km]
        Map[Mapa SVG e timeline]
        Front --> Address
        Front --> Limits
        Front --> Map
    end
    subgraph API[FastAPI]
        App[app.main: ciclo de vida e GET /health]
        Network[RouteNetwork: grafo e índice compartilhados]
        Config[GET /config/geocoding]
        Stations[GET /stations: modo alternativo]
        Candidates[POST /snap/candidates]
        Routes[POST /routes/search]
        App --> Network
        App --> Config
        App --> Stations
        App --> Candidates
        App --> Routes
        Stations --> Network
        Candidates --> Network
        Routes --> Network
        Routes --> Candidates
    end
    subgraph Core[Domínio em memória]
        Simulator[RouteSimulator: A* temporal, bisect e heapq]
        Graph[TransportGraph: listas de adjacência]
        Itinerary[Itinerary: totais, passos e instruções]
        Snap[SnapCandidate e snap_to_network]
        Overlay[Overlay privado de arestas WALK]
        Analyzer[GraphAnalyzer: DFS e Tarjan iterativos]
        Time[TimeUtils]
        Simulator --> Graph
        Simulator --> Snap
        Snap --> Overlay
        Simulator --> Overlay
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
    Address -->|autocomplete restrito a Belo Horizonte| Geocoder
    Front -->|obtém chave pública configurada| Config
    Front -->|coordenadas e limite em metros| Candidates
    Front -->|mode address, pontos, limites e HH:MM| Routes
    Front -->|modo REST alternativo por IDs| Stations
    Network -->|carga na inicialização| Loader
    Network --> Graph
    Candidates --> Simulator
    Routes --> Simulator
    Routes -->|cria após receber o caminho| Itinerary
```

O domínio não importa FastAPI, frontend ou NetworkX. A API reutiliza um grafo
por data de serviço; o roteador retorna um caminho e a API cria `Itinerary`.
O frontend geocodifica os endereços, pré-visualiza candidatas por
`POST /snap/candidates` e envia a rota por endereço. A API repete a validação,
aplica limites independentes de 100 a 2.000 metros e cria duas caminhadas
direcionais em um overlay descartável. O grafo compartilhado não é mutado.

A [CLI topológica](../../../docs/GRAPH_ANALYZER.md) usa `GraphAnalyzer` sem
endpoint analítico. Articulações usam projeção não direcionada simples; CFCs
usam Tarjan iterativo. A análise ignora horários e vértices temporários.
NetworkX fica somente no benchmark.

Recuperar vizinhos custa `O(1)` médio; inserir uma conexão ordenada custa
`O(K)` no pior caso. O `bisect` localiza a primeira partida em `O(log K)`,
seguido da varredura do sufixo relevante. O grafo permanece na RAM.
