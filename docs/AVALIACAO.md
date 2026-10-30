# Plano de avaliação

**Estado:** os campos abaixo são um protocolo a preencher. Não são resultados
medidos. A validação técnica do starter está em `VALIDACAO.md`.

## Ambiente

- Commit:
- Sistema e arquitetura:
- CPU e memória:
- Versão Python:
- Versões de dependências:
- Modelo e SHA256:
- Câmera e resolução efetiva:
- Quantidade de mãos:
- Espelhamento e parâmetros:

## Protocolo sugerido

1. Aqueça a execução e documente o intervalo descartado.
2. Meça em cenários fixos por um período definido, por exemplo 60 segundos.
3. Separe tempo de inferência, tempo do loop e atraso de confirmação de gesto.
4. Para classificação, reserve pessoas ou sessões antes de ajustar parâmetros.
5. Inclua desconhecidos e transições na avaliação de uso contínuo.
6. Registre quantidade de apresentações e participantes, além de frames.

| Resultado | Valor | Contexto |
| --- | --- | --- |
| FPS do loop | A medir | Descrever se há exibição gráfica |
| Inferência mediana | A medir | Milissegundos, após aquecimento |
| Inferência p95 | A medir | Milissegundos |
| F1 macro | A medir | Classes e divisão dos dados |
| F1 por classe | A medir | Incluir suporte por classe |
| Falsos eventos por minuto | A medir | Definir tarefa e sequência |
| Rejeição de desconhecidos | A medir | Descrever exemplos e limiar |

O score de uma previsão não mede acurácia. FPS não mede qualidade geométrica dos
landmarks. O modo de foto fornece um tempo de execução único, que não substitui um
benchmark aquecido. A coleta de latência de câmera a tela exige um protocolo
específico; não confunda essa medida com a duração da chamada de inferência.

## Análise de erros

Liste as três confusões mais frequentes e exemplos permitidos. Registre o que
mudaria na coleta, nos atributos ou no modelo. Se repetir ajustes após ver o
teste, reserve novos dados para uma avaliação final independente.

## Referências

- https://scikit-learn.org/stable/common_pitfalls.html
- https://scikit-learn.org/stable/modules/cross_validation.html
