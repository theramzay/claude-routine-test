# CLAUDE.md

This repo tracks what's new in the technology stacks of big tech companies. A scheduled cloud routine runs daily at 07:00 UTC and produces a news digest.

## Layout

- `tech-stack.csv`: the list of companies and the technologies to track. This is the only input. Edit it to add or remove companies or technologies.
- `.claude/skills/tech-stack-news/SKILL.md`: the full procedure for building the digest, including CSV format, sources, filtering rules and output format.
- `.claude/skills/tech-stack-news/feeds.json`: official RSS/Atom feeds per technology. Add an entry when you add a technology to the CSV; technologies without one are researched with web search only.
- `.claude/skills/tech-stack-news/scripts/fetch_feeds.py`: fetches the feeds and releases and prints entries inside the lookback window. Python 3 standard library only.
- `.claude/skills/tech-stack-news/news-page.json`: the URL of the Tech Stack News page (a claude.ai artifact) that each run also publishes to.
- `artifacts/tech-stack-news.html`: source of that page. It reads its data live from the artifact's database; daily runs never republish it.
- `reports/YYYY-MM-DD.md`: generated daily digests, one file per UTC date.

## When running the daily routine

1. Use the `tech-stack-news` skill and follow it exactly.
2. Treat `tech-stack.csv` as the single source of truth. Don't add companies or technologies that aren't in it.
3. Only report news you verified from a source with a publication date inside the lookback window. Every item needs a link.
4. Write only `reports/<today>.md`. Don't modify `tech-stack.csv`, the skill, the page source, or older reports.
5. Commit the report with the message `report: tech stack news YYYY-MM-DD` and push it to `main`.
6. Publish the same digest to the news page's database, as described in the skill's "Publish to the news page" section. Write only today's `runs` and `items` documents.

## Conventions

- Dates are UTC and use the `YYYY-MM-DD` format.
- Keep summaries short and factual. Say what changed and why it matters to developers, without marketing language.
- Always write and push a report, even on days with no news. If some sources can't be reached, list them under "Sources unavailable" instead of skipping the report.
- The only reason to skip the report is a missing or empty `tech-stack.csv`, or web search not working at all. In that case, end the session with a clear explanation of what went wrong.
