(()=>{
  if(window.__pjContactV3) return;
  window.__pjContactV3=true;
  const URL='https://nvfqxsnyrgjszrvmlrgf.supabase.co';
  const KEY='sb_publishable_Mo_KNAmLRcBWdg6wC7QGVQ_hbEGkAw5';
  const email='pujanchapagain.software@gmail.com';

  const CSS=`
    .pj-contact-form{display:grid;gap:12px;margin-top:22px}
    .pj-contact-form .row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
    .pj-contact-form input,.pj-contact-form textarea,.pj-contact-form select{width:100%;box-sizing:border-box;border:1px solid rgba(38,51,75,.16);border-radius:14px;background:#fff;color:#20293a;padding:13px 14px;font:inherit;outline:none;box-shadow:0 8px 24px rgba(38,51,75,.04)}
    .pj-contact-form input:focus,.pj-contact-form textarea:focus,.pj-contact-form select:focus{border-color:#3157d5;box-shadow:0 0 0 3px rgba(49,87,213,.10)}
    .pj-contact-form textarea{min-height:150px;resize:vertical}
    .pj-contact-form select{appearance:none}
    .urgent-check{display:flex!important;gap:10px;align-items:flex-start;padding:12px 13px;border:1px solid rgba(38,51,75,.14);border-radius:14px;background:#fffaf3;color:#293247}
    .urgent-check input{width:auto!important;margin-top:3px;box-shadow:none}
    .urgent-check span{display:grid;gap:2px}.urgent-check b{color:#20293a}.urgent-check small,.form-note{color:#718096;font-size:.72rem}
    .pj-contact-form button{border:0;border-radius:14px;padding:13px 16px;font-weight:900;cursor:pointer;background:linear-gradient(135deg,#3157d5,#7357d6);color:#fff;box-shadow:0 12px 28px rgba(49,87,213,.18)}
    .pj-contact-form button:disabled{opacity:.55;cursor:wait}.contact-result{min-height:18px;color:#64748b;font-size:.75rem}.contact-result.ok{color:#16794f}.contact-result.err{color:#b83b3b}
    .contact-email{display:inline-block;margin-top:8px}
    @media(max-width:700px){.pj-contact-form .row{grid-template-columns:1fr}}
  `;

  function style(){if(document.getElementById('pj-contact-v3-style'))return;const s=document.createElement('style');s.id='pj-contact-v3-style';s.textContent=CSS;document.head.appendChild(s)}
  function sid(){let v=localStorage.getItem('pj_portfolio_sid');if(!v){v=crypto.randomUUID();localStorage.setItem('pj_portfolio_sid',v)}return v}
  async function post(table,body){return fetch(`${URL}/rest/v1/${table}`,{method:'POST',headers:{apikey:KEY,Authorization:`Bearer ${KEY}`,'Content-Type':'application/json',Prefer:'return=minimal'},body:JSON.stringify(body)})}
  async function visit(){try{await post('portfolio_visits',{session_id:sid(),page_path:location.pathname+location.hash,referrer:document.referrer||null,user_agent:navigator.userAgent.slice(0,500)})}catch{}}

  function mount(){
    style();
    const card=document.querySelector('#contact.contact-card')||document.querySelector('#contact .contact-card')||document.getElementById('contact');
    if(!card||card.querySelector('#portfolio-contact-form')) return;
    let mail=card.querySelector('.contact-email');
    if(!mail){mail=document.createElement('a');mail.className='contact-email';mail.href=`mailto:${email}`;mail.textContent=email+' ↗';card.appendChild(mail)}
    const form=document.createElement('form');
    form.className='pj-contact-form';form.id='portfolio-contact-form';
    form.innerHTML=`<div class="row"><input name="name" required maxlength="120" autocomplete="name" placeholder="Your name *"><input name="email" required type="email" maxlength="320" autocomplete="email" placeholder="Email address *"></div><div class="row"><input name="phone" maxlength="40" autocomplete="tel" placeholder="Phone / WhatsApp (optional)"><input name="company" maxlength="120" autocomplete="organization" placeholder="Company / organisation (optional)"></div><div class="row"><select name="enquiry_type" aria-label="Enquiry type"><option>Project enquiry</option><option>Collaboration</option><option>Website / app</option><option>AI / automation</option><option>Other</option></select><input name="subject" maxlength="200" placeholder="Subject"></div><textarea name="message" required maxlength="5000" placeholder="Tell me what you would like to build, improve or discuss *"></textarea><label class="urgent-check"><input type="checkbox" name="urgent"><span><b>Urgent contact</b><small>Mark this only when you need a priority response.</small></span></label><button type="submit">Send message ↗</button><div class="contact-result" id="contact-result" aria-live="polite"></div><p class="form-note">Your message is sent securely to my private PJBUILTS contact inbox.</p>`;
    card.appendChild(form);
    form.addEventListener('submit',async e=>{e.preventDefault();const btn=form.querySelector('button');const out=form.querySelector('#contact-result');btn.disabled=true;out.className='contact-result';out.textContent='Sending…';const f=new FormData(form);try{const r=await post('portfolio_contacts',{name:f.get('name'),email:f.get('email'),subject:f.get('subject')||null,phone:f.get('phone')||null,company:f.get('company')||null,enquiry_type:f.get('enquiry_type')||'Project enquiry',message:f.get('message'),is_urgent:f.get('urgent')==='on'});if(!r.ok)throw new Error('send');form.reset();out.className='contact-result ok';out.textContent='Message sent successfully.'}catch{out.className='contact-result err';out.textContent='Could not send. Please use the email link above.'}finally{btn.disabled=false}})
  }

  visit();mount();
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});
  setTimeout(mount,400);setTimeout(mount,1400);
})();

(()=>{
  if(document.getElementById('pjbuilts-scamlens-live')) return;
  const s=document.createElement('script');
  s.id='pjbuilts-scamlens-live';
  s.src='./portfolio-scamlens.js?v=20261004-live1';
  s.defer=true;
  document.head.appendChild(s);
})();
