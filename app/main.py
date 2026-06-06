from __future__ import annotations

import io
import os
import re
from decimal import Decimal, InvalidOperation
from typing import Iterable

import fitz
import pytesseract
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook
from PIL import Image
from pypdf import PdfReader
from starlette.requests import Request

app = FastAPI(title="Invoice to Transfer Export")
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


IBAN_REGEX = re.compile(r"\b[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}\b")
BIC_REGEX = re.compile(r"\b[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b")
AMOUNT_VALUE_REGEX = re.compile(r"([0-9]{1,3}(?:[.,\s][0-9]{3})*(?:[.,][0-9]{2})|[0-9]+[.,][0-9]{2})")
AMOUNT_LABELS = (
    "gesamtbetrag",
    "endbetrag",
    "rechnungsbetrag",
    "zahlbetrag",
    "zu zahlen",
    "summe",
    "gesamt",
    "total",
    "amount due",
    "amount payable",
    "balance due",
    "amount to pay",
    "payable amount",
    "grand total",
    "invoice total",
    "payment due",
    "montant total",
    "montant a payer",
    "a payer",
    "total ttc",
    "importe total",
    "total a pagar",
    "saldo a pagar",
    "neto a pagar",
    "monto a pagar",
    "totale",
    "totale da pagare",
    "importo da pagare",
    "pagare",
    "totale documento",
    "document total",
)
AMOUNT_NEGATIVE_LABELS = (
    "netto",
    "net",
    "subtotal",
    "sub total",
    "imponibile",
    "taxable",
    "iva esclusa",
    "excl",
)
IBAN_LABELS = ("iban", "account", "bank account", "konto", "banca", "banco", "banque")
BIC_LABELS = ("bic", "swift", "swift code", "codice swift")
ACCOUNT_HOLDER_LABELS = (
    "kontoinhaber",
    "begünstigter",
    "empfänger",
    "zahlungsempfänger",
    "account holder",
    "beneficiary",
    "payee",
    "bank beneficiary",
    "beneficiaire",
    "destinatario",
    "intestatario",
    "beneficiario",
    "titulaire du compte",
    "destinataire",
)
ACCOUNT_HOLDER_STRONG_LABELS = (
    "sede legale",
    "legal seat",
    "company",
    "ragione sociale",
)
ACCOUNT_HOLDER_NEGATIVE_WORDS = (
    "vendita",
    "documento",
    "numero",
    "data",
    "pagina",
    "partita iva",
    "codice fiscale",
    "causale",
    "modalita",
    "modalità",
    "pagamento",
    "banca d'appoggio",
    "spettabile",
)
AMOUNT_NEGATIVE_CONTEXT_WORDS = (
    "partita iva",
    "codice fiscale",
    "rea",
    "pec",
    "tel",
    "telefono",
    "vat",
    "tax",
    "codice univoco",
)
CURRENCY_REGEX = re.compile(r"\b(EUR|USD|GBP|CHF|CAD|AUD|SEK|NOK|DKK|PLN|CZK|HUF|RON)\b", re.IGNORECASE)
LINE_SPLIT_MARKER_REGEX = re.compile(
    r"(?i)(?=\b(?:IBAN:|BIC:|Verwendungszweck:|Guthaben\b|Ihr\s+Guthaben|"
    r"Buchungsbestätigung|SOCCATOURS Austria GmbH|Voraussetzungen|Zahlungsmodalitäten)\b)"
)
EURO_AMOUNT_REGEX = re.compile(r"([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})|[0-9]+,[0-9]{2})\s*€?")
VALID_IBAN_COUNTRY_CODES = {
    "AT", "BE", "CH", "CY", "CZ", "DE", "DK", "EE", "ES", "FI", "FR", "GB", "GI", "GR", "HR", "HU", "IE",
    "IS", "IT", "LI", "LT", "LU", "LV", "MC", "MT", "NL", "NO", "PL", "PT", "RO", "SE", "SI", "SK",
}


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.post("/api/extract")
async def extract_to_excel(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="Bitte mindestens eine PDF hochladen.")

    rows: list[dict[str, str]] = []
    diagnostics: list[dict[str, str | int | bool]] = []
    for upload in files:
        if not upload.filename.lower().endswith(".pdf"):
            continue

        content = await upload.read()
        text, extraction_meta = extract_pdf_text(content)
        rows.append(extract_transfer_data(text, upload.filename))
        diagnostics.append(build_diagnostics(text, upload.filename, extraction_meta))

    if not rows:
        raise HTTPException(status_code=400, detail="Keine PDF-Dateien erkannt.")

    output = build_excel(rows)
    with open("transfer_export.xlsx", "wb") as f:
        f.write(output.getvalue())

    return {
        "message": "Export erstellt.",
        "rows": rows,
        "download": "/download/transfer_export.xlsx",
        "diagnostics": diagnostics,
    }


