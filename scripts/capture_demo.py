#!/usr/bin/env python3
"""Capture a model-free Fuserio walkthrough and encode it with FFmpeg."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from localchat import app as app_module


ASSETS = ROOT / "assets"
FPS = 15
CLIP_SECONDS = 1.8
FADE_SECONDS = 0.4


class QuietSignal:
    def connect(self, _callback):
        pass


class QuietServerProbe:
    def __init__(self, _base_url):
        self.found = QuietSignal()
        self.failed = QuietSignal()

    def start(self):
        pass

    def cancel(self):
        pass

    def isRunning(self):
        return False


def capture_frames(frame_directory: Path) -> list[Path]:
    app_module.ExistingServerProbe = QuietServerProbe
    app_module.load_progress = lambda: {"selection": {}, "sessions": {}}
    app_module.save_progress = lambda _progress: None

    application = QApplication.instance() or QApplication([])
    window = app_module.MainWindow()
    window.resize(1440, 900)
    window.model_info.setText("DEMO MODE · NO MODEL REQUIRED")
    window.connection_status.setText("PREVIEW")
    window.statusBar().showMessage("Sample preview · no model required")
    window.show()
    application.processEvents()

    frames: list[Path] = []

    def capture(name: str) -> None:
        application.processEvents()
        frame_path = frame_directory / f"{name}.png"
        if not window.grab().save(str(frame_path), "PNG"):
            raise RuntimeError(f"Could not capture {frame_path}")
        frames.append(frame_path)

    capture("01-level")
    window.select_gce_level("Ordinary Level")
    capture("02-stream")
    window.select_gce_stream("Sciences")
    capture("03-subject")
    window.open_gce_subject("Physics")
    window.messages = [
        {
            "role": "user",
            "content": "A taxi travels 120 km in 2 hours. Find its average speed.",
        },
        {
            "role": "assistant",
            "reasoning": "Identify distance and time, then apply average speed = distance / time.",
            "content": (
                "**Given:** distance $d = 120\\,\\text{km}$ and time $t = 2\\,\\text{h}$.\n\n"
                "Use the formula $v = \\frac{d}{t}$.\n\n"
                "$$v = \\frac{120}{2} = 60\\,\\text{km/h}$$\n\n"
                "**Answer:** The average speed is **60 km/h**."
            ),
        },
    ]
    window.mode_bar.show()
    window._render_messages()
    capture("04-tutor-chat")
    window.close()
    application.processEvents()
    return frames


def encode_video(frames: list[Path], video_path: Path) -> None:
    inputs: list[str] = []
    for frame_path in frames:
        inputs.extend(
            [
                "-loop", "1", "-framerate", str(FPS),
                "-t", str(CLIP_SECONDS), "-i", str(frame_path),
            ]
        )

    filters = []
    for index in range(len(frames)):
        filters.append(
            f"[{index}:v]scale=1280:-2:flags=lanczos,setsar=1,"
            f"fps={FPS},format=yuv420p[v{index}]"
        )

    current = "v0"
    current_duration = CLIP_SECONDS
    for index in range(1, len(frames)):
        output_label = f"mix{index}"
        offset = current_duration - FADE_SECONDS
        filters.append(
            f"[{current}][v{index}]xfade=transition=fade:duration={FADE_SECONDS}:"
            f"offset={offset:.3f}[{output_label}]"
        )
        current = output_label
        current_duration += CLIP_SECONDS - FADE_SECONDS
    filters.append(f"[{current}]format=yuv420p[out]")

    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        *inputs,
        "-filter_complex", ";".join(filters),
        "-map", "[out]", "-an", "-r", str(FPS),
        "-c:v", "libx264", "-crf", "21", "-preset", "medium",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video_path),
    ]
    subprocess.run(command, check=True)


def encode_gif(video_path: Path, gif_path: Path) -> None:
    palette_filter = (
        f"fps={FPS},scale=1000:-2:flags=lanczos,split[palette_source][gif_source];"
        "[palette_source]palettegen=max_colors=192:stats_mode=diff[palette];"
        "[gif_source][palette]paletteuse=dither=bayer:bayer_scale=3"
    )
    subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-i", str(video_path), "-filter_complex", palette_filter,
            "-loop", "0", str(gif_path),
        ],
        check=True,
    )


def main() -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("FFmpeg is required. Install it with your system package manager, then retry.")
    ASSETS.mkdir(parents=True, exist_ok=True)
    video_path = ASSETS / "fuserio-demo.mp4"
    gif_path = ASSETS / "fuserio-demo.gif"
    with tempfile.TemporaryDirectory(prefix="fuserio-demo-") as temporary_directory:
        frames = capture_frames(Path(temporary_directory))
        encode_video(frames, video_path)
    encode_gif(video_path, gif_path)
    print(f"Created {gif_path.relative_to(ROOT)} ({gif_path.stat().st_size / 1024:.0f} KB)")
    print(f"Created {video_path.relative_to(ROOT)} ({video_path.stat().st_size / 1024:.0f} KB)")
if __name__ == "__main__":
    main()
