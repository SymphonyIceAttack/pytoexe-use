#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SurPriseShock 1.0
Classic instant messenger
Single-file Python implementation.

Requirements:
    Python 3.x
    Tkinter
    SQLite3

No third-party packages required.

Files created automatically:
    surprise_shock.db

Optional:
    connect.gif
"""

import argparse
import hashlib
import os
import queue
import secrets
import socket
import sqlite3
import string
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

APP_NAME = "SurPriseShock"
VERSION = "1.0"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000

DB_FILE = "surprise_shock.db"

MAX_USERNAME = 24
MAX_PASSWORD = 128
MAX_MESSAGE = 2048
MAX_AWAY = 256
MAX_PACKET = 8192

STATUS_ONLINE = "Online"
STATUS_AWAY = "Away"
STATUS_BUSY = "Busy"
STATUS_INVISIBLE = "Invisible"
STATUS_OFFLINE = "Offline"

VALID_STATUSES = {
    STATUS_ONLINE,
    STATUS_AWAY,
    STATUS_BUSY,
    STATUS_INVISIBLE,
}

# ============================================================
# DATABASE
# ============================================================

class Database:
    def __init__(self, filename=DB_FILE):
        self.filename = filename
        self.lock = threading.RLock()

        self.conn = sqlite3.connect(
            self.filename,
            check_same_thread=False
        )

        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")

        self.create_tables()

    def create_tables(self):
        with self.lock:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Offline',
                    away_message TEXT NOT NULL DEFAULT '',
                    created_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS buddies (
                    owner TEXT NOT NULL COLLATE NOCASE,
                    buddy TEXT NOT NULL COLLATE NOCASE,
                    group_name TEXT NOT NULL DEFAULT 'Buddies',

                    PRIMARY KEY(owner, buddy),

                    FOREIGN KEY(owner)
                        REFERENCES users(username)
                        ON DELETE CASCADE,

                    FOREIGN KEY(buddy)
                        REFERENCES users(username)
                        ON DELETE CASCADE
                );
            """)

            self.conn.commit()

    def close(self):
        with self.lock:
            self.conn.close()

    @staticmethod
    def normalize_username(username):
        return username.strip()

    @staticmethod
    def valid_username(username):
        if not username:
            return False

        if len(username) > MAX_USERNAME:
            return False

        allowed = string.ascii_letters + string.digits + "_-."

        return all(c in allowed for c in username)

    def user_exists(self, username):
        with self.lock:
            row = self.conn.execute(
                "SELECT 1 FROM users WHERE username = ? COLLATE NOCASE",
                (username,)
            ).fetchone()

            return row is not None

    def create_user(self, username, password):
        username = self.normalize_username(username)

        if not self.valid_username(username):
            return False, "Invalid username."

        if not password:
            return False, "Password cannot be empty."

        if len(password) > MAX_PASSWORD:
            return False, "Password is too long."

        if self.user_exists(username):
            return False, "Username already exists."

        salt = secrets.token_hex(32)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("ascii"),
            200_000
        ).hex()

        try:
            with self.lock:
                self.conn.execute(
                    """
                    INSERT INTO users
                    (username, password_hash, salt, status, away_message, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        username,
                        password_hash,
                        salt,
                        STATUS_OFFLINE,
                        "",
                        int(time.time())
                    )
                )

                self.conn.commit()

            return True, "Registration successful."

        except sqlite3.IntegrityError:
            return False, "Username already exists."

    def verify_login(self, username, password):
        with self.lock:
            row = self.conn.execute(
                """
                SELECT username, password_hash, salt
                FROM users
                WHERE username = ? COLLATE NOCASE
                """,
                (username,)
            ).fetchone()

        if row is None:
            return False, "Invalid username or password."

        real_username, stored_hash, salt = row

        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("ascii"),
            200_000
        ).hex()

        if not secrets.compare_digest(candidate, stored_hash):
            return False, "Invalid username or password."

        return True, real_username

    def set_status(self, username, status, away_message=""):
        if status not in VALID_STATUSES:
            status = STATUS_ONLINE

        away_message = away_message[:MAX_AWAY]

        with self.lock:
            self.conn.execute(
                """
                UPDATE users
                SET status = ?, away_message = ?
                WHERE username = ? COLLATE NOCASE
                """,
                (status, away_message, username)
            )

            self.conn.commit()

    def set_offline(self, username):
        with self.lock:
            self.conn.execute(
                """
                UPDATE users
                SET status = ?, away_message = ''
                WHERE username = ? COLLATE NOCASE
                """,
                (STATUS_OFFLINE, username)
            )

            self.conn.commit()

    def get_buddies(self, username):
        with self.lock:
            rows = self.conn.execute(
                """
                SELECT buddy, group_name
                FROM buddies
                WHERE owner = ? COLLATE NOCASE
                ORDER BY group_name, buddy COLLATE NOCASE
                """,
                (username,)
            ).fetchall()

        return rows

    def add_buddy(self, owner, buddy, group_name="Buddies"):
        if owner.lower() == buddy.lower():
            return False, "You cannot add yourself."

        if not self.user_exists(buddy):
            return False, "That user does not exist."

        try:
            with self.lock:
                self.conn.execute(
                    """
                    INSERT INTO buddies(owner, buddy, group_name)
                    VALUES (?, ?, ?)
                    """,
                    (owner, buddy, group_name)
                )

                self.conn.commit()

            return True, "Buddy added."

        except sqlite3.IntegrityError:
            return False, "That buddy is already in your list."

    def remove_buddy(self, owner, buddy):
        with self.lock:
            cur = self.conn.execute(
                """
                DELETE FROM buddies
                WHERE owner = ? COLLATE NOCASE
                AND buddy = ? COLLATE NOCASE
                """,
                (owner, buddy)
            )

            self.conn.commit()

            return cur.rowcount > 0

    def buddy_of(self, owner, buddy):
        with self.lock:
            row = self.conn.execute(
                """
                SELECT 1
                FROM buddies
                WHERE owner = ? COLLATE NOCASE
                AND buddy = ? COLLATE NOCASE
                """,
                (owner, buddy)
            ).fetchone()

        return row is not None

    def get_user_status(self, username):
        with self.lock:
            row = self.conn.execute(
                """
                SELECT status, away_message
                FROM users
                WHERE username = ? COLLATE NOCASE
                """,
                (username,)
            ).fetchone()

        if row is None:
            return STATUS_OFFLINE, ""

        return row


# ============================================================
# PROTOCOL
# ============================================================

def encode_field(value):
    """
    Percent-escape protocol separators.

    | becomes %7C
    % becomes %25
    CR becomes %0D
    LF becomes %0A
    """
    value = str(value)

    return (
        value
        .replace("%", "%25")
        .replace("|", "%7C")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )


def decode_field(value):
    try:
        result = ""
        i = 0

        while i < len(value):
            if value[i] == "%" and i + 2 < len(value):
                code = value[i + 1:i + 3]

                try:
                    result += chr(int(code, 16))
                    i += 3
                    continue
                except ValueError:
                    pass

            result += value[i]
            i += 1

        return result

    except Exception:
        return value


def packet(command, *fields):
    return (
        command +
        "".join("|" + encode_field(field) for field in fields) +
        "\n"
    ).encode("utf-8")


def parse_packet(line):
    parts = line.rstrip("\r\n").split("|")

    if not parts:
        return "", []

    command = parts[0]

    return command, [
        decode_field(x)
        for x in parts[1:]
    ]


# ============================================================
# SERVER CLIENT CONNECTION
# ============================================================

class ClientConnection:
    def __init__(self, server, sock, address):
        self.server = server
        self.sock = sock
        self.address = address

        self.username = None
        self.authenticated = False

        self.send_lock = threading.Lock()
        self.alive = True

    def send(self, command, *fields):
        if not self.alive:
            return False

        try:
            data = packet(command, *fields)

            with self.send_lock:
                self.sock.sendall(data)

            return True

        except OSError:
            self.alive = False
            return False

    def close(self):
        self.alive = False

        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        try:
            self.sock.close()
        except OSError:
            pass


# ============================================================
# SERVER
# ============================================================

class SurPriseShockServer:
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port

        self.database = Database()

        self.sock = None
        self.running = False

        self.clients = {}
        self.clients_lock = threading.RLock()

    def log(self, text):
        print(text, flush=True)

    def start(self):
        if self.running:
            return

        self.sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        self.sock.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        self.sock.bind((self.host, self.port))
        self.sock.listen(32)

        self.running = True

        self.log("")
        self.log("====================================")
        self.log("   SurPriseShock Server 1.0")
        self.log("====================================")
        self.log(
            "Listening on %s:%d" %
            (self.host, self.port)
        )

        thread = threading.Thread(
            target=self.accept_loop,
            daemon=True
        )

        thread.start()

    def stop(self):
        self.running = False

        try:
            self.sock.close()
        except Exception:
            pass

        with self.clients_lock:
            clients = list(self.clients.values())

        for client in clients:
            client.close()

        self.database.close()

    def accept_loop(self):
        while self.running:
            try:
                client_sock, address = self.sock.accept()

                connection = ClientConnection(
                    self,
                    client_sock,
                    address
                )

                self.log(
                    "[+] connection from %s:%d" %
                    address
                )

                threading.Thread(
                    target=self.client_loop,
                    args=(connection,),
                    daemon=True
                ).start()

            except OSError:
                if self.running:
                    self.log("[!] Accept error.")

    def client_loop(self, client):
        buffer = b""

        try:
            client.sock.settimeout(300)

            while client.alive:
                data = client.sock.recv(4096)

                if not data:
                    break

                buffer += data

                if len(buffer) > MAX_PACKET * 4:
                    client.send(
                        "ERROR",
                        "Packet buffer overflow."
                    )
                    break

                while b"\n" in buffer:
                    raw_line, buffer = buffer.split(
                        b"\n",
                        1
                    )

                    if len(raw_line) > MAX_PACKET:
                        client.send(
                            "ERROR",
                            "Packet too large."
                        )
                        continue

                    try:
                        line = raw_line.decode(
                            "utf-8",
                            errors="replace"
                        )
                    except Exception:
                        continue

                    command, fields = parse_packet(line)

                    try:
                        self.handle_packet(
                            client,
                            command,
                            fields
                        )
                    except Exception as exc:
                        self.log(
                            "[!] Packet error from %s: %s" %
                            (client.username or "unauthenticated", exc)
                        )

                        client.send(
                            "ERROR",
                            "Malformed request."
                        )

        except socket.timeout:
            client.send("ERROR", "Connection timeout.")

        except OSError:
            pass

        finally:
            self.disconnect_client(client)

    def handle_packet(self, client, command, fields):
        if command == "REGISTER":
            self.handle_register(client, fields)
            return

        if command == "LOGIN":
            self.handle_login(client, fields)
            return

        if not client.authenticated:
            client.send(
                "ERROR",
                "Authentication required."
            )
            return

        if command == "LOGOUT":
            client.close()
            return

        if command == "MSG":
            self.handle_message(client, fields)
            return

        if command == "STATUS":
            self.handle_status(client, fields)
            return

        if command == "BUDDY_ADD":
            self.handle_buddy_add(client, fields)
            return

        if command == "BUDDY_REMOVE":
            self.handle_buddy_remove(client, fields)
            return

        client.send(
            "ERROR",
            "Unknown command."
        )

    def handle_register(self, client, fields):
        if len(fields) != 2:
            client.send(
                "REGISTER_FAIL",
                "Invalid registration packet."
            )
            return

        username, password = fields

        if len(username) > MAX_USERNAME:
            client.send(
                "REGISTER_FAIL",
                "Username is too long."
            )
            return

        ok, result = self.database.create_user(
            username,
            password
        )

        if ok:
            self.log(
                "[REG] %s registered" %
                username
            )

            client.send(
                "REGISTER_OK",
                result
            )

        else:
            client.send(
                "REGISTER_FAIL",
                result
            )

    def handle_login(self, client, fields):
        if len(fields) != 2:
            client.send(
                "LOGIN_FAIL",
                "Invalid login packet."
            )
            return

        username, password = fields

        if client.authenticated:
            client.send(
                "LOGIN_FAIL",
                "Already logged in."
            )
            return

        ok, result = self.database.verify_login(
            username,
            password
        )

        if not ok:
            client.send(
                "LOGIN_FAIL",
                result
            )
            return

        real_username = result

        with self.clients_lock:
            existing = self.clients.get(
                real_username.lower()
            )

            if existing is not None and existing.alive:
                client.send(
                    "LOGIN_FAIL",
                    "This account is already logged in."
                )
                return

            client.username = real_username
            client.authenticated = True

            self.clients[
                real_username.lower()
            ] = client

        self.database.set_status(
            real_username,
            STATUS_ONLINE,
            ""
        )

        self.log(
            "[+] %s connected" %
            real_username
        )

        client.send(
            "LOGIN_OK",
            real_username
        )

        self.send_buddy_list(client)
        self.send_presence_for_buddies(client)

        self.broadcast_presence(
            real_username,
            STATUS_ONLINE,
            "",
            include_self=False
        )

    def handle_message(self, client, fields):
        if len(fields) != 2:
            client.send(
                "ERROR",
                "Invalid message packet."
            )
            return

        recipient, message = fields

        message = message.strip()

        if not recipient:
            client.send(
                "ERROR",
                "Recipient is required."
            )
            return

        if not message:
            client.send(
                "ERROR",
                "Empty messages are not allowed."
            )
            return

        if len(message) > MAX_MESSAGE:
            client.send(
                "ERROR",
                "Message is too long."
            )
            return

        target = self.get_client(recipient)

        timestamp = time.strftime(
            "%H:%M:%S"
        )

        if target is None:
            client.send(
                "MSG_FAIL",
                recipient,
                "User is offline."
            )
            return

        target.send(
            "MSG_FROM",
            client.username,
            timestamp,
            message
        )

        client.send(
            "MSG_SENT",
            recipient,
            timestamp,
            message
        )

        self.log(
            "[MSG] %s -> %s: %s" %
            (
                client.username,
                recipient,
                message
            )
        )

    def handle_status(self, client, fields):
        if not fields:
            return

        status = fields[0]
        away = fields[1] if len(fields) > 1 else ""

        if status not in VALID_STATUSES:
            client.send(
                "ERROR",
                "Invalid status."
            )
            return

        if status != STATUS_AWAY:
            away = ""

        away = away[:MAX_AWAY]

        self.database.set_status(
            client.username,
            status,
            away
        )

        self.broadcast_presence(
            client.username,
            status,
            away,
            include_self=True
        )

    def handle_buddy_add(self, client, fields):
        if len(fields) != 1:
            client.send(
                "ERROR",
                "Invalid buddy request."
            )
            return

        buddy = fields[0].strip()

        if not buddy:
            client.send(
                "ERROR",
                "Buddy name is required."
            )
            return

        if len(buddy) > MAX_USERNAME:
            client.send(
                "ERROR",
                "Buddy name is too long."
            )
            return

        ok, result = self.database.add_buddy(
            client.username,
            buddy
        )

        if not ok:
            client.send(
                "ERROR",
                result
            )
            return

        client.send(
            "BUDDY_ADDED",
            buddy
        )

        self.send_buddy_list(client)

        target = self.get_client(buddy)

        if target is not None:
            status, away = self.database.get_user_status(
                client.username
            )

            target.send(
                "BUDDY_NOTICE",
                client.username,
                status,
                away
            )

    def handle_buddy_remove(self, client, fields):
        if len(fields) != 1:
            client.send(
                "ERROR",
                "Invalid buddy request."
            )
            return

        buddy = fields[0]

        if self.database.remove_buddy(
            client.username,
            buddy
        ):
            client.send(
                "BUDDY_REMOVED",
                buddy
            )

            self.send_buddy_list(client)

        else:
            client.send(
                "ERROR",
                "Buddy was not in your list."
            )

    def get_client(self, username):
        with self.clients_lock:
            return self.clients.get(
                username.lower()
            )

    def send_buddy_list(self, client):
        buddies = self.database.get_buddies(
            client.username
        )

        client.send(
            "BUDDY_LIST_BEGIN"
        )

        for buddy, group_name in buddies:
            status, away = self.database.get_user_status(
                buddy
            )

            client.send(
                "BUDDY",
                buddy,
                group_name,
                status,
                away
            )

        client.send(
            "BUDDY_LIST_END"
        )

    def send_presence_for_buddies(self, client):
        buddies = self.database.get_buddies(
            client.username
        )

        for buddy, _group in buddies:
            status, away = self.database.get_user_status(
                buddy
            )

            client.send(
                "PRESENCE",
                buddy,
                status,
                away
            )

    def broadcast_presence(
        self,
        username,
        status,
        away,
        include_self=False
    ):
        with self.clients_lock:
            clients = list(
                self.clients.values()
            )

        for client in clients:
            if not client.authenticated:
                continue

            if not include_self:
                if client.username.lower() == username.lower():
                    continue

            if self.database.buddy_of(
                client.username,
                username
            ):
                client.send(
                    "PRESENCE",
                    username,
                    status,
                    away
                )

    def disconnect_client(self, client):
        if not client.authenticated:
            client.close()
            return

        username = client.username

        with self.clients_lock:
            current = self.clients.get(
                username.lower()
            )

            if current is client:
                del self.clients[
                    username.lower()
                ]

        self.database.set_offline(
            username
        )

        self.log(
            "[-] %s disconnected" %
            username
        )

        self.broadcast_presence(
            username,
            STATUS_OFFLINE,
            "",
            include_self=False
        )

        client.close()


# ============================================================
# CLIENT NETWORK CONNECTION
# ============================================================

class NetworkClient:
    def __init__(self, host, port, events):
        self.host = host
        self.port = port
        self.events = events

        self.sock = None
        self.running = False

        self.send_lock = threading.Lock()

    def connect(self):
        try:
            self.sock = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            self.sock.settimeout(10)

            self.sock.connect(
                (self.host, self.port)
            )

            self.sock.settimeout(None)

            self.running = True

            threading.Thread(
                target=self.receive_loop,
                daemon=True
            ).start()

            self.emit(
                "connected"
            )

            return True

        except OSError as exc:
            self.emit(
                "connection_error",
                str(exc)
            )

            try:
                self.sock.close()
            except Exception:
                pass

            self.sock = None

            return False

    def emit(self, event, *args):
        try:
            self.events.put(
                (event, args)
            )
        except Exception:
            pass

    def send(self, command, *fields):
        if not self.running or self.sock is None:
            return False

        try:
            data = packet(
                command,
                *fields
            )

            with self.send_lock:
                self.sock.sendall(data)

            return True

        except OSError as exc:
            self.emit(
                "connection_error",
                str(exc)
            )

            self.close()

            return False

    def receive_loop(self):
        buffer = b""

        try:
            while self.running:
                data = self.sock.recv(4096)

                if not data:
                    break

                buffer += data

                if len(buffer) > MAX_PACKET * 4:
                    self.emit(
                        "connection_error",
                        "Server sent too much data."
                    )
                    break

                while b"\n" in buffer:
                    raw, buffer = buffer.split(
                        b"\n",
                        1
                    )

                    if len(raw) > MAX_PACKET:
                        continue

                    line = raw.decode(
                        "utf-8",
                        errors="replace"
                    )

                    command, fields = parse_packet(
                        line
                    )

                    self.emit(
                        "packet",
                        command,
                        fields
                    )

        except OSError:
            pass

        finally:
            was_running = self.running
            self.running = False

            if was_running:
                self.emit(
                    "disconnected"
                )

    def close(self):
        self.running = False

        try:
            self.sock.shutdown(
                socket.SHUT_RDWR
            )
        except Exception:
            pass

        try:
            self.sock.close()
        except Exception:
            pass

        self.sock = None


# ============================================================
# CLASSIC UI
# ============================================================

class ClassicButton(tk.Button):
    def __init__(self, master, text="", command=None, **kwargs):
        super().__init__(
            master,
            text=text,
            command=command,
            relief=tk.RAISED,
            bd=2,
            padx=8,
            pady=2,
            font=("MS Sans Serif", 8),
            **kwargs
        )


class StatusIcon(tk.Canvas):
    COLORS = {
        STATUS_ONLINE: "#00aa00",
        STATUS_AWAY: "#e0a000",
        STATUS_BUSY: "#cc0000",
        STATUS_INVISIBLE: "#777777",
        STATUS_OFFLINE: "#bbbbbb",
    }

    def __init__(self, master, status=STATUS_OFFLINE):
        super().__init__(
            master,
            width=16,
            height=16,
            bd=0,
            highlightthickness=0,
            bg="#eeeeee"
        )

        self.status = status
        self.draw()

    def set_status(self, status):
        self.status = status
        self.draw()

    def draw(self):
        self.delete("all")

        color = self.COLORS.get(
            self.status,
            "#777777"
        )

        self.create_oval(
            2,
            2,
            14,
            14,
            fill=color,
            outline="#333333"
        )

        if self.status == STATUS_ONLINE:
            self.create_oval(
                5,
                5,
                8,
                8,
                fill="white",
                outline=""
            )


# ============================================================
# LOGIN WINDOW
# ============================================================

class LoginScreen:
    def __init__(self, app):
        self.app = app

        self.window = tk.Toplevel(
            app.root
        )

        self.window.title(
            "SurPriseShock"
        )

        self.window.geometry(
            "360x260"
        )

        self.window.resizable(
            False,
            False
        )

        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.app.quit
        )

        self.build()

    def build(self):
        root = self.window

        title = tk.Label(
            root,
            text="SurPriseShock",
            font=("Arial", 20, "bold"),
            bg="#316ac5",
            fg="white",
            pady=10
        )

        title.pack(
            fill=tk.X
        )

        body = tk.Frame(
            root,
            bg="#eeeeee"
        )

        body.pack(
            fill=tk.BOTH,
            expand=True,
            padx=16,
            pady=12
        )

        tk.Label(
            body,
            text="Username:",
            bg="#eeeeee",
            font=("MS Sans Serif", 9)
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=5
        )

        self.username = tk.Entry(
            body,
            font=("MS Sans Serif", 10)
        )

        self.username.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=5
        )

        tk.Label(
            body,
            text="Password:",
            bg="#eeeeee",
            font=("MS Sans Serif", 9)
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=5
        )

        self.password = tk.Entry(
            body,
            show="*",
            font=("MS Sans Serif", 10)
        )

        self.password.grid(
            row=1,
            column=1,
            sticky="ew",
            pady=5
        )

        body.columnconfigure(
            1,
            weight=1
        )

        buttons = tk.Frame(
            body,
            bg="#eeeeee"
        )

        buttons.grid(
            row=2,
            column=0,
            columnspan=2,
            pady=12
        )

        ClassicButton(
            buttons,
            "Login",
            self.login
        ).pack(
            side=tk.LEFT,
            padx=4
        )

        ClassicButton(
            buttons,
            "Register",
            self.register
        ).pack(
            side=tk.LEFT,
            padx=4
        )

        self.status = tk.Label(
            body,
            text="Disconnected",
            bg="#eeeeee",
            fg="#555555",
            anchor="w"
        )

        self.status.grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="ew"
        )

        self.password.bind(
            "<Return>",
            lambda e: self.login()
        )

        self.username.focus_set()

    def set_status(self, text):
        self.status.config(
            text=text
        )

    def login(self):
        username = self.username.get().strip()
        password = self.password.get()

        if not username or not password:
            messagebox.showerror(
                "SurPriseShock",
                "Enter your username and password.",
                parent=self.window
            )
            return

        self.set_status(
            "Connecting..."
        )

        self.app.connect_and_login(
            username,
            password
        )

    def register(self):
        RegisterWindow(
            self.app
        )


# ============================================================
# REGISTRATION
# ============================================================

class RegisterWindow:
    def __init__(self, app):
        self.app = app

        self.window = tk.Toplevel(
            app.root
        )

        self.window.title(
            "Register - SurPriseShock"
        )

        self.window.geometry(
            "350x240"
        )

        self.window.resizable(
            False,
            False
        )

        self.build()

    def build(self):
        root = self.window

        frame = tk.Frame(
            root,
            bg="#eeeeee"
        )

        frame.pack(
            fill=tk.BOTH,
            expand=True,
            padx=15,
            pady=15
        )

        tk.Label(
            frame,
            text="Create a SurPriseShock account",
            bg="#eeeeee",
            font=("Arial", 12, "bold")
        ).pack(
            pady=(0, 12)
        )

        fields = tk.Frame(
            frame,
            bg="#eeeeee"
        )

        fields.pack(
            fill=tk.X
        )

        tk.Label(
            fields,
            text="Username:",
            bg="#eeeeee"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=4
        )

        self.username = tk.Entry(
            fields
        )

        self.username.grid(
            row=0,
            column=1,
            sticky="ew",
            pady=4
        )

        tk.Label(
            fields,
            text="Password:",
            bg="#eeeeee"
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=4
        )

        self.password = tk.Entry(
            fields,
            show="*"
        )

        self.password.grid(
            row=1,
            column=1,
            sticky="ew",
            pady=4
        )

        tk.Label(
            fields,
            text="Confirm:",
            bg="#eeeeee"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=4
        )

        self.confirm = tk.Entry(
            fields,
            show="*"
        )

        self.confirm.grid(
            row=2,
            column=1,
            sticky="ew",
            pady=4
        )

        fields.columnconfigure(
            1,
            weight=1
        )

        ClassicButton(
            frame,
            "Register",
            self.do_register
        ).pack(
            pady=12
        )

    def do_register(self):
        username = self.username.get().strip()
        password = self.password.get()
        confirm = self.confirm.get()

        if not username:
            messagebox.showerror(
                "Register",
                "Enter a username.",
                parent=self.window
            )
            return

        if password != confirm:
            messagebox.showerror(
                "Register",
                "Passwords do not match.",
                parent=self.window
            )
            return

        if not password:
            messagebox.showerror(
                "Register",
                "Enter a password.",
                parent=self.window
            )
            return

        if not self.app.net.running:
            if not self.app.connect_network():
                return

        self.app.pending_register = True
        self.app.net.send(
            "REGISTER",
            username,
            password
        )

        self.window.destroy()


# ============================================================
# BUDDY LIST
# ============================================================

class BuddyList:
    def __init__(self, app, parent):
        self.app = app
        self.parent = parent

        self.entries = {}

        self.frame = tk.Frame(
            parent,
            bg="#eeeeee"
        )

        self.listbox = tk.Listbox(
            self.frame,
            font=("MS Sans Serif", 9),
            activestyle="none",
            selectmode=tk.SINGLE,
            bg="white",
            relief=tk.SUNKEN,
            bd=2
        )

        self.listbox.pack(
            fill=tk.BOTH,
            expand=True
        )

        self.listbox.bind(
            "<Double-Button-1>",
            self.double_click
        )

        self.listbox.bind(
            "<Return>",
            self.double_click
        )

    def pack(self, **kwargs):
        self.frame.pack(
            **kwargs
        )

    def update(self, buddies):
        self.entries = buddies

        self.listbox.delete(
            0,
            tk.END
        )

        order = {
            STATUS_ONLINE: 0,
            STATUS_AWAY: 1,
            STATUS_BUSY: 2,
            STATUS_INVISIBLE: 3,
            STATUS_OFFLINE: 4
        }

        sorted_names = sorted(
            buddies.keys(),
            key=lambda name: (
                order.get(
                    buddies[name]["status"],
                    4
                ),
                name.lower()
            )
        )

        for name in sorted_names:
            data = buddies[name]

            status = data["status"]

            icon = {
                STATUS_ONLINE: "●",
                STATUS_AWAY: "◐",
                STATUS_BUSY: "■",
                STATUS_INVISIBLE: "○",
                STATUS_OFFLINE: "○"
            }.get(
                status,
                "○"
            )

            self.listbox.insert(
                tk.END,
                "%s %s" % (
                    icon,
                    name
                )
            )

    def double_click(self, event=None):
        selection = self.listbox.curselection()

        if not selection:
            return

        text = self.listbox.get(
            selection[0]
        )

        name = text[2:].strip()

        if name in self.entries:
            self.app.open_chat(
                name
            )


# ============================================================
# CHAT WINDOW
# ============================================================

class ChatWindow:
    def __init__(self, app, buddy):
        self.app = app
        self.buddy = buddy

        self.window = tk.Toplevel(
            app.root
        )

        self.window.title(
            "SurPriseShock - " + buddy
        )

        self.window.geometry(
            "500x420"
        )

        self.window.minsize(
            380,
            300
        )

        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.close
        )

        self.build()

    def build(self):
        root = self.window

        top = tk.Frame(
            root,
            bg="#316ac5",
            height=35
        )

        top.pack(
            fill=tk.X
        )

        self.title_label = tk.Label(
            top,
            text=self.buddy,
            bg="#316ac5",
            fg="white",
            font=("Arial", 11, "bold")
        )

        self.title_label.pack(
            side=tk.LEFT,
            padx=8,
            pady=7
        )

        self.history = tk.Text(
            root,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=("MS Sans Serif", 9),
            bg="white",
            relief=tk.SUNKEN,
            bd=2
        )

        self.history.pack(
            fill=tk.BOTH,
            expand=True,
            padx=6,
            pady=6
        )

        bottom = tk.Frame(
            root,
            bg="#eeeeee"
        )

        bottom.pack(
            fill=tk.X,
            padx=6,
            pady=(0, 6)
        )

        self.input = tk.Entry(
            bottom,
            font=("MS Sans Serif", 9)
        )

        self.input.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            padx=(0, 5)
        )

        ClassicButton(
            bottom,
            "Send",
            self.send
        ).pack(
            side=tk.RIGHT
        )

        self.input.bind(
            "<Return>",
            lambda e: self.send()
        )

        self.input.focus_set()

        self.update_status()

    def update_status(self):
        data = self.app.buddies.get(
            self.buddy
        )

        if data:
            status = data["status"]

            away = data.get(
                "away",
                ""
            )

            if away:
                text = "%s - %s" % (
                    status,
                    away
                )
            else:
                text = status

            self.title_label.config(
                text="%s (%s)" %
                (
                    self.buddy,
                    text
                )
            )

    def append(self, sender, timestamp, message):
        self.history.config(
            state=tk.NORMAL
        )

        self.history.insert(
            tk.END,
            "[%s] %s: %s\n" %
            (
                timestamp,
                sender,
                message
            )
        )

        self.history.see(
            tk.END
        )

        self.history.config(
            state=tk.DISABLED
        )

    def send(self):
        message = self.input.get()

        if not message.strip():
            return

        if len(message) > MAX_MESSAGE:
            messagebox.showerror(
                "SurPriseShock",
                "Message is too long.",
                parent=self.window
            )
            return

        if self.app.net.send(
            "MSG",
            self.buddy,
            message
        ):
            self.input.delete(
                0,
                tk.END
            )

    def close(self):
        self.app.chat_windows.pop(
            self.buddy.lower(),
            None
        )

        self.window.destroy()


# ============================================================
# MAIN APPLICATION
# ============================================================

class SurPriseShockApp:
    def __init__(
        self,
        root,
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        embedded_server=False
    ):
        self.root = root

        self.host = host
        self.port = port

        self.embedded_server = embedded_server

        self.root.withdraw()

        self.events = queue.Queue()

        self.net = NetworkClient(
            host,
            port,
            self.events
        )

        self.server = None

        self.login_window = None
        self.main_window = None

        self.username = None

        self.pending_username = None
        self.pending_password = None
        self.pending_register = False

        self.buddies = {}
        self.chat_windows = {}

        self.root.after(
            50,
            self.process_events
        )

        self.show_login()

    def start_embedded_server(self):
        self.server = SurPriseShockServer(
            self.host,
            self.port
        )

        try:
            self.server.start()
        except OSError as exc:
            messagebox.showerror(
                APP_NAME,
                "Could not start server:\n%s" %
                exc
            )

    def show_login(self):
        self.root.withdraw()

        if self.login_window:
            try:
                self.login_window.window.destroy()
            except Exception:
                pass

        self.login_window = LoginScreen(
            self
        )

    def connect_network(self):
        if self.net.running:
            return True

        return self.net.connect()

    def connect_and_login(
        self,
        username,
        password
    ):
        self.pending_username = username
        self.pending_password = password
        self.pending_register = False

        if not self.connect_network():
            return

        self.net.send(
            "LOGIN",
            username,
            password
        )

    def process_events(self):
        try:
            while True:
                event, args = self.events.get_nowait()

                self.handle_event(
                    event,
                    *args
                )

        except queue.Empty:
            pass

        self.root.after(
            50,
            self.process_events
        )

    def handle_event(self, event, *args):
        if event == "connected":
            if self.login_window:
                self.login_window.set_status(
                    "Connected"
                )
            return

        if event == "connection_error":
            if self.login_window:
                self.login_window.set_status(
                    "Error: " + str(args[0])
                )

            return

        if event == "disconnected":
            if self.main_window:
                messagebox.showwarning(
                    APP_NAME,
                    "The server connection was lost.",
                    parent=self.main_window
                )

                self.logout_local()

            elif self.login_window:
                self.login_window.set_status(
                    "Disconnected"
                )

            return

        if event == "packet":
            command, fields = args

            self.handle_packet(
                command,
                fields
            )

    def handle_packet(self, command, fields):
        if command == "REGISTER_OK":
            messagebox.showinfo(
                "Registration",
                fields[0] if fields else "Registration successful."
            )
            return

        if command == "REGISTER_FAIL":
            messagebox.showerror(
                "Registration",
                fields[0] if fields else "Registration failed."
            )
            return

        if command == "LOGIN_OK":
            self.username = fields[0]

            self.pending_password = None

            self.show_messenger()

            return

        if command == "LOGIN_FAIL":
            self.pending_password = None

            if self.login_window:
                self.login_window.set_status(
                    "Error"
                )

            messagebox.showerror(
                "Login failed",
                fields[0] if fields else "Login failed.",
                parent=self.login_window.window
            )

            return

        if command == "BUDDY_LIST_BEGIN":
            self.buddies.clear()
            return

        if command == "BUDDY":
            if len(fields) >= 4:
                name, group, status, away = fields[:4]

                self.buddies[name] = {
                    "group": group,
                    "status": status,
                    "away": away
                }

            return

        if command == "BUDDY_LIST_END":
            self.refresh_buddy_list()
            return

        if command == "PRESENCE":
            if len(fields) >= 3:
                name, status, away = fields[:3]

                if name not in self.buddies:
                    self.buddies[name] = {
                        "group": "Buddies",
                        "status": status,
                        "away": away
                    }
                else:
                    self.buddies[name]["status"] = status
                    self.buddies[name]["away"] = away

                self.refresh_buddy_list()

                chat = self.chat_windows.get(
                    name.lower()
                )

                if chat:
                    chat.update_status()

            return

        if command == "BUDDY_ADDED":
            if fields:
                name = fields[0]

                if name not in self.buddies:
                    self.buddies[name] = {
                        "group": "Buddies",
                        "status": STATUS_OFFLINE,
                        "away": ""
                    }

                self.refresh_buddy_list()

            return

        if command == "BUDDY_REMOVED":
            if fields:
                self.buddies.pop(
                    fields[0],
                    None
                )

                self.refresh_buddy_list()

            return

        if command == "MSG_FROM":
            if len(fields) >= 3:
                sender, timestamp, message = fields[:3]

                self.open_chat(
                    sender
                )

                chat = self.chat_windows.get(
                    sender.lower()
                )

                if chat:
                    chat.append(
                        sender,
                        timestamp,
                        message
                    )

                    self.flash_window(
                        chat.window
                    )

            return

        if command == "MSG_SENT":
            if len(fields) >= 3:
                recipient, timestamp, message = fields[:3]

                self.open_chat(
                    recipient
                )

                chat = self.chat_windows.get(
                    recipient.lower()
                )

                if chat:
                    chat.append(
                        self.username,
                        timestamp,
                        message
                    )

            return

        if command == "MSG_FAIL":
            recipient = fields[0] if fields else ""
            reason = fields[1] if len(fields) > 1 else "Message failed."

            messagebox.showerror(
                "Message failed",
                "%s: %s" %
                (
                    recipient,
                    reason
                ),
                parent=self.main_window
            )

            return

        if command == "ERROR":
            messagebox.showerror(
                APP_NAME,
                fields[0] if fields else "Unknown error.",
                parent=self.main_window
            )

            return

    def refresh_buddy_list(self):
        if hasattr(
            self,
            "buddy_list"
        ):
            self.buddy_list.update(
                self.buddies
            )

    def show_messenger(self):
        if self.login_window:
            try:
                self.login_window.window.destroy()
            except Exception:
                pass

            self.login_window = None

        if self.main_window:
            return

        self.main_window = tk.Toplevel(
            self.root
        )

        self.main_window.title(
            "SurPriseShock - %s" %
            self.username
        )

        self.main_window.geometry(
            "390x520"
        )

        self.main_window.minsize(
            300,
            400
        )

        self.main_window.protocol(
            "WM_DELETE_WINDOW",
            self.quit
        )

        self.build_messenger()

    def build_messenger(self):
        root = self.main_window

        top = tk.Frame(
            root,
            bg="#316ac5",
            height=50
        )

        top.pack(
            fill=tk.X
        )

        tk.Label(
            top,
            text="SurPriseShock",
            bg="#316ac5",
            fg="white",
            font=("Arial", 14, "bold")
        ).pack(
            side=tk.LEFT,
            padx=8,
            pady=8
        )

        self.status_button = tk.Menubutton(
            top,
            text="● Online",
            relief=tk.RAISED,
            bd=2,
            bg="#eeeeee",
            font=("MS Sans Serif", 8)
        )

        self.status_button.pack(
            side=tk.RIGHT,
            padx=8
        )

        self.status_menu = tk.Menu(
            self.status_button,
            tearoff=False
        )

        self.status_menu.add_command(
            label="● Online",
            command=lambda: self.change_status(
                STATUS_ONLINE
            )
        )

        self.status_menu.add_command(
            label="◐ Away",
            command=lambda: self.change_status(
                STATUS_AWAY
            )
        )

        self.status_menu.add_command(
            label="■ Busy",
            command=lambda: self.change_status(
                STATUS_BUSY
            )
        )

        self.status_menu.add_command(
            label="○ Invisible",
            command=lambda: self.change_status(
                STATUS_INVISIBLE
            )
        )

        self.status_button.configure(
            menu=self.status_menu
        )

        user_bar = tk.Frame(
            root,
            bg="#dddddd",
            bd=1,
            relief=tk.SUNKEN
        )

        user_bar.pack(
            fill=tk.X
        )

        tk.Label(
            user_bar,
            text=self.username,
            bg="#dddddd",
            font=("MS Sans Serif", 9, "bold")
        ).pack(
            side=tk.LEFT,
            padx=7,
            pady=4
        )

        body = tk.Frame(
            root,
            bg="#eeeeee"
        )

        body.pack(
            fill=tk.BOTH,
            expand=True,
            padx=7,
            pady=7
        )

        tk.Label(
            body,
            text="Buddies",
            bg="#eeeeee",
            font=("Arial", 10, "bold"),
            anchor="w"
        ).pack(
            fill=tk.X
        )

        self.buddy_list = BuddyList(
            self,
            body
        )

        self.buddy_list.pack(
            fill=tk.BOTH,
            expand=True,
            pady=5
        )

        buttons = tk.Frame(
            root,
            bg="#eeeeee"
        )

        buttons.pack(
            fill=tk.X,
            padx=7,
            pady=(0, 7)
        )

        ClassicButton(
            buttons,
            "Add Buddy",
            self.add_buddy
        ).pack(
            side=tk.LEFT,
            padx=2
        )

        ClassicButton(
            buttons,
            "Remove",
            self.remove_buddy
        ).pack(
            side=tk.LEFT,
            padx=2
        )

        ClassicButton(
            buttons,
            "Logout",
            self.logout
        ).pack(
            side=tk.RIGHT,
            padx=2
        )

        self.refresh_buddy_list()

    def change_status(self, status):
        away = ""

        if status == STATUS_AWAY:
            away = tk.simpledialog.askstring(
                "Away message",
                "Enter your away message:",
                parent=self.main_window
            )

            if away is None:
                away = ""

            away = away[:MAX_AWAY]

        self.net.send(
            "STATUS",
            status,
            away
        )

        self.status_button.config(
            text="● " + status
        )

    def selected_buddy(self):
        selection = self.buddy_list.listbox.curselection()

        if not selection:
            return None

        text = self.buddy_list.listbox.get(
            selection[0]
        )

        return text[2:].strip()

    def add_buddy(self):
        name = tk.simpledialog.askstring(
            "Add Buddy",
            "Username:",
            parent=self.main_window
        )

        if not name:
            return

        self.net.send(
            "BUDDY_ADD",
            name.strip()
        )

    def remove_buddy(self):
        name = self.selected_buddy()

        if not name:
            return

        if not messagebox.askyesno(
            "Remove Buddy",
            "Remove %s from your buddy list?" %
            name,
            parent=self.main_window
        ):
            return

        self.net.send(
            "BUDDY_REMOVE",
            name
        )

    def open_chat(self, buddy):
        key = buddy.lower()

        existing = self.chat_windows.get(
            key
        )

        if existing:
            try:
                existing.window.deiconify()
                existing.window.lift()
                existing.window.focus_force()
                return
            except tk.TclError:
                self.chat_windows.pop(
                    key,
                    None
                )

        chat = ChatWindow(
            self,
            buddy
        )

        self.chat_windows[key] = chat

    def flash_window(self, window):
        try:
            window.deiconify()
            window.lift()
            window.focus_force()

            window.bell()

        except tk.TclError:
            pass

    def logout(self):
        if self.net.running:
            self.net.send(
                "LOGOUT"
            )

        self.logout_local()

    def logout_local(self):
        for chat in list(
            self.chat_windows.values()
        ):
            try:
                chat.window.destroy()
            except Exception:
                pass

        self.chat_windows.clear()

        self.buddies.clear()

        if self.main_window:
            try:
                self.main_window.destroy()
            except Exception:
                pass

            self.main_window = None

        self.username = None

        self.net.close()

        self.show_login()

    def quit(self):
        try:
            if self.net.running:
                self.net.send(
                    "LOGOUT"
                )
        except Exception:
            pass

        self.net.close()

        if self.server:
            self.server.stop()

        self.root.destroy()


# ============================================================
# SERVER-ONLY MODE
# ============================================================

def run_server(host, port):
    server = SurPriseShockServer(
        host,
        port
    )

    try:
        server.start()

        print("")
        print("Press Ctrl+C to stop the server.")
        print("")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("")
        print("Shutting down SurPriseShock Server...")

    finally:
        server.stop()


# ============================================================
# CLIENT MODE
# ============================================================

def run_client(host, port):
    root = tk.Tk()

    app = SurPriseShockApp(
        root,
        host,
        port,
        embedded_server=False
    )

    root.mainloop()


# ============================================================
# SERVER + CLIENT MODE
# ============================================================

def run_all(host, port):
    root = tk.Tk()

    app = SurPriseShockApp(
        root,
        host,
        port,
        embedded_server=True
    )

    app.start_embedded_server()

    root.mainloop()


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="SurPriseShock 1.0"
    )

    parser.add_argument(
        "--mode",
        choices=[
            "client",
            "server",
            "all"
        ],
        default="all"
    )

    parser.add_argument(
        "--host",
        default=DEFAULT_HOST
    )

    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT
    )

    args = parser.parse_args()

    if args.port < 1 or args.port > 65535:
        raise SystemExit(
            "Invalid port."
        )

    if args.mode == "server":
        run_server(
            args.host,
            args.port
        )

    elif args.mode == "client":
        run_client(
            args.host,
            args.port
        )

    else:
        run_all(
            args.host,
            args.port
        )


if __name__ == "__main__":
    main()