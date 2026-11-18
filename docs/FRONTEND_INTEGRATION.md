# Passagem do frontend #30 para a integracao #32

Revisao: 18/11/2026. Este documento descreve a demonstracao entregue e os
acordos necessarios com a #31 (API) e a #29 (Itinerary). Os exemplos abaixo
sao do frontend atual; ainda nao constituem um contrato HTTP implementado.

## Base da revisao

| Referencia | Estado observado |
|---|---|
| codigo/30-interface-visual, 9b8ca4d | Etapas 1 a 4 commitadas; base local da revisao final |
| Base original da branch, a2434af | Quatro arquivos GTFS, antes da atualizacao de calendario e A* |
| origin/main, b107e234e70665c433d3708a8f3d48d7fbea21f9 | A* e calendario integrados; dataset renovado em 17/11 |

A main foi consultada com fetch em 18/11. Essa consulta atualizou referencias,
sem integrar commits aos arquivos ou ao historico da branch da interface.
Os testes de regressao desta entrega se referem a base local auditada.

Na main observada, o metodo implementado e
[RouteSimulator.calculate_route](https://github.com/Luizfmaia10-dev/TP-Grafos/blob/b107e234e70665c433d3708a8f3d48d7fbea21f9/backend/app/route_simulator.py),
que recebe Station, Station e minutos fracionarios. Retorna uma lista ordenada
de pares (Station de origem, Connection), None para destino inalcancavel e []
para origem igual ao destino. Nao retorna Itinerary nem possui o find_route
que aparece nos diagramas iniciais.

O DataLoader da main aceita service_date ou active_service_ids, mutuamente
exclusivos. Calendar e excecoes por data ja existem nessa revisao; o problema
anterior consta como resolvido em docs/ISSUE_SERVICE_CALENDAR.md da main.
O main.py observado ainda expoe /health e a montagem estatica. Os endpoints
de paradas/rotas e a serializacao Itinerary permanecem pendentes nessa revisao.

Antes de iniciar a #32, alinhar a base que reune a #30 e a main atualizada,
executar a regressao dessa base e obter os seis GTFS completos via Git LFS
conforme data/gtfs/README.md atualizado. A demonstracao usa uma viagem da
base anterior; nao assumir que seus IDs, horarios ou coordenadas foram
revalidados no feed novo ou que operam em qualquer data escolhida.

## Fronteira atual da consulta

validateSelection produz IDs confirmados e horario com segundos:

```json
{
  "originId": "15252270",
  "destinationId": "14787448",
  "departureTime": "07:45:00"
}
```

IDs sao strings, separados do texto mostrado nos campos. Qualquer edicao
do nome invalida seu ID ate nova selecao. HH:MM e normalizado para HH:MM:00;
horas acima de 24 sao mantidas no dia de servico, sem Date ou modulo 24.

searchDemoRoute(query, { signal }) devolve uma Promise. createRouteRequest
cuida de loading, bloqueio de envios repetidos e descarte de respostas antigas,
inclusive quando o servico ignora AbortSignal. Um servico HTTP podera ocupar
essa fronteira depois do acordo do DTO, propagando signal ao fetch.

O retorno local encontrado possui:

| Campo | Significado/unidade atual |
|---|---|
| status | found |
| query | Copia da consulta normalizada |
| routeId, routeShortName | ID e numero de uma unica linha |
| tripId, serviceId | Procedencia da viagem de exemplo |
| boardingTime, arrivalTime | HH:MM:SS do mesmo dia de servico |
| waitingSeconds, vehicleSeconds, totalSeconds | Segundos inteiros, antes do arredondamento visual |
| distanceKm | Soma Haversine em km, aproximada entre paradas |
| stops | Paradas na ordem do trecho com coordenadas, arrivalTime e departureTime |

Para a consulta acima: boardingTime 07:51:00, arrivalTime 08:20:16,
waitingSeconds 360, vehicleSeconds 1756, totalSeconds 2116 e distanceKm
aproximadamente 9.02794. A tela resume 35 min, conserva o total exato no
texto acessivel e mostra segundos nas etapas e no tempo do onibus.

Outros retornos locais sao {status: "no-route", boardingTime} e
{status: "outside-sample"}. O controlador acrescenta idle, loading e error.
outside-sample e uma limitacao da demonstracao, nao um erro do roteador real.

## Acordos com os responsaveis pela API e pelo Itinerary

| Ponto | Encaminhamento para a #32 |
|---|---|
| GET /stations?query=texto | Caminho/query previstos no diagrama. Definir envelope JSON, limite de resultados e comportamento sem correspondencias |
| DTO de Station | O dominio possui station_id, name, latitude e longitude. Definir seus nomes no JSON; manter ID string e coordenadas em graus decimais |
| POST /routes/search | Definir nomes de origem, destino e horario no DTO e mapear a consulta interna acima; enviar a hora normalizada com segundos |
| Data de servico | Tornar explicita a data da carga ou da consulta. Conectar a selecao ao calendario real da main, sem inferir dia a partir do service_id |
| Custos | Declarar unidades no JSON. O dominio usa minutos fracionarios; o frontend atual usa segundos inteiros e km |
| Itinerary | Serializar passos por modal, origem/destino, coordenadas, partida, chegada, espera, duracao e distancia; incluir identificacao da linha quando existir |
| Rota inexistente | Definir uma resposta tratavel e distinta de falha HTTP; None do motor representa ausencia de caminho |
| Origem igual ao destino | O frontend rejeita esse par. [] do motor nao deve ser confundido com None; alinhar validacao tambem na API |
| Erros de entrada | Definir codigo e mensagem para ID desconhecido, formato de hora, data sem servico e ponto fora do raio permitido |

mapName, shortName, label, platform e district sao dados de apresentacao da
amostra. Nao existem todos no Station atual e nao devem se tornar exigencias
do dominio por causa desse prototipo. A interface deve conseguir usar name
quando um metadado opcional nao estiver disponivel.

Connection possui route_id, destination, vehicle_type, travel_time, distance
e departure_time. Nao guarda trip_id, service_id ou o numero comercial da
linha. O Itinerary nao pode inventar esses metadados a partir do caminho.
Alinhar com a ingestao/API o catalogo route_id -> route_short_name e quais
identificadores de viagem serao realmente disponibilizados. O routeId interno
nao deve ser apresentado automaticamente como o numero visivel do onibus.

Para os custos, preferir um DTO com unidades explicitas e uma politica unica
de arredondamento na serializacao. TimeUtils usa o empate para par no segundo
mais proximo; Math.round do JavaScript nao tem a mesma regra de empate.
Nao converter minutos para segundos com floor, nem arredondar cada valor em
camadas diferentes. A equipe deve garantir coerencia entre os horarios dos
passos, a soma das duracoes e o total apresentado. O arredondamento em minutos
do cartao de resumo e apenas visual.
No resultado multimodal, o total deve incluir tambem a caminhada; a barra
atual com apenas espera/onibus precisara representar os novos componentes.

A montagem do Itinerary deve considerar a disponibilidade dos modais:
BUS/SUBWAY usam departure_time agendado e espera a partir da chegada anterior;
WALK parte imediatamente no horario corrente, com espera zero. O valor 0.0
da Connection WALK e uma convencao do motor, nao um embarque a meia-noite.
VehicleType usa os valores BUS, SUBWAY e WALK. A resposta deve identificar
cada trecho para que a interface use as cores do AGENTS.md e instrucoes reais.

## O que precisa mudar no frontend

Trocar somente searchDemoRoute por fetch nao conclui a integracao:

| Arquivo | Trabalho necessario |
|---|---|
| js/selection.js | Retirar a validacao e a busca presas a DEMO_STATIONS; validar IDs contra o catalogo recebido, preservando invalidacao por edicao |
| js/app.js | Alimentar mapa/sugestoes com as paradas reais, tratar suas consultas assincronas e definir a apresentacao dos modos real e demonstrativo |
| js/route-request.js | Preservar cancelamento e versao; mapear respostas de dominio e falhas HTTP sem perder os campos |
| Novo adaptador HTTP | Chamar os endpoints relativos, verificar response.ok e converter o DTO acordado para a apresentacao |
| js/route-view.js | Renderizar passos do Itinerary, baldeacoes e WALK/SUBWAY; hoje ha textos fixos de onibus e sentido Centro |
| js/map.js e styles/app.css | Generalizar o catalogo criado no inicio, limites do mapa e offsets especificos dos tres IDs; desenhar os trechos/modais recebidos |
| js/demo-data.js e js/demo-service.js | Manter identificados como exemplo, sem usar a viagem fixa para preencher uma falha da API real |

As coordenadas arbitrarias dependem da exposicao do snap_to_network pela API.
Hoje apenas os botoes das tres paradas selecionam pontos. O frontend nao deve
duplicar a criacao ou a limpeza de vertices temporarios do dominio.

A busca de sugestoes precisara descartar respostas de textos antigos, alem
do cancelamento de rotas ja existente. Preservar as interacoes de combobox,
labels, foco, descricoes de erro e o mesmo estado no desktop/celular.

## Montagem das rotas e tratamento de erros

Registrar os endpoints ou include_router antes de app.mount("/", ...), pois
a montagem estatica captura caminhos sob a raiz. /health segue essa ordem
no main.py atual. A interface servida pelo mesmo FastAPI pode usar caminhos
relativos, como /stations e /routes/search.

| Situacao | Comportamento esperado na interface |
|---|---|
| Carregamento | Indicador e bloqueio de envio simultaneo; consulta pode ser editada para cancelar |
| Sucesso | Resumo, horarios e geometria exclusivamente da resposta atual |
| Sem caminho no horario/data | Orientacao para ajustar a busca; sem reaproveitar o trajeto anterior |
| ID/hora/data/ponto invalidos | Mensagem tratavel junto ao campo ou ao mapa, preservando o restante da consulta |
| Falha de rede, HTTP ou JSON | Mensagem de falha e nova tentativa; nao apresentar como ausencia de caminho |
| Resposta de consulta antiga | Ignorar, mesmo que o cancelamento nao tenha interrompido o servidor |

Definir os codigos HTTP e o envelope de erro com a #31. O diagrama preve 200
com itinerario em caso de sucesso; o formato de ausencia de rota ainda deve
ser acordado. Nao transformar toda resposta nao-200 em sem caminho, nem
repassar uma excecao interna do Python como texto de produto.

## Criterios de aceite da #32

- Sugestoes reais confirmam IDs; vazio, texto antigo e ID desconhecido sao tratados.
- Rota real corresponde a origem, destino, horario e data de servico informados.
- Espera, duracoes e chegada permanecem coerentes, incluindo segundos e horas acima de 24.
- WALK, BUS e SUBWAY aparecem com tempos, instrucoes e cores apropriados quando presentes.
- Sem caminho, entrada invalida e indisponibilidade da API produzem respostas distintas.
- Edicao durante carregamento descarta a resposta anterior sem apagar a selecao nova.
- Paradas fora da amostra e pontos temporarios usam dados da API, sem depender dos tres IDs fixos.
- Teclado, toque, foco e leitura responsiva continuam funcionando.
- npm test, npm run check:server, regressao Python e verificacao no navegador passam na base integrada.

Os comandos de execucao e testes estao em [frontend/README.md](../frontend/README.md).
O historico e os limites da #30 estao em [FRONTEND_PLAN.md](FRONTEND_PLAN.md).
