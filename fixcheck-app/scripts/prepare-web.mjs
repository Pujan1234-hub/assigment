import { mkdirSync, writeFileSync, copyFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const appRoot = resolve(here, '..');
const repoRoot = resolve(appRoot, '..');
const webAssets = resolve(repoRoot, 'fixcheck');
const out = resolve(appRoot, 'www');
const appSource = 'https://raw.githubusercontent.com/Pujan1234-hub/assigment/0afecb6aab4da3775ba79b4eb4a8d6dfd697ea7f/fixcheck/index.html';
mkdirSync(out, { recursive: true });

// Keep the native app on the tested FixCheck v0.7 UI even if the public web folder
// is later reused by the portfolio site. A failed source fetch aborts the build rather
// than silently packaging the wrong page.
const sourceResponse = await fetch(appSource, { cache: 'no-store' });
if (!sourceResponse.ok) throw new Error(`Unable to load FixCheck v0.7 source: ${sourceResponse.status}`);
let html = await sourceResponse.text();

// The host-baseline experiment is no longer part of the native product UI.
// Keep a tiny local compatibility value so the older pinned v0.7 run function can
// finish without making the removed baseline request; the native diagnosis below
// intentionally ignores that compatibility value.
const oldBaselineProbe = "const srv=await probes('./ping.txt',7,false);";
if (!html.includes(oldBaselineProbe)) throw new Error('Pinned FixCheck source changed: baseline probe marker not found');
html = html.replace(oldBaselineProbe, 'const srv=summary([0],1);');

const nativePatch = `<style>
#install{display:none!important}
.compare{grid-template-columns:1fr!important}
</style>
<script>
window.FIXCHECK_NATIVE=true;
(function(){
  function hideClosest(selector, closestSelector){
    const el=document.querySelector(selector);
    const box=el&&el.closest(closestSelector);
    if(box)box.style.display='none';
  }

  // Remove every visible FixCheck-host baseline element while keeping the legacy
  // DOM nodes available for the pinned v0.7 code path during this compatibility build.
  hideClosest('#s-server','.check');
  hideClosest('#serverTop','.pill');
  hideClosest('#serverMed','.card');

  const intro=document.querySelector('h1 + p');
  if(intro)intro.textContent='Pick a service. FixCheck measures DNS and repeated HTTPS response timing to the selected domain from this device.';
  const version=document.querySelector('.version');
  if(version)version.textContent='FixCheck v0.7.1';

  // Native verdicts now use only the selected service signals. The removed host
  // baseline cannot create a warning, lower confidence, or appear in the diagnosis.
  classify=function(tg,d,svc){
    if(!navigator.onLine)return{level:'bad',title:'Your device is offline',text:'FixCheck cannot test '+tg.name+' until this device has an active connection.',why:'The local device reported offline before service testing began.'};
    if(!d.ok)return{level:'bad',title:'DNS problem for '+tg.name,text:d.nx?tg.host+' does not resolve in public DNS.':'FixCheck could not confirm DNS for '+tg.host+'.',why:'No service response timing is shown when DNS is not confirmed.'};
    if(!svc.success)return{level:'bad',title:tg.name+' did not respond',text:'DNS resolved, but none of the HTTPS probes to '+tg.name+' completed from this device.',why:'This shows a problem reaching the selected service/path from this device. It does not prove a global outage.'};
    if(svc.rel<80)return{level:'warn',title:tg.name+' response is unstable',text:'Only '+svc.success+' of '+svc.total+' HTTPS probes completed.',why:'Repeated probe failures can come from the selected service path, congestion, VPN/firewall behaviour, or the current connection.'};
    if(svc.jitter!=null&&svc.jitter>120)return{level:'warn',title:tg.name+' response varies a lot',text:'The selected service responded, but request timing changed heavily between probes.',why:'High variation can make a service feel inconsistent even when it remains reachable.'};
    if(svc.rel>=95)return{level:'good',title:'No clear problem detected',text:tg.name+' responded reliably from this device.',why:'DNS resolved and repeated HTTPS probes completed successfully. This is a device-to-service check, not proof of global service health.'};
    return{level:'warn',title:'Result is mixed',text:tg.name+' responded, but the probe pattern is not strong enough for a confident result.',why:'Run the check again and compare the result over time.'};
  };

  renderHistory=function(){
    const e=document.querySelector('#history'),h=historyAll().slice(0,12);
    e.innerHTML=h.length?'':'<p class="muted">No service checks yet.</p>';
    h.forEach(x=>{
      const d=document.createElement('div');
      d.className='hist';
      d.innerHTML='<span><b>'+x.target+'</b><br><small class="muted">'+x.when+' · service '+(x.serviceMedian??'--')+' ms</small></span><strong>'+(x.score==null?'--':x.score+'/100')+'</strong>';
      e.appendChild(d);
    });
  };

  report=function(){
    if(!last)return'';
    return [
      'FixCheck v0.7.1 service report',
      'Target: '+last.target,
      'Diagnosis: '+last.diagnosis,
      'Service score: '+(last.score??'Not rated'),
      'DNS: '+(last.dnsMs??'--')+' ms',
      'Service median: '+(last.serviceMedian??'--')+' ms',
      'Service jitter: '+(last.serviceJitter??'--')+' ms',
      'Service success: '+(last.serviceRel??'--')+'%'
    ].join('\\n');
  };

  renderHistory();
})();
</script>`;

html = html.replace('</body>', nativePatch + '\n</body>');
writeFileSync(resolve(out, 'index.html'), html);
for (const name of ['favicon.svg', 'manifest.webmanifest']) {
  try { copyFileSync(resolve(webAssets, name), resolve(out, name)); } catch {}
}
console.log('Prepared pinned FixCheck v0.7.1 assets with host baseline removed from native UI.');
