from __future__ import annotations

import base64
import io
import zipfile

from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.templating import Jinja2Templates
from PIL import Image
from starlette.requests import Request

from app.image_processor import (
    BRANDS,
    ImageTooSmallError,
    MIN_PIXEL_COUNT,
    SUPPORTED_IMAGE_EXTENSIONS,
    process_hotel_image,
    sanitize_filename_part,
    validate_min_pixel_count,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

LOGO_DIR = Path(__file__).parent / "static" / "logos"
LOGO_EXTENSIONS = (".svg", ".png", ".webp", ".jpg")
THUMB_SIZE = (480, 320)
THUMB_QUALITY = 80


@router.get("/")
async def hotel_index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="hotel.html",
        context={
            "brands": BRANDS,
            "logos": _brand_logos(),
            "extensions": sorted(SUPPORTED_IMAGE_EXTENSIONS),
            "min_pixels": MIN_PIXEL_COUNT,
        },
    )


# Bewusst ohne async: die Bildbearbeitung rechnet blockierend und läuft so im
# Threadpool von FastAPI, statt den Server für alle anderen Nutzer anzuhalten.
@router.post("/api/process")
def process_upload(
    hotel_name: str = Form(...),
    brand: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Bearbeitet eine hochgeladene Datei (Einzelbild oder ZIP mit Bildern).

    Antwort: die bearbeiteten Bilder als Base64 (Vollbild 1800 x 1200 und Vorschau),
    dazu übersprungene und fehlgeschlagene Dateien. Die Dateinamen und die ZIP
    für den Download entstehen erst im Browser, nach der Sortierung.
    """
    hotel = hotel_name.strip()
    if not hotel:
        raise HTTPException(status_code=400, detail="Bitte einen Hotelnamen eingeben.")

    brand_upper = brand.strip().upper()
    if brand_upper not in BRANDS:
        raise HTTPException(status_code=400, detail="Bitte eine gültige Brand auswählen.")

    payloads, failed = _collect_image_payloads(file)

    images: list[dict[str, str]] = []
    skipped: list[str] = []
    for source_name, content in payloads:
        try:
            validate_min_pixel_count(content)
        except ImageTooSmallError:
            skipped.append(source_name)
            continue
        except Exception:
            failed.append({"source": source_name, "error": "Datei ist kein lesbares Bild."})
            continue

        try:
            processed, _ = process_hotel_image(content)
        except Exception as exc:  # einzelnes Bild scheitert, der Rest läuft weiter
            failed.append({"source": source_name, "error": str(exc)})
            continue

        images.append(
            {
                "source": source_name,
                "data": base64.b64encode(processed).decode("ascii"),
                "thumb": base64.b64encode(_make_thumbnail(processed)).decode("ascii"),
            }
        )

    return {
        "prefix": f"{sanitize_filename_part(hotel)}_{sanitize_filename_part(brand_upper)}",
        "images": images,
        "skipped": skipped,
        "failed": failed,
    }


def _brand_logos() -> dict[str, str]:
    """Logo je Brand aus app/static/logos/<brand>.<svg|png|webp|jpg>, Dateiname klein geschrieben.
    Fehlt ein Logo, zeigt die Oberfläche den Namen als Text."""
    logos: dict[str, str] = {}
    for brand in BRANDS:
        for ext in LOGO_EXTENSIONS:
            path = LOGO_DIR / f"{brand.lower()}{ext}"
            if path.is_file():
                logos[brand] = f"/static/logos/{path.name}?v={int(path.stat().st_mtime)}"
                break
    return logos


def _make_thumbnail(jpeg: bytes) -> bytes:
    with Image.open(io.BytesIO(jpeg)) as image:
        image.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
        out = io.BytesIO()
        image.save(out, format="JPEG", quality=THUMB_QUALITY, optimize=True)
        return out.getvalue()


def _has_image_extension(name: str) -> bool:
    lower = name.lower()
    return any(lower.endswith(ext) for ext in SUPPORTED_IMAGE_EXTENSIONS)


def _collect_image_payloads(upload: UploadFile) -> tuple[list[tuple[str, bytes]], list[dict[str, str]]]:
    name = upload.filename or "(unbekannt)"
    content = upload.file.read()
    if not content:
        return [], [{"source": name, "error": "Datei ist leer."}]

    if _has_image_extension(name) or not name.lower().endswith(".zip"):
        # Auch Bilder ohne passende Endung (z. B. aus der Zwischenablage) versuchen;
        # was kein Bild ist, landet bei der Prüfung unter "failed".
        return [(name, content)], []

    payloads: list[tuple[str, bytes]] = []
    try:
        with zipfile.ZipFile(io.BytesIO(content), mode="r") as archive:
            for member in archive.infolist():
                if member.is_dir() or not _has_image_extension(member.filename):
                    continue
                # macOS legt in ZIPs Schattendateien an (__MACOSX/._bild.jpg)
                base = member.filename.rsplit("/", 1)[-1]
                if member.filename.startswith("__MACOSX/") or base.startswith("._"):
                    continue
                member_content = archive.read(member)
                if member_content:
                    payloads.append((f"{name} › {member.filename}", member_content))
    except zipfile.BadZipFile:
        return [], [{"source": name, "error": "ZIP-Datei konnte nicht gelesen werden."}]

    if not payloads:
        return [], [{"source": name, "error": "ZIP enthält keine Bilddateien."}]
    return payloads, []
