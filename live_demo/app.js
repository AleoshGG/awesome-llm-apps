const $ = (selector) => document.querySelector(selector);
const transcriptEl = $("#transcript");
const checklistEl = $("#checklist");
const activityList = $("#activityList");
const callStatus = $("#callStatus");
const liveDot = $("#liveDot");
const cameraButton = $("#cameraButton");
const micButton = $("#micButton");
const cameraStage = $("#cameraStage");
const cameraPreview = $("#cameraPreview");
const frameCanvas = $("#frameCanvas");
const cameraFlash = $("#cameraFlash");
const profileImage = $("#profileImage");
const portraitPlaceholder = $("#portraitPlaceholder");
const portraitShell = document.querySelector(".portrait-shell");
const imageStatus = $("#imageStatus");
const textForm = $("#textForm");
const textInput = $("#textInput");
const downloadButton = $("#downloadButton");

const API_ORIGIN = window.location.protocol === "file:" ? "http://127.0.0.1:4177" : window.location.origin;
const WS_ORIGIN = API_ORIGIN.replace(/^http/, "ws");
const FRAME_INTERVAL_MS = 850;
const FRAME_WIDTH = 640;

if (window.location.protocol === "file:") window.location.replace(`${API_ORIGIN}/index.html`);

const emptyState = {
  profile: {}, checklist: [], progress: 0, photo: null,
  avatar: { status: "idle", url: null }, transcript: [], tool_activity: [],
  card_ready: false, print_ready: false,
};

let state = { ...emptyState };
let sessionId = null;
let socket = null;
let connectionPromise = null;
let generation = 0;
let cameraStream = null;
let frameTimer = null;
let audioStream = null;
let audioContext = null;
let inputSource = null;
let inputProcessor = null;
let isRecording = false;
let nextPlaybackTime = 0;
const playbackSources = new Set();

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}

function setStatus(text, online = false) {
  callStatus.textContent = text;
  liveDot.classList.toggle("online", online);
}

function setState(next) {
  state = {
    ...emptyState, ...next,
    transcript: next.transcript ?? state.transcript,
    tool_activity: next.tool_activity ?? state.tool_activity,
  };
  render();
}

function render() {
  const profile = state.profile || {};
  $("#cardName").textContent = profile.full_name || "Tu nombre";
  $("#cardAge").textContent = profile.age ? `${profile.age} años` : "— años";
  $("#cardDepartment").textContent = (profile.department || "TU DEPARTAMENTO").toUpperCase();
  $("#cardDescription").textContent = profile.short_description || "Tu rol, superpoder o afición aparecerá aquí.";

  const completed = (state.checklist || []).filter((item) => item.complete).length;
  $("#progressBadge").textContent = `${completed} / 5`;
  $("#percentLabel").textContent = `${state.progress || 0}%`;
  checklistEl.innerHTML = (state.checklist || [])
    .map((item) => `<li class="${item.complete ? "complete" : ""}">${escapeHtml(item.label)}</li>`).join("");

  const avatar = state.avatar || { status: "idle" };
  const imageUrl = avatar.url || state.photo?.url;
  if (imageUrl) {
    const absolute = new URL(imageUrl, API_ORIGIN).href;
    if (profileImage.src !== absolute) profileImage.src = absolute;
    profileImage.hidden = false;
    portraitPlaceholder.hidden = true;
  } else {
    profileImage.hidden = true;
    portraitPlaceholder.hidden = false;
  }
  portraitShell.classList.toggle("generating", avatar.status === "generating");
  if (avatar.status === "generating") imageStatus.textContent = "Creando avatar…";
  else if (avatar.status === "ready") imageStatus.textContent = "Avatar listo";
  else if (avatar.status === "failed") imageStatus.textContent = "Usando foto · reintenta";
  else if (state.photo) imageStatus.textContent = "Foto capturada";
  else imageStatus.textContent = "Esperando foto";

  if (state.card_ready) {
    $("#resultTitle").textContent = "Tu tarjeta está lista";
    $("#resultHint").textContent = "Ábrela y guárdala como PDF desde el navegador.";
  } else if (avatar.status === "generating") {
    $("#resultTitle").textContent = "El avatar se genera en segundo plano";
    $("#resultHint").textContent = "Sigue conversando: los datos se actualizan sin esperar.";
  } else if (state.photo) {
    $("#resultTitle").textContent = "Foto tomada";
    $("#resultHint").textContent = "Ahora cuéntanos sobre ti.";
  } else {
    $("#resultTitle").textContent = "Primero, tu foto";
    $("#resultHint").textContent = "Después conversaremos mientras creamos el avatar.";
  }
  downloadButton.disabled = !state.print_ready;
  renderTranscript();
  renderActivity();
}

