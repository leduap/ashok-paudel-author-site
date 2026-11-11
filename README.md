# Ashok Paudel: author site

An author website with a blog. The home page is plain HTML, CSS and JavaScript. Blog posts and book reviews are markdown files that a small Python script turns into ordinary web pages. There is nothing to install beyond Python 3, which is already on a Mac.

## File layout

| File or folder | Purpose |
| --- | --- |
| `content.js` | All site-wide text, links and lists: headline, bio, books, footer line, newsletter, contact. The file you edit to change the home page. |
| `posts/` | One markdown file per blog post or book review. Adding a file here publishes it. |
| `BOT_GUIDE.md` | Instructions for the bot that adds one post a day: file naming, fields, examples, rules. |
| `build.py` | Turns `posts/` into web pages and assembles the finished site in `_site/`. |
| `index.html` | Home page structure: hero, books, latest writing, about, plus sections that stay hidden until they have content. Its header and footer are reused on every blog page. |
| `styles.css` | Layout and the mint and teal theme matched to the book covers. Colours are variables at the top. |
| `main.js` | Reads `content.js` and fills in the home page. |
| `signup.js` | Shows the thank-you message after a newsletter sign-up. Only used once the newsletter is switched on. |
| `assets/` | Your own book covers (from the Amazon.de listings) and the author photo. |
| `assets/covers/` | Covers of the books reviewed on the blog, one per review. |
| `assets/icons/monogram/` | The "AP" icon shown in the browser tab. |
| `.github/workflows/publish.yml` | Tells GitHub to run `build.py` and publish the result after every push. |
| `_site/` | The finished site, created by `build.py`. Never edit it by hand; it is rebuilt from scratch each time and is not stored on GitHub. |
| `.handover/` | Two leftover files from an interrupted work session (an unfinished script and an unused settings file). Not used by anything; safe to delete. |

What the build produces inside `_site/`:

- `index.html`: the home page, with the six latest posts added
- `blog/`: the blog index, newest first
- `blog/posts/` and `blog/reviews/`: the same list filtered to posts or to book reviews
- `blog/tag/<tag>/`: the list filtered to one tag
- `blog/<file-name>/`: one page per post or review
- `feed.xml`: the RSS feed

## Previewing on this computer

In Terminal, in this folder:

```
python3 build.py --serve
```

Then open <http://127.0.0.1:8000>. Press Ctrl+C to stop. Run it again after changing anything.

`python3 build.py` on its own builds `_site/` without starting the preview.

Opening `index.html` directly shows the home page without the blog, because the blog pages exist only after a build.

## Editing the home page

Open `content.js`, change the text between the quotes, save, and rebuild.

- Lines marked `DRAFT` (the headline and tagline) were written for you; replace them with your own words.
- Lines marked `PLACEHOLDER` (further social profiles, newsletter address) are waiting for your details.
- **Empty means hidden.** While a value is `""` or a list is `[]`, that part of the page does not appear. The Newsletter, Writing elsewhere, Events and Press, and Contact sections are all switched off this way. Fill one in and it appears, together with its menu link where it has one.
- **Books not yet for sale.** A book in the `books` list may carry the optional line `status: "Coming soon",`. Its card then shows that label and no buy button, and an empty `blurb` and `amazonId` leave no gap. "The Own the Whole Market Workbook" is set up this way, with a placeholder cover (`assets/own-the-whole-market-workbook-placeholder.svg`). Once the book is live: put the real cover in `assets/` and point `cover` at it, add the `blurb` and the book's `amazonId`, and delete the `status` line.
- Dates use `YYYY-MM-DD`. Events sort themselves into Upcoming and Past.
- A link without a real `https://` address is never shown as a link.

## Blog posts and book reviews

Each post is one file in `posts/` named `YYYY-MM-DD-short-title.md`. A book review also has a picture of the book's cover in `assets/covers/`; the build refuses a review without one. The top of the file holds a few labelled lines (title, date, type, tags, summary, and for reviews the book's title, author, an optional rating and an optional Amazon code), followed by the text. `BOT_GUIDE.md` has the full rules and two complete examples. You can add posts by hand in exactly the same way the bot does.

