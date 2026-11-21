# Carregamento e higienização de dados GTFS

`app.data_loader.DataLoader` lê os quatro arquivos principais e os calendários GTFS
para retornar um `TransportGraph` com objetos `Station` e `Connection`. Utiliza a biblioteca padrão do Python, sem
bibliotecas de grafos ou dependências da API. Os arquivos originais não são alterados.

## Uso

Os seis TXT de `data/gtfs/` são versionados com **Git LFS**. Antes de carregar
a base real, instale e configure o LFS e execute, na raiz do repositório:

```sh
git lfs pull
git lfs fsck
```

Os arquivos devem conter CSVs completos, não ponteiros iniciados por
`version https://git-lfs.github.com/spec/v1`. Se os objetos já estiverem no cache
local, `git lfs checkout` restaura os TXT sem acessar o remoto. O carregador não
baixa arquivos nem interpreta ponteiros LFS. Consulte [o guia do dataset](../data/gtfs/README.md).

Execute a partir de `backend/`:

```python
import json
from datetime import date
from app.data_loader import DataLoader

loader = DataLoader("../data/gtfs", service_date=date(2026, 11, 17))
graph = loader.build_graph()
print(json.dumps(loader.report.to_dict(), ensure_ascii=False, indent=2))
```

O exemplo resolve os serviços ativos na data informada, incluindo o convencional
e o suplementar. A seleção efetiva fica em `report["active_service_ids"]` e a data
em `report["service_date"]`. Instruções de execução estão em
[GTFS_VALIDATION.md](GTFS_VALIDATION.md).

## Seleção por calendário

- `service_date` recebe um `datetime.date` e representa o **dia de serviço GTFS**.
- `calendar.txt` ativa serviços pelo dia da semana e pela vigência, incluindo as
  datas inicial e final.
- `calendar_dates.txt`, quando presente, é aplicado depois: tipo 1 adiciona o
  serviço na data e tipo 2 o remove. As exceções prevalecem sobre a regra semanal.
- São aceitos feeds apenas com `calendar.txt`, apenas com `calendar_dates.txt`,
  ou com ambos. Informar uma data sem nenhum calendário causa erro explícito.
- Datas, flags e chaves inválidas ou duplicadas nos calendários interrompem a carga,
  com identificação do arquivo e da linha. Não é inferido o significado dos IDs.
- Serviços do calendário sem viagens em `trips.txt` não geram conexões.
- Uma data sem serviços ativos retorna um grafo com as paradas cadastradas e sem
  conexões de transporte; o resumo registra a seleção vazia.
- Horários acima de 24h continuam associados ao dia de serviço informado. Por
  exemplo, `25:00:00` pertence ao serviço que começou no dia anterior à sua chegada
  cronológica. A carga não agrega automaticamente serviços de dias vizinhos.
- A alternativa manual `active_service_ids={"307679"}` continua disponível, mas
  não pode ser combinada com `service_date`. Sem data, feeds com vários serviços
  continuam exigindo seleção explícita para impedir mistura silenciosa.

A resolução do calendário percorre C registros semanais e E exceções em O(C + E)
no tempo e no espaço, incluindo a verificação de duplicidades. O filtro de viagens
é O(T). A leitura de `stop_times.txt` ainda percorre todos os registros, mesmo os
serviços ignorados; o grafo armazena apenas as conexões aceitas dos serviços ativos.

## Leitura e construção

- Os arquivos são CSV com cabeçalho, separador vírgula e codificação UTF-8,
  aceitando também BOM. Campos opcionais vazios são preservados.
- Espaços nas extremidades dos valores são removidos; espaços internos dos IDs
  são preservados. IDs continuam sendo strings.
- Arquivo ausente gera `FileNotFoundError`. Cabeçalho sem colunas necessárias,
  colunas duplicadas ou registros com quantidade incorreta de campos geram
  `ValueError` com indicação do arquivo. Esses erros interrompem o carregamento.
- Os registros de horários são lidos incrementalmente, mantendo uma viagem por vez.
  Uma viagem deve ocupar um bloco contíguo em `stop_times.txt`. Se reaparecer após
  outro bloco, o carregamento falha explicitamente, sem retornar um grafo parcial.
- Cada viagem é ordenada pelo valor numérico de `stop_sequence` e validada por
  inteiro antes da inserção de qualquer conexão. Rejeitar uma viagem não cria
  atalhos entre paradas nem remove conexões de outras viagens.
- Viagens de serviços não selecionados são ignoradas com o motivo
  `inactive_service`. Seleções vazias ou inexistentes são rejeitadas.
