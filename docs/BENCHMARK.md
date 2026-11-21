# Benchmark de roteamento

Compara o A* dependente do tempo do projeto com Dijkstra do NetworkX sobre uma
expansão temporal equivalente. Há vértices por estação/horário, arestas de viagem
e de espera. A referência usa
[`single_source_dijkstra`](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.weighted.single_source_dijkstra.html).
NetworkX permanece exclusivo de `backend/benchmarks/`.

## Executar

Requer Python 3.11+ e `backend/requirements.txt`, incluindo `psutil`. A implementação
usa APIs portáveis para Linux, Windows e macOS; foi validada no Windows 11 nesta
entrega, além da execução Linux histórica abaixo. Não há workflows de validação configurados. Obtenha os TXT completos com
Git LFS conforme `data/gtfs/README.md`. A partir de `backend/`, use o mesmo comando
em Bash, PowerShell ou CMD:

```sh
python -m benchmarks.run --data-dir ../data/gtfs --service-date 2026-11-17 --queries ../docs/benchmarks/queries.json --repetitions 7 --warmups 2 --timeout 600 --memory-limit-mib 4096 --output ../data/cache/benchmark
```

Use o Python do ambiente instalado; no PowerShell deste repositório, substitua
`python` por `../.venv/Scripts/python.exe`. As oito dependências diretas estão
fixadas em `backend/requirements.txt`; dependências transitivas não têm lockfile.

O manifesto incluído tem oito pares reais distintos, com semente 42. Cada entrada
contém `id` único, IDs string em `origin`/`destination` e `departure`
em `HH:MM:SS`, aceitando horários acima de 24h. O calendário é selecionado pela data.
Ponteiros LFS são rejeitados antes da ingestão. A CLI também aceita a lista simples
de consultas usada nas execuções históricas.

### Gerar e conferir o manifesto

```sh
python -m benchmarks.queries --data-dir ../data/gtfs --service-date 2026-11-17 --output ../docs/benchmarks/queries.json
python -m benchmarks.queries --data-dir ../data/gtfs --service-date 2026-11-17 --output ../docs/benchmarks/queries.json --check
```

A seleção amostra pares ordenados distintos a partir dos IDs ordenados, com
`random.Random(42)`, até preencher uma consulta alcançável por faixa/horário e
dois casos sem rota. Faixas Haversine: curta `<2 km`, média `2–<8 km` e longa
`>=8 km`; horários `07:00` e `14:00`. Um par aceito ocupa somente um caso. Há
limite explícito de 10.000 candidatos distintos e erro se faltarem estratos.
O manifesto registra hashes, serviços ativos, distância, índice do candidato e
chegada calculada pelo A* no grafo completo. A referência NetworkX é verificada
pela campanha, não presumida pela seleção. Os dois casos sem rota encontrados
neste feed são das 07:00. Essa seleção descritiva não é uma amostra estatística
representativa da cidade.

Antes de iniciar workers, a campanha confere `selection.service_date`, `seed` e
os hashes dos arquivos GTFS contra suas entradas atuais. Incompatibilidades
produzem relatório incompleto com diagnóstico. A procedência é preservada em
`results.json`; manifestos antigos em lista simples continuam aceitos sem essa
evidência adicional.

### Executar a matriz

```sh
python -m benchmarks.campaign --data-dir ../data/gtfs --service-date 2026-11-17 --queries ../docs/benchmarks/queries.json --output ../docs/benchmarks/campaign
```

A matriz executa `100`, `1000` e `full`, com sete repetições, dois aquecimentos,
semente 42, limite amostrado de 4.096 MiB e 600 s por processo. Cada tamanho tem
18 processos: um de tempo e oito de memória por motor. Há reingestão completa
em cada processo; a duração total pode superar meia hora nesta máquina.
Um tamanho interrompido por timeout ou memória preserva seus arquivos e a matriz
continua no tamanho seguinte após encerrar e recolher o worker.

`campaign.json` indica o estado de cada tamanho concluído; cada diretório contém
`results.json`, `measurements.csv`, `summary.csv` e checkpoints por execução/worker.
O JSON consolidado é atualizado após cada worker; checkpoints atômicos são
gravados nas fases e após cada amostra cronometrada, fora do temporizador da consulta.
Uma falha incorpora o último checkpoint ao relatório, com etapa, amostras já
concluídas, causa, limite de tamanho e RSS observada. Checkpoints antigos são
isolados por identificador de execução, evitando sua reutilização em falhas novas.

