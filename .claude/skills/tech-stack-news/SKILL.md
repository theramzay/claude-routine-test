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

1. Run the feed script from the repo root:

   ```bash
   python3 .claude/skills/tech-stack-news/scripts/fetch_feeds.py
   ```

   It reads `tech-stack.csv`, sets the window to the last 24 hours (pass `--hours N` if the user asks for a different period), and prints, for every company and technology in CSV order, the official feed posts (and GitHub releases, if any are configured) published inside the window, in UTC. Each entry has its title, link, source, and a `Summary:` line with the text from the feed. Its first line is the window; use it in the report.
   - Exit code 2 means `tech-stack.csv` is missing or empty. Stop and report it.
   - Use the script's output as given. Don't write your own feed-parsing code, and don't re-fetch the feeds it already read.
   - Copy every entry under "Sources unavailable" into the report's "Sources unavailable" section.
2. Supplement **every** technology separately with web search. Never merge technologies into one search or skip one. Run at least 2 searches per technology with different angles, for example `"<technology>" release`, `"<technology>" announcement <month> <year>`, `<company> <technology> blog`. For a technology the script marks "No feeds configured", web search and its official blog are the only sources.
3. Check each candidate from web search against the window (see "Dates" below). Drop anything outside it. Script entries are already inside the window.
4. Apply the relevance filter (see "What counts as news" below) to all candidates, including the script's. The same post can appear under several technologies (for example the .NET blog under both .NET and ASP.NET): put it under the one it's actually about.
5. For each item you keep, record: title, date, a 1–2 sentence summary of what changed and why it matters to developers, and the source URL (see "Links" below).
   - **Script entries:** write the summary from the script's `Summary:` line. Open the page only if that text isn't enough to say what changed. If the page comes back empty or as a bare shell (some official pages, such as `azure.microsoft.com/updates?id=…`, render with JavaScript), keep the item and use the feed summary. Never drop a script entry because its page didn't render.
   - **Web search items:** open the page and confirm it loads with the item's content before you use it.
6. Write the digest (format below).

### Sources

Use these, in this order:

1. **Official feeds**, read by the script. The list per technology is in `.claude/skills/tech-stack-news/feeds.json`.
2. **Official blogs and docs** that have no feed.
3. **Well-known tech press**, such as InfoQ, The Verge, and heise. Use these only to fill gaps, and link to the original announcement when the article cites one.

Don't scrape `azure.microsoft.com/updates`. It loads its list with JavaScript and returns no entries; the Azure product updates feed in `feeds.json` covers it.

To track a new technology's official feed, add it to `feeds.json` under the technology's exact name from `tech-stack.csv`.

`feeds.json` also takes a `github` list of `owner/repo` entries, read with `gh api`. In a cloud routine, the session's GitHub access only covers repos attached to the routine, so other repos return HTTP 403. Leave `github` empty unless the repo is attached.

### Dates

- The script already applies these rules to feed and release entries.
- For other sources, use the exact timestamp whenever there is one, convert it to UTC, and compare it with the window.
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

- For script entries, use the link the script printed. It comes from the official feed, so it counts as confirmed even if the page renders with JavaScript.
- For web search items, link only to URLs you actually opened and confirmed load with the item's content.
- Never build or guess a URL from a title or slug.
- A URL you guessed that fails is not a "source unavailable". Leave it out of the report entirely.

### When a source can't be reached

If a source fails (blocked, timeout, 4xx/5xx), try the next source in the list and keep going. An article page that renders empty for an entry the script already found is not a failed source; don't list it. One unreachable source must never stop the run or the report. Record every source that failed, with the error, for the "Sources unavailable" section.

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
- `https://devblogs.microsoft.com/dotnet/feed/` — URLError: timed out (.NET checked through web search instead)

---
3 items across 2 companies.
```

- Follow the order of companies and technologies in the CSV.
- Every technology gets a section. If nothing was found, write `_No notable news._`; don't leave it out. If its primary sources were unreachable *and* nothing turned up elsewhere, write `_No notable news found; primary sources unavailable._`
- Every item must link to its source. Don't include items you couldn't verify.
- Include the "Sources unavailable" section only when at least one fetch failed.
- End with a one-line summary of the item count.
