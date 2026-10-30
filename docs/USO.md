# Como usar o GestureLab

[Início](../README.md) · [Documentação](README.md) · [Instalação](INSTALACAO.md)

Escolha um modo, execute o comando e interaja com a janela que ele abre.
Este guia reúne os controles e as opções disponíveis. Se ainda não preparou o
ambiente e os modelos, comece pela [instalação](INSTALACAO.md).

**Nesta página:** [escolher um modo](#escolha-um-modo) ·
[mãos](#mãos--hands) · [gestos](#gestos--gestures) ·
[escrita](#escrita-no-ar--airwrite) · [poses parecidas](#poses-parecidas--posematch) ·
[fotos](#processar-uma-foto) · [opções](#referência-de-opções) ·
[arquivos e privacidade](#arquivos-e-privacidade)

## Escolha um modo

| Quero... | Modo | O que aparece |
| --- | --- | --- |
| Ver os pontos e as conexões das mãos | `hands` | 21 pontos por mão, conexões e indicação de esquerda/direita |
| Ver o nome de um gesto conhecido | `gestures` | Pontos, nome do gesto e pontuação do modelo |
| Desenhar com o indicador | `airwrite` | Cursor, traços e estado da caneta |
| Encontrar uma imagem com pose corporal parecida | `posematch` | Sua captura e a referência mais próxima aceita do catálogo |

Os exemplos são para **PowerShell no Windows**, na pasta que contém `app.py`.
No macOS/Linux, substitua `.\.venv\Scripts\python.exe` por `.venv/bin/python`.
Coloque caminhos com espaços entre aspas, como `--image "minhas fotos/pose.jpg"`.

O modo é escolhido ao iniciar. Para trocar, pressione **Q** ou **Esc**, espere
o terminal ficar disponível e execute o próximo comando. Clique na janela do
GestureLab para que ela receba os atalhos. O aplicativo roda no seu computador;
a página do GitHub apresenta o código e os guias.

## Mãos — hands

```powershell
.\.venv\Scripts\python.exe app.py --mode hands
```

Mostre uma ou duas mãos à câmera. Cada mão detectada recebe 21 pontos vermelhos
e conexões claras. A indicação `Esquerda` ou `Direita` se refere à pessoa.
Quando nenhuma mão é encontrada, aparece `SEM MAO DETECTADA`.

Para estudar quais pontos formam cada dedo:

```powershell
.\.venv\Scripts\python.exe app.py --mode hands --show-indices
```

Os números vão de 0 a 20; o ponto 8 é a ponta do indicador. Consulte o
[mapa dos pontos da mão](assets/hand_landmarks.png) e a
[arquitetura](ARQUITETURA.md) para relacionar o desenho ao código.

## Gestos — gestures

```powershell
.\.venv\Scripts\python.exe app.py --mode gestures
```

Faça um dos gestos da tabela com a mão bem visível. O modelo pronto do MediaPipe
reconhece estas classes; o projeto traduz os rótulos exibidos:

| Classe do modelo | Texto na janela |
| --- | --- |
| `Closed_Fist` | `PUNHO FECHADO` |
| `Open_Palm` | `MAO ABERTA` |
| `Pointing_Up` | `INDICADOR PARA CIMA` |
| `Thumb_Down` | `POLEGAR PARA BAIXO` |
| `Thumb_Up` | `JOIA` |
| `Victory` | `VITORIA` |
| `ILoveYou` | `I LOVE YOU` |
| `None`, classe ausente ou pontuação abaixo do limiar | `DESCONHECIDO` |

`DESCONHECIDO` significa que há uma mão, mas nenhum gesto foi aceito.
`SEM MAO DETECTADA` significa que o modelo não encontrou uma mão.
Os textos da janela usam caracteres sem acentos por compatibilidade com a
fonte do OpenCV. `ILoveYou` é apenas o nome de uma classe; o aplicativo não
traduz Libras.

O `score` exibido é a pontuação do modelo, não uma porcentagem de acerto medida.
O limiar padrão é `0.65`. Para exigir uma pontuação maior:

```powershell
.\.venv\Scripts\python.exe app.py --mode gestures --threshold 0.75
```

Um limiar maior pode aumentar as rejeições. Os nomes são atualizados a cada
frame e ainda podem oscilar entre classes. A confirmação temporal dos outros
modos não se aplica aos rótulos de `gestures`.

## Escrita no ar — airwrite

```powershell
.\.venv\Scripts\python.exe app.py --mode airwrite
```

1. Deixe somente uma mão visível, aproximadamente de frente para a câmera.
2. Estenda o indicador e recolha médio, anelar e mínimo. O polegar é ignorado.
3. Mantenha a pose brevemente até o cursor indicar escrita e mova o indicador.
4. Abra a mão ou dobre o indicador para levantar a caneta e reposicionar.
5. Volte à pose de escrita para começar outro traço.

Cada traço é independente: reposicionar a mão com a caneta levantada não deve
criar uma linha entre letras. Perder a mão ou detectar duas mãos interrompe o
traço. O filtro de suavização reduz oscilações do cursor.

### Atalhos da escrita

| Tecla | Ação |
| --- | --- |
| **Espaço** | Pausar ou retomar a caneta |
| **C** | Limpar todo o desenho |
| **Z** | Desfazer o último traço |
| **B** | Alternar entre a webcam e o fundo branco |
| **S** | Salvar o desenho em PNG e as trajetórias em JSON |
| **Q** ou **Esc** | Sair |

**Pressione S antes de sair.** Não há salvamento automático nem reabertura de
sessões. Os arquivos aparecem em `outputs/`, criada no primeiro salvamento.
O terminal informa os caminhos. Cada salvamento recebe um nome próprio.

Para começar sobre uma folha branca, mudar a espessura ou comparar sem filtro:

```powershell
.\.venv\Scripts\python.exe app.py --mode airwrite --canvas
.\.venv\Scripts\python.exe app.py --mode airwrite --pen-width 7
.\.venv\Scripts\python.exe app.py --mode airwrite --smooth-ms 0
```

Execute uma linha de cada vez. A escrita usa uma sequência da webcam e não
aceita `--image`. Ela gera desenhos e trajetórias; ainda não transforma letras
desenhadas em texto. O [guia de escrita no ar](ESCRITA_NO_AR.md) explica a regra
da caneta, a suavização, o formato dos dados e a evolução para reconhecer letras.

## Poses parecidas — posematch

```powershell
.\.venv\Scripts\python.exe app.py --mode posematch
```

Fique sozinho no enquadramento e mostre ombros, quadris, braços e pernas.
Faça uma pose e mantenha-a brevemente. O painel da direita mostra a referência
aceita mais próxima, seu título, a distância e os créditos. O catálogo inicial
contém 12 ilustrações originais de personagens articulados.

**Menor distância significa maior semelhança geométrica.** Esse valor não é uma
probabilidade de acerto. O título pertence à imagem do catálogo e não representa
uma classificação universal do movimento. Se não houver referência próxima
o suficiente, o aplicativo informa que não encontrou uma imagem adequada.

O limiar padrão é `0.8`, experimental. Para exigir maior proximidade:

```powershell
.\.venv\Scripts\python.exe app.py --mode posematch --match-threshold 0.5
```

A busca ocorre no catálogo local. Ela não pesquisa a internet nem gera uma
imagem nova. O detector trabalha com anatomia humana; o indexador não oferece
detecção genérica de poses de animais ou objetos.

### Usar fotografias próprias

Coloque fotos com uma pessoa e corpo visível em `data/minhas_fotos`. Então:

```powershell
.\.venv\Scripts\python.exe scripts/build_pose_catalog.py --input data/minhas_fotos --output data/minha_galeria
.\.venv\Scripts\python.exe app.py --mode posematch --gallery data/minha_galeria/catalog.json
```

A pasta de saída deve ser nova. O indexador aceita PNG, JPG, JPEG e WebP
diretamente na pasta de entrada e informa quais imagens não produzem uma pose
utilizável. As fotos originais são preservadas. Prepare o modelo `poses` antes,
conforme a [instalação](INSTALACAO.md).

Consulte o [catálogo](../pose_gallery/README.md) para informar origem e licença
das imagens, e o [guia do PoseMatch](posematch/README.md) para entender a
comparação e a confirmação temporal.

## Processar uma foto

Os modos `hands`, `gestures` e `posematch` também processam uma fotografia.
Use seus próprios arquivos nos exemplos abaixo:

```powershell
.\.venv\Scripts\python.exe app.py --mode hands --image foto_da_mao.jpg
.\.venv\Scripts\python.exe app.py --mode gestures --image foto_da_mao.jpg --output outputs/gesto.png
.\.venv\Scripts\python.exe app.py --mode posematch --image minha_pose.jpg --output outputs/comparacao.png
```

Esse uso **não abre a webcam nem uma janela**: o resultado aparece como JSON
no terminal. `--output` é opcional; quando fornecido, grava uma imagem para
você abrir no visualizador do sistema. Os diretórios necessários são criados.

Nos modos de mãos, o JSON inclui coordenadas, lateralidade e, em `gestures`,
o nome e a pontuação. As coordenadas pertencem à imagem original, mesmo se a
visualização estiver espelhada. Em `posematch`, ele informa a referência,
a distância e até três candidatas aceitas; se não houver correspondência,
`match` será `null`.

A saída deve usar outro nome que o original e não pode existir previamente.
As extensões de saída aceitas são `.png`, `.jpg`, `.jpeg` e `.webp`.
O aplicativo processa webcam ou uma foto; não há opção `--video` para arquivos.

## Referência de opções

A ajuda da versão instalada está sempre disponível:

```powershell
.\.venv\Scripts\python.exe app.py --help
```

### Gerais

| Opção | Padrão | Uso |
| --- | --- | --- |
| `--mode` | `hands` | Escolher `hands`, `gestures`, `airwrite` ou `posematch` |
| `--camera` | `0` | Índice da webcam; tente `1` se houver outra câmera |
| `--mirror` / `--no-mirror` | Espelhamento ativado | Alterar a visualização; a imagem enviada ao modelo permanece original |
| `--model` | Modelo correspondente em `models/` | Informar outro arquivo `.task` compatível com a tarefa escolhida |
| `--image` | Desativado | Processar uma foto; disponível em `hands`, `gestures` e `posematch` |
| `--output` | Sem arquivo de imagem | Gravar a foto anotada ou comparação; exige `--image` |
| `--headless` | Desativado | Executar a webcam sem janela; exige `--max-frames` |
| `--max-frames` | Sem limite | Encerrar a captura após um número inteiro positivo de frames |

`--camera` e `--max-frames` atuam na webcam, não no processamento de foto.
`--headless` dispensa a janela, mas ainda precisa de uma câmera acessível.
Sem janela, os atalhos de escrita e o salvamento por S ficam indisponíveis.

```powershell
.\.venv\Scripts\python.exe app.py --mode hands --camera 1
.\.venv\Scripts\python.exe app.py --mode hands --no-mirror
.\.venv\Scripts\python.exe app.py --mode hands --headless --max-frames 30
```

### Específicas de cada modo

| Opção | Onde tem efeito | Padrão e restrições |
| --- | --- | --- |
| `--num-hands` | Detecção nos modos de mãos | `2`; inteiro positivo. Em `airwrite`, o detector procura pelo menos duas para interromper a escrita se ambas aparecerem |
| `--show-indices` | Desenho de `hands` e `gestures` | Desativado; exibe os índices de 0 a 20 |
| `--threshold` | Rótulos de `gestures` | `0.65`; número entre `0` e `1` |
| `--canvas` | `airwrite` | Desativado; inicia com fundo branco; rejeitado nos outros modos |
| `--smooth-ms` | `airwrite` | `45`; número finito maior ou igual a zero; `0` desliga a suavização |
| `--pen-width` | `airwrite` | `5` pixels; inteiro positivo |
| `--gallery` | `posematch` | `pose_gallery/catalog.json`; rejeitado nos outros modos |
| `--match-threshold` | `posematch` | `0.8`; distância finita maior ou igual a zero; rejeitado nos outros modos |

Use ponto como separador decimal nos comandos: `0.65`, não `0,65`.
Quanto maior `--smooth-ms`, maior a suavização e o possível atraso da caneta.
Os parâmetros de `gestures` e `posematch` têm significados diferentes: um
rejeita pontuações baixas; o outro rejeita distâncias altas.

## Arquivos e privacidade

| Operação | O que fica salvo |
| --- | --- |
| Executar qualquer modo com webcam | Nenhum vídeo ou frame é gravado automaticamente |
| Pressionar **S** em `airwrite` | PNG com tinta sobre branco, sem webcam nem textos da interface; JSON com os traços e suas coordenadas |
| Usar `--image` sem `--output` | JSON impresso no terminal; nenhuma imagem de saída |
| Usar `--image` com `--output` em `hands` ou `gestures` | Sua foto com pontos e rótulos |
| Usar `--image` com `--output` em `posematch` | Composição que contém sua foto e a imagem de referência |
| Criar um catálogo de fotos | Cópias das imagens aceitas e `catalog.json` na pasta de saída escolhida |

O processamento usa modelos locais. O download inicial dos modelos precisa de
internet; a inferência e a busca no catálogo não enviam frames a um serviço.
O [aviso do MediaPipe](https://pypi.org/project/mediapipe/1.2.0/) informa que a
biblioteca pode enviar métricas de desempenho e uso; processamento local não
significa ausência absoluta de comunicação de rede.
`outputs/`, `data/` e os modelos baixados estão ignorados pelo Git. Antes de
compartilhar resultados, confira quais arquivos contêm pessoas e quais imagens
você tem autorização para publicar.

## Próximo passo

- Algo não funcionou? Consulte [Solução de problemas](SOLUCAO_DE_PROBLEMAS.md).
- Quer entender o código? Siga a [Arquitetura](ARQUITETURA.md).
- Quer modificar ou testar? Leia [Como contribuir](../CONTRIBUTING.md) e
  [Testes](../tests/README.md).
- Quer explorar todos os guias? Volte à [Documentação](README.md).
