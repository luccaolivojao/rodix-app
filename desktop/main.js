const { app, BrowserWindow, Menu } = require('electron');
const path = require('path');
app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');
function create() {
  const w = new BrowserWindow({ width: 1280, height: 720, backgroundColor: '#070d1a', autoHideMenuBar: true, title: 'Rodix Football', icon: path.join(__dirname, 'icon.png'), webPreferences: { backgroundThrottling: false } });
  Menu.setApplicationMenu(null);
  w.loadFile(path.join(__dirname, 'www', 'index.html'));
  w.webContents.on('before-input-event', (e, i) => { if (i.type === 'keyDown' && i.key === 'F11') w.setFullScreen(!w.isFullScreen()); });
}
app.whenReady().then(create);
app.on('window-all-closed', () => app.quit());
