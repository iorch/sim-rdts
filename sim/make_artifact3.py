"""Genera results/report3.html: dashboard del modelo económico v2 (atiende la crítica).
Panel 1: premio de equilibrio (incentivo neto) vs hashpower. Panel 2: convergencia de la
cadena, Core spamea-siempre vs Core-deja-de-spamear. Lee results/economics_summary.json.
"""
import json
import os

RES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")


def build():
    with open(os.path.join(RES, "economics_summary.json")) as f:
        rows = json.load(f)["rows"]
    # umbral: primer hashpower donde el premio de equilibrio supera 1 (100% del premio de bloque)
    thr = next((r for r in rows if r["breakeven_fee"] is None or r["breakeven_fee"] >= 1), None)
    thr_share = f"~{thr['knots_share']*100:.0f}%" if thr else "—"
    stats = [
        ("Umbral económico", thr_share,
         "hashpower de Knots donde el dato tendría que pagar más del 100% del premio de bloque para "
         "compensar el riesgo de orfandad — deja de convenir incluirlo"),
        ("El incentivo real", "premio = p/(1−p)",
         "cuánto debe pagar el dato (como fracción del premio de bloque) para valer el riesgo de orfandad p"),
        ("Respuesta racional", "dejar de incluir datos",
         "no 'señalar RDTS': el minero Core que pierde bloques deja de incluir datos — pero solo "
         "reacciona una vez que Knots ya lo orfana, así que refuerza el desenlace, no lo adelanta"),
    ]
    stat_html = "\n".join(
        f'<div class="tile"><div class="tile-label">{a}</div>'
        f'<div class="tile-value">{b}</div><div class="tile-note">{c}</div></div>'
        for a, b, c in stats)
    html = TEMPLATE.replace("__DATA__", json.dumps({"rows": rows})).replace("__STATS__", stat_html)
    out = os.path.join(RES, "report3.html")
    with open(out, "w") as f:
        f.write(html)
    print("escrito", out, f"({len(rows)} puntos)")
    return out


