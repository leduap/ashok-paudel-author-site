// ---------------------------------------------------------------------------
// ALL SITE-WIDE CONTENT LIVES IN THIS FILE.
// Edit the text between the quotes and save.
//
// Blog posts and book reviews do NOT go here: each one is its own file in the
// posts/ folder (see BOT_GUIDE.md).
//
// Anything marked PLACEHOLDER is waiting for your real details. While a value
// is empty ("") or a list is empty ([]), that part of the page is hidden, so
// visitors never see anything unfinished. Fill it in and it appears.
//
// Keep each piece of text on one line, inside double quotes.
// ---------------------------------------------------------------------------

const SITE = {
  name: "Ashok Paudel",

  // Shown next to your name. As printed on the book covers. Leave "" to hide.
  credentials: "CPA, MBA",

  // The big line at the top of the home page: one sentence saying what readers get.
  headline: "Finance, made simple.",

  // The smaller green line under it.
  // DRAFT written from the book listings. Change it to your own words.
  tagline: "Plain-English books on investing, options and corporate finance.",

  // "About" text. Each item is one paragraph.
  // This is the "About the author" text from the back cover of Inside FP&A, word for word.
  bio: [
    "Ashok Paudel is a senior finance professional holding CPA and MBA credentials. He has spent years in management consulting and corporate finance, building forecasts, closing the books and helping leaders make better decisions with numbers. He writes plain, practical guides that turn complex finance into steps anyone can use."
  ],

  // Your own photo. It is shown as a square, cropped around the centre.
  photo: "assets/author-photo.jpg",

  // The line in the footer of every page. Leave "" to remove it.
  disclaimer: "The views expressed on this site are the author's own. Nothing here is financial, investment, tax or legal advice.",

  // Titles, covers and descriptions are taken from the Amazon.de listings (November 2026).
  // Blurbs are shortened from the published descriptions.
  //
  // Optional: status. For a book that is not for sale yet, add the line
  //   status: "Coming soon",
  // The card then shows that label and no buy button. Leave blurb as "" and
  // buyLinks as [] until they exist. Published books have no status line.
  books: [
    {
      title: "Rolling, Repair and Risk",
      subtitle: "The Wheel Strategy Playbook for Real Markets",
      cover: "assets/rolling-repair-and-risk.jpg",
      blurb: "Most wheel trades end quietly. This book is about the ones that do not. A practical guide to rolling, repairing stuck positions and managing risk, for readers who already know how the wheel works.",
      buyLinks: [{ label: "Buy on Amazon", url: "https://www.amazon.de/dp/B0HQVRJQ1P" }]
    },
    {
      title: "Own the Whole Market",
      subtitle: "A Plain-English Playbook for Building Wealth with Low-Cost Index Funds, from First Paycheck to Financial Freedom",
      cover: "assets/own-the-whole-market.jpg",
      blurb: "Most people are never taught how money actually grows. This book fixes that in plain English, with real data and worked numbers, and without hype, from your first paycheck to the day your investments can pay for your life.",
      buyLinks: [{ label: "Buy on Amazon", url: "https://www.amazon.de/dp/B0HQVWGD1R" }]
    },
    {
      // NOT YET PUBLISHED. The cover is a placeholder and there is no description yet.
      // When the book is live: point cover at the real cover file, fill in blurb,
      // add the buy link, and delete the status line.
      title: "The Own the Whole Market Workbook",
      subtitle: "Build Your Money System: Worksheets, Trackers and Checklists for Every Stage, from First Paycheck to Financial Freedom",
      cover: "assets/own-the-whole-market-workbook-placeholder.svg",
      status: "Coming soon",
      blurb: "",
      buyLinks: []
    },
    {
      title: "The Mindful Grid",
      subtitle: "365 Sudokus & 365 Questions for the Soul",
      cover: "assets/the-mindful-grid.jpg",
      blurb: "A daily ritual for the mindful thinker: one Sudoku to focus your attention and one open-ended question for reflection, every day for a year. Questions are presented in English, German, Spanish, French and Italian.",
      buyLinks: [{ label: "Buy on Amazon", url: "https://www.amazon.de/dp/B0HQP95S6B" }]
    },
    {
      title: "The Wheel Strategy",
      subtitle: "From Zero to Hero",
      cover: "assets/the-wheel-strategy.jpg",
      blurb: "The wheel options strategy explained from zero. You do not need to know what an option is. The book walks through the wheel one step at a time, with order tickets, payoff tables and worked examples, including the parts that are easy to get wrong.",
      buyLinks: [{ label: "Buy on Amazon", url: "https://www.amazon.de/dp/B0HQPBQVBJ" }]
    },
    {
      title: "Inside FP&A",
      subtitle: "How Planning, Forecasting and Analysis Really Work in Large Companies",
      cover: "assets/inside-fpa.jpg",
      blurb: "FP&A is learned on the job, one deadline at a time. Follow one fictional company through a full planning year, from the plan and the forecast call to the board pack, with worked numbers that tie out from chapter to chapter.",
      buyLinks: [{ label: "Buy on Amazon", url: "https://www.amazon.de/dp/B0HQW1LKZB" }]
    }
  ],

  // -------------------------------------------------------------------------
  // The four parts below are SWITCHED OFF because there is nothing real to show
  // yet. Each one appears on the home page as soon as you fill it in.
  // -------------------------------------------------------------------------

  // "Writing elsewhere": articles published on other sites or in magazines.
  // (Your own blog posts are separate: they live in the posts/ folder.)
  // To switch on, add lines like the example between the square brackets.
  // Dates use the form YYYY-MM-DD.
  articles: [
    // { title: "Article title", outlet: "Publication", date: "2026-10-01", url: "https://..." },
  ],

  // Events. Upcoming ones are shown first; past ones move below automatically.
  events: [
    // { title: "Book reading and signing", date: "2027-02-14", location: "Venue, City", url: "https://..." },
  ],

  // Press. Only add real quotes with their real source.
  press: {
    // Link to a PDF or folder with your bio, photos and book details. Leave "" to hide.
    kitUrl: "",
    mentions: [
      // { quote: "A short quote from a review or interview.", source: "Publication", url: "https://..." },
    ]
  },

  // Newsletter. The signup box and the "Newsletter" menu link stay hidden until formAction is filled in.
  newsletter: {
    // DRAFT. Tell readers what they get and how often.
    blurb: "New posts, book reviews and book news by email.",
    // PLACEHOLDER: paste the https:// form address from your newsletter provider (Buttondown, Mailchimp, etc.).
    formAction: ""
  },

  // Contact. The contact section stays hidden until there is an email address or at least one profile link.
  contact: {
    // PLACEHOLDER: the address readers and press should write to, e.g. "hello@yourdomain.com".
    email: "",
    // PLACEHOLDER: your real profiles. Remove the // in front of a line and put in the full address.
    socials: [
      { label: "LinkedIn", url: "https://www.linkedin.com/in/paudela/" },
      // { label: "Goodreads", url: "https://www.goodreads.com/author/show/..." },
      // { label: "Amazon author page", url: "https://www.amazon.de/..." },
    ],

    // The kinds of request people can send you, shown as cards in the contact section.
    // Each card's button opens an email with the subject filled in. While no email
    // address is set above, the button links to your first profile (LinkedIn) instead.
    // Remove a card by deleting its line; leave the list empty ([]) to show none.
    inquiries: [
      { title: "Press and media", text: "Interview requests, quotes and review copies.", subject: "Press inquiry" },
      { title: "Speaking engagements", text: "Talks, workshops and panels on investing and corporate finance.", subject: "Speaking inquiry" },
      { title: "Podcasts and guest articles", text: "Podcast appearances and guest contributions.", subject: "Podcast or guest article inquiry" },
      { title: "Bulk orders and rights", text: "Bulk and corporate orders, translation and other rights.", subject: "Bulk order or rights inquiry" }
    ]
  }
};
