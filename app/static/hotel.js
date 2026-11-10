/* Hotelbilder: Upload, Zuordnung zu Kategorien, Sortierung und ZIP-Export.
   Der Server bearbeitet jedes Bild und schickt es zurück; Zuordnung,
   Dateinamen und ZIP entstehen hier im Browser. Auf dem Server wird nichts
   gespeichert. */

/* Kategorien mit festen Nummernkreisen (Basis = erste Nummer). */
const CATS = [
  { id: 1, base: 10, name: "Außenansicht und Lage" },
  { id: 2, base: 20, name: "Hotel innen (Restaurant, Buffet, Lobby)" },
  { id: 3, base: 30, name: "Zimmer" },
  { id: 4, base: 40, name: "Sportstätte" },
  { id: 5, base: 50, name: "Meeting, Fitness, Regeneration" },
  { id: 6, base: 60, name: "Freizeit und Teambuilding" },
  { id: 7, base: 70, name: "Umgebung und Destination" },
];
const MAX_PER_CAT = 10;
const POOL = 0;

const IMAGE_EXTENSIONS = (document.body.dataset.ext || "").split(",").filter(Boolean);
const MIN_PIXELS = Number(document.body.dataset.minPixels || 0).toLocaleString("de-DE");

const $ = (id) => document.getElementById(id);
const hotelInput = $("hotelName");
const brandBox = $("brands");
const dropzone = $("dropzone");
const fileInput = $("fileInput");
const exportBtn = $("exportBtn");
const resetBtn = $("resetBtn");

/* ------------------------------------------------------------ Zustand */
const state = {
  brand: null,
  locked: false,
  prefix: null,
  busy: false,
  queue: [],
  done: 0,
  total: 0,
};
const items = new Map(); // id -> {id, source, full: Blob, fullUrl, thumbUrl, el}
const lists = { 0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: [], 7: [] };
let nextId = 1;

const catById = (id) => CATS.find((c) => c.id === id);
const rangeLabel = (c) => `${pad3(c.base)}–${pad3(c.base + MAX_PER_CAT - 1)}`;
const pad3 = (n) => String(n).padStart(3, "0");

function catOf(id) {
  for (const k of Object.keys(lists)) if (lists[k].includes(id)) return Number(k);
  return null;
}

function fileNameOf(id) {
  const cat = catOf(id);
  if (!cat) return null;
  const c = catById(cat);
  return `${state.prefix}_${pad3(c.base + lists[cat].indexOf(id))}.jpg`;
}

/* ------------------------------------------------------------ Hotel und Brand */
brandBox.addEventListener("click", (e) => {
  const b = e.target.closest("[data-brand]");
  if (!b || state.locked) return;
  state.brand = b.dataset.brand;
  brandBox.querySelectorAll("[data-brand]").forEach((x) =>
    x.setAttribute("aria-pressed", String(x === b))
  );
  updateUploadState();
});
hotelInput.addEventListener("input", updateUploadState);

function ready() {
  return Boolean(hotelInput.value.trim() && state.brand);
}

function setLocked(on) {
  state.locked = on;
  hotelInput.disabled = on;
  brandBox.querySelectorAll("[data-brand]").forEach((b) => (b.disabled = on));
  resetBtn.hidden = !on;
}

function updateUploadState() {
  const ok = ready();
  dropzone.classList.toggle("locked", !ok);
  dropzone.setAttribute("aria-disabled", String(!ok));
}

/* ------------------------------------------------------------ Upload */
dropzone.addEventListener("click", () => openPicker());
dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    openPicker();
  }
});
fileInput.setAttribute("accept", ["image/*", ...IMAGE_EXTENSIONS, ".zip", "application/zip"].join(","));
fileInput.addEventListener("change", () => {
  addFiles([...fileInput.files]);
  fileInput.value = "";
});

