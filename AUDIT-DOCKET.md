# Brand books · fix docket

210 raw findings in, 69 out: 11 blockers, 24 major, 24 minor, 10 polish. 15 raw findings were dropped and are listed at the end with the reason. Every number below was recomputed against the capture of
16:00 (`_audit/geom`, `_audit/png`, `_audit/pdf`), which is the first capture taken with
the stylesheets resolving and the viewport at 1600px. Work top to bottom inside each
section. Re-run `python3 harness.py && python3 cdp.py` after each geometry fix and check
the new numbers before moving on.

**Reference frame.** The slide is 1600 × 900. Margins are 96px top and bottom, 112px left
and right, so the content floor is y = 804 and the right margin is x = 1488. The running
foot occupies y 825 to 844, inside the bottom margin. Every well-behaved slide bottoms its
ink at or above 804 and leaves the foot 21px of air.

---

## Do first · the ten that matter

| # | Where | What |
|---|---|---|
| 1 | book.css:40 | The running foot is 2.56:1. It is on 14 of 16 pages. One line. |
| 2 | book.css:46,43 | Fix the second baseline. Every overflow sum below assumes it. |
| 3 | build.py:86 | The contents loses two entries in print. |
| 4 | book.css:126, build.py:262 | The weight ladder is clipped at the sheet edge. |
| 5 | book.css:119, build.py:272 | The scale ladder runs 498px off the sheet. |
| 6 | build.py:280 | The scale slide renders 96px and 72px at the same size. |
| 7 | book.css:94 | The colour captions print through the running foot. |
| 8 | book.css:173 | CE slide 15 prints its code through the running foot. |
| 9 | book.css:85,109,122,130,137,171 | 53 nodes per book print at 8.26pt. |
| 10 | build.py:146 | The CE book publishes a minimum mark size the CE kit does not define. |

---

# All three books

## Blocker

### B1 · Slide 11 · the scale ladder runs 498px off the sheet
`build.py:272-285`, `book.css:119-124`

Nine `.scale-row` boxes run y 344 to 1398. That is 594px past the 804 floor and 498px past
the 900 frame. 15 text nodes carry `pastBottom`. In `_audit/pdf/apex.pdf` page 11 the
deepest block is `Interfacility transport` at y 662.3 to 691.6pt against a 675.12pt sheet,
clipped 16.5pt into the glyphs; the h3, h4, body-lg and body rows produce no text on the
page at all.

The row heights are set by the `.m` spec block, not by the specimen: `.m` is 59px on every
row (three lines of 11px at line-height 1.8 inside a 210px column) while the h2 sample is a
40px line box.

Change, in `book.css`:

```css
.scale-row { display: grid; grid-template-columns: 260px 1fr; gap: 32px; align-items: baseline;
             padding: 8px 0; border-top: 1px solid var(--border-1); }
.scale-row .m { font-family: var(--font-mono); font-size: 12px; line-height: 1.6; color: var(--fg-3); }
```

At 260px and 12px mono a spec string of 35 characters sets on one line, so `.m` becomes two
lines at 38.4px instead of three at 59px.

Change, in `build.py`, the slide 11 body from one column to two:

```python
+ f'<div class="s-body" style="display:grid;grid-template-columns:800px 512px;gap:0 64px">'
+ f'<div>{rows_display}</div><div>{rows_text}</div></div>'
```

with `rows_display` carrying `display-xl` through `h2` and `rows_text` carrying `h3` through
`eyebrow`. 800 + 64 + 512 = 1376. Set the sample word to `Dispatch`, which at 96px ExtraBold
measures about 428px and clears the 508px the left column leaves after the spec block.

Arithmetic to verify after re-capture: column one 100.8 + 77.8 + 61.6 + 47.2 + 40 line boxes
plus 5 × 17 of padding and rule = 412px; column two seven rows at about 55px = 388px. Both
inside 460. If column two overruns, split the ladder across two slides at h3 rather than
shrinking the specimen further.

### B2 · Slide 10 · the weight ladder is clipped at the sheet edge
`book.css:126-132`, `build.py:256-266`

Six `.wt-row` boxes run y 344 to 1083: 279px past the floor, 183px past the frame. In
`apex.pdf` page 10 the last block, `800 ExtraBold / Interfacility transport`, spans
y 639.8 to 676.5pt against the 675.12pt sheet and overlaps the running foot at
y 620.1 to 630.6pt. Same 59px `.m` block driving the height as B1.

Change, in `book.css`:

```css
.wt-row { display: grid; grid-template-columns: 300px 1fr; gap: 32px; align-items: baseline;
          padding: 8px 0; border-top: 1px solid var(--border-1); }
.wt-row .m { font-family: var(--font-mono); font-size: 12px; line-height: 1.6; color: var(--fg-3); }
```

Change, in `build.py:262-266`, so the two reserved rows carry the label alone and no live
sample. This is also what clears the R2 validator failure in M3, because `font-weight: 200`
and `font-weight: 900` then leave the source entirely:

```python
wr = "".join(
    (f'<div class="wt-row off"><div class="m"><b>{"100 · 200 · 300" if w == 200 else 900} '
     f'{E(nm.split(",")[0])}</b>{E(use)}</div><div></div></div>' if off else
     f'<div class="wt-row"><div class="m"><b>{w} {E(nm.split(",")[0])}</b>{E(use)}</div>'
     f'<div class="sample" style="font-weight:{w}">{E(spec)}</div></div>')
    for (w, nm, use, off), spec in zip(W, SPECIMENS))
```

Four sample rows at about 75px plus two label rows at about 36px is 372px inside 460.

### B3 · Slide 2 · the contents loses two of its thirteen entries in print
`build.py:86-92`

Thirteen 56px rows run y 278 to 979: 188px past the floor and 92px past the frame. The row
carrying `13 Components` sits at y 838 and prints straight through the foot span
`APEX PARAMEDICS` at y 825; it is visible as struck-through type in `png/apex-02.png`. In
`apex.pdf` page 2 the deepest block is a bare `14` at y 671.9 to 683.3pt against the
675.12pt sheet, `Do and do not` produces no text, and `15 Assets` is absent.

Change, in `build.py:86-92`, to two columns of seven and six:

```python
rows = "".join(
    f'<div style="display:grid;grid-template-columns:56px 1fr;gap:20px;padding:12px 0;'
    f'border-top:1px solid var(--border-1)">'
    f'<span style="font-family:var(--font-mono);font-size:12px;color:var(--fg-3)">{i + 1:02d}</span>'
    f'<span class="bk-body-lg">{E(t)}</span></div>'
    for i, t in enumerate(toc))
add("", head("Contents", "Thirteen sections.")
    + f'<div class="s-body" style="display:grid;grid-template-columns:656px 656px;'
      f'gap:0 64px;grid-template-rows:repeat(7,auto);grid-auto-flow:column">{rows}</div>')
```

