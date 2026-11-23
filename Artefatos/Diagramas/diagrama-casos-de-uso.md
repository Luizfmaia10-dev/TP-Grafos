# Diagrama de Casos de Uso - MVP RotasGraph

Capacidades disponíveis, representadas com `flowchart`.

```mermaid
flowchart LR
    Passenger[Passageiro]
    Geocoder[Geoapify / OpenStreetMap]
    Operator[Operador de dados]
    Analyst[Analista da rede]
    GTFS[Arquivos GTFS de Belo Horizonte]
    subgraph Public[Interface e REST]
        Address([Selecionar endereços de Belo Horizonte])
        Limits([Configurar limites A e B entre 100 m e 2 km])
        Candidates([Consultar paradas dentro do limite])
        Origin([Confirmar parada de acesso da origem])
        Destination([Usar parada mais próxima do destino])
        Search([Buscar rota por endereços para HH:MM])
        Validate([Validar endereços, limites, parada de origem e horário])
        Calculate([Calcular menor chegada com A* temporal])
        Itinerary([Montar itinerário com caminhadas])
        View([Visualizar resumo, timeline e mapa])
        Edit([Editar ou cancelar consulta])
        StationREST([Consultar rota por IDs via REST])
    end
    subgraph CLI[Ferramentas por linha de comando]
        Load([Carregar e higienizar GTFS por data])
        Check([Validar grafo e carga])
        Analyze([Analisar topologia com GraphAnalyzer])
        Critical([Listar articulações, CFCs e Top 20])
        Benchmark([Comparar roteamento com NetworkX])
    end
    Passenger --> Address
    Passenger --> Limits
    Passenger --> Origin
    Passenger --> Search
    Passenger --> View
    Passenger --> Edit
    Address --> Geocoder
    Address -.->|inclui| Candidates
    Candidates -.->|origem| Origin
    Candidates -.->|destino| Destination
    Search -.->|inclui| Validate
    Search -.->|inclui| Origin
    Search -.->|inclui| Destination
    Search -.->|inclui| Calculate
    Search -.->|se houver caminho| Itinerary
    StationREST -.->|modo alternativo| Calculate
    Operator --> Load
    Operator --> Check
    GTFS --> Load
    Check -.->|inclui| Load
    Analyst --> Analyze
    Analyst --> Benchmark
    Analyze -.->|inclui| Load
    Analyze -.->|gera| Critical
```

O frontend usa `GET /config/geocoding`, Geoapify/OpenStreetMap e
`POST /snap/candidates`. A origem recomenda a parada mais próxima, mas permite
outra candidata dentro do limite; o destino usa automaticamente a primeira.
Os limites são independentes, aceitam metros inteiros entre 100 e 2.000 e podem
ser salvos antes do endereço.

`POST /routes/search` recebe `mode: "address"`, os dois endereços com
coordenadas e limites, a parada confirmada da origem e `departure_time`. O modo
por `origin_id` e `destination_id` permanece como contrato REST alternativo.
As caminhadas temporárias são removidas ao final da consulta.
A análise usa `python -m app.analyze_topology`, sem endpoint analítico.
Seu ranking mede impacto estrutural, sem inferir demanda. O benchmark existente
não comprova a escalabilidade da campanha ainda pendente.

Consulte [a API](../../docs/API.md), [a CLI](../../docs/GRAPH_ANALYZER.md) e
[o benchmark](../../docs/BENCHMARK.md).

## Referências do padrão

- [OMG - Unified Modeling Language](https://www.omg.org/UML/what-is-uml.htm)
- [Mermaid - Use case diagrams](https://mermaid.js.org/syntax/usecase.html)
- [GitHub - Diagramas Mermaid em Markdown](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
