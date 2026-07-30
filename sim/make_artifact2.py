"""Genera results/report2.html: dashboard interactivo de sim-2 (hashpower concentrado).
Curva P(el softfork gana) + "bloques que tira Core" (pico en el cruce), tema claro/oscuro.
"""

import os as _os
_ROOT = _os.environ.get("SIM_RDTS_ROOT") or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json
import math

RES = _os.path.join(_ROOT, "results")
BLOCKS = 45      # bloques por corrida
PER_DAY = 144    # bloques/día a 10 min


def build():
    with open(f"{RES}/sim2_summary.json") as f:
        rows = json.load(f)["rows"]
    total = sum(r["runs"] for r in rows)
    # frecuencia de reemplazo de la cadena de Core en tiempo real
    for r in rows:
        rpd = r["reorgs_mean"] * PER_DAY / BLOCKS
        r["reorgs_day"] = round(rpd, 2)
        r["p_ge1_day"] = round(1 - math.exp(-rpd), 3)
    incentive = next((r for r in rows if r["reorgs_day"] >= 1), None)
    inc_share = f"~{incentive['knots_share']*100:.0f}%" if incentive else "—"

    def at(share_lo, share_hi, key):
        for r in rows:
            if share_lo <= r["knots_share"] * 100 <= share_hi:
                return r[key]
        return None

    cross = next((r for r in rows if r["p_win"] >= 0.5), None)
    peak = max(rows, key=lambda r: r["disc_mean"])

    stats = [
        ("El número de nodos no manda", "16→26",
         "Knots corre en muchos más nodos que Core y aun así pierde por debajo del umbral de hashpower — lo que decide es el hashpower"),
        ("Umbral de victoria", "~57%",
         "hashpower Knots donde el softfork ya gana (Core reorganiza hacia la cadena limpia y descarta su spam)"),
        ("Core pierde ≥1 bloque/día desde", inc_share,
         "hashpower donde la cadena de Core es reemplazada al menos una vez al día (frecuencia). La lectura económica —cuánto debe pagar el dato— está en el Experimento 3"),
        ("Pico de desperdicio", f"{peak['disc_mean']:.0f} bloques",
         f"máximo de bloques que descarta Core, cerca del cruce ({peak['knots_share']*100:.0f}% del hashpower)"),
    ]
    stat_html = "\n".join(
        f'<div class="tile"><div class="tile-label">{a}</div>'
        f'<div class="tile-value">{b}</div><div class="tile-note">{c}</div></div>'
        for a, b, c in stats)

    payload = {"rows": rows}
    html = TEMPLATE.replace("__DATA__", json.dumps(payload))
    html = html.replace("__STATS__", stat_html).replace("__TOTAL__", str(total))
    out = f"{RES}/report2.html"
    with open(out, "w") as f:
        f.write(html)
    print("escrito", out, f"({len(rows)} puntos, {total} corridas)")
    return out


