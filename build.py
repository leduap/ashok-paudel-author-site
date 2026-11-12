#!/usr/bin/env python3
"""Build the author site into the _site/ folder.

    python3 build.py            build the site into _site/
    python3 build.py --serve    build, then preview at http://127.0.0.1:8000

Uses only the Python 3 standard library. Nothing to install.

What it does:
  * reads every markdown file in posts/ (one blog post or book review each),
  * checks each one strictly (fields, dates, cover image, sections, no Amazon links),
  * writes a static HTML page for each one, a blog index with filters
    (all / posts / book reviews / each tag), an RSS feed and a sitemap,
  * puts the latest posts on the home page,
  * copies the home page files (index.html, styles.css, main.js, content.js,
    assets/) alongside.

If any post is malformed the build stops with a message naming the file and
nothing is written, so a bad post can never reach the live site.
"""

import datetime as dt
import functools
import html
import http.server
import json
import os
import re
import shutil
import sys
import urllib.parse
from email.utils import format_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"
POSTS_DIR = ROOT / "posts"

# --- Settings you may change -------------------------------------------------
HOME_POSTS = 6          # how many of the latest posts appear on the home page
POSTS_PER_PAGE = 20     # how many posts per page in the blog archive
FEED_ITEMS = 30         # how many posts the RSS feed carries
# The public address of the site, e.g. "https://www.example.com". Leave "" when
# publishing with the GitHub workflow: it supplies the address automatically.
SITE_URL = ""
# -----------------------------------------------------------------------------

TYPES = {"review": "Book review", "post": "Post"}
TYPE_PAGES = {"post": ("posts", "Posts"), "review": ("reviews", "Book reviews")}
FIELDS = ["title", "date", "updated", "type", "tags", "summary", "book_title", "book_author", "rating",
          "amazon_id", "cover", "cover_source"]
REQUIRED = ["title", "date", "type", "tags", "summary"]
REVIEW_ONLY = ["book_title", "book_author", "rating", "amazon_id", "cover", "cover_source"]
# A review must show the book's cover: a JPEG or PNG saved in assets/covers/.
COVER_PATH = re.compile(r"^assets/covers/[a-z0-9]+(?:-[a-z0-9]+)*\.(?:jpg|jpeg|png)$")
COVER_MIN_WIDTH, COVER_MIN_HEIGHT, COVER_MAX_BYTES = 120, 160, 400_000
# Sections with a fixed meaning. The build gives each its own look (see BOT_GUIDE.md).
SECTION_KINDS = {
    "the short answer": "answer", "who it is for": "for", "who it is not for": "notfor",
    "key ideas": "ideas", "what works": "pros", "what to be aware of": "cons",
    "the verdict": "verdict", "faq": "faq", "sources": "sources",
}
# Every review has these sections, with exactly these headings, in this order.
REVIEW_SECTIONS = ["The short answer", "Who it is for", "Who it is not for", "Key ideas", "What works",
                   "What to be aware of", "The verdict", "FAQ", "Sources"]
NEEDS_LIST = {"for", "notfor", "pros", "cons", "sources"}
REVIEW_CLOSING = "A review describes a book. It is not advice"
MIN_FAQ, MIN_REVIEW_SOURCES = 2, 2
TOC_MIN_SECTIONS = 3    # a post with at least this many ## sections gets an "On this page" list
RELATED_POSTS = 3       # how many "More from the blog" cards a post shows
# Newsletter: the sign-up form posts to whatever https:// address is in newsletter.formAction.
# Kit (formerly ConvertKit) is understood to call its email field "email_address"; this has NOT
# been confirmed against a live Kit form. Any other provider gets the usual name "email".
KIT_HOST = re.compile(r"^https://app\.(?:kit|convertkit)\.com/", re.I)
# Amazon stores that get a "Get the book" link on reviews. The affiliate tag for
# each store is read from content.js (affiliate.amazon); it is written nowhere else.
AMAZON_STORES = [("us", "www.amazon.com", "Amazon US"), ("uk", "www.amazon.co.uk", "Amazon UK"),
                 ("de", "www.amazon.de", "Amazon Germany")]
AMAZON_ID = re.compile(r"^(\d{9}[\dX]|B0[A-Z0-9]{8})$")
AMAZON_TAG = re.compile(r"^[A-Za-z0-9]+-[A-Za-z0-9]+$")
# Any web address pointing at Amazon. Posts must not contain one: the build makes them.
# Gumroad links in posts are allowed only while templates.show is true in content.js.
GUMROAD_URL = re.compile(r"\bgumroad\.com\b|\bgum\.co\b", re.I)
AMAZON_URL = re.compile(r"(?:https?:)?//[^\s)>\]]*\b(?:amazon\.[a-z]{2,3}(?:\.[a-z]{2})?|amzn\.(?:to|eu|com))\b", re.I)
FILENAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
TAG = re.compile(r"^[a-z0-9]+(?:[ -][a-z0-9]+)*$")
MAX_TITLE, MAX_SUMMARY, MAX_TAGS, MAX_TAG_LENGTH = 120, 220, 5, 30

esc = functools.partial(html.escape, quote=True)


# What the markdown code needs to know while it turns one post into HTML: the site's
# affiliate tags and own products (from content.js), the problems found in the post so
# far, and whether the post ended up containing an affiliate link.
CTX = {"site": None, "problems": [], "affiliate": False}
POST_ROOT = "../../"    # every post page lives at blog/<file-name>/, two folders below the site root
DIRECTIVE = re.compile(r"^::(\w+)(?:\s+(\S+))?\s*$")


def amazon_id_problem(code):
    """Why a 10-character Amazon code is not acceptable, or "" if it is fine."""
    if not AMAZON_ID.match(code):
        return (f"'{code}' is not a valid Amazon code. It must be the 10-character code from the product's "
                "Amazon address (the part after /dp/): a 10-digit ISBN such as 0857197681, or a code "
                "starting with B0 such as B0HQVRJQ1P")
    if code[0] != "B" and sum((10 - k) * (10 if c == "X" else int(c)) for k, c in enumerate(code)) % 11:
        return f"'{code}' is not a real ISBN-10 (its check digit is wrong). Copy it again from the Amazon address"
    return ""


def store_links(code, title, css=""):
    """Tagged links to one product on each Amazon store that has a tag in content.js."""
    links = []
    for key, host, label in AMAZON_STORES:
        tag = CTX["site"]["amazon_tags"].get(key) if CTX["site"] else ""
        if not tag:
            continue
        text = label if css else label.replace("Amazon ", "")
        links.append(
            f'<a{f" class={chr(34)}{css}{chr(34)}" if css else ""} href="https://{host}/dp/{code}?tag={tag}" '
            f'target="_blank" rel="sponsored nofollow noopener" '
            f'aria-label="{esc(title)} on {label} (affiliate link, opens in a new tab)">{text}'
            + (' <span aria-hidden="true">↗</span>' if css else "") + "</a>")
    if links:
        CTX["affiliate"] = True
    return links


