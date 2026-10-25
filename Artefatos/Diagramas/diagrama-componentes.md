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
        RouteSimulator["RouteSimulator (Time-Dependent A*)"]
        TransportGraph["TransportGraph (Adjacency List: dict)"]
        TemporaryVertexHandler["TemporaryVertex & Snapping"]
        PriorityQueue["Priority Queue (heapq)"]
        ItineraryModel["Itinerary Model & Serializer"]

        RouteSimulator --> TransportGraph
        RouteSimulator --> PriorityQueue
        RouteSimulator --> TemporaryVertexHandler
        RouteSimulator --> ItineraryModel
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
    class RouteSimulator,TransportGraph,TemporaryVertexHandler,PriorityQueue,ItineraryModel core;
    class DataLoader,Sanitizer,TimeUtils ingestion;
    class GTFSFiles storage;
```

## Architectural Justification & Decoupling

1. **Zero UI Coupling in Graph Core**: The mathematical engine (`TransportGraph`, `RouteSimulator`) has no dependencies on HTTP frameworks, presentation logic, or external graphing libraries like NetworkX.
2. **In-Memory Performance**: `TransportGraph` relies strictly on native Python dictionary-based adjacency lists, ensuring $O(1)$ vertex lookup and neighbor retrieval.
3. **Pluggable Ingestion**: `DataLoader` isolates file format specifics (GTFS CSVs from BHTRANS or any city). Swapping the data source does not require changing the routing engine.
4. **Admissible Heuristics**: `RouteSimulator` implements Time-Dependent A* with Haversine distance normalized by maximum network velocity ($h(u, v) = \text{haversine}(u, v) / V_{\max}$), ensuring optimality and fast pruning.

