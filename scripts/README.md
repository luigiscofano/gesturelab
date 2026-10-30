# Scripts de preparação e diagnóstico

[Início](../README.md) · [Documentação](../docs/README.md) · [Instalação](../docs/INSTALACAO.md)

Execute os comandos abaixo na pasta que contém `app.py` e `requirements.txt`.
O downloader e o diagnóstico básico usam a biblioteca padrão do Python. O
diagnóstico só importa visão com `--imports`; o indexador de fotos utiliza as
bibliotecas de visão para detectar as poses nas imagens fornecidas.

| Script | Finalidade | Altera arquivos? |
| --- | --- | --- |
| [download_models.py](download_models.py) | Baixar os modelos oficiais e conferir SHA-256 | Sim, na pasta de modelos |
| [check_environment.py](check_environment.py) | Conferir Python, pacotes e verificações opcionais | Não altera o projeto |
| [build_pose_catalog.py](build_pose_catalog.py) | Indexar fotos locais para a busca por pose | Sim, na pasta de saída fornecida; preserva originais |

**Nesta página**

- [1. Conferir a instalação](#1-conferir-a-instalação)
- [2. Baixar modelos](#2-baixar-modelos)
- [3. Verificar modelos e ambiente juntos](#3-verificar-modelos-e-ambiente-juntos)
- [4. Criar um catálogo de fotos para posematch](#4-criar-um-catálogo-de-fotos-para-posematch)

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

Para preparar os quatro modos do aplicativo, baixe os três modelos:

```powershell
.\.venv\Scripts\python.exe scripts/download_models.py
```

No macOS / Linux, substitua o executável pelo da sua `.venv`:

```bash
.venv/bin/python scripts/download_models.py
```

| Opção | Resultado |
| --- | --- |
| Sem `--only` | Baixa Hand Landmarker, Gesture Recognizer e Pose Landmarker Lite |
| `--only hands` | Prepara `hands` e `airwrite` |
| `--only gestures` | Prepara `gestures` |
| `--only poses` | Prepara `posematch` e o indexador de fotos |
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

`--models hands` verifica Hand Landmarker; `--models gestures`, Gesture Recognizer;
`--models poses`, Pose Landmarker Lite. Sem `--models`, os arquivos `.task` não são
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
| Importação de biblioteca nativa falhou | Leia o erro e siga o [guia de solução de problemas](../docs/SOLUCAO_DE_PROBLEMAS.md). |

Use `python scripts/check_environment.py --help` e
`python scripts/download_models.py --help` para consultar as opções com o Python
do ambiente escolhido.

## 4. Criar um catálogo de fotos para posematch

Coloque fotografias autorizadas, preferencialmente de uma pessoa com o corpo
visível, em `data/minhas_fotos`. Depois de instalar as dependências e baixar o
modelo `poses`, execute:

```powershell
.\.venv\Scripts\python.exe scripts/build_pose_catalog.py --input data/minhas_fotos --output data/minha_galeria
.\.venv\Scripts\python.exe app.py --mode posematch --gallery data/minha_galeria/catalog.json
```

No macOS/Linux, use `.venv/bin/python`. A saída deve ser uma pasta nova. O
indexador prepara imagens e landmarks no mesmo catálogo, sem depender dos
caminhos dos originais e sem sobrescrevê-los. Fotos sem uma pose utilizável são
recusadas com um motivo. `data/` já é excluído do Git por padrão.

Veja o [README do catálogo](../pose_gallery/README.md) para opções, procedência e
limitações, e o [guia do modo](../docs/posematch/README.md) para execução e ranking.

---

**Próxima leitura:** [usar os quatro modos](../docs/USO.md), [resolver problemas](../docs/SOLUCAO_DE_PROBLEMAS.md) e [origem dos modelos](../models/README.md).
