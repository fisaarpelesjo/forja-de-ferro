"""Operacoes de video para extracao de frames via ffmpeg."""

import math
import os
from pathlib import Path
import platform
import shutil
import subprocess


FORMATOS_SUPORTADOS = {"bmp", "jpeg", "jpg", "png", "webp"}


def _normalizar_formato(formato):
    formato = formato.lstrip(".").strip().lower()
    if formato not in FORMATOS_SUPORTADOS:
        formatos = ", ".join(sorted(FORMATOS_SUPORTADOS))
        raise ValueError(f"Formato de imagem invalido. Use: {formatos}.")
    return formato


def _formatar_numero(valor):
    return str(int(valor) if valor == int(valor) else valor)


def _normalizar_fps(fps):
    if fps is None:
        return None

    fps = float(fps)
    if not math.isfinite(fps) or fps <= 0:
        raise ValueError("FPS deve ser um numero maior que zero.")
    return fps


def _build_ffmpeg_command(video_path, output_dir, fps=None, formato="jpg"):
    video_path = Path(video_path)
    output_dir = Path(output_dir)
    formato = _normalizar_formato(formato)
    fps = _normalizar_fps(fps)
    output_pattern = output_dir / f"{video_path.stem}_frame_%06d.{formato}"

    command = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-nostdin",
        "-y",
        "-i",
        str(video_path),
    ]
    if fps is not None:
        command.extend(["-vf", f"fps={_formatar_numero(float(fps))}"])
    command.extend(["-start_number", "1", str(output_pattern)])
    return command


def ffmpeg_disponivel():
    return shutil.which("ffmpeg") is not None


def _atualizar_path_windows():
    caminhos = [os.environ.get("PATH", "")]
    link_winget = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Links"
    if link_winget.is_dir():
        caminhos.append(str(link_winget))

    try:
        import winreg

        registros = [
            (winreg.HKEY_CURRENT_USER, r"Environment"),
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            ),
        ]
        for raiz, chave in registros:
            with winreg.OpenKey(raiz, chave) as handle:
                valor, _ = winreg.QueryValueEx(handle, "Path")
                caminhos.append(os.path.expandvars(valor))
    except (ImportError, FileNotFoundError, OSError):
        pass

    os.environ["PATH"] = os.pathsep.join(caminho for caminho in caminhos if caminho)


def instalar_ffmpeg():
    if ffmpeg_disponivel():
        return shutil.which("ffmpeg")

    sistema = platform.system()
    if sistema == "Windows":
        if shutil.which("winget") is None:
            raise RuntimeError(
                "winget nao encontrado. Instale o ffmpeg manualmente e tente novamente."
            )
        command = [
            "winget",
            "install",
            "--id",
            "Gyan.FFmpeg",
            "--exact",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ]
    elif sistema == "Darwin":
        if shutil.which("brew") is None:
            raise RuntimeError(
                "Homebrew nao encontrado. Instale o ffmpeg manualmente e tente novamente."
            )
        command = ["brew", "install", "ffmpeg"]
    else:
        if shutil.which("apt-get") is None:
            raise RuntimeError(
                "apt-get nao encontrado. Instale o ffmpeg pelo gerenciador do sistema."
            )
        prefixo = [] if hasattr(os, "geteuid") and os.geteuid() == 0 else ["sudo"]
        command = [*prefixo, "apt-get", "install", "-y", "ffmpeg"]

    try:
        result = subprocess.run(command)
    except OSError as exc:
        raise RuntimeError(f"Nao foi possivel iniciar a instalacao do ffmpeg: {exc}") from exc
    if result.returncode != 0:
        raise RuntimeError("A instalacao do ffmpeg nao foi concluida.")

    if sistema == "Windows":
        _atualizar_path_windows()
    if not ffmpeg_disponivel():
        raise RuntimeError(
            "O ffmpeg foi instalado, mas ainda nao esta no PATH. Reabra o terminal."
        )
    return shutil.which("ffmpeg")


def _limpar_frames_anteriores(output_dir, video_stem):
    removidos = 0
    for formato in FORMATOS_SUPORTADOS:
        for frame in output_dir.glob(f"{video_stem}_frame_*.{formato}"):
            frame.unlink()
            removidos += 1
    return removidos


def contar_frames(output_dir, video_stem, formato="jpg"):
    formato = _normalizar_formato(formato)
    return sum(
        1 for _ in Path(output_dir).glob(f"{video_stem}_frame_*.{formato}")
    )


def extrair_frames(video_path, saida=None, fps=None, formato="jpg"):
    video_path = Path(video_path)
    if not video_path.is_file():
        raise FileNotFoundError(f"Arquivo de video nao encontrado: {video_path}")

    output_dir = Path(saida) if saida else video_path.parent / f"{video_path.stem}_frames"
    command = _build_ffmpeg_command(video_path, output_dir, fps=fps, formato=formato)

    if not ffmpeg_disponivel():
        raise RuntimeError("ffmpeg nao encontrado no PATH.")

    output_dir.mkdir(parents=True, exist_ok=True)
    _limpar_frames_anteriores(output_dir, video_path.stem)

    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except OSError as exc:
        raise RuntimeError(f"Nao foi possivel executar o ffmpeg: {exc}") from exc

    if result.returncode != 0:
        stderr = (result.stderr or "").strip()
        detalhe = f" {stderr}" if stderr else ""
        raise RuntimeError(f"Falha ao extrair frames do video.{detalhe}")

    return output_dir
