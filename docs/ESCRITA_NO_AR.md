# Escrita no ar no GestureLab

O modo `airwrite` transforma o movimento da ponta do indicador em traços persistentes.
Ele reutiliza o Hand Landmarker já usado no modo `hands`. A escrita e o reconhecimento
de letras são etapas diferentes: esta versão desenha e exporta os traços; ainda não
converte a escrita em texto.

## Executar

No PowerShell, dentro da pasta do projeto e com as dependências instaladas:

```powershell
.\.venv\Scripts\python.exe scripts\download_models.py --only hands
.\.venv\Scripts\python.exe app.py --mode airwrite
```

Para iniciar com uma folha branca:

```powershell
.\.venv\Scripts\python.exe app.py --mode airwrite --canvas
```

Não há dependências novas para esse modo. Ele precisa de uma sequência de frames;
`--image` não é aceito com `airwrite`.

## Como usar a caneta

Mantenha somente uma mão visível. Estenda o indicador e recolha médio, anelar e
mínimo. O polegar é ignorado pela regra. Mantenha a pose brevemente até aparecer
o estado de escrita e então mova o indicador. A ponta do indicador é o landmark 8.

Para mover a mão sem desenhar, deixe a pose de escrita: por exemplo, abra a mão
ou dobre o indicador. O traço termina, mas o que já foi desenhado permanece.
Volte à pose de escrita para iniciar outro traço. A confirmação de entrada evita
começar um risco durante uma pose muito passageira; a interrupção ocorre assim
que os critérios deixam de ser atendidos.

| Controle | Efeito |
| --- | --- |
| Indicador estendido e outros três dedos recolhidos | Solicita escrita |
| Outra pose, ausência de mão ou duas mãos detectadas | Interrompe o traço |
| Espaço | Pausa ou retoma a ferramenta |
| C | Limpa o desenho |
| Z | Desfaz o último traço |
| B | Alterna vídeo e fundo branco |
| S | Salva o desenho em PNG e os traços em JSON |
| Q ou Esc | Sai |

Os textos na janela usam caracteres sem acentos por compatibilidade com as fontes
do OpenCV. O programa não grava a webcam. Ao pressionar S, o PNG contém somente
o desenho sobre fundo branco, sem a imagem da câmera e sem os textos da interface.

## O que foi acrescentado ao pipeline

O detector fornece posições. O motor `airwriting.py` acrescenta memória e estados:

1. Receber a configuração da mão e o ponto do indicador.
2. Decidir se a caneta pode escrever.
3. Confirmar a entrada na pose por um intervalo curto.
4. Suavizar a coordenada dentro do traço atual.
5. Acrescentar o ponto à lista daquele traço.
6. Encerrar o traço quando a pose, o rastreamento ou o controle exigirem.
7. Desenhar os traços concluídos e o atual a cada frame.

O aplicativo usa os mesmos pixels da visualização para marcador e tinta. A imagem
original segue para o modelo, e o espelhamento é aplicado somente à exibição e
às coordenadas correspondentes. Isso evita que o cursor se desloque para um lado
e o risco apareça no outro.

## Por que manter traços separados

Uma letra pode precisar de vários traços. Para desenhar um H, você pode fazer a
haste esquerda, levantar a caneta, fazer a haste direita, levantar novamente e
desenhar a barra central. Não deve existir linha entre o fim de uma haste e o
início da outra.

**Fim de traço não significa fim de letra.** O futuro reconhecimento precisa de
uma confirmação de caractere ou de uma estratégia de segmentação. Nesta versão,
você desenha livremente e salva o conjunto de traços.

Perda da mão, detecção de outra mão, mudança de lateralidade, intervalo excessivo
sem atualização ou um salto grande na coordenada encerram a continuidade. Esses
critérios reduzem riscos indevidos; não implementam identificação persistente de
pessoas. Uma mão diferente que substitua outra de forma visualmente indistinguível
não pode ser identificada com certeza por essa regra simples.

## Suavização e limites da regra

O filtro combina a posição anterior filtrada com a posição atual. Sua intensidade
considera o tempo entre frames, de modo que a resposta não dependa apenas de uma
quantidade fixa de frames. O filtro é reiniciado em cada novo traço para não puxar
a caneta para a posição anterior ao reposicionamento.

```powershell
.\.venv\Scripts\python.exe app.py --mode airwrite --smooth-ms 45
.\.venv\Scripts\python.exe app.py --mode airwrite --smooth-ms 0
.\.venv\Scripts\python.exe app.py --mode airwrite --pen-width 7
```


O padrão confirma a entrada em 100 ms e interrompe a continuidade após um intervalo maior que 250 ms sem atualização. Se a caneta nunca iniciar em uma máquina lenta, meça o tempo entre frames e reduza a resolução antes de alterar esses limites. Deslocamentos inferiores a 1 pixel não acrescentam pontos; o filtro continua sendo atualizado.

