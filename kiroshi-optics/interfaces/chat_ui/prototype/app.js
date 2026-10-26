"use strict";

const video = document.querySelector("#camera-video");
const stage = document.querySelector("#camera-stage");
const placeholder = document.querySelector("#camera-placeholder");
const errorBox = document.querySelector("#camera-error");
const selectionBox = document.querySelector("#selection-box");
const startButton = document.querySelector("#start-analysis");
const stopButton = document.querySelector("#stop-camera");
const cameraStatus = document.querySelector("#camera-status");
const sourceValue = document.querySelector("#source-value");
const regionValue = document.querySelector("#region-value");
const selectionLabel = document.querySelector("#selection-label");
const selectionHelp = document.querySelector("#selection-help");
const settingsStatus = document.querySelector("#camera-settings-status");
const settingsDetail = document.querySelector("#camera-settings-detail");
const toast = document.querySelector("#toast");

let mediaStream = null;
let hasSelection = false;
let dragStart = null;
let toastTimer = 0;

const screenTitles = {
  scanner: "ESCÁNER VISUAL",
  analysis: "ANÁLISIS ACTIVO",
  result: "RESULTADO",
  history: "HISTORIAL",
  camera: "CÁMARA Y PERMISOS"
};

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove("is-visible"), 3200);
}

function setScreen(name) {
  const target = screenTitles[name] ? name : "scanner";
  document.querySelectorAll(".screen").forEach((screen) => {
    const isCurrent = screen.id === `screen-${target}`;
    screen.classList.toggle("is-visible", isCurrent);
    screen.hidden = !isCurrent;
  });
  document.querySelectorAll(".nav-item").forEach((item) => {
    const isCurrent = item.dataset.screen === target;
    item.classList.toggle("is-active", isCurrent);
    if (isCurrent) item.setAttribute("aria-current", "page");
    else item.removeAttribute("aria-current");
  });
  document.querySelector("#screen-breadcrumb").textContent = screenTitles[target];
}

async function connectCamera() {
  errorBox.hidden = true;
  if (!navigator.mediaDevices?.getUserMedia) {
    setCameraError("El navegador no permite usar la cámara en este origen. Abre esta página desde localhost o HTTPS.");
    return;
  }
  if (mediaStream) return;

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: { facingMode: "user" }
    });
    video.srcObject = mediaStream;
    await video.play();
    video.classList.add("is-active");
    placeholder.hidden = true;
    stopButton.disabled = false;
    cameraStatus.textContent = "CÁMARA: ACTIVA";
    sourceValue.textContent = "CONECTADA";
    sourceValue.classList.add("demo-text");
    settingsStatus.textContent = "CÁMARA CONECTADA";
    settingsDetail.textContent = "La vista previa está activa en esta sesión";
    document.querySelector(".source-led").classList.add("is-live");
    document.querySelector(".camera-tag").classList.add("is-live");
    showToast("Cámara conectada. El video se muestra solo en esta página.");
  } catch (error) {
    const message = error?.name === "NotAllowedError"
      ? "Permiso denegado. Permite el acceso a la cámara en la configuración del navegador."
      : error?.name === "NotFoundError"
        ? "No se encontró una cámara disponible en el equipo."
        : error?.name === "NotReadableError"
          ? "La cámara no se puede abrir. Comprueba si otra aplicación la está usando."
          : "No fue posible acceder a la cámara. Revisa los permisos del navegador y vuelve a intentar.";
    setCameraError(message);
  }
}

function setCameraError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
  settingsStatus.textContent = "NO DISPONIBLE";
  settingsDetail.textContent = message;
  cameraStatus.textContent = "CÁMARA: NO DISPONIBLE";
  showToast(message);
}

function disconnectCamera() {
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
  }
  video.srcObject = null;
  video.classList.remove("is-active");
  placeholder.hidden = false;
  stopButton.disabled = true;
  cameraStatus.textContent = "CÁMARA: SIN CONECTAR";
  sourceValue.textContent = "PENDIENTE";
  sourceValue.classList.remove("demo-text");
  settingsStatus.textContent = "PERMISO PENDIENTE";
  settingsDetail.textContent = "Disponibilidad por comprobar";
  document.querySelector(".source-led").classList.remove("is-live");
  document.querySelector(".camera-tag").classList.remove("is-live");
  resetSelection();
  errorBox.hidden = true;
}