The build checks every post. If one is malformed (a missing field, a wrong date, a misspelt field name, a bad file name) the build stops, names the file and the problem, and publishes nothing, so the live site stays as it was. Any HTML typed into a post is shown as plain text and never run, so a post cannot inject scripts into the site.

The first ten posts are book reviews dated weekly from 7 September to 9 November 2026. They were drafted with AI assistance and should be read over by the author. Each lists the pages its facts were checked against under "Sources".

### How a review page is laid out

From top to bottom: a trail back to the blog, the title, the author line with the date and reading time, the summary, the affiliate disclosure, a box with the book's cover, title, author and three Amazon buttons, a contents list, and then the review in fixed sections: the short answer, who it is for and who it is not for, key ideas, what works and what to be aware of, the verdict (followed by the book box again), frequently asked questions, and sources. After that come the tags, three related posts, and the newsletter box when it is switched on. The blog list and the home page show a small cover beside each review.

The build checks all of this. A review that lacks a cover, a section, a source list or the closing line is refused, and the message names the file and the problem. `BOT_GUIDE.md` has the full rules.

### Cover pictures

The covers of reviewed books are in `assets/covers/`. They were found by ISBN on Open Library, or on the publisher's own page, never on Amazon, and each review credits its source under the cover.

### Links inside posts

Posts may link to your Gumroad templates, your own published books, other Amazon products and other posts. Amazon links are never typed by hand: a post asks for one by the product's code and the build writes the US, UK and German links with the right tags. `::book CODE` and `::template ID` on a line of their own make a "From the author" card from the details in `content.js`. The exact forms are in `BOT_GUIDE.md` under "Links".

## Amazon affiliate links

The site earns Amazon Associates commission through tagged links. The three tags (US, UK, Germany) are written once, in the `affiliate` block near the top of `content.js`, and nowhere else. Change a tag there and every link on the site changes with it; set a tag to `""` and that store's links disappear.

- **Your own books.** Each book in `content.js` has an `amazonId` (the 10-character code after `/dp/` in its Amazon address). Its card shows "Buy on Amazon" buttons for the US, UK and German stores, each with the right tag. A book marked `status: "Coming soon"` shows none.
- **Book reviews.** Every review shows a book box near the top, and again after the verdict, with buttons for the same three stores. If the review has an `amazon_id` line, the links open the book's page; if not, they open an Amazon search for the title and author. Either way the tag is added by the build. Posts must not contain Amazon links of their own: the build rejects them.
- **Disclosure.** Amazon requires the sentence "As an Amazon Associate I earn from qualifying purchases." It is `affiliate.disclosure` in `content.js` and appears in the footer of every page. A shorter note (`affiliate.note`) appears near the top of every post that contains Amazon links, above the first of them. The build refuses to run if tags are set and the disclosure is empty.
- Affiliate links open in a new tab and are marked `rel="sponsored nofollow noopener"`, as search engines ask.
- Links to the Gumroad templates are ordinary links to Ashok's own products. They are not affiliate links and need no tag. Where a review shows one of his books or templates, it is labelled "From the author".

Amazon's own rules, which the site cannot enforce: do not put affiliate links in emails, PDFs or ebooks; do not buy through your own links or ask friends and family to; and do not show prices copied from Amazon.

## Publishing

The site is designed for GitHub Pages:

1. Put this folder in a GitHub repository, on a branch called `main`.
2. On GitHub: Settings, then Pages, then under "Build and deployment" set Source to **GitHub Actions**.
3. From then on, every push to `main` runs the "Publish site" workflow, which runs `build.py` and publishes `_site/`. The site appears at `https://<username>.github.io/<repo-name>/` (or at your own domain if you set one up in the Pages settings).

