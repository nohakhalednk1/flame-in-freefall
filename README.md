<p align="center">
  <img src="docs/img/readme/banner.svg" alt="Flame in Freefall: AI fire-safety insights from NASA microgravity fire data" width="100%">
</p>

<p align="center">
  <a href="https://nohakhalednk1.github.io/flame-in-freefall/"><img src="https://img.shields.io/badge/🚀_Live_website-open-45e0ff?style=for-the-badge&labelColor=0a1022" alt="Live website"></a>
  <img src="https://img.shields.io/badge/NASA_Space_Apps-2026-6aa8ff?style=for-the-badge&labelColor=0a1022" alt="NASA Space Apps 2026">
  <img src="https://img.shields.io/badge/Challenge-Flame_in_Freefall-ff8a3d?style=for-the-badge&labelColor=0a1022" alt="Challenge: Flame in Freefall">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Data-NASA_PSI-0b3d91?style=flat-square" alt="NASA PSI data">
  <img src="https://img.shields.io/badge/ML-Random_Forest_87%25-69e3b0?style=flat-square" alt="ML random forest, 87% accuracy">
  <img src="https://img.shields.io/badge/AI-RAG_+_Gemini-ffc86b?style=flat-square" alt="RAG with Gemini">
  <img src="https://img.shields.io/badge/Languages-English_|_العربية-ff8a76?style=flat-square" alt="English and Arabic">
  <img src="https://img.shields.io/badge/Python-3-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python 3">
  <img src="https://img.shields.io/badge/Charts-Plotly-3f4f75?style=flat-square&logo=plotly&logoColor=white" alt="Plotly">
</p>

---

## 🔥 The problem

On Earth, hot gas rises and a flame stretches into a bright teardrop. In orbit nothing rises, so fire becomes a dim, round, often **invisible** ball.
NASA has lit hundreds of fires on the International Space Station on purpose. The results sit in raw tables that crews and mission planners rarely read.

**Flame in Freefall** turns those tables into one interactive website, two kinds of AI, and a fire card a crew could actually use on the Moon or Mars.

## ✨ What we found in the data

| | Finding | NASA source |
|:-:|---|---|
| 🟠 | The visible flame died at **12.6 s**, but the fuel kept burning inside an invisible cool flame for **33 s more** (2.6× longer). | PSI-117 |
| 🔁 | A flame that went out at 8 s **re-ignited by itself at 26 s**, hotter than before. | PSI-117 |
| 🌬️ | The same fabric burned **420 s** with airflow along the flame and **70 s** against it: **6×** longer. | Saffire-1 |
| ☠️ | Thick plastic raised carbon monoxide **21×** more than thin film. Nomex never ignited. | BASS-II, Saffire-2 |
| 🌍 | An Earth fire test gave a **different result in 5 of 9** samples than the same test in space. | Saffire-2 |

## 🧭 Tour of the website

<table>
<tr>
<td width="50%"><img src="docs/img/readme/hero.jpg" alt="Website home"><br><b>Story + replay.</b> Earth vs orbit candle, a droplet replay driven by ISS measurements with an infrared switch, and 8 data chapters with interactive charts and NASA photos.</td>
<td width="50%"><img src="docs/img/readme/predictor.jpg" alt="Toxic smoke predictor"><br><b>🤖 Toxic smoke predictor (ML).</b> A random forest trained on 111 ISS fires predicts the chance of high carbon monoxide and shows the closest real tests.</td>
</tr>
<tr>
<td><img src="docs/img/readme/ask.jpg" alt="Ask the data"><br><b>💬 Ask the data (RAG).</b> BM25 retrieval picks the matching NASA facts, then Gemini answers only from them and cites each one. Works in English and Arabic.</td>
<td><img src="docs/img/readme/earth-vs-space.jpg" alt="Earth vs space"><br><b>🌍 Earth vs space.</b> Sample by sample, how far each material burned on Earth and in orbit.</td>
</tr>
<tr>
<td><img src="docs/img/readme/fire-card.jpg" alt="Crew fire card"><br><b>🧯 Crew fire card.</b> Six first-response steps, each with the measurement behind it. One click prints it.</td>
<td><b>Also inside</b><br>• Material risk check that says "no data" instead of guessing<br>• Full Arabic version, right to left, one click<br>• "Honest limits" section<br>• Every number links to its dataset or paper</td>
</tr>
</table>

## 🧠 How it works

```mermaid
flowchart LR
    A["🛰️ NASA PSI<br/>13 raw CSV files"]:::nasa --> B["🐍 Python cleaning<br/>build_data.py"]:::py
    B --> C["📦 data.js"]:::data
    A --> M["🤖 scikit-learn<br/>Random forest"]:::ml
    M --> J["📦 model.js<br/>60 trees in JSON"]:::data
    C --> W["🌐 Website<br/>HTML · Plotly · Canvas"]:::web
    J --> W
    C --> K["📚 13 sourced facts"]:::data
    K --> R["🔎 BM25 retrieval"]:::rag
    R --> G["✨ Gemini answer<br/>with citations"]:::rag
    G --> W

    classDef nasa fill:#0b3d91,stroke:#6aa8ff,color:#ffffff
    classDef py fill:#1f3b5c,stroke:#ffd43b,color:#ffffff
    classDef data fill:#0e1630,stroke:#45e0ff,color:#e9eefb
    classDef ml fill:#12382c,stroke:#69e3b0,color:#ffffff
    classDef rag fill:#3d2a08,stroke:#ffc86b,color:#ffffff
    classDef web fill:#3d1a0a,stroke:#ff8a3d,color:#ffffff
```

