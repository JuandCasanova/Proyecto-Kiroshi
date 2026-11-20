const MEDIAPIPE_VERSION = "0.10.14";
const MEDIAPIPE_BUNDLE = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${MEDIAPIPE_VERSION}/vision_bundle.mjs`;
const MEDIAPIPE_WASM = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${MEDIAPIPE_VERSION}/wasm`;
const OBJECT_MODEL = "https://storage.googleapis.com/mediapipe-models/object_detector/efficientdet_lite0/float16/1/efficientdet_lite0.tflite";
const HAND_MODEL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task";
const MIN_GAP_RATIO = 0.12;
const MAX_GAP_RATIO = 0.68;
const MIN_ZOOM = 0.7;
const MAX_ZOOM = 3;
const OBJECT_LABELS = {
  person: "PERSONA",
  bottle: "BOTELLA",
  cup: "TAZA",
  laptop: "LAPTOP",
  mouse: "MOUSE",
  keyboard: "TECLADO",
  chair: "SILLA",
  "teddy bear": "JUGUETE/PELUCHE",
  tv: "PANTALLA",
  "cell phone": "TELEFONO",
  book: "LIBRO",
  remote: "CONTROL REMOTO",
  couch: "SOFA",
  "dining table": "MESA",
  backpack: "MOCHILA",
  handbag: "BOLSO",
  suitcase: "MALETA",
  clock: "RELOJ",
  "sports ball": "PELOTA",
  bicycle: "BICICLETA",
  car: "AUTO",
  dog: "PERRO",
  cat: "GATO"
};
const OBJECT_DESCRIPTIONS = {
  person: "Persona detectada; no se intenta identificarla.",
  bottle: "Recipiente para almacenar y transportar líquidos.",
  cup: "Recipiente pequeño para beber.",
  laptop: "Computadora portátil para trabajar y ejecutar programas.",
  mouse: "Periférico para mover el cursor y seleccionar.",
  keyboard: "Teclado para escribir e ingresar comandos.",
  chair: "Asiento con respaldo para una persona.",
  "teddy bear": "Juguete de peluche para jugar o acompañar.",
  tv: "Pantalla para ver contenido audiovisual.",
  "cell phone": "Teléfono portátil para comunicarse y usar aplicaciones.",
  book: "Publicación impresa para leer o consultar.",
  remote: "Control para manejar aparatos a distancia.",
  couch: "Asiento amplio para varias personas.",
  "dining table": "Superficie para comer o apoyar objetos.",
  backpack: "Bolso que se lleva en la espalda.",
  handbag: "Bolso para transportar objetos personales.",
  suitcase: "Maleta para llevar pertenencias durante un viaje.",
  clock: "Dispositivo que indica la hora.",
  "sports ball": "Balón o pelota usado en actividades deportivas.",
  bicycle: "Vehículo de dos ruedas impulsado con pedales.",
  car: "Vehículo motorizado para transportar personas.",
  dog: "Animal doméstico; la detección solo indica la categoría.",
  cat: "Animal doméstico; la detección solo indica la categoría."
};

const optics = document.querySelector("#hud");
const video = document.querySelector("#camera");
const detectionsCanvas = document.querySelector("#detections");
const placeholder = document.querySelector("#camera-placeholder");
const activateButton = document.querySelector("#activate-camera");
const cameraButton = document.querySelector("#camera-button");
const voiceButton = document.querySelector("#voice-button");
const scanButton = document.querySelector("#scan-button");
const gestureButton = document.querySelector("#gesture-button");
const settingsToggle = document.querySelector("#settings-toggle");
const settingsPanel = document.querySelector("#settings-panel");
const fullscreenButton = document.querySelector("#fullscreen-button");
const zoomInput = document.querySelector("#zoom");
const zoomValue = document.querySelector("#zoom-value");
const cameraState = document.querySelector("#camera-state");
const voiceReadout = document.querySelector("#voice-readout");
const scanReadout = document.querySelector("#scan-readout");
const gestureReadout = document.querySelector("#gesture-readout");
const objectDescription = document.querySelector("#object-description");
const errorPanel = document.querySelector("#error-panel");
const clock = document.querySelector("#clock");

