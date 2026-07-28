"""Construye el sitio estático docs/ para GitHub Pages a partir de los dashboards
autocontenidos de results/. Envuelve cada fragmento en un documento HTML completo
(con <meta charset="utf-8">, clave para los acentos) y genera la landing index.html.

Uso:  python3 deploy/build_pages.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
DOCS = os.path.join(ROOT, "docs")

HEAD = ('<!doctype html>\n<html lang="es">\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n')


def wrap(fragment_path, out_path):
    with open(fragment_path, encoding="utf-8") as f:
        frag = f.read()
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(HEAD + frag)
    print("escrito", out_path)


def _md_to_html(md):
    """Conversor Markdown→HTML mínimo para CRITICA.md (contenido controlado)."""
    import re
    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def inline(s):
        s = esc(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
        s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
        s = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2">\1</a>', s)
        return s

    out, lst, para = [], [], []

    def flush_para():
        if para:
            out.append("<p>" + " ".join(para) + "</p>")
            para.clear()

    def flush_list():
        if lst:
            out.append("<ul>" + "".join(f"<li>{inline(x)}</li>" for x in lst) + "</ul>")
            lst.clear()

    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush_para(); flush_list(); continue
        if line.startswith("### "):
            flush_para(); flush_list(); out.append(f"<h3>{inline(line[4:])}</h3>")
        elif line.startswith("## "):
            flush_para(); flush_list(); out.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("# "):
            flush_para(); flush_list(); out.append(f"<h1>{inline(line[2:])}</h1>")
        elif line.startswith("> "):
            flush_para(); flush_list(); out.append(f"<blockquote>{inline(line[2:])}</blockquote>")
        elif line.strip() == "---":
            flush_para(); flush_list(); out.append("<hr>")
        elif line.startswith("- "):
            flush_para(); lst.append(line[2:])
        else:
            flush_list(); para.append(inline(line))
    flush_para(); flush_list()
    return "\n".join(out)


def build():
    os.makedirs(DOCS, exist_ok=True)
    wrap(os.path.join(RESULTS, "report.html"), os.path.join(DOCS, "sim1.html"))
    wrap(os.path.join(RESULTS, "report2.html"), os.path.join(DOCS, "sim2.html"))
    with open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8") as f:
        f.write(INDEX)
    # página de crítica renderizada desde CRITICA.md (fuente única)
    with open(os.path.join(ROOT, "CRITICA.md"), encoding="utf-8") as f:
        body = _md_to_html(f.read())
    with open(os.path.join(DOCS, "critica.html"), "w", encoding="utf-8") as f:
        f.write(CRITICA_PAGE.replace("__BODY__", body))
    # .nojekyll para que Pages sirva los archivos tal cual
    open(os.path.join(DOCS, ".nojekyll"), "w").close()
    print("escrito", os.path.join(DOCS, "index.html"))
    print("escrito", os.path.join(DOCS, "critica.html"))


INDEX = r"""<!doctype html>
<html lang="es">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>sim-rdts · Fork Core vs Knots (BIP-110 / RDTS)</title>
<style>
:root{
  --bg:#f4f2ec; --card:#fffdf8; --ink:#191c24; --muted:#6c7280; --hair:#e4e1d8;
  --fork:#d61f69; --win:#1f9d57; --core:#2f6fed; --knots:#e07b0a;
  --shadow:0 1px 2px rgba(20,22,30,.05),0 10px 34px rgba(20,22,30,.07);
}
@media (prefers-color-scheme:dark){:root{
  --bg:#0f1117; --card:#1a1e28; --ink:#e9ebf2; --muted:#949bad; --hair:#262a35;
  --fork:#f0559b; --win:#3fca82; --core:#6a9bff; --knots:#f5a03d;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 14px 38px rgba(0,0,0,.36);
}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  line-height:1.6;-webkit-font-smoothing:antialiased;}
.wrap{max-width:820px;margin:0 auto;padding:clamp(24px,6vw,64px) clamp(16px,4vw,32px) 72px;}
.eyebrow{font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:12px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--fork);font-weight:600;display:flex;gap:10px;align-items:center;}
.eyebrow::before{content:"";width:28px;height:2px;background:var(--fork);}
h1{font-size:clamp(30px,6vw,50px);line-height:1.06;margin:.6rem 0 .4rem;letter-spacing:-.02em;
  font-weight:780;text-wrap:balance;}