656 + 64 + 656 = 1376. Seven rows at 54px is 378px inside the 460px body. The same edit
carries the fixes in B5 (`--fg-3`), M14 (`i + 1`), m1 (`bk-body-lg`) and m11
(the heading).

### B4 · Slide 6 · the colour captions print through the running foot
`book.css:94-98`

`.swatch .chip` is a fixed 340px inside a 460px body. Apex `.swatch` boxes bottom at y 912,
12px past the sheet; Royal and CE at 889. The caption `p.use` sits at y 816 to 884 in Apex
and overlaps the foot band at 825 to 844. Confirmed in print: `royal.pdf` page 6 returns
`Headers, links, accent rules, column heads` at y 612.8 to 643.0pt and `ROYAL AMBULANCE / 06`
at y 620.1 to 630.6pt. The rightmost swatch also encloses the folio, so `06` floats inside
the Surface chip in `apex-06.png`.

Apex is the worst case because its Accent caption runs three lines. Below the chip the info
block needs 24 padding + 32 name + 8 + 46 hex + 16 + 68 caption + 24 padding = 218px, so the
chip may be at most 460 − 218 − 1 = 241px.

```css
.swatch .chip { height: 240px; flex: none; }
.swatch .info { flex: 1 1 auto; padding: 24px; background: var(--bg-canvas); }
.swatch .nm   { font-weight: var(--weight-bold); font-size: 20px; letter-spacing: -0.008em; margin: 0 0 8px; }
.swatch .use  { font-size: 14px; line-height: 1.5; color: var(--fg-3); margin: 16px 0 0; max-width: 26ch; }
```

Do not solve this by shortening the captions in `build.py`. The line count varies by brand
and the geometry has to hold for the longest one.

### B5 · The running foot is set in a colour every kit forbids as text
`book.css:40`, `build.py:89`

41 text nodes per book fall under 3:1: the 28 running-foot spans on slides 2 to 15 plus the
13 contents numerals on slide 2. Apex and Royal render `#94A3B8` on white at 2.56:1 at 12px
and 13px. CE renders `#9A9A9A` at 2.81:1.

The kits say so themselves. `collective-edge-brand-kit/tokens.json` on `#9A9A9A`: "Dimmed
non-text marks. 2.81:1 on white, so never text at any size". `apex-brand-kit/tokens.json`
on `#94A3B8`: "dimmed labels, never body text", and separately names `#64748B` "secondary
text, metadata, footer". The kit names a footer colour and the book uses a dimmer one.

```css
.s-foot { ... color: var(--fg-3); }
```

4.76:1 in Apex and Royal, 5.10:1 in CE. The `build.py:89` half is folded into B3.

### B6 · Slide 11 clamps its own specimen
`build.py:280`

`font-size:{min(px,58)}px`. The row labelled `96px · 72pt · 800 · 1.05 · -0.020em` renders
at 58px and the row labelled `72px · 54pt · 800 · 1.08 · -0.018em` also renders at 58px,
while the row below, labelled 56px, renders at 56px. Three declared steps of 96, 72 and 56
render as 58, 58 and 56, and the two top rows are indistinguishable in `png/apex-11.png`.
The one slide whose entire job is to prove the scale disproves it.

```python
f'<div class="sample" style="font-size:{px}px;font-weight:{r["weight"]};'
```

Delete the clamp. The two-column layout in B1 is what makes true size fit.

### B7 · Slide 11 states a rule that is false and hides the counter-example
`build.py:274, 282-284`

The subhead reads "Every step lands on a whole point size, so the same scale executes in
PowerPoint and Word." `type-tokens.json` has twelve steps and `body-sm` is 10.5pt. The loop
renders `TOK["scale"][:9]`, so the three steps it suppresses are `body-sm`, `caption` and
`eyebrow`, and `body-sm` is the one that would disprove the sentence. The book also sets
from all three: `.bk-body-sm` on slide 13 and `.bk-caption` on slides 5, 9, 12 and 13.

```python
for r in TOK["scale"]:
```

and

```python
add("", head("09", "The ladder.",
             "Twelve steps. Eleven land on a whole point size; body-sm is 10.5pt. "
             "The same scale sets in PowerPoint and Word.")
```

Drop the trailing "The top of the ladder is 72pt." It restates row one of the table directly
beneath it. The heading change is M15.

### B8 · 53 nodes per book print below the house's own 9pt floor
`book.css:85, 109, 122, 130, 137, 171`

`apex.pdf` MediaBox is `[0 0 1200.95996 675.12]` over a 1600 × 900px slide, so the scale is
0.7506 pt/px and 11px prints at 8.26pt. `type-system.css:435` names the floor in the kit's
own words: "under the 9pt floor in section 9". Counted at 11px: Apex 53 nodes, Royal 53,
CE 52, on slides 5, 7, 8, 10, 11, 13 and 15. The ladder's smallest step is 12px, which
prints at exactly 9.01pt.

Raise every one of the six rules to `font-size: 12px`. B1 and B2 already do `.scale-row .m`
and `.wt-row .m`. The remaining four are `.logo-grid .cap`, `.pair .spec`, `.demo .lbl` and
`.ref th` (see m2, which deletes the `.ref th` size outright).

### B9 · font-weight 500 on 51 to 53 nodes per book
`book.css:86, 123, 131, 171, 174`

500 is not in the ladder, and section 3 of the standard names it explicitly: "600 is the
floor, because 500 is not in the ladder". The `@font-face` clamps the axis to 400 to 800, so
500 is inside the range and renders as a true 500. It appears on slides 3, 5, 9, 10, 11, 12
and 15 in all three books.

It is also why those slides carry four weights against rule 3's maximum of three. Measured
per slide, removing 500 drops slides 3, 5, 12 and 15 from `400 / 500 / 600 / 700` to exactly
`400 / 600 / 700`.

Replace all five with `font-weight: var(--weight-semibold)`.

## Major

### M1 · There is no fixed second baseline
`book.css:43, 46`

The horizontal rule sits at y 223, 272 or 303 and the body starts at y 264, 313 or 344,
depending on whether that slide's standfirst exists and how many lines it runs. The steps
are 49px and 31px. In a printed manual the reader sees the rule jump by 80px between
spreads.

The rule also floats: 48px above it, 40px below it. It binds to neither the head nor the
body, which is why the top of every content slide reads detached in `png/apex-03.png` and
`png/apex-05.png`.

```css
.s-rule { height: 1px; background: var(--border-1); margin: 0 0 39px; flex: none; }
.s-head { flex: none; height: 160px; margin: 0 0 48px; }
```

