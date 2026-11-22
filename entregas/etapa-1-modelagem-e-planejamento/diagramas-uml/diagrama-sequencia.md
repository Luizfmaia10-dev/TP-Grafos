# Diagramas de Sequência - MVP RotasGraph

## 1. Inicialização para uma data de serviço

```mermaid
sequenceDiagram
    actor Operator as Operador
    participant API as FastAPI lifespan
    participant Network as RouteNetwork
    participant Loader as DataLoader
    participant GTFS as Arquivos GTFS
    participant Simulator as RouteSimulator
    Operator->>API: Configurar GTFS_SERVICE_DATE e iniciar
    API->>Network: load(data_directory, service_date)
    Network->>Loader: DataLoader(data_directory, service_date=service_date)
    Network->>Loader: build_graph()
    Loader->>GTFS: Ler calendários e quatro TXT principais
    GTFS-->>Loader: Registros
    Loader->>Loader: Higienizar e filtrar serviços ativos
    Loader-->>Network: TransportGraph
    Note over Loader: Diagnóstico em loader.report
    Network->>Simulator: max_speed_of(graph)
    Simulator-->>Network: max_speed
    Network-->>API: RouteNetwork com grafo, índice, velocidade e data
    API->>API: Armazenar em app.state.network
    API-->>Operator: Aplicação pronta
    Note over API: Sem data, rede não configurada. Erro de carga interrompe startup
```

## 2. Busca por estações

```mermaid
sequenceDiagram
    actor Passenger as Passageiro
    participant UI as Frontend
    participant API as Controladores REST
    participant Network as RouteNetwork
    participant Simulator as RouteSimulator
    participant Graph as TransportGraph
    participant Itinerary as Itinerary
    Passenger->>UI: Pesquisar nome ou ID
    UI->>API: GET /stations?query=texto&limit=20
    API->>Network: Filtrar network.stations
    Network-->>API: Estações correspondentes
    API-->>UI: Lista JSON
    Passenger->>UI: Selecionar estações e HH:MM
    UI->>API: POST /routes/search (origin_id, destination_id, departure_time)
    API->>API: Validar RouteSearchRequest e IDs
    Note over API: 422 entrada inválida / 404 ID desconhecido / 503 sem rede
    API->>Simulator: RouteSimulator(network.graph, network.max_speed)
    API->>Simulator: calculate_route(origin, destination, departure_time)
    loop Estações expandidas no A* temporal
        Simulator->>Graph: get_neighbors(station)
        Graph-->>Simulator: Conexões ordenadas
        Simulator->>Simulator: bisect, varredura e relaxamentos com heapq
    end
    Simulator-->>API: path ou None
    alt path é None
        API-->>UI: 200, status=no-route, route=null
        UI-->>Passenger: Orientar ajuste da busca
    else Caminho não vazio
        API->>API: build_route_result(path, departure_time)
        API->>Itinerary: Itinerary(path[0][0], departure_time, path)
        Itinerary-->>API: Passos, totais e instruções
        API-->>UI: 200, status=found, route preenchida
        UI-->>Passenger: Resumo, timeline e segmentos SVG
    end
    Note over UI,Graph: snap_to_network é interno e não participa do REST
```

O roteador retorna `list[tuple[Station, Connection]] | None`. No domínio,
origem igual ao destino retorna `[]`; o REST exige IDs distintos. Editar
cancela a requisição no frontend e descarta respostas antigas.

A CLI `app.analyze_topology` chama `DataLoader.build_graph` e `GraphAnalyzer`
e exporta JSON separadamente, sem endpoint analítico. Veja
[a API](../../docs/API.md) e [a CLI](../../docs/GRAPH_ANALYZER.md).

## Referência do padrão

- [Mermaid - Sequence diagrams](https://mermaid.js.org/syntax/sequenceDiagram)
