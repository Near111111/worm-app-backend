let socket = null;
let statsSocket = null; // NEW: Stats WebSocket
let notifSocket = null;
let notificationTimeout = null;

const img = document.getElementById("video");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const deleteAllBtn = document.getElementById("deleteAllBtn");
const deleteAllNotifBtn = document.getElementById("deleteAllNotifBtn");
const notifElement = document.getElementById("notification");
const statusElement = document.getElementById("status");
const deleteStatusElement = document.getElementById("deleteStatus");

// Stats elements
const larvaeCountEl = document.getElementById("larvaeCount");
const densityCm2El = document.getElementById("densityCm2");
const densityM2El = document.getElementById("densityM2");
const statusIndicatorEl = document.getElementById("statusIndicator");
const alertBadgeEl = document.getElementById("alertBadge");

let WS_URL_CAMERA = null;
let WS_URL_STATS = null; // NEW: Stats WebSocket URL
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
    WS_URL_STATS = `ws://${cameraInfo.ip}:${cameraInfo.port}/ws/camera-stats`; // NEW
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

    // Also connect to stats WebSocket
    connectStats();
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

    // Close stats socket too
    if (statsSocket) {
      statsSocket.close();
    }
  };
};

stopBtn.onclick = () => {
  if (socket) {
    socket.close();
  }
  if (statsSocket) {
    statsSocket.close();
  }
};

// NEW: Handle Stats WebSocket
function connectStats() {
  if (statsSocket || !WS_URL_STATS) return;

  console.log("📊 Connecting to stats:", WS_URL_STATS);
  statsSocket = new WebSocket(WS_URL_STATS);

  statsSocket.onopen = () => {
    console.log("✅ Stats WebSocket connected");
  };

  statsSocket.onmessage = (event) => {
    try {
      const stats = JSON.parse(event.data);
      updateStatsDisplay(stats);
    } catch (error) {
      console.error("❌ Error parsing stats:", error);
    }
  };

  statsSocket.onerror = (error) => {
    console.error("❌ Stats WebSocket error:", error);
  };

  statsSocket.onclose = () => {
    console.log("🔴 Stats WebSocket closed");
    statsSocket = null;
  };
}

// NEW: Update stats display
function updateStatsDisplay(stats) {
  // Update values
  larvaeCountEl.textContent = stats.larvae_count;
  densityCm2El.textContent = stats.density_cm2.toFixed(2);
  densityM2El.textContent = stats.density_m2.toFixed(1);

  // Update status indicator
  if (stats.is_high_density) {
    statusIndicatorEl.textContent = "●";
    statusIndicatorEl.style.color = "#ff6b6b";
    statusIndicatorEl.classList.add("highlight");

    // Show alert badge
    alertBadgeEl.classList.add("active");

    // Highlight density values
    densityCm2El.classList.add("highlight");
  } else {
    statusIndicatorEl.textContent = "●";
    statusIndicatorEl.style.color = "#2ecc71";
    statusIndicatorEl.classList.remove("highlight");

    // Hide alert badge
    alertBadgeEl.classList.remove("active");

    // Remove highlight
    densityCm2El.classList.remove("highlight");
  }
}

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

// Handle Delete All Images
deleteAllBtn.onclick = async () => {
  if (
    !confirm(
      "⚠️ Are you sure you want to delete ALL saved images?\n\nThis action cannot be undone!",
    )
  ) {
    return;
  }

  try {
    deleteAllBtn.disabled = true;
    deleteAllBtn.textContent = "🗑️ Deleting...";

    deleteStatusElement.style.display = "block";
    deleteStatusElement.className = "";
    deleteStatusElement.textContent = "⏳ Deleting all images...";

    const response = await fetch(
      `http://${location.hostname}:8000/api/images/delete-all`,
      {
        method: "DELETE",
      },
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log("🗑️ Delete result:", result);

    deleteStatusElement.className = "success";
    deleteStatusElement.textContent = `✅ Successfully deleted ${result.total_images} images from storage and database!`;

    setTimeout(() => {
      deleteStatusElement.style.display = "none";
    }, 5000);
  } catch (error) {
    console.error("❌ Failed to delete images:", error);

    deleteStatusElement.className = "error";
    deleteStatusElement.textContent = `❌ Failed to delete images: ${error.message}`;

    setTimeout(() => {
      deleteStatusElement.style.display = "none";
    }, 5000);
  } finally {
    deleteAllBtn.disabled = false;
    deleteAllBtn.textContent = "🗑️ Delete All Images";
  }
};

// Handle Delete All Notifications
deleteAllNotifBtn.onclick = async () => {
  if (
    !confirm(
      "⚠️ Are you sure you want to delete ALL notifications?\n\nThis action cannot be undone!",
    )
  ) {
    return;
  }

  try {
    deleteAllNotifBtn.disabled = true;
    deleteAllNotifBtn.textContent = "🔔 Deleting...";

    deleteStatusElement.style.display = "block";
    deleteStatusElement.className = "";
    deleteStatusElement.textContent = "⏳ Deleting all notifications...";

    const response = await fetch(
      `http://${location.hostname}:8000/api/notifications/delete-all`,
      {
        method: "DELETE",
      },
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log("🔔 Delete result:", result);

    deleteStatusElement.className = "success";
    deleteStatusElement.textContent = `✅ Successfully deleted ${result.deleted_count} notifications from database!`;

    setTimeout(() => {
      deleteStatusElement.style.display = "none";
    }, 5000);
  } catch (error) {
    console.error("❌ Failed to delete notifications:", error);

    deleteStatusElement.className = "error";
    deleteStatusElement.textContent = `❌ Failed to delete notifications: ${error.message}`;

    setTimeout(() => {
      deleteStatusElement.style.display = "none";
    }, 5000);
  } finally {
    deleteAllNotifBtn.disabled = false;
    deleteAllNotifBtn.textContent = "🔔 Delete All Notifications";
  }
};

// Initialize connection when page loads
window.addEventListener("load", () => {
  console.log("🚀 Page loaded, initializing connection...");
  startBtn.disabled = true;
  initializeConnection();
});