def own_card(kind, key):
    """A 'From the author' card for one of his own books (::book CODE) or templates (::template ID).

    Everything on the card comes from content.js, so a post cannot describe the product differently.
    """
    site = CTX["site"]
    if kind == "book":
        item = next((b for b in site["books"] if b.get("amazonId") == key and not b.get("status")), None)
        if not item:
            CTX["problems"].append(
                f"'::book {key}' does not match a published book in content.js. Use the amazonId of one of "
                "the author's own published books: " + ", ".join(
                    f"{b['amazonId']} ({b.get('title', '')})" for b in site["books"]
                    if b.get("amazonId") and not b.get("status")))
            return ""
        label, image, alt = "From the author: his own book", item.get("cover", ""), "Cover of "
        buttons = store_links(key, item.get("title", ""), "button button-small")
        action = ('<p class="bookbox-get-label">Buy on Amazon <span class="aff-tag">Affiliate links</span></p>'
                  f'<p class="bookbox-buttons">{" ".join(buttons)}</p>') if buttons else ""
    else:
        item = next((t for t in site["templates"] if t.get("url", "").rstrip("/").endswith("/l/" + key)), None)
        if not item:
            CTX["problems"].append(
                f"'::template {key}' does not match a template in content.js. Use the last part of the "
                "template's Gumroad address (after /l/): " + ", ".join(
                    f"{t['url'].rstrip('/').rsplit('/', 1)[-1]} ({t.get('title', '')})"
                    for t in site["templates"] if t.get("url")))
            return ""
        label, image, alt = "From the author: his own template", item.get("image", ""), "Preview of "
        free = item.get("tag", "").strip().lower() == "free"
        action = (f'<p class="bookbox-buttons"><a class="button button-small" href="{esc(item["url"])}" '
                  f'target="_blank" rel="noopener">{"Get it free on Gumroad" if free else "Get it on Gumroad"} '
                  '<span aria-hidden="true">↗</span></a></p>')
    picture = ""
    if re.match(r"^assets/[A-Za-z0-9._/-]+$", image) and ".." not in image and (ROOT / image).is_file():
        picture = (f'<img class="owncard-img" src="{POST_ROOT}{esc(image)}" '
                   f'alt="{alt}{esc(item.get("title", ""))}" loading="lazy" decoding="async">')
    text = "".join(f'<p class="owncard-{css}">{esc(item[field])}</p>'
                   for css, field in (("t", "title"), ("s", "subtitle"), ("b", "blurb")) if item.get(field))
    return (f'<aside class="owncard owncard-{kind}" aria-label="{label}">{picture}'
            f'<div class="owncard-main"><p class="bookbox-k">{label}</p>{text}{action}</div></aside>')


class BuildError(Exception):
    """Raised with a list of plain-language problems."""

    def __init__(self, problems):
        super().__init__("\n".join(problems))
        self.problems = problems


# ---------------------------------------------------------------------------
# Markdown (a deliberately small subset; see BOT_GUIDE.md). Raw HTML in a post
# is shown as text, never run.
# ---------------------------------------------------------------------------

LIST_ITEM = re.compile(r"^(\s{0,3})([-*+]|\d{1,9}[.)])\s+(.*)$")
HEADING = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
RULE = re.compile(r"^\s{0,3}([-*_])(\s*\1){2,}\s*$")
QUOTE = re.compile(r"^\s{0,3}>\s?")
FENCE = re.compile(r"^\s{0,3}(```+|~~~+)")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def safe_url(url):
    """Links may go to http(s) pages, mailto addresses, or plain relative paths. Nothing else."""
    if re.match(r"^(https?://|mailto:)", url, re.I):
        return True
    return ":" not in url and bool(re.match(r"^[A-Za-z0-9_./#?=%~+,-]+$", url))


def inline(text):
    """Convert inline markdown to HTML. Everything else is escaped."""
    stash = []

    def keep(fragment):
        stash.append(fragment)
        return f"\x00{len(stash) - 1}\x00"

    def link(match):
        label, url = match.group(1), html.unescape(match.group(2))
        if url.lower().startswith("amazon:"):
            # [text](amazon:CODE): the build writes the tagged store links after the text.
            code = url[len("amazon:"):]
            problem = amazon_id_problem(code)
            if problem:
                CTX["problems"].append(f"link '[{plain(label)}](amazon:{code})': {problem}")
                return label
            links = store_links(code, plain(re.sub(r"\x00\d+\x00", "", label)))
            if not links:
                return label
            return label + keep(' <span class="amz">(Amazon: ' + " · ".join(links) + ")</span>")
        if not safe_url(url):
            return label
        attrs = f'href="{esc(url)}"'
        if re.match(r"^https?://", url, re.I):
            attrs += ' rel="noopener"'
        return keep(f"<a {attrs}>") + label + keep("</a>")

    def image(match):
        alt, url = html.unescape(match.group(1)), html.unescape(match.group(2))
        if not re.match(r"^https://", url, re.I):
            return esc(alt)
        return keep(f'<img src="{esc(url)}" alt="{esc(alt)}" loading="lazy">')

    text = re.sub(r"`([^`\n]+)`", lambda m: keep("<code>" + html.escape(m.group(1), quote=False) + "</code>"), text)
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|>~])", lambda m: keep(html.escape(m.group(1))), text)
    text = html.escape(text, quote=False)
    text = re.sub(r"!\[([^\]]*)\]\(\s*([^)\s]+)(?:\s+\"[^\"]*\")?\s*\)", image, text)
    text = re.sub(r"\[([^\]]+)\]\(\s*([^)\s]+)(?:\s+\"[^\"]*\")?\s*\)", link, text)
    text = re.sub(r"&lt;(https?://[^\s&]+)&gt;",
                  lambda m: keep(f'<a href="{esc(html.unescape(m.group(1)))}" rel="noopener">') + m.group(1) + keep("</a>"), text)
    text = re.sub(r"\*\*(?=\S)(.+?)(?<=\S)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\w_])__(?=\S)(.+?)(?<=\S)__(?![\w_])", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![*\w])\*(?=\S)([^*\n]+?)(?<=\S)\*(?![*\w])", r"<em>\1</em>", text)
    text = re.sub(r"(?<![\w_])_(?=\S)([^_\n]+?)(?<=\S)_(?![\w_])", r"<em>\1</em>", text)
    text = re.sub(r" {2,}\n", "<br>\n", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: stash[int(m.group(1))], text)


def starts_block(line):
    item = LIST_ITEM.match(line)
    if item and (not item.group(2)[0].isdigit() or item.group(2)[:-1] == "1"):
        return True
    return bool(HEADING.match(line) or RULE.match(line) or QUOTE.match(line) or FENCE.match(line)
                or DIRECTIVE.match(line))


def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line)]


def blocks(lines):
    out, i, n = [], 0, len(lines)
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        fence = FENCE.match(line)
        if fence:
            marker, buf = fence.group(1), []
            i += 1
            while i < n and not lines[i].strip().startswith(marker):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf), quote=False) + "</code></pre>")
            continue

        directive = DIRECTIVE.match(line)
        if directive:
            name, key = directive.group(1), directive.group(2) or ""
            if name == "template" and key and not CTX["site"].get("templates_on"):
                CTX["problems"].append(
                    f"line '{line.strip()}' links a Gumroad template, and Gumroad links are switched off for now. "
                    "Remove the line. (They come back when templates.show is set to true in content.js.)")
            elif name in ("book", "template") and key:
                out.append(own_card(name, key))
            else:
                CTX["problems"].append(
                    f"line '{line.strip()}' is not understood. The only lines that may start with :: are  "
                    "::book CODE  (one of the author's own books) and  ::template ID  (one of his templates)")
            i += 1
            continue

        heading = HEADING.match(line)
        if heading:
            # The post title is the page's only h1, so body headings start at h2.
            level = min(max(len(heading.group(1)), 2), 4)
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
            i += 1
            continue

        if RULE.match(line):
            out.append("<hr>")
            i += 1
            continue

        if QUOTE.match(line):
            buf = []
            while i < n and QUOTE.match(lines[i]):
                buf.append(QUOTE.sub("", lines[i], count=1))
                i += 1
            out.append("<blockquote>" + blocks(buf) + "</blockquote>")
            continue

        if "|" in line and i + 1 < n and "|" in lines[i + 1] and TABLE_SEP.match(lines[i + 1]):
            head = split_row(line)
            i += 2
            rows = []
            while i < n and lines[i].strip() and "|" in lines[i]:
                rows.append(split_row(lines[i]))
                i += 1
            table = "<thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
            for row in rows:
                row = (row + [""] * len(head))[:len(head)]
                table += "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in row) + "</tr>"
            out.append(f'<div class="table-wrap"><table>{table}</tbody></table></div>')
            continue

        item = LIST_ITEM.match(line)
        if item:
            ordered = item.group(2)[0].isdigit()
            items = []
            while i < n:
                item = LIST_ITEM.match(lines[i])
                if not item or item.group(2)[0].isdigit() != ordered:
                    break
                indent = len(item.group(1)) + len(item.group(2)) + 1
                buf = [item.group(3)]
                i += 1
                while i < n:
                    cur = lines[i]
                    if not cur.strip():
                        j = i
                        while j < n and not lines[j].strip():
                            j += 1
                        if j < n and len(lines[j]) - len(lines[j].lstrip()) >= 2:
                            buf.append("")
                            i = j
                            continue
                        break
                    lead = len(cur) - len(cur.lstrip())
                    if lead < 2 and (LIST_ITEM.match(cur) or starts_block(cur)):
                        break
                    buf.append(cur[min(lead, indent):])
                    i += 1
                items.append(buf)
                # Blank lines between items of the same list do not end the list.
                j = i
                while j < n and not lines[j].strip():
                    j += 1
                nxt = LIST_ITEM.match(lines[j]) if j < n else None
                if nxt and (nxt.group(2)[0].isdigit() == ordered) and not RULE.match(lines[j]):
                    i = j
            rendered = []
            for buf in items:
                inner = blocks(buf)
                if inner.startswith("<p>") and inner.count("<p>") == 1:
                    inner = inner.replace("<p>", "", 1).replace("</p>", "", 1)
                rendered.append(f"<li>{inner}</li>")
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(rendered) + f"</{tag}>")
            continue

        buf = [line.strip()]
        i += 1
        while i < n and lines[i].strip() and not starts_block(lines[i]):
            # Keep two trailing spaces: they mean a line break.
            buf.append(lines[i].lstrip())
            i += 1
        buf[0] = line.lstrip()
        out.append("<p>" + inline("\n".join(buf).rstrip()) + "</p>")
    return "\n".join(out)


