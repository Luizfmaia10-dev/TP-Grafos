# Address Snap Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Status:** histórico. A entrega final usa Geoapify/OpenStreetMap, dois controles no cabeçalho e resolução livre por metro entre 100 e 2.000; consulte `docs/API.md` para o contrato vigente.

**Goal:** Permitir buscas de rota por endereços de Belo Horizonte, com autocomplete, limites independentes de caminhada e snap-to-network seguro nas duas extremidades.

**Architecture:** O navegador resolve endereços e coordenadas com `PlaceAutocompleteElement`; a API apenas publica a configuração, calcula candidatas e revalida a busca. `RouteSimulator` usa conexões temporárias locais à instância, sem modificar o `TransportGraph` compartilhado.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, pytest, HTML/CSS, Vanilla JavaScript, Node test runner, Google Maps JavaScript Places API (New).

**Spec:** `docs/superpowers/specs/2026-11-22-address-snap-flow-design.md`

## Global Constraints

- Código, nomes e documentação interna em inglês; textos da interface em português.
- Limites de caminhada entre 100 e 2.000 metros, em passos de 100 metros; padrão de 800 metros para origem e destino.
- Nenhuma biblioteca de grafos ou dependência espacial em produção.
- `TemporaryVertex`, modelos e estruturas de domínio de alta cardinalidade usam `__slots__`.
- A chave do Google fica somente em `.env.local`, ignorado pelo Git; nenhum teste, documento ou commit contém o valor.
- Endereço de destino permanece na página principal; endereço e escolha de parada de origem permanecem no modal de origem; o modal de limites altera apenas distâncias.
- Nenhum commit será criado sem autorização explícita do usuário.

---

### Task 1: Configuração local e carregamento seguro do Google Places

**Files:**
- Modify: `.gitignore`
- Create: `.env.example`
- Create (ignored): `.env.local`
- Create: `backend/app/api/config.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_config_api.py`

**Interfaces:**
- Produces: `GET /config/maps -> {"api_key": str | null, "available": bool}`.
- Consumes: `GOOGLE_MAPS_API_KEY` do ambiente ou da linha correspondente em `.env.local`.

- [ ] **Step 1: escrever teste falhando da configuração**

```python
def test_maps_config_uses_environment_key(monkeypatch, client):
    monkeypatch.setenv("GOOGLE_MAPS_API_KEY", "test-key")
    assert client.get("/config/maps").json() == {
        "api_key": "test-key", "available": True,
    }
```

Adicionar também teste sem chave, esperando `api_key is None` e `available is False`, sem registrar o valor nos logs.

- [ ] **Step 2: confirmar a falha**

Run: `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_config_api.py -q`

Expected: FAIL porque `/config/maps` ainda não existe.

- [ ] **Step 3: implementar configuração mínima**

Criar `read_local_setting(name: str) -> str | None` que prioriza `os.environ` e lê somente a chave solicitada de `PROJECT_DIR / ".env.local"`. Criar o router de configuração e incluí-lo antes do `StaticFiles`.

Adicionar a `.gitignore`:

```gitignore
.env.local
.superpowers/
```

Adicionar `.env.example`:

```dotenv
GOOGLE_MAPS_API_KEY=
```

- [ ] **Step 4: executar teste e verificação de segredo**

Run: `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_config_api.py -q`

Expected: PASS.

Run: `git check-ignore .env.local`

Expected: `.env.local`.

- [ ] **Step 5: checkpoint sem commit**

Registrar o conjunto de arquivos alterados e continuar; não executar `git commit`.

---

### Task 2: Candidatas de snap e conexões temporárias isoladas

**Files:**
- Modify: `backend/app/route_simulator.py`
- Modify: `backend/tests/test_route_simulator.py`

**Interfaces:**
- Produces: `SnapCandidate(station: Station, distance_km: float)` com `@dataclass(frozen=True, slots=True)`.
- Produces: `find_snap_candidates(latitude: float, longitude: float, max_distance_km: float) -> list[SnapCandidate]`.
- Produces: `snap_to_network(latitude, longitude, marker_type, max_distance_km, station_id=None, label=None)`.

- [ ] **Step 1: escrever testes falhando dos limites e ordenação**

```python
def test_find_snap_candidates_returns_only_real_stations_in_distance_order():
    candidates = simulator.find_snap_candidates(0.0, 0.0, 0.8)
    assert [item.station.station_id for item in candidates] == ["near", "far"]
    assert candidates[0].distance_km < candidates[1].distance_km
```