- Cada conexão parte no horário de saída da parada atual e chega no horário de
  chegada à próxima. `TimeUtils` preserva segundos e horários acima de 24h,
  representando os tempos em minutos fracionários.
- A distância é uma aproximação em linha reta por Haversine, em quilômetros,
  com raio terrestre de 6.371 km. Não utiliza `shape_dist_traveled`.

## Regras de higienização

| Situação | Tratamento |
|---|---|
| ID, nome ou coordenadas obrigatórias de parada vazios | Rejeitar o registro |
| Coordenadas não numéricas, infinitas ou `NaN` | Rejeitar a parada |
| Latitude fora de [-90, 90] ou longitude fora de [-180, 180] | Rejeitar a parada; extremos são aceitos |
| Nomes iguais em IDs diferentes | Preservar as paradas |
| Registros idênticos após limpeza, com o mesmo ID | Manter apenas o primeiro |
| Mesmo ID com dados conflitantes | Excluir o registro previamente aceito e rejeitar os conflitantes e posteriores desse ID |
| Tipo de linha diferente de 1 ou 3 | Rejeitar a linha; 1 corresponde a `SUBWAY` e 3 a `BUS` |
| Viagem sem ID, `service_id` ou linha | Rejeitar o registro |
| Viagem com linha rejeitada ou inexistente | Rejeitar o registro |
| Horários de viagem rejeitada ou inexistente | Rejeitar o bloco inteiro |
| Parada rejeitada ou inexistente na viagem | Rejeitar a viagem inteira |
| Menos de duas paradas na viagem | Rejeitar a viagem |
| Horário vazio ou inválido | Rejeitar a viagem |
| Sequência vazia, não inteira não negativa ou duplicada | Rejeitar a viagem |
| Sequências fora de ordem no arquivo | Ordenar antes da validação temporal |
| Partida anterior à chegada na mesma parada | Rejeitar a viagem |
| Chegada à próxima parada anterior à partida atual | Rejeitar a viagem |
| Tempo zero entre IDs de paradas distintos | Colocar a viagem inteira em quarentena, excluindo suas conexões |
| Velocidade Haversine acima de 120 km/h, com tempo positivo | Manter a viagem e emitir alerta |
| Viagem válida no cadastro, mas sem horários | Registrar `missing_stop_times`; não criar conexões |
| Mais de um `service_id` sem data ou seleção explícita | Interromper a carga antes de criar o grafo |
| Viagem de serviço não selecionado | Ignorar o bloco com `inactive_service` |
| `pickup_type` ou `drop_off_type` fora de 0 a 3 | Rejeitar a viagem inteira |
| `pickup_type` ou `drop_off_type` igual a 1, 2 ou 3 | Colocar a viagem inteira em quarentena |

Os conflitos de IDs são verificados em paradas, linhas e viagens, comparando os
campos completos dos registros após limpeza. Um registro inválido já rejeitado
não bloqueia um registro válido posterior. `stop_times.txt` não é deduplicado:
sequências repetidas tornam a viagem ambígua e provocam sua rejeição.

O limiar de 120 km/h é um indicador de suspeita, não uma comprovação de erro nem
um limite legal. Não são inventadas coordenadas, distâncias de percurso ou durações.
A quarentena permanece apenas no diagnóstico; não move ou modifica arquivos.

## Resumo do carregamento

`loader.report.to_dict()` retorna uma estrutura serializável em JSON:

| Campo | Significado |
|---|---|
| `files` | Contagens `read`, `accepted` e `rejected` por arquivo |
| `reasons` | Número de registros rejeitados por motivo |
| `warnings` | Contagem de alertas; `suspicious_speed` conta trechos e `missing_stop_times` conta viagens |
| `examples` | Até cinco exemplos por motivo/alerta, com arquivo, linha e ID |
| `rejected_trips` | IDs dos blocos de viagem rejeitados ou das viagens sem horários, com motivo |
| `loaded_trips` | Total de viagens que produziram conexões |
| `connections` | Total de conexões inseridas no grafo |
| `service_date` | Dia de serviço em formato ISO, ou `null` na seleção manual |
| `active_service_ids` | IDs efetivamente selecionados e declarados em `trips.txt` |

Após uma execução bem-sucedida, `read = accepted + rejected` em cada arquivo.
Nas tabelas de cadastro, `accepted` conta registros únicos válidos, mesmo quando
não utilizados por viagens. Nos horários, uma viagem rejeitada contabiliza todos
os seus registros como rejeitados, com o primeiro motivo detectado. Alertas não
alteram as contagens de aceitação.

