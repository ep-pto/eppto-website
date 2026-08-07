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
| `shop.html` | Popcorn Express subscription, monthly Spirit Shop balance, spirit wear |
| `contact.html` | Catch-all email, board contacts, other ways to connect |
| `social.html` | Social media links |
| `favorites.html` | Teachers' favorite things |
| `minutes.html` | Meeting minutes (documents) |
| `budget.html` | Budget (documents) |
| `bylaws.html` | Bylaws (documents) |
| `_blocks.html` | **Source of truth for shared blocks.** Not a public page |
| `style.css` | All styling for every page |
| `script.js` | Dropdown menus (tap support on touch devices) and the mobile hamburger nav toggle |
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
| `board` | current board roster, full (photo, bio, role, name, email) | `about.html` |
| `board-compact` | the same roster, minus the photo and bio | `contact.html` |

A page opts out of a block simply by not having its markers. The `board`
block, for example, only has markers on `about.html`; every other page
omits them. The script reports pages without a given block's markers as
"no markers", which is informational, not an error.

**`board-compact` is a *derived* block, not markup of its own.** `about.html`'s
cards need a photo and bio per board member; `contact.html` just wants a plain
contact list. Rather than hand-maintain two roster copies that could drift, only
`board` has real markup in `_blocks.html` — `board-compact` is defined in
`sync-shared.py`'s `BLOCKS` list as "`board`, minus anything classed
`board-photo`, `board-photo-placeholder`, or `board-bio`", and the script strips
those elements (and any HTML comments) at sync time. There is exactly one place
to edit a board member: the `board` block. `board`'s photo/bio are themselves
placeholders (`.board-photo-placeholder`, "Bio coming soon.") until real ones
exist — see `img/board/` and the commented-out `<img>` tag next to each person.

A derived block is declared like this:

```python
Block("board-compact", source="board", strip_classes=["board-photo", "board-bio"])
```

`source` says which block's content to start from; `strip_classes` says what to
remove. Everything else about it (its own `:start`/`:end` markers on whatever
page uses it, showing up in `--check`, etc.) works exactly like a normal block.

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

### Cache-busting for style.css and script.js

The `head` block stamps a `?v=<hash>` onto `style.css` and `script.js` -
`href="style.css?v=d8ac98a4"` rather than a bare `href="style.css"`. The hash
is computed from each file's actual bytes at sync time (`add_asset_versions()`
in `sync-shared.py`), so it always matches the current content automatically.

This exists because a browser (or any CDN in front of the host) caches a file
by its URL. If you edit `style.css` in place, the URL never changes, so
visitors can keep getting the old cached copy until it expires. Changing the
query string makes it a new URL from the browser's point of view, so it
fetches the new content on a normal visit - nobody has to force-refresh.

**The fix only takes effect once you re-run the sync.** Editing `style.css` or
`script.js` alone doesn't touch any page - run `python3 sync-shared.py head`
(or a full `python3 sync-shared.py`) afterward so the new hash goes out.
`_blocks.html` itself keeps a plain, unversioned `href="style.css"` in its own
copy of the head block; only the generated copies on real pages get the `?v=`.

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

### Adding a derived (subset) block

Use this when a new page needs *most* of an existing block but should never
show a couple of specific elements — the `board` / `board-compact` split above
is the example to copy.

1. Make sure the elements to exclude have a distinguishing class (add one if
   they don't)
2. Add a `Block(...)` to `BLOCKS` with `source` set to the base block's name
   and `strip_classes` set to the classes to remove — no markers for it go in
   `_blocks.html`, since it has no markup of its own
3. Put that new block's own `:start`/`:end` markers on the page that should
   get the subset (never the base block's markers there — those still render
   the full version)

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
  (`--surface`). The `.section-1` / `.section-2` / `.section-3` classes are
  markup hooks only — they don't set a background color. Sections are set
  apart by whitespace and a short red underline under each `<h2>`
  (`main h2::after`). Don't reintroduce full-width colored section
  backgrounds; keep new sections on the same light surface.
- `.section-inner` caps content at 1100px and centers it.
- `.section-lead` is the larger intro paragraph.
- `.bullet-list` is the square-bullet list style.
- `.section-image` is a flyer/promo image dropped into a section's copy —
  capped at the same `var(--measure)` width as body text, rounded corners,
  card-style shadow. Used on `shop.html` for the Popcorn Express flyer
  (`img/popcorn-express.webp`).
- `.board-grid` / `.board-card` is a generic card grid (white card, hairline
  border, red top accent) — not board-specific, and reused for sponsors, the
  Silver/Bronze sponsor tiers, and teacher favorites.
- `.teacher-card` (favorites.html) collapses to just grade + name by default,
  with the full favorites `<dl>` behind a native `<details>`/`<summary>` toggle
  (`.fav-toggle`) — no JS needed for the expand/collapse itself. Cards use
  `align-self: start` so expanding one card doesn't stretch its row-mates to
  match its height.
- `.board-photo` / `.board-photo-placeholder` / `.board-bio` (about.html's
  board cards only, via the `board` block — these are exactly the classes
  `board-compact` strips out for contact.html) — a circular photo, a dashed
  placeholder circle standing in for it until a real photo exists, and a short
  bio line.
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
  - **Gold banner artwork should be 1200x400px (3:1)** — ask each Golden Eagle
    sponsor for this when they sign on. `object-fit: contain` keeps an
    off-ratio image from being cropped (it just letterboxes on white), so a
    wrong size won't break the layout, but 1200x400 is what fills the tile
    edge-to-edge. Until a sponsor sends artwork, use `.sponsor-banner-fallback`
    (business name on a plain white tile) as a placeholder — see
    `.sponsor-card-placeholder` below for the currently-commented-out example.
  - Each Gold tile can also carry a short `.sponsor-info` blurb and, if the
    business has one, a `.sponsor-social` icon row (Facebook/Instagram SVGs
    copied from the `social` block's icons) — see any live Gold tile for the
    pattern. Both are optional; the banner and website link are the only
    required parts.
  - **`.sponsor-card-placeholder`** is a billboard-style "this spot is open"
    card standing in for a tier with no sponsor — dashed border instead of
    the solid red/shadow card treatment, a `.sponsor-placeholder-name` line,
    and a price + link to `#become-a-sponsor` (the id on the pricing table's
    `<section>`). Live right now on Silver and Bronze (each tier's only
    `<li>`); Gold's version is commented out directly above "Become a
    Sponsor" in `sponsors.html` since all three Gold spots are currently
    filled — restore it if a Gold sponsor lapses. Width is tier-specific:
    Silver `max-width: 50%`, Bronze `max-width: 20%` (Gold implicitly 100%,
    it's just the full-width banner column) — see the "Tile widths follow
    the tier hierarchy" comment in `style.css` for why `width: 100%` is also
    needed alongside `max-width` (grid `justify-self: center` otherwise
    shrinks the card to fit its text instead of claiming its intended size).