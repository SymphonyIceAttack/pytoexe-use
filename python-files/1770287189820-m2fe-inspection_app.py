import tkinter as tk
import webbrowser
import tempfile
import os
import sys

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Asebraoui CM4D Tool</title>

<script src="https://cdnjs.cloudflare.com/ajax/libs/PapaParse/5.3.2/papaparse.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>

<style>
body{font-family:Arial;background:#f8fafc;margin:0;padding:20px}
.container{max-width:1200px;margin:auto;background:#fff;padding:20px;border-radius:10px}
.upload{border:2px dashed #ccc;padding:20px;text-align:center;cursor:pointer}
table{width:100%;border-collapse:collapse;margin-top:20px}
th,td{border:1px solid #ddd;padding:8px;font-size:13px}
th{background:#0f172a;color:#fff}
</style>
</head>

<body>
<div class="container">
<h2>Asebraoui CM4D Tool</h2>

<div class="upload" onclick="fileInput.click()">Click to load CSV
<input id="fileInput" type="file" accept=".csv" hidden>
</div>

<table id="tbl">
<thead>
<tr><th>Feature</th><th>Value</th><th>Measured</th></tr>
</thead>
<tbody></tbody>
</table>
</div>

<script>
fileInput.addEventListener("change", e=>{
 Papa.parse(e.target.files[0],{
  skipEmptyLines:true,
  complete:r=>{
   const tb=document.querySelector("tbody");
   tb.innerHTML="";
   r.data.slice(1).forEach(x=>{
    tb.innerHTML+=`<tr>
     <td>${x[0]||""}</td>
     <td>${x[1]||""}</td>
     <td><input></td>
    </tr>`;
   });
  }
 });
});
</script>
</body>
</html>
"""

def main():
    # Skapa temporär HTML-fil
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
    tmp.write(HTML.encode("utf-8"))
    tmp.close()

    # Starta webbläsaren
    webbrowser.open("file://" + tmp.name)

    # Minimal Tk-loop så exe inte stängs
    root = tk.Tk()
    root.withdraw()
    root.mainloop()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        with open("error.log","w") as f:
            f.write(str(e))
