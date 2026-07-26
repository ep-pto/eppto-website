#!/usr/bin/env python3
"""Copy shared blocks from _blocks.html into every page that carries them.

_blocks.html is the single source of truth. A block is whatever sits
between a matching pair of marker comments:

    <!-- nav:start -->   ...   <!-- nav:end -->
    <!-- board:start --> ...   <!-- board:end -->

Edit a block in _blocks.html, run this script, and every page with the
same markers is updated. Blocks on those pages are overwritten, so never
edit them there -- the script writes a GENERATED notice into each copy as
a reminder.

The nav block additionally gets its `active` class set per page, derived
from each page's own filename, so no page can carry a stale highlight.

A block can also be *derived*: instead of its own markup in _blocks.html,
it's defined as another block with certain elements removed. `board-compact`
is the board roster minus its photo and bio -- there's still only one place
to edit a board member (the `board` block), and the compact copy on
contact.html is generated from it automatically, never hand-duplicated.

The `head` block additionally stamps a `?v=<hash>` query string onto
style.css and script.js, hashed from each file's current contents. This is
cache-busting: without it, a visitor's browser (or a CDN in front of the
host) can keep serving an old cached copy of style.css after it's changed,
since the URL never changed. The hash changes automatically whenever either
file's content changes, so a normal sync run is enough to make every page
pick up the new version -- nobody has to remember to bump a version number,
and nobody visiting the site has to force-refresh.

Usage:
    python3 sync-shared.py            sync every block
    python3 sync-shared.py --check    report what would change, write nothing
    python3 sync-shared.py nav        sync only the named block(s)
    python3 sync-shared.py --help     show this message

Files beginning with "_" are partials: they are sources, never destinations.

To add a shared block:
    1. wrap it in <!-- name:start --> / <!-- name:end --> in _blocks.html
    2. put the same markers where it should appear on each page
    3. add its name to BLOCKS below

To add a derived (subset) block instead -- one whose content is always some
other block minus a few tagged elements, so there's nothing extra to
hand-maintain:
    1. give the elements to exclude a distinguishing class, if they don't
       already have one
    2. add a Block(...) to BLOCKS with `source` set to the base block's name
       and `strip_classes` set to the classes to remove
    3. put that new block's own markers where the subset should appear
       (never the base block's markers -- those still get the full version)
"""

import hashlib
import re
import sys
from collections import namedtuple
from pathlib import Path

SOURCE = "_blocks.html"

# name:            the block's own marker name, and what pages reference
# does_active:     set the `active` class per destination page? (nav only)
# source:          None for a normal block (content comes from its own
#                  markers in _blocks.html); another block's name to derive
#                  this one from that block's content instead
# strip_classes:   when `source` is set, remove every element whose class
#                  list contains any of these
# versions_assets: stamp a content-hash `?v=` query string onto style.css
#                  and script.js references (head block only) - see
#                  add_asset_versions() below
Block = namedtuple("Block", "name does_active source strip_classes versions_assets")


def _block(
    name, does_active=False, source=None, strip_classes=None, versions_assets=False
):
    return Block(name, does_active, source, strip_classes, versions_assets)


BLOCKS = [
    _block("head", versions_assets=True),
    _block("nav", does_active=True),
    _block("board"),
    _block(
        "board-compact",
        source="board",
        strip_classes=["board-photo", "board-photo-placeholder", "board-bio"],
    ),
]

# Assets that get a cache-busting ?v=<hash> query string wherever the head
# block references them by a bare filename (href="style.css", src="script.js").
VERSIONED_ASSETS = ["style.css", "script.js"]

# When the current page is inside a dropdown, also mark its parent active.
MARK_PARENT_OF_ACTIVE_CHILD = True

ROOT = Path(__file__).parent
ANCHOR_RE = re.compile(r"<a\b[^>]*>", re.IGNORECASE)
HREF_RE = re.compile(r'href="([^"]*)"', re.IGNORECASE)
CLASS_RE = re.compile(r'class="([^"]*)"', re.IGNORECASE)
TAG_WITH_CLASS_RE = re.compile(r'<(\w+)\b[^>]*\bclass="([^"]*)"[^>]*>', re.IGNORECASE)
COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

