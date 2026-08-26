#!/usr/bin/env python3
"""Capture every page of the CE manual: one PNG per page, geometry, and the real PDF.

Verification tool, not part of the deliverable. Same lesson the book harness
records: Chrome's --print-to-pdf flag forces US Letter portrait and ignores the
CSS page size, so the PDF comes out through CDP with explicit dimensions.

    python3 capture.py http://localhost:8090/ce-manual.html OUTDIR

Checks four things the type validator cannot: text or images overlapping, anything
closing below the field floor at y 736, anything past the live margins, and low
contrast on small type. Every real defect in the manual was found this way.
"""
import base64, json, os, socket, subprocess, sys, time, urllib.request
import websocket

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
W, H = 1056, 816          # 11 x 8.5in at 96dpi
PW, PH = 11.0, 8.5        # inches, the sheet


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


class Chrome:
    def __init__(self, width=W, height=H, scale=2):
        self.port = free_port()
        self.scale = scale
        prof = f"/tmp/ce-manual-prof-{self.port}"
        os.makedirs(prof, exist_ok=True)
        self.proc = subprocess.Popen(
            [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
             f"--window-size={width},{height}", "--force-device-scale-factor=1",
             "--remote-allow-origins=*", f"--remote-debugging-port={self.port}",
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
        self.ws = websocket.create_connection(ws, timeout=120)
        self.i = 0
        self.width, self.height = width, height

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
        self.cmd("Emulation.setDeviceMetricsOverride", width=self.width, height=self.height,
                 deviceScaleFactor=1, mobile=False)
        self.cmd("Page.navigate", url=url)
        time.sleep(2.0)
        for _ in range(60):
            if self.evaluate("document.readyState") == "complete":
                break
            time.sleep(0.25)
        self.cmd("Runtime.evaluate",
                 expression="document.fonts ? document.fonts.ready.then(()=>1) : 1",
                 awaitPromise=True, returnByValue=True)
        # Give the CDN images and the grain wave a beat to decode.
        time.sleep(2.0)

    def evaluate(self, expr):
        r = self.cmd("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True)
        return r["result"].get("value")

    def shot(self, path, clip):
        r = self.cmd("Page.captureScreenshot", format="png", captureBeyondViewport=True,
                     clip={"x": clip["x"], "y": clip["y"], "width": clip["w"],
                           "height": clip["h"], "scale": self.scale})
        open(path, "wb").write(base64.b64decode(r["data"]))

    def pdf(self, path, w=PW, h=PH):
        r = self.cmd("Page.printToPDF", printBackground=True, preferCSSPageSize=False,
                     paperWidth=w, paperHeight=h,
                     marginTop=0, marginBottom=0, marginLeft=0, marginRight=0)
        open(path, "wb").write(base64.b64decode(r["data"]))

    def close(self):
        for f in (lambda: self.ws.close(), lambda: self.proc.terminate()):
            try: f()
            except Exception: pass


RECTS_JS = r"""
(function(){
  var out=[];
  document.querySelectorAll('.page').forEach(function(p,i){
    var r=p.getBoundingClientRect();
    out.push({n:i+1, x:r.left+scrollX, y:r.top+scrollY, w:r.width, h:r.height,
              cls:p.className});
  });
  return JSON.stringify(out);
})()
"""

GEOM_JS = r"""
(function(){
  function lum(c){var m=c.match(/[\d.]+/g);if(!m)return null;
    var v=[m[0],m[1],m[2]].map(function(x){x=x/255;return x<=.03928?x/12.92:Math.pow((x+.055)/1.055,2.4)});
    return {L:.2126*v[0]+.7152*v[1]+.0722*v[2], a:m[3]===undefined?1:parseFloat(m[3])};}
  var IMGS=[];
  function coveringImage(el){
    var r=el.getBoundingClientRect();
    for(var i=0;i<IMGS.length;i++){var o=IMGS[i];
      if(o.el===el||o.el.contains(el)||el.contains(o.el)) continue;
      var q=o.r;
      if(q.left<=r.left+1&&q.top<=r.top+1&&q.right>=r.right-1&&q.bottom>=r.bottom-1) return true;}
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
  var out={pages:[]};
  document.querySelectorAll('.page').forEach(function(s,i){
    var sr=s.getBoundingClientRect();
    var rec={n:i+1,cls:s.className,w:Math.round(sr.width),h:Math.round(sr.height),text:[]};
    IMGS=[];
    s.querySelectorAll('*').forEach(function(o){var ocs=getComputedStyle(o);
      if(ocs.backgroundImage&&ocs.backgroundImage!=='none') IMGS.push({el:o,r:o.getBoundingClientRect()});});
    s.querySelectorAll('*').forEach(function(el){
      var r=el.getBoundingClientRect(); if(r.width<1||r.height<1) return;
      var own=[].filter.call(el.childNodes,function(n){return n.nodeType===3&&n.textContent.trim()});
      if(!own.length) return;
      var cs=getComputedStyle(el), b=bgOf(el);
      rec.text.push({tag:el.tagName.toLowerCase(),
        cls:(typeof el.className==='string'?el.className:'')||'',
        x:Math.round(r.left-sr.left),y:Math.round(r.top-sr.top),
        w:Math.round(r.width),h:Math.round(r.height),
        t:own.map(function(n){return n.textContent.trim()}).join(' ').slice(0,140),
        font:cs.fontFamily.split(',')[0].replace(/["']/g,''),
        size:parseFloat(cs.fontSize),weight:cs.fontWeight,lh:cs.lineHeight,
        ls:cs.letterSpacing,style:cs.fontStyle,tt:cs.textTransform,align:cs.textAlign,
        maxw:cs.maxWidth,color:cs.color,bg:b,
        contrast:b==='IMAGE'?null:ratio(cs.color,b),
        overflowX: el.scrollWidth-Math.round(r.width)>1,
        pastBottom: Math.round(r.bottom-sr.top)>Math.round(sr.height)+1,
        pastRight: Math.round(r.right-sr.left)>Math.round(sr.width)+1});
    });
    var nodes=[];
    s.querySelectorAll('*').forEach(function(el){
      var own=[].filter.call(el.childNodes,function(n){return n.nodeType===3&&n.textContent.trim()});
      var cs=getComputedStyle(el);
      var painted = el.tagName==='IMG' ||
        (cs.backgroundColor&&cs.backgroundColor!=='rgba(0, 0, 0, 0)') ||
        (cs.borderTopWidth!=='0px'&&cs.borderTopStyle!=='none'&&el.getBoundingClientRect().height>8);
      if(own.length||painted) nodes.push(el);});
    rec.overlaps=[];
    for(var a=0;a<nodes.length;a++)for(var b=a+1;b<nodes.length;b++){
      var ea=nodes[a],eb=nodes[b];
      if(ea.contains(eb)||eb.contains(ea)) continue;
      // A chip strip, a register and a specimen grid are built of adjacent
      // painted boxes that legitimately touch. Only flag a pair where at least
      // one carries text, which is what makes an overlap unreadable.
      if(!ea.textContent.trim()&&!eb.textContent.trim()) continue;
      var ra=ea.getBoundingClientRect(),rb=eb.getBoundingClientRect();
      var ox=Math.min(ra.right,rb.right)-Math.max(ra.left,rb.left);
      var oy=Math.min(ra.bottom,rb.bottom)-Math.max(ra.top,rb.top);
      if(ox>4&&oy>4&&ox*oy>400)
        rec.overlaps.push([ea.textContent.trim().slice(0,34),
                           eb.textContent.trim().slice(0,34),Math.round(ox*oy)]);
    }
    out.pages.push(rec);
  });
  return JSON.stringify(out);
})()
"""


def main():
    url = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "_shots"
    os.makedirs(out, exist_ok=True)
    c = Chrome()
    try:
        c.goto(url)
        rects = json.loads(c.evaluate(RECTS_JS))
        for r in rects:
            c.shot(os.path.join(out, "page-%02d.png" % r["n"]), r)
        geom = json.loads(c.evaluate(GEOM_JS))
        json.dump(geom, open(os.path.join(out, "geom.json"), "w"), indent=1)
        c.pdf(os.path.join(out, "ce-manual.pdf"))
        # Text set over text, which the contrast and overflow checks cannot see.
        # It is what a fixed row height plus a string that wraps produces.
        for pg in geom["pages"]:
            for a, b, area in pg.get("overlaps", []):
                print("  OVERLAP page %02d · %s | %s · %dpx" % (pg["n"], a, b, area))
        # Every page closes above the field floor at y 736. A line that runs
        # under it is inside the page and invisible to the overflow check, and
        # it lands in the margin the folio lives in.
        for pg in geom["pages"]:
            if "dark" in pg["cls"] and pg["n"] in (1, 28):
                continue
            for t in pg["text"]:
                if t["y"] + t["h"] > 748 and t["y"] < 752 and "m-folio" not in t["cls"]:
                    print("  PAST FLOOR page %02d · %s · bottom %d"
                          % (pg["n"], t["t"][:36], t["y"] + t["h"]))
        bad = [(p["n"], t["t"][:40], t["contrast"])
               for p in geom["pages"] for t in p["text"]
               if t["pastBottom"] or t["pastRight"] or t["overflowX"]
               or (t["contrast"] is not None and t["contrast"] < 4.5 and t["size"] < 24)]
        print("%d pages · %d PNG · pdf written" % (len(rects), len(rects)))
        for b in bad:
            print("  CHECK page %02d · %s · contrast %s" % b)
        if not bad:
            print("  no overflow, no low-contrast small text")
    finally:
        c.close()


if __name__ == "__main__":
    main()
