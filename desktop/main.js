const { app, BrowserWindow } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

let mainWindow;
let fastapiProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // ✅ DevTools helps debugging blank screen/errors
  mainWindow.webContents.openDevTools();

  const isDev = !app.isPackaged;

  if (isDev) {
    // ✅ DEV MODE: Load Vite server
    mainWindow.loadURL("http://localhost:5173");
  } else {
    // ✅ PROD MODE: Load built React dist
    mainWindow.loadFile(
      path.join(__dirname, "..", "frontend", "dist", "index.html")
    );
  }
}

function startFastAPI() {
  // ✅ IMPORTANT: Use your backend venv python.exe (Windows)
  const pythonExecutable = path.join(
    __dirname,
    "..",
    "backend",
    "venv",
    "Scripts",
    "python.exe"
  );

  const serverScript = path.join(__dirname, "..", "backend", "run_server.py");

  fastapiProcess = spawn(pythonExecutable, [serverScript], {
    shell: false,
    cwd: path.join(__dirname, "..", "backend"),
  });

  fastapiProcess.stdout.on("data", (data) => {
    console.log(`FastAPI stdout: ${data}`);
  });

  fastapiProcess.stderr.on("data", (data) => {
    console.error(`FastAPI stderr: ${data}`);
  });

  fastapiProcess.on("close", (code) => {
    console.log(`FastAPI process exited with code ${code}`);
  });
}

app.whenReady().then(() => {
  startFastAPI();
  createWindow();
});

app.on("window-all-closed", () => {
  if (fastapiProcess) {
    fastapiProcess.kill();
  }
  app.quit();
});
