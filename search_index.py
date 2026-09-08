"""Build optional local full-text search data from the sources being published."""
import datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import quote, urljoin, urlsplit
from zoneinfo import ZoneInfo


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('style', 'script'):
            self.hidden += 1
        if tag in ('p', 'div', 'li', 'br', 'h1', 'h2', 'h3', 'pre', 'td', 'th'):
            self.parts.append(' ')

    def handle_endtag(self, tag):
        if tag in ('style', 'script'):
            self.hidden = max(0, self.hidden - 1)
        if tag in ('p', 'div', 'li', 'h1', 'h2', 'h3', 'pre', 'td', 'th'):
            self.parts.append(' ')

    def handle_data(self, text):
        if not self.hidden:
            self.parts.append(text)


def plain(value):
    parser = Text()
    parser.feed(value)
    return re.sub(r'\s+', ' ', ''.join(parser.parts)).strip()


def date(value, timezone):
    try:
        return datetime.datetime.fromtimestamp(int(value), timezone).date().isoformat()
    except (TypeError, ValueError, OverflowError, OSError):
        return ''


def write_search_index(sources, cfg, root):
    root = Path(root)
    target = root / cfg['search_index']
    timezone = ZoneInfo(cfg.get('timezone', 'UTC'))
    base = urlsplit(cfg.get('url', '/')).path.rstrip('/') + '/'
    entries = []
    for source in sorted(map(Path, sources)):
        lines = source.read_text(encoding='utf-8', errors='replace').splitlines()
        if not lines:
            continue
        title = re.sub(r'^#+\s*', '', lines[0]).strip() or source.stem
        published = date(lines[1], timezone) if len(lines) > 1 else ''
        output = source.with_suffix('.html') if source.suffix == '.md' else source
        relative = output.relative_to(root)
        if source.suffix == '.md':
            rendered = output.read_text(encoding='utf-8')
            body = re.search(r'<body>(.*?)</body>', rendered, re.S)
            text = plain(body.group(1) if body else rendered)
        else:
            text = ' '.join(lines[2:] if published else lines[1:])
        entries.append(dict(title=title, url=urljoin(base, quote(relative.as_posix())),
                            category=relative.parts[0] if len(relative.parts) > 1 else '',
                            date=published, content=text))
    for section, links in cfg.get('link_folders', {}).items():
        for link in links:
            entries.append(dict(title=link.get('title') or link['name'], url=link['url'],
                                category=section, date=date(link.get('date', ''), timezone),
                                content=link['name'] + ' ' + link.get('title', '')))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(entries, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    print(f'Indexed {len(entries)} posts and links in {target}.')
