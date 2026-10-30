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

Os testes locais de visão não fizeram benchmark de tempo real nem avaliariam
generalização com uma única foto. Registre esses resultados separadamente à
medida que o projeto evoluir.

## Publicação e GitHub Actions

O projeto foi publicado em [luigiscofano/gesturelab](https://github.com/luigiscofano/gesturelab)
em 30/10/2026. A [primeira execução do workflow](https://github.com/luigiscofano/gesturelab/actions/runs/41074869460),
referente ao commit `2157bc78d0e449e192fa418d90cb43ecf38c50cb`, terminou com sucesso.

| Ambiente do CI | Análise de código | Testes determinísticos |
| --- | --- | --- |
| Ubuntu, Python 3.12 | Aprovada | Aprovados |
| Windows, Python 3.12 | Aprovada | Aprovados |

O CI instala pytest e Ruff e verifica a lógica sem webcam. Ele não instala o
conjunto completo de bibliotecas de visão nem valida a janela ou a câmera física.
O badge do README acompanha as execuções seguintes.

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

## Revisão de robustez, diagnóstico e documentação

Em 30/10/2026, uma nova etapa revisou a versão publicada, preservando os três
modos. As mudanças estão descritas no [changelog](../CHANGELOG.md) e nas issues
[#1](https://github.com/luigiscofano/gesturelab/issues/1) a
[#4](https://github.com/luigiscofano/gesturelab/issues/4). A implementação e a
revisão de código desta etapa foram realizadas com assistência de IA; isso não
representa uma aprovação humana independente.

| Verificação da revisão | Resultado observado |
| --- | --- |
| Suíte completa local | **59 testes passaram**, usando o mesmo Python 3.12.14 |
| Ruff e compilação | Nenhum erro reportado |
| Regressões contra o código anterior | Três casos reproduziram sobrescrita ou exportação incompleta |
| Exportação após a correção | Preserva arquivos existentes e tenta remover apenas as saídas criadas pela tentativa que falhou |
| Diagnóstico padrão | Confere Python, arquitetura, versões fixas e distribuições OpenCV |
| Diagnóstico com `--imports --models all` | Imports reais e hashes dos dois modelos aprovados |
| CLI sem bibliotecas de visão | Ajuda acessível; diagnóstico informa pacotes ausentes com código 1 |
| Links dos READMEs e contribuição | 110 links relativos verificados, sem destinos ausentes |
| Workflow e formulários de issue | YAML analisado sem erro de sintaxe |

Na verificação adicional de exportação, OpenCV e NumPy reais produziram um PNG
válido de **120 × 80 pixels** e um JSON com **dois traços de dois pontos**. O
espaço entre os traços permaneceu branco. Os caminhos de teste continham acento.
A leitura e a escrita de foto também preservaram a entrada byte a byte e
produziram uma saída PNG legível. Nesse teste de foto, a inferência e a anotação
foram substituídas para isolar o comportamento de arquivos; não houve avaliação
nova da detecção de mãos. As imagens eram sintéticas e os arquivos temporários.

Os testes automatizados de falha usam codificadores substitutos e arquivos
temporários para reproduzir colisões e erros de escrita. Isso é distinto da
verificação adicional com o codificador real. O rollback trata exceções comuns;
não garante uma exportação completa após queda de energia ou falha da própria
remoção dos arquivos.

O diagnóstico real utilizou a biblioteca nativa temporária descrita no ambiente
acima. O MediaPipe/Matplotlib emitiu um aviso de cache temporário no ambiente
restrito, sem impedir a verificação. Imports, hashes e versões aprovados não
comprovam que a câmera ou a janela funcionam no computador do usuário.

Os resultados remotos da etapa ficam associados aos commits e pull requests em
[GitHub Actions](https://github.com/luigiscofano/gesturelab/actions) e
[Pull requests](https://github.com/luigiscofano/gesturelab/pulls?q=is%3Apr).
O workflow revisto mantém a matriz Windows/Ubuntu e acrescenta compilação e
ajuda das CLIs. Ele continua sem instalar dependências de visão ou testar
hardware; consulte o [README da automação](../.github/README.md).

## Modo posematch e catálogo de referências

Em 30/10/2026 foi acrescentada busca local de imagens por semelhança de pose
corporal. A implementação, a revisão independente entre agentes e as ilustrações
foram preparadas com assistência de IA. Os três modos anteriores foram preservados.

| Verificação | Resultado observado |
| --- | --- |
| Suíte completa local | **124 testes passaram** |
| Ruff e diff-check | Aprovados |
| Núcleo geométrico | 25 testes novos de normalização, proporção, espelhamento, cobertura, ranking e catálogo |
| Runtime corporal | 21 testes de confirmação, ausência/ambiguidade, orientação, tarefa, captura e saída |
| Catálogo/indexador | 12 testes, incluindo proporções extremas e continuação após erro OpenCV |
| CLI | Novos casos para modo separado, opções específicas e distâncias inválidas |
| Modelo corporal | Pose Landmarker Lite versão de artefato 1, SHA-256 conferido pelo downloader |
| Catálogo inicial | 12 referências ilustradas, arquivos existentes e autorrecuperação geométrica coerente |
| Indexador real | Uma pessoa aceita na imagem oficial de teste, landmarks reais e PNG portátil gerados |
| Busca com a imagem oficial | Referência ilustrada de avanço com braços abertos selecionada; composição inspecionada |
| Busca em catálogo de foto indexada | Referência recuperada com distância próxima de zero após redimensionamento |
| Interface | Proporção preservada e créditos legíveis; texto removido das ilustrações para não inverter ao espelhar |

A foto usada internamente veio de
[pose.jpg, exemplo oficial do MediaPipe](https://storage.googleapis.com/mediapipe-assets/pose.jpg).
Ela e as composições correspondentes permaneceram em arquivos temporários e
**não acompanham o repositório**. As referências distribuídas são ilustrações
originais com geometria conhecida. A prévia publicada nos READMEs também utiliza
pontos sintéticos e está identificada explicitamente.

Na execução IMAGE com a foto original, a referência `wide-lunge` foi selecionada
com distância aproximada **0,1085**, usando 12 articulações. Ao pesquisar em um
catálogo gerado da mesma foto, a distância foi aproximadamente **0,0196**: o
indexador havia redimensionado a entrada antes de detectar os pontos. Esses
valores verificam um caso de integração e não constituem acurácia nem avaliação
de generalização. Não houve seleção de limiar com um conjunto de teste amplo.

Uma sequência VIDEO repetiu a foto positiva nos timestamps 0, 90, 180 e 270 ms.
A referência ficou em confirmação até 90 ms e apareceu a partir de 180 ms. Um
frame vazio em 360 ms retornou zero pessoas e limpou a referência. Esse teste
verificou a tarefa temporal e a transição de estado, usando imagens repetidas;
não foi uma captura de webcam nem uma medição de movimento real.

O ambiente usou as mesmas versões e a biblioteca nativa temporária descritas
acima. O TFLite emitiu mensagens sobre delegate CPU, feedback e projeção de ROI,
sem impedir as execuções. Webcam física, desempenho contínuo, generalização
para pessoas novas e qualidade em diferentes ângulos continuam pendentes de
avaliação local.

As verificações do CI continuam limitadas à lógica e às CLIs, sem instalação
das bibliotecas de visão. O teste real de modelo e imagens descrito nesta seção
foi executado localmente no ambiente de preparação.