`--timeout` limita cada processo em segundos; `--memory-limit-mib` encerra o worker
quando a soma das RSS dos processos do worker ultrapassa o limite. Não é um teto rígido: pode haver excesso
entre amostragens. Esse limite de RSS substitui o antigo limite de espaço virtual
com `RLIMIT_AS`. Falhas produzem
`status: incomplete`, diagnóstico e saída não zero. Não há resumo comparativo
quando ocorrer falha ou divergência. Amostras brutas parciais são preservadas;
`equivalence.status` só vale `verified` quando ambos os motores forneceram
respostas concordantes para todos os casos, mesmo se um outro worker falhar.
Qualquer divergência posterior muda o estado para `failed` e invalida a confirmação
anterior; nenhum resumo comparativo é publicado.
Use um diretório de saída por experimento:
os arquivos CSV/JSON são substituídos a cada execução.

## Métricas

Os motores executam sequencialmente em processos independentes. Um processo por
motor mede tempo após aquecimento, reutilizando a rede. Processos adicionais,
um por motor e consulta, medem RAM sem consultas anteriores. Cada processo repete
a ingestão; manifestos grandes podem tornar o experimento demorado.

`measurements.csv` registra durações em nanossegundos e memória em bytes:

| Fase | Conteúdo |
|---|---|
| `load` | `DataLoader.build_graph` |
| `selection` | Seleção opcional de subgrafo induzido |
| `prepare` | Velocidade máxima nativa ou importação/construção NetworkX |
| `prepared` | RSS do worker após liberar a referência local ao grafo de conversão e executar a coleta de lixo; não possui duração própria |
| `query_prepare` | Fonte, sumidouro e arestas auxiliares NetworkX |
| `search` | Busca e reconstrução dos trechos de transporte |
| `cleanup` | Remoção dos nós auxiliares NetworkX |
| `query_total` | Preparação, busca e limpeza da consulta |

No motor próprio, a chamada inteira de `calculate_route` corresponde a `search`;
preparação/limpeza por consulta valem zero. No NetworkX, `query_total` é medido
internamente ao adaptador. Validação, exportação e impressão ficam fora da busca.
A coleta de lixo permanece habilitada nos dois motores.

