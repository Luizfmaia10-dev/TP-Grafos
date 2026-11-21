# Especificação das Correções da Auditoria Final

**Data:** 20/11/2026<br>
**Status:** aprovado<br>
**Escopo:** correções obrigatórias e recomendadas identificadas na auditoria integral do RotasGraph

## Objetivo

Eliminar as divergências funcionais, visuais, documentais e de reprodutibilidade
encontradas na auditoria, concluir os recursos acadêmicos ainda previstos para o
MVP e preparar um conjunto coerente de artefatos finais. A execução deve preservar
o motor de grafo em Python puro, a API atual baseada em estações e o frontend sem
framework JavaScript.

## Decisões de escopo

1. O fluxo público do MVP continuará recebendo estações por `origin_id` e
   `destination_id`. O encaixe de coordenadas arbitrárias permanecerá como
   capacidade interna do motor até existir um contrato REST específico.
2. Os diagramas descreverão separadamente o sistema implementado e as extensões
   planejadas. Nenhum componente futuro será apresentado como disponível.
3. `GraphAnalyzer` será implementado porque aparece como requisito arquitetural e
   item pendente do plano acadêmico.
4. O relatório de complexidade já produzido será uma fonte técnica do artigo SBC,
   não o artigo final.
5. As correções serão executadas em cinco planos especializados, coordenados por
   um plano mestre. Cada plano deverá produzir um resultado verificável de forma
   independente.
6. Commits serão propostos em português, com uma responsabilidade por commit, mas
   só serão criados após autorização explícita do responsável pelo repositório.

## Organização dos planos

### Plano 1 — Mapa e regressões visuais

Corrigir o algoritmo de posicionamento dos rótulos no mapa. A solução deverá:

- limitar rótulos nos eixos horizontal e vertical;
- preservar a posição geográfica dos marcadores;
- manter origem e destino identificáveis quando estiverem próximos;
- evitar que os vinte resultados do autocomplete tornem o mapa ilegível;
- funcionar nos recortes desktop e celular;
- respeitar `prefers-reduced-motion` e a árvore acessível existente.

O algoritmo de posicionamento continuará em `frontend/js/map.js`, mas sua parte
geométrica deverá ser extraída para uma função pura quando isso permitir testes
determinísticos. O DOM apenas medirá os retângulos, chamará a função e aplicará as
transformações retornadas.

Os testes unitários cobrirão limites superiores, inferiores e laterais, colisões
entre A e B e conjuntos densos. Uma verificação Playwright executará a rota real
`15140072` para `14788235` e uma pesquisa com vinte estações em 390×844 e
1280×720. Origem, destino e seus rótulos deverão permanecer dentro do painel.

### Plano 2 — Contratos e documentação coerente

Atualizar os artefatos para refletirem o código executado:

- diagrama de classes com as assinaturas reais de `Connection`, `DataLoader`,
  `Itinerary`, `RouteSimulator` e `GraphAnalyzer`;
- diagrama de sequência usando `calculate_route` e mostrando que a API constrói o
  `Itinerary` depois da busca;
- diagramas de estados, casos de uso e histórias de usuário sem alegar suporte
  público a coordenadas arbitrárias;
- diagrama de componentes distinguindo componentes implementados de componentes
  analíticos executados por linha de comando;
- `ROUTE_SIMULATOR.md` com o limite rigoroso da fila `heapq`;
- documentos históricos identificados como históricos, sem serem confundidos com
  o acompanhamento oficial de `docs/PLAN.md`.

As três capturas em `Artefatos/Prototipos/` serão substituídas por imagens da
interface atual, sem marca d'água. As cores deverão obedecer ao `AGENTS.md`:
ônibus vermelho, metrô azul, caminhada cinza e pontos temporários amarelos.

Todos os blocos Mermaid serão renderizados. Links locais, UTF-8, arquivos HTML,
SVG, PNG e o LaTeX serão validados automaticamente antes da conclusão.

### Plano 3 — Reprodutibilidade e benchmark

Substituir intervalos abertos de versões Python por versões comprovadas no
ambiente validado. O arquivo utilizado por instalações comuns deverá ser
reproduzível; dependências exclusivas de teste e benchmark permanecerão
identificadas, sem serem importadas por `backend/app/`.

A campanha de benchmark deverá usar o mesmo dia de serviço GTFS e registrar:

- pares curtos, médios e longos;
- horários de pico e fora de pico;
- casos com rota e sem rota;
- tamanhos crescentes da rede;
- aquecimentos e repetições suficientes para mediana e dispersão;
- tempo de preparação, tempo total da consulta, busca e memória RSS;
- hashes dos dados, versões, plataforma, commit e estado da árvore Git.

O A* próprio e a referência NetworkX deverão concordar sobre a chegada ótima ou
ausência de rota. Resultados incompletos por tempo ou memória serão preservados e
identificados, nunca removidos silenciosamente. O relatório não poderá concluir
superioridade geral com base apenas na amostra reduzida.

