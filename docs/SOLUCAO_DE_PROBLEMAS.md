# Solução de problemas

[Início](../README.md) · [Documentação](README.md) · [Como usar](USO.md)

Comece pelo sintoma observado. Execute os comandos na pasta que contém `app.py`
e use o mesmo Python da instalação. Os exemplos abaixo são para PowerShell;
em macOS/Linux, troque `.\.venv\Scripts\python.exe` por `.venv/bin/python`.

| O que aconteceu? | Consulte |
| --- | --- |
| Python ou pacote não encontrado | [Python e ambiente virtual](#python-e-ambiente-virtual) |
| Modelo ausente, download interrompido ou hash incorreto | [Modelos](#modelos) |
| Webcam não abre, tela sem resposta ou teclas não funcionam | [Câmera e controles](#câmera-e-controles) |
| Erro de DLL, biblioteca `.so` ou interface gráfica | [Dependências nativas e janela](#dependências-nativas-e-janela) |
| Gesto instável, caneta sem traço ou referência corporal ausente | [Resultados dos modos](#resultados-dos-modos) |
| Imagem, desenho ou catálogo não foi salvo | [Arquivos e exportações](#arquivos-e-exportações) |
| O problema continua | [Relatar um erro](#relatar-um-erro) |

## Diagnóstico inicial

```powershell
.\.venv\Scripts\python.exe scripts/check_environment.py --imports --models all
```

O relatório mostra o executável usado e marca cada verificação como `[OK]` ou
`[FALHA]`. Resolva as falhas indicadas antes de testar novamente. O comando não
abre a câmera, não baixa modelos e não mede a qualidade das detecções.

Se a própria `.venv` ainda não existe, siga primeiro a
[instalação](INSTALACAO.md).

## Python e ambiente virtual

### `py -3.12` ou `python3.12` não foi encontrado

Confira se Python **3.12 de 64 bits** está instalado. O comando de criação do
ambiente precisa apontar para essa versão. Feche e reabra o terminal depois de
instalar o Python. A seção do seu sistema no
[guia de instalação](INSTALACAO.md) mostra os comandos completos.

### `No module named ...` ou dependências ausentes

Instale os pacotes usando explicitamente o executável do projeto:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/check_environment.py --imports
```

No VS Code, selecione o mesmo executável em **Python: Select Interpreter**.
Instalar um pacote com outro `pip` pode colocá-lo em um ambiente diferente
daquele que executa `app.py`.

### O PowerShell bloqueou `Activate.ps1`

Use diretamente `.\.venv\Scripts\python.exe`, como nos exemplos. A ativação
do ambiente e a alteração da política de execução não são necessárias.

### Há mais de uma distribuição OpenCV instalada

`opencv-python`, `opencv-contrib-python` e suas variantes headless fornecem o
mesmo módulo `cv2`. O projeto usa a distribuição fixada em
[`requirements.txt`](../requirements.txt).

Feche os processos que usam a `.venv`, preserve a pasta antiga com outro nome
e crie um ambiente novo seguindo [a instalação](INSTALACAO.md). Instale apenas
os requisitos do projeto nesse ambiente. Confira o diagnóstico antes de voltar
a executar o aplicativo.

### `mediapipe` não tem o atributo `solutions`

O GestureLab utiliza **MediaPipe Tasks**. Essa mensagem pode vir de um exemplo
antigo que usa `mp.solutions.hands`. Confira o arquivo executado e mantenha a
API usada pelo código atual do repositório.

## Modelos

### `Modelo não encontrado` ou arquivo `.task` ausente

```powershell
.\.venv\Scripts\python.exe scripts/download_models.py
.\.venv\Scripts\python.exe scripts/check_environment.py --models all
```

Os pesos ficam em `models/` e são baixados separadamente do Git. `hands` e
`airwrite` usam o mesmo Hand Landmarker. O modelo corporal pode ser preparado
separadamente com `scripts/download_models.py --only poses`.

Se você usou `--directory` no downloader, indique o arquivo correto com
`app.py --model caminho/arquivo.task`; mudar a pasta do download não altera o
caminho padrão do aplicativo. Veja [Modelos](../models/README.md).

### Download falhou ou o SHA-256 é diferente

Confira a conexão e a mensagem completa no terminal. Um modelo válido já
baixado é reutilizado. Um arquivo existente com hash divergente é preservado,
e o downloader interrompe a operação.

Confira a origem desse arquivo, mova-o para fora da pasta de modelos e tente
o download novamente. O hash deve conferir antes do uso. Detalhes de origem e
integridade estão no [guia dos scripts](../scripts/README.md#2-baixar-modelos).

## Câmera e controles

### `Webcam 0 indisponível`

1. Feche outros aplicativos que possam estar usando a câmera.
2. Confira se o sistema permite câmera para o terminal ou editor utilizado.
3. Confirme que a webcam está conectada e funciona em outro aplicativo; feche
   esse aplicativo antes de voltar ao GestureLab.
4. Experimente outro índice:

```powershell
.\.venv\Scripts\python.exe app.py --mode hands --camera 1
```

O índice padrão é `0`. Câmeras integradas, USB e virtuais podem receber índices
diferentes em cada equipamento.

### A câmera abriu, mas não entregou um frame válido

Confira a conexão, feche a execução e abra novamente. Se estiver usando câmera
virtual, confirme que sua fonte está ativa. O aplicativo encerra ao receber um
quadro inválido; a sessão da câmera é liberada ao sair.

### Teclas não respondem

Clique na **janela do GestureLab**, não no terminal, e tente novamente. **Q**
ou **Esc** encerra o modo. Espaço, C, Z, B e S são controles exclusivos de
`airwrite`. Os atalhos não existem na execução com `--headless`.

Feche o modo atual antes de iniciar outro. Veja a
[referência de uso](USO.md) para os controles completos.

### Quero verificar captura sem abrir uma janela

```powershell
.\.venv\Scripts\python.exe app.py --mode hands --headless --max-frames 30
```

Esse comando ainda usa webcam e modelo, mas termina após 30 quadros. Não exibe
a imagem e não testa os atalhos. O limite `--max-frames` é obrigatório para
webcam com `--headless`.

## Dependências nativas e janela

### A janela não abre

Use uma sessão local com interface gráfica. A janela OpenCV não aparece na
página do GitHub, em um notebook hospedado ou em um terminal remoto sem suporte
gráfico. Confira também se não passou `--headless`.

O modo `--image` processa uma foto e termina sem janela por definição. Para
ver a cópia anotada, forneça `--output` e abra o arquivo salvo.

Se houver conflito de pacotes OpenCV, siga
[a recuperação do ambiente](#há-mais-de-uma-distribuição-opencv-instalada).

### DLL ou biblioteca `.so` ausente

Rode o diagnóstico com `--imports` e identifique o nome da biblioteca na
mensagem. Em Linux mínimo, OpenCV/MediaPipe podem precisar de bibliotecas
gráficas mesmo em processamento por CPU. As orientações já usadas no projeto
para Ubuntu são `libgles2` para `libGLESv2.so.2` e `libgl1` para `libGL.so.1`.
Use o gerenciador da distribuição e a dependência correspondente ao erro.

No Windows, confira primeiro Python de 64 bits, ambiente virtual e pacotes.
Se a falha continuar, inclua a mensagem completa da DLL no
[relato do erro](#relatar-um-erro); ela determina qual componente falta.

## Resultados dos modos

### Mão não detectada, gesto desconhecido ou nome oscilando

Mantenha a mão inteira visível, melhore a iluminação e reduza movimentos
rápidos. `gestures` reconhece apenas as classes incluídas no modelo. Um gesto
rejeitado recebe `DESCONHECIDO`; ausência de mão recebe `SEM MAO DETECTADA`.

O score e o limiar `--threshold` controlam aceitação, mas não eliminam oscilações
entre quadros. A estabilização temporal dos nomes ainda está no
[roadmap](ROADMAP.md). Consulte [Como usar](USO.md) antes de alterar o limiar.

### Esquerda e direita parecem invertidas

A inferência usa a imagem original e o aplicativo espelha a visualização por
padrão. Confira se o driver ou a câmera virtual já espelha o sinal. Compare com
`--no-mirror` e verifique o resultado usando a própria mão.

### A caneta não desenha

Use **uma mão visível**, com indicador estendido e médio, anelar e mínimo
recolhidos. O polegar é ignorado. Mantenha a pose brevemente para confirmar a
escrita e confira se ela está pausada; Espaço pausa ou retoma.

A caneta interrompe o traço quando a mão some, quando há duas mãos ou quando
a pose de escrita deixa de ser aceita. Esse comportamento permite reposicionar
o dedo sem riscar. Movimento, perspectiva e oclusão podem dificultar a regra.
Veja [Escrita no ar](ESCRITA_NO_AR.md).

### PoseMatch não mostra uma referência

| Mensagem na tela | Próximo passo |
| --- | --- |
| `SEM PESSOA DETECTADA` | Confira iluminação e enquadramento do corpo. |
| `DEIXE APENAS UMA PESSOA VISIVEL` | Mantenha somente uma pessoa na imagem. |
| `MOSTRE O CORPO: OMBROS, QUADRIS E MEMBROS` | Afaste-se o suficiente para mostrar tronco e membros sem cortes. |
| `SEM IMAGEM SUFICIENTEMENTE PARECIDA` | Confira se o catálogo tem uma pose próxima e se o limiar não está restritivo. |
| `CONFIRMANDO POSE; MANTENHA A POSICAO` | Sustente a pose para manter a mesma candidata durante a confirmação. |

O catálogo inicial tem um conjunto finito de ilustrações. Uma pose nova pode
não ter uma correspondência adequada. Diminuir `--match-threshold` exige mais
semelhança; aumentar esse limite aceita referências mais distantes. Avalie os
resultados antes de mudar o padrão.

Na webcam, a confirmação dura 180 ms e reinicia se houver um intervalo maior
que 750 ms entre quadros. Uma execução muito lenta pode impedir a confirmação.
O [guia do PoseMatch](posematch/README.md) explica o critério e a avaliação.

## Arquivos e exportações

### O desenho não apareceu em `outputs/`

Em `airwrite`, pressione **S com a janela em foco antes de sair**. O terminal
mostra os caminhos do PNG e do JSON gravados. A pasta `outputs/` fica na raiz
do projeto e é criada no primeiro salvamento.

Não há salvamento automático nem reabertura de sessão. O PNG contém os traços
em fundo branco; não contém a imagem da webcam.

### `--output` foi recusado ou a saída já existe

`--output` serve para uma foto fornecida com `--image`. Use um caminho diferente
da imagem de entrada e um nome de saída ainda inexistente, terminado em `.png`,
`.jpg`, `.jpeg` ou `.webp`. Para a escrita ao vivo, use o atalho S.

Se o caminho tiver espaços, coloque-o entre aspas:

```powershell
.\.venv\Scripts\python.exe app.py --mode hands --image "minhas fotos/mao.jpg" --output outputs/mao_anotada.png
```

### O indexador de poses recusou a pasta ou as fotos

Escolha uma **pasta de saída nova**. Coloque arquivos PNG, JPG, JPEG ou WebP
diretamente na pasta de entrada; subpastas não são percorridas. Cada imagem
precisa fornecer uma pessoa e articulações suficientes para a comparação.

Confira os motivos impressos pelo script. Um catálogo sem nenhuma imagem
aceita não é criado. Siga as instruções de
[catálogo personalizado](../pose_gallery/README.md).

## Relatar um erro

Se o problema continuar, abra
[Relatar um erro](https://github.com/luigiscofano/gesturelab/issues/new?template=bug_report.yml)
e inclua:

- Sistema, arquitetura, versão do Python e commit ou branch utilizado.
- Comando exato executado e modo escolhido.
- Resultado esperado e o que aconteceu.
- Trecho relevante do terminal e resultado do diagnóstico.

Remova dados pessoais dos logs e das imagens antes de publicar. Se clonou o
repositório, obtenha o identificador da versão com `git rev-parse HEAD`.

---

[Rever a instalação](INSTALACAO.md) · [Voltar à documentação](README.md)
