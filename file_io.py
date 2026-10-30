"""Gravação exclusiva compartilhada pelos modos da aplicação."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from pathlib import Path


def write_new_files(files: Mapping[Path, bytes]) -> None:
    """Cria saídas e tenta desfazer a tentativa se ocorrer uma exceção.

    Arquivos anteriores nunca são sobrescritos. A limpeza não é uma transação
    resistente a queda de energia e pode falhar por permissões do sistema.
    """
    created = []
    try:
        for path, data in files.items():
            with path.open("xb") as output:
                created.append(path)
                output.write(data)
    except BaseException:
        for path in reversed(created):
            try:
                path.unlink(missing_ok=True)
            except OSError as exc:
                print(f"Não foi possível remover a saída incompleta {path}: {exc}",
                      file=sys.stderr)
        raise
