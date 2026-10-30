# Modelos oficiais

Execute `python scripts/download_models.py` na raiz do projeto. O script baixa
os bundles oficiais versionados `/float16/1/` e verifica seu SHA-256.

| Arquivo | Tarefa | SHA-256 |
| --- | --- | --- |
| `hand_landmarker.task` | Landmarks das mãos | `fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1` |
| `gesture_recognizer.task` | Landmarks e gestos conhecidos | `97952348cf6a6a4915c2ea1496b4b37ebabc50cbbf80571435643c455f2b0482` |

URLs completas estão no script. Os modelos não fazem parte do código MIT deste
projeto. Consulte documentação, model cards e condições do fornecedor antes de
redistribuir pesos ou usar em produção. Downloads não estão incluídos no Git.

- [Hand Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker)
- [Gesture Recognizer](https://ai.google.dev/edge/mediapipe/solutions/vision/gesture_recognizer)
