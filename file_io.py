"""Gravação exclusiva compartilhada pelos modos da aplicação."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path


def write_new_files(files: Mapping[Path, bytes]) -> None:
    """Grava arquivos novos e remove as saídas desta chamada em caso de falha.

    Arquivos anteriores nunca são sobrescritos. A limpeza não é uma transação
    resistente a queda de energia e pode falhar por permissões do sistema.
    """
    created_paths: list[Path] = []
    try:
        for path, contents in files.items():
            # 'x' recusa arquivos existentes; 'b' permite gravar o conteúdo como bytes.
            with path.open("xb") as output:
                # Só entram na limpeza os arquivos que esta chamada conseguiu criar.
                created_paths.append(path)
                output.write(contents)
    except BaseException:
        # A interrupção pelo teclado também deve limpar as saídas parciais.
        for path in reversed(created_paths):
            try:
                path.unlink(missing_ok=True)
            except OSError as exc:
                print(
                    f"Não foi possível remover a saída incompleta {path}: {exc}",
                    file=sys.stderr,
                )
        raise
