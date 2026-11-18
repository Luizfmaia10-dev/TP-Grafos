# Validação manual do carregamento GTFS

## Preparar os arquivos

Os seis TXT são versionados com Git LFS. Instale e inicialize a ferramenta
conforme [o guia do dataset](../data/gtfs/README.md). Na raiz, execute:

```sh
git lfs pull
git lfs fsck
```

Se os objetos estiverem no cache local, `git lfs checkout` restaura os CSVs sem
download. Os arquivos devem conter os dados completos, não ponteiros iniciados
por `version https://git-lfs.github.com/spec/v1`.

## Executar a validação

A partir de `backend/`, com Python 3.11 ou superior em Linux/macOS:

```sh
python3 -m app.validate_gtfs ../data/gtfs --date 2026-11-17 \
  --output ../data/cache/gtfs-validation.json
```

O comando utiliza a biblioteca padrão e carrega o grafo na RAM. Após verificar
todas as conexões, salva o diagnóstico JSON e mostra `Validação aprovada.` quando
todas as verificações passam. O grafo é liberado ao encerrar o processo.
O arquivo de saída fica no diretório de cache, ignorado pelo Git.

No resultado, confira `passed: true` e todos os valores de `checks` como `true`.
O comando verifica contagens, destinos cadastrados, pesos finitos e não negativos
e ordenação dos horários. `load_report` discrimina aceitação, rejeição e alertas;
`metrics` informa tempo e pico de RAM do processo.
O campo `load_report.service_date` registra o dia de serviço, e
`load_report.active_service_ids` registra os serviços efetivamente selecionados.
Os hashes em `source_sha256` incluem os calendários existentes quando a seleção
é por data. As contagens em `load_report.files` referem-se aos quatro arquivos
principais; erros de calendário interrompem a carga com uma mensagem explícita.

Para conferir um sábado ou uma exceção real de Carnaval:

```sh
python3 -m app.validate_gtfs ../data/gtfs --date 2026-11-21 \
  --output ../data/cache/gtfs-2026-11-21.json
python3 -m app.validate_gtfs ../data/gtfs --date 2026-02-17 \
  --output ../data/cache/gtfs-2026-02-17.json
```

Os comandos não alteram os CSVs e devem ser executados separadamente para medir o
pico de memória de cada processo. A data é do dia de serviço GTFS; horários acima
de 24h não são convertidos em serviços de outro dia.

A alternativa `--service-id` repetível continua disponível. Ela não pode ser usada
junto com `--date`. Datas sem operação produzem um grafo sem conexões, sem inventar
serviços. A ausência dos dois calendários é um erro quando uma data é solicitada.

Se usar `--audit`, a comparação continua exigindo os hashes e contagens dos quatro
arquivos principais da referência. Com data ou seleção manual, a comparação da
quarentena global fica `null`, pois não corresponde ao subconjunto selecionado.
Os hashes dos calendários são registrados, mas não comparados a essa auditoria antiga.

## Resultados do pacote completo com calendário

| Data de serviço | Serviços ativos | Viagens | Conexões | Carga (s) | Pico do processo (MiB) |
|---|---|---:|---:|---:|---:|
| 2026-11-17 | 307679, 307682 | 25.956 | 1.458.808 | 25,494 | 215,520 |
| 2026-11-21 | 307681, 307684 | 15.436 | 881.502 | 22,438 | 165,797 |
| 2026-02-17 | 447982, 447986 | 11.521 | 692.577 | 21,557 | 150,738 |

Todas as verificações passaram. Cada carga manteve 9.925 estações. Os serviços
convencionais e suplementares foram selecionados juntos para cada data. Os JSONs
locais detalhados estão em `data/cache/`; essa pasta é ignorada pelo Git.

## Referência histórica da versão anterior com seleção manual

Para os arquivos cujos hashes estão na seção histórica do README do dataset:

| Medida | Resultado |
|---|---:|
| Estações | 9.659 |
| Viagens carregadas | 24.363 |
| Conexões | 1.336.540 |
| Registros ignorados por serviço inativo | 4.854.964 |
| Registros rejeitados por tempo zero | 2.106 |
| Registros em viagens com embarque/desembarque restrito | 3.034 |
| Alertas de velocidade acima de 120 km/h | 49 |

A execução do serviço `307679` registrou 123,999 segundos de carga e pico de
205,293 MiB de RAM do processo. São resultados de uma máquina local; tempo e
memória variam. Uma versão nova do GTFS pode alterar os números acima e exige
nova avaliação.

## Testes automatizados

Com as dependências de `backend/requirements.txt` instaladas, a partir de `backend/`:

```sh
python -m pytest
```

Os testes usam arquivos temporários sintéticos, sem depender de download por LFS.
Para executar apenas os testes de ingestão e validação:

```sh
python -m pytest tests/test_service_calendar.py tests/test_data_loader.py tests/test_validate_gtfs.py -v
```

O LFS prepara os arquivos; o `DataLoader` continua lendo CSVs locais normalmente.
Regras de higienização, semântica da data e limites de embarque estão em [DATA_LOADER.md](DATA_LOADER.md).
