# Problema: o grafo mistura todos os calendarios de servico (`service_id`)

Status: resolvido em 17/11/2026. A carga por data resolve o calendario semanal e
as excecoes; a selecao manual permanece como alternativa explicita.
Data: 16/11/2026.

## 1. Resumo

Antes da mitigacao, o `DataLoader` carregava todas as viagens de `trips.txt` em um
unico `TransportGraph`, independentemente do `service_id`. No GTFS, `service_id`
define **em quais dias** uma
viagem opera (dias uteis, sabado, domingo, feriados, periodos especiais), por meio dos
arquivos `calendar.txt` e/ou `calendar_dates.txt`. Inicialmente esses arquivos nao
estavam no repositorio. Foram adicionados em 17/11/2026 com a atualizacao completa
do dataset e agora sao lidos quando `service_date` e informado.

O resultado anterior continha, para um mesmo horario, partidas de varios tipos de dia ao
mesmo tempo. O roteador pode montar uma rota usando um onibus que so circula no
sabado seguido de outro que so circula em dia util. O roteador vai continuar
correto do ponto de vista matematico, mas o resultado nao corresponde a nenhum dia real.

Desde 17/11/2026, feeds com mais de um servico exigem `service_date` ou
`active_service_ids`. A opcao `--date` aplica o calendario e suas excecoes. O comando
de validacao aceita `--service-id` repetivel, e blocos de servicos nao selecionados
sao ignorados com `inactive_service`. Selecoes vazias ou inexistentes falham antes da
construcao do grafo.

## 2. Evidencias

### 2.1 O dataset inicial tinha 8 servicos distintos

Contagem historica por `service_id` no `trips.txt` anterior a atualizacao completa:

| `service_id` | Viagens |
|---|---:|
| 307679 | 24.503 |
| 447983 | 20.491 |
| 307681 | 14.458 |
| 447985 | 14.334 |
| 447984 | 12.805 |
| 447982 | 11.280 |
| 307680 | 9.788 |
| 447986 | 13 |
| **Total** | **107.672** |

A hipotese inicial sobre periodos diferentes nao foi usada para inferir servicos.
Os calendarios obtidos depois identificaram servicos semanais em `3076xx` e
servicos especiais de Carnaval em `4479xx`, incluindo convencional e suplementar.

### 2.2 Uma mesma linha aparece com 7 calendarios

Linha `route_id = 561787` (PC1 - Barreiro):

| `service_id` | Viagens |
|---|---:|
| 307679 | 51 |
| 447983 | 47 |
| 307681 | 39 |
| 447984 | 39 |
| 447985 | 39 |
| 307680 | 24 |
| 447982 | 24 |
| **Total no grafo** | **263** |

Em qualquer dia real, so uma parte dessas viagens opera. No grafo, as 263 estao
disponiveis ao mesmo tempo, o que diminui artificialmente o tempo de espera.

### 2.3 Ausencia inicial dos calendarios e atualizacao do dataset

Antes da atualizacao, `data/gtfs/` continha apenas `routes.txt`, `stops.txt`,
`stop_times.txt` e `trips.txt`, sem os arquivos de calendario.

Em 17/11/2026, o pacote da URL oficial continha ambos os calendarios, mas seus quatro
arquivos principais tinham hashes diferentes dos versionados. Uma comparacao encontrou
horarios distintos para o mesmo `trip_id`; por isso os calendarios atuais nao foram
misturados com a versao local.

Posteriormente, em 17/11/2026, os quatro arquivos principais foram substituidos
pelos do ZIP completo oficial, e os dois calendarios foram extraidos desse mesmo
pacote. O dataset agora abrange o sistema convencional e o suplementar, com
326 linhas, 14 servicos e 67 excecoes. A origem e os hashes atuais estao em
`data/gtfs/README.md`. O padrao LFS existente cobre os seis TXT.
A leitura automatica dos calendarios e a revalidacao foram concluidas. As medicoes
anteriores continuam sendo referencias historicas do dataset antigo.

### 2.4 Tratamento aplicado

