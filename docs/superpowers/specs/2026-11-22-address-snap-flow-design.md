# Endereços e limites configuráveis no snap-to-network

Status: histórico. A implementação final substituiu Google Places por
Geoapify/OpenStreetMap, adotou dois controles no cabeçalho e permite qualquer
metro inteiro entre 100 e 2.000. O contrato vigente está em `docs/API.md` e no
código; as decisões abaixo registram a proposta anterior à validação visual.

Status: aprovado.

## Objetivo

Permitir que o usuário planeje uma rota a partir de endereços de Belo Horizonte. O frontend obtém endereço e coordenadas pelo Google Maps Places, o backend associa cada coordenada a uma parada real dentro do limite de caminhada escolhido e o itinerário inclui os trechos temporários de caminhada.

O fluxo mantém três responsabilidades separadas:

1. A página principal recebe o endereço de destino.
2. O modal de origem recebe o endereço inicial e permite trocar a parada recomendada.
3. O modal de limites altera somente as distâncias máximas aceitas para origem e destino.

## Decisões de interface

O cabeçalho terá dois controles independentes:

- `Definir origem`: abre exclusivamente o modal de endereço de origem.
- `Limites: O 800 m · D 800 m`: abre exclusivamente o modal de limites.

O modal de origem contém o autocomplete do Google Maps, a parada recomendada e as demais paradas que estejam dentro do limite de origem. A recomendada é a parada mais próxima. O usuário pode escolher outra parada da lista, mas nunca uma parada fora do limite.

O destino continua no formulário principal. Seu campo passa a receber um endereço por autocomplete do Google Maps. Após a confirmação do endereço, o sistema usa automaticamente a parada mais próxima dentro do limite de destino. A troca manual solicitada aplica-se somente à parada de origem.

O modal de limites contém abas `Origem` e `Destino`, valor em metros, controle deslizante, opções rápidas e botão de confirmação. Ele não contém campos de endereço nem seleção de paradas.

Os limites aceitos serão de 100 a 2.000 metros, em passos de 100 metros, com 800 metros como valor inicial para cada lado. A API também valida essa faixa; não será possível contornar a regra manipulando o JavaScript.

Quando o endereço da aba selecionada ainda não existir, o modal mostrará:

> Endereço de destino ainda não informado. Você pode salvar este limite agora. Depois de informar o destino na página principal, mostraremos a parada mais próxima dentro dele.

Quando o endereço existir, o modal exibirá abaixo do controle:

- a distância até a parada mais próxima;
- `Distância mínima necessária: X m`;
- a quantidade de paradas encontradas dentro do limite atual.

Se o limite atual for menor que a distância mínima, o modal mostrará `Nenhuma parada encontrada dentro deste limite`, manterá visível a distância mínima necessária e impedirá a confirmação até o usuário aumentar o limite. Sem endereço informado, a confirmação do limite permanece permitida porque ainda não existe uma coordenada para validar.

Todos os botões, abas, sugestões, cartões selecionáveis e campos terão estados de `hover`, `focus-visible`, desabilitado e carregamento. Os hovers serão aplicados dentro de `@media (hover: hover)` para não criarem estados presos em telas sensíveis ao toque.

## Integração com Google Maps

O frontend usará `PlaceAutocompleteElement` da Places API (New), restrito ao Brasil e à região de Belo Horizonte. Depois da seleção, solicitará somente `formattedAddress` e `location`.

A chave será lida de `GOOGLE_MAPS_API_KEY` pelo backend e fornecida ao frontend por uma configuração pública mínima. Chaves de navegador não são tratadas como segredo; a documentação exigirá restrição por origem HTTP e por APIs autorizadas no Google Cloud. O repositório não armazenará chave real.

Se a chave não estiver configurada ou o Google estiver indisponível, os campos de endereço ficarão indisponíveis com uma mensagem objetiva. O autocomplete de paradas atual não será usado como substituto silencioso, pois isso mudaria o significado do campo.

## API e modelos

Será criado `POST /snap/candidates` para pré-visualização. A entrada terá latitude, longitude e limite em metros. A resposta terá as paradas dentro do limite ordenadas por distância, a parada mais próxima e a distância mínima necessária. A busca examina apenas estações reais e ignora `TemporaryVertex`.

`POST /routes/search` continuará aceitando o contrato atual de IDs de estações para não quebrar testes, scripts ou integrações existentes. Ele também aceitará uma consulta por endereços com:

- endereço, latitude, longitude e limite da origem;
- ID da parada de origem escolhida;
- endereço, latitude, longitude e limite do destino;
- horário de partida.

No modo por endereço, o servidor repetirá todas as validações. A parada de origem escolhida deverá existir e estar dentro do limite informado. A parada de destino será a estação real mais próxima dentro do limite de destino. Coordenadas inválidas, limites fora da faixa, parada escolhida fora do limite e ausência de parada produzirão respostas estruturadas com códigos diferentes.

## Motor de rotas