### Plano 4 — Análise topológica

Criar `GraphAnalyzer` como módulo de domínio desacoplado de FastAPI, frontend e
NetworkX. O módulo consumirá `TransportGraph` e oferecerá:

```python
class GraphAnalyzer:
    def __init__(self, graph: TransportGraph) -> None: ...
    def find_articulation_points(self) -> set[Station]: ...
    def find_strongly_connected_components(self) -> list[set[Station]]: ...
    def get_critical_stations(self, top_n: int) -> list[Station]: ...
```

Para pontos de articulação, as arestas direcionadas serão projetadas em uma visão
não direcionada simples, decisão que deverá aparecer no relatório. Para
componentes fortemente conexos, será usado Tarjan em tempo `O(V + E)`. A análise
de criticidade ordenará estações por impacto estrutural definido e testado, sem
misturar volume de viagens ou métricas não disponíveis no domínio.

Os testes TDD cobrirão cadeia, ciclo, grafo desconectado, múltiplas componentes,
arestas paralelas, autoarestas e grafo vazio. A aplicação de `__slots__` será
obrigatória para qualquer nova classe de dados de alta cardinalidade.

### Plano 5 — Artefatos acadêmicos finais

Consolidar um artigo LaTeX no modelo SBC, com 12 a 15 páginas, contendo:

- problema e requisitos;
- modelagem do grafo temporal;
- ingestão e higienização GTFS;
- A* dependente do tempo e prova da heurística;
- análise formal de tempo e espaço;
- análise topológica;
- benchmark e limitações;
- arquitetura, interface e resultados;
- responsabilidades dos seis integrantes;
- referências e reprodutibilidade.

O artigo será compilado e inspecionado página por página. As afirmações numéricas
deverão apontar para dados versionados ou comandos reproduzíveis.

Os slides deverão caber em dez minutos e usar o mesmo vocabulário, cores e
números do artigo. O roteiro do vídeo deverá distribuir de 12 a 18 minutos entre
os seis participantes, indicando telas, comandos e responsabilidades. A gravação
em si depende da participação humana e não será declarada concluída apenas com o
roteiro.

Por fim, será auditado o histórico de commits por integrante. O pacote ZIP será
montado somente com código-fonte, fontes LaTeX, PDF, instruções, artefatos exigidos
e dados permitidos. Uma extração limpa deverá conseguir executar testes e
recompilar o relatório conforme as instruções documentadas.

## Ordem e dependências

1. Corrigir o mapa, porque existe um defeito funcional observável.
2. Implementar `GraphAnalyzer`, estabelecendo as assinaturas definitivas.
3. Atualizar contratos, diagramas e documentação com base no código definitivo.
4. Fixar o ambiente e executar a campanha de benchmark.
5. Produzir artigo, slides, roteiro e pacote final usando somente resultados
   verificados.

O plano mestre impedirá iniciar uma etapa que consuma resultados ainda não
produzidos. Em particular, o artigo não receberá números de benchmark provisórios
nem métodos fictícios de diagramas antigos.

## Tratamento de falhas

- Falha de teste interrompe a tarefa responsável; não será contornada alterando o
  teste para aceitar o comportamento defeituoso.
- Falha de benchmark por limite de recursos será registrada como resultado
  incompleto com causa, tamanho e ambiente.
- Falha de compilação ou diagrama impede considerar o artefato concluído.
- Ausência de conteúdo humano, como responsabilidades individuais ou gravação,
  será registrada como dependência externa, sem fabricação de informações.
- Nenhuma correção permitirá NetworkX no motor de produção.

## Estratégia de testes e aceitação

Cada implementação seguirá vermelho, verde e refatoração. Ao final de cada plano,
serão executadas as suítes focadas e a regressão aplicável. Antes da entrega final,
serão exigidos:

- suíte Python completa;
- suíte JavaScript completa;
- cobertura sem redução injustificada;
- build do frontend sem diferença inesperada;
- verificação HTTP dos recursos locais;
- navegador desktop e celular sem erro de console;
- carga e validação do GTFS real;
- renderização de todos os diagramas Mermaid;
- compilação e inspeção visual de todos os PDFs;
- `git diff --check`, `pip check`, auditoria npm e verificação do Git LFS;
- árvore Git contendo somente alterações esperadas antes de qualquer commit.

## Critério global de conclusão

As correções estarão concluídas quando não houver divergência entre comportamento,
API, diagramas, plano e relatório; a falha de rótulos do mapa estiver coberta por
regressão; a análise topológica e a campanha de escalabilidade tiverem resultados
reproduzíveis; e os artefatos acadêmicos existentes puderem ser gerados a partir
de uma extração limpa do repositório. Itens que dependam de ação humana serão
explicitamente identificados como pendentes.
