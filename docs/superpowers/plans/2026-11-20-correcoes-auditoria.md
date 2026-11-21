# Plano de Implementação das Correções e da Finalização

> Execução aprovada em 20/11/2026. As tarefas seguem TDD e não autorizam commits.

## Task 1: Corrigir os rótulos do mapa

**Arquivos principais:** `frontend/js/map.js`, `frontend/css/styles.css`, testes frontend relacionados ao mapa.

1. Criar testes que falhem para contenção nos quatro limites, colisão A/B e conjuntos densos.
2. Extrair `calculateLabelTranslations(panelRect, labelRects, options)` como função pura.
3. Aplicar `padding=12` e `gap=14`, priorizando A acima e B abaixo sem mover marcadores.
4. Manter rótulos A/B visíveis; mostrar rótulos não selecionados apenas em foco ou hover, preservando o nome acessível.
5. Executar a suíte frontend e registrar os resultados.

## Task 2: Implementar a análise topológica

**Arquivos principais:** `backend/app/graph_analyzer.py`, `backend/tests/test_graph_analyzer.py`.

1. Criar testes que falhem para grafo vazio, cadeia, ciclo, componentes desconectados, CFCs, arestas paralelas, autoarestas e vértices temporários.
2. Implementar articulações com DFS iterativa e projeção não direcionada simples.
3. Implementar Tarjan iterativo para CFCs.
4. Implementar criticidade estrutural e ordenação determinística.
5. Executar testes focados, suíte backend e cobertura.

## Task 3: Criar o comando e o relatório topológico

**Arquivos principais:** módulos de CLI em `backend`, testes de CLI, `docs/analysis/topology.json`.

1. Criar testes que falhem para argumentos, formato JSON, metadados e erros.
2. Implementar CLI sem expor análise pela API REST.
3. Executar no dia de serviço `2026-11-17`, registrando tempo, pico de memória, contagens, Top 20 e tamanhos de CFCs.
4. Validar determinismo e formato do JSON.

## Task 4: Corrigir documentação e diagramas

**Arquivos principais:** documentação em `docs/`, fontes Mermaid e artefatos renderizados.

1. Alinhar classes, componentes, sequência, estados, casos de uso e histórias ao código disponível.
2. Substituir `find_route` por `calculate_route`; remover interfaces fictícias.
3. Explicitar criação do `Itinerary` pela API e snap-to-network interno.
4. Corrigir as complexidades do `RouteSimulator` e marcar planos antigos como históricos.
5. Alterar a especificação aprovada para `Status: aprovado`.
6. Renderizar e validar Mermaid, links, UTF-8, SVG, PNG, HTML e LaTeX.

## Task 5: Fixar dependências e ampliar o benchmark

**Arquivos principais:** `requirements.txt`, `backend/benchmarks/`, testes e documentação de benchmark.

1. Criar testes que falhem para seleção determinística e preservação de resultados incompletos.
2. Fixar as versões Python aprovadas.
3. Implementar amostragem com semente 42, faixas curta/média/longa, horários 07:00/14:00 e casos sem rota.
4. Implementar matriz 100/1.000/todas, 7 repetições, 2 aquecimentos, 4.096 MiB e 600 s.
5. Exigir equivalência A*/NetworkX e documentar medianas, dispersão, RSS, preparação, hashes, ambiente e limitações.
6. Verificar que `backend/app/` não importa NetworkX.

## Task 6: Validar a interface e atualizar capturas

**Arquivos principais:** testes de navegador e três capturas do protótipo.

1. Executar a aplicação com o GTFS real e verificar a rota `15140072` para `14788235` às `04:00`.
2. Usar Playwright visível em 1280x720, 1440x900 e 390x844, nos temas claro/escuro e movimento normal/reduzido.
3. Verificar autocomplete, Limpar, horário, loading, erro, ausência de rota, timeline e edição.
4. Confirmar zero erros de console, ausência de dependências externas inesperadas e rótulos A/B dentro do painel.
5. Abrir a inspeção anotada para aceite e substituir as três capturas por screenshots 1440x900 sem marca d'água.

## Task 7: Consolidar os artefatos acadêmicos

**Arquivos principais:** relatório SBC, PDF, apresentação, roteiro e auditoria de autoria em `docs/`.

1. Consolidar relatório SBC de 12 a 15 páginas com os resultados efetivamente medidos.
2. Compilar e inspecionar visualmente todas as páginas.
3. Criar apresentação de dez minutos e roteiro de vídeo de 12 a 18 minutos para seis integrantes.
4. Auditar autores e responsabilidades pelo histórico Git sem reescrever o histórico.
5. Manter a gravação como pendência humana até haver evidência.

## Task 8: Empacotar e verificar a entrega

**Arquivos principais:** pacote ZIP final e apenas checkboxes aplicáveis de `docs/PLAN.md`.

1. Executar suites, cobertura, `compileall`, `pip check`, `npm audit`, `git diff --check`, verificações LFS e compilação documental.
2. Gerar ZIP sem `.git`, `.venv`, `node_modules`, caches nem TXT brutos do GTFS.
3. Extrair em diretório temporário e validar instalação, testes e compilação do relatório.
4. Marcar somente checkboxes comprovadamente concluídos em `docs/PLAN.md`, sem alterar o texto dos itens.
5. Produzir relatório final com evidências, pendências humanas e commits propostos, sem criar commits.
