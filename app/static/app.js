const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const result = document.getElementById("result");
const downloadLink = document.getElementById("downloadLink");

let selectedFiles = [];

dropzone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => setFiles([...fileInput.files]));

dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("active");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("active");
});

dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("active");
  setFiles([...e.dataTransfer.files]);
});

uploadBtn.addEventListener("click", async () => {
  if (!selectedFiles.length) return;

  const formData = new FormData();
  selectedFiles.forEach((file) => formData.append("files", file));

  uploadBtn.disabled = true;
  uploadBtn.textContent = "Verarbeite...";
  result.textContent = "Rechnungen werden analysiert...";
  downloadLink.classList.add("hidden");

  try {
    const res = await fetch("/api/extract", { method: "POST", body: formData });
    const contentType = res.headers.get("content-type") || "";
    const isJson = contentType.includes("application/json");
    const data = isJson ? await res.json() : null;

    if (!res.ok) {
      const fallbackText = isJson ? "" : await res.text();
      const message =
        data?.detail ||
        (fallbackText ? `Serverfehler (${res.status}): ${fallbackText.slice(0, 180)}` : `Serverfehler (${res.status})`);
      throw new Error(message);
    }

    result.textContent = JSON.stringify(
      {
        extractedRows: data.rows,
        diagnostics: data.diagnostics || [],
      },
      null,
      2
    );
    downloadLink.href = data.download;
    downloadLink.classList.remove("hidden");
  } catch (err) {
    result.textContent = `Fehler: ${err.message}`;
  } finally {
    uploadBtn.disabled = false;
    uploadBtn.textContent = "Verarbeiten & Excel erstellen";
  }
});

function setFiles(files) {
  selectedFiles = files.filter((f) => f.name.toLowerCase().endsWith(".pdf"));
  uploadBtn.disabled = selectedFiles.length === 0;
  result.textContent = selectedFiles.length
    ? `Ausgewählt: ${selectedFiles.map((f) => f.name).join(", ")}`
    : "Keine gültigen PDF-Dateien ausgewählt.";
}
