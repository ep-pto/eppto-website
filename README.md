# Eagle Pointe Elementary PTO — website

A plain static site: HTML, one stylesheet, one small script. No build step,
no framework, no server needed. Open any `.html` file in a browser to view it.

## Files

| File | What it is |
|---|---|
| `index.html` | Home page: welcome, news, call-to-action |
| `about.html` | Mission, current board, outgoing board, get involved |
| `events.html` | This month's events (calendar tiles) |
| `meetings.html` | PTO meeting schedule (calendar tiles) |
| `fundraisers.html` | Fundraising updates |
| `membership.html` | Become a member |
| `volunteer.html` | Volunteer opportunities |
| `sponsors.html` | Community sponsors, in Golden / Silver / Bronze Eagle tiers |
| `donate.html` | Donate money (external link) and donate items (wishlist) |
| `contact.html` | Catch-all email, board contacts, other ways to connect |
| `social.html` | Social media links |
| `favorites.html` | Teachers' favorite things (documents) |
| `minutes.html` | Meeting minutes (documents) |
| `budget.html` | Budget (documents) |
| `bylaws.html` | Bylaws (documents) |
| `_blocks.html` | **Source of truth for shared blocks.** Not a public page |
| `style.css` | All styling for every page |
| `script.js` | Dropdown menus (tap support on touch devices) |
| `sync-shared.py` | Copies shared blocks from `_blocks.html` into the pages |
| `img/` | Images and favicon |

Files starting with `_` are partials — sources, not pages. Don't upload
`_blocks.html`, `sync-shared.py`, or `README.md` to the web host; they aren't
part of the public site.

## Shared blocks: the one thing to know

The navigation and the board roster appear on multiple pages. They are **not**
maintained separately. `_blocks.html` holds the canonical copy of each.

```
Edit _blocks.html  →  run: python3 sync-shared.py  →  every page updates
```

Blocks on the individual pages are **overwritten** by the script. Each copy
carries a `<!-- GENERATED ... -->` comment saying so. If you edit a block
directly on `about.html` or `contact.html`, your change is destroyed the next
time anyone runs the script.

A block is the markup between a pair of marker comments:

```html
<!-- board:start -->
  ... the shared markup ...
<!-- board:end -->
```

Current blocks:

| Block | What it holds | Appears on |
|---|---|---|
| `head` | favicon, font links, `style.css`, `script.js` | every page |
| `nav` | the whole navigation menu | every page |
| `board` | the current board roster | `about.html`, `contact.html` |

A page opts out of a block simply by not having its markers. The `board` block,
for example, only has markers on `about.html` and `contact.html`; every other
page omits them. The script reports pages without a given block's markers as
"no markers", which is informational, not an error.

(There used to be a `cta` "Don't Miss Out" block on every page. It was removed:
the call-to-action now lives only on the home page as its own section, so it is
no longer a shared block.)

### What is *not* in the `head` block

Anything page-specific stays outside the markers, above them in the `<head>`:

- `<title>` — different on every page
- `<meta charset>` and `<meta name="viewport">` — these must come first in
  the document, so they sit above the block
- Any future per-page `<meta name="description">` or social-share tags

So a page's `<head>` looks like this, and only the marked part is managed:

```html
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title</title>          <!-- yours, per page -->
  <!-- head:start -->                 <!-- managed by the script -->
  ...
  <!-- head:end -->
</head>
```

### Commands

```bash
python3 sync-shared.py            # sync everything
python3 sync-shared.py --check    # show what would change, write nothing
python3 sync-shared.py board      # sync one block only
python3 sync-shared.py --help     # full explanation
```

Use `--check` first if you're unsure — it never writes.

### The `active` nav highlight

You don't set this by hand. The script derives it from each page's filename:
on `about.html` it highlights the About Us link, and if the current page sits
inside a dropdown it highlights that dropdown's parent too. This is why a page
can never end up with a stale or doubled highlight.

### Adding a new shared block

1. Wrap the markup in `<!-- name:start -->` / `<!-- name:end -->` in `_blocks.html`
2. Put the same markers where it should appear on each page
3. Add the name to the `BLOCKS` list at the top of `sync-shared.py`

## Adding a new page

1. Copy an existing page (`contact.html` is a good starting point)
2. Change the `<title>` and the banner `<h1>`
3. Keep the `head:` and `nav:` marker pairs — you can empty the contents,
   the script fills them in
