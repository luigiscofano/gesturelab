# Mapa do projeto

[Início](../README.md) · [Documentação](README.md) · [Arquitetura](ARQUITETURA.md)

Use este mapa para localizar um arquivo ou descobrir onde um comportamento é
implementado. Os nomes das funções e variáveis estão em inglês; os comentários
e as explicações estão em português.

**Nesta página:** [pastas](#pastas-e-arquivos-principais) · [módulos](#módulos-da-aplicação) ·
[onde alterar](#onde-alterar-cada-comportamento) · [roteiro de leitura](#roteiro-para-ler-o-código) ·
[arquivos locais](#arquivos-criados-no-seu-computador)

## Pastas e arquivos principais

| Caminho | O que guarda | Guia |
| --- | --- | --- |
| Raiz do projeto | Módulos Python e configuração da aplicação | [Módulos abaixo](#módulos-da-aplicação) |
| [docs/](README.md) | Instalação, uso, arquitetura, estudo e registros | [Central de documentação](README.md) |
| [scripts/](../scripts/) | Preparação do ambiente e do catálogo | [Utilitários](../scripts/README.md) |
| [models/](../models/) | Modelos `.task` baixados localmente | [Origem e integridade](../models/README.md) |
| [pose_gallery/](../pose_gallery/) | Catálogo e 12 ilustrações originais, em PNG e SVG | [Referências de poses](../pose_gallery/README.md) |
| [tests/](../tests/) | Testes da lógica e dos casos de falha | [Como testar](../tests/README.md) |
| [.github/](../.github/) | Automação e modelos para contribuições | [GitHub Actions e templates](../.github/AUTOMACAO.md) |
| [docs/assets/](assets/) | Banner, diagramas e prévia da interface | [Recursos visuais](assets/README.md) |

Na raiz, [requirements.txt](../requirements.txt) fixa as dependências de execução;
[requirements-dev.txt](../requirements-dev.txt) acrescenta as de desenvolvimento.
[pyproject.toml](../pyproject.toml) configura pytest e Ruff. O
[changelog](../CHANGELOG.md) registra as mudanças e o
[guia de contribuição](../CONTRIBUTING.md) explica como propor a próxima.

## Módulos da aplicação

### Entrada, câmera e arquivos

| Arquivo | Responsabilidade |
| --- | --- |
| [app.py](../app.py) | Lê os argumentos, rejeita combinações incompatíveis e inicia o modo escolhido |
| [vision_runtime.py](../vision_runtime.py) | Carrega as bibliotecas de visão, lê imagens, converte BGR para RGB e controla os recursos da câmera |
| [file_io.py](../file_io.py) | Cria saídas sem sobrescrever arquivos existentes e limpa arquivos da tentativa quando ocorre uma falha |

### Mãos, gestos e escrita

| Arquivo | Responsabilidade |
| --- | --- |
| [hand_app.py](../hand_app.py) | Executa `hands`, `gestures` e `airwrite`, desenha resultados, recebe teclas e exporta saídas |
| [core.py](../core.py) | Define conexões da mão, converte coordenadas, traduz rótulos e mantém timestamps crescentes |
| [airwriting.py](../airwriting.py) | Decide a pose de escrita e mantém o estado da caneta, a suavização e os traços separados |

### Busca por pose corporal

| Arquivo | Responsabilidade |
| --- | --- |
| [pose_match_app.py](../pose_match_app.py) | Executa o modelo corporal, confirma a referência ao longo dos frames e compõe o painel de comparação |
| [pose_matching.py](../pose_matching.py) | Valida catálogos, normaliza pontos do corpo e calcula o ranking geométrico |
| [pose_gallery/catalog.json](../pose_gallery/catalog.json) | Relaciona as referências iniciais, seus pontos, títulos, imagens e créditos |

Os arquivos permanecem na raiz para que a entrada `python app.py` e os imports
continuem fáceis de acompanhar. Preparação, testes, referências e documentação
têm suas próprias pastas. A [arquitetura](ARQUITETURA.md) explica como esses módulos
colaboram.

## Onde alterar cada comportamento

| Quero trabalhar em... | Começar por | Verificação relacionada |
| --- | --- | --- |
| Uma opção de terminal | [app.py](../app.py) | [test_cli.py](../tests/test_cli.py) |
| Nomes de gestos e coordenadas da mão | [core.py](../core.py) | [test_core.py](../tests/test_core.py) |
| Pose da caneta, suavização ou separação de traços | [airwriting.py](../airwriting.py) | [test_airwriting.py](../tests/test_airwriting.py) |
| Janela, controles ou exportação da escrita | [hand_app.py](../hand_app.py) | [test_airwriting.py](../tests/test_airwriting.py) e teste manual da janela |
| Distância, espelhamento ou rejeição de poses | [pose_matching.py](../pose_matching.py) | [test_pose_matching.py](../tests/test_pose_matching.py) |
| Confirmação e interface do PoseMatch | [pose_match_app.py](../pose_match_app.py) | [test_pose_match_app.py](../tests/test_pose_match_app.py) e teste manual da janela |
| Conversão de imagem e liberação da câmera | [vision_runtime.py](../vision_runtime.py) | [test_vision_runtime.py](../tests/test_vision_runtime.py) |
| Diagnóstico e modelos | [scripts/](../scripts/README.md) | [test_environment.py](../tests/test_environment.py) |
| Indexação de fotos e referências ilustradas | [Catálogo](../pose_gallery/README.md) | [test_pose_catalog.py](../tests/test_pose_catalog.py) |
| Formatação e análise de código | [pyproject.toml](../pyproject.toml) | [Comandos de qualidade](../tests/README.md) |
| Verificações automáticas no GitHub | [ci.yml](../.github/workflows/ci.yml) | [Guia de automação](../.github/AUTOMACAO.md) |
| Um comando ou controle documentado | [USO.md](USO.md) | Conferir `app.py --help` e o comportamento do modo |

Alguns testes verificam somente a lógica com entradas simuladas. A tabela é um
ponto de partida para localizar cenários; não representa cobertura completa da
interface ou da webcam. Veja os limites no [guia dos testes](../tests/README.md).

## Roteiro para ler o código

1. **Entrada:** em [app.py](../app.py), acompanhe `parse_args()` e `main()` para
   entender como o comando seleciona um modo.
2. **Captura:** em [vision_runtime.py](../vision_runtime.py), veja como a câmera
   é aberta, a imagem é preparada e os recursos são liberados.
3. **Um modo de cada vez:** siga [hand_app.py](../hand_app.py) para mãos/escrita
   ou [pose_match_app.py](../pose_match_app.py) para o corpo.
4. **Regra principal:** leia [airwriting.py](../airwriting.py) para a caneta ou
   [pose_matching.py](../pose_matching.py) para a comparação.
5. **Exemplos verificáveis:** abra o teste correspondente e observe a entrada,
   a ação e o resultado esperado. Os comentários explicam o objetivo de cada cenário.

Não é necessário compreender todos os módulos antes de executar. Escolher uma
funcionalidade, experimentar e seguir seu caminho no código torna a leitura mais concreta.

## Arquivos criados no seu computador

| Caminho local | Quando aparece | Entra no Git? |
| --- | --- | --- |
| `.venv/` | Ao criar o ambiente Python | Não |
| `models/*.task` | Ao baixar os modelos | Não |
| `outputs/` | Ao salvar um desenho ou usar esse destino em uma exportação | Não |
| `data/` | Quando você cria uma pasta para fotos ou catálogos próprios | Não |
| `__pycache__/` e caches de teste | Durante a execução e as verificações | Não |

Essas exclusões estão em [.gitignore](../.gitignore). Os pesos baixados são
diferentes do [README de modelos](../models/README.md), que faz parte do repositório.
Uma pasta de saída personalizada fora desses caminhos precisa ser revisada antes
de um commit, principalmente se contiver fotos.

**Próxima leitura:** [Arquitetura](ARQUITETURA.md) ·
[Guia completo](GUIA_COMPLETO.md) · [Como contribuir](../CONTRIBUTING.md)