const hasFiles = (e) => [...(e.dataTransfer?.types || [])].includes("Files");
dropzone.addEventListener("dragover", (e) => {
  if (!hasFiles(e)) return;
  e.preventDefault();
  dropzone.classList.add("active");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("active"));
dropzone.addEventListener("drop", (e) => {
  if (!hasFiles(e)) return;
  e.preventDefault();
  dropzone.classList.remove("active");
  addFiles([...e.dataTransfer.files]);
});
/* Dateien, die neben die Fläche fallen, soll der Browser nicht öffnen. */
window.addEventListener("dragover", (e) => hasFiles(e) && e.preventDefault());
window.addEventListener("drop", (e) => hasFiles(e) && e.preventDefault());

function openPicker() {
  if (!ready()) {
    toast("Bitte zuerst Hotelname und Brand angeben.");
    (hotelInput.value.trim() ? brandBox.querySelector("button") : hotelInput).focus();
    return;
  }
  fileInput.click();
}

function isSupported(file) {
  const name = (file.name || "").toLowerCase();
  const type = (file.type || "").toLowerCase();
  return (
    type.startsWith("image/") ||
    name.endsWith(".zip") ||
    type === "application/zip" ||
    type === "application/x-zip-compressed" ||
    IMAGE_EXTENSIONS.some((ext) => name.endsWith(ext))
  );
}

function addFiles(files) {
  if (!files.length) return;
  if (!ready()) {
    toast("Bitte zuerst Hotelname und Brand angeben.");
    return;
  }
  const accepted = files.filter(isSupported);
  files
    .filter((f) => !isSupported(f))
    .forEach((f) => addMessage(f.name, "kein Bild und keine ZIP-Datei"));
  if (!accepted.length) return;

  setLocked(true);
  state.queue.push(...accepted);
  state.total += accepted.length;
  if (!state.busy) runQueue();
  render();
}

async function runQueue() {
  state.busy = true;
  $("progress").hidden = false;
  while (state.queue.length) {
    const file = state.queue.shift();
    showProgress(file.name);
    try {
      await processFile(file);
    } catch (err) {
      addMessage(file.name, err.message || "Verarbeitung fehlgeschlagen");
    }
    state.done++;
    render();
  }
  state.busy = false;
  state.done = 0;
  state.total = 0;
  $("progress").hidden = true;
  render();
}

function showProgress(name) {
  $("progressText").textContent = `Bearbeite ${state.done + 1} von ${state.total}: ${name}`;
  $("progressBar").style.width = `${(state.done / Math.max(state.total, 1)) * 100}%`;
}

async function processFile(file) {
  const fd = new FormData();
  fd.append("hotel_name", hotelInput.value.trim());
  fd.append("brand", state.brand);
  fd.append("file", file);

  const res = await fetch("/api/process", { method: "POST", body: fd });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail = typeof data.detail === "string" ? data.detail : `Fehler ${res.status}`;
    throw new Error(detail);
  }

  state.prefix = state.prefix || data.prefix;
  for (const img of data.images || []) {
    const id = nextId++;
    const full = b64ToBlob(img.data);
    items.set(id, {
      id,
      source: img.source,
      full,
      fullUrl: URL.createObjectURL(full),
      thumbUrl: URL.createObjectURL(b64ToBlob(img.thumb)),
      el: null,
    });
    lists[POOL].push(id);
  }
  (data.skipped || []).forEach((n) => addMessage(n, `übersprungen, weniger als ${MIN_PIXELS} Pixel`));
  (data.failed || []).forEach((f) => addMessage(f.source, f.error));
}

function b64ToBlob(b64) {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return new Blob([bytes], { type: "image/jpeg" });
}

function addMessage(name, text) {
  const ul = $("messages");
  const li = document.createElement("li");
  const b = document.createElement("b");
  b.textContent = name;
  li.append(b, `: ${text}`);
  ul.append(li);
  ul.hidden = false;
}

/* ------------------------------------------------------------ Verschieben und Entfernen */
function move(id, toCat, index) {
  const from = catOf(id);
  if (from === null) return false;
  if (toCat !== from && toCat !== POOL && lists[toCat].length >= MAX_PER_CAT) {
    toast(`„${catById(toCat).name}“ ist voll (${MAX_PER_CAT} Bilder).`);
    return false;
  }
  const oldIdx = lists[from].indexOf(id);
  lists[from].splice(oldIdx, 1);
  let idx = index === undefined ? lists[toCat].length : index;
  if (from === toCat && oldIdx < idx) idx--;
  idx = Math.max(0, Math.min(idx, lists[toCat].length));
  lists[toCat].splice(idx, 0, id);
  render();
  return true;
}

let undo = null; // {id, cat, idx, timer}
function remove(id) {
  finalizeUndo();
  const cat = catOf(id);
  const idx = lists[cat].indexOf(id);
  lists[cat].splice(idx, 1);
  undo = { id, cat, idx, timer: setTimeout(finalizeUndo, 6000) };
  render();
  toast("Bild entfernt.", () => {
    if (!undo) return;
    const { id: uid, cat: ucat, idx: uidx } = undo;
    clearTimeout(undo.timer);
    undo = null;
    const target = ucat !== POOL && lists[ucat].length >= MAX_PER_CAT ? POOL : ucat;
    lists[target].splice(Math.min(uidx, lists[target].length), 0, uid);
    render();
  });
}

