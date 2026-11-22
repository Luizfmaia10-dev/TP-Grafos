# Diagrama de Casos de Uso - MVP RotasGraph

Capacidades disponíveis, representadas com `flowchart`.

```mermaid
flowchart LR
    Passenger[Passageiro]
    Operator[Operador de dados]
    Analyst[Analista da rede]
    GTFS[Arquivos GTFS de Belo Horizonte]
    subgraph Public[Interface e REST]
        Stations([Consultar estações])
        Selection([Selecionar paradas por nome ou marcador])
        Search([Buscar rota para HH:MM])
        Validate([Validar IDs distintos e horário])
        Calculate([Calcular menor chegada com A* temporal])
        Itinerary([Montar itinerário na API])
        View([Visualizar resumo, timeline e mapa])
        Edit([Editar ou cancelar consulta])
    end
    subgraph CLI[Ferramentas por linha de comando]
        Load([Carregar e higienizar GTFS por data])
        Check([Validar grafo e carga])
        Analyze([Analisar topologia com GraphAnalyzer])
        Critical([Listar articulações, CFCs e Top 20])
        Benchmark([Comparar roteamento com NetworkX])
    end
    Passenger --> Stations
    Passenger --> Selection
    Passenger --> Search
    Passenger --> View
    Passenger --> Edit
    Search -.->|inclui| Validate
    Search -.->|inclui| Calculate
    Search -.->|se houver caminho| Itinerary
    Operator --> Load
    Operator --> Check
    GTFS --> Load
    Check -.->|inclui| Load
    Analyst --> Analyze
    Analyst --> Benchmark
    Analyze -.->|inclui| Load
    Analyze -.->|gera| Critical
```

O REST expõe `GET /stations`, `POST /routes/search` e `GET /health`, além dos
recursos estáticos e documentação FastAPI. A busca recebe apenas `origin_id`,
`destination_id` e `departure_time`; marcadores escolhem estações cadastradas.

`snap_to_network` é interno, sem caso de uso público de coordenadas arbitrárias.
A análise usa `python -m app.analyze_topology`, sem endpoint analítico.
Seu ranking mede impacto estrutural, sem inferir demanda. O benchmark existente
não comprova a escalabilidade da campanha ainda pendente.

Consulte [a API](../../docs/API.md), [a CLI](../../docs/GRAPH_ANALYZER.md) e
[o benchmark](../../docs/BENCHMARK.md).

## Referências do padrão

- [OMG - Unified Modeling Language](https://www.omg.org/UML/what-is-uml.htm)
- [Mermaid - Use case diagrams](https://mermaid.js.org/syntax/usecase.html)
- [GitHub - Diagramas Mermaid em Markdown](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
