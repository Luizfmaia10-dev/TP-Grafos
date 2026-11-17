# Diagrama de Casos de Uso - MVP RotasGraph

Este diagrama representa a arquitetura-alvo do MVP completo. Ele inclui
funcionalidades implementadas e planejadas no `docs/PLAN.md`.

O limite do sistema e os casos de uso seguem a notação UML. O código usa
`flowchart`, em vez do `usecase-beta` introduzido no Mermaid 12, para manter a
renderização compatível com visualizadores Mermaid anteriores.

```mermaid
flowchart LR
    Passenger[Passageiro]
    DataOperator[Operador de dados]
    NetworkAnalyst[Analista da rede]
    GTFS[Base GTFS de Belo Horizonte]

    subgraph System[RotasGraph - Otimizador de Rotas]
        ListStations([Consultar estações])
        SelectPoints([Selecionar origem e destino])
        SelectMapPoint([Selecionar ponto no mapa])
        SearchRoute([Buscar rota otimizada])
        ValidateRequest([Validar dados da consulta])
        SnapToNetwork([Conectar ponto temporário à rede])
        CalculateRoute([Calcular menor tempo com A* temporal])
        BuildItinerary([Gerar itinerário passo a passo])
        ViewRoute([Visualizar trajeto e resumo])

        LoadGTFS([Carregar dados GTFS])
        FilterCalendar([Filtrar calendário de serviço])
        SanitizeData([Higienizar dados de transporte])
        BuildGraph([Construir grafo em memória])
        ValidateGraph([Validar carga e topologia])

        AnalyzeNetwork([Analisar resiliência da rede])
        FindCriticalStations([Identificar estações críticas])
        BenchmarkRouting([Comparar desempenho dos algoritmos])
    end

    Passenger --> ListStations
    Passenger --> SelectPoints
    Passenger --> SearchRoute
    Passenger --> ViewRoute

    SelectMapPoint -.->|«extend»| SelectPoints
    SearchRoute -.->|«include»| ValidateRequest
    SearchRoute -.->|«include»| CalculateRoute
    SnapToNetwork -.->|«extend»| CalculateRoute
    BuildItinerary -.->|«extend»| SearchRoute
    ViewRoute -.->|«extend»| SearchRoute

    DataOperator --> LoadGTFS
    DataOperator --> ValidateGraph
    GTFS --> LoadGTFS
    LoadGTFS -.->|«include»| FilterCalendar
    LoadGTFS -.->|«include»| SanitizeData
    LoadGTFS -.->|«include»| BuildGraph

    NetworkAnalyst --> AnalyzeNetwork
    NetworkAnalyst --> BenchmarkRouting
    AnalyzeNetwork -.->|«include»| FindCriticalStations
```

## Atores

| Ator | Responsabilidade |
|---|---|
| Passageiro | Informa o deslocamento e consulta a melhor rota disponível. |
| Operador de dados | Prepara, carrega e valida a base GTFS usada pelo sistema. |
| Analista da rede | Avalia vulnerabilidades e desempenho do modelo de grafos. |
| Base GTFS | Sistema externo que fornece paradas, linhas, viagens e calendários. |

## Referências do padrão

- [OMG - Unified Modeling Language](https://www.omg.org/UML/what-is-uml.htm)
- [Mermaid - Use case diagrams](https://mermaid.js.org/syntax/usecase.html)
- [GitHub - Diagramas Mermaid em Markdown](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
