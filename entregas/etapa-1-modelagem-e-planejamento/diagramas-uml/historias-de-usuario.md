# Histórias de Usuário - MVP RotasGraph

Histórias das funcionalidades disponíveis. O acompanhamento oficial fica em
[PLAN.md](../../docs/PLAN.md).

## US-01 - Selecionar estações

Como passageiro, quero escolher origem e destino por nome, ID ou marcador de
parada no mapa para preparar minha consulta.

- Ao pesquisar um texto, recebo sugestões com nome e ID.
- Ao editar uma estação confirmada, seu ID é invalidado.
- Com paradas iguais ou horário inválido, o envio fica bloqueado.

O REST não aceita coordenadas arbitrárias; `snap_to_network` é interno,
com limite de 800 m.

## US-02 - Encontrar a menor chegada

Como passageiro, quero consultar a rota para um horário de partida para reduzir
o tempo total de espera e deslocamento.

- Com estações distintas e `HH:MM`, a busca usa conexões do dia de serviço
  carregado e respeita partidas, esperas e durações.
- Com caminho viável, `calculate_route` retorna trechos e a API cria
  `Itinerary` com custos e instruções.
- Sem caminho, recebo `no-route` e posso ajustar os dados.

## US-03 - Compreender o itinerário

Como passageiro, quero ver trajeto e etapas para interpretar a viagem.

- Com rota encontrada, vejo chegada, total, espera, deslocamento, distância
  aproximada e instruções em português.
- Mapa e timeline identificam os modais dos passos: ônibus vermelho, metrô azul
  e caminhada cinza. O mapa é esquemático.
- Ao editar a busca, o resultado é removido e os campos são preservados.

## US-04 - Recuperar-se de falhas

Como passageiro, quero mensagens e cancelamento para corrigir minha consulta.

- Editar dados durante a busca cancela a requisição e descarta respostas antigas.
- Erros HTTP, indisponibilidade, falha de conexão e ausência de rota permitem
  tentar novamente; dados inválidos são sinalizados nos campos.

## US-05 - Preparar e validar a rede

Como operador, quero carregar GTFS por data para disponibilizar viagens ativas.

- A carga aplica calendários e exceções, higieniza registros e registra
  rejeições ou quarentenas em `loader.report`.
- `app.validate_gtfs` verifica invariantes e exporta contagens, hashes,
  tempo e pico de memória do processo.
- A API reutiliza a rede da inicialização; trocar a data exige reinício.

## US-06 - Examinar a topologia

Como analista, quero executar a CLI topológica para identificar cortes
estruturais e componentes da malha.

- `app.analyze_topology` recebe diretório GTFS e `--date` e exporta JSON com
  articulações, tamanhos de CFCs e até vinte estações com criticidade positiva.
- Articulações usam projeção não direcionada simples; CFCs usam Tarjan iterativo.
  Horários e vértices temporários são ignorados.
- O ranking usa criticidade decrescente, grau simples decrescente e ID crescente.
  Não mede demanda ou viabilidade temporal e não tem endpoint REST.

## US-07 - Comparar implementações de roteamento

Como analista, quero executar o benchmark para comparar chegada ótima, custos
de preparação, consulta e memória com a referência NetworkX.

- Entradas e ambiente ficam em JSON/CSV; falhas são preservadas como incompletas.
- Subgrafos com semente permitem experimentos de tamanho. A campanha completa
  e suas conclusões de escalabilidade permanecem pendentes no plano.

Consulte [API.md](../../docs/API.md), [GRAPH_ANALYZER.md](../../docs/GRAPH_ANALYZER.md)
e [BENCHMARK.md](../../docs/BENCHMARK.md).

## Referências do padrão

- [Agile Alliance - User Story Template](https://agilealliance.org/glossary/user-story-template/)
- [Agile Alliance - INVEST](https://agilealliance.org/glossary/invest/)
- [Cucumber - Gherkin Reference](https://cucumber.io/docs/gherkin/reference/)
