# Ashmita Pandey: portfolio review

Open index.html in a browser. This site does not require installation, local hosting, or a build to view. The embedded talk needs an internet connection.

The Blogs page indexes verified titles, dates, and topics. It does not publish interview summaries or condensed technical articles as if they were originals, and it does not link visitors to LinkedIn. Add permission-cleared original content by adding an original object with blocks to the relevant entry in blogs/catalog.json, then regenerate with python3 blogs/build.py. Use --check to verify freshness. Plain strings are paragraphs; structured blocks may be a heading, list, code, or inline figure. Optional original.cover has a local assets path and alt text.

The reviewed old adaptation pages and editorial manifest are kept separately outside this public site folder.

Inline figures use `{"figure":{"path":"assets/blogs/example.webp","alt":"Diagram showing the request flow","caption":"Two workers sharing one queue","credit":"Ashmita Pandey"}}`. Caption and credit are optional plain text. Add only local, permission-cleared WebP/PNG/JPEG files.

Posts use `"kind":"post"` with an ID, a title or short catalog locator, ISO date, tags, and a complete `original.blocks` array. Leave incomplete posts out of the catalog; even if included privately, a post without an original body is not rendered. Existing entries default to articles. Plain body strings preserve line breaks. Block objects include `heading`, `subheading`, `list`, `ordered_list`, `quote`, `code`, `figure`, and `paragraph` for formatted runs. Formatted runs contain plain strings, `{"strong":"text"}`, `{"em":"text"}`, `{"code":"text"}`, or `{"text":"Original label","href":"https://example.com/"}`. No source HTML is accepted. Preserve source order and keep each image in its own figure block, or place an actual cover in `original.cover`.

For an offline LinkedIn article capture, keep the raw HTML and URL-to-local-media manifest outside the public site, then run `python blogs/import_linkedin.py CAPTURE.json MEDIA_MAP.json` (requires lxml for importing only). That optional helper converts source HTML to typed document nodes, preserves nested list structure, inline emphasis and links, code whitespace, quotes and section dividers, and rejects unrecognized markup or missing images instead of omitting content. A plain `python blogs/build.py` build still needs only the standard library.

## Optional site integrations

Both integrations are off until their public identifiers are set in
`site-integrations-config.js`. Never put passwords, private keys or OAuth
tokens in this repository. Bump the config script's cache version in
`index.html` and `blogs/build.py` after changing identifiers, then run the blog
build before deploying.

- **Google Analytics 4:** Set `analyticsId` to the production web stream
  measurement ID. Turn off Enhanced measurement and Google Signals for this
  stream and leave Google Ads disconnected. The tag loads only after visitors
  opt in; they can turn it off on any page. The site sends canonical path-based
  page views, without blog search text in page URLs or contact form values.
  Check Google Analytics Realtime after making a consented test visit.
- **EmailJS:** Set `emailServiceId`, `emailTemplateId`, and `emailPublicKey`.
  Use a fixed recipient in the EmailJS dashboard (the site's public contact
  address), with plain-text template variables `from_name`, `reply_to`, and
  `message`. Set Reply-To to the visitor's email, not the recipient. Restrict
  allowed origins to the deployed site if the plan supports it, and use EmailJS
  rate limits to protect the account. Do not insert unsanitized values in HTML.
  The site's existing Email me link is retained, including when the form is off.
  Check delivery with an authorized test note before announcing the form.
