# Integração Visual e Revisão da API - Especificação

Data: 18/11/2026.

## Objetivo

Integrar ao frontend existente uma confirmação visual futurista da origem,
uma máscara de horário, um seletor de tema coerente com o RotasGraph e a
correção do fluxo de limpeza, preservando o autocomplete limitado às estações
da demonstração. Revisar os requisitos de `GET /stations`,
`POST /routes/search` e `Itinerary`, corrigindo apenas lacunas comprovadas.

## Estado atual confirmado

- O frontend é HTML, Tailwind compilado e JavaScript nativo. Não usa React.
- Origem e destino já oferecem um combobox acessível, mas pesquisam somente
  `DEMO_STATIONS`.
- A demonstração ainda consulta `searchDemoRoute`, sem `fetch` para a API real.
- O botão Limpar apaga a seleção, força foco no campo e reabre as opções com
  `openOptions()`, fazendo a limpeza parecer uma nova seleção.
- O horário é texto livre validado como `HH:MM` ou `HH:MM:SS` e aceita horas
  de serviço acima de 24; o contrato atual ainda permite segundos, contra a
  regra de entrada definida para esta entrega.
- `GET /stations` e `POST /routes/search` já existem, usam a rede carregada no
  ciclo de vida do FastAPI e possuem testes de sucesso e erro.
- `Itinerary` já usa `__slots__`, calcula totais, distância, passos e instruções,
  e serializa para dicionário e JSON.
- A resposta HTTP usa os cálculos de `Itinerary`, mas descarta
  `Itinerary.instructions` no adaptador para `RouteResult`.
- Há documentação da API que ainda afirma, incorretamente, que `Itinerary` não
  foi implementado.

## Decisões

### Compatibilidade tecnológica

Os componentes visuais de referência não serão instalados. O Expand Map da
21st e os componentes Kokonut foram feitos para React, enquanto o projeto exige
JavaScript nativo. Os comportamentos relevantes serão adaptados com CSS,
JavaScript, Web Animations e View Transitions, sem nova dependência de runtime.

### Autocomplete

O autocomplete continuará usando somente `DEMO_STATIONS`, conforme decisão do
responsável. O contrato e os testes existentes que invalidam o ID ao editar o
texto serão preservados. Esta entrega não marcará como concluída a integração
do frontend com `GET /stations`.

### Confirmação visual da origem

A transição será disparada quando todas as condições forem verdadeiras:

1. a origem tem um `stationId` confirmado por sugestão ou mapa;
2. o foco saiu de todo o contêiner do campo de origem;
3. essa estação ainda não recebeu a animação desde sua última seleção.

Mover o foco entre o input, o botão Limpar e a lista de opções não disparará a
transição. Selecionar uma sugestão e avançar ao destino contará como saída do
campo. Editar ou limpar a origem reiniciará o controle da animação.

No desktop, o painel do mapa receberá uma expansão curta, um contorno luminoso,
uma linha de varredura e um pulso no marcador da origem. No celular, além do
mesmo estado visual, o mapa será levado para a área visível. O nome da estação
confirmada será anunciado na região de status já existente. A animação não
mudará a seleção nem o grafo.

Com `prefers-reduced-motion: reduce`, o estado confirmado será aplicado sem
escala, deslocamento, varredura ou rolagem suave.

### Limpeza do campo

Limpar uma estação deve:

- remover texto e ID;
- cancelar uma consulta em andamento;
- fechar sugestões;
- retirar o estado visual confirmado;
- devolver foco ao input por acessibilidade;
- não reabrir opções até nova digitação, clique explícito no campo ou comando
  de teclado.

O campo ativo pode continuar sendo a origem ou o destino, mas nenhuma parada
será tratada como selecionada enquanto o ID for nulo.

### Máscara do horário

A máscara atuará na entrada, acompanhada da mesma validação estrita na API:

- `0745` vira `07:45`;
- `2515` vira `25:15`;
- texto já formatado como `07:45` permanece aceito;
- segundos nunca entram no valor: `07:45:30` é reduzido a `07:45` no campo e
  rejeitado pela API;
- caracteres que não sejam dígitos ou separadores válidos não entram no valor;
- apagar continua natural, sem recolocar separadores depois do cursor;
- na submissão, o frontend envia somente `HH:MM`.

O campo permanecerá `type="text"` com `inputmode="numeric"`. `type="time"` não
será usado porque seu domínio convencional não representa corretamente horas
GTFS acima de 23. A API aceitará somente `HH:MM`, inclusive para horas
estendidas. `TimeUtils` e os horários internos do GTFS continuarão usando
segundos; a rota REST acrescentará `:00` apenas ao entrar no motor.

### Tema

Um botão com semântica de switch será adicionado ao cabeçalho. O rótulo
acessível permanecerá estável e `aria-checked` indicará o tema escuro.

O tema claro preservará a aparência atual. O escuro usará as variáveis já
existentes como base: Navy para superfícies principais, painel de mapa para
cartões e campos, texto claro e a mesma paleta de modais e ações definida em
`AGENTS.md`. O tema será aplicado por atributo em `<html>` e salvo em
`localStorage`; na ausência de escolha, será usada a preferência do sistema.

