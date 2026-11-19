# Benchmark de roteamento

Compara o A* dependente do tempo do projeto com Dijkstra do NetworkX sobre uma
expansão temporal equivalente. Há vértices por estação/horário, arestas de viagem
e de espera. A referência usa
[`single_source_dijkstra`](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.shortest_paths.weighted.single_source_dijkstra.html).
NetworkX permanece exclusivo de `backend/benchmarks/`.

## Executar

Requer Python 3.11+ e `backend/requirements.txt`, incluindo `psutil`. A implementação
usa APIs portáveis para Linux, Windows e macOS; foi validada localmente apenas no
Linux. Não há workflows de validação configurados. Obtenha os TXT completos com
Git LFS conforme `data/gtfs/README.md`. A partir de `backend/`, use o mesmo comando
em Bash, PowerShell ou CMD:

```sh
python -m benchmarks.run --data-dir ../data/gtfs --service-date 2026-11-17 --queries ../docs/benchmarks/queries.json --repetitions 5 --warmups 1 --timeout 600 --memory-limit-mib 4096 --output ../data/cache/benchmark
```

O manifesto incluído é uma consulta real de exemplo, não uma amostra representativa.
Cada entrada contém `id` único, IDs string em `origin`/`destination` e `departure`
em `HH:MM:SS`, aceitando horários acima de 24h. O calendário é selecionado pela data.
Ponteiros LFS são rejeitados antes da ingestão.

`--timeout` limita cada processo em segundos; `--memory-limit-mib` encerra o worker
quando a RSS amostrada ultrapassa o limite. Não é um teto rígido: pode haver excesso
entre amostragens. Esse limite de RSS substitui o antigo limite de espaço virtual
com `RLIMIT_AS`. Falhas produzem
`status: incomplete`, diagnóstico e saída não zero. Não há resumo comparativo
quando ocorrer falha ou divergência. Use um diretório de saída por experimento:
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
O controlador amostra o worker aproximadamente a cada 10 ms e registra
`sampled_peak_rss_bytes` e `memory_sample_count`. Esse máximo observado pode perder
picos breves; não representa o pico exato fornecido pelo sistema operacional.
O intervalo efetivo pode ser maior devido ao escalonamento do sistema.

Sem limite de RAM, processos de tempo não são amostrados: seu pico vale `null` no
JSON e fica vazio no CSV. Com limite de RAM, também são monitorados, com possível
interferência no tempo medido. Para medições finais de tempo, prefira executar sem
limite de RAM. Os snapshots de RSS dentro do worker ficam fora do cronômetro de busca.

RSS mede o processo, não o tamanho exato das
estruturas. O JSON registra snapshots antes/depois das fases e após liberar o grafo
nativo no worker NetworkX. O pico amostrado pode incluir as duas representações;
o alocador pode reter memória após liberar objetos. O motor próprio mantém seu
grafo nativo, necessário às consultas.

Cada amostra registra memória após a busca, antes da validação. O pico observado
abrange toda a execução do worker, incluindo inicialização, ingestão, validação,
armazenamento de caminhos/amostras e serialização. No CSV, o mesmo pico do worker
é repetido nas linhas de suas fases; não é um pico individual de cada fase.
Picos são cumulativos: não subtrair para obter memória exclusiva da busca.

`results.json` contém caminhos, chegada absoluta em minutos, contagens das duas
representações, serviços ativos, hashes das entradas e manifesto, versões, CPU,
memória disponível/total do sistema, commit e alterações locais. `schema_version: 2`
identifica a medição portátil; método, intervalo e tipo do limite são registrados.
O resumo por caso/motor inclui mediana,
mínimo, máximo e intervalo interquartil do tempo `search`. As amostras brutas,
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

Em `backend/`, execute `python -m pytest tests/test_benchmark.py tests/test_benchmark_metrics.py`.
Os testes usam
somente grafos e GTFS sintéticos. Cobrem equivalência temporal, esperas, baldeações,
ultrapassagens, empates, duração zero, horários acima de 24h, ausência de caminho,
limpeza após erros, subgrafos aninhados, exportação, parâmetros inválidos, falhas
de worker, timeout e limite de RSS. Testam processos reais, caminhos com espaços e
acentos, comunicação UTF-8, saídas maiores que um buffer de pipe e encerramento
dos workers após falhas. Não exigem valores específicos de tempo ou RAM.
Execuções reais no Windows e macOS continuam pendentes; simulações não comprovam
compatibilidade nesses sistemas. Compare desempenho entre motores no mesmo ambiente.

## Verificação inicial com dados reais

Registro histórico da implementação Linux anterior à adaptação portátil. Os campos
`peak_rss_bytes` desses arquivos representam picos do sistema operacional e não
devem ser confundidos com o novo `sampled_peak_rss_bytes`. Os arquivos originais
foram preservados; a campanha real não foi repetida com o novo método nesta entrega.

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
