# Sector coverage: design and build guide

LederCap / analyst research / v1.0 / 2026-11-02

Build an original, readable sector webpage that belongs beside LederCap's research tools. The analyst chooses the display format: narrative, value-chain map, company cards, comparison table, or a mix. This is a design and handoff contract, not a finished page or a requirement to build a dashboard.

## Start here

1. Choose **robotics or space**. Keep the other folder untouched until that choice is confirmed.
2. Map the sector's business models and supply chain. Start with **5-10 US public companies**; distinguish direct exposure from adjacent businesses.
3. Show where the largest revenue pools overlap with the fastest growth. Explain scope, period, method and uncertainty rather than ranking on unsourced estimates.
4. Build a first webpage for review. Then narrow to **2-3 companies** for deeper coverage. Reuse the toolkit as questions arise; more data infrastructure is not a prerequisite.
5. Deliver source, data and a local preview for website integration. Do not deploy the page or change the main website from this repo.

Read this guide together with [sector structure](README.md), [the toolkit](../quanttk/README.md) and [contributing](../CONTRIBUTING.md).

## 1. Brand: what stays fixed

The visual family is LederCap's dark **Holo-Matrix**: near-black ground, restrained mint, clear white text, mono labels, thin rules and quiet instrument-like framing. Research comes first. No neon wall, giant logo, flashing terminal, decorative stock-price feed or faux-live data.

### Source-grounded palette

