import io
import sys
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtWidgets import QApplication


class _NoopSignal:
    def connect(self, _callback):
        pass


class _NoopServerProbe:
    def __init__(self, _base_url):
        self.found = _NoopSignal()
        self.failed = _NoopSignal()

    def start(self):
        pass

    def cancel(self):
        pass

    def isRunning(self):
        return False


def _capture_widget(widget, output_size: tuple[int, int]) -> Image.Image:
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not widget.grab().save(buffer, "PNG"):
        buffer.close()
        raise RuntimeError("Could not capture an app frame.")
    image = Image.open(io.BytesIO(bytes(buffer.data()))).convert("RGB")
    buffer.close()
    if image.size != output_size:
        resized = image.resize(output_size, Image.Resampling.LANCZOS)
        image.close()
        return resized
    return image


def create_titration_gif(
    output_path: str | Path,
    *,
    frame_count: int = 48,
    size: tuple[int, int] = (960, 600),
    frame_duration_ms: int = 80,
    desktop_intro_frames: int = 6,
) -> Path:
    if frame_count < 2:
        raise ValueError("An animated GIF needs at least two frames.")
    if frame_duration_ms < 20:
        raise ValueError("Frame duration must be at least 20 milliseconds.")
    if desktop_intro_frames < 1:
        raise ValueError("The desktop intro must include at least one frame.")

    application = QApplication.instance() or QApplication([])
    from localchat import app as app_module

    original_probe = app_module.ExistingServerProbe
    original_load_progress = app_module.load_progress
    original_save_progress = app_module.save_progress
    app_module.ExistingServerProbe = _NoopServerProbe
    app_module.load_progress = lambda: {"selection": {}, "sessions": {}}
    app_module.save_progress = lambda _progress: None
    window = app_module.MainWindow()
    window.resize(1280, 800)
    window.connection_status.setText("OFFLINE DEMO")
    window.statusBar().showMessage("Fuserio OS · offline simulation preview")
    window.show()
    application.processEvents()

    endpoint_volume = 25.0
    frames = []
    try:
        for _ in range(desktop_intro_frames):
            frames.append(_capture_widget(window, size))

        window.open_experiment("titration")
        canvas = window.lab_canvas
        for equipment in ("flask", "pipette", "indicator", "burette", "wash_bottle"):
            canvas.place_titration_equipment(equipment, canvas.rect().center())
        window._titration_action("pipette_acid")
        window._titration_action("add_indicator")

        for frame_index in range(frame_count):
            progress = frame_index / (frame_count - 1)
            volume = 30.0 * progress
            canvas.parameters["volume"] = volume
            canvas.elapsed = frame_index / 8
            canvas.titration_drop_progress = (frame_index % 7) / 7
            canvas.titration_transient_flash = max(0.0, 1.0 - abs(volume - endpoint_volume) / 1.5)
            canvas.titration_swirl_intensity = 0.35 if abs(volume - endpoint_volume) < 0.5 else 0.0
            canvas.update()
            window._sync_titration_setup()
            application.processEvents()
            frames.append(_capture_widget(window, size))
    finally:
        window.close()
        application.processEvents()
        app_module.ExistingServerProbe = original_probe
        app_module.load_progress = original_load_progress
        app_module.save_progress = original_save_progress

    destination = Path(output_path).expanduser()
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        frames[0].save(
            destination,
            format="GIF",
            save_all=True,
            append_images=frames[1:],
            duration=frame_duration_ms,
            loop=0,
            optimize=True,
            disposal=2,
            comment=b"Fuserio desktop walkthrough, then interactive acid-base titration simulation",
        )
    finally:
        for frame in frames:
            frame.close()
    return destination


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("assets/titration-operation.gif")
    print(create_titration_gif(target))