# Modelos de visão computacional

[Início](../README.md) · [Documentação](../docs/README.md) · [Scripts](../scripts/README.md)

Esta pasta recebe os modelos **pré-treinados do MediaPipe** usados na inferência.
O GestureLab não treinou esses modelos. O código da aplicação controla captura,
visualização, estado da escrita e exportação; os arquivos `.task` fornecem a
detecção de mãos, a classificação pronta de gestos e os landmarks corporais.

## Qual modelo cada modo utiliza

| Arquivo | Modos do aplicativo | Finalidade |
| --- | --- | --- |
| `hand_landmarker.task` | `hands`, `airwrite` | Detectar os pontos das mãos |
| `gesture_recognizer.task` | `gestures` | Detectar pontos e classificar gestos conhecidos |
| `pose_landmarker_lite.task` | `posematch`, indexador de fotos | Detectar 33 pontos corporais; a comparação é feita pelo código do projeto |

O modo `airwrite` usa uma regra geométrica sobre os pontos retornados pelo Hand
Landmarker. Não há um modelo de reconhecimento de letras nesta pasta. O modo
`gestures` utiliza somente Gesture Recognizer, que já fornece os landmarks.

## Preparação

Execute na raiz do projeto, com o ambiente virtual criado e o Python correto.

**Windows / PowerShell:**

```powershell
.\.venv\Scripts\python.exe scripts/download_models.py
.\.venv\Scripts\python.exe scripts/check_environment.py --models all
```

**macOS / Linux:**

```bash
.venv/bin/python scripts/download_models.py
.venv/bin/python scripts/check_environment.py --models all
```

O primeiro comando baixa os três modelos; o segundo confere sua integridade e
as versões das dependências. Para preparar somente `hands` e `airwrite`, use
`download_models.py --only hands` e `check_environment.py --models hands`.
Nesse caso, o modo `gestures` ainda precisa do outro arquivo.
Para preparar apenas a busca corporal, use `download_models.py --only poses` e
`check_environment.py --models poses`.

O download precisa de internet. Depois que os arquivos estão na pasta esperada,
não é necessário baixá-los novamente para cada execução.

## Origem e integridade

Os bundles estão fixados na versão `/float16/1/`. O downloader e o diagnóstico
compartilham a mesma tabela de referências em
[`scripts/download_models.py`](../scripts/download_models.py).

| Arquivo | SHA-256 esperado |
| --- | --- |
| `hand_landmarker.task` | `fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1` |
| `gesture_recognizer.task` | `97952348cf6a6a4915c2ea1496b4b37ebabc50cbbf80571435643c455f2b0482` |
| `pose_landmarker_lite.task` | `59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a` |

Fontes dos arquivos:

- [Hand Landmarker, bundle versão 1](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task).
- [Gesture Recognizer, bundle versão 1](https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task).
- [Pose Landmarker Lite, bundle versão 1](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task).

Se um arquivo existente tiver outro hash, o downloader preserva esse arquivo e
informa a divergência. Confira a origem e mova-o para fora desta pasta antes de
tentar novamente. Verificar o hash confirma que o arquivo corresponde à versão
esperada; não mede a qualidade da detecção.

## Modelos alternativos

O aplicativo aceita `--model caminho/arquivo.task` para substituir o bundle do
modo escolhido. O arquivo precisa ser compatível com a tarefa executada. O
diagnóstico `--models` foi feito para os bundles oficiais desta tabela;
um modelo personalizado terá outro hash e não passará nessa comparação.

Se baixar os oficiais com `--directory outra_pasta`, use a mesma opção no
diagnóstico e aponte `app.py --model` para o arquivo dessa pasta. A configuração
padrão do aplicativo continua apontando para `models`.

## Versionamento e licença

Nesta pasta, os arquivos `.task` e downloads incompletos ficam excluídos do Git; este README
documenta como obtê-los sem acrescentar pesos ao histórico. Os modelos mantêm
as condições e licenças do fornecedor, separadas da licença MIT do código do
GestureLab. Consulte as referências oficiais antes de redistribuir os pesos:

- [Documentação e modelos do Hand Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker).
- [Documentação e modelos do Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer).
- [Documentação e modelos do Pose Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker).
- [Avisos de terceiros do projeto](../THIRD_PARTY_NOTICES.md).

---

**Próxima leitura:** [diagnóstico do ambiente](../scripts/README.md), [como usar os modelos](../docs/USO.md) e [créditos](../THIRD_PARTY_NOTICES.md).
