import sys
import json
import time
import random
import string
import vdf
import jwt
import os
import psutil
import subprocess
import winreg
import stat
import zlib
import win32crypt
import shutil
import base64
import requests
import multiprocessing
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, List
from loguru import logger
import dearpygui.dearpygui as dpg

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    os.environ["PYI_SPLASH_NO_MULTIPROCESSING"] = "1"
    os.environ["DEARPYGUI_DISABLE_MULTIPROCESSING"] = "1"

@dataclass
class SteamPaths:
    install_path: Path
    local_vdf_path: Path
    config_path: Path

class SteamUtils:
    @staticmethod
    def get_steam_paths() -> SteamPaths:
        install_path = SteamUtils._get_steam_install_path()
        local_appdata = SteamUtils._read_registry_value(
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
            "Local AppData",
        )

        return SteamPaths(
            install_path=Path(install_path),
            local_vdf_path=Path(local_appdata) / "Steam" / "local.vdf",
            config_path=Path(install_path) / "config",
        )

    @staticmethod
    def _get_steam_install_path() -> str:
        try:
            # Try direct registry key first
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\WOW6432Node\Valve\Steam",
                0,
                winreg.KEY_READ,
            )
            install_path, _ = winreg.QueryValueEx(key, "InstallPath")
            winreg.CloseKey(key)
            return install_path
        except WindowsError:
            # Fall back to existing methods
            steam_pid = SteamUtils._get_process_pid("steam.exe")
            if steam_pid:
                process = psutil.Process(steam_pid)
                steam_path = process.exe()
                SteamUtils._kill_steam_processes()
                return os.path.dirname(steam_path)

            steam_path = SteamUtils._read_registry_value(
                r"Software\Classes\steam\Shell\Open\Command", ""
            ).strip('"')
            return os.path.dirname(steam_path)

    @staticmethod
    def _kill_steam_processes():
        subprocess.run("taskkill /f /im steam.exe", shell=True)
        subprocess.run("taskkill /f /im steamwebhelper.exe", shell=True)
        time.sleep(2)

    @staticmethod
    def is_steam_running() -> bool:
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] in ['steam.exe', 'steamwebhelper.exe']:
                return True
        return False

    @staticmethod
    def shutdown_steam(steam_path: Path):
        if steam_path.exists():
            subprocess.run(f'"{steam_path}" -shutdown', shell=True)
            time.sleep(2)  # Give it time to shut down

    @staticmethod
    def _get_process_pid(process_name: str) -> int:
        for proc in psutil.process_iter(["name", "pid"]):
            if proc.info["name"] == process_name:
                return proc.info["pid"]
        return 0

    @staticmethod
    def _read_registry_value(key_path: str, value_name: str) -> str:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, value_name)
            winreg.CloseKey(key)
            return value.decode("utf-8") if isinstance(value, bytes) else value
        except Exception:
            return ""

    @staticmethod
    def compute_crc32(data: str) -> str:
        crc32_value = zlib.crc32(data.encode("utf-8"))
        return f"{crc32_value:08x}".lstrip("0")
    
    @staticmethod
    def steamid64_to_friend_code(steamid64: str) -> int:
        try:
            steamid64_int = int(steamid64)
            friend_code = steamid64_int - 76561197960265728
            return friend_code
        except Exception as e:
            logger.error(f"Failed to convert SteamID64 to friend code: {e}")
            return 0

    @staticmethod
    def write_registry_value(key_path: str, value_name: str, value: str):
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, value)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            logger.error(f"Failed to write registry value: {e}")
            return False

class SteamCrypto:

    OBFUSCATE_BUFFER = b"B\x00O\x00b\x00f\x00u\x00s\x00c\x00a\x00t\x00e\x00B\x00u\x00f\x00f\x00e\x00r\x00\x00\x00"

    @classmethod
    def encrypt(cls, token: str, account_name: str) -> str:
        try:
            data = token.encode("utf-8")
            key = account_name.encode("utf-8")
            encrypted = win32crypt.CryptProtectData(
                data, 
                cls.OBFUSCATE_BUFFER.decode("utf-8"), 
                key, 
                None, 
                None, 
                17  # CRYPTPROTECT_UI_FORBIDDEN
            )
            return encrypted.hex()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return ""

    @classmethod
    def decrypt(cls, encrypted_hex: str, account_name: str) -> str:
        try:
            encrypted = bytes.fromhex(encrypted_hex)
            key = account_name.encode("utf-8")
            decrypted = win32crypt.CryptUnprotectData(
                encrypted, 
                key, 
                None, 
                None, 
                0  # CRYPTPROTECT_UI_FORBIDDEN
            )
            return decrypted[1].decode("utf-8")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ""

