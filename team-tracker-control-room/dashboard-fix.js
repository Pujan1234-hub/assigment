/* Dashboard correctness patch: WAITING counts only pending tasks for staff currently on shift. */
(() => {
  const oldRender = window.render;
  if (typeof oldRender !== 'function') return;

  window.render = function correctedRender(){
    oldRender();
    try {
      const activeIds = new Set((Array.isArray(rows) ? rows : []).map(r => r.staff_id).filter(Boolean));
      const waitingNow = (Array.isArray(taskRows) ? taskRows : []).filter(t =>
        activeIds.has(t.staff_id) && ['assigned','acknowledged'].includes(t.status)
      ).length;
      const el = document.getElementById('waitCount');
      if (el) el.textContent = waitingNow;
    } catch {}
  };

  // Correct immediately if the page was already rendered before this patch loaded.
  try {
    if (document.getElementById('app') && !document.getElementById('app').classList.contains('hidden')) {
      window.render();
    }
  } catch {}
})();