function finalizeUndo() {
  if (!undo) return;
  clearTimeout(undo.timer);
  dropItem(undo.id);
  undo = null;
}

function dropItem(id) {
  const it = items.get(id);
  if (!it) return;
  URL.revokeObjectURL(it.fullUrl);
  URL.revokeObjectURL(it.thumbUrl);
  it.el?.remove();
  items.delete(id);
}

/* ------------------------------------------------------------ Bildkarten */
const categoryOptions = [
  `<option value="0">Nicht zugeordnet</option>`,
  ...CATS.map((c) => `<option value="${c.id}">${rangeLabel(c)} ${escapeHtml(c.name)}</option>`),
].join("");

function cardFor(item) {
  if (item.el) return item.el;
  const el = document.createElement("div");
  el.className = "thumb";
  el.draggable = true;
  el.dataset.id = item.id;
  el.innerHTML = `
    <img class="img" alt="" loading="lazy" draggable="false">
    <div class="name"></div>
    <div class="src"></div>
    <div class="row">
      <select aria-label="Kategorie">${categoryOptions}</select>
      <button type="button" class="ib" data-act="left" aria-label="Eine Position nach vorne" title="Nach vorne">◀</button>
      <button type="button" class="ib" data-act="right" aria-label="Eine Position nach hinten" title="Nach hinten">▶</button>
      <button type="button" class="ib del" data-act="del" aria-label="Bild entfernen" title="Entfernen">✕</button>
    </div>`;
  const img = el.querySelector("img");
  img.src = item.thumbUrl;
  img.alt = item.source;
  const src = el.querySelector(".src");
  src.textContent = item.source;
  src.title = item.source;

  img.addEventListener("click", () => openViewer(item.id));
  el.querySelector("select").addEventListener("change", (e) => {
    if (!move(item.id, Number(e.target.value))) render();
  });
  el.querySelector(".row").addEventListener("click", (e) => {
    const act = e.target.closest("[data-act]")?.dataset.act;
    if (!act) return;
    const cat = catOf(item.id);
    const idx = lists[cat].indexOf(item.id);
    if (act === "left") move(item.id, cat, idx - 1);
    if (act === "right") move(item.id, cat, idx + 2);
    if (act === "del") remove(item.id);
  });
  el.addEventListener("dragstart", (e) => {
    drag.id = item.id;
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", String(item.id));
    requestAnimationFrame(() => el.classList.add("dragging"));
  });
  el.addEventListener("dragend", () => {
    drag.id = null;
    el.classList.remove("dragging");
    clearDropMarks();
  });
  item.el = el;
  return el;
}

function updateCard(item, cat, idx, len) {
  const el = item.el;
  const name = el.querySelector(".name");
  const fn = cat ? fileNameOf(item.id) : null;
  if (fn) {
    // Nummer hervorheben, Rest als normaler Text (Hotelname kann Sonderzeichen enthalten)
    const m = fn.match(/^(.*_)(\d{3})(\.jpg)$/);
    const b = document.createElement("b");
    b.textContent = m[2];
    // Umbruch nur nach Unterstrichen erlauben, nicht mitten im Wort
    const nodes = [];
    for (const part of m[1].split(/(?<=_)/)) nodes.push(part, document.createElement("wbr"));
    name.replaceChildren(...nodes, b, m[3]);
  } else {
    name.textContent = "Noch nicht zugeordnet";
  }
  name.classList.toggle("open", !fn);
  const sel = el.querySelector("select");
  sel.value = String(cat);
  [...sel.options].forEach((o) => {
    const v = Number(o.value);
    o.disabled = v !== cat && v !== POOL && lists[v].length >= MAX_PER_CAT;
  });
  el.classList.toggle("in-pool", cat === POOL);
  const left = el.querySelector('[data-act="left"]');
  const right = el.querySelector('[data-act="right"]');
  left.hidden = right.hidden = cat === POOL;
  left.disabled = idx === 0;
  right.disabled = idx === len - 1;
}

/* ------------------------------------------------------------ Drag & Drop zwischen den Bereichen */
const drag = { id: null, cat: null, before: null };