def split_at_headings(lines, hashes):
    """Split lines at headings written with one of those numbers of # signs at the start of a line.

    Returns (lines before the first heading, [(heading text, lines under it), ...]).
    Headings inside a fenced code block are left alone.
    """
    lead, parts, current, fence = [], [], None, None
    for line in lines:
        if fence:
            if line.strip().startswith(fence):
                fence = None
        elif FENCE.match(line):
            fence = FENCE.match(line).group(1)
        else:
            heading = HEADING.match(line) if line.startswith("#") else None
            if heading and len(heading.group(1)) in hashes:
                current = (heading.group(2), [])
                parts.append(current)
                continue
        (current[1] if current else lead).append(line)
    return lead, parts


def plain(markup):
    """The text of a piece of generated HTML, with the tags removed."""
    return html.unescape(re.sub(r"<[^>]+>", "", markup))


def has_text(lines):
    return any(line.strip() for line in lines)


def structure(body, kind, bad):
    """Turn a post body into its parts: the opening text, the ## sections and the closing line.

    Sections whose heading has a fixed meaning (The short answer, Who it is for, FAQ, Sources
    and so on) are marked so the page can style them. A review must have all of them, in order.
    Problems are reported through bad().
    """
    # NUL characters are used internally as placeholders, so they are removed from input.
    lines = body.replace("\x00", "").expandtabs(4).split("\n")
    closing = ""
    if kind == "review":
        while lines and not lines[-1].strip():
            lines.pop()
        last = lines[-1].strip() if lines else ""
        if re.match(r"^([*_])" + re.escape(REVIEW_CLOSING) + r"\b[^*_]*\1$", last):
            closing = inline(last)
            lines.pop()
            while lines and (not lines[-1].strip() or RULE.match(lines[-1])):
                lines.pop()
        else:
            bad(f"a review must end with the line  *{REVIEW_CLOSING} to buy or sell any investment.*  "
                "(in italics, as the very last line)")

    intro, parts = split_at_headings(lines, {1, 2})
    sections, used, order = [], set(), []
    for title, content in parts:
        title_html = inline(title)
        label = plain(title_html).strip()
        name = SECTION_KINDS.get(re.sub(r"\s+", " ", label).lower().rstrip(":"), "")
        if name:
            if name in order:
                bad(f"the section '{label}' appears twice")
            order.append(name)
        base = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-") or "section"
        anchor, n = base, 2
        while anchor in used:
            anchor, n = f"{base}-{n}", n + 1
        used.add(anchor)

        if name in NEEDS_LIST and not any(LIST_ITEM.match(line) and line[:1] != " " for line in content):
            bad(f"the section '{label}' must be a list (lines starting with - or 1.)")
        if name == "faq":
            lead, questions = split_at_headings(content, {3})
            if has_text(lead):
                bad("the FAQ section must contain only questions: each question on a line starting with ###, "
                    "with its answer underneath")
            if len(questions) < MIN_FAQ:
                bad(f"the FAQ section needs at least {MIN_FAQ} questions, each on a line starting with ###")
            items = []
            for question, answer in questions:
                if not has_text(answer):
                    bad(f"the FAQ question '{question}' has no answer under it")
                items.append(f"<details><summary>{inline(question)}</summary>\n{blocks(answer)}\n</details>")
            rendered = '<div class="faq">\n' + "\n".join(items) + "\n</div>"
        else:
            if not has_text(content):
                bad(f"the section '{label}' is empty")
            rendered = blocks(content)
        if name == "sources" and kind == "review":
            links = len(re.findall(r"\]\(\s*https?://", "\n".join(content)))
            if links < MIN_REVIEW_SOURCES:
                bad(f"the Sources section of a review needs at least {MIN_REVIEW_SOURCES} links to pages "
                    "that were actually opened and checked (publisher, author or library pages)")
        sections.append({"kind": name, "id": anchor, "title": title_html, "label": label, "html": rendered})

    if kind == "review":
        if not has_text(intro):
            bad("a review must start with a short opening paragraph before the first ## heading")
        wanted = [SECTION_KINDS[title.lower()] for title in REVIEW_SECTIONS]
        missing = [title for title in REVIEW_SECTIONS if SECTION_KINDS[title.lower()] not in order]
        if missing:
            bad("a review needs these sections, each as a ## heading with exactly this wording: "
                + ", ".join(missing))
        elif [name for name in order if name in wanted] != wanted:
            bad("the sections of a review must come in this order: " + ", ".join(REVIEW_SECTIONS))
    return {"intro": blocks(intro), "sections": sections, "closing": closing}


