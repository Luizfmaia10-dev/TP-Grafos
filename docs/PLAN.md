# Plano Geral de Desenvolvimento (Trabalho Pratico - Grafos)

Projeto: Otimizador de Rotas de Transporte Urbano (MVP)
Equipe: Caio Cesar Falinacio dos Santos, Gabriel Aredes, Joaquim Antonio, Luiz Fernando Cunha Maia, Pedro Henrique Nogueira, Wanessa Oliveira Marcos.
Disciplina: Teoria dos Grafos e Computabilidade - PUC Minas
Data Limite: 22/11/2026 23:59

---

## Parte 1: Planejamento e Documentacao Inicial
- [x] Consolidar requisitos e limitacoes academicas no arquivo `AGENTS.md`.
- [x] Padronizar toda a arquitetura de codigo e entidades de dominio em ingles.
- [x] Especificar o diagrama UML de classes em Mermaid com as classes `Station`, `TemporaryVertex`, `Connection`, `VehicleType`, `TransportGraph`, `DataLoader`, `RouteSimulator`, `Itinerary`, `TimeUtils`.
- [x] Criar o diagrama de componentes justificando a separacao em camadas (Data Ingestion, Core Graph Engine, API Controller, Presentation).
- [x] Revisao e aprovacao do plano de trabalho por todos os 6 membros da equipe.

## Parte 2: Scaffolding e Infraestrutura
- [x] Configurar a estrutura de diretorios do projeto: `backend/` (`app/`, `tests/`), `frontend/`, `docs/`, `data/`.
- [x] Configurar ambiente virtual Python (`venv`) e `requirements.txt` com dependencias estritas (`fastapi`, `uvicorn`, `pytest`, `pytest-cov`, e `networkx` exclusivo para benchmarks de performance).
- [x] Configurar suite de testes automatizados com `pytest` para a aplicacao do Test-Driven Development (TDD).
- [x] Criar endpoint basico de teste (`/health`) em FastAPI e servir o prototipo estatico da interface para validar o ciclo completo localmente.

## Parte 3: Ingestao de Dados (Data Ingestion)
- [ ] Obter e organizar o dataset de transporte publico de Belo Horizonte (BHTRANS / GTFS) no diretorio `data/`, mantendo os parsers desacoplados para permitir troca de fonte de dados se necessario.
- [ ] Implementar a classe `TimeUtils` com testes unitarios (conversao de strings `HH:MM:SS` para minutos inteiros e vice-versa).
- [ ] Implementar a classe `DataLoader` para leitura dos arquivos CSV/GTFS (`stops.txt`, `stop_times.txt`, `routes.txt`, `trips.txt`).
- [ ] Aplicar sanitizacao e tratamento de dados ausentes (coordenadas invalidas, horarios fora de ordem, paradas duplicadas).
- [ ] Instanciar os objetos de dominio `Station`, `Connection` e `VehicleType` com base nos dados higienizados.
- [ ] Validar cobertura de testes unitarios do modulo de ingestao.

## Parte 4: Estrutura do Grafo em Memoria
- [x] Implementar a classe `Station` com metodos especiais `__hash__`, `__eq__`, atributos geograficos (`latitude`, `longitude`) e identificador unico.
- [x] Implementar a classe `Connection` representando arestas direcionadas com destino, tipo de veiculo (`VehicleType`), tempo de percurso e horario.
- [ ] Implementar a classe `TransportGraph` utilizando lista de adjacencia baseada em dicionarios nativos do Python (`dict[Station, list[Connection]]`).
- [ ] Garantir complexidade $O(1)$ para adicao de vertices e recuperacao de vizinhos (`get_neighbors`).
- [ ] Implementar metodos para adicao e remocao de vertices e conexoes temporarias (`remove_temporary_vertex`).
- [ ] Proibir terminantemente qualquer dependencia de bibliotecas de grafos prontas nesta camada.
- [ ] Desenvolver bateria de testes unitarios em TDD para validar insercao, busca de adjacencias e consistencia da topologia.

