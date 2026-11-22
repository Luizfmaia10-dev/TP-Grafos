# Validação final da entrega

Data da validação: 21/11/2026.

Ambiente: Windows 11 Home, Python 3.14.7, Node.js 22.23.2, npm 10.9.8,
Git 2.49.0 e Git LFS 3.6.1. A validação foi executada sobre a árvore de
trabalho da branch `main`, sem criar commit.

## Código e dependências

- `pytest` executou 362 testes do backend: todos passaram. A cobertura de
  `backend/app` foi 96,17%, acima do limite de 96%.
- `npm test` executou 150 testes do frontend: todos passaram.
- `npm run build` gerou o CSS e copiou as fontes sem erro.
- `npm audit --audit-level=high` encontrou zero vulnerabilidades.
- `python -m compileall` e `pip check` passaram.
- O verificador HTTP percorreu `/health`, o HTML e 27 recursos locais, além
  de confirmar `404` para três recursos inexistentes. A rota real
  `15140072` para `14788235`, às `04:00`, retornou `found`.

## Dataset e resultados analíticos

- `git lfs fsck` passou e os seis TXT estão associados ao filtro LFS.
- A validação GTFS de 17/11/2026 passou com 9.925 estações,
  1.458.808 conexões e todos os sete checks verdadeiros.
- A campanha de benchmark tem estado `valid`, 54 workers, 384 amostras,
  96 resumos e equivalência verificada entre os dois motores.
- Foram lidos com sucesso 78 JSONs e 11 CSVs. Os seis fontes Mermaid têm
  seis SVGs e seis PNGs válidos. Os links Markdown locais estão íntegros.

## Documentos finais

- O artigo SBC recompilado tem 15 páginas A4.
- A apresentação recompilada tem 12 slides em 16:9.
- O relatório de complexidade recompilado tem 6 páginas A4.
- Os 15 renders do artigo e os 12 dos slides coincidiram exatamente com os
  renders aprovados. As seis páginas de complexidade foram reinspecionadas.
- As compilações Tectonic terminaram com código zero e sem referências
  indefinidas na última passagem. Permanecem apenas avisos não bloqueantes de
  justificação `Underfull` e metadados do `hyperref`, sem corte visual.
- A compilação alternativa do artigo com TeX Live 2026, pdfTeX 1.40.29 e
  `latexmk` 4.89 terminou com código zero e gerou 15 páginas A4. Todas as
  páginas foram renderizadas com Poppler e reinspecionadas sem cortes, páginas
  vazias, sobreposições ou glifos ilegíveis. O template SBC recebeu apenas a
  adaptação do hook legado de bibliografia para o kernel LaTeX atual.

## Pacote limpo

O procedimento de empacotamento foi validado em um ZIP candidato extraído fora
do repositório. A cópia continha 368 arquivos antes da inclusão deste relatório,
instalou as dependências Python e Node do zero e repetiu com sucesso os 362
testes backend, 150 testes frontend, cobertura de 96,17%, build, auditoria,
`compileall`, `pip check`, verificação HTTP e as três compilações LaTeX.

O filtro do pacote exclui `.git`, `.venv`, `.worktrees`, `.superpowers`,
`node_modules`, caches, temporários, `data/cache` e `data/gtfs/*.txt`. O pacote
inclui o código, lockfile, testes, documentação, fontes LaTeX, três PDFs,
slides, roteiro, capturas, resultados finais de benchmark e o guia Git LFS.
Uma varredura por formatos comuns de segredo não encontrou ocorrências.

Os TXT do GTFS não são incorporados ao ZIP. Como a entrega também exclui `.git`,
`git lfs pull` não deve ser executado diretamente na pasta extraída. O fluxo
documentado em `data/gtfs/README.md` cria ou reutiliza um clone Git separado,
baixa e verifica os objetos LFS e copia somente os seis CSVs completos para
`data/gtfs/` na pasta extraída.

## Pendências humanas

- Gravar e editar o vídeo de 12 a 18 minutos com os seis integrantes.
- Realizar o ensaio cronometrado da apresentação oral.
- Registrar o aceite visual humano da inspeção anotada no navegador.

Essas pendências permanecem desmarcadas no plano e não invalidam os testes
automatizados ou os artefatos já gerados.
