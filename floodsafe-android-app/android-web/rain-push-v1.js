// Android beta has no native background push transport. Never imply it is active.
export function setupRainAlerts({getLanguage}) {
  let status;
  function render() {
    if (status) status.textContent = getLanguage() === 'en'
      ? 'Rain notifications while the app is closed are not available in this beta. Open the app to check the forecast.'
      : 'यो beta मा app बन्द हुँदा वर्षा सूचना उपलब्ध छैन। मौसम हेर्न app खोल्नुहोस्।';
  }
  return {
    mount(after) {
      status = document.createElement('p');
      status.id = 'rainAlertStatus';
      status.setAttribute('role', 'status');
      status.style.cssText = 'font-size:.75rem;line-height:1.5;margin-top:10px';
      after.after(status);
      render();
    }, render, locationChanged() {}, async check() {}
  };
}