function resetSelection() {
  hasSelection = false;
  selectionBox.classList.remove("is-visible");
  startButton.disabled = true;
  regionValue.textContent = "VACÍA";
  selectionLabel.textContent = "Ninguna región marcada";
  selectionHelp.textContent = "Activa la cámara y arrastra para seleccionar un área.";
  document.querySelector(".overlay-bottom").textContent = "MARCA UNA REGIÓN PARA CONTINUAR";
}

function updateSelection(event) {
  if (!dragStart) return;
  const bounds = stage.getBoundingClientRect();
  const currentX = Math.min(Math.max(event.clientX, bounds.left), bounds.right);
  const currentY = Math.min(Math.max(event.clientY, bounds.top), bounds.bottom);
  const left = Math.min(dragStart.x, currentX);
  const top = Math.min(dragStart.y, currentY);
  const width = Math.abs(currentX - dragStart.x);
  const height = Math.abs(currentY - dragStart.y);
  selectionBox.style.left = `${((left - bounds.left) / bounds.width) * 100}%`;
  selectionBox.style.top = `${((top - bounds.top) / bounds.height) * 100}%`;
  selectionBox.style.width = `${(width / bounds.width) * 100}%`;
  selectionBox.style.height = `${(height / bounds.height) * 100}%`;
  selectionBox.classList.add("is-visible");
}

function addDemoHistoryEntry() {
  const rows = document.querySelector("#history-rows");
  const row = document.createElement("tr");
  const time = new Date().toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" });
  row.innerHTML = `<td>${time}</td><td>Taza con asa · muestra</td><td><span class="history-demo">DATOS DE DEMOSTRACIÓN</span></td><td>Cámara · no se guardó video</td>`;
  rows.prepend(row);
  document.querySelector("#history-empty").hidden = true;
  document.querySelector("#history-table-wrap").hidden = false;
}

document.querySelectorAll("[data-screen]").forEach((control) => {
  control.addEventListener("click", () => setScreen(control.dataset.screen));
});

document.querySelector("#connect-camera").addEventListener("click", connectCamera);
document.querySelector("#connect-camera-settings").addEventListener("click", connectCamera);
stopButton.addEventListener("click", disconnectCamera);

stage.addEventListener("pointerdown", (event) => {
  if (!mediaStream || event.target.closest("button")) return;
  stage.setPointerCapture(event.pointerId);
  dragStart = { x: event.clientX, y: event.clientY };
  updateSelection(event);
});
stage.addEventListener("pointermove", updateSelection);
stage.addEventListener("pointerup", (event) => {
  if (!dragStart) return;
  updateSelection(event);
  const box = selectionBox.getBoundingClientRect();
  const bounds = stage.getBoundingClientRect();
  dragStart = null;
  hasSelection = box.width >= 18 && box.height >= 18;
  if (!hasSelection) {
    resetSelection();
    return;
  }
  startButton.disabled = false;
  regionValue.textContent = "MARCADA";
  selectionLabel.textContent = "Región objetivo marcada";
  selectionHelp.textContent = "Área seleccionada manualmente en la vista de cámara.";
  document.querySelector(".overlay-bottom").textContent =
    `REGIÓN · ${Math.round((box.width / bounds.width) * 100)}% × ${Math.round((box.height / bounds.height) * 100)}%`;
});
stage.addEventListener("pointercancel", () => {
  dragStart = null;
});

startButton.addEventListener("click", () => {
  if (!mediaStream || !hasSelection) return;
  addDemoHistoryEntry();
  setScreen("analysis");
  showToast("Vista de análisis ilustrativa; aún no hay un modelo conectado.");
});

document.querySelectorAll(".nav-item").forEach((item) => {
  item.addEventListener("click", () => {
    if (item.dataset.screen === "analysis") {
      showToast("El análisis activo muestra una secuencia de demostración.");
    }
    if (item.dataset.screen === "result") {
      showToast("El resultado es una muestra de interfaz, no un diagnóstico real.");
    }
  });
});

function updateClock() {
  document.querySelector("#clock").textContent = new Date().toLocaleTimeString("es", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  });
}

updateClock();
window.setInterval(updateClock, 1000);
window.addEventListener("beforeunload", () => {
  if (mediaStream) mediaStream.getTracks().forEach((track) => track.stop());
});
