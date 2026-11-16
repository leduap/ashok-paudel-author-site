---
title: AI has found the internet's cracks. Now someone must pay for the repairs
date: 2026-10-27
type: post
tags: ai, cybersecurity, open source, europe
summary: Machines can spot software flaws far faster than the small, underfunded teams who maintain the web's foundations can fix them. Europe should make sure the fixers are paid.
image: assets/images/code-on-screen.jpg
image_alt: Computer code on a monitor
image_credit: Markus Spiske, Wikimedia Commons (CC0)
image_source: https://commons.wikimedia.org/wiki/File:Code_on_computer_monitor_(Unsplash).jpg
---

Last week two critical flaws were disclosed in PHP, the language behind about 69 per cent of websites whose server-side language can be identified. Researchers found them with the help of AI models, partly through a programme led by OpenAI. Details leaked before the planned release, and Cloudflare's chief executive reported "millions" of attempts to exploit the flaws within hours. All Nippon Airways and MUFG Bank pulled parts of their online services while they patched. The fixes were written, as they nearly always are, by PHP's own maintainers.

Part of the web's safety came from the fact that hardly anyone had time to read its code closely. Machines now do. This will not be a one-off. Google's threat intelligence group says the number of vulnerabilities disclosed each month doubled this year, from 5,045 in January to 10,740 in August. OpenAI expects findings like the PHP flaws to "increase sharply in the coming months". Finding weaknesses in software is becoming cheap and fast. Fixing them is not.

In corporate controlling, a simple principle applies: what a company depends on but does not record, goes unfunded. Companies capitalise and budget for the software they build and buy. The open-source code beneath it shows up nowhere in their books, with no maintenance budget, no named owner and no line in the risk register. It is an unrecorded liability, and AI has just put a price on it.

Consider who does the fixing. The PHP Foundation, which pays developers to look after the language's core, received $730,534 in donations in 2025. That supported 11 contracted developers, some part-time. It deliberately spent more than it took in to keep its engineers, while its number of sponsors fell substantially. A language that runs most of the web is looked after by a team you could seat around a dining table. And the oldest code is the hardest to rescue: the project issues no fixes for versions 8.1 and earlier, yet more than a third of PHP websites still run version 7 or older.

Europe has begun to see the problem. Since 11 September, its Cyber Resilience Act has required manufacturers of digital products sold in the EU to send an early warning within 24 hours of learning that a flaw is being actively exploited. When they find a flaw in an open-source component, they must report it to whoever maintains it. This is sensible. But a duty to report is not a capacity to repair. A law that sends more alerts to a few maintainers, just as machines multiply those alerts, risks swamping the very people it depends on.

The model makers have a part to play too. OpenAI has promised $1bn of subsidised access to its tools for defenders with limited security resources, which is welcome. More useful still would be a norm that every AI-found flaw reaches its maintainer with a tested patch, not just a report. If finding is automated and fixing is not, the industry is quietly passing its costs to volunteers.

Germany has already shown what paying for repairs looks like. Since 2022 its Sovereign Tech Agency has put more than €60mn into maintaining and securing open-source software across more than 110 projects, including curl, Log4j and Python, and it helped pay for a security audit of PHP. That is the right idea on the wrong scale for a continent whose companies, hospitals and public services all stand on this code. The natural next step is a European maintenance fund sized for the AI era, financed mainly by the companies that sell digital products into the single market and profit from free foundations. Its work would be dull and vital: paying engineers to fix what the machines find, carrying fixes back to older versions people still run, and helping small projects meet the new reporting rules rather than be crushed by them. Machines have learnt to find the cracks. Someone now has to be paid to fill them.

## Sources

1. W3Techs, usage statistics of PHP (69.2% of websites with a known server-side language; version 7 at 26.6%, version 5 at 7.7%, version 4 at 0.1% of PHP sites), 27 October 2026
2. OpenAI, "Patch the Planet: global response coordination as agents uncover critical vulnerabilities", 21 October 2026
3. Google Cloud, "Responding to core PHP vulnerabilities CVE-2026-109618 and CVE-2026-109619"
4. Cloudflare, "Cloudflare deploys protections against php2shell vulnerability"
5. PBS NewsHour and AP, 22 October 2026 (Cloudflare chief executive on "millions" of exploit attempts)
6. Nikkei Asia, 22 October 2026 (ANA, MUFG Bank and others suspended online services)
7. Google Threat Intelligence Group, "Vulnerability Discovery and Exploitation Trends in the AI Era"
8. The PHP Foundation, Impact and Transparency Report 2025
9. European Commission, Cyber Resilience Act reporting obligations (from 11 September 2026), and Regulation (EU) 2024/2847, Article 13(6)
10. Sovereign Tech Agency, "Wir feiern fünf Jahre" and 2026 report

---

*The views expressed are the author's own.*