.lede{font-size:clamp(15px,2.3vw,18px);color:var(--muted);max-width:62ch;}
.lede b{color:var(--ink);}
.cards{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:34px 0 24px;}
@media(max-width:600px){.cards{grid-template-columns:1fr}}
a.card{display:block;text-decoration:none;color:inherit;background:var(--card);border:1px solid var(--hair);
  border-radius:16px;padding:22px 22px 20px;box-shadow:var(--shadow);transition:transform .12s,border-color .12s;}
a.card:hover{transform:translateY(-3px);border-color:var(--fork);}
a.card:focus-visible{outline:2px solid var(--fork);outline-offset:3px;}
.card .tag{font-family:ui-monospace,Menlo,monospace;font-size:11.5px;letter-spacing:.08em;
  text-transform:uppercase;color:var(--muted);}
.card h2{font-size:19px;margin:8px 0 6px;letter-spacing:-.01em;}
.card p{font-size:13.5px;color:var(--muted);margin:0 0 12px;}
.card .go{font-family:ui-monospace,Menlo,monospace;font-size:13px;color:var(--fork);font-weight:600;}
.card.win .go,.card.win:hover{border-color:var(--win);} .card.win .go{color:var(--win);}
.mech{background:var(--card);border:1px solid var(--hair);border-radius:16px;padding:22px 24px;
  box-shadow:var(--shadow);margin:8px 0 24px;}
.mech h3{margin:0 0 10px;font-size:15px;}
.mech table{width:100%;border-collapse:collapse;font-size:13.5px;}
.mech td,.mech th{text-align:left;padding:7px 8px;border-bottom:1px solid var(--hair);}
.mech th{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);}
.mech .ok{color:var(--win);} .mech .bad{color:var(--knots);font-family:ui-monospace,Menlo,monospace;font-size:12px;}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:6px;vertical-align:middle;}
.dot.core{background:var(--core)} .dot.knots{background:var(--knots)}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 0;}
.chip{font-family:ui-monospace,Menlo,monospace;font-size:12px;border:1px solid var(--hair);border-radius:999px;
  padding:5px 11px;color:var(--muted);}
