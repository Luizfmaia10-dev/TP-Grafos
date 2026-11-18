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
