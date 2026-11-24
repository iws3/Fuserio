#!/usr/bin/env python3
"""Capture a model-free, desktop-first Fuserio product walkthrough."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PySide6.QtCore import QPointF
from PySide6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from localchat import app as app_module


ASSETS = ROOT / "assets"
FPS = 24
GIF_FPS = 8
OUTPUT_WIDTH = 1280
CROSSFADE_SECONDS = 0.45
TOOL_TRAVEL_FRAMES = 10


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


def ease_out_cubic(progress: float) -> float:
    progress = max(0.0, min(1.0, progress))
    return 1 - (1 - progress) ** 3


def capture_frames(frame_directory: Path) -> list[Path]:
    original_probe = app_module.ExistingServerProbe
    original_load_progress = app_module.load_progress
    original_save_progress = app_module.save_progress
    app_module.ExistingServerProbe = QuietServerProbe
    app_module.load_progress = lambda: {"selection": {}, "sessions": {}}
    app_module.save_progress = lambda _progress: None

    application = QApplication.instance() or QApplication([])
    window = app_module.MainWindow()
    window.resize(1440, 900)
    window.connection_status.setText("OFFLINE DEMO")
    window.statusBar().showMessage("Fuserio OS · local-first learning workspace")
    window.show()
    application.processEvents()

    frames: list[Path] = []
    frame_index = 0

    def save_frame(label: str) -> Path:
        nonlocal frame_index
        application.processEvents()
        frame_index += 1
        path = frame_directory / f"frame-{frame_index:05d}-{label}.png"
        if not window.grab().save(str(path), "PNG"):
            raise RuntimeError(f"Could not capture {path}")
        return path

    def hold(seconds: float) -> None:
        if frames:
            frames.extend([frames[-1]] * max(1, round(seconds * FPS)))

    def scene(label: str, seconds: float = 0.7) -> Path:
        frame = save_frame(label)
        frames.append(frame)
        hold(seconds)
        return frame

    def transition(label: str, seconds: float = 0.8) -> Path:
        source_path = frames[-1]
        target_path = save_frame(label)
        with Image.open(source_path) as source, Image.open(target_path) as target:
            source_rgb = source.convert("RGB")
            target_rgb = target.convert("RGB")
            count = max(2, round(CROSSFADE_SECONDS * FPS))
            for index in range(1, count + 1):
                blended = Image.blend(source_rgb, target_rgb, index / count)
                path = frame_directory / f"frame-{frame_index + index:05d}-fade-{label}.png"
                blended.save(path, "PNG")
                frames.append(path)
                blended.close()
            source_rgb.close()
            target_rgb.close()
        frames.append(target_path)
        hold(seconds)
        return target_path

    try:
        scene("fuserio-desktop", 1.2)

        window.open_ai_workspace()
        window.input.setPlainText("model inspect")
        scene("terminal-model-command", 0.25)
        window.send_message()
        transition("terminal-model-inspection", 1.0)
        window.input.setPlainText("/agent list models")
        window.send_message()
        scene("terminal-model-catalog", 0.8)

        window.input.setPlainText("/agent open titration")
        window.send_message()
        transition("empty-titration-table", 0.9)

        canvas = window.lab_canvas
        canvas.show_equipment_labels = False
        equipment_targets = (
            ("retort_stand", 0.24, 0.58),
            ("burette", 0.43, 0.38),
            ("flask", 0.43, 0.73),
            ("ph_meter", 0.78, 0.43),
            ("pipette", 0.24, 0.77),
            ("indicator", 0.61, 0.77),
            ("wash_bottle", 0.78, 0.74),
        )
        for equipment_id, target_x, target_y in equipment_targets:
            button = window.titration_equipment_buttons[equipment_id]
            source = canvas.mapFromGlobal(button.mapToGlobal(button.rect().center()))
            target = QPointF(canvas.width() * target_x, canvas.height() * target_y)
            canvas.place_titration_equipment(equipment_id, target)
            item = canvas._equipment_items[equipment_id]
            destination = item.pos()
            start_x = max(0, min(source.x() - item.width() // 2, canvas.width() - item.width()))
            start_y = max(0, min(source.y() - item.height() // 2, canvas.height() - item.height()))
            item.move(start_x, start_y)

            for frame in range(1, TOOL_TRAVEL_FRAMES + 1):
                eased = ease_out_cubic(frame / TOOL_TRAVEL_FRAMES)
                item.move(
                    round(start_x + (destination.x() - start_x) * eased),
                    round(start_y + (destination.y() - start_y) * eased),
                )
                frames.append(save_frame(f"place-{equipment_id}"))
            item.move(destination)
            scene(f"placed-{equipment_id}", 0.12)

        window._titration_action("pipette_acid")
        scene("measure-25ml-analyte", 0.45)
        window._titration_action("add_indicator")
        window._titration_action("add_indicator")
        scene("indicator-in-flask", 0.45)

        endpoint_volume = 25.0
        for index in range(121):
            volume = 25.3 * index / 120
            canvas.parameters["volume"] = volume
            canvas.elapsed = index / 8
            canvas.titration_drop_progress = (index % 8) / 8
            canvas.titration_transient_flash = max(0.0, 1.0 - abs(volume - endpoint_volume) / 1.1)
            canvas.titration_swirl_intensity = 0.4 if abs(volume - endpoint_volume) < 0.2 else 0.0
            window._sync_lab_runtime()
            frames.append(save_frame("endpoint-titration"))
        canvas.pause()
        hold(1.4)
    finally:
        window.close()
        application.processEvents()
        app_module.ExistingServerProbe = original_probe
        app_module.load_progress = original_load_progress
        app_module.save_progress = original_save_progress

    return frames


def encode_video(frames: list[Path], video_path: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="fuserio-showcase-") as temporary_directory:
        manifest = Path(temporary_directory) / "frames.txt"
        frame_duration = 1 / FPS
        with manifest.open("w", encoding="utf-8") as output:
            for frame in frames:
                output.write(f"file '{frame.as_posix()}'\n")
                output.write(f"duration {frame_duration:.6f}\n")
            output.write(f"file '{frames[-1].as_posix()}'\n")
        subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "concat", "-safe", "0", "-i", str(manifest),
                "-vf", f"scale={OUTPUT_WIDTH}:-2:flags=lanczos,setsar=1,fps={FPS},format=yuv420p",
                "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(video_path),
            ],
            check=True,
        )


def encode_gif(video_path: Path, gif_path: Path) -> None:
    palette_filter = (
        f"fps={GIF_FPS},scale=800:-2:flags=lanczos,split[palette_source][gif_source];"
        "[palette_source]palettegen=max_colors=128:stats_mode=diff[palette];"
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
    with tempfile.TemporaryDirectory(prefix="fuserio-showcase-frames-") as temporary_directory:
        frames = capture_frames(Path(temporary_directory))
        encode_video(frames, video_path)
    encode_gif(video_path, gif_path)
    print(f"Created {gif_path.relative_to(ROOT)} ({gif_path.stat().st_size / 1024:.0f} KB)")
    print(f"Created {video_path.relative_to(ROOT)} ({video_path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
