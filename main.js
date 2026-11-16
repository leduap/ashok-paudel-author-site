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
    if ($(id)) { $(id).hidden = !show; }
    document.querySelectorAll('[data-nav="' + id + '"]').forEach(function (navLink) { navLink.hidden = !show; });
  }

  // A real web address: placeholders such as "#", "" or "TODO" do not count.
  function isRealUrl(url) { return /^https?:\/\/[^\s.]+\.\S+$/.test(url || "") && !/\.\.\.|TODO/.test(url); }
  function isRealEmail(email) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email || "") && !/TODO|example\.com$/i.test(email); }

  // Pages other than the home page live in a folder, so pictures need the site root in front.
  var ROOT = window.SITE_ROOT || "";
  function asset(path) {
    if (!path || /^(https?:|mailto:|data:|#)/.test(path)) { return path; }
    return ROOT + String(path).replace(/^\//, "");
  }

  // Simple text fields
  document.querySelectorAll("[data-text]").forEach(function (node) {
    var value = lookup(node.getAttribute("data-text"));
    if (typeof value === "string") { node.textContent = value; }
  });
  if ($("eyebrow")) { $("eyebrow").textContent = [SITE.name, SITE.credentials].filter(Boolean).join(" · "); }
  if ($("year")) { $("year").textContent = String(new Date().getFullYear()); }

  // Bio and photo. The home page has the hero photo; the About page has its own.
  if ($("bio")) {
    (SITE.bio || []).forEach(function (paragraph) { $("bio").appendChild(el("p", {}, paragraph)); });
  }
  if ($("photo") && SITE.photo) {
    $("photo").src = asset(SITE.photo);
    $("photo").alt = "Portrait of " + SITE.name;
  }
  if ($("about-photo") && SITE.photo) {
    $("about-photo").src = asset(SITE.photo);
    $("about-photo").alt = "Portrait of " + SITE.name;
  }

  // Books, in rows by group (see bookGroups in content.js). Books without a known group go last.
  var books = SITE.books || [];
  if ($("book-list")) { showSection("books", books.length > 0); }
  var groups = (SITE.bookGroups || []).slice();
  var groupIds = groups.map(function (group) { return group.id; });
  if (books.some(function (book) { return groupIds.indexOf(book.group) < 0; })) {
    groups.push({ id: "", title: groups.length ? "More books" : "", text: "" });
  }
  if ($("book-list")) { groups.forEach(function (group) {
    var members = books.filter(function (book) {
      return group.id ? book.group === group.id : groupIds.indexOf(book.group) < 0;
    });
    if (!members.length) { return; }
    var grid = el("div", { className: members.length === 4 ? "book-grid book-grid-4" : "book-grid" });
    var parts = [];
    if (group.title) { parts.push(el("h3", { className: "book-group-title" }, group.title)); }
    if (group.text) { parts.push(el("p", { className: "book-group-text" }, group.text)); }
    parts.push(grid);
    $("book-list").appendChild(el("div", { className: "book-group" }, parts));
    members.forEach(function (book) { grid.appendChild(bookCard(book)); });
  }); }

  function bookCard(book) {
    // A book with a status (e.g. "Coming soon") is not for sale yet: it gets a label and no buy button.
    var status = String(book.status || "").trim();
    var parts = [];
    if (status) { parts.push(el("p", { className: "book-status" }, status)); }
    if (book.series) { parts.push(el("p", { className: "book-series" }, book.series)); }
    parts.push(el("h4", {}, book.title));
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
    var card = [el("div", { className: "book-body" }, parts)];
    if (book.cover) {
      card.unshift(el("img", { src: asset(book.cover), alt: "Cover of " + book.title, loading: "lazy" }));
    }
    return el("article", { className: book.cover ? "book" : "book no-cover" }, card);
  }

  // Finance templates (sold on Gumroad)
  var templates = SITE.templates || {};
  var templateItems = templates.show === false ? [] :
    (templates.items || []).filter(function (item) { return isRealUrl(item.url); });
  if ($("template-list")) { showSection("templates", templateItems.length > 0); }
  if ($("template-list")) { templateItems.forEach(function (item) {
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
      el("img", { src: asset(item.image), alt: "Preview of " + item.title, loading: "lazy" }),
      el("div", { className: "book-body" }, parts)
    ]));
  }); }
  var hasStore = templates.show !== false && isRealUrl(templates.storeUrl);
  if ($("store-link") && hasStore) { $("store-link").href = templates.storeUrl; }
  if ($("store-line")) { $("store-line").hidden = !hasStore; }

  // Articles, newest first
  var articles = (SITE.articles || []).slice().sort(function (a, b) {
    return parseDate(b.date) - parseDate(a.date);
  });
  if ($("article-list")) { showSection("writing", articles.length > 0); }
  if ($("article-list")) { articles.forEach(function (article) {
    // One card per article: the publication's name (as plain text), the headline as the link, the date.
    var parts = [];
    if (article.outlet) { parts.push(el("span", { className: "outlet" }, article.outlet)); }
    parts.push(link(article.title, article.url, "title"));
    if (article.date) { parts.push(el("span", { className: "meta" }, formatDate(article.date))); }
    $("article-list").appendChild(el("li", {}, parts));
  }); }

  // Under the About text: "Published in Fortune", one link per outlet, newest article first.
  var outlets = [];
  articles.forEach(function (article) {
    if (article.outlet && isRealUrl(article.url) &&
        !outlets.some(function (seen) { return seen.outlet === article.outlet; })) {
      outlets.push(article);
    }
  });
  if ($("featured-in") && outlets.length) {
    $("featured-in").appendChild(document.createTextNode("Published in "));
    outlets.forEach(function (article, i) {
      if (i) { $("featured-in").appendChild(document.createTextNode(i === outlets.length - 1 ? " and " : ", ")); }
      $("featured-in").appendChild(link(article.outlet, article.url));
    });
  }
  if ($("featured-in")) { $("featured-in").hidden = !outlets.length; }

  // For editors: the article list is written by the build. This adds the bios, headshot and email.
  var editors = SITE.editors || {};
  var editorEmail = isRealEmail((SITE.contact || {}).email) ? SITE.contact.email : "";
  if ($("editors-intro")) {
  showSection("editors", Boolean(editors.intro || editors.shortBio || editors.longBio));
  $("editors-intro").textContent = editors.intro || "";
  $("editors-intro").hidden = !editors.intro; }
  [["Short bio", editors.shortBio], ["Longer bio", editors.longBio]].forEach(function (pair) {
    if (!pair[1]) { return; }
    var copy = el("button", { type: "button", className: "button button-quiet button-small" }, "Copy");
    copy.addEventListener("click", function () {
      if (!navigator.clipboard) { return; }
      navigator.clipboard.writeText(pair[1]).then(function () {
        copy.textContent = "Copied";
        setTimeout(function () { copy.textContent = "Copy"; }, 2000);
      });
    });
    if ($("bio-blocks")) {
      $("bio-blocks").appendChild(el("h3", {}, pair[0]));
      $("bio-blocks").appendChild(el("div", { className: "bio-block" }, [el("p", {}, pair[1]), copy]));
    }
  });
  if ($("headshot-link")) {
    if (editors.photo) { $("headshot-link").href = asset(editors.photo); }
    $("headshot-link").hidden = !editors.photo;
  }
  if ($("editors-email")) {
    if (editorEmail) { $("editors-email").href = "mailto:" + editorEmail; }
    $("editors-email").hidden = !editorEmail;
  }

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
  if ($("upcoming-list")) {
    upcoming.forEach(function (event) { $("upcoming-list").appendChild(eventRow(event)); });
    past.forEach(function (event) { $("past-list").appendChild(eventRow(event)); });
    $("upcoming-block").hidden = !upcoming.length;
    $("past-block").hidden = !past.length;
  }

  // Press
  var press = SITE.press || {};
  var mentions = press.mentions || [];
  if ($("press-list")) {
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
  }

  // Newsletter: build.py writes the sign-up box and un-hides the "Newsletter" links, but only
  // once newsletter.formAction is set in content.js. signup.js handles the form itself.

  // Contact: shown only when there is a real email address or at least one real profile link
  var contact = SITE.contact || {};
  var hasEmail = isRealEmail(contact.email);
  if ($("email-link") && hasEmail) {
    $("email-link").textContent = contact.email;
    $("email-link").href = "mailto:" + contact.email;
  }
  if ($("email-line")) { $("email-line").hidden = !hasEmail; }
  var socials = (contact.socials || []).filter(function (social) { return isRealUrl(social.url); });
  if ($("social-list")) {
    socials.forEach(function (social) {
      $("social-list").appendChild(el("li", {}, [link(social.label, social.url, "button button-quiet button-small")]));
    });
  }
  // The kinds of request, as short descriptions. There is one button for all of them:
  // the email address above.
  var inquiries = (hasEmail || socials.length > 0) ? (contact.inquiries || []) : [];
  if ($("inquiry-list")) {
    inquiries.forEach(function (inquiry) {
      var parts = [el("h3", {}, inquiry.title)];
      if (inquiry.text) { parts.push(el("p", {}, inquiry.text)); }
      $("inquiry-list").appendChild(el("li", { className: "inquiry" }, parts));
    });
  }
  if ($("inquiry-list")) { $("inquiry-list").hidden = !inquiries.length; }
  if ($("contact")) { showSection("contact", hasEmail || socials.length > 0); }
})();
