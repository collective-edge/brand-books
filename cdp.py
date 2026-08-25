#!/usr/bin/env python3
"""Drive headless Chrome over CDP to produce the real PDF and the real geometry.

Chrome's --print-to-pdf CLI flag ignores @page and forces US Letter. CDP's
Page.printToPDF takes explicit dimensions, which is what the browser's own
Save as PDF path does, so this measures the deliverable the user actually gets.

On measuring type size in the output. The screen geometry below is captured in
screen media, so a print-media rule cannot show up in it. Reading a print point
size off a screen pixel size and the page's 0.7506 pt/px scale therefore states
a size the PDF does not set: .bk-code nested in a .bk-caption resolves to
11.28px on screen, and the @media print floor in type-system.css raises it to
9pt before it reaches paper. Measure the PDF itself:

    import fitz
    for s in (sp for b in fitz.open(p)[n].get_text("dict")["blocks"]
              for l in b.get("lines", []) for sp in l["spans"]):
        print(s["size"], s["font"], s["text"])

Across all 48 pages of the three books the smallest span is exactly 9.0pt and
nothing falls under it, which is the floor section 9 of the standard sets.
"""
import json, os, subprocess, sys, time, urllib.request, base64, socket
import websocket

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_audit")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BOOKS = ["apex", "royal", "ce"]

AUDIT_JS = open(os.path.join(HERE, "audit.js"), encoding="utf-8").read() \
    if os.path.exists(os.path.join(HERE, "audit.js")) else None


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


