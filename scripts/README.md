# Scripts de preparação e diagnóstico

[Visão geral](../README.md) · [Modelos](../models/README.md) ·
[Documentação](../docs/README.md)

Execute os comandos abaixo na pasta que contém `app.py` e `requirements.txt`.
Os dois scripts usam somente a biblioteca padrão do Python; o diagnóstico só
importa as bibliotecas de visão quando recebe `--imports`.

| Script | Finalidade | Altera arquivos? |
| --- | --- | --- |
| `download_models.py` | Baixar os modelos oficiais e conferir SHA-256 | Sim, na pasta de modelos |
| `check_environment.py` | Conferir Python, pacotes e verificações opcionais | Não altera o projeto |

## 1. Conferir a instalação

Depois de criar `.venv` e instalar `requirements.txt`, use o mesmo executável
Python que vai executar o aplicativo.

**Windows / PowerShell:**

```powershell
.\.venv\Scripts\python.exe scripts/check_environment.py
```

**macOS / Linux:**

```bash
.venv/bin/python scripts/check_environment.py
```

A verificação padrão compara o ambiente com a referência do repositório:
Python **3.12 de 64 bits** e as versões diretas fixadas em
[`requirements.txt`](../requirements.txt). Ela identifica pacotes ausentes,
versões diferentes e a presença de mais de uma distribuição OpenCV que forneça
`cv2`. Outra versão do Python é sinalizada como divergência do ambiente de
referência; o diagnóstico não demonstra incompatibilidade de todas as outras
versões.

Esse comando também funciona antes da instalação das dependências. Nesse caso,
é esperado que ele liste os pacotes ausentes e termine com código `1`.

Para verificar as bibliotecas nativas, acrescente `--imports`:

```powershell
.\.venv\Scripts\python.exe scripts/check_environment.py --imports
```

Isso carrega NumPy, OpenCV e MediaPipe Tasks. Erros como DLL ausente ou
`libGLESv2.so.2` aparecem como falhas de importação. O script não abre webcam,
não cria janela e não executa inferência. As próprias bibliotecas podem emitir
mensagens e criar caches durante a inicialização.

## 2. Baixar modelos

Para preparar os três modos do aplicativo, baixe os dois modelos:

```powershell
.\.venv\Scripts\python.exe scripts/download_models.py
```

No macOS / Linux, substitua o executável pelo da sua `.venv`:

```bash
.venv/bin/python scripts/download_models.py
```

| Opção | Resultado |
| --- | --- |
| Sem `--only` | Baixa Hand Landmarker e Gesture Recognizer |
| `--only hands` | Prepara `hands` e `airwrite` |
| `--only gestures` | Prepara `gestures` |
| `--directory caminho` | Usa uma pasta diferente de `models` |

O download exige conexão à internet. URLs versionados, nomes e hashes estão em
[`download_models.py`](download_models.py). Se um modelo já existe e seu hash
confere, ele é reutilizado. Se o hash diverge, o script interrompe a operação e
preserva esse arquivo: confira a origem e mova-o para fora da pasta antes de
tentar novamente. Um download incompleto fica temporariamente com extensão
`.part` e esse arquivo temporário é removido ao terminar a tentativa.

Não é necessário executar o download a cada abertura do aplicativo. Os pesos
baixados permanecem locais e estão excluídos do Git.

## 3. Verificar modelos e ambiente juntos

**Windows / PowerShell:**

```powershell
.\.venv\Scripts\python.exe scripts/check_environment.py --imports --models all
```

**macOS / Linux:**

```bash
.venv/bin/python scripts/check_environment.py --imports --models all
```

`--models hands` verifica apenas Hand Landmarker; `--models gestures` verifica
apenas Gesture Recognizer. Sem `--models`, os arquivos `.task` não são
verificados. O diagnóstico lê os arquivos e compara SHA-256 com as mesmas
referências do downloader; não baixa, apaga nem substitui modelos.

Para usar uma pasta personalizada, passe `--directory caminho` nos dois
scripts. Depois indique o arquivo correspondente com `app.py --model caminho/arquivo.task`:
o aplicativo continua usando `models` por padrão.

### Interpretar o resultado

| Código de saída | Significado |
| --- | --- |
| `0` | Todas as verificações solicitadas passaram |
| `1` | Ao menos uma verificação falhou |
| `2` | Argumentos inválidos, tratados pelo parser da CLI |

Um resultado aprovado não comprova funcionamento da webcam, abertura da janela,
qualidade dos gestos, velocidade ou precisão da escrita. Esses pontos exigem
execução local e registro em [`docs/VALIDACAO.md`](../docs/VALIDACAO.md).

| Falha | Próximo passo |
| --- | --- |
| Pacote ausente ou versão diferente | Use o Python da `.venv` para instalar `-r requirements.txt`. |
| Mais de um OpenCV instalado | Recrie a `.venv` e instale as dependências do projeto. |
| Modelo ausente | Execute o downloader para a tarefa desejada. |
| SHA-256 diferente | Confira a origem, mova o arquivo divergente e baixe novamente. |
| Importação de biblioteca nativa falhou | Leia o erro e as orientações de instalação no README geral. |

Use `python scripts/check_environment.py --help` e
`python scripts/download_models.py --help` para consultar as opções com o Python
do ambiente escolhido.
