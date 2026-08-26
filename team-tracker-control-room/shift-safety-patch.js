/* Team Tracker Control Room — shift safety audit.
   Stable shift cards: only the live duration text updates every second. */
(() => {
  let auditRows = [];
  let firstLoad = true;
  let seen = new Map();
  let pollBusy = false;

  const css = document.createElement('style');
  css.textContent = `
    .tt-shift-now{margin-top:7px;padding:7px 9px;border:1px solid #31536b;border-radius:9px;background:#071b2a;font-size:12px;color:#dceaf4}
    .tt-shift-now b{color:#72e3a0}.tt-shift-now .clock{color:#f3ca67;font-weight:900;display:inline-block;min-width:52px;font-variant-numeric:tabular-nums}
    #shiftSafety{margin-top:16px;border-top:1px solid #294258;padding-top:14px}
    .tt-shift-head{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-bottom:8px}
    .tt-shift-head h3{margin:0}.tt-shift-head small{color:#93a7b9}
    .tt-shift-log{display:grid;gap:7px}
    .tt-shift-item{display:grid;grid-template-columns:minmax(120px,.8fr) minmax(170px,1.5fr) auto;gap:9px;align-items:center;padding:10px;border:1px solid #263f54;border-radius:11px;background:#081724;font-size:12px}
    .tt-shift-item.active{border-color:#2d7050;background:#082018}.tt-shift-item.ended{border-color:#5a4d2b}
    .tt-shift-name{font-weight:900;color:#fff}.tt-shift-meta{color:#a9bac7;line-height:1.45}.tt-shift-state{font-weight:900;text-align:right}
    .tt-shift-state.on{color:#67e39a}.tt-shift-state.off{color:#f0c96b}.tt-shift-state.offsite{color:#ffaaaa}
    .tt-live-duration{font-variant-numeric:tabular-nums;display:inline-block;min-width:60px}
    #shiftEventToast{position:fixed;left:50%;top:14px;transform:translateX(-50%);z-index:10050;display:none;min-width:min(92vw,420px);max-width:620px;padding:13px 15px;border-radius:13px;border:1px solid #6c8293;background:#071927;color:#fff;box-shadow:0 8px 30px rgba(0,0,0,.45);font:800 13px/1.35 system-ui;text-align:center}
    #shiftEventToast.end{border-color:#e6b54b;background:#2a210b}#shiftEventToast.start{border-color:#49b97a;background:#082518}
    @media(max-width:700px){.tt-shift-item{grid-template-columns:1fr}.tt-shift-state{text-align:left}}
  `;
  document.head.appendChild(css);

  const fmtTime = v => { if (!v) return '—'; try { return new Date(v).toLocaleTimeString([], {hour:'2-digit', minute:'2-digit', second:'2-digit'}); } catch { return '—'; } };
  const fmtDateTime = v => { if (!v) return '—'; try { const d=new Date(v); return `${d.toLocaleDateString([], {day:'2-digit',month:'short'})} ${d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}`; } catch { return '—'; } };
  const fmtDuration = sec => { sec=Math.max(0,Math.floor(Number(sec)||0)); const h=Math.floor(sec/3600),m=Math.floor((sec%3600)/60),s=sec%60; if(h)return `${h}h ${String(m).padStart(2,'0')}m`; if(m)return `${m}m ${String(s).padStart(2,'0')}s`; return `${s}s`; };
  const shiftLabel = r => { try { return typeof badge==='function'?badge(r):`${String(r.team_code||'STAFF').toUpperCase()} ${r.badge_number??''}`.trim(); } catch { return `${String(r.team_code||'STAFF').toUpperCase()} ${r.badge_number??''}`.trim(); } };
  const safe = s => typeof esc==='function'?esc(s):String(s??'');
  const currentDuration = r => r.ended_at ? Number(r.duration_seconds)||0 : Math.max(0,Math.floor((Date.now()-new Date(r.started_at).getTime())/1000));

  function ensureUi(){
    if(!document.getElementById('shiftEventToast')){const t=document.createElement('div');t.id='shiftEventToast';document.body.appendChild(t)}
    if(!document.getElementById('shiftSafety')){const staff=document.getElementById('staff');if(!staff)return;const sec=document.createElement('section');sec.id='shiftSafety';sec.innerHTML=`<div class="tt-shift-head"><h3>Shift Safety Log</h3><small>Start / end audit</small></div><div id="shiftSafetyLog" class="tt-shift-log"><div class="muted">Loading shift history…</div></div>`;staff.insertAdjacentElement('afterend',sec)}
  }

  function beep(kind){try{const Ctx=window.AudioContext||window.webkitAudioContext;if(!Ctx)return;const ctx=new Ctx(),o=ctx.createOscillator(),g=ctx.createGain();o.type='sine';o.frequency.value=kind==='end'?520:760;g.gain.setValueAtTime(.0001,ctx.currentTime);g.gain.exponentialRampToValueAtTime(.12,ctx.currentTime+.02);g.gain.exponentialRampToValueAtTime(.0001,ctx.currentTime+.25);o.connect(g);g.connect(ctx.destination);o.start();o.stop(ctx.currentTime+.28);setTimeout(()=>ctx.close().catch(()=>{}),500)}catch{}}

  function showEvent(kind,r){ensureUi();const t=document.getElementById('shiftEventToast');if(!t)return;const who=shiftLabel(r),ended=kind==='end';const text=ended?`${who} ENDED SHIFT • ${fmtTime(r.ended_at)} • ${fmtDuration(r.duration_seconds)}`:`${who} STARTED SHIFT • ${fmtTime(r.started_at)}`;t.textContent=text;t.className=ended?'end':'start';t.style.display='block';clearTimeout(t._timer);t._timer=setTimeout(()=>t.style.display='none',8000);beep(kind);try{if('Notification'in window&&Notification.permission==='granted')new Notification('Team Tracker — Shift Safety',{body:text})}catch{}}

  function annotateActiveCards(){
    const activeByStaff=new Map(auditRows.filter(r=>r.is_active).map(r=>[r.staff_id,r]));
    document.querySelectorAll('#staff .row').forEach(card=>{
      const input=card.querySelector('input[id^="a_"]');if(!input)return;
      const staffId=input.id.slice(2),r=activeByStaff.get(staffId);let line=card.querySelector('.tt-shift-now');
      if(!r){if(line)line.remove();return}
      if(!line){
        line=document.createElement('div');line.className='tt-shift-now';line.dataset.staffId=staffId;
        line.innerHTML=`<b>SHIFT ACTIVE</b> • started <span class="tt-start-time"></span> • <span class="clock"></span><span class="tt-start-area"></span>`;
        const assign=card.querySelector('.assign');if(assign)card.insertBefore(line,assign);else card.appendChild(line);
        line.querySelector('.tt-start-time').textContent=fmtTime(r.started_at);
        line.querySelector('.tt-start-area').textContent=r.start_area?` • ${r.start_area}`:'';
      }
      const clock=line.querySelector('.clock');if(clock)clock.textContent=fmtDuration(currentDuration(r));
    });
  }
  window.__ttAnnotateActiveCards=annotateActiveCards;

  function renderLog(){
    ensureUi();const log=document.getElementById('shiftSafetyLog');if(!log)return;
    if(!auditRows.length){log.innerHTML='<div class="muted">No shift records yet.</div>';return}
    const list=[...auditRows.filter(r=>r.is_active),...auditRows.filter(r=>!r.is_active)].slice(0,24);
    log.innerHTML=list.map(r=>{const offsite=!r.is_active&&/off[- ]?site/i.test(String(r.end_area||''));const stateClass=r.is_active?'on':offsite?'offsite':'off';const stateText=r.is_active?'ON SHIFT':offsite?'ENDED • OFF-SITE':'ENDED';const timing=r.is_active?`START ${fmtDateTime(r.started_at)} • LIVE <span class="tt-live-duration" data-shift-id="${safe(r.shift_id)}"></span>`:`START ${fmtDateTime(r.started_at)} • END ${fmtDateTime(r.ended_at)} • ${fmtDuration(r.duration_seconds)}`;const areas=r.is_active?`${r.start_area||'Start area not set'}`:`${r.start_area||'Start area not set'} → ${r.end_area||'End area not set'}`;return `<div class="tt-shift-item ${r.is_active?'active':'ended'}"><div><div class="tt-shift-name">${safe(shiftLabel(r))}</div><div class="sub">${safe(r.real_name||'')}</div></div><div class="tt-shift-meta">${timing}<br>${safe(areas)}</div><div class="tt-shift-state ${stateClass}">${stateText}</div></div>`}).join('');
    updateClocks();
  }

  function updateClocks(){
    annotateActiveCards();
    const byShift=new Map(auditRows.filter(r=>r.is_active).map(r=>[String(r.shift_id),r]));
    document.querySelectorAll('.tt-live-duration[data-shift-id]').forEach(el=>{const r=byShift.get(el.dataset.shiftId);if(r)el.textContent=fmtDuration(currentDuration(r))});
  }

  function detectEvents(next){if(firstLoad){seen=new Map(next.map(r=>[r.shift_id,r.ended_at||null]));firstLoad=false;return}for(const r of next){if(!seen.has(r.shift_id))showEvent(r.ended_at?'end':'start',r);else if(!seen.get(r.shift_id)&&r.ended_at)showEvent('end',r)}seen=new Map(next.map(r=>[r.shift_id,r.ended_at||null]))}

  async function pollAudit(){const app=document.getElementById('app');if(!app||app.classList.contains('hidden')||document.hidden||pollBusy||typeof rpc!=='function')return;pollBusy=true;try{const data=await rpc('control_room_shift_audit',{p_limit:60});const next=Array.isArray(data)?data:[];detectEvents(next);auditRows=next;renderLog();annotateActiveCards()}catch(e){console.warn('Shift audit unavailable:',e?.message||e)}finally{pollBusy=false}}

  setInterval(pollAudit,2000);
  // Important: this timer updates ONLY text nodes. No card/box is rebuilt each second.
  setInterval(updateClocks,1000);
  window.addEventListener('focus',pollAudit);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)pollAudit()});
  setTimeout(pollAudit,350);
})();