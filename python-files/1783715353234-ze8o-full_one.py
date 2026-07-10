import nfc
import subprocess
import webbrowser
import usb1
import binascii
import os
import time
import socket
import platform
import sys
import pygame
import win32con
import ctypes
import threading
import warnings
import psutil



# Update these imports at the top of your file
import win32gui
import win32con
import ctypes

# Required for console handling
kernel32 = ctypes.WinDLL('kernel32')
user32 = ctypes.WinDLL('user32')

# Console handling functions
def is_caps_lock_on():
    return bool(user32.GetKeyState(win32con.VK_CAPITAL) & 1)

def get_console_window():
    return kernel32.GetConsoleWindow()

def toggle_console_visibility():
    hwnd = get_console_window()
    if hwnd:
        last_state = None
        
        while True:
            try:
                current_state = is_caps_lock_on()
                if current_state != last_state:
                    if current_state:
                        # CapsLock ON = Show console
                        user32.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
                    else:
                        # CapsLock OFF = Hide console
                        user32.ShowWindow(hwnd, win32con.SW_HIDE)
                    last_state = current_state
            except Exception as e:
                print(f"Console toggle error: {e}")
            time.sleep(0.1)

# Add these lines to explicitly import the acr122 module
from nfc.clf import acr122
import nfc.clf.acr122

warnings.filterwarnings("ignore", message=".*nfc.clf.acr122.*")
warnings.filterwarnings("ignore")



# Initialize pygame mixer for sound
pygame.mixer.init()

# Load sound effect
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sound_file = os.path.join(current_dir, "device.mp3")
    startup_sound = pygame.mixer.Sound(sound_file)
except Exception as e:
    print(f"Error loading sound file: {e}")
    startup_sound = None

# Track currently active card and process
active_card = {
    'tag_id': None,
    'action': None,
    'process': None,
    'start_time': None
}

# Required for console handling
kernel32 = ctypes.WinDLL('kernel32')
user32 = ctypes.WinDLL('user32')

# Create console at startup
kernel32.AllocConsole()
sys.stdout = open('CONOUT$', 'w')
sys.stderr = open('CONOUT$', 'w')


