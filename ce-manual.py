#!/usr/bin/env python3
"""Generate the Collective Edge brand manual.

Twenty-eight pages, US Letter landscape, 11 x 8.5in, which at 96 pixels to the
inch is 1056 x 816 exactly. Print-ready through Chrome's Save as PDF with
background graphics on and margins set to none.

This is not one of the three brand books and it does not share their generator.
Those are spec sheets for people building with the kit. This is written for a
partner, a prospective hire, or somebody who followed "Powered by Collective
Edge" out of a footer, and it never names a file, a class, a script, a
repository or a version tag. If a sentence only makes sense with the
repository checked out, it does not belong in the document.

Everything measurable is read rather than typed: the palette and its use
strings come from the kit's own tokens, every contrast ratio is computed with
the WCAG formula below, and every artwork proportion is derived from the drawn
extents of the shipping SVGs. The marks, the typeface and the grain wave are
embedded as data so the sheet prints identically with no network.

    python3 ce-manual.py            writes ce-manual.html
"""
import base64
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def _kits():
    """Where the sibling brand kits are cloned."""
    for c in (os.path.dirname(HERE), os.path.expanduser("~/collective-edge"),
              "/Users/jacob.sarasohn/collective-edge"):
        if os.path.isdir(os.path.join(c, "collective-edge-brand-kit")):
            return c
    raise SystemExit("no brand kits found beside this repository")


KITS = _kits()
CE = os.path.join(KITS, "collective-edge-brand-kit")
APEX = os.path.join(KITS, "apex-brand-kit")
ROYAL = os.path.join(KITS, "royal-brand-kit")

TOK = json.load(open(os.path.join(CE, "tokens.json"), encoding="utf-8"))
REG = json.load(open(os.path.join(CE, "brands.json"), encoding="utf-8"))
TYPE = json.load(open(os.path.join(CE, "snippets", "type-tokens.json"), encoding="utf-8"))

PIN = "@v1.3"
CDN = "https://cdn.jsdelivr.net/gh/collective-edge/collective-edge-brand-kit" + PIN + "/"
NB = "&nbsp;"


# ---------- text ----------------------------------------------------------

def E(s):
    return html.escape(str(s), quote=False)


def unit(n, u):
    """A number and its unit, joined so they never break across a line.

    Measurements stay in Montserrat with tabular figures. The mono face in this
    document holds one class of string and one only: a colour value.
    """
    return "%s%s%s" % (n, NB, u)


def hexs(h):
    """A colour value, in the second face.

    Montserrat's zero and capital O are the same circle, which is the whole
    reason the face exists here. Nothing else in this book takes it.
    """
    return '<span class="bk-code">%s</span>' % h.upper()


# ---------- contrast ------------------------------------------------------

def lum(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]


def ratio(a, b):
    l1, l2 = sorted([lum(a), lum(b)], reverse=True)
    return (l1 + .05) / (l2 + .05)


def ink_on(bg):
    """The reading colour for a chip, chosen by measurement rather than by eye.

    Every hex printed inside a swatch on the ramp page has to clear 4.5:1
    against the swatch it sits on, and the ramp runs from black to white, so
    the answer changes halfway down.
    """
    return "#FFFFFF" if ratio("#FFFFFF", bg) >= ratio("#111111", bg) else "#111111"


# ---------- the palette, read from the kit --------------------------------

RAMP = [(k, v["hex"].upper(), v["use"])
        for k, v in TOK["palette"].items()
        if isinstance(v, dict) and v.get("hex")]

STATUS = [(k, v["hex"].upper(), v.get("use", ""))
          for k, v in TOK["status"].items() if isinstance(v, dict) and v.get("hex")]

# The dimmest value the system will set as text is #6E6E6E at 5.10:1. Anything
# lighter is a swatch, a hairline or a dimmed non-text mark, and this book never
# sets one as type, including as a demonstration of failure.
TEXT_FLOOR = 4.5

# Two of the kit's use strings do not fit the register column on one line, and
# a wrapped cell pushes the last of twelve 40px rows under the folio. Shortened
# here, in the kit's own words, rather than truncated with an ellipsis.
USE_SHORT = {"fog": "The Edge wedge, standing alone",
             "black": "Header bands and title pages"}


# ---------- the drawn artwork ---------------------------------------------

def art_geometry():
    """The drawn extents of the horizontal lockup, read out of the artwork.

    Every proportion this manual states about the mark is measured here rather
    than typed, so a redrawn mark moves the numbers instead of stranding them.
    The block, the letters and the bar all draw in black, so they are separated
    by extent rather than by colour: the block is the black path that closes
    before the letters open, and the bar is not a filled path at all. It is a
    stroked line inside its own transform, which is why reading the clip boxes
    instead of the drawing put the wedge at the wrong end of the lockup once.
    """
    src = open(os.path.join(CE, "assets", "logos", "horizontal-black.svg"),
               encoding="utf-8").read()
    box = [float(v) for v in re.search(r'viewBox="([^"]+)"', src).group(1).split()]
    fills, blacks = {}, []
    for fill, d in re.findall(r'<path[^>]*?fill="([^"]+)"[^>]*?d="([^"]+)"', src):
        n = [float(x) for x in re.findall(r"-?\d+\.?\d*", d)]
        if not n:
            continue
        xs, ys = n[0::2], n[1::2]
        ext = [min(xs), max(xs), min(ys), max(ys)]
        if fill.lower() == "#000000":
            blacks.append(ext)
        elif fill.lower() != "none":
            f = fills.setdefault(fill.lower(), list(ext))
            f[0], f[1] = min(f[0], ext[0]), max(f[1], ext[1])
            f[2], f[3] = min(f[2], ext[2]), max(f[3], ext[3])
    block = min(blacks, key=lambda e: e[0])
    letters = min((e for e in blacks if e[0] > block[1]), key=lambda e: e[0])
    m = re.search(r'<path[^>]*transform="matrix\(([^)]+)\)"[^>]*fill="none"'
                  r'[^>]*d="M\s*([\d.eE+-]+)', src)
    a = [float(v) for v in m.group(1).split(",")]
    bar = float(m.group(2)) * a[0] + a[4]
    return {"w": box[2], "h": box[3], "block": block, "wedge": fills["#cccccc"],
            "letters": letters, "edge": fills["#666666"], "bar": bar}


ART = art_geometry()

LOCKUP_IN = 2.0          # every inch value on the anatomy page is quoted at this size


def pc(x):
    """A drawn measurement as a share of the lockup width. Unit-free, so it is
    true at every size the mark is ever set."""
    return x / ART["w"] * 100.0


def inches(x):
    return x / ART["w"] * LOCKUP_IN


def fmt(v, places=2):
    s = ("%%.%df" % places) % v
    return s.rstrip("0").rstrip(".") if "." in s else s


# ---------- embedded assets -----------------------------------------------

def data_uri(path, mime):
    with open(path, "rb") as fh:
        return "data:%s;base64,%s" % (mime, base64.b64encode(fh.read()).decode("ascii"))


def logo(name, kit=CE):
    return data_uri(os.path.join(kit, "assets", "logos", name), "image/svg+xml")


L_HORIZ_BLACK = logo("horizontal-black.svg")
L_HORIZ_WHITE = logo("horizontal-white.svg")
L_MARK_BLACK = logo("mark-black.svg")
L_MARK_WHITE = logo("mark-white.svg")
L_MARK_ROYAL = logo("mark-black-royal.svg")
L_MARK_APEX = logo("mark-black-apex.svg")
L_APEX_WHITE = logo("horizontal-white.svg", APEX)
L_APEX_COLOR = logo("horizontal-color.svg", APEX)
L_ROYAL_PURPLE = logo("horizontal-purple.svg", ROYAL)
WAVE = data_uri(os.path.join(CE, "assets", "imagery", "CE_Background_1920.jpg"), "image/jpeg")
FONT = data_uri(os.path.join(CE, "assets", "fonts", "Montserrat-VariableFont_wght.woff2"),
                "font/woff2")

