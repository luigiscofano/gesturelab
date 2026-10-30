# Como contribuir com o GestureLab

[README principal](README.md) · [Testes](tests/README.md) ·
[Automação do GitHub](.github/README.md) · [Roadmap](docs/ROADMAP.md)

O objetivo é manter os modos `hands`, `gestures` e `airwrite` utilizáveis enquanto
o projeto evolui. Uma boa contribuição tem um problema concreto, uma mudança
compreensível e evidências proporcionais ao que alterou.

## Preparar o ambiente

Siga a instalação no [README](README.md). Execute os comandos na pasta que contém
`app.py` e use o mesmo Python do ambiente virtual.

Para desenvolver no Windows, depois de criar `.venv`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check .
```

No macOS/Linux, substitua o executável por `.venv/bin/python`. Para trabalhar
somente na lógica e na documentação sem instalar as bibliotecas de visão, siga
a instalação mínima no [README dos testes](tests/README.md).

## Fluxo de uma mudança

1. Consulte as [issues](https://github.com/luigiscofano/gesturelab/issues) e o
   roadmap. Para uma mudança maior, registre o problema e o critério de conclusão.
2. Atualize a `main` local e crie uma branch com um nome que descreva o trabalho.
3. Implemente a mudança, atualize a documentação afetada e teste o comportamento.
4. Faça commits que agrupem mudanças coerentes. Explique a intenção na mensagem.
5. Envie a branch e abra um pull request para `main`, descrevendo o motivo,
   o resultado e a validação efetivamente executada.
6. Confira o diff e o resultado do CI. Integre quando o escopo estiver resolvido.
   Se a `main` mudou durante o trabalho, verifique o resultado combinado.

Exemplo para quem já tem permissão de escrita neste repositório:

```bash
git switch main
git pull --ff-only origin main
git switch -c fix/descricao-curta
# Edite e valide os arquivos antes de continuar.
git status
git diff
# Substitua os caminhos abaixo pelos arquivos realmente alterados.
git add caminho/do/arquivo.py tests/test_arquivo.py
git commit -m "fix: descreve o comportamento corrigido"
git push -u origin fix/descricao-curta
```

No GitHub, use **Compare & pull request**. Se você não tiver permissão de escrita,
faça um fork, trabalhe nele e proponha o PR para `luigiscofano/gesturelab:main`.

Depois de um merge, com o diretório de trabalho sem alterações pendentes:

```bash
git switch main
git pull --ff-only origin main
```

`push` envia commits ao remoto. `pull` busca e integra mudanças no clone local.
Um **pull request** é a proposta registrada no GitHub para integrar branches;
é uma operação diferente de `git pull`.

## Branches, commits e revisão

Use nomes como `fix/exportacao`, `feat/diagnostico`, `docs/instalacao` e
`chore/ci`. São exemplos de convenção, não branches que você precisa criar.
Uma branch por entrega costuma ser suficiente; não é necessário um `develop`
permanente para este projeto.

Os commits existentes devem preservar as datas e a autoria reais. Registre
problemas encontrados, correções e melhorias efetivas. A quantidade de commits
ou branches não mede qualidade nem tempo de desenvolvimento.

Branches já integradas podem ser mantidas para consulta ao histórico. A `main`
continua sendo a entrada para usar a versão integrada. Para esta etapa do
projeto, usamos merge commits para conservar os commits de cada entrega e o
vínculo com seu PR. Não faça force-push na `main` compartilhada.

Uma revisão pode ser feita pelo próprio autor ou com assistência de IA. Informe
qual foi realizada; não atribua aprovação humana a uma verificação automática.
Os checks do GitHub Actions não substituem a leitura do código nem os testes
com hardware quando a mudança depende da câmera.

## Validação por tipo de alteração

| Alteração | Evidência útil |
| --- | --- |
| Regra geométrica, estados ou exportação | Caso reproduzível e teste de regressão da mudança de comportamento |
| CLI ou instalação | `--help`, exemplos executáveis e mensagens para os erros relevantes |
| Webcam, desenho ou interação | Teste local e registro do sistema, câmera e condições observadas |
| Modelo ou limiar | Procedência, dados de avaliação e métricas com limitações explícitas |
| Documentação | Links válidos, caminhos existentes e comandos compatíveis com o código |

Não acrescente um teste que apenas repita a implementação. Verifique o contrato
que importa para quem usa o aplicativo. Não remova um teste para ocultar uma
regressão. Para uma edição simples de texto, revisão de links e conteúdo basta.

Registre novas verificações em [VALIDACAO.md](docs/VALIDACAO.md) quando trouxerem
evidências relevantes. Um teste sintético ou uma foto repetida não demonstram
desempenho em webcam real. Preserve essa distinção ao descrever resultados.

## Documentação e créditos

Atualize o README geral se a forma de instalar ou usar mudar. Mantenha instruções
específicas nos READMEs de [scripts](scripts/README.md), [modelos](models/README.md),
[testes](tests/README.md) e [automação](.github/README.md). Evite replicar o mesmo
texto em todos os arquivos.

O projeto utiliza modelos prontos e teve sua implementação inicial preparada
com assistência de IA. Preserve essa informação e registre sua contribuição
com precisão: o que estudou, modificou, testou ou mediu. Consulte
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) antes de incorporar referências
externas. Código, bibliotecas e pesos podem ter licenças diferentes.

Modelos baixados, `outputs/`, datasets e vídeos ficam fora do versionamento por
padrão. Revise `git diff --cached` antes de enviar um commit. Para uma demo de
portfólio, prefira a própria gravação e documente as condições do teste.