Cobrir 0,1 km e 2,0 km como válidos, valores externos como `ValueError`, coordenadas inválidas, `TemporaryVertex` ignorado e desempate por `station_id`.

- [ ] **Step 2: confirmar as falhas**

Run: `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_route_simulator.py -k "snap or candidate" -q`

Expected: FAIL por interfaces ausentes ou assinatura antiga.

- [ ] **Step 3: implementar candidatas e validação compartilhada**

Adicionar:

```python
MIN_SNAP_DISTANCE_KM = 0.1
MAX_SNAP_DISTANCE_KM = 2.0

@dataclass(frozen=True, slots=True)
class SnapCandidate:
    station: Station
    distance_km: float
```

Validar coordenadas e limite em funções privadas únicas. Varrer `graph.iter_stations()`, ignorar temporários, filtrar pelo limite e ordenar por `(distance_km, station_id)`.

- [ ] **Step 4: escrever testes falhando de isolamento**

Cobrir dois simuladores sobre o mesmo grafo, snap de origem escolhido, destino automático, rota com ambas as caminhadas e limpeza após sucesso e exceção. Durante e depois do contexto, `set(graph.iter_stations())` deve permanecer inalterado.

- [ ] **Step 5: substituir mutação global por overlay local**

Adicionar `_temporary_connections: dict[Station, list[Connection]]` aos `__slots__`. Fazer `calculate_route()` consultar `_neighbors(station)`, que combina conexões temporárias e reais preservando as caminhadas antes das partidas agendadas. `snap_to_network()` altera somente esse dicionário e remove suas entradas no `finally`.

Quando `station_id` for informado, aceitar somente uma candidata com esse ID. Usar `label` no nome do `TemporaryVertex`.

- [ ] **Step 6: verificar a unidade**

Run: `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_route_simulator.py -q`

Expected: PASS, inclusive os testes antigos adaptados ao novo limite parametrizado.

- [ ] **Step 7: checkpoint sem commit**

Revisar o diff de `route_simulator.py`; não executar `git commit`.

---

### Task 3: API de candidatas e busca por endereço

**Files:**
- Create: `backend/app/api/snap.py`
- Modify: `backend/app/api/route_models.py`
- Modify: `backend/app/api/routes.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_snap_api.py`
- Modify: `backend/tests/test_routes_api.py`

**Interfaces:**
- Produces: `POST /snap/candidates`.
- Produces: modo `address` em `POST /routes/search` sem remover o modo atual por IDs.
- Consumes: `RouteSimulator.find_snap_candidates()` e `RouteSimulator.snap_to_network()` da Task 2.

- [ ] **Step 1: escrever testes falhando do endpoint de candidatas**

```python
response = client.post("/snap/candidates", json={
    "latitude": -19.92,
    "longitude": -43.94,
    "max_walk_meters": 800,
})
assert response.status_code == 200
assert response.json()["candidates"][0]["distance_meters"] <= 800
```

Cobrir `snap_distance_out_of_range`, `invalid_coordinates`, `no_station_within_limit` e `503` sem rede.

- [ ] **Step 2: confirmar a falha**

Run: `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_snap_api.py -q`

Expected: FAIL com 404 do endpoint.

- [ ] **Step 3: implementar modelos e router de snap**

Criar modelos Pydantic com `extra="forbid"`. A resposta contém `minimum_distance_meters`, `count` e candidatas com estação e distância arredondada ao metro. Quando o limite atual não alcançar nenhuma candidata, `no_station_within_limit` inclui `minimum_distance_meters` se a estação mais próxima estiver dentro do máximo global de 2.000 m; acima disso, o campo será `null`. Traduzir `ValueError` do domínio para detalhes estruturados, sem comparar texto no frontend.

- [ ] **Step 4: escrever testes falhando da busca por endereços**

Usar payload:

```python
{
    "mode": "address",
    "origin": {"label": "Rua A", "latitude": -19.92, "longitude": -43.94,
               "max_walk_meters": 800, "station_id": "001"},
    "destination": {"label": "Rua B", "latitude": -19.91, "longitude": -43.93,
                    "max_walk_meters": 800},
    "departure_time": "07:45",
}
```

