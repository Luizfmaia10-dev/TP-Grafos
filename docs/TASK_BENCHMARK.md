# Plano de implementação: benchmark do motor próprio e NetworkX

> Documento histórico: registra decisões e instruções da época, não tarefas abertas atuais. O progresso vigente está em [docs/PLAN.md](PLAN.md); contratos atuais em [API.md](API.md).

## Atualização da Task 5 — 21/11/2026

As dependências diretas foram fixadas nas versões verificadas no ambiente. A
metodologia atual e os comandos estão em [BENCHMARK.md](BENCHMARK.md). O manifesto
[queries.json](benchmarks/queries.json) é gerado do feed real com semente 42,
seis pares alcançáveis (curta/média/longa às 07:00/14:00) e dois pares sem rota;
inclui distâncias Haversine, evidência de chegada e hashes. `--check` regenera e
compara o manifesto sem substituí-lo.
Antes de iniciar workers, a campanha rejeita diferenças entre a seleção e suas
entradas de data, semente ou hashes GTFS, preservando essa procedência no relatório.

`benchmarks.campaign` executa os limites 100/1.000/completo com sete repetições,
dois aquecimentos, 4.096 MiB amostrados e 600 segundos por processo. Os resultados
ficam em [campaign/](benchmarks/campaign/), com um relatório por tamanho,
amostras e checkpoints preservados, inclusive antes de timeout ou estouro de RSS.
Cada tamanho interrompido é registrado e a execução continua no próximo tamanho.
JSON e CSV identificam preparação, RSS, tempos brutos e, quando válido, mediana/IQR.
Respostas parciais são comparadas quando disponíveis; a confirmação de equivalência
exige os dois motores em todos os casos. Um tamanho incompleto não entra no resumo
comparativo. Subgrafos induzidos podem tornar os seis casos alcançáveis do grafo
completo inalcançáveis; isso não é divergência se ambos os motores concordarem.
Uma divergência posterior invalida explicitamente qualquer confirmação de
equivalência anterior (`failed`).

A matriz final foi concluída em 21/11/2026, com três tamanhos válidos, 54 workers,
384 amostras e concordância entre os motores nos oito casos de cada tamanho.
Os subgrafos de 100 e 1.000 estações deixaram todos os casos sem rota; o de 100
não contém conexões. No grafo completo, seis casos têm rota e dois não têm.
Tentativas interrompidas anteriores foram preservadas separadamente com causa.

Esses resultados comparam implementações e representações distintas e uma seleção
pequena; não fundamentam superioridade geral de um algoritmo. O registro histórico
abaixo permanece como contexto da implementação original.

## Objetivo e escopo

Entregar um script reproduzível que compare o A* de `RouteSimulator` com Dijkstra do NetworkX, preservando o problema de menor horário de chegada do mesmo dia de serviço GTFS. Medir tempo de execução e RAM, validar a equivalência das respostas e exportar resultados para o relatório da SBC.

O item principal está na Parte 9 de `docs/PLAN.md`: scripts de benchmark de tempo e memória. A matriz de experimentos também prepara a avaliação de escalabilidade, mas esse segundo item só estará concluído após sua execução e análise.

NetworkX permanece exclusivo de `backend/benchmarks/`, sem importações em `backend/app/`. Não alterar API, frontend ou motor para acomodar o benchmark. Código e documentação interna em inglês; documentação analítica em português. Novas classes de dados usam `slots=True`.

## 1. Comparação matematicamente equivalente

O NetworkX receberá uma expansão temporal do grafo, com pesos estáticos não negativos. Usar apenas `travel_time` como peso perderia esperas e disponibilidade de partidas.

- Criar um vértice `(station_id, time)` para cada instante de partida e chegada de conexões agendadas. Unificar eventos de uma estação no mesmo instante.
- Conectar eventos consecutivos de cada estação com arestas de espera, de peso igual à diferença de horários.
- Para cada conexão, criar uma aresta entre seu evento de partida e seu evento de chegada, com peso `travel_time`. Preservar conexões com os mesmos extremos temporais por metadados representativos: seus custos são iguais e basta uma para reconstruir uma solução ótima.
- Para cada consulta, conectar uma fonte ao primeiro evento da origem em horário maior ou igual à partida solicitada. O peso inclui a espera inicial.
- Conectar eventos do destino a um sumidouro com peso zero. Remover fonte, sumidouro e ligações de consulta após a busca.
- Executar Dijkstra do NetworkX e reconstruir os trechos de transporte do caminho encontrado. Somar a duração ao horário inicial para obter a chegada absoluta.
- Tratar origem igual ao destino e ausência de caminho conforme o contrato do motor.