def image_size(path):
    """(width, height) of a JPEG or PNG file, or None if it is neither. Standard library only."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")
    if data[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(data):
        if data[i] != 0xFF:
            return None
        marker = data[i + 1]
        if marker == 0xFF:
            i += 1
            continue
        if 0xD0 <= marker <= 0xD9 or marker == 0x01:
            i += 2
            continue
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            return int.from_bytes(data[i + 7:i + 9], "big"), int.from_bytes(data[i + 5:i + 7], "big")
        i += 2 + int.from_bytes(data[i + 2:i + 4], "big")
    return None


# ---------------------------------------------------------------------------
# Reading posts
# ---------------------------------------------------------------------------

def pretty_date(day):
    return f"{day.day} {day.strftime('%B %Y')}"


def tag_slug(tag):
    return tag.replace(" ", "-")


def load_post(path, problems):
    """Read and check one post. Returns a dict, or None after recording problems."""
    name = f"posts/{path.name}"
    found = []

    def bad(message):
        found.append(f"{name}: {message}")

    match = FILENAME.match(path.name)
    if not match:
        problems.append(f"{name}: the file name must look like 2026-11-10-short-title.md "
                        "(a real date, then lower-case letters, digits and hyphens only)")
        return None
    file_date = match.group(1)
    stem = path.name[:-3]

    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        problems.append(f"{name}: the file is not valid UTF-8 text")
        return None
    lines = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines[0].strip() != "---":
        problems.append(f"{name}: front matter is missing. The first line of the file must be ---")
        return None
    end = next((k for k in range(1, len(lines)) if lines[k].strip() == "---"), None)
    if end is None:
        problems.append(f"{name}: the front matter is never closed. Add a second --- line after the last field")
        return None

    meta = {}
    for number, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            bad(f"line {number}: expected 'field: value' but found '{line.strip()}'")
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1].strip()
        if key not in FIELDS:
            bad(f"line {number}: unknown field '{key}'. Allowed fields: {', '.join(FIELDS)}")
        elif key in meta:
            bad(f"line {number}: field '{key}' appears twice")
        else:
            meta[key] = value

    for key in REQUIRED:
        if not meta.get(key):
            bad(f"required field '{key}' is missing or empty")

    day = None
    if meta.get("date"):
        try:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", meta["date"]):
                raise ValueError
            day = dt.date.fromisoformat(meta["date"])
        except ValueError:
            bad(f"date '{meta['date']}' is not a real date in the form YYYY-MM-DD")
        else:
            if meta["date"] != file_date:
                bad(f"date '{meta['date']}' does not match the date in the file name ({file_date})")
            latest = dt.datetime.now(dt.timezone.utc).date() + dt.timedelta(days=1)
            if day > latest:
                bad(f"date {meta['date']} is in the future")

    kind = meta.get("type")
    if kind and kind not in TYPES:
        bad(f"type '{kind}' is not allowed. Use one of: {', '.join(TYPES)}")

    tags = []
    if meta.get("tags"):
        raw = meta["tags"].strip()
        if raw.startswith("[") and raw.endswith("]"):
            raw = raw[1:-1]
        for item in raw.split(","):
            tag = re.sub(r"\s+", " ", item.strip().strip("\"'").strip().lower())
            if not tag:
                continue
            if not TAG.match(tag) or len(tag) > MAX_TAG_LENGTH:
                bad(f"tag '{tag}' is not allowed. A tag is 1 to {MAX_TAG_LENGTH} characters: "
                    "letters a-z, digits, single spaces or hyphens")
            elif tag_slug(tag) not in [tag_slug(t) for t in tags]:
                tags.append(tag)
        if not tags and not found:
            bad("field 'tags' needs at least one tag, for example: tags: investing, index funds")
        if len(tags) > MAX_TAGS:
            bad(f"there are {len(tags)} tags; the limit is {MAX_TAGS}")

    if len(meta.get("title", "")) > MAX_TITLE:
        bad(f"title is {len(meta['title'])} characters; the limit is {MAX_TITLE}")
    if len(meta.get("summary", "")) > MAX_SUMMARY:
        bad(f"summary is {len(meta['summary'])} characters; the limit is {MAX_SUMMARY}")

    if kind == "review":
        for key in ("book_title", "book_author"):
            if not meta.get(key):
                bad(f"a review needs the field '{key}'")
    elif kind == "post":
        for key in REVIEW_ONLY:
            if key in meta:
                bad(f"field '{key}' is only allowed when type is review")
    rating = None
    if meta.get("rating"):
        if meta["rating"] in {"1", "2", "3", "4", "5"}:
            rating = int(meta["rating"])
        else:
            bad(f"rating '{meta['rating']}' must be a whole number from 1 to 5 (or leave the field out)")

    amazon_id = meta.get("amazon_id", "")
    if "amazon_id" in meta and kind == "review":
        if not AMAZON_ID.match(amazon_id):
            bad(f"amazon_id '{amazon_id}' is not valid. It must be the 10-character code from the book's "
                "Amazon address (the part after /dp/): either a 10-digit ISBN such as 0857197681, "
                "or a code starting with B0 such as B0HQVRJQ1P. Leave the field out if unsure")
        elif amazon_id[0] != "B":
            total = sum((10 - k) * (10 if c == "X" else int(c)) for k, c in enumerate(amazon_id))
            if total % 11:
                bad(f"amazon_id '{amazon_id}' is not a real ISBN-10 (its check digit is wrong). "
                    "Copy it again from the book's Amazon address, or leave the field out")

    updated = None
    if meta.get("updated"):
        try:
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", meta["updated"]):
                raise ValueError
            updated = dt.date.fromisoformat(meta["updated"])
        except ValueError:
            bad(f"updated '{meta['updated']}' is not a real date in the form YYYY-MM-DD")
        else:
            if day and updated < day:
                bad(f"updated {meta['updated']} is earlier than the post's date; leave the field out")
            if updated > dt.datetime.now(dt.timezone.utc).date() + dt.timedelta(days=1):
                bad(f"updated {meta['updated']} is in the future")

    # Every review shows the book's cover, so a review without a usable cover image fails.
    cover, cover_width, cover_height = "", 0, 0
    if kind == "review":
        cover = meta.get("cover", "")
        if not cover:
            bad("a review needs a cover image. Save the book's cover in assets/covers/ and add the line  "
                "cover: assets/covers/the-book-title.jpg  (see BOT_GUIDE.md for where covers may come from)")
        elif not COVER_PATH.match(cover):
            bad(f"cover '{cover}' is not allowed. It must be a .jpg or .png file in assets/covers/ named with "
                "lower-case letters, digits and hyphens, for example assets/covers/the-book-title.jpg")
        elif not (ROOT / cover).is_file():
            bad(f"cover image {cover} does not exist. Add the image file in the same commit as the review")
        else:
            size = image_size(ROOT / cover)
            if not size:
                bad(f"cover image {cover} is not a real JPEG or PNG picture")
            elif size[0] < COVER_MIN_WIDTH or size[1] < COVER_MIN_HEIGHT:
                bad(f"cover image {cover} is only {size[0]}x{size[1]} pixels, which looks like a blank "
                    f"placeholder. A cover must be at least {COVER_MIN_WIDTH}x{COVER_MIN_HEIGHT}")
            elif (ROOT / cover).stat().st_size > COVER_MAX_BYTES:
                bad(f"cover image {cover} is larger than {COVER_MAX_BYTES // 1000} KB. Save a smaller copy "
                    "(about 400 pixels wide is plenty)")
            else:
                cover_width, cover_height = size
        source = meta.get("cover_source", "")
        if not source:
            bad("a review needs the field 'cover_source': the https:// address of the page the cover image "
                "came from (the book's Open Library page or the publisher's page)")
        elif AMAZON_URL.search(source):
            bad("cover_source points at Amazon. Cover images must not be taken from Amazon; use Open Library "
                "or the publisher's own page")
        elif not re.match(r"^https://[A-Za-z0-9.-]+\.[A-Za-z]{2,}(/[^\s\"<>]*)?$", source):
            bad(f"cover_source '{source}' is not an https:// web address")

    body = "\n".join(lines[end + 1:]).strip()
    parts = None
    if not body:
        bad("there is no text after the front matter")
    elif AMAZON_URL.search(body):
        bad("the text contains a link to Amazon. Do not write Amazon links or affiliate tags in a post: "
            "for a review, set book_title, book_author and (optionally) amazon_id, and the build adds "
            "the 'Get the book' buttons with the right tags")
    elif GUMROAD_URL.search(body) and not (CTX["site"] or {}).get("templates_on"):
        bad("the text contains a link to Gumroad. Gumroad links are switched off for now, so remove it. "
            "(They come back when templates.show is set to true in content.js.)")
    else:
        CTX["problems"], CTX["affiliate"] = [], False
        parts = structure(body, kind if kind in TYPES else "post", bad)
        for problem in CTX["problems"]:
            bad(problem)

    if found:
        problems.extend(found)
        return None
    words = len(re.findall(r"\w+", body))
    return {
        "stem": stem, "file": path.name, "day": day, "updated": updated if updated and updated != day else None,
        "type": kind, "rating": rating,
        "title": meta["title"], "summary": meta["summary"], "tags": tags,
        "book_title": meta.get("book_title", ""), "book_author": meta.get("book_author", ""),
        "amazon_id": amazon_id if kind == "review" else "",
        "cover": cover, "cover_width": cover_width, "cover_height": cover_height,
        "cover_source": meta.get("cover_source", "") if kind == "review" else "",
        "parts": parts, "minutes": max(1, round(words / 220)),
        "affiliate": CTX["affiliate"],
        "links_to": re.findall(r"\]\(\s*(\.\.?/[^)\s]*)", body),
        "url": f"blog/{stem}/",
    }


def load_posts():
    """Read every post, newest first. Raises BuildError listing every problem found."""
    posts, problems = [], []
    if POSTS_DIR.is_dir():
        for path in sorted(POSTS_DIR.iterdir()):
            if path.name.startswith("."):
                continue
            if path.is_dir() or path.suffix != ".md":
                problems.append(f"posts/{path.name}: only .md post files belong in the posts folder")
                continue
            post = load_post(path, problems)
            if post:
                posts.append(post)
    stems = {post["stem"] for post in posts}
    for post in posts:
        for target in post["links_to"]:
            other = re.match(r"^\.\./([^/#?]+)/?(#.*)?$", target)
            if not other or other.group(1) not in stems:
                problems.append(f"posts/{post['file']}: the link ({target}) does not lead to a post on this site. "
                                "To link to another post write ../ then its file name without .md then /, "
                                "for example (../2026-09-14-review-the-psychology-of-money/)")
    if problems:
        raise BuildError(problems)
    posts.sort(key=lambda p: (p["day"], p["file"]), reverse=True)
    return posts


# ---------------------------------------------------------------------------
# Site-wide text from content.js and the shared header and footer from index.html
# ---------------------------------------------------------------------------

def content_string(source, key, scope=None):
    """Return the value of  key: "text"  in content.js, or None if it is absent."""
    if scope:
        block = re.search(r"^\s*" + re.escape(scope) + r"\s*:\s*\{(.*?)^\s*\}", source, re.S | re.M)
        if not block:
            return None
        source = block.group(1)
    match = re.search(r"^\s*" + re.escape(key) + r'\s*:\s*("(?:[^"\\\n]|\\.)*")', source, re.M)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except ValueError:
        return None


def content_items(source, key):
    """The items of a list in content.js such as  books: [ {...}, {...} ]  as dictionaries of their text values."""
    block = re.search(r"^\s*" + re.escape(key) + r"\s*:\s*\[(.*?)^\s*\]", source, re.S | re.M)
    items = []
    for body in re.findall(r"\{(.*?)\}", block.group(1) if block else "", re.S):
        item = {}
        for name, value in re.findall(r'^\s*(\w+)\s*:\s*("(?:[^"\\\n]|\\.)*")', body, re.M):
            try:
                item[name] = json.loads(value)
            except ValueError:
                pass
        if item:
            items.append(item)
    return items


def public_address():
    """The site's public address, without a trailing slash, or "" when none is set.

    GitHub reports a custom domain as http:// until "Enforce HTTPS" is ticked in
    the Pages settings. The site is always served over https, so the address is
    written as https:// (addresses on this computer are left alone).
    """
    url = (os.environ.get("SITE_URL") or SITE_URL or "").strip().rstrip("/")
    if url.startswith("http://") and not re.match(r"^http://(127\.0\.0\.1|localhost|\[::1\])(:|/|$)", url):
        url = "https://" + url[len("http://"):]
    return url


def load_site():
    problems = []
    for needed in ("index.html", "content.js", "styles.css", "main.js", "signup.js"):
        if not (ROOT / needed).is_file():
            problems.append(f"{needed}: file is missing")
    if problems:
        raise BuildError(problems)

    content = (ROOT / "content.js").read_text(encoding="utf-8")
    page = (ROOT / "index.html").read_text(encoding="utf-8")
    site = {
        "name": content_string(content, "name"),
        "credentials": content_string(content, "credentials"),
        "disclaimer": content_string(content, "disclaimer"),
        "affiliate.disclosure": content_string(content, "disclosure", "affiliate"),
        "affiliate_note": content_string(content, "note", "affiliate") or "",
        "amazon_tags": {key: (content_string(content, key, "amazon") or "").strip()
                        for key, _, _ in AMAZON_STORES},
        "tagline": content_string(content, "tagline") or "",
        "form_action": (content_string(content, "formAction", "newsletter") or "").strip(),
        "newsletter_heading": content_string(content, "heading", "newsletter") or "Newsletter",
        "newsletter_blurb": content_string(content, "blurb", "newsletter") or "",
        "newsletter_thanks": content_string(content, "thanks", "newsletter") or "Thank you.",
        "photo": content_string(content, "photo") or "",
        "books": content_items(content, "books"),
        "templates": content_items(content, "items"),
        # One switch for everything Gumroad: the home page section and links from posts.
        "templates_on": bool(re.search(r"^\s*templates\s*:\s*\{[^{}\[\]]*?\bshow\s*:\s*true\b", content, re.M)),
        "articles": [item for item in content_items(content, "articles")
                     if re.match(r"^https?://[^\s.]+\.\S+$", item.get("url", ""))],
        "url": public_address(),
        "home": page,
    }
    if not site["name"]:
        problems.append('content.js: could not find the line  name: "..."  near the top')
    for key, tag in site["amazon_tags"].items():
        if tag and not AMAZON_TAG.match(tag):
            problems.append(f"content.js: affiliate.amazon.{key} is '{tag}', which does not look like an "
                            "Amazon Associates tag (for example yourname-20). Fix it or set it to \"\"")
    if any(site["amazon_tags"].values()) and not site["affiliate.disclosure"]:
        problems.append("content.js: affiliate.disclosure is empty. Amazon requires the line "
                        "'As an Amazon Associate I earn from qualifying purchases.' while affiliate tags are set")
    if site["form_action"] and not re.match(r"^https://[A-Za-z0-9.-]+\.[A-Za-z]{2,}/\S*$", site["form_action"]):
        problems.append("content.js: newsletter.formAction must be empty or the full https:// address of your "
                        "sign-up form, copied from your newsletter provider")
    if not re.match(r"^assets/[A-Za-z0-9._/-]+\.(jpg|jpeg|png)$", site["photo"]) or ".." in site["photo"] \
            or not (ROOT / site["photo"]).is_file():
        site["photo"] = ""    # the small author picture beside the byline is simply left out

    header = re.search(r"<header class=\"site-header\">.*?</header>", page, re.S)
    footer = re.search(r"<footer class=\"site-footer\">.*?</footer>", page, re.S)
    if not header or not footer:
        problems.append("index.html: could not find the <header class=\"site-header\"> or "
                        "<footer class=\"site-footer\"> block that every page shares")
    if "<!-- BUILD:LATEST -->" not in page or "<!-- /BUILD:LATEST -->" not in page:
        problems.append("index.html: the markers <!-- BUILD:LATEST --> and <!-- /BUILD:LATEST --> "
                        "(where the latest posts go) are missing")
    if "<!-- BUILD:NEWSLETTER -->" not in page or "<!-- /BUILD:NEWSLETTER -->" not in page:
        problems.append("index.html: the markers <!-- BUILD:NEWSLETTER --> and <!-- /BUILD:NEWSLETTER --> "
                        "(where the newsletter sign-up box goes) are missing")
    if problems:
        raise BuildError(problems)
    site["header"], site["footer"] = header.group(0), footer.group(0)
    CTX["site"] = site
    return site


def fill_text(markup, site):
    """Fill in the bits main.js fills on the home page, so pages work without JavaScript."""
    for key in ("name", "credentials", "disclaimer", "affiliate.disclosure"):
        if site[key] is None:
            continue
        markup = re.sub(r'(<[^>]*data-text="' + re.escape(key) + r'"[^>]*>)[^<]*(?=<)',
                        lambda m, value=site[key]: m.group(1) + esc(value), markup)
    markup = re.sub(r'(<span id="year">)[^<]*(?=</span>)',
                    lambda m: m.group(1) + str(dt.date.today().year), markup)
    # Newsletter links: shown once a Kit form address is set, otherwise removed from the page altogether.
    if site["form_action"]:
        markup = re.sub(r'(<a[^>]*data-nav="newsletter"[^>]*?) hidden(?=[ >])', r"\1", markup)
    else:
        markup = re.sub(r'\s*<a\b[^>]*data-nav="newsletter"[^>]*>.*?</a>', "", markup, flags=re.S)
    # "Articles" links: shown once content.js lists at least one article with a real address.
    if site.get("articles"):
        markup = re.sub(r'(<a[^>]*data-nav="writing"[^>]*?) hidden(?=[ >])', r"\1", markup)
    return markup


def shared(block, site, root):
    """The home page header or footer, with its links pointed back at the home page."""
    block = fill_text(block, site)
    block = re.sub(r'href="#top"', f'href="{root}"', block)
    block = re.sub(r'href="#([^"]+)"', lambda m: f'href="{root}#{m.group(1)}"', block)
    block = re.sub(r'href="(blog/|feed\.xml)"', lambda m: f'href="{root}{m.group(1)}"', block)
    return block.replace('data-nav="blog"', 'data-nav="blog" aria-current="page"')


# ---------------------------------------------------------------------------
# HTML pieces
# ---------------------------------------------------------------------------

def root_for(path):
    """Relative path from a page back to the site root, e.g. '../../'."""
    return "../" * path.count("/")


def page_url(path):
    """Public path of an output file: 'blog/x/index.html' becomes 'blog/x/'."""
    return path[:-len("index.html")] if path.endswith("index.html") else path


def stars(rating):
    return ('<span class="stars" role="img" aria-label="Rated {0} out of 5">{1}'
            '<span class="stars-off">{2}</span></span>').format(rating, "★" * rating, "★" * (5 - rating))


def amazon_buttons(site, post):
    """The store buttons on a review: one per Amazon store that has a tag in content.js.

    With amazon_id the links go straight to the book's page; without it they go to
    a search for the title and author. Every link carries that store's affiliate tag.
    """
    links = []
    for key, host, label in AMAZON_STORES:
        tag = site["amazon_tags"].get(key)
        if not tag:
            continue
        if post["amazon_id"]:
            url = f"https://{host}/dp/{post['amazon_id']}?tag={tag}"
        else:
            query = urllib.parse.quote_plus(f"{post['book_title']} {post['book_author']}")
            url = f"https://{host}/s?k={query}&i=stripbooks&tag={tag}"
        links.append(
            f'<a class="button button-small" href="{esc(url)}" target="_blank" rel="sponsored nofollow noopener" '
            f'aria-label="{esc(post["book_title"])} on {label} (affiliate link, opens in a new tab)">'
            f'{label} <span aria-hidden="true">↗</span></a>')
    return links


def cover_img(post, root, css, lazy=True):
    return (f'<img class="{css}" src="{root}{esc(post["cover"])}" width="{post["cover_width"]}" '
            f'height="{post["cover_height"]}" alt="Cover of {esc(post["book_title"])}"'
            + (' loading="lazy"' if lazy else "") + ' decoding="async">')


def cover_credit(post):
    """Says where the cover picture came from, e.g. 'Cover image via Open Library'."""
    host = urllib.parse.urlsplit(post["cover_source"]).hostname or ""
    host = host[4:] if host.startswith("www.") else host
    name = "Open Library" if host.endswith("openlibrary.org") else host
    return (f'<p class="cover-credit">Cover image via <a href="{esc(post["cover_source"])}" rel="noopener">'
            f'{esc(name)}</a>. Cover art belongs to the publisher.</p>')


def affiliate_note(site):
    """The disclosure shown close to the affiliate links on a review."""
    text = " ".join(part for part in (site["affiliate.disclosure"], site["affiliate_note"]) if part)
    return f'<p class="aff-note" role="note">{esc(text)}</p>' if text else ""


def book_box(site, post, root, end=False):
    """The box with the book's cover, title, author and store buttons.

    Shown near the top of a review and again, smaller, after the verdict.
    """
    buttons = amazon_buttons(site, post)
    get = ""
    if buttons:
        get = ('<div class="bookbox-get"><p class="bookbox-get-label">Get the book '
               '<span class="aff-tag">Affiliate links</span></p>'
               f'<p class="bookbox-buttons">{" ".join(buttons)}</p>'
               '<p class="bookbox-small">No prices are shown here because they change. '
               'Check the edition and format on the store page before you buy.</p></div>')
    rating = (f'<p class="book-rating">{stars(post["rating"])} '
              f'<span>{post["rating"]} out of 5</span></p>') if post["rating"] else ""
    label = "Where to get it" if end else "Book reviewed"
    box = (f'<aside class="bookbox{" bookbox-end" if end else ""}" aria-label="{label}">'
           + cover_img(post, root, "bookbox-cover", lazy=end)
           + f'<div class="bookbox-main"><p class="bookbox-k">{label}</p>'
           f'<p class="bookbox-t">{esc(post["book_title"])}</p>'
           f'<p class="bookbox-a">by {esc(post["book_author"])}</p>{rating}{get}</div></aside>')
    if end:
        return (affiliate_note(site) if buttons else "") + box
    return (affiliate_note(site) if buttons else "") + box + cover_credit(post)


def post_item(post, root, heading="h2"):
    book, thumb = "", ""
    if post["type"] == "review":
        book = (f'<p class="post-book">{esc(post["book_title"])} '
                f'<span>by {esc(post["book_author"])}</span>'
                + (" " + stars(post["rating"]) if post["rating"] else "") + "</p>")
        thumb = (f'<a class="post-thumb" href="{root}{post["url"]}" tabindex="-1" aria-hidden="true">'
                 + cover_img(post, root, "post-thumb-img").replace(f'alt="Cover of {esc(post["book_title"])}"', 'alt=""')
                 + "</a>")
    return (
        f'<li class="post-item post-{post["type"]}{" has-thumb" if thumb else ""}">{thumb}<div class="post-item-body">'
        f'<p class="post-kicker"><span class="badge">{TYPES[post["type"]]}</span> '
        f'<time datetime="{post["day"].isoformat()}">{pretty_date(post["day"])}</time>'
        f'<span>{post["minutes"]} min read</span></p>'
        f'<{heading} class="post-title"><a href="{root}{post["url"]}">{esc(post["title"])}</a></{heading}>'
        f'{book}<p class="post-summary">{esc(post["summary"])}</p></div></li>'
    )


def related_posts(post, posts):
    """Other posts that share the most tags with this one, newest first among equals."""
    mine = {tag_slug(t) for t in post["tags"]}
    scored = []
    for position, other in enumerate(posts):
        if other is post:
            continue
        shared_tags = len(mine & {tag_slug(t) for t in other["tags"]})
        scored.append((-shared_tags, other["type"] != post["type"], position, other))
    scored.sort(key=lambda item: item[:3])
    return [item[3] for item in scored[:RELATED_POSTS]]


def newsletter_block(site):
    """The newsletter sign-up box. Returns nothing at all until a Kit form address is set in content.js.

    The form posts straight to the address in newsletter.formAction. signup.js sends it in
    the background and shows the thank-you line; if that fails, or without JavaScript, the
    form is sent the ordinary way and the provider shows its own confirmation page.
    """
    if not site["form_action"]:
        return ""
    field = "email_address" if KIT_HOST.match(site["form_action"]) else "email"
    return f"""
    <section id="newsletter" class="band-dark">
      <div class="wrap narrow">
        <div class="signup center">
          <p class="eyebrow">Newsletter</p>
          <h2>{esc(site["newsletter_heading"])}</h2>
          <p>{esc(site["newsletter_blurb"])}</p>
          <form class="signup-form" method="post" action="{esc(site["form_action"])}" data-thanks="{esc(site["newsletter_thanks"])}">
            <label class="visually-hidden" for="signup-email">Email address</label>
            <input id="signup-email" name="{field}" type="email" autocomplete="email" placeholder="you@example.com" required>
            <button class="button" type="submit">Subscribe</button>
          </form>
          <p class="note signup-status" role="status" aria-live="polite" hidden></p>
        </div>
      </div>
    </section>"""


def render_page(site, path, title, description, main, kind="website", extra_head="", image=""):
    root = root_for(path)
    head = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{esc(title)} | {esc(site['name'])}</title>",
        f'<meta name="description" content="{esc(description)}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(description)}">',
        f'<meta property="og:type" content="{kind}">',
        f'<link rel="stylesheet" href="{root}styles.css">',
        f'<link rel="icon" href="{root}assets/icons/monogram/favicon.ico" sizes="48x48">',
        f'<link rel="icon" href="{root}assets/icons/monogram/icon.svg" type="image/svg+xml">',
        f'<link rel="apple-touch-icon" href="{root}assets/icons/monogram/apple-touch-icon.png">',
        f'<link rel="alternate" type="application/rss+xml" title="{esc(site["name"])}: blog" href="{root}feed.xml">',
    ]
    if site["url"]:
        head.append(f'<link rel="canonical" href="{esc(site["url"] + "/" + page_url(path))}">')
        if image:
            head.append(f'<meta property="og:image" content="{esc(site["url"] + "/" + image)}">')
    if extra_head:
        head.append(extra_head)
    script = f'\n  <script src="{root}signup.js"></script>' if site["form_action"] else ""
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n  ' + "\n  ".join(head) + "\n</head>\n<body>\n  "
        + shared(site["header"], site, root)
        + f'\n\n  <main id="top">{main}\n  </main>\n\n  '
        + shared(site["footer"], site, root)
        + script + "\n</body>\n</html>\n"
    )


def render_sections(sections, after_verdict=""):
    """The ## sections of a post. 'For / not for' and 'works / be aware' sit side by side on wide screens."""
    def one(section):
        css = f"sec sec-{section['kind']}" if section["kind"] else "sec"
        return (f'<section class="{css}" id="{section["id"]}">\n<h2>{section["title"]}</h2>\n'
                f'{section["html"]}\n</section>')

    out, i = [], 0
    while i < len(sections):
        kinds = (sections[i]["kind"], sections[i + 1]["kind"] if i + 1 < len(sections) else "")
        if kinds in (("for", "notfor"), ("pros", "cons")):
            out.append(f'<div class="pair pair-{kinds[0]}">\n{one(sections[i])}\n{one(sections[i + 1])}\n</div>')
            i += 2
        else:
            out.append(one(sections[i]))
            if kinds[0] == "verdict" and after_verdict:
                out.append(after_verdict)
            i += 1
    return "\n".join(out)


