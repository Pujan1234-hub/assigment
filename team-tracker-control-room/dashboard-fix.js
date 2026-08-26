/* Dashboard correctness patch: PENDING TASKS counts only pending tasks for staff currently on shift.
   Also adds a live SIYARA summary counter. No auth/GPS/task/shift behavior is changed. */
(() => {
  const oldRender = window.render;
  if (typeof oldRender !== 'function') return;

  const style = document.createElement('style');
  style.textContent = `
    #app .stats{grid-template-columns:repeat(5,minmax(0,1fr))}
    #siyaraStat:before{background:linear-gradient(90deg,#8e72ff,#d5c8ff)!important}
    #siyaraCount{color:#e4dcff!important}
    .stat.tt-pending-stat:before{background:linear-gradient(90deg,#d49932,#ffd777)!important}
    .stat.tt-pending-stat #waitCount{color:#ffe5a2!important}
    @media(max-width:700px){#app .stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
  `;
  document.head.appendChild(style);

  function ensureSiyaraCard(){
    const hotelCount = document.getElementById('hotelCount');
    const hotelCard = hotelCount?.closest('.stat');
    const stats = hotelCard?.parentElement;
    if (!hotelCard || !stats) return;

    let card = document.getElementById('siyaraStat');
    if (!card) {
      card = document.createElement('div');
      card.className = 'stat';
      card.id = 'siyaraStat';
      card.innerHTML = '<small>SIYARA</small><b id="siyaraCount">0</b>';
      hotelCard.insertAdjacentElement('afterend', card);
    }

    const waitCard = document.getElementById('waitCount')?.closest('.stat');
    if (waitCard) waitCard.classList.add('tt-pending-stat');
  }

  function relabel(){
    const el = document.getElementById('waitCount');
    const small = el?.parentElement?.querySelector('small');
    if (small) small.textContent = 'PENDING TASKS';
  }

  function updateDashboardExtras(){
    ensureSiyaraCard();
    relabel();
    try {
      const activeRows = Array.isArray(rows) ? rows : [];
      const activeIds = new Set(activeRows.map(r => r.staff_id).filter(Boolean));
      const waitingNow = (Array.isArray(taskRows) ? taskRows : []).filter(t =>
        activeIds.has(t.staff_id) && ['assigned','acknowledged'].includes(t.status)
      ).length;
      const waiting = document.getElementById('waitCount');
      if (waiting) waiting.textContent = waitingNow;

      const siyara = document.getElementById('siyaraCount');
      if (siyara) siyara.textContent = activeRows.filter(r => String(r.team_code || '').toLowerCase() === 'siyara').length;
    } catch {}
  }

  window.render = function correctedRender(){
    oldRender();
    updateDashboardExtras();
  };

  updateDashboardExtras();
  try {
    if (document.getElementById('app') && !document.getElementById('app').classList.contains('hidden')) {
      window.render();
    }
  } catch {}
})();