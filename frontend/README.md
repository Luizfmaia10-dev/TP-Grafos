# RotasGraph - frontend

Interface responsiva em HTML/Tailwind e JavaScript nativo, servida pelo FastAPI.
O modo atual demonstra tres paradas de uma viagem da linha 50. Horarios fixos
e mapa esquematico; a consulta ainda usa a amostra local.

## Abrir a demonstracao

Na raiz do repositorio, com o ambiente Python do projeto ativo e suas
dependencias instaladas:

```powershell
python -m pip install -r backend/requirements.txt
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Abra http://127.0.0.1:8000/. Use Ctrl+C para encerrar o servidor.
CSS, fontes e SVGs ja estao versionados; a demonstracao usa recursos locais.
O frontend nao precisa carregar o GTFS completo para executar esse exemplo.

## Build e testes

Em outro terminal, a partir da raiz, com Node.js 20+ e npm:

```powershell
cd frontend
npm.cmd ci
npm.cmd test
npm.cmd run build
npm.cmd run check:server
```

Em Linux/macOS, use npm no lugar de npm.cmd. npm ci instala as versoes do
lockfile. npm test executa 84 testes independentes do servidor. npm run build
copia as fontes e compila styles/app.css para assets/app.css; edite o arquivo
de origem. npm run watch:css acompanha mudancas de estilo durante a edicao.

check:server exige o FastAPI aberto no primeiro terminal. Usa o executor de
testes e o fetch do Node, sem dependencias novas: verifica /health, HTML,
imports JavaScript, imagens, fontes do CSS, tipos HTTP e arquivos ausentes.
Os 34 testes incluem 28 URLs distintas de recursos. O script percorre imports
estaticos e atribuicoes literais de imagens dos modulos atuais; ele complementa
a verificacao dos fluxos no navegador.

Para outra porta, no PowerShell:

```powershell
$env:FRONTEND_BASE_URL = "http://127.0.0.1:8765"
npm.cmd run check:server
Remove-Item Env:FRONTEND_BASE_URL
```

Para os testes Python, na raiz com o ambiente ativo:

```powershell
python -m pytest -c backend/pytest.ini backend/tests
```

## Roteiro de conferencia

1. Use Experimente a linha 50 e Calcular trajeto. As 07:45, confira espera
   de 6 min, onibus de 29 min 16 s, total exato de 35 min 16 s e chegada 08:20:16.
2. Edite a busca: as paradas e o horario devem permanecer, sem o trajeto antigo.
3. Digite 0751 para conferir a mascara e o embarque sem espera. Compare 07:52
   e 25:00, ambos sem partida na amostra. Segundos nao sao aceitos.
4. Inverta as paradas para conferir o limite do exemplo. Um nome digitado
   precisa ser confirmado por uma sugestao ou pelo mapa para obter o ID.
5. Consulte e edite rapidamente uma parada ou o horario durante o carregamento;
   o resultado cancelado nao deve substituir a selecao nova.
6. Percorra o formulario com Tab/Shift+Tab, setas, Enter e Escape. Ao sair da
   origem confirmada, confira a transicao do mapa. Limpar deve manter o foco
   sem reabrir as sugestoes.
7. Alterne o tema no cabecalho e recarregue a pagina para conferir a escolha
   salva. Repita com movimento reduzido ativado no sistema.
8. Confira desktop e celular (1440, 390 e 360 px), redimensione com o resultado
   aberto e amplie o texto. Horarios e nomes devem continuar legiveis.

## Procedencia e proximos passos

O exemplo usa route_id 561929, trip_id 2662438S307679P075100 e service_id 307679,
da base inicial do projeto. Nao atribui um dia da semana a esse servico.
A distancia e uma soma Haversine aproximada entre paradas, sem seguir ruas.

O dataset da main foi atualizado depois da base dessa demonstracao. Os IDs e
horarios precisam ser revalidados para a data e o feed usados pela API real.
Fontes, coordenadas, horarios e verificacoes estao no
[plano do frontend](../docs/FRONTEND_PLAN.md). A passagem para endpoints,
Itinerary, calendario e multiplos modais esta no
[guia de integracao da #32](../docs/FRONTEND_INTEGRATION.md).
