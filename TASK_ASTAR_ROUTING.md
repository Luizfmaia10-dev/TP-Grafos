# Tarefa: Motor de Busca A* Dependente do Tempo (`RouteSimulator.calculate_route`)

Documento de handoff para o agente implementador. Leia por inteiro antes de escrever codigo.
Avance checkpoint por checkpoint; cada um termina com testes verdes e um commit.

---

## 1. Objetivo

Implementar o nucleo do roteamento em `backend/app/route_simulator.py`:

```python
def calculate_route(
    self, origin: Station, destination: Station, departure_time: float
) -> list[tuple[Station, Connection]] | None:
```

- Encontra a rota de **menor horario de chegada** (*earliest arrival*) partindo de `origin` no instante `departure_time`.
- Usa A* com fila de prioridade `heapq` nativa.
- O custo de cada aresta inclui o **tempo de espera dinamico** na estacao ate a proxima partida, localizada por busca binaria (`bisect`) em $O(\log K)$ para modais agendados (`BUS`, `SUBWAY`), e partida imediata (espera zero) para caminhada (`WALK`).
- Reconstroi o caminho otimo a partir de ponteiros de predecessores.

Itens do `docs/PLAN.md` cobertos (Parte 5):
- Implementar a busca heuristica A* dependente do tempo ... `heapq` ...
- Utilizar busca binaria (`bisect`) ... proxima partida em $O(\log K)$ e calcular o tempo de espera dinamico.
- Reconstruir o caminho otimo a partir dos ponteiros de predecessores.
- Escrever testes unitarios cobrindo rotas diretas, transferencias e casos sem caminho viavel.

Fora de escopo: `Itinerary` e serializacao JSON (restante da Parte 6), endpoints FastAPI (Parte 8), benchmark com NetworkX (Parte 9).
*(Nota: `TemporaryVertex` e `snap_to_network` ja foram entregues nos commits recentes da Parte 6 e serao integrados diretamente com `calculate_route`).*

---

## 2. Regras obrigatorias do projeto (resumo do `AGENTS.md`)

- **TDD estrito**: escreva o teste, veja falhar, implemente o minimo, refatore. Commits de teste e de implementacao podem ser separados (`test(routing): ...` seguido de `feat(routing): ...`), padrao ja usado pela equipe.
- Codigo, nomes, docstrings e testes **em ingles**. Documentacao em `docs/` em portugues.
- Python puro: `heapq`, `bisect`, `math`. **Proibido** NetworkX ou qualquer biblioteca de grafos no motor.
- `__slots__` em toda classe nova de dominio/dados.
- Keep it simple: sem programacao defensiva desnecessaria (estacao inexistente pode levantar `KeyError` naturalmente do grafo).
- Sem emojis. README minimo.
- Problema encontrado: provar a causa raiz com evidencia antes de corrigir.
- Ao concluir, marcar os checkboxes correspondentes em `docs/PLAN.md` sem alterar o texto dos itens.

---

## 3. Contexto do codigo existente (leia estes arquivos)

