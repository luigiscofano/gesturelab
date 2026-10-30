# Automação e colaboração

[Início](../README.md) · [Documentação](../docs/README.md) · [Como contribuir](../CONTRIBUTING.md)

Esta pasta contém o workflow do GitHub Actions e os modelos usados para abrir
issues e pull requests. Ela não é necessária para executar a webcam localmente.

## Arquivos

| Arquivo | Finalidade |
| --- | --- |
| [workflows/ci.yml](workflows/ci.yml) | Formatação, análise de código, compilação, ajuda das CLIs e testes em Windows/Ubuntu |
| [PULL_REQUEST_TEMPLATE.md](PULL_REQUEST_TEMPLATE.md) | Registrar problema, mudança, evidências e limitações |
| [ISSUE_TEMPLATE/bug_report.yml](ISSUE_TEMPLATE/bug_report.yml) | Informar um erro reproduzível, o ambiente e o resultado esperado |
| [ISSUE_TEMPLATE/feature_request.yml](ISSUE_TEMPLATE/feature_request.yml) | Propor uma melhoria com objetivo e critério de conclusão |
| [ISSUE_TEMPLATE/config.yml](ISSUE_TEMPLATE/config.yml) | Mostrar atalhos para instalação e solução de problemas ao abrir uma issue |

## O que o CI executa

O workflow **Python checks** roda em cada push, em eventos de pull request e
quando iniciado manualmente em **Actions → Python checks → Run workflow**.

Cada execução usa Python 3.12 em dois runners: `ubuntu-latest` e `windows-latest`.
O job instala somente as versões fixas de pytest e Ruff especificadas no YAML e
executa estas etapas:

1. `ruff format --check` confere a formatação de todos os arquivos Python.
2. `ruff check` verifica imports, sintaxe, simplificações e erros comuns definidos em `pyproject.toml`.
3. `compileall` verifica se os módulos, scripts e testes podem ser compilados.
4. `--help` do aplicativo, downloader, diagnóstico e indexador de poses confirma que suas entradas
   funcionam sem importar as dependências de visão.
5. pytest verifica a lógica determinística, incluindo os casos de regressão.

O workflow tem limite de dez minutos por job. Uma nova execução da mesma
referência cancela a anterior ainda em andamento; branches diferentes e os
eventos de push/PR podem ter execuções separadas. Uma falha em um sistema não
interrompe a verificação do outro. A permissão do token é apenas leitura de
conteúdo e os testes não precisam de segredos.

Veja o estado atual em [Actions](https://github.com/luigiscofano/gesturelab/actions).
Uma execução cancelada por um push posterior não equivale a um teste reprovado:
consulte a execução correspondente ao commit mais recente.

## O que um check verde comprova

Comprova que essas verificações passaram no commit e nos runners exibidos. O CI
não instala MediaPipe/OpenCV, não baixa pesos, não abre a webcam e não mede
acurácia, FPS ou qualidade da escrita. Para verificar imports e pesos no seu
computador, siga o [README de scripts](../scripts/README.md).

O workflow também não configura proteção de branch nem exige aprovação de uma
segunda pessoa. Essas políticas são configurações separadas do repositório.
Consulte os resultados e revise o diff antes de integrar uma mudança, conforme
o [guia de contribuição](../CONTRIBUTING.md).

## Templates

Ao criar uma issue, o seletor oferece **Relatar um erro**, **Propor uma melhoria**
e atalhos para os guias de instalação e solução de problemas. Também permite abrir
uma issue em branco quando os modelos disponíveis não se aplicarem. Escolha o
caminho adequado e preencha os campos relevantes. Logs e comandos reproduzíveis ajudam mais que
uma descrição genérica. Não inclua credenciais ou imagens de terceiros.

O template de pull request solicita o motivo da alteração, seu efeito e os
comandos realmente executados. Mantenha explícito quando um teste físico não
foi feito. Use `Closes #numero` apenas quando o PR resolver aquela issue; o
encerramento automático ocorre ao integrar na branch padrão.

## Referências oficiais

- [Sintaxe de workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Templates de issues e pull requests](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests)
- [Vincular uma issue a um pull request](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue)

---

**Próxima leitura:** [fluxo de contribuição](../CONTRIBUTING.md), [testes](../tests/README.md) e [histórico de alterações](../CHANGELOG.md).
