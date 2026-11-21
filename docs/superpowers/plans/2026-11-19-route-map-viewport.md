# Route Map Viewport Implementation Plan

> Documento histórico: registra decisões e instruções da época, não tarefas abertas atuais. O progresso vigente está em [docs/PLAN.md](../../PLAN.md); contratos atuais em [API.md](../../API.md).

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Manter todos os segmentos e marcadores da rota visíveis no mapa SVG sem alterar o recorte de rotas que já cabem no mapa.

**Architecture:** Expandir o viewport base somente quando os pontos da rota ultrapassarem seus limites. O viewport preserva a proporção do layout e alimenta uma única transformação compartilhada pelo fundo, pelo SVG e pelos marcadores HTML.

**Final review clarification:** O viewport lógico base permanece exato para rotas contidas nele. Todo resultado contém a camada física no painel, reservando as caixas completas dos marcadores; uma extensão desfocada do mapa preenche o espaço externo sem deformar a camada principal. Cover fica restrito à busca/edição sem resultado. Essa regra corrige o corte demonstrado mesmo com coordenadas dentro do viewport base.

**Tech Stack:** Vanilla JavaScript, SVG, CSS e `node:test`.

**Spec:** `docs/superpowers/specs/2026-11-19-route-map-viewport-design.md`

## Global Constraints

- Funções, variáveis, classes e documentação interna de código permanecem em inglês.
- Não alterar backend, contratos HTTP, domínio, dataset ou dependências.
- Não criar commits sem autorização explícita do usuário.
- Aplicar TDD estrito: observar cada teste novo falhar pelo motivo esperado antes da implementação mínima.
- Rotas já contidas no recorte mantêm exatamente `0 0 960 780` no desktop e `0 0 358 256` no mobile.
- O viewport expandido deve manter a proporção `width / height` do layout.

---

### Task 1: Expandir o viewport e manter todas as camadas alinhadas

**Files:**
- Modify: `frontend/js/map.js`
- Modify: `frontend/tests/map.test.js`

**Interfaces:**
- Consumes: passos normalizados `{ vehicleType, origin, destination }` e os layouts existentes `desktop`/`mobile`.
- Produces: `fitRouteViewport(steps, layout, padding = 24)` retornando `{ x, y, width, height }`; `createStationMap` aplica esse viewport ao fundo, ao SVG e aos marcadores.

- [x] **Step 1: Escrever testes RED para o viewport puro**

Adicionar testes que exijam:

```js
assert.deepEqual(fitRouteViewport(inBoundsSteps, "desktop"), {
  x: 0, y: 0, width: 960, height: 780,
});

const viewport = fitRouteViewport([{
  vehicleType: "BUS",
  origin: { longitude: -44.02171289, latitude: -19.97429891 },
  destination: { longitude: -44.02377811, latitude: -19.97580814 },
}], "desktop");
assert.ok(viewport.y + viewport.height > 816.91 + 23);
assert.ok(Math.abs(viewport.width / viewport.height - 960 / 780) < 1e-9);
```

- [x] **Step 2: Executar os testes e confirmar RED**

Run: `node --test tests/map.test.js`

Expected: FAIL porque `fitRouteViewport` ainda não é exportada.

- [x] **Step 3: Implementar o cálculo mínimo do viewport**

Em `map.js`, partir do retângulo base, expandir seus quatro limites para conter
todos os extremos dos passos mais `padding`, e depois expandir apenas o eixo
menor até recuperar a proporção do layout. Uma lista vazia retorna o retângulo
base sem criar outra abstração.

- [x] **Step 4: Executar os testes puros e confirmar GREEN**

Run: `node --test tests/map.test.js`

Expected: PASS para viewport base, expansão e proporção.

- [x] **Step 5: Escrever testes RED de integração das camadas**

Estender a fixture do mapa e exigir que uma rota fora do recorte:

```js
assert.equal(route.attributes.viewBox, `${viewport.x} ${viewport.y} ${viewport.width} ${viewport.height}`);
assert.match(background.style.transform, /^matrix\(/u);
assert.ok(Number.parseFloat(originButton.style.top) >= 0);
assert.ok(Number.parseFloat(originButton.style.top) <= 100);
```

Após `map.update(selection, "origin")`, exigir `viewBox` base, transformação
identidade no fundo e ausência das linhas da rota. Repetir a verificação após
`resizeToMobile()`.

- [x] **Step 6: Executar os testes e confirmar RED de alinhamento**

Run: `node --test tests/map.test.js`

Expected: FAIL porque SVG, fundo e marcadores ainda usam planos diferentes.

- [x] **Step 7: Aplicar o viewport compartilhado**

Em `createStationMap.render()`:

- calcular uma vez `fitRouteViewport(result?.steps ?? [], layout)`;
- usar seus quatro valores no `viewBox`;
- aplicar ao `.network-background` uma matriz uniforme com escala
  `size.width / viewport.width` e translação proporcional a `-viewport.x` e
  `-viewport.y`;
- posicionar marcadores por `(point.x - viewport.x) / viewport.width` e
  `(point.y - viewport.y) / viewport.height`;
- usar `layer.clientWidth / viewport.width` no cálculo de densidade;
- deixar o viewport vazio produzir naturalmente a matriz identidade.

- [x] **Step 8: Executar teste do mapa e suíte frontend**

Run: `node --test tests/map.test.js`

Expected: PASS.

Run: `npm test`

Expected: todos os testes passam sem erros ou avisos.

### Task 2: Atualizar documentação e verificar o fluxo completo

**Files:**
- Modify: `frontend/README.md`
- Modify: `docs/FRONTEND_INTEGRATION.md`

**Interfaces:**
- Consumes: comportamento final aprovado na Task 1.
- Produces: instruções atuais para executar e conferir API, loading, timeline e mapa ajustável.

- [x] **Step 1: Remover o contrato histórico da demonstração**

Reescrever o início, execução e roteiro de conferência do README para descrever
`GET /stations`, `POST /routes/search`, horário `HH:MM`, estados de loading,
timeline e segmentos por modal. Remover números fixos de testes para evitar nova
desatualização.

- [x] **Step 2: Documentar o enquadramento ajustável**

Em `docs/FRONTEND_INTEGRATION.md`, substituir a limitação de pontos fora do
recorte pela regra: o mapa preserva o recorte original e expande o viewport
quando necessário, mantendo fundo, marcadores e segmentos alinhados.

- [x] **Step 3: Verificar documentação e build**

Run: `rg -n "consulta ainda usa a amostra local|Experimente a linha 50|88 testes" frontend/README.md`

Expected: nenhuma ocorrência.

Run: `npm run build && npm test`

Expected: build concluído e todos os testes aprovados.

- [x] **Step 4: Executar smoke com o GTFS real**

Iniciar o FastAPI com `GTFS_SERVICE_DATE=2026-11-17`, selecionar
`15140072` → `14788235` às `04:14` e verificar no navegador desktop e mobile:
loading, timeline, segmento BUS, marcadores dentro do painel e console limpo.

- [x] **Step 5: Verificação final sem commit**

Run: `git diff --check`

Expected: nenhuma saída.

Run: `git status --short`

Expected: somente os arquivos previstos neste plano; nenhum commit é criado.
