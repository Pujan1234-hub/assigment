(()=>{
  const boot=()=>{
    if(document.documentElement.dataset.motionReady==='1') return;
    document.documentElement.dataset.motionReady='1';

    const style=document.createElement('style');
    style.textContent=`
      :root{--motion-blue:#3157d5;--motion-coral:#e9694d}
      .motion-progress{position:fixed;top:0;left:0;height:3px;width:100%;z-index:100;pointer-events:none;transform-origin:left center;transform:scaleX(0);background:linear-gradient(90deg,var(--motion-blue),var(--motion-coral));box-shadow:0 1px 10px rgba(49,87,213,.18)}
      .motion-reveal{opacity:0;translate:0 24px;transition:opacity .72s cubic-bezier(.2,.7,.2,1),translate .72s cubic-bezier(.2,.7,.2,1)}
      .motion-reveal.is-visible{opacity:1;translate:0 0}
      .motion-reveal[data-delay="1"]{transition-delay:.08s}.motion-reveal[data-delay="2"]{transition-delay:.16s}.motion-reveal[data-delay="3"]{transition-delay:.24s}.motion-reveal[data-delay="4"]{transition-delay:.32s}
      .hero .kicker{animation:motionFade .65s .05s both}.hero h1{animation:motionHero .85s .1s cubic-bezier(.2,.75,.2,1) both}.hero-copy{animation:motionFade .7s .24s both}.hero-actions{animation:motionFade .7s .34s both}.hero-aside{animation:motionAside .85s .22s cubic-bezier(.2,.75,.2,1) both}
      @keyframes motionHero{from{opacity:0;translate:0 22px;letter-spacing:-.07em}to{opacity:1;translate:0 0;letter-spacing:-.055em}}
      @keyframes motionFade{from{opacity:0;translate:0 14px}to{opacity:1;translate:0 0}}
      @keyframes motionAside{from{opacity:0;translate:28px 0;rotate:1deg}to{opacity:1;translate:0 0;rotate:0deg}}
      .ticket{transition:box-shadow .25s ease,border-color .25s ease,translate .25s ease;animation:ticketDrift 5.5s ease-in-out infinite;animation-delay:calc(var(--ticket-i,0) * -.7s)}
      .ticket:hover{translate:0 -5px;box-shadow:7px 9px 0 rgba(23,25,29,.10);border-color:var(--motion-blue)}
      @keyframes ticketDrift{0%,100%{translate:0 0}50%{translate:0 -3px}}
      .ticket a,.side-links a,.footlinks a{transition:color .2s ease,letter-spacing .2s ease}.ticket a:hover,.side-links a:hover,.footlinks a:hover{color:var(--motion-blue);letter-spacing:.015em}
      .btn{position:relative;overflow:hidden;isolation:isolate;transition:translate .2s ease,box-shadow .2s ease,background .2s ease,color .2s ease}.btn:hover{translate:0 -3px;box-shadow:0 9px 20px rgba(23,25,29,.09)}.btn:active{translate:0 0}
      .project{transition:border-color .25s ease}.project:hover{border-color:var(--motion-blue)}
      .project .project-side h3{transition:color .25s ease,translate .25s ease}.project:hover .project-side h3{color:var(--motion-blue);translate:4px 0}
      .preview{transform:perspective(900px) rotateX(var(--tilt-x,0deg)) rotateY(var(--tilt-y,0deg));transform-style:preserve-3d;transition:transform .18s ease,box-shadow .28s ease,translate .28s ease;will-change:transform}
      .project:hover .preview{translate:0 -4px;box-shadow:8px 10px 0 rgba(23,25,29,.08)}
      .preview .ui-box,.preview .phone,.preview .map,.preview .wave{transition:translate .25s ease,box-shadow .25s ease}.preview:hover .ui-box,.preview:hover .map,.preview:hover .wave{translate:0 -2px}.preview:hover .phone{translate:0 -3px;box-shadow:6px 8px 0 #d8d0c4}
      .dot{animation:statusPulse 2.2s ease-in-out infinite}@keyframes statusPulse{0%,100%{box-shadow:0 0 0 0 rgba(31,158,116,0)}50%{box-shadow:0 0 0 5px rgba(31,158,116,.12)}}
      .section-number{transition:color .28s ease,translate .28s ease}.section-head:hover .section-number{color:var(--motion-coral);translate:3px -2px}
      .about-card{transition:translate .25s ease,rotate .25s ease,box-shadow .25s ease}.about-card:hover{translate:0 -5px;rotate:.25deg;box-shadow:8px 9px 0 rgba(23,25,29,.09)}
      .navlinks a.motion-active{color:var(--ink);font-weight:800}.navlinks a.motion-active:after{right:0;background:var(--motion-blue);height:2px}
      .motion-orb{position:fixed;z-index:-1;width:280px;height:280px;border-radius:50%;pointer-events:none;opacity:.12;filter:blur(8px);background:radial-gradient(circle,rgba(49,87,213,.45),rgba(233,105,77,.12) 48%,transparent 70%);translate:-50% -50%;left:50%;top:30%;transition:opacity .3s ease}
      @media(max-width:700px){.motion-orb{display:none}.ticket{animation-duration:7s}.preview{transform:none!important}.motion-reveal{translate:0 16px}}
      @media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation-duration:.001ms!important;animation-iteration-count:1!important;transition-duration:.001ms!important}.motion-reveal{opacity:1!important;translate:0 0!important}.motion-orb,.motion-progress{display:none!important}.preview{transform:none!important}}
    `;
    document.head.appendChild(style);

    const progress=document.createElement('div');
    progress.className='motion-progress';
    progress.setAttribute('aria-hidden','true');
    document.body.appendChild(progress);

    const reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
    if(!reduce && matchMedia('(pointer:fine)').matches){
      const orb=document.createElement('div');
      orb.className='motion-orb';
      orb.setAttribute('aria-hidden','true');
      document.body.appendChild(orb);
      let tx=innerWidth*.5,ty=innerHeight*.3,cx=tx,cy=ty,raf=0;
      const draw=()=>{cx+=(tx-cx)*.08;cy+=(ty-cy)*.08;orb.style.left=cx+'px';orb.style.top=cy+'px';raf=requestAnimationFrame(draw)};
      addEventListener('pointermove',e=>{tx=e.clientX;ty=e.clientY},{passive:true});
      addEventListener('blur',()=>orb.style.opacity='.04');addEventListener('focus',()=>orb.style.opacity='.12');
      draw();
    }

    const reveal=[...document.querySelectorAll('.section-head,.project,.note-grid,.about-grid,#contact .about-grid')];
    reveal.forEach((el,i)=>{el.classList.add('motion-reveal');el.dataset.delay=String((i%4)+1)});
    if('IntersectionObserver' in window && !reduce){
      const io=new IntersectionObserver(entries=>entries.forEach(entry=>{if(entry.isIntersecting){entry.target.classList.add('is-visible');io.unobserve(entry.target)}}),{threshold:.12,rootMargin:'0px 0px -7% 0px'});
      reveal.forEach(el=>io.observe(el));
    }else reveal.forEach(el=>el.classList.add('is-visible'));

    document.querySelectorAll('.ticket').forEach((el,i)=>el.style.setProperty('--ticket-i',i));

    if(!reduce && matchMedia('(pointer:fine)').matches){
      document.querySelectorAll('.preview').forEach(card=>{
        card.addEventListener('pointermove',e=>{
          const r=card.getBoundingClientRect();
          const x=(e.clientX-r.left)/r.width-.5;
          const y=(e.clientY-r.top)/r.height-.5;
          card.style.setProperty('--tilt-y',(x*4).toFixed(2)+'deg');
          card.style.setProperty('--tilt-x',(-y*3).toFixed(2)+'deg');
        });
        card.addEventListener('pointerleave',()=>{card.style.setProperty('--tilt-x','0deg');card.style.setProperty('--tilt-y','0deg')});
      });
    }

    const updateProgress=()=>{
      const max=Math.max(1,document.documentElement.scrollHeight-innerHeight);
      progress.style.transform=`scaleX(${Math.min(1,scrollY/max)})`;
    };
    updateProgress();
    addEventListener('scroll',updateProgress,{passive:true});
    addEventListener('resize',updateProgress,{passive:true});

    const navLinks=[...document.querySelectorAll('.navlinks a[href^="#"]')];
    const sectionMap=navLinks.map(a=>[a,document.querySelector(a.getAttribute('href'))]).filter(x=>x[1]);
    if('IntersectionObserver' in window){
      const activeObserver=new IntersectionObserver(entries=>{
        const visible=entries.filter(e=>e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];
        if(!visible) return;
        navLinks.forEach(a=>a.classList.remove('motion-active'));
        const item=sectionMap.find(([,s])=>s===visible.target);
        if(item) item[0].classList.add('motion-active');
      },{threshold:[.18,.35,.55],rootMargin:'-15% 0px -55% 0px'});
      sectionMap.forEach(([,s])=>activeObserver.observe(s));
    }
  };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot); else boot();
})();