# Diagrama de Estados - Consulta de Rota

Esta máquina de estados representa a arquitetura-alvo da consulta principal do
MVP, desde a seleção dos pontos até a apresentação do itinerário. Os vértices
temporários existem somente durante a busca e são removidos antes da resposta.

```mermaid
stateDiagram-v2
    [*] --> AwaitingSelection

    state "Aguardando seleção" as AwaitingSelection
    state "Origem selecionada" as OriginSelected
    state "Consulta pronta" as ReadyToSearch
    state "Validando consulta" as Validating
    state "Conectando pontos à rede" as Snapping
    state "Calculando rota" as Calculating
    state "Montando itinerário" as BuildingItinerary
    state "Limpando vértices temporários" as Cleaning
    state "Exibindo rota" as ShowingRoute
    state "Exibindo ausência de rota" as ShowingNoRoute
    state "Exibindo erro" as ShowingError

    AwaitingSelection --> OriginSelected: selecionar origem
    OriginSelected --> AwaitingSelection: limpar origem
    OriginSelected --> ReadyToSearch: selecionar destino e horário
    ReadyToSearch --> OriginSelected: alterar destino ou horário
    ReadyToSearch --> Validating: solicitar busca

    Validating --> ShowingError: dados inválidos
    Validating --> Snapping: origem ou destino é coordenada
    Validating --> Calculating: origem e destino são estações

    Snapping --> Cleaning: nenhuma estação em até 800 m
    Snapping --> Calculating: arestas WALK criadas

    Calculating --> BuildingItinerary: caminho encontrado
    Calculating --> Cleaning: caminho inexistente
    Calculating --> Cleaning: falha durante a busca
    BuildingItinerary --> Cleaning: itinerário concluído

    Cleaning --> ShowingRoute: itinerário disponível
    Cleaning --> ShowingNoRoute: caminho inexistente
    Cleaning --> ShowingError: falha interna

    ShowingRoute --> AwaitingSelection: iniciar nova busca
    ShowingNoRoute --> ReadyToSearch: ajustar consulta
    ShowingError --> ReadyToSearch: corrigir consulta

    ShowingRoute --> [*]: encerrar
    ShowingNoRoute --> [*]: encerrar
    ShowingError --> [*]: encerrar
```

## Regras representadas

- Uma busca só começa com origem, destino e horário válidos.
- Cliques arbitrários usam `TemporaryVertex` e conexões `WALK` até a estação
  real mais próxima, limitada a 800 metros.
- A busca temporal considera horários de partida e tempo de espera.
- A limpeza acontece antes de qualquer resposta que suceda à criação de
  vértices temporários, inclusive quando ocorre uma exceção.

## Referência do padrão

- [Mermaid - State diagrams](https://mermaid.js.org/syntax/stateDiagram.html)