Quando disponível e permitido pela preferência de movimento, a View
Transitions API revelará o novo tema em um círculo originado no botão. Sem essa
API ou com movimento reduzido, a troca será imediata. O controle funcionará
com clique, toque, Enter e Espaço e terá alvo mínimo de 44 por 44 pixels.

## Revisão dos requisitos de backend

### `GET /stations`

O requisito está implementado: pesquisa por nome ou ID, normalização de caixa
e acentos, limite de 1 a 100, IDs preservados como string, resposta vazia e
erros 422/503 possuem cobertura. Nenhuma alteração funcional é necessária.

### `POST /routes/search`

O requisito está implementado: recebe IDs de origem e destino e horário de
partida, valida entrada, usa o A* dependente do tempo e distingue rota
encontrada, rota inexistente, estação desconhecida e rede não configurada. A
lacuna é o formato ainda aceitar segundos. `departure_time` passará a aceitar
somente `HH:MM`; a conversão para `HH:MM:00` ocorrerá dentro da rota, antes de
chamar `TimeUtils`, sem alterar o algoritmo.

### `Itinerary`

O requisito de encapsular caminho, totais, distância, passos, instruções e
serialização está implementado. A lacuna é o adaptador HTTP não transportar as
instruções já calculadas. `RouteResult` passará a expor `instructions` e
`build_route_result` copiará a lista de `Itinerary`, sem recalcular nem gerar
texto na camada FastAPI. A documentação da API será corrigida para refletir o
estado real.

## Fluxo de dados

1. O usuário confirma uma estação da lista local ou do mapa.
2. `selectStation` armazena ID e rótulo; edição futura invalida o ID.
3. Ao sair do campo de origem, o controlador verifica se o ID é novo.
4. O mapa aplica o estado de confirmação e a transição apropriada ao viewport.
5. O usuário informa o horário `HH:MM` com separador automático; segundos não
   são aceitos.
6. A demonstração local continua responsável pela consulta nesta entrega.
7. Na API, quando usada diretamente, `Itinerary` continua sendo a fonte única
   dos custos, passos e agora também das instruções retornadas.

## Tratamento de erros e estados

- Limpar ou editar durante carregamento continuará cancelando a consulta.
- A animação nunca será executada para texto não confirmado.
- Repetir foco e blur na mesma origem não repetirá a animação.
- Uma nova origem poderá animar novamente.
- Falha no armazenamento do tema não impedirá a troca na sessão.
- Falta da View Transitions API não será considerada erro.
- Erros da API conservarão os contratos HTTP existentes.

## Arquivos previstos

- `frontend/index.html`: switch de tema e atributos do horário/mapa.
- `frontend/styles/app.css`: variáveis dos temas e estados das animações.
- `frontend/assets/app.css`: CSS compilado versionado.
- `frontend/js/app.js`: eventos de confirmação, limpeza e máscara.
- `frontend/js/map.js`: estado e animação da origem confirmada.
- `frontend/js/theme.js`: controle isolado e pequeno do tema.
- `frontend/js/time-mask.js`: transformação pura do valor digitado.
- `frontend/tests/theme.test.js`: decisão e persistência do tema sem DOM real.
- `frontend/tests/time-mask.test.js`: entrada, edição e horas estendidas.
- testes atuais de seleção/mapa: regressão da limpeza e confirmação quando
  observável em funções puras.
- `backend/app/api/route_models.py`: validação `HH:MM` e instruções no
  resultado.
- `backend/app/api/routes.py`: conversão interna para segundos e cópia das
  instruções de `Itinerary`.
- `backend/tests/test_routes_api.py`: contrato `HH:MM`, rejeição de segundos e
  JSON com instruções.
- `docs/API.md` e documentação do frontend: contrato e comportamento real.
- `docs/PLAN.md`: somente checkboxes dos itens efetivamente concluídos.

## Estratégia de testes

Toda função nova não trivial seguirá RED-GREEN-REFACTOR.

- Testes JavaScript puros cobrirão máscara, preferência inicial, alternância e
  controle que impede repetição da confirmação.
- Testes existentes do frontend cobrirão regressão de seleção, horários,
  cancelamento e mapa.
- Os testes da API falharão primeiro pela aceitação de segundos e pela ausência
  de `instructions`; depois validarão o contrato `HH:MM` e a lista produzida
  por `Itinerary`.
- Serão executados `npm test`, build do Tailwind, verificação HTTP dos recursos,
  suíte Python completa e inspeção responsiva em 375, 768, 1024 e 1440 pixels.
- Movimento reduzido e navegação por teclado serão conferidos no fluxo final.

## Fora do escopo

- Migrar o frontend para React.
- Instalar Framer Motion, shadcn ou bibliotecas de mapas.
- Consultar todas as estações pelo frontend nesta entrega.
- Trocar a demonstração local por `POST /routes/search` nesta entrega.
- Aceitar coordenadas arbitrárias no contrato HTTP.
- Alterar A*, calendário, `TransportGraph` ou `DataLoader`.
