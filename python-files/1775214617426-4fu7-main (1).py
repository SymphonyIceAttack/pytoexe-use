import socket
import json
import time
import random
import string
import logging
from datetime import datetime
import urllib.request

# =========================
# CONFIG
# =========================
BEACON_INTERVAL = 10
JITTER = 5
CYCLES = 0

LOG_FILE = "realistic_sim_liveips.log"

# SAFE test IPs (non-routable)
SAFE_IPS = [
    "192.0.2.1",
    "198.51.100.2",
    "203.0.113.5",
    "192.0.2.55",
    "198.51.100.77"
]

# Real IPs — will actually connect
REAL_IPS = [
    "93.123.109.214",
    "60.205.233.234"
]

TCP_PORTS = [3333, 4444, 5555]

HTTP_ENDPOINTS = [
    "https://httpbin.org/post",
    "https://httpbin.org/put",
    "https://httpbin.org/get"
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "python-urllib/3.x",
    "curl/7.68.0"
]

HOSTS = ["win11-lab", "win10-test", "server-lab1"]

# =========================
# COLORS
# =========================
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

# =========================
# LOGGING
# =========================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(message)s"
)

def log_event(event, data):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "data": data
    }
    logging.info(json.dumps(entry))

    # Console coloring
    console_data = data.copy()
    for key in console_data:
        if key in ["domain", "port"]:
            console_data[key] = f"{GREEN}{console_data[key]}{RESET}"
        if key == "status":
            console_data[key] = f"{YELLOW}{console_data[key]}{RESET}"
        if key == "error":
            console_data[key] = f"{RED}{console_data[key]}{RESET}"
        if key == "cycle":
            console_data[key] = f"{CYAN}{console_data[key]}{RESET}"

    print({
        "timestamp": entry["timestamp"],
        "event": event,
        "data": console_data
    })

# =========================
# HELPERS
# =========================
def generate_dga_domain():
    prefix = random.choice(["login-", "update-", "pay-", "secure-"])
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}{name}.invalid"

def jitter_sleep():
    delay = BEACON_INTERVAL + random.randint(-JITTER, JITTER)
    log_event("sleep", {"seconds": delay})
    time.sleep(delay)

# =========================
# DNS Simulation
# =========================
def simulate_dns_beacon():
    domain = generate_dga_domain()
    try:
        socket.gethostbyname(domain)
    except Exception as e:
        log_event("dns_failed", {"domain": domain, "error": str(e)})

# =========================
# TCP Simulation (with real outbound IPs)
# =========================
def simulate_tcp_beacon():
    ip = random.choice(SAFE_IPS + REAL_IPS)
    port = random.choice(TCP_PORTS)

    is_real = ip in REAL_IPS

    try:
        log_event("tcp_connect_attempt", {
            "ip": ip,
            "port": port,
            "real_connection": is_real
        })

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        sock.connect((ip, port))

        for method in ["login", "getwork", "submit", "heartbeat"]:
            payload = {"method": method, "params": {"login": "fake_wallet"}}
            sock.sendall((json.dumps(payload) + "\n").encode())

        sock.close()

        log_event("tcp_success", {"ip": ip, "port": port, "real_connection": is_real})

    except Exception as e:
        log_event("tcp_failed", {"ip": ip, "port": port, "error": str(e), "real_connection": is_real})

# =========================
# HTTP Simulation
# =========================
def simulate_http_beacon():
    endpoint = random.choice(HTTP_ENDPOINTS)
    try:
        payload = {
            "status": random.choice(["alive", "working", "idle"]),
            "timestamp": datetime.utcnow().isoformat(),
            "host": random.choice(HOSTS),
            "cpu": random.randint(1, 100),
            "memory": random.randint(100, 16000)
        }

        data = json.dumps(payload).encode()

        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Content-Type": "application/json"
        }

        req = urllib.request.Request(endpoint, data=data, headers=headers)

        with urllib.request.urlopen(req, timeout=5) as response:
            log_event("http_post", {
                "endpoint": endpoint,
                "status": response.getcode()
            })

    except Exception as e:
        log_event("http_failed", {"endpoint": endpoint, "error": str(e)})

# =========================
# MAIN LOOP
# =========================
def run():
    global CYCLES
    print(f"{CYAN}Realistic Crypto-Mining Behavior Simulator (LIVE IPs){RESET}")
    log_event("start", {"env": "Isolated Lab"})

    while True:
        CYCLES += 1
        log_event("cycle", {"cycle": CYCLES})

        # DNS
        for _ in range(random.randint(2, 4)):
            simulate_dns_beacon()

        # TCP (sequential, now allows real IP connections)
        for _ in range(random.randint(1, 3)):
            simulate_tcp_beacon()

        # HTTP
        simulate_http_beacon()

        # Sleep
        jitter_sleep()

# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    run()