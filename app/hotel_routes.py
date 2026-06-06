from __future__ import annotations

import io
import zipfile
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from app.image_processor import (
    BRANDS,
    ImageTooSmallError,
    process_hotel_image,
    sanitize_filename_part,
    validate_min_pixel_count,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"}


@router.get("/")
async def hotel_index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="hotel.html",
        context={"brands": BRANDS},
    )


@router.post("/api/process")
async def process_hotel_images(
    hotel_name: str = Form(...),
    brand: str = Form(...),
    files: list[UploadFile] = File(...),
):
    hotel = hotel_name.strip()
    if not hotel:
        raise HTTPException(status_code=400, detail="Bitte einen Hotelnamen eingeben.")

    brand_upper = brand.strip().upper()
    if brand_upper not in BRANDS:
        raise HTTPException(status_code=400, detail="Bitte eine gültige Brand auswählen.")

    image_payloads = await _collect_image_payloads(files)
    if not image_payloads:
        raise HTTPException(status_code=400, detail="Bitte mindestens eine Bilddatei oder ZIP-Datei hochladen.")

    safe_hotel = sanitize_filename_part(hotel)
    safe_brand = sanitize_filename_part(brand_upper)

    prepared: list[tuple[str, bytes]] = []
    too_small_files: list[str] = []
    for source_name, content in image_payloads:
        try:
            validate_min_pixel_count(content)
        except ImageTooSmallError:
            too_small_files.append(source_name)
            continue
        prepared.append((source_name, content))

    if not prepared:
        if too_small_files:
            formatted = ", ".join(too_small_files)
            raise HTTPException(
                status_code=400,
                detail=(
                    "Keine ZIP erstellt: Alle Dateien wurden übersprungen, weil sie weniger als 480000 Pixel haben: "
                    f"{formatted}"
                ),
            )
        raise HTTPException(status_code=400, detail="Keine verarbeitbaren Bilddateien vorhanden.")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for index, (source_name, content) in enumerate(prepared, start=1):
            try:
                processed, _ = process_hotel_image(content)
            except Exception as exc:
                raise HTTPException(
                    status_code=400,
                    detail=f"Bild konnte nicht verarbeitet werden ({source_name}): {exc}",
                ) from exc

            filename = f"{safe_hotel}_{safe_brand}_{index:03d}.jpg"
            archive.writestr(filename, processed)

    zip_buffer.seek(0)
    zip_name = f"{safe_hotel}_{safe_brand}.zip"

    headers = {"Content-Disposition": f'attachment; filename="{zip_name}"'}
    if too_small_files:
        encoded = "|".join(quote(name, safe="") for name in too_small_files)
        headers["X-Skipped-Files"] = encoded
        headers["X-Skipped-Count"] = str(len(too_small_files))

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers=headers,
    )


def _is_image_upload(upload: UploadFile) -> bool:
    name = (upload.filename or "").lower()
    return any(name.endswith(ext) for ext in IMAGE_EXTENSIONS)


def _is_zip_upload(upload: UploadFile) -> bool:
    return (upload.filename or "").lower().endswith(".zip")


async def _collect_image_payloads(files: list[UploadFile]) -> list[tuple[str, bytes]]:
    payloads: list[tuple[str, bytes]] = []
    for upload in files:
        if _is_image_upload(upload):
            content = await upload.read()
            if content:
                payloads.append((upload.filename or "(unbekannt)", content))
            continue

        if not _is_zip_upload(upload):
            continue

        zip_bytes = await upload.read()
        if not zip_bytes:
            continue

        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes), mode="r") as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    member_name = member.filename
                    if not _name_has_image_extension(member_name):
                        continue
                    member_content = archive.read(member)
                    if not member_content:
                        continue
                    source = f"{upload.filename}::{member_name}"
                    payloads.append((source, member_content))
        except zipfile.BadZipFile as exc:
            raise HTTPException(
                status_code=400,
                detail=f"ZIP-Datei konnte nicht gelesen werden ({upload.filename}).",
            ) from exc
    return payloads


def _name_has_image_extension(name: str) -> bool:
    lower = name.lower()
    return any(lower.endswith(ext) for ext in IMAGE_EXTENSIONS)
