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

## 6. Unfinished: the Collective Edge brand manual

This is the work in flight. It was stopped cleanly before it wrote any files.

**To restart, in `~/collective-edge`:**

```
build the CE manual
```

**What it is.** A full Collective Edge brand manual. Print-ready PDF, US Letter
landscape, 11 × 8.5in, 1056 × 816px, roughly 20 to 26 pages.

**Who it is for.** Semi-public. A partner considering working with Collective
Edge, a hospital system's marketing lead, a senior hire, someone who followed
"Powered by Collective Edge" out of a footer. Not employees, and they will never
run a script.

**The one rule that governs it.** No CDN URLs, no file paths, no class names, no
script names, no repository names, no version tags. If a sentence only makes
sense to someone with the repository checked out, it does not belong in the
document. That is the difference between a brand manual and internal
documentation.

**Deliberately separate** from the three internal brand books, which are spec
sheets for people building with the kit. Different reader, different document,
different format. Do not extend `build.py`; build it as its own generator.

**Output** goes to `brand-books/` as `ce-manual.py`, `ce-manual.css` and
`ce-manual.html`.

**Source material**, all in `collective-edge-brand-kit`:

- `reference/brand.md` the brand thesis, colour, the Edge wedge, the co-brand
  model, and a voice section that is the best writing in the estate. The manual
  should be written **in** CE's rhetorical patterns, "Not this. This." and
  bold-then-explain, rather than describing them.
- `reference/type-system.md` the type standard the manual must itself obey.
- `assets/logos/` the marks. `assets/imagery/` the grain wave.

**Two format notes that cost time to learn.** Declare `@page` size in inches,
because a px page size is ignored and the sheet falls back to portrait Letter.
Put any toolbar clearance inside `@media screen`; unscoped, it leaks into print
and pushes the first page off the sheet.

---

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
whether they are right is a judgement rather than a measurement.

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