def render_post(site, post, posts, newer, older):
    path = post["url"] + "index.html"
    root = root_for(path)
    review = post["type"] == "review"
    parts = post["parts"]
    folder, type_label = TYPE_PAGES[post["type"]]

    crumbs = (f'<nav class="crumbs" aria-label="Breadcrumb"><a href="{root}">Home</a> <span>/</span> '
              f'<a href="{root}blog/">Blog</a> <span>/</span> <a href="{root}blog/{folder}/">{type_label}</a></nav>')
    photo = (f'<img class="byline-photo" src="{root}{esc(site["photo"])}" width="40" height="40" alt="">'
             if site["photo"] else "")
    author = esc(site["name"]) + (f', {esc(site["credentials"])}' if site["credentials"] else "")
    meta = [f'<span>By {author}</span>',
            f'<span><time datetime="{post["day"].isoformat()}">{pretty_date(post["day"])}</time></span>']
    if post["updated"]:
        meta.append(f'<span>Updated <time datetime="{post["updated"].isoformat()}">'
                    f'{pretty_date(post["updated"])}</time></span>')
    meta.append(f'<span>{post["minutes"]} min read</span>')

    toc = ""
    if len(parts["sections"]) >= TOC_MIN_SECTIONS:
        toc = ('<nav class="toc" aria-labelledby="toc-h"><details open><summary id="toc-h">On this page</summary><ol>'
               + "".join(f'<li><a href="#{s["id"]}">{s["title"]}</a></li>' for s in parts["sections"])
               + "</ol></details></nav>")
    top = (book_box(site, post, root) if review else (affiliate_note(site) if post["affiliate"] else "")) + toc
    closing = f'\n<p class="post-disclaimer">{parts["closing"]}</p>' if parts["closing"] else ""
    body = "\n".join(piece for piece in (
        parts["intro"], render_sections(parts["sections"], book_box(site, post, root, end=True) if review else "")
    ) if piece) + closing

    tags = "".join(f'<li><a href="{root}blog/tag/{tag_slug(t)}/">{esc(t)}</a></li>' for t in post["tags"])
    more = related_posts(post, posts)
    related = ""
    if more:
        related = ('\n        <section class="related" aria-labelledby="related-h"><h2 id="related-h">More from the blog</h2>'
                   '<ul class="post-list related-list">' + "".join(post_item(p, root, "h3") for p in more)
                   + "</ul></section>")
    nav = ""
    if newer or older:
        nav = '\n        <nav class="post-nav" aria-label="Older and newer posts">'
        if older:
            nav += (f'<a class="post-nav-older" href="{root}{older["url"]}"><span>Older</span>'
                    f'{esc(older["title"])}</a>')
        if newer:
            nav += (f'<a class="post-nav-newer" href="{root}{newer["url"]}"><span>Newer</span>'
                    f'{esc(newer["title"])}</a>')
        nav += "</nav>"
    main = f"""
    <article class="post post-{post["type"]}">
      <header class="page-head">
        <div class="wrap narrow">
          {crumbs}
          <h1 class="page-title">{esc(post["title"])}</h1>
          <p class="post-meta byline">{photo}{"".join(meta)}</p>
          <p class="post-lead">{esc(post["summary"])}</p>
        </div>
      </header>
      <div class="wrap narrow">
        <div class="post-top">{top}</div>
        <div class="prose">
{body}
        </div>
        <ul class="tag-list" aria-label="Tags">{tags}</ul>{related}{nav}
        <p class="post-cta">
          <a class="button" href="{root}#books">See the books by {esc(site["name"])}</a>
          <a class="button button-quiet" href="{root}blog/">All posts and reviews</a>
        </p>
      </div>
    </article>{newsletter_block(site)}"""
    data = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": post["title"], "description": post["summary"],
        "datePublished": post["day"].isoformat(),
        "dateModified": (post["updated"] or post["day"]).isoformat(),
        "author": {"@type": "Person", "name": site["name"]},
    }
    if site["url"]:
        data["url"] = site["url"] + "/" + post["url"]
        if post["cover"]:
            data["image"] = site["url"] + "/" + post["cover"]
    # "<" is written as \u003c so nothing in a post can close the script tag.
    extra = ('<script type="application/ld+json">'
             + json.dumps(data, ensure_ascii=False).replace("<", "\\u003c") + "</script>")
    return path, render_page(site, path, post["title"], post["summary"], main, "article", extra, post["cover"])


