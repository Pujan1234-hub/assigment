/* PJBUILTS intro: startup only, original 2.65-second Android animation.
 * Does not modify the website's project DOM, form, router, or other scripts.
 */
(()=>{
  const id='pjbuilts-original-intro';
  const intro=document.getElementById(id);
  if(!intro)return;
  const skip=intro.querySelector('.pj-orig-skip');
  let finished=false;
  let timer;
  function finish(){
    if(finished)return;
    finished=true;
    clearTimeout(timer);
    intro.classList.add('pj-orig-dismissed');
    intro.setAttribute('aria-hidden','true');
    if(document.activeElement===skip)skip.blur();
    window.setTimeout(()=>{
      intro.remove();
      window.__pjbuiltsIntroFinished=true;
      document.dispatchEvent(new Event('pjbuilts:intro-complete'));
    },210);
  }
  skip?.addEventListener('click',finish,{once:true});
  // CSS also dismisses after 2.65 seconds if JS is delayed.
  // On every fresh homepage opening, play again, not on in-page anchor clicks.
  const reduced=window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches;
  timer=window.setTimeout(finish,reduced?0:2840);
  window.addEventListener('pagehide',finish,{once:true});
})();