# Elements with no closing tag - stripping one only needs to drop its own
# <tag ...> match, never a matching close.
VOID_TAGS = {"img", "br", "hr", "input", "meta", "link"}


def notice(name):
    return (
        "\n<!-- GENERATED from %s (%s block) by sync-shared.py."
        " Edit it there, not here. -->" % (SOURCE, name)
    )


def _classes(tag):
    m = CLASS_RE.search(tag)
    return (m, m.group(1).split() if m else [])


def _with_classes(tag, classes):
    m = CLASS_RE.search(tag)
    if not m:
        return tag
    return tag[: m.start(1)] + " ".join(classes) + tag[m.end(1) :]


def _matching_li_end(html, open_start):
    """Index just past the </li> closing the <li> beginning at open_start.

    Tracks nesting, so a parent item containing a dropdown <ul> of <li>s
    returns its own closing tag rather than the first nested one.
    """
    return _matching_tag_end(html, open_start, "li")


def _matching_tag_end(html, open_start, tag):
    """Index just past the closing tag matching the open tag at open_start.

    Generic version of the li-matcher above: tracks nesting depth so an
    element containing others of the same name returns its own close, not
    the first nested one.
    """
    open_re = re.compile(r"<%s\b" % re.escape(tag), re.IGNORECASE)
    close_re = re.compile(r"</%s\s*>" % re.escape(tag), re.IGNORECASE)
    depth = 0
    pos = open_start
    while pos < len(html):
        nxt_open = open_re.search(html, pos)
        nxt_close = close_re.search(html, pos)
        if not nxt_close:
            return len(html)
        if nxt_open and nxt_open.start() < nxt_close.start():
            depth += 1
            pos = nxt_open.end()
        else:
            depth -= 1
            pos = nxt_close.end()
            if depth == 0:
                return pos
    return len(html)


def strip_elements(html, classes):
    """Remove every element whose class list intersects `classes`.

    Also drops HTML comments entirely: the ones in practice sit right next
    to a stripped element (e.g. "uncomment once available" next to a photo),
    and make no sense to keep on a derived block that no longer has it.
    """
    html = COMMENT_RE.sub("", html)

    out = []
    pos = 0
    while True:
        m = TAG_WITH_CLASS_RE.search(html, pos)
        if not m:
            out.append(html[pos:])
            break
        out.append(html[pos : m.start()])
        tag, tag_classes = m.group(1), m.group(2).split()
        if any(c in tag_classes for c in classes):
            end = m.end() if tag.lower() in VOID_TAGS else _matching_tag_end(
                html, m.start(), tag
            )
            pos = end
        else:
            out.append(html[m.start() : m.end()])
            pos = m.end()

    # Collapse the blank line(s) a removed element leaves behind.
    return re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", "".join(out))


def _content_hash(path, length=8):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:length]


def add_asset_versions(html):
    """Stamp a `?v=<hash>` onto each VERSIONED_ASSETS reference in `html`.

    The hash is computed fresh from the asset's current bytes every time this
    runs, so it's always correct and never needs updating by hand - editing
    style.css or script.js and re-running the sync is enough to bust every
    page's cached copy.
    """
    for asset in VERSIONED_ASSETS:
        path = ROOT / asset
        if not path.exists():
            continue
        version = _content_hash(path)
        ref_re = re.compile(
            r'((?:href|src)=")%s(?:\?v=[0-9a-f]+)?(")' % re.escape(asset)
        )
        html = ref_re.sub(r"\g<1>%s?v=%s\g<2>" % (asset, version), html)
    return html


