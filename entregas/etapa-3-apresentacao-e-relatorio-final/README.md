# Etapa 3 – Apresentacao e Relatorio Final

## 1. Escopo da Etapa Conforme o Enunciado (TP.pdf)
> "Contextualizacao, modelagem, analise dos resultados obtidos, avaliacao do desempenho, conclusoes e apresentacao da solucao.  
> **Entregaveis**:
> - Relatorio tecnico em LaTeX usando o template oficial da SBC (obrigatorio, entre 12 e 15 paginas);
> - Apresentacao oral com demonstracao da ferramenta (10 minutos);
> - Apresentacao em video (entre 12 e 18 minutos) com foco no funcionamento e na explicacao das features produzidas por cada aluno do grupo;
> - Repositorio Git contendo o historico de desenvolvimento (commits individuais serao avaliados);
> - Um arquivo .zip contendo o codigo-fonte do trabalho, o codigo-fonte do relatorio (.tex) e o PDF do relatorio;
> - Indicacao no relatorio das responsabilidades e o que foi feito por cada membro do grupo."

---

## 2. Conteudo Deste Diretorio

1. **`relatorio-latex/` (Codigo-Fonte do Relatorio)**:
   - `rotasgraph.tex`: Codigo-fonte principal do artigo em LaTeX estruturado de acordo com as normas da Sociedade Brasileira de Computacao (SBC).
   - `sbc-template.sty`: Folha de estilo oficial da SBC exigida pelo enunciado.
   - `benchmark-results.tex`: Tabelas de medicao de tempo de execucao e consumo de memoria comparando o motor proprio contra o NetworkX.
   - `ANALISE_COMPLEXIDADE.tex`: Formalizacao matematica da complexidade assintotica temporal e espacial (Big-O).
   - `figures/`: Figuras e graficos inseridos no relatorio.

2. **`pdf-finais/` (Documentos Compilados Prontos para Avaliacao)**:
   - `rotasgraph.pdf`: **Artigo final compilado com exatamente 15 paginas** (aderente ao limite estrito de 12 a 15 paginas da SBC). Inclui a secao formal de responsabilidades individuais dos 6 integrantes da equipe.
   - `rotasgraph-slides.pdf`: Slides oficiais da apresentacao oral em formato 16:9 (12 slides para 10 minutos).
   - `ANALISE_COMPLEXIDADE.pdf`: Relatorio formal complementar de complexidade Big-O (6 paginas).
   - `analise-complexidade-big-o.pdf`: Versao analitica de suporte.

3. **`slides/`**:
   - `rotasgraph-slides.tex`: Codigo-fonte dos slides em LaTeX Beamer.
   - `rotasgraph-slides.pdf`: PDF dos slides para projecao durante a defesa de 10 minutos.

4. **`VIDEO_SCRIPT.md`**:
   - Roteiro completo, minutado e roteirizado com as falas e demonstracoes de cada um dos 6 integrantes para a gravacao do video obrigatorio de 12 a 18 minutos:
     - 00:00 - 02:30: Caio César (Introducao, problema e arquitetura MVC).
     - 02:30 - 05:00: Luiz Fernando (Estrutura do Grafo nativo e ordenacao temporal).
     - 05:00 - 07:30: Gabriel Aredes (Frontend interativo e mapa SVG).
     - 07:30 - 10:00: Joaquim Antônio (Ingestao GTFS e sanitizacao de dados).
     - 10:00 - 12:30: Pedro Henrique (Motor de roteamento A* e heuristica de Haversine).
     - 12:30 - 15:00: Wanessa Oliveira (Analise topologica com GraphAnalyzer e Pontos de Articulacao).
     - 15:00 - 17:00: Conclusao conjunta, benchmarks e demonstracao ao vivo.

5. **`AUTHORSHIP_AUDIT.md`**:
   - Relatorio de auditoria de autoria comprovando os commits individuais e as responsabilidades atribuidas a cada um dos 6 integrantes da equipe no historico do Git.

6. **`FINAL_VALIDATION.md`**:
   - Relatorio de validacao final atestando a execucao com sucesso de 100% dos testes, integridade da base GTFS e validacao da compilacao do LaTeX.

7. **`pacote-zip/RotasGraph-entrega-final.zip`**:
   - Arquivo comprimido oficial pronto para submissao no Canvas contendo codigo-fonte completo, fontes LaTeX e os PDFs exigidos.

---

## 3. Checklist de Entregaveis e Alertas (O Que Falta?)

| Entregavel Exigido | Status no Projeto | Acao Necessaria |
| :--- | :--- | :--- |
| **Relatorio em LaTeX (.tex)** | Concluido | Disponivel em `relatorio-latex/rotasgraph.tex` e no `.zip`. |
| **PDF do Relatorio (12 a 15 paginas)** | Concluido | Disponivel em `pdf-finais/rotasgraph.pdf` (15 paginas exatas no template SBC). |
| **Divisao de Responsabilidades no Relatorio** | Concluido | Presente na Secao 8 de `rotasgraph.tex` / `rotasgraph.pdf` e detalhado em `AUTHORSHIP_AUDIT.md`. |
| **Arquivo .zip da Entrega** | Concluido | Disponivel em `pacote-zip/RotasGraph-entrega-final.zip`. |
| **Slides da Apresentacao (10 min)** | Concluido | Disponivel em `slides/rotasgraph-slides.pdf` (12 slides). |
| **Roteiro do Video (12 a 18 min)** | Concluido | Disponivel em `VIDEO_SCRIPT.md`. |
| **Arquivo/Link do Video Gravado** | **PENDENCIA HUMANA** | **O grupo de alunos precisa gravar e editar o video conforme o roteiro, anexando o arquivo ou link no Canvas.** |
| **Apresentacao Oral Presencial** | **PENDENCIA HUMANA** | **O grupo precisa realizar a apresentacao presencial de 10 minutos em sala de aula.** |
| **Submissao Individual no Canvas** | **PENDENCIA HUMANA** | **Todos os 6 alunos devem fazer o upload no Canvas individualmente para nao zerarem a nota.** |
