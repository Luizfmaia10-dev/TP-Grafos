# Etapa 1 – Modelagem e Planejamento da Solucao

## 1. Escopo da Etapa Conforme o Enunciado (TP.pdf)
> "Escolha do tema, definicao do problema, levantamento de dados e modelagem do grafo. A utilizacao de diagramas UML sera avaliado na modelagem.  
> **Entregavel**: Documento com a descricao do problema, justificativa da modelagem e plano de desenvolvimento."

---

## 2. Conteudo Deste Diretorio

1. **`DESCRICAO_E_MODELAGEM.md` (antigo `AGENTS.md`)**:
   - Tema selecionado: *Otimizacao de rotas urbanas com base em mapas e redes de transporte publico* (BHTRANS / GTFS de Belo Horizonte).
   - Definicao formal do problema e modelagem do grafo como um *Time-Dependent Graph* direcionado e ponderado.
   - Restricoes academicas atendidas: operacao 100% em memoria RAM, Python nativo com dicionarios, `heapq` e busca binaria `bisect`, sem bibliotecas prontas de processamento de grafos (como NetworkX no nucleo).
   - Otimizacao com `__slots__` para diminuir o overhead de memoria.
   - Modelação matematica da heuristica admissivel baseada na distancia de Haversine ($h(u, v) = \text{haversine}(u, v) / V_{\max}$).

2. **`PLAN.md`**:
   - Plano geral de desenvolvimento estruturado em 10 partes, com checkboxes de rastreabilidade de progresso e detalhamento de tarefas por fase.

3. **`GUIA_TECNICO_DIDATICO.md`**:
   - Documento tecnico detalhado que explica didaticamente toda a engenharia, os conceitos de grafos dependentes do tempo e a fundamentacao matematica.

4. **`diagramas-uml/`**:
   - `diagrama-classes.md`: Diagrama de classes UML completo com as entidades `Station`, `TemporaryVertex`, `Connection`, `VehicleType`, `TransportGraph`, `DataLoader`, `RouteSimulator`, `GraphAnalyzer`, `Itinerary` e `TimeUtils`.
   - `diagrama-componentes.md`: Diagrama de componentes com a justificativa de desacoplamento em 4 camadas (*Data Ingestion*, *Core Graph Engine*, *API Controller* e *Presentation*).
   - `diagrama-casos-de-uso.md`: Atores e casos de uso do usuario e do sistema.
   - `diagrama-sequencia-busca.md`: Diagrama de sequencia do fluxo de consulta de rota.
   - `diagrama-sequencia-inicializacao.md`: Diagrama de sequencia da inicializacao e carga do grafo.
   - `diagrama-estados.md`: Diagrama de estados das consultas e da interface.
   - `historias-de-usuario.md`: Historias de usuario (US-01 a US-04).

5. **`diagramas-renderizados/`**:
   - Arquivos vetoriais SVG e imagens PNG em alta resolucao dos diagramas UML e arquiteturais.

6. **`prototipos-ui/`**:
   - Prototipos visuais de interface (tela inicial, busca de rotas e instrucoes passo a passo).

---

## 3. Avaliacao de Completude
- [x] Escolha do tema justificada.
- [x] Levantamento de dados (GTFS BHTRANS).
- [x] Modelagem matematica do grafo dependente do tempo.
- [x] Diagramas UML obrigatorios (Classes, Componentes, Sequencia, Estados, Casos de Uso).
- [x] Plano de desenvolvimento estruturado.
- **Status**: **100% Concluido**. Nenhum item em falta nesta etapa.
