# Resume

Nothing is in flight. The Collective Edge brand manual, which this file used to
describe as unfinished, was built on 2026-08-25.

## What is here

```bash
python3 serve.py          # http://localhost:8090
```

Four documents. The Collective Edge brand manual, twenty-eight pages of US Letter
landscape written for a partner or a senior hire, and the three internal brand books,
seventeen slides each, written for whoever is building with the kit.

Print either with background graphics on and margins set to none.

## The two gates, before shipping anything

```bash
python3 ../collective-edge-brand-kit/scripts/check-sync.py            # expect PASS
python3 ../collective-edge-brand-kit/scripts/validate.py ce-manual.html
```

Both are clean as of the last build. `validate.py` checks the seven mechanical rules
and cannot check the other eight, so run it and then look at the thing. Every real
defect found in the manual came from looking at a rendered page: text set over text,
a claim in near-black on a black ground, an anatomy callout pointing at the wrong end
of the mark, a column that ran under the folio.

## Worth doing whenever you have twenty minutes

Read the manual end to end. Every number in it is verified and every page has been
looked at, but whether the whole reads as one object is a judgement, and no script
has an opinion about it.
