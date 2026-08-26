# Handoff

Everything needed to pick this up on another machine. Written 2026-08-25.

Paste this file to Claude Code on the new machine and it will have the full
picture. Nothing here depends on the session it was written in.

---

## 1. What exists

A design system for three brands, in four public repositories under the
`collective-edge` GitHub organisation.

| Repository | Tag | What it holds |
|---|---|---|
| `collective-edge-brand-kit` | `v1.3` | The parent. Type system, UI layer, layout auditor, brand registry. |
| `apex-brand-kit` | `v1.3` | Apex Paramedics palette, logos, references. |
| `royal-brand-kit` | `v1.3` | Royal Ambulance palette, logos, references. |
| `brand-books` | main | The generator for the three printed manuals. |

**The architecture.** Apex and Royal are operating companies under Collective
Edge. Exactly two things vary between the brands: palette and logo. Seven files
are byte-identical across all three kits and `scripts/check-sync.py` fails if
they ever drift. Change a shared file once, copy it to the other two.

Anything can use the system with two link tags, no clone required:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/collective-edge/collective-edge-brand-kit@v1.3/snippets/type-system.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/collective-edge/apex-brand-kit@v1.3/snippets/palette.css">
```

---

## 2. Set up the new machine

Clone all four into one directory. The tools assume they are siblings.

```bash
mkdir -p ~/collective-edge && cd ~/collective-edge
git clone https://github.com/collective-edge/collective-edge-brand-kit.git
git clone https://github.com/collective-edge/apex-brand-kit.git
git clone https://github.com/collective-edge/royal-brand-kit.git
git clone https://github.com/collective-edge/brand-books.git
```

Dependencies. Python 3.9 or later, and Google Chrome at the standard macOS path.

```bash
pip3 install Pillow websocket-client fonttools
```

`Pillow` crops rendered slides. `websocket-client` drives Chrome over its debug
protocol, which is required because Chrome's `--print-to-pdf` flag ignores the
CSS page size and forces US Letter portrait. `fonttools` measures the typeface.

Confirm it works:

```bash
cd ~/collective-edge/collective-edge-brand-kit
python3 scripts/check-sync.py          # expect PASS
python3 scripts/ui-audit.py --list-checks
```

---

## 3. Run the books

```bash
cd ~/collective-edge/brand-books
python3 serve.py                        # http://localhost:8090
```

Open a book and use **Save as PDF**. Seventeen pages per brand, landscape,
one slide per page. The server rebuilds on every page load, so editing
`build.py` or `book.css` shows up on refresh.

To regenerate the audit artefacts, roughly ninety seconds:

```bash
python3 build.py && python3 harness.py && python3 cdp.py
```

That writes `_audit/`, which is gitignored and reaches about 2GB:

- `png/<book>-NN.png` every slide at 1600 × 900
- `geom/<book>.json` every text node with box, font, size, weight, leading,
  tracking, measure, colour, resolved background, computed contrast, overflow
- `pdf/<book>.pdf` the print output

---

## 4. The two gates

Run both before shipping anything.

```bash
# from inside any kit
python3 scripts/check-sync.py                    # shared layer has not drifted
python3 scripts/validate.py path/to/page.html    # the fifteen type rules
python3 scripts/ui-audit.py http://localhost:4321   # what a person sees
```

`ui-audit.py` renders at 375, 768 and 1440 and reports twenty checks: text on
text, a graphic over type, a rule through a letterform, spacing off the 4px
grid, contrast below AA, targets under 44px, measure over 75 characters, type
off the ladder. It exits non-zero on an error, so it can gate a build.

It ships with its own regression test. `Examples/_audit-fixture.html` plants one
of every fault, each labelled with the check it must trip. It catches 14 of 14.
If a change to the auditor drops that number, the auditor has gone blind.

---

## 5. The standard

`reference/type-system.md` in any kit. Section 10 is the fifteen rules. The
short version:

- Montserrat only. **No italic at any weight, anywhere.**
- Four weights: 400 body, 600 subheads and caps labels, 700 headings and
  emphasis, 800 hero. The `@font-face` clamps the axis to 400–800, so a banned
  weight renders at the nearest permitted one rather than silently shipping Thin.
- Tracking in `em`, never `px`. Uppercase always tracked, never past four words.
- Body measure `54ch`, which is 70 real characters. Montserrat is 16.7% wider
  than Helvetica, so `1ch` buys 1.302 characters.
- Flush left, ragged right. Never justified.
- On a dark ground, add `0.005em` tracking at every step and drop one weight at
  700 and heavier. 600 is the floor.
- The mono face is a whitelist of four: colour values, paths and filenames, code
  shown as code, and record identifiers a person dictates. Everything else,
  including measurements, ratios, counts and ordinals, is Montserrat with
  tabular figures.

**Measure the font at weight 400.** Montserrat's variable default instance is
weight 100, and measuring there describes Thin rather than the Regular that
actually sets body copy. That mistake was made once and corrected.

---

## 6. The Collective Edge brand manual

Built 2026-08-25. Twenty-eight pages, US Letter landscape, 11 × 8.5in. It lives in
`brand-books/` as `ce-manual.py`, `ce-manual.css` and `ce-manual.html`, and it is
deliberately not part of `build.py`: different reader, different format, its own
generator.

```bash
cd brand-books && python3 serve.py      # the manual is the first card
```

Print with **background graphics on and margins none**. Both matter and neither is
recoverable after the fact.

**The rule it holds.** No CDN paths, no file names, no class names, no scripts, no
repository names, no version tags, anywhere a reader can see. `guard()` in the
generator greps the rendered text for those and for straight quotes and em dashes,
and refuses to write the file. It has caught real ones.

**The design, in one line.** The bar inside the lockup, at 21.2% of the drawn width,
enlarged to a spine at x 294 that runs down every interior page. Label to its left,
statement to its right. It never touches the head rule, which starts at x 306.

**What is read rather than typed.** The palette and its use strings, from the kit's
tokens. Every contrast ratio, computed. Every proportion of the mark, measured off
the drawn SVG by `art_geometry()`. That last one matters: the signature bar is a
stroked line inside a transform, not a filled path, and reading the clip boxes
instead of the drawing put the wedge at the wrong end of the lockup on the first
build.

**Where the numbers cross-check.** The measured artwork gives the wedge as the right
43.1% of the block and clear space as 8.84% of the lockup width, 0.18in at a 2in
lockup. Those were derived independently while the copy was being written and they
agree, which is the only reason to trust either.

**State on the sheet.** Twenty-eight pages, smallest type 9pt with nothing under it,
every size in the PDF a step on the ladder except the 180pt metric specimen, which is
declared artwork. Clean on all seven of `validate.py`'s mechanical rules.

**Audited 2026-08-26.** Fourteen agents swept all 28 rendered pages, three lenses ran across
the whole book, and skeptics refused anything they could not see themselves. 111 findings
survived. The ones worth recording as classes rather than instances: an absolutely positioned
specimen leaves the flow and the prose runs underneath it; a fixed row height plus a string
that wraps sets text on text; `line-height: 1` inside a 1.219em natural line box drops a glyph
26px away from the rules measuring it; and `table-layout: fixed` takes its column widths from
the first row, so a header cell that disagrees with its body cell widens the whole table.

Three of the audit's own top recommendations were wrong, and they were wrong because the brief
given to the auditors omitted the reversed-text palette and rule 13. They would have pulled
`#D6D6D6` and `#9E9E9E` out of the book, moved the on-dark tertiary to a value the standard
says is never text, taken colour values out of the mono face the standard puts them in, and
re-cut a shipped logo the kit says never to recolour. Check an audit's premises against the
kit before executing it.

