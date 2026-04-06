import socket
import json
import time
import random
import string
import logging
import math
from datetime import datetime
import urllib.request

# =========================
# CONFIG
# =========================
BEACON_INTERVAL = 10
JITTER = 5
CYCLES = 0

LOG_FILE = "realistic_sim_advanced.log"

SAFE_IPS = [
    "192.0.2.1",
    "198.51.100.2",
    "203.0.113.5",
    "192.0.2.55",
    "198.51.100.77"
]

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

TLD_LIST = ["xyz", "top", "online", "site", "store"]

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

# =========================
# METRICS
# =========================
def reset_metrics():
    return {
        "dns_attempts": 0,
        "dns_failed": 0,
        "tcp_attempts": 0,
        "tcp_success": 0,
        "tcp_failed": 0,
        "tcp_real": 0,
        "tcp_safe": 0,
        "http_success": 0,
        "http_failed": 0
    }

metrics = reset_metrics()

# =========================
# ENTROPY CALCULATION
# =========================
def calculate_entropy(domain):
    prob = [float(domain.count(c)) / len(domain) for c in set(domain)]
    entropy = - sum([p * math.log2(p) for p in prob])
    return round(entropy, 2)

def classify_entropy(entropy):
    if entropy > 4.0:
        return "high"
    elif entropy > 3.0:
        return "medium"
    else:
        return "low"

def simulate_threat_intel():
    return random.choice(["clean", "newly_registered", "known_malicious"])

# =========================
# LOG FUNCTION
# =========================
def log_event(event, data):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": event,
        "data": data
    }
    logging.info(json.dumps(entry))

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
        if key == "threat":
            if console_data[key] == "known_malicious":
                console_data[key] = f"{RED}{console_data[key]}{RESET}"

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
    name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    tld = random.choice(TLD_LIST)
    return f"{prefix}{name}.{tld}"

def jitter_sleep():
    delay = BEACON_INTERVAL + random.randint(-JITTER, JITTER)
    log_event("sleep", {"seconds": delay})
    time.sleep(delay)

# =========================
# DNS
# =========================
def simulate_dns_beacon():
    metrics["dns_attempts"] += 1

    domain = generate_dga_domain()
    entropy = calculate_entropy(domain)
    entropy_level = classify_entropy(entropy)
    threat = simulate_threat_intel()

    try:
        socket.gethostbyname(domain)
    except Exception as e:
        metrics["dns_failed"] += 1
        log_event("dns_failed", {
            "domain": domain,
            "entropy": entropy,
            "dga_score": entropy_level,
            "threat": threat,
            "error": str(e)
        })

# =========================
# TCP
# =========================
def simulate_tcp_beacon():
    metrics["tcp_attempts"] += 1

    ip = random.choice(SAFE_IPS + REAL_IPS)
    port = random.choice(TCP_PORTS)
    is_real = ip in REAL_IPS

    if is_real:
        metrics["tcp_real"] += 1
    else:
        metrics["tcp_safe"] += 1

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

        metrics["tcp_success"] += 1
        log_event("tcp_success", {"ip": ip, "port": port})

    except Exception as e:
        metrics["tcp_failed"] += 1
        log_event("tcp_failed", {"ip": ip, "port": port, "error": str(e)})

# =========================
# HTTP
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
            metrics["http_success"] += 1
            log_event("http_post", {
                "endpoint": endpoint,
                "status": response.getcode()
            })

    except Exception as e:
        metrics["http_failed"] += 1
        log_event("http_failed", {"endpoint": endpoint, "error": str(e)})

# =========================
# DASHBOARD
# =========================
def print_summary():
    print(f"\n{CYAN}===== CYCLE SUMMARY ====={RESET}")
    print(f"DNS:   attempts={metrics['dns_attempts']} failed={metrics['dns_failed']}")
    print(f"TCP:   attempts={metrics['tcp_attempts']} success={metrics['tcp_success']} failed={metrics['tcp_failed']}")
    print(f"       real_ip={metrics['tcp_real']} safe_ip={metrics['tcp_safe']}")
    print(f"HTTP:  success={metrics['http_success']} failed={metrics['http_failed']}")
    print(f"{CYAN}=========================\n{RESET}")

# =========================
# MAIN LOOP
# =========================
def run():
    global CYCLES, metrics

    print(f"{CYAN}Advanced SOC Simulation (DGA + Threat Intel + Live IPs){RESET}")
    log_event("start", {"env": "Isolated Lab"})

    while True:
        metrics = reset_metrics()

        CYCLES += 1
        log_event("cycle", {"cycle": CYCLES})

        for _ in range(random.randint(2, 4)):
            simulate_dns_beacon()

        for _ in range(random.randint(1, 3)):
            simulate_tcp_beacon()

        simulate_http_beacon()

        print_summary()

        jitter_sleep()

# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    run()