O valor zero desliga a suavização. Mais suavização pode reduzir tremor, mas também
aumentar o atraso e arredondar cantos. Compare o resultado em retas, círculos e
letras com quinas antes de escolher um valor.

O post de referência decide extensão do dedo comparando a altura da ponta com
uma articulação. Essa regra depende da orientação da mão. O kit usa ângulos e
alcance geométrico em coordenadas coerentes, com o polegar ignorado. Ainda é uma
heurística: oclusão e perspectiva podem prejudicá-la. Comece com a mão visível e
aproximadamente de frente para a câmera. Teste o gesto no seu equipamento antes
de ajustar os limiares ou afirmar robustez.

## Arquivos exportados

Cada salvamento recebe um nome novo em `outputs` e inclui:

- PNG do desenho sobre branco.
- JSON com tamanho do quadro, convenção de espelhamento, parâmetro de suavização,
  separação de traços e pontos `x`, `y`, `t_ms`.

As coordenadas são pixels da visualização. O JSON declara `coordinate_space` como
`display_pixels`, identifica `mirrored` e informa se os pontos foram suavizados.
Não são coordenadas métricas do espaço físico. O arquivo ainda não possui rótulo
de letra, participante ou sessão; esses campos entram no futuro coletor de dados.

## Evolução para reconhecer letras e números

### Etapa 1 Desenhar e salvar de forma previsível

Valide traços, interrupção, desfazer, fundo branco e exportação. O objetivo é
conseguir produzir amostras sem linhas de ligação indesejadas.

### Etapa 2 Reconhecer dígitos isolados

Crie uma área para desenhar um único número de 0 a 9 e um botão ou tecla de
confirmar. A confirmação será uma nova funcionalidade; ela não existe ainda.
Somente após confirmar, recorte a região escrita, preserve a proporção, acrescente
margem e redimensione para o tamanho escolhido no treinamento.

Use o desenho limpo como entrada, não o frame que contém seu rosto e o fundo.
Colete exemplos de participantes e sessões diferentes. Registre as apresentações
que falharam por perda de rastreamento, além das imagens classificadas.

Comece com um classificador pequeno, como SVM sobre os pixels normalizados ou
atributos da imagem. O exemplo oficial do scikit-learn demonstra classificação
de dígitos com SVM; seu dataset didático não substitui a coleta de escrita no ar.

### Etapa 3 Letras e palavras

Depois dos números, escolha letras maiúsculas isoladas. Amplie o vocabulário
conforme a matriz de confusão e os testes com novas pessoas. Palavras introduzem
separação de caracteres, múltiplos traços, ordem temporal e ambiguidades.

Há dois caminhos de representação:

| Entrada do reconhecedor | Informação disponível |
| --- | --- |
| Imagem do desenho | Forma final dos traços |
| Sequência de traços com x, y e tempo | Forma, ordem e evolução da escrita |

O segundo caminho é chamado de reconhecimento de tinta digital ou escrita online.
Online, nesse contexto, refere-se à sequência temporal disponível, não à necessidade
de internet. A documentação de Digital Ink do Google apresenta essa distinção;
a API descrita ali é para Android e iOS, não uma dependência pronta deste programa
Python.

EMNIST é uma referência de imagens de caracteres manuscritos. Seu uso pode ajudar
a experimentar modelos, mas uma boa métrica nesse conjunto não comprova desempenho
em desenhos feitos no ar. Avalie exemplos coletados pelo seu próprio aplicativo.

## Critérios de aceite e portfólio

Antes de gravar a demo, verifique:

1. O cursor acompanha o dedo na convenção de espelhamento escolhida.
2. Mover a mão com a caneta levantada não cria marca.
3. Um H com três traços não ganha diagonais entre as hastes.
4. Tirar a mão e voltar em outro ponto não cria uma linha longa.
5. Pausar, limpar e desfazer não conectam o próximo traço ao anterior.
6. O PNG salvo contém só o desenho e o JSON preserva os limites dos traços.

Documente tempo de confirmação, continuidade indevida entre traços, atraso do
cursor e qualidade do desenho com e sem filtro. O novo módulo demonstra lógica
temporal, geometria, interação e persistência de dados, além da integração com
visão computacional. Apresente-o como escrita ou desenho no ar enquanto o
reconhecimento de caracteres não estiver implementado e avaliado.

## Referências

- MediaPipe Hand Landmarker: https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/python
- OpenCV desenho: https://docs.opencv.org/4.x/dc/da5/tutorial_py_drawing_functions.html
- Conceito de Digital Ink: https://developers.google.com/ml-kit/vision/digital-ink-recognition
- EMNIST: https://www.nist.gov/itl/products-and-services/emnist-dataset
- Classificação de dígitos com SVM: https://scikit-learn.org/stable/auto_examples/classification/plot_digits_classification.html
