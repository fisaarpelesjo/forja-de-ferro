import sys

from limulus import telegram_poller


def main():
    telegram_poller.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
