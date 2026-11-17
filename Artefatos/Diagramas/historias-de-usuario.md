# Histórias de Usuário - MVP RotasGraph

Estas histórias representam o MVP final planejado. Elas usam o formato
papel-capacidade-benefício e critérios observáveis em Given-When-Then.

## US-01 - Selecionar os pontos da viagem

**Como** passageiro, **quero** escolher origem e destino por estação ou clique
no mapa **para** planejar uma viagem mesmo quando meu ponto exato não coincide
com uma parada.

**Critérios de aceitação**

- **Dado** que as estações foram carregadas, **quando** pesquiso pelo nome de
  uma parada, **então** recebo opções compatíveis para origem ou destino.
- **Dado** um clique a até 800 metros de uma estação real, **quando** seleciono
  o ponto, **então** o sistema o conecta temporariamente à estação por caminhada.
- **Dado** um clique sem estação no raio permitido, **quando** tento usá-lo,
  **então** sou informado de que o ponto está fora da rede.

## US-02 - Encontrar a rota de menor tempo

**Como** passageiro, **quero** buscar a rota mais rápida para um horário de
partida **para** reduzir meu tempo total de deslocamento e espera.

**Critérios de aceitação**

- **Dado** origem, destino e horário válidos, **quando** solicito a busca,
  **então** o sistema considera viagens ativas, partidas, esperas e durações.
- **Dado** mais de um caminho viável, **quando** a busca termina, **então** o
  itinerário retornado possui o menor tempo encontrado pelo A* temporal.
- **Dado** um trecho de caminhada, **quando** ele é avaliado, **então** fica
  disponível imediatamente e usa velocidade média de 5 km/h.

## US-03 - Compreender o itinerário

**Como** passageiro, **quero** visualizar o trajeto e as instruções por etapa
**para** conseguir executar a viagem sem interpretar o grafo diretamente.

**Critérios de aceitação**

- **Dado** que uma rota foi encontrada, **quando** a resposta é exibida,
  **então** vejo tempo total, distância total e instruções passo a passo.
- **Dado** um itinerário com caminhada, ônibus e metrô, **quando** observo o
  mapa e a timeline, **então** cada trecho é identificado pelo modal correto.

## US-04 - Recuperar-se de uma consulta sem resultado

**Como** passageiro, **quero** receber mensagens claras quando a consulta não
puder ser atendida **para** corrigir os dados e tentar novamente.

**Critérios de aceitação**

- **Dado** origem e destino desconectados, **quando** a busca termina,
  **então** sou informado de que não existe rota viável.
- **Dado** um dado inválido ou uma falha tratável, **quando** a resposta chega,
  **então** a interface preserva os campos e permite uma nova tentativa.
- **Dado** qualquer término após criar pontos temporários, **quando** a consulta
  encerra, **então** nenhum vértice ou conexão temporária permanece no grafo.

## US-05 - Preparar a rede de transporte

**Como** operador de dados, **quero** carregar e validar uma versão coerente da
base GTFS **para** disponibilizar uma rede temporal confiável ao roteador.

**Critérios de aceitação**

- **Dado** um pacote GTFS válido, **quando** informo a data de serviço,
  **então** somente viagens ativas nessa data entram no grafo.
- **Dado** um registro inválido, **quando** a carga é executada, **então** ele é
  rejeitado ou colocado em quarentena com motivo registrado.
- **Dado** o fim da carga, **quando** consulto o relatório, **então** vejo
  contagens, rejeições, alertas, tempo e pico de memória.

## US-06 - Avaliar a resiliência da rede

**Como** analista da rede, **quero** identificar articulações e componentes
fortemente conexos **para** reconhecer hubs e regiões vulneráveis.

**Critérios de aceitação**

- **Dado** o grafo carregado, **quando** executo a análise, **então** recebo os
  pontos de articulação e os componentes fortemente conexos.
- **Dado** o resultado analítico, **quando** solicito as estações mais críticas,
  **então** recebo uma lista ordenada para uso no relatório acadêmico.

## US-07 - Medir desempenho e complexidade

**Como** analista da rede, **quero** comparar o motor próprio com uma referência
**para** demonstrar sua correção, consumo de memória e escalabilidade.

**Critérios de aceitação**

- **Dado** um conjunto reproduzível de pares de rota, **quando** executo o
  benchmark, **então** obtenho tempos e memória do motor próprio e da referência.
- **Dado** tamanhos diferentes da rede, **quando** comparo os resultados,
  **então** consigo relacioná-los às complexidades temporal e espacial descritas.

## Rastreabilidade

| História | Casos de uso relacionados | Plano |
|---|---|---|
| US-01 | Consultar estações; Selecionar origem e destino; Conectar ponto temporário | Partes 6 e 7 |
| US-02 | Buscar rota otimizada; Calcular menor tempo | Parte 5 |
| US-03 | Gerar itinerário; Visualizar trajeto e resumo | Partes 6 e 8 |
| US-04 | Validar consulta; Buscar rota otimizada | Partes 7 e 8 |
| US-05 | Carregar GTFS; Higienizar; Construir e validar grafo | Parte 3 |
| US-06 | Analisar resiliência; Identificar estações críticas | Parte 9 |
| US-07 | Comparar desempenho dos algoritmos | Parte 9 |

## Referências do padrão

- [Agile Alliance - User Story Template](https://agilealliance.org/glossary/user-story-template/)
- [Agile Alliance - INVEST](https://agilealliance.org/glossary/invest/)
- [Cucumber - Gherkin Reference](https://cucumber.io/docs/gherkin/reference/)
