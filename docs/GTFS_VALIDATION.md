# Validação manual do carregamento GTFS

## Preparar os arquivos

Os quatro TXT são versionados com Git LFS. Instale e inicialize a ferramenta
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
python3 -m app.validate_gtfs ../data/gtfs --output ../data/cache/gtfs-validation.json
```

O comando utiliza a biblioteca padrão e carrega o grafo na RAM. Após verificar
todas as conexões, salva o diagnóstico JSON e mostra `Validação aprovada.` quando
todas as verificações passam. O grafo é liberado ao encerrar o processo.
O arquivo de saída fica no diretório de cache, ignorado pelo Git.

No resultado, confira `passed: true` e todos os valores de `checks` como `true`.
O comando verifica contagens, destinos cadastrados, pesos finitos e não negativos
e ordenação dos horários. `load_report` discrimina aceitação, rejeição e alertas;
`metrics` informa tempo e pico de RAM do processo.

## Referência da versão inicial

Para os arquivos com os hashes registrados no README do dataset:

| Medida | Resultado |
|---|---:|
| Estações | 9.659 |
| Viagens carregadas | 107.621 |
| Conexões | 6.110.036 |
| Viagens em quarentena por tempo zero | 51 |
| Registros de horários rejeitados | 3.350 |
| Alertas de velocidade acima de 120 km/h | 414 |

A execução anterior à migração registrou 40,893 segundos de carga e pico de
598,641 MiB de RAM do processo. São resultados históricos de uma máquina local;
tempo e memória variam. A migração preserva os CSVs byte a byte. Uma versão nova
do GTFS pode alterar os números acima e exige nova avaliação.

## Testes automatizados

Com as dependências de `backend/requirements.txt` instaladas, a partir de `backend/`:

```sh
python -m pytest
```

Os testes usam arquivos temporários sintéticos, sem depender de download por LFS.
Para executar apenas os testes de ingestão e validação:

```sh
python -m pytest tests/test_data_loader.py tests/test_validate_gtfs.py -v
```

O LFS prepara os arquivos; o `DataLoader` continua lendo CSVs locais normalmente.
Regras de higienização e limites de calendário e embarque estão em [DATA_LOADER.md](DATA_LOADER.md).