O limite fixo de 800 metros será substituído por um parâmetro validado em cada chamada de snap. A velocidade de caminhada continuará em 5 km/h e a distância continuará sendo estimada por Haversine; a interface informará que se trata de uma aproximação em linha reta, não de uma rota pedestre de ruas.

O grafo compartilhado não será modificado durante uma requisição. Cada `RouteSimulator`, já criado por busca, manterá uma sobreposição local de conexões temporárias:

- origem temporária para a parada de origem escolhida;
- parada de destino calculada para o destino temporário.

O A* consultará as conexões do grafo e essa pequena sobreposição local. Ao terminar a busca, inclusive em erro, a sobreposição e os vértices temporários deixam de ser usados. Isso preserva a limpeza solicitada e evita que duas requisições simultâneas enxerguem os vértices temporários uma da outra.

Os nomes dos `TemporaryVertex` usarão os endereços formatados para que o `Itinerary` gere instruções de caminhada compreensíveis. As arestas `WALK` continuarão aparecendo na timeline e no mapa pelos renderizadores existentes.

## Fluxo de dados

1. O usuário abre `Definir origem`, escolhe um endereço e recebe as paradas candidatas conforme o limite de origem.
2. A parada mais próxima é selecionada inicialmente; o usuário pode trocar por outra candidata e confirma.
3. O usuário informa o endereço de destino no formulário principal. O frontend pré-visualiza a parada mais próxima conforme o limite de destino.
4. O usuário pode abrir `Limites` a qualquer momento. Sem endereço, apenas salva a distância. Com endereço, vê a distância mínima necessária e a validade do limite.
5. Ao calcular, o frontend envia coordenadas, endereços, limites, parada de origem escolhida e horário.
6. O backend revalida, cria os vértices e conexões temporários locais, executa o A* e constrói o `Itinerary` antes de descartar o estado temporário.
7. O frontend renderiza os trechos de caminhada, transporte e chegada como já faz hoje.

## Tratamento de erros

- `snap_distance_out_of_range`: limite menor que 100 m ou maior que 2.000 m.
- `invalid_coordinates`: latitude ou longitude inválida.
- `no_station_within_limit`: nenhuma estação real dentro do limite.
- `selected_station_outside_limit`: parada de origem escolhida não pertence às candidatas válidas.
- `unknown_station`: ID de parada inexistente.
- `maps_unavailable`: chave ausente ou carregamento do Google Maps indisponível no frontend.
- `invalid_address_selection`: texto digitado sem confirmação de uma sugestão do Google.

O frontend exibirá mensagens em português próximas ao controle afetado e também em região `aria-live`. Alterar endereço ou limite cancela qualquer busca de rota em andamento e invalida pré-visualizações antigas.

## Testes

O desenvolvimento seguirá TDD.

Backend:

- validação dos limites 100 e 2.000 m e rejeição dos valores externos;
- candidatos ordenados e exclusão de vértices temporários;
- troca da parada de origem dentro do limite;
- rejeição da parada de origem fora do limite;
- ausência de parada no limite;
- origem e destino temporários no mesmo cálculo;
- limpeza em sucesso, ausência de rota e exceção;
- isolamento entre simuladores simultâneos;
- compatibilidade do contrato antigo de `POST /routes/search`.

Frontend:

- estado do modal de limites com e sem endereço;
- distância mínima necessária e confirmação bloqueada quando o limite é insuficiente;
- separação entre modal de origem, campo de destino e modal de limites;
- seleção de parada de origem somente entre candidatas válidas;
- invalidação após alteração de endereço ou limite;
- estados de carregamento, erro, teclado, foco, Escape e restauração de foco;
- hovers apenas em dispositivos que os suportam;
- serialização da nova consulta e renderização dos trechos `WALK`.

Navegador:

- desktop e celular, temas claro e escuro;
- abertura e fechamento dos dois modais;
- endereço de destino informado exclusivamente na página principal;
- limite salvo antes do endereço;
- origem com troca de parada válida;
- limite abaixo da distância mínima;
- rota completa com caminhada nas duas extremidades;
- nenhuma regressão no seletor de horário, Limpar, mapa e timeline.

## Alternativas descartadas

Não será usado um único modal para endereço, parada e distância porque ele mistura responsabilidades e foi rejeitado na validação visual.

Não será criado um proxy completo para o autocomplete do Google. O componente oficial no navegador já administra a sessão de autocomplete, acessibilidade e seleção do local com menos código.

Não serão adicionadas bibliotecas espaciais ou bancos de dados. Para o MVP, a varredura linear das aproximadamente dez mil estações mantém o motor em memória e evita dependências proibidas. Uma estrutura espacial somente seria justificada por medições futuras.

## Fora do escopo

- cálculo de rota pedestre real pelas ruas;
- escolha manual da parada de destino;
- suporte a endereços fora de Belo Horizonte;
- persistência dos endereços ou preferências do usuário no servidor;
- criação ou cobrança de uma conta Google Cloud.

