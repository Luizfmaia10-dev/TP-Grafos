# Histórias de Usuário - MVP RotasGraph

Histórias das funcionalidades disponíveis. O acompanhamento oficial fica em
[PLAN.md](../../docs/PLAN.md).

## US-01 - Informar origem e destino por endereço

Como passageiro, quero informar endereços de Belo Horizonte para conectar meu
ponto de partida e meu destino à rede de transporte.

- O autocomplete do Geoapify/OpenStreetMap retorna endereço e coordenadas.
- Na origem, recebo até vinte candidatas e posso trocar a recomendada por outra
  parada dentro do limite.
- No destino, a parada mais próxima dentro do limite é selecionada
  automaticamente.
- Alterar um endereço invalida as candidatas anteriores.

## US-02 - Configurar a caminhada aceitável

Como passageiro, quero definir limites diferentes para origem e destino para
controlar quanto aceito caminhar em cada ponta da viagem.

- Cada limite aceita qualquer metro inteiro entre 100 e 2.000; o padrão é 800.
- Posso salvar o limite antes de informar o endereço.
- Com endereço informado, a aplicação recalcula as candidatas e mostra a
  distância mínima necessária quando nenhuma parada cabe no limite.
- Uma parada de origem escolhida é preservada somente enquanto continuar dentro
  do novo limite.

## US-03 - Encontrar a menor chegada

Como passageiro, quero consultar a rota para um horário de partida para reduzir
o tempo total de espera e deslocamento.

- Com os dois endereços conectados e `HH:MM`, a busca usa conexões do dia de
  serviço e respeita caminhadas, partidas, esperas e durações.
- Com caminho viável, `calculate_route` retorna trechos e a API cria
  `Itinerary` com custos e instruções.
- Sem caminho, recebo `no-route` e posso ajustar os dados.
- As arestas temporárias são removidas ao final, inclusive quando há exceção.

## US-04 - Compreender o itinerário

Como passageiro, quero ver trajeto e etapas para interpretar a viagem.

- Com rota encontrada, vejo chegada, total, espera, deslocamento, distância
  aproximada e instruções em português.
- Mapa e timeline identificam os modais dos passos: ônibus vermelho, metrô azul
  e caminhada cinza. O mapa é esquemático.
- Ao editar a busca, o resultado é removido e os campos são preservados.

## US-05 - Recuperar-se de falhas

Como passageiro, quero mensagens e cancelamento para corrigir minha consulta.

- Editar dados durante a busca cancela a requisição e descarta respostas antigas.
- Limite fora de 100 a 2.000 metros, coordenadas inválidas, parada de origem
  fora do raio e ausência de parada apresentam erros específicos.
- Erros HTTP, indisponibilidade, falha de conexão e ausência de rota permitem
  tentar novamente; dados inválidos são sinalizados nos campos.

## US-06 - Preparar e validar a rede

Como operador, quero carregar GTFS por data para disponibilizar viagens ativas.

- A carga aplica calendários e exceções, higieniza registros e registra
  rejeições ou quarentenas em `loader.report`.
- `app.validate_gtfs` verifica invariantes e exporta contagens, hashes,
  tempo e pico de memória do processo.
- A API reutiliza a rede da inicialização; trocar a data exige reinício.

## US-07 - Examinar a topologia

Como analista, quero executar a CLI topológica para identificar cortes
estruturais e componentes da malha.

- `app.analyze_topology` recebe diretório GTFS e `--date` e exporta JSON com
  articulações, tamanhos de CFCs e até vinte estações com criticidade positiva.
- Articulações usam projeção não direcionada simples; CFCs usam Tarjan iterativo.
  Horários e vértices temporários são ignorados.
- O ranking usa criticidade decrescente, grau simples decrescente e ID crescente.
  Não mede demanda ou viabilidade temporal e não tem endpoint REST.

## US-08 - Comparar implementações de roteamento

Como analista, quero executar o benchmark para comparar chegada ótima, custos
de preparação, consulta e memória com a referência NetworkX.

- Entradas e ambiente ficam em JSON/CSV; falhas são preservadas como incompletas.
- Subgrafos com semente permitem experimentos de tamanho. O relatório separa
  preparação, consultas e RSS e não extrapola superioridade geral.

Consulte [API.md](../../docs/API.md), [GRAPH_ANALYZER.md](../../docs/GRAPH_ANALYZER.md)
e [BENCHMARK.md](../../docs/BENCHMARK.md).

## Referências do padrão

- [Agile Alliance - User Story Template](https://agilealliance.org/glossary/user-story-template/)
- [Agile Alliance - INVEST](https://agilealliance.org/glossary/invest/)
- [Cucumber - Gherkin Reference](https://cucumber.io/docs/gherkin/reference/)
