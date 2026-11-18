# Dataset GTFS e Git LFS

Esta pasta contém os dados dos sistemas convencional e suplementar de ônibus de Belo Horizonte,
disponibilizados pela BHTRANS/SUMOB no [Portal de Dados Abertos da PBH](https://ckan.pbh.gov.br/dataset/gtfs).

| Arquivo | Conteúdo | Tamanho desta versão |
|---|---|---:|
| `stops.txt` | Paradas, estações e coordenadas | 714.358 bytes |
| `routes.txt` | Linhas e tipos de transporte | 23.397 bytes |
| `trips.txt` | Viagens, linhas e identificadores de serviço | 10.377.665 bytes |
| `stop_times.txt` | Sequência de paradas e horários por viagem | 513.650.590 bytes |
| `calendar.txt` | Dias da semana e vigência dos serviços | 987 bytes |
| `calendar_dates.txt` | Exceções de operação por data | 1.236 bytes |

Apesar da extensão `.txt`, os arquivos são tabelas CSV. Eles são versionados com
**Git LFS**, porque `stop_times.txt` supera o limite de 100 MiB do GitHub para
arquivos no Git comum. O Git guarda um pequeno ponteiro e o LFS armazena o conteúdo
completo separadamente. O `DataLoader` lê os CSVs completos na pasta de trabalho.
O rastreamento é definido no `.gitattributes` da raiz e abrange somente
`data/gtfs/*.txt`; este README permanece no Git comum.

## Versão atual

Os seis arquivos foram extraídos juntos do [ZIP completo oficial](https://s3.amazonaws.com/mobilibus-uploads/gtfs/GTFSBHTRANS.zip),
consultado em 17/11/2026. O pacote inclui 326 linhas, 9.925 registros de paradas,
113.692 viagens, 14 serviços no calendário e 67 exceções de data.
Os 14 serviços referenciados em `trips.txt` estão presentes em `calendar.txt`.
A resolução automática por data está implementada no `DataLoader`. A base completa
foi validada em dia útil, sábado e uma data de Carnaval; os resultados estão em
[GTFS_VALIDATION.md](../../docs/GTFS_VALIDATION.md).

SHA-256 do ZIP utilizado:

```text
ce59b84334363364639848677f3a1aa1aabf7a3fc53a577ebfac9ba1f52f6d15
```

SHA-256 dos CSVs completos desta versão:

```text
294f5330e5750b37c824609ee6dbbb531b0248c8e08e40fed864f34b12002127  stops.txt
ca0f00d27cf61774ad0d2f191e6e820311ae26be67e33ed612278c24dbdf07ff  routes.txt
fb41ac59bce19d52f6274fcb159e2c71d8ccd510fe324fbe948631bbb7847ce5  trips.txt
ee3db9ff1dce3b5d5db9091a0ea07526796fb7f5f42f6aad326326fe78da6930  stop_times.txt
a537a8b0f39a671079a9d70ac1380f834759d3b0e48d2e44ccc774552675d57c  calendar.txt
4274d1317758dc25c4fa2051105f38c1c8918c5a885ac0abb9114cb5b1105efd  calendar_dates.txt
```

## Preparação

No Linux Mint/Ubuntu, instale uma vez:

```sh
sudo apt install git-lfs
git lfs install
```

Para inicializar somente um repositório existente, use `git lfs install --local`
na raiz dele. Em outros sistemas, siga a [instalação oficial](https://git-lfs.com/).

Com o LFS instalado antes do clone, o Git normalmente baixa os arquivos completos
automaticamente. Para um clone existente, após atualizar a branch, execute na raiz:

```sh
git lfs pull
git lfs ls-files
git lfs fsck
```

Depois que esta alteração for integrada à `main`, o fluxo de atualização será:

```sh
git switch main
git pull origin main
git lfs pull
```

Os objetos LFS precisam estar publicados pelo responsável pela branch para que
outros clones possam baixá-los. A migração local, sozinha, não os disponibiliza
no servidor. Neste trabalho, não é necessário migrar novamente a cada clone.

## Se o TXT contiver apenas uma referência

Um arquivo com três linhas começando assim ainda é um ponteiro:

```text
version https://git-lfs.github.com/spec/v1
oid sha256:...
size ...
```

Ele não pode ser usado como CSV. Na raiz do repositório, execute:

```sh
git lfs install --local
git lfs pull
```

Se os objetos já tiverem sido baixados, `git lfs checkout` restaura os TXT sem
acessar a rede. Se o download falhar, confira o acesso ao repositório, a conexão
e se os objetos foram enviados ao remoto. Não substitua o ponteiro por dados
inventados nem altere o carregador para aceitá-lo.

## Atualizar o dataset

1. Obtenha uma nova versão no portal oficial e extraia os seis arquivos listados
   acima do mesmo pacote, sem misturar versões. Não apague os demais arquivos da pasta.
2. Execute a [validação do carregamento](../../docs/GTFS_VALIDATION.md).
3. Na raiz, confira `git check-attr filter -- data/gtfs/*.txt`; o filtro deve ser `lfs`.
4. Prepare os TXT com `git add data/gtfs/*.txt`, revise com `git lfs status` e faça
   o commit da atualização. O filtro LFS gera os ponteiros automaticamente.
5. Ao publicar a atualização, o hook do Git LFS envia os objetos associados.

Datasets novos podem alterar contagens, alertas e hashes. Repita a auditoria antes
de adotar os números novos como referência. Não execute `git lfs migrate` para
cada atualização: a configuração existente já rastreia os TXT.

## Referência histórica da versão inicial

Os hashes SHA-256 abaixo identificam os CSVs completos usados na validação inicial:

```text
fe6cb25d74e21dd53261470e669f1b5f4ff4cfb17e18a9fdcea5d4567922215d  routes.txt
46bb0c6b45685651bf3c45009c120bd20d2ef60d91228d8bceadd96f1c0098ce  stop_times.txt
3ad490027bba8dc4067ca88a3c4e4310ec4675998747fa889927387b8687b5e4  stops.txt
261c9d029efa9df122a8d4c523da23d23e74677a95c7bc40c635a2af27c0fd9b  trips.txt
```

Use `sha256sum data/gtfs/*.txt` a partir da raiz para comparar com a versão atual.
Os quatro hashes desta seção são históricos e não devem ser usados para validar
o pacote completo atualizado. A migração para LFS preserva o conteúdo dos CSVs.

Referência: [Git LFS no GitHub](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage).