Measured head heights are 79px (no standfirst), 128px (one line) and 159px (two lines), so
160px holds the tallest. Every content slide then rules at y 304 and starts its body at
y 344 with a 460px body, and the 1px rule plus the 39px margin is a 40px step. Every
overflow sum in B1 through B4 and M11 assumes this.

### M2 · Five `max-width: none` on `.bk-caption`
`build.py:151, 316, 345, 351, 352`

`validate.py` flags all five as R9 in all three books. The slide 5 caption then sets 130
characters on one unbroken 1376px line, which is 173ch against the 40ch caption measure;
slide 13's diagram caption sets 618px, 77ch. The book switches off the measure token it
teaches two slides later.

Delete `max-width:none` from all five and let `--measure-caption` hold. The two footer
strings on slide 13 are 47 and 4 characters, inside 40ch = 52 real characters, so they are
unaffected. The slide 5 caption then breaks to three lines; its rewrite is m13.

### M3 · All three books fail the house validator
`build.py`, `collective-edge-brand-kit/scripts/validate.py`

`python3 scripts/validate.py` returns exit 1 on all three: 15 violations across 3 rules.
Section 11 requires this gate before shipping, and these books are the reference specimen.

- R2 × 2: `font-weight: 200` and `font-weight: 900` at line 100. Cleared by B2, which
  removes the two live samples.
- R9 × 5: cleared by M2.
- R14 × 8: all eight are inside the slide 15 code specimen, where straight quotes are
  correct. The validator is wrong here and the book is right. Teach `validate.py` to skip
  text inside `pre` and `.bk-code`, which is the only place straight quotes belong. Do not
  add an opt-out attribute to the book; a reference specimen should pass without an
  exemption.

The prose apostrophes are a separate, real R14 case: see m15.

### M4 · 58 percent of the type in the book is a system monospace
`book.css:39, 62, 66, 85, 109, 122, 130, 137, 159, 170`

Nodes rendering in `ui-monospace`: Apex 183 of 316, Royal 182 of 313, CE 184 of 314. Section
2 of the standard: "Any string a person retypes, dictates or reads aloud goes in the mono
face ... Everything else is Montserrat." Rule 13 repeats it. The mono currently carries the
brand name on the cover, every running foot, every panel label, every table label column and
every specimen annotation. On slide 15 the whole Asset column (`Type system`, `Palette`,
`Colour tokens`, `Brand registry`) is Menlo where only the path column is a code.

Strip `font-family: var(--font-mono)` from `.s-foot` (:39), `.slide.cover .meta` (:62),
`.logo-grid .cap` (:85), `.demo .lbl` (:137), `.dd h4` (:159) and `.ref` (:170).

Keep it, or re-apply it narrowly, where the content is genuinely a code:
`.swatch .hex`, `.bk-code`, `.pair .spec` (the hex pair line only), `.scale-row .m b` and
`.wt-row .m b` (token names), `.ref td:not(:first-child)` (the path column), and the
`{repo}` string on the back cover, which should be wrapped in `.bk-code` at
`build.py:409`.

`.slide.divider .num` (:66) is dead: no divider slide is emitted. See m18.

### M5 · Nine invented sizes carry 53 percent of the text
`book.css:97, 107, 150, 164, 170`, `build.py:233, 234`

Apex size census across 316 nodes: 11, 11.28, 12, 12.5, 13, 14, 15, 15.04, 16, 17, 20, 24,
32, 34, 40, 52, 56, 58, 72, 150. Twenty distinct sizes. Off the ladder and not a `.bk-code`
derivative (`.bk-code` is 0.94em, which is where 11.28 and 15.04 come from): 11 (53 nodes),
12.5 (60), 13 (23), 15 (8), 17 (19), 34 (1), 52 (2), 58 (2), 150 (1) = 169 of 316, 53
percent.

| Site | Now | Ladder step |
|---|---|---|
| `book.css:170` `.ref` | 12.5px | 12px |
| `book.css:97` `.swatch .hex` | 13px | 12px |
| `book.css:107` `.pair .demo` | 17px | 16px (M7) |
| `book.css:164` `.dd li` | 17px | 16px |
| `book.css:98` `.swatch .use` | 15px | 14px (B4) |
| `book.css:150` `.d-stat .bk-stat` | 52px | 56px |
| `build.py:234` alphabet | 34px | 40px (M11) |

58px is deleted by B6. Keep 150px on slide 9: it is a face specimen and reads as one.

### M6 · The muted foreground fails AA on the tinted surface
`book.css:138, 146`

11 nodes per book at 4.31:1 in Apex and 4.43:1 in Royal: `#64748B` on the Apex tint
`#F3F3FB` and the Royal tint `#FAF5FD`, across slides 7, 13 and 15. The same colour on white
is 4.76:1, so the tint alone costs 0.45 and 0.33. On slide 13 every even row of the demo
table is below AA while every odd row passes. CE escapes it: `#6E6E6E` on `#FAFAFA` is
4.89:1 and CE has zero nodes in the 4.2 to 4.5 band.

```css
.demo .lbl { ... color: var(--fg-1); ... }
.d-table td { padding: 12px 16px; border-bottom: 1px solid var(--border-1); color: var(--fg-1); }
```

`#1E293B` on `#F3F3FB` is 13.25:1.

### M7 · The contrast specimen is set at a size at which its own verdict fails
`book.css:107`, `build.py:218`

`.pair .demo` is `font-size: 17px; font-weight: var(--weight-semibold)`. WCAG large is 24px,
or 18.66px at 700; 600 is not bold. Apex marks two pairs LARGE OR BOLD and renders both at
17px/600: `#B77808` on white at 3.68:1 and white on `#4A8E3A` at 4.02:1.
`apex-brand-kit/tokens.json` is explicit about the first: `#B77808` "clears the 3:1
large-text threshold only: 18pt print or 24px web and up, never an eyebrow, a caption, a
table cell or body copy". The slide's own subhead reads "A pair marked large or bold is
never body copy" and the specimen beside it is body size. 17px is also not on the ladder.

```css
.pair .demo { display: flex; align-items: center; padding: 0 24px;
              font-weight: var(--weight-regular); font-size: 16px; }
```

and `build.py:218`, the tile string, `Aa 17px` becomes `Aa 16px`.

The tile then shows the pair at true body size and the verdict column says whether that is
legal, which is the honest reading of the slide.

### M8 · The word that grades the contrast is itself under 4.5:1
`book.css:115`

`.pair .verdict.large { color: var(--status-warn) }`. `#B5821A` on white is 3.40:1, rendered
at 12px weight 400, twice in Apex and once each in Royal and CE. The other two verdict
colours pass: `--status-go` `#1E7A4D` is 5.32:1 and `--status-stop` `#B0322B` is 6.29:1. The
kits document 3.40:1 correctly, so the book knowingly sets 12px type in a colour its own
token measures below AA.

```css
.pair .verdict.large { color: var(--fg-1); box-shadow: inset 4px 0 0 var(--status-warn); }
```

