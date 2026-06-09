import subprocess
import time
import threading
from datetime import datetime

BLOCK_DURATION = 360  # 6 minutes
RULE_PREFIX = "PY_BLOCK"

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True)

def get_listening_ports():
    # Windows netstat parsing
    result = run("netstat -ano -p tcp")
    ports = set()

    for line in result.stdout.splitlines():
        if "LISTENING" in line:
            parts = line.split()
            addr = parts[1]
            try:
                port = int(addr.rsplit(":", 1)[-1])
                ports.add(port)
            except:
                continue

    return sorted(list(ports))


def add_firewall_rule(port):
    rule_name = f"{RULE_PREFIX}_{port}"

    cmd = (
        f'netsh advfirewall firewall add rule '
        f'name="{rule_name}" '
        f'dir=in action=block protocol=TCP localport={port}'
    )

    run(cmd)
    print(f"[BLOCKED] Port {port}")
    return rule_name


def remove_firewall_rule(rule_name):
    cmd = (
        f'netsh advfirewall firewall delete rule name="{rule_name}"'
    )
    run(cmd)
    print(f"[UNBLOCKED] Rule {rule_name}")


def apply_block(ports):
    rules = []

    print(f"\nListening ports: {ports}")
    print(f"Blocking ports: {ports}\n")

    for p in ports:
        try:
            rule = add_firewall_rule(p)
            rules.append(rule)
        except Exception as e:
            print(f"[ERROR] Port {p}: {e}")

    return rules


def rollback_rules(rules):
    for r in rules:
        try:
            remove_firewall_rule(r)
        except Exception as e:
            print(f"[ERROR removing] {r}: {e}")


def main():
    ports = get_listening_ports()

    if not ports:
        print("No listening ports found.")
        return

    rules = apply_block(ports)

    print(f"\n[+] System locked down for {BLOCK_DURATION} seconds...\n")

    time.sleep(BLOCK_DURATION)

    print("\n[+] Rolling back firewall rules...\n")
    rollback_rules(rules)

    print("\n[+] System restored.")


if __name__ == "__main__":
    main()