let mediaStream = null;
let speechRecognition = null;
let scanEnabled = false;
let gestureEnabled = false;
let voiceModeEnabled = false;
let voiceRecognitionSupported = false;
let voicePermissionBlocked = false;
let voiceListening = false;
let voiceRestartTimer = null;
let voiceRestartDelay = 500;
let visionModulePromise = null;
let visionFilesetPromise = null;
let objectDetectorPromise = null;
let handLandmarkerPromise = null;
let objectDetector = null;
let handLandmarker = null;
let lastObjectTimestamp = 0;
let lastHandTimestamp = 0;
let lastFrameTime = 0;
let lastVideoTime = -1;
let currentZoom = 1;
let smoothedGap = null;
let latestDetections = [];
let gestureMessage = "BUSCANDO MANO";

function showError(message) {
  errorPanel.textContent = message;
  errorPanel.hidden = false;
}

function clearError() {
  errorPanel.textContent = "";
  errorPanel.hidden = true;
}

function setZoom(zoom) {
  currentZoom = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, zoom));
  optics.style.setProperty("--zoom", currentZoom);
  zoomInput.value = String(currentZoom);
  zoomValue.value = `${currentZoom.toFixed(1)}x`;
}

function updateFeatureReadouts() {
  scanReadout.textContent = scanEnabled
    ? objectDetector ? "ESCANEO: ACTIVO" : "ESCANEO: CARGANDO"
    : "ESCANEO: INACTIVO";
  scanReadout.classList.toggle("active", scanEnabled);
  scanButton.setAttribute("aria-pressed", String(scanEnabled));
  scanButton.textContent = `ESCANEO DE OBJETOS: ${scanEnabled ? "ON" : "OFF"}`;

  gestureReadout.hidden = !gestureEnabled;
  gestureReadout.textContent = `ZOOM GESTUAL: ${gestureEnabled ? gestureMessage : "INACTIVO"}`;
  gestureReadout.classList.toggle("active", gestureEnabled);
  gestureButton.setAttribute("aria-pressed", String(gestureEnabled));
  gestureButton.textContent = `ZOOM GESTUAL: ${gestureEnabled ? "ON" : "OFF"}`;
}

function updateFeatureControls() {
  const cameraActive = Boolean(mediaStream);
  scanButton.disabled = !cameraActive;
  gestureButton.disabled = !cameraActive;
  zoomInput.disabled = !cameraActive;
  updateVoiceReadout();
  updateFeatureReadouts();
}

function updateVoiceReadout() {
  voiceReadout.hidden = !mediaStream;
  voiceReadout.classList.toggle("active", voiceModeEnabled);
  voiceButton.disabled = !mediaStream || !voiceRecognitionSupported || voicePermissionBlocked;
  voiceButton.setAttribute("aria-pressed", String(voiceModeEnabled));

  if (!mediaStream) {
    voiceReadout.textContent = "VOZ: INACTIVA";
    voiceButton.textContent = "COMANDOS DE VOZ: OFF";
  } else if (!voiceRecognitionSupported) {
    voiceReadout.textContent = "VOZ: NO DISPONIBLE";
    voiceButton.textContent = "VOZ: NO DISPONIBLE";
  } else if (voicePermissionBlocked) {
    voiceReadout.textContent = "VOZ: REVISA EL PERMISO";
    voiceButton.textContent = "VOZ: BLOQUEADA";
  } else if (voiceModeEnabled) {
    voiceReadout.textContent = "VOZ: COMANDOS ACTIVOS";
    voiceButton.textContent = "COMANDOS DE VOZ: ON";
  } else {
    voiceReadout.textContent = voiceListening ? "VOZ: EN ESPERA" : "VOZ: CONECTANDO";
    voiceButton.textContent = "COMANDOS DE VOZ: OFF";
  }
}

