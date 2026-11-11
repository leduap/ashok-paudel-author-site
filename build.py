#!/usr/bin/env python3
"""Build the author site into the _site/ folder.

    python3 build.py            build the site into _site/
    python3 build.py --serve    build, then preview at http://127.0.0.1:8000

Uses only the Python 3 standard library. Nothing to install.

What it does:
  * reads every markdown file in posts/ (one blog post or book review each),
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
FIELDS = ["title", "date", "type", "tags", "summary", "book_title", "book_author", "rating", "amazon_id"]
REQUIRED = ["title", "date", "type", "tags", "summary"]
REVIEW_ONLY = ["book_title", "book_author", "rating", "amazon_id"]
# Amazon stores that get a "Get the book" link on reviews. The affiliate tag for
# each store is read from content.js (affiliate.amazon); it is written nowhere else.
AMAZON_STORES = [("us", "www.amazon.com", "Amazon US"), ("uk", "www.amazon.co.uk", "Amazon UK"),
                 ("de", "www.amazon.de", "Amazon Germany")]
AMAZON_ID = re.compile(r"^(\d{9}[\dX]|B0[A-Z0-9]{8})$")
AMAZON_TAG = re.compile(r"^[A-Za-z0-9]+-[A-Za-z0-9]+$")
# Any web address pointing at Amazon. Posts must not contain one: the build makes them.
AMAZON_URL = re.compile(r"(?:https?:)?//[^\s)>\]]*\b(?:amazon\.[a-z]{2,3}(?:\.[a-z]{2})?|amzn\.(?:to|eu|com))\b", re.I)
FILENAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-([a-z0-9]+(?:-[a-z0-9]+)*)\.md$")
TAG = re.compile(r"^[a-z0-9]+(?:[ -][a-z0-9]+)*$")
MAX_TITLE, MAX_SUMMARY, MAX_TAGS, MAX_TAG_LENGTH = 120, 220, 5, 30

esc = functools.partial(html.escape, quote=True)


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
    return bool(HEADING.match(line) or RULE.match(line) or QUOTE.match(line) or FENCE.match(line))


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


def markdown(text):
    # NUL characters are used internally as placeholders, so they are removed from input.
    return blocks(text.replace("\x00", "").expandtabs(4).split("\n"))


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

    body = "\n".join(lines[end + 1:]).strip()
    if not body:
        bad("there is no text after the front matter")
    elif AMAZON_URL.search(body):
        bad("the text contains a link to Amazon. Do not write Amazon links or affiliate tags in a post: "
            "for a review, set book_title, book_author and (optionally) amazon_id, and the build adds "
            "the 'Get the book' links with the right tags")

    if found:
        problems.extend(found)
        return None
    words = len(re.findall(r"\w+", body))
    return {
        "stem": stem, "file": path.name, "day": day, "type": kind, "rating": rating,
        "title": meta["title"], "summary": meta["summary"], "tags": tags,
        "book_title": meta.get("book_title", ""), "book_author": meta.get("book_author", ""),
        "amazon_id": amazon_id if kind == "review" else "",
        "html": markdown(body), "minutes": max(1, round(words / 220)),
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


def load_site():
    problems = []
    for needed in ("index.html", "content.js", "styles.css", "main.js"):
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
        "form_action": content_string(content, "formAction", "newsletter") or "",
        "newsletter_blurb": content_string(content, "blurb", "newsletter") or "",
        "url": (os.environ.get("SITE_URL") or SITE_URL or "").strip().rstrip("/"),
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
    if site["form_action"] and not re.match(r"^https://\S+$", site["form_action"]):
        problems.append("content.js: newsletter.formAction must be an https:// address or empty")

    header = re.search(r"<header class=\"site-header\">.*?</header>", page, re.S)
    footer = re.search(r"<footer class=\"site-footer\">.*?</footer>", page, re.S)
    if not header or not footer:
        problems.append("index.html: could not find the <header class=\"site-header\"> or "
                        "<footer class=\"site-footer\"> block that every page shares")
    if "<!-- BUILD:LATEST -->" not in page or "<!-- /BUILD:LATEST -->" not in page:
        problems.append("index.html: the markers <!-- BUILD:LATEST --> and <!-- /BUILD:LATEST --> "
                        "(where the latest posts go) are missing")
    if problems:
        raise BuildError(problems)
    site["header"], site["footer"] = header.group(0), footer.group(0)
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
    if site["form_action"]:
        markup = re.sub(r'(<a[^>]*data-nav="newsletter"[^>]*?) hidden(?=[ >])', r"\1", markup)
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


def amazon_links(site, post):
    """The 'Get the book' line on a review: one link per Amazon store that has a tag in content.js.

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
        links.append(f'<a href="{esc(url)}" target="_blank" rel="sponsored nofollow noopener">{label}</a>')
    if not links:
        return ""
    note = f'<p class="book-get-note">{esc(site["affiliate_note"])}</p>' if site["affiliate_note"] else ""
    return (f'<p class="book-get"><span class="book-get-label">Get the book</span> '
            + '<span class="book-get-links">' + " ".join(links) + "</span></p>" + note)