A 3.40:1 non-text mark is legitimate; a 3.40:1 word is not.

### M9 · 35 off-grid vertical declarations
`book.css` × 18, `build.py` × 17

Rule 12 admits no exceptions. Parsed vertical margin, padding and gap values, excluding
border widths and the screen toolbar:

`book.css` 47 (14), 49 (18), 80 (22), 82 (150), 84 (110), 95 (26), 96 (10), 98 (14),
108 (18), 120 (18), 138 (14), 139 (26), 141 (22), 143 (9), 149 (10), 152 (14), 160 (26),
173 (11).

`build.py` 87 (13), 97 (26), 102 (26), 111 (34), 151 (26), 181 (150), 187 (14), 234 (34),
238 (30), 314 (26), 316 (10), 326 (10), 345 (18), 396 (26), 398 (10), 407 (58), 408 (34).

Snap each to the nearest step: 9, 10 and 11 to 8 or 12; 13 and 14 to 12 or 16; 18 to 16;
22 to 24; 26 to 24; 30 and 34 to 32; 58 to 56; 110 to 112; 150 to 152. Several sites are
already carried by B1, B2, B3, B4 and M11.

### M10 · Three different column gutters
`build.py:106, 231, 292`, `book.css:135`

Measured sibling gutters: 80px on slide 3, 64px on slides 9 and 12, 40px on slides 7 and 13.
Slide 3 is `1.1fr 1fr; gap: 80px`, which resolves to 679px and 617px with the fold at
x 791 and the second column opening at 871. Nothing on any other slide aligns to either
number.

Pick 64 and hold it. `book.css:135` `.demo-grid { gap: 64px }` gives two 656px columns.
`build.py:106` becomes `grid-template-columns:736px 576px;gap:64px` (736 + 64 + 576 = 1376).
Slides 9 and 12 already use 64px and need no change.

### M11 · Slide 9 · both columns run past the floor and the panel encloses the folio
`build.py:231-252`, `book.css:170-174`

Both `.s-body` grid children measure y 344 to 842, 38px past the floor, because their
content is 498px inside a 460px body. The right panel spans x 1108 to 1488 and the folio
span sits at x 1471 to 1488, y 825 to 844, so the panel's bottom border passes through the
numeral and `09` reads as a table row in `png/apex-09.png` and `png/ce-09.png`.

The eight-row `.ref` table is 344px of that. Cutting the row height fixes the overflow and,
because the grid children stretch once their content fits, drops the panel bottom back onto
804 automatically:

```css
.ref th { text-align: left; letter-spacing: 0.11em; text-transform: uppercase;
          font-weight: var(--weight-semibold); color: var(--fg-3);
          padding: 8px 16px; border-bottom: 1px solid var(--border-1); }
.ref td { padding: 4px 16px; border-bottom: 1px solid var(--border-1); color: var(--fg-2); }
```

Eight rows then measure about 224px against 344px today. This is the same edit that clears
the CE slide 15 blocker.

Second half of the slide: the alphabet `div` at `build.py:234` declares
`max-width: 22ch` = 495px and reports `scrollWidth` 630 with ink reaching x 742, so the
declared box describes nothing. It also gives the slide a fourth size above body
(20, 34, 40, 150) against rule 3's maximum of three, and it is not a scale specimen, so it
has no claim on the exemption slides 10 and 11 have. Move it to a class and set it on the
ladder:

```css
.alpha { font-size: 40px; line-height: 1.35; margin-top: 32px;
         color: var(--fg-2); max-width: 780px; }
```

Slide 9 then reads 20 / 40 / 150.

### M12 · Four uppercase runs over four words
`book.css:62`, `build.py:308, 343`

Rule 6 and rule 7 cap an uppercase run at four words. Measured across all three books:

- Slide 16 `.meta`, 11 words: `HOUSE TYPE SYSTEM V1.0 · COLLECTIVE-EDGE/APEX-BRAND-KIT · VERIFY WITH SCRIPTS/VALIDATE.PY BEFORE YOU SHIP`. This is a full instructional sentence in caps.
- Slide 1 `.meta`, 7 words.
- Slide 12 `.bk-eyebrow`, 5 words: `MEASURE, AT THE REAL WIDTH`.
- Slide 13 `.lbl`, 6 words: `DIAGRAM ROLES, IDENTICAL IN EVERY BRAND`.

Both `.meta` nodes also report `overflowX` true, running past their 488px box because
`book.css:62` sets `white-space: nowrap` while the `max-width` is inherited and can never
bind. On CE the back-cover line reaches x 1376, exactly the right margin, with zero
clearance.

```css
.slide.cover .meta { margin: 32px 0 0; max-width: none; font-size: 14px;
                     letter-spacing: 0.06em; color: var(--fg-on-dark-2); }
```

Drop `text-transform: uppercase`, drop `white-space: nowrap`, drop the mono per M4, and let
both cover lines set sentence case. In `build.py`, slide 12's eyebrow becomes `Real measure`
and slide 13's label becomes `Diagram roles, house-wide` (three words, and it keeps the
fact the panel cannot show).

### M13 · Slide 3 · the At a glance panel is an empty box
`build.py:111-121`

The bordered panel runs y 264 to 804 and its last table rule lands at y 582. That leaves
222px of empty box below the last row, in a slide whose left column also stops at y 480.
Visible in `png/apex-03.png` as a tall frame with content in its top third. The slide reads
unfinished.

Add the two facts the book has and does not print here, so the panel earns its height:

```python
<tr><td>Measure</td><td>54ch = 70 characters</td></tr>
<tr><td>Minimum mark</td><td>{E(mn.get('horizontal', 'no minimum set'))}</td></tr>
<tr><td>Surface tint</td><td>{col['surfaceTint'].upper()}</td></tr>
<tr><td>Registry</td><td>brands.json · {E(key)}</td></tr>
```

Ten rows at 43px is 430px against the 540px this slide's body gives it. If the panel is to
stay at six rows, close the box instead: drop `height` from the panel so it wraps its
content and let the slide breathe under it, rather than drawing a frame around white.

### M14 · The contents numbers a different thing from the slide it points at
`build.py:89`

The contents rows print 03 to 15, the deck page number. Each slide badges itself 01 to 13,
the section number, in its eyebrow. Every row is off by two: a reader who follows
`08 Contrast` arrives at a page labelled `06`. Print `{i + 1:02d}`. Folded into B3.

### M15 · The contents does not match the headings it points at
`build.py:83-85`

Four of thirteen entries use different words from the heading on the page: `Contrast` vs
`Contrast, measured.`; `Typeface` vs `Montserrat.`; `The weight ladder` vs `Four weights
carry every brand.`; `The scale` vs `One ladder.` The other nine match once the full stop is
removed.