function scheduleVoiceRestart() {
  if (!mediaStream || !speechRecognition || voicePermissionBlocked || voiceRestartTimer) return;
  const delay = voiceRestartDelay;
  voiceRestartDelay = Math.min(voiceRestartDelay * 2, 4000);
  voiceRestartTimer = window.setTimeout(() => {
    voiceRestartTimer = null;
    startVoiceRecognition();
  }, delay);
}

function startVoiceRecognition() {
  if (!mediaStream || !speechRecognition || voiceListening || voicePermissionBlocked) return;
  try {
    speechRecognition.start();
    voiceListening = true;
    updateVoiceReadout();
  } catch (error) {
    if (error?.name === "InvalidStateError") return;
    console.error("No se pudo iniciar el reconocimiento de voz.", error);
    voicePermissionBlocked = true;
    voiceModeEnabled = false;
    updateVoiceReadout();
    showError("No se pudo iniciar la voz. Revisa el permiso del microfono y la conexion.");
  }
}

function initializeVoiceRecognition() {
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!Recognition) {
    voiceRecognitionSupported = false;
    updateVoiceReadout();
    return;
  }

  try {
    speechRecognition = new Recognition();
  } catch (error) {
    console.error("No se pudo crear el reconocedor de voz.", error);
    voiceRecognitionSupported = false;
    updateVoiceReadout();
    showError("El navegador no pudo iniciar el reconocimiento de voz.");
    return;
  }
  speechRecognition.lang = "es-CO";
  speechRecognition.continuous = true;
  speechRecognition.interimResults = false;
  speechRecognition.maxAlternatives = 1;
  speechRecognition.onstart = () => {
    voiceListening = true;
    voiceRestartDelay = 500;
    updateVoiceReadout();
  };
  speechRecognition.onresult = handleVoiceResult;
  speechRecognition.onerror = (event) => {
    voiceListening = false;
    if (event.error === "not-allowed" || event.error === "service-not-allowed") {
      voicePermissionBlocked = true;
      voiceModeEnabled = false;
      showError("Permite el microfono y el reconocimiento de voz en el navegador.");
    }
    updateVoiceReadout();
  };
  speechRecognition.onend = () => {
    voiceListening = false;
    updateVoiceReadout();
    scheduleVoiceRestart();
  };
  voiceRecognitionSupported = true;
  updateVoiceReadout();
  startVoiceRecognition();
}

function stopVoiceRecognition() {
  if (voiceRestartTimer) {
    window.clearTimeout(voiceRestartTimer);
    voiceRestartTimer = null;
  }

  const recognition = speechRecognition;
  speechRecognition = null;
  voiceModeEnabled = false;
  voiceRecognitionSupported = false;
  voicePermissionBlocked = false;
  voiceListening = false;
  if (recognition) {
    recognition.onstart = null;
    recognition.onresult = null;
    recognition.onerror = null;
    recognition.onend = null;
    try {
      recognition.stop();
    } catch (error) {
      if (error?.name !== "InvalidStateError") {
        console.error("No se pudo detener el reconocimiento de voz.", error);
      }
    }
  }
  updateVoiceReadout();
}

function normalizeVoiceCommand(transcript) {
  return transcript
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9 ]/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function handleVoiceResult(event) {
  for (let index = event.resultIndex; index < event.results.length; index += 1) {
    const result = event.results[index];
    if (!result.isFinal || !result[0]?.transcript) continue;
    processVoiceCommand(normalizeVoiceCommand(result[0].transcript));
  }
}

