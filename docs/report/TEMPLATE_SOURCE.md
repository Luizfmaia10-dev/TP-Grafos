# Modelo SBC

O enunciado `TP.pdf` indica o [SBC Conferences Template](https://www.overleaf.com/latex/templates/sbc-conferences-template/blbxwjwzdngr), publicado pela Sociedade Brasileira de Computação no Overleaf, versão do estilo atualizada em dezembro de 2017. A página atribui licença [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/).

O botão de criação do Overleaf exige autenticação. O arquivo necessário `sbc-template.sty` foi obtido sem modificação em 21/11/2026 no [espelho de templates do SBGames](https://www.sbgames.org/arquivos/Template_SBC/template-latex/sbc-template.sty), evento da SBC. Seu cabeçalho credita Jomi Hubner e Rafael Bordini (junho de 2001), com atualizações de março de 2005 e dezembro de 2017. A origem oficial e esses créditos ficam preservados; nenhuma margem, fonte ou macro foi simulada no artigo.

SHA-256 do arquivo distribuído: `703b91a676624a91215502d152fc6a01d63500c0c629fca87097b6dce197a866`.

Somente o estilo é necessário: figuras e texto de exemplo foram excluídos. O artigo usa bibliografia explícita em `thebibliography`, dispensando o arquivo `sbc.bst`; seus itens seguem o padrão autor-ano. Pacotes TeX adicionais são resolvidos pela distribuição LaTeX.

Compilação validada neste ambiente, no PowerShell, a partir de `C:/Users/ferna/TP-Grafos`:

```powershell
.venv/Scripts/python.exe C:/Users/ferna/.codex/plugins/cache/openai-bundled/latex/0.2.10/scripts/compile_latex.py docs/report/rotasgraph.tex --compiler tectonic --output-directory output/pdf
.venv/Scripts/python.exe C:/Users/ferna/.codex/plugins/cache/openai-bundled/latex/0.2.10/scripts/compile_latex.py docs/presentation/rotasgraph-slides.tex --compiler tectonic --output-directory output/pdf
```

O utilitário externo pertence ao plugin LaTeX do Codex e não é um arquivo deste repositório. Ele localiza o Tectonic 0.17 do runtime e executa a compilação com o diretório da fonte como diretório de trabalho. Assim, `figures/*.tex`, o estilo SBC e os caminhos das capturas são resolvidos corretamente.

Em outra máquina com uma distribuição LaTeX que inclua os pacotes do artigo e Beamer, o fluxo usual abaixo dispensa o plugin. Essa alternativa não foi executada neste ambiente, que utiliza Tectonic:

```powershell
New-Item -ItemType Directory -Force output/pdf | Out-Null
Push-Location docs/report
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=../../output/pdf rotasgraph.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=../../output/pdf rotasgraph.tex
Pop-Location
Push-Location docs/presentation
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=../../output/pdf rotasgraph-slides.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=../../output/pdf rotasgraph-slides.tex
Pop-Location
```

Os PDFs finais são `output/pdf/rotasgraph.pdf` e `output/pdf/rotasgraph-slides.pdf`. As figuras resumidas em `docs/report/figures/` são fontes LaTeX editáveis derivadas dos contratos dos diagramas completos em `docs/diagrams/`; os originais completos permanecem disponíveis em Mermaid, SVG e PNG.