## Parte 5: Motor de Roteamento (Algoritmo A*)
- [ ] Implementar a formula da distancia de Haversine em `RouteSimulator` para calculo de distancia geodésica em linha reta entre duas coordenadas.
- [ ] Formular a funcao heuristica consistente e admissivel $h(u, v) = \text{haversine}(u, v) / V_{\max}$, em que $V_{\max}$ e a velocidade maxima teorica observavel na rede.
- [ ] Implementar a busca heuristica A* dependente do tempo (*Time-Dependent A\**) na classe `RouteSimulator` utilizando a biblioteca nativa `heapq` para controle da fila de prioridade.
- [ ] Considerar o tempo de espera dinamico na estacao com base no horario de partida e tabela de horarios das conexoes.
- [ ] Reconstruir o caminho otimo a partir dos ponteiros de predecessores gerados pelo algoritmo.
- [ ] Escrever testes unitarios cobrindo cenarios com rotas diretas, transferencias entre linhas/modais e casos em que nao ha caminho viavel.

## Parte 6: Vertices Temporarios e Resposta Estruturada
- [ ] Implementar a especializacao `TemporaryVertex` e a logica de aproximacao (*snap-to-network*) a partir de cliques do usuario em coordenadas arbitrarias.
- [ ] Conectar o ponto temporario as estacoes mais proximas dentro de um raio configuravel (ex: 800m) criando arestas do modal `WALK` ponderadas pela velocidade media de caminhada (~5 km/h).
- [ ] Implementar a classe `Itinerary` para encapsular a solucao (tempo total de viagem, tempo de espera, distancia total percorrida e lista de instrucoes passo a passo).
- [ ] Implementar serializacao para dicionario e JSON no `Itinerary`.
- [ ] Garantir limpeza automatica dos vertices temporarios no grafo apos cada consulta.

## Parte 7: Interface Grafica (Frontend)
- [ ] Integrar o prototipo HTML/Tailwind ao backend FastAPI servido estaticamente.
- [ ] Garantir a aplicacao das cores do guia de design do `AGENTS.md` (Metro em Blue `#209dd7`, Onibus em Red `#e11d48`, Acoes em Purple `#753991`, Cabecalho em Navy `#032147`, Caminhada/Temporario em Yellow `#ecad0a` e Gray `#888888`).
- [ ] Implementar a interacao de selecao de origem e destino diretamente no mapa e via campos de texto.
- [ ] Exibir indicadores visuais de carregamento durante a consulta a API.

## Parte 8: Integracao Frontend + Backend
- [ ] Desenvolver endpoints REST no FastAPI:
  - `GET /stations`: listagem de estacoes disponiveis para autocompletar.
  - `POST /routes/search`: calculo de rota recebendo origem, destino e horario de partida.
- [ ] Conectar os eventos de clique e submissao do frontend as chamadas da API via `fetch`.
- [ ] Renderizar o itinerario retornado na timeline lateral com instrucoes discriminadas por modal.
- [ ] Desenhar o trajeto no mapa SVG com as cores e espessuras correspondentes a cada trecho.
- [ ] Tratar cenarios extremos no frontend (origem/destino identicos, estacoes desconexas, horario sem viagens disponiveis).

## Parte 9: Avaliacao de Desempenho e Complexidade
- [ ] Desenvolver scripts de benchmark comparando tempo de execucao e consumo de memoria do motor proprio de A* com o algoritmo de Dijkstra/A* do NetworkX (uso exclusivo para analise comparativa).
- [ ] Avaliar a escalabilidade variando o tamanho da base de dados e a distancia entre os pares de teste.
- [ ] Documentar analise formal da complexidade temporal e espacial na notacao Big-O para todas as estruturas centrais.
- [ ] Identificar limitacoes computacionais e oportunidades de otimizacao.

## Parte 10: Artefatos Finais e Entrega
- [ ] Redigir o relatorio tecnico em LaTeX aderindo estritamente ao template oficial da SBC (12 a 15 paginas).
- [ ] Detalhar formalmente no relatorio a modelagem do grafo, analise de corretude, complexidade e secao de responsabilidades com o trabalho individual dos 6 integrantes.
- [ ] Elaborar os slides para a apresentacao oral presencial (duracao exata de 10 minutos).
- [ ] Gravar e editar o video demonstrativo (12 a 18 minutos) com a participacao e explicacao de features por todos os 6 membros da equipe.
- [ ] Auditar o historico de commits no repositorio Git para garantir a presenca dos commits individuais de cada integrante.
- [ ] Gerar pacote final `.zip` contendo o codigo-fonte completo, o arquivo `.tex` fonte e o PDF compilado para submissao no Canvas ate 22/11/2026.
