# Getting the site found: what the code does and what only you can do

The site is new to Google and Bing (Search Console began recording impressions on 14 November 2026). A new site is normal to find nowhere for the first weeks. Everything the code can do for search engines is now built in; the steps below are the ones that need you, because they happen in accounts only you can log in to.

## What is already handled by the build

- Every page has one address, always `https://ashokpaudel.com/…/` with a trailing slash, and says so in its `<link rel="canonical">`. `www.`, `http://` and the old `leduap.github.io` address all redirect (301) to it. Search Console's "Page with redirect" notice is about those alias addresses, not about a fault: Google found a link to the `www` or `http://` form, followed it, and reports that it was redirected. That is the correct behaviour and needs no action. Make sure any link you post elsewhere uses `https://ashokpaudel.com/` so the notices do not multiply.
- `sitemap.xml` lists every indexable page with a `lastmod` date, `robots.txt` points to it, and there is an RSS feed at `/feed.xml`.
- The books, your biography and the contact details are written into the HTML by the build (not added by JavaScript), so crawlers read them directly.
- Each published book has its own page (`/books/own-the-whole-market/`, `/books/the-wheel-strategy/` and so on) with Book structured data, the Amazon links and the rest of its series. Each review carries Review and Book structured data; each opinion piece carries BlogPosting data; every page carries a breadcrumb trail.
- There is a 404 page, a favicon at the site root, and per-page Open Graph and Twitter tags.
- Tag pages with only one post are marked `noindex` so they do not compete with the post itself.

## Do once, now

1. **Google Search Console** (search.google.com/search-console), property `https://ashokpaudel.com/` (or the Domain property for `ashokpaudel.com`).
   - Sitemaps → add `https://ashokpaudel.com/sitemap.xml`.
   - URL inspection → paste each of these and click *Request indexing* (a few a day is enough; Google rate-limits the button):
     - `https://ashokpaudel.com/`
     - `https://ashokpaudel.com/about/`
     - `https://ashokpaudel.com/books/`
     - `https://ashokpaudel.com/books/own-the-whole-market/`
     - `https://ashokpaudel.com/books/the-wheel-strategy/`
     - `https://ashokpaudel.com/books/inside-fpa/`
     - `https://ashokpaudel.com/blog/reviews/`
     - `https://ashokpaudel.com/blog/opinion/`
     - the two or three newest reviews and opinion pieces
   - Pages report → the "Page with redirect" entries should list `www.` or `http://` addresses. If any entry is a plain `https://ashokpaudel.com/…/` address, send it to me.
2. **Bing Webmaster Tools** (bing.com/webmasters). Use *Import from Google Search Console* to verify in one click, then submit the same sitemap. Bing's index is also used by DuckDuckGo and other search tools, so this is not optional.
3. **Check the structured data** once the site has redeployed: paste `https://ashokpaudel.com/books/own-the-whole-market/` and one review into search.google.com/test/rich-results and validator.schema.org. Both should report no errors. (The reviews carry no star ratings on purpose; without a rating Google will not show review stars, and inventing ratings is not an option.)

## Links to the site from places you already control

Search engines rank a new site by who links to it. Each of these is a real profile of yours and takes a few minutes:

- **LinkedIn** (linkedin.com/in/paudela): add `https://ashokpaudel.com/` as the website on your profile, and in the About section. Share the newest opinion piece or review as a post from time to time with its full address.
- **Amazon Author Central** (author.amazon.com): the author page is `https://www.amazon.com/author/ashokpaudel`, and that address is already in `profiles` in `content.js`. Add the site address to the Amazon bio, and make sure all seven books are attached to the page.
- **The books themselves**: put `ashokpaudel.com` on the "About the author" page of each Kindle and paperback edition (a KDP re-upload of the interior is free), and in the Amazon book descriptions where Amazon's rules allow a plain mention.
- **X / Twitter, Goodreads, Medium, Substack** or any other profile that is actually yours: add the website field. Then add the address to `profiles` in `content.js`. Do not add profiles of other people called Ashok Paudel.
- **Fortune**: the author page `fortune.com/author/ashok-paudel/` already links back to Fortune's own pages. If Fortune lets contributors add a website, add it.
- **Email signature**: a one-line link to the site.

## Keep publishing, and keep the names consistent

- Use the same name everywhere: *Ashok Paudel, CPA, MBA*. Search engines connect profiles by matching the name, photo and links.
- Google treats a site that is updated regularly as worth crawling more often. The one-post-a-day routine is exactly right; keep it going.
- When you publish elsewhere (Fortune or another outlet), ask the editor to include the site address in the author line where the publication allows it.

## What to expect

- Week 1 to 2 after submitting the sitemap: the home page and a handful of pages appear for a search on `ashokpaudel.com` and, usually, for `"Ashok Paudel" author`.
- Weeks 3 to 8: book pages begin to show for the exact titles, and reviews for `"<book title>" review`. Competing for the title of a well-known book (The Psychology of Money, for instance) takes much longer; the reviews mainly help by showing Google the site is about money books.
- Searches for `Ashok Paudel` alone: the site competes with other people of the same name on LinkedIn and elsewhere. The LinkedIn link, the Amazon author page and the consistent name are what move this.

## Things that are deliberately not on the site

- No employer, job title, former employers or project claims anywhere, including inside opinion pieces. The build does not check this automatically, so when adding or publishing a piece, read it once for such mentions.
- The Fortune article is linked from "Featured in Fortune" and from the writing list. Do not copy the article's text onto the site.
- No invented ratings, awards, quotes or profiles.
