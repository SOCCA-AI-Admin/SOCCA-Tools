from __future__ import annotations

import io
import re
from typing import Final

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageStat

TARGET_WIDTH: Final[int] = 1800
TARGET_HEIGHT: Final[int] = 1200
TARGET_RATIO: Final[float] = 3 / 2
JPEG_QUALITY: Final[int] = 90
MIN_PIXEL_COUNT: Final[int] = 480_000
MAX_TARGET_BYTES: Final[int] = 1_000_000

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


def validate_min_pixel_count(content: bytes) -> None:
    with Image.open(io.BytesIO(content)) as source:
        width, height = source.size
    if width * height < MIN_PIXEL_COUNT:
        raise ImageTooSmallError(
            f"Bild hat nur {width * height} Pixel (Minimum: {MIN_PIXEL_COUNT})."
        )


def process_hotel_image(content: bytes) -> tuple[bytes, list[str]]:
    """Create premium web output with conservative adaptive corrections."""
    with Image.open(io.BytesIO(content)) as source:
        image = ImageOps.exif_transpose(source)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        elif image.mode == "L":
            image = image.convert("RGB")

        image = _auto_level_horizon(image)
        image = _ensure_landscape(image)
        image = _center_crop_ratio(image, TARGET_RATIO)
        image = image.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)
        image, adjustments = _adaptive_premium_adjust(image)

        encoded, quality = _encode_jpeg_with_limit(image)
        adjustments.append(f"jpeg_quality={quality}")
        return encoded, adjustments


def _ensure_landscape(image: Image.Image) -> Image.Image:
    width, height = image.size
    if height > width:
        return image.rotate(90, expand=True, resample=Image.Resampling.BICUBIC)
    return image


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


def _auto_level_horizon(image: Image.Image) -> Image.Image:
    """Rotate slightly tilted images to a more horizontal position."""
    width, height = image.size
    rgb = image.convert("RGB")
    frame = np.array(rgb)
    gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150, apertureSize=3)

    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=90,
        minLineLength=max(60, min(width, height) // 4),
        maxLineGap=25,
    )
    if lines is None:
        return rgb

    weighted_angles: list[tuple[float, float]] = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0 and dy == 0:
            continue
        angle = float(np.degrees(np.arctan2(dy, dx)))
        if angle > 90:
            angle -= 180
        elif angle < -90:
            angle += 180
        # Only consider near-horizontal lines.
        if abs(angle) > 12:
            continue
        length = float(np.hypot(dx, dy))
        if length < min(width, height) * 0.12:
            continue
        weighted_angles.append((angle, length))

    if len(weighted_angles) < 10:
        return rgb

    angles = np.array([angle for angle, _ in weighted_angles], dtype=np.float32)
    weights = np.array([weight for _, weight in weighted_angles], dtype=np.float32)
    rotation_angle = _weighted_median(angles, weights)
    spread = _weighted_median(np.abs(angles - rotation_angle), weights)

    # Only rotate when signal is clear and tilt is meaningful.
    if spread > 1.8 or abs(rotation_angle) < 1.2:
        return rgb
    rotation_angle = float(np.clip(rotation_angle, -5.0, 5.0))

    rotated = rgb.rotate(
        -rotation_angle,
        resample=Image.Resampling.BICUBIC,
        expand=True,
        fillcolor=(255, 255, 255),
    )
    return ImageOps.fit(rotated, (width, height), method=Image.Resampling.BICUBIC, centering=(0.5, 0.5))


def _weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    order = np.argsort(values)
    sorted_values = values[order]
    sorted_weights = weights[order]
    cumulative = np.cumsum(sorted_weights)
    cutoff = sorted_weights.sum() * 0.5
    index = int(np.searchsorted(cumulative, cutoff))
    return float(sorted_values[min(index, len(sorted_values) - 1)])


def _encode_jpeg_with_limit(image: Image.Image) -> tuple[bytes, int]:
    for quality in range(JPEG_QUALITY, 34, -5):
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

    # Hard cap fallback.
    output = io.BytesIO()
    image.save(
        output,
        format="JPEG",
        quality=30,
        optimize=True,
        progressive=True,
        subsampling="4:2:0",
    )
    data = output.getvalue()
    if len(data) <= MAX_TARGET_BYTES:
        return data, 30
    raise ValueError("Zieldatei überschreitet 1MB trotz maximaler Kompression.")


