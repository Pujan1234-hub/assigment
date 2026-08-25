const { contextBridge } = require('electron');
contextBridge.exposeInMainWorld('FixCheckDesktop', {
  platform: process.platform,
  nativeShell: true
});
