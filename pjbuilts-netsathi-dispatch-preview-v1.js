/* NetSathi portfolio visual only. The real screenshots, actual ISP app, buttons, title and text are untouched. */
(()=>{
  'use strict';
  if(window.__pjNetsathiDispatchV1) return;
  window.__pjNetsathiDispatchV1=true;
  const html="\n<div class=\"nsx-shell\" role=\"img\" aria-label=\"Illustrative NetSathi ISP workflow: customer complaint, control-room dispatch, technician ETA, and repair completion. Not live ticket data.\">\n  <div class=\"nsx-top\">\n    <div class=\"nsx-brand\"><span class=\"nsx-brandmark\"><i></i><i></i><i></i></span><span>NetSathi<small>ISP SERVICE CONTROL</small></span></div>\n    <span class=\"nsx-label\"><i></i> WORKFLOW PREVIEW</span>\n  </div>\n  <div class=\"nsx-titlebar\">\n    <div><span class=\"nsx-eyebrow\">OPERATIONS / SERVICE DISPATCH</span><strong>From fault to <em>fix.</em></strong></div>\n    <span class=\"nsx-case\">DEMO CASE <b>NS-1042</b></span>\n  </div>\n  <div class=\"nsx-steps\">\n    <div class=\"nsx-step nsx-step-one\"><div class=\"nsx-step-top\"><span class=\"nsx-step-icon\">01</span><span>CUSTOMER</span></div><b>Internet offline</b><small>New support request</small><span class=\"nsx-chip\">REPORTED</span></div>\n    <div class=\"nsx-packet nsx-packet-one\" aria-hidden=\"true\"><span></span></div>\n    <div class=\"nsx-step nsx-step-two\"><div class=\"nsx-step-top\"><span class=\"nsx-step-icon\">02</span><span>CONTROL ROOM</span></div><b>Job assigned</b><small>Technician notified</small><span class=\"nsx-chip\">DISPATCHED</span></div>\n    <div class=\"nsx-packet nsx-packet-two\" aria-hidden=\"true\"><span></span></div>\n    <div class=\"nsx-step nsx-step-three\"><div class=\"nsx-step-top\"><span class=\"nsx-step-icon\">03</span><span>FIELD TECH</span></div><b>On the way</b><small>ETA shared</small><span class=\"nsx-chip\">EN ROUTE</span></div>\n  </div>\n  <div class=\"nsx-bottom\">\n    <div class=\"nsx-route\"><div class=\"nsx-route-top\"><span>FIELD VISIT</span><b>TECHNICIAN → CUSTOMER</b></div><svg viewBox=\"0 0 260 72\" preserveAspectRatio=\"none\" aria-hidden=\"true\"><path class=\"nsx-road\" d=\"M6 57 C53 57 45 10 98 20 S148 58 196 37 S232 9 254 15\"/><path class=\"nsx-journey\" d=\"M6 57 C53 57 45 10 98 20 S148 58 196 37 S232 9 254 15\"/><circle class=\"nsx-start\" cx=\"6\" cy=\"57\" r=\"5\"/><circle class=\"nsx-end\" cx=\"254\" cy=\"15\" r=\"5\"/></svg></div>\n    <div class=\"nsx-resolved\"><div class=\"nsx-resolved-mark\">✓</div><b>Repair complete</b><small>Customer + Control Room updated</small><span>CASE RESOLVED</span></div>\n  </div>\n  <div class=\"nsx-footer\"><span><i></i> COMPLAINT → ASSIGNMENT → ETA → REPAIR</span><span>ILLUSTRATIVE UI</span></div>\n</div>";
  let completed=false;
  function swap(){
    if(completed)return true;
    const preview=document.querySelector('#netsathi > .project-visual');
    if(!preview)return false;
    if(preview.dataset.nsDispatchV1==='1'){completed=true;return true;}
    const t=document.createElement('template');
    t.innerHTML=html;
    preview.replaceChildren(t.content.cloneNode(true));
    preview.classList.add('nsx-active');
    preview.dataset.nsDispatchV1='1';
    completed=true;
    return true;
  }
  function begin(){
    if(swap())return;
    const root=document.querySelector('#work .project-list')||document.body;
    const observer=new MutationObserver(()=>{if(swap())observer.disconnect()});
    observer.observe(root,{childList:true,subtree:true});
    setTimeout(()=>{swap();observer.disconnect()},16000);
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',begin,{once:true});
  else begin();
})();