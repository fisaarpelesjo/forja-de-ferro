"""Launcher local para gerar frames de um video com ffmpeg."""

import argparse
from pathlib import Path

from limulus import video_ops


ROOT_DIR = Path(__file__).resolve().parent
VIDEO_ROOT_DIR = ROOT_DIR / "videos"
INPUT_DIR = VIDEO_ROOT_DIR / "entrada"
OUTPUT_DIR = VIDEO_ROOT_DIR / "saida"
EXTENSOES_DE_VIDEO = {
    ".3gp",
    ".avi",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".webm",
}


def _fps_positivo(valor):
    try:
        fps = float(valor)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("FPS deve ser um numero maior que zero.") from exc
    if fps <= 0:
        raise argparse.ArgumentTypeError("FPS deve ser um numero maior que zero.")
    return fps


def _build_parser():
    parser = argparse.ArgumentParser(
        description="Gera frames de um video usando ffmpeg."
    )
    parser.add_argument(
        "video",
        nargs="?",
        help="Nome do arquivo de video dentro de videos/entrada/ ou caminho completo.",
    )
    parser.add_argument(
        "--todos",
        action="store_true",
        help="Processa todos os videos encontrados em videos/entrada/.",
    )
    parser.add_argument(
        "--instalar-ffmpeg",
        action="store_true",
        help="Instala o ffmpeg se ele nao estiver disponivel.",
    )
    parser.add_argument(
        "--saida",
        help="Diretorio base de saida. Padrao: videos/saida/<nome do video>.",
    )
    parser.add_argument(
        "--fps",
        type=_fps_positivo,
        help="Gera apenas um frame por segundo configurado.",
    )
    parser.add_argument(
        "--formato",
        default="jpg",
        help="Formato das imagens de saida. Padrao: jpg.",
    )
    return parser


def _resolver_video(video):
    candidato = Path(video)
    if candidato.exists():
        return candidato

    input_dir = INPUT_DIR.resolve()
    if not candidato.is_absolute():
        por_nome = input_dir / candidato
        if por_nome.exists():
            return por_nome

    raise FileNotFoundError(
        f"Arquivo de video nao encontrado: {video} (verifique videos/entrada/)"
    )


def _resolver_saida(video_path, saida):
    base_dir = Path(saida) if saida else OUTPUT_DIR
    return base_dir / video_path.stem


def _listar_videos():
    if not INPUT_DIR.is_dir():
        return []
    return sorted(
        caminho
        for caminho in INPUT_DIR.iterdir()
        if caminho.is_file() and caminho.suffix.lower() in EXTENSOES_DE_VIDEO
    )


def _resolver_videos(args):
    if args.todos and args.video:
        raise ValueError("Use um arquivo especifico ou --todos, nao os dois.")
    if args.todos:
        videos = _listar_videos()
        if not videos:
            raise FileNotFoundError(
                f"Nenhum video encontrado em: {INPUT_DIR.resolve()}"
            )
        return videos
    if not args.video:
        raise ValueError("Informe um video ou use --todos.")
    return [_resolver_video(args.video)]


def _garantir_ffmpeg(instalar):
    if video_ops.ffmpeg_disponivel():
        return
    if not instalar:
        raise RuntimeError(
            "ffmpeg nao encontrado. Rode novamente com --instalar-ffmpeg."
        )
    print("ffmpeg nao encontrado. Iniciando instalacao...")
    video_ops.instalar_ffmpeg()
    print("ffmpeg instalado.")


def main(argv=None):
    args = _build_parser().parse_args(argv)

    try:
        videos = _resolver_videos(args)
        _garantir_ffmpeg(args.instalar_ffmpeg)

        total_frames = 0
        for video_path in videos:
            output_dir = _resolver_saida(video_path, args.saida)
            output = video_ops.extrair_frames(
                video_path,
                saida=output_dir,
                fps=args.fps,
                formato=args.formato,
            )
            quantidade = video_ops.contar_frames(
                output,
                video_path.stem,
                formato=args.formato,
            )
            total_frames += quantidade
            print(f"{video_path.name}: {quantidade} frames em {output}")
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"Erro: {exc}")
        return 1

    print(f"Concluido: {len(videos)} video(s), {total_frames} frame(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
