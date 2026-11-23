# Integração frontend e API

O FastAPI serve a interface e os endpoints na mesma origem. Configure
`GTFS_DIR` e `GTFS_SERVICE_DATE=YYYY-MM-DD` antes de iniciar o servidor para
carregar a rede do dia de serviço. Sem data configurada, a interface continua
disponível e as consultas apresentam a indisponibilidade da rede.

## Fluxo

- Na inicialização, o frontend consulta `GET /config/geocoding`. Com uma chave
  disponível, o autocomplete do Geoapify/OpenStreetMap pesquisa somente
  endereços de Belo Horizonte e devolve rótulo, latitude e longitude.
- O botão de origem abre um modal. Depois da escolha do endereço, o frontend
  chama `POST /snap/candidates`; a candidata mais próxima é recomendada, mas o
  usuário pode confirmar outra parada dentro do limite.
- O destino permanece na página principal. Selecionar seu endereço chama o
  mesmo endpoint e conecta automaticamente a parada mais próxima.
- O modal de caminhada mantém limites independentes A e B. Cada um aceita
  qualquer metro inteiro entre 100 e 2.000, começa em 800 e pode ser salvo sem
  endereço. Com endereço, a alteração revalida as candidatas após 220 ms.
- Autocomplete, snap e rota usam `AbortSignal`; limpar, editar ou fechar cancela
  a operação correspondente e respostas antigas são descartadas.
- O formulário envia um único `POST /routes/search` enquanto estiver carregando:

```json
{
  "mode": "address",
  "origin": {
    "label": "Rua de origem, 10",
    "latitude": -19.9001,
    "longitude": -43.9002,
    "max_walk_meters": 650,
    "station_id": "001"
  },
  "destination": {
    "label": "Rua de destino, 20",
    "latitude": -19.9101,
    "longitude": -43.9102,
    "max_walk_meters": 900
  },
  "departure_time": "07:59"
}
```

`api-service.js` converte os nomes internos em camelCase para esse JSON HTTP.
O horário enviado é `HH:MM`, sem segundos. Horas acima de 24 pertencem ao mesmo
dia de serviço; a interface não aplica módulo 24. Tema, máscara de horário,
seletor de horas/minutos e limpeza de campo permanecem disponíveis.

## Resposta e apresentação

`api-service.js` valida e converte o JSON da API para os nomes internos em
camelCase. IDs permanecem strings. A resposta informa `status`, `service_date`,
origem e destino. Quando `status` é `found`, `route` contém chegada, duração
total, espera e deslocamento em segundos, distância em quilômetros, passos e
instruções. Cada passo informa extremos com coordenadas, modal, ID interno,
número público da linha, partida, chegada, espera, duração e distância.

A timeline usa os passos e as instruções recebidos, incluindo esperas e os
modais BUS, SUBWAY e WALK. Instruções são preservadas no idioma fornecido pela
API. O resumo arredonda minutos apenas para exibição e mantém os valores exatos
acessíveis. O dia de serviço aparece no resultado.

O mapa mantém a união das paradas consultadas, selecionadas e presentes no
trajeto. Cada passo gera um segmento SVG: ônibus vermelho, metrô azul e
caminhada cinza tracejada. A projeção é esquemática e não representa ruas.
Rotas contidas no recorte original preservam exatamente o `viewBox` lógico base
(`0 0 960 780` no desktop e `0 0 358 256` no celular). Quando um ponto fica fora
dele, o viewport expande com margem e mantém a proporção do layout. Em todo
resultado, a camada física cabe no painel com espaço para os marcadores
completos. Uma extensão desfocada e não interativa do mapa preenche o espaço
externo, evitando faixas livres sem deformar ou recortar a camada principal.
Fundo, segmentos SVG e marcadores usam a mesma transformação, inclusive após
redimensionar entre desktop e celular. Editar ou limpar a busca restaura o
viewport base e o dimensionamento cover da busca sem resultado.
Os segmentos inicial e final de caminhada ligam os endereços às paradas usadas
pelo snap-to-network. A distância é Haversine em linha reta, não uma rota
pedestre sobre ruas.

## Estados e cancelamento

| Situação | Apresentação |
|---|---|
| Consulta pendente | Texto de carregamento, `aria-busy`, anúncio acessível e envio bloqueado |
| `found` | Resumo, timeline e segmentos da resposta atual |
| `no-route` | Nenhum trajeto encontrado; orientação para ajustar paradas ou horário |
| HTTP 404 no snap | Nenhuma parada dentro do limite; mostra a distância mínima quando disponível |
| HTTP 422 | Endereço, coordenada, limite, parada de origem ou horário inválido |
| HTTP 503 | Rede indisponível |
| Outros erros HTTP | Não foi possível consultar a rede |
| Falha de Fetch, JSON ou contrato | Falha de conexão; orientação para tentar novamente |

Editar ou limpar os campos cancela a rota pendente. Os controladores descartam
respostas antigas mesmo quando o serviço não respeita o cancelamento. Edição,
cancelamento, ausência de rota e erro removem o itinerário e os segmentos
anteriores, mantendo os valores ainda válidos do formulário.

## Verificação

Em `frontend/`, execute `npm run build`, `npm test` e `npm run check:server`.
O último comando requer o FastAPI ativo; use `FRONTEND_BASE_URL` caso ele esteja
fora de `http://127.0.0.1:8000`. O teste `integration-flow.test.js` conecta o
adaptador Fetch, os controladores, seleção, timeline e geometria com uma única
fronteira HTTP em memória. A suíte Python valida o contrato do backend.

O smoke de aceitação deve cobrir desktop e celular, sugestões e carregamento,
envio em HH:MM, rota multimodal, edição/cancelamento, ausência de caminho,
indisponibilidade, teclado, tema e limpeza de campos. Os testes automatizados
usam dados sintéticos; a rede completa requer os arquivos GTFS reais via Git LFS.

Confira também uma rota dentro do recorte base e uma fora dele, verificando
visibilidade integral e alinhamento de fundo, marcadores e segmentos após
redimensionar. No feed de `2026-11-17`, o caso de referência é `15140072` para
`14788235` às `04:14`. Ao editar, o mapa deve voltar ao recorte original.