@app.get("/download/transfer_export.xlsx")
async def download_file():
    return FileResponse(
        "transfer_export.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="transfer_export.xlsx",
    )


def extract_pdf_text(content: bytes) -> tuple[str, dict[str, str | int | bool]]:
    direct_text = extract_pdf_text_direct(content)
    direct_score = score_transfer_text(direct_text)
    if should_skip_ocr(direct_text, direct_score):
        return direct_text, {"used_ocr": False, "selected_source": "direct", "direct_score": direct_score, "ocr_score": 0}

    if os.getenv("OCR_ENABLED", "1") == "0":
        return direct_text, {"used_ocr": False, "selected_source": "direct", "direct_score": direct_score, "ocr_score": 0}

    ocr_text = extract_pdf_text_ocr(content)
    ocr_score = score_transfer_text(ocr_text)
    if ocr_score > direct_score:
        return ocr_text, {"used_ocr": True, "selected_source": "ocr", "direct_score": direct_score, "ocr_score": ocr_score}
    return direct_text, {"used_ocr": False, "selected_source": "direct", "direct_score": direct_score, "ocr_score": ocr_score}


def should_skip_ocr(direct_text: str, direct_score: int) -> bool:
    if len(direct_text.strip()) >= 180:
        return True
    return direct_score >= 18


def score_transfer_text(text: str) -> int:
    if not text.strip():
        return 0
    upper = text.upper()
    lower = text.lower()
    score = 0
    if BIC_REGEX.search(upper):
        score += 6
    if IBAN_REGEX.search(upper) or bool(find_iban_candidates(upper)):
        score += 10
    if any(label in lower for label in AMOUNT_LABELS):
        score += 5
    if AMOUNT_VALUE_REGEX.search(text):
        score += 3
    if any(label in lower for label in ACCOUNT_HOLDER_LABELS):
        score += 4
    return score


def extract_pdf_text_direct(content: bytes) -> str:
    try:
        reader = PdfReader(io.BytesIO(content))
        parts: list[str] = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        return "\n".join(parts)
    except Exception:
        return ""


def extract_pdf_text_ocr(content: bytes) -> str:
    tesseract_path = os.getenv("TESSERACT_CMD")
    if tesseract_path:
        pytesseract.pytesseract.tesseract_cmd = tesseract_path

    try:
        # Languages can be adjusted via env, e.g. OCR_LANGS=eng+deu+ita+fra+spa
        languages = os.getenv("OCR_LANGS", "eng+deu+ita+fra+spa")
        max_pages = int(os.getenv("OCR_MAX_PAGES", "2"))
        dpi = int(os.getenv("OCR_DPI", "170"))
        doc = fitz.open(stream=content, filetype="pdf")
        extracted_parts: list[str] = []
        for page_idx, page in enumerate(doc):
            if page_idx >= max_pages:
                break
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            text = pytesseract.image_to_string(img, lang=languages, config="--psm 6")
            if text:
                extracted_parts.append(text)
        return "\n".join(extracted_parts)
    except Exception:
        return ""


