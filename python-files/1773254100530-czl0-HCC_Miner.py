#!/usr/bin/env python3
"""
HCC (Hash Cash Credits) CLI Miner - Python Implementation
Converted from Go version HCC-cli-miner.go
"""

import argparse
import hashlib
import json
import math
import os
import random
import re
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import requests

# Default configuration
DEFAULT_URL = "https://hashcashfaucet.com/api"
DEFAULT_WORKERS = 0  # 0 = auto-detect
DEFAULT_PROGRESS_INTERVAL = 2
DEFAULT_BENCH_BITS = 28
DEFAULT_BENCH_ROUNDS = 10
DEFAULT_NONCE_OFFSET = -1  # -1 = random

# Global state
args = None
session = requests.Session()
session.timeout = 30
cancel_event = threading.Event()
total_tries = 0
total_tries_lock = threading.Lock()


# =====================
# Data Classes (API structs)
# =====================

@dataclass
class MeResponse:
    account_id: str
    credits: int
    earned_today: int
    daily_earn_cap: int
    cooldown_until: int
    server_time: int
    next_seq: int = 0  # Some API responses include this
    
    def __init__(self, **kwargs):
        self.account_id = kwargs.get('account_id', '')
        self.credits = kwargs.get('credits', 0)
        self.earned_today = kwargs.get('earned_today', 0)
        self.daily_earn_cap = kwargs.get('daily_earn_cap', 0)
        self.cooldown_until = kwargs.get('cooldown_until', 0)
        self.server_time = kwargs.get('server_time', 0)
        self.next_seq = kwargs.get('next_seq', 0)


@dataclass
class ChallengeResponse:
    stamp: str
    bits: int
    sig: str
    
    def __init__(self, **kwargs):
        self.stamp = kwargs.get('stamp', '')
        self.bits = kwargs.get('bits', 0)
        self.sig = kwargs.get('sig', '')


@dataclass
class SubmitResponse:
    ok: bool
    credits: int
    next_seq: int
    cooldown_until: int
    message: str = ""
    
    def __init__(self, **kwargs):
        self.ok = kwargs.get('ok', False)
        self.credits = kwargs.get('credits', 0)
        self.next_seq = kwargs.get('next_seq', 0)
        self.cooldown_until = kwargs.get('cooldown_until', 0)
        self.message = kwargs.get('message', '')


@dataclass
class PowResult:
    nonce: int
    tries: int
    elapsed: float
    rate_khs: float
    canceled: bool


# =====================
# CLI Argument Parsing
# =====================

def parse_args():
    global args
    parser = argparse.ArgumentParser(
        description="HCC (Hash Cash Credits) CLI Miner - PoW Faucet Client"
    )
    parser.add_argument(
        "--url",
        type=str,
        default=DEFAULT_URL,
        help="Base URL of the Hashcash PoW faucet API"
    )
    parser.add_argument(
        "--key",
        type=str,
        default="7c1bd1f8c2bc1e1762358a054a894f8ecdc56f77d1558842",
        help="Private key (from the web UI)"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help="Number of PoW worker threads (0 = auto-detect CPU cores)"
    )
    parser.add_argument(
        "--stop-at-cap",
        action="store_true",
        default=False,
        help="Stop when daily earn cap is reached"
    )
    parser.add_argument(
        "--no-stop-at-cap",
        action="store_false",
        dest="stop_at_cap",
        help="Continue mining even after daily cap reached"
    )
    parser.add_argument(
        "--extreme",
        action="store_true",
        default=False,
        help="Enable HashCash Extreme mode (no cooldown, higher difficulty, separate daily cap)"
    )
    parser.add_argument(
        "--potato",
        action="store_true",
        default=False,
        help="Enable HashCash POTATO mode (lower difficulty, counts toward normal cap, longer cooldown)"
    )
    parser.add_argument(
        "--bench",
        action="store_true",
        default=False,
        help="Run local benchmark only (no API calls)"
    )
    parser.add_argument(
        "--bench-bits",
        type=int,
        default=DEFAULT_BENCH_BITS,
        help="Benchmark difficulty in leading zero bits"
    )
    parser.add_argument(
        "--bench-rounds",
        type=int,
        default=DEFAULT_BENCH_ROUNDS,
        help="Number of benchmark rounds"
    )
    parser.add_argument(
        "--progress",
        action="store_true",
        default=True,
        help="Show live PoW progress (hashrate/ETA)"
    )
    parser.add_argument(
        "--no-progress",
        action="store_false",
        dest="show_progress",
        help="Disable live progress"
    )
    parser.add_argument(
        "--progress-interval",
        type=int,
        default=DEFAULT_PROGRESS_INTERVAL,
        help="Progress update interval in seconds"
    )
    parser.add_argument(
        "--nonce-offset",
        type=int,
        default=DEFAULT_NONCE_OFFSET,
        help="Nonce start offset (-1 = random)"
    )
    
    args = parser.parse_args()
    return args


