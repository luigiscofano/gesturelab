# Referências e componentes de terceiros

[Início](README.md) · [Documentação](docs/README.md) · [Licença do código](LICENSE)

O código inicial foi preparado para Luigi Scofano de Araujo com assistência de IA.
Sua licença MIT não altera os termos de modelos, bibliotecas ou outros materiais.
Ao publicar sua evolução, documente o que estudou, alterou, implementou e avaliou.

## MediaPipe

- Projeto oficial: https://github.com/google-ai-edge/mediapipe
- Distribuição usada: https://pypi.org/project/mediapipe/1.2.0/
- API: MediaPipe Tasks para Python.
- Código do MediaPipe: licença Apache 2.0 conforme o projeto oficial.
- Modelos: Hand Landmarker, Gesture Recognizer e Pose Landmarker Lite oficiais,
  versão de artefato 1.
- Procedência, URLs e hashes: [documentação dos modelos](models/README.md) e [downloader](scripts/download_models.py).

Os pesos não acompanham o ZIP. O script baixa os artefatos oficiais. Consulte os
termos publicados pelo fornecedor antes de redistribuir pesos em outro produto;
não trate a licença do seu código como licença desses artefatos.

## OpenCV e NumPy

- OpenCV: https://pypi.org/project/opencv-contrib-python/
- NumPy: https://numpy.org/

O ambiente também instala dependências transitivas dos pacotes. Seus créditos e
licenças permanecem sob responsabilidade dos respectivos fornecedores.

## Referências de implementação

- https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/python
- https://developers.google.com/edge/mediapipe/solutions/vision/gesture_recognizer/python
- https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python
- https://docs.opencv.org/4.x/dd/d43/tutorial_py_video_display.html

O comportamento inicial foi inspirado no post mostrado pelo usuário: captura
de webcam, desenho dos pontos das mãos e evolução para reconhecimento de gestos.
O código não foi transcrito do screenshot. Imagens de teste de terceiros não são
incluídas nos entregáveis. As imagens de referência em `pose_gallery` são
ilustrações originais do projeto, conforme seu [README](pose_gallery/README.md).
Elas usam pontos definidos na construção do desenho, sem serem apresentadas
como fotografias detectadas pelo modelo. Fotografias adicionadas pelo usuário
mantêm sua origem e condições de uso; o indexador não transfere direitos sobre elas.

---

**Próxima leitura:** [procedência dos modelos](models/README.md), [origem das imagens](pose_gallery/README.md) e [como contribuir](CONTRIBUTING.md).
