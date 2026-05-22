try:
    from rich.console import Console
    from rich.text import Text
except ImportError:
    Console = None
    Text = None


BANNER = [
    ("         .       (     .      )       .", "bright_red"),
    ("             )    )   (    (     )", "yellow"),
    ("        .   (    (     )    )   (    .", "bright_red"),
    (r"            )\    )\  /\   /(   /(", "yellow"),
    ("           /  \\  /  \\/  \\ /  \\ /  \\", "orange1"),
    ("          (    )(   FOGO NA FORJA   )", "bright_yellow"),
    (r"           \__/  \__/ \__/ \__/ \__/", "red"),
    ("       .=================================.", "bright_black"),
    ("      /  DIARIO DE TREINO FORJA DE FERRO     \\", "bright_white"),
    ("     /_____________________________________\\ ", "bright_black"),
    (r"      \   _   _   _   _   _   _   _   _  /", "white"),
    (r"       \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/ \_/", "bright_black"),
    ("             .-------..___", "bright_white"),
    ("             '-._     :_.-'", "white"),
    ("              .- ) _ ( -.", "bright_black"),
    ("             :  '-' '-'  ;", "white"),
    (r"            /'-.._____.-' \ ", "bright_white"),
    (r"            \__   ACO   __/", "bright_black"),
    ("               '-._____.-'", "white"),
]


def print_plain_banner():
    print()
    for line, _style in BANNER:
        print(line.rstrip())
    print()


def print_rich_banner():
    console = Console(
        force_terminal=True,
        color_system="truecolor",
        legacy_windows=False,
    )
    console.print()
    for line, style in BANNER:
        console.print(Text(line.rstrip(), style=style))
    console.print()


def print_banner():
    if Console is None or Text is None:
        print_plain_banner()
    else:
        print_rich_banner()


if __name__ == "__main__":
    print_banner()