Worse, the ladder metaphor is attached to two different slides: `The weight ladder` points at
slide 10 and `One ladder.` is the heading on slide 11. A reader looking for the ladder is
sent to the wrong page.

Set the headings so the contents wording is what the reader scans for, and derive the `toc`
list from the same strings passed to `head()` instead of maintaining a second list:
slide 8 `Contrast, measured.`, slide 9 `Typeface.`, slide 10 `Four weights.`, slide 11
`The ladder.`

### M16 · Montserrat is not embedded in any of the three PDFs
`build.py:422-429`

`/BaseFont` entries in all three PDFs: `Menlo-Regular` (five subsets) and `Menlo-Bold`. No
Montserrat entry. `apex.pdf` contains 102 `/Type3` objects, 6 `/FontFile2` and 6 `/Type0`,
all of them Menlo. Type3 is Chrome drawing glyph procedures rather than embedding the face,
so the manual's own type is unsearchable and unselectable in the print deliverable, and the
only real font in it is the one M4 is trying to remove. Section 11 requires Montserrat
actually embedded for PDF.

The cause is the variable `@font-face` with `font-weight: 400 800`, which Chrome's PDF writer
degrades. The kit ships only `Montserrat-VariableFont_wght.woff2/.ttf`, so this needs static
instances first:

```bash
python3 -m fontTools.varLib.instancer \
  collective-edge-brand-kit/assets/fonts/Montserrat-VariableFont_wght.ttf \
  wght=400 -o Montserrat-Regular.ttf     # repeat for 600, 700, 800
```

Then add a print-path `@font-face` block to `build.py`'s head pinning the four static
instances, and re-check `/BaseFont` after. This one crosses into the kit repo; confirm before
committing there.

### M17 · Slide 8 dies well above the floor, by a different amount in each book
`book.css:101-102`

The pair table bottoms at y 651 in Apex and Royal (four rows) and y 574 in CE (three rows),
against a floor at 804. That is 153px and 230px of dead white in a book that simultaneously
overflows five other slides. The lower third of `png/ce-08.png` is empty.

`.pairs` gets a fixed 460px and lets the rows divide it, so the table bottoms on the floor
whatever row count the brand supplies:

```css
.pairs { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0;
         border: 1px solid var(--border-1); height: 100%; grid-auto-rows: 1fr; }
```

115px per row at four rows, 153px at three. Do not centre the short table vertically; the
body column starts at a consistent y throughout the book.

## Minor

- **m1 · `build.py:90`** The contents rows use `.bk-h4` with `font-weight` forced to 400,
  which is 20px at 400, which is exactly `.bk-body-lg`. The override also silently buys a
  1.45 leading where the body step it imitates leads at 1.55. Use `class="bk-body-lg"` and
  delete the inline weight. Folded into B3.
- **m2 · `book.css:171`** `.ref th` is 11px against `.ref` at 12.5px. Section 4: "Caps
  labels sit at the same size as the body they label, never smaller." Delete the
  `font-size` declaration from `.ref th` so it inherits. Carried by M11.
- **m3 · `book.css:159`** `.dd h4` sets family, size, tracking and transform but no weight,
  so the user-agent bold applies and `DO` and `NEVER` render uppercase at 700. Rule 2 gives
  uppercase labels to 600. Add `font-weight: var(--weight-semibold)`.
- **m4 · `book.css:97`** `.swatch .hex` declares no `letter-spacing`, so the six hex values
  are the only untracked uppercase runs in the book; every other mono run carries between
  0.06em and 0.16em. Rule 6: uppercase is always tracked. Add `letter-spacing: 0.06em`.
- **m5 · `book.css:152`** `.node` is 13px at 600. White on `#4A8E3A` is 4.02:1 and
  `brands.json` licenses the fill with `"large or bold only, which is what a node label
  is"`. At 13px/600 it is neither. Set `font-size: 20px; font-weight: var(--weight-bold)`,
  which is above the 18.66px bold threshold the sentence relies on. Three nodes at 20px
  measure about 535px inside the 642px panel.
- **m6 · `build.py:265, 276`** `Interfacility transport` appears 13 times per book: six on
  slide 10, six on slide 11, once on slide 7, plus `Interfacility transport brief` on slide
  13. It reads as a placeholder nobody replaced. Give the weight ladder four different
  two-word specimens so a reader sees each weight on different letterforms:
  `Interfacility transport` (400), `Critical care ground` (600), `Dispatch and staging`
  (700), `Bay Area coverage` (800).
- **m7 · `build.py:277`** Slides 11 and 12 demonstrate different rules with the same words.
  Shared 4-grams: "crews receive the authorization", "receive the authorization number",
  "and the return window". Change slide 11's text-step sample to
  `Dispatch quotes the level of service and the receiving unit before the crew rolls.` and
  leave slide 12 as the single measure specimen.
- **m8 · `build.py:361-372`** Four of the twelve do/never items restate four of the ten rows
  in the composition table two slides earlier (uppercase tracking, mono for codes,
  justification, body measure), and the same rule is written `4 words` on slide 12 and
  `four words` on slide 14. Cut the four duplicates, replace them with rules the book has
  not yet stated, and hold one numeral style: numerals for measured values, words for counts
  under ten, so slide 12 reads `never past four words`.
- **m9 · `build.py:373-377`** The heading is `Do and do not.` and the column head is
  `Never`. Under `Do` every item is an imperative; under `Never` five of six are noun
  fragments. Set the column head to `Do not` so heading, contents row and column agree, and
  rewrite the six as imperatives.
- **m10 · Restatement, six sites.** Section 11's checklist forbids helper text and captions
  that restate the thing above them.
  - `build.py:92` eyebrow `Contents` over heading `What is in this book.` Set the heading to
    `Thirteen sections.` (carried by B3).
  - `build.py:228-230` heading `Montserrat.` over a subhead that restates it and then lists
    the other two brands by name in a book issued to one. Set
    `Every brand in the house sets in Montserrat. The kit ships the variable font with the
    axis clamped from 400 to 800.`
  - `build.py:192, 196` labels `Header band` above a header band and `Stat callout` above a
    stat callout. Set `Header band, deep on primary` and `Stat callout, accent rule only`.
  - `build.py:332, 348, 354` labels `Table`, `Footer`, `Eyebrow and heading` naming what sits
    under them. Set `Table, header band and mono figures`, `Footer, 2px band rule above`,
    `Eyebrow at 12px, heading at 24px`.
  - `build.py:312` caption `54ch · 70 characters · 572px at 16px` under a table row reading
    `54ch = 70 characters`. Cut the repeated pair, keep `572px at 16px`.
  - `build.py:250` caption `Montserrat is wide. That is why measure caps at 54ch ...` two
    lines under a table row headed `Cap height`, and the 54ch figure appears twice more on
    slide 12. Set `Montserrat runs 16.7% wider than Helvetica. That is why no wrapping line
    leads below 1.05.`