Verificar passos `WALK` no início e no fim, nomes dos endereços, parada de origem fora do limite, destino sem candidata e grafo inalterado. Manter todos os testes do payload antigo sem campo `mode`.

- [ ] **Step 5: implementar contrato compatível**

Manter `mode="station"` como padrão. O validador exige IDs no modo station e objetos de endereço no modo address. No controller, aninhar os contextos de snap, calcular o caminho e construir o resultado ainda dentro dos contextos.

- [ ] **Step 6: verificar API**

Run: `backend\.venv\Scripts\python.exe -m pytest backend/tests/test_snap_api.py backend/tests/test_routes_api.py -q`

Expected: PASS.

- [ ] **Step 7: checkpoint sem commit**

Executar `git diff --check`; não executar `git commit`.

---

### Task 4: Estado de endereços, limites e cliente HTTP

**Files:**
- Create: `frontend/js/address-selection.js`
- Modify: `frontend/js/api-service.js`
- Modify: `frontend/js/route-request.js`
- Create: `frontend/tests/address-selection.test.js`
- Modify: `frontend/tests/api-service.test.js`
- Modify: `frontend/tests/integration-flow.test.js`

**Interfaces:**
- Produces: `createAddressSelection()`, `setAddress()`, `setOriginStation()`, `setWalkLimit()` e `validateAddressSelection()`.
- Produces: `listSnapCandidates(point, options)`.
- Produces: `searchRoute(query, options)` serializando `mode: "address"`.

- [ ] **Step 1: escrever testes falhando do estado**

Cobrir valores iniciais de 800 m, destino ausente com limite válido, endereço confirmado, alteração que invalida candidatas, origem sem parada escolhida e rejeição de limites fora da faixa.

- [ ] **Step 2: confirmar a falha**

Run: `npm test -- --test-name-pattern="address|snap|walk limit"`

Workdir: `frontend`

Expected: FAIL porque o módulo não existe.

- [ ] **Step 3: implementar estado puro**

Representar cada ponto como `{ label, latitude, longitude, maxWalkMeters, candidates, stationId }`; destino não possui escolha manual de `stationId`. Toda mudança de endereço limpa candidatas; toda mudança de limite invalida candidatas anteriores.

- [ ] **Step 4: escrever testes falhando do cliente HTTP**

Verificar o JSON exato de `/snap/candidates` e `/routes/search`, `AbortSignal` e mapeamento dos códigos de erro estruturados.

- [ ] **Step 5: implementar cliente HTTP mínimo**

Reutilizar `readJson`, `mapStation` e `mapRouteResponse`; não criar wrapper de `fetch` adicional. Preservar os métodos de estações existentes para compatibilidade.

- [ ] **Step 6: verificar frontend puro**

Run: `npm test`

Workdir: `frontend`

Expected: PASS.

- [ ] **Step 7: checkpoint sem commit**

Registrar testes executados; não executar `git commit`.

---

### Task 5: Google Places e modais acessíveis

**Files:**
- Create: `frontend/js/google-places.js`
- Create: `frontend/js/dialog.js`
- Create: `frontend/js/snap-controls.js`
- Modify: `frontend/js/app.js`
- Modify: `frontend/index.html`
- Modify: `frontend/styles/app.css`
- Create: `frontend/tests/google-places.test.js`
- Create: `frontend/tests/snap-controls.test.js`

**Interfaces:**
- Produces: `loadGooglePlaces(apiKey) -> Promise<typeof google.maps.places>`.
- Produces: `createDialog(element, { initialFocus })` com `open()`, `close()` e restauração de foco.
- Produces: controlador dos dois modais e do campo de destino.

- [ ] **Step 1: escrever testes falhando do carregador**

Testar carregamento único do script, rejeição sem chave, restrição `includedRegionCodes = ["br"]`, `locationRestriction` de Belo Horizonte e solicitação apenas de `formattedAddress` e `location`.

- [ ] **Step 2: confirmar a falha**

Run: `npm test -- --test-name-pattern="Google Places|dialog|snap controls"`

Workdir: `frontend`

Expected: FAIL por módulos ausentes.

- [ ] **Step 3: implementar carregador e diálogo**

Usar `PlaceAutocompleteElement` e evento `gmp-select`. O diálogo usa `<dialog>`, fecha com Escape e clique explícito, mantém foco interno e devolve foco ao botão de abertura. Sem chave, mostrar `Busca de endereços indisponível` e desabilitar somente os controles dependentes do Google.

