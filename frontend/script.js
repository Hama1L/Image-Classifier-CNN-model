const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const preview = document.getElementById("preview");
const hint = document.getElementById("hint");
const sweep = document.getElementById("sweep");
const status = document.getElementById("status");
const results = document.getElementById("results");

dropzone.setAttribute("tabindex", "0");
dropzone.setAttribute("role", "button");
dropzone.setAttribute("aria-label", "Upload an image to classify");

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("keydown", (e) => {
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault();
    fileInput.click();
  }
});

["dragenter", "dragover"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  })
);

["dragleave", "drop"].forEach((evt) =>
  dropzone.addEventListener(evt, (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
  })
);

dropzone.addEventListener("drop", (e) => {
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) handleFile(fileInput.files[0]);
});

function handleFile(file) {
  const allowed = ["image/jpeg", "image/png", "image/webp"];
  if (!allowed.includes(file.type)) {
    setStatus("error", "Unsupported file");
    renderError("Please choose a JPEG, PNG, or WEBP image.");
    return;
  }

  preview.src = URL.createObjectURL(file);
  preview.hidden = false;
  hint.hidden = true;

  classify(file);
}

async function classify(file) {
  setStatus("scanning", "Scanning");
  sweep.classList.add("active");
  results.innerHTML = "";

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/predict", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Something went wrong.");
    }

    renderResults(data.predictions);
    setStatus("done", "Complete");
  } catch (err) {
    renderError(err.message || "Could not reach the classifier.");
    setStatus("error", "Failed");
  } finally {
    sweep.classList.remove("active");
  }
}

function renderResults(predictions) {
  results.innerHTML = "";

  predictions.forEach((p, i) => {
    const pct = Math.round(p.confidence * 100);

    const row = document.createElement("div");
    row.className = "result-row";
    row.innerHTML = `
      <div class="result-label-line">
        <span><span class="result-rank">0${i + 1}</span><span class="result-label">${escapeHtml(p.label)}</span></span>
        <span class="result-value">${pct}%</span>
      </div>
      <div class="gauge"><div class="gauge-fill" style="width: ${pct}%"></div></div>
    `;
    results.appendChild(row);
  });
}

function renderError(message) {
  results.innerHTML = `<p class="error-message">${escapeHtml(message)}</p>`;
}

function setStatus(kind, label) {
  status.textContent = label;
  status.className = `readout-status ${kind}`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
