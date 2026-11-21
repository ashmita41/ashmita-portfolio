#!/usr/bin/env python3
"""Convert authorized, offline LinkedIn captures into site data. Requires lxml for import only.

Usage: python blogs/import_linkedin.py CAPTURE.json MEDIA_MAP.json
The media map is keyed by captured source URL (ignoring a trailing slash).
Each value has a local site "cover" image object, and optionally "inline": a list
of local image objects ordered like the source HTML's image elements.
No network access, source HTML, CDN links, or signed download links are published.
"""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit

from lxml import html
from build import ROOT, RICH_CONTAINERS, RICH_VOID, render_original

AUTHOR = "Ashmita Pandey"
AUTHOR_PATH = "/in/ashmitapandey47"
FLEX_NAMES = {"b":"strong", "i":"em", "strike":"s", "del":"s", "ins":"u"}
NUMBER_ATTRS = {"ol": ("start",), "li": ("value",), "td": ("colspan", "rowspan"), "th": ("colspan", "rowspan")}

def capture_url(value):
    url = urlsplit(value)
    if url.scheme != "https" or url.hostname not in ("www.linkedin.com", "linkedin.com") or url.username or url.password:
        raise ValueError("Unexpected LinkedIn source URL")
    return url.path.rstrip("/")

def document_nodes(source, source_url, local_images):
    parser = html.HTMLParser(remove_comments=True)
    root = html.fragment_fromstring(source, create_parent=True, parser=parser)
    all_headings = [int(n.tag[1]) for n in root.iter() if isinstance(n.tag, str) and re.fullmatch(r"h[1-6]", n.tag)]
    baseline = min(all_headings, default=2)
    images = iter(local_images)

    def contents(el):
        out = [el.text] if el.text else []
        for child in el:
            out.extend(convert(child))
            if child.tail:
                out.append(child.tail)
        return out

    def convert(el):
        tag = el.tag
        if not isinstance(tag, str):
            raise ValueError("Unexpected non-element in source after sanitization")
        if tag == "img":
            try:
                image = next(images)
            except StopIteration:
                raise ValueError("A source inline image has no verified local file") from None
            return [{"figure": image}]
        if tag == "figure":
            pic = el.xpath(".//img")
            captions = el.xpath("./figcaption")
            if len(pic) != 1 or len(captions) > 1:
                raise ValueError("Review source figure with missing/multiple pictures or captions")
            row = dict(convert(pic[0])[0]["figure"])
            if captions:
                caption = captions[0].text_content().strip()
                if caption and row.get("caption", caption) != caption:
                    raise ValueError("Source caption differs from supplied caption")
                if caption:
                    row["caption"] = caption
            other = re.sub(r"\s+", " ", el.text_content()).strip()
            if other != (re.sub(r"\s+", " ", captions[0].text_content()).strip() if captions else ""):
                raise ValueError("Figure includes additional visible material; review manually")
            return [{"figure": row}]
        if tag == "div" and {"reader-content-blocks-container", "reader-image-block"} & set(el.get("class", "").split()):
            return contents(el)
        if tag in ("span", "abbr"):
            return contents(el)
        if re.fullmatch(r"h[1-6]", tag):
            tag = f"h{min(6, int(tag[1]) - baseline + 2)}"
        tag = FLEX_NAMES.get(tag, tag)
        if tag in RICH_VOID:
            return [{"node": tag}]
        if tag not in RICH_CONTAINERS:
            raise ValueError(f"Unexpected source element {tag!r}; review before converting")
        attrs = {}
        if tag == "a":
            href = el.get("href")
            if not href:
                raise ValueError("Source link lacks an href")
            attrs["href"] = urljoin(source_url, href)
        for attr in NUMBER_ATTRS.get(tag, ()):
            if attr in el.attrib:
                attrs[attr] = int(el.attrib[attr])
        node = {"node": tag, "children": contents(el)}
        if attrs:
            node["attrs"] = attrs
        return [node]

    converted = [node for node in contents(root) if not isinstance(node, str) or node.strip()]
    if next(images, None) is not None:
        raise ValueError("Supplied more local inline images than references in the source")
    if not converted:
        raise ValueError("Article body cannot be empty")
    return converted

def import_articles(catalog, capture, media):
    media_by_path = {capture_url(url): row for url, row in media.items()}
    by_title = {row["title"]: row for row in catalog}
    for source in capture["articles"]:
        key = capture_url(source["sourceURL"])
        if not key.startswith("/pulse/") or source["author"] != AUTHOR or capture_url(source["byline"]) != AUTHOR_PATH:
            raise ValueError("Source is not a verified authored article")
        row = by_title.get(source["title"])
        if row is None:
            raise ValueError(f"Add source-verified title/date/tags to the site catalog first: {source['title']}")
        date = datetime.strptime(source["publicationDate"], "%B %d, %Y").date().isoformat()
        if date != row["date"]:
            raise ValueError(f"Source date differs from catalog for {row['id']}")
        media_row = media_by_path.get(key, {})
        if bool(source.get("cover")) != bool(media_row.get("cover")):
            raise ValueError(f"Missing materialized cover or source cover mismatch: {row['id']}")
        local_images = media_row.get("inline", [])
        if len(local_images) != len(source.get("inlineImages", [])):
            raise ValueError(f"Source inline image count differs from local assets: {row['id']}")
        original = {"blocks": [{"document": document_nodes(source["bodyHTML"], source["sourceURL"], local_images)}]}
        if "cover" in media_row:
            original["cover"] = media_row["cover"]
        proposed = {**row, "original": original}
        render_original(proposed)  # Verify local assets, paths, outbound links, and all nodes before saving.
        row.update(proposed)
        print(f"Imported {row['id']} ({date})")

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("media_map", type=Path)
    args = parser.parse_args()
    catalog_file = ROOT / "blogs/catalog.json"
    catalog = json.loads(catalog_file.read_text())
    import_articles(catalog, json.loads(args.capture.read_text()), json.loads(args.media_map.read_text()))
    catalog_file.write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+"\n")

if __name__ == "__main__":
    main()