| Arquivo | O que importa para esta tarefa |
|---|---|
| `backend/app/domain.py` | `Station` (frozen, `slots=True`, hash/eq por `station_id`, **nao ordenavel**). `TemporaryVertex` (subclasse de `Station`, `slots=("marker_type",)`). `Connection(route_id, destination, vehicle_type, travel_time, distance, departure_time)`. Tempos em **minutos fracionarios** desde o inicio do dia de servico, podendo passar de 1440 (viagens apos meia-noite). Distancia em km. |
| `backend/app/graph.py` | `TransportGraph.get_neighbors(station)` retorna a lista **interna** (nao copiar, nao mutar) de conexoes de saida, **ordenada por `departure_time`** (insercao via `bisect_right`). `TransportGraph.remove_temporary_vertex(vertex)` remove vertices e arestas temporarias. |
| `backend/app/route_simulator.py` | Ja existem `haversine(...)`, `RouteSimulator(graph, max_speed)` com `heuristic(current, target) = haversine / max_speed` e o context manager `snap_to_network(latitude, longitude, marker_type)` que conecta cliques a rede com arestas `WALK`. `max_speed` em **km/min**. Nao quebrar os testes existentes. |
| `backend/app/data_loader.py` | Carrega GTFS com selecao explicita de calendario (`selected_service_ids`) ou servico dominante, isolando viagens de servicos inativos e tratando restricoes de embarque/desembarque. Cada `Connection` parte em `departure_time` e chega em `departure_time + travel_time`. |
| `backend/tests/test_route_simulator.py` | Testes atuais de Haversine, heuristica e `snap_to_network`. Acrescentar os novos testes aqui. |
| `docs/DATA_LOADER.md`, `docs/TIME_UTILS.md` | Padrao de documentacao a seguir para `docs/ROUTE_SIMULATOR.md`. |

Execucao dos testes (venv na raiz do repositorio, `pytest.ini` em `backend/`):

```powershell
cd backend
..\venv\Scripts\python.exe -m pytest
```

Os testes unitarios devem usar **grafos sinteticos pequenos**, nunca o dataset real.

---

## 4. Modelo matematico

### 4.1 Funcao de custo dependente do tempo

Estando na estacao `u` no instante `t`, o comportamento depende do modal:

1. **Modais agendados (`BUS`, `SUBWAY`):**
   Uma conexao `c` so pode ser usada se `c.departure_time >= t`.
   $$\text{arr}(c) = c.\text{departure\_time} + c.\text{travel\_time}$$
   $$w_c(t) = \underbrace{(c.\text{departure\_time} - t)}_{\text{espera dinamica}} + c.\text{travel\_time} = \text{arr}(c) - t$$

2. **Modal a pe / caminhada (`WALK`):**
   Caminhada e sob demanda (on-demand), sem horario fixo na grade. Em conexoes geradas por `snap_to_network`, `departure_time = 0.0`.
   A partida ocorre imediatamente no instante atual `t`:
   $$\text{arr}(c) = t + c.\text{travel\_time}$$
   $$w_c(t) = c.\text{travel\_time} \quad (\text{espera} = 0)$$

Logo, o rotulo `g[v]` do A* e diretamente o **horario absoluto de chegada** em `v`, e o custo total da rota e `g[destination] - departure_time`.

### 4.2 Propriedade FIFO (garante corretude do label-setting)

Como a escolha e "a melhor conexao com partida >= t" (para transporte agendado) e partida imediata (para caminhada), a funcao de chegada da aresta e nao decrescente em `t` (chegar mais tarde nunca permite chegar antes). Isso satisfaz FIFO, condicao que torna Dijkstra/A* dependente do tempo correto sem reprocessar vertices fechados.

### 4.3 Heuristica

$$h(u, \text{dest}) = \frac{\text{haversine}(u, \text{dest})}{V_{\max}}$$

E admissivel e consistente **somente se** `V_max >= distance / travel_time` para toda aresta com `travel_time > 0` (espera so aumenta o custo). `V_max` deve ser calculado a partir do grafo (Checkpoint 1). `f(v) = g[v] + h(v)`.

### 4.4 Busca binaria das partidas e tratamento de modais

Para cada estacao expandida no instante `t`:
Como a lista `connections = self.graph.get_neighbors(station)` e ordenada por `departure_time`, arestas `WALK` (com `departure_time == 0.0`) aparecem no inicio da lista.

Estrategia de expansao:
- **Arestas `WALK`:** expandir com partida imediata `t` e chegada `t + c.travel_time`.
- **Arestas agendadas (`BUS`, `SUBWAY`):** localizar a primeira partida via `bisect_left`:
  ```python
  start = bisect_left(connections, t, key=lambda c: c.departure_time)
  ```
  Iterar a partir de `start` considerando apenas conexoes de modais agendados.

