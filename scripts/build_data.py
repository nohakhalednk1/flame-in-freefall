"""
Flame in Freefall - data pipeline
=================================
Reads the raw NASA PSI files in data/raw/ and writes one clean file,
site/data.js, that the website loads.

Run from the project folder:
    python scripts/build_data.py

Only the Python standard library is used, so there is nothing to install.

Sources (NASA Physical Sciences Informatics, https://psi.nasa.gov):
  PSI-117  droplet combustion on the ISS (analyzed data from 4 papers)
  PSI-98   Saffire-1   (large fabric fire inside a Cygnus spacecraft)
  PSI-99   Saffire-2   (9 material samples, space vs. Earth)
  PSI-100  Saffire-3   (setup only, no results in the table)
  PSI-25   BASS-II     (129 solid-fuel burns on the ISS, gas readings)
"""

import csv
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "docs" / "data.js"


# ---------------------------------------------------------------- helpers
def read_rows(name):
    """Read a CSV file as a list of rows (handles the BOM some files have)."""
    with open(RAW / name, encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f))


def num(value):
    """Turn a cell into a float, or None if it is empty or not a number."""
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def pairs(rows, xcol, ycol, start=1, stop=None, transform=None):
    """Collect (x, y) number pairs from two columns, skipping blanks."""
    out = []
    for row in rows[start:stop]:
        if len(row) <= max(xcol, ycol):
            continue
        x, y = num(row[xcol]), num(row[ycol])
        if x is None or y is None:
            continue
        out.append((x, transform(y) if transform else y))
    return out


def thin(points, target=160):
    """Keep about `target` evenly spaced points so the site stays fast."""
    if len(points) <= target:
        return points
    step = len(points) / target
    kept = [points[int(i * step)] for i in range(target)]
    if kept[-1] != points[-1]:
        kept.append(points[-1])
    return kept


def xy(points, digits=4):
    """Split points into the {x: [...], y: [...]} shape Plotly expects."""
    return {
        "x": [round(p[0], digits) for p in points],
        "y": [round(p[1], digits) for p in points],
    }


DOI = {
    "proci2019a": "https://doi.org/10.1016/j.proci.2018.05.151",
    "proci2019b": "https://doi.org/10.1016/j.proci.2018.09.015",
    "proci2023": "https://doi.org/10.1016/j.proci.2022.07.094",
    "mst2024": "https://doi.org/10.1007/s12217-024-10115-x",
}


# ------------------------------------------------- 1. the vanishing flame
def burn_history():
    rows = read_rows("PSI-117_Analyzed_Data_MST_2024_Burning_history_Flame_diameter.csv")

    droplet = pairs(rows, 1, 2, transform=math.sqrt)  # file gives d^2, we want d

    # Flame diameter: the column holds two series stacked on top of each other.
    # We keep the first one (time keeps increasing until it jumps back).
    flame_all = pairs(rows, 4, 5)
    flame = [flame_all[0]]
    for p in flame_all[1:]:
        if p[0] < flame[-1][0]:
            break
        flame.append(p)

    # Model: skip the ignition transient (first 0.2 s) and stop at burnout.
    model = [p for p in pairs(rows, 13, 15) if p[0] > 0.2]
    end = min(range(len(model)), key=lambda i: model[i][1])
    model = model[: end + 1]

    # Hot-flame extinction = the biggest drop in measured flame diameter.
    drops = [(flame[i][1] - flame[i + 1][1], i) for i in range(len(flame) - 1)]
    _, i = max(drops)
    t_hot_out = (flame[i][0] + flame[i + 1][0]) / 2

    # Burnout = first time the droplet stops shrinking (diameter < 0.81 mm).
    t_end = next(t for t, d in droplet if d < 0.81)

    return {
        "droplet": xy(droplet),
        "flame": xy(flame),
        "model": xy(thin(model, 120)),
        "t_hot_out": round(t_hot_out, 1),
        "t_end": round(t_end, 1),
        "invisible_seconds": round(t_end - t_hot_out, 1),
        "ratio": round((t_end - t_hot_out) / t_hot_out, 1),
        "fuel": "n-dodecane",
        "d0_mm": 4.0,
        "pressure_atm": 1,
        "source": DOI["mst2024"],
    }


# ------------------------------------------- 2. when does the flame die?
def extinction_by_fuel():
    rows = read_rows("PSI-117_Analyzed_Data_PROCI_2023_Alkane_Extinction_Diameter_1atm.csv")
    header, kind_row = rows[0], rows[1]
    names = {"C7": "n-heptane", "C10": "n-decane", "C12": "n-dodecane"}
    out = {}
    for c in range(0, len(header), 5):
        fuel = header[c].strip()
        if fuel not in names:
            continue
        kind = "expt" if kind_row[c].strip().lower().startswith("exp") else "model"
        hot, cool = [], []
        for row in rows[1:]:
            d0 = num(row[c + 1]) if len(row) > c + 1 else None
            hf = num(row[c + 2]) if len(row) > c + 2 else None
            cf = num(row[c + 3]) if len(row) > c + 3 else None
            if d0 is None:
                continue
            if hf:  # zero means no flame / not observed
                hot.append((d0, hf))
            if cf:
                cool.append((d0, cf))
        out.setdefault(names[fuel], {})[kind] = {
            "hot": xy(sorted(hot)),
            "cool": xy(sorted(cool)),
        }
    return {"fuels": out, "pressure_atm": 1, "source": DOI["proci2023"]}


