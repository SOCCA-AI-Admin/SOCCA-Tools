from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
from pathlib import Path
from typing import Final

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

# iPhone-HEIC/HEIF (und AVIF, wenn verfügbar) über Pillow öffnen.
register_heif_opener()

TARGET_WIDTH: Final[int] = 1800
TARGET_HEIGHT: Final[int] = 1200
TARGET_RATIO: Final[float] = 3 / 2
JPEG_QUALITY: Final[int] = 90
MIN_PIXEL_COUNT: Final[int] = 480_000
MAX_TARGET_BYTES: Final[int] = 1_000_000

# Größere Bilder werden vor LightCraft verkleinert: Das Ergebnis hat ohnehin nur 1800 px Breite,
# der Rest bringt keine Qualität, kostet aber Zeit und Speicher (12 MP ≈ 5 s und 670 MB).
MAX_INPUT_EDGE: Final[int] = 3000

# LightCraft (Open-Source-Nachbau von Lightroom, https://github.com/storytold/lightcraft)
LIGHTCRAFT_CLI: Final[str] = os.environ.get("LIGHTCRAFT_CLI", "lightcraft-cli")
LIGHTCRAFT_TIMEOUT_S: Final[int] = 120
PRESET_PATH: Final[Path] = Path(__file__).parent / "presets" / "SOCCA.xmp"
# Höchstens zwei LightCraft-Läufe gleichzeitig, damit der Server bei mehreren Nutzern nicht ins Swappen gerät.
_LIGHTCRAFT_SLOTS = threading.Semaphore(2)

SUPPORTED_IMAGE_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".jpg",
        ".jpeg",
        ".jfif",
        ".png",
        ".webp",
        ".bmp",
        ".tif",
        ".tiff",
        ".gif",
        ".heic",
        ".heif",
        ".avif",
    }
)

BRANDS: Final[tuple[str, ...]] = (
    "SOCCATOURS",
    "SOCCACUP",
    "SWIMTOURS",
    "ATHLETICSTOURS",
    "TENNISTOURS",
)


def sanitize_filename_part(value: str) -> str:
    cleaned = re.sub(r"[^\w\-]+", "_", value.strip(), flags=re.UNICODE)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned[:80] or "Hotel"


class ImageTooSmallError(ValueError):
    pass


class LightCraftError(RuntimeError):
    pass


def validate_min_pixel_count(content: bytes) -> None:
    with Image.open(io.BytesIO(content)) as source:
        width, height = source.size
    if width * height < MIN_PIXEL_COUNT:
        raise ImageTooSmallError(
            f"Bild hat nur {width * height} Pixel (Minimum: {MIN_PIXEL_COUNT})."
        )


def _preset_id() -> str:
    """LightCraft vergibt importierten XMP-Presets die ID user.xmp.<UUID in Kleinbuchstaben>."""
    text = PRESET_PATH.read_text(encoding="utf-8")
    match = re.search(r'crs:UUID="([0-9A-Fa-f]+)"', text)
    if not match:
        raise LightCraftError(f"{PRESET_PATH.name} enthält keine crs:UUID.")
    return f"user.xmp.{match.group(1).lower()}"


def lightcraft_available() -> bool:
    return shutil.which(LIGHTCRAFT_CLI) is not None or Path(LIGHTCRAFT_CLI).is_file()


def process_hotel_image(content: bytes) -> tuple[bytes, list[str]]:
    """
    1. Öffnen, EXIF-Drehung übernehmen, verkleinern (max. MAX_INPUT_EDGE)
    2. LightCraft: Preset SOCCA.xmp anwenden, Gerade ausrichten (Auto), exportieren
    3. Mittig auf 3:2 Querformat zuschneiden (Hochformat wird dabei oben und unten beschnitten)
    4. Auf 1800 × 1200 skalieren, als JPG mit höchstens 1 MB speichern
    """
    notes: list[str] = []
    with Image.open(io.BytesIO(content)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
    image.thumbnail((MAX_INPUT_EDGE, MAX_INPUT_EDGE), Image.Resampling.LANCZOS)

    image, lc_notes = _develop_with_lightcraft(image)
    notes.extend(lc_notes)

    if image.height > image.width:
        notes.append("hochformat_zugeschnitten")
    image = _center_crop_ratio(image, TARGET_RATIO)
    image = image.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)

    encoded, quality = _encode_jpeg_with_limit(image)
    notes.append(f"jpeg_quality={quality}")
    return encoded, notes


