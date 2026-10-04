const home = document.querySelector("#home");
const ultratech = document.querySelector("#ultratech");
const accLalan = document.querySelector("#acc-lalan");
const accShila = document.querySelector("#acc-shila");
const dalmiaLalan = document.querySelector("#dalmia-lalan");
const dalmiaShila = document.querySelector("#dalmia-shila");
const billList = document.querySelector("#bill-list");
const homeError = document.querySelector("#home-error");
const form = document.querySelector("#ultratech-form");
const dateInput = document.querySelector("#invoice-date");
const billingMonth = document.querySelector("#billing-month");
const invoiceNumber = document.querySelector("#invoice-number");
const billPeriod = document.querySelector("#bill-period");
const formError = document.querySelector("#form-error");
const formStatus = document.querySelector("#form-status");
const generateBtn = document.querySelector("#generate-btn");
const downloadBtn = document.querySelector("#download-btn");

let busy = false;
let downloadUrl = "";
let downloadName = "UltraTech_Invoice.pdf";
let previewRequest = 0;

document.querySelector("#back-home").addEventListener("click", () => {
  showHome();
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  generatePdf();
});

downloadBtn.addEventListener("click", () => {
  if (!downloadUrl) return;
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = downloadName;
  document.body.appendChild(link);
  link.click();
  link.remove();
});

dateInput.addEventListener("input", () => refreshPreview());
dateInput.addEventListener("change", () => refreshPreview());

loadBills();
loadDateLimits();

function showHome() {
  ultratech.hidden = true;
  accLalan.hidden = true;
  accShila.hidden = true;
  dalmiaLalan.hidden = true;
  dalmiaShila.hidden = true;
  home.hidden = false;
}

function showUltratech() {
  home.hidden = true;
  accLalan.hidden = true;
  accShila.hidden = true;
  dalmiaLalan.hidden = true;
  dalmiaShila.hidden = true;
  ultratech.hidden = false;
  dateInput.focus();
}

async function loadBills() {
  homeError.hidden = true;
  try {
    const response = await fetch("/api/bills");
    if (!response.ok) throw new Error("bills");
    const bills = await response.json();
    billList.replaceChildren();
    bills.forEach((bill) => {
      const card = document.createElement(bill.available ? "button" : "div");
      card.className = bill.available ? "card" : "card is-disabled";
      if (!bill.available) card.setAttribute("aria-disabled", "true");
      if (bill.available) card.type = "button";
      card.innerHTML = `
        <span class="kicker">${bill.available ? "Active" : "Coming soon"}</span>
        <span class="card-title"></span>
      `;
      card.querySelector(".card-title").textContent = bill.name;
      if (bill.available && bill.id === "ultratech") {
        card.addEventListener("click", showUltratech);
      }
      if (bill.available && bill.id === "acc-lalan") {
        card.addEventListener("click", () => showAcc(accLalan, accLalanDate));
      }
      if (bill.available && bill.id === "acc-shila") {
        card.addEventListener("click", () => showAcc(accShila, accShilaDate));
      }
      if (bill.available && bill.id === "dalmia-lalan") {
        card.addEventListener("click", () => showAcc(dalmiaLalan, dalmiaLalanDate));
      }
      if (bill.available && bill.id === "dalmia-shila") {
        card.addEventListener("click", () => showAcc(dalmiaShila, dalmiaShilaDate));
      }
      billList.appendChild(card);
    });
  } catch (_error) {
    homeError.hidden = false;
    homeError.textContent = "The bill list could not be loaded. Refresh the page and try again.";
  }
}

async function loadDateLimits() {
  try {
    const response = await fetch("/api/ultratech/config");
    if (!response.ok) return;
    const config = await response.json();
    dateInput.min = config.minDate;
    dateInput.max = config.maxDate;
  } catch (_error) {
    // The server still rejects dates outside the financial year.
  }
}

async function refreshPreview() {
  clearDownload();
  const value = dateInput.value;
  if (!value) {
    clearComputed();
    setError("");
    setStatus("");
    return;
  }
  const requestId = ++previewRequest;
  try {
    const response = await fetch(`/api/ultratech/preview?invoiceDate=${encodeURIComponent(value)}`);
    const payload = await response.json();
    if (requestId !== previewRequest) return;
    if (!response.ok) {
      clearComputed();
      setError(payload.error || "Enter a valid invoice date.");
      return;
    }
    billingMonth.value = payload.billingMonth;
    invoiceNumber.value = payload.invoiceNumber;
    billPeriod.value = payload.billPeriod;
    setError("");
  } catch (_error) {
    if (requestId !== previewRequest) return;
    clearComputed();
    setError("The invoice details could not be calculated. Try again.");
  }
}