.foot{color:var(--muted);font-size:13px;margin-top:30px;line-height:1.7;border-top:1px solid var(--hair);padding-top:18px;}
.foot a{color:var(--fork);text-decoration:none;} .foot a:hover{text-decoration:underline;}
.foot code{font-family:ui-monospace,Menlo,monospace;font-size:12px;}
</style>
<div class="wrap">
  <div class="eyebrow">BIP-110 / RDTS · simulación regtest</div>
  <h1>¿Cuándo se parte la cadena entre Bitcoin Core y Knots?</h1>
  <p class="lede"><b>Bitcoin Knots</b> activa el softfork <b>BIP-110 / RDTS</b> y rechaza por
  consenso las transacciones con datos grandes. <b>Bitcoin Core</b> no lo conoce y las mina.
  Cada bloque con datos que Core produce es válido para Core e <b>inválido para Knots</b> → la
  cadena puede partirse. Estas simulaciones en regtest miden la probabilidad de ese fork y sus
  incentivos económicos, en función del reparto de hashpower.</p>

  <div class="cards">
    <a class="card" href="sim1.html">
      <div class="tag">Experimento 1 · nodos iguales</div>
      <h2>Probabilidad de fork vs hashpower</h2>
      <p>20 nodos, cada uno 1/20 del hashpower. Barrido 1→19 nodos Knots. ¿Dónde aparece el
      fork persistente?</p>
      <div class="go">Ver dashboard →</div>
    </a>
    <a class="card win" href="sim2.html">
      <div class="tag">Experimento 2 · hashpower concentrado</div>
      <h2>Nodos vs hashpower + incentivo</h2>
      <p>Core en pocos mineros grandes vs Knots disperso. ¿Importa el número de nodos? ¿Cada
      cuánto pierde bloques Core?</p>
      <div class="go">Ver dashboard →</div>
    </a>
  </div>

  <div class="mech">
    <h3>La asimetría de consenso</h3>
    <table>
      <thead><tr><th>Transacción (RDTS)</th><th><span class="dot core"></span>Core 31.1</th>
      <th><span class="dot knots"></span>Knots v29.3 (RDTS)</th></tr></thead>
      <tbody>
        <tr><td>OP_RETURN &gt; 83 bytes</td><td class="ok">acepta y relaya</td><td class="bad">bad-txns-vout-script-toolarge</td></tr>
        <tr><td>Item de witness &gt; 256 bytes</td><td class="ok">acepta (&lt; 520 B)</td><td class="bad">Push value size limit exceeded</td></tr>
      </tbody>
    </table>
  </div>

  <div class="chips">
    <span class="chip">Bitcoin Core 31.1</span>
    <span class="chip">Bitcoin Knots v29.3.knots20260508</span>
    <span class="chip">regtest · Docker</span>
    <span class="chip">Monte Carlo</span>
  </div>

  <p class="foot">
    <b>Hallazgos.</b> Lo decisivo es el <b>cruce de incentivos, no el de la victoria</b>: Core empieza
    a perder <b>al menos un bloque por día</b> por reorganización desde apenas <b>~30% del hashpower
    de Knots</b> — mucho antes del <b>~55-57%</b> en que el softfork realmente gana. Esa pérdida
    diaria le da a un minero Core incentivo a <b>señalar RDTS</b> para dejar de perder bloques,
    empujando el hashpower hacia arriba (efecto cascada). Además: el fork es de consenso (no solo de
    retransmisión), y <b>el número de nodos no importa</b> — solo el hashpower (Knots con 16 a 30
    nodos pierde igual por debajo del umbral).<br><br>
    <b>Lo que esto NO prueba:</b> ver la <a href="critica.html">crítica honesta</a> (supuestos,
    límites y qué faltaría medir).<br><br>
    Código y datos: <a href="https://github.com/iorch/sim-rdts">github.com/iorch/sim-rdts</a> ·
    reproducible con <code>docker</code> + <code>python3</code>.
  </p>
</div>
"""


CRITICA_PAGE = r"""<!doctype html>
<html lang="es">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Crítica honesta · sim-rdts</title>
<style>
:root{--bg:#f4f2ec;--ink:#191c24;--muted:#5f6570;--hair:#e0ddd3;--accent:#d61f69;--code:#f0eee7;}
@media (prefers-color-scheme:dark){:root{--bg:#0f1117;--ink:#e9ebf2;--muted:#9aa1b2;--hair:#252a35;--accent:#f0559b;--code:#1a1e28;}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:ui-serif,Georgia,"Times New Roman",serif;line-height:1.72;-webkit-font-smoothing:antialiased;}
.wrap{max-width:44rem;margin:0 auto;padding:clamp(28px,6vw,64px) clamp(18px,5vw,28px) 80px;}
.back{font-family:ui-monospace,Menlo,monospace;font-size:13px;color:var(--accent);text-decoration:none;}
.back:hover{text-decoration:underline;}
h1{font-size:clamp(28px,5vw,40px);line-height:1.12;letter-spacing:-.01em;margin:1.2rem 0 .3rem;text-wrap:balance;}
h2{font-size:clamp(20px,3.2vw,25px);margin:2.2rem 0 .5rem;letter-spacing:-.01em;}
h3{font-size:17px;margin:1.6rem 0 .2rem;}
p{margin:.7rem 0;} b{font-weight:700;} em{font-style:italic;}
blockquote{margin:1.2rem 0;padding:.4rem 0 .4rem 1.1rem;border-left:3px solid var(--accent);
  color:var(--muted);font-style:italic;}
ul{margin:.6rem 0;padding-left:1.3rem;} li{margin:.35rem 0;}
hr{border:0;border-top:1px solid var(--hair);margin:2.4rem 0;}
code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.86em;background:var(--code);
  border:1px solid var(--hair);border-radius:5px;padding:.05em .4em;}
a{color:var(--accent);}
.wrap>h1:first-of-type+*{}
</style>
<div class="wrap">
<a class="back" href="index.html">← volver a las simulaciones</a>
__BODY__
<hr>
<a class="back" href="index.html">← volver a las simulaciones</a>
</div>
"""


if __name__ == "__main__":
    build()
