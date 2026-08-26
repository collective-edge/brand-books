#!/usr/bin/env python3
"""Offline audit harness for the three brand books.

Vendors every CDN asset locally, rebuilds the books against those local paths,
then renders each book headlessly and emits, per slide:

  _audit/png/<book>-NN.png     the rendered slide, 1600x900
  _audit/geom/<book>.json      every text node: box, computed type, contrast
  _audit/pdf/<book>.pdf        the print output
  _audit/index.json            manifest

Nothing here touches the network, so runs are deterministic and fast.

  python3 harness.py            build, render, measure
  python3 harness.py --render   skip vendoring, re-render only
"""
import json, os, re, shutil, subprocess, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_audit")
def _kits():
    """Where the sibling brand kits are cloned.

    The setup clones all four repositories into one directory, so the parent of
    this one is the answer on any machine that followed it. The literal path is
    the machine this was written on and stays as a last resort.
    """
    for c in (os.path.dirname(HERE), os.path.expanduser("~/collective-edge"),
              "/Users/jacob.sarasohn/collective-edge"):
        if os.path.isdir(os.path.join(c, "collective-edge-brand-kit")):
            return c
    raise SystemExit("no brand kits found beside this repository")


KITS = _kits()
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BOOKS = ["apex", "royal", "ce"]
CDN = "https://cdn.jsdelivr.net/gh/collective-edge/"


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


