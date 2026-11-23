# Diagrama de Estados - Consulta de Rota

Estados observáveis da consulta pública por endereços. Origem e destino têm
limites independentes e podem ser preenchidos em qualquer ordem.

```mermaid
stateDiagram-v2
    [*] --> Editing
    state "Edição incompleta" as Editing
    state "Buscando endereço" as Geocoding
    state "Consultando paradas no limite" as Snapping
    state "Confirmando parada da origem" as OriginChoice
    state "Limite sem parada alcançável" as Insufficient
    state "Editando limite A ou B" as LimitEditing
    state "Consulta pronta" as Ready
    state "Carregando (loading)" as Loading
    state "Rota encontrada (found)" as Found
    state "Sem rota (no-route)" as NoRoute
    state "Falha da consulta (error)" as Error
    Editing --> Geocoding: digitar e selecionar sugestão
    Geocoding --> Snapping: endereço com coordenadas
    Geocoding --> Editing: vazio, erro ou cancelamento
    Snapping --> OriginChoice: candidatas de nova origem
    Snapping --> Editing: destino conectado à mais próxima
    Snapping --> LimitEditing: limite existente revalidado
    Snapping --> Insufficient: nenhuma parada no limite
    OriginChoice --> Editing: confirmar candidata válida
    OriginChoice --> Geocoding: trocar endereço
    Insufficient --> LimitEditing: aumentar limite
    Insufficient --> Geocoding: trocar endereço
    Editing --> LimitEditing: abrir preferências
    LimitEditing --> Editing: confirmar sem consulta completa
    LimitEditing --> Ready: confirmar com consulta completa
    LimitEditing --> Snapping: validar endereço existente
    Editing --> Ready: origem confirmada, destino conectado e HH:MM válido
    Ready --> Editing: editar endereço ou horário
    Ready --> LimitEditing: alterar limite
    Ready --> Loading: enviar
    Loading --> Found: caminho
    Loading --> NoRoute: sem caminho
    Loading --> Error: falha
    Loading --> Editing: editar e cancelar
    Found --> Editing: editar busca
    NoRoute --> Loading: repetir
    NoRoute --> Editing: ajustar
    Error --> Loading: repetir
    Error --> Editing: corrigir
```

`validateAddressSelection` só libera o envio com endereço e parada confirmada
na origem, endereço e candidata no destino e horário `HH:MM`. O limite varia
por metro entre 100 e 2.000; sem endereço, pode ser salvo sem consultar a API.
Com endereço, a alteração chama `POST /snap/candidates` e bloqueia a confirmação
quando nenhuma parada cabe no raio.

A origem recomenda a candidata mais próxima e permite selecionar outra válida.
O destino escolhe automaticamente a primeira. Durante `loading`, editar cancela
a requisição e descarta respostas antigas. O modo por IDs continua disponível
na API, mas não representa o fluxo principal da interface.

[Referência Mermaid](https://mermaid.js.org/syntax/stateDiagram.html).