- **m11 · `build.py:345-346`** The diagram caption promises measured text colours and prints
  none, in a book that spends a full slide printing seven contrast ratios. Print the ratio
  under each node chip from `dr[k]['contrast']` and cut the sentence; `Rectangles, 6px
  radius. Role is carried by fill, never by shape.` is enough prose.
- **m12 · `build.py:268`** `The @font-face clamps the axis to 400 to 800` stumbles on
  `to ... to`. Set `clamps the axis from 400 to 800`. In the same pass,
  `build.py:290` `These are the rules that make a page look set rather than typed.` becomes
  `These rules make a page look set rather than typed.`
- **m13 · `build.py:151-154`** Three specs hang off one label that describes only the first,
  and clear space is not a minimum size. Each cell also prints its name three ways:
  `Horizontal`, `on light`, `horizontal-on-light`. Split into two captions,
  `Minimum size · horizontal {h} on screen, 1&nbsp;inch in print · mark {m}` and
  `Clear space · the height of the mark, on all four sides`, and in the cell drop the human
  label and keep the filename in mono, since the slide's own point is that the file is named
  for the background.
- **m14 · Units without a non-breaking space, four sites.** Rule 14 requires one.
  `1 inch` (slide 5), `1.302 chars` (slide 9), `70 characters` (slide 12, twice),
  `4 words` (slide 12). The three `min` values on slide 13 are already inside `.bk-code`,
  which sets `white-space: nowrap`, so they are safe. Replace the space with `&nbsp;` in the
  four real sites.
- **m15 · `build.py:329, 361`** Straight apostrophes in prose: `this brand's palette` on
  slide 13 and `this brand's palette.css` on slide 14, in all three books. Rule 14 asks for
  curly. Use U+2019. The eight apostrophes and quotes inside the slide 15 code specimen are
  correct as they are; see M3.
- **m16 · `build.py:196-200`** The stat callout renders `Median 7.2` and `On time 98%`.
  Median of what is never stated, and `98%` reads as marketing furniture on a page of
  measured hex values. Reuse the figures already printed in the slide 13 table so the book
  carries one dummy dataset instead of two: `Median minutes 22` and `Runs 1,284`.
- **m17 · `book.css:64-67`** `.slide.divider`, `.slide.divider .num` and `.slide.divider h2`
  are dead. `build.py` emits no divider slide. Delete the three rules, or add the divider the
  book's section numbering implies.
- **m18 · `harness.py`** Nothing fails the build when the capture is wrong. Two guards, both
  cheap, both of which would have caught defects this audit had to find downstream:
  after `make_audit_html`, assert that every `href` and `src` in the written file resolves on
  disk and abort if one does not; and after the geometry pass, fail the run if any `.s-body`
  reports `scrollHeight > clientHeight`, so an over-stuffed slide is a build error rather
  than something the PDF discovers.
- **m19 · `cdp.py` GEOM_JS `bgOf()`** The function walks ancestors only and returns `IMAGE`
  only when an ancestor paints one, so it cannot see a background painted by an absolutely
  positioned sibling. Across all three books, 943 text nodes, not one resolved to `IMAGE`,
  including the CE cover, which sits on a photograph. Before returning a colour, use
  `document.elementsFromPoint` at the box centre and return `'IMAGE'` if any element under it
  paints a `background-image`. The CE cover measures fine when measured properly (see
  CE-major-2), but nothing in the harness would have said so if it did not.

## Polish

- **p1 · `book.css:61`** The cover has three left edges. Measured first ink in
  `png/apex-01.png`: mark x 114, the 72px headline x 118, the mono meta line x 113. All
  three boxes are at x 112. Add `margin-left: -5px` to `.slide.cover h1`.
- **p2 · `book.css:36-41`** The folio never reaches the right margin. On all 42 content
  slides the `.s-rule` and the table borders put their last ink at x 1487; the folio's last
  ink is at x 1485. The cause is the trailing letter-space of `letter-spacing: 0.10em` at
  12px. Add `.s-foot > :last-child { margin-right: -0.10em }`.
- **p3 · `book.css:61, 67`** `max-width: 20ch` on the cover headline and `18ch` on the
  divider heading, against `--measure-display: 16ch`. The system publishes the value; the
  book invents two others. Use `var(--measure-display)`. `Brand guidelines` is 16 characters
  and still sets on one line.
- **p4 · `build.py:150-154`** Slide 5 stops 107px above the floor: the variant cards end at
  y 654 and the caption at y 697. It is the only element on the slide and there is height to
  give it. Raise `.logo-grid .frame` `min-height` from 150px to 232px so the row bottoms with
  the rest of the book.
- **p5 · Voice.** `Every` opens nine distinct strings across eight consecutive slides:
  slides 5, 6, 9, 10, 11, 12, 13, 14 twice. The rules read as one voice repeating itself
  rather than as a set of separate laws. Keep it where it is a real universal quantifier
  (slides 6, 11, 14) and rewrite the rest.
- **p6 · Heading punctuation.** Eleven of thirteen headings are noun labels wearing a full
  stop; only `Four weights carry every brand.` and `One ladder.` are sentences. The cover
  takes no stop. Pick one and hold it: either drop the stop from the eleven labels, or make
  all thirteen declarative.
- **p7 · `build.py:78, 408`** The cover and the back cover share the version line, so the
  last page adds one new fact in nine words. Drop the version from the back cover and let it
  carry only what the cover cannot.
- **p8 · `build.py:149`, apex `colorNote`** Two semicolons in a book that bans the em dash
  on the grounds that a period or a comma does the work. `Never recolour a mark; every
  variant ships as a file.` becomes two sentences.
- **p9 · `collective-edge-brand-kit/brands.json`** `diagramRoles.process.contrast` reads
  `10.37:1` for `#FFFFFF` on `#3E3E3E`. The WCAG formula gives 10.70:1, and the rendered
  Process node measures 10.7 in all three geometry files. Every other documented ratio in
  the three kits checks out exactly: 4.02, 6.98, 2.70, 3.68, 1.91, 2.74, 2.81, 5.10, 3.40,
  5.32 and 6.29 all match to two decimals. Set `10.70:1`.
- **p10 · `apex-brand-kit/tokens.json`, `royal-brand-kit/tokens.json`** Their `diagramRoles`
  entries carry `fill`, `border`, `css` and `use` but no `text`, `contrast` or `textRule`,
  while `brands.json` carries all three. `#111111` is the Warning node label in Apex and
  Royal slide 13 at 6.98:1 and a generator reading a brand kit alone cannot reproduce it.
  Mirror the three fields into both kits. Otherwise the off-palette scan is clean: every
  text and background colour in all three books is present in that brand's `tokens.json`.
  Inventory: Apex 13 distinct text colours and 7 backgrounds, Royal 13 and 7, CE 10 and 6.

