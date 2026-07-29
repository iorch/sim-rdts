"""Genera results/report4.html: dashboard del Experimento 4 (topología de la red).
A hashpower FIJO (Core 78% disperso en 16 nodos vs Knots 22% en 4), barre la fracción de
enlaces Core-Core y muestra que el desenlace se invierte SOLO por la topología. Lee
results/topology_summary.json.
"""
import json
import os

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def build():
    with open(os.path.join(RES, "topology_summary.json")) as f:
        d = json.load(f)
    rows = sorted(d["rows"], key=lambda r: r["core_core_prob"])
    total = sum(r["runs"] for r in rows)
    # ventana del giro: entre el mayor prob con p_win==0 y el primer prob (desc) con p_win>0
    onset = max((r["core_core_prob"] for r in rows if r["p_win"] > 0), default=None)   # empieza a ganar
    last0 = min((r["core_core_prob"] for r in rows if r["p_win"] == 0), default=None)  # aún pierde
    if onset is not None and last0 is not None:
        flip_txt = f"{onset*100:.0f}–{last0*100:.0f}%"
    else:
        flip_txt = "—"
    stats = [
        ("El giro (umbral)", flip_txt,
         "ventana de fracción de enlaces Core-Core donde el subgrafo Core se desconecta y el softfork "
         "empieza a ganar — con Core en mayoría de hashpower (78%)"),
        ("Hashpower Core", "78%",
         "idéntico en todos los puntos: lo único que cambia es la topología, no el poder de cómputo"),
        ("Por qué", "el 78% no se suma",
         "sin enlaces Core-Core, Knots no retransmite los bloques con datos → los 16 mineros Core "
         "(~4.9% c/u) no comparten cadena y pierden contra el 22% de Knots coordinado"),
    ]
    stat_html = "\n".join(
        f'<div class="tile"><div class="tile-label">{a}</div>'
        f'<div class="tile-value">{b}</div><div class="tile-note">{c}</div></div>'
        for a, b, c in stats)
    html = TEMPLATE.replace("__DATA__", json.dumps({"rows": rows})).replace("__STATS__", stat_html)
    html = html.replace("__TOTAL__", str(total))
    out = os.path.join(RES, "report4.html")
    with open(out, "w") as f:
        f.write(html)
    print("escrito", out, f"({len(rows)} puntos, {total} corridas)")
    return out


