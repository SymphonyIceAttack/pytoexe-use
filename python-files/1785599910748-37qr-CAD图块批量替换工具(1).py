# -*- coding: utf-8 -*-
import os
import sys
import time
import traceback
import shutil
import subprocess
import csv
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

# PyQt6 导入
from PyQt6.QtWidgets import (
	QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
	QPushButton, QLabel, QLineEdit, QTextEdit, QFileDialog,
	QGroupBox, QGridLayout, QCheckBox, QSpinBox, QDoubleSpinBox,
	QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView,
	QTabWidget, QSplitter, QMessageBox, QFrame
)
from PyQt6.QtCore import (
	Qt, QThread, pyqtSignal, QTimer, QCoreApplication
)
from PyQt6.QtGui import QFont, QTextCursor, QIcon, QColor

# AutoCAD COM 相关
import pythoncom
import win32com.client
from win32com.client import dynamic

# ============================================================
# 原始功能代码 (完全保留，只做极小调整)
# ============================================================

# ============================================================
# Configuration (路径配置)
# ============================================================
WORKSPACE = Path(__file__).resolve().parent
SOURCE_DIR = WORKSPACE 
OUTPUT_DIR = WORKSPACE 
A3_ORIG_PATH = WORKSPACE 
TEMP_BASE = Path(r"C:\Temp\cad_tk_replace")
TEMP_SRC = TEMP_BASE / "src"
TEMP_SCRIPT = TEMP_BASE / "script"
TEMP_A3_PATH = TEMP_BASE 
RUN_RECORD_DIR = WORKSPACE / "运行记录"