Essa construção permite embarques exatamente no horário, conexões de duração zero, ultrapassagens entre serviços e horários acima de 24h. Usar minutos fracionários internamente, sem arredondar eventos para minutos inteiros.

O escopo inicial é a rede GTFS de conexões agendadas, sem vértices temporários ou caminhada sob demanda. O adaptador deve rejeitar explicitamente grafos com `WALK`, pois uma expansão apenas dos eventos agendados não representa caminhadas arbitrárias corretamente. Suporte a caminhada fica para uma extensão própria.

Comparar chegada ótima e validade do itinerário, sem exigir a mesma sequência de estações quando houver empate. Usar tolerância numérica explícita, por exemplo `1e-7` minuto. Divergências invalidam o experimento e produzem diagnóstico com consulta e caminhos.

## 2. Organização e entradas

Arquivos previstos:

- `backend/benchmarks/__init__.py`.
- `backend/benchmarks/networkx_adapter.py`: expansão temporal e consulta de referência.
- `backend/benchmarks/run.py`: CLI, processos isolados, medições e exportação.
- `backend/benchmarks/metrics.py`: snapshots e monitoramento portável de RSS.
- `backend/tests/test_benchmark.py`: testes sintéticos do adaptador e do executor.
- `docs/BENCHMARK.md`: metodologia, comandos e interpretação dos resultados.
- `docs/benchmarks/`: manifestos de consultas e resultados selecionados para o relatório.

Reutilizar `DataLoader`, `TransportGraph`, `RouteSimulator` e `TimeUtils` diretamente, sem depender da camada HTTP de `app.network`.

A CLI deve receber diretório GTFS, data de serviço, arquivo de consultas, repetições, aquecimentos e diretório de saída. O manifesto de consultas contém identificador, IDs de origem/destino e horário `HH:MM:SS`. Validar os IDs antes das medições. Horários acima de 24h são aceitos pelo contrato existente.

Exemplo da interface a implementar, executado em `backend/`:

```bash
python -m benchmarks.run --data-dir ../data/gtfs --service-date YYYY-MM-DD --queries ../docs/benchmarks/queries.json --repetitions 5 --warmups 1 --output ../docs/benchmarks/results
```

## 3. Medições e isolamento

Executar cada motor em processos independentes e sequenciais, com as mesmas entradas. Não executar os motores simultaneamente. Registrar separadamente:

| Fase | Medição |
|---|---|
| Ingestão comum | Tempo de `DataLoader.build_graph` e pico de RAM do processo |
| Preparação própria | Tempo de cálculo de `max_speed` |
| Preparação NetworkX | Tempo de expansão temporal e contagens de vértices/arestas expandidos |
| Consulta | Tempo de preparação da consulta, busca com reconstrução e limpeza, discriminados |
| Memória | RSS antes da preparação, após preparar o motor e pico de RSS do processo |

Usar `time.perf_counter_ns()` para durações. Após a solicitação de portabilidade, substituir `/proc` e `resource` por `psutil` para snapshots de RSS em bytes em Linux, Windows e macOS. O controlador amostra RSS a cada 10 ms nas execuções de memória e registra `sampled_peak_rss_bytes`: um máximo observado que pode perder picos curtos. Não confundir com o pico exato do sistema operacional. Execuções de tempo não são amostradas, exceto quando o limite monitorado de RSS estiver habilitado. Esse limite substitui `RLIMIT_AS`, com possibilidade de excesso entre amostras. Validar localmente no Linux; execução real nos outros sistemas permanece pendente e workflows estão fora do escopo solicitado.

O pico de RSS é cumulativo durante a vida do processo: não apresentar sua diferença como memória exclusiva da busca. Usar uma execução adicional em processo novo por motor e consulta para registrar o pico total de cada caso. Medições de tempo podem reutilizar uma rede preparada após aquecimento; mantê-las separadas das execuções de memória.

O processo NetworkX inicialmente precisa do grafo nativo para a conversão. Registrar o pico de conversão como tal; liberar o grafo nativo e referências auxiliares antes da RSS da rede preparada. Memória retida pelo alocador pode permanecer: documentar que RSS mede o processo, não o tamanho exato dos objetos. Não atribuir o pico de ingestão à estrutura final.

Para tempo de busca, comparar a chamada do motor próprio com Dijkstra e reconstrução equivalente. Resumir `query_total` como comparação principal do custo completo por consulta e manter `search` como decomposição interna; preparação amortizável permanece separada. Não incluir CSV/JSON, validação ou impressão no cronômetro da busca. Manter a política de coleta de lixo igual para ambos.

## 4. Resultados reproduzíveis

Exportar medições brutas em CSV e metadados/resumos em JSON:

- Motor, caso, repetição, fase, duração em nanossegundos e memória em bytes.
- Origem, destino, partida, chegada, alcançabilidade e número de trechos.
- Estações/conexões originais e vértices/arestas da expansão temporal.
- Data e serviços GTFS ativos, hashes dos arquivos de entrada e do manifesto.
- Versões de Python e NetworkX, sistema, CPU, RAM disponível, commit Git e indicação de alterações locais.
- Aquecimentos, repetições, resultados da verificação e eventuais erros.

Resumir `query_total` e `search` por caso e motor com mediana, mínimo, máximo e intervalo interquartil, apresentando `query_total` primeiro. Preservar amostras, inclusive valores extremos. Razões de desempenho devem identificar a fase comparada; casos inválidos ou incompletos não entram no resumo comparativo.

Um limite de memória/tempo atingido deve ser registrado como experimento incompleto. Não reduzir silenciosamente o dataset para conseguir executar a expansão.

## 5. Sequência de implementação com TDD

- [x] Criar testes que falhem para espera inicial, baldeação, partida perdida, partida exata, serviço posterior mais rápido, arestas paralelas, empate, duração zero, horário acima de 24h, origem igual ao destino e destino inalcançável.
- [x] Implementar a expansão temporal e a referência Dijkstra; conferir documentação oficial da versão instalada do NetworkX antes da integração.
- [x] Validar temporalmente os caminhos dos dois motores e comparar a chegada ótima em grafos sintéticos pequenos com semente fixa, incluindo casos desconexos. Coordenadas e durações devem respeitar a heurística admissível do motor.
- [x] Testar a rejeição explícita de `WALK` e a limpeza dos nós auxiliares entre consultas.
- [x] Criar testes do contrato da CLI e das exportações, incluindo unidades, metadados, divergências e falhas de subprocesso. Não testar limiares de velocidade ou consumo de RAM.
- [x] Implementar o executor isolado, medição de fases, aquecimentos, repetições e resumos.
- [x] Executar o fluxo completo em um feed GTFS sintético pequeno, sem depender do download da base real nos testes automatizados.
- [x] Executar a suíte de testes relevante e a suíte completa do backend antes da entrega.
- [x] Documentar metodologia e comandos em `docs/BENCHMARK.md`.

## 6. Experimentos reais e escalabilidade

- [x] Confirmar que os TXT são dados completos, não ponteiros LFS, e escolher uma data coberta pelos calendários do feed.
- [x] Versionar um manifesto de consultas com IDs reais: distâncias curtas, médias e longas por Haversine, horários de pico e fora de pico. Preservar consultas sem rota e identificá-las separadamente.
- [x] Executar primeiro uma amostra pequena e depois a base completa, respeitando os recursos da máquina. Registrar os resultados sem prometer antecipadamente que a expansão completa caberá em RAM.
- [x] Para escalabilidade, definir subconjuntos aninhados e determinísticos de estações com semente fixa, mantendo apenas conexões cujos extremos estejam no subconjunto. Aplicar a mesma seleção aos dois motores e registrar as contagens efetivas.
- [x] Manter pares comuns quando possível, informar mudanças de alcançabilidade e não interpretar subgrafos induzidos como redes de transporte realistas.
- [ ] Analisar separadamente variação de tamanho e distância geográfica. Distância em linha reta não equivale a dificuldade de busca.
- [x] Registrar tabelas de tempo, RAM e expansão da representação em `docs/BENCHMARK.md`, com referências aos arquivos brutos.

## 7. Critérios de aceite e atualização do plano geral

- O comando documentado executa os dois motores e gera CSV/JSON reproduzíveis.
- Todos os casos concluídos têm caminhos temporalmente válidos e a mesma chegada ótima ou concordam sobre ausência de rota.
- NetworkX não é importado pelo domínio, roteador ou API.
- Preparação, RSS do motor preparado, busca e picos de processo são identificados sem confundir RSS com memória exclusiva do algoritmo.
- O relatório distingue comparação entre implementações e representações de uma comparação isolada entre algoritmos: A* nativo e Dijkstra temporalmente expandido usam estruturas diferentes.
- Ao entregar o script validado, marcar apenas o item de scripts de benchmark da Parte 9 em `docs/PLAN.md`.
- Marcar escalabilidade, análise formal de complexidade e limitações apenas quando suas respectivas análises estiverem concluídas. A fila com entradas obsoletas do A* e o tamanho da expansão temporal precisam ser considerados na análise espacial; não copiar limites existentes sem revisão.
- Não marcar os itens de implementação do motor da Parte 5 como parte desta entrega; sua conciliação com o código existente é uma revisão separada.