def render_listings(site, posts):
    """The blog index and its filtered views, each split into pages. Returns {path: html}."""
    pages = {}
    all_tags = {}
    for post in posts:
        for tag in post["tags"]:
            all_tags.setdefault(tag_slug(tag), [tag, 0])[1] += 1

    views = [("blog/", "all", "Blog", "Posts and book reviews", posts)]
    for kind, (folder, label) in TYPE_PAGES.items():
        views.append((f"blog/{folder}/", kind, label, label, [p for p in posts if p["type"] == kind]))
    for slug, (tag, _count) in sorted(all_tags.items()):
        views.append((f"blog/tag/{slug}/", "tag:" + slug, f"Tagged: {tag}", f"Tagged \u201C{tag}\u201D",
                      [p for p in posts if slug in [tag_slug(t) for t in p["tags"]]]))

    for base, key, title, heading, subset in views:
        chunks = [subset[i:i + POSTS_PER_PAGE] for i in range(0, len(subset), POSTS_PER_PAGE)] or [[]]
        for number, chunk in enumerate(chunks, start=1):
            path = base + ("index.html" if number == 1 else f"page/{number}/index.html")
            root = root_for(path)

            def tab(label, href, name, count):
                current = ' aria-current="page"' if name == key else ""
                return f'<a href="{root}{href}"{current}>{label} <span>{count}</span></a>'

            tabs = tab("All", "blog/", "all", len(posts))
            for kind, (folder, label) in TYPE_PAGES.items():
                tabs += tab(label, f"blog/{folder}/", kind, sum(1 for p in posts if p["type"] == kind))
            tags = "".join(
                '<li><a href="{0}blog/tag/{1}/"{2}>{3}</a></li>'.format(
                    root, slug, ' aria-current="page"' if key == "tag:" + slug else "", esc(tag))
                for slug, (tag, _count) in sorted(all_tags.items()))
            tag_row = f'\n          <ul class="tag-list" aria-label="Browse by tag">{tags}</ul>' if tags else ""

            if chunk:
                listing = '<ul class="post-list">\n          ' + "\n          ".join(
                    post_item(p, root) for p in chunk) + "\n        </ul>"
            else:
                listing = '<p class="empty">Nothing here yet. Please check back soon.</p>'

            pager = ""
            if len(chunks) > 1:
                def page_href(n):
                    return root + base + ("" if n == 1 else f"page/{n}/")
                pager = '\n        <nav class="pager" aria-label="Pages">'
                if number > 1:
                    pager += f'<a class="button button-quiet button-small" href="{page_href(number - 1)}">Newer</a>'
                pager += f"<span>Page {number} of {len(chunks)}</span>"
                if number < len(chunks):
                    pager += f'<a class="button button-quiet button-small" href="{page_href(number + 1)}">Older</a>'
                pager += "</nav>"

            main = f"""
    <header class="page-head">
      <div class="wrap narrow">
        <p class="eyebrow">Blog</p>
        <h1 class="page-title">{esc(heading)}</h1>
        <p class="page-lede">Posts and book reviews from {esc(site["name"])}, newest first.</p>
        <nav class="filters" aria-label="Filter">{tabs}</nav>{tag_row}
      </div>
    </header>
    <section class="listing">
      <div class="wrap narrow">
        {listing}{pager}
      </div>
    </section>{newsletter_block(site)}"""
            page_title = title + (f" (page {number})" if number > 1 else "")
            description = f"Posts and book reviews from {site['name']}." if key == "all" else \
                f"{heading}: from the blog of {site['name']}."
            pages[path] = render_page(site, path, page_title, description, main)
    return pages


