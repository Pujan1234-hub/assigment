(()=>{
  const boot=()=>{
    if(document.documentElement.dataset.motionReady==='2') return;
    document.documentElement.dataset.motionReady='2';

    const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
    const finePointer=matchMedia('(pointer:fine)').matches;

    const style=document.createElement('style');
    style.textContent=`
      :root{--motion-blue:#3157d5;--motion-coral:#e9694d;--cs-green:#1c8a68;--cs-ink:#17191d;--cs-paper:#f2eee6;--cs-mono:"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace}
      .motion-progress{position:fixed;top:0;left:0;height:3px;width:100%;z-index:110;pointer-events:none;transform-origin:left center;transform:scaleX(0);background:linear-gradient(90deg,var(--motion-blue),#687ce4,var(--motion-coral));box-shadow:0 1px 10px rgba(49,87,213,.18)}
      .motion-reveal{opacity:0;translate:0 24px;transition:opacity .72s cubic-bezier(.2,.7,.2,1),translate .72s cubic-bezier(.2,.7,.2,1)}
      .motion-reveal.is-visible{opacity:1;translate:0 0}
      .motion-reveal[data-delay="1"]{transition-delay:.06s}.motion-reveal[data-delay="2"]{transition-delay:.12s}.motion-reveal[data-delay="3"]{transition-delay:.18s}.motion-reveal[data-delay="4"]{transition-delay:.24s}

      .hero{position:relative;overflow:hidden;isolation:isolate}.hero>.wrap{position:relative;z-index:2}.cs-network{position:absolute;inset:0;width:100%;height:100%;z-index:0;pointer-events:none;opacity:.52;mix-blend-mode:multiply}.hero:after{content:"";position:absolute;inset:0;z-index:1;pointer-events:none;background:linear-gradient(90deg,rgba(242,238,230,.98) 0%,rgba(242,238,230,.90) 43%,rgba(242,238,230,.64) 72%,rgba(242,238,230,.78) 100%)}
      .hero .kicker{animation:motionFade .65s .05s both}.hero h1{animation:motionHero .85s .1s cubic-bezier(.2,.75,.2,1) both}.hero-copy{animation:motionFade .7s .24s both}.hero-actions{animation:motionFade .7s .34s both}.hero-aside{animation:motionAside .85s .22s cubic-bezier(.2,.75,.2,1) both}
      @keyframes motionHero{from{opacity:0;translate:0 22px;letter-spacing:-.07em}to{opacity:1;translate:0 0;letter-spacing:-.055em}}
      @keyframes motionFade{from{opacity:0;translate:0 14px}to{opacity:1;translate:0 0}}
      @keyframes motionAside{from{opacity:0;translate:28px 0;rotate:1deg}to{opacity:1;translate:0 0;rotate:0deg}}

      .cs-console{margin-top:26px;border:1px solid var(--cs-ink);background:#11151b;color:#dfe7f3;max-width:690px;box-shadow:6px 7px 0 rgba(23,25,29,.10);font-family:var(--cs-mono);animation:consoleIn .75s .42s cubic-bezier(.2,.75,.2,1) both;overflow:hidden}
      @keyframes consoleIn{from{opacity:0;translate:0 14px;clip-path:inset(0 100% 0 0)}to{opacity:1;translate:0 0;clip-path:inset(0 0 0 0)}}
      .cs-console-bar{height:34px;display:flex;align-items:center;justify-content:space-between;padding:0 11px;border-bottom:1px solid rgba(255,255,255,.10);background:#191f27;color:#8e9bac;font-size:.68rem;letter-spacing:.05em;text-transform:uppercase}
      .cs-console-dots{display:flex;gap:5px}.cs-console-dots i{display:block;width:7px;height:7px;border-radius:50%;background:#e9694d}.cs-console-dots i:nth-child(2){background:#f2d46e}.cs-console-dots i:nth-child(3){background:#56b995}
      .cs-console-body{padding:13px 15px 14px;min-height:116px;font-size:.76rem;line-height:1.7}.cs-line{display:flex;gap:9px;min-height:1.7em}.cs-prompt{color:#6e8cff}.cs-output{color:#bdc9d8}.cs-ok{color:#66d6aa}.cs-cursor{display:inline-block;width:7px;height:1.05em;background:#dfe7f3;vertical-align:-.15em;animation:blink 1s steps(1) infinite}@keyframes blink{50%{opacity:0}}
      .cs-console-foot{border-top:1px solid rgba(255,255,255,.08);padding:7px 15px;color:#718096;font-size:.65rem;display:flex;justify-content:space-between;gap:12px;background:#141a21}

      .cs-stack{border-top:1px solid var(--rule,#cbc3b6);border-bottom:1px solid var(--rule,#cbc3b6);overflow:hidden;background:rgba(255,253,248,.38);position:relative}.cs-stack:before,.cs-stack:after{content:"";position:absolute;top:0;bottom:0;width:70px;z-index:2;pointer-events:none}.cs-stack:before{left:0;background:linear-gradient(90deg,var(--cs-paper),transparent)}.cs-stack:after{right:0;background:linear-gradient(270deg,var(--cs-paper),transparent)}
      .cs-stack-track{display:flex;width:max-content;gap:0;animation:stackMarquee 24s linear infinite}.cs-stack-item{font-family:var(--cs-mono);font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;white-space:nowrap;padding:11px 20px;border-right:1px solid var(--rule,#cbc3b6);color:#4e5661}.cs-stack-item b{color:var(--motion-blue);font-weight:800;margin-right:7px}@keyframes stackMarquee{to{translate:-50% 0}}

      .cs-pipeline{display:grid;grid-template-columns:repeat(7,max-content);align-items:center;gap:12px;margin:0 0 30px;padding:15px 0;border-top:1px dashed #bdb5a8;border-bottom:1px dashed #bdb5a8;font-family:var(--cs-mono);overflow-x:auto;scrollbar-width:none}.cs-pipeline::-webkit-scrollbar{display:none}.cs-node{display:flex;align-items:center;gap:9px;white-space:nowrap;font-size:.72rem;text-transform:uppercase;letter-spacing:.06em}.cs-node i{width:9px;height:9px;border:1px solid var(--cs-ink);background:var(--cs-paper);position:relative}.cs-node.active i{background:var(--motion-blue);box-shadow:0 0 0 4px rgba(49,87,213,.10)}.cs-arrow{color:#8a8174;font-family:var(--cs-mono);animation:arrowPulse 1.6s ease-in-out infinite}@keyframes arrowPulse{0%,100%{opacity:.35;translate:-2px 0}50%{opacity:1;translate:2px 0}}

      .cs-project-meta{display:flex;flex-wrap:wrap;gap:7px;margin-top:17px}.cs-chip{font-family:var(--cs-mono);font-size:.65rem;letter-spacing:.035em;border:1px solid #c9c1b5;background:rgba(255,253,248,.72);padding:5px 7px;color:#545b65;transition:.2s ease}.project:hover .cs-chip{border-color:#9aacec}.cs-chip:before{content:"<";color:var(--motion-blue)}.cs-chip:after{content:"/>";color:var(--motion-blue)}
      .cs-preview-label{position:absolute;right:13px;bottom:11px;z-index:4;font-family:var(--cs-mono);font-size:.58rem;letter-spacing:.08em;text-transform:uppercase;color:#6f7781;background:rgba(255,253,248,.88);border:1px solid #d8d0c4;padding:4px 6px;pointer-events:none}

      .ticket{transition:box-shadow .25s ease,border-color .25s ease,translate .25s ease;animation:ticketDrift 5.5s ease-in-out infinite;animation-delay:calc(var(--ticket-i,0) * -.7s)}.ticket:hover{translate:0 -5px;box-shadow:7px 9px 0 rgba(23,25,29,.10);border-color:var(--motion-blue)}@keyframes ticketDrift{0%,100%{translate:0 0}50%{translate:0 -3px}}
      .ticket a,.side-links a,.footlinks a{transition:color .2s ease,letter-spacing .2s ease}.ticket a:hover,.side-links a:hover,.footlinks a:hover{color:var(--motion-blue);letter-spacing:.015em}
      .btn{position:relative;overflow:hidden;isolation:isolate;transition:translate .2s ease,box-shadow .2s ease,background .2s ease,color .2s ease}.btn:hover{translate:0 -3px;box-shadow:0 9px 20px rgba(23,25,29,.09)}.btn:active{translate:0 0}
      .project{transition:border-color .25s ease}.project:hover{border-color:var(--motion-blue)}.project .project-side h3{transition:color .25s ease,translate .25s ease}.project:hover .project-side h3{color:var(--motion-blue);translate:4px 0}
      .preview{transform:perspective(900px) rotateX(var(--tilt-x,0deg)) rotateY(var(--tilt-y,0deg));transform-style:preserve-3d;transition:transform .18s ease,box-shadow .28s ease,translate .28s ease;will-change:transform}.project:hover .preview{translate:0 -4px;box-shadow:8px 10px 0 rgba(23,25,29,.08)}.preview .ui-box,.preview .phone,.preview .map,.preview .wave{transition:translate .25s ease,box-shadow .25s ease}.preview:hover .ui-box,.preview:hover .map,.preview:hover .wave{translate:0 -2px}.preview:hover .phone{translate:0 -3px;box-shadow:6px 8px 0 #d8d0c4}
      .dot{animation:statusPulse 2.2s ease-in-out infinite}@keyframes statusPulse{0%,100%{box-shadow:0 0 0 0 rgba(31,158,116,0)}50%{box-shadow:0 0 0 5px rgba(31,158,116,.12)}}
      .section-number{transition:color .28s ease,translate .28s ease}.section-head:hover .section-number{color:var(--motion-coral);translate:3px -2px}.about-card{transition:translate .25s ease,rotate .25s ease,box-shadow .25s ease}.about-card:hover{translate:0 -5px;rotate:.25deg;box-shadow:8px 9px 0 rgba(23,25,29,.09)}
      .navlinks a.motion-active{color:var(--ink);font-weight:800}.navlinks a.motion-active:after{right:0;background:var(--motion-blue);height:2px}
      .motion-orb{position:fixed;z-index:-1;width:280px;height:280px;border-radius:50%;pointer-events:none;opacity:.10;filter:blur(8px);background:radial-gradient(circle,rgba(49,87,213,.45),rgba(233,105,77,.12) 48%,transparent 70%);translate:-50% -50%;left:50%;top:30%;transition:opacity .3s ease}

      @media(max-width:950px){.cs-pipeline{grid-template-columns:repeat(7,max-content)}.cs-console{max-width:none}.cs-network{opacity:.36}}
      @media(max-width:700px){.motion-orb{display:none}.ticket{animation-duration:7s}.preview{transform:none!important}.motion-reveal{translate:0 16px}.cs-network{opacity:.23}.cs-stack-item{padding:10px 15px}.cs-console-body{font-size:.7rem}.cs-console-foot{display:none}.hero:after{background:rgba(242,238,230,.88)}}
      @media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}.motion-reveal{opacity:1!important;translate:0 0!important}.motion-orb,.motion-progress,.cs-network{display:none!important}.preview{transform:none!important}.cs-stack-track{animation:none!important}}
    `;
    document.head.appendChild(style);

    const hero=document.querySelector('.hero');
    if(hero && !hero.querySelector('.cs-network')){
      const canvas=document.createElement('canvas');
      canvas.className='cs-network';
      canvas.setAttribute('aria-hidden','true');
      hero.prepend(canvas);
      if(!reduce){
        const ctx=canvas.getContext('2d');
        let w=0,h=0,dpr=1,raf=0,t=0;
        const nodes=[
          [.08,.25],[.18,.67],[.30,.38],[.43,.73],[.53,.23],[.64,.54],[.75,.18],[.83,.66],[.92,.34],[.70,.83],[.38,.14]
        ];
        const edges=[[0,2],[1,2],[2,4],[2,3],[3,5],[4,5],[4,6],[5,7],[5,9],[6,8],[7,8],[7,9],[2,10],[10,4]];
        const resize=()=>{
          const r=hero.getBoundingClientRect();dpr=Math.min(2,devicePixelRatio||1);w=Math.max(1,r.width);h=Math.max(1,r.height);canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);canvas.style.width=w+'px';canvas.style.height=h+'px';ctx.setTransform(dpr,0,0,dpr,0,0);
        };
        const draw=()=>{
          t+=.008;ctx.clearRect(0,0,w,h);ctx.lineWidth=1;
          edges.forEach((e,i)=>{
            const a=nodes[e[0]],b=nodes[e[1]],ax=a[0]*w,ay=a[1]*h,bx=b[0]*w,by=b[1]*h;
            ctx.strokeStyle=i%3===0?'rgba(49,87,213,.26)':'rgba(23,25,29,.12)';ctx.beginPath();ctx.moveTo(ax,ay);ctx.lineTo(bx,by);ctx.stroke();
            const p=(t+i*.11)%1,px=ax+(bx-ax)*p,py=ay+(by-ay)*p;ctx.fillStyle=i%3===0?'rgba(49,87,213,.72)':'rgba(233,105,77,.48)';ctx.beginPath();ctx.arc(px,py,2.1,0,Math.PI*2);ctx.fill();
          });
          nodes.forEach((n,i)=>{const x=n[0]*w,y=n[1]*h;ctx.fillStyle=i%4===0?'#3157d5':'rgba(255,253,248,.95)';ctx.strokeStyle='rgba(23,25,29,.45)';ctx.lineWidth=1;ctx.beginPath();ctx.arc(x,y,i%4===0?4:3,0,Math.PI*2);ctx.fill();ctx.stroke()});
          raf=requestAnimationFrame(draw);
        };
        resize();draw();addEventListener('resize',resize,{passive:true});document.addEventListener('visibilitychange',()=>{if(document.hidden){cancelAnimationFrame(raf)}else{draw()}});
      }
    }

    const heroActions=document.querySelector('.hero-actions');
    if(heroActions && !document.querySelector('.cs-console')){
      const consoleEl=document.createElement('div');
      consoleEl.className='cs-console';
      consoleEl.innerHTML=`<div class="cs-console-bar"><span class="cs-console-dots"><i></i><i></i><i></i></span><span>portfolio-terminal</span><span>bash</span></div><div class="cs-console-body"><div class="cs-line"><span class="cs-prompt">$</span><span id="cs-command"></span><span class="cs-cursor"></span></div><div id="cs-terminal-output"></div></div><div class="cs-console-foot"><span>Computer Science · Software Systems · Networking</span><span>status: building</span></div>`;
      heroActions.insertAdjacentElement('afterend',consoleEl);
      const command=consoleEl.querySelector('#cs-command');
      const output=consoleEl.querySelector('#cs-terminal-output');
      const sequence=[
        ['whoami','Pujan Chapagain · software builder'],
        ['stack --current','JavaScript · Web APIs · PWA · realtime data · GitHub'],
        ['projects --active','Team Tracker · FixCheck · FloodSafe Nepal · DateMate'],
        ['mode','build → test → debug → refine']
      ];
      if(reduce){command.textContent='projects --active';output.innerHTML='<div class="cs-line"><span class="cs-ok">✓</span><span class="cs-output">Team Tracker · FixCheck · FloodSafe Nepal · DateMate</span></div>'}
      else{
        let s=0;
        const run=()=>{
          const [cmd,out]=sequence[s%sequence.length];let i=0;command.textContent='';output.innerHTML='';
          const type=()=>{if(i<cmd.length){command.textContent+=cmd[i++];setTimeout(type,38+Math.random()*35)}else{setTimeout(()=>{output.innerHTML=`<div class="cs-line"><span class="cs-ok">✓</span><span class="cs-output">${out}</span></div>`;setTimeout(()=>{s++;run()},1750)},260)}};type();
        };setTimeout(run,600);
      }
    }

    const ruleBand=document.querySelector('.rule-band');
    if(ruleBand && !document.querySelector('.cs-stack')){
      const stack=document.createElement('div');stack.className='cs-stack';
      const labels=['JavaScript','HTML / CSS','Web APIs','Realtime UI','PWA','Supabase','GitHub','Geolocation','Data validation','Networking','Testing','Responsive UI'];
      const items=[...labels,...labels].map((x,i)=>`<span class="cs-stack-item"><b>${String((i%labels.length)+1).padStart(2,'0')}</b>${x}</span>`).join('');
      stack.innerHTML=`<div class="cs-stack-track">${items}</div>`;ruleBand.insertAdjacentElement('afterend',stack);
    }

    const work=document.getElementById('work');
    if(work && !work.querySelector('.cs-pipeline')){
      const firstProject=work.querySelector('.project');
      if(firstProject){
        const pipeline=document.createElement('div');pipeline.className='cs-pipeline';pipeline.setAttribute('aria-label','Software system pipeline');
        pipeline.innerHTML='<span class="cs-node active"><i></i>Input</span><span class="cs-arrow">→</span><span class="cs-node"><i></i>Logic</span><span class="cs-arrow">→</span><span class="cs-node"><i></i>Data</span><span class="cs-arrow">→</span><span class="cs-node"><i></i>Interface</span>';
        firstProject.insertAdjacentElement('beforebegin',pipeline);
        if(!reduce){
          const nodes=[...pipeline.querySelectorAll('.cs-node')];let k=0;setInterval(()=>{nodes.forEach(n=>n.classList.remove('active'));nodes[k%nodes.length].classList.add('active');k++},1100);
        }
      }
    }

    const tech={
      teamtracker:['Realtime UI','Geolocation','Event-driven state','Browser app'],
      fixcheck:['Network diagnostics','Browser APIs','Connectivity logic','PWA'],
      floodsafe:['Live public data','Map layers','Data freshness','Fallback logic'],
      datemate:['Date logic','Reminder flow','Local state','Mobile-first']
    };
    document.querySelectorAll('.project').forEach(project=>{
      const id=project.id||'';const copy=project.querySelector('.project-copy');
      if(copy && tech[id] && !copy.querySelector('.cs-project-meta')){
        const meta=document.createElement('div');meta.className='cs-project-meta';meta.innerHTML=tech[id].map(x=>`<span class="cs-chip">${x}</span>`).join('');copy.appendChild(meta);
      }
      const preview=project.querySelector('.preview');
      if(preview && !preview.querySelector('.cs-preview-label')){
        const label=document.createElement('span');label.className='cs-preview-label';label.textContent=(id||'system')+' / interface-preview';preview.appendChild(label);
      }
    });

    const progress=document.createElement('div');progress.className='motion-progress';progress.setAttribute('aria-hidden','true');document.body.appendChild(progress);

    if(!reduce && finePointer){
      const orb=document.createElement('div');orb.className='motion-orb';orb.setAttribute('aria-hidden','true');document.body.appendChild(orb);let tx=innerWidth*.5,ty=innerHeight*.3,cx=tx,cy=ty;
      const drawOrb=()=>{cx+=(tx-cx)*.08;cy+=(ty-cy)*.08;orb.style.left=cx+'px';orb.style.top=cy+'px';requestAnimationFrame(drawOrb)};addEventListener('pointermove',e=>{tx=e.clientX;ty=e.clientY},{passive:true});addEventListener('blur',()=>orb.style.opacity='.04');addEventListener('focus',()=>orb.style.opacity='.10');drawOrb();
    }

    const reveal=[...document.querySelectorAll('.section-head,.project,.note-grid,.about-grid,#contact .about-grid,.cs-pipeline')];reveal.forEach((el,i)=>{el.classList.add('motion-reveal');el.dataset.delay=String((i%4)+1)});
    if('IntersectionObserver' in window && !reduce){const io=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('is-visible');io.unobserve(entry.target)}}),{threshold:.12,rootMargin:'0px 0px -7% 0px'});reveal.forEach(el=>io.observe(el))}else reveal.forEach(el=>el.classList.add('is-visible'));

    document.querySelectorAll('.ticket').forEach((el,i)=>el.style.setProperty('--ticket-i',i));

    if(!reduce && finePointer){document.querySelectorAll('.preview').forEach(card=>{card.addEventListener('pointermove',e=>{const r=card.getBoundingClientRect(),x=(e.clientX-r.left)/r.width-.5,y=(e.clientY-r.top)/r.height-.5;card.style.setProperty('--tilt-y',(x*4).toFixed(2)+'deg');card.style.setProperty('--tilt-x',(-y*3).toFixed(2)+'deg')});card.addEventListener('pointerleave',()=>{card.style.setProperty('--tilt-x','0deg');card.style.setProperty('--tilt-y','0deg')})})}

    const updateProgress=()=>{const max=Math.max(1,document.documentElement.scrollHeight-innerHeight);progress.style.transform=`scaleX(${Math.min(1,scrollY/max)})`};updateProgress();addEventListener('scroll',updateProgress,{passive:true});addEventListener('resize',updateProgress,{passive:true});

    const navLinks=[...document.querySelectorAll('.navlinks a[href^="#"]')];const sectionMap=navLinks.map(a=>[a,document.querySelector(a.getAttribute('href'))]).filter(x=>x[1]);
    if('IntersectionObserver' in window){const activeObserver=new IntersectionObserver(entries=>{const visible=entries.filter(e=>e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];if(!visible)return;navLinks.forEach(a=>a.classList.remove('motion-active'));const item=sectionMap.find(([,s])=>s===visible.target);if(item)item[0].classList.add('motion-active')},{threshold:[.18,.35,.55],rootMargin:'-15% 0px -55% 0px'});sectionMap.forEach(([,s])=>activeObserver.observe(s))}
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();