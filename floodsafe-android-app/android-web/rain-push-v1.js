// Native Firebase push bridge. A tap registers this device for the official Nepal alert topic.
// Firebase delivers the notification even after the app is closed (unless Android has force-stopped it).
export function setupRainAlerts({getLanguage}) {
  let status;
  let onStatus;
  const message = (enabled) => getLanguage() === 'en'
    ? (enabled
      ? 'Official Nepal alerts are active.'
      : 'Notification permission was not granted. Turn it on in Android Settings to receive official alerts.')
    : (enabled
      ? 'आधिकारिक नेपाल सूचना सक्रिय छ।'
      : 'सूचना अनुमति दिइएन। आधिकारिक सूचना पाउन Android Settings मा अनुमति दिनुहोस्।');

  function render(enabled) {
    if (status) status.textContent = message(enabled);
  }

  return {
    mount(after) {
      status = document.createElement('p');
      status.id = 'rainAlertStatus';
      status.setAttribute('role', 'status');
      status.style.cssText = 'font-size:.75rem;line-height:1.5;margin-top:10px';
      after.after(status);
      render(false);

      onStatus = (event) => render(Boolean(event?.detail?.enabled));
      window.addEventListener('floodsafe-alerts-status', onStatus);

      // The visible home-screen Warning Alert button is #alertBtn.
      // Capture the tap as well as the compact rain-widget button when present.
      document.addEventListener('click', (event) => {
        if (!event.target.closest('#alertBtn, #rainAlertBtn')) return;
        if (window.FloodSafeNative?.enableRainAlerts) window.FloodSafeNative.enableRainAlerts();
        else render(false);
      });
    },
    render() {},
    locationChanged() {},
    async check() {}
  };
}
