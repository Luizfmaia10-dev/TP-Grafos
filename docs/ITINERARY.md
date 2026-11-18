# Itinerary

`app.itinerary.Itinerary(origin, departure_time, path)` encapsula a sequência
ordenada `list[tuple[Station, Connection]]` retornada por `RouteSimulator`.
Os horários de entrada usam minutos fracionários desde o início do dia de serviço;
horários acima de 24h são preservados. Um caminho vazio representa a permanência
na origem. Uma rota indisponível (`None`) deve ser tratada por quem chama o
roteador e não deve ser convertida em um itinerário vazio.

O itinerário é imutável, utiliza `__slots__` e expõe `origin`, `destination`,
`departure_time`, `arrival_time`, `total_seconds`, `waiting_seconds`,
`travel_seconds`, `distance_km`, `steps` e `instructions`. Cada trecho armazena
uma cópia dos dados da conexão. A caminhada começa imediatamente; conexões com
horário marcado incluem o tempo de espera. Os horários absolutos são arredondados
para segundos antes das subtrações, garantindo que a soma das durações corresponda
ao tempo total. Caminhos desconectados, partidas anteriores à chegada e tempos de
deslocamento negativos geram `ValueError`.

As instruções são strings em inglês para cada conexão, com instruções separadas
para a espera. Elas identificam modal, linha, estações e horários, sem pressupor
que conexões consecutivas da mesma linha pertencem ao mesmo veículo.

`to_dict()` retorna dicionários independentes de estações e trechos, compatíveis
com JSON, representando os tipos de veículo por seus valores textuais.
`to_json()` preserva os nomes com caracteres Unicode. Ambos incluem instruções
e totais. A construção e a serialização têm complexidade de tempo e espaço O(N)
para N conexões.

A função `build_route_result()` da API adapta os trechos e totais do itinerário
aos modelos de resposta existentes. O esquema HTTP e o tipo de retorno do
roteador permanecem inalterados; as instruções estão disponíveis no objeto de
domínio e em sua serialização.