# ---------------------------------------------------------------- vendor
def vendor():
    """Copy every asset the books reference out of the local kits."""
    a = os.path.join(OUT, "assets")
    os.makedirs(a, exist_ok=True)
    urls = set()
    for b in BOOKS:
        p = os.path.join(HERE, f"{b}.html")
        if os.path.exists(p):
            urls |= set(re.findall(r'https://cdn\.jsdelivr\.net/gh/collective-edge/([^"\')\s]+)',
                                   open(p, encoding="utf-8").read()))
    mapping = {}
    for u in sorted(urls):
        u = u.rstrip(".,)")
        repo, _, rel = u.partition("/")
        repo = repo.split("@")[0]
        src = os.path.join(KITS, repo, rel)
        dst = os.path.join(a, repo, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            mapping[u] = f"../assets/{repo}/{rel}"
        else:
            print(f"  MISSING SOURCE {src}")
    # The kit CSS pulls the variable font by CDN url(). Vendor those too, or
    # the offline render falls back to a system face and every measured metric
    # is a browser default rather than the type system. Match url() only: the
    # kit CSS also cites sibling stylesheets inside comments, and re-copying
    # one of those clobbers a file this pass has already rewritten.
    for u, local in list(mapping.items()):
        if not local.endswith(".css"):
            continue
        dst = os.path.join(a, local.replace("../assets/", "", 1))
        css = open(dst, encoding="utf-8").read()
        for inner in set(re.findall(
                r'url\(["\']?https://cdn\.jsdelivr\.net/gh/collective-edge/([^"\')\s]+)', css)):
            irepo, _, irel = inner.partition("/")
            irepo = irepo.split("@")[0]
            isrc = os.path.join(KITS, irepo, irel)
            idst = os.path.join(a, irepo, irel)
            if not os.path.exists(isrc):
                print(f"  MISSING SOURCE {isrc}")
                continue
            if not os.path.exists(idst):
                os.makedirs(os.path.dirname(idst), exist_ok=True)
                shutil.copy2(isrc, idst)
            # relative to the stylesheet itself, which sits in <repo>/snippets/
            css = css.replace(CDN + inner, os.path.relpath(idst, os.path.dirname(dst)))
            mapping.setdefault(inner, f"../assets/{irepo}/{irel}")
        open(dst, "w", encoding="utf-8").write(css)
    print(f"  vendored {len(mapping)} assets")
    return mapping


AUDIT_JS = r"""
<script>
(function(){
  function lum(c){var m=c.match(/\d+(\.\d+)?/g);if(!m)return null;
    var v=[m[0],m[1],m[2]].map(function(x){x=x/255;return x<=.03928?x/12.92:Math.pow((x+.055)/1.055,2.4)});
    var a=m[3]===undefined?1:parseFloat(m[3]); return {L:.2126*v[0]+.7152*v[1]+.0722*v[2], a:a};}
  function bg(el){var e=el;while(e&&e!==document.documentElement){
      var c=getComputedStyle(e).backgroundColor;var l=lum(c);
      if(l&&l.a>0.98) return c; var bi=getComputedStyle(e).backgroundImage;
      if(bi&&bi!=='none') return 'IMAGE'; e=e.parentElement;} return 'rgb(255,255,255)';}
  function ratio(f,b){var a=lum(f),c=lum(b);if(!a||!c)return null;
    var hi=Math.max(a.L,c.L),lo=Math.min(a.L,c.L);return (hi+.05)/(lo+.05);}
  var out={slides:[]};
  document.querySelectorAll('.slide').forEach(function(s,i){
    var sr=s.getBoundingClientRect();
    var rec={index:i+1, cls:s.className, w:Math.round(sr.width), h:Math.round(sr.height),
             overflow:{x:s.scrollWidth-Math.round(sr.width), y:s.scrollHeight-Math.round(sr.height)},
             text:[], boxes:[]};
    s.querySelectorAll('*').forEach(function(el){
      var r=el.getBoundingClientRect();
      if(r.width<1||r.height<1) return;
      var cs=getComputedStyle(el);
      var own=[].filter.call(el.childNodes,function(n){return n.nodeType===3&&n.textContent.trim()});
      var box={tag:el.tagName.toLowerCase(),cls:(el.className&&el.className.baseVal!==undefined?el.className.baseVal:el.className)||'',
        x:Math.round(r.left-sr.left),y:Math.round(r.top-sr.top),
        w:Math.round(r.width),h:Math.round(r.height)};
      rec.boxes.push(box);
      if(!own.length) return;
      var b=bg(el), fg=cs.color;
      rec.text.push({tag:box.tag,cls:box.cls,x:box.x,y:box.y,w:box.w,h:box.h,
        text:own.map(function(n){return n.textContent.trim()}).join(' ').slice(0,140),
        font:cs.fontFamily.split(',')[0].replace(/["']/g,''),
        size:parseFloat(cs.fontSize),weight:cs.fontWeight,
        lh:cs.lineHeight,ls:cs.letterSpacing,style:cs.fontStyle,
        transform:cs.textTransform, align:cs.textAlign, wrap:cs.textWrap||cs.textWrapStyle||'',
        maxw:cs.maxWidth, color:fg, bg:b,
        contrast:b==='IMAGE'?null:(function(){var v=ratio(fg,b);return v?Math.round(v*100)/100:null})(),
        clippedX: el.scrollWidth-Math.round(r.width) > 1,
        belowFold: Math.round(r.bottom-sr.top) > Math.round(sr.height)+1,
        pastRight: Math.round(r.right-sr.left) > Math.round(sr.width)+1});
    });
    out.slides.push(rec);
  });
  var pre=document.createElement('pre'); pre.id='AUDIT'; pre.textContent=JSON.stringify(out);
  pre.style.display='none'; document.body.appendChild(pre);
})();
</script>
"""


def make_audit_html(book, mapping):
    src = open(os.path.join(HERE, f"{book}.html"), encoding="utf-8").read()
    # Section 14 prints the drop-in snippet inside a visible <pre>. Those three
    # CDN urls are the page's content, not links the renderer resolves, so
    # rewriting them to a vendored path publishes a local file path as the
    # snippet a reader copies, in the png, the geometry and the PDF alike.
    # Lift every visible code block out before the rewrite, put it back after,
    # and the audit stops corrupting the thing it audits.
    held = []

    def hold(m):
        held.append(m.group(0))
        return f"\x00CODE{len(held) - 1}\x00"

    src = re.sub(r"<pre\b[^>]*>.*?</pre>|<code\b[^>]*>.*?</code>", hold, src, flags=re.S)
    # mapping values are relative to _audit/. The audit build lives one level
    # deeper, in _audit/html/, so every vendored path needs the extra hop.
    # Getting this wrong drops the whole type system and every logo, silently.
    for u, local in mapping.items():
        rel = local if local.startswith("../") else "../" + local
        src = src.replace(CDN + u, rel)
    # _audit/html/x.html -> ../../book.css. Getting this wrong renders the
    # books with no stylesheet at all, which is silent and looks plausible.
    src = src.replace('href="/book.css"', 'href="../../book.css"')
    for i, block in enumerate(held):
        src = src.replace(f"\x00CODE{i}\x00", block)
    if "\x00CODE" in src:
        raise SystemExit(f"{book}: a held code block was not restored")
    # contiguous slides, no chrome, so a full-page shot crops cleanly
    src = src.replace("</head>", """<style>
      .bar{display:none!important}
      .deck{gap:0!important;padding:0!important}
      .slide{box-shadow:none!important;margin:0!important}
      html,body{background:#fff!important}
    </style></head>""")
    src = src.replace("</body>", AUDIT_JS + "</body>")
    p = os.path.join(OUT, "html", f"{book}.html")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(src)
    # A link that does not resolve renders a plausible-looking page with no type
    # system and no logos, and says nothing. Every capture in this audit before
    # 16:00 was taken that way. Refuse to hand one back.
    root = os.path.dirname(p)
    missing = sorted({u for u in re.findall(r'(?:href|src)="([^"#?]+)"', src)
                      if not u.startswith(("http:", "https:", "data:", "/"))
                      and not os.path.exists(os.path.normpath(os.path.join(root, u)))})
    if missing:
        for u in missing:
            print(f"  UNRESOLVED {book}: {u}")
        raise SystemExit(f"{book}: {len(missing)} asset links do not resolve on disk")
    return p


def chrome(args, wait_for, timeout=90):
    prof = os.path.join(OUT, "prof", str(abs(hash(tuple(args))) % 99999))
    os.makedirs(prof, exist_ok=True)
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                             "--hide-scrollbars", "--force-device-scale-factor=1",
                             f"--user-data-dir={prof}"] + args,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < timeout:
        if wait_for and os.path.exists(wait_for) and os.path.getsize(wait_for) > 0:
            time.sleep(0.6)
            break
        if proc.poll() is not None:
            break
        time.sleep(0.4)
    try:
        proc.terminate()
    except Exception:
        pass
    return wait_for and os.path.exists(wait_for)


