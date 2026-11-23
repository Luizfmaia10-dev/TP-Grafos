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

## 2. Busca por endereços com snap-to-network

```mermaid
sequenceDiagram
    actor Passenger as Passageiro
    participant UI as Frontend
    participant Geo as Geoapify / OSM
    participant API as Controladores REST
    participant Network as RouteNetwork
    participant Simulator as RouteSimulator
    participant Graph as TransportGraph
    participant Itinerary as Itinerary
    UI->>API: GET /config/geocoding
    API-->>UI: disponibilidade e chave configurada
    Passenger->>UI: Informar origem e destino
    UI->>Geo: Autocomplete restrito a Belo Horizonte
    Geo-->>UI: Endereço, latitude e longitude
    par Origem
        UI->>API: POST /snap/candidates (coordenadas, limite A)
        API->>Simulator: find_snap_candidates(..., até 2 km)
        Simulator->>Graph: iter_stations()
        Graph-->>Simulator: Estações reais
        Simulator-->>API: Candidatas ordenadas por distância e ID
        API-->>UI: Paradas dentro do limite A
        Passenger->>UI: Confirmar parada recomendada ou outra válida
    and Destino
        UI->>API: POST /snap/candidates (coordenadas, limite B)
        API->>Simulator: find_snap_candidates(..., até 2 km)
        Simulator->>Graph: iter_stations()
        Graph-->>Simulator: Estações reais
        Simulator-->>API: Candidatas ordenadas por distância e ID
        API-->>UI: Parada mais próxima dentro do limite B
    end
    opt Alterar preferência de caminhada
        Passenger->>UI: Escolher A ou B e valor entre 100 e 2.000 m
        UI->>API: POST /snap/candidates se o endereço já existe
        API-->>UI: Candidatas atualizadas ou distância mínima necessária
    end
    Passenger->>UI: Confirmar HH:MM e calcular
    UI->>API: POST /routes/search (mode address, pontos, limites, station_id da origem)
    API->>API: Validar RouteSearchRequest e limites
    API->>Simulator: Revalidar candidatas e parada escolhida
    Note over API: 422 entrada ou limite inválido / 404 sem parada / 503 sem rede
    API->>Simulator: RouteSimulator(network.graph, network.max_speed)
    API->>Simulator: snap_to_network(origem, parada confirmada)
    API->>Simulator: snap_to_network(destino, parada mais próxima)
    Note over Simulator: Arestas WALK direcionais em overlay privado
    API->>Simulator: calculate_route(origin, destination, departure_time)
    loop Estações expandidas no A* temporal
        Simulator->>Graph: get_neighbors(station)
        Graph-->>Simulator: Conexões ordenadas
        Simulator->>Simulator: Combinar overlay, bisect e relaxar com heapq
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
    API->>Simulator: Encerrar contextos de origem e destino
    Simulator->>Simulator: Remover todas as conexões temporárias
    Note over Simulator,Graph: O TransportGraph compartilhado não é mutado
```

Os limites A e B são independentes, começam em 800 metros e aceitam qualquer
inteiro entre 100 e 2.000. Eles podem ser salvos antes dos endereços. A API
repete todas as validações do frontend; a origem deve indicar uma candidata
válida e o destino usa a mais próxima.

O modo `station`, com `origin_id` e `destination_id`, permanece disponível no
mesmo endpoint para clientes REST. A interface usa `mode: "address"`. Editar
endereços, limites ou horário cancela a consulta e descarta respostas antigas.

A CLI `app.analyze_topology` chama `DataLoader.build_graph` e `GraphAnalyzer`
e exporta JSON separadamente, sem endpoint analítico. Veja
[a API](../../../docs/API.md) e [a CLI](../../../docs/GRAPH_ANALYZER.md).

## Referência do padrão

- [Mermaid - Sequence diagrams](https://mermaid.js.org/syntax/sequenceDiagram)
