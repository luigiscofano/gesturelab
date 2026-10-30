# Instalação e primeiro uso

[Início](../README.md) · [Documentação](README.md) · [Como usar](USO.md)

Este guia leva do download do projeto à primeira janela com os pontos da mão.
O GestureLab roda no seu computador; a página do GitHub reúne código e documentação.

**Nesta página:** [Preparação](#antes-de-começar) · [Obter o projeto](#1-obter-o-projeto) ·
[Windows](#2-instalar-no-windows) · [macOS/Linux](#3-instalar-no-macos-ou-linux) ·
[Primeiro resultado](#4-confirmar-o-primeiro-resultado) · [Atualizar](#atualizar-uma-instalação)

## Antes de começar

| Você precisa de | Para quê |
| --- | --- |
| [Python **3.12 de 64 bits**](https://www.python.org/downloads/) | Executar o aplicativo no ambiente de referência do projeto |
| Webcam e sessão com interface gráfica | Usar os quatro modos ao vivo |
| Internet durante a preparação | Instalar os pacotes e baixar os modelos |
| [Git](https://git-scm.com/downloads), se escolher clonar | Obter o repositório e receber atualizações com `git pull` |
| Editor de código, como [VS Code](https://code.visualstudio.com/download) | Ler e editar os arquivos; é opcional para executar |

Os links levam aos sites oficiais. Para seguir os comandos deste projeto,
escolha a série **Python 3.12**, mesmo que a página destaque uma versão mais nova.
No VS Code, a extensão **Python**, publicada pela Microsoft, disponibiliza a
seleção do interpretador. Veja também o
[roteiro de preparação dos programas](GUIA_COMPLETO.md#41-instalar-os-programas).

As versões diretas das bibliotecas estão em
[`requirements.txt`](../requirements.txt). Use um ambiente virtual próprio para
este projeto: ele mantém essas dependências separadas das de outros programas.

O CI verifica lógica e formatação em Windows e Ubuntu. O funcionamento da
webcam e da janela precisa ser confirmado no computador que vai executar o
aplicativo. O procedimento para macOS está incluído abaixo, mas não representa
uma validação de hardware nesse sistema. Os registros estão em
[Validação](VALIDACAO.md).

## 1. Obter o projeto

### Com Git

No terminal, escolha a pasta em que deseja guardar o projeto e execute:

```bash
git clone https://github.com/luigiscofano/gesturelab.git
cd gesturelab
```

### Pelo ZIP

Na [página do repositório](https://github.com/luigiscofano/gesturelab), escolha
**Code → Download ZIP**, extraia o arquivo e abra a pasta extraída no editor.
Ela normalmente se chama `gesturelab-main`.

**A pasta correta contém diretamente `app.py` e `requirements.txt`.** Abra o
terminal nessa pasta. Não execute os comandos de dentro do ZIP nem na pasta
que apenas contém o projeto. No VS Code, use **Terminal → New Terminal** depois
de abrir a pasta correta.

Escolha agora a seção do seu sistema operacional.

## 2. Instalar no Windows

Os comandos desta seção são para o **PowerShell**, na raiz do projeto.

### Criar o ambiente e instalar os pacotes

Confirme primeiro que o Python esperado está disponível:

```powershell
py -3.12 --version
```

A resposta deve começar com `Python 3.12`. Em seguida:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Cada comando usa explicitamente o Python da `.venv`. Não é necessário ativar o
ambiente nem alterar a política de execução do PowerShell. Se `py -3.12` não
encontrar o Python, confira se a versão 3.12 de 64 bits está instalada.

No VS Code, abra **Python: Select Interpreter** na paleta de comandos e
selecione `.venv\Scripts\python.exe`.

### Preparar e conferir os modelos

```powershell
.\.venv\Scripts\python.exe scripts/download_models.py
.\.venv\Scripts\python.exe scripts/check_environment.py --imports --models all
```

O primeiro comando baixa os três modelos necessários aos quatro modos. O
segundo verifica Python, versões dos pacotes, importações e integridade dos
arquivos. Ao terminar sem falhas, ele exibe
`Todas as verificações solicitadas passaram.`

Se aparecer `[FALHA]`, consulte a mensagem correspondente em
[Solução de problemas](SOLUCAO_DE_PROBLEMAS.md) antes de abrir o aplicativo.

### Abrir o primeiro modo

```powershell
.\.venv\Scripts\python.exe app.py --mode hands
```

Continue em [Confirmar o primeiro resultado](#4-confirmar-o-primeiro-resultado).

## 3. Instalar no macOS ou Linux

Execute estes comandos em um terminal, na raiz do projeto, com Python 3.12
disponível como `python3.12`:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/download_models.py
.venv/bin/python scripts/check_environment.py --imports --models all
.venv/bin/python app.py --mode hands
```

No VS Code, selecione `.venv/bin/python` como interpretador. Os exemplos dos
outros guias usam PowerShell: nesses sistemas, substitua
`.\.venv\Scripts\python.exe` por `.venv/bin/python`, mantendo os argumentos.

Use uma sessão local com interface gráfica e permita acesso à câmera para o
terminal ou editor utilizado. Se uma biblioteca nativa estiver ausente, veja
[Dependências nativas e janela](SOLUCAO_DE_PROBLEMAS.md#dependências-nativas-e-janela).

## 4. Confirmar o primeiro resultado

1. Aguarde a janela **GestureLab** abrir e permita o acesso à câmera, caso o
   sistema solicite.
2. Mostre uma mão inteira, com boa iluminação. Os pontos e suas conexões devem
   acompanhar a mão quando ela for detectada.
3. Clique na janela e pressione **Q** ou **Esc** para encerrar.
4. Com a execução anterior encerrada, experimente outro modo:

| Quero experimentar | Argumentos depois do executável Python |
| --- | --- |
| Pontos e conexões das mãos | `app.py --mode hands` |
| Nomes de gestos conhecidos | `app.py --mode gestures` |
| Desenho com o indicador | `app.py --mode airwrite` |
| Uma imagem com pose corporal parecida | `app.py --mode posematch` |

O [guia de uso](USO.md) explica o resultado de cada modo, os controles e os
arquivos de saída. Na escrita, pressione **S antes de sair** para guardar o
desenho. Não há salvamento automático.

### Usar uma foto sem webcam

Os modos `hands`, `gestures` e `posematch` também processam uma foto. Por
exemplo, salve uma fotografia sua como `minha_foto.jpg` na raiz do projeto e use:

```powershell
.\.venv\Scripts\python.exe app.py --mode hands --image minha_foto.jpg --output outputs/minha_foto_anotada.png
```

Esse comando imprime os dados no terminal e salva uma cópia anotada. Ele não
abre câmera nem janela. Escolha uma saída nova: arquivos existentes não são
sobrescritos. A foto de exemplo deve ser fornecida por você.

`airwrite` precisa de movimento ao longo do tempo e não aceita `--image`.

## Atualizar uma instalação

### Se você clonou com Git

Feche o aplicativo e confira o estado da cópia local:

```bash
git status
```

Se houver alterações suas, salve-as em um commit na sua branch de trabalho
antes de atualizar. O [guia de contribuição](../CONTRIBUTING.md) explica esse
fluxo. Com a cópia de trabalho limpa, execute:

```bash
git switch main
git pull --ff-only origin main
```

Se o Git informar que as branches divergiram, pare a atualização e confira o
histórico. Não descarte commits locais para forçar o comando.

Depois, confira novamente dependências e modelos.

**Windows / PowerShell:**

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts/download_models.py
.\.venv\Scripts\python.exe scripts/check_environment.py --imports --models all
```

**macOS / Linux:**

```bash
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/download_models.py
.venv/bin/python scripts/check_environment.py --imports --models all
```

Modelos já presentes com SHA-256 correto são reutilizados. Consulte o
[histórico de alterações](../CHANGELOG.md) para saber o que mudou.

### Se você baixou o ZIP

Baixe a versão nova e extraia em **outra pasta**. Refaça a instalação nela e
copie apenas os dados próprios que deseja manter, como `data/` e `outputs/`.
Preserve a cópia antiga até conferir seus arquivos e a nova execução. O ZIP
não contém o histórico necessário para usar `git pull`.

## Preparação opcional

| Necessidade | Onde continuar |
| --- | --- |
| Baixar só o modelo de um modo | [Opções do downloader](../scripts/README.md#2-baixar-modelos) |
| Usar fotografias próprias como referências | [Catálogo de poses](../pose_gallery/README.md) |
| Executar testes e verificações de código | [Guia de testes](../tests/README.md) |
| Entender um erro da instalação | [Solução de problemas](SOLUCAO_DE_PROBLEMAS.md) |
| Aprender os controles dos quatro modos | [Como usar](USO.md) |

---

[Próximo: usar o GestureLab](USO.md) · [Voltar à documentação](README.md)