function processVoiceCommand(command) {
  const disableVoice = command.includes("desactivar deteccion de voz") ||
    command.includes("desactiva deteccion de voz") ||
    command.includes("detener deteccion de voz");

  if (!voiceModeEnabled) {
    if (!disableVoice && command.includes("deteccion de voz")) {
      voiceModeEnabled = true;
      clearError();
      updateVoiceReadout();
    }
    return;
  }

  if (disableVoice) {
    voiceModeEnabled = false;
    updateVoiceReadout();
    return;
  }

  if (command.includes("detener escaneo") || command.includes("desactivar escaneo")) {
    if (scanEnabled) void toggleObjectScan();
    return;
  }
  if (command.includes("modo escaneo") || command.includes("modo de escaneo")) {
    if (!scanEnabled) void toggleObjectScan();
    return;
  }

  if (command.includes("detener zoom") || command.includes("desactivar zoom")) {
    if (gestureEnabled) void toggleGestureZoom();
    return;
  }
  if (command === "zoom" || command.includes("activar zoom") || command.includes("modo zoom")) {
    if (!gestureEnabled) void toggleGestureZoom();
  }
}

function toggleVoiceMode() {
  if (!mediaStream) {
    showError("Activa la camara para habilitar los comandos de voz.");
    return;
  }
  if (!voiceRecognitionSupported || voicePermissionBlocked) {
    showError("El reconocimiento de voz no esta disponible o no tiene permiso.");
    return;
  }
  voiceModeEnabled = !voiceModeEnabled;
  updateVoiceReadout();
}

async function loadVisionModule() {
  if (!visionModulePromise) {
    visionModulePromise = import(MEDIAPIPE_BUNDLE).catch((error) => {
      visionModulePromise = null;
      throw error;
    });
  }
  return visionModulePromise;
}

async function loadVisionFileset() {
  if (!visionFilesetPromise) {
    visionFilesetPromise = loadVisionModule()
      .then(({ FilesetResolver }) => FilesetResolver.forVisionTasks(MEDIAPIPE_WASM))
      .catch((error) => {
        visionFilesetPromise = null;
        throw error;
      });
  }
  return visionFilesetPromise;
}

async function loadObjectDetector() {
  if (!objectDetectorPromise) {
    objectDetectorPromise = Promise.all([loadVisionModule(), loadVisionFileset()])
      .then(([{ ObjectDetector }, vision]) => ObjectDetector.createFromOptions(vision, {
        baseOptions: { modelAssetPath: OBJECT_MODEL, delegate: "CPU" },
        runningMode: "VIDEO",
        scoreThreshold: 0.4,
        maxResults: 20,
        categoryDenylist: ["person"]
      }))
      .then((detector) => {
        objectDetector = detector;
        return detector;
      })
      .catch((error) => {
        objectDetectorPromise = null;
        throw error;
      });
  }
  return objectDetectorPromise;
}

async function loadHandLandmarker() {
  if (!handLandmarkerPromise) {
    handLandmarkerPromise = Promise.all([loadVisionModule(), loadVisionFileset()])
      .then(([{ HandLandmarker }, vision]) => HandLandmarker.createFromOptions(vision, {
        baseOptions: { modelAssetPath: HAND_MODEL, delegate: "CPU" },
        runningMode: "VIDEO",
        numHands: 1,
        minHandDetectionConfidence: 0.55,
        minHandPresenceConfidence: 0.55,
        minTrackingConfidence: 0.5
      }))
      .then((landmarker) => {
        handLandmarker = landmarker;
        return landmarker;
      })
      .catch((error) => {
        handLandmarkerPromise = null;
        throw error;
      });
  }
  return handLandmarkerPromise;
}

