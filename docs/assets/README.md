# Diagramas da documentação

Esta pasta reúne as ilustrações explicativas usadas nos guias do GestureLab.
São diagramas esquemáticos, não capturas de uma execução da webcam nem evidências
de desempenho. O aplicativo não carrega esses arquivos para funcionar.

## Arquivos

| Tema | Fonte vetorial | Imagem para os guias | Uso atual |
| --- | --- | --- | --- |
| Índices dos 21 landmarks da mão | [hand_landmarks.svg](hand_landmarks.svg) | [hand_landmarks.png](hand_landmarks.png) | [Guia completo](../GUIA_COMPLETO.md) |
| Captura, inferência e três modos | [pipeline.svg](pipeline.svg) | [pipeline.png](pipeline.png) | [Arquitetura](../ARQUITETURA.md) e [guia completo](../GUIA_COMPLETO.md) |
| Interface do PoseMatch | Renderização do aplicativo com pontos sintéticos | [posematch_preview.png](posematch_preview.png) | [Guia do quarto modo](../posematch/README.md) e README geral |

Os SVGs preservam elementos vetoriais e textos para edição. Os PNGs são as versões
usadas pelos links de imagem dos documentos. Mantenha os dois formatos coerentes
ao corrigir um rótulo, índice, conexão ou etapa.

A prévia do PoseMatch não tem um SVG correspondente: é uma composição produzida
pela interface com geometria sintética do catálogo ilustrado. Ela mostra o layout
e está identificada como sintética; não comprova detecção de uma webcam real.

## Atualizar um diagrama

1. Edite o SVG correspondente, preservando a legibilidade e o significado dos
   índices ou das etapas. Não altere a numeração dos landmarks para ajustar o layout.
2. Exporte também o PNG correspondente com o mesmo nome-base. Os guias usam os
   nomes desta tabela; se mudar o caminho, atualize os links que o referenciam.
3. Abra os dois arquivos e confira cortes, textos, setas e correspondência visual.
4. Visualize o documento que usa a imagem e verifique se ela continua legível no
   tamanho de leitura. Descreva no commit o conteúdo alterado.

O repositório contém os SVGs e PNGs, mas não inclui um script de geração dessas
figuras. Editá-las não exige alterar as dependências da aplicação.

## Relação com o código

O mapa da mão ajuda a localizar a ponta do indicador, índice 8, e os demais pontos.
As conexões desenhadas pela aplicação estão definidas em [core.py](../../core.py).
A entrada dos modos está em [app.py](../../app.py); a execução das mãos e da escrita fica em [hand_app.py](../../hand_app.py), e o estado da caneta em
[airwriting.py](../../airwriting.py).

O diagrama de fluxo resume a arquitetura. As restrições de cada modo, como a
exigência de uma sequência de frames no modo `airwrite`, estão descritas na
[arquitetura](../ARQUITETURA.md) e no [guia de escrita](../ESCRITA_NO_AR.md).

Voltar ao [índice da documentação](../README.md) ou ao [README do projeto](../../README.md).

