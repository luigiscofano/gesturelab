# Histórico de alterações

## 30 de outubro de 2026

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