async function connectCamera() {
  clearError();
  if (!navigator.mediaDevices?.getUserMedia) {
    showError("Este navegador requiere HTTPS y permiso de camara para mostrar la vista.");
    return;
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: false,
      video: { facingMode: { ideal: "environment" }, width: { ideal: 1920 }, height: { ideal: 1080 } }
    });
    video.srcObject = mediaStream;
    await video.play();
    video.classList.add("active");
    placeholder.hidden = true;
    cameraState.textContent = "CAMARA ACTIVA";
    cameraState.parentElement.classList.add("active");
    cameraButton.textContent = "DESCONECTAR CAMARA";
    activateButton.hidden = true;
    mediaStream.getVideoTracks()[0].addEventListener("ended", disconnectCamera, { once: true });
    initializeVoiceRecognition();
    updateFeatureControls();
  } catch (error) {
    if (mediaStream) mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
    stopVoiceRecognition();
    const messages = {
      NotAllowedError: "Permiso denegado. Permite la camara en la configuracion del navegador.",
      NotFoundError: "No se encontro una camara trasera disponible; revisa la configuracion del dispositivo.",
      NotReadableError: "La camara esta ocupada por otra aplicacion."
    };
    showError(messages[error?.name] || "No fue posible activar la camara.");
  }
}

function clearDetectionOverlay() {
  const context = detectionsCanvas.getContext("2d");
  context.clearRect(0, 0, detectionsCanvas.width, detectionsCanvas.height);
  objectDescription.hidden = true;
  objectDescription.textContent = "";
}

function disconnectCamera() {
  if (mediaStream) {
    mediaStream.getTracks().forEach((track) => track.stop());
    mediaStream = null;
  }
  stopVoiceRecognition();
  scanEnabled = false;
  gestureEnabled = false;
  latestDetections = [];
  smoothedGap = null;
  gestureMessage = "BUSCANDO MANO";
  video.srcObject = null;
  video.classList.remove("active");
  placeholder.hidden = false;
  cameraState.textContent = "CAMARA EN ESPERA";
  cameraState.parentElement.classList.remove("active");
  cameraButton.textContent = "ACTIVAR CAMARA";
  activateButton.hidden = false;
  updateFeatureControls();
  clearDetectionOverlay();
  setZoom(1);
}

function toggleSettings() {
  const isExpanded = settingsToggle.getAttribute("aria-expanded") === "true";
  settingsToggle.setAttribute("aria-expanded", String(!isExpanded));
  settingsToggle.textContent = isExpanded ? "+" : "-";
  settingsPanel.hidden = isExpanded;
}

async function toggleFullscreen() {
  try {
    if (document.fullscreenElement) {
      await document.exitFullscreen();
    } else {
      await optics.requestFullscreen();
    }
  } catch {
    showError("El navegador no permitio cambiar a pantalla completa.");
  }
}

async function toggleObjectScan() {
  if (!mediaStream) {
    showError("Activa la camara antes de iniciar el escaneo.");
    return;
  }
  clearError();
  scanEnabled = !scanEnabled;
  latestDetections = [];
  updateFeatureReadouts();
  if (!scanEnabled) {
    clearDetectionOverlay();
    return;
  }

  try {
    await loadObjectDetector();
    if (scanEnabled) updateFeatureReadouts();
  } catch (error) {
    if (!scanEnabled) return;
    console.error("No se pudo iniciar el detector de objetos.", error);
    scanEnabled = false;
    updateFeatureReadouts();
    clearDetectionOverlay();
    showError("No se pudo cargar el escaner. Revisa tu conexion e intenta de nuevo.");
  }
}

async function toggleGestureZoom() {
  if (!mediaStream) {
    showError("Activa la camara antes de iniciar el zoom gestual.");
    return;
  }
  clearError();
  gestureEnabled = !gestureEnabled;
  smoothedGap = null;
  gestureMessage = "BUSCANDO MANO";
  updateFeatureReadouts();
  if (!gestureEnabled) return;

  try {
    await loadHandLandmarker();
    if (gestureEnabled) updateFeatureReadouts();
  } catch (error) {
    if (!gestureEnabled) return;
    console.error("No se pudo iniciar el detector de manos.", error);
    gestureEnabled = false;
    updateFeatureReadouts();
    showError("No se pudo cargar el zoom gestual. Revisa tu conexion e intenta de nuevo.");
  }
}

