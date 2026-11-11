# Guide for the publishing bot

You publish to Ashok Paudel's author site. Your whole job is to **add one markdown file per day** to the `posts/` folder of this repository and commit it to the `main` branch. The site rebuilds and publishes itself. You run nothing.

## The rules

1. **One new file per day.** Each file is either one blog post or one book review.
2. **Add only. Never edit, rename, move or delete any other file**, including earlier posts, `content.js`, `index.html`, `build.py`, `styles.css` and the workflow.
3. Put the file directly in `posts/`. No sub-folders, no images, no other file types.
4. Follow the file name and front matter rules below exactly. If anything is wrong the build fails, **nothing is published**, and the site stays as it was until the file is fixed.
5. Write plain markdown. Do not write HTML: any HTML is shown to readers as literal text, never run.
6. Content rules:
   - Do not give personalised financial advice and do not tell readers to buy, sell or hold any specific security.
   - Do not invent facts, quotes, statistics, awards or events about Ashok Paudel or anyone else.
   - A review describes the book: what it covers, what works, what does not, and who it suits. Quote the book sparingly and accurately.
   - Do not name Ashok Paudel's employer or clients.
   - When a post's subject closely matches one of Ashok's finance templates, you may end with one sentence linking to that template's own page under `https://financea2z.gumroad.com/l/`. At most one such link per post, and only where it fits; most posts will have none. See the existing reviews in `posts/` for examples.

## Where the file goes and what it is called

```
posts/YYYY-MM-DD-short-title.md
```

- `YYYY-MM-DD` is the publication date, for example `2026-11-12`. It must be a real date, must equal the `date` field inside the file, and must not be in the future.
- `short-title` uses only lower-case letters `a-z`, digits `0-9` and single hyphens. No spaces, capitals, underscores or accents.
- The extension is `.md`.
- The file name becomes the page address: `posts/2026-11-12-reading-a-cash-flow-statement.md` is published at `/blog/2026-11-12-reading-a-cash-flow-statement/`. Never reuse a file name.

## What goes in the file

The file starts with front matter: a line containing only `---`, then one `field: value` per line, then another line containing only `---`. After that comes the body in markdown.

Front matter is deliberately simple. It is **not** full YAML:

- one field per line, written `field: value`; values never continue onto a second line
- quotes around a value are optional and are removed; colons inside the value are fine
- no nesting, no lists with dashes, no multi-line text

### Fields

| Field | Required | Allowed values |
| --- | --- | --- |
| `title` | always | Plain text, at most 120 characters. No markdown. |
| `date` | always | `YYYY-MM-DD`. Must match the date in the file name. Not in the future. |
| `type` | always | Exactly `post` or `review`. |
| `tags` | always | 1 to 5 tags separated by commas, e.g. `investing, index funds`. Each tag: lower-case letters, digits, single spaces or hyphens, at most 30 characters. |
| `summary` | always | One or two plain sentences, at most 220 characters. Shown in the blog list, on the home page, in search results and in the RSS feed. No markdown. |
| `book_title` | when `type` is `review` | Title of the book reviewed. Not allowed on a `post`. |
| `book_author` | when `type` is `review` | Author of the book reviewed. Not allowed on a `post`. |
| `rating` | optional, reviews only | A whole number `1`, `2`, `3`, `4` or `5`. Leave the line out for no rating. Not allowed on a `post`. |

Any other field name is rejected, so a misspelt field (such as `sumary`) fails the build rather than being silently ignored.

### Tags

Prefer these tags so the archive stays tidy, and reuse existing ones before inventing new ones:

`investing`, `index funds`, `options`, `corporate finance`, `fpa`, `forecasting`, `accounting`, `personal finance`, `behaviour`, `careers`, `books`

### Body

Standard markdown, limited to what the site supports:

- paragraphs separated by a blank line
- headings with `##`, `###` or `####` (the title is the page's only top-level heading; a single `#` is treated as `##`)
- `**bold**`, `*italic*`, `` `code` ``
- links: `[text](https://example.com)`. Only `http://`, `https://`, `mailto:` and relative links are kept; any other kind is dropped and only the text is shown
- bullet lists with `-` and numbered lists with `1.`
- quotations with `>`
- simple tables with `|` and a `| --- | --- |` line under the header row
- code blocks fenced with three backticks
- a horizontal rule with `---` on its own line (in the body only)
- images: `![description](https://...)`, `https://` addresses only. Prefer not to use images

Do not repeat the title at the top of the body; the site adds it. The body must not be empty.

## Complete example: a book review

File: `posts/2026-11-12-review-the-example-book.md`

```markdown
---
title: Review: The Example Book by A. N. Author
date: 2026-11-12
type: review
tags: books, personal finance
summary: A short, practical introduction to household budgeting. Clear on the basics, thin on investing.
book_title: The Example Book
book_author: A. N. Author
rating: 4
---

The Example Book is a 200-page introduction to household budgeting, written for readers who have never kept a budget.

## What the book covers

The first half explains how to track spending for a month. The second half turns that record into a simple plan.

## What works

- Every chapter ends with a one-page worksheet.
- The examples use small, realistic numbers.

## What to be aware of

The chapter on investing is brief and stays at the level of definitions.

## Who should read it

Readers who want a first budget will get the most from it. Readers who already keep one will find little that is new.
```

## Complete example: a blog post

File: `posts/2026-11-13-budget-forecast-and-actuals.md`

```markdown
---
title: Budget, forecast and actuals: what each word means
date: 2026-11-13
type: post
tags: corporate finance, forecasting
summary: Three words appear in every finance meeting. Here is what each one means and how they fit together.
---

Three words appear in almost every finance meeting: budget, forecast and actuals.

## The budget

The budget is the plan for the year, agreed before the year starts. It does not change.

## The forecast

The forecast is the latest estimate of how the year will really turn out. It is updated as the year goes on.

## Actuals

Actuals are what has already happened, as recorded in the books.

| Term | Answers the question |
| --- | --- |
| Budget | What did we plan? |
| Forecast | What do we now expect? |
| Actuals | What has happened so far? |

The difference between any two of these is called a **variance**.
```

## Before you commit: checklist

- [ ] Exactly one new file, in `posts/`, named `YYYY-MM-DD-short-title.md`
- [ ] First line is `---`; front matter is closed by a second `---`
- [ ] `title`, `date`, `type`, `tags` and `summary` are all present and not empty
- [ ] `date` equals the date in the file name and is today's date
- [ ] `type` is `post` or `review`; a review also has `book_title` and `book_author`
- [ ] `rating`, if present, is a whole number from 1 to 5 and the file is a review
- [ ] The body is markdown, has no HTML, and does not repeat the title
- [ ] No other file in the repository was changed

## What happens after the commit

Each push to `main` starts the "Publish site" workflow. It runs `python3 build.py`, which checks every file in `posts/`, turns each one into a web page, and updates the blog index, the home page's latest posts and the RSS feed. If a file breaks a rule, the workflow fails with a message that names the file and the problem, for example:

```
BUILD FAILED. Nothing was published. Fix the following and try again:
  - posts/2026-11-12-my-post.md: required field 'summary' is missing or empty
```

A failed build blocks every later post too, until the faulty file is corrected. If you can read the workflow result, check that it succeeded after each commit.