def render_home(site, posts):
    latest = ""
    if posts:
        items = "\n          ".join(post_item(p, "", "h3") for p in posts[:HOME_POSTS])
        latest = f"""
    <section id="latest">
      <div class="wrap">
        <p class="eyebrow">From the blog</p>
        <h2>Latest writing</h2>
        <ul class="post-list post-cards">
          {items}
        </ul>
        <p class="more"><a class="button button-quiet" href="blog/">All posts and reviews</a></p>
      </div>
    </section>
    """
    page = re.sub(r"<!-- BUILD:LATEST -->.*?<!-- /BUILD:LATEST -->",
                  lambda m: "<!-- BUILD:LATEST -->" + latest + "<!-- /BUILD:LATEST -->",
                  site["home"], flags=re.S)
    # The sign-up box is written into the home page only when a Kit form address is set.
    page = re.sub(r"<!-- BUILD:NEWSLETTER -->.*?<!-- /BUILD:NEWSLETTER -->",
                  lambda m: "<!-- BUILD:NEWSLETTER -->" + newsletter_block(site) + "\n    <!-- /BUILD:NEWSLETTER -->",
                  page, flags=re.S)
    if not site["form_action"]:
        page = re.sub(r'\s*<script src="signup\.js"></script>', "", page)
    if site["url"]:
        page = page.replace("</head>", f'  <link rel="canonical" href="{esc(site["url"] + "/")}">\n</head>', 1)
    return fill_text(page, site)