TEMPLATE = r"""<title>Cuando la topología importa — sim-rdts (BIP-110/RDTS)</title>
<style>
:root{--bg:#f4f2ec;--surface:#fffdf8;--card:#fff;--ink:#191c24;--muted:#6c7280;--hair:#e4e1d8;
  --topo:#0d9488;--core:#2f6fed;--knots:#e07b0a;--ref:#a7abb6;--shadow:0 1px 2px rgba(20,22,30,.05),0 8px 30px rgba(20,22,30,.06);}
@media (prefers-color-scheme:dark){:root{--bg:#0f1117;--surface:#161922;--card:#1a1e28;--ink:#e9ebf2;--muted:#949bad;
  --hair:#262a35;--topo:#2dd4bf;--core:#6a9bff;--knots:#f5a03d;--ref:#565d6c;--shadow:0 1px 2px rgba(0,0,0,.3),0 12px 34px rgba(0,0,0,.34);}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased;}
.wrap{max-width:940px;margin:0 auto;padding:clamp(20px,5vw,56px) clamp(16px,4vw,32px) 72px;}
.back{font-family:ui-monospace,Menlo,monospace;font-size:13px;color:var(--topo);text-decoration:none;} .back:hover{text-decoration:underline;}
.eyebrow{font-family:ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--topo);font-weight:600;display:flex;gap:10px;align-items:center;margin-top:10px;}
.eyebrow::before{content:"";width:26px;height:2px;background:var(--topo);display:inline-block;}
h1{font-size:clamp(28px,5.2vw,44px);line-height:1.08;margin:.5rem 0;letter-spacing:-.02em;text-wrap:balance;font-weight:760;}
.lede{font-size:clamp(15px,2.2vw,18px);color:var(--muted);max-width:64ch;margin:0 0 8px;} .lede b{color:var(--ink);}
.versions{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px;}
.chip{font-family:ui-monospace,Menlo,monospace;font-size:12px;border:1px solid var(--hair);border-radius:999px;padding:5px 11px;color:var(--muted);background:var(--surface);}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin:32px 0;}
.tile{background:var(--card);border:1px solid var(--hair);border-radius:14px;padding:18px;box-shadow:var(--shadow);}
.tile-label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:600;}
.tile-value{font-family:ui-monospace,Menlo,monospace;font-size:22px;font-weight:600;margin:6px 0 4px;letter-spacing:-.02em;}
.tile-note{font-size:12.5px;color:var(--muted);line-height:1.4;}
.card{background:var(--card);border:1px solid var(--hair);border-radius:16px;box-shadow:var(--shadow);padding:clamp(18px,3vw,28px);margin:22px 0;}
.card h2{font-size:20px;margin:0 0 4px;letter-spacing:-.01em;} .card .sub{color:var(--muted);font-size:14px;margin:0 0 18px;max-width:64ch;}
.chart-wrap{position:relative;width:100%;overflow-x:auto;} svg{display:block;width:100%;height:auto;}
.legend{display:flex;gap:18px;flex-wrap:wrap;margin-top:12px;font-size:13px;color:var(--muted);}
.legend span{display:inline-flex;align-items:center;gap:7px;} .sw{width:16px;height:3px;border-radius:2px;display:inline-block;}
.tooltip{position:absolute;pointer-events:none;background:var(--card);border:1px solid var(--hair);border-radius:10px;padding:10px 12px;font-size:12.5px;box-shadow:var(--shadow);opacity:0;transition:opacity .12s;min-width:180px;z-index:5;}
.tooltip .tt-n{font-family:ui-monospace,Menlo,monospace;font-weight:600;font-size:13px;margin-bottom:5px;} .tooltip .tt-row{display:flex;justify-content:space-between;gap:14px;color:var(--muted);} .tooltip .tt-row b{color:var(--ink);font-family:ui-monospace,Menlo,monospace;}
table{width:100%;border-collapse:collapse;font-size:13.5px;} th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--hair);}
th{font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:600;} td.num{font-family:ui-monospace,Menlo,monospace;text-align:right;font-variant-numeric:tabular-nums;}
.foot{color:var(--muted);font-size:13px;margin-top:26px;line-height:1.6;} .foot b{color:var(--ink);}
.foot code{font-family:ui-monospace,Menlo,monospace;background:var(--surface);border:1px solid var(--hair);padding:1px 6px;border-radius:6px;font-size:12px;color:var(--ink);}
</style>
<div class="wrap">
  <a class="back" href="index.html">← volver a las simulaciones</a>
  <div class="eyebrow">Experimento 4 · topología de la red</div>
  <h1>Cuando la topología importa más que el hashpower</h1>
  <p class="lede">Knots <b>no retransmite</b> los bloques que RDTS invalida. Si los mineros Core
  dependen de retransmitirse sus bloques con datos entre sí, y esa retransmisión pasa por nodos
  Knots que la bloquean, la minería Core se <b>fragmenta</b>. Aquí el hashpower es fijo —
  <b>Core 78%</b> disperso en 16 nodos, Knots 22% en 4— y lo único que se mueve es la fracción de
  enlaces Core-Core. El desenlace se invierte solo por eso.</p>
  <div class="versions">
    <span class="chip"><b>Core</b> 78% · 16 nodos</span>
    <span class="chip"><b>Knots</b> 22% · 4 nodos</span>
    <span class="chip">__TOTAL__ corridas · regtest</span>
  </div>

  <div class="grid">__STATS__</div>

  <div class="card">
    <h2>Probabilidad de que gane el softfork, según la conectividad de Core</h2>
    <p class="sub">Eje horizontal: fracción de enlaces Core-Core presentes (100% = malla completa,
    0% = cada Core conectado solo a través de nodos Knots). El hashpower NO cambia. El giro ocurre
    cuando el subgrafo Core se <b>desconecta</b> (umbral de percolación), no a un porcentaje fijo.</p>
    <div class="chart-wrap" id="w1"><svg id="c1" viewBox="0 0 800 320" preserveAspectRatio="xMidYMid meet"></svg><div class="tooltip" id="t1"></div></div>
  </div>

  <div class="card">
    <h2>La cadena de Core colapsa cuando se fragmenta</h2>
    <p class="sub">Altura media de la cadena de cada bando al final de la corrida. Con enlaces, la
    cadena de Core (78%) domina; al cortarlos, su hashpower deja de sumarse y su cadena cae hasta
    encontrarse con la de Knots (que crece coordinada al 22%).</p>
    <div class="chart-wrap" id="w2"><svg id="c2" viewBox="0 0 800 300" preserveAspectRatio="xMidYMid meet"></svg><div class="tooltip" id="t2"></div></div>
    <div class="legend">
      <span><span class="sw" style="background:var(--core)"></span>Cadena de Core (78% hashpower)</span>
      <span><span class="sw" style="background:var(--knots)"></span>Cadena de Knots (22% hashpower)</span>
    </div>
  </div>

  <div class="card">
    <h2>Datos</h2>
    <div class="chart-wrap"><table><thead><tr>
      <th>Enlaces Core-Core</th><th class="num">Corridas</th><th class="num">Gana el softfork</th>
      <th class="num">Probabilidad</th><th class="num">Altura cadena Core</th><th class="num">Altura cadena Knots</th>
    </tr></thead><tbody id="tb"></tbody></table></div>
  </div>

  <p class="foot">
    <b>La lección.</b> El hashpower solo cuenta si se puede <b>sumar</b> sobre una misma cadena. Con
    Core disperso y desconectado, su 78% se desmenuza en 16 fuerzas de ~4.9% que no comparten cadena;
    ninguna, sola, le gana al 22% de Knots coordinado. Por eso una <b>mayoría de hashpower puede perder
    por topología</b>: el bando que rechaza el spam (Knots), si está bien conectado, actúa como un
    cortafuegos que impide a los mineros de spam construir una cadena común.<br><br>
    <b>El matiz.</b> No es tener "todos" los enlaces: basta con que el subgrafo Core quede
    <b>conectado</b> (por encima del umbral de percolación, ~17% para 16 nodos) para que el spam se
    propague por caminos indirectos y Core gane. Y el efecto necesita hashpower <b>disperso</b>: un
    solo pool grande (&gt; 22%) extiende su propia cadena sin depender de nadie y es inmune.<br><br>
    <b>Honestidad.</b> Es regtest, sin latencia real ni comisiones; la topología está idealizada
    (Core conectado solo vía Knots es un caso extremo). Muestra el mecanismo, no una predicción de la red real.
  </p>
</div>
<script>
const ROWS=__DATA__.rows;
const cssv=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function E(t,a){const e=document.createElementNS('http://www.w3.org/2000/svg',t);for(const k in a)e.setAttribute(k,a[k]);return e;}
const xs=(p,mL,iw)=>mL+p*iw;   // p in [0,1] = fracción de enlaces
function axisX(svg,W,H,mL,mB,iw){const muted=cssv('--muted');
  for(let k=0;k<=5;k++){const p=k/5;const t=E('text',{x:mL+p*iw,y:H-mB+20,'text-anchor':'middle',fill:muted,'font-size':11,'font-family':'ui-monospace,Menlo,monospace'});t.textContent=(p*100)+'%';svg.appendChild(t);}
  const xl=E('text',{x:mL+iw/2,y:H-3,'text-anchor':'middle',fill:muted,'font-size':12});xl.textContent='Fracción de enlaces Core-Core';svg.appendChild(xl);}

function drawWin(){
  const svg=document.getElementById('c1');svg.innerHTML='';const W=800,H=320,mL=52,mR=20,mT=16,mB=42,iw=W-mL-mR,ih=H-mT-mB;
  const topo=cssv('--topo'),hair=cssv('--hair'),muted=cssv('--muted');const ys=v=>mT+(1-v)*ih;
  for(let i=0;i<=5;i++){const y=ys(i/5);svg.appendChild(E('line',{x1:mL,y1:y,x2:W-mR,y2:y,stroke:hair,'stroke-width':1}));
    const t=E('text',{x:mL-9,y:y+4,'text-anchor':'end',fill:muted,'font-size':11,'font-family':'ui-monospace,Menlo,monospace'});t.textContent=(i*20)+'%';svg.appendChild(t);}
  axisX(svg,W,H,mL,mB,iw);
  svg.appendChild(E('path',{d:'M'+ROWS.map(r=>`${xs(r.core_core_prob,mL,iw)},${ys(r.p_win)}`).join(' L'),fill:'none',stroke:topo,'stroke-width':2.4,'stroke-linejoin':'round'}));
  ROWS.forEach(r=>svg.appendChild(E('circle',{cx:xs(r.core_core_prob,mL,iw),cy:ys(r.p_win),r:3.8,fill:topo,stroke:cssv('--card'),'stroke-width':1.3})));
  const tt=document.getElementById('t1');
  svg.addEventListener('pointermove',ev=>{const rc=svg.getBoundingClientRect();const px=(ev.clientX-rc.left)/rc.width*W;
    let b=ROWS[0],bd=1e9;ROWS.forEach(r=>{const d=Math.abs(xs(r.core_core_prob,mL,iw)-px);if(d<bd){bd=d;b=r;}});tt.style.opacity=1;
    tt.innerHTML=`<div class="tt-n">${(b.core_core_prob*100).toFixed(0)}% enlaces Core-Core</div>`+
      `<div class="tt-row"><span>Gana softfork</span><b>${b.softfork_wins}/${b.runs}</b></div>`+
      `<div class="tt-row"><span>Probabilidad</span><b>${(b.p_win*100).toFixed(0)}%</b></div>`;
    const cx=xs(b.core_core_prob,mL,iw)/W*rc.width;tt.style.left=Math.min(Math.max(cx-90,4),rc.width-190)+'px';tt.style.top='8px';});
  svg.addEventListener('pointerleave',()=>tt.style.opacity=0);
}

function drawHeights(){
  const svg=document.getElementById('c2');svg.innerHTML='';const W=800,H=300,mL=52,mR=20,mT=16,mB=42,iw=W-mL-mR,ih=H-mT-mB;
  const core=cssv('--core'),knots=cssv('--knots'),hair=cssv('--hair'),muted=cssv('--muted');
  const vals=ROWS.flatMap(r=>[r.core_h,r.knots_h]);const lo=Math.min(...vals)*0.96,hi=Math.max(...vals)*1.02;
  const ys=v=>mT+(1-(v-lo)/(hi-lo))*ih;
  for(let i=0;i<=4;i++){const v=lo+(hi-lo)*i/4,y=ys(v);svg.appendChild(E('line',{x1:mL,y1:y,x2:W-mR,y2:y,stroke:hair,'stroke-width':1}));
    const t=E('text',{x:mL-9,y:y+4,'text-anchor':'end',fill:muted,'font-size':11,'font-family':'ui-monospace,Menlo,monospace'});t.textContent=Math.round(v);svg.appendChild(t);}
  axisX(svg,W,H,mL,mB,iw);
  [['core_h',core],['knots_h',knots]].forEach(([k,c])=>{
    svg.appendChild(E('path',{d:'M'+ROWS.map(r=>`${xs(r.core_core_prob,mL,iw)},${ys(r[k])}`).join(' L'),fill:'none',stroke:c,'stroke-width':2.4,'stroke-linejoin':'round'}));
    ROWS.forEach(r=>svg.appendChild(E('circle',{cx:xs(r.core_core_prob,mL,iw),cy:ys(r[k]),r:3.4,fill:c,stroke:cssv('--card'),'stroke-width':1.2})));});
  const tt=document.getElementById('t2');
  svg.addEventListener('pointermove',ev=>{const rc=svg.getBoundingClientRect();const px=(ev.clientX-rc.left)/rc.width*W;
    let b=ROWS[0],bd=1e9;ROWS.forEach(r=>{const d=Math.abs(xs(r.core_core_prob,mL,iw)-px);if(d<bd){bd=d;b=r;}});tt.style.opacity=1;
    tt.innerHTML=`<div class="tt-n">${(b.core_core_prob*100).toFixed(0)}% enlaces Core-Core</div>`+
      `<div class="tt-row"><span>Cadena Core</span><b>${b.core_h}</b></div>`+
      `<div class="tt-row"><span>Cadena Knots</span><b>${b.knots_h}</b></div>`;
    const cx=xs(b.core_core_prob,mL,iw)/W*rc.width;tt.style.left=Math.min(Math.max(cx-90,4),rc.width-190)+'px';tt.style.top='8px';});
  svg.addEventListener('pointerleave',()=>tt.style.opacity=0);
}

function fillTable(){document.getElementById('tb').innerHTML=ROWS.slice().reverse().map(r=>
  `<tr><td class="num">${(r.core_core_prob*100).toFixed(0)}%</td><td class="num">${r.runs}</td>`+
  `<td class="num">${r.softfork_wins}/${r.runs}</td><td class="num">${(r.p_win*100).toFixed(0)}%</td>`+
  `<td class="num">${r.core_h}</td><td class="num">${r.knots_h}</td></tr>`).join('');}
function render(){drawWin();drawHeights();fillTable();}
render();
new MutationObserver(render).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
window.matchMedia('(prefers-color-scheme:dark)').addEventListener('change',render);
window.addEventListener('resize',()=>{clearTimeout(window._r);window._r=setTimeout(render,150);});
</script>
"""


if __name__ == "__main__":
    build()