# =====================
# HTTP Helpers
# =====================

def api_get(path: str, into_class=None) -> Any:
    """Make GET request to API"""
    url = args.url + path
    headers = {}
    if args.key:
        headers["Authorization"] = f"Bearer {args.key}"
    
    try:
        resp = session.get(url, headers=headers)
        if resp.status_code < 200 or resp.status_code >= 300:
            raise Exception(f"GET {path} failed: {resp.status_code} - {resp.text}")
        
        if into_class:
            data = resp.json()
            return into_class(**data) if isinstance(data, dict) else data
        return resp.json() if resp.text else None
    except requests.RequestException as e:
        raise Exception(f"GET {path} request failed: {e}")


def api_post(path: str, payload: Dict, into_class=None) -> Any:
    """Make POST request to API"""
    url = args.url + path
    headers = {"Content-Type": "application/json"}
    if args.key:
        headers["Authorization"] = f"Bearer {args.key}"
    
    try:
        resp = session.post(url, json=payload, headers=headers)
        if resp.status_code < 200 or resp.status_code >= 300:
            raise Exception(f"POST {path} failed: {resp.status_code} - {resp.text}")
        
        if into_class:
            data = resp.json()
            return into_class(**data) if isinstance(data, dict) else data
        return resp.json() if resp.text else None
    except requests.RequestException as e:
        raise Exception(f"POST {path} request failed: {e}")


def cancel_pow():
    """Cancel current PoW (best-effort cleanup)"""
    url = args.url + "/cancel_pow"
    headers = {}
    if args.key:
        headers["Authorization"] = f"Bearer {args.key}"
    
    try:
        # Short timeout for cleanup
        cancel_session = requests.Session()
        cancel_session.timeout = 5
        resp = cancel_session.post(url, headers=headers)
        if resp.status_code < 200 or resp.status_code >= 300:
            print(f"[!] cancel_pow failed: {resp.status_code} - {resp.text}")
            return
        print("[*] cancel_pow: ok (best-effort)")
    except Exception as e:
        print(f"[!] cancel_pow: {e}")


# =====================
# PoW Implementation
# =====================

def get_nonce_offset() -> int:
    """Get nonce offset - random by default"""
    if args.nonce_offset >= 0:
        return args.nonce_offset
    
    # Random offset: avoid multiple instances searching same nonces
    return random.randint(0, 10**12)


def leading_zero_bits(b: bytes) -> int:
    """Count leading zero bits in a byte array"""
    total = 0
    for v in b:
        if v == 0:
            total += 8
            continue
        # Count leading zeros in this byte
        for i in range(7, -1, -1):
            if (v >> i) & 1:
                break
            total += 1
        break
    return total


def expected_tries(bits: int) -> float:
    """Expected number of trials for given difficulty"""
    if bits <= 0:
        return 1
    return 2.0 ** bits


def fmt_mm_ss(seconds: float) -> str:
    """Format duration as Xm YYs"""
    if seconds < 0:
        seconds = 0
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes}m {secs:02d}s"


def mine_nonce_range(stamp: str, bits: int, start_nonce: int, step: int, 
                     result_holder: dict, worker_id: int) -> Optional[PowResult]:
    """Mine nonces in a given range (start, start+step, start+2*step, ...)"""
    global total_tries
    
    prefix = stamp + '|'
    nonce = start_nonce
    tries = 0
    
    while not cancel_event.is_set():
        # Build input: stamp + '|' + nonce
        data = f"{prefix}{nonce}".encode()
        
        # SHA256 hash
        h = hashlib.sha256(data).digest()
        tries += 1
        
        # Update global counter periodically
        if tries & 0xFFF == 0:
            with total_tries_lock:
                total_tries += 0x1000
            tries = tries & 0xFFF  # Keep remainder
        
        # Check if solution found
        if leading_zero_bits(h) >= bits:
            # Flush remaining tries
            with total_tries_lock:
                total_tries += tries
            
            result_holder['found'] = True
            result_holder['nonce'] = nonce
            result_holder['worker_id'] = worker_id
            return PowResult(
                nonce=nonce,
                tries=0,  # Will be calculated globally
                elapsed=0,
                rate_khs=0,
                canceled=False
            )
        
        nonce += step
    
    # Worker was canceled
    with total_tries_lock:
        total_tries += tries
    
    return None


