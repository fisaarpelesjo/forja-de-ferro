import importlib
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


REQUIRED_MODULES = [
    "requests",
    "limulus.db_ops",
    "limulus.ods_ops",
    "limulus.video_ops",
    "limulus.dashboard",
    "limulus.telegram_poller",
    "gerar_frames",
    "start_bot",
]


def main():
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10+ is required.")

    for module_name in REQUIRED_MODULES:
        importlib.import_module(module_name)

    db_path = ROOT_DIR / "data" / "limulus.db"
    if not db_path.exists():
        raise FileNotFoundError(f"Missing database: {db_path}")

    print("Teste de fumaca passou.")


if __name__ == "__main__":
    main()