def _develop_with_lightcraft(image: Image.Image) -> tuple[Image.Image, list[str]]:
    if not lightcraft_available():
        raise LightCraftError("LightCraft ist auf dem Server nicht installiert (lightcraft-cli fehlt).")

    with tempfile.TemporaryDirectory(prefix="lightcraft-") as tmp:
        src = Path(tmp) / "in.tif"
        dst = Path(tmp) / "out.tif"
        image.save(src, format="TIFF")

        cmd = [
            LIGHTCRAFT_CLI, "run", "--keep-going",
            "--import", str(src),
            "preset.import", f"paths={json.dumps([str(PRESET_PATH)])}",
            "preset.apply", f"id={_preset_id()}",
            "crop.autoStraighten",
            "app.export", f"path={dst}", "longEdge=0",
        ]
        # Eigenes HOME je Lauf: LightCraft legt so keine Einstellungen oder Caches dauerhaft ab.
        env = {**os.environ, "HOME": tmp}
        with _LIGHTCRAFT_SLOTS:
            try:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=LIGHTCRAFT_TIMEOUT_S, env=env
                )
            except subprocess.TimeoutExpired as exc:
                raise LightCraftError("LightCraft hat zu lange gebraucht.") from exc

        results = _parse_results(proc.stdout)
        failed = {k: v for k, v in results.items() if not v.get("ok")}
        for step in ("preset.import", "preset.apply", "app.export"):
            if step in failed or step not in results:
                detail = failed.get(step, {}).get("error") or proc.stderr.strip()[-300:] or "keine Antwort"
                raise LightCraftError(f"LightCraft-Schritt {step} fehlgeschlagen: {detail}")
        if not dst.is_file():
            raise LightCraftError("LightCraft hat keine Datei exportiert.")

        notes = ["lightcraft_preset=SOCCA"]
        straighten = results.get("crop.autoStraighten", {})
        result = straighten.get("result") or {}
        if straighten.get("ok") and result.get("changed"):
            notes.append(f"gerade_ausgerichtet={result.get('angle', 0):.2f}°")
        else:
            notes.append("gerade_ausrichten=keine_änderung")

        with Image.open(dst) as developed:
            return developed.convert("RGB"), notes


def _parse_results(stdout: str) -> dict[str, dict]:
    """lightcraft-cli run gibt je Befehl eine JSON-Zeile aus: {command, ok, result|error, ms}."""
    results: dict[str, dict] = {}
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "command" in entry:
            results[entry["command"]] = entry
    return results


def _center_crop_ratio(image: Image.Image, target_ratio: float) -> Image.Image:
    width, height = image.size
    current_ratio = width / height

    if current_ratio > target_ratio:
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        return image.crop((left, 0, left + new_width, height))

    new_height = int(width / target_ratio)
    top = (height - new_height) // 2
    return image.crop((0, top, width, top + new_height))


def _encode_jpeg_with_limit(image: Image.Image) -> tuple[bytes, int]:
    for quality in range(JPEG_QUALITY, 29, -5):
        output = io.BytesIO()
        image.save(
            output,
            format="JPEG",
            quality=quality,
            optimize=True,
            progressive=True,
            subsampling="4:2:0",
        )
        data = output.getvalue()
        if len(data) <= MAX_TARGET_BYTES:
            return data, quality
    raise ValueError("Zieldatei überschreitet 1 MB trotz maximaler Kompression.")