class SteamFiles:

    @staticmethod
    def save_file(path: Path, content: str):
        try:
            if path.exists():
                path.chmod(stat.S_IWRITE)
                path.unlink()
            path.write_text(content, encoding="utf-8")
        except Exception as e:
            logger.error(f"Failed to save file {path}: {e}")

    @staticmethod
    def remove_directory(path: Path):
        try:
            if path.exists():
                shutil.rmtree(
                    str(path),
                    onerror=lambda f, p, e: (
                        Path(p).chmod(stat.S_IWRITE),
                        Path(p).unlink(),
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to remove directory {path}: {e}")

    @staticmethod
    def clear_directory(path: Path):
        try:
            if path.exists() and path.is_dir():
                for item in path.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
        except Exception as e:
            logger.error(f"Failed to clear directory {path}: {e}")

class SteamConfig:
    @staticmethod
    def update_config(config_data: dict, mtbf: str, steam_id: str, account_name: str) -> dict:
        # Ensure the structure exists
        if "InstallConfigStore" not in config_data:
            config_data["InstallConfigStore"] = {}
        if "Software" not in config_data["InstallConfigStore"]:
            config_data["InstallConfigStore"]["Software"] = {}
        if "Valve" not in config_data["InstallConfigStore"]["Software"]:
            config_data["InstallConfigStore"]["Software"]["Valve"] = {}
        if "Steam" not in config_data["InstallConfigStore"]["Software"]["Valve"]:
            config_data["InstallConfigStore"]["Software"]["Valve"]["Steam"] = {}
        
        steam_section = config_data["InstallConfigStore"]["Software"]["Valve"]["Steam"]
        
        # Update existing fields
        steam_section["AutoUpdateWindowEnabled"] = "0"
        steam_section["ipv6check_http_state"] = "bad"
        steam_section["ipv6check_udp_state"] = "bad"
        steam_section["ShaderCacheManager"] = {
            "HasCurrentBucket": "1",
            "CurrentBucketGPU": "b4799b250d4196b0;36174e7cc31a08f9",
            "CurrentBucketDriver": "W2:c18b09d9c69329b41cdbbf3de627bc9f;W2:ee32edf67d134b7cc2ec0cdecbd00037",
        }
        steam_section["RecentWebSocket443Failures"] = ""
        steam_section["RecentWebSocketNon443Failures"] = ""
        steam_section["RecentUDPFailures"] = ""
        steam_section["RecentTCPFailures"] = ""
        steam_section["CellIDServerOverride"] = "170"
        steam_section["MTBF"] = mtbf
        steam_section["cip"] = "02000000507a6c24d6e96c6b00004021a356"
        steam_section["SurveyDate"] = "2017-10-22"
        steam_section["SurveyDateVersion"] = "-1724767764117155760"
        steam_section["SurveyDateType"] = "3"
        steam_section["Rate"] = "30000"
        
        # Add/update account
        if "Accounts" not in steam_section:
            steam_section["Accounts"] = {}
        steam_section["Accounts"][account_name] = {"SteamID": steam_id}
        
        return config_data

    @staticmethod
    def update_login_users(login_users: dict, steam_id: str, account_name: str) -> dict:
        if "users" not in login_users:
            login_users["users"] = {}
        
        # Update existing users to not be most recent
        for user in login_users["users"].values():
            user["MostRecent"] = "0"
        
        # Add new user or update existing
        login_users["users"][steam_id] = {
            "AccountName": account_name,
            "PersonaName": account_name,
            "RememberPassword": "1",
            "WantsOfflineMode": "0",
            "SkipOfflineModeWarning": "0",
            "AllowAutoLogin": "1",
            "MostRecent": "1",
            "Timestamp": str(int(time.time())),
        }
        
        return login_users

    @staticmethod
    def update_local(local_data: dict, crc32: str, jwt: str) -> dict:
        # Ensure the structure exists
        if "MachineUserConfigStore" not in local_data:
            local_data["MachineUserConfigStore"] = {}
        if "Software" not in local_data["MachineUserConfigStore"]:
            local_data["MachineUserConfigStore"]["Software"] = {}
        if "Valve" not in local_data["MachineUserConfigStore"]["Software"]:
            local_data["MachineUserConfigStore"]["Software"]["Valve"] = {}
        if "Steam" not in local_data["MachineUserConfigStore"]["Software"]["Valve"]:
            local_data["MachineUserConfigStore"]["Software"]["Valve"]["Steam"] = {}
        if "ConnectCache" not in local_data["MachineUserConfigStore"]["Software"]["Valve"]["Steam"]:
            local_data["MachineUserConfigStore"]["Software"]["Valve"]["Steam"]["ConnectCache"] = {}
        
        # Add new connection cache entry
        connect_cache = local_data["MachineUserConfigStore"]["Software"]["Valve"]["Steam"]["ConnectCache"]
        connect_cache[crc32] = jwt
        
        return local_data

    @staticmethod
    def generate_mtbf() -> str:
        return "".join(random.choices(string.digits, k=9))

    @staticmethod
    def build_config(mtbf: str, steam_id: str, account_name: str) -> str:
        config = {
            "InstallConfigStore": {
                "Software": {
                    "Valve": {
                        "Steam": {
                            "AutoUpdateWindowEnabled": "0",
                            "ipv6check_http_state": "bad",
                            "ipv6check_udp_state": "bad",
                            "ShaderCacheManager": {
                                "HasCurrentBucket": "1",
                                "CurrentBucketGPU": "b4799b250d4196b0;36174e7cc31a08f9",
                                "CurrentBucketDriver": "W2:c18b09d9c69329b41cdbbf3de627bc9f;W2:ee32edf67d134b7cc2ec0cdecbd00037"
                            },
                            "RecentWebSocket443Failures": "",
                            "RecentWebSocketNon443Failures": "",
                            "RecentUDPFailures": "",
                            "RecentTCPFailures": "",
                            "Accounts": {
                                account_name: {
                                    "SteamID": steam_id
                                }
                            },
                            "CellIDServerOverride": "170",
                            "MTBF": mtbf,
                            "cip": "02000000507a6c24d6e96c6b00004021a356",
                            "SurveyDate": "2017-10-22",
                            "SurveyDateVersion": "-1724767764117155760",
                            "SurveyDateType": "3",
                            "Rate": "30000"
                        }
                    }
                },
                "SDL_GamepadBind": {
                    "03000000de280000ff11000001000000,Steam Virtual Gamepad": "a:b0,b:b1,back:b6,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,dpup:h0.1,leftshoulder:b4,leftstick:b8,lefttrigger:+a2,leftx:a0,lefty:a1,rightshoulder:b5,rightstick:b9,righttrigger:-a2,rightx:a3,righty:a4,start:b7,x:b2,y:b3,platform:Windows",
                    "03000000de280000ff11000000000000,Steam Virtual Gamepad": "a:b0,b:b1,back:b6,dpdown:h0.4,dpleft:h0.8,dpright:h0.2,dpup:h0.1,leftshoulder:b4,leftstick:b8,lefttrigger:+a2,leftx:a0,lefty:a1,rightshoulder:b5,rightstick:b9,righttrigger:-a2,rightx:a3,righty:a4,start:b7,x:b2,y:b3",
                    "03000000de280000ff11000000007701,Steam Virtual Gamepad": "a:b0,b:b1,x:b2,y:b3,back:b6,start:b7,leftstick:b8,rightstick:b9,leftshoulder:b4,rightshoulder:b5,dpup:b10,dpdown:b12,dpleft:b13,dpright:b11,leftx:a1,lefty:a0~,rightx:a3,righty:a2~,lefttrigger:a4,righttrigger:a5,"
                },
                "streaming": {
                    "ClientID": "-6167702798309564492"
                },
                "Music": {
                    "LocalLibrary": {
                        "Directories": {
                            "0": "0200000013500d50b7e96d1b621bcb56f5a12ce5e0651b4c3b3a50a59063d16c7d6fc334d903be2347030590f9d63c5a09370ac77bcfc6c945d0b348b91a586438e4162d56e494c9c73173ae",
                            "1": "0200000013500d50b7e96d1b621bcb56f2a12ce3e76508523b7812f4c237ec51786ff63aac72a1212b7416a2f0d71b7039302dcc2ebca3bb45d2c02bd87645623d8a784832e49cc1a01779a2209be04c"
                        }
                    }
                }
            }
        }
        return vdf.dumps(config)

    @staticmethod
    def build_login_users(steam_id: str, account_name: str) -> str:
        login_users = {
            "users": {
                steam_id: {
                    "AccountName": account_name,
                    "PersonaName": account_name,
                    "RememberPassword": "1",
                    "WantsOfflineMode": "0",
                    "SkipOfflineModeWarning": "0",
                    "AllowAutoLogin": "1",
                    "MostRecent": "1",
                    "Timestamp": str(int(time.time()))
                }
            }
        }
        return vdf.dumps(login_users)

    @staticmethod
    def build_local(crc32: str, jwt: str) -> str:
        local = {
            "MachineUserConfigStore": {
                "Software": {
                    "Valve": {
                        "Steam": {
                            "ConnectCache": {
                                crc32: jwt
                            }
                        }
                    }
                }
            }
        }
        return vdf.dumps(local)

class UserCache:
    CACHE_FILE = "user_backup.json"

    @classmethod
    def load(cls) -> Dict[str, str]:
        try:
            with open(cls.CACHE_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    @classmethod
    def save(cls, data: Dict[str, str]):
        with open(cls.CACHE_FILE, "w") as f:
            json.dump(data, f)

    @classmethod
    def add_user(cls, account_name: str, eya: str):
        cache = cls.load()
        cache[account_name] = eya
        cls.save(cache)

    @classmethod
    def remove_user(cls, account_name: str):
        cache = cls.load()
        if account_name in cache:
            del cache[account_name]
            cls.save(cache)

class JWTValidator:
    @staticmethod
    def verify_steam_jwt(refresh_token: str) -> int:
        try:
            decoded_jwt = jwt.decode(refresh_token, options={"verify_signature": False})

            if decoded_jwt.get("iss") != "steam" or "client" not in decoded_jwt.get(
                "aud", []
            ):
                return -1

            expires_in = decoded_jwt.get("exp", 0) - time.time()
            if expires_in <= 0:
                logger.info("Token has expired")
                return -1

            logger.info(f"Token expires in {expires_in} seconds")
            return expires_in

        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return -1

    @staticmethod
    def parse_eya(eya: str) -> Optional[Dict]:
        try:
            token_parts = eya.split(".")
            if len(token_parts) != 3:
                return None

            # Add padding if needed
            payload = token_parts[1]
            padding = len(payload) % 4
            if padding:
                payload += "=" * (4 - padding)

            return jwt.decode(eya, options={"verify_signature": False})

        except Exception as e:
            logger.error(f"Error parsing EYA token: {e}")
            return None

class ShareUtils:

    @staticmethod
    def import_from_url(url: str) -> tuple:
        try:
            response = requests.get(
                url,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    username = result.get("username", "")
                    key = result.get("key", "")
                    return username, key
                else:
                    raise Exception(f"Server error: {result.get('message', 'Unknown error')}")
            else:
                raise Exception(f"HTTP error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to import from URL: {e}")
            raise

class SteamLoginManager:
    def __init__(self):
        self.paths = SteamUtils.get_steam_paths()

    def login(self, eya: str, account_name: str) -> bool:
        try:
            # Validate token
            if JWTValidator.verify_steam_jwt(eya) < 0:
                self.show_message("Error", "Token has expired or is invalid")
                return False

            json_data = JWTValidator.parse_eya(eya)
            if not json_data:
                return False

            # Prepare login data
            steam_id = json_data["sub"]
            mtbf = SteamConfig.generate_mtbf()
            jwt = SteamCrypto.encrypt(eya, account_name)
            crc32 = f"{SteamUtils.compute_crc32(account_name)}1"

            self._ensure_steam_not_running()
            self._prepare_directories()
            self._update_config_files(account_name, steam_id, mtbf, jwt, crc32)

            # Launch Steam
            self._launch_steam_with_login(account_name)

            self.show_message("Success", "Login initiated successfully")
            return True

        except Exception as e:
            self.show_message("Error", f"Login failed: {str(e)}")
            return False

    def overwrite_login(self, eya: str, account_name: str) -> bool:
        try:
            # Validate token
            if JWTValidator.verify_steam_jwt(eya) < 0:
                self.show_message("Error", "Token has expired or is invalid")
                return False

            json_data = JWTValidator.parse_eya(eya)
            if not json_data:
                return False

            # Prepare login data
            steam_id = json_data["sub"]
            mtbf = SteamConfig.generate_mtbf()
            jwt = SteamCrypto.encrypt(eya, account_name)
            crc32 = f"{SteamUtils.compute_crc32(account_name)}1"

            self._ensure_steam_not_running()
            self._clean_config_files()
            self._prepare_directories()
            self._overwrite_config_files(account_name, steam_id, mtbf, jwt, crc32)

            SteamUtils.write_registry_value(r"SOFTWARE\Valve\Steam", "AutoLoginUser", account_name)
            self._launch_steam(account_name)

            self.show_message("Success", "Overwrite login initiated successfully")
            return True

        except Exception as e:
            self.show_message("Error", f"Overwrite login failed: {str(e)}")
            return False

    def show_message(self, title, message):
        dpg.configure_item("modal_window", show=True)
        dpg.set_value("modal_title", title)
        dpg.set_value("modal_message", message)

    def _ensure_steam_not_running(self):
        if SteamUtils.is_steam_running():
            logger.info("Steam is running, shutting down...")
            steam_exe = self.paths.install_path / "steam.exe"
            SteamUtils.shutdown_steam(steam_exe)
            
            # Wait for Steam to shut down
            for _ in range(5):
                if not SteamUtils.is_steam_running():
                    logger.info("Steam has been shut down")
                    return
                time.sleep(1)
            
            SteamUtils._kill_steam_processes()

    def _prepare_directories(self):
        self.paths.config_path.mkdir(parents=True, exist_ok=True)

    def _clean_config_files(self):
        try:
            if self.paths.config_path.exists():
                SteamFiles.clear_directory(self.paths.config_path)
                logger.info(f"Cleared config directory: {self.paths.config_path}")

            if self.paths.local_vdf_path.exists():
                try:
                    os.chmod(self.paths.local_vdf_path, stat.S_IWRITE)
                except:
                    pass
                self.paths.local_vdf_path.unlink()
                logger.info(f"Deleted local.vdf file: {self.paths.local_vdf_path}")
            
        except Exception as e:
            logger.error(f"Failed to clean config files: {e}")
            raise

    def _update_config_files(
        self, account_name: str, steam_id: str, mtbf: str, jwt: str, crc32: str
    ):
        # Update config.vdf
        config_path = self.paths.config_path / "config.vdf"
        config_data = {}
        if config_path.exists():
            try:
                config_data = vdf.load(config_path.open("r", encoding="utf-8"))
            except Exception:
                config_data = {}
        
        updated_config = SteamConfig.update_config(config_data, mtbf, steam_id, account_name)
        SteamFiles.save_file(config_path, vdf.dumps(updated_config, pretty=True))
        
        # Update loginusers.vdf
        loginusers_path = self.paths.config_path / "loginusers.vdf"
        loginusers_data = {}
        if loginusers_path.exists():
            try:
                loginusers_data = vdf.load(loginusers_path.open("r", encoding="utf-8"))
            except Exception:
                loginusers_data = {}
        
        updated_loginusers = SteamConfig.update_login_users(loginusers_data, steam_id, account_name)
        SteamFiles.save_file(loginusers_path, vdf.dumps(updated_loginusers, pretty=True))
        
        # Update local.vdf
        local_path = self.paths.local_vdf_path
        local_data = {}
        if local_path.exists():
            try:
                local_data = vdf.load(local_path.open("r", encoding="utf-8"))
            except Exception:
                local_data = {}
        
        updated_local = SteamConfig.update_local(local_data, crc32, jwt)
        SteamFiles.save_file(local_path, vdf.dumps(updated_local, pretty=True))

    def _overwrite_config_files(
        self, account_name: str, steam_id: str, mtbf: str, jwt: str, crc32: str
    ):
        try:
            # Write config.vdf
            config_path = self.paths.config_path / "config.vdf"
            config_content = SteamConfig.build_config(mtbf, steam_id, account_name)
            SteamFiles.save_file(config_path, config_content)
            logger.info(f"Wrote config.vdf to {config_path}")
            
            # Write loginusers.vdf
            loginusers_path = self.paths.config_path / "loginusers.vdf"
            loginusers_content = SteamConfig.build_login_users(steam_id, account_name)
            SteamFiles.save_file(loginusers_path, loginusers_content)
            logger.info(f"Wrote loginusers.vdf to {loginusers_path}")
            
            # Write local.vdf
            local_path = self.paths.local_vdf_path
            local_content = SteamConfig.build_local(crc32, jwt)
            SteamFiles.save_file(local_path, local_content)
            logger.info(f"Wrote local.vdf to {local_path}")
            
        except Exception as e:
            logger.error(f"Failed to overwrite config files: {e}")
            raise

    def _launch_steam_with_login(self, account_name: str):
        steam_exe = self.paths.install_path / "steam.exe"
        if steam_exe.exists():
            subprocess.Popen(f'"{steam_exe}" -login {account_name}', shell=True)
        else:
            logger.error(f"Steam executable not found at {steam_exe}")

    def _launch_steam(self, account_name: str):

        steam_exe = self.paths.install_path / "steam.exe"
        if steam_exe.exists():
            subprocess.Popen(f'"{steam_exe}"', shell=True)
            logger.info(f"Launched Steam without login parameter")
        else:
            logger.error(f"Steam executable not found at {steam_exe}")

class SteamLoginGUI:
    def __init__(self, version: str):
        self.version = version
        self.login_manager = SteamLoginManager()
        self.setup_gui()
        logger.info("Dear PyGui initialized")

    def setup_gui(self):
        dpg.create_context()
        
        # Setup theme and fonts
        self.setup_theme()
        
        # Create main window
        with dpg.window(tag="main_window", label=f"Steam EYA v{self.version}", width=600, height=550):
            # Header
            with dpg.group(horizontal=True):
                dpg.add_text("Steam EYA", color=[255, 255, 255])
                dpg.add_text(f"Version: {self.version}", color=[200, 200, 200])
            
            # Tab bar
            with dpg.tab_bar(tag="tab_bar"):
                self.create_login_tab()
            
            # Status bar
            with dpg.group(horizontal=True):
                dpg.add_text("Status:", color=[150, 150, 255])
                dpg.add_text("Ready", tag="status_label")
        
        # Create modal window for messages
        with dpg.window(tag="modal_window", label="Message", show=False, modal=True, width=400, height=200):
            dpg.add_text(tag="modal_title", default_value="Title")
            dpg.add_separator()
            dpg.add_text(tag="modal_message", default_value="Message content", wrap=350)
            dpg.add_spacer(height=10)
            with dpg.group(horizontal=True):
                dpg.add_button(label="OK", width=75, callback=lambda: dpg.configure_item("modal_window", show=False))
        
        # Setup viewport and start
        dpg.create_viewport(title=f'Steam EYA v{self.version}', width=620, height=570)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main_window", True)

    def setup_theme(self):
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10)
                dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 4)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 4)
        
        dpg.bind_theme(global_theme)

    def create_login_tab(self):
        with dpg.tab(tag="login_tab", label="Login"):
            # Input section
            with dpg.group():
                dpg.add_text("Account Login", color=[255, 255, 0])
                
                # Account input
                dpg.add_text("Steam Account Name:")
                dpg.add_input_text(tag="account_input", hint="Enter your Steam account name", width=580)
                
                # Token input
                dpg.add_text("EYA Token:")
                dpg.add_input_text(tag="token_input", hint="Enter your EYA token", width=580, multiline=True, height=60)
                
                # Overwrite data checkbox
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(tag="overwrite_checkbox", label="Overwrite data", default_value=False)
                    dpg.add_text("(will result in the loss of the previous account data)", color=[150, 150, 150])
                
                # Login button
                dpg.add_button(tag="login_btn", label="Login to Steam", callback=self.handle_login, width=580)
            
            dpg.add_separator()
            
            # Import from URL section
            with dpg.group():
                dpg.add_text("Import from URL", color=[255, 255, 0])
                
                dpg.add_text("Share URL:")
                dpg.add_input_text(tag="url_input", hint="Enter share URL", width=580)
                
                dpg.add_button(tag="import_btn", label="Import from URL", callback=self.handle_import_from_url, width=580)
            
            dpg.add_separator()
            
            # Steam Configuration section
            with dpg.group():
                dpg.add_text("Steam Configuration", color=[255, 255, 0])
                with dpg.group(horizontal=True):
                    dpg.add_button(tag="reset_btn", label="Reset Steam", callback=self.handle_reset, width=290)
                    dpg.add_button(tag="csgo_btn", label="730", callback=self.handle_730, width=290)

    def update_status(self, message):
        dpg.set_value("status_label", message)
        logger.info(message)

    def show_modal_message(self, title, message):
        dpg.set_value("modal_title", title)
        dpg.set_value("modal_message", message)
        dpg.configure_item("modal_window", show=True)

    def handle_login(self, sender, app_data):
        self.update_status("Processing login...")
        account_name = dpg.get_value("account_input").strip()
        eya_token = dpg.get_value("token_input").strip()
        overwrite_mode = dpg.get_value("overwrite_checkbox")
        
        if not account_name:
            self.show_modal_message("Error", "Please enter your Steam account name")
            self.update_status("Login failed: Missing account name")
            return
            
        if not eya_token:
            self.show_modal_message("Error", "Please enter your EYA token")
            self.update_status("Login failed: Missing token")
            return
            
        # Clean up token if needed
        eya_token = eya_token.replace(
            "EyAidHlwIjogIkpXVCIsICJhbGciOiAiRWREU0EiIH0",
            "eyAidHlwIjogIkpXVCIsICJhbGciOiAiRWREU0EiIH0"
        )
        
        expire_time = JWTValidator.verify_steam_jwt(eya_token)

        if expire_time < 0:
            self.show_modal_message("Error", "Token has expired.")
            self.update_status("Login failed: Token expired")
            return
        
        if overwrite_mode:
            self.update_status(f"Using overwrite mode for account: {account_name}")
            if self.login_manager.overwrite_login(eya_token, account_name):
                self.show_success_message(expire_time, account_name, "overwrite")
        else:
            self.update_status(f"Using append mode for account: {account_name}")
            if self.login_manager.login(eya_token, account_name):
                self.show_success_message(expire_time, account_name, "append")

    def show_success_message(self, expire_time, account_name, mode):
        days = expire_time // 86400
        hours = (expire_time % 86400) // 3600
        minutes = (expire_time % 3600) // 60
        seconds = expire_time % 60
        
        mode_text = "Overwrite" if mode == "overwrite" else "Append"
        
        self.show_modal_message(
            "Token Valid",
            f"Token is valid for {days} days, {hours} hours, {minutes} "
            f"minutes, and {seconds} seconds.\n\n"
            f"Logged in as {account_name} using {mode_text} mode."
        )
        self.update_status(f"Logged in as {account_name} ({mode_text} mode)")

    def handle_import_from_url(self, sender, app_data):
        url = dpg.get_value("url_input").strip()
        if not url:
            self.show_modal_message("Error", "Please enter a share URL")
            return
            
        try:
            self.update_status("Importing account from URL...")
            username, key = ShareUtils.import_from_url(url)
            
            # Auto-fill the login form
            dpg.set_value("account_input", username)
            dpg.set_value("token_input", key)
            
            self.update_status(f"Successfully imported account: {username}")
            self.show_modal_message(
                "Import Successful", 
                f"Successfully imported account: {username}\n\nLogin form has been auto-filled. Click 'Login to Steam' to continue."
            )
            
        except Exception as e:
            self.show_modal_message("Error", f"Failed to import from URL: {str(e)}")
            self.update_status(f"Import failed: {str(e)}")

    def handle_reset(self, sender, app_data):
        self.update_status("Resetting Steam...")
        
        paths = SteamUtils.get_steam_paths()
        
        try:
            # Clear config directory contents
            if paths.config_path.exists():
                SteamFiles.clear_directory(paths.config_path)
                self.update_status("Cleared Steam config directory")
            
            # Delete local.vdf file
            if paths.local_vdf_path.exists():
                paths.local_vdf_path.unlink()
                self.update_status("Deleted local.vdf file")
            
            # Shutdown Steam if running
            if SteamUtils.is_steam_running():
                steam_exe = paths.install_path / "steam.exe"
                SteamUtils.shutdown_steam(steam_exe)
                self.update_status("Sent shutdown command to Steam")
            
            self.show_modal_message("Reset Completed", "Steam configuration has been reset successfully.")
            self.update_status("Steam reset completed")
            
        except Exception as e:
            self.show_modal_message("Error", f"Failed to reset Steam: {str(e)}")
            self.update_status(f"Reset failed: {str(e)}")

    def handle_730(self, sender, app_data):
        self.update_status("Processing 730 operation...")
        
        try:
            paths = SteamUtils.get_steam_paths()

            loginusers_path = paths.config_path / "loginusers.vdf"
            if not loginusers_path.exists():
                self.show_modal_message("Error", "Please login to an account first.")
                self.update_status("730 operation failed: loginusers.vdf not found")
                return

            try:
                with open(loginusers_path, 'r', encoding='utf-8') as f:
                    loginusers_data = vdf.load(f)
            except Exception as e:
                self.show_modal_message("Error", f"Failed to read loginusers.vdf: {str(e)}")
                self.update_status(f"730 operation failed: {str(e)}")
                return
            
            users = loginusers_data.get("users", {})
            if not users:
                self.show_modal_message("Error", "No users found in loginusers.vdf")
                self.update_status("730 operation failed: No users found")
                return
            
            first_steamid = next(iter(users))
            self.update_status(f"First SteamID found: {first_steamid}")

            friend_code = SteamUtils.steamid64_to_friend_code(first_steamid)
            if friend_code == 0:
                self.show_modal_message("Error", "Failed to convert SteamID to friend code")
                self.update_status("730 operation failed: Friend code conversion failed")
                return
            
            self.update_status(f"Friend code: {friend_code}")
            
            userdata_path = paths.install_path / "userdata" / str(friend_code)
            
            source_730_path = Path("730")
            if not source_730_path.exists() or not source_730_path.is_dir():
                self.show_modal_message("Error", "730 folder not found in current directory")
                self.update_status("730 operation failed: Source 730 folder not found")
                return

            userdata_path.mkdir(parents=True, exist_ok=True)

            target_730_path = userdata_path / "730"
            if target_730_path.exists():
                try:
                    if target_730_path.is_dir():
                        shutil.rmtree(target_730_path)
                    else:
                        target_730_path.unlink()
                    self.update_status(f"Removed existing 730 folder from {target_730_path}")
                except Exception as e:
                    self.show_modal_message("Error", f"Failed to remove existing 730 folder: {str(e)}")
                    self.update_status(f"730 operation failed: {str(e)}")
                    return
            
            try:
                shutil.copytree(source_730_path, target_730_path)
                self.update_status(f"Copied 730 folder to {target_730_path}")
                self.show_modal_message("Success", f"730 folder copied successfully!\n\nSteamID: {first_steamid}\nFriend Code: {friend_code}\nTarget Path: {target_730_path}")
            except Exception as e:
                self.show_modal_message("Error", f"Failed to copy 730 folder: {str(e)}")
                self.update_status(f"730 operation failed: {str(e)}")
                return
            
        except Exception as e:
            self.show_modal_message("Error", f"An unexpected error occurred: {str(e)}")
            self.update_status(f"730 operation failed: {str(e)}")

    def run(self):
        try:
            dpg.start_dearpygui()
        except Exception as e:
            logger.error(f"Application error: {e}")
        finally:
            dpg.destroy_context()

if __name__ == "__main__":
    logger.info("Starting Dear PyGui application...")

    app = SteamLoginGUI("1.0")
    app.run()