"""Genera results/report5.html: Experimento 5 — ¿policy o consenso?
Lee results/adoption.csv y compara, a igual hashpower adoptado, la probabilidad de que gane el
softfork cuando los mineros Core adoptan por POLICY (siguen Core, dejan de spamear) vs por
CONSENSO (se vuelven Knots, enforzan RDTS).
"""
import csv
import json
import os
import statistics as st
from collections import defaultdict

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
CSV = os.path.join(RES, "adoption.csv")


def load():
    by = defaultdict(list)
    with open(CSV) as f:
        for r in csv.DictReader(f):
            by[(r["mode"], int(r["step"]))].append(r)
    rows = []
    steps = sorted({s for (_, s) in by})
    for s in steps:
        row = {"step": s}
        for mode in ("policy", "consensus"):
            g = by.get((mode, s), [])
            if g:
                row["adopted_hp"] = float(g[0]["adopted_hp"])
                wins = sum(1 for r in g if r["softfork_wins"] in ("True", "1"))
                row[f"{mode}_win"] = round(wins / len(g), 3)
                row[f"{mode}_n"] = len(g)
                row[f"{mode}_knots"] = float(g[0]["knots_share"])
        rows.append(row)
    return rows


def build():
    rows = load()
    total = sum(r.get("policy_n", 0) + r.get("consensus_n", 0) for r in rows)
    # umbral de cada modo: menor hashpower adoptado con p_win>=0.5
    def thr(mode):
        xs = [r["adopted_hp"] for r in rows if r.get(f"{mode}_win", 0) >= 0.5]
        return f"{min(xs)*100:.0f}%" if xs else "—"
    stats = [
        ("Consenso gana con", thr("consensus"),
         "hashpower Core que debe adoptar RDTS (volverse Knots) para que gane el softfork — un umbral de MAYORÍA"),
        ("Policy gana con", thr("policy"),
         "hashpower Core que debe endurecer su policy — se necesita que adopten casi TODOS los que spamean"),
        ("¿Equivalente?", "No",
         "adoptar por consenso mueve hashpower al bando limpio; por policy no mueve a nadie de cadena — solo deja de producir spam"),
    ]
    stat_html = "\n".join(
        f'<div class="tile"><div class="tile-label">{a}</div>'
        f'<div class="tile-value">{b}</div><div class="tile-note">{c}</div></div>'
        for a, b, c in stats)
    html = TEMPLATE.replace("__DATA__", json.dumps({"rows": rows})).replace("__STATS__", stat_html)
    html = html.replace("__TOTAL__", str(total))
    out = os.path.join(RES, "report5.html")
    with open(out, "w") as f:
        f.write(html)
    print("escrito", out, f"({len(rows)} pasos, {total} corridas)")
    return out