def render_feed(site, posts):
    base = site["url"] or "http://127.0.0.1:8000"
    items = []
    for post in posts[:FEED_ITEMS]:
        stamp = dt.datetime.combine(post["day"], dt.time(8, 0), tzinfo=dt.timezone.utc)
        link = f"{base}/{post['url']}"
        items.append(
            "    <item>\n"
            f"      <title>{esc(post['title'])}</title>\n"
            f"      <link>{esc(link)}</link>\n"
            f"      <guid isPermaLink=\"true\">{esc(link)}</guid>\n"
            f"      <pubDate>{format_datetime(stamp)}</pubDate>\n"
            + "".join(f"      <category>{esc(t)}</category>\n" for t in [TYPES[post["type"]]] + post["tags"])
            + f"      <description>{esc(post['summary'])}</description>\n"
            "    </item>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n  <channel>\n'
        f"    <title>{esc(site['name'])}: blog and book reviews</title>\n"
        f"    <link>{esc(base)}/blog/</link>\n"
        f'    <atom:link href="{esc(base)}/feed.xml" rel="self" type="application/rss+xml"/>\n'
        f"    <description>{esc(site['tagline'] or 'Posts and book reviews')}</description>\n"
        "    <language>en</language>\n"
        + "\n".join(items) + ("\n" if items else "") + "  </channel>\n</rss>\n")


def render_sitemap(site, paths):
    urls = "".join(f"  <url><loc>{esc(site['url'] + '/' + page_url(p))}</loc></url>\n" for p in sorted(paths))
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n")


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def build():
    site = load_site()
    posts = load_posts()

    # Work out every page first, so a problem never leaves a half-built site.
    pages = {"index.html": render_home(site, posts)}
    for index, post in enumerate(posts):
        newer = posts[index - 1] if index > 0 else None
        older = posts[index + 1] if index + 1 < len(posts) else None
        path, markup = render_post(site, post, posts, newer, older)
        pages[path] = markup
    pages.update(render_listings(site, posts))
    extras = {"feed.xml": render_feed(site, posts), ".nojekyll": ""}
    if site["url"]:
        extras["sitemap.xml"] = render_sitemap(site, pages)
        extras["robots.txt"] = f"User-agent: *\nAllow: /\nSitemap: {site['url']}/sitemap.xml\n"

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for name in ("styles.css", "main.js", "content.js", "signup.js"):
        shutil.copy2(ROOT / name, OUT / name)
    if (ROOT / "assets").is_dir():
        shutil.copytree(ROOT / "assets", OUT / "assets", ignore=shutil.ignore_patterns(".*"))
    if (ROOT / "CNAME").is_file():
        shutil.copy2(ROOT / "CNAME", OUT / "CNAME")
    for path, text in {**pages, **extras}.items():
        target = OUT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    reviews = sum(1 for p in posts if p["type"] == "review")
    print(f"Built {len(pages)} pages into _site/ from {len(posts)} posts "
          f"({reviews} reviews, {len(posts) - reviews} posts).")
    if not site["url"]:
        print("Note: no site address is set, so the RSS feed uses a local address and no sitemap "
              "was written. This is normal on your own computer; the GitHub workflow sets it.")


def main():
    try:
        build()
    except BuildError as error:
        print("BUILD FAILED. Nothing was published. Fix the following and try again:", file=sys.stderr)
        for problem in error.problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    if "--serve" in sys.argv[1:]:
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(OUT))
        print("Preview at http://127.0.0.1:8000  (press Ctrl+C to stop)")
        try:
            http.server.ThreadingHTTPServer(("127.0.0.1", 8000), handler).serve_forever()
        except KeyboardInterrupt:
            print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
