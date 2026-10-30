# Planejamento do dataset

**Estado:** a coleta e o classificador próprio ainda não estão implementados.
Este documento orienta a próxima etapa; não descreve um dataset existente.

## Definição da tarefa

- Gestos que serão reconhecidos:
- O que caracteriza cada classe:
- Gestos de transição e outros:
- Uma ou duas mãos por exemplo:
- Distância e orientação de câmera previstas:
- Público e condições de uso:

## Esquema mínimo

Cada observação deve possuir `participant_id`, `session_id`, `presentation_id`,
`label`, `timestamp_ms`, `hand_detected`, `handedness`, `width`, `height` e 63 valores de landmarks.
Documente se usa coordenadas da imagem ou world landmarks. Não misture essas
representações sem uma transformação explícita.

Se a mão visível não for detectada, mantenha o registro da apresentação com
`hand_detected=false` e landmarks ausentes. Conte essas falhas na avaliação do
sistema completo; o classificador pode ser avaliado separadamente nos exemplos válidos.

Uma apresentação é uma repetição independente da pose. Frames próximos da mesma
apresentação permanecem no mesmo conjunto. Guarde identificadores codificados, sem
nomes ou contatos no CSV público.

## Protocolo a preencher

| Item | Planejado | Efetivamente coletado |
| --- | --- | --- |
| Participantes | A definir | Não coletado |
| Sessões por pessoa | A definir | Não coletado |
| Classes | A definir | Não coletado |
| Apresentações por classe | A definir | Não coletado |
| Frames por apresentação | A definir | Não coletado |
| Exemplos de desconhecidos | A definir | Não coletado |

## Divisão dos dados

Para medir generalização para novas pessoas, use `participant_id` como grupo.
Para medir novas sessões da mesma pessoa, use identificadores de sessão e declare
essa limitação. Se houver múltiplos participantes, uma chave composta pode ser
necessária para identificar sessões de modo único.

Registre os grupos destinados a treino, validação e teste antes de treinar.
Considere validação cruzada por grupos quando a quantidade permitir. Estatísticas
aprendidas de normalização devem usar apenas o treino. Não distribua frames
vizinhos aleatoriamente entre os conjuntos.

Mantenha o teste final fora da validação cruzada de desenvolvimento e da seleção
de atributos, modelos e limiares. Informe se a avaliação é por frame, apresentação
ou evento. Uma gravação longa não equivale a mais apresentações independentes.

## Permissão de uso e limitações

Registre o que foi combinado com participantes sobre uso dos dados e publicação
de demonstrações. O `.gitignore` exclui `data/` por padrão. Para publicar amostras,
revise o conteúdo, a finalidade e a permissão antes de mudar essa regra.

Documente iluminação, distância, orientações e perfis que faltaram à coleta.
Muitas linhas no CSV não garantem diversidade de pessoas ou situações.

## Referência

https://scikit-learn.org/stable/modules/cross_validation.html
