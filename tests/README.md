# Testes do GestureLab

[Projeto](../README.md) · [Índice da documentação](../docs/README.md) ·
[Registro de validação](../docs/VALIDACAO.md)

Esta pasta verifica contratos da aplicação: conversão de coordenadas, rejeição de
gestos, estados da caneta, argumentos da linha de comando e proteção das saídas.
Os testes determinísticos usam dados sintéticos e arquivos temporários. Eles não
abrem a webcam, não baixam modelos e não precisam importar OpenCV ou MediaPipe.

## Executar a partir da raiz

Abra o terminal na pasta que contém `app.py` e `pyproject.toml`. O Python de
referência é o **3.12**. Se você já instalou o aplicativo, pode usar sua `.venv`;
os exemplos abaixo criam um ambiente separado apenas para testes.

### Windows — PowerShell

```powershell
py -3.12 -m venv .venv-tests
.\.venv-tests\Scripts\python.exe -m pip install pytest==9.2.0 ruff==0.17.3
.\.venv-tests\Scripts\python.exe -m pytest -q
.\.venv-tests\Scripts\python.exe -m ruff check .
```

### macOS ou Linux

```bash
python3.12 -m venv .venv-tests
.venv-tests/bin/python -m pip install pytest==9.2.0 ruff==0.17.3
.venv-tests/bin/python -m pytest -q
.venv-tests/bin/python -m ruff check .
```

O `pyproject.toml` define a raiz de importação e a pasta de testes. Para manter
consistência, execute com `python -m pytest` usando o executável do ambiente
virtual. Não é necessário ativar esse ambiente nem alterar a política do PowerShell.

## O que cada arquivo verifica

| Arquivo | Comportamentos cobertos |
| --- | --- |
| [test_core.py](test_core.py) | Espelhamento, limites da imagem, coordenadas finitas, classes conhecidas e desconhecidas, limiar de score e timestamps crescentes. |
| [test_cli.py](test_cli.py) | Opções e combinações aceitas, encerramento obrigatório em webcam sem janela, restrições do modo foto e proteção contra sobrescrita durante a exportação. |
| [test_airwriting.py](test_airwriting.py) | Pose geométrica, confirmação, separação de traços, perda de mão, salto, duas mãos, pausa, limpar, desfazer, suavização, metadados e falhas de exportação. |
| [test_environment.py](test_environment.py) | Contratos do diagnóstico de instalação, com dependências e arquivos controlados pelo teste. Consulte também o [README dos scripts](../scripts/README.md). |

Você pode executar um subconjunto durante uma alteração:

```powershell
.\.venv-tests\Scripts\python.exe -m pytest -q tests/test_airwriting.py
.\.venv-tests\Scripts\python.exe -m pytest -q tests/test_cli.py -k export
```

Em macOS/Linux, substitua o executável pelo caminho `.venv-tests/bin/python`.
`-k export` filtra nomes de testes; não é um novo modo do aplicativo.

## Por que existem testes de falha de exportação

O contrato é preservar arquivos que já existiam e, em uma exceção de gravação,
tentar remover os arquivos incompletos criados pela tentativa atual. A suíte
reproduz três situações concretas:

1. Outro processo cria o destino da foto entre a verificação inicial e a escrita.
2. O JSON de um desenho já existe, embora o caminho do PNG esteja livre.
3. A escrita do JSON falha depois de começar, como poderia ocorrer com disco cheio.

Esses casos usam o sistema de arquivos temporário do pytest. As funções de
codificação de imagem são substituídas nesses testes; o conteúdo `png` usado pelo
substituto não é uma imagem real. Eles verificam a preservação e a limpeza de
arquivos, não a qualidade do codificador PNG.

O par PNG + JSON não é uma transação resistente a desligamento abrupto. Se o
sistema interromper o processo ou impedir a remoção, podem restar saídas
incompletas. O aplicativo informa falhas normais; não trate arquivos órfãos como
uma exportação bem-sucedida.

## O que uma aprovação não demonstra

Passar na suíte e no Ruff não mede acurácia de gestos, legibilidade da escrita,
FPS, latência ou funcionamento da câmera e da janela no seu computador. Também
não prova robustez da regra de pose para todas as pessoas, distâncias e posições.

Os testes de visão e as verificações já executadas estão em
[VALIDACAO.md](../docs/VALIDACAO.md). Para uma validação manual, confira os três
modos, feche a janela corretamente, escreva dois traços separados, salve com `S`
e abra os arquivos exportados. Registre ambiente, resultado e limitações em
[EXPERIMENTOS.md](../docs/EXPERIMENTOS.md), sem publicar imagens de terceiros.

## Ao corrigir um problema

Reproduza o comportamento com o menor caso útil, adicione uma asserção sobre o
resultado esperado e confirme que ela detecta o problema. Depois da correção,
execute o grupo afetado e a suíte completa antes de abrir o pull request. Use
`tmp_path` para arquivos e `monkeypatch` para dependências externas; não dependa
da sua câmera ou de arquivos pessoais para um teste automático.

O [workflow do repositório](../.github/workflows/ci.yml) executa as verificações
configuradas no GitHub Actions. Consulte o [README de automação](../.github/README.md)
para entender o que roda em cada job. A contagem de testes pode aumentar com
regressões novas; quantidade não substitui um comportamento bem verificado.
