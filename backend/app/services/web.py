import httpx
import re
from html.parser import HTMLParser
from app.models.paper import PaperBase


class _TextExtractor(HTMLParser):
    SKIP_TAGS = {'script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript'}

    def __init__(self):
        super().__init__()
        self.title = ''
        self._in_title = False
        self._skip = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == 'title':
            self._in_title = True
        if tag in self.SKIP_TAGS:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False
        if tag in self.SKIP_TAGS and self._skip > 0:
            self._skip -= 1

    def handle_data(self, data):
        text = data.strip()
        if not text:
            return
        if self._in_title:
            self.title = text
        elif self._skip == 0:
            self._parts.append(text)

    @property
    def text(self) -> str:
        # Collapse repeated whitespace between parts
        return '\n'.join(self._parts)


def _detect_source(raw: str) -> tuple[str, str]:
    """Returns ('arxiv', clean_id) or ('web', url)."""
    raw = raw.strip()

    # alphaXiv → treat as arXiv
    for prefix in ('https://alphaxiv.org/abs/', 'http://alphaxiv.org/abs/', 'alphaxiv.org/abs/'):
        if raw.startswith(prefix):
            arxiv_id = raw[len(prefix):]
            return 'arxiv', arxiv_id

    # Standard arXiv URL
    for prefix in ('https://arxiv.org/abs/', 'http://arxiv.org/abs/', 'arxiv.org/abs/'):
        if raw.startswith(prefix):
            return 'arxiv', raw[len(prefix):]

    # Bare arXiv ID  e.g. 2301.00001 or 2301.00001v2
    if re.match(r'^\d{4}\.\d{4,5}(v\d+)?$', raw):
        return 'arxiv', raw

    # Any other URL
    if raw.startswith('http://') or raw.startswith('https://'):
        return 'web', raw

    # Fallback: treat as arXiv ID
    return 'arxiv', raw


async def fetch_web_paper(url: str) -> PaperBase:
    """Scrape a web page and return a PaperBase with raw text as abstract."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        resp = await client.get(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; PaperArchive/1.0)'})
        resp.raise_for_status()

    parser = _TextExtractor()
    parser.feed(resp.text)

    title = parser.title or url
    # Truncate to ~6000 chars to stay within token budget
    text = parser.text[:6000]

    return PaperBase(
        arxiv_id=url,          # use URL as unique ID
        title=title,
        authors=[],            # Claude will extract these
        abstract=text,         # raw page text — Claude will use this
        arxiv_url=url,
        pdf_url=None,
    )
