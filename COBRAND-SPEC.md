# Powered by Collective Edge

Captured from the three places it already ships, so the brand kits document what
is real rather than what someone reinvented. Do not paraphrase these values.

## Where it already lives

| Surface | File | Placement |
|---|---|---|
| Apex website footer | `apex-website/src/components/Footer.astro:53` | Under the Apex mark, hairline above |
| Apex internal dashboard | `web-apex-internal-dashboard/src/components/Sidebar.astro:38` | Sidebar header, directly under the Apex mark |
| Apex customer dashboard | `apex-customer-dashboard/src/components/Sidebar.astro:68` | Sidebar header, text only, no lockup |
| Apex partner page | `apex-website/src/pages/partner.astro:436` | Section-level lockup |

## The model, in the words already in the code

Two comments say the same thing, and that sentence is the rule:

> the CE lockup rides beside the partner brand, never inside it, so a hairline
> keeps the two marks distinct

> the two read as two brands rather than one combined mark

And on size:

> sized to read at a glance rather than sit quietly in a corner, which is why it
> runs wider than the partner mark above it

## The lockup

```html
<div class="ce-powered">
  <span>Powered by</span>
  <img src="{CE_CDN}assets/logos/horizontal-white.svg"
       alt="CE | Collective Edge" width="204">
</div>
```

```css
.ce-powered {
  display: grid;
  gap: var(--space-3);
  margin-top: var(--space-5);
  padding-top: var(--space-5);
  border-top: 1px solid var(--border-on-dark);
}
.ce-powered span {
  font-size: var(--fs-caption);
  font-weight: var(--weight-semibold);
  letter-spacing: var(--tr-caps-small);
  text-transform: uppercase;
  color: var(--fg-on-dark-3);
}
.ce-powered img { width: 204px; max-width: 100%; display: block; }
```

**204px** is the shipped width in both the website footer and the dashboard
sidebar. It is deliberate and it is wider than the partner mark above it. The CE
kit's own 120px minimum is a floor, not a target.

The label sits at caption size in the dashboard and 13px in the website footer,
where a comment notes it is the one caps label that is not micro, so it takes the
standard tracking step rather than the wide one.

Colour of the label is the tertiary foreground of the surface it sits on:
`--fg-on-dark-3` on the dashboard, `--apex-blue-light` in the Apex footer.

## Text-only variant

Where no lockup fits, the customer dashboard sets the phrase as type:

```css
font-size: 9px; font-weight: 700; letter-spacing: 0.16em;
text-transform: uppercase; color: var(--fg-4);
```

Under house type system v1.0 that becomes `.bk-eyebrow`, which is 12px at weight
600 with 0.08em tracking. 9px is below the 9pt print floor and 700 is heavier
than the caps-label step. Use the class.

## The easter egg

`web-apex-internal-dashboard` closes every page with:

> Powered by Collective Edge Sweat

Set faint, caption size, 0.75 opacity. It is italic in the current CSS, which the
type system now forbids at any weight. Keep the line, drop the italic, carry the
tone with colour and size instead.

## Where it belongs, and where it does not

Put it where a partner surface is doing something a reader might wonder about:
the footer of any site, the sidebar of any dashboard, the back cover of a deck,
the foot of a report, a data or methodology page, anywhere a number was computed
rather than typed.

Do not put it on the partner's own mark, inside their lockup, on a clinical
instruction, on a patient-facing consent or safety document, or twice on one
surface.

## What the brand books need

Each of the three books gains a co-brand section:

- **Apex and Royal** get one showing the lockup on their own dark band at 204px
  with the hairline, the text-only fallback, the placement rules above, and the
  reason: an operating company is powered by Collective Edge and the reader
  should be able to see it.
- **Collective Edge** already documents the model in `reference/brand.md`. Its
  book gains the shipped pattern and the two real examples, so the parent book
  shows what the partners are asked to do.

The Collective Edge kit's `SKILL.md` and `reference/brand.md` already carry the
"Powered by Collective Edge" model. This spec is the shipped implementation of
it, and the two should agree.
