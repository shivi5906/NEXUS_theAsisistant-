import { app, BrowserWindow } from "electron";

let mainWindow: BrowserWindow | null = null;

function loadReactApp() {
    if (!mainWindow) return;

    mainWindow.loadURL("http://localhost:5173").catch(() => {
        setTimeout(loadReactApp, 500);
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 1100,
        minHeight: 800,
    });

    loadReactApp();

    mainWindow.on("closed", () => {
        mainWindow = null;
    });
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
    if (process.platform !== "darwin") {
        app.quit();
    }
});