def extract_transfer_data(text: str, source: str) -> dict[str, str]:
    normalized = " ".join(text.split())
    lines = build_lines(text)
    normalized_upper = normalized.upper()
    normalized_lower = normalized.lower()
    is_credit_doc = (
        ("guthaben" in normalized_lower and "verwendungszweck" in normalized_lower)
        or "ihr guthaben" in normalized_lower
        or bool(re.search(r"\bguthaben\b.*\biban:\b.*\bverwendungszweck:\b", normalized_lower))
    )

    if is_credit_doc:
        credit = extract_credit_fields(text, lines)
        return {
            "Quelle": source,
            "Kontoinhaber": credit.get("Kontoinhaber", ""),
            "IBAN": credit.get("IBAN", ""),
            "BIC": credit.get("BIC", ""),
            "Betrag": credit.get("Betrag", ""),
            "Verwendungszweck": credit.get("Verwendungszweck", ""),
        }

    iban = extract_iban_for_credit(lines) if is_credit_doc else ""
    if not iban:
        iban = extract_iban(lines, normalized_upper)
    bic = extract_labeled_value(lines, BIC_LABELS, BIC_REGEX) or first_match(BIC_REGEX, normalized)
    amount_raw = extract_credit_amount(lines) if is_credit_doc else extract_amount(lines, normalized)
    amount = normalize_amount(amount_raw) if amount_raw else ""
    account_holder = infer_credit_account_holder(lines) if is_credit_doc else infer_account_holder(lines, iban, bic)
    purpose = extract_verwendungszweck(lines)

    return {
        "Quelle": source,
        "Kontoinhaber": account_holder,
        "IBAN": iban,
        "BIC": bic,
        "Betrag": amount,
        "Verwendungszweck": purpose,
    }


def extract_credit_fields(text: str, lines: list[str]) -> dict[str, str]:
    compact = " ".join(text.split())
    account_holder = extract_credit_account_holder_from_text(compact) or infer_credit_account_holder(lines)
    iban = extract_credit_iban_from_text(compact) or extract_iban_for_credit(lines)
    bic = extract_credit_bic_from_text(compact)
    amount = normalize_amount(extract_credit_amount_from_text(compact) or extract_credit_amount(lines))
    purpose = extract_credit_purpose_from_text(compact) or extract_verwendungszweck(lines)
    return {
        "Kontoinhaber": account_holder,
        "IBAN": iban,
        "BIC": bic,
        "Betrag": amount,
        "Verwendungszweck": purpose,
    }


def extract_credit_account_holder_from_text(compact: str) -> str:
    # Pattern from provided SOCCATOURS credit docs.
    match = re.search(r"SOCCATOURS Austria GmbH .*? Österreich\s*([A-Za-zÄÖÜäöüß \-]+?)\s*c/o\b", compact, flags=re.IGNORECASE)
    if match:
        candidate = sanitize_name(match.group(1))
        if candidate:
            return candidate
    # Fallback without explicit Austria marker.
    match = re.search(r"Österreich\s*([A-Za-zÄÖÜäöüß \-]+?)\s*c/o\b", compact, flags=re.IGNORECASE)
    if match:
        candidate = sanitize_name(match.group(1))
        if candidate:
            return candidate
    return ""


def extract_credit_iban_from_text(compact: str) -> str:
    # Prefer IBAN in refund section, not company bank list.
    iban_capture = r"([A-Z]{2}\s*[0-9]{2}(?:\s*[A-Z0-9]){11,30})"
    match = re.search(rf"Ihr Guthaben .*? zurück:\s*IBAN:\s*{iban_capture}", compact, flags=re.IGNORECASE)
    if not match:
        match = re.search(rf"Guthaben .*? IBAN:\s*{iban_capture}", compact, flags=re.IGNORECASE)
    if not match:
        match = re.search(rf"\bIBAN:\s*{iban_capture}", compact, flags=re.IGNORECASE)
    if not match:
        return ""
    raw = re.sub(r"[^A-Z0-9]", "", match.group(1).upper())
    if is_valid_iban(raw):
        return raw
    candidates = find_iban_candidates(raw)
    for candidate in candidates:
        if is_valid_iban(candidate):
            return candidate
    return ""