The bot only needs permission to add files to the repository. It commits one new post to `posts/` each day (and, for a review, the cover picture to `assets/covers/`) and the workflow does the rest. If a build fails, the Actions tab on GitHub shows the message, and GitHub emails the repository owner.

This is already set up:

- Repository (public): <https://github.com/leduap/ashok-paudel-author-site>
- Copy it with: `git clone https://github.com/leduap/ashok-paudel-author-site.git`
- Live site: <https://ashokpaudel.com/>. The earlier address, <https://leduap.github.io/ashok-paudel-author-site/>, forwards to it.

The domain `ashokpaudel.com` is registered at Hostinger and its DNS is managed there. It is connected to the site in two places: the DNS records at Hostinger (four A and four AAAA records on the bare domain pointing at GitHub Pages, and `www` as a CNAME to `leduap.github.io`), and the "Custom domain" box under Settings, then Pages, on GitHub. Because the site is published by the workflow, no `CNAME` file is needed in this folder. The workflow passes the address to `build.py`, so the feed, the sitemap and the page addresses follow the domain by themselves; nothing in this folder has the address typed into it.

## Images

Put your files in `assets/` and point to them from `content.js`, for example `photo: "assets/author-photo.jpg"` or `cover: "assets/my-book.jpg"`. Covers look best at a 2:3 shape; the photo is shown as a square, cropped around the centre.

## Colours

The theme matches the "Inside FP&A" paperback cover and is set by the variables at the top of `styles.css`. The values were sampled from the cover: the pale mint gradient (`--mint-light`, `--mint`, `--mint-deep`), the deep teal name band (`--band`), the navy title colour (`--navy`), the greens of the labels and subtitle (`--green-label`, `--green-bright`) and the chart-bar accents (`--bar-teal`, `--bar-aqua`, `--bar-orange`, `--bar-yellow`). Change those variables to re-tint the whole site, blog included.

Headings use the font stack in `--display`. It names Poppins first, which is the closest match to the cover title, but the site does not load it: visitors see it only if it is installed on their device, and otherwise get Avenir Next or the nearest system font. To make every visitor see Poppins, download it from Google Fonts into `assets/` and add an `@font-face` rule.

## Newsletter

A static site cannot store email addresses, so the sign-up box hands the address to a newsletter service. The site is prepared for Kit (formerly ConvertKit), but any service that gives you a form address will work.

- **What to do:** paste the form's address into `newsletter.formAction` in `content.js`. It must be a full address starting with `https://`.
- **Which value from Kit:** create a form in Kit, choose to embed it as HTML, and in the code Kit shows look for `<form action="...">`. The address inside those quotes is the value. It is expected to look like `https://app.kit.com/forms/1234567/subscriptions`. This has not been confirmed against a real Kit account, so check it with one test sign-up after pasting it in.
- **While the value is empty** the sign-up box, the "Newsletter" menu link and the hero button are left out of the site completely. Nothing half-working is shown.
- **Once it is set** the box appears on the home page and at the end of every post and review, and "Newsletter" appears in the menu. The heading, the one-line offer and the thank-you message are `newsletter.heading`, `newsletter.blurb` and `newsletter.thanks` in `content.js`. The current wording is a draft for you to edit.
- After signing up the visitor sees the thank-you message on the page. If the service does not answer in the expected way, the form is sent the ordinary way and the visitor sees the service's own confirmation page instead.

## Contact

The Contact section shows one button with the email address from `contact.email` in `content.js`. Clicking it opens the visitor's email program. The four kinds of inquiry under it (`contact.inquiries`) are short descriptions only. Social profiles can be added to `contact.socials`; the list is empty at present and so is not shown.

## The tab icon

The small "AP" icon in the browser tab comes from the files in `assets/icons/monogram/`. To change it, replace those files with new ones of the same names.

## Settings in build.py

Near the top of `build.py`: `HOME_POSTS` (how many posts the home page shows, 6), `POSTS_PER_PAGE` (posts per page in the blog lists, 20) and `FEED_ITEMS` (posts in the RSS feed, 30).
