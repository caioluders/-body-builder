import contextlib
from email.utils import parsedate_to_datetime
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from xml.etree import ElementTree

import app


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name)
        self.write('templates/site.html', '<html><head><style>body { color: white; }</style></head><body><h1>$blog_title</h1><table class="index">$posts_table</table><footer>$footnote</footer></body></html>')
        self.cfg = dict(theme='templates/site.html', title='Generic test site', url='https://example.test/blog/',
                        footnote='Example author', rss=True, timezone='America/Sao_Paulo',
                        ignore=['index.html', 'config.json', 'templates', 'assets', 'private'],
                        page_scripts=['/blog/assets/ui.js'], search_index='assets/search.json',
                        link_folders={'bookmarks': [dict(name='External', url='https://example.org/', title='A link')]})

    def write(self, path, text):
        target = self.site / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        return target

    def build(self):
        self.write('config.json', json.dumps(self.cfg))
        with contextlib.redirect_stdout(io.StringIO()):
            app.main(SimpleNamespace(path=str(self.site), config=str(self.site / 'config.json')))

    def test_one_build_publishes_articles_navigation_search_and_rss(self):
        self.write('notes/hello.md', '# Hello café\n1704153600\n\nAn **accented** post.\n\n```python\nprint("hi")\n```')
        self.write('another/hello.md', 'Plain title\n1704153600\n\nOther post.')
        self.write('notes/deep/a #b.md', '## Nested title\n1704153600\n\nNested token.')
        self.write('root.txt', 'Root note\n1704153600\n\nText token.')
        self.write('private/secret.md', '# Secret\n1704153600\n\nDo not index.')
        self.write('.hidden/secret.md', '# Hidden\n1704153600\n\nDo not index.')
        artwork = self.write('notes/art.html', '<html><script>let art = 1;</script></html>')
        original = artwork.read_bytes()
        self.build()
        self.assertEqual(artwork.read_bytes(), original)
        self.assertFalse((self.site / 'private/secret.html').exists())
        root = (self.site / 'index.html').read_text()
        self.assertNotIn('href="../"', root)
        self.assertIn('href="notes/">notes/</a>', root)
        self.assertIn('href="../"', (self.site / 'notes/index.html').read_text())
        for name in ['notes/hello.html', 'another/hello.html', 'notes/deep/a #b.html']:
            article = (self.site / name).read_text()
            self.assertEqual(article.count('src="/blog/assets/ui.js"'), 1)
            self.assertEqual(article.count('name="viewport"'), 1)
            self.assertIn('<h1>', article)
            self.assertIn('<title>', article)
            self.assertIn('body { color: white; }', article)
            self.assertLess(article.index('src="/blog/assets/ui.js"'), article.index('</body>'))
        entries = json.loads((self.site / 'assets/search.json').read_text())
        urls = {entry['url'] for entry in entries}
        self.assertEqual(urls, {'/blog/notes/hello.html', '/blog/another/hello.html', '/blog/notes/deep/a%20%23b.html', '/blog/root.txt', 'https://example.org/'})
        entry = next(e for e in entries if e['title'] == 'Hello café')
        self.assertEqual(entry['date'], '2024-01-01')
        self.assertIn('An accented post.', entry['content'])
        self.assertNotIn('body {', entry['content'])
        rss = ElementTree.parse(self.site / 'rss.xml')
        links = {e.findtext('link') for e in rss.findall('.//item')}
        self.assertIn('https://example.test/blog/notes/hello.html', links)
        self.assertIn('https://example.test/blog/another/hello.html', links)
        self.assertIn('https://example.test/blog/notes/deep/a%20%23b.html', links)
        for item in rss.findall('.//item'):
            self.assertIsNotNone(parsedate_to_datetime(item.findtext('pubDate')).tzinfo)
        before = {str(p.relative_to(self.site)): p.read_bytes() for p in self.site.rglob('*') if p.is_file()}
        self.build()
        self.assertEqual(before, {str(p.relative_to(self.site)): p.read_bytes() for p in self.site.rglob('*') if p.is_file()})
        self.write('brand-new/topic.md', '# Added later\n1704153600\n\nFresh search token.')
        self.build()
        self.assertTrue(any(e['url'] == '/blog/brand-new/topic.html' for e in json.loads((self.site / 'assets/search.json').read_text())))
        (self.site / 'brand-new/topic.md').unlink()
        self.build()
        self.assertFalse(any(e['url'] == '/blog/brand-new/topic.html' for e in json.loads((self.site / 'assets/search.json').read_text())))

    def test_old_config_does_not_require_blog_scripts_or_search(self):
        for key in ['page_scripts', 'search_index', 'timezone']:
            self.cfg.pop(key)
        self.write('post.md', '# A post\n1704153600\n\nBody.')
        self.build()
        self.assertFalse((self.site / 'assets/search.json').exists())
        self.assertNotIn('<script', (self.site / 'post.html').read_text())
        self.assertNotIn('<script', (self.site / 'index.html').read_text())


if __name__ == '__main__':
    unittest.main()
