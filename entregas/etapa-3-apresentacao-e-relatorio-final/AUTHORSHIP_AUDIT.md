# Auditoria de autoria

Recorte: commits alcançáveis por `HEAD` na branch `main`, revisão `b4359d62b6e1fc7cebe231243bcb48be4df9ed25`, consultados em 21/11/2026. Foram encontrados 116 commits, sendo 110 sem merge e seis merges. Não se usou `--all`, pois referências de stash, branches não integradas e backups não representam necessariamente a entrega integrada. Não houve alteração do histórico nem criação de `.mailmap`.

## Método

```sh
git rev-parse HEAD
git rev-list --count HEAD
git log HEAD --format='%H|%an|%ae|%s'
git log HEAD --no-merges --format='%H|%an|%ae|%s'
git log HEAD --merges --format='%h|%ae|%s'
git log HEAD --format='%h|%ae|%s%n%(trailers:key=Co-authored-by)' --grep='Co-authored-by'
git show --stat <commit>
```

A chave de consolidação é o e-mail de autor (`%ae`), não o nome exibido nem o committer. Os seis nomes canônicos abaixo são exatamente os do README. A associação de cada e-mail ao nome usa os aliases encontrados e o conteúdo dos commits. O endereço noreply de Pedro identifica a mesma conta; não foi adivinhado um e-mail pessoal. Contagens medem registros Git, não esforço, qualidade, participação presencial ou autoria exclusiva. Mudanças atuais ainda não commitadas não foram atribuídas por esse método.

Também foram verificados os trailers de coautoria. Cinco commits de Caio (`393f4b3`, `8aad5a6`, `31cdcc6`, `1cb5714` e `b1eba8a`) registram `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`. Esse registro de assistência é preservado e não foi contado como sétimo integrante humano nem ocultado ao interpretar a autoria. A tabela conta o autor primário de cada commit uma única vez; não afirma trabalho sem assistência.

| Nome do README | E-mail de autor | Aliases no histórico | Commits | Sem merge | Merges |
|---|---|---|---:|---:|---:|
| Caio Cesar Falinacio dos Santos | caio.falinacio@sga.pucminas.br | CaioCFalinacio; Caio César Falinacio dos Santos | 30 | 29 | 1 |
| Gabriel Aredes | gabrielaredes1@gmail.com | ImGabrielAredes | 13 | 12 | 1 |
| Joaquim Antonio | joaquim.antonio.camargos@gmail.com | Joaquim Antonio | 8 | 6 | 2 |
| Luiz Fernando Cunha Maia | lf.cunhamaia@gmail.com | Luiz Maia; Luiz Fernando Maia; LuizMaia | 57 | 55 | 2 |
| Pedro Henrique Nogueira | 64815567+PedroHNFerreira@users.noreply.github.com | Pedro Nogueira | 4 | 4 | 0 |
| Wanessa Oliveira Marcos | wanessa.marcos@sga.pucminas.br | WanessaOliveiraMarcos | 4 | 4 | 0 |
| Total | | | 116 | 110 | 6 |

## Atribuições sustentadas

| Integrante | Evidência representativa | Responsabilidade comprovada no histórico |
|---|---|---|
| Caio Cesar Falinacio dos Santos | `1cb5714`, `24d1ed4`, `75b51fc`, `f1e1132`, `30c3ce0`, `edc672f` | Planejamento e modelagem; slots; velocidade máxima; A* temporal, reconstrução e testes de equivalência com oráculo independente. |
| Gabriel Aredes | `a792c66`, `9d1ed6b`, `acb2f00`, `ae7cbb4`, `dcf012b`, `baf806e` | Conversão temporal; interface HTML/CSS/JavaScript responsiva, seleção de paradas, demonstração inicial e verificação de recursos estáticos. |
| Joaquim Antonio | `f40374c`, `e50455c`, `cad3770`, `5a2924f`, `e00b416` | Dataset e ingestão GTFS; calendários; Itinerary; implementação inicial do benchmark com NetworkX. |
| Luiz Fernando Cunha Maia | `37521e7`, `321793f`, `4f0e08`, `b52bc31`, `1436f5c`, `856e832`, `c3e444e` | Listas de adjacência ordenadas; vértices temporários; higienização GTFS; integração REST/frontend, mapa e correções de apresentação. |
| Pedro Henrique Nogueira | `4eb8fd9`, `1a2415e`, `58d8934`, `c3cec22` | Entidades de domínio; ciclo de vida da rede compartilhada; endpoints de estações e busca de rotas. |
| Wanessa Oliveira Marcos | `52e0ccf`, `bc1a438`, `0476e7f`, `3a18f09` | Configuração inicial de testes e saúde da API; Haversine e heurística do A* com testes e documentação de progresso. |

Os commits podem tocar o mesmo módulo em momentos diferentes. Por exemplo, Joaquim implementou o carregador, Luiz registrou a higienização e Caio diagnosticou a mistura de serviços; isso não autoriza atribuir o módulo inteiro a uma única pessoa. Merges contam integração, não transferência de autoria dos commits contidos.

GraphAnalyzer, campanha ampliada, correções da auditoria e artefatos acadêmicos presentes apenas no diretório de trabalho não têm autoria individual demonstrável por commits neste recorte. O artigo e o roteiro os apresentam como consolidação do projeto e distribuem a explicação pelos conhecimentos documentados, sem atribuir desenvolvimento não comprovado. A validação oral dessas responsabilidades pela equipe e a gravação do vídeo são atividades humanas.
