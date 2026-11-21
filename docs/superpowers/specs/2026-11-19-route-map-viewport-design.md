# Enquadramento completo da rota no mapa

> Documento histórico: registra decisões e instruções da época, não tarefas abertas atuais. O progresso vigente está em [docs/PLAN.md](../../PLAN.md); contratos atuais em [API.md](../../API.md).

## Objetivo

Garantir que toda rota retornada por `POST /routes/search` permaneça visível no
mapa esquemático, inclusive quando suas estações estiverem fora do recorte
original de desktop ou mobile.

## Decisão

O viewport lógico original continua sendo a visualização mínima. Quando uma rota possui
pontos fora dele, o frontend expande o plano de coordenadas apenas o necessário,
com margem interna, sem aproximar rotas que já cabem no mapa. A expansão mantém
a proporção do layout para evitar deformação.

Todo resultado contém a camada física no painel e reserva espaço para as caixas
completas dos marcadores, mesmo quando o viewport lógico permanece no tamanho
base. Uma extensão desfocada e decorativa do próprio mapa preenche o espaço
externo sem deformar a camada principal. O dimensionamento cover fica restrito
à busca/edição sem resultado.

O mesmo viewport deve controlar:

- o `viewBox` do SVG da rota;
- a transformação do fundo esquemático;
- as posições percentuais dos marcadores;
- o cálculo de proximidade usado nos rótulos A/B.

Ao editar ou limpar a busca, o mapa restaura automaticamente o viewport base e
o dimensionamento cover.

## Escopo

- Alterar apenas a projeção/apresentação do mapa no frontend.
- Preservar as cores BUS, SUBWAY e WALK e o tracejado de caminhada.
- Preservar o contrato HTTP e os objetos normalizados existentes.
- Atualizar o README do frontend e o guia de integração.
- Não adicionar dependências ou alterar backend, domínio ou GTFS.

## Critérios de aceitação

1. Rotas contidas no recorte atual mantêm exatamente o `viewBox` lógico original
   (`0 0 960 780` no desktop e `0 0 358 256` no mobile), com contenção física da
   camada e das caixas dos marcadores dentro do painel.
2. A rota real `15140072` para `14788235`, às `04:14` no serviço de
   `2026-11-17`, fica integralmente visível em desktop e mobile.
3. Viewports expandidos mantêm a proporção nativa do layout.
4. Linhas e marcadores usam a mesma transformação e permanecem alinhados.
5. Editar ou limpar a busca remove a rota e restaura o viewport original e cover.
6. A suíte cobre RED e GREEN para os casos dentro e fora do recorte.
