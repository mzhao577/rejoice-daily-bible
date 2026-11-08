"""Rejoice! — Daily Bible Enjoyment.

A Streamlit mirror of https://sites.google.com/view/rejoice-him/ that works without
any Google-hosted resources (fonts, images, audio are all served locally).

Pages are addressed with the ``p`` query parameter:
    ?p=               home
    ?p=january        month index
    ?p=january/01-01  daily reading
    ?p=audio/<file>   audio player for a locally hosted recording
"""
import html
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).resolve().parent
SITE_PREFIX = "https://sites.google.com/view/rejoice-him/"

st.set_page_config(page_title="Rejoice!", page_icon="✝️", layout="wide",
                   initial_sidebar_state="auto")


@st.cache_data
def load_site():
    return json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))


def static_url(path):
    # files under ./static are served by Streamlit at app/static/...
    return "app/" + path


def href(url):
    """Map links to the old Google site / local media onto routes of this app."""
    if url.startswith(SITE_PREFIX):
        slug = url[len(SITE_PREFIX):].strip("/")
        return "./" if slug in ("", "home") else f"?p={slug}"
    if url.startswith("static/media/"):
        return f"?p=audio/{url.rsplit('/', 1)[1]}&from={st.query_params.get('p', '')}"
    return url


def link(text, url):
    target = "_blank" if url.startswith("http") else "_self"
    return f'<a href="{html.escape(href(url))}" target="{target}">{html.escape(text)}</a>'


def render_runs(runs):
    out = "".join(link(t, u) if u else html.escape(t) for t, u in runs)
    return out.replace("\n", "<br>")


def render_sections(sections):
    parts = []
    for sec in sections:
        blocks = "".join(
            f'<{b["tag"]} style="text-align:{b["align"]}">{render_runs(b["runs"])}</{b["tag"]}>'
            for b in sec["blocks"]
        )
        parts.append(f'<section class="rj-sec rj-{sec["style"]}"><div class="rj-inner">{blocks}</div></section>')
    return "".join(parts)


def render_banner(title, banner, header_style):
    bg = f"background-image:url('{static_url(banner)}');" if banner else ""
    return (f'<header class="rj-banner rj-{header_style}" style="{bg}">'
            f'<h1>{html.escape(title)}</h1><div class="rj-bar"></div></header>')


def render_sidebar(site, current):
    month_open = current.split("/")[0]
    items = [f'<a class="rj-nav-item{" rj-active" if current in ("", "home") else ""}" href="./" target="_self">Home</a>']
    for m in site["months"]:
        days = "".join(
            f'<a class="rj-nav-item rj-nav-day{" rj-active" if current == m["slug"] + "/" + d["slug"] else ""}" '
            f'href="?p={m["slug"]}/{d["slug"]}" target="_self">{d["slug"]}</a>'
            for d in m["days"]
        )
        active = " rj-active" if current == m["slug"] else ""
        is_open = " open" if month_open == m["slug"] else ""
        items.append(
            f'<details class="rj-month"{is_open}><summary><span class="rj-chev"></span>'
            f'<a class="rj-nav-item{active}" href="?p={m["slug"]}" target="_self">{m["title"]}</a></summary>{days}</details>'
        )
    logo = f'<img src="{static_url(site["logo"])}" alt="">' if site.get("logo") else ""
    st.sidebar.markdown(
        f'<div class="rj-nav"><a class="rj-brand" href="./" target="_self">{logo}<div>{html.escape(site["site_name"])}</div></a>'
        f'<hr>{"".join(items)}</div>',
        unsafe_allow_html=True,
    )


def find_page(site, slug):
    if slug in ("", "home"):
        return site["home"]
    month, _, day = slug.partition("/")
    for m in site["months"]:
        if m["slug"] == month:
            if not day:
                return m
            return next((d for d in m["days"] if d["slug"] == day), None)
    return None


