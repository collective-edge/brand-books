#!/usr/bin/env python3
"""Generate one brand book per brand from the published v1.0 kits.

The books load type-system.css and palette.css straight from the CDN, so they
are a live test of the house system: identical type layer, palette swapped.
"""
import json, os, re, html

HERE = os.path.dirname(os.path.abspath(__file__))
KITS = "/Users/jacob.sarasohn/collective-edge"
REG = json.load(open(f"{KITS}/collective-edge-brand-kit/brands.json", encoding="utf-8"))
TOK = json.load(open(f"{KITS}/collective-edge-brand-kit/snippets/type-tokens.json", encoding="utf-8"))
# The floor under the co-brand lockup, from the parent kit's own tokens.json.
# cobrand.css calls it a floor and not a target, and section 07 says so where it
# prints the fallback, so the figure is read from the kit rather than typed.
CE_FLOOR = json.load(open(f"{KITS}/collective-edge-brand-kit/tokens.json",
                          encoding="utf-8"))["logos"]["minWidth"]["horizontal"]
PIN = "@v1.1"
NB = "\u00a0"
NUM = {2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}
CDN_ROOT = "https://cdn.jsdelivr.net/gh/collective-edge/"

# One source of truth for the section list. The contents rows, the eyebrow
# badges and the headings all read from it, so a reader who follows a row
# arrives at a page with the same number and the same words on it.
SECTIONS = ["The brand", "The mark", "Mark variants", "Colour", "Colour in use",
            "Contrast, measured", "Powered by Collective Edge", "Typeface",
            "Four weights", "The ladder", "Composition", "Components",
            "Do and do not", "Assets"]

# The partner mark on the co-brand specimen. 158px is the width the shipped
# mode A snippet in the Collective Edge kit's reference/layout.md sets under the
# 204px CE lockup, and the difference is the point: 204 - 158 = 46px of hairline
# running past the right edge of the mark above it.
MARK_W = 158

# The co-brand label on each brand's own dark band, as cobrand.css publishes it.
# label_contrast() recomputes every figure from that brand's palette.css and
# refuses to build if one has moved, so these three numbers cannot go stale.
LABEL_CONTRAST = {"apex-brand-kit": 5.98, "royal-brand-kit": 6.61,
                  "collective-edge-brand-kit": 7.84}


# ---------- contrast ----------
def lum(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def ratio(a, b):
    l1, l2 = sorted([lum(a), lum(b)], reverse=True)
    return (l1 + .05) / (l2 + .05)


def verdict(r):
    return ("pass", "AA any size") if r >= 4.5 else \
           (("large", "large or bold") if r >= 3 else ("fail", "fails"))


def palette_value(repo, name):
    """Resolve a semantic colour out of that brand's published palette.css.

    The book prints measured contrast ratios, so the foreground it names has
    to be the one the stylesheet actually paints, not a literal typed here.
    """
    path = f"{KITS}/{repo.split('/')[-1]}/snippets/palette.css"
    decl = {}
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;]+);", open(path, encoding="utf-8").read()):
        decl.setdefault(m.group(1), m.group(2).strip())
    v = decl.get(name)
    while v and v.startswith("var("):
        v = decl.get(v[4:-1].strip())
    return v


def label_contrast(repo):
    """The co-brand label on that brand's own dark band, measured not cited.

    cobrand.css publishes 5.98:1 for Apex, 6.61:1 for Royal and 7.84:1 for
    Collective Edge. Section 07 paints the same label on the same grounds, so
    it recomputes the figure with the WCAG formula above and stops the build if
    a palette has moved under the number the comment beside it names. Returns
    the two colours it measured, which is what the Collective Edge book writes
    inline when it borrows a partner's band.
    """
    fg = palette_value(repo, "--fg-on-dark-3")
    bg = palette_value(repo, "--bg-band")
    r = ratio(fg, bg)
    want = LABEL_CONTRAST[repo.split("/")[-1]]
    if round(r, 2) != want:
        raise SystemExit(f"co-brand label on {repo}: {r:.2f}:1 against a stated {want}:1")
    return fg, bg


def surface_tint(repo, col):
    """The tint the book actually paints.

    Two files in the kit answer this question. brands.json publishes
    color.surfaceTint; palette.css publishes --bg-surface, and --bg-surface is
    what every panel, table stripe and callout in this book paints. All three
    brands now agree: #F3F3FB for Apex, #FAF5FD for Royal, #FAFAFA for
    Collective Edge. Collective Edge did not. brands.json typed #F4F4F4 while
    palette.css resolved --bg-surface to --ce-bone, #FAFAFA, which tokens.json
    publishes under the same name; the registry entry has been corrected to the
    paint in all three kits. The fallback stays, because a brand that ships no
    palette.css still has to resolve.
    """
    return (palette_value(repo, "--bg-surface") or col["surfaceTint"]).upper()


# The swatch caption is a claim about one brand's palette, so one set of
# strings cannot serve three. Apex is blue structure and a gold spark, which
# is what the shared strings were written for. Royal is purple end to end, and
# royal-brand-kit/tokens.json calls #43205B the logo fill, not a signature
# highlight. Collective Edge overrides every chip from its own tokens.json in
# sw_entry below, so its entries here never reach the page.
SWATCH_USE = {
    "apex": {
        "Primary":     "Headers, links, accent rules, column heads",
        "Deep":        "Hero bands, full-width strips, footers",
        "Accent":      "The spark. A highlight, never a large field",
        "Accent deep": "The text-safe step of the gold",
        "Surface":     "Alternating rows, callouts, quiet panels",
    },
    "royal": {
        "Primary":     "The workhorse. Column heads, accent bars, links, brand text on white",
        "Deep":        "The dominant tone. Header bands, hero grounds, dividers, table heads",
        "Accent":      "The logo fill on light. An alternate dark accent, never a field",
        "Accent deep": "The text-safe step of the accent",
        "Surface":     "Alternating rows, callouts, quiet panels",
    },
    "collective-edge": {
        "Primary":     "Headers, links, accent rules, column heads",
        "Deep":        "Hero bands, full-width strips, footers",
        "Accent":      "The signature. A highlight, never a large field",
        "Accent deep": "The text-safe step of the accent",
        "Surface":     "Alternating rows, callouts, quiet panels",
    },
}

HEX_RE = re.compile(r"#[0-9a-fA-F]{6}\b")
E = html.escape


def P(s):
    """A sentence in a .ref value column, rather than a value.

    The column no longer takes the mono by selector, so this no longer switches
    a face. It marks the cells that are prose, and running prose keeps
    proportional figures where the column around it is tabular (rule 14).
    "flush left, ragged right" is a sentence, not a string anybody retypes.
    """
    return f'<span class="prose">{E(s)}</span>'


