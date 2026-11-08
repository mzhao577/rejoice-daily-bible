# Rejoice! — Daily Bible Enjoyment (Streamlit)

A copy of https://sites.google.com/view/rejoice-him/ that friends in China can open.
Google sites, images, fonts and Drive are blocked there, so every page, banner image,
the logo and the 02-29 audio recording are stored in this folder and served by the app itself.

## Run

    pip install -r requirements.txt
    ./start.sh

Then open http://localhost:8502. (`./start.sh` runs `streamlit run app.py --server.port 8502`
and first stops any old copy still holding that port.)

Pages: `/` (home), `/?p=january` (month), `/?p=january/01-01` (daily reading).

## Files

- `app.py` — the website (sidebar navigation, banners, page content).
- `data/site.json` — all page content scraped from the Google site (home, 12 months, 366 days).
- `static/images/` — banner images and logo; `static/media/` — audio recordings.
- `.streamlit/config.toml` — turns on static file serving and turns off usage telemetry.
- `scripts/scrape_site.py` — re-downloads everything from the Google site if it changes
  (run it from a machine that can reach Google): `python scripts/scrape_site.py`.

## Hosting for users in China

Run it on a server that is reachable from mainland China (for example Alibaba Cloud or
Tencent Cloud, or a Hong Kong / Singapore VPS) with `streamlit run app.py --server.port 80`.
Streamlit Community Cloud (*.streamlit.app) may be slow or unreachable from China.

The daily "NT:" / "OT:" links go to churchinpiscataway.com (as on the original site);
that site is not hosted by Google.
