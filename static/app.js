// ─────────────────────────────────────────────
//  WebSocket instances
// ─────────────────────────────────────────────
let socket = null; // camera
let statsSocket = null; // camera-stats
let notifSocket = null; // notifications
let sensorSocket = null; // DHT22 sensors

// ─────────────────────────────────────────────
//  WebSocket URLs
// ─────────────────────────────────────────────
let WS_URL_CAMERA = null;
let WS_URL_STATS = null;
let WS_URL_NOTIF = null;
let WS_URL_SENSORS = null;

// ─────────────────────────────────────────────
//  DOM references
// ─────────────────────────────────────────────
const img = document.getElementById("video");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const deleteAllBtn = document.getElementById("deleteAllBtn");
const deleteAllNotifBtn = document.getElementById("deleteAllNotifBtn");
const notifElement = document.getElementById("notification");
const statusElement = document.getElementById("status");
const deleteStatusElement = document.getElementById("deleteStatus");

// Stats panel
const larvaeCountEl = document.getElementById("larvaeCount");
const densityCm2El = document.getElementById("densityCm2");
const densityM2El = document.getElementById("densityM2");
const statusIndicatorEl = document.getElementById("statusIndicator");
const alertBadgeEl = document.getElementById("alertBadge");

// Sensor panel
const tempValueEl = document.getElementById("tempValue");
const humidValueEl = document.getElementById("humidValue");
const sensorStatusEl = document.getElementById("sensorStatus");

let notificationTimeout = null;

// ─────────────────────────────────────────────
//  Init — fetch server info then connect
// ─────────────────────────────────────────────
async function initializeConnection() {
  try {
    statusElement.textContent = "🔍 Fetching server info...";

    const [cameraRes, notifRes] = await Promise.all([
      fetch(`http://${location.hostname}:8000/api/camera-info`),
      fetch(`http://${location.hostname}:8000/api/notification-info`),
    ]);

    if (!cameraRes.ok) throw new Error("Failed to fetch camera info");
    if (!notifRes.ok) throw new Error("Failed to fetch notification info");

    const cameraInfo = await cameraRes.json();
    const notifInfo = await notifRes.json();

    WS_URL_CAMERA = cameraInfo.websocket_url;
    WS_URL_STATS = `ws://${cameraInfo.ip}:${cameraInfo.port}/ws/camera-stats`;
    WS_URL_NOTIF = notifInfo.websocket_url;
    WS_URL_SENSORS = `ws://${cameraInfo.ip}:${cameraInfo.port}/ws/sensors`;

    statusElement.textContent = `✅ Connected to ${cameraInfo.ip}:${cameraInfo.port}`;

    connectNotifications();
    connectSensors();
    startBtn.disabled = false;
  } catch (error) {
    console.error("❌ Failed to fetch server info:", error);
    statusElement.textContent = "❌ Failed to connect to server";
    statusElement.style.color = "#ff6b6b";
  }
}

// ─────────────────────────────────────────────
//  Camera WebSocket
// ─────────────────────────────────────────────
startBtn.onclick = () => {
  if (socket || !WS_URL_CAMERA) return;
  socket = new WebSocket(WS_URL_CAMERA);

  socket.onopen = () => {
    startBtn.disabled = true;
    stopBtn.disabled = false;
    connectStats();
  };
  socket.onmessage = (event) => {
    img.src = "data:image/jpeg;base64," + event.data;
  };
  socket.onerror = (e) => console.error("❌ Camera WS error:", e);
  socket.onclose = () => {
    socket = null;
    img.src = "";
    startBtn.disabled = false;
    stopBtn.disabled = true;
    if (statsSocket) statsSocket.close();
  };
};

stopBtn.onclick = () => {
  if (socket) socket.close();
  if (statsSocket) statsSocket.close();
};

// ─────────────────────────────────────────────
//  Stats WebSocket  (live YOLO updates)
// ─────────────────────────────────────────────
function connectStats() {
  if (statsSocket || !WS_URL_STATS) return;
  statsSocket = new WebSocket(WS_URL_STATS);

  statsSocket.onopen = () => console.log("✅ Stats WS connected");
  statsSocket.onmessage = (event) => {
    try {
      updateStatsPanel(JSON.parse(event.data));
    } catch (e) {
      console.error("❌ Stats parse error:", e);
    }
  };
  statsSocket.onerror = (e) => console.error("❌ Stats WS error:", e);
  statsSocket.onclose = () => {
    statsSocket = null;
  };
}

