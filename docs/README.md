# Documentação do GestureLab

Este índice ajuda a escolher o próximo documento sem confundir o que o aplicativo
já faz com os experimentos e recursos ainda planejados. Para instalar e executar,
comece pelo [README principal](../README.md).

## Guias do aplicativo

| Documento | Quando consultar | Conteúdo |
| --- | --- | --- |
| [README principal](../README.md) | Primeiro uso | Instalação, modos, comandos, atalhos e erros comuns |
| [Guia completo](GUIA_COMPLETO.md) | Estudar e evoluir o projeto | Conceitos de visão computacional, ferramentas, desenvolvimento, GitHub e portfólio |
| [Arquitetura](ARQUITETURA.md) | Entender ou alterar o código | Responsabilidade dos módulos, inferência, espelhamento e estado da escrita |
| [Escrita no ar](ESCRITA_NO_AR.md) | Usar ou modificar a caneta | Pose, confirmação, suavização, traços separados, exportação e limitações |
| [Busca por pose corporal](posematch/README.md) | Encontrar uma imagem de pose parecida | Comparação, interface, catálogo e limites do modo posematch |
| [Recursos visuais](assets/README.md) | Editar os diagramas dos guias | Arquivos SVG e PNG, finalidade e cuidados de atualização |

Os modos `hands`, `gestures`, `airwrite` e `posematch` estão implementados. A escrita produz
desenhos e trajetórias; ela ainda não reconhece letras. O reconhecimento de gestos
usa classes de um modelo pronto. A busca corporal usa distâncias geométricas
entre referências locais, sem classificar universalmente movimentos. Essas distinções devem aparecer também em
demonstrações e descrições do portfólio.

## Evidências e próximas entregas

| Documento | Natureza do conteúdo | Como usar |
| --- | --- | --- |
| [Validação](VALIDACAO.md) | Registro de verificações executadas | Consultar ambiente, resultados e limites dos testes já realizados |
| [Roadmap](ROADMAP.md) | Propostas de evolução | Escolher uma entrega e seu critério de conclusão |
| [Experimentos](EXPERIMENTOS.md) | Modelo de registro a preencher | Documentar hipótese, alteração, comparação e resultado observado |
| [Avaliação](AVALIACAO.md) | Protocolo a executar | Planejar medições e registrar equipamento, cenários e métricas |
| [Dataset](DATASET.md) | Planejamento para uma etapa futura | Definir classes, participantes, sessões e divisão de dados antes do treino |
| [Histórico de alterações](../CHANGELOG.md) | Resumo de mudanças realizadas | Entender a evolução funcional e consultar o histórico do repositório |

Os campos vazios nos planos são trabalho pendente. Eles não representam dados
coletados, acurácia medida ou testes de hardware concluídos. Os registros de
validação devem identificar a versão testada e distinguir teste automatizado,
inferência com imagem e observação em webcam real.

## Leituras por objetivo

### Quero executar pela primeira vez

1. Siga a instalação do [README principal](../README.md) na pasta que contém
   `app.py` e `requirements.txt`.
2. Use o [README dos scripts](../scripts/README.md) para preparar os modelos e
   conferir os utilitários disponíveis.
3. Abra `hands`, encerre com Q ou Esc e experimente `gestures`, `airwrite` e `posematch`.
4. No modo de escrita, mantenha a janela em foco e pressione S antes de sair.
   Não há salvamento automático.

### Quero entender e modificar

1. Leia a [arquitetura](ARQUITETURA.md) e localize o módulo responsável pela mudança.
2. Consulte o [README dos testes](../tests/README.md) e execute a suíte existente.
3. Siga o [guia de contribuição](../CONTRIBUTING.md) para preparar uma branch e um
   pull request. O [README do GitHub](../.github/README.md) explica a automação.
4. Faça uma mudança delimitada, descreva seu efeito e registre a validação pertinente.

### Quero apresentar no portfólio

1. Use o [guia completo](GUIA_COMPLETO.md) como roteiro de apresentação.
2. Execute a versão escolhida no próprio equipamento e registre os resultados em
   [Experimentos](EXPERIMENTOS.md) ou [Avaliação](AVALIACAO.md).
3. Grave uma demonstração com suas próprias imagens e mostre também os limites
   observados, como perda de rastreamento ou atraso do cursor.
4. Explique quais partes você estudou e alterou, o uso de modelos pré-treinados e
   a assistência de IA registrada nos [créditos](../THIRD_PARTY_NOTICES.md).

## Documentação por pasta

- [Scripts](../scripts/README.md): preparação e diagnóstico do ambiente.
- [Modelos](../models/README.md): artefatos, origem e verificação de integridade.
- [Testes](../tests/README.md): execução, cobertura de cenários e limites.
- [GitHub](../.github/README.md): automação e organização do trabalho.
- [Recursos visuais](assets/README.md): diagramas usados nos documentos.
- [Busca por pose](posematch/README.md): uso e arquitetura do quarto modo.
- [Catálogo de poses](../pose_gallery/README.md): imagens de referência e indexação.

## Como manter estes documentos

Atualize o guia afetado junto com o código que muda o comportamento. Exemplos de
comando precisam usar opções realmente aceitas por `app.py --help`. Uma mudança
de atalho, formato de saída ou requisito de instalação deve aparecer também no
README principal.

Ao registrar um teste, inclua o commit, o ambiente, o comando ou procedimento e
o resultado observado. Preserve o contexto dos registros antigos para que uma
verificação do protótipo inicial não seja confundida com a validação de uma versão
posterior. Use links relativos para arquivos do repositório e links permanentes
para evidências externas quando disponíveis.