TEMPLATE = r"""<title>El incentivo real — modelo económico (BIP-110/RDTS)</title>
<style>
:root{--bg:#f4f2ec;--surface:#fffdf8;--card:#fff;--ink:#191c24;--muted:#6c7280;--hair:#e4e1d8;
  --fee:#c2410c;--base:#8a92a6;--adap:#1f9d57;--ref:#a7abb6;--shadow:0 1px 2px rgba(20,22,30,.05),0 8px 30px rgba(20,22,30,.06);}
@media (prefers-color-scheme:dark){:root{--bg:#0f1117;--surface:#161922;--card:#1a1e28;--ink:#e9ebf2;--muted:#949bad;
  --hair:#262a35;--fee:#fb923c;--base:#6b7280;--adap:#3fca82;--ref:#565d6c;--shadow:0 1px 2px rgba(0,0,0,.3),0 12px 34px rgba(0,0,0,.34);}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased;}
.wrap{max-width:940px;margin:0 auto;padding:clamp(20px,5vw,56px) clamp(16px,4vw,32px) 72px;}
.eyebrow{font-family:ui-monospace,Menlo,monospace;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--fee);font-weight:600;display:flex;gap:10px;align-items:center;}
.eyebrow::before{content:"";width:26px;height:2px;background:var(--fee);display:inline-block;}
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
.tooltip .tt-n{font-family:ui-monospace,Menlo,monospace;font-weight:600;font-size:13px;margin-bottom:5px;}
.tooltip .tt-row{display:flex;justify-content:space-between;gap:14px;color:var(--muted);} .tooltip .tt-row b{color:var(--ink);font-family:ui-monospace,Menlo,monospace;}
table{width:100%;border-collapse:collapse;font-size:13.5px;} th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--hair);}
th{font-size:11.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:600;} td.num{font-family:ui-monospace,Menlo,monospace;text-align:right;font-variant-numeric:tabular-nums;}
.foot{color:var(--muted);font-size:13px;margin-top:26px;line-height:1.6;} .foot b{color:var(--ink);}
.foot code{font-family:ui-monospace,Menlo,monospace;background:var(--surface);border:1px solid var(--hair);padding:1px 6px;border-radius:6px;font-size:12px;color:var(--ink);}
a.back{font-family:ui-monospace,Menlo,monospace;font-size:13px;color:var(--fee);text-decoration:none;} a.back:hover{text-decoration:underline;}
</style>
<div class="wrap">
  <a class="back" href="index.html">← volver a las simulaciones</a>
  <div class="eyebrow">modelo económico · atiende la crítica</div>
  <h1>El incentivo real: ¿cuánto debe pagar el dato?</h1>
  <p class="lede">Contar reorganizaciones mide solo un lado de la balanza. Un minero Core no
  decide por miedo a la orfandad, sino por <b>ganancia neta</b>: incluir un bloque con datos
  conviene solo si esos datos pagan lo suficiente para compensar la probabilidad de que el
  bloque quede huérfano. Este modelo mide esa probabilidad de orfandad <b>real</b> (marcando
  cada bloque con datos y viendo si sobrevive) y la convierte en el fee que el dato tendría que
  pagar.</p>
  <div class="versions">
    <span class="chip"><b>Core</b> 31.1</span>
    <span class="chip"><b>Knots</b> v29.3.knots20260508</span>
    <span class="chip">modelo v2 · orfandad medida por hash</span>
    <span class="chip">baseline 8 · adaptativo 3 corridas/punto</span>
  </div>

  <div class="grid">__STATS__</div>

  <div class="card">
    <h2>Premio de equilibrio del dato, según el hashpower de Knots</h2>
    <p class="sub">Cuánto debe pagar el dato, como fracción del premio de bloque, para que valga
    el riesgo de orfandad: <b>premio = p / (1 − p)</b>, con p = probabilidad de que un bloque con
    datos quede huérfano. Eje vertical logarítmico. Al 100% (línea) el dato tendría que pagar un
    premio igual a todo el subsidio del bloque.</p>
    <div class="chart-wrap" id="w1"><svg id="c1" viewBox="0 0 800 320" preserveAspectRatio="xMidYMid meet"></svg><div class="tooltip" id="t1"></div></div>
  </div>

  <div class="card">
    <h2>La respuesta racional: dejar de incluir datos</h2>
    <p class="sub">Probabilidad de que la cadena converja (sin fork persistente). <b>Spamea siempre</b>:
    Core incluye datos en todos sus bloques (supuesto original). <b>Deja de spamear</b>: un minero
    Core que ve un bloque suyo huérfano deja de incluir datos. <b>Resultado (contraintuitivo):</b>
    las dos curvas van casi juntas — dejar de spamear NO adelanta la convergencia, porque un minero
    solo se rinde <i>después</i> de que le orfanan un bloque, y eso solo pasa cuando Knots ya va
    ganando. La respuesta racional refuerza el desenlace donde Knots ya domina; no lo crea antes.</p>
    <div class="chart-wrap" id="w2"><svg id="c2" viewBox="0 0 800 320" preserveAspectRatio="xMidYMid meet"></svg><div class="tooltip" id="t2"></div></div>
    <div class="legend">
      <span><span class="sw" style="background:var(--base)"></span>Core spamea siempre</span>
      <span><span class="sw" style="background:var(--adap)"></span>Core deja de spamear</span>
    </div>
  </div>

  <div class="card">
    <h2>Datos</h2>
    <div class="chart-wrap"><table><thead><tr>
      <th>Hashpower de Knots</th><th class="num">Orfandad del dato</th><th class="num">Premio de equilibrio</th>
      <th class="num">Converge (spamea siempre)</th><th class="num">Converge (deja de spamear)</th><th class="num">Mineros que se rinden</th>
    </tr></thead><tbody id="tb"></tbody></table></div>
  </div>

  <p class="foot">
    <b>El incentivo real es económico, no "señalar RDTS".</b> Un minero Core deja de incluir datos
    cuando el <b>premio de equilibrio</b> (lo que el dato debería pagar para compensar el riesgo de
    orfandad) supera lo que el dato realmente paga. Ese premio cruza el 100% del premio de bloque a
    <b>~54% de hashpower Knots</b> y se dispara desde ahí — arriba de eso, ningún fee razonable lo
    justifica.<br><br>
    <b>Y un resultado honesto que corrige la intuición.</b> Simular que los mineros Core
    <i>reaccionan</i> (dejan de spamear tras ser orfanados) no adelanta el desenlace: la curva
    adaptativa casi coincide con la de "spamea siempre". Un minero solo se rinde después de perder un
    bloque, y eso ocurre cuando Knots ya va ganando. La reacción racional <b>refuerza</b> el
    resultado, pero el que manda es el <b>premio de equilibrio</b> — el precio del dato frente al
    riesgo de orfandad.<br><br>
    <b>Honestidad.</b> Sigue siendo regtest (dificultad fija, sin latencia real). El premio de
    equilibrio supone que un bloque huérfano se pierde por completo y que un bloque limpio nunca se
    orfana; no modela comisiones absolutas ni minería estratégica. Es el incentivo de primer orden,
    no una predicción de la red real.
  </p>
</div>
<script>
const ROWS=__DATA__.rows;
const cssv=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function E(t,a){const e=document.createElementNS('http://www.w3.org/2000/svg',t);for(const k in a)e.setAttribute(k,a[k]);return e;}
const XMIN=15,XMAX=90;
const xs=(s,mL,iw)=>mL+((s*100-XMIN)/(XMAX-XMIN))*iw;

function axisX(svg,W,H,mL,mB,iw){
  const muted=cssv('--muted');
  for(let s=20;s<=90;s+=10){const t=E('text',{x:mL+((s-XMIN)/(XMAX-XMIN))*iw,y:H-mB+20,'text-anchor':'middle',fill:muted,'font-size':11,'font-family':'ui-monospace,Menlo,monospace'});t.textContent=s+'%';svg.appendChild(t);}
  const xl=E('text',{x:mL+iw/2,y:H-3,'text-anchor':'middle',fill:muted,'font-size':12});xl.textContent='Hashpower de Knots (%)';svg.appendChild(xl);
}

function drawFee(){
  const svg=document.getElementById('c1');svg.innerHTML='';const W=800,H=320,mL=56,mR=20,mT=16,mB=42,iw=W-mL-mR,ih=H-mT-mB;
  const LO=0.01,HI=20;const fee=cssv('--fee'),hair=cssv('--hair'),muted=cssv('--muted'),ref=cssv('--ref');
  const ys=v=>{v=Math.max(v,LO);const t=(Math.log10(v)-Math.log10(LO))/(Math.log10(HI)-Math.log10(LO));return mT+(1-t)*ih;};
  [[0.01,'1%'],[0.1,'10%'],[1,'100%'],[10,'1000%']].forEach(([v,lbl])=>{const y=ys(v);svg.appendChild(E('line',{x1:mL,y1:y,x2:W-mR,y2:y,stroke:hair,'stroke-width':1}));
    const t=E('text',{x:mL-9,y:y+4,'text-anchor':'end',fill:muted,'font-size':11,'font-family':'ui-monospace,Menlo,monospace'});t.textContent=lbl;svg.appendChild(t);});
  svg.appendChild(E('line',{x1:mL,y1:ys(1),x2:W-mR,y2:ys(1),stroke:fee,'stroke-width':1.3,'stroke-dasharray':'2 3',opacity:.6}));
  axisX(svg,W,H,mL,mB,iw);
  const pts=ROWS.map(r=>({x:xs(r.knots_share,mL,iw),v:r.breakeven_fee,inf:r.breakeven_fee===null,r}));
  svg.appendChild(E('path',{d:'M'+pts.filter(p=>!p.inf).map(p=>`${p.x},${ys(p.v)}`).join(' L'),fill:'none',stroke:fee,'stroke-width':2.4,'stroke-linejoin':'round'}));
  pts.forEach(p=>{const y=p.inf?mT+4:ys(p.v);svg.appendChild(E('circle',{cx:p.x,cy:y,r:p.inf?3:3.6,fill:p.inf?'none':fee,stroke:fee,'stroke-width':p.inf?1.6:1.2}));
    if(p.inf){const t=E('text',{x:p.x,y:mT-2,'text-anchor':'middle',fill:fee,'font-size':13});t.textContent='∞';svg.appendChild(t);}});
  const tt=document.getElementById('t1');
  svg.addEventListener('pointermove',ev=>{const rc=svg.getBoundingClientRect();const px=(ev.clientX-rc.left)/rc.width*W;
    let b=pts[0],bd=1e9;pts.forEach(p=>{const d=Math.abs(p.x-px);if(d<bd){bd=d;b=p;}});tt.style.opacity=1;
    const be=b.inf?'∞ (ningún fee lo justifica)':`${(b.v*100).toFixed(0)}% del premio`;
    tt.innerHTML=`<div class="tt-n">${(b.r.knots_share*100).toFixed(0)}% Knots</div>`+
      `<div class="tt-row"><span>Orfandad del dato</span><b>${(b.r.orphan_rate*100).toFixed(0)}%</b></div>`+
      `<div class="tt-row"><span>Premio de equilibrio</span><b>${be}</b></div>`;
    const cx=b.x/W*rc.width;tt.style.left=Math.min(Math.max(cx-90,4),rc.width-190)+'px';tt.style.top='8px';});
  svg.addEventListener('pointerleave',()=>tt.style.opacity=0);
}

function drawConv(){
  const svg=document.getElementById('c2');svg.innerHTML='';const W=800,H=320,mL=56,mR=20,mT=16,mB=42,iw=W-mL-mR,ih=H-mT-mB;
  const base=cssv('--base'),adap=cssv('--adap'),hair=cssv('--hair'),muted=cssv('--muted');
  const ys=p=>mT+(1-p)*ih;
  for(let i=0;i<=5;i++){const y=ys(i/5);svg.appendChild(E('line',{x1:mL,y1:y,x2:W-mR,y2:y,stroke:hair,'stroke-width':1}));
    const t=E('text',{x:mL-9,y:y+4,'text-anchor':'end',fill:muted,'font-size':11,'font-family':'ui-monospace,Menlo,monospace'});t.textContent=(i*20)+'%';svg.appendChild(t);}
  axisX(svg,W,H,mL,mB,iw);
  const line=(key,color)=>{const pts=ROWS.filter(r=>r[key]!==null);if(!pts.length)return;
    svg.appendChild(E('path',{d:'M'+pts.map(r=>`${xs(r.knots_share,mL,iw)},${ys(r[key])}`).join(' L'),fill:'none',stroke:color,'stroke-width':2.4,'stroke-linejoin':'round'}));
    pts.forEach(r=>svg.appendChild(E('circle',{cx:xs(r.knots_share,mL,iw),cy:ys(r[key]),r:3.4,fill:color,stroke:cssv('--card'),'stroke-width':1.2})));};
  line('baseline_converge',base);line('adaptive_converge',adap);
  const tt=document.getElementById('t2');
  svg.addEventListener('pointermove',ev=>{const rc=svg.getBoundingClientRect();const px=(ev.clientX-rc.left)/rc.width*W;
    let b=ROWS[0],bd=1e9;ROWS.forEach(r=>{const d=Math.abs(xs(r.knots_share,mL,iw)-px);if(d<bd){bd=d;b=r;}});tt.style.opacity=1;
    const f=x=>x===null?'-':`${(x*100).toFixed(0)}%`;
    tt.innerHTML=`<div class="tt-n">${(b.knots_share*100).toFixed(0)}% Knots</div>`+
      `<div class="tt-row"><span>Spamea siempre</span><b>${f(b.baseline_converge)}</b></div>`+
      `<div class="tt-row"><span>Deja de spamear</span><b>${f(b.adaptive_converge)}</b></div>`;
    const cx=xs(b.knots_share,mL,iw)/W*rc.width;tt.style.left=Math.min(Math.max(cx-90,4),rc.width-190)+'px';tt.style.top='8px';});
  svg.addEventListener('pointerleave',()=>tt.style.opacity=0);
}

function fillTable(){
  document.getElementById('tb').innerHTML=ROWS.map(r=>{
    const be=r.breakeven_fee===null?'∞':`${(r.breakeven_fee*100).toFixed(0)}%`;
    const f=x=>x===null?'-':`${(x*100).toFixed(0)}%`;
    return `<tr><td class="num">${(r.knots_share*100).toFixed(0)}%</td><td class="num">${(r.orphan_rate*100).toFixed(0)}%</td>`+
      `<td class="num">${be}</td><td class="num">${f(r.baseline_converge)}</td><td class="num">${f(r.adaptive_converge)}</td>`+
      `<td class="num">${r.adaptive_gaveup===null?'-':r.adaptive_gaveup}</td></tr>`;}).join('');
}
function render(){drawFee();drawConv();fillTable();}
render();
new MutationObserver(render).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
window.matchMedia('(prefers-color-scheme:dark)').addEventListener('change',render);
window.addEventListener('resize',()=>{clearTimeout(window._r);window._r=setTimeout(render,150);});
</script>
"""


if __name__ == "__main__":
    build()