- [ ] **Step 4: construir HTML separado por responsabilidade**

Adicionar ao cabeçalho os botões `Definir origem` e `Limites`. Transformar a origem do formulário em resumo somente leitura com `Alterar origem ou parada`. Transformar o destino no contêiner do autocomplete. Criar um diálogo de origem e um diálogo de limites; o segundo não contém inputs de endereço nem listas de paradas.

- [ ] **Step 5: implementar os estados visuais**

No modal de limites, sem endereço mostrar o aviso aprovado e permitir salvar. Com endereço, buscar candidatas e exibir `Distância mínima necessária: X m`; se o limite for insuficiente, desabilitar a confirmação. No modal de origem, listar somente candidatas dentro do limite e permitir escolher uma delas.

- [ ] **Step 6: adicionar CSS, hover e responsividade**

Aplicar `hover` dentro de `@media (hover: hover)` a botões, abas, sugestões e cartões. Preservar `focus-visible`, alvo mínimo de 44 px, temas claro/escuro e layout 390×844. Executar `npm run build` para atualizar `frontend/assets/app.css`.

- [ ] **Step 7: verificar testes e build**

Run: `npm test && npm run build`

Workdir: `frontend`

Expected: PASS e build sem erros.

- [ ] **Step 8: checkpoint sem commit**

Executar `git diff --check`; não executar `git commit`.

---

### Task 6: Integração completa e regressões de navegador

**Files:**
- Modify: `frontend/browser-tests/route-search.js`
- Create: `frontend/browser-tests/address-snap.js`
- Modify: `frontend/README.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: todos os endpoints e controladores anteriores.
- Produces: fluxo funcional de origem por modal, destino na página e rota com caminhada nas duas extremidades.

- [ ] **Step 1: iniciar servidor com GTFS sintético e chave local**

Run: `backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`

Expected: `/health` retorna 200 e `/config/maps` indica disponibilidade sem imprimir a chave.

- [ ] **Step 2: executar cenário desktop**

Validar 1280×720: abrir origem, escolher endereço, trocar parada recomendada, configurar limites, escolher destino na página, calcular e conferir dois passos de caminhada.

- [ ] **Step 3: executar cenários de erro**

Validar destino não informado no modal de limites, limite abaixo da distância mínima, nenhuma parada em 2 km, Google indisponível e edição após resultado.

- [ ] **Step 4: executar cenário móvel e acessibilidade**

Validar 390×844, temas claro/escuro, teclado, Escape, restauração de foco, `prefers-reduced-motion` e ausência de erros de console.

- [ ] **Step 5: documentar configuração**

Documentar que `.env.local` contém somente:

```dotenv
GOOGLE_MAPS_API_KEY=cole-a-chave-local-aqui
```

Explicar restrição de chave por HTTP referrer e Places API, sem registrar valor real.

- [ ] **Step 6: checkpoint sem commit**

Salvar evidências de teste; não executar `git commit`.

---

### Task 7: Verificação final e progresso

**Files:**
- Modify: `docs/PLAN.md` somente nos checkboxes já existentes que esta entrega conclui.

**Interfaces:**
- Consumes: implementação completa.
- Produces: entrega validada sem segredo versionado.

- [ ] **Step 1: executar backend completo**

Run: `backend\.venv\Scripts\python.exe -m pytest backend/tests -q`

Expected: PASS.

- [ ] **Step 2: executar frontend completo**

Run: `npm test && npm run build && npm audit`

Workdir: `frontend`

Expected: testes e build PASS; nenhuma vulnerabilidade impeditiva.

- [ ] **Step 3: verificar qualidade e segredo**

Run: `backend\.venv\Scripts\python.exe -m compileall -q backend/app`

Run: `git diff --check`

Run: `git status --short --ignored`

Expected: `.env.local` aparece ignorado e nenhuma chave aparece em `git diff` ou arquivos rastreados.

- [ ] **Step 4: atualizar o plano geral**

Alterar somente `[ ]` para `[x]` em itens existentes de `docs/PLAN.md` comprovadamente concluídos; não reescrever descrições.

- [ ] **Step 5: apresentar resultado sem commit**

Relatar arquivos, testes, limitações da Demo Key e alterações propostas para commits. Aguardar autorização explícita antes de qualquer `git commit` ou `git push`.