---

# Apex

## Minor

- **A1 · `build.py:117-118`, slide 3** The At a glance table prints one hex lower case and
  the next upper case: `#2c338e` then `#1D225E`. The palette slide two pages later prints the
  same colour a third way, `#2C338E`. Set `{col['primary'].upper()}` and
  `{col['bandBackground'].upper()}`, and upper-case the hexes inside `colorNote` when it is
  rewritten (`#f9ad16`). Royal has the same defect: slide 3 prints `#572e72` and `#2f193b`
  lower against `#572E72` on slide 6.
- **A2 · `brands.json` apex `colorNote`** The lede ends `Gold is a brand accent, never a
  status color.` The same book renders the heading `Colour.`, the contents rows `Colour` and
  `Colour in use`, and `Never recolour a mark` on slide 5. There is no other American
  spelling in the corpus. Use `status colour`, and hold one locale house-wide including
  `centred` on slide 14, which is already British.

---

# Royal

## Major

- **R1 · `build.py:212-213`, slides 3, 6 and 8** The brand slide bans light purple as text
  on white and the contrast slide five pages later passes it at AA any size. Slide 3:
  `Light purple #8260a2 is for tertiary accents and hover only, never text on white.`
  Slide 6 use string: `Tertiary accents and hover only, never text`. Slide 8 verdict row:
  `Light as text on white · #8260A2 on #FFFFFF · 5.07:1 · AA any size`. The measurement is
  right; the collision is that the row is labelled as a text test for a colour the brand
  reserves. Change the slide 8 label from `Light as text on white` to `Light on white`, and
  make the slide 6 `use` string per brand so Royal reads
  `Tertiary accents and hover. 5.07:1 on white, and still reserved.` The shared string is
  correct for Apex, whose light purple is 2.74:1 and genuinely fails.
- **R2 · `build.py:179-190`, slide 7** The band labelled the spark is invisible against the
  band beside it. Sampled `png/royal-07.png` at y 420: 16% primary `#572E72` against 6%
  accent `#43205B` is 1.28:1. The subhead says "the accent sparks". Royal is the only book
  where the accent band is darker than the primary it is meant to punctuate, because
  `brands.json` gives Royal `accent: #43205B`, which `royal-brand-kit/tokens.json` calls
  "the logo fill", while the accent that kit nominates for brand-coloured text, `#572E72`,
  is already spent on primary. Setting a new accent is the brand owner's call, not the
  fixer's. Until they make it, drop the 6% band for any brand whose accent does not separate
  from its primary rather than print a band nobody can see.
- **R3 · `build.py:162, 209`, slides 6 and 8** One hex carries two names two slides apart.
  Slide 6 swatch: `Deep · #2F193B`. Slide 8 spec: `Accent deep as text on white · #2F193B on
  #FFFFFF · 15.87:1`. `col['accentDeep']` resolves to the same value as `primaryDeep`, and
  slide 6 already suppresses the swatch on that condition while slide 8 does not. Apply the
  same guard at line 209 so Royal shows six rows and no colour has two names.

## Minor

- **R4 · `build.py:206-213`, slide 8** Seven rows carry five distinct measurements, because
  contrast is symmetric and the table prints two pairs in both directions: 15.87, 10.30,
  10.30, 15.87, 13.16, 5.07, 4.02. Apex prints 10.65 twice of seven; CE prints 18.88 twice
  of six. Keep one direction per pair and let the label carry the usage, e.g. a single row
  `Primary and white, either direction`. That frees rows for pairs the book needs and does
  not have, such as body copy on the surface tint, which M6 shows is the case the book gets
  wrong.

---

# Collective Edge

## Blocker

- **C1 · `build.py:146, 151-153`, slide 5** The CE book publishes minimum mark sizes the CE
  kit does not define. `brands.json` gives Apex and Royal
  `minWidth {horizontal: 110px, mark: 32px}`; the `collective-edge` entry has no `minWidth`
  key at all. `mn.get('horizontal', '110px')` and `mn.get('mark', '32px')` then print Apex's
  numbers as CE spec, and `png/ce-05.png` renders
  `horizontal 110px on screen, 1 inch in print · mark 32px`. A brand manual publishing a
  fabricated spec is the one thing it cannot do. Emit the minimum-size clause only when
  `b.get("minWidth")` is present and fall through to the clear-space clause alone for CE, or
  add a real `minWidth` to the `collective-edge` entry in `brands.json` first.
- **C2 · `book.css:170-174`, `build.py:396-399`, slide 15** The drop-in callout prints
  through the running foot. CE's `.ref` carries eight asset rows against Apex's six, so the
  table occupies y 344 to 716 and the callout runs y 756 to 887, 83px past the floor and
  13px from the sheet edge. In `ce.pdf` page 15 the code lines sit at y 621.7 to 633.0pt and
  639.7 to 651.0pt and the foot `COLLECTIVE EDGE / 15` at y 620.1 to 630.6pt: two overlapping
  blocks. Apex and Royal clear this with 24px to spare, so the slide must hold CE's eight
  rows, not Apex's six. The `.ref` row-height fix in M11 takes the table from 344px to about
  224px; also set the `pre` at `build.py:398` to
  `font-size:12px;line-height:1.6;margin:8px 0 0` and the callout padding to `24px 28px`.
  Budget after: 260 table + 40 gap + 111 callout = 411px inside 460.

## Major

- **C3 · `build.py:102-104`, slide 3** The lede and the paragraph directly under it repeat
  three of four clauses, on the first content page of the parent book. Lede: `Collective Edge
  has no hue of its own. It runs on a grey ramp. On a co-brand surface the Edge wedge takes
  the PARTNER's hue.` Paragraph: `Collective Edge is the parent. It has no hue of its own and
  runs on a grey ramp. On a co-brand surface the colour belongs to the partner.` Delete the
  second paragraph for `is_ce` and set the lede to
  `Collective Edge is the parent. It has no hue of its own and runs a grey ramp from #000000
  to #F4F4F4. On a co-brand surface the Edge wedge takes the partner’s colour and Collective
  Edge stays grey.`
- **C4 · `build.py:74`, slide 1** On the cover of the parent brand's own manual the white
  wordmark sits in the bright lobe of the grain. Measured from `png/ce-01.png`, box-blurred
  at radius 12 for local mean luminance, on the bands immediately above and below the mark
  box: at x 112 the ground is 2.35:1 against white, at x 160 it is 3.03:1, at x 208 4.42:1,
  at x 256 6.62:1, at x 304 9.72:1. The block mark and the first letters of COLLECTIVE sit in
  the failing half. The type below is safe and should not be touched: the headline sits on
  ground no lighter than rgb(3,3,3) and the meta line clears 14:1. The overlay gradient runs
  light to dark top to bottom, so the title is protected and the mark is not. Add a matching
  dark stop at the top: `rgba(0,0,0,.70) 0%, rgba(0,0,0,.10) 30%`, then re-measure the same
  bands.