function clearDropMarks() {
  document.querySelectorAll(".grid.over, .grid.reject").forEach((g) => g.classList.remove("over", "reject"));
  document.querySelectorAll(".drop-before, .drop-after").forEach((c) => c.classList.remove("drop-before", "drop-after"));
}

/* Nächste Karte zum Mauszeiger, auch wenn er in einer Lücke steht. */
function nearestCard(grid, x, y) {
  let best = null;
  let bestD = Infinity;
  for (const card of grid.querySelectorAll(".thumb")) {
    if (Number(card.dataset.id) === drag.id) continue;
    const r = card.getBoundingClientRect();
    const dx = x < r.left ? r.left - x : x > r.right ? x - r.right : 0;
    const dy = y < r.top ? r.top - y : y > r.bottom ? y - r.bottom : 0;
    const d = dx * dx + dy * dy;
    if (d < bestD) {
      bestD = d;
      best = card;
    }
  }
  return best;
}

let lastReject = null;
function bindGrid(grid) {
  const cat = Number(grid.dataset.cat);
  grid.addEventListener("dragover", (e) => {
    if (drag.id === null) return;
    const from = catOf(drag.id);
    if (cat !== from && cat !== POOL && lists[cat].length >= MAX_PER_CAT) {
      grid.classList.add("reject");
      if (lastReject !== cat) {
        lastReject = cat;
        toast(`„${catById(cat).name}“ ist voll (${MAX_PER_CAT} Bilder).`);
      }
      return;
    }
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    document.querySelectorAll(".drop-before, .drop-after").forEach((c) => c.classList.remove("drop-before", "drop-after"));
    grid.classList.add("over");
    const card = nearestCard(grid, e.clientX, e.clientY);
    drag.cat = cat;
    drag.target = card ? Number(card.dataset.id) : null;
    if (card) {
      const r = card.getBoundingClientRect();
      drag.before = e.clientX < r.left + r.width / 2;
      card.classList.add(drag.before ? "drop-before" : "drop-after");
    }
  });
  grid.addEventListener("dragleave", (e) => {
    if (grid.contains(e.relatedTarget)) return;
    grid.classList.remove("over", "reject");
    grid.querySelectorAll(".drop-before, .drop-after").forEach((c) => c.classList.remove("drop-before", "drop-after"));
    lastReject = null;
  });
  grid.addEventListener("drop", (e) => {
    if (drag.id === null) return;
    e.preventDefault();
    let idx;
    if (drag.target !== null && drag.cat === cat) {
      idx = lists[cat].indexOf(drag.target) + (drag.before ? 0 : 1);
    }
    const id = drag.id;
    clearDropMarks();
    move(id, cat, idx);
  });
}

/* ------------------------------------------------------------ Aufbau der Kategorien */
function buildCategories() {
  $("cats").innerHTML = CATS.map(
    (c) => `
    <div class="cat" id="cat-${c.id}">
      <div class="cat-head">
        <span class="cat-range">${rangeLabel(c)}</span>
        <h3>${escapeHtml(c.name)}</h3>
        <span class="cat-count" id="count-${c.id}"></span>
      </div>
      <div class="grid" data-cat="${c.id}" aria-label="${escapeHtml(c.name)}"></div>
    </div>`
  ).join("");
  document.querySelectorAll(".grid[data-cat]").forEach(bindGrid);
}

