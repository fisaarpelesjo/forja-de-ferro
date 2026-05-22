import sys

from forja_de_ferro import banner
from forja_de_ferro import telegram_poller


def main():
    banner.print_banner()
    print("Iniciando bot de treino...\n")
    telegram_poller.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