function updateStatsPanel(stats) {
  larvaeCountEl.textContent = stats.larvae_count;
  densityCm2El.textContent = parseFloat(stats.density_cm2).toFixed(2);
  densityM2El.textContent = parseFloat(stats.density_m2).toFixed(1);

  if (stats.is_high_density) {
    statusIndicatorEl.className = "stat-value danger";
    alertBadgeEl.classList.add("active");
    densityCm2El.classList.add("danger");
  } else {
    statusIndicatorEl.className = "stat-value good";
    alertBadgeEl.classList.remove("active");
    densityCm2El.classList.remove("danger");
  }
}

// ─────────────────────────────────────────────
//  Sensor WebSocket  (live MQTT updates)
// ─────────────────────────────────────────────
function connectSensors() {
  if (sensorSocket) return;
  WS_URL_SENSORS =
    WS_URL_SENSORS || `ws://${location.hostname}:8000/ws/sensors`;
  sensorSocket = new WebSocket(WS_URL_SENSORS);

  sensorSocket.onopen = () => {
    sensorStatusEl.innerHTML = `<span class="sensor-dot"></span>Connected — waiting for data...`;
  };
  sensorSocket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      // ignore ping keepalives
      if (data.ping) return;
      updateSensorPanel(data.temperature, data.humidity);
    } catch {
      sensorStatusEl.innerHTML = `<span class="sensor-dot"></span>Raw: ${event.data}`;
    }
  };
  sensorSocket.onerror = () => {
    sensorStatusEl.textContent = "❌ Sensor connection error";
  };
  sensorSocket.onclose = () => {
    sensorSocket = null;
    sensorStatusEl.innerHTML = `<span class="sensor-dot" style="background:var(--danger)"></span>Reconnecting...`;
    setTimeout(connectSensors, 3000);
  };
}

function updateSensorPanel(temperature, humidity) {
  if (temperature && temperature !== "--") {
    tempValueEl.textContent = parseFloat(temperature).toFixed(1);
  }
  if (humidity && humidity !== "--") {
    humidValueEl.textContent = parseFloat(humidity).toFixed(1);
  }
  const now = new Date().toLocaleTimeString();
  sensorStatusEl.innerHTML = `<span class="sensor-dot"></span>Last updated: ${now}`;
}

// ─────────────────────────────────────────────
//  Notification WebSocket
// ─────────────────────────────────────────────
function connectNotifications() {
  if (notifSocket || !WS_URL_NOTIF) return;
  notifSocket = new WebSocket(WS_URL_NOTIF);

  notifSocket.onopen = () => console.log("✅ Notification WS connected");
  notifSocket.onmessage = (event) => {
    try {
      handleNotification(JSON.parse(event.data));
    } catch (e) {
      console.error("❌ Notification parse error:", e);
    }
  };
  notifSocket.onerror = (e) => console.error("❌ Notif WS error:", e);
  notifSocket.onclose = () => {
    notifSocket = null;
    setTimeout(connectNotifications, 3000);
  };
}

