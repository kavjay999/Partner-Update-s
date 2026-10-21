# Microsoft Partner News bot

Checks the Microsoft Partner Center announcements page every 3 hours and rebuilds a
mobile-friendly site (`index.html`) with search and filters. Free to run.

## One-time setup (about 10 minutes, all doable from a phone browser)

1. Create a free account at github.com and make a **new public repository** (e.g. `partner-news`).
2. Upload these into the repo root, keeping the folder structure:
   - `update_news.py`
   - `config.json`
   - `.github/workflows/update.yml`
3. **Settings > Actions > General > Workflow permissions** > choose *Read and write permissions* > Save.
4. **Actions tab** > "Update partner news" > **Run workflow**. This builds `index.html` the first time.
5. **Settings > Pages** > Source: *Deploy from a branch* > Branch: `main` / `(root)` > Save.
6. Your site is live at `https://<your-username>.github.io/partner-news/`.
7. Put that link in your WhatsApp status, Business profile, or Channel description.

From then on it refreshes itself every 3 hours. Change the schedule in `update.yml` (the `cron` line).

## Customise

Edit `config.json`:
- `brand`: the title shown at the top of the site
- `whatsapp_channel_url`: your WhatsApp Channel invite link; adds a "Follow on WhatsApp" button
- `max_items`: how many announcements to keep

## Notes

- Reads Microsoft Learn's own Markdown version of the page, not scraped HTML. If Microsoft changes the
  table layout, the bot refuses to overwrite your site (fewer than 10 items parsed) and the Actions tab
  shows a red failed run, so you will know.
- The site shows titles, dates and categories, and every card links to Microsoft's original page.
  It is an unofficial feed; keep the "content belongs to Microsoft" footer.
- WhatsApp has no public API for posting to Channels, so Channel posts stay manual. The site updates itself.
