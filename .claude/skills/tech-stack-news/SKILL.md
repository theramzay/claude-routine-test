---
name: tech-stack-news
description: Check what's new in the technology stacks of big tech companies listed in tech-stack.csv at the repo root, and write a dated digest. Use when asked for tech stack news, a daily tech digest, or "what's new" for the tracked companies and technologies.
---

# Tech Stack News

Find recent news, releases and announcements for the technologies each company in `tech-stack.csv` owns, and write a short digest.

## Input: `tech-stack.csv`

The file lives at the repo root. If it is missing or has no data rows, stop and report that; do not invent a list. This is the only case where no report is written.

Format:

```csv
company,technologies
Microsoft,Azure;.NET;ASP.NET
Apple,Swift;SwiftUI
```

- Row 1 is a header: `company,technologies`.
- One row per company.
- `technologies` is a `;`-separated list. Trim whitespace around each item and skip empty items.
- If a value contains a comma, it is wrapped in double quotes.

## Steps

1. Read `tech-stack.csv` and build the list of (company, technology) pairs.
2. Set the lookback window: the last 24 hours, unless the user asks for a different period.
3. Research **every** pair separately. Never merge technologies into one search or skip one. For each pair:
   - Run at least 2 web searches with different angles, for example `"<technology>" release`, `"<technology>" announcement <month> <year>`, `<company> <technology> blog`.
   - Check the primary sources for that technology (see below), starting with its official feed.
4. Open each candidate item and check its publication date against the window (see "Dates" below). Drop anything outside it.
5. Apply the relevance filter (see "What counts as news" below).
6. For each item, record: title, date, a 1–2 sentence summary of what changed and why it matters to developers, and the source URL.
7. Write the digest (format below).

### Primary sources

Prefer these, in this order:

1. **Official RSS/Atom feeds.** Read these first: they list posts with exact publish times and don't depend on JavaScript. Fetch them with `curl -sL --compressed <url>` in Bash, because some are gzip-compressed.

   | Technology | Feed |
   |---|---|
   | Azure (product updates) | `https://www.microsoft.com/releasecommunications/api/v2/azure/rss` |
   | Azure (blog) | `https://azure.microsoft.com/en-us/blog/feed/` |
   | .NET, ASP.NET | `https://devblogs.microsoft.com/dotnet/feed/` |
   | Swift | `https://www.swift.org/atom.xml` |
   | Apple platforms, SwiftUI | `https://developer.apple.com/news/rss/news.rss` |

   Don't scrape `azure.microsoft.com/updates`. It loads its list with JavaScript and returns no entries; use the product updates feed above instead.
2. **GitHub releases** for the technology, such as `github.com/dotnet/core/releases`, `github.com/dotnet/aspnetcore/releases`, and `github.com/swiftlang/swift/releases`. Use `gh api` or the releases Atom feed (`/releases.atom`).
3. **Well-known tech press**, such as InfoQ, The Verge, and heise. Use these only to fill gaps, and link to the original announcement when the article cites one.

For technologies not listed here, find the equivalent official feed, blog and GitHub repo yourself.

### Dates

- Use the exact timestamp from the feed or page whenever there is one, convert it to UTC, and compare it with the window.
- If a source gives only a date with no time, include the item when that date is on or after the date the window starts, and on or before today. For example, with a window of 2026-10-06 14:51 to 2026-10-07 14:51, a post dated 2026-10-06 is in.
- Show dates in the report as `YYYY-MM-DD`.

### What counts as news

Include only items that change what developers can use or need to do:

- releases, previews, and GA announcements
- new features and API changes
- deprecations, retirements, and breaking changes
- security fixes and advisories
- pricing or licensing changes that affect developers

Leave out:

- analyst rankings (Gartner, Forrester), awards, and "named a Leader" posts
- marketing, customer stories, case studies, and event promos
- rumors, opinion pieces, and articles that only repeat older news

### Links

- Link only to URLs you actually opened and confirmed load (HTTP 200) with the item's content.
- Never build or guess a URL from a title or slug. If a feed entry has a `<link>`, use it. If the article page fails to load, link to the feed entry's link only if you confirmed it, otherwise drop the item.
- A URL you guessed that fails is not a "source unavailable". Leave it out of the report entirely.

### When a source can't be reached

If a primary source fails (blocked, timeout, 4xx/5xx, or a page that renders no content), try the next source in the list and keep going. One unreachable source must never stop the run or the report. Record every source that failed, with the error, for the "Sources unavailable" section.

## Output

Always write the digest to `reports/YYYY-MM-DD.md`, using today's UTC date, even when there is no news at all. Create the `reports/` folder if it doesn't exist. If a file for today already exists, overwrite it.

```markdown
# Tech Stack News — YYYY-MM-DD

Window: <start> to <end> (UTC)

## Microsoft

### Azure
- **<title>** (<date>) — <summary> [source](<url>)

### .NET
_No notable news._

## Apple
...

## Sources unavailable
- `devblogs.microsoft.com/dotnet/feed/` — timeout (.NET checked through GitHub releases and search instead)

---
3 items across 2 companies.
```

- Follow the order of companies and technologies in the CSV.
- Every technology gets a section. If nothing was found, write `_No notable news._`; don't leave it out. If its primary sources were unreachable *and* nothing turned up elsewhere, write `_No notable news found; primary sources unavailable._`
- Every item must link to its source. Don't include items you couldn't verify.
- Include the "Sources unavailable" section only when at least one fetch failed.
- End with a one-line summary of the item count.