def ce_palette():
    """The Collective Edge palette, keyed by hex, with each token's own name
    and its own use string. CE ships no accent, so it cannot borrow the accent
    narrative the operating companies share."""
    t = json.load(open(f"{KITS}/collective-edge-brand-kit/tokens.json", encoding="utf-8"))
    return {v["hex"].upper(): (k.title(), v["use"])
            for k, v in t["palette"].items() if isinstance(v, dict) and v.get("hex")}


def hex_code(s):
    """One hex is one string, and rule 13 puts a colour value in the mono face
    wherever it stands, running prose included. The registry types some of them
    lower, so they are cased here too. Returns escaped HTML: the caller inserts
    it raw, because the whole point is the span around each match. The slide 3
    standfirst used to set its hexes in Montserrat while the At a glance panel
    beside it set the same value in .bk-code."""
    out, i = [], 0
    for m in HEX_RE.finditer(s):
        out.append(E(s[i:m.start()]))
        out.append('<span class="bk-code">%s</span>' % m.group(0).upper())
        i = m.end()
    out.append(E(s[i:]))
    return "".join(out)


def slide(cls, inner, foot=None, n=None, book=None):
    f = ""
    if foot is not False:
        f = f'<div class="s-foot"><span>{E(book)}</span><span>{n:02d}</span></div>'
    return f'<section class="slide {cls}">{inner}{f}</section>\n'


def head(eyebrow, title, sub=None):
    s = f'<p class="bk-body-lg sub">{E(sub)}</p>' if sub else ""
    return (f'<div class="s-head"><p class="bk-eyebrow">{E(eyebrow)}</p>'
            f'<h2 class="bk-h1">{E(title)}</h2>{s}</div><div class="s-rule"></div>')


def sec(i, sub=None):
    """Section i, numbered and titled from SECTIONS."""
    return head(f"{i:02d}", SECTIONS[i - 1] + ".", sub)


