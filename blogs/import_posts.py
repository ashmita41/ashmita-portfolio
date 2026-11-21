#!/usr/bin/env python3
"""Import explicitly selected public authored posts from a verified offline capture."""
import argparse
from datetime import date
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from build import ROOT, render_original

def runs(body):
    output = []
    end = 0
    for match in re.finditer(r"https?://[^\s<>\"']+", body):
        candidate = match.group().rstrip(".,;!?)]}")
        url = urlsplit(candidate)
        if not url.hostname or url.username or url.password:
            raise ValueError("Original post has an unsafe link")
        if end < match.start():
            output.append(body[end:match.start()])
        output.append({"text": candidate, "href": candidate})
        end = match.start() + len(candidate)
    if not output:
        return body
    if end < len(body):
        output.append(body[end:])
    return {"paragraph": output}

def import_posts(catalog, captured, chosen, approved_flags, media_map):
    by_id = {row["id"]:row for row in captured}
    ids = {row["id"] for row in catalog}
    for uid in chosen:
        if not re.fullmatch(r"\d{12,24}", uid):
            raise ValueError(f"Unexpected post identifier: {uid!r}")
        source = by_id[uid]
        if source["author"] != "Ashmita Pandey" or source["visibility"] != "Global":
            raise ValueError(f"Post is not verified as authored and globally visible: {uid}")
        held_flags = set(source["reviewFlags"])-approved_flags.get(uid,set())
        if held_flags:
            raise ValueError(f"Post {uid} requires review: {sorted(held_flags)}")
        eid = f"post-{uid}"
        local_images = media_map.get(uid,[])
        if len(local_images) != len(source["media"]):
            raise ValueError(f"Post {uid} local media count differs from source")
        row = {
            "id": eid, "kind": "post", "title": source["title"],
            "date": date.fromisoformat(source["publicationDate"]).isoformat(),
            "tags": source["tags"],
            "original": {"blocks": [runs(source["body"]), *({"figure": image} for image in local_images)]}
        }
        render_original(row)
        if eid in ids:
            previous = next(e for e in catalog if e["id"] == eid)
            if previous != row:
                raise ValueError(f"Existing post differs from this capture: {uid}")
        else:
            catalog.append(row)
            ids.add(eid)
        print(f"Imported public authored post {uid} ({row['date']}); {len(local_images)} local figures")

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("capture", type=Path)
    cli.add_argument("media_map", type=Path)
    cli.add_argument("ids", nargs="+")
    cli.add_argument("--approve-flag", action="append", default=[], metavar="POST_ID:FLAG")
    args = cli.parse_args()
    approved = {}
    for entry in args.approve_flag:
        uid, flag = entry.split(":",1)
        approved.setdefault(uid,set()).add(flag)
    path = ROOT / "blogs/catalog.json"
    rows = json.loads(path.read_text())
    import_posts(rows, json.loads(args.capture.read_text()), args.ids, approved, json.loads(args.media_map.read_text()))
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2)+"\n")

if __name__=="__main__":
    main()