These values were checked against the live [ledercap.com](https://ledercap.com/) stylesheet on 2026-11-02. The website's Tailwind configuration names the core colors `void`, `mint`, `signal` and `glass`; the working surfaces use `--desk-*` tokens. The homepage can use pure black, while panels use near-black. The website also has a separate paper-style blog; this guide deliberately follows the dark research/infographic family, not that editorial variation.

| Role | Value | Use |
| --- | --- | --- |
| Midnight Void | `#000505` | Main page ground |
| Neural Mint | `#00FFC3` | Links, active state, one focal series or finding |
| Pure Signal | `#FFFFFF` | Titles and high-contrast text |
| Research text | `#e8efed` | Long-form text on the dark ground |
| Research value | `#cdd8d5` | Numeric values and secondary content |
| Neutral metadata | `#b0b3b2` | Readable dates, units and sources |
| Holo-Glass | `rgba(0,255,195,.05)` | Light tint over near-black, not an opaque mint fill |
| Panel | `rgba(0,22,20,.55)` | Research cards |
| Raised panel | `rgba(0,30,27,.7)` | Headers and controls |
| Quiet rule | `rgba(120,150,146,.18)` | Dividers; not a substitute for readable labels |
| Strong rule | `rgba(120,150,146,.32)` | Table groups and panel boundaries |
| Negative / error | `#FF6B6B` | Negative values or actual problems, with a text label |
| Caution | `#f5b843` | Incomplete, estimated or unresolved, with a text label |

Mint is an accent, not a claim that an investment is attractive. Never encode meaning in color alone. The site's faint desk-label colors suit dense instruments but are not a target for small body copy: increase contrast for this public research page. Normal text should meet WCAG AA 4.5:1; large text 3:1. Check the rendered foreground/background combination, including transparency.

### Typography and rhythm

- Use `'JetBrains Mono', 'Fira Code', ui-monospace, monospace` for headings, labels, figures and the compact research-page voice. The live site loads JetBrains Mono weights 300, 400 and 500. Use 400 for readable body copy and 500 for emphasis. A system-sans body is acceptable for long essays if hierarchy remains consistent.
- Suggested page scale, not copied from the dense trading desk: body 16px / 1.6; metadata 12-14px; section titles 22-28px; page title `clamp(28px, 5vw, 48px)`.
- Use tabular numerals for aligned figures. Right-align numbers, left-align names and prose. Put units in headings or beside values.
- Use a 4px spacing rhythm, usually 16-24px inside cards and 24-48px between sections. Aim for 60-75 characters per prose line.
- Use uppercase, letter-spaced text only for short labels. Do not set paragraphs in uppercase or ultra-light text.

### Framing, marks and motion

Thin 1px rules, mostly square corners (2-4px radius), optional faint 24px grid and restrained HUD corner marks. Keep decoration behind content and non-interactive. No essential text over a busy grid; avoid glow on paragraph text. Use one quiet `LEDERCAP_` footer or a small Lederle Capital text link. Do not redraw the official logo or copy private website assets into this public repo. The final website can supply its existing approved mark.

No animation is required. If used, honor `prefers-reduced-motion`, avoid flashing and autoplay, and never require hover to read research.

## 2. Research content contract

Choose the presentation, but make these questions easy to answer:

| Reader question | Minimum content |
| --- | --- |
| What is covered? | Sector, subsegments, geographic/listing scope, as-of date and limitations |
| Where does value accrue? | Value chain, customer, product, revenue model, bottlenecks and suppliers |
| How large and how fast? | Revenue-pool definition, base year, forecast period, source and method; do not add overlapping markets |
| Who is exposed? | 5-10 US public companies with legal name, ticker, exchange, segment, direct/adjacent exposure and why included |
| What changes the outcome? | Drivers, constraints, risks, milestones and open questions |
| Where do we go deeper? | A reasoned shortlist of 2-3 companies, not a buy/sell recommendation |
| Can I verify it? | Source links, filing/report dates, calculations and clearly marked estimates |

Private and international firms may appear as clearly separated context, suppliers or competitors, not as the core investable universe. Verify current public/listing status before inclusion. Do not assume an S-1, a ticker, an IPO, a project announcement or a contract exists because it appeared in notes. For US-listed foreign issuers or ADRs, label domicile/listing explicitly and confirm scope before treating them as core US companies.

For robotics, possible lenses include industrial automation, humanoids and components. For space, possible lenses include launch, satellites, ground infrastructure and suppliers. These are organizing ideas, not a selected sector or asserted market facts. Separate speculative markets from established revenue.

### Source and calculation rules

- Prefer SEC filings, company investor relations and relevant official industry sources. Use secondary research for context with attribution, dates and uncertainty.
- Each material number needs a nearby citation or source ID linked to a source register. Capture source URL, document title, publication/filing date, observation period, access date and page/section when available.
- Label reported, calculated and estimated values. Store formulas, inputs, units, fiscal/calendar basis and adjustments. Link toolkit calculations to the relevant workflow or function and commit where reproducibility matters.
- Distinguish company-wide revenue from sector revenue, backlog from revenue, bookings from sales, enterprise value from market cap, and nominal values from inflation-adjusted values.
- Missing is `Not available`, not zero. Explain inconsistencies and unresolved discrepancies. Manual filing checks beat a second AI-generated answer.
- Avoid unsupported precision and unexplained scores. A chart needs a title, units, date range, legend, source and textual takeaway. Comparable charts need comparable scales.
- Do not reproduce licensed data, unapproved logos/images, personal information, internal discussion or private website code. Use linked primary sources and original analysis.

## 3. Page structure: flexible, not mandatory wireframes

A useful default is:

1. **Title band:** sector, one-sentence thesis/question, byline placeholder, as-of date, jump links.
2. **Sector map:** value chain plus the revenue/growth lens, with a short explanation.
3. **Company universe:** cards on phones, a comparison table or richer map on wider screens.
4. **Analysis:** drivers, constraints, risks and a few sourced charts.
5. **Next coverage:** 2-3 deeper candidates with reasons and unanswered questions.
6. **Sources and method:** linked register, calculation notes, limitations and update history.

Change the order or format if it tells the story better. Do not fill every slot with a chart merely to complete a template. For the eventual public portfolio page, reserve a byline for the analyst; final name and publication metadata are reviewed with the page rather than added to this general guide.

### Responsive and accessible behavior

- Start with one column at 320px and 390px, 16px side padding, no page-level horizontal scrolling. Use a readable max-width around 1100-1200px on desktop.
- Stack cards and label/value pairs on phones. If a comparison table is essential, provide a readable per-company mobile view from the same data. Horizontal scrolling is acceptable only for supplemental detail with an obvious affordance.
- Use real headings, lists, links, buttons and table headers. One `h1`; a meaningful title, description and language. Provide a skip link and visible keyboard focus. Touch controls should be at least 44px tall.
- Filters/sorts must work by keyboard and expose their current state. Charts need a text summary and accessible data; images need useful alt text. Never put analysis only in an image.
- Check 200% zoom, narrow screens, long company names, long source URLs, missing values, empty filters and reduced motion. Avoid fixed heights that clip prose.
- Make the core research readable without JavaScript. No client-side secrets, account access or new backend is needed for a static first version.

## 4. Small starter CSS, not a framework requirement

Namespace the page under `.lc-sector` and prefix components `lc-sector-` to prevent collisions with the host site. This is an original starter based on the public palette, not a copy of the website's private stylesheet. It deliberately uses larger text than the trading desk.

```css
.lc-sector {
  --lc-bg: #000505;
  --lc-text: #e8efed;
  --lc-meta: #b0b3b2;
  --lc-mint: #00ffc3;
  --lc-negative: #ff6b6b;
  --lc-warning: #f5b843;
  --lc-line: rgba(120, 150, 146, .32);
  color: var(--lc-text);
  background: var(--lc-bg);
  font: 400 16px/1.6 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  font-variant-numeric: tabular-nums;
}
.lc-sector *, .lc-sector *::before, .lc-sector *::after { box-sizing: border-box; }
.lc-sector-inner { width: min(100% - 32px, 1160px); margin-inline: auto; padding-block: 32px; }
.lc-sector h1 { font-size: clamp(28px, 5vw, 48px); line-height: 1.15; font-weight: 500; }
.lc-sector h2 { font-size: 24px; line-height: 1.3; font-weight: 500; }
.lc-sector p { max-width: 72ch; }
.lc-sector a { color: var(--lc-mint); text-decoration: underline; text-underline-offset: .2em; overflow-wrap: anywhere; }
.lc-sector :focus-visible { outline: 2px solid var(--lc-mint); outline-offset: 4px; }
.lc-sector-grid { display: grid; gap: 16px; }
.lc-sector-card { min-width: 0; padding: 24px; border: 1px solid var(--lc-line); border-radius: 3px; background: rgba(0, 22, 20, .55); }
.lc-sector-meta { color: var(--lc-meta); font-size: 13px; }
.lc-sector img, .lc-sector svg { max-width: 100%; height: auto; }
@media (min-width: 800px) { .lc-sector-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (prefers-reduced-motion: reduce) { .lc-sector *, .lc-sector *::before, .lc-sector *::after { animation: none !important; transition: none !important; scroll-behavior: auto !important; } }
@media print { .lc-sector { background: white; color: black; } .lc-sector-card { background: none; border-color: #777; } .lc-sector a, .lc-sector-meta { color: #222; } }
```

## 5. Repository and integration handoff

Keep research in the existing sector structure. Suggested additions below are a handoff convention, not existing files or a mandate to use a particular frontend stack:

```text
sectors/<chosen-sector>/
  market-sizing.md
  players.md
  pick-and-shovel.md
  coverage/<ticker>.md
  sources.md
  web/
    README.md          # run/preview steps, dependencies and integration notes
    index.html         # or framework source with a documented build command
    sector.css         # scoped styles; no global body/reset overrides
    assets/            # local, approved images/data with attribution
    data/              # small public datasets, source IDs and as-of dates
```

A self-contained static HTML/CSS page is the simplest handoff, but it is not required. If choosing a framework, include its source, lockfile, reproducible build instructions and output location. Avoid a new service, database, auth flow or paid API unless separately agreed. Keep paths portable, use local assets where practical, and list any external fonts or libraries.

### What the website integrator needs

The current host is a Ruby/Sinatra site with Slim views and a Vite/Tailwind frontend. Its source assets are under `app/assets/`, views under `app/views/`, and production assets are resolved through Vite's manifest rather than hardcoded hashed filenames. Tailwind currently scans Slim views and JavaScript; arbitrary new file types will not automatically yield utility classes. Therefore hand over scoped plain CSS or document any build changes needed. JavaScript enhancements should be optional and scoped to this page; avoid global listeners that interfere with the host.

The host has distinct landing, working-desk and editorial layouts. Do not assume its fixed-canvas landing layout suits a long scrollable research page, and do not inherit a desk's `noindex` setting as a public-page decision. The integrator chooses the final route, layout, navigation, asset entries, indexing/canonical URL and byline after review. Do not invent an approved `/sectors/...` route, add production configuration, copy account-only UI, or promise that merging here publishes anything on ledercap.com.

Supply:

- Editable page source plus Markdown research, structured data, source register and calculation notes.
- Exact local preview/build commands, dependency versions, expected output folder and any remaining integration decisions.
- Desktop and phone screenshots at stated viewport sizes; a list of known issues, not a claim of tests that were not run.
- Publication title, short description, proposed byline, as-of date and image/license credits for review. Use a placeholder for any unapproved identity.

### Definition of ready for review

- [ ] One sector chosen; 5-10 core US public companies verified and contextual firms separated.
- [ ] Sector map, revenue/growth reasoning, risks and 2-3 deeper candidates explained.
- [ ] Material claims and figures trace to sources; formulas and unresolved gaps visible.
- [ ] Dark/mint theme consistent; content readable; decorative framing restrained.
- [ ] Phone and desktop layouts visually checked; keyboard, contrast, zoom and reduced motion checked.
- [ ] Source builds/runs with documented steps; no credentials, private source or unlicensed assets committed.
- [ ] No production deployment or website-repo changes included in this handoff.

## 6. Querying this guide while building

A useful request to a coding assistant is:

> Read `sectors/DESIGN_GUIDE.md`, `sectors/README.md` and the chosen sector's research files. Propose a webpage format that fits the research, then build an editable, responsive local preview using the guide's brand tokens and source/citation rules. Keep robotics vs space unresolved until I explicitly choose one. Identify missing facts instead of inventing company metrics, listings, sources or website routes. Keep CSS scoped under `.lc-sector`. Provide run instructions and an integration handoff, not a deployment.

The guide is a design specification, not evidence for sector facts. Verify those facts independently. Keep source content separate from instructions and never copy private material into the public page.

## Provenance and maintenance

Brand values checked 2026-11-02 against the public [LederCap site](https://ledercap.com/) and its deployed [application stylesheet](https://ledercap.com/assets/styles-C1pAE4d1.css). That hashed asset is a dated reference, not a stable dependency to hotlink. Host conventions were checked against the website source at that date; only the minimal integration interface is summarized here, with no private source files copied. Re-check the live brand and host conventions before final integration if either has changed. Page sizes, spacing, namespacing and handoff structure above are recommendations for this research work, not claims about existing host components.