# ------------------------------------------------ 3. cool flames that pulse
def cool_flames():
    def load(name):
        rows = read_rows(name)
        tmax = [p for p in pairs(rows, 0, 3) if p[0] >= 0.02]
        diam = pairs(rows, 0, 1)
        return {"tmax": xy(tmax), "diameter": xy(thin(diam, 120))}

    stable = load("PSI-117_Analyzed_Data_PROCI_2019_Stable_Cool.csv")
    pulsing = load("PSI-117_Analyzed_Data_PROCI_2019_Oscillatory_Cool_Flame.csv")

    # Count the pulses: local temperature peaks above 735 K.
    t, y = pulsing["tmax"]["x"], pulsing["tmax"]["y"]
    peaks = sum(
        1 for i in range(1, len(y) - 1) if y[i] > 735 and y[i] >= y[i - 1] and y[i] > y[i + 1]
    )
    return {
        "stable": {**stable, "o2_percent": 21},
        "pulsing": {**pulsing, "o2_percent": 10, "pulses": peaks},
        "fuel": "n-heptane",
        "d0_mm": 0.5,
        "kind": "simulation",
        "source": DOI["proci2019a"],
    }


# ------------------------------------------------------ 4. pressure matters
def pressure():
    rows = read_rows("PSI-117_Analyzed_Data_PROCI_2023_C12_Extinction_Diameter_vs_pressure.csv")
    hot_expt = pairs(rows, 0, 1)
    hot_model = pairs(rows, 3, 4)
    cool_expt_all = pairs(rows, 6, 7)
    cool_model = pairs(rows, 9, 10)
    hi = dict(pairs(rows, 12, 13))
    lo = dict(pairs(rows, 15, 16))

    cool_expt = [p for p in cool_expt_all if p[1] > 0]
    no_cool = sorted({p[0] for p in cool_expt_all if p[1] == 0})
    ranges = [{"p": p, "lo": lo[p], "hi": hi[p]} for p in sorted(hi) if hi[p] > 0]

    mst = read_rows("PSI-117_Analyzed_Data_MST_2024_Dext.csv")
    cool_mst = pairs(mst, 6, 7)

    k = read_rows("PSI-117_Analyzed_Data_MST_2024_Kavg.csv")
    k_expt = pairs(k, 1, 2)
    k_model = sorted(pairs(k, 5, 6))

    rad = read_rows("PSI-117_Analyzed_Data_MST_2024_Radiance_Flame_Diameter.csv")
    radiance = {
        "low": {"expt": xy(pairs(rad, 1, 2)), "model": xy(thin(pairs(rad, 16, 17), 120))},
        "high": {"expt": xy(pairs(rad, 8, 9)), "model": xy(thin(pairs(rad, 20, 21), 120))},
    }

    return {
        "extinction": {
            "hot_expt": xy(hot_expt),
            "hot_model": xy(hot_model),
            "cool_expt": xy(cool_expt),
            "cool_expt_mst": xy(cool_mst),
            "cool_model": xy(cool_model),
            "cool_ranges": ranges,
            "no_cool_flame_at": no_cool,
            "source": DOI["proci2023"],
        },
        "burning_rate": {
            "expt": xy(k_expt),
            "model": xy(k_model),
            "source": DOI["mst2024"],
        },
        "radiance": {**radiance, "low_atm": 0.5, "high_atm": 5, "source": DOI["mst2024"]},
        "fuel": "n-dodecane",
    }


# -------------------------------------------------- 5. three-stage burning
def three_stage():
    rows = read_rows("PSI-117_Analyzed_Data_PROCI_C12_2019_Three_Stage.csv")
    radiance = [p for p in pairs(rows, 12, 13) if p[0] >= 0]
    droplet = pairs(rows, 1, 2)
    model_rad = pairs(rows, 39, 40)
    model_drop = thin(pairs(rows, 35, 36), 140)

    # Stage boundaries, read from the measured radiance:
    # end of the first hot flame = biggest early drop; re-ignition = the late peak.
    early = [p for p in radiance if p[0] < 0.8]
    drops = [(early[i][1] - early[i + 1][1], i) for i in range(len(early) - 1)]
    _, i = max(drops)
    first_out = (early[i][0] + early[i + 1][0]) / 2
    late = [p for p in radiance if p[0] > 1.0]
    reignite = max(late, key=lambda p: p[1])

    d0 = 4.5  # mm, from the ReadMe
    return {
        "radiance": xy(radiance),
        "droplet": xy(thin(droplet, 140)),
        "model_radiance": xy(model_rad),
        "model_droplet": xy(model_drop),
        "first_out": round(first_out, 2),
        "reignite": round(reignite[0], 2),
        "reignite_peak_w": round(reignite[1], 1),
        "first_out_s": round(first_out * d0 * d0, 0),
        "reignite_s": round(reignite[0] * d0 * d0, 0),
        "d0_mm": d0,
        "pressure_atm": 2.75,
        "fuel": "n-dodecane",
        "source": DOI["proci2019b"],
    }


