let socket = null;

const img = document.getElementById("video");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");

const WS_URL = `ws://${location.hostname}:8000/ws/camera`;

startBtn.onclick = () => {
  if (socket) return;

  socket = new WebSocket(WS_URL);

  socket.onopen = () => {
    console.log("WebSocket connected");
    startBtn.disabled = true;
    stopBtn.disabled = false;
  };

  socket.onmessage = (event) => {
    img.src = "data:image/jpeg;base64," + event.data;
  };

  socket.onclose = () => {
    console.log("WebSocket closed");
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
