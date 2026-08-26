/* Control Room: add SIYARA live counter only. No auth/GPS/task/shift logic changes. */
(() => {
  function ensureCard() {
    const stats = document.querySelector('#app .stats');
    const hotel = document.getElementById('hotelCount')?.closest('.stat');
    if (!stats || !hotel) return null;

    let card = document.getElementById('siyaraStat');
    if (!card) {
      card = document.createElement('div');
      card.className = 'stat tt-siyara-stat';
      card.id = 'siyaraStat';
      card.innerHTML = '<small>SIYARA</small><b id="siyaraCount">0</b>';
      hotel.insertAdjacentElement('afterend', card);
    }
    return card;
  }

  function updateCount() {
    ensureCard();
    const el = document.getElementById('siyaraCount');
    if (!el) return;
    try {
      const list = Array.isArray(rows) ? rows : [];
      el.textContent = list.filter(r => String(r.team_code || '').toLowerCase() === 'siyara').length;
    } catch {
      el.textContent = '0';
    }
  }

  const style = document.createElement('style');
  style.textContent = `
    #siyaraStat{position:relative;overflow:hidden}
    #siyaraStat:before{content:'';position:absolute;left:0;right:0;top:0;height:4px;background:linear-gradient(90deg,#9a7cff,#d4c3ff)}
    #siyaraStat #siyaraCount{color:#ddd5ff}
    @media (min-width:701px){#app .stats:has(#siyaraStat){grid-template-columns:repeat(5,minmax(0,1fr))}}
    @media (max-width:700px){#siyaraStat{grid-column:auto}}
  `;
  document.head.appendChild(style);

  ensureCard();
  updateCount();

  const oldRender = window.render;
  if (typeof oldRender === 'function') {
    window.render = function renderWithSiyaraCounter(){
      const out = oldRender.apply(this, arguments);
      updateCount();
      return out;
    };
  }

  // Safety sync with the existing 2-second live refresh without changing it.
  setInterval(updateCount, 2000);
})();
