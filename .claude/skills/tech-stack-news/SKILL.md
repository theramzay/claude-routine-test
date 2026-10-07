---
name: tech-stack-news
description: Check what's new in the technology stacks of big tech companies listed in tech-stack.csv at the repo root, and write a dated digest. Use when asked for tech stack news, a daily tech digest, or "what's new" for the tracked companies and technologies.
---

# Tech Stack News

Find recent news, releases and announcements for the technologies each company in `tech-stack.csv` owns, and write a short digest.

## Input: `tech-stack.csv`

The file lives at the repo root. If it is missing, stop and report that it is missing; do not invent a list.

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
3. For each pair, search the web for news inside the window. Prefer primary sources: the company's official blogs, release notes, changelogs, GitHub releases, and developer docs. Use well-known tech press only to fill gaps. Useful queries look like `"<technology>" release`, `"<technology>" announcement`, `<company> <technology> blog`.
4. Open each candidate source and check its publication date. Drop anything outside the window. Drop rumors, opinion pieces, and articles that only repeat older news.
5. For each item, record: title, date, a 1–2 sentence summary of what changed and why it matters to developers, and the source URL.
6. Write the digest (format below).

## Output

Write the digest to `reports/YYYY-MM-DD.md`, using today's UTC date. Create the `reports/` folder if it doesn't exist. If a file for today already exists, overwrite it.

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
```

- Follow the order of companies and technologies in the CSV.
- Every technology gets a section. If nothing was found, write `_No notable news._`; don't leave it out.
- Every item must link to its source. Don't include items you couldn't verify.
- End with a one-line summary, for example: `3 items across 2 companies.`
