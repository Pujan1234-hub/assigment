/* Keep staff/task cards stable while the 2s live poll refreshes the dashboard. */
(() => {
  const oldRenderStaff = window.renderStaff;
  if (typeof oldRenderStaff !== 'function') return;

  const drafts = new Map();
  let lastSignature = '';

  const remember = el => {
    if (!el || !el.id) return;
    const m = el.id.match(/^([atp])_(.+)$/);
    if (!m) return;
    const [, kind, staffId] = m;
    const d = drafts.get(staffId) || {};
    if (kind === 'a') d.area = el.value;
    if (kind === 't') d.task = el.value;
    if (kind === 'p') d.priority = el.value;
    drafts.set(staffId, d);
  };

  document.addEventListener('input', e => remember(e.target), true);
  document.addEventListener('change', e => remember(e.target), true);

  function structuralSignature(){
    try {
      const now = Date.now();
      const rs = Array.isArray(rows) ? rows : [];
      const ts = Array.isArray(taskRows) ? taskRows : [];
      return rs.map(r => {
        const latest = ts.find(t => t.staff_id === r.staff_id);
        const stale = !r.updated_at || now - new Date(r.updated_at).getTime() > 180000;
        return [r.staff_id,r.real_name||'',r.area||'',r.task||'',latest?.status||'',stale?'stale':'live'].join('~');
      }).join('|');
    } catch { return String(Date.now()); }
  }

  function restoreDrafts(){
    drafts.forEach((d, staffId) => {
      const a = document.getElementById('a_' + staffId);
      const t = document.getElementById('t_' + staffId);
      const p = document.getElementById('p_' + staffId);
      if (a && d.area !== undefined) a.value = d.area;
      if (t && d.task !== undefined) t.value = d.task;
      if (p && d.priority !== undefined) p.value = d.priority;
    });
  }

  window.renderStaff = function stableRenderStaff(){
    const holder = document.getElementById('staff');
    const active = document.activeElement;

    // Never replace the form while the user is typing/selecting.
    if (holder && active && holder.contains(active) && /^(INPUT|SELECT|TEXTAREA)$/.test(active.tagName)) return;

    const sig = structuralSignature();
    // GPS timestamp/coordinates may update every 2s. If the visible card content did not
    // meaningfully change, leave the whole DOM untouched so timers/inputs do not blink.
    if (holder && holder.children.length && sig === lastSignature) return;

    lastSignature = sig;
    oldRenderStaff();
    restoreDrafts();
    // If shift-safety is installed, restore its line immediately after a genuine card rebuild.
    try { window.__ttAnnotateActiveCards?.(); } catch {}
  };

  const oldAssign = window.assignTask;
  if (typeof oldAssign === 'function') {
    window.assignTask = async function patchedAssignTask(staffId){
      const result = await oldAssign(staffId);
      const t = document.getElementById('t_' + staffId);
      if (t && t.value === '') {
        const d = drafts.get(staffId) || {};
        d.task = '';
        drafts.set(staffId, d);
      }
      return result;
    };
  }
})();