/* ------------------------------------------------------------ Darstellung */
function render() {
  const total = Object.values(lists).reduce((s, l) => s + l.length, 0);
  const open = lists[POOL].length;
  const hasItems = total > 0;

  $("s-pool").hidden = !hasItems && !state.busy;
  $("s-cats").hidden = !hasItems && !state.busy;

  for (const key of Object.keys(lists)) {
    const cat = Number(key);
    const grid = document.querySelector(`.grid[data-cat="${cat}"]`);
    const list = lists[cat];
    list.forEach((id, idx) => {
      const item = items.get(id);
      const el = cardFor(item);
      if (grid.children[idx] !== el) grid.insertBefore(el, grid.children[idx] || null);
      updateCard(item, cat, idx, list.length);
    });
    // Alles hinter der Liste (verschobene Karten sind schon umgezogen) und Leerhinweise entfernen
    while (grid.children.length > list.length) grid.lastChild.remove();
    if (!list.length) {
      const p = document.createElement("p");
      p.className = "empty";
      p.textContent =
        cat === POOL
          ? state.busy
            ? "Bilder werden bearbeitet …"
            : "Alle Bilder sind zugeordnet."
          : "Bilder hierher ziehen";
      grid.append(p);
    }
    if (cat !== POOL) {
      const cnt = $(`count-${cat}`);
      cnt.textContent = `${list.length} / ${MAX_PER_CAT}`;
      cnt.classList.toggle("full", list.length >= MAX_PER_CAT);
    }
  }

  $("poolHint").textContent = open
    ? `${open} ${open === 1 ? "Bild wartet" : "Bilder warten"} auf eine Kategorie.`
    : "";

  const capacity = CATS.length * MAX_PER_CAT;
  const parts = [];
  if (hasItems) {
    parts.push(`<b>${total}</b> ${total === 1 ? "Bild" : "Bilder"}`);
    parts.push(open ? `<b>${open}</b> nicht zugeordnet` : "alle zugeordnet");
    if (total > capacity) parts.push(`<span class="warn">${total - capacity} zu viel, höchstens ${capacity}</span>`);
  }
  $("summary").innerHTML = parts.join(" · ");

  const canExport = hasItems && !open && !state.busy;
  exportBtn.disabled = !canExport;
  exportBtn.title = canExport
    ? ""
    : !hasItems
    ? "Noch keine Bilder hochgeladen."
    : state.busy
    ? "Bitte warten, bis alle Bilder bearbeitet sind."
    : "Erst alle Bilder einer Kategorie zuordnen.";
  resetBtn.disabled = state.busy;
}

/* ------------------------------------------------------------ Export */
exportBtn.addEventListener("click", async () => {
  if (exportBtn.disabled) return;
  finalizeUndo();
  exportBtn.disabled = true;
  try {
    const files = [];
    for (const c of CATS) {
      for (const id of lists[c.id]) {
        files.push({
          name: fileNameOf(id),
          data: new Uint8Array(await items.get(id).full.arrayBuffer()),
        });
      }
    }
    const blob = window.SoccaZip.buildZip(files);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${state.prefix}.zip`;
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
    toast(`${state.prefix}.zip mit ${files.length} ${files.length === 1 ? "Bild" : "Bildern"} heruntergeladen.`);
  } catch (err) {
    toast(`ZIP konnte nicht erstellt werden: ${err.message}`);
  } finally {
    render();
  }
});

/* ------------------------------------------------------------ Neu beginnen */
resetBtn.addEventListener("click", () => {
  if (state.busy) return;
  if (items.size && !confirm("Alle Bilder und die Sortierung verwerfen und neu beginnen?")) return;
  finalizeUndo();
  for (const id of [...items.keys()]) dropItem(id);
  Object.keys(lists).forEach((k) => (lists[k] = []));
  state.prefix = null;
  $("messages").innerHTML = "";
  $("messages").hidden = true;
  setLocked(false);
  render();
});

window.addEventListener("beforeunload", (e) => {
  if (!items.size) return;
  e.preventDefault();
  e.returnValue = "";
});

/* ------------------------------------------------------------ Großansicht */
const viewer = $("viewer");
function openViewer(id) {
  const it = items.get(id);
  $("viewerImg").src = it.fullUrl;
  $("viewerImg").alt = it.source;
  $("viewerName").textContent = fileNameOf(id) || it.source;
  viewer.showModal();
}
$("viewerClose").addEventListener("click", () => viewer.close());
viewer.addEventListener("click", (e) => {
  if (e.target === viewer) viewer.close();
});

/* ------------------------------------------------------------ Hinweis unten */
let toastTimer = null;
function toast(text, onUndo) {
  $("toastText").textContent = text;
  const btn = $("toastUndo");
  btn.hidden = !onUndo;
  btn.onclick = onUndo
    ? () => {
        onUndo();
        $("toast").hidden = true;
      }
    : null;
  $("toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => ($("toast").hidden = true), onUndo ? 6000 : 3500);
}

/* ------------------------------------------------------------ Hell/Dunkel wie im Cockpit */
const themeBtn = $("themeBtn");
function isDark() {
  const t = document.documentElement.getAttribute("data-theme");
  return t ? t === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
}
function syncTheme() {
  themeBtn.textContent = isDark() ? "Hell" : "Dunkel";
  themeBtn.setAttribute("aria-pressed", String(isDark()));
}
themeBtn.addEventListener("click", () => {
  document.documentElement.setAttribute("data-theme", isDark() ? "light" : "dark");
  syncTheme();
});

function escapeHtml(text) {
  return String(text).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

/* ------------------------------------------------------------ Start */
buildCategories();
syncTheme();
updateUploadState();
render();
