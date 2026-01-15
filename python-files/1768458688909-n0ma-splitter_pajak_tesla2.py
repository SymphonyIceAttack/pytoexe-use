#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Web app kecil untuk:
- Mode "Split per Tanggal": 1 file CSV/TSV/TXT di-split per tanggal jadi ZIP.
- Mode "Merge": beberapa file CSV/TSV/TXT digabung jadi 1 CSV.

Cara jalan:
  pip install flask pandas
  python csv_tools_app.py
Buka: http://127.0.0.1:5000
"""

import io
import os
import re
import zipfile

import pandas as pd
from flask import Flask, request, render_template_string, send_file, abort

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 256 * 1024 * 1024  # 256 MB

PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Splitter & Merger CSV</title>
  <style>
    body{font-family:system-ui,Arial,sans-serif;max-width:820px;margin:40px auto;padding:0 16px}
    .card{border:1px solid #ddd;border-radius:12px;padding:18px;margin-bottom:20px}
    input[type=file]{padding:10px;border:1px dashed #aaa;border-radius:8px;width:100%}
    button{padding:10px 16px;border:none;border-radius:10px;background:#111;color:#fff;cursor:pointer}
    button:hover{opacity:.9}
    .hint{color:#666;font-size:13px}
  </style>
</head>
<body>
  <h2>Converter: Split / Gabung CSV</h2>

  <div class="card">
    <h3>1. Split per Tanggal</h3>
    <form method="post" action="/split" enctype="multipart/form-data">
      <p><input type="file" name="file" accept=".csv,.txt,.tsv" required></p>
      <p class="hint">
        Upload 1 file → otomatis dipisah jadi banyak CSV per tanggal.
      </p>
      <p><button type="submit">Upload & Split</button></p>
    </form>
  </div>

  <div class="card">
    <h3>2. Gabungkan Beberapa File</h3>
    <form method="post" action="/merge" enctype="multipart/form-data">
      <p><input type="file" name="files" accept=".csv,.txt,.tsv" multiple required></p>
      <p class="hint">
        Upload banyak file → digabung jadi 1 CSV.<br>
        Kolom disejajarkan berdasarkan nama. Jika ada kolom tanggal, hasil akan diurutkan.
      </p>
      <p><button type="submit">Upload & Merge</button></p>
    </form>
  </div>
</body>
</html>
"""

RANGE_HEADER_RE = re.compile(
    r"pajak\s*:\s*\d{4}-\d{2}-\d{2}\s*-\s*\d{4}-\d{2}-\d{2}", re.I
)

def _read_dataframe_smart(file_storage) -> pd.DataFrame:
    """
    Baca CSV/TSV/TXT dengan:
    - Skip baris pertama jika header 'Pajak: yyyy-mm-dd - yyyy-mm-dd'
    - Deteksi delimiter otomatis
    - Coba encoding UTF-8, fallback CP1252
    """
    raw = file_storage.read()
    if not raw:
        raise ValueError("File kosong.")

    for enc in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError("Gagal decode file (bukan UTF-8 atau CP1252).")

    lines = text.splitlines()
    if not lines:
        raise ValueError("File tidak berisi baris data.")

    skip_first = bool(RANGE_HEADER_RE.search(lines[0]))
    payload = "\n".join(lines[1:] if skip_first else lines)

    df = pd.read_csv(io.StringIO(payload), sep=None, engine="python", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    return df

def _find_datetime_column(df: pd.DataFrame) -> str | None:
    """
    Cari kolom tanggal/waktu.
    """
    cols = list(df.columns)
    lc = [c.lower() for c in cols]

    for i, name in enumerate(lc):
        if "tanggal" in name and ("waktu" in name or "transaksi" in name):
            return cols[i]
    for i, name in enumerate(lc):
        if "tanggal" in name:
            return cols[i]
    for i, name in enumerate(lc):
        if "waktu" in name:
            return cols[i]

    for c in cols:
        try:
            s = pd.to_datetime(df[c], errors="coerce", infer_datetime_format=True)
            if s.notna().mean() >= 0.6:
                return c
        except Exception:
            pass
    return None

def _normalize_datetime_series(series: pd.Series) -> pd.Series:
    dt = pd.to_datetime(series, errors="coerce", infer_datetime_format=True)
    if dt.isna().all():
        raise ValueError("Nilai pada kolom tanggal tidak dapat diparse.")
    return dt

@app.route("/", methods=["GET"])
def index():
    return render_template_string(PAGE)

@app.route("/split", methods=["POST"])
def split():
    if "file" not in request.files:
        abort(400, "Tidak ada file yang diupload.")
    f = request.files["file"]
    if not f or f.filename == "":
        abort(400, "Nama file kosong.")

    try:
        df = _read_dataframe_smart(f)
        dt_col = _find_datetime_column(df)
        if not dt_col:
            raise ValueError("Kolom tanggal/waktu tidak ditemukan.")
        dt_series = _normalize_datetime_series(df[dt_col])
        df[dt_col] = dt_series
        df["_DATE_ONLY_"] = df[dt_col].dt.date

        mem = io.BytesIO()
        with zipfile.ZipFile(mem, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for date_key, group in df.groupby("_DATE_ONLY_"):
                out = group.drop(columns=["_DATE_ONLY_"])
                csv_bytes = out.to_csv(index=False).encode("utf-8-sig")
                zf.writestr(f"trx-{date_key}.csv", csv_bytes)

        mem.seek(0)
        base = os.path.splitext(os.path.basename(f.filename))[0] or "split"
        out_name = f"{base}_per_tanggal.zip"
        return send_file(mem, mimetype="application/zip", as_attachment=True, download_name=out_name)

    except Exception as e:
        return f"Gagal memproses: {e}", 400

@app.route("/merge", methods=["POST"])
def merge():
    if "files" not in request.files:
        abort(400, "Tidak ada file yang diupload.")
    files = request.files.getlist("files")
    if not files:
        abort(400, "Tidak ada file yang dipilih.")

    try:
        dfs = []
        for f in files:
            if f and f.filename:
                df = _read_dataframe_smart(f)
                dfs.append(df)

        if not dfs:
            raise ValueError("Semua file kosong atau gagal dibaca.")

        merged = pd.concat(dfs, ignore_index=True, sort=False)

        # urutkan jika ada kolom tanggal
        dt_col = _find_datetime_column(merged)
        if dt_col:
            merged[dt_col] = _normalize_datetime_series(merged[dt_col])
            merged = merged.sort_values(dt_col, ignore_index=True)

        mem = io.BytesIO()
        merged.to_csv(mem, index=False, encoding="utf-8-sig")
        mem.seek(0)
        out_name = "merged.csv"
        return send_file(mem, mimetype="text/csv", as_attachment=True, download_name=out_name)

    except Exception as e:
        return f"Gagal menggabungkan: {e}", 400

if __name__ == '__main__':
     app.run(debug=True, host='0.0.0.0', port=8005)