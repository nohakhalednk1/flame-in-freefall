# Flame in Freefall

NASA Space Apps Challenge 2026 · Challenge: *Flame in Freefall*

A one-page website that turns NASA microgravity combustion data into a story about
fire safety for the Moon and Mars.

## Folders

```
data/raw/            the original files downloaded from NASA PSI
scripts/build_data.py  cleans the raw files and writes docs/data.js
docs/index.html      the website (HTML, CSS, JavaScript, Plotly charts)
docs/data.js         generated data (do not edit by hand)
```

## Run it on your laptop (VS Code)

1. Rebuild the data (only needed if you change the raw files or the script):

   ```
   python scripts/build_data.py
   ```

2. Open the site with a small local server:

   ```
   cd docs
   python -m http.server 8000
   ```

3. Open http://localhost:8000 in your browser.

Nothing needs to be installed: the script uses only the Python standard library.

## Put it online (GitHub Pages, free)

1. Create a new public repository on GitHub and upload this whole folder.
2. In the repository: **Settings → Pages → Build and deployment**.
   Source: *Deploy from a branch*, branch `main`, folder `/docs`, then **Save**.
3. Wait a minute, then open the link GitHub shows. Put this link in your
   Space Apps project submission.

## Data sources (NASA Physical Sciences Informatics, psi.nasa.gov)

| PSI ID  | Experiment | Used for |
|---------|------------|----------|
| PSI-117 | Droplet combustion on the ISS (analyzed data) | vanishing flame, extinction, cool flames, pressure, three-stage burning |
| PSI-98  | Saffire-1 | airflow direction and fire duration |
| PSI-99  | Saffire-2 | which materials burn in space vs. on Earth |
| PSI-100 | Saffire-3 | setup only (no results in the table) |
| PSI-25  | BASS-II | carbon monoxide per material, extinction at low airflow |
| PSI-26  | BASS | test log only (not charted) |
| PSI-22  | ACME E-FIELD | test log only (not charted) |

Papers behind PSI-117:
- https://doi.org/10.1016/j.proci.2018.05.151
- https://doi.org/10.1016/j.proci.2018.09.015
- https://doi.org/10.1016/j.proci.2022.07.094
- https://doi.org/10.1007/s12217-024-10115-x

## Data cleaning notes

- Saffire-2 thickness typos such as `037 mm` are read as `0.37 mm`; blank material
  cells take the material of the row above.
- BASS-II carbon monoxide rise = final CO − initial CO for each test, inside the
  experiment box. Candle and odd-shaped samples are left out.
- In the extinction files a value of 0 means no flame was observed; those points
  are not plotted.
- The three-stage run uses scaled time t/d0²; the site converts it to seconds with
  d0 = 4.5 mm.

## Ask the data (Gemini AI)

The "Ask the data" section sends questions to Google's Gemini API with a
knowledge base of 13 NASA facts built from `docs/data.js`. Gemini is told to
answer only from those facts and to cite them as [K1], [K2]...

- Get a free key at https://aistudio.google.com/apikey
- Paste it into the key field on the site. It is saved only in your browser
  (localStorage) and sent only to Google. It is never in the code or on GitHub.
- No key? The four example questions show pre-written answers from the same
  knowledge base, so the section still works for visitors.
- If a model name stops working, pick another one in the Model menu.
- The preview inside Claude blocks outside connections, so live answers only
  work from GitHub Pages or `python -m http.server` on your laptop.
