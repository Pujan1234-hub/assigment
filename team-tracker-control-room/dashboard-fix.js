/* Dashboard correctness patch: PENDING TASKS counts only pending tasks for staff currently on shift. */
(() => {
  const oldRender = window.render;
  if (typeof oldRender !== 'function') return;

  function relabel(){
    const el = document.getElementById('waitCount');
    const small = el?.parentElement?.querySelector('small');
    if (small) small.textContent = 'PENDING TASKS';
  }

  window.render = function correctedRender(){
    oldRender();
    try {
      const activeIds = new Set((Array.isArray(rows) ? rows : []).map(r => r.staff_id).filter(Boolean));
      const waitingNow = (Array.isArray(taskRows) ? taskRows : []).filter(t =>
        activeIds.has(t.staff_id) && ['assigned','acknowledged'].includes(t.status)
      ).length;
      const el = document.getElementById('waitCount');
      if (el) el.textContent = waitingNow;
      relabel();
    } catch {}
  };

  relabel();
  try {
    if (document.getElementById('app') && !document.getElementById('app').classList.contains('hidden')) {
      window.render();
    }
  } catch {}
})();