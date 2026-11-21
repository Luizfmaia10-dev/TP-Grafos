# Motor de Roteamento A* Dependente do Tempo (`RouteSimulator`)

`app.route_simulator.RouteSimulator` implementa o algoritmo de busca heurística A* dependente do tempo (*Time-Dependent A\**) sobre o grafo em memória (`TransportGraph`). Utiliza apenas módulos da biblioteca padrão do Python (`heapq`, `bisect`, `math`, `itertools`), sem dependência de bibliotecas de grafos externas.

---

## 1. Contrato interno do motor

### `calculate_route(origin: Station, destination: Station, departure_time: float) -> list[tuple[Station, Connection]] | None`

Calcula o caminho de menor horário de chegada (*earliest arrival*) partindo de `origin` no instante `departure_time` (em minutos fracionários desde o início do dia de serviço) até `destination`.

- **Retorno de sucesso:** Lista de tuplas `(estacao_embarque, conexao)` em ordem cronológica de percurso. A estação de desembarque de cada trecho é dada por `conexao.destination`.
- **Origem idêntica ao destino:** Retorna lista vazia `[]`.
- **Destino inalcançável:** Retorna `None`.

A API REST recebe `origin_id`, `destination_id` e `departure_time`; após receber
o caminho, `build_route_result` cria o `Itinerary`. O roteador não o constrói.
`snap_to_network` é uma capacidade interna, sem contrato REST para coordenadas.

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
  - Operações de fila de prioridade: $O(|E|\log(|E|+1)+1)$. O `heapq` não possui `decrease-key`: cada melhora de rótulo insere uma nova entrada e mantém as obsoletas até sua remoção, permitindo $O(|E|+1)$ entradas no heap, inclusive a entrada inicial quando não há arestas.
  - Conexões de caminhada (`WALK`): $O(W+1)$ por estação expandida, onde $W$ é o número de conexões com horário zero ($0.0$). Como as conexões são mantidas ordenadas por `departure_time` e arestas de caminhada são sob demanda com `departure_time == 0.0`, a varredura percorre apenas o prefixo e interrompe no primeiro elemento com `departure_time > 0.0`, sem custo $O(K)$ sobre toda a lista de partidas. O termo constante inclui a verificação do laço vazio.
  - Busca binária de partidas agendadas: $O(\log(K+1)+1)$ em cada estação expandida para localizar a primeira partida $\ge t$ via `bisect_left`, onde $K$ é o número de partidas da estação. O termo constante cobre listas vazias e as verificações da expansão.
  - Varredura de partidas agendadas: $O(K_{\text{relevante}})$ por expansão a partir do índice `start`, iterada diretamente sem alocação de listas intermediárias e interrompida pela poda de parada assim que $c.\text{departure\_time} \ge g[\text{destination}]$.
- **Espaço:**
  - `g`, `predecessor` e `closed` ocupam $O(|V|)$; o heap ocupa $O(|E|+1)$ e o caminho retornado $O(L)$, para $L$ trechos. O espaço auxiliar total é $O(|V|+|E|+1)$, equivalente a $O(|V|+|E|)$ para uma rede não vazia.

Como cada estação é expandida no máximo uma vez, o número de conexões
inspecionadas é $O(|E|)$. Se $X$ é o conjunto de estações expandidas, $H$ o
número de inserções no heap e $K_v$ o tamanho da lista de saída de $v$, o limite
refinado é $O(|E|+\sum_{v\in X}\log(K_v+1)+H\log(H+1)+L+|X|+1)$.
Com $K_{\max}$ conexões na maior lista de saída (zero em rede sem conexões),
o pior caso geral é
$O(|E|\log(|E|+1)+|V|\log(K_{\max}+1)+L+|V|+1)$.
Os termos $|X|+1$ e $|V|+1$ explicitam a inicialização e o custo constante por
expansão omitidos na forma anterior aprovada. Mesmo com $|E|=K_{\max}=L=0$,
uma consulta entre estações isoladas inicializa e remove a entrada da origem;
o trabalho não é zero. Em instâncias onde o heap domina, a forma anterior
continua sendo uma simplificação assintótica.
As operações em tabelas hash são consideradas de tempo médio amortizado.
Esse limite corresponde à análise em [ANALISE_COMPLEXIDADE.tex](ANALISE_COMPLEXIDADE.tex).

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

A validação foi realizada sobre o dataset oficial de Belo Horizonte (`data/gtfs`), filtrando o serviço `307679` via `active_service_ids`:
- **Grafo em memória:** 9.659 estações e 1.336.540 conexões temporais.
- **Velocidade máxima derivada (`max_speed_of`):** $2,60\text{ km/min}$ ($156,2\text{ km/h}$), computada em $0,38\text{ s}$.

### Resultados de 10 Consultas em Horários de Pico (07:00) e Fora de Pico (14:00)

| Consulta | Origem | Destino | Horário | Tempo de Resposta | Estações Expandidas | Trechos | Consistência Temporal |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|
| 01 | Rua Joana Angelica 985 | Rua Chasquiel Zinquier 57 | 07:00 | $751,99\text{ ms}$ | 3.565 | 31 trechos | Válida |
| 02 | Rua Sao Fidelis 1052 | Rua Quintino Bocaiuva 40 | 07:00 | $652,77\text{ ms}$ | 3.422 | 59 trechos | Válida |
| 03 | Avenida Presidente Antoni | Rua Maria Felicia 153 | 07:00 | $777,19\text{ ms}$ | 3.873 | 51 trechos | Válida |
| 04 | Rua Caetano Pirri, 1444 | Rua Josue Martins De Souz | 07:00 | $1212,28\text{ ms}$ | 7.857 | 71 trechos | Válida |
| 05 | Avenida Tito Fulgencio 60 | Avenida Dos Andradas 5801 | 07:00 | $814,40\text{ ms}$ | 4.708 | 99 trechos | Válida |
| 06 | Rua Joinville 643 | Rua Major Barbosa 188 | 14:00 | $136,16\text{ ms}$ | 1.779 | 83 trechos | Válida |
| 07 | Rua Costa Rica 33 | Rua das Petúnias, 881 | 14:00 | $699,12\text{ ms}$ | 7.085 | 67 trechos | Válida |
| 08 | Rua Sao Pedro Da Aldeia 3 | Estação Barreiro - Plataf | 14:00 | $13,47\text{ ms}$ | 158 | 23 trechos | Válida |
| 09 | Rua Joao Batista Vieira 4 | Rua Regia 123 | 14:00 | $420,15\text{ ms}$ | 3.963 | 68 trechos | Válida |
| 10 | Rua Joaquim Cardoso 409 | Rua Mestre Valentim 511 | 14:00 | $75,30\text{ ms}$ | 794 | 44 trechos | Válida |

- **Tempo médio por consulta:** $555,28\text{ ms}$ (redução substancial após eliminação da varredura linear de conexões de caminhada)
- **Tempo máximo:** $1212,28\text{ ms}$ (significativamente abaixo do limiar de $5\text{ s}$)
- **Estações expandidas médias:** $3.720,4$ (máximo de $7.857$ no caso mais disperso e mínimo de $158$ na ligação local para o Barreiro)
- **Consistência temporal:** 100% das rotas verificadas programaticamente (para cada percurso, $u_i = \text{dest}_{i-1}$, $c_i.\text{departure\_time} \ge t_{i-1}$ e tempo estritamente monótono).