async function generatePdf() {
  if (busy) return;
  clearDownload();
  setStatus("");
  if (!dateInput.value) {
    setError("Choose an invoice date.");
    return;
  }

  busy = true;
  generateBtn.disabled = true;
  dateInput.disabled = true;
  setError("");
  setStatus("Generating your bill...");

  try {
    const response = await fetch("/api/ultratech/pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ invoiceDate: dateInput.value }),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      setStatus("");
      setError(payload.error || "The bill could not be generated. Please try again.");
      return;
    }
    const blob = await response.blob();
    downloadUrl = URL.createObjectURL(blob);
    downloadName = filenameFrom(response);
    downloadBtn.hidden = false;
    setStatus("PDF generated successfully.");
  } catch (_error) {
    setStatus("");
    setError("The bill could not be generated. Check your connection and try again.");
  } finally {
    busy = false;
    generateBtn.disabled = false;
    dateInput.disabled = false;
  }
}

function filenameFrom(response, fallback = "UltraTech_Invoice.pdf") {
  const header = response.headers.get("Content-Disposition") || "";
  const match = header.match(/filename="([^"]+)"/);
  return match ? match[1] : fallback;
}

function clearComputed() {
  billingMonth.value = "";
  invoiceNumber.value = "";
  billPeriod.value = "";
}

function clearDownload() {
  if (downloadUrl) URL.revokeObjectURL(downloadUrl);
  downloadUrl = "";
  downloadBtn.hidden = true;
}

function setError(message) {
  formError.hidden = !message;
  formError.textContent = message;
}

function setStatus(message) {
  formStatus.hidden = !message;
  formStatus.textContent = message;
  formStatus.classList.toggle("is-error", false);
}

const accLalanDate = document.querySelector("#acc-lalan-date");
const accShilaDate = document.querySelector("#acc-shila-date");
const dalmiaLalanDate = document.querySelector("#dalmia-lalan-date");
const dalmiaShilaDate = document.querySelector("#dalmia-shila-date");

bindAccForm({
  screen: accLalan,
  back: document.querySelector("#acc-lalan-back"),
  form: document.querySelector("#acc-lalan-form"),
  dateInput: accLalanDate,
  invoiceNumber: document.querySelector("#acc-lalan-number"),
  timePeriod: document.querySelector("#acc-lalan-period"),
  formError: document.querySelector("#acc-lalan-error"),
  formStatus: document.querySelector("#acc-lalan-status"),
  generateBtn: document.querySelector("#acc-lalan-generate"),
  downloadBtn: document.querySelector("#acc-lalan-download"),
  configUrl: "/api/acc-lalan/config",
  previewUrl: "/api/acc-lalan/preview",
  pdfUrl: "/api/acc-lalan/pdf",
  fallbackName: "ACC_Lalan_Invoice.pdf",
});

bindAccForm({
  screen: accShila,
  back: document.querySelector("#acc-shila-back"),
  form: document.querySelector("#acc-shila-form"),
  dateInput: accShilaDate,
  invoiceNumber: document.querySelector("#acc-shila-number"),
  timePeriod: document.querySelector("#acc-shila-period"),
  formError: document.querySelector("#acc-shila-error"),
  formStatus: document.querySelector("#acc-shila-status"),
  generateBtn: document.querySelector("#acc-shila-generate"),
  downloadBtn: document.querySelector("#acc-shila-download"),
  configUrl: "/api/acc-shila/config",
  previewUrl: "/api/acc-shila/preview",
  pdfUrl: "/api/acc-shila/pdf",
  fallbackName: "ACC_Shila_Invoice.pdf",
});

bindAccForm({
  screen: dalmiaLalan,
  back: document.querySelector("#dalmia-lalan-back"),
  form: document.querySelector("#dalmia-lalan-form"),
  dateInput: dalmiaLalanDate,
  invoiceNumber: document.querySelector("#dalmia-lalan-number"),
  timePeriod: document.querySelector("#dalmia-lalan-period"),
  formError: document.querySelector("#dalmia-lalan-error"),
  formStatus: document.querySelector("#dalmia-lalan-status"),
  generateBtn: document.querySelector("#dalmia-lalan-generate"),
  downloadBtn: document.querySelector("#dalmia-lalan-download"),
  configUrl: "/api/dalmia-lalan/config",
  previewUrl: "/api/dalmia-lalan/preview",
  pdfUrl: "/api/dalmia-lalan/pdf",
  fallbackName: "Dalmia_Lalan_Invoice.pdf",
});