function renderTranscript() {
  transcriptEl.innerHTML = (state.transcript || []).map((turn) => {
    const cls = turn.speaker === "Agent" ? "agent" : turn.speaker === "System" ? "system" : "user";
    const who = turn.speaker === "Agent" ? "AI" : turn.speaker === "System" ? "!" : "TÚ";
    return `<article class="turn ${cls} ${turn.streaming ? "streaming" : ""}"><span class="who">${who}</span><p>${escapeHtml(turn.text)}</p></article>`;
  }).join("");
  transcriptEl.scrollTop = transcriptEl.scrollHeight;
}

function renderActivity() {
  const entries = [...(state.tool_activity || [])].slice(-6).reverse();
  if (state.avatar?.status === "generating" && !entries.some((item) => item.name === "generate_corporate_avatar" && item.phase === "running")) {
    entries.unshift({ id: "avatar-state", phase: "running", headline: "Creando avatar Neurotry" });
  }
  activityList.innerHTML = entries.length ? entries.map((item) => {
    const duration = item.duration_ms != null ? `${item.duration_ms} ms` : item.phase === "running" ? "trabajando sin bloquear" : "";
    return `<li class="${escapeHtml(item.phase || "running")}"><span>${escapeHtml(item.headline || item.name)}<small>${escapeHtml(duration)}</small></span></li>`;
  }).join("") : `<li class="activity-empty"><span>Las tareas aparecerán aquí.</span></li>`;
}

function upsertTurn(speaker, text, final, id) {
  if (!String(text || "").trim()) return;
  const transcript = [...(state.transcript || [])];
  const index = transcript.findIndex((turn) => turn.id === id);
  const turn = { id, speaker, text, streaming: !final };
  if (index >= 0) transcript[index] = turn; else transcript.push(turn);
  setState({ ...state, transcript });
}

function mergeById(authoritative, local) {
  const values = new Map((authoritative || []).map((item) => [item.id, item]));
  for (const item of local || []) if (!values.has(item.id)) values.set(item.id, item);
  return [...values.values()];
}

async function api(path, options = {}) {
  const response = await fetch(`${API_ORIGIN}${path}`, { headers: { "Content-Type": "application/json" }, ...options });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || `Error ${response.status}`);
  return payload;
}

function fireFlash() {
  cameraFlash.classList.remove("fire");
  void cameraFlash.offsetWidth;
  cameraFlash.classList.add("fire");
}