def extract_credit_bic_from_text(compact: str) -> str:
    # Credit docs: only accept BIC from the explicit refund block.
    match = re.search(
        r"Ihr Guthaben .*? zurück:\s*IBAN:\s*[A-Z0-9 ]{15,40}\s*BIC:\s*([A-Z0-9]{8,11})\b",
        compact,
        flags=re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    return ""


def extract_credit_bic_from_lines(lines: list[str]) -> str:
    section = get_credit_section(lines)
    for line in section:
        if not line.lower().startswith("bic"):
            continue
        match = re.search(r"\b([A-Z0-9]{8,11})\b", line.upper())
        if match:
            return match.group(1)
        return ""
    return ""


def extract_credit_amount_from_text(compact: str) -> str:
    match = re.search(r"\bGuthaben\b\D{0,30}([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2}|[0-9]+,[0-9]{2})\s*€?", compact, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"Guthaben\s*([0-9][0-9\.\,]+)\s*€", compact, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"\bIhr Kontostand\b.*?\bGuthaben\b\D{0,30}([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2}|[0-9]+,[0-9]{2})", compact, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return ""


def extract_credit_purpose_from_text(compact: str) -> str:
    match = re.search(
        r"Verwendungszweck:\s*(.*?)\s*(?:Voraussetzungen für einen reibungslosen Ablauf|Bitte achten Sie|$)",
        compact,
        flags=re.IGNORECASE,
    )
    if not match:
        return ""
    return match.group(1).strip()


def first_match(pattern: re.Pattern[str], text: str, group: int = 0) -> str:
    match = pattern.search(text)
    if not match:
        return ""
    value = match.group(group).replace(" ", "")
    return value.strip()


def extract_labeled_value(lines: list[str], labels: tuple[str, ...], value_pattern: re.Pattern[str]) -> str:
    for idx, line in enumerate(lines):
        lower = line.lower()
        if not any(label in lower for label in labels):
            continue

        inline_match = value_pattern.search(line.upper())
        if inline_match:
            return inline_match.group(0).replace(" ", "")

        if idx + 1 < len(lines):
            next_match = value_pattern.search(lines[idx + 1].upper())
            if next_match:
                return next_match.group(0).replace(" ", "")
    return ""


def extract_amount(lines: list[str], normalized: str) -> str:
    for idx, line in enumerate(lines):
        lower = line.lower()
        if any(word in lower for word in AMOUNT_NEGATIVE_CONTEXT_WORDS):
            continue
        if any(neg in lower for neg in AMOUNT_NEGATIVE_LABELS):
            continue
        if not any(label in lower for label in AMOUNT_LABELS):
            continue

        inline = AMOUNT_VALUE_REGEX.search(line)
        if inline:
            return inline.group(1)

        if idx + 1 < len(lines):
            next_line = AMOUNT_VALUE_REGEX.search(lines[idx + 1])
            if next_line:
                return next_line.group(1)

    # Fallback: pick the largest likely payable amount, avoid netto/subtotal lines.
    candidates: list[Decimal] = []
    for line in lines:
        lower = line.lower()
        if any(word in lower for word in AMOUNT_NEGATIVE_CONTEXT_WORDS):
            continue
        if any(neg in lower for neg in AMOUNT_NEGATIVE_LABELS):
            continue
        for match in AMOUNT_VALUE_REGEX.finditer(line):
            parsed = to_decimal(match.group(1))
            if parsed is not None:
                candidates.append(parsed)

    if not candidates:
        fallback_candidates: list[Decimal] = []
        for match in AMOUNT_VALUE_REGEX.finditer(normalized):
            parsed = to_decimal(match.group(1))
            if parsed is not None:
                fallback_candidates.append(parsed)
        candidates = fallback_candidates

    valid = [c for c in candidates if c is not None]
    if not valid:
        return ""
    return f"{max(valid):.2f}"


def extract_iban(lines: list[str], normalized_upper: str) -> str:
    labeled = extract_iban_from_labeled_lines(lines)
    if labeled and is_valid_iban(labeled):
        return labeled

    strict = first_match(IBAN_REGEX, normalized_upper)
    if strict and is_valid_iban(strict):
        return strict

    return ""


def extract_iban_from_labeled_lines(lines: list[str]) -> str:
    for idx, line in enumerate(lines):
        if "iban" not in line.lower():
            continue
        candidates = [line]
        if idx + 1 < len(lines):
            candidates.append(lines[idx + 1])
        for candidate_line in candidates:
            candidate_upper = candidate_line.upper()
            # Remove trailing text like BIC section if present.
            candidate_upper = re.split(r"\bBIC\b|\bSWIFT\b", candidate_upper)[0]
            matches = find_iban_candidates(candidate_upper)
            for candidate in matches:
                if is_valid_iban(candidate):
                    return candidate
    return ""


def extract_iban_for_credit(lines: list[str]) -> str:
    section = get_credit_section(lines)
    for line in section:
        if "iban" not in line.lower():
            continue
        candidate_text = re.split(r"\bBIC\b|\bVERWENDUNGSZWECK\b", line, flags=re.IGNORECASE)[0]
        matches = find_iban_candidates(candidate_text.upper())
        for candidate in matches:
            if is_valid_iban(candidate):
                return candidate
    return ""


def extract_credit_amount(lines: list[str]) -> str:
    section = get_credit_section(lines)
    for idx, line in enumerate(section):
        if "guthaben" not in line.lower():
            continue
        inline = EURO_AMOUNT_REGEX.search(line)
        if inline:
            return inline.group(1)
        if idx + 1 < len(section):
            nxt = EURO_AMOUNT_REGEX.search(section[idx + 1])
            if nxt:
                return nxt.group(1)
    return ""


def extract_verwendungszweck(lines: list[str]) -> str:
    section = get_credit_section(lines)
    for line in section:
        if line.lower().startswith("verwendungszweck"):
            for splitter in [":", "-", "|"]:
                if splitter in line:
                    return line.split(splitter, 1)[1].strip()
            return line.replace("Verwendungszweck", "").strip(" :")
    for line in section:
        lower = line.lower()
        if "verwendungszweck" not in lower:
            continue
        for splitter in [":", "-", "|"]:
            if splitter in line:
                return line.split(splitter, 1)[1].strip()
        return line
    return ""


def find_iban_candidates(text: str) -> list[str]:
    # OCR often breaks IBAN with extra separators; strip to alnum and scan.
    clean = re.sub(r"[^A-Z0-9]", "", text.upper())
    results: list[str] = []
    for idx in range(len(clean) - 14):
        if not clean[idx : idx + 2].isalpha() or not clean[idx + 2 : idx + 4].isdigit():
            continue
        for length in range(15, 35):
            end = idx + length
            if end > len(clean):
                break
            token = clean[idx:end]
            if token[:2].isalpha() and token[2:4].isdigit() and token[4:].isalnum():
                if 15 <= len(token) <= 34:
                    results.append(token)
    # Preserve order, remove duplicates.
    return list(dict.fromkeys(results))


def is_valid_iban(candidate: str) -> bool:
    iban = re.sub(r"[^A-Z0-9]", "", candidate.upper())
    if not (15 <= len(iban) <= 34):
        return False
    if not (iban[:2].isalpha() and iban[2:4].isdigit()):
        return False
    if iban[:2] not in VALID_IBAN_COUNTRY_CODES:
        return False
    rearranged = iban[4:] + iban[:4]
    converted = ""
    for ch in rearranged:
        if ch.isdigit():
            converted += ch
        else:
            converted += str(ord(ch) - 55)
    try:
        return int(converted) % 97 == 1
    except ValueError:
        return False


def normalize_amount(raw: str) -> str:
    value = to_decimal(raw)
    if value is None:
        return ""
    return f"{value:.2f}"


def to_decimal(raw: str) -> Decimal | None:
    compact = raw.replace(" ", "")
    if "." in compact and "," in compact:
        # Assume the last separator is decimal separator, remove the other as thousand separator.
        if compact.rfind(",") > compact.rfind("."):
            compact = compact.replace(".", "").replace(",", ".")
        else:
            compact = compact.replace(",", "")
    elif "," in compact:
        compact = compact.replace(",", ".")
    try:
        return Decimal(compact)
    except InvalidOperation:
        return None


def infer_account_holder(lines: list[str], iban: str, bic: str) -> str:
    strong_candidate = infer_from_strong_holder_labels(lines)
    if strong_candidate:
        return strong_candidate

    labeled_candidate = infer_from_holder_labels(lines)
    if labeled_candidate:
        return labeled_candidate

    bank_section_candidate = infer_from_bank_section(lines, iban, bic)
    if bank_section_candidate:
        return bank_section_candidate

    for idx, line in enumerate(lines):
        lower = line.lower()
        if any(label in lower for label in ACCOUNT_HOLDER_LABELS):
            candidate = extract_name_after_label(line)
            if candidate:
                return candidate
            for next_idx in range(idx + 1, min(idx + 4, len(lines))):
                candidate = sanitize_name(lines[next_idx])
                if candidate:
                    return candidate

    for idx, line in enumerate(lines):
        lower = line.lower()
        if "rechnung an" in lower or "bill to" in lower:
            if idx + 1 < len(lines):
                candidate = sanitize_name(lines[idx + 1])
                if candidate:
                    return candidate

    for line in lines[:12]:
        candidate = sanitize_name(line)
        if candidate:
            return candidate
    return ""


def infer_credit_account_holder(lines: list[str]) -> str:
    # In credit documents the club is usually in first-page address block:
    # after "SOCCATOURS Austria GmbH ..." and before booking details.
    skip_tokens = (
        "reiseveranstalter",
        "soccatours",
        "kontoinhaber",
        "volksbank",
        "raiffeisen",
        "kantonalbank",
        "buchungsbestätigung",
        "österreich",
        "schweiz",
    )
    cutoff = next((i for i, line in enumerate(lines) if "buchungsbestätigung" in line.lower()), min(len(lines), 40))
    scoped = lines[:cutoff]
    for idx, line in enumerate(scoped):
        lower = line.lower()
        if "soccatours austria gmbh" in lower:
            for look_ahead in range(idx + 1, min(len(scoped), idx + 10)):
                candidate = scoped[look_ahead].strip()
                clower = candidate.lower()
                if not candidate or any(token in clower for token in skip_tokens):
                    continue
                if clower.startswith("c/o"):
                    continue
                if any(char.isdigit() for char in candidate):
                    continue
                return candidate
    # Fallback to generic holder extraction.
    return infer_account_holder(lines, "", "")


def get_credit_section(lines: list[str]) -> list[str]:
    start = next((i for i, line in enumerate(lines) if "ihr guthaben" in line.lower() or line.lower().startswith("guthaben")), -1)
    if start == -1:
        start = next((i for i, line in enumerate(lines) if "guthaben" in line.lower()), 0)
    end = next(
        (
            i
            for i, line in enumerate(lines[start + 1 :], start + 1)
            if "voraussetzungen" in line.lower() or "buchungsbestätigung" in line.lower()
        ),
        min(len(lines), start + 30),
    )
    return lines[start:end]


def build_lines(text: str) -> list[str]:
    raw_parts = re.split(r"[\r\n|]+", text)
    lines: list[str] = []
    for part in raw_parts:
        chunk = part.strip()
        if not chunk:
            continue
        split_parts = LINE_SPLIT_MARKER_REGEX.split(chunk)
        for item in split_parts:
            candidate = item.strip()
            if candidate:
                lines.append(candidate)
    return lines


def infer_from_strong_holder_labels(lines: list[str]) -> str:
    for line in lines:
        lower = line.lower()
        if not any(label in lower for label in ACCOUNT_HOLDER_STRONG_LABELS):
            continue
        # Example: "Sede legale: BELLA ITALIA SPORT SRL Via ..."
        for splitter in [":", "-"]:
            if splitter in line:
                right = line.split(splitter, 1)[1].strip()
                right = re.split(r"\b(Via|Viale|Piazza|Strada|Street|Road)\b", right, maxsplit=1)[0].strip()
                candidate = sanitize_name(right)
                if candidate:
                    return candidate
    return ""


def infer_from_holder_labels(lines: list[str]) -> str:
    for idx, line in enumerate(lines):
        lower = line.lower()
        if any(label in lower for label in ACCOUNT_HOLDER_LABELS):
            inline = extract_name_after_label(line)
            if inline:
                return inline
            for next_idx in range(idx + 1, min(len(lines), idx + 4)):
                candidate = sanitize_name(lines[next_idx])
                if candidate:
                    return candidate
    return ""


def infer_from_bank_section(lines: list[str], iban: str, bic: str) -> str:
    anchor_idxs: list[int] = []
    for idx, line in enumerate(lines):
        upper = line.upper()
        if (iban and iban in upper.replace(" ", "")) or (bic and bic in upper.replace(" ", "")):
            anchor_idxs.append(idx)
        elif "IBAN" in upper or "SWIFT" in upper or "BIC" in upper:
            anchor_idxs.append(idx)

    for anchor in anchor_idxs:
        for idx in range(max(0, anchor - 3), min(len(lines), anchor + 4)):
            if idx == anchor:
                continue
            line = lines[idx]
            if any(label in line.lower() for label in ACCOUNT_HOLDER_LABELS):
                explicit = extract_name_after_label(line)
                if explicit:
                    return explicit
            candidate = sanitize_name(line)
            if candidate:
                return candidate
    return ""


def extract_name_after_label(line: str) -> str:
    splitters = [":", "-", "|"]
    for splitter in splitters:
        if splitter in line:
            right = line.split(splitter, 1)[1]
            candidate = sanitize_name(right)
            if candidate:
                return candidate
    return ""


def sanitize_name(value: str) -> str:
    candidate = value.strip(" :;-")
    if len(candidate) < 3:
        return ""
    if CURRENCY_REGEX.search(candidate):
        return ""
    if len(candidate.split()) > 8:
        return ""
    digit_count = sum(char.isdigit() for char in candidate)
    if digit_count > 2:
        return ""
    upper = candidate.upper()
    lower = candidate.lower()
    if any(word in lower for word in ACCOUNT_HOLDER_NEGATIVE_WORDS):
        return ""
    blocked_prefixes = (
        "IBAN",
        "BIC",
        "SWIFT",
        "BANCA",
        "BANCO",
        "BANQUE",
        "UST-ID",
        "VAT",
        "TAX",
        "INVOICE",
        "RECHNUNG",
        "AMOUNT",
        "TOTAL",
    )
    if upper.startswith(blocked_prefixes):
        return ""
    if "HTTP" in upper or "WWW." in upper or "@" in upper:
        return ""
    return candidate


def build_excel(rows: Iterable[dict[str, str]]) -> io.BytesIO:
    wb = Workbook()
    ws = wb.active
    ws.title = "Überweisungen"
    headers = ["Kontoinhaber", "IBAN", "BIC", "Betrag", "Verwendungszweck"]
    ws.append(headers)

    for row in rows:
        ws.append([row.get(header, "") for header in headers])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output


def build_diagnostics(text: str, source: str, extraction_meta: dict[str, str | int | bool]) -> dict[str, str | int | bool]:
    lines = build_lines(text)
    preview = " | ".join(lines[:12])[:600]
    return {
        "Quelle": source,
        "text_length": len(text),
        "line_count": len(lines),
        "contains_iban_pattern": bool(IBAN_REGEX.search(text.upper())),
        "contains_bic_pattern": bool(BIC_REGEX.search(text.upper())),
        "looks_like_scan_or_unreadable_text": len(text.strip()) < 40,
        "used_ocr": bool(extraction_meta.get("used_ocr", False)),
        "selected_source": str(extraction_meta.get("selected_source", "direct")),
        "direct_score": int(extraction_meta.get("direct_score", 0)),
        "ocr_score": int(extraction_meta.get("ocr_score", 0)),
        "text_preview": preview or "(kein auslesbarer Text gefunden)",
    }
