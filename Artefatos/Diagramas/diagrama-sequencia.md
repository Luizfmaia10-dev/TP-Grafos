# Diagramas de Sequência - MVP RotasGraph

As sequências abaixo descrevem a arquitetura-alvo completa. A primeira prepara
o grafo em memória; a segunda executa a consulta principal do passageiro.

## 1. Inicialização e carga do grafo

```mermaid
sequenceDiagram
    autonumber
    actor Operator as Operador de dados
    participant API as FastAPI
    participant Loader as DataLoader
    participant GTFS as Arquivos GTFS
    participant Graph as TransportGraph

    Operator->>API: Inicializar sistema para uma data de serviço
    API->>Loader: build_graph(data_servico)
    Loader->>GTFS: Ler calendário, paradas, linhas e viagens
    GTFS-->>Loader: Registros GTFS

    loop Cada registro e bloco de viagem
        Loader->>Loader: Validar, higienizar e filtrar serviço ativo
        Loader->>Graph: add_station / add_connection
    end

    Loader->>Loader: Consolidar diagnóstico da carga
    Graph-->>Loader: Grafo construído em memória
    Loader-->>API: TransportGraph e relatório da carga
    API-->>Operator: Sistema pronto ou diagnóstico da falha
```

## 2. Busca de rota otimizada

```mermaid
sequenceDiagram
    autonumber
    actor Passenger as Passageiro
    participant UI as Frontend
    participant API as FastAPI
    participant Simulator as RouteSimulator
    participant Graph as TransportGraph
    participant Itinerary as Itinerary

    Passenger->>UI: Informar origem, destino e horário
    opt Autocomplete por estação
        UI->>API: GET /stations?query=texto
        API->>Graph: Consultar estações
        Graph-->>API: Estações correspondentes
        API-->>UI: Lista de estações
    end

    Passenger->>UI: Solicitar rota otimizada
    UI->>API: POST /routes/search
    API->>API: Validar DTO da consulta
    API->>Simulator: find_route(origem, destino, horário)

    opt Origem ou destino é um ponto do mapa
        Simulator->>Graph: Localizar estação real mais próxima
        Graph-->>Simulator: Estação em até 800 m
        Simulator->>Graph: Adicionar TemporaryVertex e aresta WALK
    end

    loop A* temporal até concluir a busca
        Simulator->>Graph: get_neighbors(estação)
        Graph-->>Simulator: Conexões ordenadas por partida
        alt Conexão WALK
            Simulator->>Simulator: Usar conexão imediatamente disponível
        else Conexão BUS ou SUBWAY
            Simulator->>Simulator: Selecionar próxima partida com bisect
        end
        Simulator->>Simulator: Atualizar prioridade com heurística Haversine
    end

    alt Caminho encontrado
        Simulator->>Itinerary: Construir passos, tempos e distâncias
        Itinerary-->>Simulator: Itinerário estruturado
        Simulator->>Graph: Remover vértices temporários
        Simulator-->>API: Itinerary
        API-->>UI: 200 + itinerário JSON
        UI-->>Passenger: Exibir resumo, passos e trajeto no mapa
    else Não existe caminho viável
        Simulator->>Graph: Remover vértices temporários
        Simulator-->>API: Rota inexistente
        API-->>UI: Resposta sem rota viável
        UI-->>Passenger: Orientar ajuste da consulta
    else Falha durante a consulta
        Simulator->>Graph: Remover vértices temporários
        Simulator-->>API: Erro de domínio
        API-->>UI: Erro tratável
        UI-->>Passenger: Exibir mensagem e permitir nova tentativa
    end
```

## Referência do padrão

- [Mermaid - Sequence diagrams](https://mermaid.js.org/syntax/sequenceDiagram)
