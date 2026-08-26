/* Team Tracker Control Room — premium visual-only theme.
   CSS only: no auth, GPS, map, shift, task or database behavior is changed. */
(() => {
  const style = document.createElement('style');
  style.id = 'tt-premium-control-room-ui';
  style.textContent = `
    :root{
      --tt-bg0:#030913;
      --tt-bg1:#07131f;
      --tt-bg2:#0a1a29;
      --tt-panel:#0a1825;
      --tt-panel2:#0d2030;
      --tt-line:rgba(118,158,190,.27);
      --tt-line-strong:rgba(128,177,214,.42);
      --tt-gold:#f2bd47;
      --tt-gold-soft:#ffe29a;
      --tt-cyan:#63c8ff;
      --tt-green:#62e49a;
      --tt-red:#ff8888;
      --tt-muted:#91a8ba;
      --tt-shadow:0 18px 48px rgba(0,0,0,.34);
    }

    html{background:var(--tt-bg0)}
    body{
      background:
        radial-gradient(circle at 12% -5%,rgba(41,116,163,.22),transparent 31%),
        radial-gradient(circle at 92% 12%,rgba(239,182,50,.07),transparent 28%),
        linear-gradient(180deg,var(--tt-bg0) 0%,#06101b 42%,#040b13 100%) !important;
      color:#f7fbff;
      min-height:100vh;
    }
    body:before{
      content:'';position:fixed;inset:0;pointer-events:none;z-index:-1;
      background-image:linear-gradient(rgba(255,255,255,.012) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.012) 1px,transparent 1px);
      background-size:34px 34px;
      mask-image:linear-gradient(to bottom,black,transparent 82%);
    }

    .wrap{max-width:1160px !important;padding:16px !important}
    .brand{
      margin:7px 2px 16px !important;padding:10px 12px;border:1px solid rgba(239,182,50,.14);
      border-radius:14px;background:linear-gradient(180deg,rgba(18,39,55,.72),rgba(5,17,28,.58));
      box-shadow:inset 0 1px rgba(255,255,255,.035),0 8px 24px rgba(0,0,0,.16)
    }
    .brand b{color:#ffd76e !important;font-size:12px;letter-spacing:.17em !important;text-shadow:0 0 18px rgba(239,182,50,.13)}
    .pill{background:rgba(239,182,50,.08);border-color:rgba(239,182,50,.36) !important;color:#f7ce70 !important;font-weight:800;letter-spacing:.035em}

    .card{
      position:relative;
      background:linear-gradient(145deg,rgba(12,29,43,.98),rgba(6,18,29,.98)) !important;
      border:1px solid var(--tt-line) !important;
      border-radius:22px !important;
      box-shadow:var(--tt-shadow),inset 0 1px 0 rgba(255,255,255,.035) !important;
      overflow:visible;
    }
    #app>.card:first-child:before{
      content:'';position:absolute;left:22px;right:22px;top:0;height:1px;
      background:linear-gradient(90deg,transparent,rgba(99,200,255,.42),rgba(242,189,71,.42),transparent);
    }
    #app>.card:last-child{margin-top:17px}

    .head{padding-bottom:13px;border-bottom:1px solid rgba(122,157,184,.17)}
    .head h2{
      font-size:clamp(27px,4vw,40px) !important;line-height:1.02;letter-spacing:-.025em;
      text-shadow:0 7px 24px rgba(0,0,0,.38)
    }
    #who{margin-top:7px;font-size:13px;letter-spacing:.025em;color:#8ca6bb !important}
    #signout{
      min-height:47px;padding:10px 15px !important;border-radius:13px !important;
      background:linear-gradient(180deg,#173149,#10263a) !important;border-color:#395b73 !important;
      color:#f3f8fc !important;box-shadow:inset 0 1px rgba(255,255,255,.07),0 6px 14px rgba(0,0,0,.2);
      transition:transform .08s ease,filter .12s ease
    }
    #signout:active{transform:translateY(2px);filter:brightness(.93)}

    .stats{gap:11px !important;margin:17px 0 21px !important}
    .stat{
      position:relative;min-height:92px;padding:14px 15px 13px !important;overflow:hidden;
      background:linear-gradient(145deg,rgba(5,18,29,.96),rgba(8,27,41,.96)) !important;
      border:1px solid var(--tt-line) !important;border-radius:16px !important;
      box-shadow:inset 0 1px rgba(255,255,255,.035),0 7px 18px rgba(0,0,0,.18)
    }
    .stat:before{content:'';position:absolute;left:0;right:0;top:0;height:3px;background:#55768f}
    .stat:nth-child(1):before{background:linear-gradient(90deg,#45d68b,#91ffc3)}
    .stat:nth-child(2):before{background:linear-gradient(90deg,#49a9e8,#75d7ff)}
    .stat:nth-child(3):before{background:linear-gradient(90deg,#b88a30,#f2c75f)}
    .stat:nth-child(4):before{background:linear-gradient(90deg,#d49932,#ffd777)}
    .stat small{font-size:10.5px !important;font-weight:850;letter-spacing:.11em;color:#879fb2 !important}
    .stat b{font-size:31px !important;line-height:1;margin-top:9px !important;letter-spacing:-.035em}
    .stat:nth-child(1) b{color:#c6ffe0}.stat:nth-child(2) b{color:#ccefff}.stat:nth-child(3) b{color:#fff1c5}.stat:nth-child(4) b{color:#ffe5a2}

    h3{
      font-size:18px;letter-spacing:-.01em;color:#f6fbff;margin-bottom:11px;
    }
    #app>.card:first-child>h3{
      display:flex;align-items:center;gap:9px;margin-top:22px !important
    }
    #app>.card:first-child>h3:before{
      content:'';width:4px;height:20px;border-radius:99px;background:linear-gradient(#69d2ff,#2f89c5);box-shadow:0 0 12px rgba(99,200,255,.2)
    }

    #mapbox.tt-live-map{
      border:1px solid rgba(114,163,199,.48) !important;border-radius:18px !important;
      box-shadow:0 13px 31px rgba(0,0,0,.3),0 0 0 1px rgba(255,255,255,.025) inset !important
    }
    .tt-chip{
      border-radius:11px !important;background:linear-gradient(180deg,rgba(6,23,36,.97),rgba(4,16,27,.94)) !important;
      border-color:rgba(126,173,207,.55) !important;box-shadow:0 7px 20px rgba(0,0,0,.34) !important
    }
    .tt-map-btn{
      border-radius:11px !important;background:linear-gradient(180deg,rgba(25,51,70,.97),rgba(10,30,45,.97)) !important;
      border-color:rgba(130,174,205,.48) !important;box-shadow:inset 0 1px rgba(255,255,255,.08),0 5px 12px rgba(0,0,0,.32) !important
    }
    .tt-map-btn:active{transform:translateY(2px);filter:brightness(.9)}
    .tt-attrib{opacity:.82;border:1px solid rgba(255,255,255,.16)}

    .tt-outside-wrap{
      margin-top:13px !important;padding:13px !important;border-radius:16px !important;
      background:linear-gradient(145deg,rgba(28,13,19,.96),rgba(13,11,18,.98)) !important;
      border-color:rgba(255,120,120,.28) !important;box-shadow:inset 0 1px rgba(255,255,255,.025),0 8px 20px rgba(0,0,0,.16)
    }
    .tt-outside-head{font-size:11px !important;letter-spacing:.06em;color:#ffcaca !important}
    .tt-outside-count{min-width:30px;text-align:center;background:linear-gradient(180deg,#812b37,#591820) !important;box-shadow:inset 0 1px rgba(255,255,255,.08)}
    .tt-outside-item{padding:11px 0 !important}.tt-outside-name{font-size:13px !important}.tt-outside-meta{color:#bdaeb5 !important}
    .tt-outside-link{display:inline-flex;align-items:center;gap:4px;color:#74ccff !important}

    #staff{margin-top:13px}
    #staff .row{
      position:relative;padding:16px !important;margin:12px 0 !important;border-radius:18px !important;
      background:linear-gradient(145deg,rgba(8,27,41,.99),rgba(5,20,31,.99)) !important;
      border:1px solid rgba(102,151,185,.31) !important;
      box-shadow:inset 0 1px rgba(255,255,255,.035),0 10px 24px rgba(0,0,0,.19)
    }
    #staff .row:before{
      content:'';position:absolute;left:0;top:18px;bottom:18px;width:3px;border-radius:0 99px 99px 0;background:linear-gradient(#5fcfff,#318ac4);opacity:.8
    }
    .rowtop{align-items:flex-start}.badge{font-size:15px;letter-spacing:.015em;color:#fff}.live,.stale{font-size:11px;letter-spacing:.055em;padding:5px 8px;border-radius:99px}
    .live{color:#8af0b2 !important;background:rgba(68,196,124,.09);border:1px solid rgba(83,217,143,.25)}
    .stale{color:#ffd88a !important;background:rgba(232,174,65,.08);border:1px solid rgba(240,201,101,.23)}
    .sub{color:#91a7b9 !important;line-height:1.4}

    .tt-shift-now{
      margin-top:10px !important;padding:10px 12px !important;border-radius:12px !important;
      background:linear-gradient(145deg,rgba(7,33,31,.88),rgba(6,24,32,.94)) !important;
      border-color:rgba(79,201,132,.3) !important;box-shadow:inset 3px 0 0 rgba(83,222,145,.7),inset 0 1px rgba(255,255,255,.025)
    }
    .tt-shift-now b{letter-spacing:.025em}.tt-shift-now .clock{display:inline-block;min-width:44px;color:#ffd271 !important;font-variant-numeric:tabular-nums}

    .assign{gap:9px !important;margin-top:13px !important}
    .assign input,.assign select{
      min-height:47px !important;background:linear-gradient(180deg,#071725,#06131f) !important;
      border:1px solid rgba(93,145,182,.48) !important;border-radius:12px !important;color:#f5f9fc !important;
      padding:11px 12px !important;box-shadow:inset 0 1px 2px rgba(0,0,0,.25);transition:border-color .15s ease,box-shadow .15s ease,background .15s ease
    }
    .assign input::placeholder{color:#71899d !important}
    .assign input:focus,.assign select:focus{
      outline:none;border-color:#62bde9 !important;background:#081a29 !important;
      box-shadow:0 0 0 3px rgba(71,169,222,.11),inset 0 1px 2px rgba(0,0,0,.18)
    }

    #shiftSafety{margin-top:22px !important;padding-top:19px !important;border-top:1px solid rgba(112,153,184,.23) !important}
    .tt-shift-head{margin-bottom:11px !important}.tt-shift-head h3{font-size:20px;margin:0 !important}.tt-shift-head small{font-size:11px;letter-spacing:.04em}
    .tt-shift-log{gap:9px !important}
    .tt-shift-item{
      padding:12px 13px !important;border-radius:14px !important;background:linear-gradient(145deg,rgba(7,23,35,.97),rgba(5,17,27,.97)) !important;
      border-color:rgba(100,146,178,.25) !important;box-shadow:inset 0 1px rgba(255,255,255,.025)
    }
    .tt-shift-item.active{
      background:linear-gradient(145deg,rgba(5,31,25,.96),rgba(4,21,22,.98)) !important;
      border-color:rgba(74,194,126,.35) !important;box-shadow:inset 3px 0 0 rgba(75,216,139,.7)
    }
    .tt-shift-item.ended{border-color:rgba(192,158,77,.25) !important}
    .tt-shift-name{font-size:13px !important}.tt-shift-meta{color:#a3b4c0 !important}.tt-shift-state{font-size:11px;letter-spacing:.045em}

    #app>.card:last-child>h3{
      display:flex;align-items:center;gap:9px;padding-bottom:11px;border-bottom:1px solid rgba(111,151,181,.18)
    }
    #app>.card:last-child>h3:before{content:'';width:4px;height:19px;border-radius:99px;background:linear-gradient(#f3c95d,#aa7720)}
    .task{
      padding:12px 5px !important;border-top:1px solid rgba(99,139,170,.17) !important;align-items:center
    }
    .task:first-child{border-top:0 !important}
    .status{justify-self:end;padding:5px 8px;border-radius:99px;font-size:10.5px;letter-spacing:.055em;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.08)}
    .status.assigned{background:rgba(239,202,105,.08);border-color:rgba(239,202,105,.2)}
    .status.acknowledged{background:rgba(101,191,255,.08);border-color:rgba(101,191,255,.2)}
    .status.completed{background:rgba(120,224,165,.08);border-color:rgba(120,224,165,.2)}
    .status.declined,.status.cancelled{background:rgba(242,162,162,.07);border-color:rgba(242,162,162,.18)}

    .toast,#shiftEventToast{
      backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
      box-shadow:0 14px 35px rgba(0,0,0,.42) !important
    }

    .login{background:linear-gradient(145deg,#0c2030,#071521) !important}
    .login h2{letter-spacing:-.02em}.login .field{min-height:48px;border-radius:12px !important;background:#06131f !important;border-color:#35536c !important}
    .login .field:focus{outline:none;border-color:#55b9e8 !important;box-shadow:0 0 0 3px rgba(85,185,232,.1)}

    @media(max-width:700px){
      .wrap{padding:10px !important}
      .card{border-radius:18px !important;padding:17px 14px !important}
      .brand{padding:8px 10px;margin-bottom:11px !important}
      .brand b{font-size:10px}.pill{font-size:9px;padding:5px 7px}
      .head{align-items:flex-start !important;gap:12px}.head h2{font-size:31px !important;max-width:220px}
      #signout{min-width:82px;font-size:12px;padding:10px 12px !important}
      .stats{grid-template-columns:repeat(2,minmax(0,1fr)) !important;gap:9px !important}
      .stat{min-height:88px;padding:13px !important}.stat b{font-size:28px !important}
      #staff .row{padding:15px 13px !important}
      .assign{gap:10px !important}.assign input,.assign select{min-height:51px !important;font-size:15px}
      .tt-shift-head h3{font-size:19px}.tt-shift-head small{font-size:10px}
      .tt-shift-item{padding:12px !important;gap:6px !important}
      .status{justify-self:start}
    }

    @media(min-width:900px){
      #app>.card:first-child{padding:22px !important}
      #staff .row{padding:17px 18px !important}
    }

    @media(prefers-reduced-motion:reduce){*{scroll-behavior:auto !important}}
  `;
  document.head.appendChild(style);
})();
