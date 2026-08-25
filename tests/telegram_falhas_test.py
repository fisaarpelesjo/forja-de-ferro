import sys
from pathlib import Path

import requests


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from limulus import telegram_poller


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {"result": []}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError()

    def json(self):
        return self._payload


def main():
    original_get = telegram_poller.requests.get
    original_post = telegram_poller.requests.post
    original_sleep = telegram_poller.time.sleep
    sleeps = []

    try:
        telegram_poller.requests.get = lambda *args, **kwargs: FakeResponse(401)
        try:
            telegram_poller.get_updates()
            raise AssertionError("Token invalido deveria encerrar o polling.")
        except telegram_poller.TelegramConfigurationError:
            pass

        def failing_get(*args, **kwargs):
            raise requests.ConnectionError()

        telegram_poller.requests.get = failing_get
        try:
            telegram_poller.get_updates()
            raise AssertionError("Falha de rede deveria ser temporaria.")
        except telegram_poller.TelegramTemporaryError as exc:
            assert str(exc) == "ConnectionError"

        attempts = {"count": 0}

        def unstable_post(*args, **kwargs):
            attempts["count"] += 1
            if attempts["count"] < 3:
                raise requests.Timeout()
            return FakeResponse()

        telegram_poller.requests.post = unstable_post
        telegram_poller.time.sleep = sleeps.append
        assert telegram_poller.send("teste") is True
        assert attempts["count"] == 3
        assert sleeps == [1, 2]

        assert telegram_poller._command_name("/status") == "/status"
        assert telegram_poller._command_name("/peso 118,5") == "/peso"
        assert telegram_poller._command_name("/cintura 110,5") == "/cintura"
        assert telegram_poller._command_name("80 9") == "registro_carga"
        assert "80" not in telegram_poller._command_name("80 9")
        assert telegram_poller._is_session_input("/status") is True
        assert telegram_poller._is_session_input("/desfazer") is True
        assert telegram_poller._is_session_input("80 9") is True
        assert telegram_poller._is_session_input("80,5") is True
        assert telegram_poller._is_session_input("status") is False
        assert telegram_poller._is_session_input("ajuda") is False
        assert telegram_poller._is_session_input("/help") is False
        assert telegram_poller._is_session_input("/generate") is False

        print("Teste de falhas do Telegram passou.")
    finally:
        telegram_poller.requests.get = original_get
        telegram_poller.requests.post = original_post
        telegram_poller.time.sleep = original_sleep


if __name__ == "__main__":
    main()
