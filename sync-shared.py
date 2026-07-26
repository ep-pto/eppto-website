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
"""

import re
import sys
from pathlib import Path

SOURCE = "_blocks.html"

BLOCKS = [
    # block name, set the `active` class per destination page?
    ("head", False),
    ("nav", True),
    ("board", False),
]

# When the current page is inside a dropdown, also mark its parent active.
MARK_PARENT_OF_ACTIVE_CHILD = True

ROOT = Path(__file__).parent
ANCHOR_RE = re.compile(r"<a\b[^>]*>", re.IGNORECASE)
HREF_RE = re.compile(r'href="([^"]*)"', re.IGNORECASE)
CLASS_RE = re.compile(r'class="([^"]*)"', re.IGNORECASE)
LI_OPEN_RE = re.compile(r"<li\b", re.IGNORECASE)
LI_CLOSE_RE = re.compile(r"</li\s*>", re.IGNORECASE)


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
    depth = 0
    pos = open_start
    while pos < len(html):
        nxt_open = LI_OPEN_RE.search(html, pos)
        nxt_close = LI_CLOSE_RE.search(html, pos)
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


def sync_block(name, does_active, check_only, source_html):
    span = find_block(source_html, name)
    if span is None:
        return (
            ["[%s] ERROR: no %s:start/%s:end markers in %s"
             % (name, name, name, SOURCE)],
            False,
        )

    template = source_html[span[0] : span[1]]
    changed, same, skipped = [], [], []

    for page in destinations():
        html = page.read_text()
        span = find_block(html, name)
        if span is None:
            skipped.append(page.name)
            continue

        content = set_active(template, page.name) if does_active else template
        updated = html[: span[0]] + notice(name) + content + html[span[1] :]

        if updated == html:
            same.append(page.name)
        else:
            changed.append(page.name)
            if not check_only:
                page.write_text(updated)

    lines = ["[%s]" % name]
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

    known = {b[0] for b in BLOCKS}
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
    for name, does_active in BLOCKS:
        if name not in wanted:
            continue
        lines, good = sync_block(name, does_active, check_only, source_html)
        print("\n".join(lines))
        ok = ok and good
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
