# Estrutura Oficial de Entregas do Trabalho Pratico

Este diretorio consolida os arquivos e entregaveis do projeto **RotasGraph (Otimizador de Rotas de Transporte Urbano)** divididos exatamente conforme as tres etapas especificadas nas instrucoes oficiais da disciplina ([TP.pdf](../../TP.pdf)).

---

## Divisao das Entregas

```
entregas/
├── etapa-1-modelagem-e-planejamento/
│   ├── DESCRICAO_E_MODELAGEM.md       # Descricao do problema, justificativa e regras tecnicas
│   ├── PLAN.md                        # Plano geral de desenvolvimento (10 partes)
│   ├── GUIA_TECNICO_DIDATICO.md       # Guia didatico completo da arquitetura e matematica
│   ├── diagramas-uml/                 # Modelagem UML (classes, componentes, casos de uso, sequencia, estados)
│   ├── diagramas-renderizados/        # Diagramas renderizados em SVG e PNG de alta resolucao
│   └── prototipos-ui/                 # Telas e prototipos de interface do usuario
│
├── etapa-2-desenvolvimento-da-ferramenta/
│   ├── backend/                       # Codigo-fonte completo do motor de calculo e API (Python/FastAPI)
│   ├── frontend/                      # Interface web funcional (HTML5, Tailwind CSS, Vanilla JS, SVG)
│   ├── data/                          # Estrutura do dataset GTFS e instrucoes de restauracao via Git LFS
│   ├── docs-tecnicos/                 # Documentacoes tecnicas de API, algoritmos e validacao
│   └── README_PROJETO.md              # Guia completo de instalacao, execucao e testes
│
└── etapa-3-apresentacao-e-relatorio-final/
    ├── relatorio-latex/               # Codigo-fonte completo em LaTeX no template oficial da SBC
    ├── pdf-finais/                    # PDFs compilados (Artigo de 14 paginas, Slides, Analise de Complexidade)
    ├── slides/                        # Slides da apresentacao de 10 min (LaTeX Beamer e PDF)
    ├── VIDEO_SCRIPT.md                # Roteiro detalhado com falas para gravacao do video (12 a 18 min)
    ├── AUTHORSHIP_AUDIT.md            # Rastreamento individual de responsabilidades e commits dos 6 membros
    ├── FINAL_VALIDATION.md            # Auditoria de integridade e cobertura de testes (96.17%)
    └── pacote-zip/                    # Pacote ZIP final oficial (RotasGraph-entrega-final.zip)
```

---

## Analise de Completude e Pendencias (O Que Falta?)

Conforme as exigencias do [TP.pdf](../../TP.pdf), todos os artefatos tecnicos, codigos, modelos, testes automatizados e o artigo SBC LaTeX foram concluidos com sucesso. As unicas pendencias sao **acoes humanas externas** que dependem da gravacao e apresentacao presencial dos alunos:

1. **Gravacao do Video Demonstrativo (12 a 18 minutos)**:
   - *Exigencia*: Video com duracao entre 12 e 18 minutos, com a participacao obrigatoria de **todos os 6 membros do grupo**, demonstrando o funcionamento da ferramenta e a explicacao das features produzidas por cada um.
   - *Status atual*: O roteiro completo com marcacoes de tempo e falas para cada aluno esta pronto em `etapa-3-apresentacao-e-relatorio-final/VIDEO_SCRIPT.md`.
   - *Acao necessaria*: Os integrantes do grupo devem gravar, editar e anexar o arquivo de video (ou link do YouTube/Drive) no Canvas.

2. **Apresentacao Oral Presencial (10 minutos)**:
   - *Exigencia*: Apresentacao presencial com slides (10 minutos de duracao).
   - *Status atual*: Os slides estao prontos em PDF e LaTeX Beamer (`etapa-3-apresentacao-e-relatorio-final/slides/rotasgraph-slides.pdf`).
   - *Acao necessaria*: Ensaio cronometrado e apresentacao em sala de aula.

3. **Submissao Individual no Canvas por Todos os Membros**:
   - *Regra estrita do TP.pdf*: *"Cada um dos membros do grupo devera entregar uma copia do trabalho (alunos que nao entregarem, mesmo que outros membros do grupo entreguem, receberao nota igual a zero)"*.
   - *Acao necessaria*: Todos os 6 membros da equipe devem submeter os arquivos/links no Canvas antes do prazo final (22/11 as 23:59).