### 4.5 Varredura e podas (decisao de projeto)

Nao ha garantia de FIFO estrito entre linhas diferentes (uma linha expressa pode sair depois e chegar antes de uma linha paradora). Estrategia **exata** adotada:

1. Para arestas `WALK`, avaliar imediatamente.
2. Para conexoes agendadas a partir de `start`:
   - **Poda de parada**: se `c.departure_time >= best_arrival_at_destination` (melhor chegada ja conhecida no destino final), interromper o laco (`break`): nenhuma partida posterior podera chegar mais cedo.
   - **Poda de relaxamento**: so relaxar e colocar na heap se `arr(c) < g.get(c.destination, inf)`.

Isso preserva a otimalidade. O custo pior caso por expansao e $O(\log K + K)$; o desempenho real e medido no Checkpoint 6.

### 4.6 Decisoes do MVP (documentar em `docs/ROUTE_SIMULATOR.md`)

- Sem penalidade nem tempo minimo de transferencia: desembarcar e embarcar em outra linha no mesmo instante e permitido.
- Sem virada de dia: consulta as 23:50 sem partidas posteriores retorna `None`; nao se busca no dia seguinte.
- Calendarios: o `DataLoader` agora filtra por `selected_service_ids` (ou servico dominante), garantindo grafo cronologicamente consistente.
- `origin == destination` retorna lista vazia `[]`.
- Destino inalcancavel retorna `None`.

---

## 5. Contrato de saida

`calculate_route` retorna `list[tuple[Station, Connection]]`, um item por aresta usada, em ordem cronologica. Cada tupla e `(estacao_de_embarque, conexao_usada)`; o desembarque e `conexao.destination`.

Derivaveis pelo consumidor (o futuro `Itinerary` da Parte 6):
- horario de chegada final: horario de chegada do ultimo trecho
- espera em cada trecho:
  - para `WALK`: 0
  - para transporte publico: `conexao.departure_time - chegada_do_trecho_anterior` (no primeiro trecho, menos `departure_time` da consulta)

Nao criar `Itinerary` nem nova classe de resultado nesta tarefa.

---

## 6. Esboco do algoritmo

```text
calculate_route(origin, destination, t0):
    if origin == destination: return []
    g = {origin: t0}                       # earliest known arrival (absolute minutes)
    predecessor = {}                       # station -> (previous_station, connection)
    closed = set()
    counter = itertools.count()            # heap tie-breaker; Station is not orderable
    heap = [(t0 + h(origin), next(counter), origin)]

    while heap:
        _, _, station = heappop(heap)
        if station in closed: continue      # lazy deletion of stale entries
        if station == destination: return reconstruct(predecessor, origin, destination)
        closed.add(station)
        t = g[station]
        connections = graph.get_neighbors(station)

        # 1. Conexoes de caminhada (on-demand: saida imediata em t)
        walk_connections = [c for c in connections if c.vehicle_type == VehicleType.WALK]
        for c in walk_connections:
            arrival = t + c.travel_time
            if arrival < g.get(c.destination, inf):
                g[c.destination] = arrival
                predecessor[c.destination] = (station, c)
                heappush(heap, (arrival + h(c.destination), next(counter), c.destination))

        # 2. Conexoes agendadas (partida >= t localizada via bisect_left)
        start = bisect_left(connections, t, key=lambda c: c.departure_time)
        for c in connections[start:]:
            if c.vehicle_type == VehicleType.WALK:
                continue
            if c.departure_time >= g.get(destination, inf):
                break
            arrival = c.departure_time + c.travel_time
            if arrival < g.get(c.destination, inf):
                g[c.destination] = arrival
                predecessor[c.destination] = (station, c)
                heappush(heap, (arrival + h(c.destination), next(counter), c.destination))

    return None
```

Observacoes:
- Use a tupla `(f, counter, station)` no heap: sem o contador, empates em `f` fariam o Python comparar `Station` e lancar `TypeError`.
- A reconstrucao percorre `predecessor` de `destination` ate `origin` e inverte a lista: $O(L)$, `L` = numero de trechos.