- `backend/app/data_loader.py` preserva `service_id` durante a carga e filtra as
  viagens pelos IDs ativos antes de criar conexoes.
- `backend/app/service_calendar.py` resolve vigencia, dias da semana e excecoes por data.
- `backend/app/validate_gtfs.py` expoe `--date` e a alternativa repetivel `--service-id`,
  mutuamente exclusivas. O diagnostico registra a data e os IDs selecionados.
- `docs/DATA_LOADER.md` documenta a selecao obrigatoria e a quarentena conservadora
  de restricoes de embarque e desembarque.

## 3. Impacto historico antes da correcao

| Area | Efeito |
|---|---|
| Correcao do resultado (Parte 5) | Rotas e horarios de chegada que nao existem em nenhum dia real. Tempos de espera subestimados. |
| Itinerario e interface (Partes 6 a 8) | Mostra para o usuario horarios de onibus que podem nao circular no dia escolhido. |
| Memoria e desempenho | O servico `307679` reduziu o grafo de 6.110.036 para 1.336.540 conexoes e o pico observado de 598,641 para 205,293 MiB. A carga ainda percorre todas as linhas e levou 123,999 s contra 40,893 s historicos; ambientes e versoes diferem, portanto isso nao comprova regressao nem ganho de tempo. |
| Benchmark e relatorio (Partes 9 e 10) | Medicoes de complexidade e de tempo de rota feitas sobre um grafo inflado e semanticamente incorreto. |

## 4. Em que tarefa isso deveria ter sido tratado

**Parte 3 - Ingestao de Dados**, em dois itens do `docs/PLAN.md`:

1. "Obter e organizar o dataset de transporte publico de Belo Horizonte (BHTRANS / GTFS)
   no diretorio `data/` [...]": o calendario deveria ter vindo junto com o dataset.
2. "Implementar a classe `DataLoader` para leitura dos arquivos CSV/GTFS (`stops.txt`,
   `stop_times.txt`, `routes.txt`, `trips.txt`)": o carregador deveria filtrar as viagens
   pelo calendario ativo.

Autor desses itens: **Joaquim Antonio** (commits `f40374c`, `e50455c` e `9d437c8`, de 12/11/2026).

**Observacao:** a falha tambem e do plano. O texto do item lista explicitamente apenas os
quatro arquivos e nao menciona calendario. Joaquim seguiu o plano e documentou a
limitacao. A correcao deve ser tratada como lacuna do planejamento atribuida ao dono do
modulo, nao como erro de implementacao.

## 5. Resolucao e revalidacao concluidas

- Os seis TXT foram extraidos do mesmo ZIP completo e estao cobertos pelo LFS.
- O carregador aplica a vigencia inclusiva e o dia da semana de `calendar.txt`,
  depois as adicoes (tipo 1) e remocoes (tipo 2) de `calendar_dates.txt`.
- Sem calendario nao ha inferencia; com data sem servico nao sao criadas conexoes.
- Testes TDD cobrem servico ativo/inativo, excecoes, limites de vigencia,
  calendarios ausentes ou invalidos, selecao manual e interface de linha de comando.
- As cargas reais de 17/11/2026, 21/11/2026 e 17/02/2026 foram aprovadas.
  Contagens, memoria e tempos estao em `docs/DATA_LOADER.md` e `docs/GTFS_VALIDATION.md`.
- Os itens correspondentes da Parte 3 de `docs/PLAN.md` foram marcados como concluidos.

`Connection`, `TransportGraph` e `RouteSimulator` nao precisaram ser alterados.
A data informada e o dia de servico GTFS, e nao uma agregacao de dias vizinhos.
A opcao manual continua exigindo escolha consciente dos IDs, sem rotular dias
por heuristica. A quarentena conservadora de embarque/desembarque permanece.

## 6. Relacao com a tarefa do A*

`TASK_ASTAR_ROUTING.md` (secao 4.6) registra este problema como limitacao conhecida e
nao depende da correcao. Como a solucao recomendada filtra na carga, o motor de
roteamento nao precisa mudar quando ela for implementada.
