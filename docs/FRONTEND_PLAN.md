# Plano de desenvolvimento do frontend - tarefa #30

Data de referencia: 17/11/2026.
Revisao final: 18/11/2026.
Responsavel pelos commits: Gabriel Aredes.
Branch proposta para a implementacao: `codigo/30-interface-visual`.
Status: etapas 1 a 5 concluidas para a demonstracao da #30. Commits e envio da entrega final a cargo de Gabriel; integracao real acompanhada na #32.

## Referencias e ponto de partida

- [Prototipo Figma](https://www.figma.com/design/4UMBqFal4asnKlE4oKsIN8).
- Desktop inicial `3:4`, resultado desktop `3:446`, resultado celular `5:2852`.
- `AGENTS.md`, Parte 7 de `docs/PLAN.md` e historias US-01, US-03 e US-04.
- `Artefatos/Diagramas/diagrama-estados.md` e `docs/ISSUE_SERVICE_CALENDAR.md`.

No inicio do frontend, em 17/11, a verificacao confirmou `HEAD`, `origin/main` e a `main` do GitHub
em `a2434af46a85029b266999ba5e1e75e5cd60b2f8`. A pasta estava limpa.
O backend passou nos 138 testes existentes, com um aviso de descontinuacao do
TestClient relacionado a httpx. Naquela base, o frontend era um HTML com resultado fixo.

O pull trouxe `TemporaryVertex`, remocao da topologia temporaria,
`RouteSimulator.snap_to_network`, historias de usuario e diagramas adicionais.
A heuristica de Haversine e o DataLoader ja existem. A busca A* completa,
`Itinerary`, `GET /stations` e `POST /routes/search` ainda estavam pendentes.
Na revisao final de 18/11, a main remota ja continha A* e calendario. As
diferencas entre as bases e os contratos atuais estao em
[FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md).

Na etapa 1, o Figma forneceu o contexto detalhado e o screenshot do desktop.
A consulta seguinte do celular atingiu a cota MCP do plano Starter. As telas
mobile e seus screenshots foram construidos e revisados na rodada anterior.
Na etapa 4, o contexto do resultado celular forneceu o mapa e os icones que
estavam pendentes. Eles foram baixados e integrados sem alterar seus vetores.

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
um dia da semana ao seu `service_id`. A integracao deve conectar a configuracao
da API a selecao de calendario ja disponivel na main atualizada. O seletor de data so devera ser
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
- [x] Conferir o contexto do Figma e obter os recursos exatos da marca, icones,
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

- [x] Escrever testes para partida exatamente no horario, partida perdida,
      espera, segundos, consulta fora da amostra e busca sem conexao disponivel.
- [x] Criar a consulta assincrona demonstrativa sobre os horarios da amostra.
      Seu limite deve ficar documentado e identificado na interface.
- [x] Mostrar carregamento durante a operacao e impedir envios simultaneos.
- [x] Renderizar resumo, espera, tempo no veiculo, distancia aproximada e
      itinerario com segundos a partir do resultado.
- [x] Destacar as arestas e paradas selecionadas no mapa conforme o Figma.
- [x] Permitir editar a busca e repetir a consulta. Uma resposta antiga nao pode
      substituir o estado de uma consulta que ja foi alterada.
- [x] Mostrar ausencia de viagem na amostra para saidas apos a partida conhecida.
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

- [x] Comparar no navegador as telas inicial e de resultado com o Figma em
      1440 px e 390 px. Verificar tambem 360 px e larguras intermediarias.
- [x] Ajustar contraste, alinhamento, tipografia, espessura das arestas e
      etiquetas do mapa, mantendo nomes e tempos legiveis.
- [x] Conferir o fluxo completo por teclado e toque, labels, foco visivel,
      avisos acessiveis e tamanho dos alvos de interacao.
- [x] Garantir que busca, mapa e itinerario conservem o mesmo estado ao mudar
      o tamanho da janela. Ajustar altura e rolagem para o celular.
- [x] Respeitar a preferencia por movimento reduzido em animacoes de interface.
- [x] Verificar erros de console, recursos ausentes e funcionamento da pagina
      com os recursos locais da demonstracao.

**Criterio de conclusao**

Todos os estados da amostra sao utilizaveis com teclado e toque. Textos e botoes
ficam dentro de seus paineis e o itinerario segue legivel com nomes maiores.
A verificacao visual cobre a mudanca do mapa desktop para o recorte celular.

**Commit sugerido**

`fix(front): refina a leitura e a navegacao no desktop e celular`

## Etapa 5 - Regressao, documentacao e passagem para a #32

- [x] Testar o fluxo servido pelo FastAPI e conferir conteudo e tipo dos recursos
      HTML, CSS e JavaScript, evitando respostas HTML para caminhos de assets.
- [x] Executar os testes de comportamento do frontend e a suite Python completa.
- [x] Registrar comandos de build, execucao e teste, os limites da amostra e a
      procedencia dos dados junto deste plano.
- [x] Anotar os campos de consulta e resultado que precisarao de acordo com os
      responsaveis pela API e pelo Itinerary, incluindo unidades e erros.
- [x] Atualizar em `docs/PLAN.md` somente os checkboxes concluidos na #30.
- [x] Conferir o diff final e orientar Gabriel a selecionar os arquivos de cada
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

`stop_times.txt` contem esses registros nas linhas 3906806 a 3906808 na
versao de origem da amostra (base a2434af). `trips.txt` associa a viagem a linha e ao servico.
O dataset renovado da main precisa de revalidacao dos IDs e horarios para a #32.
A distancia de cerca
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
nao conseguiu verificar a URL da janela. Por isso, ate a etapa 3, o celular
usou um recorte responsivo do SVG desktop. Essa adaptacao foi substituida na
etapa 4 pelo SVG mobile exato do componente 2:503, obtido no contexto de 5:2852.
O checkbox de recursos exatos foi encerrado depois da conferencia dos arquivos.

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

## Etapa 3 - Consulta demonstrativa implementada

Os dois commits da etapa 2 foram conferidos na branch codigo/30-interface-visual:
acb2f00 contem a selecao de paradas e 7c21e82 registra a documentacao. Ambos
tem Gabriel como autor e committer. A pasta estava limpa antes desta etapa.

A consulta agora percorre o recorte conhecido de uma unica viagem da linha 50.
Sao aceitos os tres pares de paradas na ordem da viagem: Pampulha -> Rio de
Janeiro, Pampulha -> Av. Parana e Rio de Janeiro -> Av. Parana. A viagem de
volta e IDs fora da amostra produzem uma mensagem de limite do exemplo.
Nao e uma implementacao do A*, uma busca de outras viagens ou um calendario.

Todos os custos sao calculados em segundos inteiros desde o inicio do dia de
servico. Nao se usa Date nem se aplica resto por 24 horas. Partida exatamente
no horario do embarque e aceita; um segundo depois ja perde essa viagem.
Horarios HH:MM sao normalizados para HH:MM:00 antes da consulta.

| Consulta Pampulha -> Av. Parana | Espera | Onibus | Total exato | Chegada |
|---|---|---|---|---|
| 07:45:00 | 6 min | 29 min 16 s | 35 min 16 s | 08:20:16 |
| 07:50:59 | 1 s | 29 min 16 s | 29 min 17 s | 08:20:16 |
| 07:51:00 | 0 min | 29 min 16 s | 29 min 16 s | 08:20:16 |
| 07:51:01 ou 25:00 | Sem outra partida na amostra | - | - | - |

A amostra faz uma pausa local de 500 ms para tornar o carregamento observavel.
O botao fica indisponivel durante a operacao. Editar os campos, escolher uma
parada, limpar uma escolha ou usar o atalho cancela a consulta atual. Cada
consulta recebe uma versao: uma resposta anterior e ignorada mesmo quando o
servico nao respeita AbortSignal. Sem partida, trecho fora do exemplo e falha
inesperada tem mensagens diferentes. Os campos permanecem para nova tentativa.

No resultado, o total em minutos usa Math.round(totalSeconds / 60), seguindo
o resumo do desenho. O valor exato continua no texto acessivel e nos horarios
do itinerario, e a legenda mostra a espera e o tempo no onibus com segundos.
A barra divide os tempos usando os segundos originais, antes de arredondar.
As distancias sao a soma de Haversine entre as paradas (raio terrestre 6371 km),
com exibicao aproximada em km. Nao sao distancias medidas pelas ruas.

O SVG sobreposto liga somente as paradas do resultado, em vermelho de onibus.
No desktop, resumo e itinerario ficam a esquerda do mapa; no celular, a ordem
e resumo, mapa e itinerario. Editar busca retoma os mesmos campos e remove o
trajeto anterior. Para vertices muito proximos, o mapa conserva as coordenadas
e identifica A/B nas etiquetas, com marcadores menores. A legenda identifica
a linha e a etiqueta flutuante e omitida nesse trecho curto para evitar choque.

O resultado usa os recursos locais ja obtidos e as referencias das telas
3:446 e 5:2852. Na etapa 3, a etiqueta da linha usava o texto Linha 50, e o
icone branco e o mapa mobile exato ainda estavam pendentes. Esses recursos
foram obtidos e integrados na etapa 4, encerrando essa pendencia.

### Arquivos da etapa 3

| Arquivo | Responsabilidade |
|---|---|
| frontend/js/demo-service.js | Recorte da viagem, espera, custos em segundos, distancia e consulta local cancelavel |
| frontend/js/route-request.js | Carregamento, bloqueio de envios simultaneos, cancelamento e descarte de respostas antigas |
| frontend/js/route-view.js | Resumo e timeline gerados a partir do resultado |
| frontend/js/app.js | Eventos de consulta, resultado, avisos, edicao e foco |
| frontend/js/map.js | Arestas SVG, paradas da rota e legenda, sobre o mapa existente |
| frontend/index.html | Estrutura semantica dos estados e avisos acessiveis |
| frontend/styles/app.css | Arranjos do resultado, timeline e carregamento com movimento reduzido |
| frontend/assets/app.css | CSS compilado para executar sem CDN |
| frontend/tests/demo-service.test.js | 19 testes de horarios, recortes, distancias e cancelamento |
| frontend/tests/route-request.test.js | 6 testes de estados, concorrencia, resposta antiga e nova tentativa |

O formato local possui status (found, no-route ou outside-sample). Um resultado
found contem query, routeId, routeShortName, tripId, serviceId, boardingTime,
arrivalTime, waitingSeconds, vehicleSeconds, totalSeconds, distanceKm e stops
ordenadas. A camada de requisicao acrescenta idle, loading e error. Esse e um
formato da demonstracao: o contrato JSON real continua sendo acordado na #32
com os responsaveis pelo endpoint e pelo Itinerary, incluindo suas unidades.

Nenhuma dependencia foi adicionada, e nenhum arquivo de backend ou GTFS foi
alterado. docs/PLAN.md conserva os itens de carregamento da API e integracao
abertos, como definido neste plano. A consulta local nao conclui esses itens.

### Como testar a etapa 3

Em frontend/, execute npm test para os 63 testes (38 anteriores e 25 novos).
Use npm run build para reconstruir os recursos. Para abrir a pagina, use o
servidor FastAPI da etapa 1 com o ambiente Python do projeto ativo.

1. Acione Experimente a linha 50 e Calcular trajeto. Observe o carregamento,
   o resumo, a barra de tempos, as quatro etapas com segundos e o mapa vermelho.
2. Acione Editar busca. Confira os campos preservados e a remocao do resultado.
3. Repita com 07:51:00 e 07:50:59 para esperas de zero e um segundo.
4. Consulte 07:51:01 e 25:00. A mensagem deve indicar falta de partida nesta
   amostra, sem manter o resultado anterior nem afirmar indisponibilidade da rede.
5. Inverta origem e destino para conferir a mensagem de trecho fora do exemplo.
6. Comece uma consulta e edite o horario ou uma parada durante o carregamento.
   A resposta cancelada nao deve aparecer sobre a selecao editada.
7. Escolha Rio de Janeiro como origem e Av. Parana como destino, com 08:16:50.
   Confira espera de 1 s, percurso de 3 min 25 s e somente esse trecho no mapa.
8. Repita no celular, por teclado e toque, e redimensione a janela no resultado.

Os testes foram escritos antes dos modulos. As falhas iniciais de importacao
foram confirmadas e depois os 63 testes passaram. A verificacao no navegador
servido pelo FastAPI cobriu dez tamanhos de janela entre 320 e 1440 px, baixa
altura, ordem dos blocos, ausencia de overflow, teclado, toque e movimento
reduzido. Tambem cobriu envios repetidos, cancelamento por campo e parada,
resposta antiga de um servico que ignora cancelamento e falha seguida de
nova tentativa. Esses dois ultimos cenarios foram induzidos apenas no navegador
de verificacao, sem caminhos de erro artificiais na interface do produto.

As telas de carregamento, resultado desktop/celular, falta de partida e trecho
curto foram revisadas visualmente. Os recursos HTML/CSS/JS responderam com os
tipos corretos, sem erros de pagina, recursos ausentes ou chamadas externas.
Os 138 testes Python passaram; permanece apenas o aviso ja registrado do
TestClient. Ao final da etapa 3, as etapas 4 e 5 ainda estavam abertas.

## Etapa 4 - Refinamento visual e acessibilidade

Os commits ae7cbb4 (implementacao) e 09762c6 (documentacao) foram conferidos
na codigo/30-interface-visual, ambos com Gabriel como autor e committer. A
pasta estava limpa antes desta entrega. Nenhum commit foi feito pelo agente.

### Recursos exatos e leitura visual

O contexto de 5:2852 forneceu o SVG do mapa mobile 2:503, o onibus branco do
resultado e a seta de voltar. Os tres arquivos foram baixados das URLs do
Figma e preservados byte a byte. As consultas seguintes voltaram a encontrar
o limite do Starter, mas os recursos necessarios ja estavam disponiveis.

network-mobile.svg tem 358 x 256 unidades; o desktop conserva 960 x 780.
Cada layout usa os limites geograficos do respectivo desenho. projectStation
converte latitude/longitude em pixels nativos desse SVG. O ResizeObserver do
painel atualiza escala, marcadores, arestas e etiquetas ao redimensionar, sem
alterar a consulta ou os horarios. A escala conserva as proporcoes e as
dimensoes intrinsecas dos arquivos. As etiquetas sao mantidas dentro do recorte
e separadas quando o texto ampliado aproximaria seus retangulos; os vertices
geograficos permanecem nas coordenadas reais.

O refinamento preserva a paleta do AGENTS.md e aproxima o peso dos titulos e
do resumo da referencia. O texto dos controles ganhou contraste de borda e
foco; os nomes do mapa e suas legendas usam fundos solidos para leitura sobre
a malha. O indicador de norte recebeu role img com nome acessivel.

As fontes e suas alturas de linha passaram a usar rem. Resumo e itinerario
reorganizam suas colunas quando o espaco disponivel diminui ou a fonte-base
e ampliada a 200%. Os horarios conservam segundos e os nomes podem quebrar
linha. No DOM, o mapa vem antes do itinerario, acompanhando a ordem visual do
celular; a organizacao do desktop continua sendo feita pelas areas do grid.

### Sugestoes, avisos e foco

A medicao inicial reproduziu um clique perdido em Experimente a linha 50:
fechar as sugestoes e mostrar um erro no blur mudava a altura do formulario
entre o inicio e o fim do clique. As sugestoes agora sao um popup ancorado ao
campo. Enquanto um texto ainda nao confirmado e digitado, o espaco do eventual
erro fica reservado, com sua mensagem oculta ate a validacao. Assim o blur
nao desloca o alvo do clique. Campos vazios nao recebem erro apenas por
perderem foco. Confirmar uma sugestao continua sendo necessario para obter o ID.

Uma unica regiao de status anuncia contagens de sugestoes, falta de resultados,
selecao, limpeza, carregamento, resultado e erros. Mensagens repetidas nao sao
reescritas. Erros visiveis ficam associados ao campo por aria-describedby e
aria-invalid; erros ainda nao apresentados ficam fora da descricao acessivel.
Selecionar paradas iguais pelo mapa tambem anuncia o motivo da validacao.

O foco do teclado aparece no campo, na sugestao ativa e na etiqueta da parada.
As sugestoes suportam setas, Enter e Escape; Tab segue o fluxo dos controles.
O resultado transfere foco ao titulo, e Editar busca devolve foco ao formulario
com os dados preservados. Os alvos de nome das paradas conservam pelo menos
44 px de altura, oferecendo uma alternativa maior aos pontos do mapa. A
animacao de carregamento continua respeitando prefers-reduced-motion.

Foram usadas como referencias o
[padrao de combobox WAI-ARIA](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/),
as orientacoes de
[contraste de texto](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html),
[contraste de componentes](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)
e [tamanho dos alvos](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).
As cores foram medidas sem arredondar para decidir sua aceitacao. Exemplos:
texto secundario em branco 6,39:1; texto claro no painel do mapa 7,17:1;
borda do campo contra sua superficie 3,26:1 e contra o exterior branco 3,48:1;
foco roxo contra o campo 7,17:1; linha de onibus contra o mapa 3,14:1.
Os numeros exibidos aqui estao arredondados apenas para documentacao.

### Arquivos da etapa 4

| Arquivo | Responsabilidade nesta entrega |
|---|---|
| frontend/index.html | Semantica do norte, descricoes, popup e ordem de leitura; recursos exatos do resultado |
| frontend/styles/app.css | Contraste, foco, tipografia relativa, colunas adaptativas e leitura do mapa |
| frontend/assets/app.css | CSS recompilado, servido localmente |
| frontend/js/app.js | Avisos acessiveis, validacao sem deslocar o alvo e navegacao das sugestoes |
| frontend/js/map.js | Projecao desktop/mobile, escala e posicionamento das etiquetas no recorte visivel |
| frontend/js/route-view.js | Horario exato no texto acessivel do resumo |
| frontend/assets/maps/network-mobile.svg | Base mobile exata do Figma, sem redesenho |
| frontend/assets/icons/bus-white.svg | Onibus branco do resultado |
| frontend/assets/icons/arrow-left.svg | Seta de Editar busca |
| frontend/tests/map.test.js | Seis posicoes de referencia nos dois planos de coordenadas |

### Verificacao e limites

Os seis testes de projecao foram escritos antes da funcao, e a falha inicial
de importacao foi confirmada. A suite final possui 69 testes JavaScript
aprovados. Os 138 testes Python passaram, com o mesmo aviso do TestClient.
Nao houve alteracao de backend, GTFS ou dependencias do projeto.

O navegador verificou onze tamanhos de janela, entre 320 e 1440 px, incluindo
baixa altura e mudanca somente de largura. Foram 31 verificacoes de layout,
incluindo busca, resultado, quatro larguras com fonte-base a 200% e nomes
maiores no itinerario. Os campos e o resultado foram preservados no resize,
sem overflow horizontal ou corte das etiquetas. O fluxo demonstrativo da
etapa 3 foi repetido nos dez tamanhos de sua verificacao anterior.

O axe-core 4.14.1 foi usado somente na pasta externa de verificacao, sem entrar
no package.json. Nove estados foram analisados sem violacoes automaticas:
inicial desktop, sugestoes desktop, resultado desktop/celular, resultado com
texto ampliado, busca sem sugestoes, validacao, falta de partida e paradas
iguais. As ocorrencias de contraste que a ferramenta deixou para conferencia
manual envolviam sobreposicao do popup ou do SVG; foram conferidas por cores,
geometria e capturas de tela. Isso nao representa certificacao completa WCAG.
A semantica foi conferida pela arvore acessivel do navegador; NVDA e VoiceOver
nao foram executados nesta rodada.

Foram conferidos Tab/Shift+Tab, setas, Enter, Escape, foco visivel, acionamento
por toque e movimento reduzido. As telas inicial, sugestoes e resultado foram
comparadas com as referencias disponiveis do Figma; os estados de aviso, nomes
longos e texto ampliado tambem foram inspecionados. Nao houve erros de pagina
ou console, recursos ausentes ou requisicoes externas na demonstracao.

Para repetir: execute npm test em frontend/ e abra a pagina pelo FastAPI com
o comando da etapa 1. Percorra a busca apenas com teclado, repita por toque,
abra as sugestoes e acione o atalho do exemplo, calcule e edite a busca.
Confira tambem 390 e 360 px, fonte ampliada e a preferencia por movimento
reduzido. O CSS compilado ja acompanha a entrega; npm run build o reconstrui.

docs/PLAN.md conserva abertos os itens de consulta real a API e integracao.
Ao final da etapa 4, a etapa 5 permanecia separada para a consolidacao final e passagem para a #32.

## Etapa 5 - Revisao final e passagem para integracao

Revisao realizada em 18/11/2026 sobre codigo/30-interface-visual, a partir de
9b8ca4d. Os commits dcf012b (refinamento) e 9b8ca4d (documentacao) foram
conferidos com Gabriel como autor e committer; a pasta estava limpa.

### Entrega reproduzivel

frontend/scripts/check-server.mjs acrescenta a verificacao HTTP via
npm run check:server. O script usa apenas recursos nativos do Node: consulta
health e HTML, percorre os imports estaticos e as imagens literais dos modulos,
resolve as fontes do CSS e confere status, MIME e conteudo dos recursos locais.
URLs repetidas sao verificadas uma vez. CSS, JavaScript e SVG inexistentes
devem retornar 404, sem receber a pagina inicial como substituicao.

Os comandos completos para abrir, compilar e testar foram consolidados em
[frontend/README.md](../frontend/README.md). O README principal recebeu apenas
os links de execucao e de integracao. O navegador continua recebendo os mesmos
arquivos da interface; esta etapa nao altera a consulta ou o desenho.

| Verificacao nesta branch | Resultado |
|---|---|
| npm test | 69 testes JavaScript aprovados |
| npm run check:server | 31 testes HTTP aprovados, incluindo 25 URLs distintas de recursos |
| Suite Python completa | 138 testes aprovados; mesmo aviso de descontinuacao do TestClient |
| Navegador pelo FastAPI | Fluxos da amostra aprovados em desktop e celular, sem erros ou chamadas externas |
| Layout e acessibilidade | 31 verificacoes de layout e 9 analises axe sem violacoes automaticas |
| Build com npm ci e npm run build | CSS reproduzido sem mudar o arquivo versionado |
| Erro de entrega induzido | Servidor isolado devolvendo HTML como JavaScript foi corretamente rejeitado pelo novo comando |

A verificacao de layout retomou onze tamanhos de janela, quatro larguras com
fonte-base em 200% e nomes maiores no itinerario. A regressao de trajetos
repetiu carregamento, partida exata, espera de um segundo, viagem perdida,
25:00, trecho fora da amostra, edicao, cancelamento, resposta antiga ignorada,
falha seguida de nova tentativa, teclado, toque e movimento reduzido.

As capturas finais de busca/resultado desktop e celular foram conferidas.
As analises automaticas continuam complementadas pela revisao de cores,
sobreposicoes e arvore acessivel. NVDA e VoiceOver nao foram executados.
Ambiente usado: Node 22.20.0, npm 10.9.3, Python 3.14.4 e axe-core 4.14.1
somente na pasta externa de verificacao. O projeto nao recebeu dependencias novas.

### Situacao da main e acordos para a #32

A main observada em b107e234e70665c433d3708a8f3d48d7fbea21f9 ja trouxe o
A* calculate_route, selecao de calendario e dataset completo renovado. Foi
feita uma leitura das referencias remotas, preservando os arquivos e os
commits da branch da interface. Os numeros de testes desta entrega se referem
a base local; a nova base integrada precisara de sua propria regressao.

[FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md) registra a assinatura real
do roteador, a falta dos endpoints/Itinerary na revisao observada, o formato
local da consulta e resultado, unidades, arredondamento, erros, metadados de
linhas e pontos a generalizar no mapa, catalogo e timeline. Os IDs da amostra
historica nao foram revalidados no novo GTFS. O contrato definitivo sera
acordado com os responsaveis pela API e pelo Itinerary na #32.

docs/PLAN.md foi conferido: os tres itens de interface ja concluidos continuam
marcados. Carregamento durante consulta real a API e os itens de integracao
continuam abertos. Nao houve nova marcacao que atribuisse a demonstracao ao
backend real. As atualizacoes de A*/calendario feitas pelos colegas na main
serao preservadas ao reunir as bases para a proxima tarefa.

### Arquivos e registro da entrega

Somente estes seis arquivos pertencem a etapa 5:

- frontend/package.json: novo comando check:server, com o lockfile preservado.
- frontend/scripts/check-server.mjs: regressao da entrega HTTP.
- frontend/README.md: comandos, casos de conferencia e limites do exemplo.
- docs/FRONTEND_INTEGRATION.md: passagem para a #32.
- docs/FRONTEND_PLAN.md: conclusao e evidencias da etapa.
- README.md: links para os dois guias.

Os arquivos de backend, GTFS, estilos, mapas, fontes e logica da interface
foram preservados. Nenhum arquivo foi adicionado ao staging e nenhum commit
ou push foi feito pelo agente.

Na raiz do repositorio, Gabriel pode separar a verificacao no primeiro commit:

```powershell
git branch --show-current
git status --short
git add -- frontend/package.json frontend/scripts/check-server.mjs
git diff --cached --name-status
git diff --cached --check
```

A lista deve conter apenas esses dois arquivos, na codigo/30-interface-visual.
Depois da conferencia:

```powershell
git commit -m "test(front): verifica os recursos servidos pelo FastAPI"
git add -- README.md frontend/README.md docs/FRONTEND_INTEGRATION.md docs/FRONTEND_PLAN.md
git diff --cached --name-status
git diff --cached --check
```

O segundo grupo deve conter somente os quatro documentos. Depois da conferencia:

```powershell
git commit -m "docs(front): registra a revisao final e a passagem para a #32"
git log -2 --oneline
git status
git push -u origin codigo/30-interface-visual
```

Antes do envio, o status deve mostrar working tree clean. O envio publica a
branch da interface; a reuniao com a main atualizada deve seguir o fluxo da
equipe e a preparacao de base registrada no guia da #32.
