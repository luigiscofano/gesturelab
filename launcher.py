"""Tela inicial local: abre os quatro modos sem voltar ao terminal."""

from __future__ import annotations

import sys
from types import ModuleType
from typing import TYPE_CHECKING

from app import parse_args, run_mode

if TYPE_CHECKING:
    import tkinter as tk

# A janela não carrega modelos nem aciona a webcam até a escolha de um modo.
MODES = (
    ("hands", "Mãos", "Veja os pontos e as articulações dos dedos."),
    ("gestures", "Gestos", "Experimente um joinha, mão aberta ou punho fechado."),
    ("airwrite", "Escrita no ar", "Desenhe com o indicador. Pressione S para salvar."),
    ("posematch", "Poses parecidas", "Compare a sua pose com as imagens do catálogo."),
)
BACKGROUND = "#101418"
SURFACE = "#1b2329"
TEXT = "#e1ebe4"
MUTED = "#aabbb2"
ACCENT = "#98e6b2"
WARNING = "#ffc69d"
FONT = "TkFixedFont"


class Launcher:
    """Janela de seleção; as janelas de captura continuam pertencendo ao OpenCV."""

    def __init__(self, tk: ModuleType, root: tk.Tk) -> None:
        from tkinter import font

        self.heading_font = font.nametofont(FONT, root=root).copy()
        self.heading_font.configure(size=20, weight="bold")
        self.root = root
        self.status = tk.StringVar(root, "Escolha um modo para abrir a câmera.")
        self.camera = tk.StringVar(root, "0")
        self.running = False

        root.title("GestureLab")
        root.configure(bg=BACKGROUND)
        root.resizable(False, False)

        content = tk.Frame(root, bg=BACKGROUND, padx=22, pady=18)
        content.pack()
        tk.Label(
            content,
            text="> GestureLab",
            bg=BACKGROUND,
            fg=ACCENT,
            font=self.heading_font,
            anchor="w",
        ).pack(fill="x")
        tk.Label(
            content,
            text="Visão computacional · Demonstrações com webcam",
            bg=BACKGROUND,
            fg=MUTED,
            font=FONT,
            anchor="w",
        ).pack(fill="x", pady=(3, 13))

        self.buttons = {}
        for index, (mode, title, description) in enumerate(MODES, 1):
            button = tk.Button(
                content,
                text=f"[{index}] {title}",
                command=lambda mode=mode: self.open_mode(mode),
                font=FONT,
                bg=SURFACE,
                fg=TEXT,
                activebackground=ACCENT,
                activeforeground=BACKGROUND,
                highlightbackground=BACKGROUND,
                highlightcolor=ACCENT,
                highlightthickness=2,
                relief="flat",
                anchor="w",
                padx=8,
                pady=4,
            )
            button.pack(fill="x")
            button.bind("<Return>", lambda _event, button=button: button.invoke())
            self.buttons[mode] = button
            root.bind(str(index), lambda event, mode=mode: self.open_shortcut(event, mode))
            tk.Label(
                content,
                text=description,
                bg=BACKGROUND,
                fg=MUTED,
                font=FONT,
                anchor="w",
            ).pack(fill="x", padx=10, pady=(1, 7))

        settings = tk.Frame(content, bg=BACKGROUND)
        settings.pack(fill="x", pady=(5, 6))
        tk.Label(
            settings,
            text="Câmera:",
            bg=BACKGROUND,
            fg=TEXT,
            font=FONT,
        ).pack(side="left")
        self.camera_field = tk.Entry(
            settings,
            textvariable=self.camera,
            width=4,
            font=FONT,
            bg=SURFACE,
            fg=TEXT,
            insertbackground=TEXT,
            highlightcolor=ACCENT,
        )
        self.camera_field.pack(side="left", padx=(5, 8))
        tk.Label(
            settings,
            text="0 é a padrão. Tente 1 se necessário.",
            bg=BACKGROUND,
            fg=MUTED,
            font=FONT,
        ).pack(side="left")

        tk.Label(
            content,
            text="Nos modos: Q ou Esc volta ao menu.",
            bg=BACKGROUND,
            fg=MUTED,
            font=FONT,
            anchor="w",
        ).pack(fill="x")
        self.status_label = tk.Label(
            content,
            textvariable=self.status,
            bg=BACKGROUND,
            fg=ACCENT,
            font=FONT,
            anchor="w",
            justify="left",
            wraplength=410,
        )
        self.status_label.pack(fill="x", pady=(9, 0))
        self.buttons["hands"].focus_set()

    def open_shortcut(self, event: tk.Event, mode: str) -> None:
        """Números no campo da câmera são dados, não atalhos."""
        if event.widget is not self.camera_field:
            self.open_mode(mode)

    def show_status(self, message: str, *, error: bool = False) -> None:
        self.status.set(message)
        self.status_label.configure(fg=WARNING if error else ACCENT)

    def open_mode(self, mode: str) -> None:
        if self.running:
            return
        try:
            camera = int(self.camera.get())
            if camera < 0:
                raise ValueError
        except ValueError:
            self.show_status("Use um número inteiro não negativo para a câmera.", error=True)
            self.camera_field.focus_set()
            return

        self.running = True
        self.root.withdraw()
        self.root.update_idletasks()
        try:
            run_mode(parse_args(["--mode", mode, "--camera", str(camera)]))
            self.show_status("Câmera fechada. Escolha outro modo ou feche a janela.")
        except (RuntimeError, OSError, ValueError) as exc:
            self.show_status(str(exc), error=True)
        finally:
            # Reexibe o menu só depois de o modo devolver a câmera ao sistema.
            self.running = False
            self.root.deiconify()
            self.buttons[mode].focus_set()


def main() -> int:
    """Abre o menu; a CLI permanece disponível sem Tk."""
    try:
        import tkinter as tk
    except ImportError:
        print(
            "Menu indisponível: instale o Tcl/Tk do Python ou use app.py --mode.", file=sys.stderr
        )
        return 1
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f"Não foi possível abrir a janela: {exc}", file=sys.stderr)
        return 1
    Launcher(tk, root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
