# Motor de Roteamento A* Dependente do Tempo (`RouteSimulator`)

`app.route_simulator.RouteSimulator` implementa o algoritmo de busca heurística A* dependente do tempo (*Time-Dependent A\**) sobre o grafo em memória (`TransportGraph`). Utiliza apenas módulos da biblioteca padrão do Python (`heapq`, `bisect`, `math`, `itertools`), sem dependência de bibliotecas de grafos externas.

---

## 1. Contrato da API

### `calculate_route(origin: Station, destination: Station, departure_time: float) -> list[tuple[Station, Connection]] | None`

Calcula o caminho de menor horário de chegada (*earliest arrival*) partindo de `origin` no instante `departure_time` (em minutos fracionários desde o início do dia de serviço) até `destination`.

- **Retorno de sucesso:** Lista de tuplas `(estacao_embarque, conexao)` em ordem cronológica de percurso. A estação de desembarque de cada trecho é dada por `conexao.destination`.
- **Origem idêntica ao destino:** Retorna lista vazia `[]`.
- **Destino inalcançável:** Retorna `None`.

### `max_speed_of(graph: TransportGraph) -> float` *(staticmethod)*

Percorre todas as arestas do grafo com `travel_time > 0` e retorna a velocidade máxima observada ($\text{distancia} / \text{travel\_time}$ em km/min).
- Ignora arestas com `travel_time <= 0` evitando divisões por zero.
- Se o grafo não contiver arestas com tempo positivo, retorna a velocidade de caminhada padrão ($5\text{ km/h} \approx 0.0833\text{ km/min}$).

### `heuristic(current: Station, target: Station) -> float`

Calcula a distância em linha reta via fórmula de Haversine dividida pela velocidade máxima admissível da rede:

$$h(u, v) = \frac{\text{haversine}(u, v)}{V_{\max}}$$

---

## 2. Modelo Matemático e de Custos

1. **Modais Agendados (`BUS`, `SUBWAY`):**
   - Uma viagem só pode ser embarcada se seu horário de partida for maior ou igual ao horário atual na estação: $c.\text{departure\_time} \ge t$.
   - O horário de chegada na próxima estação é $\text{arr}(c) = c.\text{departure\_time} + c.\text{travel\_time}$.
   - O custo da aresta corresponde à espera dinâmica na estação mais a duração do percurso:
     $$w_c(t) = (c.\text{departure\_time} - t) + c.\text{travel\_time} = \text{arr}(c) - t$$
   - A próxima partida disponível é localizada em tempo logarítmico $O(\log K)$ usando `bisect.bisect_left` sobre a lista ordenada de conexões da estação.

2. **Modal Sob Demanda (`WALK`):**
   - Conexões de caminhada (como as criadas pelo context manager `snap_to_network`) possuem `departure_time == 0.0` e são atemporais: a partida é imediata no instante atual $t$, com tempo de espera zero e chegada em $t + c.\text{travel\_time}$.

3. **Propriedade FIFO:**
   - A função de chegada ao longo de qualquer aresta é não decrescente em relação a $t$ (chegar mais tarde na estação de embarque nunca permite chegar mais cedo ao destino). Isso garante a propriedade FIFO e assegura a corretude do algoritmo *label-setting* sem necessidade de reabrir nós fechados.

---

## 3. Heurística e Podas de Busca

- **Admissibilidade:** Como $V_{\max}$ delimita superiormente a velocidade de qualquer modal presente no grafo e o tempo de espera é sempre não negativo ($\ge 0$), $h(u, v)$ nunca superestima o tempo real de viagem até o destino, garantindo a otimalidade da solução encontrada.
- **Desempate Seguro no Heap:** A fila de prioridade armazena tuplas `(f_score, counter, station)` onde `counter` é um iterador incremental gerado por `itertools.count()`. Isso impede que o Python tente comparar instâncias de `Station` (que têm `eq=False` e não implementam `<`) em empates de `f_score`.
- **Poda por Melhor Chegada Conhecida:** Durante a varredura das conexões após a busca binária, se $c.\text{departure\_time} \ge g[\text{destination}]$, o laço de conexões daquela estação é interrompido imediatamente com `break`, pois nenhuma partida posterior poderá chegar antes da melhor rota já conhecida.

---

## 4. Complexidade Assintótica

