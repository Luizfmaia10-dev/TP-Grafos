# API de transporte

## Carga compartilhada

A API carrega uma rede em memoria na inicializacao, para um dia de servico
GTFS explicito. O grafo, o indice de estacoes por ID e a velocidade maxima
da rede sao reutilizados nas consultas. Reinicie o servidor para trocar a
data ou o dataset. Nao ha carga do GTFS por requisicao.

Na raiz do repositorio, com os TXT completos obtidos via Git LFS:

```powershell
$env:GTFS_SERVICE_DATE = "2026-11-17"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend
```

`GTFS_SERVICE_DATE` usa `YYYY-MM-DD` e representa o dia de servico, inclusive
para horarios acima de 24h. O calendario do feed determina quais viagens
entram no grafo; uma data sem servicos ativos gera uma rede sem viagens.
O diretorio padrao e `data/gtfs/`, resolvido a partir do repositorio.
`GTFS_DIR` permite selecionar outro diretorio.

Sem `GTFS_SERVICE_DATE`, apenas a demonstracao estatica e o `/health`
funcionam; consultas que dependem da rede retornam HTTP 503 com
`{"detail": "Transport network is not configured"}`. Uma data invalida ou
uma falha na leitura de um feed configurado interrompe a inicializacao.
O `/health` indica que a aplicacao responde, nao a disponibilidade da rede.

Os testes usam grafos ou feeds sinteticos e nao dependem do dataset real.

## GET /stations

Retorna uma lista JSON de estacoes para autocomplete, a partir do catalogo
carregado na inicializacao. Nao exige chave de API.

Exemplo: `GET /stations?query=sao%20gabriel&limit=10`

```json
[
  {
    "station_id": "001",
    "name": "Estação São Gabriel",
    "latitude": -19.8801,
    "longitude": -43.9282
  }
]
```

O exemplo e sintetico. IDs sao strings; coordenadas sao graus decimais.

| Parametro | Comportamento |
|---|---|
| `query` | Opcional; busca por trecho do nome ou ID, ignorando maiusculas, acentos e espacos externos |
| `limit` | Inteiro de 1 a 100; padrao 20 |

Sem `query`, ou com texto vazio, retorna as primeiras estacoes ate o limite.
A ordem e a de cadastro no feed. Nomes iguais com IDs distintos permanecem
como sugestoes separadas. A consulta nao filtra as estacoes pela existencia
de viagens ativas ou de um caminho para o destino.

Sem correspondencias, ou com catalogo vazio, retorna HTTP 200 com `[]`.
Limite invalido retorna HTTP 422 no formato de validacao do FastAPI.
Sem rede configurada, retorna HTTP 503 conforme a secao de carga.

A busca percorre o catalogo ate encontrar `limit` resultados ou esgotar as
estacoes: no pior caso, faz O(S) verificacoes de texto para S estacoes.
Acumula apenas os resultados ate o limite, sem copiar nem ordenar o grafo.
O contrato tambem pode ser consultado em `/docs` e `/openapi.json`.

## POST /routes/search

Recebe IDs de estacoes do catalogo e horario no dia de servico carregado:

```json
{
  "origin_id": "001",
  "destination_id": "003",
  "departure_time": "07:59"
}
```

Todos os campos sao obrigatorios. IDs devem ser strings nao vazias; espacos
externos sao removidos. Origem e destino devem ser distintos. O horario usa
somente `HH:MM`, sem segundos, e permite horas acima de 23, como `25:00`.
Internamente, o motor acrescenta segundos zerados sem reduzir a precisao dos
horarios GTFS. Nao enviar data na consulta: `GTFS_SERVICE_DATE` seleciona o
calendario na inicializacao. Campos adicionais sao rejeitados para evitar
que uma data enviada pelo cliente seja ignorada silenciosamente.

Exemplo de resposta HTTP 200 para uma rota direta sintetica:

```json
{
  "status": "found",
  "service_date": "2026-11-17",
  "origin": {
    "station_id": "001", "name": "Central",
    "latitude": -19.9, "longitude": -43.9
  },
  "destination": {
    "station_id": "003", "name": "Terminal",
    "latitude": -19.901, "longitude": -43.901
  },
  "departure_time": "07:59",
  "route": {
    "arrival_time": "08:10:00",
    "total_seconds": 660,
    "waiting_seconds": 60,
    "travel_seconds": 600,
    "distance_km": 0.153,
    "steps": [
      {
        "origin": {
          "station_id": "001", "name": "Central",
          "latitude": -19.9, "longitude": -43.9
        },
        "destination": {
          "station_id": "003", "name": "Terminal",
          "latitude": -19.901, "longitude": -43.901
        },
        "route_id": "bus",
        "vehicle_type": "BUS",
        "departure_time": "08:00:00",
        "arrival_time": "08:10:00",
        "waiting_seconds": 60,
        "travel_seconds": 600,
        "distance_km": 0.153
      }
    ]
  }
}
```

Cada passo corresponde a uma conexao entre duas paradas, na ordem do
caminho. `vehicle_type` usa `BUS`, `SUBWAY` ou `WALK`. Para transporte
agendado, a espera inclui o tempo ate a partida, tambem nas baldeacoes.
Caminhada parte imediatamente na chegada a parada, sem espera; o horario
zero armazenado na conexao WALK nao e apresentado como meia-noite.

`total_seconds` inclui toda a espera e todo o deslocamento;
`travel_seconds` inclui caminhada e transporte. Os horarios absolutos sao
arredondados para o segundo mais proximo com a regra de empate para par do
`TimeUtils`. Duracoes sao diferencas desses horarios, garantindo que
`total_seconds = waiting_seconds + travel_seconds` e que as somas dos passos
coincidam com os totais. Um trecho inferior a um segundo pode aparecer com
duracao zero apos arredondamento. A busca continua usando minutos
fracionarios, sem arredondar durante o A*.

Distancias sao somas em km, sem arredondamento adicional; no GTFS, sao
estimadas por Haversine entre paradas, sem geometria de ruas. `route_id`
identifica a linha internamente, sem representar seu numero comercial.
Nao sao inventados `trip_id`, `service_id` ou nomes ausentes no dominio.

| Situacao | Resposta |
|---|---|
| Caminho encontrado | HTTP 200, `status: "found"` e `route` preenchida |
| Sem caminho, partida perdida ou data carregada sem viagens | HTTP 200, `status: "no-route"` e `route: null`; preserva os demais campos da consulta |
| ID desconhecido | HTTP 404, `{"detail": {"code": "unknown_station", "field": "origin_id"}}` ou `destination_id` |
| Campos ausentes, invalidos, adicionais ou origem igual ao destino | HTTP 422, formato de validacao do FastAPI |
| Rede nao configurada | HTTP 503, conforme a secao de carga |

A API usa `RouteSimulator.calculate_route` com um simulador por consulta e
o grafo compartilhado, sem modificar conexoes ou carregar o feed novamente.
A montagem da resposta fica em `app/api/`, em O(P) para P conexoes no
caminho; o dominio nao depende de FastAPI ou dos modelos HTTP. Esta entrega
nao implementa a classe de dominio `Itinerary`, nem coordenadas arbitrarias.

Para testar pelo PowerShell com o servidor configurado e aberto, substitua
os IDs sinteticos por IDs retornados por `/stations`:

```powershell
$body = @{
    origin_id = "001"
    destination_id = "003"
    departure_time = "07:59"
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/routes/search" -ContentType "application/json" -Body $body
```