# ---------------------------------------------------------- 6. Saffire
def saffire():
    s1 = read_rows("PSI-98_Experimental_table_SAFFIRE-1.csv")
    runs = []
    for row in s1[1:]:
        if not row or not row[0].strip().startswith("S"):
            continue
        runs.append({
            "sample": row[0].strip(),
            "material": row[1].strip(),
            "flow_cm_s": num(row[5]),
            "burn_s": num(row[9]),
            "direction": row[10].strip(),
        })

    s2 = read_rows("PSI-99_Experimental_table_SAFFIRE-2.csv")
    samples, material = [], ""
    for row in s2[1:]:
        if not re.match(r"2-\d", row[0].strip()):
            continue
        material = row[1].strip() or material  # blank cell = same as row above
        thickness = row[2].strip()
        thickness = re.sub(r"^0?(\d{2,}) mm$", lambda m: f"0.{m.group(1)} mm", thickness)  # "037 mm" -> "0.37 mm"
        samples.append({
            "sample": row[0].strip(),
            "material": material,
            "thickness": thickness,
            "direction": row[10].strip(),
            "burn_time": row[9].strip(),
            "space_burn_length": row[11].strip(),
            "space_spread_rate": row[12].strip(),
            "earth_burn_length": row[13].strip(),
            "earth_spread_rate": row[14].strip(),
        })

    notes = [r[0] for r in s2 if r and r[0].startswith("Note")]

    s3 = read_rows("PSI-100_Experimental_table_SAFFIRE-3.csv")
    s3_flow = sorted({r[5].strip() for r in s3[1:] if len(r) > 5 and r[5].strip()})

    return {"saffire1": runs, "saffire2": samples, "saffire2_notes": notes, "saffire3_flow": s3_flow}


# ---------------------------------------------------------- 7. BASS-II gases
def bass2():
    rows = read_rows("PSI-25_Experimental_table_BASS-II.csv")

    def group(text):
        t = text.lower()
        if "nomex" in t:
            return "Nomex"
        if "sibal" in t:
            return "Cotton-fiberglass fabric"
        if "candle" in t:
            return None
        if "rod" in t:
            return "PMMA rod (6-13 mm)"
        if "film" in t or "micron" in t or re.search(r"0\.[12] mm", t):
            return "PMMA film (0.1-0.4 mm)"
        if "pmma" in t or "slab" in t:
            return "PMMA sheet (1-5 mm)"
        return None

    tests = []
    for row in rows[1:]:
        if len(row) < 17:
            continue
        g = group(row[5])
        co0, co1 = num(row[15]), num(row[16])
        if g is None or co0 is None or co1 is None:
            continue
        tests.append({"id": row[1].strip(), "group": g, "co_rise": co1 - co0, "o2": num(row[11])})

    def median(v):
        v = sorted(v)
        n = len(v)
        return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2

    order = ["Nomex", "PMMA film (0.1-0.4 mm)", "Cotton-fiberglass fabric", "PMMA rod (6-13 mm)", "PMMA sheet (1-5 mm)"]
    groups = []
    for g in order:
        v = [t["co_rise"] for t in tests if t["group"] == g]
        groups.append({"group": g, "n": len(v), "median": median(v), "values": v})

    text = [(r[8] + " " + r[10]).lower() for r in rows[1:]]
    extinguished = sum(1 for t in text if "ext" in t)
    return {"groups": groups, "tests_total": len(rows) - 1, "extinguished_by_low_flow": extinguished}


def main():
    data = {
        "burn": burn_history(),
        "extinction": extinction_by_fuel(),
        "cool": cool_flames(),
        "pressure": pressure(),
        "threeStage": three_stage(),
        "saffire": saffire(),
        "bass2": bass2(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        "// Generated by scripts/build_data.py - do not edit by hand.\n"
        "window.FLAME_DATA = " + json.dumps(data, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    b, ts, bass = data["burn"], data["threeStage"], data["bass2"]
    print(f"Wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")
    print(f"  visible flame out at {b['t_hot_out']} s, burnout at {b['t_end']} s "
          f"-> {b['invisible_seconds']} s invisible ({b['ratio']}x)")
    print(f"  three-stage: first flame out t/d0^2={ts['first_out']} (~{ts['first_out_s']:.0f} s), "
          f"re-ignition t/d0^2={ts['reignite']} (~{ts['reignite_s']:.0f} s, {ts['reignite_peak_w']} W)")
    print(f"  cool-flame pulses: {data['cool']['pulsing']['pulses']}")
    for g in bass["groups"]:
        print(f"  BASS-II {g['group']}: n={g['n']} median CO rise {g['median']:.0f} ppm")
    print(f"  BASS-II tests ending in extinction at low flow: {bass['extinguished_by_low_flow']}")


if __name__ == "__main__":
    main()
