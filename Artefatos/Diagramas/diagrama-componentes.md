# System Component Architecture Diagram

This document describes the high-level architecture and layered decoupling of the Public Transit Route Optimization system, satisfying academic domain isolation and modularity requirements.

```mermaid
graph TD
    subgraph PresentationLayer["Presentation Layer (Frontend)"]
        UI["Web UI (HTML / Tailwind CSS)"]
        SVGMap["SVG Map & Graph Renderer"]
        Timeline["Itinerary & Steps Timeline"]
        ControllerJS["Client Controller (Vanilla JS)"]
        
        UI --> ControllerJS
        ControllerJS --> SVGMap
        ControllerJS --> Timeline
    end

    subgraph APILayer["API & Controller Layer (FastAPI)"]
        FastAPIServer["FastAPI Application"]
        StationsEndpoint["GET /stations"]
        RouteSearchEndpoint["POST /routes/search"]
        SchemaValidator["Pydantic Schemas & DTOs"]

        FastAPIServer --> StationsEndpoint
        FastAPIServer --> RouteSearchEndpoint
        RouteSearchEndpoint --> SchemaValidator
    end

    subgraph CoreEngineLayer["Core Domain & Graph Engine (In-Memory)"]
        RouteSimulator["RouteSimulator (Time-Dependent A* + bisect)"]
        TransportGraph["TransportGraph (Adjacency List: dict)"]
        GraphAnalyzer["GraphAnalyzer (Articulation Points & SCCs)"]
        TemporaryVertexHandler["TemporaryVertex & Snapping"]
        PriorityQueue["Priority Queue (heapq)"]
        ItineraryModel["Itinerary Model & Serializer (__slots__)"]

        RouteSimulator --> TransportGraph
        RouteSimulator --> PriorityQueue
        RouteSimulator --> TemporaryVertexHandler
        RouteSimulator --> ItineraryModel
        GraphAnalyzer --> TransportGraph
        TemporaryVertexHandler --> TransportGraph
    end

    subgraph IngestionLayer["Data Ingestion Layer"]
        DataLoader["DataLoader (GTFS / CSV Parser)"]
        Sanitizer["Data Sanitizer & Filter"]
        TimeUtils["TimeUtils (HH:MM Conversion)"]

        DataLoader --> Sanitizer
        DataLoader --> TimeUtils
    end

    subgraph StorageLayer["Data Storage (File System)"]
        GTFSFiles["GTFS Raw Datasets (BHTRANS / Kaggle)\n- stops.txt\n- stop_times.txt\n- routes.txt\n- trips.txt"]
    end

    %% Cross-layer interactions
    ControllerJS -- "HTTP / JSON" --> FastAPIServer
    RouteSearchEndpoint --> RouteSimulator
    StationsEndpoint --> TransportGraph
    DataLoader -- "Populates (O(1) insertions)" --> TransportGraph
    DataLoader -- "Reads CSV" --> GTFSFiles

    %% Styling
    classDef presentation fill:#f1f5f9,stroke:#032147,stroke-width:2px;
    classDef api fill:#e0f2fe,stroke:#209dd7,stroke-width:2px;
    classDef core fill:#ede9fe,stroke:#753991,stroke-width:2px;
    classDef ingestion fill:#fef3c7,stroke:#ecad0a,stroke-width:2px;
    classDef storage fill:#fecdd3,stroke:#e11d48,stroke-width:2px;

    class UI,SVGMap,Timeline,ControllerJS presentation;
    class FastAPIServer,StationsEndpoint,RouteSearchEndpoint,SchemaValidator api;
    class RouteSimulator,TransportGraph,GraphAnalyzer,TemporaryVertexHandler,PriorityQueue,ItineraryModel core;
    class DataLoader,Sanitizer,TimeUtils ingestion;
    class GTFSFiles storage;
```

## Architectural Justification & Decoupling

1. **Zero UI Coupling in Graph Core**: The mathematical engine (`TransportGraph`, `RouteSimulator`, `GraphAnalyzer`) has no dependencies on HTTP frameworks, presentation logic, or external graphing libraries like NetworkX.
2. **In-Memory Performance & `__slots__`**: `TransportGraph` relies strictly on native Python dictionary-based adjacency lists, ensuring $O(1)$ vertex lookup and neighbor retrieval, while high-cardinality domain entities (`Station`, `Connection`, `Itinerary`) enforce `__slots__` to eliminate per-instance `__dict__` overhead.
3. **Logarithmic Temporal Lookup**: Connections per station are sorted by departure time, enabling `RouteSimulator` to locate the next available trip in $O(\log K)$ using Python's native `bisect` module.
4. **Network Resilience & Topology Analysis**: `GraphAnalyzer` computes Articulation Points (DFS with `lowpt`) and Strongly Connected Components (Kosaraju/Tarjan) to identify critical transit hubs and structural vulnerabilities for the SBC report.
5. **Pluggable Ingestion**: `DataLoader` isolates file format specifics (GTFS CSVs from BHTRANS or any city). Swapping the data source does not require changing the routing engine.
6. **Admissible Heuristics**: `RouteSimulator` implements Time-Dependent A* with Haversine distance normalized by maximum network velocity ($h(u, v) = \text{haversine}(u, v) / V_{\max}$), ensuring optimality and fast pruning.