---

## 7. Checkpoints

Cada checkpoint: testes primeiro, implementacao minima, suite inteira verde, commit. Nao avance com testes vermelhos.

### Checkpoint 0 - Preparacao
- [ ] `git pull` na `main`; criar branch `feat/time-dependent-astar`.
- [ ] Rodar a suite atual (`pytest backend`) e confirmar que todos os 149 testes passam antes de qualquer alteracao.
- [ ] Ler os arquivos da secao 3.

Pronto quando: suite verde registrada, branch criada.

### Checkpoint 1 - Velocidade maxima admissivel
- [ ] Teste: `RouteSimulator.max_speed_of(graph)` (staticmethod) retorna o maior `distance / travel_time` (km/min) entre as arestas com `travel_time > 0`.
- [ ] Teste: arestas com `travel_time == 0` sao ignoradas (sem `ZeroDivisionError`).
- [ ] Implementar iterando `graph.iter_stations()` e `get_neighbors` ($O(V + E)$).
- [ ] Commit: `feat(routing): derive admissible max speed from graph edges`.

Pronto quando: e possivel construir `RouteSimulator(graph, RouteSimulator.max_speed_of(graph))` com heuristica garantidamente admissivel.

### Checkpoint 2 - Rota direta e espera dinamica
Grafo sintetico `A -> B` com varias partidas.
- [ ] Teste: consulta em `t` antes da primeira partida escolhe a primeira partida `>= t` e a chegada e `departure_time + travel_time`.
- [ ] Teste: partida exatamente em `t` e aceita (espera zero, valida `bisect_left`).
- [ ] Teste: conexoes que partiram antes de `t` sao ignoradas.
- [ ] Teste: `origin == destination` retorna `[]`.
- [ ] Teste: sem partidas apos `t` retorna `None`.
- [ ] Implementar `calculate_route` com `heapq`, `bisect_left`, contador de desempate e conjunto fechado.
- [ ] Commits: `test(routing): specify direct route and dynamic waiting` e `feat(routing): implement time-dependent A* core`.

Pronto quando: os cinco testes passam e os testes existentes de Haversine/heuristica/snap continuam verdes.

### Checkpoint 3 - Reconstrucao do caminho, transferencias e modal WALK
- [ ] Teste: cadeia `A -> B -> C` retorna duas tuplas na ordem correta com as estacoes de embarque corretas.
- [ ] Teste de transferencia: chegar em `B` as 10:05 nao permite embarcar em partida de `B` as 10:00; deve pegar a seguinte.
- [ ] Teste de modal `WALK`: conexao de caminhada (`VehicleType.WALK` com `departure_time == 0.0`) pode ser percorrida no instante `t > 0` com saida imediata `t` e chegada `t + travel_time`.
- [ ] Teste integrado com `TemporaryVertex` e `snap_to_network`: rota entre vertices temporarios gerados pelo context manager.
- [ ] Teste "mais rapido nem sempre e o primeiro": em `A`, linha lenta sai 08:00 e chega em `B` 09:00; linha rapida sai 08:10 e chega 08:30. Deve escolher a rapida.
- [ ] Teste "menos trechos nem sempre e melhor": rota direta `A -> C` chega 10:00; rota `A -> B -> C` chega 09:30. Deve escolher a de dois trechos.
- [ ] Teste: destino inalcancavel (componente desconexa) retorna `None`.

Pronto quando: todos passam; a reconstrucao percorre `predecessor` e inverte.