def post_item(post, root, heading="h2"):
    book = ""
    if post["type"] == "review":
        book = (f'<p class="post-book">{esc(post["book_title"])} '
                f'<span>by {esc(post["book_author"])}</span>'
                + (" " + stars(post["rating"]) if post["rating"] else "") + "</p>")
    return (
        f'<li class="post-item post-{post["type"]}">'
        f'<p class="post-kicker"><span class="badge">{TYPES[post["type"]]}</span> '
        f'<time datetime="{post["day"].isoformat()}">{pretty_date(post["day"])}</time></p>'
        f'<{heading} class="post-title"><a href="{root}{post["url"]}">{esc(post["title"])}</a></{heading}>'
        f'{book}<p class="post-summary">{esc(post["summary"])}</p></li>'
    )


def newsletter_block(site):
    """Signup box for blog pages. Empty until a provider address is set in content.js."""
    if not site["form_action"]:
        return ""
    return f"""
    <section class="band-dark">
      <div class="wrap narrow">
        <div class="signup center">
          <p class="eyebrow">Stay in touch</p>
          <h2>Newsletter</h2>
          <p>{esc(site["newsletter_blurb"])}</p>
          <form method="post" action="{esc(site["form_action"])}">
            <label class="visually-hidden" for="email">Email address</label>
            <input id="email" name="email" type="email" placeholder="you@example.com" required>
            <button class="button" type="submit">Subscribe</button>
          </form>
        </div>
      </div>
    </section>"""


def render_page(site, path, title, description, main, kind="website", extra_head=""):
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
        f'<link rel="alternate" type="application/rss+xml" title="{esc(site["name"])}: blog" href="{root}feed.xml">',
    ]
    if site["url"]:
        head.append(f'<link rel="canonical" href="{esc(site["url"] + "/" + page_url(path))}">')
    if extra_head:
        head.append(extra_head)
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n  ' + "\n  ".join(head) + "\n</head>\n<body>\n  "
        + shared(site["header"], site, root)
        + f'\n\n  <main id="top">{main}\n  </main>\n\n  '
        + shared(site["footer"], site, root)
        + "\n</body>\n</html>\n"
    )


def render_post(site, post, newer, older):
    path = post["url"] + "index.html"
    root = root_for(path)
    label = TYPES[post["type"]]
    book = ""
    if post["type"] == "review":
        rating = (f'<p class="book-rating">{stars(post["rating"])} '
                  f'<span>{post["rating"]} out of 5</span></p>') if post["rating"] else ""
        book = (f'\n          <div class="book-box"><p class="book-box-label">Book reviewed</p>'
                f'<p class="book-box-title">{esc(post["book_title"])}</p>'
                f'<p class="book-box-author">by {esc(post["book_author"])}</p>{rating}'
                f'{amazon_links(site, post)}</div>')
    tags = "".join(f'<li><a href="{root}blog/tag/{tag_slug(t)}/">{esc(t)}</a></li>' for t in post["tags"])
    nav = ""
    if newer or older:
        nav = '\n        <nav class="post-nav" aria-label="More posts">'
        if older:
            nav += (f'<a class="post-nav-older" href="{root}{older["url"]}"><span>Older</span>'
                    f'{esc(older["title"])}</a>')
        if newer:
            nav += (f'<a class="post-nav-newer" href="{root}{newer["url"]}"><span>Newer</span>'
                    f'{esc(newer["title"])}</a>')
        nav += "</nav>"
    main = f"""
    <article class="post">
      <header class="page-head">
        <div class="wrap narrow">
          <p class="eyebrow"><a href="{root}blog/">Blog</a> · {label}</p>
          <h1 class="page-title">{esc(post["title"])}</h1>
          <p class="post-meta">By {esc(site["name"])} · <time datetime="{post["day"].isoformat()}">{pretty_date(post["day"])}</time> · {post["minutes"]} min read</p>{book}
        </div>
      </header>
      <div class="wrap narrow">
        <div class="prose">
{post["html"]}
        </div>
        <ul class="tag-list" aria-label="Tags">{tags}</ul>{nav}
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
        "author": {"@type": "Person", "name": site["name"]},
    }
    if site["url"]:
        data["url"] = site["url"] + "/" + post["url"]
    # "<" is written as \u003c so nothing in a post can close the script tag.
    extra = ('<script type="application/ld+json">'
             + json.dumps(data, ensure_ascii=False).replace("<", "\\u003c") + "</script>")
    return path, render_page(site, path, post["title"], post["summary"], main, "article", extra)


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
        path, markup = render_post(site, post, newer, older)
        pages[path] = markup
    pages.update(render_listings(site, posts))
    extras = {"feed.xml": render_feed(site, posts), ".nojekyll": ""}
    if site["url"]:
        extras["sitemap.xml"] = render_sitemap(site, pages)
        extras["robots.txt"] = f"User-agent: *\nAllow: /\nSitemap: {site['url']}/sitemap.xml\n"

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    for name in ("styles.css", "main.js", "content.js"):
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
