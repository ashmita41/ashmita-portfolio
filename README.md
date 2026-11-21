# Ashmita Pandey: Personal Website

A static portfolio with a writing archive and individual article pages. Render serves these files as-is; no production build step is needed.

- Start with `index.html`. Use `writing.html` to filter the article index by topic.
- Individual reports and articles live under `writing/`. All reading works without JavaScript; topic filters are optional.
- To test locally, open `index.html` directly or run `python3 -m http.server`.
- When you update `writing/articles.json`, run `python3 writing/build.py` to regenerate the archive and article pages. Use `python3 writing/build.py --check` to check freshness.

## Practical article schema

Required fields: unique lowercase-hyphenated `id`, `title`, `source`, original HTTPS `url` for provenance, `type` ("Article" or "Interview"), and `tags`. Date and summary are optional.

- `edition: "adapted"`: distinct, condensed site edition; not a word-for-word copy.
- `edition: "original"`: original or permission-cleared full text for republication.
- `edition: "notes"`: interview synopsis, not a transcript.
- `body` can contain plain paragraph strings or objects with `p`, `h2`, `code` (plus optional `language`), or `list`.
- The generated pages don't send visitors to the original platform. The source link is kept in the manifest for editorial reference.
