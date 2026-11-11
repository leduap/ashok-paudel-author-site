// Reads SITE from content.js and fills in the page.
// You should not need to edit this file to change content.

(function () {
  "use strict";

  function $(id) { return document.getElementById(id); }

  // Build an element: el("a", { href: "#", className: "x" }, "text" or [children])
  function el(tag, props, children) {
    var node = document.createElement(tag);
    Object.keys(props || {}).forEach(function (key) { node[key] = props[key]; });
    [].concat(children || []).forEach(function (child) {
      node.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
    });
    return node;
  }

  function link(label, url, className) {
    // Without a real address the label is shown as plain text, never as a dead link.
    if (!isRealUrl(url)) { return el("span", { className: className || "" }, label); }
    var a = el("a", { href: url, className: className || "" }, label);
    a.target = "_blank";
    a.rel = "noopener";
    return a;
  }

  // Amazon affiliate links. The tags live only in content.js (affiliate.amazon).
  // A store with no tag gets no link, so the site never shows an untagged Amazon link.
  var AMAZON_STORES = [
    { key: "us", host: "www.amazon.com", label: "US" },
    { key: "uk", host: "www.amazon.co.uk", label: "UK" },
    { key: "de", host: "www.amazon.de", label: "Germany" }
  ];
  function amazonLinks(id, title) {
    var tags = (SITE.affiliate || {}).amazon || {};
    if (!/^[A-Z0-9]{10}$/.test(id || "")) { return []; }
    return AMAZON_STORES.filter(function (store) {
      return /^[A-Za-z0-9-]+$/.test(tags[store.key] || "");
    }).map(function (store) {
      var a = el("a", {
        href: "https://" + store.host + "/dp/" + id + "?tag=" + tags[store.key],
        className: "button button-small"
      }, store.label);
      a.target = "_blank";
      a.rel = "sponsored nofollow noopener";
      a.setAttribute("aria-label", "Buy " + title + " on Amazon " + store.label + " (affiliate link, opens in a new tab)");
      return a;
    });
  }

  // Dates are written YYYY-MM-DD and treated as local dates.
  function parseDate(text) {
    var parts = String(text || "").split("-").map(Number);
    return new Date(parts[0], (parts[1] || 1) - 1, parts[2] || 1);
  }

  function formatDate(text) {
    var date = parseDate(text);
    if (isNaN(date)) { return text || ""; }
    return date.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
  }

  function lookup(path) {
    return path.split(".").reduce(function (obj, key) { return obj ? obj[key] : undefined; }, SITE);
  }

  // Optional sections start hidden in index.html and are shown only when they have real content.
  function showSection(id, show) {
    $(id).hidden = !show;
    document.querySelectorAll('[data-nav="' + id + '"]').forEach(function (navLink) { navLink.hidden = !show; });
  }

  // A real web address: placeholders such as "#", "" or "TODO" do not count.
  function isRealUrl(url) { return /^https?:\/\/[^\s.]+\.\S+$/.test(url || "") && !/\.\.\.|TODO/.test(url); }
  function isRealEmail(email) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email || "") && !/TODO|example\.com$/i.test(email); }

  // Simple text fields
  document.querySelectorAll("[data-text]").forEach(function (node) {
    var value = lookup(node.getAttribute("data-text"));
    if (typeof value === "string") { node.textContent = value; }
  });
  document.title = SITE.name + " | Finance author";
  $("eyebrow").textContent = [SITE.name, SITE.credentials].filter(Boolean).join(" · ");
  $("year").textContent = String(new Date().getFullYear());

  // Bio and photo
  (SITE.bio || []).forEach(function (paragraph) { $("bio").appendChild(el("p", {}, paragraph)); });
  if (SITE.photo) { $("photo").src = SITE.photo; }
  $("photo").alt = "Portrait of " + SITE.name;

  // Books
  var books = SITE.books || [];
  showSection("books", books.length > 0);
  books.forEach(function (book) {
    // A book with a status (e.g. "Coming soon") is not for sale yet: it gets a label and no buy button.
    var status = String(book.status || "").trim();
    var parts = [];
    if (status) { parts.push(el("p", { className: "book-status" }, status)); }
    parts.push(el("h3", {}, book.title));
    if (book.subtitle) { parts.push(el("p", { className: "subtitle" }, book.subtitle)); }
    // Empty parts are left out altogether, so they leave no gap.
    if (book.blurb) { parts.push(el("p", { className: "blurb" }, book.blurb)); }
    var buyButtons = status ? [] : (book.buyLinks || []).map(function (buy) {
      return isRealUrl(buy.url) ? link(buy.label, buy.url, "button button-small") : null;
    }).filter(Boolean);
    // Amazon buttons, one per store, each carrying the affiliate tag from content.js.
    var amazonButtons = status ? [] : amazonLinks(book.amazonId, book.title);
    if (amazonButtons.length) {
      parts.push(el("div", { className: "buy buy-amazon" },
        [el("span", { className: "buy-label" }, "Buy on Amazon")].concat(amazonButtons)));
    }
    if (buyButtons.length) {
      parts.push(el("div", { className: amazonButtons.length ? "buy buy-more" : "buy" }, buyButtons));
    }
    $("book-list").appendChild(el("article", { className: "book" }, [
      el("img", { src: book.cover, alt: "Cover of " + book.title, loading: "lazy" }),
      el("div", { className: "book-body" }, parts)
    ]));
  });

  // Finance templates (sold on Gumroad)
  var templates = SITE.templates || {};
  var templateItems = templates.show === false ? [] :
    (templates.items || []).filter(function (item) { return isRealUrl(item.url); });
  showSection("templates", templateItems.length > 0);
  templateItems.forEach(function (item) {
    var free = /^free$/i.test(String(item.tag || "").trim());
    var parts = [];
    if (item.tag) { parts.push(el("p", { className: "book-status" }, item.tag)); }
    parts.push(el("h3", {}, item.title));
    if (item.subtitle) { parts.push(el("p", { className: "subtitle" }, item.subtitle)); }
    if (item.blurb) { parts.push(el("p", { className: "blurb" }, item.blurb)); }
    parts.push(el("div", { className: "buy" }, [
      link(free ? "Get it free on Gumroad" : "Get it on Gumroad", item.url, "button button-small")
    ]));
    $("template-list").appendChild(el("article", { className: "book template" }, [
      el("img", { src: item.image, alt: "Preview of " + item.title, loading: "lazy" }),
      el("div", { className: "book-body" }, parts)
    ]));
  });
  var hasStore = isRealUrl(templates.storeUrl);
  if (hasStore) { $("store-link").href = templates.storeUrl; }
  $("store-line").hidden = !hasStore;

  // Articles, newest first
  var articles = (SITE.articles || []).slice().sort(function (a, b) {
    return parseDate(b.date) - parseDate(a.date);
  });
  showSection("writing", articles.length > 0);
  articles.forEach(function (article) {
    $("article-list").appendChild(el("li", {}, [
      link(article.title, article.url, "title"),
      el("span", { className: "meta" }, [article.outlet, formatDate(article.date)].filter(Boolean).join(" · "))
    ]));
  });

  // Events: upcoming soonest first, past most recent first
  var today = new Date();
  today.setHours(0, 0, 0, 0);
  var events = SITE.events || [];
  var upcoming = events.filter(function (e) { return parseDate(e.date) >= today; })
    .sort(function (a, b) { return parseDate(a.date) - parseDate(b.date); });
  var past = events.filter(function (e) { return parseDate(e.date) < today; })
    .sort(function (a, b) { return parseDate(b.date) - parseDate(a.date); });

  function eventRow(event) {
    return el("li", {}, [
      link(event.title, event.url, "title"),
      el("span", { className: "meta" }, [formatDate(event.date), event.location].filter(Boolean).join(" · "))
    ]);
  }
  upcoming.forEach(function (event) { $("upcoming-list").appendChild(eventRow(event)); });
  past.forEach(function (event) { $("past-list").appendChild(eventRow(event)); });
  $("upcoming-block").hidden = !upcoming.length;
  $("past-block").hidden = !past.length;

  // Press
  var press = SITE.press || {};
  var mentions = press.mentions || [];
  mentions.forEach(function (mention) {
    $("press-list").appendChild(el("blockquote", {}, [
      el("p", {}, "\u201C" + mention.quote + "\u201D"),
      el("cite", {}, mention.url ? [link(mention.source, mention.url)] : mention.source)
    ]));
  });
  var hasKit = isRealUrl(press.kitUrl);
  if (hasKit) { $("kit-link").href = press.kitUrl; }
  $("kit-line").hidden = !hasKit;
  $("press-block").hidden = !mentions.length && !hasKit;
  showSection("events", events.length > 0 || !$("press-block").hidden);

  // Newsletter: shown only once a provider address is set in content.js
  var newsletter = SITE.newsletter || {};
  var hasNewsletter = /^https:\/\/\S+$/.test(newsletter.formAction || "");
  if (hasNewsletter) { $("signup-form").action = newsletter.formAction; }
  showSection("newsletter", hasNewsletter);

  // Contact: shown only when there is a real email address or at least one real profile link
  var contact = SITE.contact || {};
  var hasEmail = isRealEmail(contact.email);
  if (hasEmail) {
    $("email-link").textContent = contact.email;
    $("email-link").href = "mailto:" + contact.email;
  }
  $("email-line").hidden = !hasEmail;
  var socials = (contact.socials || []).filter(function (social) { return isRealUrl(social.url); });
  socials.forEach(function (social) {
    $("social-list").appendChild(el("li", {}, [link(social.label, social.url, "button button-quiet button-small")]));
  });
  // Inquiry cards: each button opens an email with the subject filled in, or,
  // while no email address is set, links to the first profile instead.
  var inquiries = (hasEmail || socials.length > 0) ? (contact.inquiries || []) : [];
  inquiries.forEach(function (inquiry) {
    var button;
    if (hasEmail) {
      button = el("a", {
        href: "mailto:" + contact.email + "?subject=" + encodeURIComponent(inquiry.subject || inquiry.title),
        className: "button button-small"
      }, "Send an email");
    } else {
      button = link("Message on " + socials[0].label, socials[0].url, "button button-small");
    }
    var parts = [el("h3", {}, inquiry.title)];
    if (inquiry.text) { parts.push(el("p", {}, inquiry.text)); }
    parts.push(button);
    $("inquiry-list").appendChild(el("div", { className: "inquiry" }, parts));
  });
  $("inquiry-list").hidden = !inquiries.length;
  showSection("contact", hasEmail || socials.length > 0);
})();