def kill_process(process_name):
    """Kill a process and all its subprocesses"""
    print(f"\nAttempting to kill {process_name}...")
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    print(f"Found {proc.info['name']} (PID: {proc.info['pid']})")
                    process = psutil.Process(proc.info['pid'])
                    for child in process.children(recursive=True):
                        print(f"Killing child process {child.pid}")
                        child.kill()
                    process.kill()
                    print(f"Killed {process_name}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"Error killing {process_name}: {e}")



def is_caps_lock_on():
    return user32.GetKeyState(win32con.VK_CAPITAL) & 1 != 0

def get_console_window():
    return kernel32.GetConsoleWindow()

def toggle_console_visibility():
    hwnd = get_console_window()
    if hwnd:
        last_state = None  # Force initial update
        
        while True:
            current_state = is_caps_lock_on()
            if current_state != last_state:  # Only update when state changes
                if current_state:
                    print("Showing console...")  # Debug print
                    user32.ShowWindow(hwnd, win32con.SW_SHOW)
                else:
                    print("Hiding console...")  # Debug print
                    user32.ShowWindow(hwnd, win32con.SW_HIDE)
                last_state = current_state
            time.sleep(0.1)

from subprocess import CREATE_NO_WINDOW
vlc_process = None

# Dictionary to store the mappings
mappings = {}

# Dictionary of supported cores and their file extensions
CORE_MAPPINGS = {
    'snes9x_libretro.dll': ['.sfc', '.smc'],
    'dolphin_libretro.dll': ['.gcm', '.iso', '.wbfs', '.ciso', '.gcz'],
    'dosbox_pure_libretro.dll': ['.exe', '.bat', '.com'],
    'fbalpha2012_libretro.dll': ['.zip', '.7z'],
    'fbneo_libretro.dll': ['.zip', '.7z'],
    'fceumm_libretro.dll': ['.nes', '.fds'],
    'flycast_libretro.dll': ['.cdi', '.gdi', '.chd'],
    'gambatte_libretro.dll': ['.gb', '.gbc'],
    'gpsp_libretro.dll': ['.gba'],
    'mame2003_plus_libretro.dll': ['.zip'],
    'mednafen_pce_libretro.dll': ['.pce'],
    'mednafen_saturn_libretro.dll': ['.cue', '.iso'],
    'mednafen_vb_libretro.dll': ['.vb'],
    'melondsds_libretro.dll': ['.nds'],
    'parallel_n64_libretro.dll': ['.n64', '.v64', '.z64'],
    'pcsx2_libretro.dll': ['.iso', '.bin'],
    'pcsx_rearmed_libretro.dll': ['.bin', '.iso', '.img', '.cue'],
    'picodrive_libretro.dll': ['.bin', '.gen', '.smd', '.md'],
    'ppsspp_libretro.dll': ['.iso', '.cso', '.pbp'],
    'puae_libretro.dll': ['.adf', '.adz', '.dms'],
    'scummvm_libretro.dll': ['.scummvm'],
    'snes9x_libretro.dll': ['.sfc', '.smc']
}

def clean_windows_path(path):
    """Clean and normalize Windows file path"""
    path = path.encode('ascii', 'ignore').decode()
    path = os.path.normpath(path)
    return path

def kill_interfering_processes():
    """Kill any processes that might interfere with the NFC reader"""
    if platform.system() == 'Windows':
        processes_to_kill = [
            'AcsNFCTray.exe',
            'ACSccid.exe',
            'APAcsNFCTray.exe',
            'APACSccid.exe',
            'ACR122U_NFC_API.exe'
        ]
        for proc in processes_to_kill:
            try:
                subprocess.run(['taskkill', '/F', '/IM', proc], 
                             creationflags=CREATE_NO_WINDOW,
                             stderr=subprocess.DEVNULL,
                             stdout=subprocess.DEVNULL)
            except:
                continue
        time.sleep(2)

def initialize_acr122u():
    """Initialize the ACR122U reader with generic driver first"""
    try:
        kill_interfering_processes()
        print("Attempting to connect with generic driver...")
        
        # Try generic driver first
        try:
            clf = nfc.ContactlessFrontend('usb:072f:2200')
            if clf is not None:
                print("ACR122U reader initialized with generic driver")
                return clf
        except Exception as generic_error:
            print(f"Generic driver connection failed: {generic_error}")
        
        # Only try specific chipset as fallback
        print("Attempting connection with specific chipset...")
        clf = nfc.ContactlessFrontend('usb:072f:2200:*')
        if clf is not None:
            print("ACR122U reader initialized with specific chipset")
            return clf
            
    except Exception as e:
        print(f"Error initializing reader: {e}")
        return None
        
    return None

def load_mappings():
    print("\nStarting to load mappings...")
    try:
        # Get the directory of the executable or script
        if getattr(sys, 'frozen', False):  # Check if running as a PyInstaller executable
            current_dir = sys._MEIPASS
        else:
            current_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the path to the mapping file
        mapping_file = os.getcwd() + r"\mapping.txt"
        print(f"Looking for mapping file at: {mapping_file}")

        if not os.path.exists(mapping_file):
            print("Error: mapping.txt file not found!")
            return
        
        with open(mapping_file, 'r', encoding='utf-8-sig') as file:
            print("Successfully opened mapping file")
            
            for line in file:
                if not line.strip():
                    continue
                
                print(f"\nProcessing line: {repr(line)}")
                parts = line.strip().split(',')
                
                if len(parts) >= 3:
                    tag_id = parts[0]
                    action = parts[1].lower()
                    value = parts[2]
                    
                    # Handle optional core specification for retroarch
                    core = parts[3] if len(parts) > 3 and action == 'retroarch' else None
                    
                    tag_id = ''.join(c for c in tag_id if c.isalnum()).upper()
                    
                    if action in ['vlc', 'retroarch']:
                        value = clean_windows_path(value)
                    
                    mappings[tag_id] = (action, value, core) if core else (action, value)
                    print(f"Added mapping - Tag ID: {tag_id}, Action: {action}, Value: {value}, Core: {core}")
        
        print("\nFinished loading mappings")
        print(f"Total mappings loaded: {len(mappings)}")
        
    except Exception as e:
        print(f"Error reading mappings: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())

def get_core_for_file(file_path):
    """Determine appropriate core based on file extension"""
    ext = os.path.splitext(file_path)[1].lower()
    for core, extensions in CORE_MAPPINGS.items():
        if ext in extensions:
            return core
    return None


def get_media_type(file_path):
    """Determine if path is audio, video, or a folder"""
    # Audio extensions
    audio_extensions = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg', '.wma'}
    # Video extensions
    video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.mpg', '.mpeg'}
    
    if os.path.isdir(file_path):
        return 'folder'
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext in audio_extensions:
        return 'audio'
    elif ext in video_extensions:
        return 'video'
    return 'unknown'



def play_retroarch(rom_path, specified_core=None):
    """Launch RetroArch with proper process tracking"""
    global active_card
    
    try:
        print("\nStarting RetroArch...")
        rom_path = clean_windows_path(rom_path)
        retroarch_path = r"C:\RetroArch-Win64\retroarch.exe"

        # Verify paths
        if not os.path.exists(retroarch_path):
            print("RetroArch executable not found")
            return None
        if not os.path.exists(rom_path):
            print(f"ROM path not found: {rom_path}")
            return None

        # Determine core to use
        core_name = specified_core or get_core_for_file(rom_path)
        if not core_name:
            print("No suitable core found")
            return None
            
        core_path = os.path.join(r"C:\RetroArch-Win64\cores", core_name)
        if not os.path.exists(core_path):
            print(f"Core not found: {core_path}")
            return None

        # Kill existing RetroArch instances
        kill_process('retroarch.exe')
        time.sleep(1)  # Wait for processes to terminate

        # Build command with fullscreen flag
        cmd = f'"{retroarch_path}" -L "{core_path}" "{rom_path}" --fullscreen'
        
        # Start process
        retro_process = subprocess.Popen(
            cmd,
            shell=True,
            cwd=r"C:\RetroArch-Win64",
            creationflags=CREATE_NO_WINDOW
        )
        
        # Update active card process tracking
        active_card['process'] = retro_process
        print(f"RetroArch started with PID: {retro_process.pid}")
        return retro_process

    except Exception as e:
        print(f"\nRetroArch Error: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def play_vlc_media(file_path):
    """Launch VLC media player with proper process tracking and Plex support"""
    global active_card
    
    try:
        print("\nDEBUG INFO:")
        print(f"1. Raw file path received: {repr(file_path)}")
        
        # Fix URL formatting for network streams
        if file_path.startswith(('http:', 'https:', 'dlna:', 'plex:')):
            file_path = file_path.replace('\\', '/').replace('//', '/')
            if file_path.startswith('http:/'):
                file_path = 'http://' + file_path[6:]
            media_type = 'video'
        else:
            media_type = get_media_type(file_path)
        
        print(f"2. Media type detected: {media_type}")
        
        # Kill any existing VLC processes
        kill_process('vlc.exe')
        time.sleep(1)  # Wait for processes to terminate

        # Build command based on media type
        if media_type == 'folder':
            # Handle folder of files
            folder_path = file_path
            files = []
            # Get all media files in folder
            for f in os.listdir(folder_path):
                full_path = os.path.join(folder_path, f)
                file_type = get_media_type(full_path)
                if file_type in ['audio', 'video']:
                    files.append(full_path)
            
            if not files:
                print("No media files found in folder")
                return None
                
            cmd = [
                'vlc',
                *files,
                '--play-and-exit',
                '--quiet',
                '--fullscreen',
                '--no-video-title-show',
                '--no-qt-privacy-ask',
                '--no-qt-error-dialogs',
                '--no-repeat'
            ]
        else:
            # Handle single file or URL
            cmd = [
                'vlc',
                file_path,
                '--play-and-exit',
                '--quiet',
                '--fullscreen',
                '--no-video-title-show',
                '--no-qt-privacy-ask',
                '--no-qt-error-dialogs',
                '--no-repeat'
            ]
        
        print(f"3. Command: {repr(cmd)}")
        
        # Start process with proper tracking
        vlc_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=CREATE_NO_WINDOW
        )
        
        # Update active card process tracking
        active_card['process'] = vlc_process
        print(f"VLC started with PID: {vlc_process.pid}")
        return vlc_process

    except Exception as e:
        print(f"\nVLC Error: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None
    finally:
        print("=== END VLC DEBUG ===\n")

def format_tag_id(tag):
    try:
        if isinstance(tag, str):
            tag_id = ''.join(c for c in tag if c.isalnum()).upper()
        elif hasattr(tag, 'identifier'):
            tag_id = binascii.hexlify(tag.identifier).decode('utf-8').upper()
        else:
            tag_id = ''.join(c for c in str(tag) if c.isalnum()).upper()
        print(f"Formatted tag ID: {tag_id}")
        return tag_id
    except Exception as e:
        print(f"Error formatting tag ID: {e}")
        return None

def play_sound():
    """Play the startup/interaction sound effect"""
    try:
        if startup_sound:
            startup_sound.play()
    except Exception as e:
        print(f"Error playing sound: {e}")

def stop_current_process():
    """Stop the currently running process with enhanced process tree termination"""
    print("\n=== Stopping Current Process ===")
    print(f"Active card info: {active_card}")
    
    try:
        if active_card['process']:
            print(f"Attempting to kill process tree for PID {active_card['process'].pid}")
            try:
                parent = psutil.Process(active_card['process'].pid)
                children = parent.children(recursive=True)
                
                # First kill children
                for child in children:
                    print(f"Killing child process {child.pid} ({child.name()})")
                    try:
                        child.kill()
                    except psutil.NoSuchProcess:
                        print(f"Child process {child.pid} already terminated")
                
                # Then kill parent
                print(f"Killing parent process {parent.pid} ({parent.name()})")
                try:
                    parent.kill()
                except psutil.NoSuchProcess:
                    print("Parent process already terminated")
                
                print("Process tree killed successfully")
                
            except psutil.NoSuchProcess:
                print("Process already terminated")
            except Exception as e:
                print(f"Error killing process tree: {e}")
                # Fallback to name-based killing
                if active_card['action'] == 'vlc':
                    kill_process('vlc.exe')
                elif active_card['action'] == 'retroarch':
                    kill_process('retroarch.exe')
                
    except Exception as e:
        print(f"Error in process termination: {e}")
        # Final fallback to system taskkill
        if active_card['action'] == 'vlc':
            subprocess.run(['taskkill', '/F', '/IM', 'vlc.exe'], 
                          creationflags=CREATE_NO_WINDOW)
        elif active_card['action'] == 'retroarch':
            subprocess.run(['taskkill', '/F', '/IM', 'retroarch.exe'],
                          creationflags=CREATE_NO_WINDOW)

    # Clear the active card info
    active_card.update({
        'tag_id': None,
        'action': None,
        'process': None,
        'start_time': None
    })
    print("=== Process Stop Complete ===\n")

def nfc_read(tag):
    global active_card
    print("\nTag detected!")
    tag_id = format_tag_id(tag)
    
    if not tag_id:
        print("Invalid tag ID format")
        return

    print(f"Processing tag: {tag_id}")
    
    # If same tag is tapped again, stop current content
    if tag_id == active_card['tag_id']:
        print("Same tag tapped - stopping playback")
        stop_current_process()
        play_sound()
        return

    # If different tag tapped while content is playing
    if active_card['tag_id'] is not None and active_card['tag_id'] != tag_id:
        print(f"Different tag detected ({tag_id} vs {active_card['tag_id']}) - switching content")
        stop_current_process()
        time.sleep(1)  # Allow time for process cleanup

    # Process new tag
    play_sound()
    
    if tag_id in mappings:
        action, *params = mappings[tag_id]
        print(f"Executing action: {action} for tag {tag_id}")
        
        # Update active card info before starting process
        active_card.update({
            'tag_id': tag_id,
            'action': action,
            'start_time': time.time()
        })

        try:
            if action == 'vlc':
                media_path = params[0]
                active_card['process'] = play_vlc_media(media_path)
                if not active_card['process']:
                    print("Failed to start VLC process")
                    active_card.update({
                        'tag_id': None,
                        'action': None,
                        'process': None,
                        'start_time': None
                    })
            elif action == 'retroarch':
                rom_path = params[0]
                core = params[1] if len(params) > 1 else None
                active_card['process'] = play_retroarch(rom_path, core)
                if not active_card['process']:
                    print("Failed to start RetroArch process")
                    active_card.update({
                        'tag_id': None,
                        'action': None,
                        'process': None,
                        'start_time': None
                    })
            else:
                print(f"Unknown action: {action}")
        except Exception as e:
            print(f"Error executing action: {e}")
            active_card.update({
                'tag_id': None,
                'action': None,
                'process': None,
                'start_time': None
            })
    else:
        print(f"No mapping found for tag: {tag_id}")


def main():
    # Start console visibility monitor in a separate thread
    console_thread = threading.Thread(target=toggle_console_visibility, daemon=True)
    console_thread.start()

    print("Starting ACR122U NFC Reader application...")
    play_sound()
    
    print("Loading mappings...")
    load_mappings()
    
    if not mappings:
        print("\nWarning: No mappings were loaded! Please check your mapping.txt file.")
        print("Continuing without mappings...")

    print("\nInitializing ACR122U reader...")
    max_retries = 3
    retry_count = 0
    
    while True:
        try:
            if retry_count >= max_retries:
                print("\nMaximum retry attempts reached.")
                print("\nPlease ensure you have:")
                print("1. Installed the WinUSB driver using Zadig")
                print("2. Uninstalled any ACS drivers")
                print("3. Run this program as administrator")
                print("4. No other NFC programs are running")
                print("\nAutomatically retrying in 5 seconds...")
                time.sleep(5)
                retry_count = 0
            
            # Try to initialize with a shorter timeout
            clf = initialize_acr122u()
            if clf is None:
                retry_count += 1
                print(f"\nRetrying in 3 seconds... (Attempt {retry_count} of {max_retries})")
                time.sleep(3)  # Reduced wait time
                continue
                
            print("Waiting for tags... (Press Ctrl+C to exit)")
            retry_count = 0
            
            while True:
                try:
                    # Reduced timeout for faster recovery
                    clf.connect(rdwr={'on-connect': nfc_read, 'timeout': 0.3})
                except nfc.clf.TimeoutError:
                    continue
                except socket.timeout:
                    continue
                except Exception as e:
                    if "timeout" in str(e).lower():
                        continue
                    # If we get a USB error, try to reinitialize
                    if isinstance(e, (usb1.USBErrorNotSupported, usb1.USBErrorAccess)):
                        print("USB error detected, attempting to reinitialize...")
                        break
                    else:
                        raise
                    
        except (OSError, usb1.USBErrorNotSupported, usb1.USBErrorAccess) as e:
            error_code = getattr(e, 'errno', None)
            if error_code in [5, 19] or isinstance(e, usb1.USBErrorNotSupported):
                print("\nAttempting to reconnect with generic driver...")
            kill_interfering_processes()
            retry_count += 1
            print(f"Retrying in 3 seconds... (Attempt {retry_count} of {max_retries})")
            time.sleep(3)
            
        except KeyboardInterrupt:
            print("\nApplication stopped by user")
            break
            
        except Exception as e:
            print(f"\nError occurred: {type(e).__name__}: {str(e)}")
            retry_count += 1
            print(f"Attempting to recover... Retrying in 3 seconds...")
            time.sleep(3)
            
            
if __name__ == "__main__":
    # Initialize console state - start hidden if CapsLock is off
    hwnd = get_console_window()
    if hwnd:
        if not is_caps_lock_on():
            user32.ShowWindow(hwnd, win32con.SW_HIDE)
        else:
            user32.ShowWindow(hwnd, win32con.SW_SHOW)
    
    # Start console visibility monitor in a separate thread
    console_thread = threading.Thread(target=toggle_console_visibility, daemon=True)
    console_thread.start()
    
    main()