def _adaptive_premium_adjust(image: Image.Image) -> tuple[Image.Image, list[str]]:
    """
    Conservative auto-enhancement for premium website presentation.
    Priority is natural look over aggressive effect.
    """
    adjusted = image
    adjustments: list[str] = []

    shadow_lifted, shadow_note = _lift_shadows_if_needed(adjusted)
    adjusted = shadow_lifted
    if shadow_note:
        adjustments.append(shadow_note)

    brightness_factor = _brightness_factor(adjusted)
    if abs(brightness_factor - 1.0) >= 0.015:
        adjusted = ImageEnhance.Brightness(adjusted).enhance(brightness_factor)
        adjustments.append(f"brightness={brightness_factor:.3f}")

    contrast_factor = _contrast_factor(adjusted)
    if abs(contrast_factor - 1.0) >= 0.015:
        adjusted = ImageEnhance.Contrast(adjusted).enhance(contrast_factor)
        adjustments.append(f"contrast={contrast_factor:.3f}")

    color_factor = _saturation_factor(adjusted)
    if abs(color_factor - 1.0) >= 0.015:
        adjusted = ImageEnhance.Color(adjusted).enhance(color_factor)
        adjustments.append(f"saturation={color_factor:.3f}")

    wb_image, wb_note = _neutralize_color_cast(adjusted)
    adjusted = wb_image
    if wb_note:
        adjustments.append(wb_note)

    sharp_factor = _sharpness_factor(adjusted)
    if abs(sharp_factor - 1.0) >= 0.02:
        adjusted = ImageEnhance.Sharpness(adjusted).enhance(sharp_factor)
        adjustments.append(f"sharpness={sharp_factor:.3f}")

    if not adjustments:
        adjustments.append("no_adjustment_needed")

    return adjusted, adjustments


def _brightness_factor(image: Image.Image) -> float:
    gray = np.array(image.convert("L"), dtype=np.uint8)
    luminance = float(gray.mean())
    p25 = float(np.percentile(gray, 25))
    if p25 < 40:
        return 1.32
    if p25 < 55:
        return 1.18
    if luminance < 85:
        return 1.14
    if luminance < 105:
        return 1.08
    if luminance > 185:
        return 0.93
    if luminance > 170:
        return 0.97
    return 1.0


def _contrast_factor(image: Image.Image) -> float:
    luminance_stat = ImageStat.Stat(image.convert("L"))
    stddev = luminance_stat.stddev[0]
    if stddev < 34:
        return 1.14
    if stddev < 44:
        return 1.08
    if stddev > 82:
        return 0.92
    return 1.0


def _saturation_factor(image: Image.Image) -> float:
    hsv = image.convert("HSV")
    sat_mean = ImageStat.Stat(hsv).mean[1]
    if sat_mean < 80:
        return 1.12
    if sat_mean < 110:
        return 1.06
    if sat_mean > 185:
        return 0.90
    return 1.0


def _sharpness_factor(image: Image.Image) -> float:
    # Mild edge energy estimate from luminance gradients.
    gray = np.array(image.convert("L"), dtype=np.float32)
    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    edge_energy = float(np.mean(np.hypot(grad_x, grad_y)))
    if edge_energy < 24:
        return 1.07
    if edge_energy > 62:
        return 0.97
    return 1.0


def _neutralize_color_cast(image: Image.Image) -> tuple[Image.Image, str]:
    arr = np.asarray(image, dtype=np.float32)
    channel_means = arr.reshape(-1, 3).mean(axis=0)
    mean_gray = float(channel_means.mean())
    if mean_gray <= 0:
        return image, ""

    raw_gains = mean_gray / channel_means
    # Keep correction subtle.
    gains = np.clip(raw_gains, 0.94, 1.06)
    if np.max(np.abs(gains - 1.0)) < 0.01:
        return image, ""

    corrected = arr * gains
    corrected = np.clip(corrected, 0, 255).astype(np.uint8)
    gain_text = f"wb_r={gains[0]:.3f},wb_g={gains[1]:.3f},wb_b={gains[2]:.3f}"
    return Image.fromarray(corrected, mode="RGB"), gain_text


def _lift_shadows_if_needed(image: Image.Image) -> tuple[Image.Image, str]:
    """
    Lift shadow detail on dark images with a soft gamma curve.
    Keeps highlights controlled and avoids a washed-out look.
    """
    gray = np.array(image.convert("L"), dtype=np.uint8)
    p25 = float(np.percentile(gray, 25))
    mean = float(gray.mean())
    if p25 >= 65 and mean >= 105:
        return image, ""

    if p25 < 40 or mean < 80:
        gamma = 0.82
    elif p25 < 52 or mean < 92:
        gamma = 0.88
    else:
        gamma = 0.93

    arr = np.asarray(image, dtype=np.float32) / 255.0
    lifted = np.power(arr, gamma)
    lifted = np.clip(lifted * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(lifted, mode="RGB"), f"shadow_gamma={gamma:.2f}"
