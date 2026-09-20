(()=>{
  if(window.__pjNetSathiPortfolioV2)return;
  window.__pjNetSathiPortfolioV2=true;

  const style=document.createElement('style');
  style.id='pj-netsathi-style-v2';
  style.textContent=`
    #netsathi{--accent:#52f2a8}
    #netsathi .ns-visual-wrap{position:relative;width:min(540px,90%);height:500px;border:1px solid rgba(255,255,255,.11);border-radius:24px;background:linear-gradient(145deg,rgba(12,25,34,.96),rgba(7,13,21,.98));box-shadow:0 28px 70px rgba(0,0,0,.34);overflow:hidden;padding:18px;display:flex;align-items:center;justify-content:center}
    #netsathi .ns-visual-wrap:before{content:'REAL SCREENS · CUSTOMER · TECHNICIAN · CONTROL ROOM';position:absolute;left:18px;right:18px;top:15px;color:#74f5b6;font:850 .62rem/1.3 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.08em;z-index:2}
    #netsathi .ns-visual-wrap img{display:block;max-height:435px;width:auto;max-width:91%;border-radius:17px;box-shadow:0 18px 55px rgba(0,0,0,.45);margin-top:24px}

    #netsathi-showcase{--ns:#52f2a8;margin:18px 0 34px;border:1px solid rgba(82,242,168,.22);border-radius:28px;background:linear-gradient(145deg,rgba(10,24,31,.98),rgba(8,15,24,.98));overflow:hidden;box-shadow:0 28px 80px rgba(0,0,0,.24);color:#f4f7fb}
    #netsathi-showcase *{box-sizing:border-box}
    #netsathi-showcase .ns-inner{padding:36px}
    #netsathi-showcase .ns-kicker{color:#83f8c0;font:900 .72rem/1.3 ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.12em;text-transform:uppercase}
    #netsathi-showcase .ns-head{display:grid;grid-template-columns:1.05fr .95fr;gap:24px;margin-top:10px}
    #netsathi-showcase h4{font-size:clamp(1.8rem,3vw,3rem);line-height:1.02;letter-spacing:-.045em;margin:0}
    #netsathi-showcase .ns-lead{margin:14px 0 0;color:#9eacbd;line-height:1.7;font-size:.92rem}
    #netsathi-showcase .ns-overview{padding:18px;border:1px solid rgba(255,255,255,.10);border-radius:18px;background:rgba(255,255,255,.025)}
    #netsathi-showcase .ns-overview strong{display:block;margin-bottom:8px;color:#fff}.ns-overview span{color:#8fa0b4;font-size:.8rem;line-height:1.55}
    #netsathi-showcase .ns-flow{display:grid;grid-template-columns:repeat(6,1fr);gap:8px;margin:28px 0}
    #netsathi-showcase .ns-step{padding:12px;min-height:86px;border:1px solid rgba(255,255,255,.09);border-radius:14px;background:rgba(255,255,255,.025);display:flex;flex-direction:column;justify-content:space-between;gap:8px;color:#b5c1cf;font-size:.69rem;line-height:1.35}
    #netsathi-showcase .ns-step b{color:var(--ns);font:900 .66rem ui-monospace,monospace}.ns-step strong{color:#fff;font-size:.74rem}
    #netsathi-showcase .ns-systems{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}
    #netsathi-showcase .ns-system{border:1px solid rgba(255,255,255,.10);border-radius:18px;padding:18px;background:rgba(255,255,255,.025)}
    #netsathi-showcase .ns-system h5{margin:8px 0 7px;font-size:1rem}.ns-system p{margin:0;color:#8fa0b4;font-size:.75rem;line-height:1.55}

    #netsathi-showcase .ns-gallery-title{display:flex;justify-content:space-between;gap:18px;align-items:end;margin-top:30px;padding-top:26px;border-top:1px solid rgba(255,255,255,.08)}
    #netsathi-showcase .ns-gallery-title h5{margin:0;font-size:1.15rem}.ns-gallery-title span{color:#7f91a5;font-size:.72rem}
    #netsathi-showcase .ns-gallery{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:14px}
    #netsathi-showcase .ns-gallery figure{margin:0;border:1px solid rgba(255,255,255,.10);border-radius:18px;overflow:hidden;background:#06101a;box-shadow:0 14px 42px rgba(0,0,0,.22)}
    #netsathi-showcase .ns-gallery figure.ns-wide{grid-column:1/-1}
    #netsathi-showcase .ns-gallery img{display:block;width:100%;height:auto;background:#07101a;cursor:zoom-in;transition:transform .25s ease}
    #netsathi-showcase .ns-gallery figure:hover img{transform:scale(1.015)}
    #netsathi-showcase .ns-gallery figcaption{padding:12px 14px;border-top:1px solid rgba(255,255,255,.07);color:#8797aa;font-size:.72rem;line-height:1.5}
    #netsathi-showcase .ns-gallery figcaption b{display:block;color:#edf5f1;font-size:.78rem;margin-bottom:2px}

    #netsathi-showcase .ns-proof{display:grid;grid-template-columns:.9fr 1.1fr;gap:14px;margin-top:18px}
    #netsathi-showcase .ns-proof>div{padding:18px;border:1px solid rgba(255,255,255,.09);border-radius:18px;background:rgba(255,255,255,.022)}
    #netsathi-showcase .ns-proof h5{margin:0 0 9px;font-size:1rem}.ns-proof p{margin:0;color:#8fa0b4;font-size:.77rem;line-height:1.65}
    #netsathi-showcase .ns-tags{display:flex;flex-wrap:wrap;gap:8px}.ns-tags span{border:1px solid rgba(82,242,168,.16);background:rgba(82,242,168,.055);color:#b9e9d0;border-radius:999px;padding:8px 10px;font-size:.68rem;font-weight:800}
    #netsathi-showcase .ns-actions{display:flex;gap:10px;flex-wrap:wrap;margin-top:24px}.ns-actions a{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 15px;border-radius:12px;border:1px solid rgba(255,255,255,.11);font-size:.76rem;font-weight:850}.ns-actions a:first-child{background:linear-gradient(135deg,#34e6ff,#52f2a8);color:#041016;border:0}
    #netsathi-showcase .ns-lightbox{position:fixed;inset:0;z-index:9999;background:rgba(1,5,9,.93);display:none;align-items:center;justify-content:center;padding:24px;cursor:zoom-out}.ns-lightbox.open{display:flex}.ns-lightbox img{max-width:95vw;max-height:92vh;border-radius:16px;box-shadow:0 30px 100px #000}

    @media(max-width:900px){#netsathi-showcase .ns-head,#netsathi-showcase .ns-proof{grid-template-columns:1fr}#netsathi-showcase .ns-flow{grid-template-columns:repeat(3,1fr)}}
    @media(max-width:700px){#netsathi .ns-visual-wrap{height:430px}#netsathi-showcase{border-radius:22px}#netsathi-showcase .ns-inner{padding:24px 18px}#netsathi-showcase .ns-systems,#netsathi-showcase .ns-gallery{grid-template-columns:1fr}#netsathi-showcase .ns-gallery figure.ns-wide{grid-column:auto}#netsathi-showcase .ns-flow{grid-template-columns:1fr 1fr}#netsathi-showcase .ns-gallery-title{display:block}.ns-gallery-title span{display:block;margin-top:5px}#netsathi-showcase .ns-actions{display:grid}.ns-actions a{width:100%}}
  `;
  document.head.appendChild(style);

  function buildCard(){
    if(document.getElementById('netsathi'))return document.getElementById('netsathi');
    const list=document.querySelector('.project-list');
    if(!list)return null;
    const card=document.createElement('article');
    card.className='project reveal on';
    card.id='netsathi';
    card.innerHTML=`
      <div class="project-copy">
        <span class="project-no">07 / NetSathi</span>
        <h3>NetSathi</h3>
        <span class="status"><i></i> Working realtime prototype</span>
        <p>A complete ISP customer-support and technician-dispatch system for Nepal. It connects a Customer Android app, Technician Android app and Control Room web dashboard into one realtime service workflow.</p>
        <div class="features">
          <div class="feature"><b>01</b> Customer complaint + photos</div>
          <div class="feature"><b>02</b> Technician assignment</div>
          <div class="feature"><b>03</b> ETA + live GPS</div>
          <div class="feature"><b>04</b> Repair confirmation</div>
        </div>
        <div class="project-links"><a href="#netsathi-showcase">View real screens ↓</a><a href="https://pjbuilts.com/netsathi/">Working demo ↗</a></div>
      </div>
      <div class="project-visual"><div class="visual-grid"></div><div class="ns-visual-wrap"><img src="./assets/portfolio/netsathi-showcase.svg?v=20260920-io2" alt="NetSathi customer technician and control room screenshots" loading="lazy"></div></div>`;
    list.appendChild(card);
    return card;
  }

  function buildDetail(card){
    if(!card||document.getElementById('netsathi-showcase'))return;
    const section=document.createElement('div');
    section.id='netsathi-showcase';
    section.className='reveal on';
    section.innerHTML=`<div class="ns-inner">
      <div class="ns-kicker">NETSATHI · CUSTOMER + TECHNICIAN + CONTROL ROOM</div>
      <div class="ns-head">
        <div><h4>Complaint to repair, synced across three connected products.</h4><p class="ns-lead">The screenshots below show the real prototype flow: customer issue submission, photo and service location, Control Room ticket handling, technician assignment and acceptance, ETA/delay updates, live GPS and route visibility, Android notifications, repair completion and customer confirmation.</p></div>
        <div class="ns-overview"><strong>Same ticket, three views</strong><span>Customer, technician and dispatcher see the same service request progressing through one shared workflow. The images here come from the working NetSathi screens, arranged so each part of the system is easy to inspect.</span></div>
      </div>

      <div class="ns-flow">
        <div class="ns-step"><b>01</b><strong>Customer request</strong><span>Issue + photo + address/GPS</span></div>
        <div class="ns-step"><b>02</b><strong>Control Room</strong><span>Queue + technician dispatch</span></div>
        <div class="ns-step"><b>03</b><strong>Technician accepts</strong><span>Assigned job reaches field app</span></div>
        <div class="ns-step"><b>04</b><strong>ETA + live GPS</strong><span>On-way status + route</span></div>
        <div class="ns-step"><b>05</b><strong>Repair fixed</strong><span>Field work marked complete</span></div>
        <div class="ns-step"><b>06</b><strong>Customer confirms</strong><span>Repair confirmed and ticket closed</span></div>
      </div>

      <div class="ns-systems">
        <div class="ns-system"><div>📱</div><h5>Customer Android</h5><p>Report a problem, attach issue photos, optionally share service GPS, follow realtime status, see assigned technician/ETA/live position, receive Android notifications and confirm the repair.</p></div>
        <div class="ns-system"><div>🧑‍🔧</div><h5>Technician Android</h5><p>Receive assigned jobs, inspect customer photos/details, accept jobs, publish ETA and delay reasons, share field GPS while active and mark the repair fixed.</p></div>
        <div class="ns-system"><div>🖥️</div><h5>Control Room Web</h5><p>See ticket queue, customer photos, technician availability/workload, assign staff, update ETA and follow live dispatch status and route on the map.</p></div>
      </div>

      <div class="ns-gallery-title"><h5>Real NetSathi screens</h5><span>Tap any image to enlarge</span></div>
      <div class="ns-gallery">
        <figure class="ns-wide"><img src="./assets/portfolio/netsathi-control-room.svg?v=20260920-io2" alt="NetSathi Control Room dashboard and map" loading="lazy"><figcaption><b>Control Room dashboard</b>Live dispatch map, technician status, customer issue photos and recent tickets in one operations view.</figcaption></figure>
        <figure><img src="./assets/portfolio/netsathi-operations.svg?v=20260920-io2" alt="NetSathi ticket and technician operations" loading="lazy"><figcaption><b>Ticket & technician operations</b>Queue management, dispatch controls, ETA fields, technician workload and customer evidence.</figcaption></figure>
        <figure><img src="./assets/portfolio/netsathi-customer-journey.svg?v=20260920-io2" alt="NetSathi customer Android journey" loading="lazy"><figcaption><b>Customer Android journey</b>Submit issue → receive assignment and on-way updates → see ETA/live location → confirm repair.</figcaption></figure>
        <figure><img src="./assets/portfolio/netsathi-technician-journey.svg?v=20260920-io2" alt="NetSathi technician Android journey" loading="lazy"><figcaption><b>Technician Android journey</b>Assigned job → accept → publish ETA/GPS → repair marked fixed → wait for customer confirmation.</figcaption></figure>
        <figure><img src="./assets/portfolio/netsathi-realtime-route.svg?v=20260920-io2" alt="NetSathi realtime route and notification screens" loading="lazy"><figcaption><b>Realtime route & notifications</b>Control Room route visibility and native Android status notifications keep every side in sync.</figcaption></figure>
      </div>

      <div class="ns-proof">
        <div><h5>End-to-end ticket proof</h5><p>Ticket <b>NS-215DC4D0</b> progresses through OPEN → ASSIGNED → ACCEPTED → ON WAY → FIXED/CLOSED. The same issue photo appears across the Customer app, Technician app and Control Room, while ETA, delay and field-location changes are reflected across the workflow.</p></div>
        <div><h5>Implemented prototype capabilities</h5><div class="ns-tags"><span>Realtime ticket sync</span><span>Issue photos</span><span>Service GPS</span><span>Technician dispatch</span><span>Accepted / On Way / Fixed</span><span>Live ETA</span><span>Technician GPS</span><span>Route map</span><span>Android notifications</span><span>Customer confirmation</span><span>Technician workload</span><span>Responsive dashboard</span></div></div>
      </div>

      <div class="ns-actions"><a href="https://pjbuilts.com/netsathi/">Open working NetSathi demo ↗</a><a href="#contact">Contact</a></div>
    </div><div class="ns-lightbox" aria-hidden="true"><img alt="Expanded NetSathi screenshot"></div>`;
    card.insertAdjacentElement('afterend',section);

    const box=section.querySelector('.ns-lightbox');
    const boxImg=box.querySelector('img');
    section.querySelectorAll('.ns-gallery img').forEach(img=>img.addEventListener('click',()=>{
      boxImg.src=img.src;
      box.classList.add('open');
      box.setAttribute('aria-hidden','false');
    }));
    box.addEventListener('click',()=>{
      box.classList.remove('open');
      box.setAttribute('aria-hidden','true');
      boxImg.removeAttribute('src');
    });
  }

  function apply(){const card=buildCard();if(!card)return false;buildDetail(card);return true;}
  let tries=0;
  const tick=()=>{if(apply()||tries++>30)return;setTimeout(tick,150)};
  tick();
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(apply,80),{once:true});
})();