function handleNotification(n) {
  console.log("📨 Notification:", n);

  // ignore ping keepalives
  if (n.ping) return;

  const isHourly = n.type === "hourly_report";
  const isDensity = n.type === "density_alert";

  // ── Update stats panel ─────────────────────────────────────────────────
  if (n.larvae_count !== undefined) {
    larvaeCountEl.textContent = n.larvae_count;
  }
  if (n.density_per_cm2 !== undefined) {
    const d = parseFloat(n.density_per_cm2);
    densityCm2El.textContent = d.toFixed(2);
    densityM2El.textContent = (d * 10000).toFixed(1);

    if (d > 1.25) {
      statusIndicatorEl.className = "stat-value danger";
      alertBadgeEl.classList.add("active");
      densityCm2El.classList.add("danger");
    } else {
      statusIndicatorEl.className = "stat-value good";
      alertBadgeEl.classList.remove("active");
      densityCm2El.classList.remove("danger");
    }
  }

  // ── Update sensor panel (hourly report only) ───────────────────────────
  if (isHourly && n.temperature && n.temperature !== "--") {
    updateSensorPanel(n.temperature, n.humidity);
  }

  // ── Build toast ────────────────────────────────────────────────────────
  if (notificationTimeout) clearTimeout(notificationTimeout);

  let rows = "";

  if (n.larvae_count !== undefined) {
    rows += `
      <div class="toast-row">
        <span>🪱 Larvae</span>
        <strong>${n.larvae_count}&nbsp;(${parseFloat(n.density_per_cm2).toFixed(2)}/cm²)</strong>
      </div>`;
  }

  if (isHourly && n.temperature && n.temperature !== "--") {
    rows += `
      <div class="toast-row">
        <span>🌡️ Temp</span>
        <strong>${parseFloat(n.temperature).toFixed(1)}°C</strong>
      </div>
      <div class="toast-row">
        <span>💧 Humidity</span>
        <strong>${parseFloat(n.humidity).toFixed(1)}%</strong>
      </div>`;
  }

  const bg = isDensity
    ? "linear-gradient(135deg,#c0392b,#e74c3c)"
    : "linear-gradient(135deg,#667eea,#764ba2)";
  const duration = isDensity ? 8000 : 6000;

  notifElement.innerHTML = `
    <div class="toast" style="background:${bg}">
      <div class="toast-title">${n.title}</div>
      ${rows}
    </div>`;

  notificationTimeout = setTimeout(() => {
    notifElement.innerHTML = "";
  }, duration);
}

// ─────────────────────────────────────────────
//  Delete All Images
// ─────────────────────────────────────────────
deleteAllBtn.onclick = async () => {
  if (!confirm("⚠️ Delete ALL saved images? This cannot be undone!")) return;
  try {
    deleteAllBtn.disabled = true;
    deleteAllBtn.textContent = "🗑️ Deleting...";
    showDeleteStatus("", "⏳ Deleting all images...");

    const res = await fetch(
      `http://${location.hostname}:8000/api/images/delete-all`,
      { method: "DELETE" },
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const result = await res.json();
    showDeleteStatus("success", `✅ Deleted ${result.total_images} images!`);
  } catch (e) {
    showDeleteStatus("error", `❌ Failed: ${e.message}`);
  } finally {
    deleteAllBtn.disabled = false;
    deleteAllBtn.textContent = "🗑️ Delete Images";
  }
};

// ─────────────────────────────────────────────
//  Delete All Notifications
// ─────────────────────────────────────────────
deleteAllNotifBtn.onclick = async () => {
  if (!confirm("⚠️ Delete ALL notifications? This cannot be undone!")) return;
  try {
    deleteAllNotifBtn.disabled = true;
    deleteAllNotifBtn.textContent = "🔔 Deleting...";
    showDeleteStatus("", "⏳ Deleting all notifications...");

    const res = await fetch(
      `http://${location.hostname}:8000/api/notifications/delete-all`,
      { method: "DELETE" },
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const result = await res.json();
    showDeleteStatus(
      "success",
      `✅ Deleted ${result.deleted_count} notifications!`,
    );
  } catch (e) {
    showDeleteStatus("error", `❌ Failed: ${e.message}`);
  } finally {
    deleteAllNotifBtn.disabled = false;
    deleteAllNotifBtn.textContent = "🔔 Delete Notifications";
  }
};

// ─────────────────────────────────────────────
//  Helpers
// ─────────────────────────────────────────────
function showDeleteStatus(cls, msg) {
  deleteStatusElement.style.display = "block";
  deleteStatusElement.className = cls;
  deleteStatusElement.textContent = msg;
  if (cls)
    setTimeout(() => {
      deleteStatusElement.style.display = "none";
    }, 5000);
}

// ─────────────────────────────────────────────
//  Boot
// ─────────────────────────────────────────────
window.addEventListener("load", () => {
  startBtn.disabled = true;
  initializeConnection();
});
