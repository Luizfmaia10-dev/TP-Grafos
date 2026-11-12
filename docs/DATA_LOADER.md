# Carregamento e higienização de dados GTFS

`app.data_loader.DataLoader` lê os quatro arquivos CSV e retorna um `TransportGraph`
com objetos `Station` e `Connection`. Utiliza a biblioteca padrão do Python, sem
bibliotecas de grafos ou dependências da API. Os arquivos originais não são alterados.

## Uso

Os quatro TXT de `data/gtfs/` são versionados com **Git LFS**. Antes de carregar
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
from app.data_loader import DataLoader

loader = DataLoader("../data/gtfs")
graph = loader.build_graph()
print(json.dumps(loader.report.to_dict(), ensure_ascii=False, indent=2))
```

O exemplo acima carrega a base completa. A execução real foi validada: 9.659 estações,
107.621 viagens e 6.110.036 conexões. Resultados, medições e instruções de teste manual
estão em [GTFS_VALIDATION.md](GTFS_VALIDATION.md).

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

Após uma execução bem-sucedida, `read = accepted + rejected` em cada arquivo.
Nas tabelas de cadastro, `accepted` conta registros únicos válidos, mesmo quando
não utilizados por viagens. Nos horários, uma viagem rejeitada contabiliza todos
os seus registros como rejeitados, com o primeiro motivo detectado. Alertas não
alteram as contagens de aceitação.

Os motivos incluem `missing_required_value`, `invalid_coordinate`, `duplicate_record`,
`conflicting_id`, `unsupported_route_type`, `unknown_route`, `unknown_trip`,
`unknown_stop`, `too_few_stops`, `invalid_sequence`, `duplicate_sequence`,
`invalid_time`, `departure_before_arrival`, `negative_travel_time` e `zero_travel_time`.

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

Permanecem fora do escopo: calendário por data, geometria real e aplicação das
restrições de embarque/desembarque. `Connection` ainda não armazena `trip_id` ou
`service_id`; o grafo reúne os serviços carregados. Alertas de velocidade não
garantem admissibilidade da heurística do futuro roteador.

Os índices e o grafo permanecem na RAM. Valores numéricos repetidos são compartilhados
durante a carga, e os índices auxiliares de horários, distâncias e durações são limpos
ao finalizar ou iniciar uma nova carga. A inserção de conexões utiliza o método
ordenado existente. Na execução completa registrada, a carga levou 40,893 segundos
e o pico de RAM do processo foi de 598,641 MiB; os valores variam conforme o ambiente.

## Evidências visuais da carga

O `DataLoader` é chamado pelo comando `app.validate_gtfs` e pelos testes. Ainda
não é chamado pela aplicação FastAPI em `app/main.py` nem pelo frontend. O comando
cria o grafo na RAM e o libera ao terminar.

Durante a verificação manual foram geradas imagens de uma carga real: 9.659 paradas
e 13.765 segmentos direcionados, agregando 6.110.036 conexões horárias.
Um recorte da parada `14785288`, Avenida Dos Andradas 220, mostrou 964 partidas
e cinco destinos diretos. Essas imagens não estão versionadas no repositório.

São evidências pontuais extraídas do `TransportGraph` após a higienização.
Cada segmento reúne partidas com a mesma origem, destino e modal. Os segmentos
retos não representam as ruas nem uma rota calculada por A*.

O visualizador temporário e seus testes foram removidos. A visualização funcional
ficará a cargo do frontend.