CSS = """
<style>
:root {
  --rj-brown: rgb(133,114,81);
  --rj-brown-dark: rgb(116,102,77);
  --rj-band: rgb(130,113,83);
  --rj-cream: rgb(247,244,238);
  --rj-gold: rgb(206,169,100);
  --rj-text: rgb(33,33,33);
  --rj-heading-font: Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
  --rj-body-font: "Open Sans", "Segoe UI", "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
}
/* strip Streamlit chrome so the page looks like the original site */
header[data-testid="stHeader"] { background: transparent; pointer-events: none; }
[data-testid="stMainMenu"], [data-testid="stAppDeployButton"], [data-testid="stToolbarActions"],
[data-testid="stStatusWidget"], [data-testid="stDecoration"], [data-testid="stHeaderActionElements"],
footer, #MainMenu { display: none !important; }
/* keep the button that re-opens the navigation (used on phones), drawn on a white chip over the banner */
[data-testid="stExpandSidebarButton"] { pointer-events: auto; background: rgba(255,255,255,0.9);
  border-radius: 6px; box-shadow: 0 1px 4px rgba(0,0,0,0.25); }
.stApp, [data-testid="stMain"] { background: #fff; }
[data-testid="stMainBlockContainer"], .block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stMain"] [data-testid="stVerticalBlock"] { gap: 0 !important; }
[data-testid="stMarkdownContainer"] p { margin: 0; }
iframe[height="0"], [data-testid="stIFrame"][height="0"] { display: block; }
[data-testid="stElementContainer"]:has(iframe[height="0"]) { display: none; }

/* sidebar navigation */
[data-testid="stSidebar"] { background: #fff; border-right: 1px solid rgba(0,0,0,0.12); }
[data-testid="stSidebarContent"] { padding-top: 0; }
[data-testid="stSidebarUserContent"] { padding: 0 1rem 2rem !important; }
.rj-nav { font-family: var(--rj-body-font); }
.rj-brand { display: block; text-align: center; padding-top: 40px; text-decoration: none !important; }
.rj-brand img { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; display: block; margin: 0 auto 26px; }
.rj-brand div { font-family: var(--rj-heading-font); font-size: 20pt; font-weight: 500; letter-spacing: 1px; color: var(--rj-text); }
.rj-nav hr { border: 0; border-top: 1px solid var(--rj-text); margin: 24px 0 30px; }
.rj-nav-item { display: block; padding: 9px 0 9px 21px; color: rgba(0,0,0,0.8) !important; text-decoration: none !important; font-size: 12pt; }
.rj-nav-item:hover, .rj-nav-item.rj-active { color: #000 !important; font-weight: 600; }
.rj-nav-day { padding-left: 41px; }
.rj-month > summary { list-style: none; display: flex; align-items: center; cursor: pointer; }
.rj-month > summary::-webkit-details-marker { display: none; }
.rj-month > summary .rj-nav-item { padding-left: 4px; flex: 1; }
.rj-chev { width: 17px; display: inline-block; text-align: center; color: rgba(0,0,0,0.7); }
.rj-chev::before { content: "⌄"; font-size: 18px; position: relative; top: -4px; }
.rj-month[open] .rj-chev::before { content: "⌃"; top: 4px; }

/* page banner */
.rj-banner { position: relative; height: 310px; background-size: cover; background-position: center;
  display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.rj-banner.rj-light-text::before { content: ""; position: absolute; inset: 0; background: rgba(0,0,0,0.15); }
.rj-banner h1 { position: relative; margin: 0 16px; padding: 0; font-family: var(--rj-heading-font) !important;
  font-size: clamp(30px, 5vw, 60px); font-weight: 500; letter-spacing: -0.5px; line-height: 1.26; }
.rj-banner.rj-light-text h1 { color: #fff; text-shadow: 0 1px 4px rgba(0,0,0,0.35); }
.rj-banner.rj-dark-text h1 { color: var(--rj-text); }
.rj-bar { position: relative; width: 100px; border-bottom: 8px solid var(--rj-gold); margin-top: 18px; }

/* content sections */
.rj-sec { padding: 24px 16px; }
.rj-inner { max-width: 1010px; margin: 0 auto; padding: 0 3%; }
.rj-plain { background: #fff; }
.rj-light { background: var(--rj-cream); }
.rj-dark { background: var(--rj-band); }
.rj-sec p { font-family: var(--rj-body-font); font-size: 12pt; line-height: 1.67; color: var(--rj-text); margin: 0 0 12px; }
.rj-sec h1, .rj-sec h2, .rj-sec h3 { font-family: var(--rj-heading-font) !important; font-weight: 700; color: var(--rj-brown); padding: 0; }
.rj-sec h1 { font-size: 26pt; line-height: 1.5; margin: 8px 0; }
.rj-sec h2 { font-size: 18pt; line-height: 1.56; margin: 12px 0 20px; }
.rj-sec h3 { font-size: 14pt; margin: 10px 0; }
.rj-light h1, .rj-light h2, .rj-light h3 { color: var(--rj-brown-dark); }
.rj-dark h1, .rj-dark h2, .rj-dark h3, .rj-dark p, .rj-dark a { color: rgb(255,250,241) !important; }
.rj-sec a { color: inherit; text-decoration: underline; }
.rj-light a { color: var(--rj-brown-dark); }
.rj-sec a:hover { opacity: 0.8; }
.rj-sec h1 a, .rj-sec h2 a { color: inherit; }
/* home page month list is a stack of centered h2 links */
.rj-home .rj-light h2 { margin: 6px 0 16px; }
.rj-back { font-family: var(--rj-body-font); }
@media (max-width: 640px) {
  .rj-banner { height: 220px; }
  .rj-sec h2 { font-size: 15pt; }
}
</style>
"""


