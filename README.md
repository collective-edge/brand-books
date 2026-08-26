# Brand books

Two things live here. Three internal brand books, one per brand, and the outward-facing
Collective Edge brand manual.

|  | Reader | Format |
|---|---|---|
| `apex.html` `royal.html` `ce.html` | Whoever is building with the kit | 17 slides, 16.68 × 9.38in |
| `ce-manual.html` | A partner, a hospital marketing lead, a senior hire | 28 pages, US Letter landscape |

The books are spec sheets. The manual is not: it never names a file, a class, a script, a
repository or a version tag, because its reader will never check the repository out. That rule
is enforced in the generator and the build fails on a violation.

The books are generated, not hand-written. `build.py` reads the published brand kits and emits
one HTML deck per brand. Change a token in a kit, rebuild, and the book follows. That is the
point: a manual that cannot drift from the system it documents.

## Run it

```bash
python3 serve.py          # http://localhost:8090
```

The index lists the manual first and the three books under it. Every generator reruns on each
page load, so an edit to `build.py`, `ce-manual.py` or either stylesheet shows up on refresh.

Open a book and use **Save as PDF** for a 17-page landscape file at 16.68 × 9.38in, one slide
per page. The server rebuilds on every page load, so an edit to `build.py` or `book.css` shows
up on refresh.

Nothing needs installing to view them. The audit harness below needs `Pillow` and
`websocket-client`.

## What is here

| File | What it does |
|---|---|
| `build.py` | Generates `apex.html`, `royal.html`, `ce.html` from the kits |
| `book.css` | Slide geometry and deck chrome. Owns no type and no colour. |
| `ce-manual.py` | Generates `ce-manual.html`, the outward-facing manual. Its own generator by design |
| `ce-manual.css` | Sheet geometry and page chrome for the manual. Owns no type and no colour |
| `capture.py` | Renders every page to PNG, checks overlap, floor, margins and contrast, writes the PDF |
| `serve.py` | Local server with an index, rebuilds on load |
| `harness.py` | Vendors kit assets offline, renders 48 slide PNGs |
| `cdp.py` | Drives headless Chrome over CDP for real geometry and real PDFs |
| `AUDIT-DOCKET.md` | The 69 findings from the audit that shaped these books |
| `COBRAND-SPEC.md` | The shipped "Powered by Collective Edge" pattern |

The generated HTML is gitignored. It is output, not source.

## Where the design comes from

The books load the type system and each brand's palette straight from the CDN:

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/collective-edge/collective-edge-brand-kit@v1.1/snippets/type-system.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/collective-edge/apex-brand-kit@v1.1/snippets/palette.css">
```

So the books are a live test of the house system rather than a picture of it. One type layer,
identical everywhere; palette and logo swapped per brand.

Sources of truth, all public:

- [collective-edge-brand-kit](https://github.com/collective-edge/collective-edge-brand-kit)
- [apex-brand-kit](https://github.com/collective-edge/apex-brand-kit)
- [royal-brand-kit](https://github.com/collective-edge/royal-brand-kit)

The standard the books follow is `reference/type-system.md` in any kit. Section 10 is the fifteen
rules. Every book must hold them more strictly than anything else does, because a manual that
breaks its own rules is not a manual.

## Auditing a change

```bash
python3 build.py && python3 harness.py && python3 cdp.py
```

That writes to `_audit/`, which is gitignored and can run to a couple of gigabytes:

- `png/<book>-NN.png` every slide at 1600 × 900
- `geom/<book>.json` every text node with box, font, size, weight, leading, tracking, measure,
  colour, resolved background, computed contrast and overflow flags
- `pdf/<book>.pdf` the real print output

Check any generated page against the house gate before shipping it:

```bash
python3 ../collective-edge-brand-kit/scripts/validate.py apex.html
```

Two things the harness learned the hard way, both recorded in the code:

Chrome ignores `@page` in pixels and its `--print-to-pdf` flag forces US Letter, so the PDF is
produced through CDP with explicit dimensions. And a print size must be measured in print media,
never derived by scaling a screen measurement, because a `@media print` rule does not exist in
the screen context.

## Adding a brand

Add the brand to `brands.json` in the kits first, following `NEW-BRAND.md`. The books read the
registry, so a fourth brand appears once its entry and its palette exist. Nothing here is
hard-coded per brand except the swatch captions, which are sourced from each kit's own tokens.


## The manual

`ce-manual.py` writes one self-contained file. US Letter landscape, 11 × 8.5in, which at 96
pixels to the inch is 1056 × 816 exactly, so one point is 4/3 of a pixel, every ladder step
lands on a whole pixel, and a specimen set at 96px measures an inch on paper. The manual says
so on its own scale page, which is the only reason the claim is worth making.

Print it with **background graphics on and margins set to none**. Every dark ground, every
full-bleed chip and every band depends on the first, and the sheet size depends on the second.

**The design.** The lockup carries one piece of drawn geometry that is not a letter: the bar
between the block and the name, 21.2% into the drawn width. Enlarged to page scale it is the
spine at x 294 that runs down every interior page, label to its left and statement to its
right. It never crosses the head rule, which starts 12px away at x 306, so the two systems are
visibly held apart rather than allowed to form a crosshair. Five black versos hinge the book
into parts. Because every display line in the manual stands on black, where the ladder drops
display from 800 to 700, the whole book runs on three weights and never sets 800 outside the
one labelled specimen on the weights page.

**Nothing measurable is typed.** The palette and its use strings come from the kit's tokens.
Every contrast ratio is computed. Every proportion of the mark is read out of the drawn SVG,
including the signature bar, which is a stroked line inside a transform rather than a filled
path. Reading the clip boxes instead of the drawing is what once put the wedge at the wrong end
of the lockup.

**Two gates it passes.** `validate.py` from the kit, clean on all seven mechanical rules. And
the printed PDF: 28 pages at 11 × 8.5in, smallest type exactly 9pt with nothing under it, every
size in the file a step on the ladder except the 180pt metric specimen, which is artwork.

**What the gates cannot see.** Every real defect in this book was found by rendering the pages
and looking at them. The validator passed a page with two paragraphs set underneath a logo, a
claim in near-black on a black ground, an anatomy callout pointing at the wrong end of the mark,
and a specimen sitting 26px above the metric rules that claimed to measure it. A capture harness
worth having therefore checks four things the type rules do not: text or images overlapping,
anything closing below the field floor, anything past the live margins, and every page's head
block starting on the same horizon. Run it, then look at the thing.
