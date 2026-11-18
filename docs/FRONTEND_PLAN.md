# Plano de desenvolvimento do frontend - tarefa #30

Data de referencia: 17/11/2026.
Responsavel pelos commits: Gabriel Aredes.
Branch proposta para a implementacao: `codigo/30-interface-visual`.
Status: etapas 1 (base visual) e 2 (selecao de paradas) implementadas e verificadas, com exportacao exata do mapa mobile pendente.

## Referencias e ponto de partida

- [Prototipo Figma](https://www.figma.com/design/4UMBqFal4asnKlE4oKsIN8).
- Desktop inicial `3:4`, resultado desktop `3:446`, resultado celular `5:2852`.
- `AGENTS.md`, Parte 7 de `docs/PLAN.md` e historias US-01, US-03 e US-04.
- `Artefatos/Diagramas/diagrama-estados.md` e `docs/ISSUE_SERVICE_CALENDAR.md`.

A verificacao desta rodada confirmou `HEAD`, `origin/main` e a `main` do GitHub
em `a2434af46a85029b266999ba5e1e75e5cd60b2f8`. A pasta estava limpa.
O backend passou nos 138 testes existentes, com um aviso de descontinuacao do
TestClient relacionado a httpx. O frontend atual e um HTML com resultado fixo.

O pull trouxe `TemporaryVertex`, remocao da topologia temporaria,
`RouteSimulator.snap_to_network`, historias de usuario e diagramas adicionais.
A heuristica de Haversine e o DataLoader ja existem. A busca A* completa,
`Itinerary`, `GET /stations` e `POST /routes/search` continuam pendentes.

O Figma forneceu o contexto detalhado e o screenshot do desktop nesta rodada.
A consulta seguinte do celular atingiu a cota MCP do plano Starter. As telas
mobile e seus screenshots foram construidos e revisados na rodada anterior.
A exportacao e a conferencia dos recursos restantes devem ser resolvidas na
primeira etapa antes de substituir qualquer recurso do desenho.

## Forma de trabalho

O desenvolvimento sera feito em cinco entregas verificaveis. Cada rodada de
codigo conclui uma etapa, demonstra o resultado, explica os arquivos e deixa
uma sugestao de commit. Esse e o ponto para Gabriel revisar, testar e registrar
o commit antes de seguirmos. As etapas podem ser agrupadas se Gabriel preferir.
Os commits acompanham entregas reais realizadas em sequencia.

Este documento pode ser registrado primeiro com a mensagem
`docs(front): planeja a implementacao da interface da tarefa #30`.

As etapas de implementacao abaixo ficam abertas ate a verificacao dos seus
criterios. `docs/PLAN.md` sera atualizado somente para itens efetivamente
concluidos. O carregamento visual com dados de exemplo da #30 nao conclui o
item de consulta real a API da Parte 7 nem os itens de integracao da Parte 8.

## Escopo e criterios da demonstracao

O frontend usa HTML semantico, Tailwind, CSS para a identidade visual e modulos
JavaScript nativos. O FastAPI existente serve a aplicacao e os recursos estaticos.
O modo demonstracao usa uma amostra pequena identificada na tela como exemplo.
O mapa apresenta um recorte esquematico da rede de Belo Horizonte.

Os estados visiveis sao selecao incompleta, sugestoes abertas, consulta pronta,
carregamento, resultado, ausencia de trajeto no exemplo e erro de validacao.
Selecionar uma parada pelo mapa ou pelo campo deve atualizar o mesmo estado.
Uma edicao invalida o resultado anterior. Mensagens preservam os campos para
permitir nova tentativa.

A linha 50 demonstra horarios de uma viagem especifica da base, sem atribuir
um dia da semana ao seu `service_id`. A selecao de calendario ativo e uma
dependencia da ingestao para a integracao real. O seletor de data so devera ser
conectado quando o contrato e o filtro de calendario estiverem definidos.

Cliques nas paradas da amostra fazem parte da #30. A selecao de coordenadas
arbitrarias usa o mecanismo de pontos temporarios ja implementado no backend
quando houver endpoints para essa consulta. O frontend recebe seus resultados
e mensagens de fora da rede na etapa de integracao.

## Organizacao prevista

```text
frontend/
  index.html
  styles/
    app.css                 # Tailwind e estilos de origem
  assets/
    app.css                 # CSS compilado servido pelo FastAPI
    fonts/                  # Inter e IBM Plex Mono com suas licencas
    icons/                  # Recursos usados no desenho
    maps/                   # Bases SVG desktop e celular
  js/
    app.js                  # Eventos, estado da consulta e renderizacao
    map.js                  # Selecao e destaque de pontos e trechos
    demo-data.js            # IDs, coordenadas e horarios da amostra
    demo-service.js         # Consulta assincrona limitada a amostra
docs/
  FRONTEND_PLAN.md
```

A estrutura e uma proposta inicial. Novos arquivos so aparecem quando tiverem
uma responsabilidade concreta na etapa. Funcoes puras e modulos pequenos devem
ser suficientes. Nomes e comentarios de codigo ficam em ingles, com interface
em portugues.

O Tailwind sera compilado com dependencia de desenvolvimento fixada e comando
de build documentado. O CSS gerado e os recursos locais acompanham a entrega
para a demonstracao funcionar sem depender de CDNs. O navegador executa o
JavaScript servido estaticamente. A configuracao de build sera minima.

## Etapa 1 - Recursos visuais e estrutura responsiva

- [x] Criar `codigo/30-interface-visual` a partir da main atualizada e registrar
      o estado inicial do projeto antes da implementacao.
- [ ] Conferir o contexto do Figma e obter os recursos exatos da marca, icones,
      mapa desktop e mapa celular, preservando suas proporcoes.
- [x] Centralizar as cores do AGENTS.md, tipografia Inter/IBM Plex Mono,
      espacamentos, bordas e estados de foco.
- [x] Preparar o build minimo do Tailwind e servir CSS, fontes e vetores locais.
- [x] Construir cabecalho, formulario semantico e area do mapa no layout inicial.
- [x] Implementar os arranjos desktop e celular com o mesmo formulario e estado.

**Criterio de conclusao**

As telas iniciais abrem pelo FastAPI em 1440 px e 390 px e seguem a referencia
visual. A ordem de leitura, o tamanho dos campos e os recursos locais funcionam
tambem em 360 px e nas larguras intermediarias. A pagina permite rolagem quando
o conteudo excede a altura, com ausencia de corte ou rolagem horizontal indevida.

**Commit sugerido**

`feat(front): estrutura a interface responsiva conforme o Figma`

## Etapa 2 - Dados da linha 50 e selecao de paradas

- [x] Registrar a origem dos dados de exemplo com `route_id`, `trip_id`,
      `service_id`, IDs das paradas, coordenadas e horarios.
- [x] Implementar sugestoes de paradas com selecao por mouse, toque e teclado.
- [x] Manter IDs selecionados separados do texto digitado. Editar o nome limpa
      a selecao anterior ate uma sugestao ser escolhida novamente.
- [x] Sincronizar as escolhas dos campos e dos marcadores A/B no mapa.
- [x] Implementar o atalho "Experimente a linha 50" e a limpeza das selecoes.
- [x] Validar origem, destino e formato de horario, aceitando HH:MM e HH:MM:SS
      com horas acima de 24. Normalizar HH:MM para HH:MM:00 na consulta.
- [x] Cobrir primeiro com testes as regras de validacao e transicoes que possam
      deixar um ID antigo associado a um texto novo ou aceitar pontos iguais.

**Criterio de conclusao**

O usuario preenche uma consulta pelos campos e pelo mapa com resultado identico.
Um nome digitado sem selecao, um horario invalido ou origem igual ao destino
produzem orientacao clara. As sugestoes suportam setas, Enter e Escape.
Os nomes, marcadores e foco se mantem corretos nas duas resolucoes.

**Commit sugerido**

`feat(front): permite selecionar paradas pelo mapa e pela busca`

## Etapa 3 - Consulta demonstrativa e resultado

- [ ] Escrever testes para partida exatamente no horario, partida perdida,
      espera, segundos, consulta fora da amostra e busca sem conexao disponivel.
- [ ] Criar a consulta assincrona demonstrativa sobre os horarios da amostra.
      Seu limite deve ficar documentado e identificado na interface.
- [ ] Mostrar carregamento durante a operacao e impedir envios simultaneos.
- [ ] Renderizar resumo, espera, tempo no veiculo, distancia aproximada e
      itinerario com segundos a partir do resultado.
- [ ] Destacar as arestas e paradas selecionadas no mapa conforme o Figma.
- [ ] Permitir editar a busca e repetir a consulta. Uma resposta antiga nao pode
      substituir o estado de uma consulta que ja foi alterada.
- [ ] Mostrar ausencia de viagem na amostra para saidas apos a partida conhecida.
      Um par fora do recorte deve informar a limitacao do exemplo.

**Criterio de conclusao**

A consulta de 07:45:00 da plataforma G4 ate Av. Parana, 162, mostra espera de
6 min, tempo no onibus de 29 min 16 s e chegada as 08:20:16. O total exato e
35 min 16 s. O resumo em minutos segue o desenho, com detalhamento acessivel
do valor exato. Uma consulta apos a partida dessa viagem nao reutiliza a rota.
A consulta de 25:00 demonstra a ausencia de partida na amostra.

**Commit sugerido**

`feat(front): apresenta o trajeto demonstrativo da linha 50`

## Etapa 4 - Refinamento visual e acessibilidade

- [ ] Comparar no navegador as telas inicial e de resultado com o Figma em
      1440 px e 390 px. Verificar tambem 360 px e larguras intermediarias.
- [ ] Ajustar contraste, alinhamento, tipografia, espessura das arestas e
      etiquetas do mapa, mantendo nomes e tempos legiveis.
- [ ] Conferir o fluxo completo por teclado e toque, labels, foco visivel,
      avisos acessiveis e tamanho dos alvos de interacao.
- [ ] Garantir que busca, mapa e itinerario conservem o mesmo estado ao mudar
      o tamanho da janela. Ajustar altura e rolagem para o celular.
- [ ] Respeitar a preferencia por movimento reduzido em animacoes de interface.
- [ ] Verificar erros de console, recursos ausentes e funcionamento da pagina
      com os recursos locais da demonstracao.

**Criterio de conclusao**

Todos os estados da amostra sao utilizaveis com teclado e toque. Textos e botoes
ficam dentro de seus paineis e o itinerario segue legivel com nomes maiores.
A verificacao visual cobre a mudanca do mapa desktop para o recorte celular.

**Commit sugerido**

`fix(front): refina a leitura e a navegacao no desktop e celular`

## Etapa 5 - Regressao, documentacao e passagem para a #32

- [ ] Testar o fluxo servido pelo FastAPI e conferir conteudo e tipo dos recursos
      HTML, CSS e JavaScript, evitando respostas HTML para caminhos de assets.
- [ ] Executar os testes de comportamento do frontend e a suite Python completa.
- [ ] Registrar comandos de build, execucao e teste, os limites da amostra e a
      procedencia dos dados junto deste plano.
- [ ] Anotar os campos de consulta e resultado que precisarao de acordo com os
      responsaveis pela API e pelo Itinerary, incluindo unidades e erros.
- [ ] Atualizar em `docs/PLAN.md` somente os checkboxes concluidos na #30.
- [ ] Conferir o diff final e orientar Gabriel a selecionar os arquivos de cada
      commit e enviar a branch `codigo/30-interface-visual`.

**Criterio de conclusao**

A interface completa da amostra funciona pelo servidor atual em desktop e
celular. A entrega tem verificacao visual, testes de comportamento e regressao.
O consumo futuro de `GET /stations` e `POST /routes/search`, a resposta real do
Itinerary, o calendario e os pontos arbitrarios ficam rastreados na #32 e nas
tarefas responsaveis por esses contratos.

**Commit sugerido**

`test(front): valida os fluxos da interface e os recursos estaticos`

A atualizacao documental da entrega pode acompanhar este commit ou um commit
`docs(front)` separado, conforme os arquivos efetivamente alterados.

## Dados verificaveis do exemplo

| Campo | Valor |
|---|---|
| Linha | 50 - Estacao Pampulha / Centro - Direta |
| route_id | `561929` |
| trip_id | `2662438S307679P075100` |
| service_id de origem | `307679`, sem inferir o seu calendario |
| Origem | `15252270`, Estacao Pampulha - Plataforma G4 |
| Partida | `07:51:00` |
| Parada intermediaria | `14792447`, Estacao Rio de Janeiro - Plataforma 1B |
| Horario intermediario | `08:16:51` |
| Destino | `14787448`, Avenida Parana 162 |
| Chegada | `08:20:16` |
| Consulta de referencia | `07:45:00` |

`stop_times.txt` contem esses registros nas linhas 3906806 a 3906808 nesta
versao. `trips.txt` associa a viagem a linha e ao servico. A distancia de cerca
de 9,0 km do prototipo e a soma aproximada dos segmentos Haversine entre as
tres paradas, coerente com a representacao atual de `Connection.distance`.
O desenho do mapa e esquematico. `shape_dist_traveled` tem outro significado
e nao deve ser misturado ao valor aproximado sem atualizar sua apresentacao.

## Limites e dependencias para a integracao

| Necessidade | Encaminhamento |
|---|---|
| Pesquisar todas as paradas | Contrato e endpoint da #31, consumido na #32 |
| Calcular o menor tempo real | Motor A* da #27 e endpoint de busca |
| Serializar etapas e custos reais | Itinerary da #29 |
| Usar um ponto arbitrario do mapa | Expor o snap-to-network da #28 na API |
| Selecionar viagens de um dia real | Calendario de servico da ingestao |

O exemplo concentra os dados conhecidos em `demo-data.js` e a consulta em
`demo-service.js`. Na #32, o controlador passa a consumir os endpoints e a
adaptar a resposta ao formato de apresentacao. A estrutura definitiva do JSON
sera acordada com a equipe. Uma resposta de falta de rota e uma falha de rede
devem produzir mensagens diferentes, mantendo a consulta para nova tentativa.

## O que deve destacar o frontend

A identidade visual vem da malha de Belo Horizonte, da marca RotasGraph e da
paleta de modais. O destaque funcional vem de mostrar claramente a espera,
o tempo de deslocamento e os horarios de cada etapa. Os mesmos valores devem
aparecer de forma consistente no resumo, no itinerario e no mapa. A navegacao
responsiva e o cuidado com foco, texto e proporcoes completam essa identidade.


## Etapa 1 - Execucao e verificacao local

A base visual usa o cabecalho, os campos e o mapa inicial do Figma. O formulario
e unico, com reorganizacao por CSS entre desktop e celular. O horario e um campo
de texto para acomodar as horas estendidas do dia de servico nas proximas etapas.
A busca e o atalho do exemplo estao desabilitados nesta entrega inicial.

O CSS compilado e as fontes acompanham o repositorio. Para abrir a pagina,
a partir de backend/, use o ambiente Python com as dependencias do projeto.

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abra http://127.0.0.1:8000/. Para interromper, use Ctrl+C no terminal.
Se o ambiente virtual nao estiver ativo, execute o mesmo comando com o caminho
do seu python.exe de ambiente virtual. O comando usa o FastAPI ja existente.

Para reconstruir o CSS e copiar as fontes, execute em frontend/ com Node.js 20+
e npm disponiveis. As versoes e a arvore de dependencias ficam fixadas no lockfile.

```powershell
npm ci
npm run build
```

Durante a edicao de HTML ou estilos, npm run watch:css recompila o CSS.
Edite frontend/styles/app.css. O arquivo frontend/assets/app.css e gerado.
Novos arquivos JavaScript da etapa 2 deverao ser adicionados ao @source se
contiverem classes Tailwind que nao aparecem no HTML.

A configuracao usa o CLI oficial do Tailwind.
[Referencia](https://tailwindcss.com/docs/installation/tailwind-cli).

### Recursos visuais e licencas

O mapa network-desktop.svg e os 11 SVGs de icones foram baixados dos recursos
que get_design_context forneceu para a tela 3:4. Os SVGs conservam seus bytes e
dimensoes de origem. O cabecalho, os textos, campos e etiquetas usam HTML e CSS.
Inter e IBM Plex Mono sao servidas como WOFF2 locais, com as licencas SIL Open
Font License copiadas dos pacotes Fontsource em assets/fonts/.

As consultas e a exportacao mobile do Figma foram bloqueadas pela cota MCP do
plano Starter. A tentativa pelo editor terminou porque o controle do navegador
nao conseguiu verificar a URL da janela. Por isso, o celular usa um recorte
responsivo do SVG desktop, com as etiquetas alinhadas ao mesmo plano de
coordenadas. Essa e uma adaptacao da referencia. A exportacao exata do mapa
mobile 2:503 continua pendente e o checkbox de recursos exatos permanece aberto.

### Verificacao manual desta etapa

1. Abra a pagina em 1440 x 900 e 390 x 844 e compare cabecalho, formulario,
   fontes, cores e mapa com as referencias.
2. Confira tambem 360 px e larguras intermediarias, com rolagem vertical quando
   necessaria e ausencia de rolagem horizontal.
3. Navegue com Tab. O link inicial salta para o planejador e os campos mostram
   foco visivel. Os labels ficam associados aos seus inputs.
4. Digite nos campos, redimensione a janela e confira que os valores permanecem.
5. Use a aba Network para verificar CSS, SVG e WOFF2 com status 200 e sem
   solicitacoes a CDNs. O servidor deve continuar retornando 200 em /health.
6. Execute python -m pytest em backend/ para conferir a regressao do projeto.

Os fluxos de selecao, validacao e consulta pertencem as etapas seguintes.


A verificacao desta entrega passou em dez tamanhos de janela, de 320 px a
1440 px de largura, incluindo desktop de baixa altura. Foram verificados
overflow horizontal, recorte das etiquetas do mapa, preservacao dos campos no
redimensionamento, carregamento de todos os SVGs e fontes, ausencia de chamadas
externas, navegacao por teclado e foco. As previas desktop, celular e tablet
foram inspecionadas visualmente. A suite Python permaneceu com 138 testes
aprovados e o aviso de descontinuacao do TestClient ja registrado.

## Etapa 2 - Selecao de paradas implementada

Os commits da etapa 1 foram conferidos na branch codigo/30-interface-visual.
9d1ed6b registra a base visual e 51be670 registra sua documentacao, ambos com
a autoria de Gabriel. A pasta de trabalho estava limpa antes da etapa 2.

A interface agora permite selecionar as tres paradas conhecidas do trecho
por sugestoes de nome ou pelos botoes do mapa. As buscas ignoram acentos e
maiusculas e consideram tambem as plataformas. As setas percorrem a lista,
Enter confirma a escolha e Escape fecha as sugestoes. Botoes Limpar apagam
cada escolha e o atalho da linha 50 preenche Pampulha, Av. Parana e 07:45.

O campo que recebe o proximo clique e identificado no mapa. E possivel
comecar pelo destino. Origem e destino aparecem como A e B e se mantem
sincronizados com os campos nas duas resolucoes. Se um nome selecionado for
editado, o ID antigo e apagado ate a escolha explicita de outra sugestao.
Paradas iguais geram mensagem de validacao e impedem preparar a consulta.

Horarios HH:MM e HH:MM:SS sao aceitos, com minutos e segundos entre 00 e 59.
Horas acima de 24 continuam no mesmo dia de servico. A preparacao da consulta
normaliza HH:MM para HH:MM:00. Nesta etapa, Calcular trajeto valida a selecao
e mostra a consulta preparada. O processamento assincrono da amostra e o
itinerario pertencem a etapa 3.

### Arquivos da etapa 2

| Arquivo | Responsabilidade |
|---|---|
| frontend/js/demo-data.js | IDs, nomes, coordenadas e procedencia dos horarios do trecho da linha 50 |
| frontend/js/selection.js | Estado da selecao, busca de nomes e validacao independente do DOM |
| frontend/js/map.js | Botoes de parada, projecao no SVG existente e marcadores A/B |
| frontend/js/app.js | Eventos dos campos e mapa, sugestoes, erros e preparacao da consulta |
| frontend/tests/selection.test.js | 38 casos de busca, horario, IDs e transicoes |

O HTML passou a carregar app.js como modulo. As sugestoes usam combobox e
listbox com aria-controls, aria-expanded e aria-activedescendant. O CSS de
origem inclui os arquivos JavaScript em @source e o CSS compilado acompanha
a entrega. O package.json habilita modulos nativos e o comando npm test com
o executor de testes do Node.js. A etapa nao acrescenta dependencias npm.

### Como testar a etapa 2

Em frontend/, execute npm test. Para gerar novamente o CSS, use npm run build.
A pagina continua disponivel pelo FastAPI com o comando da etapa 1.

1. Digite pampulha em Origem e escolha a sugestao por clique ou Enter.
2. Digite avenida parana em Destino e escolha a sugestao com seta e Enter.
3. Edite um nome escolhido. O marcador deve perder a letra e o botao de
   consulta deve ficar indisponivel ate a escolha explicita de outra parada.
4. Escolha os dois pontos pelos nomes no mapa e confira os campos. Repita
   com o destino primeiro, focando seu campo antes do clique.
5. Use Limpar e Experimente a linha 50 e confira os valores resultantes.
6. Selecione a mesma parada para os dois pontos e verifique a mensagem.
7. Experimente 25:15:30 e 08:60. O primeiro prepara a consulta sem perder
   segundos e o segundo produz orientacao de formato quando o campo perde foco.
8. Repita no celular e redimensione a janela com os campos preenchidos.

Os testes foram escritos antes do modulo de selecao. A falha inicial de
importacao foi confirmada e, apos a implementacao, os 38 casos passaram.
A verificacao no navegador pelo FastAPI passou para teclado, mouse e toque,
limpeza, selecao em ambas as ordens, IDs invalidados, horarios, nomes fora da
amostra e dez tamanhos de janela. As telas de busca e selecao foram revisadas
visualmente em desktop e celular. Os 138 testes Python tambem passaram, com
o aviso de descontinuacao do TestClient ja registrado na etapa 1.
