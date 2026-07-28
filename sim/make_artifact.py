"""Genera results/report.html: dashboard interactivo autocontenido a partir de summary.json.
Gráfico SVG dibujado en JS (hover con tooltip), tema claro/oscuro. Sin dependencias externas.
"""

import os as _os
_ROOT = _os.environ.get("SIM_RDTS_ROOT") or _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
import json
import os

RES = _os.path.join(_ROOT, "results")


def build():
    with open(f"{RES}/summary.json") as f:
        summary = json.load(f)
    rows = summary["rows"]
    threshold = summary["threshold"]
    total_runs = sum(r["runs"] for r in rows)

    def at(n, key, default=None):
        for r in rows:
            if r["n_knots"] == n:
                return r[key]
        return default

    cross = next((r["n_knots"] for r in rows if r["p_fork"] < 0.5), None)
    max_depth = max((r["mean_depth"] for r in rows), default=0)
    payload = {"rows": rows, "threshold": threshold}

    stats = [
        ("Corridas totales", f"{total_runs}", "20 nodos regtest · minero uniforme por bloque"),
        ("Umbral de cruce", (f"N ≈ {cross}" if cross else "—"),
         "P(fork) baja de 50% en ~55% del hashpower — algo por encima del 50% naive"),
        ("P(fork) · 1 Knots", f"{at(1,'p_fork',0)*100:.0f}%", "un solo nodo Knots contra 19 Core"),
        ("P(fork) · 19 Knots", f"{at(19,'p_fork',0)*100:.0f}%", "Knots mayoría: el softfork se impone"),
    ]
    stat_html = "\n".join(
        f'<div class="tile"><div class="tile-label">{lbl}</div>'
        f'<div class="tile-value">{val}</div>'
        f'<div class="tile-note">{note}</div></div>'
        for lbl, val, note in stats)

    rules = [
        ("OP_RETURN &gt; 83 bytes", "regla 1 · scriptPubKey de datos",
         "acepta y relaya", "bad-txns-vout-script-toolarge"),
        ("Item de witness &gt; 256 bytes", "regla 2 · push de datos (inscripción)",
         "acepta (&lt; 520 B)", "Push value size limit exceeded"),
        ("scriptPubKey no-OP_RETURN &gt; 34 B", "regla 1", "acepta", "rechaza"),
        ("Taproot annex / OP_SUCCESS / OP_IF en tapscript", "reglas 4·6·7", "acepta", "rechaza"),
    ]
    rule_html = "\n".join(
        f'<tr><td class="rule">{r0}<span class="rule-sub">{r1}</span></td>'
        f'<td class="verdict ok"><span class="dot core"></span>{r2}</td>'
        f'<td class="verdict bad"><span class="dot knots"></span><code>{r3}</code></td></tr>'
        for r0, r1, r2, r3 in rules)

    html = TEMPLATE.replace("__DATA__", json.dumps(payload))
    html = html.replace("__STATS__", stat_html).replace("__RULES__", rule_html)
    html = html.replace("__THRESHOLD__", str(threshold)).replace("__TOTAL__", str(total_runs))
    out = f"{RES}/report.html"
    with open(out, "w") as f:
        f.write(html)
    print("escrito", out, f"({len(rows)} puntos, {total_runs} corridas)")
    return out


