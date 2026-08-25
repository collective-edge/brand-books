# Resume the Collective Edge brand manual

Stopped mid-run on 2026-08-25. Nothing was lost: the run had completed its
research and planning agents but had not written a single file.

## To restart

Say to Claude Code, in this project directory:

    build the CE manual

That is enough. Everything it needs is on disk. If you want it to pick up the
exact cached research rather than redo it, say instead:

    resume the CE manual workflow

and it will replay the finished agents from cache and continue from the plan.

## What it is building

A full Collective Edge brand manual. Print-ready PDF, US Letter landscape,
11 x 8.5in, roughly 20 to 26 pages. Semi-public facing: written for a partner,
a prospective hire, or someone who followed "Powered by Collective Edge" out of
a footer. Deliberately separate from the three internal brand books, which are
spec sheets for people building with the kit.

The governing rule: no CDN paths, no file names, no class names, no scripts, no
repo references. If a sentence only makes sense with the repository checked out,
it does not belong in the document.

Output lands in `brand-books/` as `ce-manual.py`, `ce-manual.css` and
`ce-manual.html`.

## State when it stopped

All four repositories clean, pushed, and in sync with GitHub.

    apex-brand-kit               v1.3
    royal-brand-kit              v1.3
    collective-edge-brand-kit    v1.3
    brand-books                  main

Nothing is uncommitted. Nothing is half-written.

## Worth doing whenever you have two minutes

    cd brand-books && python3 serve.py

Open a book at localhost:8090 and use Save as PDF. Seventeen pages per brand.
No person has read them end to end, and every number in them is verified but
whether they are right is a judgement, not a measurement.
