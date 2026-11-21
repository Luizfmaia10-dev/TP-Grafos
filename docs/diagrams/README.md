# Diagramas renderizados

As fontes oficiais ficam em [Artefatos/Diagramas](../../Artefatos/Diagramas).
Cada bloco Mermaid é extraído na ordem de aparição para `source/<nome>-NN.mmd`;
`rendered/` contém seu SVG e PNG, com o mesmo nome determinístico.
Histórias de usuário são texto e não possuem bloco Mermaid.

| Diagrama | SVG | PNG |
|---|---|---|
| Casos de uso | [SVG](rendered/diagrama-casos-de-uso-01.svg) | [PNG](rendered/diagrama-casos-de-uso-01.png) |
| Classes | [SVG](rendered/diagrama-classes-01.svg) | [PNG](rendered/diagrama-classes-01.png) |
| Componentes | [SVG](rendered/diagrama-componentes-01.svg) | [PNG](rendered/diagrama-componentes-01.png) |
| Estados | [SVG](rendered/diagrama-estados-01.svg) | [PNG](rendered/diagrama-estados-01.png) |
| Sequência de inicialização | [SVG](rendered/diagrama-sequencia-01.svg) | [PNG](rendered/diagrama-sequencia-01.png) |
| Sequência de busca | [SVG](rendered/diagrama-sequencia-02.svg) | [PNG](rendered/diagrama-sequencia-02.png) |

Renderização local com `@mermaid-js/mermaid-cli@11.12.0`, sem serviço remoto no
runtime da aplicação. A ferramenta é de documentação e não é dependência do app.
Depois de extrair os blocos atualizados, para cada fonte execute na raiz:

```sh
mmdc -i docs/diagrams/source/diagrama-classes-01.mmd -o docs/diagrams/rendered/diagrama-classes-01.svg -b white -w 2000
mmdc -i docs/diagrams/source/diagrama-classes-01.mmd -o docs/diagrams/rendered/diagrama-classes-01.png -b white -w 2000
```