def show(markup):
    st.html(markup)


# Streamlit rewrites every link to open in a new tab. This (same-origin) helper makes links
# that stay inside this site open in the same tab, like the original Google site.
SAME_TAB_LINKS = """
<script>
const doc = window.parent.document;
if (!doc.rjSameTab) {
  doc.rjSameTab = true;
  doc.addEventListener("click", (e) => {
    const a = e.target.closest("a[href]");
    if (!a || e.ctrlKey || e.metaKey || e.shiftKey) return;
    if (new URL(a.href).origin === window.parent.location.origin) {
      a.setAttribute("target", "_self");
      a.removeAttribute("rel");
    }
  }, true);
}
</script>
"""


def main():
    site = load_site()
    slug = st.query_params.get("p", "").strip("/")
    st.markdown(CSS, unsafe_allow_html=True)
    render_sidebar(site, slug)
    components.html(SAME_TAB_LINKS, height=0)

    if slug.startswith("audio/"):
        name = Path(slug).name
        audio = ROOT / "static" / "media" / name
        origin = find_page(site, st.query_params.get("from", "")) or site["home"]
        show(render_banner(origin["title"], origin["banner"], origin["header_style"]))
        if audio.is_file():
            show('<div class="rj-sec"><div class="rj-inner"><h2 style="text-align:center">Audio</h2></div></div>')
            _, mid, _ = st.columns([1, 3, 1])
            mid.audio(str(audio), format="audio/mpeg")
            back = st.query_params.get("from", "")
            show(f'<div class="rj-sec"><div class="rj-inner"><p class="rj-back" style="text-align:center">'
                 f'<a href="?p={html.escape(back)}" target="_self">← Back</a></p></div></div>')
        else:
            show('<div class="rj-sec"><div class="rj-inner"><p>Audio not found.</p></div></div>')
        return

    page = find_page(site, slug)
    if page is None:
        show(render_banner("Page not found", site["home"]["banner"], "light-text")
             + '<section class="rj-sec"><div class="rj-inner"><p><a href="./" target="_self">Go to Home</a></p></div></section>')
        return

    wrapper = "rj-home" if page is site["home"] else ""
    show(f'<div class="{wrapper}">'
         + render_banner(page["title"], page["banner"], page["header_style"])
         + render_sections(page["sections"]) + "</div>")


main()
