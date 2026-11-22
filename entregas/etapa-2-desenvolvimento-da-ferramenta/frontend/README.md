# RotasGraph - frontend

Interface responsiva em HTML/Tailwind e JavaScript nativo, servida pelo FastAPI
na mesma origem dos endpoints `GET /stations` e `POST /routes/search`.
A busca usa a rede GTFS do dia de serviço configurado e apresenta resumo,
timeline e segmentos SVG por modal sobre o mapa esquemático de Belo Horizonte.

## Executar

Na raiz do repositório, com o ambiente Python do projeto ativo, obtenha os
arquivos GTFS completos via Git LFS conforme [o guia do dataset](../data/gtfs/README.md).
Configure a pasta e a data de serviço antes de iniciar:

```powershell
python -m pip install -r backend/requirements.txt
$env:GTFS_DIR = "$PWD/data/gtfs"
$env:GTFS_SERVICE_DATE = "2026-11-17"
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Abra http://127.0.0.1:8000/. Use Ctrl+C para encerrar o servidor. Escolha uma
data atendida pelo feed disponível. Sem `GTFS_SERVICE_DATE`, a interface abre,
mas as consultas indicam rede indisponível. CSS, fontes e SVGs são locais.

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
lockfile. npm test executa a suíte independente do servidor. npm run build
copia as fontes e compila styles/app.css para assets/app.css; edite o arquivo
de origem. npm run watch:css acompanha mudancas de estilo durante a edicao.

check:server exige o FastAPI aberto no primeiro terminal. Usa o executor de
testes e o fetch do Node, sem dependencias novas: verifica /health, HTML,
imports JavaScript, imagens, fontes do CSS, tipos HTTP e arquivos ausentes.
O script percorre imports estaticos e atribuicoes literais de imagens dos modulos
atuais; ele complementa a verificacao dos fluxos no navegador.

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

1. Pesquise origem e destino por nome ou ID. Confira carregamento e sugestões
   de `GET /stations`; confirme cada parada pela sugestão ou pelo mapa.
2. Informe a partida em `HH:MM`, sem segundos, e calcule. Confira o
   `POST /routes/search`, o estado de carregamento e o bloqueio de envio duplicado.
   Horas acima de 24 continuam no mesmo dia de serviço.
3. Em um resultado encontrado, confira dia de serviço, resumo, esperas e passos
   da timeline. No mapa, ônibus usa vermelho, metrô azul e caminhada cinza
   tracejada, conforme os modais retornados pela API.
4. Confira uma rota dentro do recorte original e outra fora dele. A primeira
   mantém o `viewBox` lógico base; a segunda expande o viewport com margem e
   preserva a proporção. Em todo resultado, a camada física cabe no painel com
   os marcadores completos; uma extensão desfocada do próprio mapa preenche o
   espaço externo sem deformar a camada principal. Fundo, segmentos e marcadores
   permanecem alinhados. Para o feed de `2026-11-17`, use também `15140072` para
   `14788235` às `04:14`; revalide os IDs ao atualizar o dataset.
5. Edite ou limpe a busca: a rota desaparece e o mapa restaura o viewport base e
   o dimensionamento cover.
   Edite também durante o carregamento; uma resposta antiga não deve substituir
   a seleção nova. Confira ausência de caminho e rede indisponível.
6. Use teclado, máscara e seletor de horário, limpeza de campos e tema salvo.
   Repita com movimento reduzido ativado no sistema.
7. Confira desktop e celular (1440, 390 e 360 px), redimensione com o resultado
   aberto e amplie o texto. Rota, horários e nomes devem continuar legíveis.

O mapa conecta paradas de forma esquemática e não representa ruas. Contratos,
estados e limites estão no [guia de integração](../docs/FRONTEND_INTEGRATION.md).