# The partner values come from each partner's own kit through the registry,
# never from a copy of them kept here.
APEX_C = REG["brands"]["apex"]["color"]
ROYAL_C = REG["brands"]["royal"]["color"]


def palette_value(kit, name):
    """Resolve a semantic colour out of a partner's own published palette.

    The co-brand label on a partner's dark ground takes that palette's tertiary
    reversed grey, which each kit supplies and which is not the same value as
    their light step. Reading it means the specimen paints what their surfaces
    actually paint.
    """
    decl = {}
    src = open(os.path.join(kit, "snippets", "palette.css"), encoding="utf-8").read()
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;]+);", src):
        decl.setdefault(m.group(1), m.group(2).strip())
    v = decl.get(name)
    while v and v.startswith("var("):
        v = decl.get(v[4:-1].strip())
    return v


APEX_ON_DARK_3 = palette_value(APEX, "--fg-on-dark-3")


# ---------- the book ------------------------------------------------------

PARTS = [
    ("One", "The brand", 4, [
        (5, "Restraint is the house style."),
        (6, "Two surfaces, and the second is rare."),
        (7, "How we sound."),
    ]),
    ("Two", "The mark", 8, [
        (9, "The lockup, built."),
        (10, "Four marks, four grounds."),
        (11, "Clear space and minimum size."),
        (12, "The Edge wedge."),
        (13, "What never happens to the mark."),
    ]),
    ("Three", "Color", 14, [
        (15, "Eleven grays and nothing else."),
        (16, "Contrast, measured."),
        (17, "Where the color comes from."),
    ]),
    ("Four", "Type", 18, [
        (19, "Montserrat, measured."),
        (20, "Four weights, one job each."),
        (21, "The ladder."),
        (22, "Measure and composition."),
        (23, "The small marks."),
    ]),
    ("Five", "The co-brand", 24, [
        (25, "Powered by Collective Edge."),
        (26, "Mode A, the partner leads."),
        (27, "Mode B, we lead."),
    ]),
]

SIG = {}
for _w, _name, _d, _pp in PARTS:
    for _n, _t in _pp:
        SIG[_n] = "Part %s · %s" % (_w, _name)
    SIG[_d] = None          # a divider carries the page number and nothing else


def part_of(n):
    return SIG.get(n, "Collective Edge")


# ---------- page chrome ---------------------------------------------------

def head(eyebrow, title, standfirst=None, dark=False):
    sf = ('<p class="bk-body-lg m-standfirst">%s</p>' % standfirst) if standfirst else ""
    return (
        '<p class="m-eyebrow">%s</p>'
        '<div class="m-head"><h2 class="bk-h2 m-title">%s</h2>%s</div>'
        '<div class="m-rule"></div>' % (E(eyebrow), title, sf))


def folio(n):
    sig = part_of(n)
    left = ('<span class="m-label">%s</span>' % E(sig.upper())) if sig else "<span></span>"
    return ('<div class="m-folio">%s<span class="m-label m-page-no">%02d</span></div>'
            % (left, n))


def page(n, inner, cls="", spine=True, foot=True):
    s = '<div class="m-spine"></div>' if spine else ""
    f = folio(n) if foot else ""
    return '<section class="page %s">%s%s%s</section>\n' % (cls, s, inner, f)


def field(inner, style=""):
    return '<div class="m-field" style="%s">%s</div>' % (style, inner)


def at(x, y, w=None, extra=""):
    """Absolute placement on the sheet. Every horizon in this book is a stated
    number, never a consequence of flow, so a flip through the pages shows one
    unmoving rule with the density changing beneath it."""
    s = "position:absolute;left:%dpx;top:%dpx;" % (x, y)
    if w is not None:
        s += "width:%dpx;" % w
    return s + extra


RAIL_X, RAIL_W = 72, 210
FIELD_X, FIELD_W = 306, 678
COL, GUT = 210, 24
COL2 = 444
FIELD_TOP, FIELD_H = 256, 480


def col_x(i):
    return FIELD_X + i * (COL + GUT)


# ---------- 01 cover ------------------------------------------------------

