# Roteiro de vídeo do RotasGraph

Duração planejada: 15 minutos. Participação: Caio, Gabriel, Joaquim, Luiz, Pedro e Wanessa. Gravação, voz, presença dos seis integrantes, edição, hospedagem e envio são pendências humanas; este roteiro não comprova que o vídeo existe.

As falas abaixo distribuem explicação e demonstração conforme os commits auditados em [AUTHORSHIP_AUDIT.md](AUTHORSHIP_AUDIT.md). Os módulos de consolidação sem autoria individual demonstrada por commits são apresentados como trabalho do projeto. Quem explica GraphAnalyzer ou os resultados não deve declarar autoria exclusiva de sua implementação. Os nomes completos do README devem aparecer nos créditos.

## Preparação da gravação

Obter os seis TXT completos com Git LFS. Instalar as dependências documentadas do backend e do frontend. Na raiz, abrir o FastAPI com `GTFS_SERVICE_DATE=2026-11-17` e `GTFS_DIR=data/gtfs`, usando `.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend`. Esperar a rede carregar antes de gravar. Confirmar que `/stations` responde, pois `/health` sozinho não comprova carga. Abrir a interface no navegador em 1440×900 e deixar os slides e o JSON topológico disponíveis. Conferir áudio de cada pessoa e ocultar notificações pessoais.

Usar o caso real `15140072` para `14788235`, partida `04:00`. Resultado registrado: chegada `04:15:11`, 14 minutos de espera, 1 minuto e 11 segundos de deslocamento, total de 15 minutos e 11 segundos, linha interna `561787`. Não trocar os IDs por nomes ambíguos nem apresentar o ID da linha como número comercial. Se os dados locais forem de outra versão, repetir a validação e explicar a diferença antes da gravação.

## Sequência de 15 minutos

