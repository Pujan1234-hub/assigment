/* Visual-only premium ASSIGN button patch. No task logic or layout behavior changes. */
(() => {
  const style = document.createElement('style');
  style.textContent = `
    .assign button {
      position: relative;
      overflow: hidden;
      min-height: 46px;
      background: linear-gradient(180deg,#ffd86f 0%,#efb632 52%,#c98912 100%) !important;
      border: 1px solid #ffe59a !important;
      color: #201500 !important;
      border-radius: 11px !important;
      padding: 10px 16px !important;
      font-weight: 950 !important;
      letter-spacing: .035em;
      text-shadow: 0 1px 0 rgba(255,255,255,.36);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,.58),
        inset 0 -2px 0 rgba(122,77,0,.25),
        0 5px 0 #7e540d,
        0 8px 16px rgba(0,0,0,.30),
        0 0 0 1px rgba(239,182,50,.16);
      transform: translateY(0);
      transition: transform .08s ease, box-shadow .08s ease, filter .12s ease;
      -webkit-tap-highlight-color: transparent;
      touch-action: manipulation;
    }
    .assign button::after {
      content: '';
      position: absolute;
      inset: 1px 1px auto 1px;
      height: 42%;
      border-radius: 9px 9px 45% 45%;
      background: linear-gradient(180deg,rgba(255,255,255,.30),rgba(255,255,255,0));
      pointer-events: none;
    }
    .assign button:hover { filter: brightness(1.06) saturate(1.04); }
    .assign button:active {
      transform: translateY(4px) scale(.992);
      box-shadow:
        inset 0 2px 4px rgba(92,55,0,.24),
        inset 0 1px 0 rgba(255,255,255,.35),
        0 1px 0 #7e540d,
        0 3px 7px rgba(0,0,0,.24);
      filter: brightness(.96);
    }
    .assign button:focus-visible {
      outline: 2px solid #fff2bf;
      outline-offset: 3px;
    }
    @media(max-width:700px){
      .assign button{min-height:50px;font-size:15px;border-radius:12px !important;}
    }
  `;
  document.head.appendChild(style);
})();
