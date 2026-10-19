/* PJBUILTS two-preview refresh — 2026-10-19
 * Changes ONLY the decorative .project-visual in #teamtracker and #fixcheck.
 * No navigation, project text, enquiry, galleries, scripts or app sources change.
 * The previews are purposefully illustrative UI, not live operational data.
 */
(() => {
  'use strict';
  if (window.__pjTwoPreviews2026) return;
  window.__pjTwoPreviews2026 = true;

  const team = `
    <div class="pjv-scene pjv-team" role="img" aria-label="Animated Team Tracker workflow preview: new requests move through assignment and completion">
      <div class="pjv-toolbar">
        <div class="pjv-app-label"><span class="pjv-app-symbol pjv-team-symbol">T</span><span>TEAM TRACKER <small>OPERATIONS</small></span></div>
        <span class="pjv-top-state"><i></i> WORKFLOW PREVIEW</span>
      </div>
      <div class="pjv-team-heading">
        <div><span class="pjv-overline">CONTROL ROOM / 01</span><h4>Work, in motion.</h4></div>
        <span class="pjv-team-date">TEAM OVERVIEW <b>↗</b></span>
      </div>
      <div class="pjv-board" aria-hidden="true">
        <div class="pjv-lane pjv-lane-one">
          <div class="pjv-lane-title"><span class="pjv-lane-dot pjv-dot-blue"></span> INBOX <b>01</b></div>
          <div class="pjv-workitem"><span class="pjv-workitem-type">REQUEST 001</span><strong>Site inspection</strong><span class="pjv-mini-tags"><i>New</i><i>Field</i></span><span class="pjv-avatar">A</span></div>
        </div>
        <div class="pjv-lane pjv-lane-two">
          <div class="pjv-lane-title"><span class="pjv-lane-dot pjv-dot-gold"></span> IN PROGRESS <b>02</b></div>
          <div class="pjv-workitem"><span class="pjv-workitem-type">TASK 002</span><strong>Job assigned</strong><span class="pjv-mini-tags"><i>On route</i></span><span class="pjv-avatar">M</span></div>
        </div>
        <div class="pjv-lane pjv-lane-three">
          <div class="pjv-lane-title"><span class="pjv-lane-dot pjv-dot-green"></span> COMPLETED <b>03</b></div>
          <div class="pjv-workitem"><span class="pjv-workitem-type">TASK 003</span><strong>Update sent</strong><span class="pjv-mini-tags"><i>Verified ✓</i></span><span class="pjv-avatar">J</span></div>
        </div>
        <div class="pjv-board-light" aria-hidden="true"></div>
      </div>
      <div class="pjv-activity" aria-hidden="true">
        <span class="pjv-activity-label">ACTIVITY FLOW</span>
        <div class="pjv-activity-line">
          <span class="pjv-activity-step"><i></i><b>Received</b></span>
          <span class="pjv-activity-step"><i></i><b>Assigned</b></span>
          <span class="pjv-activity-step"><i></i><b>Resolved</b></span>
        </div>
      </div>
      <div class="pjv-scene-foot"><span><i></i> TEAM WORKFLOW</span><span>INTERFACE CONCEPT / 01</span></div>
    </div>`;

  const fix = `
    <div class="pjv-scene pjv-fix" role="img" aria-label="Animated FixCheck diagnostic concept with scanning progress and staged browser, DNS and endpoint checks">
      <div class="pjv-toolbar pjv-fix-toolbar">
        <div class="pjv-app-label"><span class="pjv-app-symbol pjv-fix-symbol">F</span><span>FIXCHECK <small>DIAGNOSTICS</small></span></div>
        <span class="pjv-fix-top-state"><i></i> SCAN PREVIEW</span>
      </div>
      <div class="pjv-fix-overview">
        <div class="pjv-orb" aria-hidden="true">
          <div class="pjv-orb-track"></div>
          <div class="pjv-orb-track pjv-track-two"></div>
          <div class="pjv-orb-ring"></div>
          <div class="pjv-orb-core"><svg width="31" height="31" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v3M19.2 6.8l-2.1 2.1M21 12h-3M17.1 17.1l2.1 2.1M12 18v3M6.9 17.1l-2.1 2.1M6 12H3M6.9 6.9 4.8 4.8"/><circle cx="12" cy="12" r="4"/></svg></div>
        </div>
        <div class="pjv-fix-title">
          <span class="pjv-overline">SYSTEM CHECK / 02</span>
          <h4>Find the signal.<br><em>Fix the issue.</em></h4>
          <p><span class="pjv-fix-cursor"></span> Reviewing connection layers</p>
        </div>
      </div>
      <div class="pjv-checklist" aria-hidden="true">
        <div class="pjv-check-row"><span class="pjv-check-icon">01</span><span class="pjv-check-info"><strong>Browser connection</strong><i class="pjv-check-bar"></i></span><span class="pjv-check-result pjv-check-good">CHECK ✓</span></div>
        <div class="pjv-check-row"><span class="pjv-check-icon">02</span><span class="pjv-check-info"><strong>DNS resolution</strong><i class="pjv-check-bar"></i></span><span class="pjv-check-result pjv-check-good">CHECK ✓</span></div>
        <div class="pjv-check-row"><span class="pjv-check-icon">03</span><span class="pjv-check-info"><strong>Service response</strong><i class="pjv-check-bar"></i></span><span class="pjv-check-result pjv-check-pending">ANALYSING</span></div>
      </div>
      <div class="pjv-scene-foot pjv-fix-foot"><span><i></i> DIAGNOSTIC FLOW</span><span>INTERFACE CONCEPT / 02</span></div>
    </div>`;

  function install(cardId, markup) {
    const visual = document.querySelector('#' + cardId + ' > .project-visual');
    if (!visual || visual.dataset.pjRefresh === '20261019') return;
    // Scope protection: never mutate project metadata, links or any screenshot gallery.
    const template = document.createElement('template');
    template.innerHTML = markup.trim();
    visual.replaceChildren(template.content.cloneNode(true));
    visual.classList.add('pjv-replaced');
    visual.dataset.pjRefresh = '20261019';
  }

  function apply(){
    install('teamtracker', team);
    install('fixcheck', fix);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', apply, {once:true});
  else apply();
})();