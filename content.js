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
  // The first two sentences are the agreed wording and stay as they are. Never add an
  // employer, a job title or a claim about past projects here or anywhere else on the site.
  bio: [
    "Ashok Paudel (CPA, MBA) is a finance professional based in Munich, Germany. His commentary has appeared in Fortune.",
    "He writes plain-English books on investing, options and corporate finance, including Own the Whole Market, The Wheel Strategy series and Inside FP&A, and reviews books on money and business on this site."
  ],

  // Where he is based, as it appears in the bio. Used in the structured data on the home page.
  location: "Munich, Germany",

  // His own public profiles, used for the sameAs list in the structured data and shown on the
  // Contact page. Only profiles that exist and are his. Never add a profile of another person
  // of the same name. Add the Amazon author page here once it is set up in Author Central.
  profiles: [
    { label: "LinkedIn", url: "https://www.linkedin.com/in/paudela" },
    { label: "Fortune", url: "https://fortune.com/author/ashok-paudel/" }
  ],

  // Your own photo. It is shown as a square, cropped around the centre.
  photo: "assets/author-photo.jpg",

  // The line in the footer of every page. Leave "" to remove it.
  disclaimer: "The views expressed on this site are the author's own. Nothing here is financial, investment, tax or legal advice.",

  // Amazon affiliate links (Amazon Associates).
  // The three tags below are the ONLY place your Associates tags are written.
  // The site adds the right tag to every Amazon link it makes: the buy buttons
  // on your own books and the "Get the book" buttons on reviews. To change a tag,
  // change it here. To switch a store off, set its tag to "".
  // disclosure is the line Amazon requires; it is shown in the footer of every page and,
  // on book reviews, again near the top, just above the store buttons.
  // note is the sentence shown straight after it on review pages.
  affiliate: {
    disclosure: "As an Amazon Associate I earn from qualifying purchases.",
    note: "The Amazon buttons on this page are affiliate links: if you buy through them I may earn a small commission, at no extra cost to you.",
    amazon: {
      us: "remotelyscale-20",
      uk: "remotelyscale-21",
      de: "remotelysca08-21"
    }
  },

  // Titles, covers and descriptions are taken from the Amazon.de listings (November 2026).
  // Covers were last checked against amazon.com and amazon.de on 15 November 2026.
  // Blurbs are shortened from the published descriptions.
  //
  // Optional: status. For a book that is not for sale yet, add the line
  //   status: "Coming soon",
  // The card then shows that label and no buy button. Leave blurb as "" and
  // amazonId as "" until they exist. Published books have no status line.
  //
  // amazonId is the 10-character Amazon code of the book (the part after /dp/
  // in its Amazon address). The card then shows "Buy on Amazon" buttons for the
  // US, UK and German stores, each carrying your affiliate tag from above.
  // Each code below was checked on amazon.com, amazon.co.uk and amazon.de (November 2026).
  // Optional: buyLinks, for shops other than Amazon, e.g.
  //   buyLinks: [{ label: "Buy from the publisher", url: "https://..." }]
  //
  // group decides which row of the Books section a book appears in: one of the
  // ids in bookGroups below. series is the small label above the title, e.g. "Book 2".
  // Within a row, books appear in the order they are listed here.
  //
  // Every published book also gets its own page at /books/<title-as-a-slug>/, built from
  // the lines below. topics lists blog tags (comma separated) whose reviews and posts are
  // linked from that page as further reading. Leave it "" for none.
  bookGroups: [
    { id: "wheel", title: "The Wheel Strategy series", text: "Selling options for income, one step at a time. Read them in order." },
    { id: "finance", title: "Investing and corporate finance", text: "" },
    { id: "other", title: "Other books", text: "" }
  ],

  books: [
    {
      group: "wheel",
      series: "Book 1 · Start here",
      title: "The Wheel Strategy",
      subtitle: "From Zero to Hero",
      cover: "assets/the-wheel-strategy.jpg",
      blurb: "The wheel options strategy explained from zero. You do not need to know what an option is. The book walks through the wheel one step at a time, with order tickets, payoff tables and worked examples, including the parts that are easy to get wrong.",
      amazonId: "B0HQPBQVBJ",
      topics: "options, investing"
    },
    {
      group: "wheel",
      series: "Book 2",
      title: "Rolling, Repair and Risk",
      subtitle: "The Wheel Strategy Playbook for Real Markets",
      cover: "assets/rolling-repair-and-risk.jpg",
      blurb: "Most wheel trades end quietly. This book is about the ones that do not. A practical guide to rolling, repairing stuck positions and managing risk, for readers who already know how the wheel works.",
      amazonId: "B0HQVRJQ1P",
      topics: "options, investing"
    },
    {
      group: "wheel",
      series: "Book 3",
      title: "LEAPS and the Poor Man's Covered Call",
      subtitle: "The Wheel Strategy Playbook for Smaller Accounts",
      cover: "assets/leaps-and-the-poor-mans-covered-call.jpg",
      blurb: "A long-dated call, a LEAPS, can stand in for 100 shares at a fraction of the cash. That is the poor man's covered call, and it is a leveraged trade. The book shows the worst case first, then the rules that keep the trade sound, for readers who know the wheel and want to run it with less capital.",
      amazonId: "B0HRRW92Y3",
      topics: "options, investing"
    },
    {
      group: "wheel",
      series: "Book 4",
      title: "Cash-Secured Puts",
      subtitle: "How to Get Paid to Buy Stocks at Your Price",
      cover: "assets/cash-secured-puts.jpg",
      blurb: "A cash-secured put is a promise to buy a stock at a price you choose, and you are paid for making it. Book 4 of The Wheel Strategy series shows how to pick the stock, the price and the strike, ladder puts over time and plan for every outcome, with the downside shown in dollars in every example.",
      amazonId: "B0GX32LW9S",
      topics: "options, investing"
    },
    {
      group: "finance",
      title: "Own the Whole Market",
      subtitle: "A Plain-English Playbook for Building Wealth with Low-Cost Index Funds, from First Paycheck to Financial Freedom",
      cover: "assets/own-the-whole-market.jpg",
      blurb: "Most people are never taught how money actually grows. This book fixes that in plain English, with real data and worked numbers, and without hype, from your first paycheck to the day your investments can pay for your life.",
      amazonId: "B0HRS8HQWT",
      topics: "index funds, investing, personal finance"
    },
    {
      // NOT YET PUBLISHED. The cover is a placeholder and there is no description yet.
      // When the book is live: point cover at the real cover file, fill in blurb,
      // add its amazonId, and delete the status line.
      group: "finance",
      title: "The Own the Whole Market Workbook",
      subtitle: "Build Your Money System: Worksheets, Trackers and Checklists for Every Stage, from First Paycheck to Financial Freedom",
      cover: "assets/own-the-whole-market-workbook-placeholder.svg",
      status: "Coming soon",
      blurb: "",
      amazonId: ""
    },
    {
      group: "finance",
      title: "Inside FP&A",
      subtitle: "How Planning, Forecasting and Analysis Really Work in Large Companies",
      cover: "assets/inside-fpa.jpg",
      blurb: "FP&A is learned on the job, one deadline at a time. Follow one fictional company through a full planning year, from the plan and the forecast call to the board pack, with worked numbers that tie out from chapter to chapter.",
      amazonId: "B0HQW1LKZB",
      topics: "corporate finance, accounting"
    },
    {
      group: "other",
      title: "The Mindful Grid",
      subtitle: "365 Sudokus & 365 Questions for the Soul",
      cover: "assets/the-mindful-grid.jpg",
      blurb: "A daily ritual for the mindful thinker: one Sudoku to focus your attention and one open-ended question for reflection, every day for a year. Questions are presented in English, German, Spanish, French and Italian.",
      amazonId: "B0HQP95S6B",
      topics: ""
    }
  ],

  // Finance templates sold on Gumroad. Names, images and descriptions are taken
  // from the public store listings (November 2026); descriptions are the opening
  // lines of each listing. Prices are left off so they never go out of date.
  // Optional: tag, a small label on the card such as "Free".
  //
  // SWITCHED OFF: the section and its menu link are hidden while show is false.
  // The same switch covers blog posts: while show is false, posts may not link to
  // Gumroad and the build rejects such links.
  // Change false to true to bring the section back.
  templates: {
    show: false,
    storeUrl: "https://financea2z.gumroad.com/",
    items: [
      {
        title: "The Wheel Strategy Guide",
        subtitle: "Cash-Secured Puts & Covered Calls from Zero to Hero (98-page PDF)",
        image: "assets/template-wheel-strategy-guide.png",
        blurb: "Learn the wheel properly, from the first definition to a full year of trades, with numbers that reconcile.",
        url: "https://financea2z.gumroad.com/l/intixr"
      },
      {
        title: "Finance Templates Bundle",
        subtitle: "8 Models",
        image: "assets/template-finance-bundle.png",
        blurb: "Eight finance models in one bundle.",
        url: "https://financea2z.gumroad.com/l/nrjhuq"
      },
      {
        title: "Retirement Millionaire Calculator",
        subtitle: "How Much to Save Each Month to Reach $1 Million (Excel)",
        image: "assets/template-retirement-calculator.png",
        tag: "Free",
        blurb: "How much do you need to save each month to have a million by the time you retire? This free Excel calculator answers that in seconds.",
        url: "https://financea2z.gumroad.com/l/zxcrtz"
      },
      {
        title: "Home Buyer Toolkit",
        subtitle: "How Much House Can I Afford, Rent vs Buy, Closing Costs & Mortgage Amortization (Excel + Google Sheets)",
        image: "assets/template-home-buyer-toolkit.png",
        tag: "Free",
        blurb: "Before you fall for a house, know the price you can carry, the cash you need and whether buying beats renting for you.",
        url: "https://financea2z.gumroad.com/l/lnnfke"
      },
      {
        title: "FP&A Command Center",
        subtitle: "",
        image: "assets/template-fpa-command-center.png",
        blurb: "Paste one month of actuals and get the whole month-end story back.",
        url: "https://financea2z.gumroad.com/l/xxbrrm"
      },
      {
        title: "Small Business Acquisition & SBA Loan Model",
        subtitle: "SDE Recast, Valuation, SBA 7(a) + Seller Note, DSCR, Cash-on-Cash & IRR (Excel + Google Sheets)",
        image: "assets/template-sba-acquisition-model.png",
        blurb: "Know what the business is really earning, what to offer and whether the loan works, before you sign a letter of intent.",
        url: "https://financea2z.gumroad.com/l/bhcdrq"
      },
      {
        title: "Month-End Close Starter Kit",
        subtitle: "",
        image: "assets/template-month-end-close-kit.png",
        tag: "Free",
        blurb: "A free, working starter kit for your month-end close. Download it, open it in Excel and see exactly what is due and what is late.",
        url: "https://financea2z.gumroad.com/l/utrxle"
      }
    ]
  },

  // -------------------------------------------------------------------------
  // Of the parts below, Events, Press and the Newsletter are SWITCHED OFF because
  // there is nothing real to show yet. Each one appears on the home page as soon
  // as you fill it in.
  // -------------------------------------------------------------------------

  // "Writing elsewhere": articles of yours published on other sites or in magazines.
  // (Your own blog posts are separate: they live in the posts/ folder.)
  //
  // Each article is one block between { and }, with four lines:
  //   title   the headline, exactly as the publication printed it
  //   outlet  the name of the publication
  //   date    the day it was published, in the form YYYY-MM-DD
  //   url     the full https:// address of the article, or "" to list it without a link
  // To add the next one, copy a whole block, from { to }, paste it above the
  // first one, and change the four lines. Keep a comma between blocks.
  // The newest article is shown first.
  // While the list is empty the section and its menu link are hidden.
  //
  // The Fortune piece is listed by name only: Ashok has asked that the site does not
  // link to the article itself. Leave its url as "".
  articles: [
    {
      title: "60 million children got Trump Accounts. Fewer than 1% were claimed in the first week",
      outlet: "Fortune",
      date: "2026-11-10",
      url: ""
    }
  ],

  // "For editors": what editors, producers and podcast hosts need before they get in touch.
  // The articles themselves are listed by the build, from the opinion posts and the articles
  // list above. The bios are ready to paste under an article.
  // photo is the headshot offered for download (use a large, sharp file). Leave "" to hide it.
  editors: {
    intro: "Working on a story about investing, saving or corporate finance? Here is recent writing. I also give comment, usually at short notice.",
    shortBio: "Ashok Paudel (CPA, MBA) is a finance professional based in Munich, Germany, and the author of plain-English books on investing and corporate finance, including Own the Whole Market and Inside FP&A. His commentary has appeared in Fortune.",
    longBio: "Ashok Paudel (CPA, MBA) is a finance professional based in Munich, Germany. He is the author of Own the Whole Market, Inside FP&A and The Wheel Strategy series, plain-English guides that turn complex finance into steps anyone can use, and he reviews books on money and business at ashokpaudel.com. His commentary has appeared in Fortune.",
    photo: "assets/author-photo.jpg"
  },

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

  // Newsletter (Kit, formerly ConvertKit).
  // The sign-up box appears on the home page and at the end of every post and review, and a
  // "Newsletter" link appears in the menu. ALL of it stays off the site while formAction is "".
  newsletter: {
    // DRAFT. The heading of the sign-up box.
    heading: "Get new posts by email",
    // DRAFT. One line saying what readers get. Change it to your own words.
    blurb: "New book reviews and plain-English finance posts, sent to your inbox. No spam, and you can unsubscribe at any time.",
    // DRAFT. Shown in place of the form after someone signs up.
    thanks: "Thank you. Please check your inbox and confirm your email address to finish signing up.",
    // PLACEHOLDER: the full https:// address your Kit sign-up form sends to (the "action"
    // address in the form's HTML embed code). See "Newsletter" in README.md.
    formAction: ""
  },

  // Contact. The contact section stays hidden until there is an email address or at least one profile link.
  contact: {
    // The address readers and press should write to. It is shown as the one button in the
    // contact section. Leave "" to hide it.
    email: "hello@ashokpaudel.com",
    // Optional: profile links, shown as small buttons under the contact details.
    // To add one, remove the // in front of a line and put in the full address.
    socials: [
      { label: "LinkedIn", url: "https://www.linkedin.com/in/paudela" },
      // { label: "Goodreads", url: "https://www.goodreads.com/author/show/..." },
    ],

    // The kinds of request people can send you, shown as short descriptions under the button.
    // Remove one by deleting its line; leave the list empty ([]) to show none.
    inquiries: [
      { title: "Press and media", text: "Interview requests, quotes and review copies." },
      { title: "Speaking engagements", text: "Talks, workshops and panels on investing and corporate finance." },
      { title: "Podcasts and guest articles", text: "Podcast appearances and guest contributions." },
      { title: "Bulk orders and rights", text: "Bulk and corporate orders, translation and other rights." }
    ]
  }
};