async function connectLive() {
  if (connectionPromise) return connectionPromise;
  if (!sessionId) throw new Error("La sesión aún no está lista.");
  const epoch = generation;
  socket = new WebSocket(`${WS_ORIGIN}/ws/live?session_id=${encodeURIComponent(sessionId)}`);
  connectionPromise = new Promise((resolve, reject) => {
    let ready = false;
    const timeout = setTimeout(() => { reject(new Error("La conexión tardó demasiado.")); socket?.close(); }, 20000);
    socket.onmessage = (event) => {
      if (epoch !== generation) return;
      const message = JSON.parse(event.data);
      if (message.session_id !== sessionId) return;
      if (message.type === "ready") {
        ready = true; clearTimeout(timeout); setStatus("En vivo", true); resolve();
      } else if (message.type === "state") {
        setState({ ...message.state, transcript: mergeById(message.state.transcript, state.transcript), tool_activity: mergeById(message.state.tool_activity, state.tool_activity) });
      } else if (message.type === "transcript") {
        upsertTurn(message.speaker, message.text, message.final, message.id);
      } else if (message.type === "tool") {
        const others = (state.tool_activity || []).filter((item) => item.id !== message.id);
        setState({ ...state, tool_activity: [...others, message] });
      } else if (message.type === "camera_flash") {
        fireFlash();
      } else if (message.type === "audio") {
        playPcm24(message.data);
      } else if (message.type === "interrupted") {
        stopPlayback();
      } else if (message.type === "error") {
        appendSystem(message.message);
        if (!ready) { reject(new Error(message.message)); socket.close(); }
      }
    };
    socket.onerror = () => { clearTimeout(timeout); reject(new Error("No se pudo abrir la conexión en vivo.")); };
    socket.onclose = () => {
      clearTimeout(timeout);
      if (epoch !== generation) return;
      socket = null; connectionPromise = null; stopVoice(); stopCamera(false);
      setStatus("Desconectado", false);
      if (!ready) reject(new Error("La conexión terminó antes de estar lista."));
    };
  });
  return connectionPromise;
}

function appendSystem(text) {
  setState({ ...state, transcript: [...(state.transcript || []), { id: crypto.randomUUID(), speaker: "System", text }] });
}

function stopPlayback() {
  for (const source of playbackSources) { try { source.stop(); } catch (_) {} }
  playbackSources.clear();
  nextPlaybackTime = audioContext?.currentTime || 0;
}

function playPcm24(encoded) {
  audioContext = audioContext || new AudioContext();
  const binary = atob(encoded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  const pcm = new Int16Array(bytes.buffer);
  const buffer = audioContext.createBuffer(1, pcm.length, 24000);
  const channel = buffer.getChannelData(0);
  for (let i = 0; i < pcm.length; i += 1) channel[i] = pcm[i] / 32768;
  const source = audioContext.createBufferSource();
  source.buffer = buffer; source.connect(audioContext.destination);
  const starts = Math.max(audioContext.currentTime, nextPlaybackTime);
  playbackSources.add(source); source.onended = () => playbackSources.delete(source);
  source.start(starts); nextPlaybackTime = starts + buffer.duration;
}

function resample(input, inputRate, outputRate) {
  const ratio = inputRate / outputRate;
  const pcm = new Int16Array(Math.floor(input.length / ratio));
  for (let i = 0; i < pcm.length; i += 1) {
    const index = i * ratio, before = Math.floor(index), after = Math.min(before + 1, input.length - 1), weight = index - before;
    const sample = Math.max(-1, Math.min(1, input[before] * (1 - weight) + input[after] * weight));
    pcm[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;
  }
  return pcm;
}

function toBase64(buffer) {
  let value = ""; const bytes = new Uint8Array(buffer);
  for (const byte of bytes) value += String.fromCharCode(byte);
  return btoa(value);
}

async function startVoice() {
  if (isRecording) return stopVoice();
  try {
    audioContext = audioContext || new AudioContext(); await audioContext.resume(); await connectLive();
    audioStream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
    inputSource = audioContext.createMediaStreamSource(audioStream);
    inputProcessor = audioContext.createScriptProcessor(4096, 1, 1);
    inputProcessor.onaudioprocess = (event) => {
      event.outputBuffer.getChannelData(0).fill(0);
      if (!socket || socket.readyState !== WebSocket.OPEN) return;
      socket.send(JSON.stringify({ type: "audio", data: toBase64(resample(event.inputBuffer.getChannelData(0), audioContext.sampleRate, 16000).buffer) }));
    };
    inputSource.connect(inputProcessor); inputProcessor.connect(audioContext.destination);
    isRecording = true; micButton.classList.add("active"); micButton.querySelector("span:last-child").textContent = "Escuchando";
  } catch (error) { appendSystem(`No se pudo iniciar el micrófono: ${error.message}`); stopVoice(); }
}

function stopVoice() {
  isRecording = false; inputProcessor?.disconnect(); inputSource?.disconnect(); audioStream?.getTracks().forEach((track) => track.stop());
  inputProcessor = inputSource = audioStream = null; micButton.classList.remove("active"); micButton.querySelector("span:last-child").textContent = "Hablar";
}

async function startCamera() {
  if (cameraStream) return stopCamera(true);
  try {
    await connectLive();
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: { width: { ideal: 960 }, height: { ideal: 720 }, facingMode: "user" } });
    cameraPreview.srcObject = cameraStream; cameraStage.classList.add("active"); cameraButton.classList.add("active"); cameraButton.querySelector("span:last-child").textContent = "Apagar cámara";
    socket.send(JSON.stringify({ type: "camera_state", enabled: true }));
    frameTimer = setInterval(sendFrame, FRAME_INTERVAL_MS); sendFrame();
  } catch (error) { appendSystem(`No se pudo iniciar la cámara: ${error.message}`); stopCamera(false); }
}