TEMPLATE = r"""<title>Nodos vs hashpower — sim-2 (BIP-110/RDTS)</title>
<style>
:root{
  --bg:#f4f2ec; --surface:#fffdf8; --card:#ffffff; --ink:#191c24; --muted:#6c7280;
  --hair:#e4e1d8; --core:#2f6fed; --knots:#e07b0a; --win:#1f9d57; --win-fill:rgba(31,157,87,.15);
  --discard:#d61f69; --ref:#a7abb6; --shadow:0 1px 2px rgba(20,22,30,.05),0 8px 30px rgba(20,22,30,.06);
}
@media (prefers-color-scheme:dark){:root{
  --bg:#0f1117; --surface:#161922; --card:#1a1e28; --ink:#e9ebf2; --muted:#949bad;
  --hair:#262a35; --core:#6a9bff; --knots:#f5a03d; --win:#3fca82; --win-fill:rgba(63,202,130,.16);
  --discard:#f0559b; --ref:#565d6c; --shadow:0 1px 2px rgba(0,0,0,.3),0 12px 34px rgba(0,0,0,.34);
}}
:root[data-theme="light"]{
  --bg:#f4f2ec; --surface:#fffdf8; --card:#ffffff; --ink:#191c24; --muted:#6c7280;
  --hair:#e4e1d8; --core:#2f6fed; --knots:#e07b0a; --win:#1f9d57; --win-fill:rgba(31,157,87,.15);
  --discard:#d61f69; --ref:#a7abb6; --shadow:0 1px 2px rgba(20,22,30,.05),0 8px 30px rgba(20,22,30,.06);
}
:root[data-theme="dark"]{
  --bg:#0f1117; --surface:#161922; --card:#1a1e28; --ink:#e9ebf2; --muted:#949bad;
  --hair:#262a35; --core:#6a9bff; --knots:#f5a03d; --win:#3fca82; --win-fill:rgba(63,202,130,.16);
  --discard:#f0559b; --ref:#565d6c; --shadow:0 1px 2px rgba(0,0,0,.3),0 12px 34px rgba(0,0,0,.34);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.55;-webkit-font-smoothing:antialiased;}
.wrap{max-width:940px;margin:0 auto;padding:clamp(20px,5vw,56px) clamp(16px,4vw,32px) 72px;}
.eyebrow{font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:12px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--win);font-weight:600;display:flex;gap:10px;align-items:center;}
.eyebrow::before{content:"";width:26px;height:2px;background:var(--win);display:inline-block;}
h1{font-size:clamp(28px,5.2vw,44px);line-height:1.08;margin:.5rem 0 .5rem;letter-spacing:-.02em;
  text-wrap:balance;font-weight:760;}
.lede{font-size:clamp(15px,2.2vw,18px);color:var(--muted);max-width:64ch;margin:0 0 8px;}
.lede b{color:var(--ink);font-weight:640;}
.versions{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px;}
.chip{font-family:ui-monospace,Menlo,monospace;font-size:12px;border:1px solid var(--hair);
  border-radius:999px;padding:5px 11px;color:var(--muted);background:var(--surface);}
.chip b{color:var(--ink);font-weight:600;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:34px 0;}
.tile{background:var(--card);border:1px solid var(--hair);border-radius:14px;padding:18px 18px 16px;box-shadow:var(--shadow);}
.tile-label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:600;}
.tile-value{font-family:ui-monospace,Menlo,monospace;font-size:28px;font-weight:600;margin:6px 0 4px;letter-spacing:-.02em;}
.tile-note{font-size:12.5px;color:var(--muted);line-height:1.4;}
.card{background:var(--card);border:1px solid var(--hair);border-radius:16px;box-shadow:var(--shadow);
  padding:clamp(18px,3vw,28px);margin:22px 0;}
.card h2{font-size:20px;margin:0 0 4px;letter-spacing:-.01em;}
.card .sub{color:var(--muted);font-size:14px;margin:0 0 18px;max-width:64ch;}
.chart-wrap{position:relative;width:100%;overflow-x:auto;}
svg{display:block;width:100%;height:auto;}
.legend{display:flex;gap:18px;flex-wrap:wrap;margin-top:12px;font-size:13px;color:var(--muted);}
.legend span{display:inline-flex;align-items:center;gap:7px;}
.swatch{width:16px;height:3px;border-radius:2px;display:inline-block;}
.swatch.band{width:12px;height:12px;border-radius:3px;background:var(--win-fill);border:1px solid var(--win);}
.swatch.dash{width:16px;height:0;border-top:2px dashed var(--ref);}
.swatch.bar{width:12px;height:12px;border-radius:3px;background:var(--discard);}
.tooltip{position:absolute;pointer-events:none;background:var(--card);border:1px solid var(--hair);
  border-radius:10px;padding:10px 12px;font-size:12.5px;box-shadow:var(--shadow);opacity:0;
  transition:opacity .12s;min-width:170px;z-index:5;}
.tooltip .tt-n{font-family:ui-monospace,Menlo,monospace;font-weight:600;font-size:13px;margin-bottom:5px;}
.tooltip .tt-row{display:flex;justify-content:space-between;gap:14px;color:var(--muted);}
.tooltip .tt-row b{color:var(--ink);font-variant-numeric:tabular-nums;font-family:ui-monospace,Menlo,monospace;}
table{width:100%;border-collapse:collapse;font-size:13.5px;}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--hair);}
th{font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:600;}
td.num{font-family:ui-monospace,Menlo,monospace;text-align:right;font-variant-numeric:tabular-nums;}
.dist{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:6px;}
.dist .side{border:1px solid var(--hair);border-radius:12px;padding:14px 16px;background:var(--surface);}
.dist h3{margin:0 0 8px;font-size:13px;text-transform:uppercase;letter-spacing:.05em;display:flex;gap:8px;align-items:center;}
.dist .mono{font-family:ui-monospace,Menlo,monospace;font-size:13px;color:var(--muted);line-height:1.7;}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block;}
.dot.core{background:var(--core);} .dot.knots{background:var(--knots);}
.foot{color:var(--muted);font-size:13px;margin-top:26px;line-height:1.6;}
.foot b{color:var(--ink);}
.foot code{font-family:ui-monospace,Menlo,monospace;background:var(--surface);border:1px solid var(--hair);
  padding:1px 6px;border-radius:6px;font-size:12px;color:var(--ink);}
@media(max-width:560px){.dist{grid-template-columns:1fr}}
</style>

<div class="wrap">
  <div class="eyebrow">sim-2 · hashpower concentrado · BIP-110 / RDTS</div>
  <h1>¿Importa cuántos nodos, o cuánto hashpower?</h1>
  <p class="lede">El mapa real: <b>Core concentrado</b> en pocos mineros grandes (78% del
  hashpower en 5 nodos) frente a <b>Knots disperso</b> en muchos nodos pequeños (22% en 16). Vamos
  agregando mineros Knots grandes y medimos cuándo <b>gana el softfork</b> — cuando Core
  reorganiza hacia la cadena limpia y descarta sus bloques con datos.</p>
  <div class="versions">
    <span class="chip"><b>Core</b> 31.1</span>
    <span class="chip"><b>Knots</b> v29.3.knots20260508</span>
    <span class="chip">21–30 nodos · regtest</span>
    <span class="chip">__TOTAL__ corridas Monte Carlo</span>
  </div>

  <div class="grid">__STATS__</div>

  <div class="card">
    <h2>Probabilidad de que gane el softfork, según el hashpower de Knots</h2>
    <p class="sub">"Gana" = las cadenas convergen (Core adopta la limpia; los bloques con datos
    quedan huérfanos). La línea vertical marca el 50% del hashpower. El eje horizontal es
    <b>hashpower</b>, no número de nodos.</p>
    <div class="chart-wrap" id="w1">
      <svg id="c1" viewBox="0 0 800 360" preserveAspectRatio="xMidYMid meet"></svg>
      <div class="tooltip" id="t1"></div>
    </div>
    <div class="legend">
      <span><span class="swatch" style="background:var(--win)"></span>Probabilidad de que gane el softfork</span>
      <span><span class="swatch band"></span>Intervalo de confianza del 95%</span>
      <span><span class="swatch dash"></span>50% del hashpower</span>
    </div>
  </div>

  <div class="card">
    <h2>Cuánto trabajo tira Core</h2>
    <p class="sub">Bloques con datos que Core mina y luego descarta al reorganizar hacia la
    cadena limpia (media por corrida). El desperdicio <b>pico en el cruce</b>: ahí ambas cadenas
    van parejas y se acumulan ramas largas antes de que una gane.</p>
    <div class="chart-wrap" id="w2">
      <svg id="c2" viewBox="0 0 800 260" preserveAspectRatio="xMidYMid meet"></svg>
      <div class="tooltip" id="t2"></div>
    </div>
  </div>

  <div class="card">
    <h2>Frecuencia de reemplazo de la cadena de Core</h2>
    <p class="sub">Cada reorganización = la cadena de Core (con datos) reemplazada por la limpia de
    Knots → Core pierde esos bloques. En tiempo real (1 bloque ≈ 10 minutos, 144 por día). La franja
    marca <b>≥1 reemplazo por día</b>; la línea de puntos, el 50% del hashpower. Es una <b>frecuencia</b>,
    no el incentivo económico — ese (cuánto debería pagar el dato para valer el riesgo) está en el
    <a href="sim3.html" style="color:var(--discard)">Experimento 3</a>.</p>
    <div class="chart-wrap" id="w3">
      <svg id="c3" viewBox="0 0 800 300" preserveAspectRatio="xMidYMid meet"></svg>
      <div class="tooltip" id="t3"></div>
    </div>
    <p class="split-note" style="border-left:3px solid var(--discard);padding-left:14px;margin-top:14px;color:var(--muted);font-size:13.5px;">
      Core empieza a perder <b>≥1 bloque por día</b> por reorganización desde ~38% de hashpower Knots,
      antes del umbral de victoria (~57%). Que un minero <i>reaccione</i> a esa pérdida — y si le
      conviene por policy o por consenso — se analiza en los Experimentos 3 y 5.</p>
  </div>

  <div class="card">
    <h2>El reparto de partida</h2>
    <p class="sub">21 nodos, 100% del hashpower. Se van sumando mineros Knots grandes (con pesos
    de hashpower 10, 15, … 85) hasta que Knots supera a Core.</p>
    <div class="dist">
      <div class="side"><h3><span class="dot core"></span>Core · 78% · 5 nodos</h3>
        <div class="mono">25% · 20% · 15% · 10% · 8%</div></div>
      <div class="side"><h3><span class="dot knots"></span>Knots · 22% · 16 nodos</h3>
        <div class="mono">3% ×2 · 2% ×3 · 1% ×9 · 0.5% ×2</div></div>
    </div>
  </div>

  <div class="card">
    <h2>Datos por paso</h2>
    <div class="chart-wrap">
    <table><thead><tr>
      <th>Hashpower de Knots</th><th>Nodos</th><th class="num">Gana el softfork</th>
      <th class="num">Probabilidad de ganar</th><th class="num">Bloques descartados</th>
      <th class="num">Reemplazos por día</th><th class="num">Probabilidad de ≥1 por día</th><th class="num">Profundidad del fork</th>
    </tr></thead><tbody id="tb"></tbody></table>
    </div>
  </div>

  <p class="foot">
    <b>El número de nodos no importa, solo el hashpower.</b> Es el resultado central: el cruce de
    victoria (~57%) es casi idéntico al del modelo de nodos iguales, pese a que aquí Core está
    concentrado en pocos mineros y Knots repartido en hasta 30 nodos. Tener muchos nodos Knots no
    ayuda a imponer el softfork si no llevan la minería.<br><br>
    <b>Frecuencia de reemplazo.</b> Antes del umbral de victoria, Core ya pierde bloques por
    reorganización: <b>≥1 por día desde ~38% de hashpower Knots</b>. Es una frecuencia — la
    interpretación económica (cuánto debería pagar el dato para compensar ese riesgo: premio de
    equilibrio, que cruza el 100% del premio de bloque a ~54%) está en el
    <a href="sim3.html" style="color:var(--knots)">Experimento 3</a>, y si a un minero le conviene
    reaccionar por <i>policy</i> o por <i>consenso</i>, en el
    <a href="sim5.html" style="color:var(--knots)">Experimento 5</a>.<br><br>
    <b>El desperdicio hace pico cerca del cruce.</b> Los bloques que Core tira son máximos alrededor
    del cruce (~13-14 por corrida a ~61% del hashpower) y bajan hacia los extremos: con Core dominante
    nunca cede; con Knots dominante Core reorganiza seguido pero superficial.<br><br>
    <b>Método.</b> El minero de cada bloque se elige al azar, con probabilidad proporcional a su
    hashpower; cada bloque de Core lleva datos que RDTS invalida (forzados con
    <code>generateblock</code>). Todos los nodos conectados entre sí, con <code>whitelist=noban</code>
    para que la división sea por consenso y no por desconexión. RDTS activo en Knots
    (<code>-vbparams=reduced_data:-1:…</code>).
  </p>
</div>

<script>
const ROWS = __DATA__.rows;
const cssv = n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function E(t,a){const e=document.createElementNS('http://www.w3.org/2000/svg',t);for(const k in a)e.setAttribute(k,a[k]);return e;}
const XMIN=15,XMAX=90;

function drawWin(){
  const svg=document.getElementById('c1');svg.innerHTML='';
  const W=800,H=360,mL=52,mR=20,mT=16,mB=42,iw=W-mL-mR,ih=H-mT-mB;
  const xs=s=>mL+((s-XMIN)/(XMAX-XMIN))*iw, ys=p=>mT+(1-p)*ih;
  const win=cssv('--win'),band=cssv('--win-fill'),ref=cssv('--ref'),hair=cssv('--hair'),muted=cssv('--muted');
  for(let i=0;i<=5;i++){const y=ys(i/5);svg.appendChild(E('line',{x1:mL,y1:y,x2:W-mR,y2:y,stroke:hair,'stroke-width':1}));
    const t=E('text',{x:mL-9,y:y+4,'text-anchor':'end',fill:muted,'font-size':12,'font-family':'ui-monospace,Menlo,monospace'});t.textContent=(i*20)+'%';svg.appendChild(t);}
  for(let s=20;s<=90;s+=10){const t=E('text',{x:xs(s),y:H-mB+20,'text-anchor':'middle',fill:muted,'font-size':11,'font-family':'ui-monospace,Menlo,monospace'});t.textContent=s+'%';svg.appendChild(t);}
  const xl=E('text',{x:mL+iw/2,y:H-3,'text-anchor':'middle',fill:muted,'font-size':12});xl.textContent='Hashpower de Knots (%)';svg.appendChild(xl);
  svg.appendChild(E('line',{x1:xs(50),y1:mT,x2:xs(50),y2:mT+ih,stroke:ref,'stroke-width':1.5,'stroke-dasharray':'5 4'}));
  let up='M';ROWS.forEach(r=>up+=`${xs(r.knots_share*100)},${ys(r.ci_hi)} L`);
  for(let i=ROWS.length-1;i>=0;i--){const r=ROWS[i];up+=`${xs(r.knots_share*100)},${ys(r.ci_lo)} L`;}
  svg.appendChild(E('path',{d:up.slice(0,-2)+'Z',fill:band,stroke:'none'}));
  svg.appendChild(E('path',{d:'M'+ROWS.map(r=>`${xs(r.knots_share*100)},${ys(r.p_win)}`).join(' L'),fill:'none',stroke:win,'stroke-width':2.4,'stroke-linejoin':'round'}));
  ROWS.forEach(r=>svg.appendChild(E('circle',{cx:xs(r.knots_share*100),cy:ys(r.p_win),r:3.6,fill:win,stroke:cssv('--card'),'stroke-width':1.4})));
  const tt=document.getElementById('t1');const hv=E('circle',{r:6,fill:'none',stroke:win,'stroke-width':2,opacity:0});svg.appendChild(hv);
  svg.addEventListener('pointermove',ev=>{const rc=svg.getBoundingClientRect();const px=(ev.clientX-rc.left)/rc.width*W;
    let best=ROWS[0],bd=1e9;ROWS.forEach(r=>{const d=Math.abs(xs(r.knots_share*100)-px);if(d<bd){bd=d;best=r;}});
    hv.setAttribute('cx',xs(best.knots_share*100));hv.setAttribute('cy',ys(best.p_win));hv.setAttribute('opacity',1);tt.style.opacity=1;
    tt.innerHTML=`<div class="tt-n">${(best.knots_share*100).toFixed(0)}% Knots · ${(best.core_share*100).toFixed(0)}% Core</div>`+
      `<div class="tt-row"><span>Nodos</span><b>${best.n_nodes}</b></div>`+
      `<div class="tt-row"><span>Probabilidad de ganar</span><b>${(best.p_win*100).toFixed(0)}%</b></div>`+
      `<div class="tt-row"><span>Corridas ganadas</span><b>${best.wins}/${best.runs}</b></div>`+
      `<div class="tt-row"><span>Bloques descartados</span><b>${best.disc_mean}</b></div>`;
    const cx=xs(best.knots_share*100)/W*rc.width,cy=ys(best.p_win)/H*rc.height,tw=tt.offsetWidth;
    tt.style.left=Math.min(Math.max(cx-tw/2,4),rc.width-tw-4)+'px';tt.style.top=(cy-tt.offsetHeight-14)+'px';});
  svg.addEventListener('pointerleave',()=>{tt.style.opacity=0;hv.setAttribute('opacity',0);});
}

function drawDisc(){
  const svg=document.getElementById('c2');svg.innerHTML='';
  const W=800,H=260,mL=52,mR=20,mT=14,mB=42,iw=W-mL-mR,ih=H-mT-mB;
  const maxD=Math.max(...ROWS.map(r=>r.disc_mean),1);
  const xs=s=>mL+((s-XMIN)/(XMAX-XMIN))*iw;
  const disc=cssv('--discard'),hair=cssv('--hair'),muted=cssv('--muted'),ref=cssv('--ref');
  for(let i=0;i<=4;i++){const v=maxD*i/4,y=mT+ih-(v/maxD)*ih;svg.appendChild(E('line',{x1:mL,y1:y,x2:W-mR,y2:y,stroke:hair,'stroke-width':1}));
    const t=E('text',{x:mL-9,y:y+4,'text-anchor':'end',fill:muted,'font-size':12,'font-family':'ui-monospace,Menlo,monospace'});t.textContent=Math.round(v);svg.appendChild(t);}
  svg.appendChild(E('line',{x1:xs(50),y1:mT,x2:xs(50),y2:mT+ih,stroke:ref,'stroke-width':1.5,'stroke-dasharray':'5 4'}));
  const bw=iw/ROWS.length*0.62;
  ROWS.forEach(r=>{const h=(r.disc_mean/maxD)*ih;svg.appendChild(E('rect',{x:xs(r.knots_share*100)-bw/2,y:mT+ih-h,width:bw,height:h,rx:3,fill:disc}));
    const t=E('text',{x:xs(r.knots_share*100),y:H-mB+20,'text-anchor':'middle',fill:muted,'font-size':11,'font-family':'ui-monospace,Menlo,monospace'});t.textContent=(r.knots_share*100).toFixed(0)+'%';svg.appendChild(t);});
  const xl=E('text',{x:mL+iw/2,y:H-3,'text-anchor':'middle',fill:muted,'font-size':12});xl.textContent='Hashpower de Knots (%)';svg.appendChild(xl);
}

function drawIncentive(){
  const svg=document.getElementById('c3');svg.innerHTML='';
  const W=800,H=300,mL=52,mR=20,mT=16,mB=42,iw=W-mL-mR,ih=H-mT-mB;
  const xs=s=>mL+((s-XMIN)/(XMAX-XMIN))*iw;
  const LO=0.1,HI=20;                       // eje vertical logarítmico (reemplazos por día)
  const ys=v=>{const t=(Math.log10(Math.max(v,LO))-Math.log10(LO))/(Math.log10(HI)-Math.log10(LO));return mT+(1-t)*ih;};
  const disc=cssv('--discard'),hair=cssv('--hair'),muted=cssv('--muted'),ref=cssv('--ref'),win=cssv('--win');
  [0.1,1,10].forEach(v=>{const y=ys(v);svg.appendChild(E('line',{x1:mL,y1:y,x2:W-mR,y2:y,stroke:hair,'stroke-width':1}));
    const t=E('text',{x:mL-9,y:y+4,'text-anchor':'end',fill:muted,'font-size':12,'font-family':'ui-monospace,Menlo,monospace'});t.textContent=v;svg.appendChild(t);});
  // franja de incentivo (al menos 1 por día)
  svg.appendChild(E('rect',{x:mL,y:mT,width:iw,height:ys(1)-mT,fill:disc,opacity:0.07}));
  svg.appendChild(E('line',{x1:mL,y1:ys(1),x2:W-mR,y2:ys(1),stroke:disc,'stroke-width':1.5,'stroke-dasharray':'2 3'}));
  const lab=E('text',{x:W-mR,y:ys(1)-6,'text-anchor':'end',fill:disc,'font-size':11});lab.textContent='≥ 1 reemplazo de cadena por día';svg.appendChild(lab);
  svg.appendChild(E('line',{x1:xs(50),y1:mT,x2:xs(50),y2:mT+ih,stroke:ref,'stroke-width':1.5,'stroke-dasharray':'5 4'}));
  for(let s=20;s<=90;s+=10){const t=E('text',{x:xs(s),y:H-mB+20,'text-anchor':'middle',fill:muted,'font-size':11,'font-family':'ui-monospace,Menlo,monospace'});t.textContent=s+'%';svg.appendChild(t);}
  const xl=E('text',{x:mL+iw/2,y:H-3,'text-anchor':'middle',fill:muted,'font-size':12});xl.textContent='Hashpower de Knots (%)';svg.appendChild(xl);
  svg.appendChild(E('path',{d:'M'+ROWS.map(r=>`${xs(r.knots_share*100)},${ys(r.reorgs_day)}`).join(' L'),fill:'none',stroke:disc,'stroke-width':2.4,'stroke-linejoin':'round'}));
  ROWS.forEach(r=>svg.appendChild(E('circle',{cx:xs(r.knots_share*100),cy:ys(r.reorgs_day),r:3.6,fill:disc,stroke:cssv('--card'),'stroke-width':1.4})));
  const tt=document.getElementById('t3');const hv=E('circle',{r:6,fill:'none',stroke:disc,'stroke-width':2,opacity:0});svg.appendChild(hv);
  svg.addEventListener('pointermove',ev=>{const rc=svg.getBoundingClientRect();const px=(ev.clientX-rc.left)/rc.width*W;
    let best=ROWS[0],bd=1e9;ROWS.forEach(r=>{const d=Math.abs(xs(r.knots_share*100)-px);if(d<bd){bd=d;best=r;}});
    hv.setAttribute('cx',xs(best.knots_share*100));hv.setAttribute('cy',ys(best.reorgs_day));hv.setAttribute('opacity',1);tt.style.opacity=1;
    tt.innerHTML=`<div class="tt-n">${(best.knots_share*100).toFixed(0)}% Knots</div>`+
      `<div class="tt-row"><span>Reemplazos por día</span><b>${best.reorgs_day}</b></div>`+
      `<div class="tt-row"><span>Probabilidad de ≥1 por día</span><b>${(best.p_ge1_day*100).toFixed(0)}%</b></div>`+
      `<div class="tt-row"><span>Gana el softfork</span><b>${(best.p_win*100).toFixed(0)}%</b></div>`;
    const cx=xs(best.knots_share*100)/W*rc.width,cy=ys(best.reorgs_day)/H*rc.height,tw=tt.offsetWidth;
    tt.style.left=Math.min(Math.max(cx-tw/2,4),rc.width-tw-4)+'px';tt.style.top=(cy-tt.offsetHeight-14)+'px';});
  svg.addEventListener('pointerleave',()=>{tt.style.opacity=0;hv.setAttribute('opacity',0);});
}

function fillTable(){
  document.getElementById('tb').innerHTML=ROWS.map(r=>
    `<tr><td class="num">${(r.knots_share*100).toFixed(0)}%</td><td class="num">${r.n_nodes}</td>`+
    `<td class="num">${r.wins}/${r.runs}</td><td class="num">${(r.p_win*100).toFixed(0)}%</td>`+
    `<td class="num">${r.disc_mean}</td>`+
    `<td class="num">${r.reorgs_day}</td><td class="num">${(r.p_ge1_day*100).toFixed(0)}%</td>`+
    `<td class="num">${r.depth_mean}</td></tr>`).join('');
}
function render(){drawWin();drawDisc();drawIncentive();fillTable();}
render();
new MutationObserver(render).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
window.matchMedia('(prefers-color-scheme:dark)').addEventListener('change',render);
window.addEventListener('resize',()=>{clearTimeout(window._r);window._r=setTimeout(render,150);});
</script>
"""


if __name__ == "__main__":
    build()