def solve_pow(stamp: str, bits: int, num_workers: int, show_prog: bool, 
              prog_interval: float, nonce_offset: int) -> PowResult:
    """Multi-worker PoW solver"""
    global total_tries
    
    if num_workers < 1:
        num_workers = 1
    
    total_tries = 0
    cancel_event.clear()
    
    start_time = time.time()
    result_holder = {'found': False, 'nonce': 0, 'worker_id': -1}
    
    # Progress reporting thread
    prog_thread = None
    if show_prog:
        def progress_reporter():
            exp = expected_tries(bits)
            while not cancel_event.is_set():
                time.sleep(prog_interval)
                if cancel_event.is_set():
                    break
                
                with total_tries_lock:
                    current_tries = total_tries
                
                elapsed = time.time() - start_time
                rate = current_tries / elapsed / 1000.0  # kH/s
                eta = 0
                if rate > 0:
                    remaining = exp - current_tries
                    if remaining < 0:
                        remaining = 0
                    eta = remaining / (rate * 1000.0)
                
                print(f"\r[*] PoW searching... tries={current_tries}  rate={rate:.1f} kH/s  ETA≈{fmt_mm_ss(eta)}", end='', flush=True)
        
        prog_thread = threading.Thread(target=progress_reporter, daemon=True)
        prog_thread.start()
    
    # Start worker threads
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for w in range(num_workers):
            start_nonce = nonce_offset + w
            future = executor.submit(
                mine_nonce_range, stamp, bits, start_nonce, num_workers, result_holder, w
            )
            futures.append(future)
        
        # Wait for solution or cancellation
        found = False
        while not result_holder['found'] and not cancel_event.is_set():
            time.sleep(0.05)
            
            # Check if any future is done
            for f in futures:
                if f.done():
                    try:
                        f.result()
                    except Exception:
                        pass
        
        # Cancel all workers if found
        if result_holder['found']:
            cancel_event.set()
            found = True
        
        # Wait for futures to complete (with timeout)
        for f in futures:
            try:
                f.result(timeout=1)
            except Exception:
                pass
    
    # Stop progress reporter
    if show_prog and prog_thread:
        cancel_event.set()
        prog_thread.join(timeout=1)
    
    elapsed = time.time() - start_time
    tries = total_tries
    rate = tries / elapsed / 1000.0 if elapsed > 0 else 0
    
    if found:
        return PowResult(
            nonce=result_holder['nonce'],
            tries=tries,
            elapsed=elapsed,
            rate_khs=rate,
            canceled=False
        )
    else:
        return PowResult(
            nonce=0,
            tries=tries,
            elapsed=elapsed,
            rate_khs=rate,
            canceled=True
        )


# =====================
# Benchmark Mode
# =====================

def run_benchmark_mining(workers: int, bits: int, rounds: int):
    """Run local benchmark"""
    if workers <= 0:
        workers = os.cpu_count() or 4
    
    print("=== Hashcash CLI Miner Mining Benchmark ===")
    print(f"Workers: {workers}")
    print(f"NumCPU: {os.cpu_count()}")
    print(f"Difficulty (bits): {bits}")
    print(f"Rounds: {rounds}")
    print("(Uses the same inner loop as real mining: SHA256(stamp + '|' + decimal nonce))")
    print()
    
    # Dummy stamp: PoW success probability depends only on bits
    stamp = f"bench|act=earn_credit|acct=local|seq=0|bits={bits}|exp=0"
    
    total_tries_sum = 0
    total_time = 0.0
    best_rate = 0.0
    worst_rate = float('inf')
    
    for i in range(1, rounds + 1):
        nonce_offset = get_nonce_offset()
        cancel_event.clear()
        
        start = time.time()
        res = solve_pow(stamp, bits, workers, False, 0, nonce_offset)
        elapsed = time.time() - start
        
        mh = res.tries / elapsed / 1e6 if elapsed > 0 else 0
        
        total_tries_sum += res.tries
        total_time += elapsed
        if mh > best_rate:
            best_rate = mh
        if mh < worst_rate:
            worst_rate = mh
        
        print(f"Round {i}/{rounds}: tries={res.tries}  time={elapsed:.2f}s  rate={mh:.2f} MH/s  nonce={res.nonce}")
    
    avg_mh = total_tries_sum / total_time / 1e6 if total_time > 0 else 0
    avg_solve = total_time / rounds if rounds > 0 else 0
    
    print()
    print(f"Average: {avg_mh:.2f} MH/s (best {best_rate:.2f}, worst {worst_rate:.2f})")
    print(f"Average solve time: {avg_solve:.2f}s at bits={bits}")
    print(f"Theoretical expected tries: ~2^{bits} = {expected_tries(bits):.0f}")
    if avg_mh > 0:
        exp_sec = expected_tries(bits) / (avg_mh * 1e6)
        print(f"Expected time from avg rate: ~{exp_sec:.2f}s")


