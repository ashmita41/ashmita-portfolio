"""Local regression tests using synthetic articles and media only."""
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import base64
import unittest
import build

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a33sAAAAASUVORK5CYII="
)

@contextmanager
def temp_site():
    with TemporaryDirectory() as workspace:
        root = Path(workspace)
        (root / "assets/blogs").mkdir(parents=True)
        media = "assets/blogs/Synthetic #1 & chart.png"
        (root / media).write_bytes(PNG)
        with patch.object(build, "ROOT", root):
            yield root, media

def article(id_="example", blocks=None):
    result = {"id": id_, "title": "Synthetic fixture", "date": "2020-01-01", "tags": ["Sample"]}
    if blocks:
        result["original"] = {"blocks": blocks}
    return result

class BuildTests(TestCase):
    def test_inline_figure_escapes_and_stays_in_order(self):
        with temp_site() as (_, media):
            item = article(blocks=[
                "Before the figure.",
                {"figure": {"path": media, "alt": 'Example "chart" & value',
                            "caption": '<img src=x onerror="oops">',
                            "credit": "Example <Author>"}},
                "After the figure."
            ])
            html = build.render_original(item)
            self.assertIn('src="../assets/blogs/Synthetic%20%231%20%26%20chart.png"', html)
            self.assertIn('alt="Example &quot;chart&quot; &amp; value"', html)
            self.assertIn("<figcaption>&lt;img src=x onerror=&quot;oops&quot;&gt;", html)
            self.assertIn("Credit: Example &lt;Author&gt;", html)
            self.assertNotIn('<img src=x onerror=', html)
            self.assertLess(html.index("Before the figure."), html.index("<figure>"))
            self.assertLess(html.index("</figure>"), html.index("After the figure."))

    def test_cover_uses_local_path_and_optional_caption_omitted(self):
        with temp_site() as (_, media):
            item = article(blocks=[{"figure": {"path": media, "alt": "Inline alt"}}])
            item["original"]["cover"] = {"path": media, "alt": "Cover alt"}
            html = build.render_original(item)
            self.assertEqual(html.count("<img"), 2)
            self.assertNotIn("<figcaption", html)

    def test_non_local_invalid_missing_and_escaping_assets_rejected(self):
        with temp_site() as (root, media):
            outside = root / "elsewhere.png"
            outside.write_bytes(PNG)
            (root / "assets/blogs/escape.png").symlink_to(outside)
            (root / "assets/blogs/vector.svg").write_text("<svg/>")
            bad = ["/assets/absolute.png", "https://example.org/remote.png",
                   "assets/../elsewhere.png", "assets/blogs//empty.png",
                   "assets/blogs/vector.svg", "assets/blogs/missing.png",
                   "assets/blogs/escape.png", "assets/blogs/..\\escape.png"]
            for raw in bad:
                with self.subTest(raw=raw):
                    with self.assertRaises(ValueError):
                        build.render_image({"path": raw, "alt": "Alt"})
            for alt in ("", "   ", None):
                with self.assertRaises(ValueError):
                    build.render_image({"path": media, "alt": alt})

    def test_notice_matches_index_status_and_links_only_full_text(self):
        pending = article("pending")
        complete = article("complete", ["Synthetic full text."])
        html = build.to_index([pending])
        self.assertIn("Original text and cover images are not included yet.", html)
        self.assertNotIn('href="blogs/pending.html"', html)
        html = build.to_index([pending, complete])
        self.assertIn("Full text is available for 1 of 2 articles.", html)
        self.assertNotIn('href="blogs/pending.html"', html)
        self.assertIn('href="blogs/complete.html"', html)
        html = build.to_index([complete])
        self.assertNotIn('class="archive-note"', html)
        self.assertIn("No articles are listed yet.", build.to_index([]))

    def test_posts_not_exposed_until_body_available(self):
        pending = article("post-pending")
        pending["kind"] = "post"
        html = build.to_index([article(), pending])
        self.assertNotIn('id="post-pending"', html)
        self.assertNotIn('id="kind-filter"', html)
        complete = article("post-complete", ["A synthetic post."])
        complete["kind"] = "post"
        html = build.to_index([complete, article(), pending])
        self.assertIn('id="kind-filter"', html)
        self.assertIn('data-kind="post" aria-pressed="false">Posts</button>', html)
        self.assertIn('data-kind="post"', html)
        self.assertIn('href="blogs/post-complete.html"', html)
        self.assertNotIn('post-pending', html)
        self.assertNotIn('post-complete', build.home_previews([complete, article()]))

    def test_archive_cards_link_whole_item_and_use_local_thumbnails(self):
        with temp_site() as (_, media):
            item = article(blocks=["Full original."])
            item["original"]["cover"] = {"path": media, "alt": "Cover alt"}
            html = build.to_index([item])
            self.assertIn('class="archive-card" href="blogs/example.html"', html)
            self.assertIn('src="assets/blogs/Synthetic%20%231%20%26%20chart.png" alt=""', html)
            self.assertIn('id="archive-search" type="search"', html)
            self.assertNotIn('<li class="archive-item" hidden', html)
            self.assertNotIn("../assets/", html)

    def test_image_free_post_has_no_fabricated_thumbnail(self):
        item = article("short-post", ["Synthetic fixture\n\nActual post excerpt."])
        item["kind"] = "post"
        item["summary"] = None
        html = build.to_index([item])
        self.assertIn("Actual post excerpt.", html)
        self.assertNotIn("<img ", html)

    def test_multiple_media_and_original_text_order(self):
        with temp_site() as (_, media):
            item = article(blocks=[
                "First line.\nSecond line.",
                {"figure": {"path": media, "alt": "First image"}},
                {"paragraph": ["One ", {"strong": "point"}, " and ", {"text": "one source", "href": "https://example.com/?a=1&b=2"}]},
                {"figure": {"path": media, "alt": "Second image"}},
                {"ordered_list": ["One", "Two"]},
                {"quote": "A quoted line."}
            ])
            html = build.render_original(item)
            self.assertLess(html.index("First line.\nSecond line."), html.index('alt="First image"'))
            self.assertLess(html.index('<strong>point</strong>'), html.index('alt="Second image"'))
            self.assertIn('href="https://example.com/?a=1&amp;b=2"', html)
            self.assertTrue(html.endswith("</html>\n"))
            self.assertIn('<ol><li>One</li><li>Two</li></ol>', html)
            self.assertIn('<blockquote>A quoted line.</blockquote>', html)

    def test_link_protocol_is_validated(self):
        for href in ("javascript:alert(1)", "//example.com", "https://user:pw@example.com/", "https://example.com/a b"):
            with self.subTest(href=href):
                with self.assertRaises(ValueError):
                    build.render_inline([{"text": "Bad link", "href": href}])

    def test_document_retains_nested_lists_marks_and_code(self):
        body = {"document": [
            {"node": "h2", "children": ["Top"]},
            {"node": "ol", "attrs": {"start": 4}, "children": [
                {"node": "li", "children": ["Parent ", {"node": "em", "children": ["italic"]},
                    {"node": "ul", "children": [{"node": "li", "children": ["Nested"]}]}]}
            ]},
            {"node": "pre", "children": [{"node": "code", "children": ["if a < b:\n    print(a)"]}]},
            {"node": "hr"}
        ]}
        html = build.render_original(article(blocks=[body]))
        self.assertIn('<ol start="4"><li>Parent <em>italic</em><ul><li>Nested</li></ul></li></ol>', html)
        self.assertIn('<pre tabindex="0"><code>if a &lt; b:\n    print(a)</code></pre><hr>', html)
        for dangerous in ({"node": "script", "children": ["unknown"]},
                          {"node": "p", "attrs": {"onclick": "forbidden"}, "children": ["text"]}):
            with self.assertRaises(ValueError):
                build.render_source_node(dangerous)

if __name__ == "__main__":
    unittest.main()
