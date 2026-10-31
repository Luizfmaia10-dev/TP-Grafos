# Ferramenta de Otimização de Rotas de Transporte Público (MVP)

## Requisitos de Negócios

Este projeto consiste no desenvolvimento de uma ferramenta computacional para resolver a otimização de rotas urbanas por meio da modelação de grafos.
- O sistema recebe bases de dados reais de trânsito urbano e converte-as num *Time-Dependent Graph* direcionado e ponderado.
- O utilizador pode selecionar uma estação de origem e uma estação de destino através de uma interface de interação.
- O sistema calcula e apresenta a rota otimizada com base no menor tempo de deslocação, considerando os pesos dinâmicos de horários de ligação e tempos de viagem.
- O resultado é apresentado visualmente no frontend, acompanhado de um itinerário passo a passo.

## Limitações

Para o MVP, a base de dados de transporte inicial será focada no trânsito de Belo Horizonte (BHTRANS / GTFS), mantendo arquitetura modular para permitir a substituição por outros datasets abertos sem impacto no motor do grafo.
Para cumprir os requisitos disciplinares, o motor do grafo funcionará inteiramente em memória (utilizando listas de adjacência nativas em Python) sem o suporte de bases de dados e sem a importação de bibliotecas prontas de processamento de grafos, como o NetworkX (salvo para benchmark analítico no relatório).
O foco primário do MVP é a demonstração da correção da solução matemática e a análise de complexidade espacial e temporal do algoritmo de roteamento implementado.

## Decisões Técnicas

- Núcleo de Algoritmos (Backend): Python puro, utilizando dicionários nativos e `heapq` para controle da fila de prioridade.
- Gerenciamento de Memória: Uso obrigatório de `__slots__` nas classes de domínio Python (`Station`, `Connection`, `Itinerary`, etc.) para eliminar a sobrecarga do `__dict__` por instância e otimizar o consumo de memória RAM.
- Consulta Temporal em $O(\log K)$: Ordenação das conexões de cada estação por horário de partida e utilização de busca binária (módulo nativo `bisect`) no motor de roteamento para localizar a próxima partida disponível em tempo logarítmico.
- Análise de Topologia e Vulnerabilidade: Implementação de algoritmos de Pontos de Articulação (DFS com função `lowpt`) e Componentes Fortemente Conexos (CFC via Kosaraju/Tarjan) como funcionalidade analítica de suporte à avaliação de resiliência da malha no relatório da SBC.
- Camada Controladora (API): FastAPI, expondo endpoints REST para cálculo de rotas e consulta de paradas.
- Interface Gráfica (Frontend): HTML/CSS (com Tailwind) e Vanilla JavaScript, responsáveis pela visualização do trajeto sobre a malha.
- Modelação Matemática: Algoritmo A* (A-Star) com heurística admissível baseada na distância de Haversine dividida pela velocidade máxima da rede ($h(u, v) = \text{haversine}(u, v) / V_{\max}$).
- Relatório Final: Escrito em LaTeX, aderindo rigorosamente ao template de artigo de conferências da SBC.

## Arquitetura e Entidades de Domínio

O domínio do sistema é estruturado em inglês com tolerância zero a acoplamento com a interface:
- `Station`: Vértice que representa paradas ou estações da rede, implementado com `__slots__` para eficiência de memória em grafos densos.
- `TemporaryVertex`: Especialização de `Station` para representar pontos arbitrários clicados pelo usuário.
- `Connection`: Aresta direcionada ponderada por tempo de percurso e horário de partida, utilizando `__slots__` para reduzir o consumo de RAM diante da alta cardinalidade de viagens.
- `VehicleType`: Enumeração dos modais suportados (`BUS`, `SUBWAY`, `WALK`).
- `TransportGraph`: Estrutura de lista de adjacência em memória com complexidade $O(1)$ para adição de nós e obtenção de vizinhos, mantendo listas de conexões ordenadas por horário de partida.
- `DataLoader`: Módulo de parsing e higienização de arquivos GTFS/CSV.
- `RouteSimulator`: Motor de execução da busca A* dependente do tempo com seleção de conexões via busca binária (`bisect`).
- `GraphAnalyzer`: Módulo responsável pelo cálculo de Pontos de Articulação (algoritmo DFS com função `lowpt`) e Componentes Fortemente Conexos (CFC via Kosaraju/Tarjan) para avaliar gargalos e resiliência da malha de transporte.
- `Itinerary`: Estrutura de dados que empacota o trajeto ótimo, custo total e instruções passo a passo.
- `TimeUtils`: Utilitários para conversão e manipulação de horários.

## Colorações

- Accent Yellow: `#ecad0a` para marcação de vértices temporários e pontos de interesse no mapa.
- Blue Primary: `#209dd7` para a renderização de ligações e arestas do modal Metro/Comboio.
- Purple Secondary: `#753991` para botões de submissão do formulário de pesquisa de rotas.
- Dark Navy: `#032147` para cabeçalhos principais do sistema.
- Red Transit: `#e11d48` para a renderização de ligações e arestas do modal Autocarro (Ônibus).
- Gray Text: `#888888` para textos de suporte, rótulos e indicação de arestas do modal Caminhada.

## Padrões de Codificação

1. Aplicação estrita de práticas de Test-Driven Development (TDD) e Extreme Programming (XP) em todas as etapas de desenvolvimento do motor de cálculo.
2. Utilização obrigatória do idioma Inglês para a nomenclatura de funções, variáveis, classes e documentação interna de código.
3. Isolamento arquitetural de domínio (MVC/Desacoplamento): a lógica e as estruturas do grafo matemático devem manter tolerância zero a dependências visuais da interface.
4. Keep it simple - NEVER over-engineer, ALWAYS simplify, NO unnecessary defensive programming. O foco crítico está em manter a complexidade Big-O restrita.
5. Be concise. Keep README minimal. IMPORTANT: no emojis ever.
6. When hitting issues, always identify root cause before trying a fix. Do not guess. Prove with evidence, then fix the root cause.
7. Otimização de memória: todas as instâncias de classes de dados/domínio de alta cardinalidade (`Station`, `Connection`, `Itinerary`, etc.) devem utilizar `__slots__` para eliminar o overhead do dicionário interno `__dict__`.

## Documentação

Todos os documentos analíticos, diagramas em código Mermaid, relatórios e o código-fonte `.tex` para a posterior geração do PDF avaliativo estarão contidos no diretório `docs/`.
Todos os documentos analíticos, diagramas em código Mermaid, relatórios e o código-fonte `.tex` para a posterior geração do PDF avaliativo estarão contidos no diretório `docs/`.
