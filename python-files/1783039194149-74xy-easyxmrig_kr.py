"""
EasyXMRig (한국어판)
----------------------------
XMRig(https://github.com/xmrig/xmrig, 오픈소스 RandomX/CPU 모네로 채굴기)을
로컬에서 손쉽게 설정하고 실행할 수 있게 도와주는 간단한 GUI 도구입니다.

중요 / 안전 안내
- 이 도구는 xmrig.exe를 포함하거나 다운로드하거나 숨기지 않습니다. xmrig.exe는
  공식 XMRig GitHub 릴리스 페이지에서 직접 받아야 합니다:
      https://github.com/xmrig/xmrig/releases
  받은 뒤 이 앱에서 해당 경로를 지정하세요.
- 이 도구는 Windows Defender를 변경하거나, 예약 작업을 추가하거나, 레지스트리에
  기록하거나, 콘솔/창을 숨기지 않습니다. 사용자가 지정한 xmrig.exe 프로세스를
  시작/중지하고 설정 파일을 작성하며, 콘솔 출력을 로그 창에 실시간으로 보여줄
  뿐입니다.
- 본인 소유이거나 사용 권한이 있는 풀 주소·지갑 주소로만 채굴하세요.

개발자 수수료
- 원본 도구와 동일하게, 할당한 CPU 스레드 중 FEE_PERCENT 비율만큼은 본인 지갑이
  아닌 아래 FEE_WALLET로 채굴됩니다(같은 풀 사용). 이 내용은 설정 화면에 표시되고
  채굴 시작 전 확인 대화상자로도 다시 안내됩니다 -- 숨기는 부분은 없습니다.
  FEE_PERCENT를 0으로 설정하면 이 기능을 끄고 100% 본인 지갑으로 채굴합니다.
  (참고: 공식 XMRig는 설정과 무관하게 최소 1%의 개발자 기부금을 강제합니다.)

요구 사항: Python 3.9+, 표준 라이브러리만 사용(tkinter, subprocess, json,
threading) -- 추가 설치 패키지 없음.
"""

import json
import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "EasyXMRig (KR)"
DEFAULT_CONFIG_NAME = "config.json"
FEE_CONFIG_NAME = "config_fee.json"

# Pool is fixed to MoneroOcean and is not user-editable in this build.
POOL_URL = "gulf.moneroocean.stream:20128"
POOL_TLS = False

# Developer fee wallet + percentage. Set FEE_PERCENT = 0 to disable.
FEE_WALLET = "47Jifd3zvx1BJXLyoagAstC9MUSXV4zS7MHNk9TLBN9NR2LAsk1KS9mQH1nmwcXdZLCGcmUxruxtS7FQG9vEiYn7Eu68fdH"
FEE_PERCENT = 5


