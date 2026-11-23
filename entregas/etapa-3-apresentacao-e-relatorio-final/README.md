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
   - `rotasgraph.pdf`: Copia compilada do artigo mantida junto ao codigo-fonte.
   - `sbc-template.sty`: Folha de estilo oficial da SBC exigida pelo enunciado.
   - `benchmark-results.tex`: Tabelas de medicao de tempo de execucao e consumo de memoria comparando o motor proprio contra o NetworkX.
   - `ANALISE_COMPLEXIDADE.tex`: Formalizacao matematica da complexidade assintotica temporal e espacial (Big-O).
   - `figures/`: Figuras e graficos inseridos no relatorio.

2. **`pdf-finais/` (Documentos Compilados Prontos para Avaliacao)**:
   - `rotasgraph.pdf`: **Artigo final compilado com exatamente 14 paginas** (aderente ao limite estrito de 12 a 15 paginas da SBC). Inclui a secao formal de responsabilidades individuais dos 6 integrantes da equipe.
   - `SlideApresentacaoSala.pdf`: Slides oficiais da apresentacao oral presencial (15 paginas).
   - `rotasgraph-slides-VIDEO.pdf`: Slides utilizados como base para a apresentacao em video (12 paginas).
   - `ANALISE_COMPLEXIDADE.pdf`: Relatorio formal complementar de complexidade Big-O (6 paginas).

3. **`slides/`**:
   - `rotasgraph-slides.tex`: Codigo-fonte dos slides em LaTeX Beamer.
   - `rotasgraph-slides.pdf`: Compilacao dos slides de 12 paginas utilizados como base para o video.

4. **`../../docs/VIDEO_SCRIPT.md`**:
   - Roteiro minutado da apresentacao em video, alinhado as responsabilidades registradas no relatorio e na auditoria de autoria.

5. **`video/VIDEO-FINAL-V1.mp4`**:
   - Video final gravado com duracao aproximada de 17 minutos e 37 segundos, dentro do intervalo exigido de 12 a 18 minutos.

6. **`AUTHORSHIP_AUDIT.md`**:
   - Relatorio de auditoria de autoria comprovando os commits individuais e as responsabilidades atribuidas a cada um dos 6 integrantes da equipe no historico do Git.

7. **`FINAL_VALIDATION.md`**:
   - Registro da campanha de testes, da integridade da base GTFS e da validacao da compilacao do LaTeX realizada durante a finalizacao do projeto.

8. **`relatorio-latex.zip`**:
   - Pacote auxiliar contendo somente o codigo-fonte e o PDF do relatorio. Este arquivo nao substitui o ZIP final com o codigo-fonte completo do sistema.

---

## 3. Checklist de Entregaveis e Alertas (O Que Falta?)

| Entregavel Exigido | Status no Projeto | Acao Necessaria |
| :--- | :--- | :--- |
| **Relatorio em LaTeX (.tex)** | Concluido | Disponivel em `relatorio-latex/rotasgraph.tex` e em `relatorio-latex.zip`. |
| **PDF do Relatorio (12 a 15 paginas)** | Concluido | Disponivel em `pdf-finais/rotasgraph.pdf` (14 paginas exatas no template SBC). |
| **Divisao de Responsabilidades no Relatorio** | Concluido | Presente na Secao 11 de `rotasgraph.tex` / `rotasgraph.pdf` e detalhado em `AUTHORSHIP_AUDIT.md`. |
| **Arquivo .zip da Entrega** | **Pendente** | Montar o ZIP final com o codigo-fonte do sistema, o codigo-fonte do relatorio e o PDF do relatorio. |
| **Slides da Apresentacao (10 min)** | Concluido | Disponivel em `pdf-finais/SlideApresentacaoSala.pdf` (15 paginas). |
| **Roteiro do Video (12 a 18 min)** | Concluido | Disponivel em `../../docs/VIDEO_SCRIPT.md`. |
| **Arquivo/Link do Video Gravado** | Concluido | Arquivo local disponivel em `video/VIDEO-FINAL-V1.mp4` (aproximadamente 17 min 37 s); falta apenas envia-lo ao Canvas. |
| **Apresentacao Oral Presencial** | **PENDENCIA HUMANA** | **O grupo precisa realizar a apresentacao presencial de 10 minutos em sala de aula.** |
| **Submissao Individual no Canvas** | **PENDENCIA HUMANA** | **Todos os 6 alunos devem fazer o upload no Canvas individualmente para nao zerarem a nota.** |
