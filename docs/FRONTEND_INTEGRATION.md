# Integração frontend e API

O FastAPI serve a interface e os endpoints na mesma origem. Configure
`GTFS_DIR` e `GTFS_SERVICE_DATE=YYYY-MM-DD` antes de iniciar o servidor para
carregar a rede do dia de serviço. Sem data configurada, a interface continua
disponível e as consultas apresentam a indisponibilidade da rede.

## Fluxo

- Cada campo consulta `GET /stations?query=texto&limit=20` com Fetch e
  `AbortSignal`. As sugestões mostram nome e ID da parada; selecionar confirma
  seu ID. Editar o texto invalida a seleção anterior.
- Os controladores de sugestões são independentes. Fechar, limpar ou selecionar
  cancela a consulta pendente; respostas antigas não reabrem outro campo.
  Carregamento, lista vazia e falha têm estados visíveis e acessíveis.
- O formulário envia um único `POST /routes/search` enquanto estiver carregando:

```json
{
  "origin_id": "001",
  "destination_id": "003",
  "departure_time": "07:59"
}
```

O horário enviado é `HH:MM`, sem segundos. Horas acima de 24 pertencem ao mesmo
dia de serviço; a interface não aplica módulo 24. Origem e destino iguais são
rejeitados antes do envio. Tema, máscara de horário, seletor de horas/minutos e
limpeza de campo permanecem disponíveis.

## Resposta e apresentação

`api-service.js` valida e converte o JSON da API para os nomes internos em
camelCase. IDs permanecem strings. A resposta informa `status`, `service_date`,
origem e destino. Quando `status` é `found`, `route` contém chegada, duração
total, espera e deslocamento em segundos, distância em quilômetros, passos e
instruções. Cada passo informa extremos com coordenadas, modal, ID da rota,
partida, chegada, espera, duração e distância.

A timeline usa os passos e as instruções recebidos, incluindo esperas e os
modais BUS, SUBWAY e WALK. Instruções são preservadas no idioma fornecido pela
API. O resumo arredonda minutos apenas para exibição e mantém os valores exatos
acessíveis. O dia de serviço aparece no resultado.

O mapa mantém a união das paradas consultadas, selecionadas e presentes no
trajeto. Cada passo gera um segmento SVG: ônibus vermelho, metrô azul e
caminhada cinza tracejada. A projeção usa o recorte esquemático de Belo Horizonte;
não representa a geometria das ruas e pontos fora do recorte podem não aparecer.
Selecionar pontos arbitrários ainda depende de uma futura API de encaixe na rede.

## Estados e cancelamento

| Situação | Apresentação |
|---|---|
| Consulta pendente | Texto de carregamento, `aria-busy`, anúncio acessível e envio bloqueado |
| `found` | Resumo, timeline e segmentos da resposta atual |
| `no-route` | Nenhum trajeto encontrado; orientação para ajustar paradas ou horário |
| HTTP 404 | Parada não encontrada |
| HTTP 422 | Dados inválidos |
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
