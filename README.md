# Ashmita Pandey: Personal Website

Static portfolio and writing archive (HTML/CSS and a little vanilla JavaScript). Hosting requires no build step.

- Open `index.html` in a browser, or run `python3 -m http.server` and open http://localhost:8000.
- `index.html` is the portfolio; `writing.html` is the topic-filterable archive.
- Images are in `assets/` with WebP and JPG fallbacks.
- Render uses `render.yaml` to publish the static site (path `./`).

## Update the writing archive

1. Add an entry to `writing/articles.json` with a unique lower-case slug (`id`), title, source, original HTTPS URL, type (`Article` or `Interview`), and one or more topic tags. The date (`YYYY-MM-DD`) and summary are optional.
2. Leave `body` out for link-only items. If you have permission to republish the text, `body` is an array containing one string per paragraph.
3. Run `python3 writing/build.py` to update the static page. Run `python3 writing/build.py --check` to check for stale output.

All entries remain visible without JavaScript. Topic filters use `writing/filter.js` and need no network calls.