RSS atual vem de `psutil.Process().memory_info().rss`, em bytes, disponível em
[Linux, Windows e macOS](https://psutil.readthedocs.io/stable/#psutil.Process.memory_info).
O controlador amostra a árvore do worker aproximadamente a cada 10 ms e registra
`sampled_peak_rss_bytes` e `memory_sample_count`. Esse máximo observado pode perder
picos breves; não representa o pico exato fornecido pelo sistema operacional.
O intervalo efetivo pode ser maior devido ao escalonamento do sistema.

No Windows, o executável do ambiente virtual pode ser um launcher com outro Python
filho. Por isso cada amostra soma a RSS do processo raiz e dos descendentes,
contando cada PID uma única vez (`metadata.sampled_rss_scope`). A soma inclui os
launchers e pode contabilizar páginas compartilhadas em mais de um processo;
não mede RAM física exclusiva. Snapshots internos continuam medindo apenas o
Python que executa o motor. Em timeout ou excesso de memória, os descendentes
são encerrados antes do processo raiz para permitir sua coleta pelos launchers.

Sem limite de RAM, processos de tempo não são amostrados: seu pico vale `null` no
JSON e fica vazio no CSV. Com limite de RAM, também são monitorados, com possível
interferência no tempo medido. Para medições finais de tempo, prefira executar sem
limite de RAM. Os snapshots de RSS dentro do worker ficam fora do cronômetro de busca.

RSS mede o processo, não o tamanho exato das
estruturas. O JSON registra snapshots antes/depois das fases e após liberar o grafo
nativo no worker NetworkX. O CSV expõe esse último snapshot na fase `prepared`;
`prepare` continua representando o instante imediatamente posterior à construção.
O pico amostrado pode incluir as duas representações;
o alocador pode reter memória após liberar objetos. O motor próprio mantém seu
grafo nativo, necessário às consultas.

Cada amostra registra memória após a busca, antes da validação. O pico observado
abrange toda a execução do worker, incluindo inicialização, ingestão, validação,
armazenamento de caminhos/amostras, checkpoints e serialização. No CSV, o mesmo pico do worker
é repetido nas linhas de suas fases; não é um pico individual de cada fase.
Picos são cumulativos: não subtrair para obter memória exclusiva da busca.

`results.json` contém caminhos, chegada absoluta em minutos, contagens das duas
representações, serviços ativos, hashes das entradas e manifesto, versões, CPU,
memória disponível/total do sistema, commit e alterações locais. `schema_version: 3`
identifica a medição portátil com RSS preparada explícita e resumos de custo completo;
método, intervalo e tipo do limite são registrados.
O resumo por caso/motor, também exportado em `summary.csv`, inclui mediana, mínimo, máximo e intervalo interquartil
para `query_total` e `search`. `query_total` é a comparação principal entre motores,
pois inclui todo o trabalho necessário por consulta; `search` serve para decompor a
busca interna. As amostras brutas,
incluindo valores extremos e custos completos, permanecem no CSV.

## Corretude e limites

Os caminhos devem ser contíguos, respeitar os horários e alcançar o destino.
A chegada ótima deve coincidir entre execuções com tolerância absoluta de `1e-7`
minuto; ausência de rota também deve coincidir. Caminhos empatados podem diferir.
Eventos de mesmo instante são unificados. Conexões paralelas entre os mesmos
eventos têm custo igual, preservando uma conexão representativa. São aceitos
tempos de viagem zero. `WALK` é rejeitado: eventos agendados não representam
caminhada arbitrária sob demanda.

A comparação envolve implementações e representações diferentes. A expansão pode
superar muito a rede original; não atribuir ganhos exclusivamente a A* versus
Dijkstra. Apresentar custos de preparação e ingestão junto dos tempos de busca.

## Escalabilidade

Para começar pequeno, acrescente `--station-limit 100 --seed 42`. Repita com
limites crescentes e saídas distintas. Os subconjuntos são aninhados para a mesma
semente e manifesto: os extremos de todas as consultas são preservados, e as
demais estações são sorteadas a partir dos IDs ordenados. Mantêm-se apenas
conexões com ambos os extremos selecionados. Contagens efetivas ficam no JSON.
O feed completo ainda é carregado antes da seleção; o pico inclui essa ingestão.

Subgrafos induzidos podem quebrar rotas e não representam redes reais menores.
Manter o manifesto fixo e informar alcançabilidade separadamente. Para estudar
distância, preparar pares curtos, médios e longos por Haversine, em pico e fora de
pico. Distância geográfica não mede sozinha a dificuldade da busca. A campanha
completa e sua análise precisam ocorrer antes de marcar escalabilidade no plano.

## Testes

Em `backend/`, execute `python -m pytest tests/test_benchmark.py tests/test_benchmark_metrics.py tests/test_benchmark_campaign.py`.
Os testes usam
somente grafos e GTFS sintéticos. Cobrem equivalência temporal, esperas, baldeações,
ultrapassagens, empates, duração zero, horários acima de 24h, ausência de caminho,
limpeza após erros, subgrafos aninhados, exportação, parâmetros inválidos, falhas
de worker, timeout, limite de RSS, resumo do custo completo e exportação da RSS
preparada. Testam processos reais, caminhos com espaços e
acentos, comunicação UTF-8, saídas maiores que um buffer de pipe e encerramento
dos workers após falhas. Não exigem valores específicos de tempo ou RAM.
A seleção estratificada, a matriz, a continuidade após falhas, a preservação de
amostras antes do timeout, a exportação de mediana/IQR e a ausência de importações
NetworkX em `app/` também têm testes. Execução real no macOS permanece pendente;
simulações não comprovam compatibilidade. Compare desempenho no mesmo ambiente.

## Campanha real de 21/11/2026

Windows 11, Python 3.14.7 e versões de `backend/requirements.txt`, dia de serviço
17/11/2026. Resultados por tamanho em [campaign/](benchmarks/campaign/).

| Limite | Estado | Estações | Conexões | Eventos/arestas NetworkX | Casos alcançáveis |
|---|---|---:|---:|---|---:|
| 100 | válido | 100 | 0 | 0/0 | 0/8 |
| 1.000 | válido | 1.000 | 15.722 | 29.842/45.287 | 0/8 |
| completo | válido | 9.925 | 1.458.808 | 1.479.535/2.926.010 | 6/8 |

Cada tamanho concluído contém 18 workers, 128 amostras brutas (112 de tempo,
16 de memória) e 32 resumos. A matriz final terminou às 12:02:52 locais, com
54 workers, 384 amostras e 96 resumos; nenhum timeout, excesso de RSS ou
divergência. Os dois motores concordaram em todos os casos dos três tamanhos.
O subgrafo de 100 estações não contém conexões: suas
latências medem overhead e resposta sem rota. Em 1.000 estações também não há rota
para esses pares. Os dados foram preservados sem ajustar a seleção após observar
o resultado; não representam o custo de encontrar itinerários alcançáveis.
No grafo completo, os seis pares selecionados têm rota e os dois casos sem rota
foram confirmados também pelo NetworkX.

| Limite | Motor | Preparação mediana (ms) | Intervalo das medianas `query_total` (µs) | RSS máxima amostrada (MiB) |
|---|---|---:|---:|---:|
| 100 | A* | 0,111 | 24,2–27,3 | 228,266 |
| 100 | NetworkX | 457,012 | 56,3–81,8 | 228,180 |
| 1.000 | A* | 5,084 | 25,3–443,8 | 228,203 |
| 1.000 | NetworkX | 1.038,204 | 96,8–1.306,5 | 228,152 |
| completo | A* | 734,682 | 67.510–2.595.358,7 | 228,215 |
| completo | NetworkX | 14.333,139 | 4.285,9–8.290.381,7 | 2.488,203 |

Preparação é a mediana entre nove workers por motor, incluindo a importação fria
do NetworkX. O intervalo de `query_total` vai da menor à maior mediana entre os
oito casos, cada um com sete repetições; não é o IQR. O IQR individual usa
`statistics.quantiles(method='inclusive')` e está em `summary.csv` e no JSON.
RSS máxima é o máximo entre os workers do motor e inclui ingestão, launcher e
conversão, não memória exclusiva da busca. A enumeração da árvore de processos
consome CPU e pode interferir nas durações; não houve controle pareado para
separar esse efeito de outras condições da máquina. Outliers de ingestão foram
preservados. Os valores descrevem esta execução e não demonstram superioridade
geral.

No grafo completo, as medianas/IQR do custo completo por consulta, em ms, foram:

| Caso | Mediana A* | IQR A* | Mediana NetworkX | IQR NetworkX |
|---|---:|---:|---:|---:|
| long-07 | 1.640,334 | 219,319 | 113,803 | 6,619 |
| long-14 | 1.111,706 | 193,058 | 195,255 | 55,802 |
| medium-07 | 410,340 | 16,342 | 27,856 | 1,661 |
| medium-14 | 264,174 | 22,199 | 17,620 | 0,352 |
| short-07 | 149,375 | 21,296 | 4,286 | 1,012 |
| short-14 | 67,510 | 3,410 | 4,438 | 1,787 |
| no-route-1 | 2.595,359 | 258,083 | 8.290,382 | 1.873,659 |
| no-route-2 | 188,883 | 4,128 | 146,531 | 5,250 |

RSS preparada mediana no grafo completo: 212,301 MiB no A* e 2.237,703 MiB no
NetworkX. A preparação e a RSS são custos distintos das consultas amortizadas.
As medianas da ingestão comum variaram de 96,434 s nos workers nativos para
33,818 s nos workers NetworkX, exigindo cautela ao interpretar as diferenças de
latência sem controle pareado das condições do sistema. Distância Haversine
caracteriza os pares, mas não isola a dificuldade da busca; um caso sem rota
teve o maior tempo em ambos os motores. Os números e a inversão de comportamento
entre casos reforçam que esta campanha não estabelece superioridade geral.

### Execuções interrompidas preservadas

A primeira tentativa Windows da campanha atual foi interrompida ao se comprovar
que o monitor anterior media apenas o launcher (~4 MiB), enquanto o Python filho
registrava ~212 MiB após carregar o feed. Os cinco workers concluídos e os
checkpoints foram preservados em
[campaign-launcher-invalid/](benchmarks/campaign-launcher-invalid/), com
`status: incomplete` e causa `invalid_monitor_target`. Esses picos não comprovam
o limite de memória e não entram na comparação. A campanha em `campaign/` foi
reiniciada após corrigir e testar a medição da árvore de processos.

Uma segunda execução, com monitor corrigido, foi interrompida para aplicar a
revisão de procedência do manifesto e do estado de equivalência. Seus seis workers
concluídos e o último checkpoint interrompido ficaram em
[campaign-pre-review/](benchmarks/campaign-pre-review/), também incompletos e
separados da execução final.

## Verificação inicial histórica

Registro histórico da implementação Linux anterior à adaptação portátil e ao schema 3.
Os campos
`peak_rss_bytes` desses arquivos representam picos do sistema operacional e não
devem ser confundidos com o novo `sampled_peak_rss_bytes`. Os arquivos originais
foram preservados; a campanha atual utiliza o novo método e outro manifesto.

Execução em 19/11/2026, dia de serviço 17/11/2026, com `--station-limit 100
--seed 42 --repetitions 2 --warmups 1 --memory-limit-mib 2048 --timeout 120`.
O manifesto de exemplo produziu uma rede com 100 estações e 205 conexões;
a expansão NetworkX teve 410 eventos e 609 arestas. Todos os processos concordaram
com a chegada ótima em `04:15:11`.

| Motor | Mediana da busca (ms) | RSS após preparação (MiB) | Pico do processo de memória (MiB) |
|---|---:|---:|---:|
| A* próprio | 0,008767 | 110,00 | 216,76 |
| Dijkstra NetworkX | 0,015868 | 114,45 | 216,75 |

RSS e picos são das execuções de memória em processos novos. A ingestão completa
levou aproximadamente 25–28 segundos em cada processo e domina os picos desta
amostra. Os valores não medem memória exclusiva do subgrafo nem demonstram
superioridade geral de um motor: há somente um par e duas repetições cronometradas.
Os resultados brutos e metadados estão em
[results.json](benchmarks/smoke/results.json) e
[measurements.csv](benchmarks/smoke/measurements.csv). O commit registrado é a base
de trabalho, com alterações locais, conforme o campo `dirty`.
