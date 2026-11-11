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
| `assets/` | Book covers (from the Amazon.de listings) and the author photo. |
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
- Lines marked `PLACEHOLDER` (email, social profiles, newsletter address) are waiting for your details.
- **Empty means hidden.** While a value is `""` or a list is `[]`, that part of the page does not appear. The Newsletter, Writing elsewhere, Events and Press, and Contact sections are all switched off this way. Fill one in and it appears, together with its menu link where it has one.
- **Books not yet for sale.** A book in the `books` list may carry the optional line `status: "Coming soon",`. Its card then shows that label and no buy button, and an empty `blurb` and `buyLinks` leave no gap. "The Own the Whole Market Workbook" is set up this way, with a placeholder cover (`assets/own-the-whole-market-workbook-placeholder.svg`). Once the book is live: put the real cover in `assets/` and point `cover` at it, add the `blurb` and the buy link, and delete the `status` line.
- Dates use `YYYY-MM-DD`. Events sort themselves into Upcoming and Past.
- A link without a real `https://` address is never shown as a link.

## Blog posts and book reviews

Each post is one file in `posts/` named `YYYY-MM-DD-short-title.md`. The top of the file holds a few labelled lines (title, date, type, tags, summary, and for reviews the book's title, author and an optional rating), followed by the text. `BOT_GUIDE.md` has the full rules and two complete examples. You can add posts by hand in exactly the same way the bot does.

The build checks every post. If one is malformed (a missing field, a wrong date, a misspelt field name, a bad file name) the build stops, names the file and the problem, and publishes nothing, so the live site stays as it was. Any HTML typed into a post is shown as plain text and never run, so a post cannot inject scripts into the site.

The first ten posts are book reviews dated weekly from 7 September to 9 November 2026. They were drafted with AI assistance and should be read over by the author.

## Publishing

The site is designed for GitHub Pages:

1. Put this folder in a GitHub repository, on a branch called `main`.
2. On GitHub: Settings, then Pages, then under "Build and deployment" set Source to **GitHub Actions**.
3. From then on, every push to `main` runs the "Publish site" workflow, which runs `build.py` and publishes `_site/`. The site appears at `https://<username>.github.io/<repo-name>/` (or at your own domain if you set one up in the Pages settings).

The bot only needs permission to add files to the repository. It commits one new file to `posts/` each day and the workflow does the rest. If a build fails, the Actions tab on GitHub shows the message, and GitHub emails the repository owner.

This is already set up:

- Repository (public): <https://github.com/leduap/ashok-paudel-author-site>
- Copy it with: `git clone https://github.com/leduap/ashok-paudel-author-site.git`
- Live site: <https://leduap.github.io/ashok-paudel-author-site/>

## Images

Put your files in `assets/` and point to them from `content.js`, for example `photo: "assets/author-photo.jpg"` or `cover: "assets/my-book.jpg"`. Covers look best at a 2:3 shape; the photo is shown as a square, cropped around the centre.

## Colours

The theme matches the "Inside FP&A" paperback cover and is set by the variables at the top of `styles.css`. The values were sampled from the cover: the pale mint gradient (`--mint-light`, `--mint`, `--mint-deep`), the deep teal name band (`--band`), the navy title colour (`--navy`), the greens of the labels and subtitle (`--green-label`, `--green-bright`) and the chart-bar accents (`--bar-teal`, `--bar-aqua`, `--bar-orange`, `--bar-yellow`). Change those variables to re-tint the whole site, blog included.

Headings use the font stack in `--display`. It names Poppins first, which is the closest match to the cover title, but the site does not load it: visitors see it only if it is installed on their device, and otherwise get Avenir Next or the nearest system font. To make every visitor see Poppins, download it from Google Fonts into `assets/` and add an `@font-face` rule.

## Newsletter

A static site cannot store email addresses. Sign up with a provider (Buttondown, Mailchimp, and so on), copy the form address it gives you, and paste it into `newsletter.formAction` in `content.js`. Until then the signup box and its menu link are hidden. Once set, the box appears on the home page and at the end of every blog page.

## Settings in build.py

Near the top of `build.py`: `HOME_POSTS` (how many posts the home page shows, 6), `POSTS_PER_PAGE` (posts per page in the blog lists, 20) and `FEED_ITEMS` (posts in the RSS feed, 30).
