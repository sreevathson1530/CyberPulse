"""Turn the tour screenshots from tools/tour_shots.js (PNG) into the smaller
WebP files the app shows."""

from pathlib import Path

from PIL import Image

FOLDER = Path(__file__).resolve().parents[1] / "assets" / "tour"

for png in sorted(FOLDER.glob("*.png")):
    image = Image.open(png).convert("RGB")
    image.thumbnail((1560, 1560), Image.LANCZOS)
    webp = png.with_suffix(".webp")
    image.save(webp, "WEBP", quality=84, method=6)
    png.unlink()
    print(f"{webp.name}: {image.width}x{image.height}, {webp.stat().st_size // 1024} KB")