- **Tempo:**
  - Operações de fila de prioridade: $O((|V| + |E|) \log |V|)$ com inserções e remoções via `heapq`.
  - Busca binária de partidas: $O(\log K)$ em cada estação expandida, onde $K$ é o número de partidas da estação.
  - Varredura de conexões: $O(K)$ no pior caso por expansão, mitigada pela poda de corte em $g[\text{destination}]$.
- **Espaço:**
  - $O(|V|)$ para a tabela de rótulos de chegada `g`, mapa de predecessores `predecessor`, conjunto de nós fechados `closed` e elementos na fila de prioridade `heap`.

---

## 5. Validação com Testes Automatizados

A suíte em `backend/tests/test_route_simulator.py` valida:
- Distância geodésica de Haversine e admissibilidade da heurística.
- Integração com `snap_to_network` e remoção automática de topologia temporária.
- Cálculo de velocidade máxima da rede `max_speed_of()`.
- Rotas diretas com tempo de espera dinâmico e partidas no horário exato.
- Descarte de partidas que já saíram antes do horário de consulta.
- Reconstrução cronológica correta de rotas com múltiplas baldeações e transferências entre modais.
- Preferência por linhas mais rápidas que partem depois contra linhas lentas que partem antes.
- Rota indireta mais rápida escolhida em detrimento de rota direta mais demorada.
- **Prova de otimalidade por equivalência (Property-Based Test):** Teste comparativo entre A* e Dijkstra dependente do tempo sobre 50 pares aleatórios em grafos sintéticos, confirmando identidade rigorosa no horário ótimo de chegada e validade temporal de todos os trechos.

---

## 6. Validação de Desempenho com Dados Reais da BHTRANS

A validação foi realizada sobre o dataset oficial de Belo Horizonte (`data/gtfs`), filtrando o serviço dominante `307679`:
- **Grafo em memória:** 9.659 estações e 1.336.540 conexões temporais.
- **Velocidade máxima derivada (`max_speed_of`):** $2,60\text{ km/min}$ ($156,2\text{ km/h}$), computada em $0,36\text{ s}$.

### Resultados de 10 Consultas em Horários de Pico (07:00) e Fora de Pico (14:00)

| Consulta | Origem | Destino | Horário | Tempo de Resposta | Status / Trechos |
|:---|:---|:---|:---:|:---:|:---|
| 01 | Rua Joana Angelica 9 | Rua Chasquiel Zinqui | 07:00 | $784,28\text{ ms}$ | Rota encontrada (31 trechos) |
| 02 | Rua Sao Fidelis 1052 | Rua Quintino Bocaiuv | 07:00 | $692,65\text{ ms}$ | Rota encontrada (59 trechos) |
| 03 | Avenida Presidente A | Rua Maria Felicia 15 | 07:00 | $827,78\text{ ms}$ | Rota encontrada (51 trechos) |
| 04 | Rua Caetano Pirri, 1 | Rua Josue Martins De | 07:00 | $1262,97\text{ ms}$ | Rota encontrada (71 trechos) |
| 05 | Avenida Tito Fulgenc | Avenida Dos Andradas | 07:00 | $868,38\text{ ms}$ | Rota encontrada (99 trechos) |
| 06 | Rua Joinville 643 | Rua Major Barbosa 18 | 14:00 | $175,74\text{ ms}$ | Rota encontrada (83 trechos) |
| 07 | Rua Costa Rica 33 | Rua das Petúnias, 88 | 14:00 | $808,41\text{ ms}$ | Rota encontrada (67 trechos) |
| 08 | Rua Sao Pedro Da Ald | Estação Barreiro - P | 14:00 | $19,29\text{ ms}$ | Rota encontrada (23 trechos) |
| 09 | Rua Joao Batista Vie | Rua Regia 123 | 14:00 | $485,07\text{ ms}$ | Rota encontrada (68 trechos) |
| 10 | Rua Joaquim Cardoso | Rua Mestre Valentim | 14:00 | $103,38\text{ ms}$ | Rota encontrada (44 trechos) |

- **Tempo médio por consulta:** $602,80\text{ ms}$
- **Tempo máximo:** $1262,97\text{ ms}$ (significativamente abaixo do limiar de $5\text{ s}$)
- **Taxa de sucesso:** 100% das rotas encontradas respeitando a consistência temporal.

