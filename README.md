# GestureLab

[![Python checks](https://github.com/luigiscofano/gesturelab/actions/workflows/ci.yml/badge.svg)](https://github.com/luigiscofano/gesturelab/actions/workflows/ci.yml)

Protótipo em Python para detectar **21 pontos por mão**, desenhar conexões sobre a
webcam, dar nome a gestos conhecidos e **escrever no ar com o indicador**. Usa modelos prontos do
MediaPipe Tasks; o projeto não treina um detector do zero.

[Documentação](docs/README.md) · [Guia completo](docs/GUIA_COMPLETO.md) ·
[Escrita no ar](docs/ESCRITA_NO_AR.md) · [Roadmap](docs/ROADMAP.md) ·
[Validação](docs/VALIDACAO.md) · [Contribuir](CONTRIBUTING.md)

**Autor do projeto:** Luigi Scofano de Araujo. Este starter foi preparado com apoio
de IA. Antes de apresentar como projeto concluído, execute, estude, adapte e registre
os seus próprios resultados.

## Por onde começar

| Quero... | Começo por... |
| --- | --- |
| Rodar a webcam pela primeira vez | [Instalação no Windows](#instalação-no-windows) ou [macOS/Linux](#macos-ou-linux) |
| Desenhar com o dedo e salvar o resultado | [Escrever no ar](#escrever-no-ar) |
| Entender os módulos e as decisões | [Arquitetura](docs/ARQUITETURA.md) |
| Estudar o projeto e preparar o portfólio | [Guia completo](docs/GUIA_COMPLETO.md) e [índice da documentação](docs/README.md) |
| Executar ou ampliar os testes | [README de testes](tests/README.md) |
| Propor uma melhoria em um pull request | [Guia de contribuição](CONTRIBUTING.md) |

O aplicativo roda no seu computador e abre uma janela do OpenCV. O GitHub hospeda
o código e a documentação; não há um aplicativo de webcam publicado no navegador.

## O que já está implementado

- Webcam com até duas mãos por padrão; pontos vermelhos e conexões claras.
- Modo `hands`, que reproduz o objetivo visual do post de referência.
- Modo `gestures`, que mostra o nome em português dos gestos suportados pelo modelo.
- Modo `airwrite`, que usa o indicador como caneta, preserva traços separados e suaviza a trajetória.
- Na escrita: pausar, limpar, desfazer, alternar fundo e exportar PNG + JSON sem imagem da webcam.
- `DESCONHECIDO` quando há mão, mas nenhum gesto aceito; `SEM MAO DETECTADA` quando não há mão.
- Conversão BGR para RGB e timestamps crescentes para inferência sequencial.
- Espelhamento apenas da visualização, preservando o referencial das mãos no modelo.
- Foto de teste sem webcam, download de modelos com SHA-256, testes e CI de lógica pura.

**Ainda não implementado:** treino de gestos próprios, estabilização temporal dos
rótulos do modo gestures, identificação persistente das mãos, reconhecimento de letras,
poses do corpo e demo no navegador.
O [guia completo](docs/GUIA_COMPLETO.md) explica essas evoluções.

## Instalação no Windows

Use Python **3.12 de 64 bits**, VS Code e uma webcam. Os comandos abaixo são para
o **PowerShell**, executados dentro da pasta `gesturelab`. Não precisam ativar o
ambiente virtual nem alterar a política de execução do Windows.

Com Git instalado, obtenha o projeto:

```powershell
git clone https://github.com/luigiscofano/gesturelab.git
cd gesturelab
```

Você também pode baixar o ZIP pelo botão **Code → Download ZIP** no GitHub.
Extraia o arquivo e abra no VS Code a pasta que contém diretamente `app.py` e
`requirements.txt`, normalmente `gesturelab-main`. Execute os comandos no terminal
dessa pasta, não de dentro do ZIP nem da pasta que o contém. Em seguida:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/download_models.py
.\.venv\Scripts\python.exe scripts/check_environment.py --imports --models all
.\.venv\Scripts\python.exe app.py --mode hands
```

Se `py -3.12` não encontrar o Python, instale essa versão ou substitua por um
executável Python 3.12 disponível no seu computador. No VS Code, selecione
`.venv\Scripts\python.exe` em **Python: Select Interpreter**.

O diagnóstico verifica versões, importação das bibliotecas e integridade dos
modelos. Ele não abre a webcam; as opções estão no [README dos scripts](scripts/README.md).

Para nomear gestos:

```powershell
.\.venv\Scripts\python.exe app.py --mode gestures
```

O modo é escolhido ao iniciar: feche a janela atual com **Q** ou **Esc** antes de
executar outro comando. Os atalhos funcionam com a **janela do GestureLab em foco**;
clique nela se as teclas não responderem. O programa não grava a webcam por padrão.
No modo de gestos, `score` é a pontuação do modelo; não é uma probabilidade
calibrada de acerto. O limiar inicial de 0,65 precisa ser avaliado no seu cenário.

### Escrever no ar

```powershell
.\.venv\Scripts\python.exe app.py --mode airwrite
```

Use uma mão visível, com indicador estendido e médio, anelar e mínimo recolhidos.
O polegar é ignorado. Mantenha a pose brevemente e mova o indicador para escrever.
Abra a mão ou dobre o indicador para reposicionar sem riscar. O app interrompe
o traço se a mão some ou se detectar duas mãos.

| Tecla | Ação |
| --- | --- |
| Espaço | Pausar ou retomar |
| C | Limpar |
| Z | Desfazer último traço |
| B | Alternar webcam e fundo branco |
| S | Salvar PNG do desenho + JSON das trajetórias em outputs |
| Q ou Esc | Sair |

**Pressione S antes de sair para guardar o desenho.** Não há salvamento automático
nem reabertura de uma sessão anterior. Cada salvamento cria um par de arquivos com
nome próprio em `outputs/`, pasta criada no primeiro salvamento. Clique na janela
do GestureLab antes de usar os atalhos.

O modo `airwrite` precisa de uma sequência; não aceita `--image`. Os arquivos
exportados não contêm a webcam. Ainda não há conversão automática de desenhos em
letras. Veja o [guia de escrita no ar](docs/ESCRITA_NO_AR.md) para funcionamento,
limitações e a evolução para reconhecimento de caracteres.

### macOS ou Linux

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/download_models.py
.venv/bin/python scripts/check_environment.py --imports --models all
.venv/bin/python app.py --mode hands
```

Em distribuições Linux mínimas, o MediaPipe pode exigir bibliotecas gráficas do
sistema mesmo em inferência por CPU. Se a mensagem mencionar `libGLESv2.so.2`, no
Ubuntu a dependência é `libgles2`; se mencionar `libGL.so.1`, verifique `libgl1`.
Use o gerenciador da sua distribuição. Isso não se aplica ao procedimento normal
do Windows.

## Comandos úteis

| Objetivo | Argumentos depois de `python app.py` |
| --- | --- |
| Reproduzir landmarks do post | `--mode hands` |
| Nomear gestos conhecidos | `--mode gestures` |
| Escrever com o indicador | `--mode airwrite` |
| Iniciar escrita sobre branco | `--mode airwrite --canvas` |
| Comparar sem suavização | `--mode airwrite --smooth-ms 0` |
| Mudar espessura da caneta | `--mode airwrite --pen-width 7` |
| Tentar outra webcam | `--camera 1` |
| Exibir os índices dos pontos | `--show-indices` |
| Ver imagem sem espelhamento | `--no-mirror` |
| Ajustar rejeição de gestos | `--mode gestures --threshold 0.75` |
| Processar foto sem abrir janela | `--image foto.jpg --output outputs/foto.png` |
| Encerrar webcam depois de 300 frames | `--max-frames 300` |
| Testar câmera sem janela | `--headless --max-frames 30` |

O modo de foto imprime JSON com coordenadas originais, nome/score da mão e,
quando aplicável, gesto. `--output` é opcional e só pode ser usado com `--image`.
Uma saída existente não é sobrescrita; escolha outro nome. A imagem original é
preservada. Não há `--video`: este starter processa webcam ou uma foto.

## Gestos incluídos no modelo pronto

| Nome retornado pelo modelo | Rótulo na tela |
| --- | --- |
| `Closed_Fist` | Punho fechado |
| `Open_Palm` | Mão aberta |
| `Pointing_Up` | Indicador para cima |
| `Thumb_Down` | Polegar para baixo |
| `Thumb_Up` | Joia |
| `Victory` | Vitória |
| `ILoveYou` | I LOVE YOU |
| `None`, categoria ausente ou score baixo | Desconhecido |

`ILoveYou` é o nome de uma classe do modelo, não uma implementação de tradução
de Libras. A tela usa texto sem acentos por uma limitação das fontes do OpenCV.

## Como o código está organizado

| Caminho | Responsabilidade |
| --- | --- |
| `app.py` | CLI, câmera, MediaPipe, desenho e processamento de foto |
| `core.py` | Geometria do desenho, nomes, rejeição por score e timestamps |
| `airwriting.py` | Pose de escrita, separação de traços, suavização e estado da caneta |
| `scripts/download_models.py` | Modelos oficiais versionados e integridade SHA-256 |
| [`scripts/README.md`](scripts/README.md) | Uso dos utilitários de preparação e diagnóstico |
| [`models/README.md`](models/README.md) | Procedência, download e integridade dos modelos |
| [`tests/README.md`](tests/README.md) | Como executar a suíte e interpretar seus limites |
| [`.github/README.md`](.github/README.md) | Workflows e organização das contribuições no GitHub |
| `requirements.txt` | Versões fixas das dependências diretas |
| [`docs/README.md`](docs/README.md) | Índice de guias, planos e registros de validação |
| [`docs/assets/README.md`](docs/assets/README.md) | Diagramas, fontes vetoriais e manutenção das imagens |

Cada pasta documenta seu próprio conteúdo. O roteiro de estudo e portfólio está no
[guia completo](docs/GUIA_COMPLETO.md); o comportamento da caneta e sua evolução
para reconhecer caracteres estão no [guia de escrita no ar](docs/ESCRITA_NO_AR.md).

O frame original é convertido de BGR para RGB e entregue ao modelo. O desenho
espelhado usa `x_exibido = largura - 1 - x_original_em_pixels`. Assim o texto
continua legível e a inferência usa a convenção de handedness da API Tasks atual.
`Esquerda` e `Direita` se referem à pessoa. Verifique com a própria mão ao testar;
webcams virtuais e drivers podem já entregar um frame espelhado.

O modo webcam usa `VIDEO` de forma síncrona: um resultado por frame processado.
É uma escolha didática. `LIVE_STREAM` com callback pode ser uma evolução; requer
tratar concorrência e frames descartados. O modo `gestures` executa somente o
Gesture Recognizer, que já retorna landmarks: não roda dois modelos em paralelo.

## Testes e execução reproduzível

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

Os testes verificam coordenadas espelhadas, limites da imagem, rejeição de gestos,
distinção entre classes conhecidas e desconhecidas, timestamps e restrições da CLI.
Não medem a qualidade do modelo. O workflow executa a análise de código e os testes
em Windows e Linux. A [primeira execução no GitHub Actions](https://github.com/luigiscofano/gesturelab/actions/runs/41074869460)
foi aprovada nos dois sistemas; o badge acima acompanha o estado atual.
O [README de testes](tests/README.md) explica os cenários cobertos e como distinguir
verificação de lógica de validação da webcam e dos modelos.

`requirements.txt` fixa dependências diretas. Para registrar também o ambiente
completo depois de funcionar na sua máquina:

```powershell
.\.venv\Scripts\python.exe -m pip freeze | Out-File -Encoding utf8 requirements-lock-windows.txt
```

Identifique sistema, arquitetura e versão do Python junto com esse arquivo.
Um `pip freeze` de Linux não é automaticamente um lockfile universal para Windows.

## Limitações e cuidados de engenharia

- A webcam e a janela precisam ser verificadas no computador do usuário; esta
  pasta não implica teste de hardware Windows ou calibração da sua câmera.
- `FPS loop` é uma média suavizada do ciclo de captura, inferência e desenho;
  não é uma medição de latência ponta a ponta nem uma garantia de FPS.
- `z` normalizado representa profundidade estimada, não distância em centímetros.
- Movimento rápido, mãos parcialmente fora da imagem, iluminação e oclusão afetam
  o resultado. Índices de mãos na lista não são identificadores persistentes.
- O limiar aceita/rejeita a classe, mas não estabiliza os rótulos entre frames.
  Adicionar uma janela temporal exige associar a mesma mão ao longo do tempo.
- A escrita usa uma regra geométrica de pose e uma única mão por vez. Ela confirma
  a entrada na escrita e suaviza o cursor, mas não reconhece letras nem identifica
  persistentemente a mesma pessoa. Perspectiva e oclusão ainda afetam a regra.
- A aplicação não envia fotos nem vídeos para um servidor próprio. O fornecedor
  informa que o processamento de entrada ocorre no dispositivo e que APIs Tasks
  podem enviar métricas de desempenho/uso. Não prometa ausência absoluta de rede.
- Não publique imagens de outras pessoas ou datasets brutos sem autorização.
  `data/`, `outputs/`, vídeos e pesos estão no `.gitignore` por padrão.

## Soluções para erros comuns

| Sintoma | O que verificar |
| --- | --- |
| `No module named ...` | Instale com o executável de `.venv` e selecione o mesmo no VS Code. |
| `mediapipe` sem atributo `solutions` | Este projeto usa Tasks; não misture exemplos antigos de `mp.solutions.hands`. |
| Modelo não encontrado | Execute `scripts/download_models.py` e confira a pasta `models`. |
| Webcam indisponível | Permissão do sistema, outro app usando câmera, `--camera 0` ou `--camera 1`. |
| Janela não abre | Execute localmente; não use `opencv-python-headless` para esta interface. |
| Teclas não respondem | Clique na janela do GestureLab; atalhos não são comandos para digitar no terminal. |
| Desenho não aparece em `outputs/` | Use S com a janela em foco antes de sair; a aplicação não salva automaticamente. |
| Pacotes OpenCV conflitantes | Recrie `.venv` e instale apenas `requirements.txt`. |
| Mãos esquerda/direita invertidas | Verifique se o driver já espelha a captura antes do aplicativo. |
| Gesto troca de nome continuamente | Teste iluminação, distância e limiar; estabilização é uma etapa futura. |

## Documentação oficial e licença

Referências consultadas em 30/10/2026:

- [MediaPipe Tasks para Python](https://ai.google.dev/edge/mediapipe/solutions/setup_python)
- [Hand Landmarker para Python](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker/python)
- [Gesture Recognizer para Python](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer/python)
- [Pacote MediaPipe 1.2.0 e aviso de privacidade](https://pypi.org/project/mediapipe/1.2.0/)
- [Distribuições OpenCV para Python](https://pypi.org/project/opencv-contrib-python/)

Código próprio sob [MIT](LICENSE). Dependências, modelos e quaisquer imagens de
teste mantêm suas respectivas licenças. Ao publicar sua evolução, mantenha os
créditos das referências e explique quais partes implementou, mediu e modificou.
Consulte os [créditos e componentes de terceiros](THIRD_PARTY_NOTICES.md) para a
procedência das bibliotecas e dos modelos.
