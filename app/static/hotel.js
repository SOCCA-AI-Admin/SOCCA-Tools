const form = document.getElementById("hotelForm");
const hotelName = document.getElementById("hotelName");
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const fileList = document.getElementById("fileList");
const submitBtn = document.getElementById("submitBtn");
const statusEl = document.getElementById("status");
const MIN_PIXEL_COUNT = 480000;
const IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff", ".gif"];

let selectedFiles = [];

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    fileInput.click();
  }
});

fileInput.addEventListener("change", () => addFiles([...fileInput.files]));

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("active");
});

dropzone.addEventListener("dragleave", () => dropzone.classList.remove("active"));

dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("active");
  addFiles([...e.dataTransfer.files]);
});

hotelName.addEventListener("input", updateSubmitState);
form.addEventListener("change", (e) => {
  if (e.target.name === "brand") updateSubmitState();
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!canSubmit()) return;

  const validation = await splitByPixelSize(selectedFiles);
  const validFiles = validation.validFiles;
  const tooSmallFiles = validation.tooSmallFiles;
  if (!validFiles.length) {
    setStatus(
      `Keine ZIP erstellt. Alle Dateien sind kleiner als ${MIN_PIXEL_COUNT} Pixel: ${tooSmallFiles.join(", ")}`,
      "error"
    );
    return;
  }

  const brand = form.querySelector('input[name="brand"]:checked');
  const formData = new FormData();
  formData.append("hotel_name", hotelName.value.trim());
  formData.append("brand", brand.value);
  validFiles.forEach((file) => formData.append("files", file));

  submitBtn.disabled = true;
  submitBtn.textContent = "Verarbeite …";
  setStatus("Bilder werden bearbeitet …", "info");

  try {
    const response = await fetch("/api/process", { method: "POST", body: formData });
    if (!response.ok) {
      let message = `Fehler (${response.status})`;
      try {
        const data = await response.json();
        if (data.detail) {
          message = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
        }
      } catch {
        const text = await response.text();
        if (text) message = text.slice(0, 200);
      }
      throw new Error(message);
    }

    const blob = await response.blob();
    const disposition = response.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^";]+)"?/i);
    const filename = match ? match[1] : "hotel_bilder.zip";
    const skippedFilesHeader = response.headers.get("X-Skipped-Files");
    const skippedCountHeader = response.headers.get("X-Skipped-Count");

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);

    const serverSkipped = parseServerSkipped(skippedFilesHeader, skippedCountHeader);
    const allSkipped = [...tooSmallFiles, ...serverSkipped];

    if (allSkipped.length) {
      const uniqueSkipped = [...new Set(allSkipped)];
      const skippedNames = skippedFilesHeader
        ? uniqueSkipped.join(", ")
        : uniqueSkipped.join(", ");
      setStatus(
        `ZIP erstellt (${filename}). Übersprungen (<${MIN_PIXEL_COUNT} Pixel): ${skippedNames}`,
        "error"
      );
    } else {
      setStatus(`Fertig – ${validFiles.length} Bild(er) als ${filename} heruntergeladen.`, "success");
    }
  } catch (err) {
    setStatus(err.message || "Unbekannter Fehler", "error");
  } finally {
    updateSubmitState();
    submitBtn.textContent = "Bilder bearbeiten & ZIP laden";
  }
});

function addFiles(files) {
  const accepted = files.filter((f) => isSupportedInputFile(f));
  if (!accepted.length) {
    setStatus("Keine gültigen Dateien erkannt (Bilder oder ZIP).", "error");
    return;
  }

  const existingKeys = new Set(selectedFiles.map(fileKey));
  for (const file of accepted) {
    const key = fileKey(file);
    if (!existingKeys.has(key)) {
      selectedFiles.push(file);
      existingKeys.add(key);
    }
  }

  renderFileList();
  updateSubmitState();
  setStatus(`${selectedFiles.length} Bild(er) bereit.`, "info");
}

function fileKey(file) {
  return `${file.name}-${file.size}-${file.lastModified}`;
}

function renderFileList() {
  if (!selectedFiles.length) {
    fileList.hidden = true;
    fileList.innerHTML = "";
    return;
  }

  fileList.hidden = false;
  fileList.innerHTML = selectedFiles.map((f) => `<li>${escapeHtml(f.name)}</li>`).join("");
}

function getSelectedBrand() {
  return form.querySelector('input[name="brand"]:checked');
}

function canSubmit() {
  return Boolean(hotelName.value.trim() && getSelectedBrand() && selectedFiles.length);
}

function updateSubmitState() {
  submitBtn.disabled = !canSubmit();
}

function setStatus(message, type) {
  statusEl.textContent = message;
  statusEl.className = `status ${type || "info"}`;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function parseServerSkipped(skippedFilesHeader, skippedCountHeader) {
  if (skippedFilesHeader) {
    return skippedFilesHeader
      .split("|")
      .filter(Boolean)
      .map((value) => {
        try {
          return decodeURIComponent(value);
        } catch {
          return value;
        }
      });
  }
  if (skippedCountHeader) {
    return [`${skippedCountHeader} Datei(en)`];
  }
  return [];
}

async function splitByPixelSize(files) {
  const validFiles = [];
  const tooSmallFiles = [];

  for (const file of files) {
    if (isZipFile(file)) {
      validFiles.push(file);
      continue;
    }
    try {
      const pixels = await getPixelCount(file);
      if (pixels < MIN_PIXEL_COUNT) {
        tooSmallFiles.push(file.name);
      } else {
        validFiles.push(file);
      }
    } catch {
      // If dimensions cannot be read in browser, let backend validate.
      validFiles.push(file);
    }
  }

  return { validFiles, tooSmallFiles };
}

function getPixelCount(file) {
  return new Promise((resolve, reject) => {
    const objectUrl = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const pixels = img.naturalWidth * img.naturalHeight;
      URL.revokeObjectURL(objectUrl);
      resolve(pixels);
    };
    img.onerror = () => {
      URL.revokeObjectURL(objectUrl);
      reject(new Error("Bildgröße konnte nicht gelesen werden"));
    };
    img.src = objectUrl;
  });
}

function isZipFile(file) {
  const name = (file.name || "").toLowerCase();
  return (
    name.endsWith(".zip") ||
    file.type === "application/zip" ||
    file.type === "application/x-zip-compressed"
  );
}

function hasImageExtension(file) {
  const name = (file.name || "").toLowerCase();
  return IMAGE_EXTENSIONS.some((ext) => name.endsWith(ext));
}

function isSupportedInputFile(file) {
  return file.type.startsWith("image/") || hasImageExtension(file) || isZipFile(file);
}

updateSubmitState();
