#!/usr/bin/env python3
"""Рендер дашборда CEO из data/dashboard.json в index.html (self-contained, открывается по file://)."""
import json, os
ROOT = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(ROOT, "data", "dashboard.json")))
def _n(v): return f"{v:,.0f}".replace(",", " ")
def fmt(v):
    if v is None or not round(v): return '<span class="mon" data-r="0">—</span>'
    return f'<span class="mon" data-r="{round(v,2)}">{_n(v)}</span>'
def sign(v):
    if v is None or not round(v): return '<span class="mon" data-r="0">—</span>'
    s = ("−" + _n(abs(v))) if v < 0 else _n(v)
    return f'<span class="mon" data-r="{round(v,2)}">{s}</span>'
def dfmt(s):
    if not s or len(s) < 10: return s or "—"
    return f'{s[8:10]}.{s[5:7]}.{s[0:4]}'
def esc(s): return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
SYM = '<span class="cur-sym">RSD</span>'
BL = data["meta"]["bucketLabels"]
BKEYS = [b["key"] for b in BL]

html = r"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>CEO Дашборд · __COMPANY__</title>
<style>
:root{--teal:#0fb3a6;--teal-d:#0a8a80;--teal-bg:#e8f7f5;--red:#d9534f;--red-bg:#fdecea;--amber:#e8912a;--amber-bg:#fdf1df;--green:#2f9e6b;--bg:#eef1f2;--surface:#fff;--border:#e3e8ea;--text:#1f2a2e;--muted:#5f6a72;}
*{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:var(--bg);color:var(--text);display:flex;min-height:100vh}
.side{width:230px;background:#12343b;color:#cfe3e0;padding:20px 0;position:fixed;height:100vh;display:flex;flex-direction:column;overflow-y:auto}
.side-bal{padding:12px 14px;border-top:1px solid #24474e;margin-top:6px;display:flex;flex-direction:column;gap:8px}
.sb-card{background:#173e46;border:1px solid #24474e;border-radius:10px;padding:9px 12px}
.sb-total-card{background:var(--teal);border-color:var(--teal)}
.sb-tcap{font-size:10px;text-transform:uppercase;letter-spacing:.5px;color:#d6f3ef}
.sb-total{font-size:21px;font-weight:800;color:#fff;margin-top:2px;font-variant-numeric:tabular-nums}
.sb-tsub{font-size:11px;color:#eaf8f5;margin-top:1px}
.sb-cn{font-size:12px;color:#a9ccc7;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sb-cv{font-size:16px;font-weight:700;color:#fff;font-variant-numeric:tabular-nums;margin-top:1px}
.sb-csub{font-size:11.5px;color:#8fbdb6;margin-top:3px}
.sb-edit{display:flex;gap:5px;margin-top:8px}
.sb-edit input{flex:1;min-width:0;font:inherit;font-size:12px;padding:5px 7px;border:1px solid #2c565e;border-radius:6px;background:#0f2d33;color:#fff;text-align:right}
.sb-ok{font:inherit;font-size:12px;font-weight:700;padding:5px 12px;border:0;border-radius:6px;background:var(--teal);color:#fff;cursor:pointer}
.sb-total-card .sb-ok{background:#0f2d33}
.brand{padding:0 22px 18px;border-bottom:1px solid #24474e;margin-bottom:10px}.brand b{font-size:17px;color:#fff}.brand span{font-size:12px;color:#7fb0aa;display:block;margin-top:3px}
.sb-refresh{margin-top:13px;width:100%;font:inherit;font-size:13px;font-weight:600;background:var(--teal);color:#fff;border:0;border-radius:9px;padding:9px 12px;cursor:pointer}
.sb-refresh:hover{background:var(--teal-d)}
.sb-refresh:disabled{opacity:.65;cursor:default}
.nav a{display:flex;gap:10px;align-items:center;padding:11px 22px;color:#cfe3e0;text-decoration:none;font-size:14px;cursor:pointer;border-left:3px solid transparent}
.nav a:hover{background:#173e46}.nav a.on{background:#0f2d33;border-left-color:var(--teal);color:#fff;font-weight:600}
.nav .ic{width:22px;text-align:center;opacity:.85}
.nav a.dragging{opacity:.4;background:#173e46}
.nav a .grip{margin-left:auto;opacity:0;color:#7fb0aa;font-size:13px;letter-spacing:-2px;cursor:grab;transition:opacity .15s}
.nav a:hover .grip{opacity:.7}
.side .foot{margin-top:auto;padding:14px 22px;font-size:11px;color:#6b9a94}
.main{margin-left:230px;flex:1;padding:26px 30px}
.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px}
.top h1{font-size:22px}.top .as{font-size:12px;color:var(--muted)}
.top .upd{text-align:right;font-size:12px;line-height:1.45;color:var(--muted);white-space:nowrap;flex:none}
.top .upd .upd-l{display:block;font-size:11px;letter-spacing:.02em;text-transform:uppercase;opacity:.75}
.top .upd b{color:var(--text);font-weight:700;font-variant-numeric:tabular-nums}
.btn{font:inherit;font-size:13px;font-weight:600;background:var(--teal);color:#fff;border:0;border-radius:9px;padding:9px 16px;cursor:pointer}
.btn:hover{background:var(--teal-d)}.btn.gh{background:#fff;color:var(--teal-d);border:1px solid var(--border)}
.sec{display:none}.sec.on{display:block}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-bottom:22px}
.card{background:var(--surface);border:1px solid var(--border);border-radius:13px;padding:16px 18px}
.card .cap{font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:var(--muted)}
.card .val{font-size:25px;font-weight:700;margin-top:6px}.card .sub{font-size:12px;color:var(--muted);margin-top:3px}
.card.accent{background:var(--teal);color:#fff}.card.accent .cap,.card.accent .sub{color:#d6f3ef}
.pos{color:var(--green)}.neg{color:var(--red)}
.panel{background:var(--surface);border:1px solid var(--border);border-radius:13px;padding:18px 20px;margin-bottom:20px}
.panel h2{font-size:15px;color:var(--teal-d);margin-bottom:14px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:8px 9px;border-bottom:1px solid var(--border);text-align:right}
th:first-child,td:first-child{text-align:left}th{font-size:10px;text-transform:uppercase;color:var(--muted);letter-spacing:.3px;white-space:nowrap}
.num{font-variant-numeric:tabular-nums}.strong{font-weight:700}
tr.tot td{border-top:2px solid var(--teal);font-weight:700;background:var(--teal-bg)}
.rem{display:flex;gap:10px;align-items:flex-start;padding:10px 12px;border-radius:9px;margin-bottom:8px;font-size:13px;border:1px solid var(--border)}
.rem.danger{background:var(--red-bg);border-color:#f3c4c0}.rem.warn{background:var(--amber-bg);border-color:#f3d29a}.rem.info{background:var(--teal-bg);border-color:#bfe7e2}
.rem .dot{width:8px;height:8px;border-radius:50%;margin-top:5px;flex:0 0 auto}.rem.danger .dot{background:var(--red)}.rem.warn .dot{background:var(--amber)}.rem.info .dot{background:var(--teal)}
th.od,td.od{color:var(--red)}td.od{background:var(--red-bg)!important;font-weight:600}th.cw,td.cw{background:var(--teal-bg)}
.ca-row{cursor:pointer}.ca-row:hover td{background:var(--teal-bg)}.ca-row .nm{font-weight:600}
.det-row{display:none}.det-row.open{display:table-row}.det-row>td{padding:0;background:#fafcfc}
table.det,table.rdet{font-size:11.5px}.det th,.rdet th{font-size:9px;padding:6px 12px}.det td,.rdet td{padding:6px 12px;border-bottom:1px solid #eef1f2}
table.rdet{width:100%;border-collapse:collapse}.rdet th{text-align:left;color:var(--muted)}.rdet .num{text-align:right}
.bar{height:9px;background:var(--teal-bg);border-radius:5px;overflow:hidden}.bar>i{display:block;height:100%;background:var(--teal)}
.lead{font-size:12px;color:var(--muted);margin-bottom:12px}#toast{position:fixed;bottom:22px;left:50%;transform:translateX(-50%);background:#12343b;color:#fff;padding:10px 18px;border-radius:10px;font-size:13px;opacity:0;transition:.3s;pointer-events:none}#toast.show{opacity:1}
table.pl td,table.pl th{white-space:nowrap}
table.pl .col-q{display:none}
table.pl.qmode .col-m{display:none}
table.pl.qmode .col-q{display:table-cell}
.pl-res td{font-weight:700;border-top:2px solid var(--teal);background:var(--teal-bg)}
.pl-pct td{color:var(--muted);font-style:italic}.pl-pct td:first-child{padding-left:9px}
.pl-line.clk{cursor:pointer}.pl-line.clk:hover td{background:var(--teal-bg)}.pl-line .nm{font-weight:600}
.arr{display:inline-block;transition:transform .15s;color:var(--teal);font-size:11px}
tr.open>td .arr{transform:rotate(90deg)}
.pl-sub td{background:#fafcfc;font-size:12px}.pl-sub.tnode[onclick]{cursor:pointer}.pl-sub:hover td{background:var(--teal-bg)}
.pl-sub .subnm{color:#4a565b}
.mut{color:var(--muted)}
th.sortable{cursor:pointer;user-select:none;white-space:nowrap}th.sortable:hover{color:var(--teal-d)}
th.sortable[data-dir=asc]::after{content:" ▲";font-size:8px;color:var(--teal)}
th.sortable[data-dir=desc]::after{content:" ▼";font-size:8px;color:var(--teal)}
.segbar{display:flex;align-items:center;gap:8px;margin-bottom:16px}
.seglbl{font-size:12px;color:var(--muted)}
.seg{font:inherit;font-size:13px;font-weight:600;padding:7px 15px;border:1px solid var(--border);background:#fff;color:var(--muted);border-radius:9px;cursor:pointer}
.seg.on{background:var(--amber);color:#fff;border-color:var(--amber)}
/* --- одобрение платежей / реестры --- */
.kred-tabs{display:flex;gap:8px;margin-bottom:16px}
.kred-tab{font:inherit;font-size:13px;font-weight:600;padding:7px 15px;border:1px solid var(--border);background:#fff;color:var(--muted);border-radius:9px;cursor:pointer}
.kred-tab.on{background:var(--teal);color:#fff;border-color:var(--teal)}
.appr-bar{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:14px}
.kred-search{display:flex;align-items:center;gap:10px;margin-bottom:12px}
.kred-search input{font:inherit;font-size:13px;padding:8px 12px;border:1px solid var(--border);border-radius:9px;background:#fff;color:var(--text);width:280px;max-width:100%}
.kred-search input:focus{outline:2px solid var(--teal);outline-offset:1px}
.kred-search-cnt{font-size:12px;color:var(--muted)}
tr.srch-hide{display:none!important}
.appr-hint{font-size:11.5px;color:var(--muted)}
#apprBtn.on{background:#2f9e6b;color:#fff;border-color:#2f9e6b}
.appr-col{display:none}
#sec3.apprmode .appr-col{display:table-cell}
.appr-lbl{display:inline-flex;align-items:center;gap:4px;font-size:11px;white-space:nowrap;cursor:pointer}
.appr-amt{width:96px;font:inherit;font-size:11px;padding:3px 6px;border:1px solid var(--border);border-radius:6px;text-align:right}
#sec3.apprmode tr.det-pay.appr-on td{background:#eafaf1}
.pend-badge{font-size:10.5px;font-weight:600;color:#b26a00;margin-top:2px;line-height:1.3;white-space:nowrap}
.num .pend-badge{text-align:right}
.regcard{border:1px solid var(--border);border-radius:11px;padding:14px 16px;margin-bottom:12px;background:var(--surface)}
.regcard-hd{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}
.reg-sub{font-size:11.5px;color:var(--muted);margin-top:3px}
.regcard-tot{font-size:17px;font-weight:700;white-space:nowrap}
.reg-live{color:#b26a00}.reg-done{color:#2f9e6b}
.reg-toggle{cursor:pointer}
.reg-more{color:var(--teal);font-weight:600}
.reg-det{margin-top:10px;overflow-x:auto}
.reg-archived{font-size:12px;color:var(--muted);align-self:center}
.regcard-actions{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;align-items:center}
.ovmode tr.no-ov,.ovmode tr.no-ov + .det-row{display:none!important}
.ovmode .det tbody tr:not(.ovrow){display:none}
.panel-hd{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:14px}
.salesctl{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.seg-mini{display:inline-flex;border:1px solid var(--border);border-radius:8px;overflow:hidden}
.seg-mini button{font:inherit;font-size:12px;font-weight:600;padding:6px 13px;border:0;background:#fff;color:var(--muted);cursor:pointer}
.seg-mini button.on{background:var(--teal);color:#fff}
.flt{font-size:12px;color:var(--muted);display:inline-flex;align-items:center;gap:5px}
.flt select{font:inherit;font-size:12px;padding:5px 8px;border:1px solid var(--border);border-radius:7px;background:#fff;color:var(--text)}
#planQ{font:inherit;font-size:13px;font-weight:600;padding:6px 10px;border:1px solid var(--border);border-radius:8px;background:#fff;color:var(--text)}
.seg-btn{font:inherit;font-size:12px;font-weight:600;padding:6px 12px;border:1px solid var(--border);background:#fff;color:var(--teal-d);border-radius:8px;cursor:pointer}
.pgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:12px}
.pcell{display:flex;align-items:center;gap:14px;border:1px solid var(--border);border-radius:12px;padding:14px 16px}
.pinfo{flex:1;min-width:0}
.pcap{font-size:13px;font-weight:600;line-height:1.2}
.psub{font-size:11px;color:var(--muted);margin-top:1px}
.prun{font-size:17px;font-weight:800;margin-top:5px;line-height:1.1}
.pright{flex:0 0 auto;text-align:right;padding-left:12px;border-left:1px solid var(--border);align-self:stretch;display:flex;flex-direction:column;justify-content:center}
.prfc{font-size:23px;font-weight:800;line-height:1.05}
.prrem{font-size:14px;font-weight:600;margin-top:4px;opacity:.92}
.planedit{background:var(--teal-bg);border:1px solid #bfe7e2;border-radius:10px;padding:12px 14px;margin-bottom:14px}
.perow{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:8px;font-size:13px}
.perow input{width:160px;font:inherit;font-size:13px;padding:5px 8px;border:1px solid var(--border);border-radius:7px;text-align:right}
.pesave{font:inherit;font-size:13px;font-weight:600;background:var(--teal);color:#fff;border:0;border-radius:8px;padding:7px 18px;cursor:pointer}
.pehint{font-size:11px;color:var(--muted);margin-top:8px}
.rcards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px}
.rc{border:1px solid var(--border);border-left:4px solid var(--amber);border-radius:10px;padding:12px 14px}
.rc.ok{border-left-color:#2f9e6b}.rc.bad{border-left-color:var(--red)}
.rc .rt{font-size:12px;color:var(--muted)}.rc .rbig{font-size:22px;font-weight:800;margin:2px 0}
.rc .rd{font-size:12px;color:var(--text)}
.plpct{font-size:10px;font-weight:600;margin-top:1px}
.sc-amt{font-size:15px;font-weight:700}
.debt-row{cursor:pointer}.debt-row td{background:var(--amber-bg);color:#7a5a1e;font-weight:600;border-top:1px solid #f3d29a}.debt-row:hover td{background:#fbe8cf}.debt-row .nm{color:#b26a00}
#salesTable .debt-col{background:var(--amber-bg);color:#7a5a1e;font-weight:600}
#salesTable th.debt-col{color:#b26a00;font-weight:700;font-size:11px;white-space:normal}
.det tr.prior-line td{background:var(--amber-bg)}
/* --- a11y + читаемость + адаптив (ревью ui-ux-pro-max) --- */
.nav .ic svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round;vertical-align:-4px}
.plpct{font-size:12px}.det th{font-size:10px}.det td{font-size:12px}
table.pj{white-space:nowrap}table.pj td,table.pj th{vertical-align:top}
.pj-group{cursor:pointer}.pj-group:hover td{background:var(--teal-bg)}.pj-group td{font-weight:600}
.pj-proj:hover td{background:var(--teal-bg)}.pj-proj[onclick]{cursor:pointer}.pj-proj td{background:#fafcfc}.pj-proj .nm2{padding-left:22px;font-weight:600}
.pj-pay td{background:#fff;font-size:12px;font-weight:400}.pj-pay .nm3{padding-left:40px;color:#4a565b;white-space:normal}
.pj .dt{font-size:11px;color:var(--muted)}
.stwork{font-size:11px;background:var(--amber-bg);color:#8a6100;padding:2px 8px;border-radius:20px}
.tag-d{font-size:10px;background:var(--teal-bg);color:var(--teal-d);padding:1px 6px;border-radius:8px;font-weight:600}
.tag-k{font-size:10px;background:var(--amber-bg);color:#b26a00;padding:1px 6px;border-radius:8px;font-weight:600}
.stdone{font-size:11px;background:var(--teal-bg);color:var(--teal-d);padding:2px 8px;border-radius:20px}
table.pj.fmode-work .pj-proj[data-status="done"]{display:none!important}
table.pj.fmode-done .pj-proj[data-status="work"]{display:none!important}
table.pj.pmode-unpaid .pj-pay[data-paid="1"]{display:none!important}
#salesTable{table-layout:fixed;--sc1:260px}
#salesTable th:first-child,#salesTable td:first-child{width:var(--sc1);max-width:var(--sc1);overflow:hidden;text-overflow:ellipsis}
#salesTable th:not(:last-child),#salesTable td:not(:last-child){border-right:1px solid #e3e8ea}
#salesTable th:first-child,#salesTable td:first-child{border-right:2px solid var(--teal)}
#salesTable th.sc1h{position:relative}
#salesTable .col-resizer{position:absolute;top:0;right:-6px;width:12px;height:100%;cursor:col-resize;z-index:3}
#salesTable .col-resizer:hover{background:rgba(15,179,166,.18)}
.tag-ok{font-size:10px;background:#e7f4ec;color:#2f7d54;padding:1px 6px;border-radius:8px;font-weight:600}
.note-memo{font-size:12px;background:var(--teal-bg);border:1px solid #bfe7e2;border-radius:8px;padding:9px 13px;margin-bottom:12px;color:#2a4d49}
.bankedit{display:flex;gap:6px;margin-top:10px}
.card .bankfact{flex:1;min-width:0;font:inherit;font-size:12px;padding:5px 8px;border:1px solid var(--border);border-radius:7px;text-align:right;background:#fff;color:var(--text)}
.bankedit .seg-btn{padding:5px 14px}
.bankdelta{font-size:11px;font-weight:600}
.card .cap,.psub,.prsub,.dsub,.pehint,.flt,.seglbl,.rc .rt,.rc .rd{font-size:12px}
:focus-visible{outline:2px solid var(--teal);outline-offset:2px;border-radius:5px}
.side a:focus-visible{outline-color:#7fe3da;outline-offset:-2px}
.ca-row,.debt-row,.pl-line.clk,.pl-sub.tnode[onclick],th.sortable,.nav a{outline:none}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
@media (max-width:900px){
 body{flex-direction:column}
 .side{position:static;width:100%;height:auto;padding:8px 0}
 .brand{padding:8px 18px 10px;margin-bottom:4px}
 .nav{display:flex;flex-wrap:wrap;gap:2px}
 .nav a{border-left:0;border-bottom:3px solid transparent;padding:9px 14px}
 .nav a.on{border-left:0;border-bottom-color:var(--teal)}
 .cur-toggle{margin-top:0;max-width:220px}.side .foot{padding:8px 18px}
 .main{margin-left:0;padding:16px 14px}
 .panel{overflow-x:auto}
 table.pl,table.reg{min-width:620px}
 .cards{grid-template-columns:1fr 1fr}
 .pgrid{grid-template-columns:1fr}
 .panel-hd{align-items:flex-start}
}
@media (max-width:560px){.cards{grid-template-columns:1fr}.top{flex-wrap:wrap;gap:10px}.top .upd{text-align:left}}
.cur-toggle{margin-top:auto;padding:12px 18px;display:flex;gap:8px}
.curbtn{flex:1;font:inherit;font-size:12px;font-weight:700;padding:7px 0;border:1px solid #2c565e;background:transparent;color:#9fc2bd;border-radius:8px;cursor:pointer}
.curbtn.on{background:var(--teal);color:#fff;border-color:var(--teal)}
.side .foot{margin-top:0!important}
</style></head><body>
<nav class="side"><div class="brand"><b>CEO Дашборд</b><span>__COMPANY__</span>
<button class="sb-refresh" id="refreshBtn" onclick="refresh()">⟳ Обновить</button></div>
<div class="nav" role="tablist" aria-label="Разделы дашборда">
<a data-s="0" class="on" role="tab" tabindex="0" draggable="true"><span class="ic" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="9"/><rect x="14" y="3" width="7" height="5"/><rect x="14" y="12" width="7" height="9"/><rect x="3" y="16" width="7" height="5"/></svg></span>Главный</a>
<a data-s="1" role="tab" tabindex="0" draggable="true"><span class="ic" aria-hidden="true"><svg viewBox="0 0 24 24"><line x1="6" y1="20" x2="6" y2="15"/><line x1="12" y1="20" x2="12" y2="9"/><line x1="18" y1="20" x2="18" y2="4"/></svg></span>P&amp;L маржинальный</a>
<a data-s="3" role="tab" tabindex="0" draggable="true"><span class="ic" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M16 12l-4-4-4 4"/><path d="M12 16V8"/></svg></span>Кредиторка</a>
<a data-s="4" role="tab" tabindex="0" draggable="true"><span class="ic" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M3 12h4l3 8 4-16 3 8h4"/></svg></span>ДДС</a>
<a data-s="5" role="tab" tabindex="0" draggable="true"><span class="ic" aria-hidden="true"><svg viewBox="0 0 24 24"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></span>Проекты</a>
</div>
__SIDEBAL__
<div class="cur-toggle"><button class="curbtn on" data-c="RSD" onclick="setCurrency('RSD',this)">RSD</button><button class="curbtn" data-c="EUR" onclick="setCurrency('EUR',this)">EUR</button></div>
</nav>
<div class="main">
<div class="top"><div><h1 id="ttl">Главный дашборд</h1><div class="as">__COMPANY__ · показатели на __ASOF__</div></div><div class="upd" title="Дата и время последней сборки данных"><span class="upd-l">Обновлено</span><b>__GEN__</b></div></div>
__SECTIONS__
</div><div id="toast" role="status" aria-live="polite"></div>
<script>
var DATA=__DATA__;
// нормализуем сид-план (переименование статей); сохранённый общий план подмешивается позже в applySettings
try{if(DATA.salesplan){var _rm=DATA.salesplan.rename||{};Object.keys(DATA.salesplan.plans).forEach(function(q){var mp=DATA.salesplan.plans[q],nm={};Object.keys(mp).forEach(function(k){nm[_rm[k]||k]=mp[k];});DATA.salesplan.plans[q]=nm;});}}catch(e){}
var salesGran='month';var salesBasis='accrual';
function setBasis(b,btn){salesBasis=b;var p=btn.parentNode;p.querySelectorAll('button').forEach(function(x){x.classList.remove('on');});btn.classList.add('on');renderSales();if(document.getElementById('planQ'))renderPlan();}
function mBounds(m){var y=+m.slice(0,4),mo=+m.slice(5,7);return [Date.UTC(y,mo-1,1),Date.UTC(y,mo,1)];}
function pColor(p){return p>=100?'#2f9e6b':p>=85?'#0fb3a6':p>=60?'#e8912a':'#d9534f';}
function planCard(name,act,pl,pct,fpct,rem,perWeek,ended){var pos,fcMain,fcSub,runTxt;
 if(!pl){pos=null;fcMain='—';fcSub='план не задан';runTxt='—';}
 else if(ended){pos=rem<=0;fcMain=pos?'✓ выполнен':'✗ не выполнен';fcSub=pos?('план '+Math.round(pct)+'%'):('недобор '+fmtN(rem));runTxt=fmtN(act);}
 else{pos=fpct>=100;fcMain='прогноз '+Math.round(fpct)+'%';fcSub=rem<=0?'план достигнут':('осталось '+fmtN(rem));runTxt=rem<=0?'✓':fmtN(perWeek)+'/нед';}
 var rcol=pos===null?'#8a969b':(pos?'#2f9e6b':'#d9534f'),dash=Math.min(Math.max(pct,0),100)/100*175.9;
 return '<div class="pcell"><svg role="img" aria-label="'+name+': '+(pl?Math.round(pct)+'% плана, '+fcMain:'план не задан')+'" viewBox="0 0 72 72" width="62" height="62" style="flex:0 0 auto"><circle cx="36" cy="36" r="28" fill="none" stroke="#eef1f2" stroke-width="7"/><circle cx="36" cy="36" r="28" fill="none" stroke="'+rcol+'" stroke-width="7" stroke-linecap="round" stroke-dasharray="'+dash+' 175.9" transform="rotate(-90 36 36)"/><text x="36" y="41" text-anchor="middle" font-size="14" font-weight="700" fill="#1f2a2e">'+(pl?Math.round(pct)+'%':'—')+'</text></svg>'
 +'<div class="pinfo"><div class="pcap">'+name+'</div><div class="psub">'+fmtN(act)+' / '+fmtN(pl)+'</div><div class="prun" style="color:'+rcol+'">'+runTxt+'</div></div>'
 +'<div class="pright" style="color:'+rcol+'"><div class="prfc">'+fcMain+'</div><div class="prrem">'+fcSub+'</div></div></div>';}
function renderPlan(){var SP=DATA.salesplan;if(!SP)return;var m0=document.getElementById('planQ').value;
 var plan=SP.plans[m0]||{},cats=DATA.sales[salesBasis],b=mBounds(m0),qs=b[0],qe=b[1],today=Date.parse(DATA.meta.asOf+'T00:00:00Z');
 var totalDays=Math.round((qe-qs)/864e5),elapsed=Math.max(0,Math.min(totalDays,Math.round((today-qs)/864e5)+1)),remDays=Math.max(0,totalDays-elapsed),remWeeks=remDays/7,ended=m0<SP.current;
 var excl={};(SP.exclude||[]).forEach(function(n){excl[n]=1;});
 var names={};cats.forEach(function(c){if(!excl[c.name])names[c.name]=1;});Object.keys(plan).forEach(function(n){if(!excl[n])names[n]=1;});
 var g='';Object.keys(names).forEach(function(name){var c=cats.filter(function(x){return x.name===name;})[0];
  var act=c?(c.m[m0]||0):0,pl=plan[name]||0,pct=pl?act/pl*100:0,fc=elapsed?act/elapsed*totalDays:0,fpct=pl?fc/pl*100:0,rem=Math.max(0,pl-act),perWeek=remWeeks>0?rem/remWeeks:rem;
  g+=planCard(name,act,pl,pct,fpct,rem,perWeek,ended);});
 document.getElementById('planGrid').innerHTML=g;
 var bl=(salesBasis==='accrual'?'по договорам':'касса');
 document.getElementById('planMeta').textContent=ended?('Месяц завершён · базис: '+bl):('День '+elapsed+' из '+totalDays+' · осталось '+remDays+' дн ('+(Math.round(remWeeks*10)/10)+' нед) · базис: '+bl);}
function togglePlanEdit(){var e=document.getElementById('planEdit');if(e.style.display!=='none'){e.style.display='none';return;}
 var q=document.getElementById('planQ').value,plan=DATA.salesplan.plans[q]||{},names={},excl={};(DATA.salesplan.exclude||[]).forEach(function(n){excl[n]=1;});DATA.sales.accrual.forEach(function(c){if(!excl[c.name])names[c.name]=1;});Object.keys(plan).forEach(function(n){if(!excl[n])names[n]=1;});
 var h='<div style="font-weight:600;margin-bottom:8px">План на '+q+' (RSD):</div>';Object.keys(names).forEach(function(n){h+='<div class="perow"><span>'+n+'</span><input type="number" data-cat="'+n.replace(/"/g,'')+'" value="'+(plan[n]||0)+'"></div>';});
 h+='<button class="pesave" onclick="savePlan()">Сохранить</button><div class="pehint">Сохраняется на сервере — виден всем, кто заходит.</div>';
 e.innerHTML=h;e.style.display='';}
function savePlan(){var q=document.getElementById('planQ').value,obj={};document.querySelectorAll('#planEdit input').forEach(function(i){obj[i.dataset.cat]=+i.value||0;});
 DATA.salesplan.plans[q]=obj;setPut('plans',DATA.salesplan.plans);
 renderPlan();renderSales();
 document.getElementById('planEdit').innerHTML='<div style="font-weight:600;margin-bottom:6px;color:#2f9e6b">✓ План сохранён'+(SET_BACKEND==='server'?' (виден всем)':' (локально)')+'</div><div style="margin-top:4px"><button class="seg-btn" onclick="document.getElementById(\'planEdit\').style.display=\'none\'">Закрыть</button></div>';
 toast('План сохранён');}
// ОБЩИЕ настройки (Supabase через /api/settings): банк-факт, план, валюта, порядок меню, ширина колонки.
// Видны всем под одним логином. Откат на localStorage, если сервер недоступен (file://).
var SETTINGS={},BANKFACT={},SET_BACKEND='local';
var _LSKEYS={bankfact:'planfact_bankfact',plans:'planfact_plans',cur:'planfact_cur',navorder:'planfact_navorder',sc1:'planfact_sc1'};
var _RAW={cur:1,sc1:1};   // эти значения — простые строки, не JSON
function loadSettings(cb){
 fetch('/api/settings',{headers:{'Accept':'application/json'}}).then(function(r){if(!r.ok)throw 0;return r.json();})
  .then(function(s){SET_BACKEND='server';SETTINGS=s||{};
   // разовая миграция: если на сервере ещё нет плана, а в этом браузере он был — поднимаем на сервер
   if(SETTINGS.plans==null){try{var _lp=localStorage.getItem('planfact_plans');if(_lp){SETTINGS.plans=JSON.parse(_lp);setPut('plans',SETTINGS.plans);}}catch(e){}}
   BANKFACT=SETTINGS.bankfact||{};if(cb)cb();})
  .catch(function(){SET_BACKEND='local';SETTINGS={};Object.keys(_LSKEYS).forEach(function(k){try{var v=localStorage.getItem(_LSKEYS[k]);if(v!=null)SETTINGS[k]=_RAW[k]?v:JSON.parse(v);}catch(e){}});BANKFACT=SETTINGS.bankfact||{};if(cb)cb();});}
function setPut(key,val){SETTINGS[key]=val;
 try{var lk=_LSKEYS[key];if(lk){if(val==null)localStorage.removeItem(lk);else localStorage.setItem(lk,_RAW[key]?val:JSON.stringify(val));}}catch(e){}
 if(SET_BACKEND==='server')return fetch('/api/settings/'+encodeURIComponent(key),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(val)}).then(function(r){if(!r.ok)throw 0;});
 return Promise.resolve();}
function saveBankFact(){var inp=document.querySelector('.bankfact');if(!inp)return;var v=(inp.value===''?null:+inp.value);
 BANKFACT[inp.dataset.acc]=v;
 setPut('bankfact',BANKFACT).then(function(){toast(v==null?'Факт очищен — показан ПланФакт':'Факт по банку сохранён (виден всем)');})
  .catch(function(){toast('Не удалось сохранить факт на сервере');});
 applyBankFact();}
function applyBankFact(){var inp=document.querySelector('.bankfact'),num=document.getElementById('bankMainNum'),el=document.getElementById('bankDelta');if(!inp||!num)return;
 var pf=+inp.dataset.pf||0,stored=BANKFACT[inp.dataset.acc];if(stored===undefined)stored=null;
 var main=(stored!=null?+stored:pf);num.setAttribute('data-r',main);
 var tot=document.getElementById('bankTotalNum');if(tot){var base=+tot.getAttribute('data-base')||0;tot.setAttribute('data-r',base-pf+main);}
 var dtot=document.getElementById('ddsBalNum');if(dtot){var db=+dtot.getAttribute('data-base')||0;dtot.setAttribute('data-r',db-pf+main);}
 if(stored!=null){var d=stored-pf;el.textContent=' · Δ к ПФ '+(d<0?'−':'+')+Math.abs(Math.round(d)).toLocaleString('ru-RU').replace(/,/g,' ');el.style.color=Math.round(d)===0?'var(--muted)':(d>0?'#2f9e6b':'#d9534f');}else{el.textContent='';}
 applyCurrency();}
// применение всех общих настроек после загрузки с сервера + перерисовка
function applySettings(){
 if(SETTINGS.cur)applyCurUI(SETTINGS.cur);
 if(SETTINGS.plans){var RM=(DATA.salesplan&&DATA.salesplan.rename)||{};Object.keys(SETTINGS.plans).forEach(function(q){var mp=SETTINGS.plans[q]||{},nm={};Object.keys(mp).forEach(function(k){nm[RM[k]||k]=mp[k];});DATA.salesplan.plans[q]=nm;});}
 if(SETTINGS.sc1){var t=document.getElementById('salesTable');if(t)t.style.setProperty('--sc1',SETTINGS.sc1);}
 loadNavOrder();
 var inp=document.querySelector('.bankfact');if(inp){var s=BANKFACT[inp.dataset.acc];if(s!=null)inp.value=s;else inp.value='';}
 if(document.getElementById('salesFrom'))renderSales();
 if(document.getElementById('planQ'))renderPlan();
 applyBankFact();}
function ruM(m){var M=['янв','фев','мар','апр','май','июн','июл','авг','сен','окт','ноя','дек'];return M[+m.slice(5,7)-1]+" '"+m.slice(2,4);}
var CUR='RSD',RATE=117;function conv(v){return CUR==='EUR'?v/RATE:v;}
function fmtN(v){var x=Math.round(conv(v));return x?x.toLocaleString('ru-RU').replace(/,/g,' '):'—';}
function startColResize(e){e.preventDefault();var tbl=document.getElementById('salesTable');if(!tbl)return;
 var startX=e.clientX,startW=parseInt(getComputedStyle(tbl).getPropertyValue('--sc1'))||260;
 function mm(ev){var w=Math.max(120,Math.min(660,startW+(ev.clientX-startX)));tbl.style.setProperty('--sc1',w+'px');}
 function mu(){document.removeEventListener('mousemove',mm);document.removeEventListener('mouseup',mu);document.body.style.userSelect='';setPut('sc1',tbl.style.getPropertyValue('--sc1'));}
 document.body.style.userSelect='none';document.addEventListener('mousemove',mm);document.addEventListener('mouseup',mu);}
function resetCol(){var t=document.getElementById('salesTable');if(t){t.style.setProperty('--sc1','260px');}setPut('sc1',null);}
function applyCurrency(){
 document.querySelectorAll('.mon').forEach(function(el){var r=parseFloat(el.getAttribute('data-r'))||0,x=conv(r);if(!Math.round(x)){el.textContent='—';return;}var neg=x<0;x=Math.round(Math.abs(x));el.textContent=(neg?'−':'')+x.toLocaleString('ru-RU').replace(/,/g,' ');});
 document.querySelectorAll('.cur-sym').forEach(function(el){el.textContent=CUR;});
 document.querySelectorAll('.cur-code').forEach(function(el){el.textContent=CUR;});}
function applyCurUI(c){CUR=c;document.querySelectorAll('.curbtn').forEach(function(b){var on=b.getAttribute('data-c')===c;b.classList.toggle('on',on);b.setAttribute('aria-pressed',on);});}
function setCurrency(c,btn){applyCurUI(c);setPut('cur',c);
 applyCurrency();if(document.getElementById('salesFrom'))renderSales();if(document.getElementById('planQ'))renderPlan();}
function setGran(g,btn){salesGran=g;var p=btn.parentNode;p.querySelectorAll('button').forEach(function(b){b.classList.remove('on');});btn.classList.add('on');renderSales();}
function plGran(g,btn){var t=document.querySelector('#sec1 table.pl');if(t)t.classList.toggle('qmode',g==='quarter');
 var p=btn.parentNode;p.querySelectorAll('button').forEach(function(b){b.classList.remove('on');b.setAttribute('aria-pressed','false');});btn.classList.add('on');btn.setAttribute('aria-pressed','true');}
function renderSales(){var S=DATA.sales;if(!S)return;var cats=S[salesBasis]||[];
 var from=document.getElementById('salesFrom').value,to=document.getElementById('salesTo').value;
 var months=S.months.filter(function(m){return m>=from&&m<=to;});
 // долг за прошлый период = неоплаченная дебиторка по продажам ДО начала выбранного периода (вкл. до апреля)
 var priorLines=(S.debtLines||[]).filter(function(l){return l.m<from;}),priorByCat={},priorTotal=0;
 priorLines.forEach(function(l){priorByCat[l.cat]=(priorByCat[l.cat]||0)+l.val;priorTotal+=l.val;});
 var dcolH='<th class="num debt-col" title="Дебиторка: заказчик должен по продажам ДО '+ruM(from)+' (не входит в выбранный период). Всегда видна.">Долг до '+ruM(from)+'</th>';
 var periods=[];
 if(salesGran==='month'){periods=months.map(function(m){return {label:ruM(m),months:[m]};});}
 else{var order=[],q={};months.forEach(function(m){var y=m.slice(0,4),qq=Math.ceil((+m.slice(5,7))/3),key=y+'Q'+qq;if(!q[key]){q[key]={label:'Q'+qq+" '"+y.slice(2),months:[]};order.push(key);}q[key].months.push(m);});periods=order.map(function(k){return q[k];});}
 var head='<thead><tr><th class="sc1h">Статья продаж<span class="col-resizer" onmousedown="startColResize(event)" ondblclick="resetCol()" title="Потяните, чтобы изменить ширину · двойной клик — сброс"></span></th>'+dcolH+periods.map(function(p){return '<th class="num">'+p.label+'</th>';}).join('')+'<th class="num">Итого</th></tr></thead>';
 var tots=periods.map(function(){return 0;}),gt=0;
 var rows=cats.map(function(c){var vals=periods.map(function(p){return p.months.reduce(function(s,m){return s+(c.m[m]||0);},0);});return {name:c.name,vals:vals,tot:vals.reduce(function(s,v){return s+v;},0)};}).filter(function(r){return Math.round(r.tot)!==0;}).sort(function(a,b){return b.tot-a.tot;});
 var SP=DATA.salesplan||{},plans=SP.plans||{},cur=SP.current||'9999',pexcl={};(SP.exclude||[]).forEach(function(n){pexcl[n]=1;});
 var body='';rows.forEach(function(r){body+='<tr class="pl-line"><td class="nm">'+r.name+'</td><td class="num debt-col">'+fmtN(priorByCat[r.name]||0)+'</td>'+r.vals.map(function(v,i){tots[i]+=v;var cell=fmtN(v),pctHtml='';
   if(!pexcl[r.name]){var pm=periods[i],planSum=pm.months.reduce(function(s,m){return s+((plans[m]||{})[r.name]||0);},0),pastP=pm.months.every(function(m){return m<cur;});
    if(planSum>0&&pastP){var pc=v/planSum*100,col=pc>=100?'#2f9e6b':pc>=90?'#e8912a':'#d9534f';pctHtml='<div class="plpct" style="color:'+col+'">'+Math.round(pc)+'% плана</div>';}}
   if(pctHtml)cell='<span class="sc-amt">'+fmtN(v)+'</span>'+pctHtml;
   return '<td class="num">'+cell+'</td>';}).join('')+'<td class="num strong">'+fmtN(r.tot)+'</td></tr>';gt+=r.tot;});
 var tr='<tr class="pl-res"><td>Итого продажи</td><td class="num debt-col">'+fmtN(priorTotal)+'</td>'+tots.map(function(v){return '<td class="num">'+fmtN(v)+'</td>';}).join('')+'<td class="num">'+fmtN(gt)+'</td></tr>';
 // строка «Заказчик должен Доплату» = продано − получено, раскрывается в неоплаченные платежи
 var accC=DATA.sales.accrual,cashC=DATA.sales.cash;
 function psum(arr,pm){return arr.reduce(function(s,c){return s+pm.months.reduce(function(t,m){return t+(c.m[m]||0);},0);},0);}
 var dvals=periods.map(function(pm){return psum(accC,pm)-psum(cashC,pm);}),dtot=dvals.reduce(function(s,v){return s+v;},0);
 var dcells=dvals.map(function(v){return '<td class="num">'+fmtN(v)+'</td>';}).join('');
 // детализация: вся неоплаченная дебиторка вплоть до конца периода (прошлый период + текущий), прошлые помечены
 var dl=(DATA.sales.debtLines||[]).filter(function(l){return l.m<=to;}).slice().sort(function(a,b){return a.m<b.m?-1:(a.m>b.m?1:b.val-a.val);}),ddet='';
 dl.forEach(function(l){var pr=l.m<from;ddet+='<tr'+(pr?' class="prior-line"':'')+'><td>'+ruM(l.m)+(pr?' · пред.':'')+'</td><td>'+(l.project||l.ca)+'</td><td>'+(l.cmt||'—')+'</td><td class="num strong">'+fmtN(l.val)+'</td></tr>';});
 if(!ddet)ddet='<tr><td colspan="4" style="color:var(--muted)">нет неоплаченной дебиторки</td></tr>';
 var debtRow='<tr class="debt-row" onclick="toggle(this)"><td class="nm">▸ Заказчик должен Доплату</td><td class="num debt-col strong">'+fmtN(priorTotal)+'</td>'+dcells+'<td class="num strong">'+fmtN(dtot)+'</td></tr>'
  +'<tr class="det-row"><td colspan="'+(periods.length+3)+'"><table class="det"><thead><tr><th>Продан</th><th>Проект / заказчик</th><th>Описание</th><th class="num">Сумма</th></tr></thead><tbody>'+ddet+'</tbody></table></td></tr>';
 document.getElementById('salesTable').innerHTML=head+'<tbody>'+tr+body+debtRow+'</tbody>';wireKbd(document.getElementById('salesTable'));}
(function(){var s1=document.getElementById('salesFrom'),s2=document.getElementById('salesTo');if(!s1||!DATA.sales)return;
 var ms=DATA.sales.months,opts=ms.map(function(m){return '<option value="'+m+'">'+ruM(m)+'</option>';}).join('');
 s1.innerHTML=opts;s2.innerHTML=opts;s1.value=ms[0];s2.value=ms[ms.length-1];renderSales();})();
(function(){var ps=document.getElementById('planQ');if(!ps||!DATA.salesplan)return;
 var RM=DATA.salesplan.rename||{};Object.keys(DATA.salesplan.plans).forEach(function(q){var mp=DATA.salesplan.plans[q],nm={};Object.keys(mp).forEach(function(k){nm[RM[k]||k]=mp[k];});DATA.salesplan.plans[q]=nm;});
 ps.innerHTML=DATA.salesplan.months.map(function(m){return '<option value="'+m+'">'+ruM(m)+'</option>';}).join('');
 ps.value=DATA.salesplan.current;renderPlan();})();
wireKbd();
(function(){document.querySelectorAll('.seg-mini,.cur-toggle,.segbar').forEach(function(g){g.setAttribute('role','group');});
 document.querySelectorAll('.seg-mini button,.curbtn,.seg').forEach(function(x){x.setAttribute('aria-pressed',x.classList.contains('on'));});})();
// --- перетаскивание пунктов меню (drag & drop) с сохранением порядка ---
function navGripInject(){document.querySelectorAll('.nav a').forEach(function(a){if(!a.querySelector('.grip'))a.insertAdjacentHTML('beforeend','<span class="grip" aria-hidden="true">⠿</span>');});}
function saveNavOrder(){setPut('navorder',[].map.call(document.querySelectorAll('.nav a'),function(a){return a.getAttribute('data-s');}));}
function loadNavOrder(){try{var o=SETTINGS.navorder;if(!o||!o.length)return;var nav=document.querySelector('.nav');o.forEach(function(s){var a=nav.querySelector('a[data-s="'+s+'"]');if(a)nav.appendChild(a);});}catch(e){}}
function navAfter(nav,y){var best={o:-Infinity,el:null};[].slice.call(nav.querySelectorAll('a:not(.dragging)')).forEach(function(c){var b=c.getBoundingClientRect(),off=y-b.top-b.height/2;if(off<0&&off>best.o)best={o:off,el:c};});return best.el;}
function initNavDrag(){var nav=document.querySelector('.nav'),drag=null;
 nav.querySelectorAll('a').forEach(function(a){
  a.addEventListener('dragstart',function(e){drag=a;a.classList.add('dragging');e.dataTransfer.effectAllowed='move';});
  a.addEventListener('dragend',function(){a.classList.remove('dragging');drag=null;saveNavOrder();});});
 nav.addEventListener('dragover',function(e){e.preventDefault();if(!drag)return;var after=navAfter(nav,e.clientY);if(after==null)nav.appendChild(drag);else nav.insertBefore(drag,after);});}
navGripInject();initNavDrag();
function filterProjects(mode,btn){var sec=document.getElementById('sec5');if(!sec)return;
 var tbl=sec.querySelector('table.pj');tbl.classList.remove('fmode-work','fmode-done');
 if(mode==='work')tbl.classList.add('fmode-work');else if(mode==='done')tbl.classList.add('fmode-done');
 // по умолчанию всё свёрнуто: скрываем проекты и платежи, сбрасываем стрелки
 sec.querySelectorAll('tr.pj-proj,tr.pj-pay').forEach(function(r){r.style.display='none';});
 sec.querySelectorAll('#sec5 tr[data-id]').forEach(function(r){r.classList.remove('open');});
 sec.querySelectorAll('tr.pj-group').forEach(function(gr){
   var m=mode==='work'?+gr.getAttribute('data-gw'):mode==='done'?+gr.getAttribute('data-gd'):1;gr.style.display=m>0?'':'none';});
 recalcProj(mode);
 if(btn){var p=btn.parentNode;p.querySelectorAll('button').forEach(function(b){b.classList.remove('on');});btn.classList.add('on');}}
function payMode(mode,btn){var sec=document.getElementById('sec5');if(!sec)return;var tbl=sec.querySelector('table.pj');
 if(mode==='unpaid')tbl.classList.add('pmode-unpaid');else tbl.classList.remove('pmode-unpaid');
 if(btn){var p=btn.parentNode;p.querySelectorAll('button').forEach(function(b){b.classList.remove('on');});btn.classList.add('on');}}
function setMonR(td,val){var m=td&&td.querySelector('.mon');if(m)m.setAttribute('data-r',val);}
function rentTxt(i,p){return i?((Math.round(p/i*1000)/10).toFixed(1).replace('.',',')+'%'):'—';}
function recalcProj(mode){var sec=document.getElementById('sec5');if(!sec)return;var GI=0,GO=0;
 sec.querySelectorAll('tr.pj-group').forEach(function(gr){var gid=gr.getAttribute('data-id'),gi=0,go=0;
  sec.querySelectorAll('tr.pj-proj[data-parent="'+gid+'"]').forEach(function(pr){
   if(mode!=='all'&&pr.getAttribute('data-status')!==mode)return;
   var mi=pr.children[3].querySelector('.mon'),mo=pr.children[4].querySelector('.mon');
   gi+=mi?+mi.getAttribute('data-r'):0;go+=mo?+mo.getAttribute('data-r'):0;});
  var gc=gr.children;setMonR(gc[3],gi);setMonR(gc[4],go);setMonR(gc[5],gi-go);
  gc[5].classList.toggle('neg',gi-go<0);gc[5].classList.toggle('pos',gi-go>=0);
  gc[6].textContent=rentTxt(gi,gi-go);GI+=gi;GO+=go;});
 var tot=sec.querySelector('tr.tot');if(tot){var tc=tot.children;setMonR(tc[3],GI);setMonR(tc[4],GO);setMonR(tc[5],GI-GO);tc[6].textContent=rentTxt(GI,GI-GO);}
 applyCurrency();}
(function(){var b=document.querySelector('#sec5 .seg-mini button');if(b)filterProjects('all',b);})();
document.querySelectorAll('.nav a').forEach(function(a){a.onclick=function(){
 document.querySelectorAll('.nav a').forEach(x=>x.classList.remove('on'));a.classList.add('on');
 var s=a.getAttribute('data-s');document.querySelectorAll('.sec').forEach(x=>x.classList.remove('on'));
 document.getElementById('sec'+s).classList.add('on');
 document.getElementById('ttl').textContent=a.textContent.trim();};});
function toggle(el){var o=el.nextElementSibling.classList.toggle('open');el.setAttribute('aria-expanded',o);}
function grp(row){var o=row.classList.toggle('open');row.setAttribute('aria-expanded',o);document.querySelectorAll('tr.'+row.dataset.g).forEach(function(r){r.classList.toggle('show');});}
function setKids(id,show){document.querySelectorAll('tr[data-parent="'+id+'"]').forEach(function(c){c.style.display=show?'table-row':'none';if(!show){c.classList.remove('open');c.setAttribute('aria-expanded','false');setKids(c.dataset.id,false);}});}
function tnode(row){var o=row.classList.toggle('open');row.setAttribute('aria-expanded',o);setKids(row.dataset.id,o);}
function wireKbd(root){(root||document).querySelectorAll('tr[onclick],th.sortable').forEach(function(el){if(!el.hasAttribute('tabindex')){el.setAttribute('tabindex','0');el.setAttribute('role','button');if(el.tagName==='TR')el.setAttribute('aria-expanded','false');}});}
document.addEventListener('keydown',function(e){var el=document.activeElement;
 if((e.key==='Enter'||e.key===' ')&&el&&el.matches&&el.matches('tr[onclick],th.sortable,.nav a')){e.preventDefault();el.click();return;}
 if(e.altKey&&(e.key==='ArrowUp'||e.key==='ArrowDown')&&el&&el.matches&&el.matches('.nav a')){e.preventDefault();var sib=e.key==='ArrowUp'?el.previousElementSibling:el.nextElementSibling;if(sib&&sib.matches('.nav a')){if(e.key==='ArrowUp')el.parentNode.insertBefore(el,sib);else el.parentNode.insertBefore(sib,el);el.focus();if(typeof saveNavOrder==='function')saveNavOrder();}}});
// синхронизация aria-pressed на сегментных переключателях после клика
document.addEventListener('click',function(e){var b=e.target.closest&&e.target.closest('.seg-mini button,.curbtn,.seg,.tab');if(!b)return;setTimeout(function(){document.querySelectorAll('.seg-mini button,.curbtn,.seg,.tab').forEach(function(x){x.setAttribute('aria-pressed',x.classList.contains('on'));});},0);});
function pnum(s){s=(s||'').replace(/[\s ₣]/g,'').replace('—','').replace('−','-');var n=parseFloat(s);return isNaN(n)?0:n;}
function sortReg(th){var table=th.closest('table'),idx=th.cellIndex,type=th.dataset.t,tb=table.tBodies[0];
 var dir=th.getAttribute('data-dir')==='asc'?'desc':'asc';
 table.querySelectorAll('th').forEach(function(h){h.removeAttribute('data-dir');h.setAttribute('aria-sort','none');});th.setAttribute('data-dir',dir);th.setAttribute('aria-sort',dir==='asc'?'ascending':'descending');
 var pairs=Array.prototype.slice.call(tb.querySelectorAll('tr.ca-row')).map(function(r){return [r,r.nextElementSibling];});
 function cellNum(td){var m=td.querySelector('.mon');return m?(parseFloat(m.getAttribute('data-r'))||0):pnum(td.textContent);}
 pairs.sort(function(a,b){var ca=a[0].children[idx],cb=b[0].children[idx];
  if(type==='num'){var d=cellNum(ca)-cellNum(cb);return dir==='asc'?d:-d;}
  var x=ca.textContent.trim().replace(/^▸\s*/,'').toLowerCase(),y=cb.textContent.trim().replace(/^▸\s*/,'').toLowerCase();
  return dir==='asc'?x.localeCompare(y,'ru'):y.localeCompare(x,'ru');});
 pairs.forEach(function(p){tb.appendChild(p[0]);if(p[1])tb.appendChild(p[1]);});}
function kredMode(mode,btn){var sec=document.getElementById('sec3');
 if(mode==='overdue')sec.classList.add('ovmode');else sec.classList.remove('ovmode');
 sec.querySelectorAll('.seg').forEach(function(b){b.classList.remove('on');});btn.classList.add('on');}
function kredSearch(q){var sec=document.getElementById('sec3');if(!sec)return;q=(q||'').trim().toLowerCase();var shown=0,total=0;
 sec.querySelectorAll('tr.ca-row').forEach(function(r){total++;var hide=q&&(r.dataset.ca||'').toLowerCase().indexOf(q)<0;r.classList.toggle('srch-hide',hide);
  var det=r.nextElementSibling;if(det&&det.classList.contains('det-row'))det.classList.toggle('srch-hide',hide);if(!hide)shown++;});
 var c=document.getElementById('kredSearchCount');if(c)c.textContent=q?('найдено: '+shown+' из '+total):'';}
function refresh(){var b=document.getElementById('refreshBtn');
 function reset(){if(b){b.disabled=false;b.textContent=b.dataset.txt||'⟳ Обновить';}}
 if(b){b.disabled=true;b.dataset.txt=b.textContent;b.textContent='⟳ Обновляю…';}
 toast('Обновляю данные…');
 fetch('/refresh',{method:'POST'}).then(function(r){if(!r.ok)throw 0;
   var t0=Date.now();
   (function poll(){
     fetch('/refresh-status').then(function(r){return r.json();}).then(function(s){
       if(!s.running){
         if(s.ok===false){toast('Ошибка обновления — попробуйте ещё раз');reset();return;}
         toast('Данные обновлены');setTimeout(function(){location.reload();},500);return;
       }
       if(Date.now()-t0>600000){toast('Обновление затянулось — перезагрузите страницу позже');reset();return;}
       setTimeout(poll,3000);
     }).catch(function(){setTimeout(poll,3000);});
   })();
 }).catch(function(){toast('Локальный режим: перезапустите fetch_data.py + build.py');reset();});}
function toast(m){var t=document.getElementById('toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),3000);}
/* ============ Одобрение платежей и реестры (клиент, localStorage) ============ */
var BKEYS_JS=(DATA.meta.bucketLabels||[]).map(function(b){return b.key;});
function lsGet(k,def){try{var v=JSON.parse(localStorage.getItem(k));return v==null?def:v;}catch(e){return def;}}
function lsSet(k,v){try{localStorage.setItem(k,JSON.stringify(v));}catch(e){}}
// Реестры: кэш в памяти. Backend — сервер (Supabase через /api/registers) или localStorage (Фаза 1, file://).
var REGISTERS=[],REG_BACKEND='local';
function regs(){return REGISTERS;}
function saveLocal(){lsSet('planfact_registers',REGISTERS);}
function loadRegisters(cb){
 fetch('/api/registers',{headers:{'Accept':'application/json'}}).then(function(r){
   if(!r.ok)throw 0;return r.json();
 }).then(function(data){REG_BACKEND='server';REGISTERS=Array.isArray(data)?data:[];if(cb)cb();})
 .catch(function(){REG_BACKEND='local';REGISTERS=lsGet('planfact_registers',[]);if(cb)cb();});}
function regCreate(reg){
 if(REG_BACKEND==='server'){return fetch('/api/registers',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(reg)})
   .then(function(r){if(!r.ok)throw 0;return r.json();}).then(function(row){REGISTERS.push(row&&row.id?row:reg);});}
 REGISTERS.push(reg);saveLocal();return Promise.resolve();}
function regUpdate(id,patch){
 var r=REGISTERS.filter(function(x){return x.id===id;})[0];if(r){r.total=patch.total;r.items=patch.items;}
 if(REG_BACKEND==='server'){return fetch('/api/registers/'+encodeURIComponent(id),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(patch)})
   .then(function(x){if(!x.ok)throw 0;});}
 saveLocal();return Promise.resolve();}
function regDelete(id){
 REGISTERS=REGISTERS.filter(function(x){return x.id!==id;});
 if(REG_BACKEND==='server'){return fetch('/api/registers/'+encodeURIComponent(id),{method:'DELETE'}).then(function(x){if(!x.ok)throw 0;});}
 saveLocal();return Promise.resolve();}
function rub(v){v=Math.round(v);return v.toLocaleString('ru-RU').replace(/,/g,' ');}
function escJS(s){return (s==null?'':(''+s)).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function dmy(s){return (!s||s.length<10)?(s||''):(s.slice(8,10)+'.'+s.slice(5,7)+'.'+s.slice(0,4));}
function fmtDT(iso){var d=new Date(iso);function p(n){return(n<10?'0':'')+n;}return p(d.getDate())+'.'+p(d.getMonth()+1)+'.'+d.getFullYear()+' '+p(d.getHours())+':'+p(d.getMinutes());}
// текущие operationId в кредиторке -> фактическая сумма (из свежих данных ПланФакта)
function kredOps(){var m={};(DATA.payables.groups||[]).forEach(function(g){(g.lines||[]).forEach(function(l){m[l.id]=(m[l.id]||0)+l.val;});});return m;}
// одобренные, но ещё не проведённые суммы: суммируем по реестрам, но только пока платёж ещё в кредиторке
function pendingMap(){var ops=kredOps(),byOp={};regs().forEach(function(r){(r.items||[]).forEach(function(it){if(ops[it.opId]!=null)byOp[it.opId]=(byOp[it.opId]||0)+it.amount;});});
 Object.keys(byOp).forEach(function(op){if(byOp[op]>ops[op])byOp[op]=ops[op];});return byOp;}
function kredTab(t){var sec=document.getElementById('sec3');if(!sec)return;
 sec.querySelectorAll('.kred-tab').forEach(function(b){b.classList.remove('on');});
 var tb=document.getElementById('ktab-'+t);if(tb)tb.classList.add('on');
 document.getElementById('kred-main').style.display=(t==='main'?'block':'none');
 document.getElementById('kred-reg').style.display=(t==='reg'?'block':'none');
 if(t==='reg')renderRegisters();}
function approveMode(on){var sec=document.getElementById('sec3');if(!sec)return;
 if(typeof on!=='boolean')on=!sec.classList.contains('apprmode');
 sec.classList.toggle('apprmode',on);
 document.getElementById('apprActions').style.display=on?'inline-flex':'none';
 var b=document.getElementById('apprBtn');b.classList.toggle('on',on);b.setAttribute('aria-pressed',on);
 b.textContent=on?'Одобрение включено — отметьте платежи':'Режим одобрения платежей';
 if(on){kredTab('main');
 } else {sec.querySelectorAll('.appr-chk').forEach(function(c){c.checked=false;});
   sec.querySelectorAll('.appr-amt').forEach(function(i){i.value='';});
   sec.querySelectorAll('tr.det-pay.appr-on').forEach(function(r){r.classList.remove('appr-on');});}}
function apprRowSync(el){var tr=el.closest('tr.det-pay');if(!tr)return;var chk=tr.querySelector('.appr-chk');
 if(el.classList.contains('appr-amt')&&el.value!=='')chk.checked=true;
 tr.classList.toggle('appr-on',chk.checked);}
function applyApproval(){var sec=document.getElementById('sec3');var items=[];
 sec.querySelectorAll('tr.det-pay').forEach(function(tr){var chk=tr.querySelector('.appr-chk');if(!chk||!chk.checked)return;
  var val=+tr.dataset.val||0,raw=tr.querySelector('.appr-amt').value,amt=(raw===''?val:Math.min(+raw,val));
  if(!(amt>0))return;
  items.push({opId:+tr.dataset.opid,ca:tr.dataset.ca,cmt:tr.dataset.cmt,date:tr.dataset.date,accr:tr.dataset.accr,prj:tr.dataset.prj,b:+tr.dataset.b,val:val,amount:amt});});
 if(!items.length){toast('Отметьте хотя бы один платёж');return;}
 var now=new Date();var reg={id:'R'+now.getTime(),ts:now.toISOString(),total:items.reduce(function(s,i){return s+i.amount;},0),items:items};
 regCreate(reg).then(function(){
   approveMode(false);applyPending();renderRegisters();kredTab('reg');
   toast('Реестр создан: '+items.length+' платежей на '+rub(reg.total)+' RSD');
 }).catch(function(){toast('Не удалось сохранить реестр на сервере');});}
var editingReg=null;
function renderRegisters(){var rs=regs();var cnt=document.getElementById('regCount');if(cnt)cnt.textContent=rs.length?('('+rs.length+')'):'';
 var host=document.getElementById('regList');if(!host)return;
 if(!rs.length){host.innerHTML='<div class="lead">Реестров пока нет. Включите «Режим одобрения платежей», отметьте платежи и нажмите «Применить».</div>';editingReg=null;return;}
 var ops=kredOps(),h='';
 rs.slice().reverse().forEach(function(r){
  if(editingReg===r.id){h+=editRegCard(r);return;}
  var live=(r.items||[]).filter(function(it){return ops[it.opId]!=null;}).length,allDone=(live===0);
  var status=live?('<span class="reg-live">ожидают проводки в ПланФакте: '+live+' из '+r.items.length+'</span>'):'<span class="reg-done">все платежи проведены в ПланФакте</span>';
  var det=(r.items||[]).map(function(it){var part=(it.amount<it.val)?(' <span style="color:#888">(из '+rub(it.val)+')</span>'):'';
    var st=(ops[it.opId]!=null)?'<span class="reg-live">ожидает</span>':'<span class="reg-done">проведён</span>';
    return '<tr><td>'+escJS(it.ca)+'</td><td>'+escJS(it.cmt||it.prj||'—')+'</td><td>'+dmy(it.accr)+'</td><td class="num strong"><span class="mon" data-r="'+it.amount+'">'+rub(it.amount)+'</span>'+part+'</td><td>'+st+'</td></tr>';}).join('');
  var actions='<button class="seg" onclick="printRegister(\''+r.id+'\')">Скачать PDF / печать</button>';
  if(!allDone){actions+='<button class="seg" onclick="editRegister(\''+r.id+'\')">Править</button>'
    +'<button class="seg" style="color:#c0392b;border-color:#e8b4ac" onclick="cancelRegister(\''+r.id+'\')">Отменить реестр целиком</button>';}
  else{actions+='<span class="reg-archived">архив · платежи проведены</span>';}
  h+='<div class="regcard">'
    +'<div class="regcard-hd reg-toggle" onclick="toggleRegView(this)"><div><b>▸ Реестр от '+fmtDT(r.ts)+'</b><div class="reg-sub">'+r.items.length+' платежей · '+status+' · <span class="reg-more">показать платежи</span></div></div>'
    +'<div class="regcard-tot"><span class="mon" data-r="'+r.total+'">'+rub(r.total)+'</span> <span class="cur-sym">RSD</span></div></div>'
    +'<div class="reg-det" style="display:none"><table class="rdet"><thead><tr><th>Контрагент</th><th>Назначение</th><th>Начисление</th><th class="num">К оплате</th><th>Статус</th></tr></thead><tbody>'+det+'</tbody></table></div>'
    +'<div class="regcard-actions">'+actions+'</div></div>';});
 host.innerHTML=h;applyCurrency();}
function toggleRegView(el){var card=el.closest('.regcard');if(!card)return;var det=card.querySelector('.reg-det');if(!det)return;
 var open=det.style.display==='none';det.style.display=open?'':'none';
 var b=el.querySelector('b');if(b)b.textContent=b.textContent.replace(open?'▸':'▾',open?'▾':'▸');
 var m=el.querySelector('.reg-more');if(m)m.textContent=open?'скрыть платежи':'показать платежи';}
function editRegCard(r){
 var rows=(r.items||[]).map(function(it){
   return '<tr class="reg-item" data-opid="'+it.opId+'" data-removed=""><td>'+escJS(it.ca)+'</td><td>'+escJS(it.cmt||it.prj||'—')+'</td>'
     +'<td class="num"><input class="appr-amt reg-amt" type="number" min="0" value="'+it.amount+'"> <span style="color:var(--muted);font-size:10px">из '+rub(it.val)+'</span></td>'
     +'<td><button class="seg" style="padding:3px 9px;font-size:11px" onclick="toggleRegItem(this)">отменить</button></td></tr>';}).join('');
 return '<div class="regcard"><div class="regcard-hd"><div><b>Реестр от '+fmtDT(r.ts)+'</b><div class="reg-sub">режим правки · измените суммы или отмените платёж (0 = убрать)</div></div></div>'
   +'<table class="rdet" id="reg-items-'+r.id+'" style="margin-top:10px"><thead><tr><th>Контрагент</th><th>Назначение</th><th class="num">К оплате, RSD</th><th></th></tr></thead><tbody>'+rows+'</tbody></table>'
   +'<div class="regcard-actions"><button class="seg" style="background:#2f9e6b;color:#fff;border-color:#2f9e6b" onclick="saveRegisterEdits(\''+r.id+'\')">Сохранить</button>'
   +'<button class="seg" onclick="cancelEditRegister()">Отмена</button>'
   +'<button class="seg" style="color:#c0392b;border-color:#e8b4ac" onclick="cancelRegister(\''+r.id+'\')">Отменить реестр целиком</button></div></div>';}
function editRegister(id){editingReg=id;renderRegisters();}
function cancelEditRegister(){editingReg=null;renderRegisters();}
function toggleRegItem(btn){var tr=btn.closest('tr.reg-item'),inp=tr.querySelector('.reg-amt');
 if(tr.dataset.removed==='1'){tr.dataset.removed='';tr.style.opacity='';inp.disabled=false;btn.textContent='отменить';}
 else{tr.dataset.removed='1';tr.style.opacity='.4';inp.disabled=true;btn.textContent='вернуть';}}
function saveRegisterEdits(id){var r=regs().filter(function(x){return x.id===id;})[0];if(!r)return;
 var host=document.getElementById('reg-items-'+id),byOp={};(r.items||[]).forEach(function(it){byOp[it.opId]=it;});
 var newItems=[];
 host.querySelectorAll('tr.reg-item').forEach(function(tr){if(tr.dataset.removed==='1')return;
   var it=byOp[+tr.dataset.opid];if(!it)return;var v=+tr.querySelector('.reg-amt').value;
   if(!(v>0))return;var ni={};for(var k in it)ni[k]=it[k];ni.amount=Math.min(v,it.val);newItems.push(ni);});
 if(!newItems.length){regDelete(id).then(function(){
     editingReg=null;applyPending();renderRegisters();toast('Все платежи отменены — реестр удалён');
   }).catch(function(){toast('Ошибка сохранения на сервере');});return;}
 var total=newItems.reduce(function(s,i){return s+i.amount;},0);
 regUpdate(id,{total:total,items:newItems}).then(function(){
   editingReg=null;applyPending();renderRegisters();toast('Реестр обновлён: '+newItems.length+' платежей на '+rub(total)+' RSD');
 }).catch(function(){toast('Ошибка сохранения на сервере');});}
function cancelRegister(id){var r=regs().filter(function(x){return x.id===id;})[0];if(!r)return;
 if(!confirm('Отменить весь реестр от '+fmtDT(r.ts)+'? Все '+r.items.length+' одобренных платежей вернутся в кредиторку.'))return;
 regDelete(id).then(function(){
   if(editingReg===id)editingReg=null;applyPending();renderRegisters();toast('Реестр отменён — суммы возвращены в кредиторку');
 }).catch(function(){toast('Ошибка удаления на сервере');});}
function deleteRegister(id){return cancelRegister(id);}
function printRegister(id){var r=regs().filter(function(x){return x.id===id;})[0];if(!r)return;var rows='',tot=0;
 r.items.forEach(function(it){tot+=it.amount;var part=(it.amount<it.val)?(' <span style="color:#888">(из '+rub(it.val)+')</span>'):'';
  rows+='<tr><td>'+escJS(it.ca)+'</td><td>'+escJS(it.prj||'')+'</td><td>'+dmy(it.accr)+'</td><td>'+escJS(it.cmt||'')+'</td><td class="r">'+rub(it.amount)+part+'</td></tr>';});
 var html='<html><head><meta charset="utf-8"><title>Реестр платежей '+fmtDT(r.ts)+'</title>'
  +'<style>body{font-family:Arial,Helvetica,sans-serif;margin:28px;color:#111}h1{font-size:18px;margin:0 0 4px}.meta{color:#555;font-size:13px;margin-bottom:14px}'
  +'table{border-collapse:collapse;width:100%;font-size:12px}th,td{border:1px solid #bbb;padding:6px 9px;text-align:left;vertical-align:top}'
  +'th{background:#eee}td.r,th.r{text-align:right;white-space:nowrap}tfoot td{font-weight:bold;background:#f6f6f6}@media print{button{display:none}}</style></head><body>'
  +'<h1>Реестр платежей</h1><div class="meta">Tekstura DOO · сформирован '+fmtDT(r.ts)+' · платежей: '+r.items.length+'</div>'
  +'<table><thead><tr><th>Контрагент</th><th>Проект</th><th>Начисление</th><th>Назначение</th><th class="r">К оплате, RSD</th></tr></thead>'
  +'<tbody>'+rows+'</tbody><tfoot><tr><td colspan="4">ИТОГО К ОПЛАТЕ</td><td class="r">'+rub(tot)+'</td></tr></tfoot></table>'
  +'<script>window.onload=function(){window.print();}<\/script></body></html>';
 var w=window.open('','_blank');if(!w){toast('Разрешите всплывающие окна для печати');return;}w.document.write(html);w.document.close();}
function badgeHTML(pend,fact){var h='<div class="pend-badge">−<span class="mon" data-r="'+pend+'">'+rub(pend)+'</span> одобр.';
 if(fact!=null){var eff=Math.max(0,fact-pend);h+=' · ост.<span class="mon" data-r="'+eff+'">'+rub(eff)+'</span>';}
 return h+'</div>';}
function addBadge(cell,pend){if(!cell||!(pend>0))return;var m=cell.querySelector('.mon');var fact=m?(parseFloat(m.getAttribute('data-r'))||0):null;cell.insertAdjacentHTML('beforeend',badgeHTML(pend,fact));}
function setCardPend(cid,fact,pend){var c=document.getElementById(cid);if(!c||!(pend>0))return;var v=c.querySelector('.val');if(v)v.insertAdjacentHTML('afterend',badgeHTML(pend,fact));}
function applyPending(){var sec=document.getElementById('sec3');if(!sec)return;
 sec.querySelectorAll('.pend-badge').forEach(function(e){e.remove();});
 document.querySelectorAll('#card-kredtot .pend-badge,#card-kredov .pend-badge').forEach(function(e){e.remove();});
 var byOp=pendingMap();
 var caTot={},caBuk={},grand=0,over=0;
 (DATA.payables.groups||[]).forEach(function(g){(g.lines||[]).forEach(function(l){var p=byOp[l.id];if(!p)return;
   caTot[g.name]=(caTot[g.name]||0)+p;caBuk[g.name]=caBuk[g.name]||{};caBuk[g.name][l.b]=(caBuk[g.name][l.b]||0)+p;
   grand+=p;if(l.b===-1)over+=p;});});
 setCardPend('card-kredtot',DATA.payables.total,grand);
 setCardPend('card-kredov',DATA.payables.overdue,over);
 sec.querySelectorAll('tr.ca-row').forEach(function(row){var ca=row.dataset.ca;var tds=row.querySelectorAll('td.num');
   if(caTot[ca])addBadge(tds[0],caTot[ca]);
   var bk=caBuk[ca]||{};BKEYS_JS.forEach(function(key,i){if(bk[key]&&tds[i+1])addBadge(tds[i+1],bk[key]);});});
 sec.querySelectorAll('tr.det-pay').forEach(function(tr){var p=byOp[+tr.dataset.opid];if(p)addBadge(tr.querySelector('.pay-sum'),p);});
 applyCurrency();}
loadRegisters(function(){try{renderRegisters();applyPending();}catch(e){}});
loadSettings(applySettings);   // общие настройки (план, валюта, порядок меню, ширина колонки, банк-факт) → применить + перерисовать
</script></body></html>"""

# ---------------- Раздел 0: Главный ----------------
k = data["kpis"]
def card(cap, val, sub="", cls="", vcls="", cid=""):
    idattr = f' id="{cid}"' if cid else ""
    return f'<div class="card {cls}"{idattr}><div class="cap">{cap}</div><div class="val {vcls}">{val}</div><div class="sub">{sub}</div></div>'
ACC_MAIN = "DOO (Осн) 51"   # счёт с ручным вводом фактического остатка (банк-клиент отстаёт на день)
_tot = round(k["cashTotal"], 2)
_bal_cards = ""
for a in k["accounts"]:
    if a["account"] == ACC_MAIN:
        pf = round(a["balance"], 2)
        _bal_cards += (
            '<div class="sb-card">'
            f'<div class="sb-cn" title="Банк-клиент/выписка отстают на 1 день: ПланФакт показывает вчерашний остаток, в понедельник — пятничный.">{ACC_MAIN} · факт</div>'
            f'<div class="sb-cv"><span class="mon" data-r="{pf}" id="bankMainNum">{_n(a["balance"])}</span> <span class="cur-sym">RSD</span></div>'
            f'<div class="sb-csub">ПланФакт: {fmt(pf)}<span id="bankDelta" class="bankdelta"></span></div>'
            f'<div class="sb-edit"><input class="bankfact" data-acc="{ACC_MAIN}" data-pf="{pf}" type="number" inputmode="numeric" placeholder="факт из банка" aria-label="Фактический остаток по банку, {ACC_MAIN}" onkeydown="if(event.key===\'Enter\')saveBankFact()"><button class="sb-ok" onclick="saveBankFact()">ОК</button></div>'
            '</div>')
    else:
        _bal_cards += (f'<div class="sb-card"><div class="sb-cn">{a["account"]}</div>'
                       f'<div class="sb-cv">{sign(a["balance"])} <span class="cur-sym">RSD</span></div></div>')
side_bal = ('<div class="side-bal">'
            '<div class="sb-card sb-total-card"><div class="sb-tcap">Деньги на счетах</div>'
            f'<div class="sb-total"><span class="mon" data-r="{_tot}" data-base="{_tot}" id="bankTotalNum">{_n(k["cashTotal"])}</span> <span class="cur-sym">RSD</span></div>'
            f'<div class="sb-tsub">{len(k["accounts"])} счёта · с учётом факта</div></div>'
            f'{_bal_cards}</div>')
sec0 = f'''<div class="sec on" id="sec0">
<div class="panel">
<div class="panel-hd"><h2 style="margin:0">Продажи по категориям</h2>
<div class="salesctl">
<div class="seg-mini"><button class="on" onclick="setBasis('accrual',this)">Продано по договорам</button><button onclick="setBasis('cash',this)">Получено фактически</button></div>
<div class="seg-mini"><button class="on" onclick="setGran('month',this)">Месяцы</button><button onclick="setGran('quarter',this)">Кварталы</button></div>
<label class="flt">с <select id="salesFrom" onchange="renderSales()"></select></label>
<label class="flt">по <select id="salesTo" onchange="renderSales()"></select></label>
</div></div>
<div style="overflow-x:auto"><table class="pl" id="salesTable"></table></div></div>
<div class="panel">
<div class="panel-hd"><h2 style="margin:0">План продаж — выполнение (месяц)</h2>
<div class="salesctl"><select id="planQ" onchange="renderPlan()"></select>
<button class="seg-btn" onclick="togglePlanEdit()">✎ Изменить план</button></div></div>
<div id="planMeta" class="lead" style="margin-top:-4px"></div>
<div id="planEdit" class="planedit" style="display:none"></div>
<div id="planGrid" class="pgrid"></div></div>
</div>'''

# ---------------- Раздел 1: P&L (маржинальный) ----------------
p = data["pnl"]; MS = p["months"]
RU_MON = ["янв","фев","мар","апр","май","июн","июл","авг","сен","окт","ноя","дек"]
# кварталы: группируем месяцы, для переключателя Месяцы/Кварталы
def _qk(m): return f"{m[:4]}-Q{(int(m[5:7])-1)//3+1}"
QS = []; QM = {}
for _m in MS:
    _k = _qk(_m)
    if _k not in QM: QM[_k] = []; QS.append(_k)
    QM[_k].append(_m)
def _qlabel(k): y, q = k.split("-Q"); return f"Q{q} '{y[2:]}"
_lines_by_label = {ln["label"]: ln.get("months", {}) for ln in p["lines"]}
_REVM = _lines_by_label.get("Выручка", {})
QREV = {k: sum(_REVM.get(m, 0) for m in QM[k]) for k in QS}
PCT_NUM = {"Маржинальность": "Маржинальная прибыль", "Рентабельность чистой прибыли": "Чистая прибыль (убыток)"}
def mhead():
    h = "".join(f'<th class="num col-m">{RU_MON[int(m[5:7])-1]} \'{m[2:4]}</th>' for m in MS)
    return h + "".join(f'<th class="num col-q">{_qlabel(k)}</th>' for k in QS)
def _mc(v, cls, color):
    if not v: return f'<td class="num mut {cls}">—</td>'
    if color: return f'<td class="num {cls} {"neg" if v<0 else ""}">{sign(v)}</td>'
    return f'<td class="num {cls}">{fmt(v)}</td>'
def money_cells(months, color=False):
    c = "".join(_mc(months.get(m, 0), "col-m", color) for m in MS)
    return c + "".join(_mc(sum(months.get(m, 0) for m in QM[k]), "col-q", color) for k in QS)
def _pc(v, cls):
    return f'<td class="num mut {cls}">—</td>' if v is None else f'<td class="num {cls} {"neg" if v<0 else ""}">{("%.1f"%v).replace(".",",")}%</td>'
def pct_cells(months, num_months=None):
    c = "".join(_pc(months.get(m), "col-m") for m in MS)
    for k in QS:
        rev = QREV.get(k, 0); num = sum((num_months or {}).get(m, 0) for m in QM[k])
        c += _pc((num / rev * 100) if rev else None, "col-q")
    return c
plrows = ""; nid = [0]
def render_node(node, parent_dom, depth):
    nid[0] += 1; me = f"n{nid[0]}"
    has = bool(node["children"])
    arr = '<span class="arr">▸</span> ' if has else '<span class="arr" style="visibility:hidden">▸</span> '
    oc = ' onclick="tnode(this)"' if has else ""
    pad = 10 + depth * 17
    r = (f'<tr class="pl-sub tnode" data-id="{me}" data-parent="{parent_dom}" style="display:none"{oc}>'
         f'<td class="subnm" style="padding-left:{pad}px">{arr}{node["category"]}</td>'
         f'{money_cells(node["months"])}<td class="num">{fmt(node["total"])}</td></tr>')
    for ch in node["children"]:
        r += render_node(ch, me, depth + 1)
    return r
for ln in p["lines"]:
    if ln["kind"] == "percent":
        _num = _lines_by_label.get(PCT_NUM.get(ln["label"], ""), {})
        plrows += f'<tr class="pl-pct"><td>{ln["label"]}</td>{pct_cells(ln["months"], _num)}<td class="num mut">—</td></tr>'
    elif ln["kind"] == "result":
        plrows += f'<tr class="pl-res"><td>{ln["label"]}</td>{money_cells(ln["months"],True)}<td class="num {"neg" if ln["total"]<0 else ""}">{sign(ln["total"])}</td></tr>'
    else:
        has = bool(ln["tree"]); nid[0] += 1; lid = f"L{nid[0]}"
        arr = '<span class="arr">▸</span> ' if has else ""
        oc = f' onclick="tnode(this)" data-id="{lid}"' if has else ""
        plrows += f'<tr class="pl-line{" clk" if has else ""}"{oc}><td class="nm">{arr}{ln["label"]}</td>{money_cells(ln["months"])}<td class="num strong">{fmt(ln["total"])}</td></tr>'
        for node in ln["tree"]:
            plrows += render_node(node, lid, 0)
sec1 = f'''<div class="sec" id="sec1">
<div class="cards">
{card("Выручка", fmt(p["revenueTotal"])+" " + SYM, "начисление, апрель→сейчас","accent")}
{card("Чистая прибыль", sign(p["profitTotal"])+" " + SYM, "апрель→сейчас","","pos" if p["profitTotal"]>=0 else "neg")}
</div>
<div class="panel"><div class="panel-hd"><h2>Отчёт о прибылях и убытках (маржинальный)</h2>
<div class="seg-mini pl-gran"><button class="on" onclick="plGran('month',this)">Месяцы</button><button onclick="plGran('quarter',this)">Кварталы</button></div></div>
<div class="lead">Метод начисления · RSD · по статьям учёта ПланФакта, с апреля 2026. Клик по статье раскрывает подстатьи.</div>
<table class="pl"><thead><tr><th>По статьям учёта</th>{mhead()}<th class="num">Итого</th></tr></thead><tbody>{plrows}</tbody></table></div></div>'''

# ---------------- Разделы 2 и 3: реестры ----------------
def reg_section(sid, block, kind):
    glabel = block["groupLabel"]
    by_ca = (glabel == "Контрагент")
    bh = "".join(f'<th class="num sortable {("od" if b["kind"]=="overdue" else "cw" if b["kind"]=="current" else "")}" data-t="num" onclick="sortReg(this)">{b["label"]}</th>' for b in BL)
    # заголовки детализации
    appr_th = "<th class='appr-col'>Одобрить</th>" if by_ca else ""
    if by_ca:
        det_head = f"<th>Оплата</th><th>Проект</th><th>Начисление</th><th>Описание</th><th class='num'>Сумма</th>{appr_th}"
    else:
        det_head = "<th>Оплата</th><th>Контрагент</th><th>Начисление</th><th>Описание</th><th class='num'>Сумма</th>"
    appr_widget = ('<td class="appr-col"><label class="appr-lbl"><input type="checkbox" class="appr-chk" onchange="apprRowSync(this)"> платим</label>'
                   ' <input type="number" class="appr-amt" min="0" placeholder="вся сумма" oninput="apprRowSync(this)"></td>') if by_ca else ""
    rows = ""
    for c in block["groups"]:
        cells = ""
        for b in BKEYS:
            v = c["buckets"].get(str(b), 0)
            cls = "od" if (b == -1 and v) else ("cw" if (b == 0 and v) else "")
            cells += f'<td class="num {cls}">{fmt(v)}</td>'
        det = ""
        for l in c["lines"]:
            od = 'class="od"' if l["b"] == -1 else ""
            d = dfmt(l["date"])
            if by_ca:
                da = (f'data-opid="{l["id"]}" data-val="{l["val"]}" data-ca="{esc(l["ca"])}" data-cmt="{esc(l["cmt"])}" '
                      f'data-date="{l["date"]}" data-accr="{l["accr"] or ""}" data-prj="{esc(l["prj"] or "")}" data-b="{l["b"]}"')
                pcls = "det-pay ovrow" if l["b"] == -1 else "det-pay"
                det += (f'<tr class="{pcls}" {da}><td {od}>{d}</td><td>{esc(l["prj"]) or "—"}</td><td>{dfmt(l["accr"])}</td>'
                        f'<td>{esc(l["cmt"]) or "—"}</td><td class="num strong pay-sum">{fmt(l["val"])}</td>{appr_widget}</tr>')
            else:
                rc = ' class="ovrow"' if l["b"] == -1 else ''
                det += f'<tr{rc}><td {od}>{d}</td><td>{esc(l["ca"])}</td><td>{dfmt(l["accr"])}</td><td>{esc(l["cmt"]) or "—"}</td><td class="num strong">{fmt(l["val"])}</td></tr>'
        ovv = c["buckets"].get("-1", 0)
        rcls = "ca-row" + ("" if ovv else " no-ov")
        rows += f'''<tr class="{rcls}" data-ca="{esc(c["name"])}" data-ov="{round(ovv,2)}" onclick="toggle(this)"><td class="nm">▸ {esc(c["name"])}</td><td class="num strong">{fmt(c["total"])}</td>{cells}</tr>
        <tr class="det-row"><td colspan="{len(BKEYS)+2}"><table class="det"><thead><tr>{det_head}</tr></thead><tbody>{det}</tbody></table></td></tr>'''
    ov = block["overdue"]
    sub = f'{block["contragents"]} контрагентов' if by_ca else f'{block["units"]} статей · {block["contragents"]} контрагентов'
    cid_t = "card-kredtot" if by_ca else ""
    cid_o = "card-kredov" if by_ca else ""
    cards_html = f'''<div class="cards">
{card("Всего "+kind, fmt(block["total"])+" " + SYM, sub, "accent", "", cid_t)}
{card("Просрочено", fmt(ov)+" " + SYM, "срок оплаты прошёл","", "neg" if ov else "", cid_o)}
</div>'''
    toggle_ui = (f'''<div class="segbar"><span class="seglbl">Показать:</span>
<button class="seg on" onclick="kredMode('all',this)">Вся кредиторка</button>
<button class="seg" onclick="kredMode('overdue',this)">Просроченная</button></div>''' if by_ca else '')
    table_html = f'''<div class="panel"><div class="lead">Неделя = ожидаемая дата оплаты. «Тек. неделя» — {[b for b in BL if b["kind"]=="current"][0]["range"]}. Клик по заголовку столбца — сортировка; клик по строке — платежи внутри.</div>
<table class="reg"><thead><tr><th class="sortable" data-t="txt" onclick="sortReg(this)">{glabel} ({block["units"]})</th><th class="num sortable" data-t="num" onclick="sortReg(this)">Всего</th>{bh}</tr></thead><tbody>{rows}</tbody></table></div>'''
    if not by_ca:
        return f'''<div class="sec" id="sec{sid}">
{cards_html}
{table_html}</div>'''
    # --- кредиторка: вкладки «Кредиторка / Реестры» + режим одобрения ---
    return f'''<div class="sec" id="sec{sid}">
{cards_html}
<div class="kred-tabs">
<button class="kred-tab on" id="ktab-main" onclick="kredTab('main')">Кредиторка</button>
<button class="kred-tab" id="ktab-reg" onclick="kredTab('reg')">Реестры <span id="regCount"></span></button>
</div>
<div id="kred-main">
<div class="appr-bar">
<button class="seg" id="apprBtn" aria-pressed="false" onclick="approveMode()">Режим одобрения платежей</button>
<span id="apprActions" style="display:none;align-items:center;gap:10px">
<button class="seg" style="background:#2f9e6b;color:#fff;border-color:#2f9e6b" onclick="applyApproval()">Применить (создать реестр)</button>
<button class="seg" onclick="approveMode(false)">Отмена</button>
<span class="appr-hint">Отметьте «платим» у нужных платежей · пустое поле = вся сумма, иначе — частичная</span>
</span>
</div>
{toggle_ui}
<div class="kred-search"><input id="kredSearch" type="search" placeholder="🔍 Поиск по контрагенту…" oninput="kredSearch(this.value)" aria-label="Поиск по контрагенту"><span id="kredSearchCount" class="kred-search-cnt"></span></div>
{table_html}
</div>
<div id="kred-reg" style="display:none"><div class="panel" id="regList"></div></div>
</div>'''
sec2 = reg_section(2, data["receivables"], "дебиторка")
sec3 = reg_section(3, data["payables"], "кредиторка")

# ---------------- Раздел 4: ДДС ----------------
d = data["dds"]
def flow_row(name, f):
    months = {x["m"]: x["net"] for x in f["byMonth"]}
    cells = "".join(f'<td class="num {"neg" if months.get(m,0)<0 else ""}">{sign(months.get(m,0))}</td>' for m in MS)
    return f'<tr><td>{name}</td>{cells}<td class="num strong {"neg" if f["net"]<0 else "pos"}">{sign(f["net"])}</td></tr>'
gen_by_m = {}
for f in (d["operating"], d["investment"], d["financial"]):
    for x in f["byMonth"]:
        gen_by_m[x["m"]] = gen_by_m.get(x["m"], 0) + x["net"]
gen_cells = "".join(f'<td class="num {"neg" if gen_by_m.get(m,0)<0 else "pos"}">{sign(gen_by_m.get(m,0))}</td>' for m in MS)
sec4 = f'''<div class="sec" id="sec4">
<div class="cards">
{card("Чистый денежный поток", sign(d["generalNet"])+" " + SYM, "апрель→сейчас","accent")}
{card("Остаток на счетах", f'<span class="mon" data-r="{_tot}" data-base="{_tot}" id="ddsBalNum">{_n(_tot)}</span> ' + SYM, "основные счета · с учётом факта")}
</div>
<div class="panel"><h2>Движение денежных средств по видам деятельности</h2>
<div class="lead">Кассовый метод, помесячно. Первый вариант — скорректируем после вашего просмотра.</div>
<table><thead><tr><th>Поток</th>{mhead()}<th class="num">Итого</th></tr></thead><tbody>
{flow_row("Операционный", d["operating"])}
{flow_row("Инвестиционный", d["investment"])}
{flow_row("Финансовый", d["financial"])}
<tr class="tot"><td>Чистый поток</td>{gen_cells}<td class="num">{sign(d["generalNet"])}</td></tr>
</tbody></table></div></div>'''

# ---------------- Раздел 5: Проекты ----------------
PJ = data["projects"]["groups"]
def rentf(r): return "—" if r is None else f'{("%.1f"%r).replace(".",",")}%'
pjrows = ""; _gi = 0; _pi = 0
for g in PJ:
    _gi += 1; gid = f"pg{_gi}"
    _gd = sum(1 for p in g["projects"] if p["status"] == "done")
    _gw = g["n"] - _gd
    pjrows += (f'<tr class="pj-group" data-gd="{_gd}" data-gw="{_gw}" onclick="tnode(this)" data-id="{gid}"><td class="nm"><span class="arr">▸</span> {esc(g["group"])} <span class="mut">({g["n"]})</span></td>'
               f'<td></td><td class="mut" style="font-size:11px">в работе {_gw} · завершено {_gd}</td>'
               f'<td class="num">{fmt(g["income"])}</td><td class="num">{fmt(g["outcome"])}</td>'
               f'<td class="num strong {"neg" if g["profit"]<0 else "pos"}">{sign(g["profit"])}</td><td class="num">{rentf(g["rent"])}</td></tr>')
    for p in g["projects"]:
        _pi += 1; pid = f"pp{_pi}"; haspay = bool(p["payments"])
        arr = '<span class="arr">▸</span> ' if haspay else '<span class="arr" style="visibility:hidden">▸</span> '
        oc = f' onclick="tnode(this)" data-id="{pid}"' if haspay else ''
        nd = p["nd"]; nk = p["nk"]
        badge = (f' <span class="tag-d">деб {nd}</span>' if nd else '') + (f' <span class="tag-k">кред {nk}</span>' if nk else '')
        _st = ('завершён', 'stdone') if p["status"] == "done" else ('в работе', 'stwork')
        pjrows += (f'<tr class="pj-proj tnode" data-parent="{gid}" data-status="{p["status"]}" style="display:none"{oc}><td class="nm2">{arr}{esc(p["title"])}{badge}</td>'
                   f'<td class="dt">{dfmt(p["start"])}<br>{dfmt(p["end"])}</td><td><span class="{_st[1]}">{_st[0]}</span></td>'
                   f'<td class="num">{fmt(p["income"])}</td><td class="num">{fmt(p["outcome"])}</td>'
                   f'<td class="num strong {"neg" if p["profit"]<0 else "pos"}">{sign(p["profit"])}</td><td class="num">{rentf(p["rent"])}</td></tr>')
        for l in p["payments"]:
            pd = "1" if l["paid"] else "0"
            if l["kind"] == "income":
                tag = '<span class="tag-ok">получен</span>' if l["paid"] else '<span class="tag-d">деб</span>'
                cols = f'<td class="num pos">{fmt(l["val"])}</td><td></td>'
            else:
                tag = '<span class="tag-ok">оплачен</span>' if l["paid"] else '<span class="tag-k">кред</span>'
                cols = f'<td></td><td class="num neg">{fmt(l["val"])}</td>'
            pjrows += (f'<tr class="pj-pay tnode" data-parent="{pid}" data-paid="{pd}" style="display:none">'
                       f'<td class="nm3">{tag} {esc(l["ca"])} · {esc(l["cmt"][:36])}</td>'
                       f'<td class="dt">{dfmt(l["date"])}</td><td></td>{cols}<td></td><td></td></tr>')
_gt_i = sum(g["income"] for g in PJ); _gt_o = sum(g["outcome"] for g in PJ); _gt_p = _gt_i - _gt_o
_pw = sum(1 for g in PJ for p in g["projects"] if p["status"] == "work")
_pd = sum(1 for g in PJ for p in g["projects"] if p["status"] == "done")
sec5 = f'''<div class="sec" id="sec5">
<div class="panel"><div class="panel-hd"><h2 style="margin:0">Проекты — прибыль методом начисления</h2>
<div class="salesctl">
<div class="seg-mini"><button class="on" onclick="filterProjects('all',this)">Все ({_pw + _pd})</button><button onclick="filterProjects('work',this)">В работе ({_pw})</button><button onclick="filterProjects('done',this)">Завершённые ({_pd})</button></div>
<div class="seg-mini"><button class="on" onclick="payMode('unpaid',this)">Только неоплаченные</button><button onclick="payMode('all',this)">Все платежи</button></div>
</div></div>
<div class="note-memo">ℹ️ <b>Статус берётся из ПланФакта: проект «завершён», когда в его карточке установлен флаг завершения.</b> Пока флага нет — «в работе», даже если фактически сдан. Детализация платежей доступна по проектам в работе (закрытые — архив).</div>
<div class="lead">Прибыль = доходы − расходы (начисление). Клик по группе → проекты, клик по проекту → платежи. <span class="tag-d">деб</span> дебиторка / <span class="tag-k">кред</span> кредиторка — начислено, не оплачено; <span class="tag-ok">получен</span>/<span class="tag-ok">оплачен</span> — оплачено.</div>
<div style="overflow-x:auto"><table class="pj pmode-unpaid"><thead><tr><th>Группа / проект</th><th>Начало / Конец</th><th>Статус</th><th class="num">Доходы</th><th class="num">Расходы</th><th class="num">Прибыль</th><th class="num">Рент.</th></tr></thead>
<tbody>{pjrows}<tr class="tot"><td>ИТОГО ({len(PJ)} групп)</td><td></td><td></td><td class="num">{fmt(_gt_i)}</td><td class="num">{fmt(_gt_o)}</td><td class="num">{sign(_gt_p)}</td><td class="num">{rentf(round(_gt_p/_gt_i*100,1) if _gt_i else None)}</td></tr></tbody></table></div></div></div>'''

out = (html.replace("__COMPANY__", data["meta"]["company"]).replace("__CUR__", data["meta"]["currency"])
       .replace("__GEN__", data["meta"]["generatedAt"] or "—").replace("__ASOF__", data["meta"]["asOf"])
       .replace("__SIDEBAL__", side_bal)
       .replace("__SECTIONS__", sec0 + sec1 + sec3 + sec4 + sec5)
       .replace("__DATA__", json.dumps({"meta": data["meta"], "sales": data["sales"], "salesplan": data["salesplan"],
                "payables": {"total": data["payables"]["total"], "overdue": data["payables"]["overdue"],
                             "groups": [{"name": g["name"],
                                         "lines": [{"id": l["id"], "val": l["val"], "b": l["b"]} for l in g["lines"]]}
                                        for g in data["payables"]["groups"]]}}, ensure_ascii=False)))
open(os.path.join(ROOT, "index.html"), "w").write(out)
print("index.html собран:", len(out), "байт")
