let socket = null;
let notifSocket = null;
let notificationTimeout = null;

const img = document.getElementById("video");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const notifElement = document.getElementById("notification");
const statusElement = document.getElementById("status");

let WS_URL_CAMERA = null;
let WS_URL_NOTIF = null;

// Fetch server info on page load
async function initializeConnection() {
  try {
    statusElement.textContent = "🔍 Fetching server info...";

    // Fetch camera info
    const cameraResponse = await fetch(
      `http://${location.hostname}:8000/api/camera-info`,
    );
    if (!cameraResponse.ok) throw new Error("Failed to fetch camera info");
    const cameraInfo = await cameraResponse.json();

    // Fetch notification info
    const notifResponse = await fetch(
      `http://${location.hostname}:8000/api/notification-info`,
    );
    if (!notifResponse.ok) throw new Error("Failed to fetch notification info");
    const notifInfo = await notifResponse.json();

    console.log("📹 Camera Info:", cameraInfo);
    console.log("🔔 Notification Info:", notifInfo);

    // Use the WebSocket URLs from API
    WS_URL_CAMERA = cameraInfo.websocket_url;
    WS_URL_NOTIF = notifInfo.websocket_url;

    statusElement.textContent = `✅ Connected to ${cameraInfo.ip}:${cameraInfo.port}`;

    // Auto-connect to notifications
    connectNotifications();

    // Enable start button
    startBtn.disabled = false;
  } catch (error) {
    console.error("❌ Failed to fetch server info:", error);
    statusElement.textContent = "❌ Failed to connect to server";
    statusElement.style.color = "#ff6b6b";
  }
}

// Handle Camera WebSocket
startBtn.onclick = () => {
  if (socket || !WS_URL_CAMERA) return;

  console.log("📹 Connecting to:", WS_URL_CAMERA);
  socket = new WebSocket(WS_URL_CAMERA);

  socket.onopen = () => {
    console.log("✅ Camera WebSocket connected");
    startBtn.disabled = true;
    stopBtn.disabled = false;
  };

  socket.onmessage = (event) => {
    img.src = "data:image/jpeg;base64," + event.data;
  };

  socket.onerror = (error) => {
    console.error("❌ Camera WebSocket error:", error);
  };

  socket.onclose = () => {
    console.log("🔴 Camera WebSocket closed");
    socket = null;
    img.src = "";
    startBtn.disabled = false;
    stopBtn.disabled = true;
  };
};

stopBtn.onclick = () => {
  if (socket) {
    socket.close();
  }
};

// Handle Notification WebSocket
function connectNotifications() {
  if (notifSocket || !WS_URL_NOTIF) return;

  console.log("🔔 Connecting to:", WS_URL_NOTIF);
  notifSocket = new WebSocket(WS_URL_NOTIF);

  notifSocket.onopen = () => {
    console.log("✅ Notification WebSocket connected");
  };

  notifSocket.onmessage = (event) => {
    console.log("📨 Notification received:", event.data);
    try {
      const notification = JSON.parse(event.data);
      displayNotification(notification);
    } catch (error) {
      console.error("❌ Error parsing notification:", error);
    }
  };

  notifSocket.onerror = (error) => {
    console.error("❌ Notification WebSocket error:", error);
  };

  notifSocket.onclose = () => {
    console.log("🔴 Notification WebSocket closed");
    notifSocket = null;

    // Auto-reconnect after 3 seconds
    setTimeout(() => {
      console.log("🔄 Reconnecting to notifications...");
      connectNotifications();
    }, 3000);
  };
}

// Function to display notifications
function displayNotification(notification) {
  // Clear previous timeout
  if (notificationTimeout) {
    clearTimeout(notificationTimeout);
  }

  // Display notification
  notifElement.innerHTML = `
    <div style="
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 15px 20px;
      border-radius: 10px;
      margin: 10px 0;
      box-shadow: 0 4px 6px rgba(0,0,0,0.1);
      animation: slideIn 0.3s ease-out;
    ">
      <strong style="font-size: 18px; display: block; margin-bottom: 5px;">
        ${notification.title}
      </strong>
      <span style="font-size: 14px;">
        ${notification.message}
      </span>
    </div>
  `;

  // Auto-clear notification after 3 seconds
  notificationTimeout = setTimeout(() => {
    notifElement.innerHTML = "";
  }, 3000);
}

// Add CSS animation
const style = document.createElement("style");
style.textContent = `
  @keyframes slideIn {
    from {
      transform: translateY(-20px);
      opacity: 0;
    }
    to {
      transform: translateY(0);
      opacity: 1;
    }
  }
`;
document.head.appendChild(style);

// Initialize connection when page loads
window.addEventListener("load", () => {
  console.log("🚀 Page loaded, initializing connection...");
  startBtn.disabled = true; // Disable until server info is fetched
  initializeConnection();
});
