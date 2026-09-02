document.addEventListener('DOMContentLoaded',()=>{
  const EMAIL='pujanchapagain.software@gmail.com';

  // Current handcrafted/editorial portfolio.
  const editorialNav=document.querySelector('.navlinks');
  const work=document.getElementById('work');
  if(editorialNav && work){
    const desc=document.querySelector('meta[name="description"]');
    if(desc) desc.setAttribute('content','Pujan Chapagain — software portfolio featuring Team Tracker, FixCheck, FloodSafe Nepal and DateMate.');

    if(!editorialNav.querySelector('a[href="#datemate"]')){
      const a=document.createElement('a');
      a.href='#datemate'; a.textContent='DateMate';
      const about=editorialNav.querySelector('a[href="#about"]');
      if(about) editorialNav.insertBefore(a,about); else editorialNav.appendChild(a);
    }
    if(!editorialNav.querySelector('a[href="#contact"]')){
      const a=document.createElement('a');
      a.href='#contact'; a.textContent='Contact';
      editorialNav.appendChild(a);
    }

    const heroCopy=document.querySelector('.hero-copy');
    if(heroCopy && /Three products, three different problems:/i.test(heroCopy.textContent||'')){
      heroCopy.textContent='Four products, four different problems: coordinating people at work, figuring out why the internet is not behaving, making flood information more useful for people in Nepal, and helping people remember important expiry and renewal dates. I design, build, test and keep improving each one hands-on.';
    }

    const aside=document.querySelector('.hero-aside');
    if(aside && !aside.querySelector('[data-product="datemate"]')){
      const ticket=document.createElement('div');
      ticket.className='ticket';
      ticket.dataset.product='datemate';
      ticket.style.background='#eef5ff';
      ticket.style.transform='rotate(.3deg)';
      ticket.innerHTML='<div class="ticket-head"><h3>DateMate</h3><span class="tag">EARLY BUILD</span></div><p>A simple date and expiry reminder app for keeping important renewals and due dates from slipping past.</p><a href="#datemate">View build notes →</a>';
      aside.appendChild(ticket);
    }

    if(!document.getElementById('datemate')){
      const flood=document.getElementById('floodsafe');
      if(flood){
        const article=document.createElement('article');
        article.className='project';
        article.id='datemate';
        article.innerHTML=`<div class="project-side"><div><div class="project-index">04 / Date reminders</div><h3>DateMate</h3><div class="project-status"><span class="dot" style="background:#5f7fe8"></span> Early development</div></div><div class="side-links"><a href="#contact">Project contact ↗</a></div></div><div class="project-main"><div class="project-copy"><p>DateMate is a simple reminder app built around an easy problem to understand: important expiry, renewal and due dates are easy to forget when they live in different places. The aim is to keep those dates in one clear view and give people useful notice before they become urgent.</p><div class="bullets"><div class="bullet"><i>01</i><span>Fast add flow for an item and its important date.</span></div><div class="bullet"><i>02</i><span>Clear upcoming and expiry-focused reminders.</span></div><div class="bullet"><i>03</i><span>Simple blue mobile-first interface designed to stay easy to scan.</span></div><div class="bullet"><i>04</i><span>Currently in early development, with the core flow being built and tested first.</span></div></div></div><div class="preview" style="background:#eef5ff"><div class="windowbar"><span class="dots"><span></span><span></span><span></span></span><span>Date reminders</span></div><div class="phone"><div class="phone-screen" style="background:#f7faff"><div class="ticket-head"><strong>DateMate</strong><span class="tag">EARLY BUILD</span></div><div class="phone-title">What should I remember?</div><div class="phone-copy">Save the important date now, then see what is coming up without digging through notes.</div><div class="rows"><div class="row"><span>Upcoming</span><b class="blue">3 items</b></div><div class="row"><span>Due soon</span><b class="amber">1 item</b></div><div class="row"><span>Status</span><b class="green">Tracked</b></div></div><div class="big-action" style="background:#3157d5">ADD DATE</div></div></div></div></div>`;
        flood.insertAdjacentElement('afterend',article);
      }
    }

    if(!document.getElementById('contact')){
      const footer=document.querySelector('footer');
      if(footer){
        const contact=document.createElement('section');
        contact.id='contact';
        contact.innerHTML=`<div class="wrap"><div class="section-head"><div class="section-number">05</div><div class="section-title"><small>Contact</small><h2>Let’s talk software.</h2><p>For software, product, prototype, or collaboration enquiries.</p></div></div><div class="about-grid"><div class="about-card"><strong>Email</strong><span><a href="mailto:${EMAIL}">${EMAIL}</a></span></div><div class="about-copy"><p>Building practical software, testing it properly, and improving it through real use.</p><p class="small">Based in the United Kingdom · Software products & working prototypes</p></div></div></div>`;
        footer.parentNode.insertBefore(contact,footer);
      }
    }

    const foot=document.querySelector('.footlinks');
    if(foot){
      if(!foot.querySelector('a[href="#datemate"]')){
        const a=document.createElement('a'); a.href='#datemate'; a.textContent='DateMate'; foot.appendChild(a);
      }
      if(!foot.querySelector(`a[href="mailto:${EMAIL}"]`)){
        const a=document.createElement('a'); a.href=`mailto:${EMAIL}`; a.textContent='Email'; foot.appendChild(a);
      }
    }
    return;
  }

  // Legacy portfolio support: keep FloodSafe available on older layouts.
  if(document.getElementById('floodsafe')) return;

  document.querySelectorAll('.stat').forEach(el=>{
    if((el.textContent||'').includes('Active products')){
      const strong=el.querySelector('strong'); if(strong) strong.textContent='03';
    }
  });

  const nav=document.querySelector('.links');
  if(nav && !nav.querySelector('a[href="#floodsafe"]')){
    const platforms=nav.querySelector('a[href="#platforms"]');
    const a=document.createElement('a'); a.href='#floodsafe'; a.textContent='FloodSafe Nepal';
    if(platforms) nav.insertBefore(a,platforms); else nav.appendChild(a);
  }

  const style=document.createElement('style');
  style.textContent='.cards{grid-template-columns:repeat(3,1fr)}@media(max-width:850px){.cards{grid-template-columns:1fr}}';
  document.head.appendChild(style);

  const cards=document.querySelector('#products .cards');
  if(cards){
    const card=document.createElement('article');
    card.className='card';
    card.innerHTML='<div class="cardhead"><div class="icon">🌊</div><span class="status amber">Active Development</span></div><h3>FloodSafe Nepal</h3><div class="sub">नेपालका लागि local flood & river alert platform</div><p>A Nepal-focused safety app built around local-area flood awareness, live river-station updates and map-first risk context.</p><div class="actions"><a class="btn primary" href="./floodsafe-nepal/">Open web app ↗</a></div>';
    cards.appendChild(card);
  }
});