TEMPLATE = r"""<title>¿Policy o consenso? — sim-rdts (BIP-110/RDTS)</title>
<style>
:root{--bg:#f4f2ec;--surface:#fffdf8;--card:#fff;--ink:#191c24;--muted:#6c7280;--hair:#e4e1d8;
  --policy:#8a92a6;--consensus:#7048e8;--ref:#a7abb6;--shadow:0 1px 2px rgba(20,22,30,.05),0 8px 30px rgba(20,22,30,.06);}
@media (prefers-color-scheme:dark){:root{--bg:#0f1117;--surface:#161922;--card:#1a1e28;--ink:#e9ebf2;--muted:#949bad;
  --hair:#262a35;--policy:#6b7280;--consensus:#a684ff;--ref:#565d6c;--shadow:0 1px 2px rgba(0,0,0,.3),0 12px 34px rgba(0,0,0,.34);}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased;}
.wrap{max-width:940px;margin:0 auto;padding:clamp(20px,5vw,56px) clamp(16px,4vw,32px) 72px;}
a.back{font-family:ui-monospace,Menlo,monospace;font-size:13px;color:var(--consensus);text-decoration:none;} a.back:hover{text-decoration:underline;}
.eyebrow{font-family:ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--consensus);font-weight:600;display:flex;gap:10px;align-items:center;margin-top:10px;}
.eyebrow::before{content:"";width:26px;height:2px;background:var(--consensus);display:inline-block;}
h1{font-size:clamp(28px,5.2vw,44px);line-height:1.08;margin:.5rem 0;letter-spacing:-.02em;text-wrap:balance;font-weight:760;}
.lede{font-size:clamp(15px,2.2vw,18px);color:var(--muted);max-width:66ch;margin:0 0 8px;} .lede b{color:var(--ink);}
.versions{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px;}
.chip{font-family:ui-monospace,Menlo,monospace;font-size:12px;border:1px solid var(--hair);border-radius:999px;padding:5px 11px;color:var(--muted);background:var(--surface);}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:32px 0;}
.tile{background:var(--card);border:1px solid var(--hair);border-radius:14px;padding:18px;box-shadow:var(--shadow);}
.tile-label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:600;}
.tile-value{font-family:ui-monospace,Menlo,monospace;font-size:24px;font-weight:600;margin:6px 0 4px;letter-spacing:-.02em;}
.tile-note{font-size:12.5px;color:var(--muted);line-height:1.4;}
.card{background:var(--card);border:1px solid var(--hair);border-radius:16px;box-shadow:var(--shadow);padding:clamp(18px,3vw,28px);margin:22px 0;}
.card h2{font-size:20px;margin:0 0 4px;letter-spacing:-.01em;} .card .sub{color:var(--muted);font-size:14px;margin:0 0 18px;max-width:66ch;}
.chart-wrap{position:relative;width:100%;overflow-x:auto;} svg{display:block;width:100%;height:auto;}
.legend{display:flex;gap:18px;flex-wrap:wrap;margin-top:12px;font-size:13px;color:var(--muted);}
.legend span{display:inline-flex;align-items:center;gap:7px;} .sw{width:16px;height:3px;border-radius:2px;display:inline-block;}
.tooltip{position:absolute;pointer-events:none;background:var(--card);border:1px solid var(--hair);border-radius:10px;padding:10px 12px;font-size:12.5px;box-shadow:var(--shadow);opacity:0;transition:opacity .12s;min-width:200px;z-index:5;}
.tooltip .tt-n{font-family:ui-monospace,Menlo,monospace;font-weight:600;font-size:13px;margin-bottom:5px;} .tooltip .tt-row{display:flex;justify-content:space-between;gap:14px;color:var(--muted);} .tooltip .tt-row b{color:var(--ink);font-family:ui-monospace,Menlo,monospace;}
table{width:100%;border-collapse:collapse;font-size:13.5px;} th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--hair);}
th{font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:600;} td.num{font-family:ui-monospace,Menlo,monospace;text-align:right;font-variant-numeric:tabular-nums;}
.foot{color:var(--muted);font-size:13px;margin-top:26px;line-height:1.6;} .foot b{color:var(--ink);}
.foot code{font-family:ui-monospace,Menlo,monospace;background:var(--surface);border:1px solid var(--hair);padding:1px 6px;border-radius:6px;font-size:12px;color:var(--ink);}
</style>
<div class="wrap">
  <a class="back" href="index.html">← volver a las simulaciones</a>
  <div class="eyebrow">Experimento 5 · policy vs consenso</div>
  <h1>¿Es equivalente adoptar RDTS por policy o por consenso?</h1>
  <p class="lede">Un minero Core presionado puede reaccionar de dos formas. Por <b>policy</b>:
  sigue corriendo Core y deja de <i>incluir</i> datos — pero <b>acepta</b> los bloques con datos
  de otros y sigue en la cadena spam. Por <b>consenso</b>: adopta RDTS (se vuelve Knots),
  <b>rechaza</b> los bloques con datos y pasa su hashpower a la cadena limpia. Partimos de la
  base de sim-2 (Core 78% / Knots 22%) y vamos adoptando mineros Core — <b>el mismo hashpower en
  ambos modos</b>.</p>
  <div class="versions">
    <span class="chip"><b>Core</b> 31.1</span>
    <span class="chip"><b>Knots</b> v29.3.knots20260508</span>
    <span class="chip">__TOTAL__ corridas · regtest</span>
  </div>

  <div class="grid">__STATS__</div>

  <div class="card">
    <h2>Probabilidad de que gane el softfork, según el hashpower Core que adopta</h2>
    <p class="sub">Eje horizontal: hashpower de los mineros Core que "adoptan" (de 0% a 78%, todo Core).
    <b>Consenso</b> (se vuelven Knots): cada adopción mueve hashpower al bando limpio → gana al cruzar
    la mayoría. <b>Policy</b> (siguen Core, no spamean): no mueve hashpower de bando → solo sirve
    cuando adoptan casi todos los que producían spam.</p>
    <div class="chart-wrap" id="w1"><svg id="c1" viewBox="0 0 800 340" preserveAspectRatio="xMidYMid meet"></svg><div class="tooltip" id="t1"></div></div>
    <div class="legend">
      <span><span class="sw" style="background:var(--consensus)"></span>Consenso (adopta RDTS → Knots)</span>
      <span><span class="sw" style="background:var(--policy)"></span>Policy (Core, deja de spamear)</span>
    </div>
  </div>

  <div class="card">
    <h2>Datos</h2>
    <div class="chart-wrap"><table><thead><tr>
      <th>Hashpower adoptado</th><th class="num">Consenso: gana</th><th class="num">Policy: gana</th>
      <th class="num">Knots share (consenso)</th><th class="num">Knots share (policy)</th>
    </tr></thead><tbody id="tb"></tbody></table></div>
  </div>

  <p class="foot">
    <b>No son equivalentes.</b> Adoptar por <b>consenso</b> gana con una <b>mayoría</b> de hashpower
    (cada minero convertido pasa al bando limpio y, al cruzar ~50%, la cadena limpia se impone).
    Adoptar por <b>policy</b> exige <b>casi unanimidad</b>: mientras UN minero siga metiendo datos,
    la cadena Core queda contaminada y Knots la rechaza; los bloques "limpios" de los Core-policy se
    apilan sobre esa cadena spam, así que no ayudan. La policy solo hace converger cuando <b>nadie</b>
    produce spam.<br><br>
    <b>Por qué.</b> La <b>policy</b> es relay/mempool: cambia lo que un nodo produce y relaya, no qué
    bloques acepta. El <b>consenso</b> (RDTS) cambia la validez: hace que el nodo <b>rechace</b> la
    cadena spam. Solo el consenso mueve a un nodo de bando. Además, en la práctica <b>no se puede
    enforzar RDTS corriendo Core</b> — la regla solo existe en Knots; "adoptar por consenso" es,
    literalmente, pasarse a Knots.<br><br>
    <b>Honestidad.</b> regtest, sin comisiones ni latencia real; pocas corridas por punto. Muestra
    el mecanismo (policy ≠ consenso), no una predicción cuantitativa de la red.
  </p>
</div>
<script>
const ROWS=__DATA__.rows;
const cssv=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function E(t,a){const e=document.createElementNS('http://www.w3.org/2000/svg',t);for(const k in a)e.setAttribute(k,a[k]);return e;}
function draw(){
  const svg=document.getElementById('c1');svg.innerHTML='';const W=800,H=340,mL=52,mR=20,mT=16,mB=44,iw=W-mL-mR,ih=H-mT-mB;
  const cons=cssv('--consensus'),pol=cssv('--policy'),hair=cssv('--hair'),muted=cssv('--muted'),ref=cssv('--ref');
  const XMAX=Math.max(...ROWS.map(r=>r.adopted_hp))*100;
  const xs=hp=>mL+(hp*100/XMAX)*iw, ys=p=>mT+(1-p)*ih;
  for(let i=0;i<=5;i++){const y=ys(i/5);svg.appendChild(E('line',{x1:mL,y1:y,x2:W-mR,y2:y,stroke:hair,'stroke-width':1}));
    const t=E('text',{x:mL-9,y:y+4,'text-anchor':'end',fill:muted,'font-size':11,'font-family':'ui-monospace,Menlo,monospace'});t.textContent=(i*20)+'%';svg.appendChild(t);}
  ROWS.forEach(r=>{const t=E('text',{x:xs(r.adopted_hp),y:H-mB+20,'text-anchor':'middle',fill:muted,'font-size':11,'font-family':'ui-monospace,Menlo,monospace'});t.textContent=(r.adopted_hp*100).toFixed(0)+'%';svg.appendChild(t);});
  const xl=E('text',{x:mL+iw/2,y:H-4,'text-anchor':'middle',fill:muted,'font-size':12});xl.textContent='Hashpower Core que adopta (%)';svg.appendChild(xl);
  // referencia 50% del hashpower total (mayoría): Knots base 22% + adoptado = 50% => adoptado 28%
  const majX=xs(0.28);svg.appendChild(E('line',{x1:majX,y1:mT,x2:majX,y2:mT+ih,stroke:ref,'stroke-width':1.4,'stroke-dasharray':'5 4'}));
  const ml=E('text',{x:majX+5,y:mT+12,fill:ref,'font-size':10.5});ml.textContent='Knots llega a 50% del hashpower';svg.appendChild(ml);
  const line=(key,color)=>{const pts=ROWS.filter(r=>r[key]!==undefined);if(!pts.length)return;
    svg.appendChild(E('path',{d:'M'+pts.map(r=>`${xs(r.adopted_hp)},${ys(r[key])}`).join(' L'),fill:'none',stroke:color,'stroke-width':2.6,'stroke-linejoin':'round'}));
    pts.forEach(r=>svg.appendChild(E('circle',{cx:xs(r.adopted_hp),cy:ys(r[key]),r:3.8,fill:color,stroke:cssv('--card'),'stroke-width':1.3})));};
  line('consensus_win',cons);line('policy_win',pol);
  const tt=document.getElementById('t1');
  svg.addEventListener('pointermove',ev=>{const rc=svg.getBoundingClientRect();const px=(ev.clientX-rc.left)/rc.width*W;
    let b=ROWS[0],bd=1e9;ROWS.forEach(r=>{const d=Math.abs(xs(r.adopted_hp)-px);if(d<bd){bd=d;b=r;}});tt.style.opacity=1;
    const f=x=>x===undefined?'-':`${(x*100).toFixed(0)}%`;
    tt.innerHTML=`<div class="tt-n">${(b.adopted_hp*100).toFixed(0)}% del hashpower adopta</div>`+
      `<div class="tt-row"><span>Consenso: gana</span><b>${f(b.consensus_win)}</b></div>`+
      `<div class="tt-row"><span>Policy: gana</span><b>${f(b.policy_win)}</b></div>`;
    const cx=xs(b.adopted_hp)/W*rc.width;tt.style.left=Math.min(Math.max(cx-100,4),rc.width-210)+'px';tt.style.top='8px';});
  svg.addEventListener('pointerleave',()=>tt.style.opacity=0);
}
function fillTable(){document.getElementById('tb').innerHTML=ROWS.map(r=>{const f=x=>x===undefined?'-':`${(x*100).toFixed(0)}%`;
  return `<tr><td class="num">${(r.adopted_hp*100).toFixed(0)}%</td><td class="num">${f(r.consensus_win)}</td>`+
    `<td class="num">${f(r.policy_win)}</td><td class="num">${f(r.consensus_knots)}</td><td class="num">${f(r.policy_knots)}</td></tr>`;}).join('');}
function render(){draw();fillTable();}
render();
new MutationObserver(render).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
window.matchMedia('(prefers-color-scheme:dark)').addEventListener('change',render);
window.addEventListener('resize',()=>{clearTimeout(window._r);window._r=setTimeout(render,150);});
</script>
"""


if __name__ == "__main__":
    build()
