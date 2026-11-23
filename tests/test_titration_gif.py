import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PIL import ImageChops
import pytest

from localchat.titration_gif import create_titration_gif


def test_titration_gif_is_animated_and_uses_requested_dimensions(tmp_path):
    output = create_titration_gif(
        tmp_path / "titration.gif",
        frame_count=6,
        size=(480, 320),
    )

    with Image.open(output) as gif:
        assert gif.format == "GIF"
        assert gif.size == (480, 320)
        assert gif.n_frames >= 7
        assert gif.info["loop"] == 0
        first_frame = gif.convert("RGB")
        gif.seek(1)
        lab_frame = gif.convert("RGB")
        assert ImageChops.difference(first_frame, lab_frame).getbbox() is not None
        assert b"desktop walkthrough" in gif.info["comment"]


def test_titration_gif_rejects_a_single_frame(tmp_path):
    with pytest.raises(ValueError, match="at least two frames"):
        create_titration_gif(tmp_path / "invalid.gif", frame_count=1)