def render(book, path):
    from PIL import Image
    n_slides = open(path, encoding="utf-8").read().count('<section class="slide')
    tall = 900 * n_slides
    shot = os.path.join(OUT, f"_full-{book}.png")
    if os.path.exists(shot):
        os.remove(shot)
    ok = chrome([f"--window-size=1600,{tall}", "--virtual-time-budget=15000",
                 f"--screenshot={shot}", f"file://{path}"], shot)
    if not ok:
        print(f"  {book}: screenshot FAILED")
        return 0
    im = Image.open(shot)
    d = os.path.join(OUT, "png")
    os.makedirs(d, exist_ok=True)
    cut = 0
    for i in range(n_slides):
        top = i * 900
        if top + 900 > im.height:
            break
        im.crop((0, top, 1600, top + 900)).save(os.path.join(d, f"{book}-{i+1:02d}.png"))
        cut += 1
    os.remove(shot)
    return cut


def measure(book, path):
    dom = os.path.join(OUT, f"_dom-{book}.html")
    if os.path.exists(dom):
        os.remove(dom)
    try:
        r = sh([CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
                "--window-size=1600,900",
                f"--user-data-dir={os.path.join(OUT,'prof','dom'+book)}",
                "--dump-dom", f"file://{path}"], timeout=60)
        html = r.stdout
    except subprocess.TimeoutExpired:
        print(f"  {book}: dump-dom timed out")
        return None
    m = re.search(r'<pre id="AUDIT"[^>]*>(.*?)</pre>', html, re.S)
    if not m:
        print(f"  {book}: no audit payload in DOM")
        return None
    data = json.loads(re.sub(r"&quot;", '"', m.group(1)).replace("&amp;", "&")
                      .replace("&lt;", "<").replace("&gt;", ">"))
    d = os.path.join(OUT, "geom")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, f"{book}.json"), "w", encoding="utf-8").write(json.dumps(data, indent=1))
    return data


def pdf(book, path):
    d = os.path.join(OUT, "pdf")
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, f"{book}.pdf")
    if os.path.exists(out):
        os.remove(out)
    ok = chrome(["--no-pdf-header-footer", "--virtual-time-budget=15000",
                 f"--print-to-pdf={out}", f"file://{path}"], out)
    if not ok:
        return 0
    data = open(out, "rb").read()
    return len(re.findall(rb"/Type\s*/Page[^s]", data))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    mapping = vendor()
    open(os.path.join(OUT, "asset-map.json"), "w").write(json.dumps(mapping, indent=1))
    manifest = {}
    for b in BOOKS:
        p = make_audit_html(b, mapping)
        pngs = render(b, p)
        pages = pdf(b, p)
        manifest[b] = {"html": p, "png": pngs, "pdfPages": pages}
        print(f"  {b:6} {pngs} png · pdf {pages} pages")
    open(os.path.join(OUT, "index.json"), "w").write(json.dumps(manifest, indent=1))
    print(f"\n  audit artefacts in {OUT}")