### Checkpoint 4 - Prova de otimalidade (A* contra Dijkstra)
- [ ] Teste de propriedade com `random.Random(seed)` fixo: gerar varios grafos sinteticos (ex.: 30 estacoes, 300 conexoes, coordenadas proximas de BH, `travel_time` coerente com a distancia).
- [ ] Para pares aleatorios, comparar o horario de chegada do A* (com `max_speed_of(graph)`) com o de `RouteSimulator(graph, float("inf"))` (heuristica nula, ou seja, Dijkstra dependente do tempo).
- [ ] Os horarios de chegada devem ser identicos (os caminhos podem diferir em empates). `None` deve coincidir.
- [ ] Teste: cada trecho retornado respeita validade temporal (chegada do trecho anterior <= partida do proximo trecho).

Pronto quando: todos os pares coincidem. Se divergir, provar a causa (heuristica nao admissivel? poda incorreta?) antes de corrigir.

### Checkpoint 5 - Documentacao e plano
- [ ] Criar `docs/ROUTE_SIMULATOR.md` (portugues, conciso, no padrao de `docs/TIME_UTILS.md`): modelo de custo, contrato de saida, decisoes da secao 4.6, complexidade.
- [ ] Complexidade a documentar: $O((V + E)\log V)$ para as operacoes de heap, mais $O(\log K)$ por expansao para o `bisect`, mais a varredura apos o `bisect`. Espaco $O(V)$ para `g`, `predecessor`, `closed` e heap.
- [ ] Atualizar `Artefatos/Diagramas/diagrama-classes.md`: em `RouteSimulator`, trocar `find_route(...) Itinerary` por `calculate_route(origin, destination, departure_time) list` e incluir `max_speed_of(graph)$ float`.
- [ ] Marcar em `docs/PLAN.md` (Parte 5) os quatro itens cobertos, sem alterar o texto.
- [ ] Commit: `docs(routing): document time-dependent A* engine`.

### Checkpoint 6 - Validacao com o dataset real (manual, nao vai para o pytest)
Requer `git lfs pull` (ver `data/gtfs/README.md`). O `DataLoader` deve carregar o servico padrao/dominante.
- [ ] Script descartavel (nao versionar) que carrega o grafo com servico padrao, calcula `max_speed_of` e executa 10 consultas entre estacoes reais em horarios de pico (07:00) e fora de pico (14:00).
- [ ] Registrar tempo por consulta (`time.perf_counter`), numero de estacoes expandidas e se a rota foi encontrada.
- [ ] Anexar os resultados em `docs/ROUTE_SIMULATOR.md` (secao "Validacao com dados reais").
- [ ] Se alguma consulta passar de ~5 s, **parar e consultar o responsavel** com as medicoes antes de otimizar.

### Checkpoint 7 - Entrega
- [ ] Suite completa verde (149 testes existentes + novos testes).
- [ ] Revisar o diff: nada de NetworkX, nomes em ingles, sem codigo morto, sem emojis.
- [ ] Abrir Pull Request para `main` descrevendo o que foi feito, as decisoes da secao 4.6 e os resultados do Checkpoint 6.

---

## 8. Criterios de aceite

1. `calculate_route` retorna o horario de chegada otimo, comprovado pelo Checkpoint 4.
2. Espera dinamica considerada: nenhuma conexao agendada parte antes da chegada na estacao.
3. Modal `WALK` tratado corretamente como continuo/sob demanda (saida imediata em `t`).
4. Compativel com `TemporaryVertex` e `snap_to_network`.
5. `heapq` e `bisect` nativos; nenhuma biblioteca de grafos.
6. Heuristica admissivel garantida pelo `max_speed_of`.
7. Testes cobrem rota direta, transferencia, modal `WALK`, rota sem caminho e origem igual ao destino.
8. `docs/PLAN.md`, diagrama de classes e `docs/ROUTE_SIMULATOR.md` atualizados.

## 9. Quando parar e consultar o responsavel

- Necessidade de alterar `Connection`, `TransportGraph` ou `DataLoader` (ex.: adicionar `trip_id`).
- Desempenho inaceitavel no Checkpoint 6.
- Divergencia A* x Dijkstra sem causa raiz identificada.
- Qualquer duvida sobre as decisoes da secao 4.6.