function drawDetections() {
  const bounds = optics.getBoundingClientRect();
  const pixelRatio = window.devicePixelRatio || 1;
  const canvasWidth = Math.round(bounds.width * pixelRatio);
  const canvasHeight = Math.round(bounds.height * pixelRatio);
  if (detectionsCanvas.width !== canvasWidth || detectionsCanvas.height !== canvasHeight) {
    detectionsCanvas.width = canvasWidth;
    detectionsCanvas.height = canvasHeight;
  }

  const context = detectionsCanvas.getContext("2d");
  context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
  context.clearRect(0, 0, bounds.width, bounds.height);
  if (!scanEnabled || !video.videoWidth || !video.videoHeight) return;

  const scale = Math.max(bounds.width / video.videoWidth, bounds.height / video.videoHeight);
  const offsetX = (bounds.width - video.videoWidth * scale) / 2;
  const offsetY = (bounds.height - video.videoHeight * scale) / 2;
  const frameCenterX = video.videoWidth / 2;
  const frameCenterY = video.videoHeight / 2;
  let selectedObject = null;
  let nearestDistance = Infinity;
  context.lineWidth = 2;
  context.font = "12px Consolas, monospace";
  context.textBaseline = "bottom";

  latestDetections.forEach((detection) => {
    const box = detection.boundingBox;
    const category = detection.categories[0];
    if (!category) return;
    const zoomedX = (box.originX * scale + offsetX - bounds.width / 2) * currentZoom + bounds.width / 2;
    const zoomedY = (box.originY * scale + offsetY - bounds.height / 2) * currentZoom + bounds.height / 2;
    const x = zoomedX;
    const y = zoomedY;
    const width = box.width * scale * currentZoom;
    const height = box.height * scale * currentZoom;
    const label = `${category.categoryName.toUpperCase()} ${Math.round(category.score * 100)}%`;
    const labelWidth = context.measureText(label).width + 12;
    const distance = Math.hypot(
      box.originX + box.width / 2 - frameCenterX,
      box.originY + box.height / 2 - frameCenterY
    );
    if (distance < nearestDistance) {
      nearestDistance = distance;
      selectedObject = category.categoryName.toLowerCase();
    }

    context.strokeStyle = "#56ffe0";
    context.fillStyle = "rgba(3, 10, 10, 0.78)";
    context.strokeRect(x, y, width, height);
    context.fillRect(x, Math.max(0, y - 22), labelWidth, 22);
    context.fillStyle = "#b7ffe9";
    context.fillText(label, x + 6, Math.max(0, y - 6));
  });

  if (selectedObject) {
    const label = OBJECT_LABELS[selectedObject] || selectedObject.toUpperCase();
    const description = OBJECT_DESCRIPTIONS[selectedObject] ||
      "Objeto detectado localmente; descripción general no disponible.";
    objectDescription.textContent = `${label} · ${description}`;
    objectDescription.hidden = false;
  } else {
    objectDescription.hidden = true;
    objectDescription.textContent = "";
  }
}

