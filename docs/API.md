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
