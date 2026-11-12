# Dataset GTFS e Git LFS

Esta pasta contém os dados do sistema convencional de ônibus de Belo Horizonte,
disponibilizados pela BHTRANS/SUMOB no [Portal de Dados Abertos da PBH](https://ckan.pbh.gov.br/dataset/gtfs).

| Arquivo | Conteúdo | Tamanho desta versão |
|---|---|---:|
| `stops.txt` | Paradas, estações e coordenadas | 695.438 bytes |
| `routes.txt` | Linhas e tipos de transporte | 21.901 bytes |
| `trips.txt` | Viagens, linhas e identificadores de serviço | 9.865.521 bytes |
| `stop_times.txt` | Sequência de paradas e horários por viagem | 477.816.997 bytes |

Apesar da extensão `.txt`, os arquivos são tabelas CSV. Eles são versionados com
**Git LFS**, porque `stop_times.txt` supera o limite de 100 MiB do GitHub para
arquivos no Git comum. O Git guarda um pequeno ponteiro e o LFS armazena o conteúdo
completo separadamente. O `DataLoader` lê os CSVs completos na pasta de trabalho.
O rastreamento é definido no `.gitattributes` da raiz e abrange somente
`data/gtfs/*.txt`; este README permanece no Git comum.

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

1. Obtenha uma nova versão no portal oficial e extraia os quatro arquivos do mesmo
   pacote, sem misturar versões. Não apague os demais arquivos da pasta.
2. Execute a [validação do carregamento](../../docs/GTFS_VALIDATION.md).
3. Na raiz, confira `git check-attr filter -- data/gtfs/*.txt`; o filtro deve ser `lfs`.
4. Prepare os TXT com `git add data/gtfs/*.txt`, revise com `git lfs status` e faça
   o commit da atualização. O filtro LFS gera os ponteiros automaticamente.
5. Ao publicar a atualização, o hook do Git LFS envia os objetos associados.

Datasets novos podem alterar contagens, alertas e hashes. Repita a auditoria antes
de adotar os números novos como referência. Não execute `git lfs migrate` para
cada atualização: a configuração existente já rastreia os TXT.

## Verificação da versão inicial

Os hashes SHA-256 abaixo identificam os CSVs completos usados na validação inicial:

```text
fe6cb25d74e21dd53261470e669f1b5f4ff4cfb17e18a9fdcea5d4567922215d  routes.txt
46bb0c6b45685651bf3c45009c120bd20d2ef60d91228d8bceadd96f1c0098ce  stop_times.txt
3ad490027bba8dc4067ca88a3c4e4310ec4675998747fa889927387b8687b5e4  stops.txt
261c9d029efa9df122a8d4c523da23d23e74677a95c7bc40c635a2af27c0fd9b  trips.txt
```

Use `sha256sum data/gtfs/*.txt` a partir da raiz para comparar. A migração para LFS
preserva esses conteúdos e não altera o grafo construído.

Referência: [Git LFS no GitHub](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage).