def p01():
    """The cover: grain to every edge, and the mark large on it.

    Placement is measured, not judged. The wave's bright lobe is upper left, so
    the crop is pinned to the image's left edge and the mark sits low, where the
    brightest pixel under it reads 60 and white clears 11:1. Moving the mark
    40px up would put it on a 141 pixel at 3.3:1.
    """
    lock_w = 800
    lock_h = int(round(lock_w * ART["h"] / ART["w"]))
    return page(1, (
        '<div style="%s"></div>'
        '<img src="%s" alt="Collective Edge" width="%d" style="%s">'
    ) % (
        "position:absolute;inset:0;"
        "background:#000 url(%s) left center/cover no-repeat" % WAVE,
        L_HORIZ_WHITE, lock_w,
        at((1056 - lock_w) // 2, 700 - lock_h // 2, None, "display:block;"),
    ), cls="dark", spine=False, foot=False)


# ---------- 02 the statement ---------------------------------------------

def p02():
    # The one page in the book with no head-block title: the sentence IS the
    # title, promoted rather than duplicated. At 32px it was set at the size of
    # an ordinary page heading and left two thirds of the sheet empty.
    return page(2, (
        '<p class="m-eyebrow">In one line</p>'
        '<div class="m-rule"></div>'
        '<p class="bk-display-lg" style="%s">We build operating companies '
        'and stay with them for decades.</p>'
        '<p class="bk-body" style="%s">Apex Paramedics and Royal Ambulance are our '
        'operating companies.</p>'
    ) % (
        at(FIELD_X, 256, FIELD_W,
           "margin:0;max-width:678px;font-weight:700;line-height:78px;"
           "letter-spacing:-0.018em;"),
        at(FIELD_X, 672, 444, "margin:0;color:var(--fg-2);"),
    ))


# ---------- 03 contents ---------------------------------------------------

def p03():
    # Five rows of 96px fill y 256 to y 736 exactly. The column head and the
    # page-range column are gone: the range said "Pages 15 to 17" beside a
    # column that said 14, which is where the mismatched figures came from.
    rows = ""
    for i, (word, name, div, pages) in enumerate(PARTS):
        y = i * 96
        rows += ('<div style="%s"></div>'
                 '<p class="bk-body-lg" style="%s">%02d</p>'
                 '<p class="bk-h2" style="%s">%s</p>'
                 '<p class="bk-body-lg" style="%s">%02d</p>'
                 % (at(0, y, FIELD_W, "height:0;border-top:1px solid var(--border-1);"),
                    at(0, y + 32, 90, "margin:0;font-weight:700;color:var(--fg-3);"
                                      "font-variant-numeric:tabular-nums lining-nums;"),
                    i + 1,
                    at(105, y + 24, 480, "margin:0;max-width:480px;"),
                    E(name),
                    at(FIELD_W - 90, y + 32, 90,
                       "margin:0;font-weight:700;text-align:right;"
                       "font-variant-numeric:tabular-nums lining-nums;"),
                    div))
    rows += '<div style="%s"></div>' % at(0, 480, FIELD_W,
                                          "height:0;border-top:1px solid var(--border-1);")
    return page(3, (
        head("Contents", "What is in this book.",
             )
        + field(rows)
    ))


# ---------- dividers ------------------------------------------------------

WORDNUM = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


# One sentence a divider, in the house voice, saying what the part argues.
DIVIDER_CLAIM = {'One': 'We are the parent company. The operating companies keep their names and their people.', 'Two': 'One mark, four drawings. The only part of it that takes color is the wedge.', 'Three': 'Eleven grays and nothing else. Any color on a page of ours came from somewhere else.', 'Four': 'One typeface and four weights. Every number in this part is measured off the font.', 'Five': 'We rarely appear alone. When we appear beside you, we say so in words.'}


def divider(word, name, n, pages):
    """A part opener: the block mark whole, at the largest size the sheet takes.

    The kit reserves the cinematic, full-bleed, declarative treatment for a
    title or divider surface. The mark is never cut: it fills the field's full
    678px width, uncropped, with the part title and its claim beneath. At 678
    it is the largest single element in the book after the cover.
    """
    mark_w = FIELD_W
    mark_h = int(round(mark_w * 262.5 / 375))
    return page(n, (
        '<img src="%s" alt="Collective Edge" width="%d" style="%s">'
        '<p class="m-eyebrow">Part %s</p>'
        '<p class="bk-body-lg" style="%s">%02d</p>'
        '<p class="bk-display-lg bk-caps" style="%s">%s</p>'
        '<p class="bk-body-lg" style="%s">%s</p>'
    ) % (
        L_MARK_WHITE, mark_w,
        at(FIELD_X, 64, None, "display:block;"),
        E(word.lower()),
        at(RAIL_X, 622, RAIL_W,
           "margin:0;font-weight:600;color:#9E9E9E;"
           "font-variant-numeric:tabular-nums lining-nums;"),
        WORDNUM[word],
        at(FIELD_X, 580, FIELD_W, "margin:0;color:#FFFFFF;max-width:678px;"),
        E(name),
        at(FIELD_X, 672, 572, "margin:0;color:#D6D6D6;max-width:572px;"),
        E(DIVIDER_CLAIM[word]),
    ), cls="dark")


# ---------- 05 restraint --------------------------------------------------

def claim(bold, rest, cls="bk-body"):
    return ('<p class="%s" style="margin:0 0 16px"><span class="bk-emphasis">%s</span> %s</p>'
            % (cls, E(bold), E(rest)))


def p05():
    conventions = [("Canvas", "White"), ("Dividers", "Hairlines"), ("Boxes", "Never"),
                   ("Cards", "Flat"), ("Corners", "0 to 6 pixels"),
                   ("Gradients", "None"), ("Pattern", "None")]
    rows = "".join(
        '<div style="display:flex;justify-content:space-between;gap:12px;height:40px;'
        'align-items:center;border-bottom:1px solid var(--border-1)">'
        '<span class="bk-body-sm" style="margin:0">%s</span>'
        '<span class="bk-body-sm" style="margin:0;color:var(--fg-2);text-align:right">%s</span>'
        '</div>' % (E(a), E(b)) for a, b in conventions)
    return page(5, (
        head("House style", "Restraint is the house style.",
             "A white page, black type, one hairline.")
        + field(
            '<div class="m-cols-2">'
            '<div>%s%s%s%s</div>'
            '<div><p class="m-label" style="margin:0 0 12px">House conventions</p>%s'
            '</div>'
            '</div>' % (
                claim("Quiet on purpose.",
                      "A document here is a working surface, built to be read fast "
                      "and printed."),
                "",
                claim("Nothing spare.",
                      "Eleven grays, one typeface, and no pattern anywhere in the system."),
                "",
                rows))
    ))


# ---------- 06 two surfaces ----------------------------------------------

def p06():
    plate_w = 327
    doc = (
        '<div style="position:absolute;left:0;top:32px;width:%dpx;height:448px;'
        'background:#FFFFFF;border:1px solid var(--border-1);padding:32px">'
        '<p class="m-label" style="margin:0 0 12px">Operations</p>'
        '<p class="bk-h3" style="margin:0 0 16px;max-width:263px">How we operate together.</p>'
        '<div style="height:0;border-top:1px solid var(--border-1);margin:0 0 16px"></div>'
        '<p class="bk-body-sm" style="margin:0 0 12px;max-width:263px">Every deliverable '
        'opens on a white page with black type and one hairline.</p>'
        '<p class="bk-body-sm" style="margin:0;color:var(--fg-2);max-width:263px">Memos, '
        'one-pagers, reports, tables, briefs.</p></div>' % plate_w)
    hero = (
        '<div style="position:absolute;left:%dpx;top:32px;width:%dpx;height:448px;'
        'background:#000000;padding:32px;display:flex;flex-direction:column;'
        'justify-content:flex-end">'
        '<p class="m-label" style="margin:0 0 16px;color:#9E9E9E">Collective Edge</p>'
        '<p class="bk-h2 bk-caps" style="margin:0;color:#FFFFFF;font-weight:600;'
        'letter-spacing:0.045em;max-width:263px">How we<br>operate<br>together.</p></div>'
        % (plate_w + GUT, plate_w))
    return page(6, (
        head("Two treatments", "Two surfaces.",
             "Nearly everything we make is the first one.")
        + field(
            '<p class="m-label" style="%s">The document</p>'
            '<p class="m-label" style="%s">The statement · once, if at all</p>%s%s'
            % (at(0, 0, plate_w), at(plate_w + GUT, 0, plate_w), doc, hero))
    ))


# ---------- 07 voice ------------------------------------------------------

def p07():
    never = ["Leverage", "Synergize", "Unlock", "Emoji", "Exclamation points",
             "Rhetorical questions"]
    rows = "".join(
        '<p class="bk-body-sm" style="margin:0;height:32px;line-height:32px;'
        'border-bottom:1px solid var(--border-1);max-width:210px">%s</p>' % E(x)
        for x in never)
    return page(7, (
        head("Voice", "How we sound.",
             "A senior operator giving a direct briefing.")
        + field(
            '<div class="m-cols-2"><div>'
            '<p class="m-label" style="margin:0 0 16px">Bold, then explain</p>%s%s%s%s'
            '<p class="bk-caption" style="margin:24px 0 0">Headings end in a period.</p>'
            '</div><div>'
            '<p class="m-label" style="margin:0 0 12px">Words we do not use</p>%s'
            '</div></div>' % (
                claim("Proven playbooks.", "We understand what works and scale it."),
                claim("Long-term builders.", "We improve organizations for decades."),
                claim("Plain words.", "Body rarely runs past twelve words a sentence."),
                claim("Active verbs.", "Build, earn, operate, scale, reinvest."),
                rows))
    ))


# ---------- 09 the lockup, built -----------------------------------------

def p09():
    # The one bleed exemption in the book, spent on the object Part Two exists
    # to explain: the lockup runs the full 912px live area rather than sitting
    # inside the field. The spine is suppressed here because nothing in this
    # system is ever drawn on top of a mark, and at x 294 it would cross it.
    w = 912
    scale = w / ART["w"]
    mark_y = 288
    mark_h = int(round(ART["h"] * scale))
    block_w = ART["block"][1] - ART["block"][0]
    wedge_w = ART["wedge"][1] - ART["wedge"][0]
    keys = [
        ("The Edge block", ART["block"][0],
         "%s%% of the width" % ("%.1f" % pc(block_w))),
        ("The wedge", ART["wedge"][0],
         "the right %s%% of the block" % fmt(wedge_w / block_w * 100, 0)),
        ("The signature bar", ART["bar"],
         "%s%% from the left" % ("%.1f" % pc(ART["bar"]))),
        ("COLLECTIVE opens", ART["letters"][0],
         "%s%% from the left" % ("%.1f" % pc(ART["letters"][0]))),
        ("EDGE, in gray", ART["edge"][0],
         "%s%% from the left" % ("%.1f" % pc(ART["edge"][0]))),
    ]
    ticks = ""
    for i, (label, x, note) in enumerate(keys):
        px = RAIL_X + int(round(x * scale))
        ticks += '<div style="%s"></div>' % at(
            px, mark_y + mark_h + 8, None,
            "width:1px;height:16px;background:var(--border-2);")
        # 03 sets flush right of its own tick so it cannot jam into 04, which
        # stands 42px away. An ordinal is a count, so it is Montserrat with
        # tabular figures, not the second face.
        flush = "text-align:right;left:%dpx;" % (px - 40) if i == 2 else "left:%dpx;" % (px + 6)
        ticks += ('<p class="m-num" style="position:absolute;top:%dpx;width:34px;%s'
                  'margin:0;">%02d</p>' % (mark_y + mark_h + 32, flush, i + 1))

    cell = 168
    key_row = ""
    for i, (label, x, note) in enumerate(keys):
        kx = RAIL_X + i * (cell + 18)
        key_row += ('<p class="bk-body-sm" style="%s">'
                    '<span class="m-num">%02d</span>  %s</p>'
                    '<p class="bk-caption" style="%s">%s</p>'
                    % (at(kx, 512, cell, "margin:0;max-width:168px;"), i + 1, E(label),
                       at(kx, 540, cell, "margin:0;max-width:168px;"), E(note)))

    return page(9, (
        head("Anatomy", "The lockup, built.",
             "Heavy black beside gray is the signature.")
        + '<img src="%s" alt="Collective Edge" width="%d" style="%s">' % (
            L_HORIZ_BLACK, w, at(RAIL_X, mark_y, w, "display:block;"))
        + ticks + key_row
        + '<div style="%s">%s</div>' % (
            at(RAIL_X, 612, COL2),
            claim("Drawn, not typed.",
                  "The bar between the block and the name is geometry. Enlarged, it is "
                  "the line running down every other page of this manual."),
            )
    ), spine=False)


# ---------- 10 four grounds ----------------------------------------------

def p10():
    cell_w, cell_h = 327, 156
    cells = [("Lockup on light", L_HORIZ_BLACK, 204, "#FFFFFF", True),
             ("Lockup on dark", L_HORIZ_WHITE, 204, "#000000", False),
             ("Block mark on light", L_MARK_BLACK, 96, "#FFFFFF", True),
             ("Block mark on dark", L_MARK_WHITE, 96, "#000000", False)]
    out = ""
    for i, (label, src, w, bg, light) in enumerate(cells):
        x = (i % 2) * (cell_w + GUT)
        y = (i // 2) * (cell_h + 12 + 17 + 24)
        border = "border:1px solid var(--border-1);" if light else ""
        out += ('<div style="%s"><img src="%s" alt="Collective Edge" width="%d" '
                'style="display:block"></div>'
                % (at(x, y, cell_w,
                      "height:%dpx;background:%s;%sdisplay:flex;align-items:center;"
                      "justify-content:center;" % (cell_h, bg, border)), src, w))
        out += '<p class="m-label" style="%s">%s</p>' % (
            at(x, y + cell_h + 12, cell_w, "margin:0;"), E(label))
    return page(10, (
        head("Grounds", "Four marks, four grounds.",
             "Every combination already exists as artwork.")
        + field(out)
        + '<p class="bk-body-sm" style="%s"><span class="bk-emphasis">Four drawings, not '
          'two.</span> None is made by inverting another.</p>' % at(FIELD_X, 680, COL2, "margin:0;max-width:444px;")
    ))


# ---------- 11 clear space ------------------------------------------------

def p11():
    # The clear-space plate is the object this page is about, so it takes the
    # two-column chord rather than sitting at 354px. The inset is drawn from
    # the measured block height, and the value is printed beside the ticks so
    # the page measures its own rule instead of implying it.
    lock_w = 320
    clear = ART["block"][3] - ART["block"][2]
    clear_pc = pc(clear)
    pad = int(round(lock_w * clear_pc / 100))
    lock_h = int(round(lock_w * ART["h"] / ART["w"]))
    plate_w, plate_h = lock_w + pad * 2, lock_h + pad * 2
    ticks = ""
    for x, y, w_, h_ in ((0, pad, plate_w, 1), (0, plate_h - pad, plate_w, 1),
                         (pad, 0, 1, plate_h), (plate_w - pad, 0, 1, plate_h)):
        ticks += ('<div style="position:absolute;left:%dpx;top:%dpx;width:%dpx;'
                  'height:%dpx;background:var(--ce-fog)"></div>' % (x, y, w_, h_))
    box = ('<div style="position:relative;width:%dpx;height:%dpx;'
           'border:1px solid var(--border-1);margin:0 0 16px">%s'
           '<img src="%s" alt="Collective Edge" width="%d" '
           'style="position:absolute;left:%dpx;top:%dpx;display:block">'
           '</div>' % (plate_w, plate_h, ticks, L_HORIZ_BLACK, lock_w, pad, pad))
    floors = (
        '<p class="m-label" style="margin:0 0 16px">At true size</p>'
        '<img src="%s" alt="Collective Edge" width="96" style="display:block;margin:0 0 8px">'
        '<p class="bk-caption" style="margin:0 0 24px">Lockup in print · %s</p>'
        '<img src="%s" alt="Collective Edge" width="120" style="display:block;margin:0 0 8px">'
        '<p class="bk-caption" style="margin:0 0 24px">Lockup on screen · %s</p>'
        '<div style="display:flex;align-items:center;gap:16px;margin:0 0 8px">'
        '<img src="%s" alt="Collective Edge" width="28" style="display:block">'
        '<div style="background:#000000;padding:8px;display:flex">'
        '<img src="%s" alt="Collective Edge" width="28" style="display:block"></div></div>'
        '<p class="bk-caption" style="margin:0">Block mark · %s</p>' % (
            L_HORIZ_BLACK, unit("1", "in"),
            L_HORIZ_BLACK, unit("120", "px"),
            L_MARK_BLACK, L_MARK_WHITE, unit("28", "px")))
    return page(11, (
        head("Space and size", "Clear space and minimum size.",
             "Clear space is one Edge block on every side.")
        + field(
            '<div style="position:absolute;left:0;top:0;width:%dpx">'
            '<p class="m-label" style="margin:0 0 16px">Clear space · one Edge block</p>'
            '%s'
            '<p class="bk-body" style="margin:0 0 16px;max-width:444px">That block is '
            '<span class="bk-emphasis">%s%% of the lockup width</span>, which on a '
            'two-inch lockup is %s of air on every side.</p>'
            ''
            '</div>'
            '<div style="position:absolute;left:%dpx;top:0;width:%dpx">%s</div>'
            % (COL2, box, fmt(clear_pc, 1), unit(fmt(inches(clear), 2), "in"),
               col_x(2) - FIELD_X, COL, floors))
    ))


# ---------- 12 the wedge --------------------------------------------------

def p12():
    marks = [("Standing alone", L_MARK_BLACK, TOK["wedge"]["standalone"]["hex"]),
             ("With Royal Ambulance", L_MARK_ROYAL, TOK["wedge"]["royal"]["hex"]),
             ("With Apex Paramedics", L_MARK_APEX, TOK["wedge"]["apex"]["hex"])]
    out = ""
    for i, (label, src, hexv) in enumerate(marks):
        x = i * (COL + GUT)
        out += '<img src="%s" alt="Collective Edge" width="%d" style="%s">' % (
            src, COL, at(x, 0, COL, "display:block;"))
        out += ('<p class="m-label" style="%s">%s</p>'
                '<p class="bk-caption" style="%s">%s</p>' % (
                    at(x, 176, COL, "margin:0;"), E(label),
                    at(x, 200, COL, "margin:0;"), hexs(hexv)))
    return page(12, (
        head("The wedge", "The Edge wedge.",
             "The wedge is the one part of the mark that takes color, and the color "
             "is never ours.")
        + field(out
                + '<div style="%s"></div>' % at(0, 256, FIELD_W,
                                                "height:0;border-top:1px solid var(--border-1);")
                + '<div style="%s">%s%s</div>' % (
                    at(0, 288, COL2),
                    claim("The color stops at the wedge.",
                          "It never reaches the block, the letters, a rule, or anything "
                          "else on the surface."),
                    "")
                + '<p class="bk-caption" style="%s">Three drawings, never one tinted ' 'three ways.</p>' % at(
                      col_x(2) - FIELD_X, 288, COL, "margin:0;"))
    ))


# ---------- 13 misuse -----------------------------------------------------

def p13():
    # Six failures, one visual weight each. Every specimen is the horizontal
    # lockup at 168px unless the failure is about count or about the block, so
    # no single cell shouts louder than the rule it illustrates.
    cell_w, cell_h = COL, 176

    def lock(w, style=""):
        return ('<img src="' + L_HORIZ_BLACK + '" alt="Collective Edge" width="'
                + str(w) + '" style="display:block;' + style + '">')

    # A blend mode tints the transparent ground as readily as the ink, which is
    # what painted a gold rectangle here. Masking paints only where the artwork
    # has ink, so the mark takes the hue and nothing around it does.
    gold = TOK["wedge"]["apex"]["hex"]
    recolored = ('<div style="width:168px;height:28px;background:' + gold + ';'
                 '-webkit-mask:url(' + L_HORIZ_BLACK + ') center/contain no-repeat;'
                 'mask:url(' + L_HORIZ_BLACK + ') center/contain no-repeat"></div>')
    cases = [
        ("Stretched", lock(140, "transform:scaleX(1.4)")),
        ("Rotated", lock(168, "transform:rotate(-7deg)")),
        ("Shadowed", lock(168, "filter:drop-shadow(0 4px 6px rgba(0,0,0,.45))")),
        ("Recolored", recolored),
        ("Twice on one surface",
         '<div style="display:grid;gap:20px">' + lock(132) + lock(132) + '</div>'),
        ("A partner wedge, alone",
         '<img src="' + L_MARK_ROYAL + '" alt="Collective Edge" width="92" '
         'style="display:block">'),
    ]
    out = ""
    for i, (label, inner) in enumerate(cases):
        x = (i % 3) * (COL + GUT)
        y = (i // 3) * (cell_h + 12 + 17 + 32)
        out += ('<div class="m-wrong" style="%s">%s</div>'
                '<p class="m-label" style="%s">%s</p>' % (
                    at(x, y, cell_w, "height:%dpx;display:flex;align-items:center;"
                                     "justify-content:center;overflow:hidden;" % cell_h),
                    inner,
                    at(x, y + cell_h + 12, cell_w, "margin:0;"), E(label)))
    return page(13, (
        head("Misuse", "What never happens to the mark.",
             "Every result on gray is one to avoid.")
        + field(out)
    ))


# ---------- 15 the ramp ---------------------------------------------------

def p15():
    chips = ""
    n = len(RAMP)
    w = 1056 // n
    for i, (name, hexv, use) in enumerate(RAMP):
        ink = ink_on(hexv)
        edge = ("border-right:1px solid rgba(255,255,255,0.14);"
                if lum(hexv) < .5 else "border-right:1px solid rgba(0,0,0,0.06);")
        if i == n - 1:
            edge = ""
        chips += (
            '<div style="position:absolute;left:%dpx;top:0;width:%dpx;height:480px;'
            'background:%s;%s">'
            '<p class="m-label" style="position:absolute;left:16px;bottom:44px;'
            'color:%s;margin:0">%s</p>'
            '<p class="m-chip-label" style="position:absolute;left:16px;bottom:20px;'
            'color:%s;margin:0">%s</p></div>'
            % (i * w, w if i < n - 1 else 1056 - i * w, hexv, edge,
               ink, E(name.title()), ink, hexv))
    return page(15, (
        head("The ramp", "Eleven grays and nothing else.",
             "The palette is not going to grow.")
        + '<div style="position:absolute;left:0;top:%dpx;width:1056px;height:480px">%s</div>'
          % (FIELD_TOP, chips)
    ))


# ---------- 16 contrast ---------------------------------------------------

def p16():
    rows = ""
    for name, hexv, use in RAMP:
        r = ratio(hexv, "#FFFFFF")
        if r >= TEXT_FLOOR:
            shown = ('<span style="color:%s">Set in this gray.</span>' % hexv)
        else:
            shown = '<span style="color:var(--fg-3)">Never set as text</span>'
        # Header plus eleven rows on 40px stations fills the 480px field to the
        # pixel, so one wrapped cell pushes the last row under the folio. The
        # use string is cut at its first clause and held on one line.
        rows += ('<tr><td class="mono" style="width:104px">%s</td>'
                 '<td style="width:74px">%s</td>'
                 '<td style="width:134px">%s</td>'
                 '<td class="num" style="width:88px">%s:1</td>'
                 '<td class="q" style="width:278px;padding-left:16px;white-space:nowrap">'
                 '%s</td></tr>'
                 % (hexv, E(name.title()), shown, fmt(r, 2),
                    E(USE_SHORT.get(name, re.split(r"[.,]", use)[0]))))
    return page(16, (
        head("Legibility", "Contrast, measured.",
             "Measured against white. The first five are set here as live text.")
        + field('<table class="m-reg"><thead><tr>'
                '<th style="width:104px">Value</th><th style="width:74px">Name</th>'
                '<th style="width:134px">On white</th>'
                '<th class="num" style="width:88px">Ratio</th>'
                '<th style="width:278px;padding-left:16px">Use</th></tr></thead>'
                '<tbody>%s</tbody></table>' % rows)
    ))


# ---------- 17 where color comes from -------------------------------------

def p17():
    sources = [
        ("Our documents, decks and reports", "The grey ramp. Nothing else."),
        ("Our mark", "Black or white. The wedge takes their color"),
        ("A partner’s own surface", "Their palette leads. We add no hue."),
        ("A product we build for a partner", "Our ramp, plus their accent, functional only"),
        ("Anything carrying operational status", "The four status colors, used functionally"),
        ("A chart or a data view", "Series colors chosen for legibility"),
    ]
    rows = "".join('<tr><td>%s</td><td class="q">%s</td></tr>' % (E(a), E(b))
                   for a, b in sources)
    chip_w = 151
    chips = ""
    for i, (name, hexv, meaning) in enumerate(STATUS):
        chips += ('<div style="%s"></div>'
                  '<p class="m-label" style="%s">%s</p>'
                  '<p class="m-chip-label" style="%s">%s</p>'
                  % (at(i * (chip_w + GUT), 0, chip_w, "height:32px;background:%s;" % hexv),
                     at(i * (chip_w + GUT), 44, chip_w, "margin:0;"),
                     E(name.title()),
                     at(i * (chip_w + GUT), 68, chip_w, "margin:0;color:var(--fg-3);"),
                     hexv))
    return page(17, (
        head("Sources", "Where the color comes from.",
             "We have no hue of our own. Every color here belongs to a partner or a state.")
        + field('<table class="m-reg"><thead><tr><th>Surface</th>'
                '<th>Palette</th></tr></thead><tbody>%s</tbody></table>' % rows
                + '<div style="position:absolute;left:0;top:312px;width:678px">'
                  '<p class="m-label" style="margin:0 0 16px">The status set</p>'
                  '<div style="position:relative;height:92px">%s</div>'
                  '<p class="bk-caption" style="margin:0;max-width:444px">A state, never a ' 'theme.</p></div>' % chips)
    ))


# ---------- 19 montserrat -------------------------------------------------

def p19():
    # 320px overflowed: Montserrat's natural line box is 1.219em, so the glyph
    # block alone ran past the field floor before a metric line was drawn.
    size = 240
    m = TYPE["metrics"]
    asc, cap, xh = m["ascender"], m["capHeight"], m["xHeight"]
    desc = abs(m["descender"])
    top = 24
    base = top + int(round(asc * size))
    lines = [("Ascender", asc, top),
             ("Cap height", cap, base - int(round(cap * size))),
             ("x-height", xh, base - int(round(xh * size))),
             ("Baseline", 0.0, base),
             ("Descender", desc, base + int(round(desc * size)))]
    rules = ""
    for label, v, y in lines:
        # The hairline passes behind the letterform, never across it. A rule
        # through a glyph is the fault the layout auditor is built to catch.
        rules += '<div style="%s"></div>' % at(
            0, y, 456, "height:0;border-top:1px solid var(--border-1);z-index:0;")
        rules += '<p class="bk-caption" style="%s">%s · %.3f</p>' % (
            at(468, y - 9, COL, "margin:0;"), E(label), v)
    facts = [("Natural line box", "1.219", "Nothing wraps tighter than 1.05"),
             ("Average letter", "16.7% wider than Helvetica", "Count characters, not widths"),
             ("Zero and capital O", "One circle", "Why a color value changes face"),
             ("Italic", "None", "At any weight, in any brand")]
    return page(19, (
        head("The typeface", "Montserrat, measured.",
             "One face sets every word in every brand. The five lines are measured off it.")
        
        + field(
            # line-height:1 inside a 1.219em natural line box put the glyph
            # 26.3px above every rule that claimed to measure it. On the page
            # whose whole argument is that the numbers are measured.
            '<div style="%s"><span style="font-size:%dpx;line-height:1.219;'
            'font-weight:700;letter-spacing:-0.02em;color:var(--fg-1)">Eg</span></div>%s'
            % (at(0, top, None, "z-index:1;"), size, rules)
            + '<div style="%s">%s</div>' % (
                at(0, 348, FIELD_W),
                "".join(
                    '<div style="display:flex;gap:16px;height:32px;align-items:center;'
                    'border-bottom:1px solid var(--border-1)">'
                    '<span class="bk-body-sm" style="margin:0;width:176px">%s</span>'
                    '<span class="bk-body-sm" style="margin:0;width:220px;font-weight:600">'
                    '%s</span>'
                    '<span class="bk-body-sm" style="margin:0;color:var(--fg-2)">%s</span>'
                    '</div>' % (E(a), E(b), E(c)) for a, b, c in facts)))
    ))


# ---------- 20 weights ----------------------------------------------------

def p20():
    # The kit names each weight's job in its own vocabulary, which includes
    # heading levels a reader of this book has no reason to know. Same jobs,
    # stated in the words the reader already has.
    USE = {"regular": "Body, captions, footers, table cells",
           "semibold": "Subheads, uppercase labels, table headers",
           "bold": "Headings, emphasis in body, stat numerals",
           "extrabold": "Hero and title bands only"}
    rows = ""
    y = 0
    for key in ("regular", "semibold", "bold", "extrabold"):
        w = TYPE["weight"][key]
        rows += ('<div style="%s">'
                 '<span style="font-size:56px;line-height:1.1;font-weight:%d;'
                 'letter-spacing:-0.015em">Collective</span></div>'
                 '<p class="bk-body-sm" style="%s"><span style="font-weight:600;'
                 'font-variant-numeric:tabular-nums lining-nums">%d</span> · %s</p>'
                 '<p class="bk-caption" style="%s">%s</p>'
                 % (at(0, y, COL2 + GUT + COL, "height:64px;"), w["value"],
                    at(col_x(2) - FIELD_X, y + 4, COL, "margin:0;"),
                    w["value"], E(w["name"]),
                    at(col_x(2) - FIELD_X, y + 28, COL, "margin:0;"),
                    E(USE[key])))
        y += 72
    return page(20, (
        head("Weight", "Four weights, one job each.",
             "The axis runs from regular to extra bold and stops there.")
        + field(rows
                + '<div style="%s"></div>' % at(0, 296, FIELD_W,
                                                "height:0;border-top:1px solid var(--border-1);")
                + '<div style="%s">%s%s</div>' % (
                    at(0, 328, COL2),
                    claim("Three at a time.",
                          "No single piece of work reaches for more than three of the four."),
                    claim("Dark grounds bloom.",
                          "On black every step gains a little tracking, and anything bold "
                          "or heavier drops one weight."))
                )
    ))


# ---------- 21 the ladder -------------------------------------------------

def p21():
    steps = {s["token"]: s for s in TYPE["scale"]}
    big = ["display-xl", "display-lg", "display-md", "h1"]
    small = ["h2", "h3", "h4", "body-lg", "body", "body-sm", "caption"]
    names = {"display-xl": "Display, extra large", "display-lg": "Display, large",
             "display-md": "Display, medium", "h1": "Heading one", "h2": "Heading two",
             "h3": "Heading three", "h4": "Heading four", "body-lg": "Body, large",
             "body": "Body", "body-sm": "Body, small", "caption": "Caption"}

    def spec(token, word, gap=24):
        s = steps[token]
        return ('<div style="margin:0 0 4px"><span style="font-size:%dpx;line-height:%s;'
                'font-weight:%d;letter-spacing:%sem;display:block">%s</span></div>'
                '<p class="bk-caption" style="margin:0 0 %dpx">%s · %s · %s</p>'
                % (s["px"], s["leading"], s["weight"], fmt(s["tracking"], 3), E(word),
                   gap, E(names[token]), unit(s["px"], "px"), unit(fmt(s["pt"], 1), "pt")))

    # The small column runs seven steps inside 210px. At the two largest of them
    # a two-word specimen wraps, and seven wrapped steps overshoot the field
    # floor by 42px, which is how the caption ended up under the folio.
    left = "".join(spec(t, "Edge") for t in big)
    right = "".join(spec(t, "Edge" if steps[t]["px"] >= 24 else "Collective Edge", 16)
                    for t in small)
    return page(21, (
        head("Scale", "The ladder.",
             "Eleven steps, each printed here at the size it prints everywhere else.")
        + field('<div style="position:absolute;left:0;top:0;width:444px">%s</div>'
                '<div style="position:absolute;left:%dpx;top:0;width:210px">%s</div>'
                % (left, col_x(2) - FIELD_X, right))
        + '<p class="bk-caption m-rail" style="top:600px;margin:0;max-width:210px">'
          'This sheet prints at 96 pixels to the inch, so the pixel column and the '
          'point column name one physical size. The specimen is the specification.</p>'
    ))


# ---------- 22 measure ----------------------------------------------------

def p22():
    # The body measure is 572px and the field is 678px, so the specimen cannot
    # share a line with a 210px column: 572 + 24 + 210 overruns the field by
    # 128px and sets text on text. The measure blocks take the full field and
    # the list goes to the rail, which is what the rail is for.
    def block(label, width, size, text, weight=400):
        return ('<p class="m-label" style="margin:0 0 8px">%s</p>'
                '<div style="border-right:1px solid var(--border-2);width:%dpx;'
                'padding-right:16px;margin:0 0 32px">'
                '<span style="font-size:%dpx;line-height:1.6;font-weight:%d;display:block">'
                '%s</span></div>' % (E(label), width + 16, size, weight, E(text)))

    always = ("Flush left, ragged right", "Never justified",
              "Never centered past three lines", "Every vertical value a multiple of four")
    return page(22, (
        head("Composition", "Measure and composition.",
             "A measure is a width, so it is drawn here as one.")
        + '<div class="m-rail" style="top:296px">'
          '<p class="m-label" style="margin:0 0 12px">Always</p>%s</div>'
          % "".join('<p class="bk-body-sm" style="margin:0;padding:8px 0;line-height:1.35;'
                    'border-bottom:1px solid var(--border-1);max-width:210px">%s</p>' % E(x)
                    for x in always)
        + field(
            block("Body · 70 characters", 572, 16,
                  "Body sets to seventy characters and stops there. The white left at "
                  "the right edge of every page is arithmetic, not taste.")
            # 28ch at 24px is 445px. The 297 here was 28ch computed at 16px, so
            # the box contradicted the label printed beside it.
            + block("Heading · 36 characters", 445, 24,
                    "A heading stops right about here.", 600)
            + '<div style="%s"></div>' % at(0, 264, FIELD_W,
                                            "height:0;border-top:1px solid var(--border-1);")
            + '<div style="%s">%s</div>' % (
                  at(0, 296, COL2),
                  claim("Three above, one below.",
                        "Space over a heading is three times the space under it, so the "
                        "heading belongs to the text it introduces.")))
    ))


# ---------- 23 the small marks --------------------------------------------

def p23():
    marks = [("Quotation", "“Royal”"), ("Apostrophe", "crew’s"),
             ("Date range", "2024–2026"), ("Truncation", "…"),
             ("Number and unit", unit("12", "min")),
             ("Separator", "Facility · Payer"),
             ("Em dash", "Not used. A period or a comma.")]
    rows = "".join('<tr><td style="width:190px">%s</td><td>%s</td></tr>' % (E(a), b)
                   for a, b in marks)
    figs = ("".join('<div style="display:flex;justify-content:space-between;height:32px;'
                    'align-items:center;border-bottom:1px solid var(--border-1)">'
                    '<span class="bk-body-sm" style="margin:0">%s</span>'
                    '<span class="bk-body-sm" style="margin:0;font-variant-numeric:'
                    'tabular-nums lining-nums;font-weight:600">%s</span></div>'
                    % (E(a), E(b))
                    for a, b in (("Transports", "1,118"), ("On time", "94.1%"),
                                 ("Median", "11 min"), ("Crews", "108"))))
    return page(23, (
        head("Micro-typography", "The small marks.",
             "A reader notices these marks only when they are wrong.")
        + field('<div style="position:absolute;left:0;top:0;width:%dpx">'
                '<table class="m-reg"><thead><tr><th style="width:190px">Where</th>'
                '<th>Correct form</th></tr></thead><tbody>%s</tbody></table></div>'
                '<div style="position:absolute;left:%dpx;top:0;width:%dpx">'
                '<p class="m-label" style="margin:0 0 12px">Figures in a column</p>%s'
                '<p class="bk-caption" style="margin:16px 0 0">Tabular figures stack.</p></div>'
                % (COL2, rows, col_x(2) - FIELD_X, COL, figs))
    ))


# ---------- 25 powered by -------------------------------------------------

def p25():
    # The lockup is the object the page is about, so it takes the field rather
    # than a single column, with its two hairlines running the full width. At
    # 204px in a 210px column it was the smallest thing on its own page.
    lockup = (
        '<div style="%s"></div>'
        '<p class="m-label" style="%s">Powered by</p>'
        '<img src="%s" alt="Collective Edge" width="444" style="%s">'
        '<div style="%s"></div>'
        '<p class="bk-caption" style="%s">Shipped at 204&nbsp;px.</p>' % (
            at(0, 32, FIELD_W, "height:0;border-top:1px solid var(--border-1);"),
            at(0, 56, COL2, "margin:0;"),
            L_HORIZ_BLACK, at(0, 92, None, "display:block;"),
            at(0, 190, FIELD_W, "height:0;border-top:1px solid var(--border-1);"),
            at(0, 206, COL2, "margin:0;")))

    def lst(x, label, items):
        return ('<p class="m-label" style="%s">%s</p>%s' % (
            at(x, 268, 324, "margin:0;"), E(label),
            "".join('<p class="bk-body-sm" style="%s">%s</p>'
                    % (at(x, 300 + i * 36, 324,
                          "margin:0;line-height:36px;max-width:324px;"
                          "border-bottom:1px solid var(--border-1);"), E(t))
                    for i, t in enumerate(items))))

    return page(25, (
        head("The co-brand", "Powered by Collective Edge.",
             "If our mark shares a surface with another brand, the phrase is on it too.")
        
        + field(lockup
                + lst(0, "Where it belongs", [
                    "The footer of a site or a document",
                    "The sidebar header of a dashboard",
                    "The closing slide of a deck",
                    "A data or methodology page",
                    "Anywhere a number was computed"])
                + lst(354, "Where it does not", [
                    "Inside the partner\u2019s own lockup",
                    "On a clinical instruction",
                    "On a patient consent form",
                    "Twice on one surface",
                    "On a vehicle or a uniform"]))
    ))


# ---------- 26 mode A -----------------------------------------------------

def p26():
    panel = (
        '<div style="%s">'
        '<img src="%s" alt="Apex Paramedics" width="158" style="display:block;margin:0 0 24px">'
        '<div style="border-top:1px solid rgba(255,255,255,0.12);padding-top:24px">'
        '<p class="m-label" style="margin:0 0 12px;color:%s">Powered by</p>'
        '<img src="%s" alt="Collective Edge" width="204" height="34" style="display:block">'
        '</div></div>'
        '<div style="%s"></div>' % (
            at(0, 0, COL2, "height:320px;background:%s;padding:32px;" % APEX_C["primaryDeep"]),
            # The label takes that palette's own tertiary reversed grey, which
            # measures 5.98:1 on their deep ground. Their light step is a
            # different value and does not clear it.
            L_APEX_WHITE, APEX_ON_DARK_3, L_HORIZ_WHITE,
            at(COL2 - 4, 0, None, "width:4px;height:320px;background:%s;" % APEX_C["accent"])))
    contrib = "".join(
        '<p class="bk-body-sm" style="margin:0;height:36px;line-height:36px;'
        'border-bottom:1px solid rgba(255,255,255,0.12);color:#D6D6D6;max-width:210px">'
        '%s</p>' % E(x)
        for x in ("The typeface", "Hairline dividers", "Wide margins",
                  "Tabular numerals", "A disciplined scale"))
    return page(26, (
        head("Mode A", "The partner leads.",
             "Their brand owns the surface. We add structure and finish, and no color "
             "at all.")
        + field(panel
                
                + '<div style="position:absolute;left:%dpx;top:0;width:%dpx">'
                  '<p class="m-label" style="margin:0 0 12px">What we contribute</p>%s'
                  '<p class="bk-body-sm" style="margin:24px 0 0;color:#D6D6D6;'
                  'max-width:210px"><span class="bk-emphasis">When in doubt, Mode&nbsp;A.</span> '
                  'We do not take over a partner’s surface.</p></div>'
                  % (col_x(2) - FIELD_X, COL, contrib))
    ), cls="dark")


# ---------- 27 mode B -----------------------------------------------------

def p27():
    gold = APEX_C["accent"]
    card = (
        '<div style="%s">'
        '<div style="display:flex;align-items:center;gap:16px;margin:0 0 24px">'
        '<img src="%s" alt="Collective Edge" width="170" style="display:block">'
        '<span style="width:1px;height:34px;background:rgba(17,17,17,0.14);display:block">'
        '</span>'
        '<img src="%s" alt="Apex Paramedics" width="132" style="display:block"></div>'
        '<p class="m-label" style="margin:0 0 20px">Powered by Collective Edge</p>'
        '<div style="height:0;border-top:1px solid var(--border-1);margin:0 0 20px"></div>'
        '<div style="display:flex;gap:32px;margin:0 0 24px">%s</div>'
        '<div style="display:flex;gap:48px">%s</div>'
        '</div>' % (
            at(0, 0, FIELD_W, "background:var(--bg-canvas);border:1px solid var(--border-1);"
                              "padding:32px;"),
            L_HORIZ_BLACK, L_APEX_COLOR,
            "".join(
                '<span class="bk-body-sm" style="margin:0;padding:0 0 8px;'
                'border-bottom:3px solid %s;color:%s;font-weight:600">%s</span>'
                % (gold, "var(--fg-1)", E(x)) if i == 0 else
                '<span class="bk-body-sm" style="margin:0;padding:0 0 8px;'
                'border-bottom:3px solid transparent;color:var(--fg-3)">%s</span>' % E(x)
                for i, x in enumerate(("Live", "Transports", "Response", "Crews"))),
            "".join(
                '<div><p class="m-label" style="margin:0 0 8px">%s</p>'
                '<p style="margin:0;font-size:32px;line-height:1.1;font-weight:700;'
                'letter-spacing:-0.008em;font-variant-numeric:tabular-nums lining-nums">'
                '%s</p></div>' % (E(a), E(b))
                for a, b in (("Transports", "1,118"), ("On time", "94.1%"),
                             ("Median response", "11 min")))))
    return page(27, (
        head("Mode B", "We lead.",
             "Our system owns the surface. Their color is the only hue, and it is functional.")
        + field(card
                + '<div style="position:absolute;left:0;top:328px;width:%dpx">%s</div>'
                  '<div style="position:absolute;left:%dpx;top:328px;width:%dpx">'
                  '<p class="m-label" style="margin:0 0 12px">Where their color lands</p>%s'
                  '</div>' % (
                      COL2,
                      claim("One mode, held.",
                            "Our ramp never sits over a partner’s palette, and theirs " "never sits over our chrome."),
                      col_x(2) - FIELD_X, COL,
                      "".join(
                          '<p class="bk-body-sm" style="margin:0;height:32px;'
                          'line-height:32px;border-bottom:1px solid var(--border-1);'
                          'max-width:210px">%s</p>' % E(x)
                          for x in ("The active tab", "A live indicator",
                                    "One chart series"))))
    ))


# ---------- 28 back cover -------------------------------------------------

def p28():
    return page(28, (
        '<div style="%s"></div>'
        '<div class="m-spine" style="top:64px;height:344px"></div>'
        '<p class="m-eyebrow">Collective Edge</p>'
        '<img src="%s" alt="Collective Edge" width="204" height="34" style="%s">'
        '<p class="bk-caption" style="%s">First edition&nbsp;· 2026</p>'
        '<p class="bk-h2" style="%s">The parent company of Apex Paramedics and '
        'Royal Ambulance.</p>'
    ) % (
        "position:absolute;left:0;top:408px;width:1056px;height:408px;"
        "background:#000 url(%s) center 70%%/cover no-repeat" % WAVE,
        L_HORIZ_WHITE, at(RAIL_X, 232),
        at(RAIL_X, 296, RAIL_W, "color:#9E9E9E;margin:0;"),
        at(FIELD_X, 216, 593, "margin:0;color:#FFFFFF;font-weight:600;"
                              "letter-spacing:-0.003em;"),
    ), cls="dark", spine=False, foot=False)


# ---------- assembly ------------------------------------------------------

BUILDERS = {1: p01, 2: p02, 3: p03, 5: p05, 6: p06, 7: p07, 9: p09, 10: p10,
            11: p11, 12: p12, 13: p13, 15: p15, 16: p16, 17: p17, 19: p19,
            20: p20, 21: p21, 22: p22, 23: p23, 25: p25, 26: p26, 27: p27, 28: p28}
DIVIDERS = {d: (w, name, pp) for w, name, d, pp in PARTS}


def guard(doc):
    """Two things this document may never contain, checked before it is written.

    The first is a straight quote or an em dash in anything a reader sees, which
    the house rules forbid and which is easy to type by accident. The second is
    an internal reference: a file name, a class, a repository or a version tag.
    A brand manual that names its own build is not a brand manual.
    """
    visible = re.sub(r"<[^>]+>", " ", re.sub(r"<style.*?</style>", " ", doc, flags=re.S))
    visible = visible.replace("&nbsp;", " ").replace("&amp;", "&")
    bad = []
    for ch, why in (("—", "em dash"), ('"', "straight quote"), ("'", "straight apostrophe")):
        if ch in visible:
            i = visible.index(ch)
            bad.append("%s · %s" % (why, visible[max(0, i - 40):i + 40].strip()))
    for pat in (r"\.css\b", r"\.py\b", r"\.svg\b", r"\.json\b", r"\bbk-[a-z]", r"@v\d",
                r"cdn\.", r"brand-kit\b", r"\bsnippets/"):
        m = re.search(pat, visible)
        if m:
            bad.append("internal reference · %s" % visible[max(0, m.start() - 40):
                                                           m.end() + 40].strip())
    if bad:
        raise SystemExit("ce-manual: " + "\n           ".join(bad))
    return doc


def build():
    pages = []
    for n in range(1, 29):
        if n in DIVIDERS:
            w, name, pp = DIVIDERS[n]
            pages.append(divider(w, name, n, pp))
        else:
            pages.append(BUILDERS[n]())

    # The type layer and the palette come from the published kit, so this
    # document is a live test of the system rather than a picture of it. The
    # face is embedded as well, because a printed sheet that falls back to a
    # substitute face makes every measured claim in it false.
    css = open(os.path.join(HERE, "ce-manual.css"), encoding="utf-8").read()
    bar = ('<div class="bar noprint"><b>Collective Edge · Brand manual</b>'
           '<span class="hint">28 pages · 11 × 8.5in landscape</span>'
           '<span class="sp"></span>'
           '<span class="hint">Print with background graphics on, margins none</span>'
           '<button onclick="window.print()">Save as PDF</button></div>')

    doc = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>Collective Edge · Brand manual</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="%(cdn)ssnippets/type-system.css">
<link rel="stylesheet" href="%(cdn)ssnippets/palette.css">
<style>
/* The face travels with the sheet. Clamped to the ladder, not the file's full
   axis, so a request for a weight the system does not admit renders at the
   nearest one it does instead of silently shipping Thin. */
@font-face {
  font-family: "Montserrat";
  src: url("%(font)s") format("woff2-variations");
  font-weight: 400 800;
  font-style: normal;
  font-display: block;
}
%(css)s
</style>
</head><body>%(bar)s<div class="book">
%(pages)s</div></body></html>""" % {
        "cdn": CDN, "font": FONT, "css": css, "bar": bar, "pages": "".join(pages)}

    out = os.path.join(HERE, "ce-manual.html")
    open(out, "w", encoding="utf-8").write(guard(doc))
    return out, len(pages)


if __name__ == "__main__":
    p, n = build()
    print("  %-16s %d pages · %.1f MB" % (os.path.basename(p), n,
                                          os.path.getsize(p) / 1e6))
