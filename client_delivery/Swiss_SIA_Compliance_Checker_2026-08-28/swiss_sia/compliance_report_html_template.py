"""HTML/CSS/JS template for the interactive SIA compliance dashboard.

Kept separate from ``compliance_report_html.py`` so the (large) presentation
string never obscures the data-mapping logic. The template is fully data-driven:
it renders everything from ``window.__SIA_DATA__`` (injected in place of
``__DATA_JSON__``) and the page name (``__PAGE_TITLE__``). Pure text, no imports,
no ``iesve``.

Brand: IES / IESVE (iesve.com) — IES navy ``#041b4a`` band, VE blue accent
``#3daedc`` / ``#004387``, IES slate text on the ``#f5f7f9`` ground, an
Aleo-style slab display paired with a Camphor-Pro-style geometric sans (system
fallbacks, since the CSP does not load web fonts).
"""

TEMPLATE = r"""<title>__PAGE_TITLE__</title>
<style>
  :root{
    --bg:#F5F7F9; --surface:#FFFFFF; --surface-2:#ECEFF3;
    --ink:#1E293B; --ink-2:#334155; --ink-3:#64748B;
    --border:#E2E8F0; --border-strong:#CBD5E1;
    --accent:#004387; --accent-2:#3DAEDC; --accent-ink:#FFFFFF; --accent-soft:#E8F1FB;
    --header-bg:#041B4A; --header-bg-2:#004387; --header-ink:#EAF2FB; --header-ink-2:#9DB2D0; --header-line:#1B3A63;
    --ok:#16A34A; --ok-bg:#E7F6ED;
    --crit:#DC2626; --crit-bg:#FBEAEA;
    --warn:#B45309; --warn-bg:#FBF0DD;
    --unknown:#64748B; --unknown-bg:#EEF2F6;
    --info:#004387; --info-bg:#E8F1FB;
    --shadow:0 1px 2px rgba(4,27,74,.06), 0 10px 26px rgba(4,27,74,.07);
    --font-display:"Rockwell","Roboto Slab","Bitter",Georgia,"Segoe UI",serif;
    --font-sans:"Segoe UI","Avenir Next",Avenir,"Helvetica Neue",system-ui,Roboto,Arial,sans-serif;
    --font-mono:"Cascadia Code","SF Mono",Consolas,ui-monospace,monospace;
    --r:10px;
  }
  @media (prefers-color-scheme:dark){
    :root:not([data-theme="light"]){
      --bg:#0A1428; --surface:#0F1F3D; --surface-2:#13284A;
      --ink:#E7EEF7; --ink-2:#B7C6DE; --ink-3:#7E93B4;
      --border:#22345B; --border-strong:#2E4470;
      --accent:#3DAEDC; --accent-2:#5BC5EA; --accent-ink:#04122B; --accent-soft:#12294A;
      --header-bg:#020B1E; --header-bg-2:#041B4A; --header-ink:#EAF2FB; --header-ink-2:#8AA3C8; --header-line:#183156;
      --ok:#34D399; --ok-bg:#0E2A20;
      --crit:#F87171; --crit-bg:#2E1416;
      --warn:#F59E0B; --warn-bg:#2C2008;
      --unknown:#94A3B8; --unknown-bg:#172542;
      --info:#3DAEDC; --info-bg:#0F2A44;
      --shadow:0 1px 2px rgba(0,0,0,.4), 0 12px 30px rgba(0,0,0,.45);
    }
  }
  :root[data-theme="dark"]{
    --bg:#0A1428; --surface:#0F1F3D; --surface-2:#13284A;
    --ink:#E7EEF7; --ink-2:#B7C6DE; --ink-3:#7E93B4;
    --border:#22345B; --border-strong:#2E4470;
    --accent:#3DAEDC; --accent-2:#5BC5EA; --accent-ink:#04122B; --accent-soft:#12294A;
    --header-bg:#020B1E; --header-bg-2:#041B4A; --header-ink:#EAF2FB; --header-ink-2:#8AA3C8; --header-line:#183156;
    --ok:#34D399; --ok-bg:#0E2A20;
    --crit:#F87171; --crit-bg:#2E1416;
    --warn:#F59E0B; --warn-bg:#2C2008;
    --unknown:#94A3B8; --unknown-bg:#172542;
    --info:#3DAEDC; --info-bg:#0F2A44;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 12px 30px rgba(0,0,0,.45);
  }
  *{box-sizing:border-box;}
  body{margin:0; background:var(--bg); color:var(--ink); font-family:var(--font-sans); font-size:15px; line-height:1.5; -webkit-font-smoothing:antialiased;}
  .wrap{max-width:1180px; margin:0 auto; padding:0 20px 64px;}
  h1{margin:0; text-wrap:balance;}
  button{font-family:inherit;}
  :focus-visible{outline:2px solid var(--accent-2); outline-offset:2px; border-radius:6px;}

  .band{background:linear-gradient(115deg,var(--header-bg),var(--header-bg-2)); color:var(--header-ink); border-bottom:3px solid var(--accent-2);}
  .band-inner{max-width:1180px; margin:0 auto; padding:22px 20px;}
  .topbar{display:flex; align-items:center; justify-content:space-between; gap:16px; flex-wrap:wrap;}
  .brand{display:flex; align-items:center; gap:12px;}
  .mark{width:36px; height:36px; flex:0 0 auto;}
  .brand-txt{display:flex; flex-direction:column; line-height:1.15;}
  .brand-txt .p{font-family:var(--font-display); font-weight:700; letter-spacing:.01em; font-size:16px;}
  .brand-txt .s{font-size:11px; color:var(--header-ink-2); letter-spacing:.15em; text-transform:uppercase; margin-top:2px;}
  .theme-btn{background:rgba(255,255,255,.06); color:var(--header-ink-2); border:1px solid var(--header-line); border-radius:8px; padding:7px 12px; font-size:12.5px; cursor:pointer; display:flex; align-items:center; gap:7px;}
  .theme-btn:hover{color:var(--header-ink); border-color:var(--header-ink-2);}

  h1.title{font-family:var(--font-display); font-size:26px; font-weight:700; letter-spacing:-.01em; margin:22px 0 4px;}
  .subtitle{color:var(--header-ink-2); font-size:13.5px;}

  .idgrid{display:grid; grid-template-columns:repeat(auto-fit,minmax(155px,1fr)); gap:1px; background:var(--header-line); border:1px solid var(--header-line); border-radius:10px; overflow:hidden; margin-top:18px;}
  .idcell{background:rgba(4,27,74,.55); padding:11px 14px;}
  .idcell .k{font-size:10px; text-transform:uppercase; letter-spacing:.13em; color:var(--header-ink-2);}
  .idcell .v{font-size:13.5px; font-weight:600; margin-top:3px; color:var(--header-ink); overflow-wrap:anywhere;}
  .idcell .v.mono{font-family:var(--font-mono); font-weight:500; font-size:12.5px;}

  .verdict{display:flex; align-items:center; gap:14px; margin-top:16px; padding:14px 16px; background:rgba(255,255,255,.05); border:1px solid var(--header-line); border-left:4px solid var(--warn); border-radius:10px;}
  .verdict.ok{border-left-color:var(--ok);} .verdict.crit{border-left-color:var(--crit);} .verdict.warn{border-left-color:var(--warn);}
  .verdict .dot{width:12px;height:12px;border-radius:50%;background:var(--warn);flex:0 0 auto;box-shadow:0 0 0 4px rgba(180,83,9,.2);}
  .verdict.ok .dot{background:var(--ok);box-shadow:0 0 0 4px rgba(22,163,74,.2);}
  .verdict.crit .dot{background:var(--crit);box-shadow:0 0 0 4px rgba(220,38,38,.2);}
  .verdict .vt{font-weight:700; font-size:15px;}
  .verdict .vd{color:var(--header-ink-2); font-size:12.5px; margin-top:2px;}

  .outstanding{margin-top:24px; background:var(--surface); border:1px solid var(--border); border-left:4px solid var(--accent-2); border-radius:var(--r); padding:16px 18px; box-shadow:var(--shadow);}
  .outstanding h2{margin:0 0 4px; font-family:var(--font-display); font-size:15px; font-weight:700; color:var(--ink); letter-spacing:-.01em;}
  .outstanding .lead{color:var(--ink-3); font-size:12px; margin:0 0 12px;}
  .outstanding ol{list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:9px; counter-reset:oi;}
  .outstanding li{counter-increment:oi; display:grid; grid-template-columns:26px 1fr; gap:11px; align-items:start;}
  .outstanding li::before{content:counter(oi); grid-row:1/3; width:24px; height:24px; border-radius:50%; background:var(--accent-soft); color:var(--accent); font-size:12px; font-weight:700; display:flex; align-items:center; justify-content:center;}
  .outstanding li.crit::before{background:var(--crit-bg); color:var(--crit);}
  .outstanding li.warn::before{background:var(--warn-bg); color:var(--warn);}
  .outstanding .oi-label{font-weight:650; font-size:13px; color:var(--ink);}
  .outstanding .oi-detail{font-size:12.5px; color:var(--ink-2); line-height:1.45; margin-top:1px;}
  .outstanding.clear{border-left-color:var(--ok);}
  .outstanding.clear .none{display:flex; align-items:center; gap:9px; color:var(--ok); font-size:13px; font-weight:600;}

  .limitations{margin-top:24px; background:var(--surface); border:1px solid var(--border); border-left:4px solid var(--unknown); border-radius:var(--r); padding:16px 18px; box-shadow:var(--shadow);}
  .limitations h2{margin:0 0 4px; font-family:var(--font-display); font-size:15px; font-weight:700; color:var(--ink); letter-spacing:-.01em;}
  .limitations .lead{color:var(--ink-3); font-size:12px; margin:0 0 12px;}
  .limitations ul{list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:10px;}
  .limitations li{border-top:1px solid var(--border); padding-top:10px;}
  .limitations li:first-child{border-top:0; padding-top:0;}
  .limitations .lt{font-weight:650; font-size:13px; color:var(--ink); display:flex; align-items:center; gap:8px;}
  .limitations .lt::before{content:""; width:7px; height:7px; border-radius:2px; background:var(--unknown); flex:0 0 auto;}
  .limitations .lw{font-size:12.5px; color:var(--ink-2); line-height:1.5; margin-top:3px;}
  .governance{margin-top:24px; background:var(--surface); border:1px solid var(--border); border-radius:var(--r); padding:16px 18px; box-shadow:var(--shadow);}
  .governance h2{margin:0 0 5px; font-family:var(--font-display); font-size:15px; color:var(--ink);}
  .governance .legal{font-size:12.5px; line-height:1.5; color:var(--ink-2); margin:8px 0 14px; padding:10px 12px; background:var(--bg); border-left:4px solid var(--unknown);}
  .gov-item{border-top:1px solid var(--border); padding:11px 0;}
  .gov-item:first-of-type{border-top:0;}
  .gov-head{display:flex; justify-content:space-between; gap:12px; align-items:center; font-weight:650;}
  .gov-status{font-size:11px; padding:3px 7px; border-radius:999px; background:var(--bg); white-space:nowrap;}
  .gov-grid{display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:7px 18px; margin-top:7px; font-size:12px; line-height:1.45; color:var(--ink-2);}
  .gov-grid b{display:block; color:var(--ink-3); font-size:10px; text-transform:uppercase; letter-spacing:.04em;}
  @media(max-width:760px){.gov-grid{grid-template-columns:1fr;}}

  .summary{display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-top:24px;}
  .tile{background:var(--surface); border:1px solid var(--border); border-radius:var(--r); padding:14px 16px; box-shadow:var(--shadow); position:relative; overflow:hidden; cursor:pointer; text-align:left; transition:transform .12s ease, border-color .12s ease;}
  .tile:hover{transform:translateY(-2px); border-color:var(--border-strong);}
  .tile.active{border-color:var(--accent); box-shadow:0 0 0 1px var(--accent), var(--shadow);}
  .tile .stripe{position:absolute; left:0; top:0; bottom:0; width:4px;}
  .tile .n{font-size:30px; font-weight:750; letter-spacing:-.02em; font-variant-numeric:tabular-nums;}
  .tile .l{font-size:12.5px; color:var(--ink-2); margin-top:2px;}
  .tile.meter .n{font-size:26px;}
  .tile .meter-track{height:7px;border-radius:6px;background:var(--surface-2);overflow:hidden;margin-top:10px;border:1px solid var(--border);}
  .tile .meter-fill{height:100%;background:linear-gradient(90deg,var(--accent),var(--accent-2));border-radius:6px;}
  .tile.meter .hint{font-size:10.5px;color:var(--ink-3);margin-top:7px;line-height:1.35;}

  .controls{display:flex; flex-wrap:wrap; gap:12px; align-items:center; margin-top:26px; padding:14px; background:var(--surface); border:1px solid var(--border); border-radius:var(--r); box-shadow:var(--shadow); position:sticky; top:0; z-index:5;}
  .search{flex:1 1 220px; min-width:180px; display:flex; align-items:center; gap:8px; background:var(--surface-2); border:1px solid var(--border); border-radius:8px; padding:8px 11px;}
  .search input{border:0; background:transparent; color:var(--ink); font-size:14px; width:100%; outline:none;}
  .search svg{flex:0 0 auto; color:var(--ink-3);}
  .selwrap{display:flex; align-items:center; gap:8px;}
  .selwrap label{font-size:12px; color:var(--ink-2); text-transform:uppercase; letter-spacing:.08em;}
  select{font-family:inherit; font-size:13.5px; color:var(--ink); background:var(--surface-2); border:1px solid var(--border); border-radius:8px; padding:8px 10px; cursor:pointer;}
  .reset{background:transparent;border:1px solid var(--border);color:var(--ink-2);border-radius:8px;padding:8px 12px;font-size:13px;cursor:pointer;}
  .reset:hover{border-color:var(--border-strong);color:var(--ink);}

  .chips{display:flex; flex-wrap:wrap; gap:7px; margin-top:14px; align-items:center;}
  .chips .lbl{font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink-3);font-weight:700;margin-right:2px;}
  .chip{border:1px solid var(--border); background:var(--surface); color:var(--ink-2); border-radius:20px; padding:6px 13px; font-size:12.5px; cursor:pointer; display:inline-flex; align-items:center; gap:6px; transition:all .12s ease;}
  .chip:hover{border-color:var(--border-strong); color:var(--ink);}
  .chip.on{background:var(--accent); color:var(--accent-ink); border-color:var(--accent);}
  .chip .c{font-family:var(--font-mono); font-size:11px; opacity:.85;}

  .tablecard{margin-top:16px; background:var(--surface); border:1px solid var(--border); border-radius:var(--r); box-shadow:var(--shadow); overflow:hidden;}
  .thead{display:grid; grid-template-columns:2.4fr 1.1fr .9fr 1.5fr 1.1fr 34px; gap:12px; padding:11px 18px; border-bottom:1px solid var(--border); background:var(--surface-2); font-size:11px; text-transform:uppercase; letter-spacing:.09em; color:var(--ink-3); font-weight:700;}
  .thead .sortable{cursor:pointer; user-select:none; display:inline-flex; align-items:center; gap:4px;}
  .thead .sortable:hover{color:var(--ink-2);}
  .sectlabel{font-family:var(--font-display); padding:11px 18px 9px; font-size:13px; font-weight:700; letter-spacing:.01em; color:var(--accent); background:var(--surface-2); border-bottom:1px solid var(--border); display:flex; align-items:center; gap:9px;}
  .sectlabel .count{color:var(--ink-3); font-weight:600; font-family:var(--font-mono); font-size:11px;}

  .crit{border-bottom:1px solid var(--border);}
  .crit:last-child{border-bottom:0;}
  .crit-head{width:100%; text-align:left; background:transparent; border:0; cursor:pointer; color:inherit; display:grid; grid-template-columns:2.4fr 1.1fr .9fr 1.5fr 1.1fr 34px; gap:12px; align-items:center; padding:13px 18px; transition:background .1s ease;}
  .crit-head:hover{background:var(--surface-2);}
  .crit-name{font-weight:600; font-size:14px;}
  .crit-sub{font-size:11.5px; color:var(--ink-3); margin-top:2px; font-family:var(--font-mono); overflow-wrap:anywhere;}
  .cell-sect{font-size:12.5px; color:var(--ink-2);}
  .val{font-family:var(--font-mono); font-size:12.5px; color:var(--ink-2); font-variant-numeric:tabular-nums; overflow-wrap:anywhere;}
  .val b{color:var(--ink); font-weight:600;}
  .type-tag{font-size:10.5px; letter-spacing:.05em; text-transform:uppercase; font-weight:700; padding:3px 8px; border-radius:5px; white-space:nowrap;}
  .type-decisif{color:var(--accent); background:var(--accent-soft);}
  .type-diagnostic{color:var(--ink-2); background:var(--surface-2); border:1px solid var(--border);}
  .badge{display:inline-flex; align-items:center; gap:7px; font-size:12.5px; font-weight:650; padding:5px 11px; border-radius:20px; white-space:nowrap;}
  .badge .d{width:8px;height:8px;border-radius:50%;flex:0 0 auto;}
  .st-conforme{color:var(--ok); background:var(--ok-bg);} .st-conforme .d{background:var(--ok);}
  .st-non_conforme{color:var(--crit); background:var(--crit-bg);} .st-non_conforme .d{background:var(--crit);}
  .st-a_determiner{color:var(--warn); background:var(--warn-bg);} .st-a_determiner .d{background:var(--warn);}
  .st-non_verifiable{color:var(--unknown); background:var(--unknown-bg);} .st-non_verifiable .d{background:var(--unknown);}
  .st-ecart{color:var(--info); background:var(--info-bg);} .st-ecart .d{background:var(--info);}
  .chev{color:var(--ink-3); transition:transform .18s ease; justify-self:center;}
  .crit.open .chev{transform:rotate(90deg); color:var(--accent);}
  .crit-detail{display:none; padding:2px 18px 20px; background:var(--surface-2);}
  .crit.open .crit-detail{display:block; animation:reveal .18s ease;}
  @keyframes reveal{from{opacity:0; transform:translateY(-4px);} to{opacity:1; transform:none;}}
  .detail-grid{display:grid; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); gap:16px; padding-top:14px;}
  .dblock .dk{font-size:10.5px; text-transform:uppercase; letter-spacing:.1em; color:var(--ink-3); font-weight:700; margin-bottom:5px;}
  .dblock .dv{font-size:13.5px; color:var(--ink); line-height:1.5; overflow-wrap:anywhere;}
  .article{font-family:var(--font-mono); font-size:12px; color:var(--accent); background:var(--accent-soft); padding:3px 8px; border-radius:6px; display:inline-block;}
  .caveat{margin-top:14px; display:flex; gap:10px; align-items:flex-start; padding:11px 13px; border:1px solid var(--warn); background:var(--warn-bg); border-radius:8px; color:var(--warn); font-size:12.5px; line-height:1.45;}
  .caveat svg{flex:0 0 auto; margin-top:1px;}
  .caveat code{font-family:var(--font-mono); font-weight:700;}
  .empty{padding:48px 20px; text-align:center; color:var(--ink-3); font-size:14px;}

  .foot{margin-top:26px; padding:18px 20px; border:1px dashed var(--border-strong); border-radius:var(--r); background:var(--surface); color:var(--ink-2); font-size:12.5px; line-height:1.6;}
  .foot b{color:var(--ink);}

  @media (max-width:760px){
    .thead{display:none;}
    .crit-head{grid-template-columns:1fr auto; gap:8px 12px; grid-template-areas:"name chev" "meta chev" "status chev";}
    .crit-head>.cn{grid-area:name;} .crit-head>.cmeta{grid-area:meta; display:flex; gap:10px; flex-wrap:wrap; align-items:center;} .crit-head>.cstatus{grid-area:status;} .crit-head>.chev{grid-area:chev; align-self:start;}
    .crit-head>.cmeta>.cell-sect-col, .crit-head>.cmeta>.type-col, .crit-head>.cmeta>.val-col{display:inline-flex;}
  }
  @media (min-width:761px){ .crit-head .cmeta{display:contents;} }
  @media (prefers-reduced-motion:reduce){ *{animation:none!important; transition:none!important;} }
</style>

<div class="band"><div class="band-inner">
  <div class="topbar">
    <div class="brand">
      <svg class="mark" viewBox="0 0 40 40" fill="none" aria-hidden="true">
        <rect x="2" y="2" width="36" height="36" rx="8" fill="var(--accent-2)"/>
        <rect x="9" y="20" width="5" height="11" rx="1.2" fill="#fff" opacity=".9"/>
        <rect x="17.5" y="14" width="5" height="17" rx="1.2" fill="#fff" opacity=".9"/>
        <rect x="26" y="9" width="5" height="22" rx="1.2" fill="#fff"/>
      </svg>
      <div class="brand-txt"><span class="p" id="brandP"></span><span class="s" id="brandS"></span></div>
    </div>
    <button class="theme-btn" id="themeBtn" type="button" aria-label="theme">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z"/></svg>
      <span id="themeLbl"></span>
    </button>
  </div>
  <h1 class="title" id="pageTitle"></h1>
  <div class="subtitle" id="pageSub"></div>
  <div class="idgrid" id="idgrid"></div>
  <div class="verdict" id="verdictBox">
    <span class="dot"></span>
    <div><div class="vt" id="verdictTitle"></div><div class="vd" id="verdictDetail"></div></div>
  </div>
</div></div>

<div class="wrap">
  <section class="outstanding" id="outstanding" hidden></section>
  <div class="summary" id="summary"></div>
  <div class="controls">
    <div class="search">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>
      <input id="search" type="text" aria-label="search"/>
    </div>
    <div class="selwrap"><label for="sort" id="sortLbl"></label><select id="sort"></select></div>
    <button class="reset" id="reset" type="button"></button>
  </div>
  <div class="chips" id="statusChips" role="group"></div>
  <div class="chips" id="sectionChips" role="group"></div>
  <div class="tablecard">
    <div class="thead" id="thead"></div>
    <div id="rows"></div>
  </div>
  <section class="limitations" id="limitations" hidden></section>
  <section class="governance" id="governance" hidden></section>
  <div class="foot" id="foot"></div>
</div>

<script>
window.__SIA_DATA__ = __DATA_JSON__;
(function(){
  "use strict";
  var D=window.__SIA_DATA__||{}, M=D.meta||{}, UI=M.ui||{}, C=(D.criteria||[]).slice();
  var SECT=M.sectionLabels||{}, SORDER=M.sectionOrder||[], STL=M.statusLabels||{};
  var SECT_IDX={}; SORDER.forEach(function(s,i){SECT_IDX[s]=i;});
  var STATUS_ORDER={conforme:0,non_conforme:1,a_determiner:2,ecart:3,non_verifiable:4};
  var SEV={haute:0,moyenne:1,basse:2}, SEVL={haute:UI.sev_haute,moyenne:UI.sev_moyenne,basse:UI.sev_basse};
  var state={q:"",sort:"section",statuses:new Set(),section:"all"};
  var $=function(id){return document.getElementById(id);};
  function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
  function badge(st){return '<span class="badge st-'+st+'"><span class="d"></span>'+esc(STL[st]||st)+'</span>';}

  function head(){
    $("brandP").textContent=UI.product||""; $("brandS").textContent=UI.brand_sub||"";
    $("pageTitle").textContent=UI.title||""; $("pageSub").textContent=UI.subtitle||"";
    $("idgrid").innerHTML=(M.identification||[]).map(function(f){
      return '<div class="idcell"><div class="k">'+esc(f.k)+'</div><div class="v'+(f.mono?' mono':'')+'">'+esc(f.v)+'</div></div>';
    }).join("");
    var v=M.verdict||{}; var box=$("verdictBox"); box.className="verdict "+(v.tone||"warn");
    $("verdictTitle").textContent=v.title||""; $("verdictDetail").innerHTML=v.detail||"";
    outstanding();
    limitations();
    governance();
    $("search").placeholder=UI.search||""; $("sortLbl").textContent=UI.sort||""; $("reset").textContent=UI.reset||"";
    $("foot").innerHTML=UI.scope||"";
    var so=[["section",UI.sort_section],["status",UI.sort_status],["severity",UI.sort_severity],["name",UI.sort_name],["type",UI.sort_type]];
    $("sort").innerHTML=so.map(function(o){return '<option value="'+o[0]+'">'+esc(o[1])+'</option>';}).join("");
    $("thead").innerHTML=''+
      '<div class="sortable" data-sort="name">'+esc(UI.criterion)+'</div>'+
      '<div class="sortable" data-sort="section">'+esc(UI.section)+'</div>'+
      '<div class="sortable" data-sort="type">'+esc(UI.type)+'</div>'+
      '<div>'+esc(UI.measured_ref)+'</div>'+
      '<div class="sortable" data-sort="status">'+esc(UI.status)+'</div><div></div>';
  }

  function outstanding(){
    var el=$("outstanding"); if(!el)return;
    var items=M.outstanding||[];
    if(!items.length){
      el.className="outstanding clear"; el.hidden=false;
      el.innerHTML='<h2>'+esc(UI.outstanding_title||"")+'</h2>'+
        '<div class="none"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M20 6 9 17l-5-5"/></svg>'+
        esc(UI.outstanding_none||"")+'</div>';
      return;
    }
    el.className="outstanding"; el.hidden=false;
    el.innerHTML='<h2>'+esc(UI.outstanding_title||"")+'</h2>'+
      '<ol>'+items.map(function(it){
        return '<li class="'+esc(it.tone||"warn")+'">'+
          '<div class="oi-label">'+esc(it.label||"")+'</div>'+
          '<div class="oi-detail">'+esc(it.detail||"")+'</div></li>';
      }).join("")+'</ol>';
  }

  function limitations(){
    var el=$("limitations"); if(!el)return;
    var items=M.limitations||[];
    if(!items.length){el.hidden=true;return;}
    el.hidden=false;
    el.innerHTML='<h2>'+esc(UI.limitations_title||"")+'</h2>'+
      '<div class="lead">'+esc(UI.limitations_lead||"")+'</div>'+
      '<ul>'+items.map(function(it){
        return '<li><div class="lt">'+esc(it.title||"")+'</div>'+
          '<div class="lw">'+esc(it.why||"")+'</div></li>';
      }).join("")+'</ul>';
  }

  function governance(){
    var el=$("governance"), g=M.governance||{}, items=g.findings||[], l=g.labels||{};
    if(!el||!items.length){if(el)el.hidden=true;return;}
    el.hidden=false;
    el.innerHTML='<h2>'+esc(g.title||"")+'</h2>'+
      '<div><strong>'+esc(g.overall_label||"")+':</strong> '+esc(g.overall_status_label||"")+'</div>'+
      '<div class="legal">'+esc(g.legal_wording||"")+'</div>'+
      items.map(function(it){return '<div class="gov-item">'+
        '<div class="gov-head"><span>'+esc(it.title||"")+'</span><span class="gov-status">'+esc(it.status_label||it.status||"")+'</span></div>'+
        '<div class="gov-grid"><div><b>'+esc(l.evidence||"")+'</b>'+esc(it.evidence||"")+'</div>'+
        '<div><b>'+esc(l.uncertainty||"")+'</b>'+esc(it.uncertainty||"")+'</div>'+
        '<div><b>'+esc(l.action||"")+'</b>'+esc(it.required_action||"")+'</div>'+
        '<div><b>'+esc(l.responsible||"")+'</b>'+esc(it.responsible_party||"")+'</div></div></div>';}).join('');
  }

  function filtered(){
    var q=state.q.trim().toLowerCase();
    var arr=C.filter(function(d){
      if(state.section!=="all"&&d.section!==state.section)return false;
      if(state.statuses.size&&!state.statuses.has(d.status))return false;
      if(q){var h=((d.name||"")+" "+(d.article||"")+" "+(SECT[d.section]||"")+" "+(d.description||"")).toLowerCase(); if(h.indexOf(q)===-1)return false;}
      return true;
    });
    var s=state.sort;
    arr.sort(function(a,b){
      if(s==="name")return (a.name||"").localeCompare(b.name||"");
      if(s==="status")return (STATUS_ORDER[a.status]-STATUS_ORDER[b.status])||(a.name||"").localeCompare(b.name||"");
      if(s==="severity")return (SEV[a.severity]-SEV[b.severity])||(a.name||"").localeCompare(b.name||"");
      if(s==="type")return ((a.type==="decisif"?0:1)-(b.type==="decisif"?0:1))||(SECT_IDX[a.section]-SECT_IDX[b.section]);
      return (SECT_IDX[a.section]-SECT_IDX[b.section])||(a.name||"").localeCompare(b.name||"");
    });
    return arr;
  }

  function rowHTML(d){
    var typeCls=d.type==="decisif"?"type-decisif":"type-diagnostic", typeLbl=d.type==="decisif"?UI.decisif:UI.diagnostic;
    var mv=(d.value!=null&&d.value!=="")?'<b>'+esc(d.value)+'</b>'+((d.unit&&d.unit!=="-")?' '+esc(d.unit):'')+'<span style="color:var(--ink-3);padding:0 5px">→</span>':'';
    var measure='<span class="val">'+mv+esc(d.reference||"—")+'</span>';
    var cav=d.caveat?'<div class="caveat"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg><div>'+esc(d.caveat).replace(/\[TO VERIFY\]/g,'<code>[TO VERIFY]</code>')+'</div></div>':'';
    return ''+
    '<div class="crit" data-id="'+esc(d.id)+'">'+
      '<button class="crit-head" type="button" aria-expanded="false">'+
        '<span class="cn"><span class="crit-name">'+esc(d.name)+'</span><span class="crit-sub">'+esc(d.article||"")+'</span></span>'+
        '<span class="cmeta">'+
          '<span class="cell-sect cell-sect-col">'+esc(SECT[d.section]||d.section)+'</span>'+
          '<span class="type-col"><span class="type-tag '+typeCls+'">'+esc(typeLbl)+'</span></span>'+
          '<span class="val-col">'+measure+'</span>'+
          '<span class="cstatus">'+badge(d.status)+'</span>'+
        '</span>'+
        '<svg class="chev" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="m9 6 6 6-6 6"/></svg>'+
      '</button>'+
      '<div class="crit-detail"><div class="detail-grid">'+
        '<div class="dblock"><div class="dk">'+esc(UI.article)+'</div><div class="dv"><span class="article"># '+esc(d.article||"—")+'</span></div></div>'+
        '<div class="dblock"><div class="dk">'+esc(UI.measured_ref)+'</div><div class="dv val">'+measure+'</div></div>'+
        '<div class="dblock"><div class="dk">'+esc(UI.severity)+'</div><div class="dv">'+esc(SEVL[d.severity]||d.severity)+'</div></div>'+
        '<div class="dblock" style="grid-column:1/-1"><div class="dk">'+esc(UI.interpretation)+'</div><div class="dv">'+esc(d.description||"")+'</div></div>'+
        '<div class="dblock"><div class="dk">'+esc(UI.source)+'</div><div class="dv">'+esc(d.source||"—")+'</div></div>'+
        '<div class="dblock"><div class="dk">'+esc(UI.recommendation)+'</div><div class="dv">'+esc(d.recommendation||"—")+'</div></div>'+
      '</div>'+cav+'</div>'+
    '</div>';
  }

  function render(){
    var arr=filtered(), rows=$("rows");
    if(!arr.length){rows.innerHTML='<div class="empty">'+esc(UI.empty)+'</div>';return;}
    var html="",cur=null,group=state.sort==="section";
    arr.forEach(function(d){
      if(group&&d.section!==cur){cur=d.section;var cnt=arr.filter(function(x){return x.section===cur;}).length;
        html+='<div class="sectlabel">'+esc(SECT[cur]||cur)+'<span class="count">'+cnt+'</span></div>';}
      html+=rowHTML(d);
    });
    rows.innerHTML=html;
  }

  function summary(){
    var cnt={conforme:0,non_conforme:0,a_determiner:0,ecart:0,non_verifiable:0};
    C.forEach(function(d){if(cnt[d.status]!=null)cnt[d.status]++;});
    var pct=C.length?Math.round(100*(cnt.conforme+cnt.ecart*0.5+cnt.a_determiner*0.25)/C.length):0;
    var tiles=[["conforme","var(--ok)"],["a_determiner","var(--warn)"],["ecart","var(--info)"],["non_verifiable","var(--unknown)"],["non_conforme","var(--crit)"]];
    var h=tiles.map(function(t){var k=t[0];
      return '<button class="tile'+(state.statuses.has(k)?" active":"")+'" data-status="'+k+'" type="button"><span class="stripe" style="background:'+t[1]+'"></span><div class="n" style="color:'+t[1]+'">'+cnt[k]+'</div><div class="l">'+esc(STL[k])+'</div></button>';
    }).join("");
    h+='<div class="tile meter"><div class="n">'+pct+'<span style="font-size:15px;color:var(--ink-3)">/100</span></div><div class="l">'+esc(UI.precheck)+'</div><div class="meter-track"><div class="meter-fill" style="width:'+pct+'%"></div></div><div class="hint">'+(UI.precheck_hint||"")+'</div></div>';
    $("summary").innerHTML=h;
  }

  function chips(){
    var order=["conforme","non_conforme","a_determiner","ecart","non_verifiable"];
    $("statusChips").innerHTML='<span class="lbl">'+esc(UI.status)+'</span>'+order.map(function(k){
      return '<button class="chip'+(state.statuses.has(k)?" on":"")+'" data-status="'+k+'" type="button"><span class="d" style="width:8px;height:8px;border-radius:50%;background:currentColor;opacity:.55"></span>'+esc(STL[k])+'</button>';
    }).join("");
    var used={}; C.forEach(function(d){used[d.section]=(used[d.section]||0)+1;});
    var sc='<span class="lbl">'+esc(UI.section)+'</span><button class="chip'+(state.section==="all"?" on":"")+'" data-section="all" type="button">'+esc(UI.all)+'</button>';
    SORDER.forEach(function(s){ if(!used[s])return;
      sc+='<button class="chip'+(state.section===s?" on":"")+'" data-section="'+s+'" type="button">'+esc(SECT[s]||s)+' <span class="c">'+used[s]+'</span></button>';
    });
    $("sectionChips").innerHTML=sc;
  }

  function toggleStatus(k){ if(state.statuses.has(k))state.statuses.delete(k); else state.statuses.add(k); chips(); summary(); render(); }

  $("rows").addEventListener("click",function(e){var h=e.target.closest(".crit-head"); if(!h)return; var c=h.parentElement, o=c.classList.toggle("open"); h.setAttribute("aria-expanded",o?"true":"false");});
  $("summary").addEventListener("click",function(e){var t=e.target.closest(".tile[data-status]"); if(t)toggleStatus(t.getAttribute("data-status"));});
  $("statusChips").addEventListener("click",function(e){var c=e.target.closest(".chip[data-status]"); if(c)toggleStatus(c.getAttribute("data-status"));});
  $("sectionChips").addEventListener("click",function(e){var c=e.target.closest(".chip[data-section]"); if(!c)return; state.section=c.getAttribute("data-section"); chips(); render();});
  $("thead").addEventListener("click",function(e){var s=e.target.closest(".sortable"); if(!s)return; state.sort=s.getAttribute("data-sort"); $("sort").value=state.sort; render();});
  $("search").addEventListener("input",function(){state.q=this.value; render();});
  $("sort").addEventListener("change",function(){state.sort=this.value; render();});
  $("reset").addEventListener("click",function(){state={q:"",sort:"section",statuses:new Set(),section:"all"}; $("search").value=""; $("sort").value="section"; chips(); summary(); render();});

  var root=document.documentElement;
  function sysDark(){return window.matchMedia&&window.matchMedia("(prefers-color-scheme:dark)").matches;}
  function curDark(){var t=root.getAttribute("data-theme"); return t?t==="dark":sysDark();}
  function setTheme(d){root.setAttribute("data-theme",d?"dark":"light"); $("themeLbl").textContent=d?UI.dark:UI.light;}
  $("themeBtn").addEventListener("click",function(){setTheme(!curDark());});

  head(); chips(); summary(); render();
  $("themeLbl").textContent=curDark()?UI.dark:UI.light;
})();
</script>
"""
