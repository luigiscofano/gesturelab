# Central de documentação

[Início do projeto](../README.md) · [Instalação](INSTALACAO.md) ·
[Como usar](USO.md) · [Solução de problemas](SOLUCAO_DE_PROBLEMAS.md)

**Escolha o que você quer fazer.** Os guias práticos ajudam a executar o GestureLab;
os documentos técnicos explicam suas decisões; os registros mostram as evidências
e as próximas entregas.

## Comece pelo seu objetivo

| Quero... | Abra esta página |
| --- | --- |
| **Rodar pela primeira vez** | [Instalação do zero](INSTALACAO.md): programas, Git ou ZIP, ambiente e primeira janela |
| **Experimentar os quatro modos** | [Como usar](USO.md): comandos, controles, fotos e saídas |
| **Resolver algo que deu errado** | [Solução de problemas](SOLUCAO_DE_PROBLEMAS.md): sintomas e verificações |
| **Encontrar uma parte do código** | [Mapa do projeto](MAPA_DO_PROJETO.md): pastas, módulos e onde alterar cada comportamento |
| **Entender as decisões técnicas** | [Arquitetura](ARQUITETURA.md): captura, inferência, estado e separação dos módulos |
| **Aprender e apresentar o projeto** | [Guia completo](GUIA_COMPLETO.md): conceitos, desenvolvimento, GitHub e portfólio |

## Explore uma funcionalidade

| Funcionalidade | Usar agora | Entender ou personalizar |
| --- | --- | --- |
| Mãos | [Pontos e conexões](USO.md#mãos--hands) | [Índices dos pontos](assets/hand_landmarks.png) · [Arquitetura](ARQUITETURA.md) |
| Gestos | [Classes e limiar](USO.md#gestos--gestures) | [Reconhecimento e regras](GUIA_COMPLETO.md#6-identificar-e-nomear-gestos) |
| Escrita no ar | [Caneta e atalhos](USO.md#escrita-no-ar--airwrite) | [Traços, suavização e exportação](ESCRITA_NO_AR.md) |
| PoseMatch | [Buscar uma referência](USO.md#poses-parecidas--posematch) | [Como as poses são comparadas](posematch/README.md) · [Catálogo e fotos próprias](../pose_gallery/README.md) |

Precisa de um parâmetro? A [referência de opções](USO.md#referência-de-opções)
reúne todos os argumentos de `app.py`, com padrões e restrições.

## Encontre cada pasta

| Área | O que você encontra | Onde começar |
| --- | --- | --- |
| Aplicação | CLI, inferência, regras e interface | [Mapa dos módulos](MAPA_DO_PROJETO.md) |
| `scripts/` | Download, diagnóstico e indexação de fotos | [Guia dos utilitários](../scripts/README.md) |
| `models/` | Origem, nomes e integridade dos modelos | [Guia dos modelos](../models/README.md) |
| `pose_gallery/` | Catálogo inicial e geração das ilustrações | [Guia do catálogo](../pose_gallery/README.md) |
| `tests/` | Cenários automatizados e comandos de teste | [Guia dos testes](../tests/README.md) |
| `.github/` | GitHub Actions, issues e pull requests | [Automação e colaboração](../.github/AUTOMACAO.md) |
| `docs/assets/` | Identidade visual, diagramas e prévia | [Guia dos recursos visuais](assets/README.md) |

## Qualidade, evidências e evolução

| Documento | O que ele representa |
| --- | --- |
| [Validação](VALIDACAO.md) | Verificações já realizadas, ambiente, resultados e limites |
| [Testes](../tests/README.md) | Como executar a suíte e entender o que ela verifica |
| [Histórico de alterações](../CHANGELOG.md) | Mudanças que já entraram no projeto |
| [Roadmap](ROADMAP.md) | Entregas planejadas e critérios de conclusão |
| [Experimentos](EXPERIMENTOS.md) | Modelo para registrar uma hipótese e o resultado observado |
| [Avaliação](AVALIACAO.md) | Protocolo para medir o comportamento no seu equipamento |
| [Dataset](DATASET.md) | Planejamento de dados para o futuro classificador próprio |

Os campos ainda não preenchidos em experimentos, avaliação e dataset são
**planos de trabalho**. Os resultados já obtidos ficam em **Validação**, com o
contexto necessário para interpretá-los.

## Três caminhos de leitura

### Quero apenas executar

1. [Prepare o ambiente](INSTALACAO.md).
2. [Escolha um modo](USO.md#escolha-um-modo).
3. Consulte a [solução de problemas](SOLUCAO_DE_PROBLEMAS.md) se precisar.

### Quero estudar ou modificar

1. [Localize os módulos](MAPA_DO_PROJETO.md).
2. [Entenda o fluxo](ARQUITETURA.md) e aprofunde a funcionalidade desejada.
3. [Execute os testes](../tests/README.md) e siga o [fluxo de contribuição](../CONTRIBUTING.md).

### Quero apresentar no portfólio

1. Leia o [roteiro de apresentação](GUIA_COMPLETO.md#16-transformar-em-uma-peça-de-portfólio).
2. Execute no seu equipamento e registre um [experimento](EXPERIMENTOS.md).
3. Mostre uma demonstração própria, as decisões que entendeu e os limites observados.
4. Inclua os [créditos e a procedência dos componentes](../THIRD_PARTY_NOTICES.md).

## Ajuda e manutenção

Para relatar um erro ou sugerir uma melhoria, use os
[formulários de issues](https://github.com/luigiscofano/gesturelab/issues/new/choose).
Para alterar código ou documentação, consulte [Como contribuir](../CONTRIBUTING.md).

Mantenha a documentação junto da mudança: instalação em `INSTALACAO.md`, comandos
e controles em `USO.md`, explicações de implementação nos guias técnicos. Atualize
este índice quando criar uma página e verifique seus links no GitHub. O README
principal deve continuar sendo uma entrada curta para esses caminhos.

[Voltar ao projeto](../README.md) · [Mapa do projeto](MAPA_DO_PROJETO.md) ·
[Licença](../LICENSE) · [Créditos](../THIRD_PARTY_NOTICES.md)