- **C5 · `build.py:179-190`, slide 7** The proportion bar cannot show proportion, on the
  slide whose entire subject is proportion. Sampled `png/ce-07.png` at y 420: 52% surface
  rgb(255,255,255), 26% deep rgb(0,0,0), 16% primary rgb(17,17,17), 6% accent
  rgb(200,200,200). Deep against primary is 1.11:1, so the 26% and 16% bands read as one 42%
  black block and the slide shows three bands, not four. Apex reads 1.37:1 across the same
  seam and Royal 1.54:1, both marginal. Branch on `is_ce` and draw the CE bar from steps of
  the CE grey ramp that separate, for example `#000000`, `#4A4A4A`, `#C8C8C8` on white.
- **C6 · `build.py:161-163`, slide 6** The CE colour slide borrows Apex's accent narrative
  for a brand that ships no accent, so two of its five swatches are labelled wrong.
  `collective-edge-brand-kit/tokens.json` carries `"hasColor": false`. The slide labels
  `#C8C8C8` "Accent · The signature. A highlight, never a large field" where the kit says
  "The Edge wedge when CE stands alone. Never text", and labels `#6E6E6E` "Accent deep · The
  text-safe step of the accent" where the kit says "Tertiary text, metadata". `#C8C8C8` at
  1.67:1 on white is the lowest-contrast colour anywhere in the three books. Branch the
  `pal[]` name and use strings on `is_ce` and take them from each token's own `use` field
  rather than the shared accent copy. The shared Accent string is also wrong for Royal: see
  R2.

## Minor

- **C7 · `collective-edge-brand-kit`, slide 6** The colour slide advertises a surface tint
  the book never paints. The CE Surface chip is `#F4F4F4` (`--ce-paper`, "Off-white surface
  tint"), which is what `brands.json` gives as `surfaceTint`. Every quiet panel in the CE
  book actually renders `#FAFAFA`: 11 text nodes per book resolve their background to
  rgb(250,250,250), because `palette.css` maps `--bg-surface` to `--ce-bone`. Apex prints and
  paints `#F3F3FB`; Royal prints and paints `#FAF5FD`. CE is the only book whose swatch and
  whose panels disagree, and the disagreement is in the kit, not the book. Fix it in the kit
  by pointing `brands.collective-edge.color.surfaceTint` and `--bg-surface` at the same
  value. Do not hard-code around it in `build.py`; the book is correctly printing what the
  registry says.
- **C8 · `brands.json` collective-edge `colorNote`** `PARTNER's` is set in shouting caps
  mid-sentence with a straight apostrophe: `On a co-brand surface the Edge wedge takes the
  PARTNER's hue.` Emphasis by capital letters is the one typographic tell the rest of the
  book avoids, and rule 6 allows uppercase only as a tracked run of four words or fewer.
  Carried by C3, which sets `the partner’s colour` in lower case with U+2019.

---

# Dropped, and why

1. **The audit build's vendored asset links resolve one directory too high** (3 reports,
   graded blocker). Already applied and verified in this capture: `_audit/html/apex.html:4`
   reads `../assets/collective-edge-brand-kit/snippets/type-system.css`, and the cover h1
   in `geom/apex.json` reports Montserrat at 72px weight 700 with line-height 77.76px. The
   preventive half of that report survives as m18.
2. **`cdp.py` measured at Chrome's default viewport** (2 reports, graded blocker). Already
   applied and verified: `cdp.py:35` and `:72` carry `--window-size=1600,900` and
   `Emulation.setDeviceMetricsOverride(1600, 900)`, and the ladder resolves at the top of
   its clamps.
3. **"Rule 11 is inverted in the slide head: 14px above the heading, 18px below, so set the
   eyebrow margin to 48px."** Misapplication. The eyebrow is a label bound to the heading,
   not preceding content; opening 48px above it would break the group the rule exists to
   protect. The 14 and the 18 survive only as off-grid values under M9.
4. **"Section headings float: 96px above, 89px below, ratio 1.08."** The 96px is the page's
   top margin, not heading space. What is really wrong on those slides is that the rule sits
   48px below the head and 40px above the body, binding to neither. Reframed as M1.
5. **"Add per-initial optical insets to the slide headings: −3px for M, W, V, A, D and −1px
   for C, O, G, Q, S."** Measured ink offsets from x 112 across the content headings are
   T 112, C 114, M 115, against an eyebrow at 113. A 2 to 3px wobble at 40px does not earn a
   per-letter table inside a generator, which would be more fragile than the defect. The
   cover's 5px step is real and survives as p1.
6. **"The banned-weight rows cannot render their claim, so cut them."** The clamp is exactly
   what the slide's subhead promises, and the rows demonstrate it. What is actually wrong is
   that the label says `Thin` beside a sample rendering at 400 without saying so, and that
   `font-weight: 200` and `900` in the source fail validator R2. Both are handled in B2 and
   M3.
7. **Two incompatible chip heights for slide 6** (240px in one report, 244px in another).
   Merged into B4 with the arithmetic recomputed against the current capture: the Apex info
   block needs 218px, so the chip may be at most 241px.
8. **"The contents loses two of its fifteen entries."** The contents has thirteen entries.
   The defect is real and is B3; the count in that report is not.
9. **"Change `brands.collective-edge.color.surfaceTint` to `#FAFAFA`."** Asserted in the
   wrong place and in one direction only. The book faithfully prints the registry; the kit
   disagrees with itself. Kept as C7 with the fix scoped to the kit and the direction left
   open.
10. **"Set a new Royal accent in `brands.json`."** A brand owner's decision, not a fixer's.
    Kept as R2 with the fix scoped to `build.py`.
11. **"Seven sites need a non-breaking space."** Three of the seven, the `min` values on
    slide 13, are inside `.bk-code`, which already sets `white-space: nowrap`. Four real
    sites, corrected in m14.
12. **"Seven straight apostrophes against rule 14."** The rendered corpus carries two in
    prose per book and three in CE; the rest are inside the slide 15 code specimen, where
    straight quotes are correct. Corrected in m15 and M3.
13. **"Slide 9: remove `height: 100%` from the `s-body` children."** No such declaration
    exists. The columns measure 498px because their content does, inside a 460px body.
    Restated correctly in M11.
14. **"Slide 5 stops 142px above the content floor."** Measured 107px in this capture: the
    caption bottoms at y 697. Kept as p4 with the right number.
15. **"`.pair .cap` is 11px."** There is no `.pair .cap`. The rule is `.pair .spec`, and it
    is covered by B8.
