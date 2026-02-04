<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>V436 Advanced Inspection Tool</title>

<!-- Libraries -->
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

<div class="container">

<header>
<div>
    <h1 style="margin:0">Asebraoui CM4D Tool</h1>
    <p id="subtitle" style="margin:5px 0;color:#64748b">
        Geometry Analyse Support
    </p>
    <p id="routineInfo" style="margin:2px 0;color:#475569;font-weight:bold"></p>
</div>
<div style="text-align:right">
    <div id="stats" style="font-weight:bold">0 / 0 Completed</div>
    <small id="curDate"></small>
</div>
</header>

<div>
<div class="upload-zone" onclick="fileInput.click()">
    <strong>Click to select file</strong> or drag here
    <input id="fileInput" type="file" accept=".csv" hidden>
</div>

<div class="toolbar">
    <input id="search" class="search-input"
           placeholder="Search Feature, Tool, Side, Type..."
           onkeyup="doSearch()">
    <button class="btn btn-excel" onclick="saveExcel()">Excel</button>
    <button class="btn btn-pdf" onclick="window.print()">PDF</button>
</div>
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
        complete: res => buildTable(res.data, e.target.files[0].name)
    });
});

function normalize(v){
    return String(v || "").trim().toLowerCase();
}

function handleEnter(e, input) {
    if (e.key === "Enter") {
        e.preventDefault();
        const inputs = [...document.querySelectorAll(".input-measure")];
        const idx = inputs.indexOf(input);
        if (idx > -1 && idx < inputs.length - 1) {
            inputs[idx + 1].focus();
            inputs[idx + 1].select();
        }
    }
}

function buildTable(rows, name){
    tableBody.innerHTML = "";

    const hIdx = rows.findIndex(r =>
        r.some(c => normalize(c) === "feature")
    );
    if (hIdx < 0) return alert("Header row not found");

    const h = rows[hIdx];
    const idx = n => h.findIndex(c => normalize(c) === normalize(n));

    const c = {
        id: idx("Feature"),
        tool: idx("GAUGE TYPE"),
        hand: idx("SMI Hand"),
        type: idx("SMI Type"),
        routine:idx("Routine"),
        gNom: idx("Gap"),
        gUp: idx("Upper Gap"),
        fNom: idx("Flush"),
        fUp: idx("Upper Flush"),
        stdNom: idx("NOM"),
        stdTol: idx("TOL")
    };
  /* === FIND ROUTINE TEXT ANYWHERE IN CSV === */
let routineValue = "-";

rows.some(row => {
    return row.some(cell => {
        if (typeof cell === "string" && cell.includes("Routine:")) {
            const match = cell.match(/Routine:\s*(.*?)\s*No Subroutine/i);
            if (match && match[1]) {
                routineValue = match[1].trim();
                return true;
            }
        }
        return false;
    });
});

routineInfo.innerText = `Routine: ${routineValue}`;


    let count = 0;

    rows.slice(hIdx + 1).forEach(r => {
        const id = String(r[c.id] || "").trim();
        if (!id || id.toUpperCase().includes("VAR")) return;

        let nom = 0, tol = 0, type = r[c.type] || "-";

        if (r[c.gNom] && r[c.gUp]) {
            nom = +r[c.gNom];
            tol = Math.abs(+r[c.gUp]);
            type = "Gap";
        } else if (r[c.fNom] && r[c.fUp]) {
            nom = +r[c.fNom];
            tol = Math.abs(+r[c.fUp]);
            type = "Flush";
        } else if (c.stdNom >= 0) {
            nom = +r[c.stdNom];
            tol = Math.abs(String(r[c.stdTol] || "0").replace("±",""));
        }

        const lsl = nom - tol;
        const usl = nom + tol;

        tableBody.insertAdjacentHTML("beforeend", `
        <tr>
            <td><b>${id}</b></td>
            <td>${r[c.tool] || "-"}</td>
            <td>${r[c.hand] || "-"}</td>
            <td style="color:#64748b">${type}</td>
            <td>${nom.toFixed(2)}</td>
            <td><b>±${tol.toFixed(2)}</b></td>
            <td>
                <input class="input-measure"
                       type="number"
                       step="0.01"
                       min="${lsl.toFixed(2)}"
                       max="${usl.toFixed(2)}"
                       placeholder="${lsl.toFixed(2)} – ${usl.toFixed(2)}"
                       title="Allowed range: ${lsl.toFixed(2)} to ${usl.toFixed(2)}"
                       oninput="validate(this,${lsl},${usl})"
                       onkeydown="handleEnter(event, this)">
            </td>
            <td><span class="status-pill pending">Pending</span></td>
        </tr>`);
        count++;
    });

    fileInfo.innerText = `File: ${name} (${count} Points)`;
    updateStats();
}

function validate(inp, lsl, usl){
    const v = +inp.value;
    const pill = inp.closest("tr").querySelector(".status-pill");

    if (!inp.value) {
        pill.className = "status-pill pending";
        pill.innerText = "Pending";
    } else if (v >= lsl && v <= usl) {
        pill.className = "status-pill OK";
        pill.innerText = "OK";
    } else {
        pill.className = "status-pill NOK";
        pill.innerText = "NOK";
    }
    updateStats();
}

function updateStats(){
    const inputs = [...document.querySelectorAll(".input-measure")];
    stats.innerText = `${inputs.filter(i => i.value).length} / ${inputs.length} Completed`;
}

function saveExcel(){
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.table_to_sheet(mainTable);
    XLSX.utils.book_append_sheet(wb, ws, "Inspection");
    XLSX.writeFile(
        wb,
        `V436_Inspection_${new Date().toISOString().replace(/[:.]/g,"-")}.xlsx`
    );
}

function doSearch(){
    const q = search.value.toLowerCase();
    [...tableBody.rows].forEach(r => {
        r.style.display = r.innerText.toLowerCase().includes(q) ? "" : "none";
    });
}
</script>

</body>
</html>
