/* Keep task/area input stable while the 2s live poll refreshes the dashboard. */
(() => {
  const oldRenderStaff = window.renderStaff;
  if (typeof oldRenderStaff !== 'function') return;

  const drafts = new Map();
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

  window.renderStaff = function stableRenderStaff(){
    const holder = document.getElementById('staff');
    const active = document.activeElement;

    // Critical fix: do not replace the staff/task form while the user is typing/selecting.
    if (holder && active && holder.contains(active) && /^(INPUT|SELECT|TEXTAREA)$/.test(active.tagName)) {
      return;
    }

    oldRenderStaff();

    // Restore any unfinished drafts after a normal refresh.
    drafts.forEach((d, staffId) => {
      const a = document.getElementById('a_' + staffId);
      const t = document.getElementById('t_' + staffId);
      const p = document.getElementById('p_' + staffId);
      if (a && d.area !== undefined) a.value = d.area;
      if (t && d.task !== undefined) t.value = d.task;
      if (p && d.priority !== undefined) p.value = d.priority;
    });
  };

  // Clear only the task draft after a successful ASSIGN clears the visible field.
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