OLD_BLOCK_NAME = ""
NEW_BLOCK_NAME = "" 
OVERWRITE_OUTPUT = True
FORCE_CORE_CONSOLE = True
CORE_CONSOLE_WORKERS = min(4, max(1, (os.cpu_count() or 2) // 2))
CORE_CONSOLE_TIMEOUT = 180

# ============================================================
# 直接指定 accoreconsole.exe 的绝对路径（最高优先级）
# ============================================================
CUSTOM_ACCORE_PATH = ""

# ============================================================
# 比例修正系数 (半宽旧图框 -> 标准新图框，填 0.5)
# ============================================================
SCALE_CORRECTION_RATIO = 0.5 

# 全局变量用于GUI日志
GUI_LOG_CALLBACK = None


def log(msg):
	"""控制台和日志文件同步记录 - 支持GUI回调"""
	line = f"[{time.strftime('%H:%M:%S')}] {msg}"
	print(line, flush=True)
	try:
		RUN_RECORD_DIR.mkdir(parents=True, exist_ok=True)
		with LOG_FILE.open("a", encoding="utf-8-sig") as f:
			f.write(line + "\n")
	except Exception:
		pass
	# GUI回调
	if GUI_LOG_CALLBACK:
		try:
			GUI_LOG_CALLBACK(line)
		except Exception:
			pass


def make_result(file_name, mode, status, found_refs=0, output_path="", message=""):
	return {
		"文件名": file_name,
		"处理方式": mode,
		"结果": status,
		"替换图框数": found_refs,
		"输出文件": str(output_path),
		"说明": message,
	}


def write_results_csv(rows):
	RUN_RECORD_DIR.mkdir(parents=True, exist_ok=True)
	headers = ["文件名", "处理方式", "结果", "替换图框数", "输出文件", "说明"]
	with RESULT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
		writer = csv.DictWriter(f, fieldnames=headers)
		writer.writeheader()
		writer.writerows(rows)


def create_point(x: float, y: float, z: float = 0.0):
	"""创建 COM 兼容的三维坐标点"""
	return win32com.client.VARIANT(pythoncom.VT_ARRAY | pythoncom.VT_R8, (x, y, z))


# ============================================================
# 健壮的 CAD 连接与文档引擎
# ============================================================
def get_cad_app():
	prog_ids = [
		"AutoCAD.Application", "AutoCAD.Application.26", "AutoCAD.Application.25", "AutoCAD.Application.24.3",
		"AutoCAD.Application.24.2", "AutoCAD.Application.24.1", "AutoCAD.Application.24",
		"AutoCAD.Application.23.1", "AutoCAD.Application.23", "AutoCAD.Application.22",
		"Gcad.Application", "Gcad.Application.25", "Gcad.Application.24",
		"ZWCAD.Application", "ZwCAD.Application", "ZWCAD.Application.2026","ZWCAD.Application.2017",
		"ZWCAD.Application.2025", "ZWCAD.Application.2024"
	]

	for pid in prog_ids:
		try:
			acad = win32com.client.GetActiveObject(pid)
			log(f"[OK] 已连接到运行中的 CAD: {pid}")
			return acad
		except Exception:
			continue

	log("[WARN] 尝试强行唤醒或启动新 CAD 实例...")
	last_error = None
	for pid in prog_ids:
		try:
			acad = dynamic.Dispatch(pid)
			acad.Visible = True
			time.sleep(3.0)  
			log(f"[OK] 成功挂载 CAD: {pid}")
			return acad
		except Exception as e:
			last_error = e
			continue
			
	log("[FAIL] 无法连接或启动 CAD，请确认是否已安装或打开软件。")
	if last_error:
		log(f"[INFO] 最后一次连接错误: {last_error}")
	return None


def set_variable(doc, name, value):
	try: doc.SetVariable(name, value)
	except Exception: pass


@contextmanager
def safe_open_document(acad, full_path: Path):
	path_str = str(full_path.resolve())
	doc = None
	
	try:
		set_variable(acad.ActiveDocument, "FILEDIA", 0)
		set_variable(acad.ActiveDocument, "CMDDIA", 0)
	except Exception: pass

	for attempt in range(3):
		try:
			docs = acad.Documents
			if not doc:
				for d in docs:
					try:
						if Path(d.FullName).resolve() == full_path.resolve():
							doc = d
							try: doc.Activate()
							except Exception: pass
							break
					except Exception: continue
				if not doc:
					doc = acad.Documents.Open(path_str, False)
			set_variable(doc, "FILEDIA", 0)
			set_variable(doc, "CMDDIA", 0)
			break 
		except Exception as e:
			if attempt < 2:
				log(f"[WARN] 打开图纸受阻，等待 CAD 重试... ({attempt+1}/3)")
				time.sleep(2.0)
			else:
				log(f"[FAIL] 打开图纸异常: {e}")
	
	try:
		yield doc
	finally:
		try:
			set_variable(acad.ActiveDocument, "FILEDIA", 1)
			set_variable(acad.ActiveDocument, "CMDDIA", 1)
		except Exception: pass
		if doc:
			try:
				time.sleep(0.5)
				doc.Close(False)  
			except Exception: pass


# ============================================================
# 核心业务逻辑 
# ============================================================
def find_block_refs(space, block_name_substring):
	refs = []
	try: count = space.Count
	except Exception: return refs
	for i in range(count):
		try:
			ent = space.Item(i)
			if ent.ObjectName == 'AcDbBlockReference':
				names = []
				try: names.append(ent.EffectiveName)
				except Exception: pass
				try: names.append(ent.Name)
				except Exception: pass
				if any(block_name_substring.upper() in str(name).upper() for name in names):
					refs.append(ent)
		except Exception: continue
	return refs


def iter_drawing_spaces(doc):
	yielded = set()
	candidates = []
	try: candidates.append(("ModelSpace", doc.ModelSpace))
	except Exception: pass
	try: candidates.append(("PaperSpace", doc.PaperSpace))
	except Exception: pass
	try:
		for layout in doc.Layouts:
			try: candidates.append((f"Layout:{layout.Name}", layout.Block))
			except Exception: continue
	except Exception: pass
	for name, space in candidates:
		try: key = str(space.ObjectID)
		except Exception: key = name
		if key in yielded: continue
		yielded.add(key)
		yield name, space


def block_definition_exists(doc, block_name):
	for i in range(doc.Blocks.Count):
		try:
			if doc.Blocks.Item(i).Name.upper() == block_name.upper(): return True
		except Exception: continue
	return False


def collect_attribute_text(block_ref):
	values = {}
	try:
		for attr in block_ref.GetAttributes():
			try: values[str(attr.TagString).upper()] = attr.TextString
			except Exception: continue
	except Exception: pass
	return values


def apply_matching_attribute_text(block_ref, values):
	if not values: return
	try:
		for attr in block_ref.GetAttributes():
			try:
				tag = str(attr.TagString).upper()
				if tag in values: attr.TextString = values[tag]
			except Exception: continue
	except Exception: pass


# ============================================================
# AutoCAD Core Console 后备批处理 (LISP 模式)
# ============================================================
LISP_TEMPLATE = r'''
(defun cadtk-log (msg)
  (princ (strcat "\n[CADTK] " msg))
)

(defun cadtk-val (code data default / pair)
  (setq pair (assoc code data))
  (if pair (cdr pair) default)
)

(defun cadtk-setvar-safe (name value)
  (if (getvar name)
	(setvar name value)
  )
)

(defun cadtk-quiet-mode ()
  (cadtk-setvar-safe "FILEDIA" 0)
  (cadtk-setvar-safe "CMDDIA" 0)
  (cadtk-setvar-safe "ATTDIA" 0)
  (cadtk-setvar-safe "ATTREQ" 0)
  (cadtk-setvar-safe "CMDECHO" 0)
  (cadtk-setvar-safe "EXPERT" 5)
  (cadtk-setvar-safe "PROXYNOTICE" 0)
  (cadtk-setvar-safe "SECURELOAD" 0)
)

(defun cadtk-import-block (a3-path new-name / old-attreq old-cmdecho temp)
  (if (not (tblsearch "BLOCK" new-name))
	(progn
	  (cadtk-log (strcat "Importing " a3-path))
	  (cadtk-quiet-mode)
	  (setq old-attreq (getvar "ATTREQ"))
	  (setq old-cmdecho (getvar "CMDECHO"))
	  (setvar "ATTREQ" 0)
	  (setvar "CMDECHO" 0)
	  (command "_.-INSERT" a3-path "_non" "0,0,0" 1.0 1.0 0.0)
	  (setq temp (entlast))
	  (if temp (entdel temp))
	  (setvar "ATTREQ" old-attreq)
	  (setvar "CMDECHO" old-cmdecho)
	)
  )
  (tblsearch "BLOCK" new-name)
)

(defun cadtk-collect-refs (old / ss refs idx ent data name)
  (setq ss (ssget "_X" '((0 . "INSERT"))))
  (setq refs nil)
  (if ss
	(progn
	  (setq idx 0)
	  (while (< idx (sslength ss))
		(setq ent (ssname ss idx))
		(setq data (entget ent))
		(setq name (strcase (cadtk-val 2 data "")))
		(if (wcmatch name (strcat "*" (strcase old) "*"))
		  (setq refs (cons ent refs))
		)
		(setq idx (1+ idx))
	  )
	)
  )
  (reverse refs)
)

(defun cadtk-replace-one (old new-name ratio index / data ip xs ys zs rot layer layout spaceflag extr ent-data new old-qaflags)
  (setq data (entget old))
  (setq ip (cadtk-val 10 data '(0.0 0.0 0.0)))
  (setq xs (* (cadtk-val 41 data 1.0) ratio))
  (setq ys (* (cadtk-val 42 data 1.0) ratio))
  (setq zs (* (cadtk-val 43 data 1.0) ratio))
  (setq rot (cadtk-val 50 data 0.0))
  (setq layer (cadtk-val 8 data "0"))
  (setq layout (cadtk-val 410 data "Model"))
  (setq spaceflag (assoc 67 data))
  (setq extr (assoc 210 data))
  (cadtk-log
	(strcat
	  "Ref #" (itoa index)
	  " IP=(" (rtos (car ip) 2 2) "," (rtos (cadr ip) 2 2) ")"
	  " Scale=(" (rtos xs 2 6) "," (rtos ys 2 6) ")"
	)
  )
  (setq ent-data
	(list
	  '(0 . "INSERT")
	  '(100 . "AcDbEntity")
	  (cons 8 layer)
	  (cons 410 layout)
	  '(100 . "AcDbBlockReference")
	  (cons 2 new-name)
	  (cons 10 ip)
	  (cons 41 xs)
	  (cons 42 ys)
	  (cons 43 zs)
	  (cons 50 rot)
	)
  )
  (if spaceflag
	(setq ent-data
	  (list
		'(0 . "INSERT")
		'(100 . "AcDbEntity")
		(cons 8 layer)
		spaceflag
		(cons 410 layout)
		'(100 . "AcDbBlockReference")
		(cons 2 new-name)
		(cons 10 ip)
		(cons 41 xs)
		(cons 42 ys)
		(cons 43 zs)
		(cons 50 rot)
	  )
	)
  )
  (if extr (setq ent-data (append ent-data (list extr))))
  
  (setq new (entmakex ent-data))
  (if new
	(progn
	  (setvar "CMDECHO" 0)
	  ;; Use QAFLAGS 1 to force Explode to finish automatically
	  (setq old-qaflags (getvar "QAFLAGS"))
	  (setvar "QAFLAGS" 1)
	  (command "_.explode" new "")
	  (setvar "QAFLAGS" old-qaflags)
	  (entdel old)
	)
	(cadtk-log (strcat "ERROR: failed to create replacement for ref #" (itoa index)))
  )
  new
)

(defun cadtk-save-safe (/ old-cmdecho)
  ;; Use QSAVE to overwrite temp file safely
  (cadtk-quiet-mode)
  (setq old-cmdecho (getvar "CMDECHO"))
  (setvar "CMDECHO" 0)
  (command "_.QSAVE")
  (setvar "CMDECHO" old-cmdecho)
)

(defun cadtk-main (a3-path old-name new-name ratio / refs index)
  (cadtk-quiet-mode)
  (cadtk-log (strcat "Replacing " old-name " -> " new-name))
  (if (not (cadtk-import-block a3-path new-name))
	(progn
	  (cadtk-log (strcat "ERROR: block definition not found: " new-name))
	  (quit)
	)
  )
  (setq refs (cadtk-collect-refs old-name))
  (cadtk-log (strcat "Found " (itoa (length refs)) " reference(s)"))
  (setq index 1)
  (foreach old refs
	(cadtk-replace-one old new-name ratio index)
	(setq index (1+ index))
  )
  (cadtk-log "Saving changes...")
  (cadtk-save-safe)
  (cadtk-log "Done")
  (princ)
)
'''


def find_accoreconsole():
	if "CUSTOM_ACCORE_PATH" in globals() and CUSTOM_ACCORE_PATH:
		custom_path = Path(CUSTOM_ACCORE_PATH)
		if custom_path.exists() and custom_path.is_file():
			return custom_path

	candidates = [
		Path(rf"C:\Program Files\Autodesk\AutoCAD {year}\accoreconsole.exe")
		for year in range(2015, 2028)
	]
	for path in candidates:
		if path.exists(): return path
			
	search_roots = []
	for drive in ["C", "D", "E", "F", "G", "H"]:
		search_roots.extend([
			f"{drive}:\\Program Files\\Autodesk",
			f"{drive}:\\Program Files (x86)\\Autodesk",
			f"{drive}:\\Autodesk",
			f"{drive}:\\Auto CAD"
		])
	for root_path in search_roots:
		root = Path(root_path)
		if root.exists():
			try:
				found = sorted(root.rglob("accoreconsole.exe"))
				if found: return found[0]
			except Exception: continue
	return None


def to_cad_path(path: Path):
	return str(path.resolve()).replace("\\", "/")


def decode_cad_output(raw):
	if not raw: return ""
	for encoding in ("utf-16le", "utf-8", "gbk", "mbcs"):
		try:
			text = raw.decode(encoding, errors="ignore")
			if text.strip(): return text.replace("\x00", "")
		except Exception: continue
	return raw.decode(errors="ignore").replace("\x00", "")


def ensure_clean_temp_dir():
	base = TEMP_BASE.resolve()
	if str(base).lower() in (r"c:\temp", r"c:\\temp", "c:/temp"):
		raise RuntimeError("临时目录配置过宽，已停止清理。")
	if TEMP_BASE.exists():
		shutil.rmtree(TEMP_BASE)
	TEMP_SRC.mkdir(parents=True, exist_ok=True)
	TEMP_SCRIPT.mkdir(parents=True, exist_ok=True)


def write_console_assets():
	lisp_path = TEMP_SCRIPT / "cad_tk_replace.lsp"
	lisp_path.write_text(LISP_TEMPLATE, encoding="utf-8")
	shutil.copy2(A3_ORIG_PATH, TEMP_A3_PATH)
	return lisp_path


def run_console_file(accore_path: Path, lisp_path: Path, temp_src: Path, script_dir: Path):
	script_dir.mkdir(parents=True, exist_ok=True)
	scr_path = script_dir / f"{temp_src.stem}.scr"
	
	scr_lines = [
		"SECURELOAD", "0",
		"FILEDIA", "0",
		"CMDDIA", "0",
		"ATTDIA", "0",
		"ATTREQ", "0",
		"PROXYNOTICE", "0",
		"EXPERT", "5",
		f'(load "{to_cad_path(lisp_path)}")',
		f'(cadtk-main "{to_cad_path(TEMP_A3_PATH)}" "{OLD_BLOCK_NAME}" "{NEW_BLOCK_NAME}" {SCALE_CORRECTION_RATIO})',
		"_.quit",
		""
	]
	scr_path.write_text("\n".join(scr_lines), encoding="utf-8")

	result = subprocess.run(
		[str(accore_path), "/i", str(temp_src), "/s", str(scr_path)],
		cwd=str(script_dir),
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		timeout=CORE_CONSOLE_TIMEOUT,
	)
	output = decode_cad_output(result.stdout)
	found_refs = None
	if result.returncode != 0:
		log(f"  Core Console exit code: {result.returncode}")
	for line in output.splitlines():
		if "[CADTK]" in line or "ERROR" in line.upper():
			log(f"  {line.strip()}")
		if "[CADTK] Found " in line and " reference" in line:
			try:
				found_refs = int(line.split("[CADTK] Found ", 1)[1].split(" reference", 1)[0].strip())
			except Exception: pass
			
	ok = result.returncode == 0 and temp_src.exists() and temp_src.stat().st_size > 0
	return ok, found_refs


def prepare_core_console_jobs(dwg_files):
	jobs = []
	for i, src_path in enumerate(dwg_files):
		temp_name = f"file_{i+1:03d}.dwg"
		temp_src = TEMP_SRC / temp_name
		final_out = OUTPUT_DIR / src_path.name

		shutil.copy2(src_path, temp_src)

		if final_out.exists() and final_out.stat().st_size > 0:
			if OVERWRITE_OUTPUT:
				try:
					final_out.unlink()
				except Exception as e:
					err_msg = f"无法覆盖已有输出文件: {e}"
					log(f"[WARN] {err_msg} 跳过: {final_out.name}")
					jobs.append({
						"index": i + 1, "total": len(dwg_files), "src_path": src_path,
						"temp_src": temp_src, "final_out": final_out,
						"skip": True, "skip_status": "失败", "skip_message": err_msg,
					})
					continue
			else:
				jobs.append({
					"index": i + 1, "total": len(dwg_files), "src_path": src_path,
					"temp_src": temp_src, "final_out": final_out,
					"skip": True, "skip_status": "跳过", "skip_message": "输出文件已存在",
				})
				continue

		jobs.append({
			"index": i + 1, "total": len(dwg_files), "src_path": src_path,
			"temp_src": temp_src, "final_out": final_out,
			"skip": False,
		})
	return jobs


def run_core_console_job(job, accore_path: Path, lisp_path: Path):
	src_path = job["src_path"]
	final_out = job["final_out"]
	if job.get("skip"):
		status = job["skip_status"]
		message = job["skip_message"]
		log(f"[{status}] {src_path.name}: {message}")
		return make_result(src_path.name, "Core Console", status, 0, final_out, message)

	worker_name = f"worker_{job['index']:03d}"
	script_dir = TEMP_SCRIPT / worker_name
	log(f"[START] {job['index']}/{job['total']} {src_path.name}")
	try:
		ok, found_refs = run_console_file(
			accore_path, lisp_path, job["temp_src"], script_dir
		)
		found_refs = found_refs if found_refs is not None else 0
		if ok:
			shutil.copy2(job["temp_src"], final_out)
			log(f"[DONE] {job['index']}/{job['total']} {src_path.name}，替换 {found_refs} 个")
			return make_result(src_path.name, "Core Console", "成功", found_refs, final_out, "")

		log(f"[FAIL] {job['index']}/{job['total']} {src_path.name}: 未生成有效输出文件")
		return make_result(src_path.name, "Core Console", "失败", found_refs, final_out, "未生成有效输出文件")
	except subprocess.TimeoutExpired:
		log(f"[FAIL] {job['index']}/{job['total']} {src_path.name}: Core Console 处理超时")
		return make_result(src_path.name, "Core Console", "失败", 0, final_out, "Core Console 处理超时")
	except Exception as e:
		log(f"[FAIL] {job['index']}/{job['total']} {src_path.name}: {e}")
		return make_result(src_path.name, "Core Console", "失败", 0, final_out, str(e))


def run_with_core_console(dwg_files):
	accore_path = find_accoreconsole()
	if not accore_path:
		log("[FAIL] 未找到 accoreconsole.exe，无法使用无界面批处理备用模式。")
		return None

	log(f"[OK] 使用 AutoCAD Core Console: {accore_path}")
	ensure_clean_temp_dir()
	lisp_path = write_console_assets()

	total = len(dwg_files)
	workers = max(1, min(CORE_CONSOLE_WORKERS, total))
	log(f"[OK] 强制使用无界面批处理模式，并行数量: {workers}")
	log(f"[OK] 已启用弹窗限制及 QAFLAGS 全自动模式")

	jobs = prepare_core_console_jobs(dwg_files)
	result_by_index = {}

	with ThreadPoolExecutor(max_workers=workers) as executor:
		future_map = {
			executor.submit(run_core_console_job, job, accore_path, lisp_path): job
			for job in jobs
		}
		for future in as_completed(future_map):
			job = future_map[future]
			try:
				result_by_index[job["index"]] = future.result()
			except Exception as e:
				src_path = job["src_path"]
				final_out = job["final_out"]
				log(f"[FAIL] {job['index']}/{job['total']} {src_path.name}: {e}")
				result_by_index[job["index"]] = make_result(src_path.name, "Core Console", "失败", 0, final_out, str(e))

	result_rows = [result_by_index[i] for i in sorted(result_by_index)]
	success = sum(1 for row in result_rows if row["结果"] == "成功")
	fail = sum(1 for row in result_rows if row["结果"] == "失败")
	skipped = sum(1 for row in result_rows if row["结果"] == "跳过")

	log(f"\n{'='*60}")
	log(f"CORE CONSOLE COMPLETE! Success: {success}, Failed: {fail}, Skipped: {skipped}")
	log(f"Output Directory: {OUTPUT_DIR}")
	log(f"{'='*60}")
	write_results_csv(result_rows)
	return result_rows


def process_file(acad, src_path: Path, output_path: Path):
	"""处理单张图纸 (COM)"""
	filename = src_path.name
	log(f"Processing: {filename}")

	with safe_open_document(acad, src_path) as doc:
		if not doc:
			return False, 0, "图纸打开失败"
		time.sleep(1.0) 
		try:
			all_refs = []
			seen_handles = set()
			for space_name, space in iter_drawing_spaces(doc):
				for ref in find_block_refs(space, OLD_BLOCK_NAME):
					try: handle = ref.Handle
					except Exception: handle = id(ref)
					if handle in seen_handles: continue
					seen_handles.add(handle)
					all_refs.append((ref, space, space_name))

			if not all_refs:
				log(f"  No '{OLD_BLOCK_NAME}' found — saving as-is")
				doc.SaveAs(str(output_path.resolve()))
				return True, 0, "未找到旧图框，已按原样保存"

			log(f"  Found {len(all_refs)} '{OLD_BLOCK_NAME}' reference(s)")

			if not block_definition_exists(doc, NEW_BLOCK_NAME):
				log(f"  Importing definition from A3.dwg...")
				temp_pt = create_point(0, 0, 0)
				temp_ref = doc.ModelSpace.InsertBlock(temp_pt, str(A3_ORIG_PATH.resolve()), 1.0, 1.0, 1.0, 0.0)
				time.sleep(0.5)
				temp_ref.Delete()
				if not block_definition_exists(doc, NEW_BLOCK_NAME):
					raise RuntimeError(f"无法从 A3.dwg 导入名为 '{NEW_BLOCK_NAME}' 的图块定义")

			for idx, (old_ref, space, space_name) in enumerate(all_refs):
				try:
					ip = old_ref.InsertionPoint
					old_xs = old_ref.XScaleFactor
					old_ys = old_ref.YScaleFactor
					old_zs = old_ref.ZScaleFactor
					rot = old_ref.Rotation
					old_attr_values = collect_attribute_text(old_ref)
					
					new_xs = old_xs * SCALE_CORRECTION_RATIO
					new_ys = old_ys * SCALE_CORRECTION_RATIO
					new_zs = old_zs * SCALE_CORRECTION_RATIO
					
					log(f"  Ref #{idx+1}: IP=({ip[0]:.2f}, {ip[1]:.2f}), Scale changed: {old_xs:.2f} -> {new_xs:.2f}")

					old_ref.Delete()

					new_pt = create_point(ip[0], ip[1], ip[2])
					new_ref = space.InsertBlock(new_pt, NEW_BLOCK_NAME, new_xs, new_ys, new_zs, rot)
					apply_matching_attribute_text(new_ref, old_attr_values)
					
					try:
						new_ref.Explode()
						new_ref.Delete()
						log(f"  Ref #{idx+1} replaced and exploded successfully.")
					except Exception as e_exp:
						log(f"  Ref #{idx+1} explode failed: {e_exp}")
					
				except Exception as e:
					log(f"  Ref #{idx+1} replacement failed: {e}")

			try: acad.Update()
			except Exception: pass
			
			log(f"  Saving to: {output_path.name}")
			doc.SaveAs(str(output_path.resolve()))
			return True, len(all_refs), ""

		except Exception as e:
			log(f"  ERROR processing {filename}: {e}\n{traceback.format_exc()}")
			return False, 0, str(e)


# ============================================================
# PyQt6 GUI 界面
# ============================================================

class WorkerThread(QThread):
	"""后台工作线程"""
	log_signal = pyqtSignal(str)
	progress_signal = pyqtSignal(int, int)  # current, total
	finished_signal = pyqtSignal(list)  # result rows
	error_signal = pyqtSignal(str)
	
	def __init__(self, config: Dict[str, Any]):
		super().__init__()
		self.config = config
		self.is_running = True
		
	def run(self):
		"""执行处理任务"""
		try:
			# 更新全局配置
			global SOURCE_DIR, OUTPUT_DIR, A3_ORIG_PATH, OLD_BLOCK_NAME, NEW_BLOCK_NAME
			global SCALE_CORRECTION_RATIO, FORCE_CORE_CONSOLE, OVERWRITE_OUTPUT
			global CUSTOM_ACCORE_PATH, CORE_CONSOLE_WORKERS, CORE_CONSOLE_TIMEOUT
			
			SOURCE_DIR = Path(self.config.get('source_dir', SOURCE_DIR))
			OUTPUT_DIR = Path(self.config.get('output_dir', OUTPUT_DIR))
			A3_ORIG_PATH = Path(self.config.get('a3_path', A3_ORIG_PATH))
			OLD_BLOCK_NAME = self.config.get('old_block', OLD_BLOCK_NAME)
			NEW_BLOCK_NAME = self.config.get('new_block', NEW_BLOCK_NAME)
			SCALE_CORRECTION_RATIO = self.config.get('scale_ratio', SCALE_CORRECTION_RATIO)
			FORCE_CORE_CONSOLE = self.config.get('force_core_console', FORCE_CORE_CONSOLE)
			OVERWRITE_OUTPUT = self.config.get('overwrite', OVERWRITE_OUTPUT)
			CUSTOM_ACCORE_PATH = self.config.get('accore_path', CUSTOM_ACCORE_PATH)
			CORE_CONSOLE_WORKERS = self.config.get('workers', CORE_CONSOLE_WORKERS)
			CORE_CONSOLE_TIMEOUT = self.config.get('timeout', CORE_CONSOLE_TIMEOUT)
			
			# 设置日志回调
			global GUI_LOG_CALLBACK
			GUI_LOG_CALLBACK = self.log_signal.emit
			
			# 执行处理
			self._run_processing()
			
		except Exception as e:
			self.error_signal.emit(str(e))
			import traceback
			traceback.print_exc()
	
	def _run_processing(self):
		"""实际处理逻辑"""
		# 检查必要的文件
		if not SOURCE_DIR.exists():
			self.error_signal.emit(f"源文件夹不存在: {SOURCE_DIR}")
			return
		if not A3_ORIG_PATH.exists():
			self.error_signal.emit(f"找不到新图框文件: {A3_ORIG_PATH}")
			return
		
		OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
		
		dwg_files = sorted([f for f in SOURCE_DIR.iterdir() if f.is_file() and f.suffix.lower() == '.dwg'])
		
		if not dwg_files:
			self.error_signal.emit(f"没有在 [{SOURCE_DIR}] 中找到任何 .dwg 文件！")
			return
		
		self.progress_signal.emit(0, len(dwg_files))
		
		# 尝试 Core Console 模式
		if FORCE_CORE_CONSOLE:
			self.log_signal.emit("[INFO] 尝试强制使用 AutoCAD Core Console 无界面批处理模式...")
			result_rows = run_with_core_console(dwg_files)
			if result_rows is not None:
				self.progress_signal.emit(len(dwg_files), len(dwg_files))
				self.finished_signal.emit(result_rows)
				return
			self.log_signal.emit("[WARN] 未找到 Core Console 引擎，自动回退到桌面版 COM 模式...")
		
		# COM 模式
		pythoncom.CoInitialize()
		try:
			acad = get_cad_app()
			if not acad:
				self.error_signal.emit("桌面 COM 模式连接失败，程序退出。")
				return
			
			result_rows = []
			total = len(dwg_files)
			
			for i, src_path in enumerate(dwg_files):
				if not self.is_running:
					break
					
				out_path = OUTPUT_DIR / src_path.name
				
				# 检查输出文件是否已存在
				if out_path.exists() and out_path.stat().st_size > 0:
					if OVERWRITE_OUTPUT:
						try:
							out_path.unlink()
						except Exception as e:
							err_msg = f"无法覆盖已有输出文件: {e}"
							self.log_signal.emit(f"[WARN] {err_msg} 跳过: {out_path.name}")
							result_rows.append(make_result(src_path.name, "COM", "跳过", 0, out_path, err_msg))
							self.progress_signal.emit(i + 1, total)
							continue
					else:
						self.log_signal.emit(f"[SKIP] {src_path.name} -- 输出文件已存在")
						result_rows.append(make_result(src_path.name, "COM", "跳过", 0, out_path, "输出文件已存在"))
						self.progress_signal.emit(i + 1, total)
						continue
				
				self.log_signal.emit(f"\n{'='*50}")
				self.log_signal.emit(f"File {i+1}/{total}: {src_path.name}")
				self.log_signal.emit(f"{'='*50}")
				
				ok, found_refs, message = process_file(acad, src_path, out_path)
				if ok:
					result_rows.append(make_result(src_path.name, "COM", "成功", found_refs, out_path, message))
				else:
					result_rows.append(make_result(src_path.name, "COM", "失败", found_refs, out_path, message))
				
				self.progress_signal.emit(i + 1, total)
			
			# 写入结果
			write_results_csv(result_rows)
			
			# 统计
			success = sum(1 for row in result_rows if row["结果"] == "成功")
			fail = sum(1 for row in result_rows if row["结果"] == "失败")
			skipped = sum(1 for row in result_rows if row["结果"] == "跳过")
			replaced = sum(int(row["替换图框数"] or 0) for row in result_rows)
			
			self.log_signal.emit(f"\n{'='*60}")
			self.log_signal.emit(f"COMPLETE! Success: {success}, Failed: {fail}, Skipped: {skipped}")
			self.log_signal.emit(f"总共替换图框: {replaced} 个")
			self.log_signal.emit(f"Output Directory: {OUTPUT_DIR}")
			self.log_signal.emit(f"{'='*60}")
			
			self.finished_signal.emit(result_rows)
			
		finally:
			pythoncom.CoUninitialize()
	
	def stop(self):
		"""停止处理"""
		self.is_running = False


class CADBatchReplaceGUI(QMainWindow):
	"""主窗口"""
	
	def __init__(self):
		super().__init__()
		self.worker = None
		self.result_rows = []
		self.init_ui()
		
	def init_ui(self):
		"""初始化界面"""
		self.setWindowTitle("CAD图块批量替换工具(欢迎关注微信公众号：码海听潮)")
		self.setGeometry(100, 100, 800, 650)
		self.setFixedSize(800, 650)
		
		# 中央部件
		central_widget = QWidget()
		self.setCentralWidget(central_widget)
		main_layout = QVBoxLayout(central_widget)
		
		# 创建分割器
		splitter = QSplitter(Qt.Orientation.Vertical)
		main_layout.addWidget(splitter)
		
		# 上部：配置区域
		config_widget = QWidget()
		config_layout = QVBoxLayout(config_widget)
		
		# 配置分组
		config_group = QGroupBox("配置参数")
		config_grid = QGridLayout(config_group)
		
		# 源文件夹
		config_grid.addWidget(QLabel("源文件夹:"), 0, 0)
		self.source_dir_edit = QLineEdit(str(SOURCE_DIR))
		self.source_dir_edit.setReadOnly(True)
		config_grid.addWidget(self.source_dir_edit, 0, 1)
		btn_source = QPushButton("浏览...")
		btn_source.clicked.connect(self.browse_source_dir)
		config_grid.addWidget(btn_source, 0, 2)
		
		# 输出文件夹
		config_grid.addWidget(QLabel("输出文件夹:"), 1, 0)
		self.output_dir_edit = QLineEdit(str(OUTPUT_DIR))
		self.output_dir_edit.setReadOnly(True)
		config_grid.addWidget(self.output_dir_edit, 1, 1)
		btn_output = QPushButton("浏览...")
		btn_output.clicked.connect(self.browse_output_dir)
		config_grid.addWidget(btn_output, 1, 2)
		
		# A3图框文件
		config_grid.addWidget(QLabel("图框文件:"), 2, 0)
		self.a3_path_edit = QLineEdit(str(A3_ORIG_PATH))
		self.a3_path_edit.setReadOnly(True)
		config_grid.addWidget(self.a3_path_edit, 2, 1)
		btn_a3 = QPushButton("浏览...")
		btn_a3.clicked.connect(self.browse_a3_file)
		config_grid.addWidget(btn_a3, 2, 2)
		
		# 图块名称
		config_grid.addWidget(QLabel("旧图块名称:"), 3, 0)
		self.old_block_edit = QLineEdit(OLD_BLOCK_NAME)
		config_grid.addWidget(self.old_block_edit, 3, 1)
		
		config_grid.addWidget(QLabel("新图块名称:"), 3, 2)
		self.new_block_edit = QLineEdit(NEW_BLOCK_NAME)
		config_grid.addWidget(self.new_block_edit, 3, 3)
		
		# 缩放比例
		config_grid.addWidget(QLabel("缩放比例:"), 4, 0)
		self.scale_spin = QDoubleSpinBox()
		self.scale_spin.setRange(0.01, 10.0)
		self.scale_spin.setSingleStep(0.1)
		self.scale_spin.setValue(SCALE_CORRECTION_RATIO)
		config_grid.addWidget(self.scale_spin, 4, 1)
		
		# 并行数
		config_grid.addWidget(QLabel("并行处理数:"), 4, 2)
		self.workers_spin = QSpinBox()
		self.workers_spin.setRange(1, 16)
		self.workers_spin.setValue(CORE_CONSOLE_WORKERS)
		config_grid.addWidget(self.workers_spin, 4, 3)
		
		# 超时时间
		config_grid.addWidget(QLabel("超时时间(秒):"), 5, 0)
		self.timeout_spin = QSpinBox()
		self.timeout_spin.setRange(30, 600)
		self.timeout_spin.setValue(CORE_CONSOLE_TIMEOUT)
		config_grid.addWidget(self.timeout_spin, 5, 1)
		
		# 选项
		self.overwrite_check = QCheckBox("覆盖已存在的输出文件")
		self.overwrite_check.setChecked(OVERWRITE_OUTPUT)
		config_grid.addWidget(self.overwrite_check, 5, 2)
		
		self.core_console_check = QCheckBox("强制使用Core Console模式")
		self.core_console_check.setChecked(FORCE_CORE_CONSOLE)
		config_grid.addWidget(self.core_console_check, 5, 3)
		
		# Core Console路径
		config_grid.addWidget(QLabel("Core Console路径:"), 6, 0)
		self.accore_path_edit = QLineEdit(CUSTOM_ACCORE_PATH)
		config_grid.addWidget(self.accore_path_edit, 6, 1, 1, 2)
		btn_accore = QPushButton("浏览...")
		btn_accore.clicked.connect(self.browse_accore_file)
		config_grid.addWidget(btn_accore, 6, 3)
		
		config_layout.addWidget(config_group)
		
		# 控制按钮
		btn_layout = QHBoxLayout()
		self.btn_start = QPushButton("开始处理")
		self.btn_start.setStyleSheet("QPushButton { font-weight: bold; font-size: 14px; padding: 8px; }")
		self.btn_start.clicked.connect(self.start_processing)
		btn_layout.addWidget(self.btn_start)
		
		self.btn_stop = QPushButton("停止")
		self.btn_stop.setEnabled(False)
		self.btn_stop.clicked.connect(self.stop_processing)
		btn_layout.addWidget(self.btn_stop)
		
		btn_layout.addStretch()
		
		self.btn_clear_log = QPushButton("清空日志")
		self.btn_clear_log.clicked.connect(self.clear_log)
		btn_layout.addWidget(self.btn_clear_log)
		
		self.btn_export = QPushButton("导出结果")
		self.btn_export.clicked.connect(self.export_results)
		btn_layout.addWidget(self.btn_export)
		
		config_layout.addLayout(btn_layout)
		
		# 进度条
		self.progress_bar = QProgressBar()
		self.progress_bar.setVisible(False)
		config_layout.addWidget(self.progress_bar)
		
		splitter.addWidget(config_widget)
		
		# 下部：日志和结果
		bottom_widget = QWidget()
		bottom_layout = QVBoxLayout(bottom_widget)
		
		tab_widget = QTabWidget()
		
		# 日志标签页
		log_widget = QWidget()
		log_layout = QVBoxLayout(log_widget)
		self.log_text = QTextEdit()
		self.log_text.setFont(QFont("Consolas", 10))
		self.log_text.setReadOnly(True)
		log_layout.addWidget(self.log_text)
		tab_widget.addTab(log_widget, "运行日志")
		
		# 结果标签页
		result_widget = QWidget()
		result_layout = QVBoxLayout(result_widget)
		self.result_table = QTableWidget()
		self.result_table.setColumnCount(6)
		self.result_table.setHorizontalHeaderLabels(["文件名", "处理方式", "结果", "替换图框数", "输出文件", "说明"])
		self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
		self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
		result_layout.addWidget(self.result_table)
		tab_widget.addTab(result_widget, "处理结果")
		
		bottom_layout.addWidget(tab_widget)
		splitter.addWidget(bottom_widget)
		
		# 设置分割比例
		splitter.setSizes([400, 400])
		
		# 初始日志
		self.log("程序启动完成，点击\"开始处理\"运行任务")
		self.log(f"工作目录: {WORKSPACE}")
	
	def log(self, msg: str):
		"""添加日志"""
		self.log_text.append(msg)
		self.log_text.moveCursor(QTextCursor.MoveOperation.End)
		
	def browse_source_dir(self):
		"""浏览源文件夹"""
		dir_path = QFileDialog.getExistingDirectory(self, "选择源文件夹", str(SOURCE_DIR.parent))
		if dir_path:
			self.source_dir_edit.setText(dir_path)
	
	def browse_output_dir(self):
		"""浏览输出文件夹"""
		dir_path = QFileDialog.getExistingDirectory(self, "选择输出文件夹", str(OUTPUT_DIR))
		if dir_path:
			self.output_dir_edit.setText(dir_path)
	
	def browse_a3_file(self):
		"""浏览A3图框文件"""
		file_path, _ = QFileDialog.getOpenFileName(
			self, "选择A3图框文件", str(A3_ORIG_PATH.parent), 
			"DWG Files (*.dwg)"
		)
		if file_path:
			self.a3_path_edit.setText(file_path)
	
	def browse_accore_file(self):
		"""浏览accoreconsole.exe"""
		file_path, _ = QFileDialog.getOpenFileName(
			self, "选择accoreconsole.exe", "",
			"Executable Files (*.exe)"
		)
		if file_path:
			self.accore_path_edit.setText(file_path)
	
	def start_processing(self):
		"""开始处理"""
		# 收集配置
		config = {
			'source_dir': self.source_dir_edit.text(),
			'output_dir': self.output_dir_edit.text(),
			'a3_path': self.a3_path_edit.text(),
			'old_block': self.old_block_edit.text(),
			'new_block': self.new_block_edit.text(),
			'scale_ratio': self.scale_spin.value(),
			'overwrite': self.overwrite_check.isChecked(),
			'force_core_console': self.core_console_check.isChecked(),
			'accore_path': self.accore_path_edit.text(),
			'workers': self.workers_spin.value(),
			'timeout': self.timeout_spin.value(),
		}
		
		# 验证配置
		if not Path(config['source_dir']).exists():
			QMessageBox.warning(self, "警告", f"源文件夹不存在: {config['source_dir']}")
			return
		if not Path(config['a3_path']).exists():
			QMessageBox.warning(self, "警告", f"A3图框文件不存在: {config['a3_path']}")
			return
		
		# 清空旧结果
		self.result_table.setRowCount(0)
		self.result_rows = []
		
		# 禁用按钮
		self.btn_start.setEnabled(False)
		self.btn_stop.setEnabled(True)
		self.progress_bar.setVisible(True)
		self.progress_bar.setValue(0)
		
		# 启动工作线程
		self.worker = WorkerThread(config)
		self.worker.log_signal.connect(self.log)
		self.worker.progress_signal.connect(self.update_progress)
		self.worker.finished_signal.connect(self.on_finished)
		self.worker.error_signal.connect(self.on_error)
		self.worker.start()
	
	def stop_processing(self):
		"""停止处理"""
		if self.worker and self.worker.isRunning():
			self.worker.stop()
			self.log("[INFO] 正在停止处理...")
			self.btn_stop.setEnabled(False)
	
	def update_progress(self, current: int, total: int):
		"""更新进度"""
		if total > 0:
			self.progress_bar.setValue(int(current / total * 100))
			self.progress_bar.setFormat(f"{current}/{total} ({int(current/total*100)}%)")
	
	def on_finished(self, result_rows: list):
		"""处理完成"""
		self.result_rows = result_rows
		self.update_result_table(result_rows)
		
		# 统计信息
		success = sum(1 for row in result_rows if row["结果"] == "成功")
		fail = sum(1 for row in result_rows if row["结果"] == "失败")
		skipped = sum(1 for row in result_rows if row["结果"] == "跳过")
		replaced = sum(int(row["替换图框数"] or 0) for row in result_rows)
		
		self.log(f"\n处理完成! 成功: {success}, 失败: {fail}, 跳过: {skipped}, 替换图框: {replaced}")
		
		# 恢复按钮
		self.btn_start.setEnabled(True)
		self.btn_stop.setEnabled(False)
		self.progress_bar.setVisible(False)
		
		# 显示提示
		QMessageBox.information(
			self, "处理完成",
			f"处理完成!\n\n成功: {success}\n失败: {fail}\n跳过: {skipped}\n替换图框: {replaced}"
		)
	
	def on_error(self, error_msg: str):
		"""错误处理"""
		self.log(f"[ERROR] {error_msg}")
		QMessageBox.critical(self, "错误", error_msg)
		
		self.btn_start.setEnabled(True)
		self.btn_stop.setEnabled(False)
		self.progress_bar.setVisible(False)
	
	def update_result_table(self, rows: list):
		"""更新结果表格"""
		self.result_table.setRowCount(len(rows))
		
		for i, row in enumerate(rows):
			self.result_table.setItem(i, 0, QTableWidgetItem(row["文件名"]))
			self.result_table.setItem(i, 1, QTableWidgetItem(row["处理方式"]))
			
			status_item = QTableWidgetItem(row["结果"])
			if row["结果"] == "成功":
				status_item.setBackground(QColor(200, 255, 200))
			elif row["结果"] == "失败":
				status_item.setBackground(QColor(255, 200, 200))
			else:
				status_item.setBackground(QColor(255, 255, 200))
			self.result_table.setItem(i, 2, status_item)
			
			self.result_table.setItem(i, 3, QTableWidgetItem(str(row["替换图框数"])))
			
			output_item = QTableWidgetItem(str(row["输出文件"]))
			output_item.setToolTip(str(row["输出文件"]))
			self.result_table.setItem(i, 4, output_item)
			
			self.result_table.setItem(i, 5, QTableWidgetItem(row["说明"]))
		
		# 调整列宽
		self.result_table.resizeColumnsToContents()
	
	def clear_log(self):
		"""清空日志"""
		self.log_text.clear()
	
	def export_results(self):
		"""导出结果"""
		if not self.result_rows:
			QMessageBox.information(self, "提示", "没有结果可导出")
			return
		
		file_path, _ = QFileDialog.getSaveFileName(
			self, "导出结果", str(RUN_RECORD_DIR / f"导出结果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"),
			"CSV Files (*.csv)"
		)
		if file_path:
			try:
				write_results_csv(self.result_rows)
				QMessageBox.information(self, "成功", f"结果已导出到:\n{file_path}")
			except Exception as e:
				QMessageBox.critical(self, "错误", f"导出失败: {e}")


def main():
	"""主函数"""
	app = QApplication(sys.argv)
	app.setStyle('Fusion')
	
	window = CADBatchReplaceGUI()
	window.show()
	
	sys.exit(app.exec())


if __name__ == "__main__":
	main()