# Brand books

One print-ready brand manual per brand: Apex Paramedics, Royal Ambulance, Collective Edge.

The books are generated, not hand-written. `build.py` reads the published brand kits and emits
one HTML deck per brand. Change a token in a kit, rebuild, and the book follows. That is the
point: a manual that cannot drift from the system it documents.

## Run it

```bash
python3 serve.py          # http://localhost:8090
```

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
