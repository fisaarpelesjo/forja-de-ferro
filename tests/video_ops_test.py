import sys
import tempfile
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import gerar_frames
from forja_de_ferro import video_ops


def main():
    original_input_dir = gerar_frames.INPUT_DIR
    original_output_dir = gerar_frames.OUTPUT_DIR
    original_which = video_ops.shutil.which
    original_run = video_ops.subprocess.run
    original_system = video_ops.platform.system

    with tempfile.TemporaryDirectory(prefix="forja-de-ferro-video-") as temp_dir:
        temp_path = Path(temp_dir)
        videos_dir = temp_path / "videos"
        input_dir = videos_dir / "entrada"
        output_dir = videos_dir / "saida"
        input_dir.mkdir(parents=True)
        output_dir.mkdir(parents=True)
        input_video = input_dir / "agachamento.mp4"
        input_video.write_bytes(b"dummy video")
        segundo_video = input_dir / "terra.MOV"
        segundo_video.write_bytes(b"dummy video")

        captured = {}

        try:
            gerar_frames.INPUT_DIR = input_dir
            gerar_frames.OUTPUT_DIR = output_dir
            video_ops.shutil.which = lambda name: r"C:\ffmpeg\bin\ffmpeg.exe"

            def fake_run(command, capture_output, text):
                captured["command"] = command
                output_pattern = Path(command[-1])
                output_pattern.parent.mkdir(parents=True, exist_ok=True)
                for indice in range(1, 4):
                    output_pattern.with_name(
                        output_pattern.name.replace("%06d", f"{indice:06d}")
                    ).write_bytes(b"frame")

                class Result:
                    returncode = 0
                    stderr = ""

                return Result()

            video_ops.subprocess.run = fake_run

            saida = gerar_frames.main(["agachamento.mp4", "--fps", "1", "--formato", ".png"])
            assert saida == 0
            assert captured["command"][0] == "ffmpeg"
            assert "-nostdin" in captured["command"]
            assert "-y" in captured["command"]
            assert "-vf" in captured["command"]
            assert "fps=1" in captured["command"]
            assert captured["command"][-1] == str(
                output_dir / "agachamento" / "agachamento_frame_%06d.png"
            )
            assert video_ops.contar_frames(
                output_dir / "agachamento", "agachamento", ".png"
            ) == 3

            resolved = video_ops.extrair_frames(
                input_video,
                fps=1,
                formato=".png",
                saida=output_dir / "agachamento-direto",
            )
            assert resolved == output_dir / "agachamento-direto"
            assert resolved.exists()
            assert captured["command"][0] == "ffmpeg"
            assert "-vf" in captured["command"]
            assert "fps=1" in captured["command"]
            assert captured["command"][-1] == str(
                output_dir / "agachamento-direto" / "agachamento_frame_%06d.png"
            )
            frame_antigo = (
                output_dir
                / "agachamento-direto"
                / "agachamento_frame_999999.png"
            )
            frame_antigo.write_bytes(b"antigo")
            video_ops.extrair_frames(
                input_video,
                formato=".png",
                saida=output_dir / "agachamento-direto",
            )
            assert not frame_antigo.exists()

            try:
                video_ops.extrair_frames(input_video, fps=0)
                raise AssertionError("FPS zero deveria ser rejeitado.")
            except ValueError as exc:
                assert "maior que zero" in str(exc)

            try:
                video_ops.extrair_frames(input_video, formato="../jpg")
                raise AssertionError("Formato invalido deveria ser rejeitado.")
            except ValueError as exc:
                assert "Formato de imagem invalido" in str(exc)

            output = StringIO()
            with redirect_stdout(output):
                codigo = gerar_frames.main(["inexistente.mp4"])
            assert codigo == 1
            assert "videos/entrada/" in output.getvalue()

            video_ops.shutil.which = lambda name: None
            output = StringIO()
            with redirect_stdout(output):
                codigo = gerar_frames.main(["agachamento.mp4"])
            assert codigo == 1
            assert "--instalar-ffmpeg" in output.getvalue()

            chamadas = []

            def fake_which(name):
                if name == "winget":
                    return r"C:\Windows\winget.exe"
                if name == "ffmpeg" and chamadas:
                    return r"C:\ffmpeg\bin\ffmpeg.exe"
                return None

            def fake_install_run(command):
                chamadas.append(command)

                class Result:
                    returncode = 0

                return Result()

            video_ops.shutil.which = fake_which
            video_ops.subprocess.run = fake_install_run
            video_ops.platform.system = lambda: "Windows"
            video_ops.instalar_ffmpeg()
            assert chamadas[0][:4] == ["winget", "install", "--id", "Gyan.FFmpeg"]

            video_ops.shutil.which = lambda name: r"C:\ffmpeg\bin\ffmpeg.exe"
            video_ops.subprocess.run = fake_run
            output = StringIO()
            with redirect_stdout(output):
                codigo = gerar_frames.main(["--todos", "--fps", "1"])
            assert codigo == 0
            assert "agachamento.mp4: 3 frames" in output.getvalue()
            assert "terra.MOV: 3 frames" in output.getvalue()
            assert "2 video(s), 6 frame(s)" in output.getvalue()
        finally:
            gerar_frames.INPUT_DIR = original_input_dir
            gerar_frames.OUTPUT_DIR = original_output_dir
            video_ops.shutil.which = original_which
            video_ops.subprocess.run = original_run
            video_ops.platform.system = original_system

    print("Teste de video para frames passou.")


if __name__ == "__main__":
    main()
