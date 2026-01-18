let socket = null;
let notifSocket = null;

const img = document.getElementById("video");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const notifElement = document.getElementById("notification"); // Add notification area

// WebSocket URL for Camera Stream
const WS_URL_CAMERA = `ws://${location.hostname}:8000/ws/camera`;
// WebSocket URL for Notifications
const WS_URL_NOTIF = `ws://${location.hostname}:8000/ws/notify`;

// Handle Camera WebSocket
startBtn.onclick = () => {
  if (socket) return;

  socket = new WebSocket(WS_URL_CAMERA);

  socket.onopen = () => {
    console.log("WebSocket connected to camera");
    startBtn.disabled = true;
    stopBtn.disabled = false;
  };

  socket.onmessage = (event) => {
    img.src = "data:image/jpeg;base64," + event.data;
  };

  socket.onclose = () => {
    console.log("WebSocket closed for camera");
    socket = null;
    img.src = "";
    startBtn.disabled = false;
    stopBtn.disabled = true;
  };
};

// Handle Notification WebSocket
notifSocket = new WebSocket(WS_URL_NOTIF);

notifSocket.onopen = () => {
  console.log("WebSocket connected to notifications");
};

notifSocket.onmessage = (event) => {
  const notification = JSON.parse(event.data); // Assuming the backend sends JSON
  displayNotification(notification);
};

notifSocket.onclose = () => {
  console.log("WebSocket closed for notifications");
};

// Function to display notifications
function displayNotification(notification) {
  notifElement.innerHTML = `
    <div style="background-color: yellow; padding: 10px; border-radius: 5px;">
      <strong>${notification.title}</strong><br/>
      ${notification.message}
    </div>
  `;
}

stopBtn.onclick = () => {
  if (socket) {
    socket.close();
  }
};