Os motivos incluem `missing_required_value`, `invalid_coordinate`, `duplicate_record`,
`conflicting_id`, `unsupported_route_type`, `unknown_route`, `unknown_trip`,
`unknown_stop`, `too_few_stops`, `invalid_sequence`, `duplicate_sequence`,
`invalid_time`, `departure_before_arrival`, `negative_travel_time`,
`zero_travel_time`, `inactive_service`, `invalid_pickup_drop_off` e
`restricted_pickup_drop_off`.

Uma linha rejeitada pode provocar `unknown_route` no cadastro de viagens e
`unknown_trip` no bloco de horários: são rejeições distintas em arquivos diferentes.
Para viagens rejeitadas, o exemplo aponta o início do bloco; para viagens sem horários,
a linha é `null`. Os exemplos são limitados, mas as contagens e os IDs de viagens
rejeitadas são completos. O resumo é reiniciado em cada chamada a `build_graph()`.
Em caso de erro estrutural fatal, as contagens podem estar incompletas.

## Validação e limites

```sh
python -m pytest
python -m pytest tests/test_data_loader.py --cov=app.data_loader --cov-branch --cov-report=term-missing
```

Os testes utilizam arquivos temporários pequenos e cobrem dados válidos, conversões,
coordenadas, duplicidades, referências, ordenação, erros temporais, quarentena,
alertas, isolamento entre viagens e consistência do resumo.

Permanece fora do escopo a geometria real dos trajetos. Como `Connection` não armazena `trip_id` nem estado de permanência no veículo,
viagens com restrições de embarque/desembarque são rejeitadas por inteiro. Essa perda
conservadora evita rotas impossíveis até o roteador modelar esse estado. Alertas de
velocidade não garantem admissibilidade da heurística do futuro roteador.

Os índices e o grafo permanecem na RAM. Valores numéricos repetidos são compartilhados
durante a carga, e os índices auxiliares de horários, distâncias e durações são limpos
ao finalizar ou iniciar uma nova carga. A inserção de conexões utiliza o método
ordenado existente.

## Validação da base completa por data

Validações aprovadas em 17/11/2026 com o ZIP completo registrado no README do dataset:

| Data de serviço | Serviços ativos | Viagens | Conexões | Carga (s) | Pico do processo (MiB) |
|---|---|---:|---:|---:|---:|
| 2026-11-17 | 307679, 307682 | 25.956 | 1.458.808 | 25,494 | 215,520 |
| 2026-11-21 | 307681, 307684 | 15.436 | 881.502 | 22,438 | 165,797 |
| 2026-02-17 | 447982, 447986 | 11.521 | 692.577 | 21,557 | 150,738 |

Em todas as cargas foram mantidas 9.925 paradas. Os serviços de 17/11 são de dia útil;
os de 21/11, de sábado. Em 17/02, as exceções de Carnaval substituem os serviços
regulares pelos especiais. Os seis hashes de origem foram conferidos, assim como
contagens, destinos, ordenação e pesos de todas as conexões.

Os JSONs detalhados ficam em `data/cache/gtfs-<data>.json`, ignorados pelo Git e
reproduzíveis pelo comando de validação. As medições foram feitas em processos
separados, com Python 3.12.0 em Linux; o pico é do processo inteiro, não apenas do
grafo. Os valores variam com o ambiente e não constituem um benchmark comparativo.

Referência histórica: antes desta atualização, a carga manual de `307679` na base
convencional anterior produziu 1.336.540 conexões, levou 123,999 segundos e registrou
205,293 MiB de pico. Essa medição não descreve o pacote completo atual.

## Evidências visuais da carga

O `DataLoader` é chamado pelas CLIs `app.validate_gtfs` e `app.analyze_topology`,
pelos testes e por `RouteNetwork.load` na inicialização do FastAPI quando há
data de serviço configurada. O frontend consulta essa rede via REST. As CLIs
criam o grafo na RAM e o liberam ao terminar.

Antes da seleção obrigatória de serviço, foram geradas imagens de uma carga histórica:
9.659 paradas e 13.765 segmentos direcionados, agregando 6.110.036 conexões horárias.
Um recorte da parada `14785288`, Avenida Dos Andradas 220, mostrou 964 partidas
e cinco destinos diretos. Essas imagens não estão versionadas no repositório.

São evidências pontuais extraídas do `TransportGraph` após a higienização.
Cada segmento reúne partidas com a mesma origem, destino e modal. Os segmentos
retos não representam as ruas nem uma rota calculada por A*.

O visualizador temporário e seus testes foram removidos. A visualização funcional
ficará a cargo do frontend.
