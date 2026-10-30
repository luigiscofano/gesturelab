# Histórico de alterações

## 30 de outubro de 2026

### Clareza do código e responsabilidades

- `app.py` concentra a CLI e a escolha do modo; `hand_app.py` reúne a execução
  das mãos e da escrita, preservando os comandos existentes.
- `vision_runtime.py` centraliza dependências nomeadas, conversão RGB, leitura e
  gravação de imagens e liberação da câmera.
- Geometria dos dedos, continuidade da caneta, comparação de poses, validação
  de catálogos e desenho dos painéis separados em funções com responsabilidades claras.
- Scripts e gerador revisados, com nomes explícitos, unidades e constantes;
  modelos, hashes e imagens do catálogo preservados.
- Formatação Ruff em todo o Python e regras adicionais de imports, sintaxe,
  simplificação e erros comuns verificadas pelo CI em Windows/Ubuntu.
- Oito casos de regressão adicionais para inferência e recursos de câmera;
  suíte local com 132 testes aprovados.
- Comparações com a versão anterior verificaram geometria, estados, renderização,
  saídas dos modelos reais e geração do catálogo. Detalhes em `docs/VALIDACAO.md`.

### Busca de imagens por pose corporal

- Quarto modo independente, `posematch`, com Pose Landmarker corporal e imagem
  de referência exibida ao lado da captura.
- Descritor de 12 articulações, proporção de imagem, normalização por tronco,
  visibilidade, comparação espelhada e distância geométrica explícita.
- Confirmação temporal e limpeza da referência ao perder uma pose utilizável.
- Catálogo inicial de 12 ilustrações originais, fontes SVG/PNG e gerador.
- Indexação de fotografias próprias com modelo real, saída portátil e tratamento
  de imagens recusadas, incluindo proporções extremas e erros do OpenCV.
- Terceiro modelo versionado e conferido por SHA-256; nenhuma dependência direta nova.
- Gravação exclusiva extraída para um módulo comum, preservando os modos anteriores.
- READMEs próprios do modo e do catálogo, comandos de foto e prévia sintética da interface.
- Suíte local ampliada para 124 testes; integração com imagem e sequência VIDEO
  verificada sem webcam física, conforme o registro de validação.

Entregas rastreadas nas issues [#9](https://github.com/luigiscofano/gesturelab/issues/9),
[#10](https://github.com/luigiscofano/gesturelab/issues/10) e
[#11](https://github.com/luigiscofano/gesturelab/issues/11), com branches e PRs próprios.

### Robustez, diagnóstico e colaboração

- Exportação de fotos com criação exclusiva, preservando destinos criados por
  outro processo durante a codificação.
- Limpeza dos arquivos criados pela tentativa quando a exportação PNG + JSON
  falha; arquivos anteriores são preservados. Não é uma transação contra queda
  de energia.
- Diagnóstico de Python, versões, distribuições OpenCV, imports opcionais e
  integridade dos modelos, sem abrir câmera nem baixar pesos implicitamente.
- Suíte ampliada para 59 testes determinísticos e regressões de exportação
  reproduzidas contra a versão anterior.
- READMEs por pasta, índice de documentação, orientação de primeira execução e
  guia de contribuição com templates de issue e pull request.
- CI com compilação, ajuda das CLIs, execução manual e limite de duração dos jobs.

Esta etapa está vinculada às issues [#1](https://github.com/luigiscofano/gesturelab/issues/1),
[#2](https://github.com/luigiscofano/gesturelab/issues/2),
[#3](https://github.com/luigiscofano/gesturelab/issues/3) e
[#4](https://github.com/luigiscofano/gesturelab/issues/4). Os commits e pull requests
registram o trabalho realizado nesta data, com assistência de IA.

### Escrita no ar

- Novo modo `airwrite` com Hand Landmarker e indicador como caneta.
- Regra geométrica de pose, confirmação de entrada e interrupção imediata.
- Traços separados, suavização por tempo e proteção contra saltos de rastreamento.
- Pausar, limpar, desfazer e alternar webcam/fundo branco.
- Exportar somente o desenho em PNG e as trajetórias em JSON.
- Guia de uso e roteiro para reconhecer dígitos, letras e palavras no futuro.
- Suíte ampliada para 45 testes aprovados no ambiente de preparação.

### Base inicial

- Modos `hands` e `gestures`, com modelos MediaPipe Tasks prontos.
- Download versionado de modelos e integridade SHA-256.
- CLI, modo foto, erros de câmera e configuração de CI de lógica.
- Guia de projeto, GitHub, dataset, avaliação e portfólio.

Os registros de execução e os limites de validação estão em `docs/VALIDACAO.md`.
