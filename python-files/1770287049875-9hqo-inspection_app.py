import webview
import tempfile
import os

HTML_CONTENT = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V436 Advanced Inspection Tool</title>

<script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.3.2/papaparse.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>

<style>
:root {
    --brand:#0f172a; --accent:#3b82f6;
    --success:#16a34a; --danger:#dc2626; --bg:#f8fafc;
}
body {
    font-family: Inter, sans-serif;
    background:var(--bg); margin:0; padding:20px; color:#334155;
}
.container {
    max-width:1400px; margin:auto; background:white;
    padding:30px; border-radius:12px;
    box-shadow:0 10px 15px -3px rgba(0,0,0,.1);
}
header {
    display:flex; justify-content:space-between; align-items:center;
    border-bottom:2px solid #e2e8f0; padding-bottom:20px; margin-bottom:20px;
}
.upload-zone {
    background:#f1f5f9; border:2px dashed #cbd5e1;
    padding:25px; text-align:center; border-radius:8px;
    margin-bottom:20px; cursor:pointer;
}
.upload-zone:hover { border-color:var(--accent); background:#eff6ff; }
.toolbar { display:flex; gap:10px; margin-bottom:20px; }
.search-input {
    flex-grow:1; padding:12px; border:1px solid #cbd5e1;
    border-radius:6px; font-size:14px;
}
.btn {
    padding:10px 20px; border:none; border-radius:6px;
    cursor:pointer; font-weight:bold; color:white;
}
.btn-excel{background:var(--success)}
.btn-pdf{background:#64748b}

table { width:100%; border-collapse:collapse; font-size:13px; }
th {
    background:var(--brand); color:white; padding:12px;
    position:sticky; top:0; text-align:left;
}
td { padding:8px 12px; border-bottom:1px solid #e2e8f0; }
tr:hover { background:#f8fafc; }

.input-measure {
    width:95px; padding:6px;
    border:1px solid #cbd5e1;
    border-radius:4px;
    text-align:center;
    font-weight:bold;
}
.input-measure::placeholder {
    color:#94a3b8;
    font-weight:normal;
}

.status-pill {
    padding:4px 10px; border-radius:12px;
    font-size:11px; font-weight:bold;
    display:inline-block; min-width:60px; text-align:center;
}
.OK{background:#dcfce7;color:#166534}
.NOK{background:#fee2e2;color:#991b1b}
.pending{background:#f1f5f9;color:#64748b}
</style>
</head>

<body>
<div class="container">

<header>
<div>
    <h1 style="margin:0">Asebraoui CM4D Tool</h1>
    <p style="margin:5px 0;color:#64748b">Geometry Analyse Support</p>
    <p id="routineInfo" style="margin:2px 0;color:#475569;font-weight:bold"></p>
</div>
<div style="text-align:right">
    <div id="stats" style="font-weight:bold">0 / 0 Completed</div>
    <small id="curDate"></small>
</div>
</header>

<div class="upload-zone" onclick="fileInput.click()">
    <strong>Click to select file</strong> or drag here
    <input id="fileInput" type="file" accept=".csv" hidden>
</div>

<div class="toolbar">
    <input id="search" class="search-input" placeholder="Search..." onkeyup="doSearch()">
    <button class="btn btn-excel" onclick="saveExcel()">Excel</button>
    <button class="btn btn-pdf" onclick="window.print()">PDF</button>
</div>

<table id="mainTable">
<thead>
<tr>
<th>Feature ID</th>
<th>TOOL NO.</th>
<th>Side</th>
<th>Type</th>
<th>Nominal</th>
<th>TOL</th>
<th>Measured</th>
<th>Result</th>
</tr>
</thead>
<tbody id="tableBody"></tbody>
</table>

</div>

<script>
curDate.innerText = new Date().toLocaleString();

fileInput.addEventListener("change", e => {
    Papa.parse(e.target.files[0], {
        skipEmptyLines:true,
        complete: res => buildTable(res.data)
    });
});

function buildTable(rows){
    tableBody.innerHTML="";
    rows.slice(1).forEach(r=>{
        tableBody.insertAdjacentHTML("beforeend",`
        <tr>
        <td>${r[0]||""}</td>
        <td>${r[1]||""}</td>
        <td>${r[2]||""}</td>
        <td>${r[3]||""}</td>
        <td>${r[4]||""}</td>
        <td>${r[5]||""}</td>
        <td><input class="input-measure"></td>
        <td><span class="status-pill pending">Pending</span></td>
        </tr>`);
    });
}

function saveExcel(){
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.table_to_sheet(mainTable);
    XLSX.utils.book_append_sheet(wb, ws, "Inspection");
    XLSX.writeFile(wb,"Inspection.xlsx");
}

function doSearch(){
    const q = search.value.toLowerCase();
    [...tableBody.rows].forEach(r=>{
        r.style.display = r.innerText.toLowerCase().includes(q) ? "" : "none";
    });
}
</script>

</body>
</html>
"""

def main():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
        f.write(HTML_CONTENT.encode("utf-8"))
        html_path = f.name

    webview.create_window(
        "Asebraoui CM4D Tool",
        html_path,
        width=1400,
        height=900
    )
    webview.start()

if __name__ == "__main__":
    main()
