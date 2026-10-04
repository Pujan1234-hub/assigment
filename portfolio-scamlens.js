(()=>{
  if(window.__pjScamLensPortfolio) return;
  window.__pjScamLensPortfolio=true;

  const RAW='https://raw.githubusercontent.com/pujanchapagainsoftware-oss/LifeOS-Android/main/assets/portfolio/';
  const HOME=[RAW+'scamlens-home-01.txt',RAW+'scamlens-home-02.txt',RAW+'scamlens-home-03.txt'];
  const PROTECTION=[RAW+'scamlens-protection-01.txt',RAW+'scamlens-protection-02.txt',RAW+'scamlens-protection-03.txt'];

  function addStyle(){
    if(document.getElementById('scamlens-portfolio-style')) return;
    const s=document.createElement('style');
    s.id='scamlens-portfolio-style';
    s.textContent=`
      #scamlens .project-visual{overflow:hidden}
      .scamlens-stage{position:relative;width:100%;min-height:580px;display:flex;align-items:center;justify-content:center;gap:20px;padding:42px 30px;background:radial-gradient(circle at 50% 42%,rgba(23,153,143,.12),transparent 54%)}
      .scamlens-screen{width:min(235px,43%);overflow:hidden;border-radius:30px;border:1px solid rgba(18,35,57,.13);background:#fffaf2;box-shadow:0 24px 60px rgba(18,35,57,.16);transform:rotate(-2deg)}
      .scamlens-screen:nth-child(2){transform:translateY(30px) rotate(2deg)}
      .scamlens-screen img{display:block;width:100%;height:auto;background:#fffaf2}
      .scamlens-live{position:absolute;left:9%;bottom:10%;padding:10px 12px;border-radius:13px;background:rgba(17,34,56,.9);color:#fff;font-size:.7rem;font-weight:900;letter-spacing:.04em;box-shadow:0 12px 30px rgba(17,34,56,.2)}
      .scamlens-live b{display:block;color:#8de3d8;font-size:.78rem;margin-top:2px}
      .scamlens-fallback{padding:20px;color:#667085;text-align:center;font-size:.78rem;line-height:1.5}
      @media(max-width:700px){.scamlens-stage{min-height:460px;gap:12px;padding:30px 16px}.scamlens-screen{width:45%;border-radius:22px}.scamlens-screen:nth-child(2){transform:translateY(22px) rotate(2deg)}.scamlens-live{left:7%;bottom:7%;font-size:.62rem}}
    `;
    document.head.appendChild(s);
  }

  async function text(url){
    const r=await fetch(url+'?v=20261004',{cache:'no-store',mode:'cors'});
    if(!r.ok) throw new Error('image chunk '+r.status);
    return (await r.text()).trim();
  }

  async function assemble(parts){
    const chunks=await Promise.all(parts.map(text));
    return 'data:image/webp;base64,'+chunks.join('');
  }

  async function hydrate(card){
    try{
      const [home,protection]=await Promise.all([assemble(HOME),assemble(PROTECTION)]);
      const h=card.querySelector('[data-scamlens="home"]');
      const p=card.querySelector('[data-scamlens="protection"]');
      if(h){h.src=home;h.removeAttribute('alt');}
      if(p){p.src=protection;p.removeAttribute('alt');}
    }catch(err){
      card.querySelectorAll('.scamlens-screen').forEach(el=>{
        if(!el.querySelector('img[src]')) el.innerHTML='<div class="scamlens-fallback">ScamLens Android screen</div>';
      });
      console.error('ScamLens portfolio images failed',err);
    }
  }

  function mount(){
    addStyle();
    const anchor=document.getElementById('datemate-gallery');
    if(!anchor) return false;
    let card=document.getElementById('scamlens');
    if(!card){
      anchor.insertAdjacentHTML('afterend',`<article class="project reveal on" id="scamlens" style="--accent:#17998f"><div class="project-copy"><div class="project-no">NEW · Android · Scam protection</div><h3>ScamLens</h3><div class="status"><i></i> Android beta</div><p>A privacy-focused Android safety app for checking suspicious messages, links, QR codes, screenshots and phone numbers, with call-protection tools for everyday scam awareness.</p><div class="features"><div class="feature"><b>01</b>Message risk scan</div><div class="feature"><b>02</b>QR & screenshot checks</div><div class="feature"><b>03</b>Phone verification</div><div class="feature"><b>04</b>Call & privacy protection</div></div><div class="project-links"><a href="#scamlens">Real Android screens</a></div></div><div class="project-visual"><div class="visual-grid"></div><div class="scamlens-stage"><div class="scamlens-screen"><img data-scamlens="home" aria-label="ScamLens Android message scanner screen"></div><div class="scamlens-screen"><img data-scamlens="protection" aria-label="ScamLens Protection Centre and Call Protection screen"></div><div class="scamlens-live">SCAMLENS · ANDROID<b>Scan · Verify · Protect</b></div></div></div></article>`);
      card=document.getElementById('scamlens');
    }
    if(card) hydrate(card);
    return !!card;
  }

  if(!mount()){
    if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',mount,{once:true});
    [300,900,1800,3500].forEach(ms=>setTimeout(mount,ms));
  }
})();