TEMPLATE = r"""<title>Fork Core vs Knots — BIP-110 / RDTS</title>
<style>
:root{
  --bg:#f4f2ec; --surface:#fffdf8; --card:#ffffff; --ink:#191c24; --muted:#6c7280;
  --hair:#e4e1d8; --core:#2f6fed; --knots:#e07b0a; --fork:#d61f69; --fork-fill:rgba(214,31,105,.14);
  --depth:#7a4de0; --ref:#a7abb6; --ok:#2f9e5f; --shadow:0 1px 2px rgba(20,22,30,.05),0 8px 30px rgba(20,22,30,.06);
}
@media (prefers-color-scheme:dark){:root{
  --bg:#0f1117; --surface:#161922; --card:#1a1e28; --ink:#e9ebf2; --muted:#949bad;
  --hair:#262a35; --core:#6a9bff; --knots:#f5a03d; --fork:#f0559b; --fork-fill:rgba(240,85,155,.17);
  --depth:#a684ff; --ref:#565d6c; --ok:#48c986; --shadow:0 1px 2px rgba(0,0,0,.3),0 12px 34px rgba(0,0,0,.34);
}}
:root[data-theme="light"]{
  --bg:#f4f2ec; --surface:#fffdf8; --card:#ffffff; --ink:#191c24; --muted:#6c7280;
  --hair:#e4e1d8; --core:#2f6fed; --knots:#e07b0a; --fork:#d61f69; --fork-fill:rgba(214,31,105,.14);
  --depth:#7a4de0; --ref:#a7abb6; --ok:#2f9e5f; --shadow:0 1px 2px rgba(20,22,30,.05),0 8px 30px rgba(20,22,30,.06);
}
:root[data-theme="dark"]{
  --bg:#0f1117; --surface:#161922; --card:#1a1e28; --ink:#e9ebf2; --muted:#949bad;
  --hair:#262a35; --core:#6a9bff; --knots:#f5a03d; --fork:#f0559b; --fork-fill:rgba(240,85,155,.17);
  --depth:#a684ff; --ref:#565d6c; --ok:#48c986; --shadow:0 1px 2px rgba(0,0,0,.3),0 12px 34px rgba(0,0,0,.34);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.55;-webkit-font-smoothing:antialiased;}
.mono{font-family:ui-monospace,"SF Mono",SFMono-Regular,Menlo,Consolas,monospace;}
.wrap{max-width:940px;margin:0 auto;padding:clamp(20px,5vw,56px) clamp(16px,4vw,32px) 72px;}
.eyebrow{font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:12px;letter-spacing:.14em;
  text-transform:uppercase;color:var(--fork);font-weight:600;display:flex;gap:10px;align-items:center;}
.eyebrow::before{content:"";width:26px;height:2px;background:var(--fork);display:inline-block;}
h1{font-size:clamp(28px,5.2vw,44px);line-height:1.08;margin:.5rem 0 .5rem;letter-spacing:-.02em;
  text-wrap:balance;font-weight:760;}
.lede{font-size:clamp(15px,2.2vw,18px);color:var(--muted);max-width:64ch;margin:0 0 8px;}
.lede b{color:var(--ink);font-weight:640;}
.versions{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px;}
.chip{font-family:ui-monospace,Menlo,monospace;font-size:12px;border:1px solid var(--hair);
  border-radius:999px;padding:5px 11px;color:var(--muted);background:var(--surface);}
.chip b{color:var(--ink);font-weight:600;}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin:34px 0;}
.tile{background:var(--card);border:1px solid var(--hair);border-radius:14px;padding:18px 18px 16px;
  box-shadow:var(--shadow);}
.tile-label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:600;}
.tile-value{font-family:ui-monospace,Menlo,monospace;font-size:30px;font-weight:600;margin:6px 0 4px;
  letter-spacing:-.02em;font-variant-numeric:tabular-nums;}
.tile-note{font-size:12.5px;color:var(--muted);line-height:1.4;}
.card{background:var(--card);border:1px solid var(--hair);border-radius:16px;box-shadow:var(--shadow);
  padding:clamp(18px,3vw,28px);margin:22px 0;}
.card h2{font-size:20px;margin:0 0 4px;letter-spacing:-.01em;}
.card .sub{color:var(--muted);font-size:14px;margin:0 0 18px;max-width:62ch;}
.chart-wrap{position:relative;width:100%;overflow-x:auto;}
svg{display:block;width:100%;height:auto;}
.legend{display:flex;gap:18px;flex-wrap:wrap;margin-top:12px;font-size:13px;color:var(--muted);}
.legend span{display:inline-flex;align-items:center;gap:7px;}
.swatch{width:12px;height:12px;border-radius:3px;display:inline-block;}
.swatch.line{width:16px;height:3px;border-radius:2px;}
.swatch.band{background:var(--fork-fill);border:1px solid var(--fork);}
.swatch.dash{width:16px;height:0;border-top:2px dashed var(--ref);}
.tooltip{position:absolute;pointer-events:none;background:var(--card);border:1px solid var(--hair);
  border-radius:10px;padding:10px 12px;font-size:12.5px;box-shadow:var(--shadow);opacity:0;
  transition:opacity .12s;min-width:150px;z-index:5;}
.tooltip .tt-n{font-family:ui-monospace,Menlo,monospace;font-weight:600;font-size:13px;margin-bottom:5px;}
.tooltip .tt-row{display:flex;justify-content:space-between;gap:14px;color:var(--muted);}
.tooltip .tt-row b{color:var(--ink);font-variant-numeric:tabular-nums;font-family:ui-monospace,Menlo,monospace;}
table{width:100%;border-collapse:collapse;font-size:13.5px;}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--hair);vertical-align:top;}
th{font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:600;}
td.num{font-family:ui-monospace,Menlo,monospace;text-align:right;font-variant-numeric:tabular-nums;}
.rule{font-weight:560;}
.rule-sub{display:block;font-size:11.5px;color:var(--muted);font-weight:400;margin-top:2px;font-family:ui-monospace,Menlo,monospace;}
.verdict{font-size:12.5px;white-space:nowrap;}
.verdict code{font-size:11.5px;background:transparent;color:var(--knots);}
.verdict.ok{color:var(--ok);}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px;vertical-align:middle;}
.dot.core{background:var(--core);} .dot.knots{background:var(--knots);}
.barcell{position:relative;}
.bar{height:7px;border-radius:4px;background:var(--depth);display:inline-block;vertical-align:middle;}
.foot{color:var(--muted);font-size:13px;margin-top:26px;line-height:1.6;}
.foot code{font-family:ui-monospace,Menlo,monospace;background:var(--surface);border:1px solid var(--hair);
  padding:1px 6px;border-radius:6px;font-size:12px;color:var(--ink);}
.split-note{border-left:3px solid var(--fork);padding-left:14px;margin:8px 0 0;color:var(--muted);font-size:13.5px;}
</style>

<div class="wrap">
  <div class="eyebrow">BIP-110 / RDTS · simulación regtest</div>
  <h1>¿Cuándo se parte la cadena entre Core y Knots?</h1>
  <p class="lede"><b>Bitcoin Knots</b> aplica el softfork RDTS y rechaza por consenso las
  transacciones con datos grandes; <b>Bitcoin Core</b> no lo conoce y las mina. Cada bloque
  con datos que Core produce es <b>válido para Core, inválido para Knots</b> → la cadena
  puede partirse. Esto mide la probabilidad de ese fork según cuánta minería corre Knots.</p>
  <div class="versions">
    <span class="chip"><b>Core</b> 31.1</span>
    <span class="chip"><b>Knots</b> v29.3.knots20260508</span>
    <span class="chip">20 nodos · regtest</span>
    <span class="chip">__TOTAL__ corridas Monte Carlo</span>
    <span class="chip">fork ≥ __THRESHOLD__ bloques</span>
  </div>

  <div class="grid">__STATS__</div>

  <div class="card">
    <h2>Probabilidad de fork persistente</h2>
    <p class="sub">Cada punto: fracción de corridas que terminan con las cadenas Core y Knots
    divergiendo ≥ __THRESHOLD__ bloques. Banda = intervalo de confianza 95% (Wilson).
    La línea vertical marca 50% del hashpower (10 Knots / 10 Core).</p>
    <div class="chart-wrap" id="probwrap">
      <svg id="probchart" viewBox="0 0 800 380" preserveAspectRatio="xMidYMid meet"></svg>
      <div class="tooltip" id="tt"></div>
    </div>
    <div class="legend">
      <span><span class="swatch line" style="background:var(--fork)"></span>P(fork)</span>
      <span><span class="swatch band"></span>IC 95%</span>
      <span><span class="swatch dash"></span>50% hashpower</span>
    </div>
  </div>

  <div class="card">
    <h2>Profundidad del split</h2>
    <p class="sub">Bloques que separan la cadena de Knots de la de Core al final de la corrida
    (promedio). Cuanto más profundo, más irreversible el fork.</p>
    <div class="chart-wrap" id="depthwrap">
      <svg id="depthchart" viewBox="0 0 800 240" preserveAspectRatio="xMidYMid meet"></svg>
      <div class="tooltip" id="tt2"></div>
    </div>
  </div>

  <div class="card">
    <h2>Por qué se parte: la asimetría de consenso</h2>
    <p class="sub">RDTS añade reglas que solo Knots aplica. Estas transacciones se inyectan en
    los bloques que mina Core (forzadas con <code style="font-size:12px">generateblock</code>):</p>
    <table>
      <thead><tr><th>Transacción</th><th><span class="dot core"></span>Bitcoin Core 31.1</th>
      <th><span class="dot knots"></span>Bitcoin Knots (RDTS)</th></tr></thead>
      <tbody>__RULES__</tbody>
    </table>
  </div>

  <div class="card">
    <h2>Datos por proporción</h2>
    <div class="chart-wrap">
    <table id="datatable">
      <thead><tr>
        <th>Knots</th><th>Core</th><th>Hashpower</th><th class="num">Forks</th>
        <th class="num">P(fork)</th><th class="num">IC 95%</th>
        <th class="num">Prof. media</th><th>Knots gana</th>
      </tr></thead>
      <tbody id="tbody"></tbody>
    </table>
    </div>
  </div>

  <p class="foot">
    <b>Lectura.</b> RDTS es un <b>softfork</b>: no produce un split permanente si la mayoría del
    hashpower lo aplica. La simulación lo muestra — el fork persistente aparece cuando Knots es
    <b>minoría</b> (queda aislado en una cadena más corta) y desaparece cuando es <b>mayoría</b>
    (Core reorganiza hacia la cadena limpia y descarta sus bloques con datos). El cruce empírico
    está en <b>~55% del hashpower</b> (algo por encima del 50% naive): Knots necesita una leve
    supermayoría porque cada vez que su cadena limpia lidera, Core la adopta y le pone un bloque
    con datos encima, absorbiendo su ventaja. Con ≥80% del hashpower el softfork gana siempre.<br><br>
    <b>Incentivo económico.</b> Aunque el softfork solo "gana" a ~55%, Core empieza a perder
    bloques mucho antes. Contando los reemplazos de su cadena en tiempo real (1 bloque ≈ 10 min,
    144/día): con Knots al 30% del hashpower Core sufre ~0.5 reemplazos/día, al 55% ~6/día y al
    80% ~15/día. El umbral de <b>≥1 reemplazo/día</b> se cruza cerca del <b>~30% de hashpower</b> —
    muy por debajo del 55% de victoria. Es decir, una minoría del ~30% ya impone a Core una pérdida
    diaria de bloques, creando incentivo a <b>señalar RDTS</b> para dejar de perderlos (efecto
    cascada). El detalle completo, en la simulación de hashpower concentrado (sim-2).<br><br>
    <b>Método.</b> 20 nodos regtest en Docker, cada uno = 1/20 del hashpower (minero elegido
    uniforme por bloque). Malla P2P completa con <code>whitelist=noban</code> para que el split
    sea por consenso y no por desconexión. RDTS forzado activo en Knots con
    <code>-vbparams=reduced_data:-1:...</code>. En todas las corridas los nodos Core coincidieron
    entre sí y los Knots entre sí — el corte es limpio entre las dos poblaciones.
  </p>
</div>

<script>
const PAYLOAD = __DATA__;
const ROWS = PAYLOAD.rows;
const fmt = (x,d=0)=>x.toLocaleString('es',{minimumFractionDigits:d,maximumFractionDigits:d});
const cssv = n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();

function svgEl(t,a){const e=document.createElementNS('http://www.w3.org/2000/svg',t);
  for(const k in a)e.setAttribute(k,a[k]);return e;}

function drawProb(){
  const svg=document.getElementById('probchart');svg.innerHTML='';
  const W=800,H=380,mL=52,mR=20,mT=18,mB=42;
  const iw=W-mL-mR, ih=H-mT-mB;
  const xs=n=>mL+((n-1)/18)*iw, ys=p=>mT+(1-p)*ih;
  const fork=cssv('--fork'),band=cssv('--fork-fill'),ref=cssv('--ref'),hair=cssv('--hair'),muted=cssv('--muted');
  // grid + y labels
  for(let i=0;i<=5;i++){const p=i/5,y=ys(p);
    svg.appendChild(svgEl('line',{x1:mL,y1:y,x2:W-mR,y2:y,stroke:hair,'stroke-width':1}));
    const t=svgEl('text',{x:mL-9,y:y+4,'text-anchor':'end',fill:muted,'font-size':12,
      'font-family':'ui-monospace,Menlo,monospace'});t.textContent=(p*100)+'%';svg.appendChild(t);}
  // x labels
  for(let n=1;n<=19;n++){const t=svgEl('text',{x:xs(n),y:H-mB+20,'text-anchor':'middle',fill:muted,
    'font-size':11,'font-family':'ui-monospace,Menlo,monospace'});t.textContent=n;svg.appendChild(t);}
  const xlab=svgEl('text',{x:mL+iw/2,y:H-4,'text-anchor':'middle',fill:muted,'font-size':12});
  xlab.textContent='Nodos Knots (de 20)';svg.appendChild(xlab);
  // ref line at N=10
  svg.appendChild(svgEl('line',{x1:xs(10),y1:mT,x2:xs(10),y2:mT+ih,stroke:ref,'stroke-width':1.5,
    'stroke-dasharray':'5 4'}));
  // CI band
  let up='M',dn='';ROWS.forEach((r,i)=>{up+=`${xs(r.n_knots)},${ys(r.ci_hi)} `;});
  for(let i=ROWS.length-1;i>=0;i--){const r=ROWS[i];up+=`L${xs(r.n_knots)},${ys(r.ci_lo)} `;}
  svg.appendChild(svgEl('path',{d:up+'Z',fill:band,stroke:'none'}));
  // line
  let ln='M'+ROWS.map(r=>`${xs(r.n_knots)},${ys(r.p_fork)}`).join(' L');
  svg.appendChild(svgEl('path',{d:ln,fill:'none',stroke:fork,'stroke-width':2.4,'stroke-linejoin':'round'}));
  // dots
  ROWS.forEach(r=>{svg.appendChild(svgEl('circle',{cx:xs(r.n_knots),cy:ys(r.p_fork),r:3.4,
    fill:fork,stroke:cssv('--card'),'stroke-width':1.4}));});
  // hover
  const tt=document.getElementById('tt'),wrap=document.getElementById('probwrap');
  const hover=svgEl('circle',{r:6,fill:'none',stroke:fork,'stroke-width':2,opacity:0});svg.appendChild(hover);
  svg.addEventListener('pointermove',ev=>{
    const rect=svg.getBoundingClientRect();const px=(ev.clientX-rect.left)/rect.width*W;
    let n=Math.round(1+((px-mL)/iw)*18);n=Math.max(1,Math.min(19,n));
    const r=ROWS.find(x=>x.n_knots===n);if(!r){tt.style.opacity=0;return;}
    hover.setAttribute('cx',xs(n));hover.setAttribute('cy',ys(r.p_fork));hover.setAttribute('opacity',1);
    tt.style.opacity=1;
    tt.innerHTML=`<div class="tt-n">${n} Knots · ${20-n} Core</div>`+
      `<div class="tt-row"><span>Hashpower</span><b>${(r.hashpower*100).toFixed(0)}%</b></div>`+
      `<div class="tt-row"><span>P(fork)</span><b>${(r.p_fork*100).toFixed(0)}%</b></div>`+
      `<div class="tt-row"><span>IC 95%</span><b>${(r.ci_lo*100).toFixed(0)}–${(r.ci_hi*100).toFixed(0)}%</b></div>`+
      `<div class="tt-row"><span>Forks</span><b>${r.forks}/${r.runs}</b></div>`+
      `<div class="tt-row"><span>Prof. media</span><b>${r.mean_depth.toFixed(1)}</b></div>`;
    const tw=tt.offsetWidth,cx=xs(n)/W*rect.width,cy=ys(r.p_fork)/H*rect.height;
    tt.style.left=Math.min(Math.max(cx-tw/2,4),rect.width-tw-4)+'px';
    tt.style.top=(cy-tt.offsetHeight-14)+'px';
  });
  svg.addEventListener('pointerleave',()=>{tt.style.opacity=0;hover.setAttribute('opacity',0);});
}

function drawDepth(){
  const svg=document.getElementById('depthchart');svg.innerHTML='';
  const W=800,H=240,mL=52,mR=20,mT=14,mB=42,iw=W-mL-mR,ih=H-mT-mB;
  const maxD=Math.max(...ROWS.map(r=>r.mean_depth),1);
  const depth=cssv('--depth'),hair=cssv('--hair'),muted=cssv('--muted'),ref=cssv('--ref');
  const xs=n=>mL+((n-1)/18)*iw;
  for(let i=0;i<=4;i++){const v=maxD*i/4,y=mT+ih-(v/maxD)*ih;
    svg.appendChild(svgEl('line',{x1:mL,y1:y,x2:W-mR,y2:y,stroke:hair,'stroke-width':1}));
    const t=svgEl('text',{x:mL-9,y:y+4,'text-anchor':'end',fill:muted,'font-size':12,
      'font-family':'ui-monospace,Menlo,monospace'});t.textContent=Math.round(v);svg.appendChild(t);}
  svg.appendChild(svgEl('line',{x1:xs(10),y1:mT,x2:xs(10),y2:mT+ih,stroke:ref,'stroke-width':1.5,'stroke-dasharray':'5 4'}));
  const bw=iw/19*0.6;
  ROWS.forEach(r=>{const h=(r.mean_depth/maxD)*ih;
    svg.appendChild(svgEl('rect',{x:xs(r.n_knots)-bw/2,y:mT+ih-h,width:bw,height:h,rx:3,fill:depth}));
    const t=svgEl('text',{x:xs(r.n_knots),y:H-mB+20,'text-anchor':'middle',fill:muted,'font-size':11,
      'font-family':'ui-monospace,Menlo,monospace'});t.textContent=r.n_knots;svg.appendChild(t);});
  const xlab=svgEl('text',{x:mL+iw/2,y:H-4,'text-anchor':'middle',fill:muted,'font-size':12});
  xlab.textContent='Nodos Knots (de 20)';svg.appendChild(xlab);
}

function fillTable(){
  const tb=document.getElementById('tbody');
  const maxD=Math.max(...ROWS.map(r=>r.mean_depth),1);
  tb.innerHTML=ROWS.map(r=>{
    const bw=Math.max(2,(r.mean_depth/maxD)*80);
    return `<tr><td class="num">${r.n_knots}</td><td class="num">${20-r.n_knots}</td>`+
      `<td class="num">${(r.hashpower*100).toFixed(0)}%</td>`+
      `<td class="num">${r.forks}/${r.runs}</td>`+
      `<td class="num">${(r.p_fork*100).toFixed(0)}%</td>`+
      `<td class="num">${(r.ci_lo*100).toFixed(0)}–${(r.ci_hi*100).toFixed(0)}%</td>`+
      `<td class="num barcell"><span class="bar" style="width:${bw}px"></span> ${r.mean_depth.toFixed(1)}</td>`+
      `<td class="num">${r.knots_wins}/${r.runs}</td></tr>`;
  }).join('');
}

function render(){drawProb();drawDepth();fillTable();}
render();
new MutationObserver(render).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
window.matchMedia('(prefers-color-scheme:dark)').addEventListener('change',render);
window.addEventListener('resize',()=>{clearTimeout(window._rt);window._rt=setTimeout(render,150);});
</script>
"""


if __name__ == "__main__":
    build()