function updateGestureZoom(result) {
  if (!gestureEnabled) return;
  const landmarks = result.landmarks?.[0];
  if (!landmarks) {
    smoothedGap = null;
    gestureMessage = "BUSCANDO MANO";
    updateFeatureReadouts();
    return;
  }

  const thumb = landmarks[4];
  const index = landmarks[8];
  const wrist = landmarks[0];
  const middleMcp = landmarks[9];
  const width = video.videoWidth;
  const height = video.videoHeight;
  const palmLength = Math.hypot((middleMcp.x - wrist.x) * width, (middleMcp.y - wrist.y) * height);
  if (palmLength <= 1) return;

  const gap = Math.hypot((index.x - thumb.x) * width, (index.y - thumb.y) * height) / palmLength;
  const clampedGap = Math.min(MAX_GAP_RATIO, Math.max(MIN_GAP_RATIO, gap));
  const targetZoom = MIN_ZOOM + ((clampedGap - MIN_GAP_RATIO) / (MAX_GAP_RATIO - MIN_GAP_RATIO)) * (MAX_ZOOM - MIN_ZOOM);
  const zoom = smoothedGap === null ? targetZoom : currentZoom + (targetZoom - currentZoom) * 0.24;
  smoothedGap = clampedGap;
  setZoom(zoom);

  if (gap <= MIN_GAP_RATIO + 0.04) gestureMessage = `PINZA CERRADA · ${currentZoom.toFixed(1)}x`;
  else if (gap >= MAX_GAP_RATIO - 0.04) gestureMessage = `PINZA ABIERTA · ${currentZoom.toFixed(1)}x`;
  else gestureMessage = `PINZA FLUIDA · ${currentZoom.toFixed(1)}x`;
  updateFeatureReadouts();
}

function processVideoFrame(now) {
  window.requestAnimationFrame(processVideoFrame);
  if (!mediaStream || video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA ||
      video.currentTime === lastVideoTime || now - lastFrameTime < 150) return;
  if ((!scanEnabled || !objectDetector) && (!gestureEnabled || !handLandmarker)) return;

  lastVideoTime = video.currentTime;
  lastFrameTime = now;
  if (scanEnabled && objectDetector) {
    try {
      lastObjectTimestamp = Math.max(Math.floor(now), lastObjectTimestamp + 1);
      latestDetections = objectDetector.detectForVideo(video, lastObjectTimestamp).detections;
    } catch (error) {
      console.error("Fallo el escaneo de objetos.", error);
      scanEnabled = false;
      updateFeatureReadouts();
      showError("El escaneo de objetos se detuvo por un error.");
    }
    drawDetections();
  }

  if (gestureEnabled && handLandmarker) {
    try {
      lastHandTimestamp = Math.max(Math.floor(now), lastHandTimestamp + 1);
      updateGestureZoom(handLandmarker.detectForVideo(video, lastHandTimestamp));
    } catch (error) {
      console.error("Fallo el seguimiento de la mano.", error);
      gestureEnabled = false;
      updateFeatureReadouts();
      showError("El zoom gestual se detuvo por un error.");
    }
  }
}

activateButton.addEventListener("click", connectCamera);
cameraButton.addEventListener("click", () => mediaStream ? disconnectCamera() : connectCamera());
voiceButton.addEventListener("click", toggleVoiceMode);
scanButton.addEventListener("click", toggleObjectScan);
gestureButton.addEventListener("click", toggleGestureZoom);
settingsToggle.addEventListener("click", toggleSettings);
fullscreenButton.addEventListener("click", toggleFullscreen);
zoomInput.addEventListener("input", () => setZoom(Number(zoomInput.value)));

document.addEventListener("keydown", (event) => {
  if (event.repeat || event.target instanceof HTMLInputElement) return;
  const key = event.key.toLowerCase();
  if (key === "v" && mediaStream) toggleVoiceMode();
  if (key === "e") void toggleObjectScan();
  if (key === "z") void toggleGestureZoom();
  if (key === "q" && mediaStream) disconnectCamera();
  if (key === "escape" && !settingsPanel.hidden) toggleSettings();
});

function updateClock() {
  clock.textContent = new Date().toLocaleTimeString("es", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  });
}

updateFeatureControls();
updateClock();
const clockTimer = window.setInterval(updateClock, 1000);
window.requestAnimationFrame(processVideoFrame);
window.addEventListener("resize", drawDetections);
window.addEventListener("beforeunload", () => {
  window.clearInterval(clockTimer);
  stopVoiceRecognition();
  if (mediaStream) mediaStream.getTracks().forEach((track) => track.stop());
  if (objectDetector) objectDetector.close();
  if (handLandmarker) handLandmarker.close();
});
