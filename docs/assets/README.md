# Recursos visuais do GestureLab

[Início](../../README.md) · [Documentação](../README.md) · [Arquitetura](../ARQUITETURA.md)

Esta pasta reúne a capa e as ilustrações explicativas usadas nos guias do GestureLab.
São diagramas esquemáticos, não capturas de uma execução da webcam nem evidências
de desempenho. O aplicativo não carrega esses arquivos para funcionar.

## Arquivos

| Tema | Fonte vetorial | Imagem para os guias | Uso atual |
| --- | --- | --- | --- |
| Capa do projeto | [gesturelab-banner.svg](gesturelab-banner.svg) | O próprio SVG, com texto alternativo | [README principal](../../README.md) |
| Índices dos 21 landmarks da mão | [hand_landmarks.svg](hand_landmarks.svg) | [hand_landmarks.png](hand_landmarks.png) | [Guia completo](../GUIA_COMPLETO.md) |
| Fluxo dos três modos iniciais | [pipeline.svg](pipeline.svg) | [pipeline.png](pipeline.png) | [Guia completo](../GUIA_COMPLETO.md), com contexto histórico |
| Interface do PoseMatch | Renderização do aplicativo com pontos sintéticos | [posematch_preview.png](posematch_preview.png) | [Guia do quarto modo](../posematch/README.md) e README geral |

Os SVGs preservam elementos vetoriais e textos para edição. Os PNGs são as versões
usadas pelos diagramas antigos. Mantenha os dois formatos coerentes
ao corrigir um rótulo, índice, conexão ou etapa.

A capa é um SVG original e independente, sem fontes, scripts ou imagens externas.
Suas ilustrações representam as experiências do projeto; não são resultados de
inferência. O próprio SVG é usado no README para preservar a nitidez. O título,
a descrição e o texto alternativo dão contexto a leitores de tela.

O fluxo atual dos **quatro modos** está em Mermaid na
[arquitetura](../ARQUITETURA.md#estado-implementado). Edite esse diagrama junto do
texto quando alterar o fluxo. O desenho dos três modos no guia completo continua
explicando a evolução inicial.

A prévia do PoseMatch não tem um SVG correspondente: é uma composição produzida
pela interface com geometria sintética do catálogo ilustrado. Ela mostra o layout
e está identificada como sintética; não comprova detecção de uma webcam real.

## Atualizar um diagrama

1. Edite o SVG correspondente, preservando a legibilidade e o significado dos
   índices ou das etapas. Não altere a numeração dos landmarks para ajustar o layout.
2. Nos diagramas que têm PNG, exporte também essa versão com o mesmo nome-base.
   A capa usa somente SVG. Se mudar o caminho, atualize os links que o referenciam.
3. Abra os formatos existentes e confira cortes, textos, setas e correspondência visual.
4. Visualize o documento que usa a imagem e verifique se ela continua legível no
   tamanho de leitura. Descreva no commit o conteúdo alterado.

O repositório contém os SVGs e PNGs, mas não inclui um script de geração dessas
figuras. Editá-las não exige alterar as dependências da aplicação.

## Relação com o código

O mapa da mão ajuda a localizar a ponta do indicador, índice 8, e os demais pontos.
As conexões desenhadas pela aplicação estão definidas em [core.py](../../core.py).
A entrada dos modos está em [app.py](../../app.py); a execução das mãos e da escrita fica em [hand_app.py](../../hand_app.py), e o estado da caneta em
[airwriting.py](../../airwriting.py).

Os diagramas de fluxo ajudam a acompanhar a arquitetura. As restrições de cada modo, como a
exigência de uma sequência de frames no modo `airwrite`, estão descritas na
[arquitetura](../ARQUITETURA.md) e no [guia de escrita](../ESCRITA_NO_AR.md).

Voltar ao [índice da documentação](../README.md) ou ao [README do projeto](../../README.md).