4. Add a link to the new page in the nav inside `_blocks.html`
5. Run `python3 sync-shared.py`

You can start a page with nothing but empty markers:

```html
<!-- head:start -->
<!-- head:end -->
```

The script writes the real content in on the next run.

## Page structure

```html
<div class="banner">        <!-- photo + nav + page title -->
  <!-- nav:start --> ... <!-- nav:end -->
  <h1>Page Title</h1>
</div>
<main>
  <section class="section section-1">
    <div class="section-inner"> ... </div>
  </section>
  <section class="section section-2"> ... </section>
  <section class="section section-3"> ... </section>
</main>
```

- **One light surface.** The whole site sits on a single off-white background
  (`--surface`). The `.section-1` / `.section-2` / `.section-3` classes are kept
  as markup hooks but no longer flood a background color — sections are set apart
  by whitespace and a short red underline under each `<h2>` (`main h2::after`).
  This replaced the old alternating grey / navy / red bands, which created a
  "false bottom": the hard light-to-dark seam read as a footer and stopped
  people scrolling.
- `.section-inner` caps content at 1100px and centers it.
- `.section-lead` is the larger intro paragraph.
- `.bullet-list` is the square-bullet list style.
- `.board-grid` / `.board-card` is a generic card grid (white card, hairline
  border, red top accent) — not board-specific, and reused for sponsors and the
  Silver/Bronze sponsor tiers.
- Buttons (`.banner-cta-link`, `.form-btn`) are filled red pills. In-content
  links (`main a`) are brand **navy** (`--link`) with a low, thin underline that
  firms up on hover; classed link components (buttons, `.contact-primary`,
  `.doc-link`) override this and keep their own look. All components are themed
  for the light surface — don't reintroduce full-width dark section backgrounds.
- `.wishlist-card` (donate page) reuses the card shell but left-aligns and adds
  a heading + item list — one card per donation category.
- The home-page call-to-action (`.cta-section`) is a contained, softly tinted
  panel rather than a full-width band.
- **Sponsor tiers** (`sponsors.html`): `.tier-gold` full-width business banners,
  `.tier-silver` medium logo cards, `.tier-bronze` name tiles, each with a
  gold / silver / bronze heading underline. Styles live in the "Sponsor tiers"
  block of `style.css`.

## Conventions worth keeping

- **Design tokens.** Repeated values (brand reds, the `--surface` page color,
  the `--link` / `--link-hover` navy for content links, card/hairline/kicker
  colors, the `--font-display` Oswald and `--font-body` Work Sans stacks, the
  `42rem` text measure) live as CSS custom properties in the `:root` block at
  the top of `style.css`. Change them there, not at each use site.
- **Paragraph margins are opt-in.** A bare `p { margin: 0 }` reset (kept
  deliberately at type-selector specificity) zeroes everything; components
  add back the margins they want. Never raise that reset's specificity —
  a `.section p` version of it once silently defeated every component's
  spacing.
- **Text measure.** Paragraphs and lists inside `.section-inner` are capped at
  `var(--measure)` (42rem) and centered. This is a fixed unit on purpose:
  `ch` scales with font-size, which made blocks of different sizes misalign.
- **Placeholder emails** use `example.org`. It is the reserved placeholder
  domain, so it can never reach a real inbox by accident and is obviously
  unfinished at a glance. Search for `PLACEHOLDER` to find them all.
- **Dropdown menus** are anchored to the right edge of their parent so they
  open inward and can't run off the screen.
- **The split layout** on the home page stacks below 1024px. Side by side on
  narrower screens squeezed the text to ~28 characters per line.
- **Typographic apostrophes** (`&rsquo;`) are used in visible text, not `'`.
- **Images**: `banner2.jpg` is the banner. The home-page logo is served as WebP
  (`logo600.webp`, 134K) — resized down from a 1.9MB original. `logo32.png` is
  the small logo in the top-left of the nav bar, which links back to the home
  page on every page.

## Still to do

- Replace the `PLACEHOLDER` emails in `_blocks.html` (board roster) and
  `contact.html` (catch-all address), then run the sync script
- Fill in the remaining `PLACEHOLDER` content: real event dates
  (`events.html`), meeting schedule (`meetings.html`), sponsor names / logos /
  banners (`sponsors.html`), the online-giving link and item categories on
  `donate.html`, and the document links on `minutes.html`, `budget.html`, and
  `bylaws.html`
- Verify dropdown tap behavior on a real touch device

Every page linked from the nav now exists.