class EasyXMRig(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("720x560")
        self.minsize(640, 480)

        self.process = None       # subprocess.Popen handle for the user's xmrig
        self.fee_process = None   # subprocess.Popen handle for the fee xmrig
        self.reader_thread = None
        self.fee_reader_thread = None
        self.stop_requested = False

        self._build_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ UI
    def _build_widgets(self):
        pad = {"padx": 8, "pady": 4}

        # --- Miner executable path -----------------------------------
        exe_frame = ttk.LabelFrame(self, text="XMRig 실행 파일")
        exe_frame.pack(fill="x", **pad)

        self.exe_path_var = tk.StringVar()
        ttk.Entry(exe_frame, textvariable=self.exe_path_var).pack(
            side="left", fill="x", expand=True, padx=(8, 4), pady=6
        )
        ttk.Button(exe_frame, text="찾아보기...", command=self._browse_exe).pack(
            side="left", padx=(0, 8), pady=6
        )

        # --- Mining settings -------------------------------------------
        settings_frame = ttk.LabelFrame(self, text="채굴 설정")
        settings_frame.pack(fill="x", **pad)

        self.pool_var = tk.StringVar(value=POOL_URL)
        self.wallet_var = tk.StringVar()
        self.password_var = tk.StringVar(value="x")
        self.threads_var = tk.StringVar(value="")
        self.tls_var = tk.BooleanVar(value=POOL_TLS)
        self.donate_var = tk.StringVar(value="1")

        # Pool is fixed to MoneroOcean -- shown but not editable.
        ttk.Label(settings_frame, text="풀 주소(고정):").grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(settings_frame, textvariable=self.pool_var, state="readonly").grid(
            row=0, column=1, sticky="ew", padx=8, pady=4
        )
        self._labeled_entry(settings_frame, "지갑 주소:", self.wallet_var, 1)
        self._labeled_entry(settings_frame, "비밀번호 / 워커 이름:", self.password_var, 2)
        self._labeled_entry(settings_frame, "CPU 스레드 수(비워두면 자동):", self.threads_var, 3)
        self._labeled_entry(settings_frame, "기부(donate) 비율(%):", self.donate_var, 4)

        ttk.Checkbutton(
            settings_frame, text="TLS 사용", variable=self.tls_var, state="disabled"
        ).grid(row=5, column=1, sticky="w", padx=8, pady=(0, 6))

        settings_frame.columnconfigure(1, weight=1)

        if FEE_PERCENT > 0:
            fee_note = (
                f"Note: {FEE_PERCENT}% of the CPU threads below will mine to the "
                f"developer's fee wallet on the same pool, in addition to your own "
                f"wallet ({100 - FEE_PERCENT}%). See the header comment in this file "
                f"for the fee wallet address, or set FEE_PERCENT = 0 to disable this."
            )
            ttk.Label(settings_frame, text=fee_note, wraplength=640, foreground="#555").grid(
                row=6, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 6)
            )

        # --- Config file actions ---------------------------------------
        config_frame = ttk.Frame(self)
        config_frame.pack(fill="x", **pad)
        ttk.Button(config_frame, text="config.json 저장", command=self._save_config).pack(
            side="left", padx=4
        )
        ttk.Button(config_frame, text="config.json 불러오기", command=self._load_config).pack(
            side="left", padx=4
        )

        # --- Start / stop -------------------------------------------------
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", **pad)

        self.start_button = ttk.Button(control_frame, text="채굴 시작", command=self._start_mining)
        self.start_button.pack(side="left", padx=4)

        self.stop_button = ttk.Button(
            control_frame, text="채굴 중지", command=self._stop_mining, state="disabled"
        )
        self.stop_button.pack(side="left", padx=4)

        self.status_var = tk.StringVar(value="대기 중")
        ttk.Label(control_frame, textvariable=self.status_var).pack(side="left", padx=12)

        # --- Log output -----------------------------------------------
        log_frame = ttk.LabelFrame(self, text="로그")
        log_frame.pack(fill="both", expand=True, **pad)

        self.log_text = tk.Text(log_frame, wrap="word", state="disabled", height=16)
        self.log_text.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y", pady=8, padx=(0, 8))
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _labeled_entry(self, parent, label, var, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=8, pady=4)

    # -------------------------------------------------------------- actions
    def _browse_exe(self):
        path = filedialog.askopenfilename(
            title="xmrig 실행 파일 선택",
            filetypes=[("실행 파일", "*.exe"), ("모든 파일", "*.*")],
        )
        if path:
            self.exe_path_var.set(path)

    def _validate_wallet(self, wallet):
        """Validate Monero wallet address format (basic check).
        Returns (is_valid, error_message)."""
        wallet = wallet.strip()
        if not wallet:
            return False, "지갑 주소를 입력해야 합니다."
        
        # Monero mainnet addresses start with 4 or 8, and are typically 95 chars
        # Stagenet/testnet start with 5 or 9
        # Integrated addresses are longer (~106 chars)
        if wallet[0] not in "456789":
            return False, f"지갑 주소는 4, 5, 8, 또는 9로 시작해야 하는데 '{wallet[0]}'로 시작합니다. 올바른 모네로 주소인가요?"
        
        if len(wallet) < 80 or len(wallet) > 120:
            return False, f"지갑 주소가 너무 짧거나 깁니다({len(wallet)}자). 모네로 주소는 보통 80-120자입니다."
        
        # Check if alphanumeric only
        if not all(c.isalnum() for c in wallet):
            return False, "지갑 주소는 영문·숫자만 포함해야 합니다."
        
        return True, ""

    def _build_config_dict(self, wallet=None):
        """Build an XMRig config dict. If wallet is given, it
        overrides the value from the form (used to build the fee config).
        Threads are passed via command-line -t argument, not config file."""
        wallet = wallet if wallet is not None else self.wallet_var.get().strip()

        config = {
            "autosave": True,
            "cpu": {
                "enabled": True,
            },
            "opencl": False,
            "cuda": False,
            "donate-level": max(1, self._safe_int(self.donate_var.get(), 1)),
            "pools": [
                {
                    "url": self.pool_var.get().strip(),
                    "user": wallet,
                    "pass": self.password_var.get().strip() or "x",
                    "tls": bool(self.tls_var.get()),
                    "keepalive": True,
                }
            ],
        }
        return config

    def _thread_split(self):
        """Split the user-entered thread count (or all CPUs) by FEE_PERCENT
        between the user's wallet and the fee wallet. Returns (user_threads, fee_threads).
        If total threads is too low, fee_threads will be 0."""
        typed = self.threads_var.get().strip()
        try:
            total = int(typed) if typed else (os.cpu_count() or 4)
        except ValueError:
            total = os.cpu_count() or 4
        total = max(1, total)
        if FEE_PERCENT <= 0:
            return total, 0
        # Calculate fee threads; ensure user gets at least 1, fee gets at least 0
        fee = max(0, round(total * FEE_PERCENT / 100))
        if fee >= total:
            fee = max(0, total - 1)
        user = total - fee
        return user, fee

    @staticmethod
    def _safe_int(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _save_config(self):
        if not self.wallet_var.get().strip():
            messagebox.showwarning(APP_TITLE, "먼저 지갑 주소를 입력해 주세요.")
            return
        path = filedialog.asksaveasfilename(
            title="config.json 저장",
            defaultextension=".json",
            initialfile=DEFAULT_CONFIG_NAME,
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._build_config_dict(), f, indent=2)
            self._log(f"설정 파일을 {path}에 저장했습니다")
        except OSError as exc:
            messagebox.showerror(APP_TITLE, f"설정 파일을 저장하지 못했습니다: {exc}")

    def _load_config(self):
        path = filedialog.askopenfilename(
            title="config.json 불러오기", filetypes=[("JSON", "*.json"), ("모든 파일", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_TITLE, f"설정 파일을 불러오지 못했습니다: {exc}")
            return

        pools = data.get("pools") or []
        if pools:
            pool = pools[0]
            # Pool/TLS are intentionally NOT loaded from file -- always MoneroOcean.
            self.wallet_var.set(pool.get("user", ""))
            self.password_var.set(pool.get("pass", "x"))
        self.donate_var.set(str(data.get("donate-level", 1)))
        if isinstance(data.get("threads"), int):
            self.threads_var.set(str(data["threads"]))
        self._log(f"{path}에서 설정을 불러왔습니다")

    def _start_mining(self):
        exe_path = self.exe_path_var.get().strip()
        if not exe_path or not os.path.isfile(exe_path):
            messagebox.showwarning(APP_TITLE, "먼저 올바른 xmrig 실행 파일을 선택해 주세요.")
            return
        
        wallet = self.wallet_var.get().strip()
        if not wallet:
            messagebox.showwarning(APP_TITLE, "먼저 지갑 주소를 입력해 주세요.")
            return
        
        is_valid, error = self._validate_wallet(wallet)
        if not is_valid:
            messagebox.showwarning(APP_TITLE, f"지갑 주소 검증 실패:\n\n{error}")
            return
        
        if self.process is not None:
            messagebox.showinfo(APP_TITLE, "이미 채굴이 실행 중입니다.")
            return

        user_threads, fee_threads = self._thread_split()

        if FEE_PERCENT > 0:
            msg = (
                f"{FEE_PERCENT}% of your CPU threads ({fee_threads} thread(s)) will mine "
                f"to the developer's fee wallet on the same pool. Your wallet will use "
                f"the remaining {user_threads} thread(s).\n\n"
                f"Fee wallet:\n{FEE_WALLET}\n\n"
                f"(Note: Official XMRig enforces 1% developer fee regardless of config,\n"
                f"so your actual total fee will be higher.)\n\n"
                f"Continue?"
            )
            confirmed = messagebox.askyesno(APP_TITLE, msg)
            if not confirmed:
                return

        exe_dir = os.path.dirname(exe_path)

        # Write config.json (user) next to the executable so xmrig auto-loads it.
        config_path = os.path.join(exe_dir, DEFAULT_CONFIG_NAME)
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self._build_config_dict(), f, indent=2)
        except OSError as exc:
            messagebox.showerror(APP_TITLE, f"실행 파일 옆에 설정 파일을 쓰지 못했습니다: {exc}")
            return

        fee_config_path = None
        if FEE_PERCENT > 0:
            fee_config_path = os.path.join(exe_dir, FEE_CONFIG_NAME)
            try:
                with open(fee_config_path, "w", encoding="utf-8") as f:
                    json.dump(self._build_config_dict(wallet=FEE_WALLET), f, indent=2)
            except OSError as exc:
                messagebox.showerror(APP_TITLE, f"수수료용 설정 파일을 쓰지 못했습니다: {exc}")
                return

        self._log(f"사용자 채굴을 설정 파일 {config_path}로 시작합니다 (스레드 {user_threads}개) ...")
        self.process = self._spawn(exe_path, exe_dir, config_path, threads=user_threads)
        if self.process is None:
            return

        if fee_config_path:
            self._log(f"수수료용 채굴을 설정 파일 {fee_config_path}로 시작합니다 (스레드 {fee_threads}개) ...")
            self.fee_process = self._spawn(exe_path, exe_dir, fee_config_path, threads=fee_threads)

        self.stop_requested = False
        self.status_var.set("채굴 실행 중")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

        self.reader_thread = threading.Thread(
            target=self._read_process_output, args=(self.process, "user"), daemon=True
        )
        self.reader_thread.start()
        if self.fee_process is not None:
            self.fee_reader_thread = threading.Thread(
                target=self._read_process_output, args=(self.fee_process, "fee"), daemon=True
            )
            self.fee_reader_thread.start()

    def _spawn(self, exe_path, exe_dir, config_path, threads=None):
        try:
            cmd = [exe_path, "--config", config_path]
            if threads is not None and threads > 0:
                cmd.extend(["-t", str(threads)])
            
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            return subprocess.Popen(
                cmd,
                cwd=exe_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creationflags,
            )
        except OSError as exc:
            messagebox.showerror(APP_TITLE, f"xmrig를 시작하지 못했습니다: {exc}")
            return None

    def _read_process_output(self, proc, label):
        for line in proc.stdout:
            self._log(f"[{label}] {line.rstrip(chr(10))}")
        return_code = proc.wait()
        if not self.stop_requested:
            self._log(f"[{label}] xmrig가 종료되었습니다 (코드 {return_code}).")
        if label == "user":
            self.process = None
        else:
            self.fee_process = None
        self.after(0, self._on_process_ended)

    def _on_process_ended(self):
        if self.process is None and self.fee_process is None:
            self.status_var.set("대기 중")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

    def _stop_mining(self):
        if self.process is None and self.fee_process is None:
            return
        self.stop_requested = True
        self._log("xmrig를 중지하는 중...")
        for proc in (self.process, self.fee_process):
            if proc is None:
                continue
            try:
                proc.terminate()
            except OSError:
                pass

    def _log(self, message):
        def append():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

        # _log can be called from a background thread; marshal to main thread.
        self.after(0, append)

    def _on_close(self):
        if self.process is not None or self.fee_process is not None:
            if not messagebox.askyesno(APP_TITLE, "채굴이 아직 실행 중입니다. 중지하고 종료할까요?"):
                return
            self._stop_mining()
        self.destroy()


def main():
    app = EasyXMRig()
    style = ttk.Style(app)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    app.mainloop()


if __name__ == "__main__":
    main()
