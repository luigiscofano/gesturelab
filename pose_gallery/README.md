# Catálogo de imagens para poses parecidas

[Projeto](../README.md) · [Modo posematch](../docs/posematch/README.md) ·
[Scripts](../scripts/README.md)

O catálogo inicial contém **12 ilustrações originais de personagens articulados**,
com os braços e as pernas em posições diferentes. O modo `posematch` compara a
pose detectada na câmera com essas referências e mostra a imagem mais próxima
entre as candidatas aceitas pelo limiar.

As imagens não são fotografias nem resultados de uma pesquisa na internet. Elas
foram desenhadas por código para que as posições das articulações sejam conhecidas
e para permitir uma primeira execução sem baixar um banco de imagens externo.
A busca fica limitada ao conteúdo deste catálogo. Quanto mais variadas e adequadas
forem as referências, maior a possibilidade de encontrar uma pose próxima.

## Conteúdo

| Caminho | Finalidade |
| --- | --- |
| [catalog.json](catalog.json) | Poses, caminhos das imagens e metadados de origem |
| [images](images) | PNGs exibidos pelo aplicativo e SVGs editáveis correspondentes |
| [generate_catalog.py](generate_catalog.py) | Fonte reprodutível das ilustrações e dos pontos |
| [build_pose_catalog.py](../scripts/build_pose_catalog.py) | Indexador de fotos próprias com o modelo real |

As referências incluem braços ao lado, abertos, levantados, um braço elevado,
mãos na cintura, cotovelos dobrados, V baixo, agachamento aberto, passo lateral,
um joelho elevado, avanço com braços abertos e inclinação lateral. A comparação
permite espelhar as referências; o mesmo desenho
de um braço levantado pode representar o outro lado.

Os desenhos não contêm texto visível incorporado, para que o espelhamento não
inverta letras. Título, origem e créditos aparecem separadamente na interface.

## Origem e licença

Os desenhos e o gerador fazem parte do código próprio do GestureLab sob
[licença MIT](../LICENSE), preparados com assistência de IA. Não foram copiados
de fotografias, personagens ou bancos de imagens de terceiros.

Neste catálogo ilustrado, os **12 pontos usados na comparação** correspondem à
geometria exata dos desenhos: ombros, cotovelos, punhos, quadris, joelhos e
tornozelos. As demais entradas do array de 33 landmarks mantêm a forma do esquema
e não participam do cálculo. Elas não representam uma inferência do MediaPipe
sobre as ilustrações. O campo `landmark_origin` registra `exact_drawing_geometry`.

Cada referência traz `source`, `license` e `credit`. Esses dados acompanham a
imagem exibida. Os arquivos `.task` do MediaPipe têm procedência separada; consulte
o [README de modelos](../models/README.md).

## Criar um catálogo com suas próprias fotos

Prepare uma pasta contendo arquivos PNG, JPG, JPEG ou WEBP. Escolha imagens com
uma única pessoa, torso e membros visíveis. O script examina somente os arquivos
diretamente nessa pasta, sem percorrer subpastas.

Na raiz do projeto, depois de instalar as dependências:

```powershell
.\.venv\Scripts\python.exe scripts/download_models.py --only poses
.\.venv\Scripts\python.exe scripts/build_pose_catalog.py --input minhas_fotos --output data/minhas_poses --source "Fotos próprias" --license "Uso pessoal"
.\.venv\Scripts\python.exe app.py --mode posematch --gallery data/minhas_poses/catalog.json
```

Em macOS/Linux, use `.venv/bin/python` no lugar do executável do Windows.
Os valores de `--source` e `--license` são metadados informados por você;
o programa não verifica a titularidade das imagens. Se houver autores ou licenças
diferentes, revise os campos de cada referência no JSON antes de publicar.

O indexador usa **Pose Landmarker real em modo IMAGE**. Imagens sem pessoa,
com duas pessoas detectadas ou com pontos insuficientes são ignoradas. As aceitas
são copiadas como PNG, com dimensão máxima de 960 pixels e proporção preservada,
para `images/` dentro da saída. O JSON contém landmarks medidos nessas imagens;
o campo `landmark_origin` registra `mediapipe_pose_landmarker`.

O diretório de saída deve ser novo. O script recusa substituir um catálogo
existente e não modifica as fotos originais. Para atualizar a coleção, gere outra
pasta e indique o novo JSON em `--gallery`. Se nenhuma foto for aceita, ele informa
o problema e não publica um catálogo vazio. `data/` está ignorada pelo Git para
evitar que fotos locais sejam incluídas nos commits por acidente.

Use fotos com os direitos necessários. O modelo foi feito para corpos humanos;
animais, objetos e desenhos estilizados podem não ser detectados. Um catálogo
de personagens pode usar pontos revisados manualmente, mas essa anotação deve
ser identificada, como no catálogo ilustrado incluído.

## Regenerar as ilustrações incluídas

Com OpenCV e NumPy do projeto instalados:

```powershell
.\.venv\Scripts\python.exe pose_gallery/generate_catalog.py
```

Esse comando sobrescreve os arquivos **gerados desta pasta**, incluindo o catálogo
original. Ele é uma ferramenta de desenvolvimento; não use esse local para guardar
suas fotos ou edições manuais. Para mudar uma pose, altere os pontos em `POSES`,
regenere e confira visualmente PNG e SVG. O aplicativo lê os PNGs; não precisa
executar o gerador para usar a coleção distribuída.

## Esquema do catálogo

O JSON declara `schema_version: 1` e uma lista não vazia em `references`. Cada
referência precisa de `id`, `title`, `image`, `width`, `height` e 33 objetos de
landmarks com `x`, `y`, `visibility` e `presence`. Os caminhos de imagem são
relativos ao diretório do catálogo e precisam permanecer dentro dele.

O carregador rejeita identificadores repetidos, imagens ausentes e poses sem
articulações suficientes. As distâncias retornadas são geométricas, em unidades
normalizadas pelo tronco; não são probabilidades nem uma avaliação de qualidade
anatômica. A comparação não reconhece a identidade das pessoas.