# =====================
# Mining Logic
# =====================

def get_account_info() -> MeResponse:
    """Get account information"""
    return api_get("/me", MeResponse)


def request_challenge(mode: str) -> ChallengeResponse:
    """Request a mining challenge"""
    action_map = {
        "extreme": "earn_extreme",
        "potato": "earn_potato",
        "normal": "earn_credit"
    }
    
    path_map = {
        "extreme": "/challenge_extreme",
        "potato": "/challenge_potato",
        "normal": "/challenge"
    }
    
    path = path_map.get(mode, "/challenge")
    action = action_map.get(mode, "earn_credit")
    
    return api_post(path, {"action": action}, ChallengeResponse)


def submit_pow(stamp: str, sig: str, nonce: int) -> SubmitResponse:
    """Submit PoW solution"""
    payload = {
        "stamp": stamp,
        "sig": sig,
        "nonce": str(nonce)
    }
    return api_post("/submit_pow", payload, SubmitResponse)


def stamp_seq(stamp: str) -> tuple:
    """Extract seq from stamp"""
    parts = stamp.split('|')
    for p in parts:
        if p.startswith('seq='):
            try:
                return int(p[4:]), True
            except ValueError:
                return 0, False
    return 0, False


def sleep_with_countdown(total_seconds: int):
    """Sleep with countdown display"""
    if total_seconds <= 0:
        return
    
    while total_seconds > 0 and not cancel_event.is_set():
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        print(f"\r[*] Cooldown active, waiting {minutes}m {seconds:02d}s...", end='', flush=True)
        time.sleep(1)
        total_seconds -= 1
    
    print(f"\r[*] Cooldown done.                      \n")


def mine_one_credit(mode: str, nonce_offset: int) -> tuple:
    """Mine one credit - returns (SubmitResponse, PowResult)"""
    mode_label = {"normal": "normal", "extreme": "EXTREME", "potato": "POTATO"}.get(mode, "normal")
    
    while True:
        # Request challenge
        ch = request_challenge(mode)
        cur_seq, _ = stamp_seq(ch.stamp)
        print(f"[+] Challenge ({mode_label}): bits={ch.bits}, stamp={ch.stamp[:32]}...")
        
        # Cancel channel for this challenge
        cancel_event.clear()
        
        # Challenge refresh checker - check every 60s if seq changed
        refresh_stop = threading.Event()
        
        def challenge_checker(orig_seq: int):
            while not refresh_stop.is_set():
                time.sleep(60)
                if refresh_stop.is_set():
                    break
                try:
                    latest = request_challenge(mode)
                    new_seq, ok = stamp_seq(latest.stamp)
                    if ok and new_seq != orig_seq:
                        print("\n[!] another miner likely won. Refreshing challenge...")
                        cancel_event.set()
                        return
                except Exception:
                    # Ignore transient errors
                    continue
        
        checker_thread = threading.Thread(target=challenge_checker, args=(cur_seq,), daemon=True)
        checker_thread.start()
        
        # Solve PoW
        interval = args.progress_interval
        res = solve_pow(ch.stamp, ch.bits, args.workers, args.show_progress, interval, nonce_offset)
        
        # Stop the checker
        refresh_stop.set()
        checker_thread.join(timeout=1)
        
        if res.canceled:
            # Immediately restart loop
            continue
        
        khs = res.tries / res.elapsed / 1000.0 if res.elapsed > 0 else 0
        print(f"[+] PoW solved ({mode_label}): nonce={res.nonce}, time={res.elapsed:.2f}s, rate≈{khs:.1f} kH/s ({args.workers} workers)")
        
        # Submit solution
        try:
            sub = submit_pow(ch.stamp, ch.sig, res.nonce)
            return sub, res
        except Exception as e:
            err_str = str(e)
            
            # Handle stale seq / replay
            if "409" in err_str or "stale seq" in err_str or "replay" in err_str:
                print("[!] Stale seq / replay detected (another miner likely won). Refreshing challenge...")
                time.sleep(0.5)
                continue
            
            raise


# =====================
# Main
# =====================