class Chrome:
    def __init__(self):
        self.port = free_port()
        prof = os.path.join(OUT, "prof", f"cdp{self.port}")
        os.makedirs(prof, exist_ok=True)
        self.proc = subprocess.Popen(
            # The slide is 1600px wide but the type scale is clamp(..vw..), so the
            # VIEWPORT decides every font size. Without this the capture runs at
            # Chrome's default 800px window and measures a book nobody will ever
            # see: display-lg resolves to 45.36px instead of 72px.
            [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
             "--window-size=1600,900",
             "--force-device-scale-factor=1", "--remote-allow-origins=*",
             "--window-size=1600,900",
             f"--remote-debugging-port={self.port}",
             f"--user-data-dir={prof}", "about:blank"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ws = None
        for _ in range(80):
            try:
                tabs = json.loads(urllib.request.urlopen(
                    f"http://127.0.0.1:{self.port}/json", timeout=2).read())
                page = [t for t in tabs if t["type"] == "page"]
                if page:
                    ws = page[0]["webSocketDebuggerUrl"]; break
            except Exception:
                pass
            time.sleep(0.25)
        if not ws:
            raise RuntimeError("chrome did not expose a debugging target")
        self.ws = websocket.create_connection(ws, timeout=90)
        self.i = 0

    def cmd(self, method, **params):
        self.i += 1
        self.ws.send(json.dumps({"id": self.i, "method": method, "params": params}))
        while True:
            m = json.loads(self.ws.recv())
            if m.get("id") == self.i:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result", {})

    def goto(self, url):
        self.cmd("Page.enable")
        # The slide is 1600x900 and the display steps are fluid vw clamps. At
        # Chrome's default 800x600 the ladder resolves to the bottom of every
        # clamp, so an unset viewport measures a book nobody will ever see.
        self.cmd("Emulation.setDeviceMetricsOverride", width=1600, height=900,
                 deviceScaleFactor=1, mobile=False)
        self.cmd("Page.navigate", url=url)
        time.sleep(2.5)
        for _ in range(40):
            r = self.cmd("Runtime.evaluate", expression="document.readyState", returnByValue=True)
            if r["result"]["value"] == "complete":
                break
            time.sleep(0.25)
        self.cmd("Runtime.evaluate",
                 expression="document.fonts ? document.fonts.ready.then(()=>1) : 1",
                 awaitPromise=True, returnByValue=True)
        time.sleep(1.0)

    def evaluate(self, expr):
        r = self.cmd("Runtime.evaluate", expression=expr, returnByValue=True,
                     awaitPromise=True)
        return r["result"].get("value")

    def pdf(self, path, w=16.667, h=9.375):
        r = self.cmd("Page.printToPDF", printBackground=True, preferCSSPageSize=False,
                     paperWidth=w, paperHeight=h,
                     marginTop=0, marginBottom=0, marginLeft=0, marginRight=0)
        open(path, "wb").write(base64.b64decode(r["data"]))

    def close(self):
        try: self.ws.close()
        except Exception: pass
        try: self.proc.terminate()
        except Exception: pass


GEOM_JS = r"""
(function(){
  function lum(c){var m=c.match(/[\d.]+/g);if(!m)return null;
    var v=[m[0],m[1],m[2]].map(function(x){x=x/255;return x<=.03928?x/12.92:Math.pow((x+.055)/1.055,2.4)});
    return {L:.2126*v[0]+.7152*v[1]+.0722*v[2], a:m[3]===undefined?1:parseFloat(m[3])};}
  // A background painted by an absolutely positioned SIBLING is invisible to an
  // ancestor walk. The CE cover paints its photograph and its scrim that way, so
  // every node on it used to resolve to the flat band colour under them and
  // report a contrast ratio against a ground nobody sees.
  var IMGS=[];
  function coveringImage(el){
    var r=el.getBoundingClientRect();
    for(var i=0;i<IMGS.length;i++){
      var o=IMGS[i];
      if(o.el===el||o.el.contains(el)||el.contains(o.el)) continue;
      var q=o.r;
      if(q.left<=r.left+1&&q.top<=r.top+1&&q.right>=r.right-1&&q.bottom>=r.bottom-1) return true;
    }
    return false;}
  function bgOf(el){var e=el;while(e&&e!==document.documentElement){
      var cs=getComputedStyle(e);
      if(cs.backgroundImage&&cs.backgroundImage!=='none') return 'IMAGE';
      var l=lum(cs.backgroundColor);
      if(l&&l.a>0.98) return coveringImage(el)?'IMAGE':cs.backgroundColor;
      e=e.parentElement;}
    return coveringImage(el)?'IMAGE':'rgb(255, 255, 255)';}
  function ratio(f,b){var a=lum(f),c=lum(b);if(!a||!c)return null;
    var hi=Math.max(a.L,c.L),lo=Math.min(a.L,c.L);return Math.round(((hi+.05)/(lo+.05))*100)/100;}
  var out={slides:[]};
  document.querySelectorAll('.slide').forEach(function(s,i){
    var sr=s.getBoundingClientRect();
    var rec={i:i+1,cls:s.className,w:Math.round(sr.width),h:Math.round(sr.height),text:[],rects:[]};
    IMGS=[];
    s.querySelectorAll('*').forEach(function(o){
      var ocs=getComputedStyle(o);
      if(ocs.backgroundImage&&ocs.backgroundImage!=='none') IMGS.push({el:o,r:o.getBoundingClientRect()});});
    var sb=s.querySelector('.s-body');
    rec.bodyOverflow=sb?Math.max(0,sb.scrollHeight-sb.clientHeight):0;
    s.querySelectorAll('*').forEach(function(el){
      var r=el.getBoundingClientRect(); if(r.width<1||r.height<1) return;
      var cs=getComputedStyle(el);
      var box={tag:el.tagName.toLowerCase(),
        cls:(typeof el.className==='string'?el.className:'')||'',
        x:Math.round(r.left-sr.left),y:Math.round(r.top-sr.top),
        w:Math.round(r.width),h:Math.round(r.height)};
      rec.rects.push(box);
      var own=[].filter.call(el.childNodes,function(n){return n.nodeType===3&&n.textContent.trim()});
      if(!own.length) return;
      var b=bgOf(el);
      rec.text.push(Object.assign({},box,{
        t:own.map(function(n){return n.textContent.trim()}).join(' ').slice(0,160),
        font:cs.fontFamily.split(',')[0].replace(/["']/g,''),
        size:parseFloat(cs.fontSize),weight:cs.fontWeight,lh:cs.lineHeight,
        ls:cs.letterSpacing,style:cs.fontStyle,tt:cs.textTransform,
        align:cs.textAlign,maxw:cs.maxWidth,color:cs.color,bg:b,
        contrast:b==='IMAGE'?null:ratio(cs.color,b),
        overflowX: el.scrollWidth-Math.round(r.width)>1,
        pastBottom: Math.round(r.bottom-sr.top)>Math.round(sr.height)+1,
        pastRight: Math.round(r.right-sr.left)>Math.round(sr.width)+1
      }));
    });
    out.slides.push(rec);
  });
  return JSON.stringify(out);
})()
"""

if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "geom"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "pdf"), exist_ok=True)
    summary = {}
    for b in BOOKS:
        p = os.path.join(OUT, "html", f"{b}.html")
        c = Chrome()
        try:
            c.goto(f"file://{p}")
            raw = c.evaluate(GEOM_JS)
            data = json.loads(raw)
            open(os.path.join(OUT, "geom", f"{b}.json"), "w").write(json.dumps(data, indent=1))
            pdfp = os.path.join(OUT, "pdf", f"{b}.pdf")
            c.pdf(pdfp)
            import re
            pages = len(re.findall(rb"/Type\s*/Page[^s]", open(pdfp, "rb").read()))
            nodes = sum(len(s["text"]) for s in data["slides"])
            summary[b] = {"slides": len(data["slides"]), "textNodes": nodes, "pdfPages": pages}
            over = [(s["i"], s["bodyOverflow"]) for s in data["slides"] if s.get("bodyOverflow")]
            summary[b]["bodyOverflow"] = over
            print(f"  {b:6} {len(data['slides'])} slides · {nodes} text nodes · pdf {pages} pages")
            for i, px in over:
                print(f"         FAIL slide {i:02d} .s-body overflows its box by {px}px")
        finally:
            c.close()
    open(os.path.join(OUT, "capture.json"), "w").write(json.dumps(summary, indent=1))
    # An over-stuffed slide is a build error, not something the PDF discovers.
    if any(v.get("bodyOverflow") for v in summary.values()):
        raise SystemExit(1)