def build(key):
    b = REG["brands"][key]
    cdn = f"https://cdn.jsdelivr.net/gh/{b['repo']}{PIN}/"
    ce = f"https://cdn.jsdelivr.net/gh/collective-edge/collective-edge-brand-kit{PIN}/"
    col = b["color"]
    name = b["name"]
    logos = {r: cdn + p for r, p in b["logos"].items() if p}
    is_ce = key == "collective-edge"
    band_rule = col.get("bandRule") or "transparent"
    surface = surface_tint(b["repo"], col)
    USE = SWATCH_USE[key]
    n = 0
    S = []

    def add(cls, inner, foot=True):
        nonlocal n
        n += 1
        S.append(slide(cls, inner, foot=None if foot else False, n=n, book=name))

    # 01 COVER
    # One style attribute only. Two on the same element and the parser keeps the
    # first and silently drops the second, which is what blanked the CE cover.
    cover_bg = f"background:#000 url({ce}assets/imagery/CE_Background_1920.jpg) center/cover no-repeat;" if is_ce \
        else "background:var(--bg-band);"
    # The grain puts its bright lobe upper left, which is where the mark sits.
    # The scrim ran light to dark top to bottom, so it protected the headline
    # and left the wordmark on ground as light as 2.35:1. It has to close at
    # the top too. Apex and Royal sit on a flat band and keep the old ramp.
    scrim = ("rgba(0,0,0,.72) 0%,rgba(0,0,0,.14) 30%,rgba(0,0,0,.10) 40%,rgba(0,0,0,.70) 100%"
             if is_ce else
             "rgba(0,0,0,.10) 0%,rgba(0,0,0,.10) 40%,rgba(0,0,0,.70) 100%")
    add("cover dark bk-on-dark", f"""
      <div style="{cover_bg}position:absolute;inset:0;z-index:0"></div>
      <div style="position:absolute;inset:0;z-index:0;background:linear-gradient(180deg,{scrim})"></div>
      <img class="mark" style="z-index:1" src="{logos['horizontal-on-dark']}" alt="{E(name)}">
      <div style="position:relative;z-index:1">
        <h1 class="bk-display-lg">Brand guidelines</h1>
        <p class="meta">{E(name)} &nbsp;·&nbsp; House type system v1.0 &nbsp;·&nbsp; 2026</p>
      </div>
      <div class="rule-accent" style="background:{band_rule};z-index:1"></div>""", foot=False)

    # 02 CONTENTS
    # Two columns of seven. A row is intrinsically 56px, 12 + 12 padding, 1
    # border and a 31px line box, so fourteen in one column would be 784px
    # against a 460px body. Seven auto tracks in that body are not intrinsic
    # either: they stretch to fill it, so the measured pitch is 460 / 7 =
    # 65.71px and the seventh row bottoms on the y804 floor exactly.
    rows = "".join(
        f'<div style="display:grid;grid-template-columns:56px 1fr;gap:20px;padding:12px 0;'
        f'border-top:1px solid var(--border-1)">'
        # Nobody dictates a table of contents number and nobody retypes one, and
        # 01 to 14 is a closed set a reader scans, so rule 13 leaves it in
        # Montserrat. It reads as a column, so it takes the tabular figures the
        # mono was doing the aligning with.
        f'<span style="font-size:12px;color:var(--fg-3);'
        f'font-variant-numeric:tabular-nums lining-nums">{i + 1:02d}</span>'
        f'<span class="bk-body-lg">{E(t)}</span></div>'
        for i, t in enumerate(SECTIONS))
    # The column break now lands on the sentence break: column one is this
    # brand, column two is the type system. "The first" and "The last" are cut
    # because the standfirst they were in already measured 713.9px of the
    # 714.96px it is given, and six to seven would have broken it to two lines
    # with a three-word second. The 01 to 14 numerals carry the order instead.
    add("", head("Contents", "Fourteen sections.",
                 "Seven are this brand. Seven are the type system it runs on.")
        + f'<div class="s-body" style="display:grid;grid-template-columns:656px 656px;'
          f'gap:0 64px;grid-template-rows:repeat(7,auto);grid-auto-flow:column">{rows}</div>')

    # 03 THE BRAND
    # The parent-and-house relation is the standfirst, so the body carries the
    # two lists instead of a paragraph saying the same thing in prose.
    if not is_ce:
        lede = hex_code(b.get("colorNote", ""))
        standing = "An operating company of Collective Edge."
    else:
        # The ramp is the eleven --ce-* steps in palette.css, #000000 to
        # #FFFFFF. It used to be named as ending on #F4F4F4, which is --ce-paper,
        # the ninth step, and the same slide's glance table prints #FAFAFA as
        # the surface two rows down.
        lede = hex_code(
            "Collective Edge is the parent. It has no hue of its own and runs an eleven-step "
            "grey ramp from #000000 to #FFFFFF. On a co-brand surface the Edge wedge takes "
            "the partner’s colour and Collective Edge stays grey.")
        standing = "The parent of the house."
    mn = b.get("minWidth", {})
    scale_span = f"{len(TOK['scale'])} steps · {TOK['scale'][0]['px']}px to {TOK['scale'][-1]['px']}px"
    # A kit that publishes no minimum says so. Falling through to another
    # brand's numbers would print a spec this kit does not hold.
    # The third field is rule 13: 1 marks a cell whose whole string is on the
    # mono whitelist, and only those cells take .bk-code. The four hexes are
    # retyped into a stylesheet or a picker, and the kit and registry names
    # resolve against a real path. Everything else here is read and not
    # transcribed. A weight list, a scale span, a measure and a minimum size
    # are measurements, and a measurement is Montserrat.
    glance = [("Typeface", P("Montserrat"), 0),
              ("Weights", "400 · 600 · 700 · 800", 0),
              ("Scale", scale_span, 0),
              ("Italic", P("none, at any weight"), 0),
              ("Measure", "54ch " + P(f"= {TOK['measure']['body']['realChars']}{NB}characters"), 0),
              ("Primary", col["primary"].upper(), 1),
              ("Accent", col["accent"].upper(), 1),
              ("Band", col["bandBackground"].upper(), 1),
              ("Surface", surface, 1),
              ("Minimum mark", f"{E(mn['horizontal'])} {P('horizontal,')} {E(mn['mark'])} {P('mark')}"
                               if mn else P("not published in this kit"), 0),
              ("Kit", E(b["repo"].split("/")[-1]), 1),
              ("Registry", f"brands.json · {E(key)}", 1)]
    gr = "".join("<tr><td>{}</td><td{}>{}</td></tr>".format(
        E(k2), ' class="bk-code"' if c else "", v) for k2, v, c in glance)
    owns = [f"The mark, in {NUM.get(len(logos), len(logos))} named roles", "The palette",
            "The surface tint", "The proportion it sets them in"]
    house = ["Montserrat, and no italic", "The twelve-step ladder", "The four weights",
             "The composition rules"]

    def col_list(title, items):
        li = "".join(f'<li class="bk-body">{E(x)}</li>' for x in items)
        return (f'<div><p class="bk-eyebrow">{E(title)}</p>'
                f'<ul style="list-style:none;margin:16px 0 0;padding:0;display:flex;'
                f'flex-direction:column;gap:12px">{li}</ul></div>')
    add("", sec(1, standing) + f"""
      <div class="s-body" style="display:grid;grid-template-columns:736px 576px;gap:64px">
        <div>
          <p class="bk-body-lg">{lede}</p>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:64px;margin-top:64px">
            {col_list("This brand owns", owns)}{col_list("The house owns", house)}
          </div>
        </div>
        <div style="border:1px solid var(--border-1);padding:32px">
          <p class="bk-eyebrow">At a glance</p>
          <table class="ref" style="margin-top:8px">{gr}</table>
        </div>
      </div>""")

    # 04 THE MARK
    add("", sec(2, "The primary lockup. Use it wherever there is horizontal room.") + f"""
      <div class="s-body"><div class="logo-stage">
        <div><img src="{logos['horizontal-on-light']}" alt="{E(name)}"></div>
        <div class="on-dark"><img src="{logos['horizontal-on-dark']}" alt="{E(name)}"></div>
      </div></div>""")

    # 05 VARIANTS
    # Every role the registry publishes gets a cell. Overwriting mark-on-dark
    # with stacked-on-dark hid a shipped file in the Royal book, on the slide
    # that lists the files. The cell prints the role and the file it resolves
    # to, because the two are named on different principles.
    cells = []
    order = [r for r in ("horizontal-on-light", "horizontal-on-dark",
                         "compact-on-light", "compact-on-dark", "mark-on-light",
                         "mark-on-dark", "stacked-on-dark") if r in logos]
    for role in order:
        dk = role.endswith("-on-dark")
        # The horizontal SVGs paint ink to the edge of their own box, so a
        # flush frame gave the mark zero clear space on the slide that
        # publishes the clear-space rule.
        cells.append(f'<div><div class="frame {"dk" if dk else ""}" style="padding:24px">'
                     f'<img src="{logos[role]}" alt=""></div>'
                     # The role is the name you ask for and the filename is the
                     # string you type into a src, so the two lines take two
                     # faces (rule 13). Role keys are lowercase words and
                     # hyphens and never carry a digit, so the confusable pairs
                     # cannot occur in that class at all.
                     f'<div class="cap">{E(role)}<br>'
                     f'<span class="bk-code" style="color:var(--fg-3)">'
                     f'{E(b["logos"][role].split("/")[-1])}</span>'
                     f'</div></div>')
    caps = []
    if mn:
        # The caption names every minimum the registry publishes for this brand.
        # A kit that ships a compact lockup publishes a third floor, and leaving
        # it out prints a spec sheet the registry contradicts.
        parts = [f'horizontal {E(mn["horizontal"])} on screen, 1&nbsp;inch in print']
        if mn.get("compact"):
            parts.append(f'compact {E(mn["compact"])}')
        parts.append(f'mark {E(mn["mark"])}')
        caps.append('<p class="bk-caption" style="margin:0">Minimum size &nbsp;·&nbsp; '
                    + ' &nbsp;·&nbsp; '.join(parts) + '</p>')
    caps.append('<p class="bk-caption" style="margin:0">Clear space &nbsp;·&nbsp; '
                'the height of the mark, on all four sides</p>')
    add("", sec(3, "Ask for the role. The role names the background it sits on, the file names "
                   "its own ink. Never recolour a mark.") + f"""
      <div class="s-body">
        <div class="logo-grid" style="grid-template-columns:repeat({len(order)},1fr)">{''.join(cells)}</div>
        <div style="display:grid;grid-template-columns:656px 656px;gap:0 64px;margin-top:24px">{''.join(caps)}</div>
      </div>""")

    # 06 COLOUR
    CEPAL = ce_palette() if is_ce else {}

    def sw_entry(nm, hx, use):
        """Collective Edge labels every chip with its own token name and its own
        published use. tokens.json calls #C8C8C8 "The Edge wedge when CE stands
        alone. Never text", where the shared accent string called it a
        signature highlight, and #6E6E6E is tertiary text, not an accent step."""
        if hx.upper() in CEPAL:
            return (CEPAL[hx.upper()][0], hx, CEPAL[hx.upper()][1])
        return (nm, hx, use)

    pal = [sw_entry("Primary", col["primary"], USE["Primary"]),
           sw_entry("Deep", col["primaryDeep"], USE["Deep"])]
    if col.get("primaryLight"):
        # Royal's light purple clears AA on white and is still reserved, and the
        # book says so five pages before it measures it. Apex's is 2.74:1 and
        # genuinely fails, so the two brands cannot share one sentence.
        lt = ratio(col["primaryLight"], "#FFFFFF")
        use = ("Tertiary accents and hover. %.2f:1 on white, and still reserved" % lt) \
            if lt >= 4.5 else "Tertiary accents and hover only, never text"
        pal.append(sw_entry("Light", col["primaryLight"], use))
    pal.append(sw_entry("Accent", col["accent"], USE["Accent"]))
    if col.get("accentDeep") and col["accentDeep"] != col["primaryDeep"]:
        pal.append(sw_entry("Accent deep", col["accentDeep"], USE["Accent deep"]))
    pal.append(sw_entry("Surface", surface, USE["Surface"]))
    sw = ""
    for nm, hx, use in pal:
        r = int(hx.lstrip("#")[0:2], 16), int(hx.lstrip("#")[2:4], 16), int(hx.lstrip("#")[4:6], 16)
        sw += (f'<div class="swatch"><div class="chip" style="background:{hx}"></div>'
               f'<div class="info"><p class="nm">{E(nm)}</p>'
               f'<div class="hex">{hx.upper()}<br>{r[0]} {r[1]} {r[2]}</div>'
               f'<p class="use">{E(use)}</p></div></div>')
    # The exclusivity claim used to be unqualified, and three later pages then
    # printed hues that are in no brand palette. Naming section 12 alone still
    # undercounted: house status colour carries the verdict tabs on section 06
    # and the do and do not marks on section 13 as well. The claim is scoped to
    # brand elements and every page that breaks it is named. Two lines at 20px
    # in a 715px column, which is what the fixed 160px head box holds. The two
    # later numbers each moved up one when section 07 was inserted before them.
    add("", sec(4, "Every brand element draws from this palette exclusively. "
                   "The exception is house status colour, on sections 06, 12 and 13.")
        + f'<div class="s-body"><div class="swatches">{sw}</div></div>')

    # 07 COLOUR IN USE
    # A 2px canvas seam between the bands. Royal's accent is darker than its
    # primary (1.28:1 across that edge) and CE's deep and primary read as one
    # block at 1.11:1, so without a seam the bar cannot show the proportion
    # the slide exists to teach.
    canvas = palette_value(b["repo"], "--bg-canvas") or "#FFFFFF"
    bands = [(52, canvas, "canvas"), (26, col["primaryDeep"], "deep"),
             (16, col["primary"], "primary"), (6, col["accent"], "accent")]
    bar_cells = "".join(
        f'<div style="flex:{w};background:{c};'
        f'{"" if i == 0 else "border-left:2px solid var(--bg-canvas)"}"></div>'
        for i, (w, c, _) in enumerate(bands))
    # Each band prints the hex it paints. CE runs #000000 against #111111 here,
    # a 1.11:1 seam, and the label is the only thing that can tell them apart.
    bar_labels = "".join(
        f'<div style="flex:{w}">{w}% {E(t)}'
        f'<div style="font-family:var(--font-mono);color:var(--fg-2);margin-top:4px">{c.upper()}</div>'
        f'</div>' for w, c, t in bands)
    # Royal's accent is darker than the primary it punctuates, so it cannot spark.
    spark = "sparks" if lum(col["accent"]) > lum(col["primary"]) else "punctuates"
    add("", sec(5, "Proportion is the rule nobody writes down. The deep tone anchors, "
                   f"the primary structures, the accent {spark}.") + f"""
      <div class="s-body">
        <div style="display:flex;height:152px;border:1px solid var(--border-1)">{bar_cells}</div>
        <div style="display:flex;margin-top:16px;font-size:12px;color:var(--fg-3)">
          {bar_labels}
        </div>
        <div class="demo-grid" style="margin-top:32px">
          <div class="demo"><div class="lbl">Deep over primary</div><div style="padding:0">
            <div class="d-band"><span class="bk-h4 bk-caps" style="color:var(--fg-on-dark-1)">Interfacility transport</span></div>
            <div class="d-sub"><span class="bk-eyebrow" style="color:var(--fg-on-dark-1);margin:0">Partner briefing</span></div>
          </div></div>
          <div class="demo"><div class="lbl">Stat, accent rule only</div><div class="inner">
            <div class="d-stat">
              <div class="st"><p class="bk-eyebrow">Median minutes</p><div class="bk-stat">22</div></div>
              <div class="st"><p class="bk-eyebrow">Runs</p><div class="bk-stat">1,284</div></div>
            </div>
          </div></div>
        </div>
      </div>""")

    # 08 CONTRAST
    # One direction per pair. Contrast is symmetric, and seven rows carrying
    # five distinct measurements read as padding.
    muted = palette_value(b["repo"], "--fg-2")
    tests = [("#FFFFFF", col["bandBackground"], "White on the band"),
             (col["primary"], "#FFFFFF", "Primary and white, either direction")]
    if col.get("accentDeep") and col["accentDeep"] != col["primaryDeep"]:
        tests.append((col["accentDeep"], "#FFFFFF", "Accent deep as text on white"))
    tests.append((col["accent"], "#FFFFFF", "Accent as text on white"))
    if col.get("primaryLight"):
        tests.append((col["primaryLight"], "#FFFFFF", "Light on white"))
    if muted:
        tests.append((muted, surface, "Secondary text on the surface tint"))
    tests.append(("#FFFFFF", REG["diagramRoles"]["decision"]["fill"], "White on decision green"))
    pr = ""
    for fg, bg, lbl in tests:
        r = ratio(fg, bg)
        cl, txt = verdict(r)
        # The hex pair is two colour values with a connective between them, and
        # both are copied, so the whole string takes the mono. The ratio is a
        # computed measurement and the verdict is a sentence about it, and rule
        # 13 leaves both in Montserrat. Three spans, because the faces differ.
        pr += (f'<div class="pair"><div class="demo" style="background:{bg};color:{fg}">Aa 16px</div>'
               f'<div class="spec"><span>{E(lbl)}</span>'
               f'<span class="hx">{fg.upper()} on {bg.upper()}</span></div>'
               f'<div class="verdict {cl}"><span class="r">{r:.2f}:1</span>'
               f'<span class="w">{E(txt)}</span></div></div>')
    add("", sec(6, "Computed with the WCAG relative-luminance formula, not estimated. "
                   "A pair marked large or bold is never body copy.")
        + f'<div class="s-body"><div class="pairs">{pr}</div></div>')

    # 09 POWERED BY COLLECTIVE EDGE
    # The lockup is not redrawn here. The head loads the kit's own cobrand.css
    # from the CDN beside type-system.css and palette.css, and this slide sets
    # the shipped markup against it, so 204px, the 24 / 1 / 24 / 12 spacing, the
    # 0.080em label and both hairline colours are read from that file rather
    # than retyped in book.css.
    #
    # The 204px track is the whole size argument. The mark above it is 158px, so
    # the hairline cobrand.css draws across the top of .ce-powered runs
    # 204 - 158 = 46px past the mark's right edge. Drawn, not asserted.
    cb = REG["cobrand"]
    lw = cb["lockup"]["width"].removesuffix("px")
    lh = cb["lockup"]["height"].removesuffix("px")

    def kit_url(k, role):
        """(url, kit, filename) for one brand's mark. All three resolve from the
        registry through the same split section 03 uses for its captions, so no
        path and no filename is typed on this slide."""
        bb = REG["brands"][k]
        rel = bb["logos"][role]
        return (f"https://cdn.jsdelivr.net/gh/{bb['repo']}{PIN}/" + rel,
                bb["repo"].split("/")[-1], rel.split("/")[-1])

    def an(measure, *codes):
        """The annotation beside a mark. A mixed string, split at the element and
        never at the line (rule 13). The first line is a width, which is read off
        the page and not retyped, so it sets in Montserrat with tabular figures.
        The repo name and the filename under it are a package identifier and a
        path, both of which resolve against something real, so they take the
        mono."""
        return ('<div class="an">' + E(measure) + '<br><span class="bk-code">'
                + "<br>".join(E(x) for x in codes) + '</span></div>')

    def specimen(k, role, ground, light):
        """One specimen: the partner mark at 158 in a fixed bottom-aligned box,
        then the shipped .ce-powered block bound to the 204px track, each with
        its own measurements beside it rather than in a table across the slide.
        """
        src, kit, fn = kit_url(k, role)
        ce_src, ce_kit, ce_fn = kit_url(
            "collective-edge", "horizontal-on-light" if light else "horizontal-on-dark")
        return (f'<div{ground}><div class="spec">'
                f'<img src="{src}" alt="{E(REG["brands"][k]["name"])}" width="{MARK_W}">'
                + an(f"{MARK_W} px", kit, fn)
                + f'<div class="{E(cb["classes"]["light" if light else "dark"])}">'
                  f'<span>{E(cb["label"])}</span>'
                  f'<img src="{ce_src}" alt="CE · Collective Edge" '
                  f'width="{lw}" height="{lh}"></div>'
                + an(f"{lw} × {lh} px", ce_kit, ce_fn)
                + '</div></div>')

    if is_ce:
        # The mirror. The parent book shows the same construction it asks the
        # partners for, partner mark above and the CE lockup below, on each
        # partner's own band. Both grounds and both label greys resolve through
        # palette_value(), so cobrand.css reads that partner's own token and the
        # parent book prints the ratios the partner books print.
        # LABEL CONTRAST, computed by label_contrast() with the WCAG formula:
        # #9EA5C4 on Apex #1D225E is 5.98:1, #B0A2BC on Royal #2f193b is 6.61:1.
        # --border-on-dark is rgba(255,255,255,0.12) in all three kits, so the
        # hairline needs no override.
        cells = []
        for pk in ("apex", "royal"):
            pfg, pbg = label_contrast(REG["brands"][pk]["repo"])
            cells.append(specimen(pk, "horizontal-on-dark",
                                  f' class="dk bk-on-dark" style="background:{pbg};'
                                  f'--fg-on-dark-3:{pfg}"', False))
    else:
        # Cell A is the shipped default on this brand's own --bg-band, cell B
        # the light-surface variant on --bg-canvas and never on --bg-surface:
        # on the tint the same label grey measures 4.31:1 for Apex and 4.43:1
        # for Royal. LABEL CONTRAST on the band, computed by label_contrast():
        # Apex #9EA5C4 on #1D225E 5.98:1, Royal #B0A2BC on #2f193b 6.61:1.
        # On white the label takes --fg-3, #64748B, 4.76:1 in both books.
        label_contrast(b["repo"])
        cells = [specimen(key, "horizontal-on-dark", ' class="dk bk-on-dark"', False),
                 specimen(key, "horizontal-on-light", "", True)]
    # Specimen first and identification second, the same order as the two cells
    # beside it, so the three read as one system. This is the cell that carries
    # the floor, because the floor and the fallback answer the same question.
    fallback = (f'<div><p class="bk-eyebrow" style="margin:0 0 16px">Text only</p>'
                f'<p class="{E(cb["classes"]["textOnly"])}">{E(cb["phrase"])}</p>'
                # A leading dot means a reader is about to type it into markup,
                # so the selector takes the mono and the measurements after it
                # do not (rule 13).
                f'<div class="an" style="margin-top:12px">'
                f'<span class="bk-code">.{E(cb["classes"]["textOnly"])}</span>'
                f' · 12 px · 600 · 0.080em</div>'
                f'<p class="bk-body-sm" style="margin:16px 0 0">The last resort. A narrow rail '
                f'takes the lockup down to the {E(CE_FLOOR)} floor first. '
                f'{E(cb["lockup"]["width"])} is the target everywhere else.</p></div>')
    # The intent line sits in the body and not in the standfirst, which is spoken
    # for by the rule. Section 01 already opens on "An operating company of
    # Collective Edge"; this cell is the payoff of that line, six sections later.
    if is_ce:
        pair = " and ".join(REG["brands"][k2]["name"] for k2 in ("apex", "royal"))
        relation = (f"{pair} are operating companies of Collective Edge. This is the lockup "
                    "they carry, set here the way the parent asks for it.")
    else:
        relation = (f"{name} is an operating company of Collective Edge. The lockup is where "
                    "that shows, and a reader who notices it can follow the thread.")
    # Verbatim from brands.json cobrand.placement, entries 1, 2 and 6.
    belongs = [cb["placement"][i] for i in (0, 1, 5)]
    # brands.json cobrand.doNot entries 3, 4 and 5. The imperative is dropped
    # because the eyebrow supplies it, and entry 4 is cut from "a patient-facing
    # consent or safety document" so that it sets on one line in the 316px cell
    # like the two beside it. Entries 1 and 2 are the merge prohibitions and are
    # deliberately absent: they are the standfirst, and a list that restated the
    # head of the slide would be filler.
    forbidden = ["On a clinical instruction",
                 "On a patient consent or safety form",
                 "Twice on one surface"]
    # The rule is the standfirst, in the position every other section slide
    # reserves for the one idea of the page. It is the thing a reader must not
    # get wrong, and no cell below repeats it.
    add("", sec(7, "The lockup rides beside the partner brand, never inside it. "
                   "A hairline keeps the two marks distinct." if is_ce else
                "The Collective Edge lockup rides beside this brand, never inside it. "
                "A hairline keeps the two marks distinct.") + f"""
      <div class="s-body"><div class="cobrand">
        {cells[0]}{cells[1]}{fallback}
        <div><p class="bk-eyebrow">The relation</p><p class="bk-body">{E(relation)}</p></div>
        {col_list("Where it belongs", belongs)}{col_list("Where it does not", forbidden)}
      </div></div>""")

    # 10 TYPEFACE
    m = TOK["metrics"]
    add("", sec(8, "Every brand in the house sets in Montserrat. The kit ships the variable "
                   "font with the axis clamped from 400 to 800.") + f"""
      <div class="s-body" style="display:grid;grid-template-columns:1fr 380px;gap:64px">
        <div>
          <div style="font-size:150px;line-height:1;font-weight:var(--weight-bold);letter-spacing:-0.022em">Aa Gg Rr</div>
          <div class="alpha">ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 0123456789</div>
          <p class="bk-eyebrow" style="margin-top:32px">The mono, for codes</p>
          <div style="font-family:var(--font-mono);font-size:20px;line-height:1.4;
                      letter-spacing:0.02em;color:var(--fg-1);margin-top:8px">Il1 O0 · 1,284 · 08.26</div>
        </div>
        <div style="border:1px solid var(--border-1);padding:32px 28px">
          <p class="bk-eyebrow">Measured at weight 400</p>
          <table class="ref" style="margin-top:8px">
            <tr><td>Units per em</td><td>{m['unitsPerEm']}</td></tr>
            <tr><td>Cap height</td><td>{m['capHeight']}em</td></tr>
            <tr><td>x-height</td><td>{m['xHeight']}em</td></tr>
            <tr><td>x over cap</td><td>{m['xOverCap']}</td></tr>
            <tr><td>Ascender</td><td>{m['ascender']}em</td></tr>
            <tr><td>Descender</td><td>{abs(m['descender'])}em</td></tr>
            <tr><td>Line box</td><td>{m['naturalLineBox']}em</td></tr>
            <tr><td>Digit zero</td><td>{m['digitZeroAdvance']}em</td></tr>
            <tr><td>Letter advance</td><td>{m['avgLetterAdvance']}em</td></tr>
            <tr><td>vs Helvetica</td><td>{m['widthVsHelvetica']}</td></tr>
            <tr><td>1ch buys</td><td>{m['realCharsPerCh']}&nbsp;{P('chars')}</td></tr>
          </table>
          <p class="bk-caption" style="margin:16px 0 0">Montserrat runs {m['widthVsHelvetica']}
          wider than Helvetica. That is why no wrapping line leads below 1.05.</p>
        </div>
      </div>""")

    # 11 WEIGHTS
    # The two reserved rows carry no licensed specimen. A live sample at 200 or
    # 900 would put a banned weight in the source, which fails R2. They carried
    # an empty div instead, which drew the row rule to x1488 over a label column
    # that ends on x412. They now carry the clamp result: the same axis clamp
    # the standfirst names, set in the weight the banned step resolves to. 100,
    # 200 and 300 all land on 400; 900 lands on 800. Both are in the ladder.
    W = [(200, "100 · 200 · 300 Thin", "Reserved. Never at document sizes.",
          None, (400, "Clamps to Regular")),
         (400, "400 Regular", "Body, captions, footers, table cells",
          "Interfacility transport", None),
         (600, "600 SemiBold", "Subheads, uppercase labels, table headers",
          "Critical care ground", None),
         (700, "700 Bold", "Headings, emphasis in body, stat numerals",
          "Dispatch and staging", None),
         (800, "800 ExtraBold", "Hero and title bands, nothing else",
          "Bay Area coverage", None),
         (900, "900 Black", "Reserved. Closes its counters in print.",
          None, (800, "Clamps to ExtraBold"))]
    wr = "".join(
        f'<div class="wt-row{"" if spec else " off"}"><div class="m"><b>{E(lbl)}</b>{E(use)}</div>'
        + (f'<div class="sample" style="font-weight:{w}">{E(spec)}</div></div>' if spec
           else f'<div class="sample clamp" style="font-weight:{cl[0]}">{E(cl[1])}</div></div>')
        for w, lbl, use, spec, cl in W)
    add("", sec(9, "Each has exactly one job. The @font-face clamps the axis from 400 to 800, "
                   "so a banned weight renders at the nearest permitted one.")
        + f'<div class="s-body">{wr}</div>')

    # 12 SCALE
    # All twelve steps at true size, in two registers: display left, text right.
    # Clamping the specimen to 58px rendered 96 and 72 identically, on the one
    # slide whose whole job is to prove the ladder.
    def scale_rows(steps):
        out = ""
        for r in steps:
            px, tr = r["px"], r["tracking"]
            caps = tr is None
            if caps:
                tr = r["capsTracking"]
            spec = (f'{px}px · {r["pt"]}pt · {r["weight"]} · {r["leading"]} · {tr:+.3f}em'
                    + (" caps" if caps else ""))
            out += (f'<div class="scale-row"><div class="m"><b>{E(r["token"])}</b>{E(spec)}</div>'
                    f'<div class="sample" style="font-size:{px}px;font-weight:{r["weight"]};'
                    f'line-height:{r["leading"]};letter-spacing:{tr}em'
                    + (";text-transform:uppercase" if caps else "")
                    + '">Dispatch</div></div>')
        return out
    add("", sec(10, "Twelve steps. Eleven land on a whole point size, and body-sm lands on "
                   "10.5pt. The same scale sets in PowerPoint and Word.") + f"""
      <div class="s-body" style="display:grid;grid-template-columns:800px 512px;gap:0 64px">
        <div>{scale_rows(TOK["scale"][:5])}</div>
        <div>{scale_rows(TOK["scale"][5:])}</div>
      </div>""")

    # 13 COMPOSITION
    c = TOK["composition"]
    add("", sec(11, "A scale is not a type system. These rules make a page look set "
                    "rather than typed.") + f"""
      <div class="s-body" style="display:grid;grid-template-columns:1fr 1fr;gap:64px">
        <div>
          <table class="ref">
            <tr><td>Alignment</td><td>{P(c['alignment'])}</td></tr>
            <tr><td>Justified</td><td>{P(c['justify'])}</td></tr>
            <tr><td>Centred</td><td>{P(f"never past {NUM[c['centerMaxLines']]} lines")}</td></tr>
            <tr><td>Headings</td><td class="bk-code">text-wrap: {E(c['textWrapHeading'])}</td></tr>
            <tr><td>Paragraphs</td><td class="bk-code">text-wrap: {E(c['textWrapParagraph'])}</td></tr>
            <tr><td>Orphans / widows</td><td>{c['orphans']} / {c['widows']}</td></tr>
            <tr><td>Body measure</td><td>54ch {P(f"= {TOK['measure']['body']['realChars']}{NB}characters")}</td></tr>
            <tr><td>Caption measure</td><td>40ch {P(f"= {TOK['measure']['caption']['realChars']}{NB}characters")}</td></tr>
            <tr><td>Heading measure</td><td>28ch {P(f"= {TOK['measure']['heading']['realChars']}{NB}characters")}</td></tr>
            <tr><td>Heading case</td><td>{P(c['headingCase'])}</td></tr>
            <tr><td>Display case</td><td>{P(c['displayCase'])}</td></tr>
            <tr><td>Heading space</td><td>{P('3 above to 1 below')}</td></tr>
            <tr><td>Vertical rhythm</td><td>{P('multiples of 4')}</td></tr>
            <tr><td>Uppercase</td><td>{P('always tracked, never past four words')}</td></tr>
            <tr><td>Codes and IDs</td><td>{P('mono face. Nothing else takes it')}</td></tr>
          </table>
        </div>
        <div>
          <p class="bk-eyebrow">The real measure</p>
          <p class="bk-body" style="margin-top:12px">Crews receive the authorization number, the receiving
          unit and the return window in a single message. Nothing is confirmed twice, and nothing waits
          on a callback from the desk.</p>
          <p class="bk-caption" style="margin-top:16px">{TOK['measure']['body']['pxAt16']}px at 16px</p>
          <div style="margin-top:32px;border-top:1px solid var(--border-1);padding-top:24px">
            <p class="bk-eyebrow">On a dark ground</p>
            <p class="bk-caption" style="margin-top:8px">Light letterforms bloom. Add 0.005em
            tracking at every step and drop one weight at 700 and heavier. 600 is the floor.</p>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:24px">
              <div style="border:1px solid var(--border-1);padding:16px">
                <div style="font-size:32px;line-height:1.25;font-weight:var(--weight-bold);
                            letter-spacing:-0.008em">Dispatch</div>
                <p class="bk-caption" style="margin:8px 0 0">h2 · 700 · -0.008em</p>
              </div>
              <div class="bk-on-dark" style="background:var(--bg-band);padding:16px">
                <div style="font-size:32px;line-height:1.25;font-weight:var(--weight-semibold);
                            letter-spacing:-0.003em;color:var(--fg-on-dark-1)">Dispatch</div>
                <p class="bk-caption" style="margin:8px 0 0">h2 · 600 · -0.003em</p>
              </div>
            </div>
          </div>
        </div>
      </div>""")

    # 14 COMPONENTS
    # Each node prints the ratio the book computes for it, so the panel carries
    # the measurement instead of a sentence promising one.
    dr = REG["diagramRoles"]
    nodes = "".join(
        f'<div><span class="node" style="background:{v["fill"]};color:{v["text"]};'
        f'border:1px solid {v["border"]}">{E(k2)}</span>'
        # Split at the element: the hex is copied into a diagram fill and takes
        # the mono, the ratio beside it is a measurement and does not (rule 13).
        f'<p class="node-spec"><span class="bk-code">{v["text"].upper()}</span>'
        f' · {ratio(v["text"], v["fill"]):.2f}:1</p></div>'
        for k2, v in [("Process", dr["process"]), ("Decision", dr["decision"]), ("Warning", dr["warning"])])
    # Only Apex publishes a bandRule, so on Royal and Collective Edge
    # --border-band-rule is transparent and this panel drew nothing under a
    # label that named a band rule. The panel now names the divider the brand
    # actually publishes: the band rule at 2px where there is one, the house
    # hairline at 1px where there is not.
    foot_rule, foot_lbl = ("2px solid var(--border-band-rule)", "Footer, band rule above") \
        if col.get("bandRule") else ("1px solid var(--border-1)", "Footer, hairline above")
    # The demo table. A run count is a quantity and a median is a measurement,
    # so neither is on the mono whitelist (rule 13). The two columns are a real
    # stack and take .bk-tnum, and .bk-body-sm sets them on the 14px of the
    # facility column beside them rather than the 16px .bk-code resolved to, so
    # the row narrows rather than widens.
    add("", sec(12, "Built from the shared classes and this brand’s palette. Nothing here is "
                    "styled by hand.") + f"""
      <div class="s-body"><div class="demo-grid fill">
        <div class="demo"><div class="lbl">Table with tabular figures</div><div class="inner" style="padding:0">
          <table class="d-table">
            <thead><tr><th class="bk-eyebrow" style="margin:0;color:var(--fg-on-dark-1);text-align:left">Facility</th>
            <th class="bk-eyebrow" style="margin:0;color:var(--fg-on-dark-1);text-align:left">Runs</th>
            <th class="bk-eyebrow" style="margin:0;color:var(--fg-on-dark-1);text-align:left">Median</th></tr></thead>
            <tbody>
              <tr><td class="bk-body-sm">Mercy General</td><td class="bk-body-sm bk-tnum">1,284</td><td class="bk-body-sm bk-tnum">22 min</td></tr>
              <tr><td class="bk-body-sm">St. Vincent</td><td class="bk-body-sm bk-tnum">412</td><td class="bk-body-sm bk-tnum">31 min</td></tr>
              <tr><td class="bk-body-sm">Bayview</td><td class="bk-body-sm bk-tnum">968</td><td class="bk-body-sm bk-tnum">14 min</td></tr>
            </tbody>
          </table></div></div>
        <div class="demo"><div class="lbl">Diagram roles, house-wide</div><div class="inner">
          <div style="display:flex;gap:24px">{nodes}</div>
          <p class="bk-caption" style="margin-top:8px">Rectangles, 6px radius. Role is fill,
          never shape. House status colour, never brand.</p>
        </div></div>
        <div class="demo"><div class="lbl">{foot_lbl}</div><div class="inner">
          <div style="display:flex;justify-content:space-between;align-items:baseline;
                      border-top:{foot_rule};padding-top:12px">
            <span class="bk-caption">{E(name)} · Interfacility transport brief</span>
            <span class="bk-caption">Rev.&nbsp;<span class="bk-code">08.26</span></span>
          </div></div></div>
        <div class="demo"><div class="lbl">Eyebrow bound to heading</div><div class="inner">
          <p class="bk-eyebrow">Field operations</p>
          <h3 class="bk-h3" style="margin:0">Dispatch confirms level of service before the unit rolls.</h3>
        </div></div>
      </div></div>""")

    # 15 DO / DO NOT
    yes = ["Load type-system.css, then this brand’s palette.css.",
           "Style through the .bk-* classes and the semantic variables.",
           "Use the logo variant named for the background it sits on.",
           "Keep to three weights and three sizes above body on a page.",
           "Run scripts/validate.py before you hand the file over.",
           "Install the four static Montserrat files before you open PowerPoint.",
           "Render the output and look at it before calling it done."]
    no = ["Set italic, at any weight, anywhere.",
          "Reach for a weight outside 400, 600, 700 and 800.",
          "Track in px. It is a different optical amount at every size.",
          "Set a column of figures in proportional numerals.",
          "Strand the last word of a heading on its own line.",
          "Synthesize small caps. Montserrat has none.",
          "Type an em dash. Use a period, a comma or a middot."]
    # The path to the standard belongs on slide 16, where it sets in the mono
    # and cannot break. In a 20px standfirst it wrapped mid-path.
    add("", sec(13, "Seven of each, drawn from the fifteen rules in the house standard. "
                    "The marks are house status colour, not brand.") + f"""
      <div class="s-body"><div class="dd">
        <div class="yes"><h4>Do</h4><ul>{''.join(f'<li>{E(x)}</li>' for x in yes)}</ul></div>
        <div class="no"><h4>Do not</h4><ul>{''.join(f'<li>{E(x)}</li>' for x in no)}</ul></div>
      </div></div>""")

    # 16 ASSETS
    # Two columns of paths left the page two thirds white in both directions:
    # a 1145px path column for a 560px longest path, and a table that ran
    # y344 to y578 with 113px of nothing under it. A third column carries what
    # each file is for, which is the question a reader arriving at a list of
    # URLs is actually asking, and the rows divide the height. .ref.assets is
    # height:100%, so the rows stretch to whatever the flex region leaves them.
    ref = [("The standard", f"{ce}reference/type-system.md",
            "The fifteen rules, in prose"),
           ("Type system", f"{ce}snippets/type-system.css",
            "Load first. Every .bk-* class is here"),
           ("Type tokens", f"{ce}snippets/type-tokens.json",
            "The ladder, for generators that cannot read CSS"),
           ("Montserrat", f"{ce}assets/fonts/Montserrat-VariableFont_wght.woff2",
            "The variable font, axis clamped 400 to 800"),
           ("Palette", f"{cdn}snippets/palette.css",
            "Load second. The semantic variables"),
           ("Colour tokens", f"{cdn}tokens.json",
            "This palette, for those same generators"),
           # Section 07 prints .ce-powered, .ce-powered-light and
           # .ce-powered-text and this is the file that paints all three. The
           # head of this book loads it third, after the palette that supplies
           # the label and hairline variables it reads.
           ("Co-brand lockup", f"{ce}snippets/cobrand.css",
            "Load third. The three classes in section 07"),
           ("Brand registry", f"{cdn}brands.json",
            "Every brand in the house, and the diagram roles")]
    if is_ce:
        ref.append(("Grain hero", f"{ce}snippets/hero-dark.css",
                    "The dark grain. Title surfaces only"))
        # The file the cover of this book actually loads.
        ref.append(("Cover image", f"{ce}assets/imagery/CE_Background_1920.jpg",
                    "The photograph on the cover of this book"))
    # The column head names the root, so the cell carries only what follows it.
    # Printing the whole URL ran the CE table 400px wider than the sheet and
    # left the vendoring pass with no delimiter to stop on. Column three is a
    # sentence, not a string anybody retypes, so it leaves the mono (rule 13).
    rr = "".join('<tr><td>{}</td><td class="bk-code">{}</td><td>{}</td></tr>'.format(
        E(a), E(u.replace(CDN_ROOT, "")), P(w)) for a, u, w in ref)
    add("", sec(14, "Every path below hangs off cdn.jsdelivr.net/gh/collective-edge/ on the "
                    "public CDN. Pin @v1.1 for stability, @main for the latest.") + f"""
      <div class="s-body" style="display:flex;flex-direction:column">
        <div style="flex:1 1 auto;min-height:0">
          <table class="ref assets"><thead><tr><th>Asset</th><th>Path</th><th>What it is</th></tr></thead>
          <tbody>{rr}</tbody></table>
        </div>
        <div style="margin-top:32px;border:1px solid var(--border-1);padding:24px 28px;background:var(--bg-surface)">
          <p class="bk-eyebrow" style="color:var(--fg-1)">Drop-in</p>
          <pre style="font-family:var(--font-mono);font-size:12px;line-height:1.6;color:var(--fg-1);margin:8px 0 0;white-space:pre-wrap">&lt;link rel="stylesheet" href="{ce}snippets/type-system.css"&gt;
&lt;link rel="stylesheet" href="{cdn}snippets/palette.css"&gt;
&lt;link rel="stylesheet" href="{ce}snippets/cobrand.css"&gt;</pre>
        </div>
      </div>""")

    # 17 BACK
    # Two facts, one line each. Run together they reached the 54ch measure and
    # broke: Royal's kit path plus the command left "before you ship" stranded,
    # and CE's pushed the command onto a line by itself. Neither line alone
    # comes near the measure, so the measure stays and nothing wraps.
    add("cover dark bk-on-dark", f"""
      <div style="position:absolute;inset:0;background:var(--bg-band)"></div>
      <div style="position:relative;z-index:1;margin-top:auto">
        <img src="{logos['horizontal-on-dark']}" alt="{E(name)}" style="height:56px;width:auto;display:block">
        <p class="meta"><span class="bk-code">{E(b['repo'])}</span></p>
        <p class="meta">Verify with <span class="bk-code">scripts/validate.py</span> before you ship</p>
      </div>
      <div class="rule-accent" style="background:{band_rule};z-index:1"></div>""", foot=False)

    bar = ('<div class="bar noprint"><b style="letter-spacing:.12em">BRAND BOOKS</b>'
           '<a href="/">Index</a>'
           '<a href="/apex.html" id="l-apex">Apex</a>'
           '<a href="/royal.html" id="l-royal">Royal</a>'
           '<a href="/ce.html" id="l-ce">Collective Edge</a>'
           '<span class="sp"></span>'
           f'<span style="opacity:.55">{n} slides · 1600×900</span>'
           '<button onclick="window.print()">Save as PDF</button></div>')

    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>{E(name)} · Brand guidelines</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="{ce}snippets/type-system.css">
<link rel="stylesheet" href="{cdn}snippets/palette.css">
<link rel="stylesheet" href="{ce}snippets/cobrand.css">
<link rel="stylesheet" href="/book.css">
<style>:root{{--brand-primary:{col['primary']};--brand-accent:{col['accent']};
  --border-band-rule:{band_rule}}}</style>
</head><body>{bar}<div class="deck">
{''.join(S)}</div>
<script>document.getElementById('l-{ 'ce' if is_ce else key }').classList.add('on');</script>
</body></html>"""
    out = os.path.join(HERE, {"collective-edge": "ce"}.get(key, key) + ".html")
    open(out, "w", encoding="utf-8").write(doc)
    return out, n


if __name__ == "__main__":
    for k in ("apex", "royal", "collective-edge"):
        p, c = build(k)
        print(f"  {os.path.basename(p):12} {c} slides")