**One thing left open.** `reference/brand.md` still lists "Not this. This." as a CE
voice pattern and `reference/layout.md` still ships it as a layout pattern. The
manual does not use it, does not name it and does not demonstrate it, on Jacob's
explicit instruction. The kit and the manual disagree, and the kit is the one that
should move.

## 7. Deliberately not done

**The websites still carry their own tokens.** 382 CSS variables across four
projects where about 95 would do, and only one file in the estate loads the kit.
Applying the guides to the sites is its own project, to be started once the
guides are excellent. Nothing in this system has modified a website repository.

The research found what is waiting there: six separate button implementations,
touch targets at 34, 36, 40, 44 and 48px, corner radii at 6, 8, 10, 12 and
999px, three different buttons inside one stylesheet, and one project with no
focus ring at all that also switches off the browser default in two places.

`ui-audit.py` reads a page and reports. It never edits. It is ready to point at
any of them.

**Two open questions, both small.** `assets/imagery/CE_Coach.png` and
`CE_Coach Medium.png` are 3MB together and referenced by nothing. And no person
has read the three brand books end to end; every number in them is verified, but
whether they are right is a judgement rather than a measurement. The same is now
true of the manual, with one difference: every one of its twenty-eight pages has
been looked at as a rendered image, and six defects were found that way that no
check caught.

---

## 8. Two things worth knowing

**Tags never move.** `v1.0`, `v1.1`, `v1.2` and `v1.3` are frozen. New work gets
a new number. A tag that moves defeats the reason anyone pins to one.

**The tooling proves consistency, not correctness.** The two best catches in this
project came from a person looking at output: the monospace face spreading past
its rule, spotted by eye, and the first page of a PDF printing cut off, found by
exporting one. The auditor renders in screen media and the capture harness
strips the toolbar before it renders, so neither could see either defect. Run the
checks, then look at the thing.