function stopCamera(notify = true) {
  if (frameTimer) clearInterval(frameTimer); frameTimer = null;
  cameraStream?.getTracks().forEach((track) => track.stop()); cameraStream = null; cameraPreview.srcObject = null;
  cameraStage.classList.remove("active"); cameraButton.classList.remove("active"); cameraButton.querySelector("span:last-child").textContent = "Encender cámara";
  if (notify && socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: "camera_state", enabled: false }));
}

function sendFrame() {
  if (!cameraStream || !cameraPreview.videoWidth || socket?.readyState !== WebSocket.OPEN) return;
  const scale = FRAME_WIDTH / cameraPreview.videoWidth;
  frameCanvas.width = FRAME_WIDTH; frameCanvas.height = Math.round(cameraPreview.videoHeight * scale);
  frameCanvas.getContext("2d").drawImage(cameraPreview, 0, 0, frameCanvas.width, frameCanvas.height);
  const data = frameCanvas.toDataURL("image/jpeg", .72).split(",")[1];
  socket.send(JSON.stringify({ type: "video", data }));
}

async function createSession(resume = false) {
  generation += 1; const epoch = generation; const previous = sessionId || sessionStorage.getItem("neurotrySession");
  socket?.close(); socket = null; connectionPromise = null; stopVoice(); stopCamera(false); stopPlayback();
  sessionId = null; setState({ ...emptyState }); setStatus("Preparando sesión");
  try {
    let payload;
    if (resume && previous) payload = await api(`/api/sessions/${previous}`).catch(() => null);
    else if (previous) await api(`/api/sessions/${previous}`, { method: "DELETE" }).catch(() => {});
    payload = payload || await api("/api/sessions", { method: "POST" });
    if (epoch !== generation) return;
    sessionId = payload.session_id; sessionStorage.setItem("neurotrySession", sessionId); setState(payload.state);
    setStatus(payload.has_api_key ? "Lista para comenzar" : "Falta API key", false); textInput.focus();
  } catch (error) { setStatus("Backend no disponible"); appendSystem(error.message); }
}

cameraButton.addEventListener("click", startCamera);
micButton.addEventListener("click", startVoice);
$("#newSessionButton").addEventListener("click", () => createSession(false));
downloadButton.addEventListener("click", () => {
  if (state.print_ready && sessionId) window.open(`${API_ORIGIN}/api/sessions/${sessionId}/business-card`, "_blank", "noopener");
});
textForm.addEventListener("submit", async (event) => {
  event.preventDefault(); const value = textInput.value.trim(); if (!value) return; textInput.value = "";
  try {
    await connectLive(); const id = crypto.randomUUID(); socket.send(JSON.stringify({ type: "text", text: value, id })); upsertTurn("User", value, true, id);
  } catch (error) { textInput.value = value; appendSystem(error.message); }
});
window.addEventListener("pagehide", () => { if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: "close" })); });
profileImage.addEventListener("error", () => { profileImage.hidden = true; portraitPlaceholder.hidden = false; });

createSession(true);