| Intervalo | Pessoa | Tela e ação | Fala e resultado a mostrar |
|---|---|---|---|
| 00:00–01:00 | Caio | Título e tela inicial | Apresentar os seis integrantes, PUC Minas, disciplina e professor Leonardo Vilela Cardoso. Definir menor chegada como espera mais deslocamento. Explicar por que uma ligação estática não basta. |
| 01:00–02:00 | Joaquim | `data/gtfs/README.md` e tabelas do feed | Mostrar a procedência BHTRANS/SUMOB, o conjunto coerente de seis arquivos e Git LFS. Distinguir cadastro completo de viagens ativas. Sem abrir o TXT de 513 MB no editor durante a gravação. |
| 02:00–03:00 | Joaquim | Calendário e diagnóstico topológico | Mostrar dia `2026-11-17`, serviços `307679` e `307682`, 9.925 estações, 25.956 viagens e 1.458.808 conexões. Explicar rejeição integral de viagens e a perda conservadora por restrições de embarque. |
| 03:00–04:00 | Pedro | Diagrama de classes e código de domínio | Mostrar Station, Connection, VehicleType e slots; uma partida é uma conexão, não apenas um par de estações. Explicar duração, partida e destino, sem dependência visual. |
| 04:00–05:00 | Pedro | API `/docs` e diagrama de sequência | Mostrar `GET /stations` e `POST /routes/search` com IDs e HH:MM. A rede é carregada uma vez. Diferenciar 200 sem rota, 404, 422 e 503. O REST não recebe coordenadas arbitrárias. |
| 05:00–06:00 | Wanessa | Fórmula de Haversine e testes da heurística | Explicar distância geodésica dividida pela velocidade máxima derivada do grafo. Pela desigualdade triangular e espera não negativa, a estimativa não supera o custo restante. O alerta de 120 km/h não é o limite matemático usado. |
| 06:00–07:00 | Wanessa | TimeUtils e exemplo de horário estendido | Mostrar `25:15:30` como horário do mesmo dia de serviço. A interface envia HH:MM, mas o motor preserva segundos. Explicar que o custo é temporal e que a busca não avança automaticamente ao serviço do dia seguinte. A conversão foi implementada por Gabriel; a fala demonstra a integração, sem transferir autoria. |
| 07:00–08:00 | Caio | `calculate_route` e teste de partida posterior | Percorrer rótulo de chegada, heap, bisect e varredura. Usar exemplo: sair 08:00 e chegar 08:40 versus sair 08:05 e chegar 08:15. A busca binária só localiza o início do sufixo. |
| 08:00–09:00 | Caio | Testes com oráculo e análise de complexidade | Explicar reconstrução, destino inalcançável e equivalência de chegada com Dijkstra. Registrar que o heap mantém entradas obsoletas; não afirmar espaço O(V). Mostrar o limite rigoroso do artigo e o espaço O(V+E+1). |
| 09:00–10:00 | Luiz | Grafo ordenado e encaixe interno | Mostrar inserção com bisect e deslocamento de list.insert: pior caso linear na lista. Explicar vértices temporários, raio de 0,8 km, caminhada a 5 km/h e limpeza em contexto, indicando que essa capacidade ainda não está no contrato público. |
| 10:00–11:00 | Gabriel | Interface: autocomplete e horário | Digitar os dois IDs, selecionar sugestões reais e informar 04:00. Mostrar que editar o texto invalida a seleção, que sugestões usam a API e que o tema pode ser alternado. Apresentar o fluxo por teclado sem alterar o caso de referência. |
| 11:00–12:00 | Gabriel | Resultado real e timeline | Submeter uma única consulta. Mostrar 04:15:11, espera de 14 min e viagem de 1 min 11 s. Ler uma instrução de espera e uma de ônibus. Explicar que Itinerary vem do backend e que os trechos não provam permanência no mesmo veículo. |
| 12:00–13:00 | Luiz | Mapa e edição | Mostrar marcadores A/B, segmento vermelho de ônibus e legenda. Redimensionar para 390×844, conferir que os rótulos cabem e não se sobrepõem, voltar ao desktop. Editar e consultar o mesmo par às 25:15 para demonstrar ausência de rota; explicar que isso não é erro de servidor. |
| 13:00–14:00 | Joaquim | `docs/analysis/topology.json` e tabelas finais do artigo | Explicar 45 articulações e 260 CFCs; criticidade não mede demanda. Mostrar a campanha válida: 54 processos, 384 amostras, 96 resumos; seis casos com rota no completo e zero nos recortes. Preparação mediana: A* 734,682 ms e NetworkX 14.333,139 ms. NetworkX teve menor mediana de consulta nos seis casos com rota, mas um caso sem rota inverteu a relação. Preparação, consultas amortizadas e RSS são custos distintos; não concluir superioridade geral. |
| 14:00–15:00 | Todos, conduzido por Caio | Créditos e conclusão | Cada integrante resume em uma frase sua contribuição comprovada. Caio fecha com as hipóteses de correção e limites: feed planejado, sem tempo real, tarifas ou transferência mínima. Mostrar fontes editáveis, PDFs e auditoria. Todos participam do encerramento. |

## Apresentação presencial de dez minutos

Usar [rotasgraph-slides.tex](presentation/rotasgraph-slides.tex), mantendo a divisão de fala registrada nos comentários da fonte. O slide de título faz parte dos 40 segundos iniciais. A demonstração de 1 min 40 s usa os mesmos IDs e dados; deixar o servidor carregado previamente. Se a consulta ao vivo falhar por indisponibilidade local, mostrar a captura real já registrada e identificá-la como captura, sem simular uma chamada bem-sucedida.

Entre 08:10 e 09:00, Wanessa apresenta os resultados aprovados do slide 11: preparação mediana de 734,682/14.333,139 ms, RSS preparada de 212,301/2.237,703 MiB e picos amostrados máximos de 228,215/2.488,203 MiB, sempre na ordem A*/NetworkX. Explicar que RSS não é memória exclusiva do grafo e que os recortes sem rotas limitam a análise. O encerramento continua entre 09:00 e 10:00. A duração da apresentação é planejada; o ensaio humano deve confirmá-la.

Os valores do roteiro, slides e artigo devem ser conferidos contra os mesmos JSON/CSV aprovados antes de gravar. Resultados históricos, campanhas interrompidas e testes com Fetch interceptado não devem ser apresentados como medição final. A gravação deve mostrar as features de cada aluno conforme a auditoria; não é necessário expor e-mails pessoais em tela.