### 🤖 The machine-learning model

| | |
|---|---|
| **Task** | Will a fire raise CO by more than 100 ppm inside the BASS-II test box? |
| **Data** | 111 BASS-II tests from the ISS (PSI-25) |
| **Inputs** | Material, thickness, oxygen % |
| **Model** | Random forest, 60 trees (scikit-learn), exported to JSON and run in the browser |
| **Check** | 5-fold cross-validation, repeated 10 times, on tests the model never saw |
| **Result** | **87% accuracy**, AUC **0.93** (always guessing "low" scores 67%) |

We first tried predicting the exact CO number. It was barely better than a per-material average, so we switched to the risk question above, which the data supports well.

### 💬 The RAG assistant

1. **Retrieve.** A BM25 search over 13 sourced facts (English, Arabic and Egyptian Arabic keywords) picks the best 4, plus a "what the data does not cover" fact.
2. **Generate.** Only those facts go to Gemini, which must cite them as `[K1]`, `[K5]`… and say so when the data does not cover a question.
3. **Show.** Every answer lists the retrieved facts and their scores. With no API key, the site still shows the retrieved facts.

> 🔐 The Gemini key is typed into the website and saved only in the visitor's browser. It is never in this repository.

## 📂 Data

| PSI ID | Experiment | Used for |
|---|---|---|
| ![](https://img.shields.io/badge/PSI--117-ff8a3d?style=flat-square) | Droplet combustion on the ISS | Invisible cool flames, re-ignition, pressure |
| ![](https://img.shields.io/badge/PSI--98-6aa8ff?style=flat-square) | Saffire-1 | Airflow direction and fire duration |
| ![](https://img.shields.io/badge/PSI--99-45e0ff?style=flat-square) | Saffire-2 | Materials, Earth vs space |
| ![](https://img.shields.io/badge/PSI--25-69e3b0?style=flat-square) | BASS-II | Carbon monoxide, ML model |
| ![](https://img.shields.io/badge/PSI--100,_26,_22-7d88a6?style=flat-square) | Saffire-3, BASS, ACME | Reviewed: setup or logs only, no results |

<details>
<summary><b>🧹 Data cleaning notes</b></summary>

- Saffire-2 thickness typos such as `037 mm` are read as `0.37 mm`; blank material cells take the material of the row above.
- Saffire-2 burn lengths written as words are turned into numbers: `Complete` = 29 cm (the full sample), `~ 0` = 0.
- BASS-II CO rise = final CO − initial CO inside the test box. Candle and spherical samples are left out.
- BASS-II airflow was logged as changing fan settings, so it is not used by the model.
- In the PSI-117 extinction files, 0 means no flame was seen; those points are not plotted.
- The three-stage run uses scaled time t/d₀²; the site converts it with d₀ = 4.5 mm.

</details>

<details>
<summary><b>📄 Papers behind PSI-117</b></summary>

- Cool flames, steady and pulsing: https://doi.org/10.1016/j.proci.2018.05.151
- Three-stage burning: https://doi.org/10.1016/j.proci.2018.09.015
- Extinction size and pressure: https://doi.org/10.1016/j.proci.2022.07.094
- Burn history, burning rate, radiation: https://doi.org/10.1007/s12217-024-10115-x

</details>

## ⚠️ Honest limits

- Small samples: 9 Saffire-2 samples, 2 Nomex tests in BASS-II, 111 tests for the model.
- BASS-II CO was measured in a small test box, not a spacecraft cabin.
- Not tested: lunar or Martian gravity, extinguishers, oxygen above about 22%.
- The fire card, risk check and predictor are rules of thumb, not certified NASA procedures.

## 💻 Run it yourself

```bash
# 1. Rebuild the data (Python standard library only)
python scripts/build_data.py

# 2. Retrain the model (needs numpy and scikit-learn)
pip install numpy scikit-learn
python ml/export.py          # writes docs/model.js and prints the cross-validation scores

# 3. Open the website
cd docs
python -m http.server 8000   # then open http://localhost:8000
```

```
data/raw/               original NASA PSI files
scripts/build_data.py   cleaning → docs/data.js
ml/parse.py             reads BASS-II into model features
ml/export.py            trains, cross-validates and exports the model → docs/model.js
docs/index.html         the website
docs/img/               NASA photos and README images
```

## 👩‍🚀 Built by Team ERU Stellar AI

<p align="center"><sub>Data and photos: NASA Physical Sciences Informatics (psi.nasa.gov) and images.nasa.gov · Built for the NASA Space Apps Challenge 2026</sub></p>
