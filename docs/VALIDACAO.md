# Registro de validação do starter

Data: **30 de outubro de 2026**. Este registro documenta verificações realmente
executadas durante a preparação do projeto. Não é uma avaliação de acurácia e
não substitui o teste da webcam no computador de Luigi.

## Ambiente usado

| Item | Ambiente de teste |
| --- | --- |
| Sistema | Ubuntu 24.04, x86-64, ambiente sem webcam e sem janela de desktop |
| Python | 3.12.14 |
| MediaPipe | 1.2.0 |
| OpenCV | Distribuição `opencv-contrib-python` 5.0.0.93, módulo `cv2` 5.0.0 |
| NumPy | 2.5.4 |
| pytest | 9.2.0 |
| Ruff | 0.17.3 |

As dependências foram instaladas em um ambiente virtual isolado. `pip check`
terminou com **No broken requirements found**. O ambiente final contém apenas
`opencv-contrib-python`; não mistura distribuições que compartilham `cv2`.

Este Linux mínimo não tinha `libGLESv2.so.2`, necessária ao carregamento do
MediaPipe. A biblioteca oficial Ubuntu `libgles2` foi extraída para uma pasta
temporária e disponibilizada ao processo por `LD_LIBRARY_PATH`. O sistema não
foi alterado. Essa configuração é específica do ambiente de teste: não é uma
etapa extra para o Windows. Também foi usado um cache temporário gravável para
o Matplotlib, dependência indireta do MediaPipe.

## O que foi verificado

| Verificação | Resultado observado |
| --- | --- |
| `python -m pytest -q` | **18 testes passaram** |
| `python -m ruff check .` | Nenhum erro reportado |
| Imports reais | `cv2`, `mediapipe` e `numpy` carregaram com as versões acima |
| CLI `--help` | Lista os dois modos e as opções sem exigir webcam ou modelo |
| Download dos modelos | Ambos baixados dos URLs oficiais `/float16/1/` |
| Integridade | SHA-256 dos dois arquivos coincide com o script |
| Hand Landmarker em IMAGE | Uma mão, 21 landmarks na foto de teste positiva |
| Gesture Recognizer em IMAGE | Uma mão, 21 landmarks, classe `Thumb_Up`, rótulo `JOIA` |
| Desenho | Foto anotada inspecionada; pontos e conexões acompanham a mão na visualização espelhada |
| Hand Landmarker em VIDEO | Cinco frames sequenciais; uma mão e 21 landmarks em cada resultado |
| Gesture Recognizer em VIDEO | Cinco frames sequenciais; rótulo `JOIA` em cada resultado |
| Frame vazio após sequência | Zero mãos nos dois modos |

Na foto positiva, o Gesture Recognizer retornou score de aproximadamente **0,732**
para `Thumb_Up`, acima do limiar inicial 0,65. Isso descreve uma única inferência;
não representa acurácia de 73,2%, calibração, desempenho médio ou garantia de
reconhecimento em novas pessoas.

A sequência VIDEO usou a mesma foto repetida com timestamps **0, 33, 66, 100 e
133 ms**, seguida por um frame vazio em 200 ms. Ela verifica a integração com a
API temporal e a ausência de rótulo remanescente no resultado, mas não mede
rastreamento de movimentos reais nem estabilidade de gestos.

## Procedência da imagem de teste

A foto foi obtida do exemplo oficial do MediaPipe:

- [Notebook oficial Gesture Recognizer](https://github.com/google-ai-edge/mediapipe-samples/blob/main/examples/gesture_recognizer/python/gesture_recognizer.ipynb)
- [Foto thumbs_up usada pelo notebook](https://storage.googleapis.com/mediapipe-tasks/gesture_recognizer/thumbs_up.jpg)

O notebook credita as imagens ao Pixabay. A foto e suas versões anotadas foram
usadas somente em verificação interna e **não estão incluídas no projeto**.
Use a própria gravação de Luigi para a demonstração pública do portfólio.

## O que ainda deve ser testado localmente

1. Instalação e execução em Windows com Python 3.12 de 64 bits.
2. Webcam real: permissão, abertura, janela, fechamento por Q/Esc e liberação.
3. Validade de `Esquerda` e `Direita` com a câmera específica, que pode aplicar
   espelhamento no driver antes de entregar o frame.
4. Duas mãos simultâneas, movimento, oclusão, iluminação e gestos semelhantes.
5. FPS e latência no equipamento de destino, documentando resolução e hardware.
6. Execução do workflow no repositório GitHub. O YAML foi fornecido; nenhuma
   execução de GitHub Actions foi observada durante esta preparação.

Os testes locais de visão não fizeram benchmark de tempo real nem avaliariam
generalização com uma única foto. Registre esses resultados separadamente à
medida que o projeto evoluir.

## Atualização com escrita no ar

A inclusão de `airwrite` foi verificada em 30/10/2026, no mesmo ambiente Python
e com as mesmas dependências. A suíte completa passou a ter **45 testes aprovados**;
Ruff e compilação dos módulos também passaram.

| Verificação adicional | Resultado observado |
| --- | --- |
| Pose em coordenadas sintéticas | Indicador estendido aceito; outras configurações rejeitadas |
| Rotação no plano e escala | Regra manteve a decisão nos casos construídos |
| Traços e filtro | Pausa, pen-up, limpar, desfazer, perda, salto e gap não conectam traços |
| Integração independente | Espelhamento e interrupção com zero/duas mãos conferidos |
| Screenshot fornecido pelo usuário | Uma mão detectada e pose de escrita aceita |
| Foto oficial de joinha | Mão detectada, pose de escrita rejeitada |
| PNG e JSON sintéticos | Dois traços separados, coordenadas e tempos preservados |
| PNG exportado | Fundo branco, só tinta, sem frame de câmera ou interface |

O teste positivo utilizou internamente a imagem de referência do usuário, com
indicador estendido. A mesma imagem foi repetida nos timestamps 0, 40, 80, 120 e
160 ms. O estado ficou em confirmação até 80 ms e em escrita a partir de 120 ms,
coerente com o limiar de entrada de 100 ms. Isso confirma integração e um exemplo
de pose; não mede a qualidade da escrita com movimento real.

Na exportação sintética, um pixel entre dois traços permaneceu branco, confirmando
ausência de linha de ligação. A imagem de referência, a foto de terceiros e as
saídas de teste não acompanham o pacote.

Webcam física, interface no Windows e robustez entre pessoas continuam pendentes
de teste local. Reconhecimento de caracteres ainda não está implementado.