def main():
    global args
    args = parse_args()
    
    # Validate arguments
    if args.extreme and args.potato:
        print("ERROR: --extreme and --potato are mutually exclusive. Choose one.")
        sys.exit(1)
    
    # Benchmark mode
    if args.bench:
        workers = args.workers if args.workers > 0 else os.cpu_count() or 4
        run_benchmark_mining(workers, args.bench_bits, args.bench_rounds)
        return
    
    # Auto-detect workers
    if args.workers <= 0:
        args.workers = os.cpu_count() or 4
    
    # Validate private key
    if not args.key:
        print("ERROR: please provide --key with your private faucet key.")
        sys.exit(1)
    
    print("=== Hashcash PoW Faucet CLI Miner ===")
    print(f"Base URL: {args.url}")
    print(f"Workers: {args.workers}")
    print(f"NumCPU: {os.cpu_count()}")
    print(f"Stop at daily cap: {args.stop_at_cap}")
    print(f"Live progress: {args.show_progress} (interval: {args.progress_interval}s)")
    
    if args.extreme:
        print("Mode: EXTREME (no cooldown, higher difficulty, separate daily cap)")
    elif args.potato:
        print("Mode: POTATO (lower difficulty, separate daily cap; normal cooldown)")
    else:
        print("Mode: normal")
    
    nonce_offset = get_nonce_offset()
    print(f"Nonce offset: {nonce_offset} (use --nonce-offset to set manually)")
    print("Press Ctrl+C to stop.\n")
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        print("\n[!] Caught Ctrl+C / SIGTERM -> releasing IP lock...")
        cancel_pow()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Main mining loop
    session_start = time.time()
    last_known_credits = -1
    session_credits_earned = 0
    session_pow_tries = 0
    session_pow_time = 0.0
    session_solved = 0
    
    while True:
        try:
            me = get_account_info()
        except Exception as e:
            print(f"[!] /me error: {e}")
            time.sleep(10)
            continue
        
        print(f"Account: {me.account_id}")
        print(f"  Credits: {me.credits}")
        
        if args.extreme:
            print(f"  Earned EXTREME today: {me.earned_today}")
        elif args.potato:
            print(f"  Earned POTATO today: {me.earned_today}")
        else:
            print(f"  Earned today: {me.earned_today} / {me.daily_earn_cap}")
        
        if last_known_credits < 0:
            last_known_credits = me.credits
        
        # Check daily cap (normal mode only)
        if not args.extreme and not args.potato and args.stop_at_cap and me.daily_earn_cap > 0 and me.earned_today >= me.daily_earn_cap:
            print("[*] Daily cap reached, stopping miner.")
            break
        
        # Cooldown check (not for extreme mode)
        if not args.extreme:
            now = me.server_time
            if me.cooldown_until > now:
                wait = me.cooldown_until - now + 2
                sleep_with_countdown(int(wait))
                continue
        
        # Mine mode selection
        if args.extreme:
            print("[*] Mining one EXTREME credit...")
            mode = "extreme"
        elif args.potato:
            print("[*] Mining one POTATO credit...")
            mode = "potato"
        else:
            print("[*] Mining one credit...")
            mode = "normal"
        
        # Mine one credit
        try:
            sub, pow_res = mine_one_credit(mode, nonce_offset)
        except Exception as e:
            err_str = str(e)
            
            # Check for daily cap messages
            if args.extreme and "extreme daily cap" in err_str:
                print("[*] Extreme daily cap reached according to server, stopping miner.")
                break
            if args.potato and "potato daily cap" in err_str:
                print("[*] Potato daily cap reached according to server, stopping miner.")
                break
            
            print(f"[!] Mining error: {e}")
            time.sleep(10)
            continue
        
        # Update session stats
        session_solved += 1
        session_pow_tries += pow_res.tries
        session_pow_time += pow_res.elapsed
        
        delta = sub.credits - last_known_credits
        if delta < 0:
            delta = 0
        session_credits_earned += delta
        last_known_credits = sub.credits
        
        # Calculate session metrics
        session_dur = time.time() - session_start
        credits_per_hour = session_credits_earned / (session_dur / 3600) if session_dur > 0 else 0
        avg_khs = session_pow_tries / session_pow_time / 1000 if session_pow_time > 0 else 0
        
        print(f"[+] Submit ok: credits={sub.credits}, next_seq={sub.next_seq}")
        print(f"    Session: +{session_credits_earned} credits in {fmt_mm_ss(session_dur)} ({credits_per_hour:.2f} credits/hour), avg PoW rate≈{avg_khs:.1f} kH/s, solves={session_solved}\n")
        
        time.sleep(2)


if __name__ == "__main__":
    main()

