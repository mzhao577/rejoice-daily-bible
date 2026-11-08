"""Scrape https://sites.google.com/view/rejoice-him/ into data/site.json + static/.

Run once (from a machine that can reach Google) to refresh the local copy:
    python scripts/scrape_site.py
"""
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path

BASE = "https://sites.google.com/view/rejoice-him/"
ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
MONTHS = ["january", "february", "march", "april", "may", "june", "july",
          "august", "september", "october", "november", "december"]
BLOCKS = {"h1", "h2", "h3", "h4", "p", "li"}
SECTION_STYLE = {"lQAHbd": "dark", "qeLZfd": "light"}


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
                return (data, r.headers.get_content_type()) if binary else data.decode("utf-8", "ignore")
        except Exception:
            pass
    raise RuntimeError(f"failed: {url}")


def unwrap(href):
    q = urllib.parse.urlparse(href)
    if q.netloc.endswith("google.com") and q.path == "/url":
        return urllib.parse.parse_qs(q.query)["q"][0]
    return href


class MainParser(HTMLParser):
    """Collect sections -> blocks -> runs from the role=main region."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        # the page-title header comes before the first <section> inside role=main
        self.sections, self.block, self.link = [{"style": "header", "blocks": []}], None, None
        self.skip = 0  # depth inside script/style/svg

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "svg"):
            self.skip += 1
        elif tag == "section":
            classes = (a.get("class") or "").split()
            style = next((SECTION_STYLE[c] for c in classes if c in SECTION_STYLE), "plain")
            self.sections.append({"style": style, "blocks": []})
        elif tag in BLOCKS and self.sections:
            m = re.search(r"text-align:\s*(\w+)", a.get("style") or "")
            self.block = {"tag": tag, "align": m.group(1) if m else "left", "runs": []}
        elif tag == "a" and self.block is not None and a.get("href", "").startswith("http"):
            self.link = unwrap(a["href"])
        elif tag == "br" and self.block is not None:
            self._add("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg"):
            self.skip -= 1
        elif tag == "a":
            self.link = None
        elif tag in BLOCKS and self.block is not None:
            if "".join(r[0] for r in self.block["runs"]).strip():
                self.sections[-1]["blocks"].append(self.block)
            self.block = None

    def handle_data(self, data):
        if self.block is not None and not self.skip:
            self._add(data)

    def _add(self, text):
        runs = self.block["runs"]
        if runs and runs[-1][1] == self.link:
            runs[-1][0] += text
        else:
            runs.append([text, self.link])


def download(url, subdir):
    """Save a remote file under static/<subdir>/ and return its path relative to ROOT."""
    data, ctype = fetch(url, binary=True)
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
           "image/webp": ".webp", "audio/mpeg": ".mp3"}.get(ctype, "")
    # Google image URLs are signed per page load, so name files by content to dedupe
    name = hashlib.md5(data).hexdigest()[:12] + ext
    path = STATIC / subdir / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return str(path.relative_to(ROOT))


def parse_page(page, media):
    main = page[page.find('role="main"'):]
    p = MainParser()
    p.feed(main.split(">", 1)[1])
    header, *sections = p.sections
    # make Google Drive links (blocked in China) point at locally hosted copies
    for sec in sections:
        for blk in sec["blocks"]:
            for run in blk["runs"]:
                if run[1] and "drive.google.com" in run[1]:
                    run[1] = media(run[1])
    sections = [s for s in sections if s["blocks"]]
    return {
        "title": "".join(r[0] for b in header["blocks"] for r in b["runs"]).strip(),
        "header_style": "dark-text" if re.search(r'<section[^>]*class="[^"]*\btpmmCb\b', page) else "light-text",
        "sections": sections,
    }


def main():
    home = fetch(BASE)
    days = list(dict.fromkeys(re.findall(r'href="/view/rejoice-him/([a-z]+)/(\d\d-\d\d)"', home)))
    urls = [BASE] + [BASE + m for m in MONTHS] + [f"{BASE}{m}/{d}" for m, d in days]
    downloads = {}

    def media(url):
        if url not in downloads:
            fid = re.search(r"id=([\w-]+)", url)
            src = f"https://drive.google.com/uc?export=download&id={fid.group(1)}" if fid else url
            downloads[url] = download(src, "media")
        return downloads[url]

    def scrape(url):
        # signed image URLs expire quickly: fetch the page and its banner together, retrying both
        for attempt in range(4):
            page = fetch(url)
            banner = re.search(r"background-image: url\((https://sites\.google\.com/sitesv-images-rt/[^)]+)\)", page)
            try:
                local = download(banner.group(1), "images") if banner else None
                break
            except RuntimeError:
                if attempt == 3:
                    raise
        return page, local

    with ThreadPoolExecutor(8) as ex:
        results = dict(zip(urls, ex.map(scrape, urls)))
    parsed = {}
    for u, (page, banner) in results.items():
        parsed[u] = parse_page(page, media)
        parsed[u]["banner"] = banner
    banners = {p["banner"] for p in parsed.values() if p["banner"]}
    logo = re.search(r'<img[^>]*src="(https://sites\.google\.com/sitesv-images-rt/[^"]+)"', results[BASE][0]).group(1)

    home_p = parsed[BASE]
    site = {
        "site_name": "Rejoice!",
        "logo": download(logo, "images"),
        "home": home_p,
        "months": [],
    }
    for m in MONTHS:
        entry = {"slug": m, **parsed[BASE + m], "days": []}
        for mm, d in days:
            if mm == m:
                entry["days"].append({"slug": d, **parsed[f"{BASE}{m}/{d}"]})
        site["months"].append(entry)

    out = ROOT / "data" / "site.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(site, ensure_ascii=False, indent=1))
    print("days:", sum(len(m["days"]) for m in site["months"]), "banners:", len(banners), "media:", len(downloads))


if __name__ == "__main__":
    main()
