# Problema: o grafo mistura todos os calendarios de servico (`service_id`)

Status: aberto. Documento de diagnostico; nenhuma correcao foi implementada.
Data: 16/11/2026.

## 1. Resumo

O `DataLoader` carrega todas as viagens de `trips.txt` em um unico `TransportGraph`,
independentemente do `service_id`. No GTFS, `service_id` define **em quais dias** uma
viagem opera (dias uteis, sabado, domingo, feriados, periodos especiais), por meio dos
arquivos `calendar.txt` e/ou `calendar_dates.txt`. Esses arquivos nao estao no
repositorio e nao sao lidos.

Resultado: para um mesmo horario, o grafo contem partidas de varios tipos de dia ao
mesmo tempo. O roteador pode montar uma rota usando um onibus que so circula no
sabado seguido de outro que so circula em dia util. O roteador vai continuar
correto do ponto de vista matematico, mas o resultado nao corresponde a nenhum dia real.

## 2. Evidencias

### 2.1 O dataset tem 8 calendarios distintos

Contagem de viagens por `service_id` em `data/gtfs/trips.txt`:

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

Os identificadores aparecem em dois grupos (`3076xx` e `4479xx`). Uma hipotese, **ainda nao
confirmada** porque falta o calendario, e que cada grupo corresponda a um periodo de
vigencia diferente, cada um com seus tipos de dia.

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

### 2.3 Os arquivos de calendario nao fazem parte do dataset versionado

`data/gtfs/` contem apenas `routes.txt`, `stops.txt`, `stop_times.txt` e `trips.txt`.
Nao ha `calendar.txt` nem `calendar_dates.txt`.

### 2.4 A limitacao ja estava documentada, mas sem tratamento

- `backend/app/data_loader.py`, docstring de `DataLoader`: "Service calendars and
  pickup/drop-off restrictions are not applied."
- `docs/DATA_LOADER.md`: "Permanecem fora do escopo: calendario por data [...]
  `Connection` ainda nao armazena `trip_id` ou `service_id`; o grafo reune os servicos
  carregados."
- `service_id` e lido apenas para validar que o campo esta preenchido.

## 3. Impacto

| Area | Efeito |
|---|---|
| Correcao do resultado (Parte 5) | Rotas e horarios de chegada que nao existem em nenhum dia real. Tempos de espera subestimados. |
| Itinerario e interface (Partes 6 a 8) | Mostra para o usuario horarios de onibus que podem nao circular no dia escolhido. |
| Memoria e desempenho | As 6.110.036 conexoes incluem todos os calendarios. Carregar so um tipo de dia deve reduzir bastante o grafo, a memoria e o tempo de carga (hoje cerca de 41 s), alem de acelerar o A*. |
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

## 5. Caminho sugerido para a correcao (nao implementado)

1. **Confirmar a fonte:** verificar se o pacote GTFS oficial no
   [Portal de Dados Abertos da PBH](https://ckan.pbh.gov.br/dataset/gtfs) inclui
   `calendar.txt` e/ou `calendar_dates.txt` na mesma versao dos quatro arquivos atuais.
   Se incluir, versionar com Git LFS (ja coberto por `data/gtfs/*.txt`) e atualizar
   `data/gtfs/README.md` e os hashes.
2. **Filtrar na carga, nao no roteador:** o `DataLoader` passa a receber o servico
   desejado (uma data ou um tipo de dia) e ignora as viagens de outros `service_id`.
   Assim, `Connection`, `TransportGraph` e o futuro `RouteSimulator` nao mudam, e o grafo
   fica menor. E a solucao mais simples e mais barata em memoria.
3. **Testes (TDD):** viagens de servico inativo nao geram conexoes; servico ativo gera;
   uma data especifica aplica as excecoes de `calendar_dates.txt`, se o arquivo existir.
4. **Revalidar:** repetir `docs/GTFS_VALIDATION.md` e registrar as novas contagens de
   conexoes, memoria e tempo de carga.
5. **Plano:** itens adicionados em `docs/PLAN.md` (Parte 3), conforme a regra 8 do
   `AGENTS.md`.

Se o calendario oficial **nao** estiver disponivel, nao inferir o tipo de dia por
heuristica sem aprovacao. A alternativa seria escolher manualmente um conjunto de
`service_id` e documentar a escolha, mas isso precisa de decisao da equipe.

## 6. Relacao com a tarefa do A*

`TASK_ASTAR_ROUTING.md` (secao 4.6) registra este problema como limitacao conhecida e
nao depende da correcao. Como a solucao recomendada filtra na carga, o motor de
roteamento nao precisa mudar quando ela for implementada.