bindAccForm({
  screen: dalmiaShila,
  back: document.querySelector("#dalmia-shila-back"),
  form: document.querySelector("#dalmia-shila-form"),
  dateInput: dalmiaShilaDate,
  invoiceNumber: document.querySelector("#dalmia-shila-number"),
  timePeriod: document.querySelector("#dalmia-shila-period"),
  formError: document.querySelector("#dalmia-shila-error"),
  formStatus: document.querySelector("#dalmia-shila-status"),
  generateBtn: document.querySelector("#dalmia-shila-generate"),
  downloadBtn: document.querySelector("#dalmia-shila-download"),
  configUrl: "/api/dalmia-shila/config",
  previewUrl: "/api/dalmia-shila/preview",
  pdfUrl: "/api/dalmia-shila/pdf",
  fallbackName: "Dalmia_Shila_Invoice.pdf",
});

function showAcc(screen, input) {
  home.hidden = true;
  ultratech.hidden = true;
  accLalan.hidden = screen !== accLalan;
  accShila.hidden = screen !== accShila;
  dalmiaLalan.hidden = screen !== dalmiaLalan;
  dalmiaShila.hidden = screen !== dalmiaShila;
  input.focus();
}

function bindAccForm(ui) {
  let busy = false;
  let downloadUrl = "";
  let downloadName = ui.fallbackName;
  let previewRequest = 0;
  let previewReady = false;

  ui.back.addEventListener("click", () => {
    showHome();
  });

  ui.form.addEventListener("submit", (event) => {
    event.preventDefault();
    generate();
  });

  ui.downloadBtn.addEventListener("click", () => {
    if (!downloadUrl) return;
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = downloadName;
    document.body.appendChild(link);
    link.click();
    link.remove();
  });

  ui.dateInput.addEventListener("input", () => refresh());
  ui.dateInput.addEventListener("change", () => refresh());
  loadLimits();

  async function loadLimits() {
    try {
      const response = await fetch(ui.configUrl);
      if (!response.ok) return;
      const config = await response.json();
      ui.dateInput.min = config.minDate;
      ui.dateInput.max = config.maxDate;
    } catch (_error) {
      // The server still rejects dates outside 2026.
    }
  }

  async function refresh() {
    clearDownload();
    previewReady = false;
    ui.generateBtn.disabled = true;
    const value = ui.dateInput.value;
    if (!value) {
      clearComputed();
      setError("");
      setStatus("");
      return;
    }
    const requestId = ++previewRequest;
    try {
      const response = await fetch(`${ui.previewUrl}?invoiceDate=${encodeURIComponent(value)}`);
      const payload = await response.json();
      if (requestId !== previewRequest) return;
      if (!response.ok) {
        clearComputed();
        setError(payload.error || "Please select a valid invoice date.");
        return;
      }
      ui.invoiceNumber.value = payload.invoiceNumber;
      ui.timePeriod.value = payload.timePeriod;
      previewReady = Boolean(payload.invoiceNumber && payload.timePeriod);
      ui.generateBtn.disabled = !previewReady;
      setError("");
    } catch (_error) {
      if (requestId !== previewRequest) return;
      clearComputed();
      setError("The invoice details could not be calculated. Try again.");
    }
  }

  async function generate() {
    if (busy) return;
    clearDownload();
    setStatus("");
    if (!ui.dateInput.value || !previewReady || !ui.invoiceNumber.value || !ui.timePeriod.value) {
      setError("Please select a valid invoice date.");
      return;
    }

    busy = true;
    ui.generateBtn.disabled = true;
    ui.dateInput.disabled = true;
    setError("");
    setStatus("Generating your bill...");

    try {
      const response = await fetch(ui.pdfUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ invoiceDate: ui.dateInput.value }),
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        setStatus("");
        setError(payload.error || "The bill could not be generated. Please try again.");
        return;
      }
      const blob = await response.blob();
      downloadUrl = URL.createObjectURL(blob);
      downloadName = filenameFrom(response, ui.fallbackName);
      ui.downloadBtn.hidden = false;
      setStatus("PDF generated successfully.");
    } catch (_error) {
      setStatus("");
      setError("The bill could not be generated. Check your connection and try again.");
    } finally {
      busy = false;
      ui.generateBtn.disabled = !previewReady;
      ui.dateInput.disabled = false;
    }
  }

  function clearComputed() {
    ui.invoiceNumber.value = "";
    ui.timePeriod.value = "";
  }

  function clearDownload() {
    if (downloadUrl) URL.revokeObjectURL(downloadUrl);
    downloadUrl = "";
    ui.downloadBtn.hidden = true;
  }

  function setError(message) {
    ui.formError.hidden = !message;
    ui.formError.textContent = message;
  }

  function setStatus(message) {
    ui.formStatus.hidden = !message;
    ui.formStatus.textContent = message;
  }
}

