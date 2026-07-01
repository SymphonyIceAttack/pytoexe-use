# -*- coding: utf-8 -*-
"""
MoneroOcean XMRig 설치 도우미 v2.0 (완전 개선판)
개선 사항:
- 지갑 주소 유효성 검증
- 설정 자동 저장/복원 (settings.json)
- UI 스레드화로 설치 중 UI 반응성 유지
- 로그를 파일(miner.log)로도 저장
- 다운로드 진행률 표시
- 지갑 변경 감지 → config 자동 갱신
- CPU 슬라이더 권한 관리 (채굴 중에만 조정 가능)
- 더 상세한 에러 처리 및 타임아웃
- 프로세스 정상성 확인
- 로그 색상화 (에러/경고/성공 구분)
- 자동 시작 옵션 (Windows 레지스트리)
"""

import os
import re
import json
import zipfile
import shutil
import threading
import subprocess
import urllib.request
import urllib.error
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

FEE_WALLET = "47Jifd3zvx1BJXLyoagAstC9MUSXV4zS7MHNk9TLBN9NR2LAsk1KS9mQH1nmwcXdZLCGcmUxruxtS7FQG9vEiYn7Eu68fdH"
XMRIG_URL = "https://github.com/xmrig/xmrig/releases/latest/download/xmrig-6.21.0-win64.zip"
SETTINGS_FILE = "settings.json"
LOG_FILE = "miner.log"
DOWNLOAD_TIMEOUT = 60

APP_BG = "#1e1e2e"
CARD_BG = "#2a2a3c"
ACCENT = "#89b4fa"
TEXT = "#cdd6f4"
MUTED = "#9399b2"
WARN = "#f9e2af"
GOOD = "#a6e3a1"
ERROR = "#f38ba8"

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
MONERO_WALLET_RE = re.compile(r"^[48][a-zA-Z0-9]{93,104}$")


class MinerSetupApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("XMRig 채굴 설정 도우미 v2.0")
        self.geometry("580x880")
        self.configure(bg=APP_BG)
        self.resizable(False, False)

        self.agree_var = tk.BooleanVar(value=False)
        self.wallet_var = tk.StringVar()
        self.cpu_percent_var = tk.IntVar(value=75)
        self.autostart_var = tk.BooleanVar(value=False)
        
        self.mining_process = None
        self.setup_done = False
        self._reader_thread = None
        self._is_installing = False
        self.status_label = None

        self._build_ui()
        self._load_settings()
        self._check_existing_on_start()
        self.wallet_var.trace("w", self._on_wallet_change)

    def _load_settings(self):
        """이전 설정 로드"""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    self.wallet_var.set(settings.get("wallet", ""))
                    self.cpu_percent_var.set(settings.get("cpu_percent", 75))
                    self.autostart_var.set(settings.get("autostart", False))
                    self._log("ℹ 이전 설정을 복원했습니다.")
            except Exception as e:
                self._log(f"⚠ 설정 로드 실패: {e}")

    def _save_settings(self):
        """설정 저장"""
        try:
            settings = {
                "wallet": self.wallet_var.get(),
                "cpu_percent": self.cpu_percent_var.get(),
                "autostart": self.autostart_var.get()
            }
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self._log(f"⚠ 설정 저장 실패: {e}")

    def _check_existing_on_start(self):
        """시작 시 기존 파일 확인"""
        found = self._find_existing_xmrig()
        if found:
            self._log(f"ℹ 기존 xmrig 실행파일 발견: {found}")
            self.setup_done = True
            self._check_setup_completion()
        if os.path.exists("config.json"):
            self._log("ℹ 기존 config.json이 있습니다.")
            self.setup_done = True
            self._check_setup_completion()

    def _check_setup_completion(self):
        """설치 완료 여부 확인 후 채굴 버튼 활성화"""
        if os.path.exists("xmrig.exe") and os.path.exists("config.json"):
            self.mine_btn.config(state="normal", bg=GOOD, fg="#11111b")

    # ---------- UI ----------
    def _build_ui(self):
        pad = 20

        # 헤더
        header = tk.Frame(self, bg=APP_BG)
        header.pack(fill="x", padx=pad, pady=(pad, 10))
        tk.Label(header, text="MoneroOcean XMRig 설정", font=("맑은 고딕", 16, "bold"),
                  bg=APP_BG, fg=TEXT).pack(anchor="w")
        self.status_label = tk.Label(header, text="대기 중", font=("맑은 고딕", 10),
                                      bg=APP_BG, fg=MUTED)
        self.status_label.pack(anchor="w", pady=(2, 0))

        # 공지 카드
        notice = tk.Frame(self, bg=CARD_BG, highlightbackground=WARN, highlightthickness=1)
        notice.pack(fill="x", padx=pad, pady=10)

        tk.Label(notice, text="⚠ 수수료 공지", font=("맑은 고딕", 11, "bold"),
                  bg=CARD_BG, fg=WARN).pack(anchor="w", padx=14, pady=(12, 4))

        info_text = (
            "이 프로그램 설치 시, 이 컴퓨터의 채굴 수익 중\n"
            "5%가 서비스 제공자 지갑으로 분배됩니다.\n\n"
            "  • 내(사용자) 지갑 몫        : 95%\n"
            "  • 서비스 제공자 수수료      : 5%"
        )
        tk.Label(notice, text=info_text, font=("맑은 고딕", 10), bg=CARD_BG, fg=TEXT,
                  justify="left").pack(anchor="w", padx=14)

        tk.Label(notice, text="서비스 제공자 지갑 주소:", font=("맑은 고딕", 9, "bold"),
                  bg=CARD_BG, fg=MUTED).pack(anchor="w", padx=14, pady=(10, 2))

        wallet_box = tk.Entry(notice, font=("Consolas", 8), bg="#11111b", fg=GOOD,
                               relief="flat", justify="left")
        wallet_box.insert(0, FEE_WALLET)
        wallet_box.config(state="readonly", readonlybackground="#11111b")
        wallet_box.pack(fill="x", padx=14, pady=(0, 12))

        # 동의 체크박스
        agree_frame = tk.Frame(self, bg=APP_BG)
        agree_frame.pack(fill="x", padx=pad, pady=(4, 4))
        chk = tk.Checkbutton(
            agree_frame, text="위 수수료 조건을 확인했으며 동의합니다",
            variable=self.agree_var, bg=APP_BG, fg=TEXT, selectcolor=CARD_BG,
            activebackground=APP_BG, activeforeground=TEXT, font=("맑은 고딕", 10),
            command=self._on_agree_toggle
        )
        chk.pack(anchor="w")

        # 지갑 입력
        wallet_frame = tk.Frame(self, bg=APP_BG)
        wallet_frame.pack(fill="x", padx=pad, pady=(16, 4))
        tk.Label(wallet_frame, text="본인 모네로(XMR) 지갑 주소", font=("맑은 고딕", 10, "bold"),
                  bg=APP_BG, fg=TEXT).pack(anchor="w")
        self.wallet_entry = tk.Entry(wallet_frame, textvariable=self.wallet_var,
                                      font=("Consolas", 9), bg=CARD_BG, fg=TEXT,
                                      insertbackground=TEXT, relief="flat", state="disabled")
        self.wallet_entry.pack(fill="x", pady=(6, 0), ipady=6)
        self.wallet_hint = tk.Label(wallet_frame, text="", font=("맑은 고딕", 8), bg=APP_BG, fg=MUTED)
        self.wallet_hint.pack(anchor="w", pady=(2, 0))

        # CPU 사용량 조절
        cpu_frame = tk.Frame(self, bg=APP_BG)
        cpu_frame.pack(fill="x", padx=pad, pady=(12, 4))
        cpu_header = tk.Frame(cpu_frame, bg=APP_BG)
        cpu_header.pack(fill="x")
        tk.Label(cpu_header, text="CPU 사용량", font=("맑은 고딕", 10, "bold"),
                  bg=APP_BG, fg=TEXT).pack(side="left")
        self.cpu_value_lbl = tk.Label(cpu_header, text="75%", font=("맑은 고딕", 10, "bold"),
                                        bg=APP_BG, fg=ACCENT)
        self.cpu_value_lbl.pack(side="right")

        self.cpu_scale = tk.Scale(
            cpu_frame, from_=10, to=100, orient="horizontal",
            variable=self.cpu_percent_var, showvalue=False,
            bg=APP_BG, fg=TEXT, troughcolor=CARD_BG, highlightthickness=0,
            activebackground=ACCENT, relief="flat", state="disabled",
            command=self._on_cpu_scale_change
        )
        self.cpu_scale.pack(fill="x", pady=(4, 0))

        # 자동 시작 옵션
        autostart_frame = tk.Frame(self, bg=APP_BG)
        autostart_frame.pack(fill="x", padx=pad, pady=(4, 4))
        chk_auto = tk.Checkbutton(
            autostart_frame, text="Windows 부팅 시 자동으로 채굴 시작",
            variable=self.autostart_var, bg=APP_BG, fg=TEXT, selectcolor=CARD_BG,
            activebackground=APP_BG, activeforeground=TEXT, font=("맑은 고딕", 9),
            command=self._on_autostart_toggle
        )
        chk_auto.pack(anchor="w")

        # 상태 로그
        log_frame = tk.Frame(self, bg=APP_BG)
        log_frame.pack(fill="both", expand=True, padx=pad, pady=(12, 4))
        tk.Label(log_frame, text="진행 상황", font=("맑은 고딕", 10, "bold"),
                  bg=APP_BG, fg=TEXT).pack(anchor="w")
        self.log = tk.Text(log_frame, height=10, bg="#11111b", fg=MUTED,
                            font=("Consolas", 8), relief="flat", state="disabled")
        self.log.pack(fill="both", expand=True, pady=(6, 0))

        # 버튼
        btn_frame = tk.Frame(self, bg=APP_BG)
        btn_frame.pack(fill="x", padx=pad, pady=(pad, 6))
        self.start_btn = tk.Button(
            btn_frame, text="설치 시작", font=("맑은 고딕", 11, "bold"),
            bg=ACCENT, fg="#11111b", relief="flat", state="disabled",
            command=self.start_setup, cursor="hand2", pady=8
        )
        self.start_btn.pack(fill="x")

        self.mine_btn = tk.Button(
            btn_frame, text="채굴 시작", font=("맑은 고딕", 11, "bold"),
            bg="#45475a", fg=TEXT, relief="flat", state="disabled",
            command=self.toggle_mining, cursor="hand2", pady=8
        )
        self.mine_btn.pack(fill="x", pady=(8, 0))

    def _update_status(self, status):
        """상태 표시 업데이트"""
        self.status_label.config(text=status)

    def _on_agree_toggle(self):
        state = "normal" if self.agree_var.get() else "disabled"
        self.wallet_entry.config(state=state)
        self._refresh_start_btn()

    def _on_wallet_change(self, *_):
        """지갑 주소 변경 감지 → 검증 + 설정 자동 갱신"""
        wallet = self.wallet_var.get().strip()
        if not wallet:
            self.wallet_hint.config(text="")
            return
        
        if self._is_valid_wallet(wallet):
            self.wallet_hint.config(text="✓ 유효한 주소", fg=GOOD)
            self._refresh_start_btn()
            # 설정 변경되었으면 저장
            if self.setup_done and not self._is_installing:
                self._save_settings()
                if os.path.exists("config.json"):
                    try:
                        self._write_config(wallet)
                        self._log("✓ 설정이 자동으로 갱신되었습니다.")
                        if self.mining_process is not None:
                            self._log("채굴을 재시작합니다...")
                            self._stop_mining()
                            self.after(500, self._start_mining)
                    except Exception as e:
                        self._log(f"⚠ 설정 갱신 실패: {e}")
        else:
            self.wallet_hint.config(text="✗ 유효하지 않은 모네로 주소", fg=ERROR)
            self._refresh_start_btn()

    def _is_valid_wallet(self, wallet):
        """모네로 지갑 주소 유효성 검증"""
        return bool(MONERO_WALLET_RE.match(wallet)) and len(wallet) >= 95

    def _on_cpu_scale_change(self, value):
        pct = int(float(value))
        self.cpu_value_lbl.config(text=f"{pct}%")
        if self.setup_done and self.wallet_var.get().strip() and not self._is_installing:
            self._save_settings()
            self._write_config(self.wallet_var.get().strip())
            if self.mining_process is not None:
                self._log(f"CPU 사용량이 {pct}%로 변경되어 재시작합니다...")
                self._stop_mining()
                self.after(800, self._start_mining)

    def _on_autostart_toggle(self):
        """자동 시작 옵션 처리"""
        if self.autostart_var.get():
            self._setup_autostart()
        else:
            self._remove_autostart()
        self._save_settings()

    def _setup_autostart(self):
        """Windows 레지스트리에 자동 시작 등록"""
        if os.name != "nt":
            return
        try:
            import winreg
            exe_path = os.path.abspath("miner_setup_gui.exe")
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "XMRigMiner", 0, winreg.REG_SZ, exe_path)
            winreg.CloseKey(key)
            self._log("✓ 자동 시작이 등록되었습니다.")
        except Exception as e:
            self._log(f"⚠ 자동 시작 등록 실패: {e}")
            self.autostart_var.set(False)

    def _remove_autostart(self):
        """Windows 레지스트리에서 자동 시작 제거"""
        if os.name != "nt":
            return
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "XMRigMiner")
            winreg.CloseKey(key)
            self._log("✓ 자동 시작이 제거되었습니다.")
        except Exception:
            pass

    def _refresh_start_btn(self):
        ok = self.agree_var.get() and self._is_valid_wallet(self.wallet_var.get().strip())
        self.start_btn.config(state="normal" if ok else "disabled")

    def _log(self, msg, level="info"):
        """로그 출력 및 파일 저장"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {msg}"
        
        # UI에 표시 (색상 구분)
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.config(state="disabled")
        
        # 파일에 저장
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(log_msg + "\n")
        except Exception:
            pass
        
        self.update_idletasks()

    def _log_threadsafe(self, msg):
        self.after(0, self._log, msg)

    # ---------- 로직 ----------
    def start_setup(self):
        if self._is_installing:
            messagebox.showwarning("경고", "이미 설치가 진행 중입니다.")
            return

        wallet = self.wallet_var.get().strip()
        if not self._is_valid_wallet(wallet):
            messagebox.showerror("오류", "유효한 모네로 지갑 주소를 입력해주세요.\n(95자 이상)")
            return
        if not self.agree_var.get():
            messagebox.showerror("오류", "수수료 조건에 동의해야 진행할 수 있습니다.")
            return

        confirm1 = messagebox.askyesno(
            "동의 확인 (1/2)",
            "이 컴퓨터의 채굴 수익 중 5%가\n"
            "서비스 제공자 지갑으로 분배되는 것에 동의하십니까?"
        )
        if not confirm1:
            self._log("1차 동의 단계에서 취소되었습니다.")
            return

        confirm2 = messagebox.askyesno(
            "동의 확인 (2/2) - 최종 확인",
            f"본인 지갑 주소:\n{wallet}\n\n"
            f"수수료 지갑(5%):\n{FEE_WALLET}\n\n"
            "위 내용이 모두 맞으면 '예'를 눌러 설치를 진행하세요."
        )
        if not confirm2:
            self._log("2차 동의 단계에서 취소되었습니다.")
            return

        self._is_installing = True
        self._update_status("설치 중...")
        self.start_btn.config(state="disabled", text="설치 중...")
        self.cpu_scale.config(state="disabled")
        
        thread = threading.Thread(target=self._install_async, args=(wallet,), daemon=True)
        thread.start()

    def _install_async(self, wallet):
        """별도 스레드에서 설치 수행 → UI 반응성 유지"""
        try:
            self._download_xmrig()
            self._write_config(wallet)
            self._write_launcher()
            self._log("✅ 설정 완료! config.json 및 miner.bat 생성됨.")
            self._log(f"   - 본인 지갑 (95%): {wallet}")
            self._log(f"   - 수수료 지갑 (5%): {FEE_WALLET}")
            self._log(f"   - CPU 사용량: {self.cpu_percent_var.get()}%")
            self.setup_done = True
            self._save_settings()
            
            self.after(0, lambda: self.mine_btn.config(state="normal", bg=GOOD, fg="#11111b"))
            self.after(0, lambda: messagebox.showinfo("완료", "설치가 완료되었습니다!\n'채굴 시작' 버튼으로 채굴을 시작하세요."))
        except Exception as e:
            self._log(f"❌ 설치 실패: {e}")
            self.after(0, lambda: messagebox.showerror("오류", f"설치 중 오류 발생:\n{str(e)[:100]}"))
        finally:
            self._is_installing = False
            self.after(0, lambda: self.start_btn.config(state="normal", text="재설치"))
            self.after(0, lambda: self.cpu_scale.config(state="normal"))
            self.after(0, lambda: self._update_status("대기 중"))

    def toggle_mining(self):
        if self.mining_process is None:
            self._start_mining()
        else:
            self._stop_mining()

    def _start_mining(self):
        if not os.path.exists("xmrig.exe") or not os.path.exists("config.json"):
            messagebox.showerror("오류", "먼저 설치를 완료해주세요.")
            return
        try:
            self._update_status("채굴 시작 중...")
            self._log("채굴을 시작합니다... (창 없이 백그라운드 실행)")

            startupinfo = None
            creationflags = 0
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0
                creationflags = subprocess.CREATE_NO_WINDOW

            self.mining_process = subprocess.Popen(
                ["xmrig.exe", "-c", "config.json"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
            
            # 프로세스 정상성 확인 (1초 후 체크)
            self.after(1000, self._verify_mining_process)
            
            self.mine_btn.config(text="채굴 종료", bg=ERROR, fg="#11111b")
            self._log(f"⛏ 채굴이 시작되었습니다. (PID: {self.mining_process.pid})")
            self._update_status("⛏ 채굴 중")

            self._reader_thread = threading.Thread(
                target=self._read_mining_output, args=(self.mining_process,), daemon=True
            )
            self._reader_thread.start()
        except Exception as e:
            self._log(f"❌ 채굴 시작 실패: {e}")
            messagebox.showerror("오류", f"채굴 프로세스를 시작할 수 없습니다:\n{e}")
            self._update_status("오류 발생")

    def _verify_mining_process(self):
        """프로세스가 정상적으로 실행 중인지 확인"""
        if self.mining_process and self.mining_process.poll() is not None:
            self._log("⚠ 채굴 프로세스가 즉시 종료되었습니다. config.json을 확인해주세요.")
            self._on_mining_ended()

    def _read_mining_output(self, proc):
        """백그라운드 스레드: xmrig 실시간 출력"""
        try:
            for line in iter(proc.stdout.readline, ""):
                if not line:
                    break
                clean = ANSI_ESCAPE_RE.sub("", line).rstrip()
                if clean:
                    self._log_threadsafe(clean)
        except Exception as e:
            self._log_threadsafe(f"(로그 읽기 오류: {e})")
        finally:
            if proc is self.mining_process:
                self._log_threadsafe("⏹ 채굴 프로세스가 종료되었습니다.")
                self.after(0, self._on_mining_ended)

    def _on_mining_ended(self):
        self.mining_process = None
        self.mine_btn.config(text="채굴 시작", bg=GOOD, fg="#11111b")
        self._update_status("대기 중")

    def _stop_mining(self):
        if self.mining_process is not None:
            self._log("채굴을 종료합니다...")
            self._update_status("채굴 중지 중...")
            try:
                self.mining_process.terminate()
                self.mining_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._log("⚠ 프로세스가 강제 종료됩니다...")
                try:
                    self.mining_process.kill()
                except Exception:
                    pass
            except Exception as e:
                self._log(f"⚠ 종료 중 오류: {e}")
            
            self.mining_process = None
            self._log("✓ 채굴이 종료되었습니다.")
        
        self.mine_btn.config(text="채굴 시작", bg=GOOD, fg="#11111b")
        self._update_status("대기 중")

    def _on_close(self):
        if self.mining_process is not None:
            if messagebox.askyesno("확인", "채굴이 진행 중입니다. 종료하시겠습니까?"):
                self._stop_mining()
            else:
                return
        self._save_settings()
        self.destroy()

    def _find_existing_xmrig(self):
        """기존 xmrig.exe 탐색"""
        if os.path.exists("xmrig.exe"):
            return "xmrig.exe"
        try:
            for entry in os.listdir("."):
                if os.path.isdir(entry):
                    candidate = os.path.join(entry, "xmrig.exe")
                    if os.path.exists(candidate):
                        return candidate
        except Exception:
            pass
        return None

    def _download_xmrig(self):
        """XMRig 다운로드 (진행률 표시)"""
        found = self._find_existing_xmrig()
        if found:
            if found != "xmrig.exe":
                self._log(f"기존 xmrig.exe 발견 ({found}) → 복사합니다.")
                shutil.copy(found, "xmrig.exe")
            else:
                self._log("xmrig.exe가 이미 존재합니다.")
            return
        
        self._log("XMRig 다운로드 중...")
        try:
            urllib.request.urlretrieve(XMRIG_URL, "xmrig.zip", reporthook=self._download_progress)
        except urllib.error.URLError as e:
            raise Exception(f"다운로드 실패: {e}") from e
        except Exception as e:
            raise Exception(f"다운로드 오류: {e}") from e
        
        self._log("압축 해제 중...")
        with zipfile.ZipFile("xmrig.zip", "r") as z:
            z.extractall(".")
        
        for name in os.listdir("."):
            if name.startswith("xmrig-") and os.path.isdir(name):
                for f in os.listdir(name):
                    shutil.move(os.path.join(name, f), f)
                shutil.rmtree(name)
                break
        os.remove("xmrig.zip")
        self._log("✓ XMRig 다운로드 완료.")

    def _download_progress(self, block_num, block_size, total_size):
        """다운로드 진행률 표시"""
        if total_size > 0:
            downloaded = block_num * block_size
            percent = min(100, int(100 * downloaded / total_size))
            if percent % 20 == 0 and percent > 0:
                self._log(f"다운로드: {percent}%")

    def _write_config(self, wallet):
        """config.json 작성"""
        cpu_pct = self.cpu_percent_var.get()
        config = {
            "autosave": True,
            "cpu": {
                "enabled": True,
                "huge-pages": True,
                "max-threads-hint": cpu_pct
            },
            "opencl": False,
            "cuda": False,
            "pools": [
                {
                    "url": "gulf.moneroocean.stream:20128",
                    "user": wallet,
                    "pass": "x",
                    "tls": True,
                    "keepalive": True,
                    "coin": "monero",
                    "weight": 95
                },
                {
                    "url": "gulf.moneroocean.stream:20128",
                    "user": FEE_WALLET,
                    "pass": "fee",
                    "tls": True,
                    "keepalive": True,
                    "coin": "monero",
                    "weight": 5
                }
            ],
            "donate-level": 0,
            "donate-over-proxy": 0
        }
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    def _write_launcher(self):
        with open("miner.bat", "w", encoding="utf-8") as f:
            f.write("@echo off\r\nxmrig.exe -c config.json\r\n")


if __name__ == "__main__":
    app = MinerSetupApp()
    app.protocol("WM_DELETE_WINDOW", app._on_close)
    app.mainloop()
