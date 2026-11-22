# Aceite visual assistido

Data da execução: 21/11/2026  
Aplicação: `http://127.0.0.1:8916`  
Dia de serviço GTFS: 17/11/2026

## Resultado

O fluxo real `15140072 → 14788235`, com saída às `04:00`, retornou duração total de 15 minutos e chegada prevista às `04:15`. A resposta foi processada pelo frontend, a timeline foi renderizada e a rota foi desenhada no mapa.

Foram verificados:

- desktop em 1440×900 e 1280×720;
- viewport móvel em 390×844;
- temas claro e escuro;
- preferência de movimento normal e reduzido;
- autocomplete, seleção das duas paradas e limite de 20 resultados;
- seletor de horário sem segundos;
- estado de carregamento;
- resultado, timeline, mapa e edição da busca;
- limpeza isolada da origem, sem reabrir o autocomplete e sem apagar o destino;
- estados de ausência de rota e indisponibilidade da API;
- contenção dos marcadores selecionados no mapa após o cálculo;
- ausência de erros e avisos no console durante o fluxo real;
- ausência de requisições externas no fluxo real.

Os estados de ausência de rota e erro da API foram simulados no navegador, de forma controlada, somente para revisar a apresentação visual. As demais capturas utilizam o backend real e o dataset GTFS local.

## Evidências principais

- `01-desktop-inicial.png`
- `02-autocomplete-origem.png`
- `03-seletor-horario.png`
- `05-loading.png`
- `06-desktop-resultado.png`
- `07-tema-escuro-resultado.png`
- `08-limpar-origem.png`
- `09-sem-rota-simulado.png`
- `10-erro-api-simulado.png`
- `11-mobile-inicial.png`
- `12-mobile-autocomplete.png`
- `13-mobile-seletor-horario.png`
- `14-mobile-resultado.png`
- `15-desktop-1280x720.png`
- `16-desktop-1440x900-final.png`

## Observações

- No estado de seleção anterior ao cálculo, as coordenadas geográficas reais podem deixar o círculo do marcador fora do recorte esquemático. Os rótulos permanecem contidos. Após o cálculo, o enquadramento da rota mantém marcadores e rótulos visíveis dentro do painel.
- A captura móvel é uma emulação responsiva do Chromium; não substitui o teste em dispositivo físico.
- O aceite humano final permanece pendente até a revisão da tela anotada.