def set_active(block_html, page):
    """Return block_html with `active` set only on the link matching `page`."""

    def rewrite(match):
        tag = match.group(0)
        cls_m, classes = _classes(tag)
        if not cls_m:
            return tag
        classes = [c for c in classes if c != "active"]
        href_m = HREF_RE.search(tag)
        if href_m and href_m.group(1) == page:
            classes.append("active")
        return _with_classes(tag, classes)

    # Pass 1: clear every active, then set it on the anchor for this page.
    block_html = ANCHOR_RE.sub(rewrite, block_html)

    if not MARK_PARENT_OF_ACTIVE_CHILD:
        return block_html

    # Pass 2: if the active link sits in a dropdown, light up its parent.
    out = block_html
    search_from = 0
    parent_re = re.compile(
        r'<li\b[^>]*\bclass="[^"]*has-dropdown[^"]*"[^>]*>', re.IGNORECASE
    )
    while True:
        m = parent_re.search(out, search_from)
        if not m:
            break
        end = _matching_li_end(out, m.start())
        block = out[m.start() : end]
        search_from = m.start() + 1

        first = ANCHOR_RE.search(block)
        if not first:
            continue
        _, parent_classes = _classes(first.group(0))
        if "active" in parent_classes:
            continue
        if "active" not in block[first.end() :]:
            continue

        new_first = _with_classes(first.group(0), parent_classes + ["active"])
        new_block = block[: first.start()] + new_first + block[first.end() :]
        out = out[: m.start()] + new_block + out[end:]

    return out


def find_block(html, name):
    """Return (index after start marker, index of end marker), or None."""
    start, end = "<!-- %s:start -->" % name, "<!-- %s:end -->" % name
    i, j = html.find(start), html.find(end)
    if i == -1 or j == -1 or j < i:
        return None
    return i + len(start), j


def destinations():
    """Every page that can receive blocks. Partials (_*.html) are excluded."""
    return sorted(p for p in ROOT.glob("*.html") if not p.name.startswith("_"))


def sync_block(block, check_only, source_html):
    # A derived block reads its content from another block's markers (its
    # own name never appears in _blocks.html at all), then strips elements
    # from it. A normal block just reads its own markers.
    source_name = block.source or block.name
    span = find_block(source_html, source_name)
    if span is None:
        return (
            ["[%s] ERROR: no %s:start/%s:end markers in %s"
             % (block.name, source_name, source_name, SOURCE)],
            False,
        )

    template = source_html[span[0] : span[1]]
    if block.strip_classes:
        template = strip_elements(template, block.strip_classes)
    if block.versions_assets:
        template = add_asset_versions(template)
    changed, same, skipped = [], [], []

    for page in destinations():
        html = page.read_text()
        span = find_block(html, block.name)
        if span is None:
            skipped.append(page.name)
            continue

        content = set_active(template, page.name) if block.does_active else template
        updated = html[: span[0]] + notice(block.name) + content + html[span[1] :]

        if updated == html:
            same.append(page.name)
        else:
            changed.append(page.name)
            if not check_only:
                page.write_text(updated)

    lines = ["[%s]" % block.name]
    verb = "would update" if check_only else "updated"
    if changed:
        lines.append("  %s: %s" % (verb, ", ".join(changed)))
    if same:
        lines.append("  in sync: %s" % ", ".join(same))
    if skipped:
        lines.append("  no markers: %s" % ", ".join(skipped))
    return lines, True


def main():
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__.strip())
        return 0

    check_only = "--check" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    known = {b.name for b in BLOCKS}
    wanted = args or sorted(known)
    unknown = [w for w in wanted if w not in known]
    if unknown:
        print("unknown block(s): %s" % ", ".join(unknown))
        print("known blocks: %s" % ", ".join(sorted(known)))
        return 1

    src_path = ROOT / SOURCE
    if not src_path.exists():
        print("ERROR: source file %s not found" % SOURCE)
        return 1
    source_html = src_path.read_text()

    print("source: %s" % SOURCE)
    ok = True
    for block in BLOCKS:
        if block.name not in wanted:
            continue
        lines, good = sync_block(block, check_only, source_html)
        print("\n".join(lines))
        ok = ok and good
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
