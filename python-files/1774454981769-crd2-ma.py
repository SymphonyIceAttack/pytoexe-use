import asyncio
import json
import os
import sqlite3
import hashlib
import secrets
import base64
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
import threading
import time
import socket
import select
import sys
from pathlib import Path
import webbrowser
import subprocess
import platform
import re


class ChannelType(Enum):
    TEXT = "text"
    VOICE = "voice"
    ANNOUNCEMENT = "announcement"


class MessageType(Enum):
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    SYSTEM = "system"


@dataclass
class User:
    id: str
    username: str
    email: str
    password_hash: str
    avatar: Optional[str] = None
    status: str = "online"
    created_at: str = None
    friends: List[str] = field(default_factory=list)
    servers: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class Server:
    id: str
    name: str
    owner_id: str
    icon: Optional[str] = None
    channels: List[str] = field(default_factory=list)
    members: List[str] = field(default_factory=list)
    roles: Dict[str, List[str]] = field(default_factory=lambda: {"@everyone": ["read_messages", "send_messages"]})
    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class Channel:
    id: str
    name: str
    server_id: str
    channel_type: ChannelType
    topic: Optional[str] = None
    messages: List[str] = field(default_factory=list)
    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class Message:
    id: str
    channel_id: str
    author_id: str
    content: str
    message_type: MessageType = MessageType.TEXT
    attachments: List[str] = field(default_factory=list)
    reactions: Dict[str, List[str]] = field(default_factory=dict)
    reply_to: Optional[str] = None
    edited: bool = False
    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class DirectMessage:
    id: str
    participants: List[str]
    messages: List[str] = field(default_factory=list)
    created_at: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


class NetworkUtils:
    @staticmethod
    def get_local_ip():
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    @staticmethod
    def get_all_ips():
        """Get all network IP addresses"""
        ips = []

        # Get hostname IP
        try:
            hostname = socket.gethostname()
            host_ip = socket.gethostbyname(hostname)
            if host_ip not in ips:
                ips.append(host_ip)
        except:
            pass

        # Get local IP
        local_ip = NetworkUtils.get_local_ip()
        if local_ip not in ips and local_ip != '127.0.0.1':
            ips.append(local_ip)

        # Try to get all network interfaces using system commands
        try:
            if platform.system() == "Windows":
                # Windows: use ipconfig
                output = subprocess.check_output("ipconfig", encoding='cp866', shell=True)
                ip_pattern = r'\d+\.\d+\.\d+\.\d+'
                found_ips = re.findall(ip_pattern, output)
                for ip in found_ips:
                    if ip not in ips and not ip.startswith('169.254') and ip != '127.0.0.1':
                        ips.append(ip)
            else:
                # Linux/Mac: use ifconfig or ip addr
                try:
                    output = subprocess.check_output("ifconfig", encoding='utf-8', shell=True)
                    ip_pattern = r'inet (\d+\.\d+\.\d+\.\d+)'
                    found_ips = re.findall(ip_pattern, output)
                    for ip in found_ips:
                        if ip not in ips and not ip.startswith('127') and ip != '127.0.0.1':
                            ips.append(ip)
                except:
                    try:
                        output = subprocess.check_output("ip addr", encoding='utf-8', shell=True)
                        ip_pattern = r'inet (\d+\.\d+\.\d+\.\d+)'
                        found_ips = re.findall(ip_pattern, output)
                        for ip in found_ips:
                            if ip not in ips and not ip.startswith('127') and ip != '127.0.0.1':
                                ips.append(ip)
                    except:
                        pass
        except:
            pass

        # Add localhost if no other IPs found
        if not ips:
            ips.append('127.0.0.1')

        return list(set(ips))

    @staticmethod
    def get_public_ip():
        """Get public IP address"""
        try:
            import urllib.request
            with urllib.request.urlopen('https://api.ipify.org', timeout=3) as response:
                return response.read().decode('utf-8')
        except:
            try:
                with urllib.request.urlopen('https://icanhazip.com', timeout=3) as response:
                    return response.read().decode('utf-8').strip()
            except:
                try:
                    with urllib.request.urlopen('https://checkip.amazonaws.com', timeout=3) as response:
                        return response.read().decode('utf-8').strip()
                except:
                    return None


class DiscordCloneDB:
    def __init__(self, db_path="discord_clone.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.init_tables()

    def init_tables(self):
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                email TEXT UNIQUE,
                password_hash TEXT,
                avatar TEXT,
                status TEXT,
                created_at TEXT,
                friends TEXT,
                servers TEXT
            );

            CREATE TABLE IF NOT EXISTS servers (
                id TEXT PRIMARY KEY,
                name TEXT,
                owner_id TEXT,
                icon TEXT,
                channels TEXT,
                members TEXT,
                roles TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS channels (
                id TEXT PRIMARY KEY,
                name TEXT,
                server_id TEXT,
                channel_type TEXT,
                topic TEXT,
                messages TEXT,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                channel_id TEXT,
                author_id TEXT,
                content TEXT,
                message_type TEXT,
                attachments TEXT,
                reactions TEXT,
                reply_to TEXT,
                edited INTEGER,
                created_at TEXT
            );

            CREATE TABLE IF NOT EXISTS direct_messages (
                id TEXT PRIMARY KEY,
                participants TEXT,
                messages TEXT,
                created_at TEXT
            );
        """)
        self.conn.commit()

    def save_user(self, user: User):
        self.cursor.execute(
            "INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user.id, user.username, user.email, user.password_hash, user.avatar,
             user.status, user.created_at, json.dumps(user.friends), json.dumps(user.servers))
        )
        self.conn.commit()

    def get_user(self, user_id: str = None, username: str = None, email: str = None) -> Optional[User]:
        if user_id:
            self.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        elif username:
            self.cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        elif email:
            self.cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        else:
            return None

        row = self.cursor.fetchone()
        if row:
            return User(
                id=row[0], username=row[1], email=row[2], password_hash=row[3],
                avatar=row[4], status=row[5], created_at=row[6],
                friends=json.loads(row[7]), servers=json.loads(row[8])
            )
        return None

    def save_server(self, server: Server):
        self.cursor.execute(
            "INSERT OR REPLACE INTO servers VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (server.id, server.name, server.owner_id, server.icon,
             json.dumps(server.channels), json.dumps(server.members),
             json.dumps(server.roles), server.created_at)
        )
        self.conn.commit()

    def get_server(self, server_id: str) -> Optional[Server]:
        self.cursor.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
        row = self.cursor.fetchone()
        if row:
            return Server(
                id=row[0], name=row[1], owner_id=row[2], icon=row[3],
                channels=json.loads(row[4]), members=json.loads(row[5]),
                roles=json.loads(row[6]), created_at=row[7]
            )
        return None

    def save_channel(self, channel: Channel):
        self.cursor.execute(
            "INSERT OR REPLACE INTO channels VALUES (?, ?, ?, ?, ?, ?, ?)",
            (channel.id, channel.name, channel.server_id, channel.channel_type.value,
             channel.topic, json.dumps(channel.messages), channel.created_at)
        )
        self.conn.commit()

    def get_channel(self, channel_id: str) -> Optional[Channel]:
        self.cursor.execute("SELECT * FROM channels WHERE id = ?", (channel_id,))
        row = self.cursor.fetchone()
        if row:
            return Channel(
                id=row[0], name=row[1], server_id=row[2],
                channel_type=ChannelType(row[3]), topic=row[4],
                messages=json.loads(row[5]), created_at=row[6]
            )
        return None

    def save_message(self, message: Message):
        self.cursor.execute(
            "INSERT OR REPLACE INTO messages VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (message.id, message.channel_id, message.author_id, message.content,
             message.message_type.value, json.dumps(message.attachments),
             json.dumps(message.reactions), message.reply_to,
             1 if message.edited else 0, message.created_at)
        )
        self.conn.commit()

    def get_messages(self, channel_id: str, limit: int = 50) -> List[Message]:
        self.cursor.execute(
            "SELECT * FROM messages WHERE channel_id = ? ORDER BY created_at DESC LIMIT ?",
            (channel_id, limit)
        )
        messages = []
        for row in self.cursor.fetchall():
            messages.append(Message(
                id=row[0], channel_id=row[1], author_id=row[2], content=row[3],
                message_type=MessageType(row[4]), attachments=json.loads(row[5]),
                reactions=json.loads(row[6]), reply_to=row[7], edited=bool(row[8]),
                created_at=row[9]
            ))
        return messages[::-1]

    def save_dm(self, dm: DirectMessage):
        self.cursor.execute(
            "INSERT OR REPLACE INTO direct_messages VALUES (?, ?, ?, ?)",
            (dm.id, json.dumps(dm.participants), json.dumps(dm.messages), dm.created_at)
        )
        self.conn.commit()

    def get_dm_between(self, user1: str, user2: str) -> Optional[DirectMessage]:
        self.cursor.execute("SELECT * FROM direct_messages")
        for row in self.cursor.fetchall():
            participants = json.loads(row[1])
            if set(participants) == {user1, user2}:
                return DirectMessage(
                    id=row[0], participants=participants,
                    messages=json.loads(row[2]), created_at=row[3]
                )
        return None


class HTTPHandler:
    @staticmethod
    def generate_html(host, port, web_port, local_ip, public_ip, all_ips):
        ips_html = ""
        for ip in all_ips:
            if ip != '127.0.0.1':
                ips_html += f'<li><a href="http://{ip}:{web_port}" target="_blank">http://{ip}:{web_port}</a></li>'

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Discord Clone - Server Status</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    color: #eee;
                    min-height: 100vh;
                }}
                .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
                h1 {{ text-align: center; margin-bottom: 30px; color: #7289da; font-size: 2.5em; }}
                .status {{ text-align: center; margin-bottom: 20px; padding: 10px; background: #0f0f1a; border-radius: 8px; }}
                .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin-bottom: 20px; }}
                .card {{ 
                    background: rgba(15, 15, 26, 0.9);
                    backdrop-filter: blur(10px);
                    padding: 20px; 
                    border-radius: 15px; 
                    border: 1px solid rgba(114, 137, 218, 0.3);
                    transition: transform 0.3s, box-shadow 0.3s;
                }}
                .card:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                    border-color: #7289da;
                }}
                .card h3 {{ margin-bottom: 15px; color: #7289da; font-size: 1.3em; }}
                .card p {{ margin: 8px 0; line-height: 1.5; }}
                .card a {{ color: #ff79c6; text-decoration: none; }}
                .card a:hover {{ text-decoration: underline; }}
                .commands {{ background: #0f0f1a; padding: 20px; border-radius: 15px; margin-top: 20px; }}
                .commands h3 {{ margin-bottom: 15px; color: #7289da; }}
                .commands ul {{ list-style: none; }}
                .commands li {{ padding: 8px 0; border-bottom: 1px solid #2a2a3a; font-family: monospace; }}
                .commands li strong {{ color: #ff79c6; }}
                .endpoint {{ 
                    background: #00000033; 
                    padding: 10px; 
                    border-radius: 8px; 
                    margin: 10px 0; 
                    font-family: monospace;
                    word-break: break-all;
                }}
                .badge {{ 
                    display: inline-block; 
                    padding: 3px 8px; 
                    border-radius: 4px; 
                    font-size: 12px; 
                    margin-left: 10px;
                    font-weight: bold;
                }}
                .badge.success {{ background: #4caf50; }}
                .badge.info {{ background: #2196f3; }}
                .badge.warning {{ background: #ff9800; }}
                .ip-list {{ margin-top: 10px; }}
                .ip-list li {{ list-style: none; padding: 5px 0; font-family: monospace; }}
                .footer {{ text-align: center; margin-top: 40px; padding: 20px; color: #666; }}
                @keyframes pulse {{
                    0% {{ opacity: 1; }}
                    50% {{ opacity: 0.5; }}
                    100% {{ opacity: 1; }}
                }}
                .online {{ animation: pulse 2s infinite; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎮 Discord Clone Server</h1>
                <div class="status">
                    <span class="badge success online">● ONLINE</span>
                    <span class="badge info">v1.0</span>
                </div>

                <div class="grid">
                    <div class="card">
                        <h3>🌐 Connection URLs</h3>
                        <p><strong>Local Access:</strong><br>
                        <a href="http://localhost:{web_port}" target="_blank">http://localhost:{web_port}</a><br>
                        <a href="http://127.0.0.1:{web_port}" target="_blank">http://127.0.0.1:{web_port}</a></p>

                        <div class="ip-list">
                            <strong>Network Access:</strong>
                            <ul>
                                {ips_html if ips_html else '<li>No network interfaces found</li>'}
                            </ul>
                        </div>

                        {f'<p><strong>Public IP (external):</strong><br><a href="http://{public_ip}:{web_port}" target="_blank">http://{public_ip}:{web_port}</a><br><span class="badge warning">⚠️ Requires port forwarding</span></p>' if public_ip else ''}
                    </div>

                    <div class="card">
                        <h3>📡 Server Configuration</h3>
                        <p><strong>Host:</strong> {host}</p>
                        <p><strong>Socket Port:</strong> {port}</p>
                        <p><strong>Web Port:</strong> {web_port}</p>
                        <p><strong>Local IP:</strong> {local_ip}</p>
                        {f'<p><strong>Public IP:</strong> {public_ip}</p>' if public_ip else '<p><strong>Public IP:</strong> Unable to detect</p>'}
                    </div>

                    <div class="card">
                        <h3>🔌 Connection Methods</h3>
                        <div class="endpoint">
                            <strong>Python Client:</strong><br>
                            host = '{local_ip}'<br>
                            port = {port}
                        </div>
                        <div class="endpoint">
                            <strong>Telnet:</strong><br>
                            telnet {local_ip} {port}
                        </div>
                        <div class="endpoint">
                            <strong>Web Interface:</strong><br>
                            http://{local_ip}:{web_port}
                        </div>
                    </div>
                </div>

                <div class="commands">
                    <h3>📝 Client Commands (via Terminal)</h3>
                    <ul>
                        <li><strong>/create_server &lt;name&gt;</strong> - Create a new server</li>
                        <li><strong>/join_server &lt;id&gt;</strong> - Join existing server by ID</li>
                        <li><strong>/create_channel &lt;server_id&gt; &lt;name&gt;</strong> - Create channel in server</li>
                        <li><strong>/send &lt;channel_id&gt; &lt;message&gt;</strong> - Send message to channel</li>
                        <li><strong>/dm &lt;user_id&gt; &lt;message&gt;</strong> - Send direct message</li>
                        <li><strong>/servers</strong> - List your servers</li>
                        <li><strong>/messages &lt;channel_id&gt;</strong> - Get channel messages</li>
                        <li><strong>/quit</strong> - Disconnect from server</li>
                    </ul>
                </div>

                <div class="footer">
                    <p>🎮 Discord Clone v1.0 | Created with Python & Socket Programming</p>
                    <p>Share the network URL with others on the same network to connect</p>
                    <p>For external access, configure port forwarding on your router</p>
                </div>
            </div>
            <script>
                console.log("Server running on {host}:{port}");
                console.log("Web interface on port {web_port}");
            </script>
        </body>
        </html>
        """

    @staticmethod
    def handle_request(client_socket, host, port, web_port, local_ip, public_ip, all_ips):
        try:
            request = client_socket.recv(1024).decode('utf-8')
            if 'GET' in request:
                response = "HTTP/1.1 200 OK\r\n"
                response += "Content-Type: text/html; charset=utf-8\r\n"
                response += "Connection: close\r\n\r\n"
                response += HTTPHandler.generate_html(host, port, web_port, local_ip, public_ip, all_ips)
                client_socket.send(response.encode('utf-8'))
        except:
            pass
        finally:
            client_socket.close()


class DiscordCloneServer:
    def __init__(self, host='0.0.0.0', port=8888, web_port=8080):
        self.host = host
        self.port = port
        self.web_port = web_port
        self.db = DiscordCloneDB()
        self.clients: Dict[socket.socket, str] = {}
        self.user_sessions: Dict[str, socket.socket] = {}
        self.server_socket = None
        self.web_server_socket = None
        self.running = False
        self.local_ip = NetworkUtils.get_local_ip()
        self.public_ip = NetworkUtils.get_public_ip()
        self.all_ips = NetworkUtils.get_all_ips()

    def start_web_server(self):
        try:
            self.web_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.web_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.web_server_socket.bind(('0.0.0.0', self.web_port))
            self.web_server_socket.listen(5)

            def web_server_loop():
                while self.running:
                    try:
                        client, addr = self.web_server_socket.accept()
                        threading.Thread(target=HTTPHandler.handle_request,
                                         args=(client, self.host, self.port, self.web_port,
                                               self.local_ip, self.public_ip, self.all_ips),
                                         daemon=True).start()
                    except:
                        break

            threading.Thread(target=web_server_loop, daemon=True).start()
        except Exception as e:
            print(f"[WEB] Could not start web server: {e}")

    def print_connection_info(self):
        print("\n" + "=" * 70)
        print("🎮 DISCORD CLONE SERVER STARTED")
        print("=" * 70)
        print(f"\n📡 Socket Server: 0.0.0.0:{self.port}")
        print(f"🌐 Web Interface: http://localhost:{self.web_port}")
        print("\n🔗 CONNECTION LINKS:")
        print("-" * 70)

        for ip in self.all_ips:
            if ip != '127.0.0.1':
                print(f"   📱 Local Network: http://{ip}:{self.web_port}")
                print(f"   🔌 Python Client: host='{ip}', port={self.port}")

        if self.public_ip:
            print(f"\n   🌍 Public IP (external): http://{self.public_ip}:{self.web_port}")
            print("   ⚠️  NOTE: Requires port forwarding on your router!")

        print("\n" + "-" * 70)
        print("\n💡 QUICK CONNECT:")
        print(f"   • Open browser: http://localhost:{self.web_port}")
        print(f"   • Share link with friends on same network")
        print(f"   • Use Python client to connect and chat")
        print("\n" + "=" * 70 + "\n")

        try:
            webbrowser.open(f"http://localhost:{self.web_port}")
        except:
            pass

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        self.running = True

        self.start_web_server()
        self.print_connection_info()

        while self.running:
            try:
                readable, _, _ = select.select([self.server_socket] + list(self.clients.keys()), [], [], 1)
                for sock in readable:
                    if sock == self.server_socket:
                        client, addr = self.server_socket.accept()
                        print(f"[+] Client connected from {addr}")
                        self.clients[client] = None
                        threading.Thread(target=self.handle_client, args=(client,), daemon=True).start()
                    else:
                        self.handle_client_data(sock)
            except Exception as e:
                if self.running:
                    print(f"[-] Error: {e}")

    def handle_client(self, client_socket):
        try:
            while True:
                data = client_socket.recv(4096).decode('utf-8')
                if not data:
                    break

                for line in data.strip().split('\n'):
                    if line.strip():
                        self.process_command(client_socket, json.loads(line))
        except:
            pass
        finally:
            self.remove_client(client_socket)

    def handle_client_data(self, client_socket):
        try:
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                self.remove_client(client_socket)
                return

            for line in data.strip().split('\n'):
                if line.strip():
                    self.process_command(client_socket, json.loads(line))
        except:
            self.remove_client(client_socket)

    def process_command(self, client_socket, cmd):
        cmd_type = cmd.get('type')

        if cmd_type == 'register':
            username = cmd['username']
            email = cmd['email']
            password = cmd['password']

            if self.db.get_user(username=username):
                self.send_response(client_socket, {'type': 'error', 'message': 'Username exists'})
            elif self.db.get_user(email=email):
                self.send_response(client_socket, {'type': 'error', 'message': 'Email exists'})
            else:
                user_id = secrets.token_hex(8)
                user = User(
                    id=user_id,
                    username=username,
                    email=email,
                    password_hash=hashlib.sha256(password.encode()).hexdigest()
                )
                self.db.save_user(user)
                self.send_response(client_socket, {'type': 'registered', 'user_id': user_id})

        elif cmd_type == 'login':
            identifier = cmd['identifier']
            password = cmd['password']
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            user = self.db.get_user(username=identifier) or self.db.get_user(email=identifier)
            if user and user.password_hash == password_hash:
                self.clients[client_socket] = user.id
                self.user_sessions[user.id] = client_socket
                self.send_response(client_socket, {'type': 'logged_in', 'user': asdict(user)})
            else:
                self.send_response(client_socket, {'type': 'error', 'message': 'Invalid credentials'})

        elif cmd_type == 'create_server':
            user_id = self.clients.get(client_socket)
            if not user_id:
                return

            server_id = secrets.token_hex(8)
            server = Server(
                id=server_id,
                name=cmd['name'],
                owner_id=user_id,
                members=[user_id]
            )
            self.db.save_server(server)

            user = self.db.get_user(user_id=user_id)
            user.servers.append(server_id)
            self.db.save_user(user)

            self.send_response(client_socket, {'type': 'server_created', 'server': asdict(server)})

        elif cmd_type == 'join_server':
            user_id = self.clients.get(client_socket)
            if not user_id:
                return

            server = self.db.get_server(cmd['server_id'])
            if server and user_id not in server.members:
                server.members.append(user_id)
                self.db.save_server(server)

                user = self.db.get_user(user_id=user_id)
                user.servers.append(server.id)
                self.db.save_user(user)

                self.send_response(client_socket, {'type': 'joined_server', 'server': asdict(server)})

        elif cmd_type == 'create_channel':
            user_id = self.clients.get(client_socket)
            if not user_id:
                return

            server = self.db.get_server(cmd['server_id'])
            if server and user_id == server.owner_id:
                channel_id = secrets.token_hex(8)
                channel = Channel(
                    id=channel_id,
                    name=cmd['name'],
                    server_id=server.id,
                    channel_type=ChannelType(cmd.get('channel_type', 'text'))
                )
                self.db.save_channel(channel)

                server.channels.append(channel_id)
                self.db.save_server(server)

                self.send_response(client_socket, {'type': 'channel_created', 'channel': asdict(channel)})

        elif cmd_type == 'send_message':
            user_id = self.clients.get(client_socket)
            if not user_id:
                return

            message_id = secrets.token_hex(8)
            message = Message(
                id=message_id,
                channel_id=cmd['channel_id'],
                author_id=user_id,
                content=cmd['content']
            )
            self.db.save_message(message)

            channel = self.db.get_channel(cmd['channel_id'])
            if channel:
                channel.messages.append(message_id)
                self.db.save_channel(channel)

            server = self.db.get_server(channel.server_id)
            for member_id in server.members:
                if member_id in self.user_sessions:
                    self.send_response(self.user_sessions[member_id], {
                        'type': 'new_message',
                        'message': asdict(message)
                    })

        elif cmd_type == 'get_messages':
            user_id = self.clients.get(client_socket)
            if not user_id:
                return

            messages = self.db.get_messages(cmd['channel_id'], cmd.get('limit', 50))
            self.send_response(client_socket, {
                'type': 'messages_list',
                'messages': [asdict(m) for m in messages]
            })

        elif cmd_type == 'send_dm':
            user_id = self.clients.get(client_socket)
            if not user_id:
                return

            target_user = cmd['target_user_id']
            dm = self.db.get_dm_between(user_id, target_user)

            if not dm:
                dm_id = secrets.token_hex(8)
                dm = DirectMessage(id=dm_id, participants=[user_id, target_user])
                self.db.save_dm(dm)

            message_id = secrets.token_hex(8)
            message = Message(
                id=message_id,
                channel_id=dm.id,
                author_id=user_id,
                content=cmd['content']
            )
            self.db.save_message(message)

            dm.messages.append(message_id)
            self.db.save_dm(dm)

            for participant in dm.participants:
                if participant in self.user_sessions:
                    self.send_response(self.user_sessions[participant], {
                        'type': 'new_dm',
                        'message': asdict(message),
                        'dm_id': dm.id
                    })

        elif cmd_type == 'get_servers':
            user_id = self.clients.get(client_socket)
            if not user_id:
                return

            user = self.db.get_user(user_id=user_id)
            servers = []
            for server_id in user.servers:
                server = self.db.get_server(server_id)
                if server:
                    servers.append(asdict(server))

            self.send_response(client_socket, {'type': 'servers_list', 'servers': servers})

    def send_response(self, client_socket, response):
        try:
            client_socket.send((json.dumps(response) + '\n').encode('utf-8'))
        except:
            pass

    def remove_client(self, client_socket):
        user_id = self.clients.get(client_socket)
        if user_id and user_id in self.user_sessions:
            del self.user_sessions[user_id]
        if client_socket in self.clients:
            del self.clients[client_socket]
        try:
            client_socket.close()
        except:
            pass


class DiscordCloneClient:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.socket = None
        self.user_id = None
        self.username = None
        self.running = False
        self.receive_thread = None

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.running = True
        self.receive_thread = threading.Thread(target=self.receive_messages, daemon=True)
        self.receive_thread.start()
        return True

    def receive_messages(self):
        buffer = ""
        while self.running:
            try:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line.strip():
                        self.handle_response(json.loads(line))
            except:
                break

    def handle_response(self, response):
        resp_type = response.get('type')

        if resp_type == 'logged_in':
            self.user_id = response['user']['id']
            self.username = response['user']['username']
            print(f"\n[LOGIN] Welcome {self.username}!")
            print(
                "[HELP] Available commands: /create_server <name>, /join_server <id>, /create_channel <name>, /send <channel> <msg>, /dm <user> <msg>, /servers, /messages <channel>")

        elif resp_type == 'new_message':
            msg = response['message']
            print(f"\n[{msg['channel_id']}] {msg['author_id']}: {msg['content']}")

        elif resp_type == 'new_dm':
            msg = response['message']
            print(f"\n[DM] {msg['author_id']}: {msg['content']}")

        elif resp_type == 'servers_list':
            print("\n[YOUR SERVERS]:")
            for server in response['servers']:
                print(f"  {server['name']} (ID: {server['id']}) - Channels: {len(server['channels'])}")

        elif resp_type == 'messages_list':
            print("\n[MESSAGES]:")
            for msg in response['messages']:
                print(f"  {msg['author_id']}: {msg['content']}")

        elif resp_type == 'error':
            print(f"\n[ERROR] {response['message']}")

        elif resp_type == 'server_created':
            print(f"\n[SUCCESS] Server created: {response['server']['name']} (ID: {response['server']['id']})")

        elif resp_type == 'joined_server':
            print(f"\n[SUCCESS] Joined server: {response['server']['name']}")

        elif resp_type == 'channel_created':
            print(f"\n[SUCCESS] Channel created: {response['channel']['name']}")

        elif resp_type == 'registered':
            print(f"\n[SUCCESS] Registered! User ID: {response['user_id']}")

        print("\n> ", end='', flush=True)

    def send_command(self, cmd):
        try:
            self.socket.send((json.dumps(cmd) + '\n').encode('utf-8'))
        except:
            print("[ERROR] Connection lost")
            self.running = False

    def run(self):
        print("=== Discord Clone Client ===")
        print(f"Connecting to {self.host}:{self.port}...")

        while not self.user_id:
            action = input("Login or Register? (l/r): ").strip().lower()
            if action == 'r':
                username = input("Username: ")
                email = input("Email: ")
                password = input("Password: ")
                self.send_command({
                    'type': 'register',
                    'username': username,
                    'email': email,
                    'password': password
                })
                time.sleep(1)
            elif action == 'l':
                identifier = input("Username or Email: ")
                password = input("Password: ")
                self.send_command({
                    'type': 'login',
                    'identifier': identifier,
                    'password': password
                })
                time.sleep(1)

        while self.running:
            try:
                user_input = input("> ").strip()
                if not user_input:
                    continue

                if user_input.startswith('/'):
                    parts = user_input.split()
                    cmd = parts[0]

                    if cmd == '/create_server' and len(parts) >= 2:
                        self.send_command({
                            'type': 'create_server',
                            'name': ' '.join(parts[1:])
                        })

                    elif cmd == '/join_server' and len(parts) >= 2:
                        self.send_command({
                            'type': 'join_server',
                            'server_id': parts[1]
                        })

                    elif cmd == '/create_channel' and len(parts) >= 3:
                        self.send_command({
                            'type': 'create_channel',
                            'server_id': parts[1],
                            'name': ' '.join(parts[2:])
                        })

                    elif cmd == '/send' and len(parts) >= 3:
                        self.send_command({
                            'type': 'send_message',
                            'channel_id': parts[1],
                            'content': ' '.join(parts[2:])
                        })

                    elif cmd == '/dm' and len(parts) >= 3:
                        self.send_command({
                            'type': 'send_dm',
                            'target_user_id': parts[1],
                            'content': ' '.join(parts[2:])
                        })

                    elif cmd == '/servers':
                        self.send_command({'type': 'get_servers'})

                    elif cmd == '/messages' and len(parts) >= 2:
                        self.send_command({
                            'type': 'get_messages',
                            'channel_id': parts[1],
                            'limit': int(parts[2]) if len(parts) > 2 else 50
                        })

                    elif cmd == '/quit':
                        self.running = False
                        break

                    else:
                        print(
                            "Commands: /create_server <name>, /join_server <id>, /create_channel <server_id> <name>, /send <channel_id> <msg>, /dm <user_id> <msg>, /servers, /messages <channel_id>")
                else:
                    print("Use / commands")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

        self.socket.close()
        print("\nDisconnected")


def main():
    print("\n" + "=" * 60)
    print("🎮 DISCORD CLONE - Python Implementation")
    print("=" * 60)
    print("1. 🖥️  Start Server (Auto-detect IP)")
    print("2. 💻 Start Client")
    print("3. ❌ Exit")
    print("=" * 60)

    choice = input("\nSelect mode (1/2/3): ").strip()

    if choice == '1':
        port = input("Socket port (press Enter for 8888): ").strip()
        if not port:
            port = 8888
        else:
            port = int(port)

        web_port = input("Web port (press Enter for 8080): ").strip()
        if not web_port:
            web_port = 8080
        else:
            web_port = int(web_port)

        server = DiscordCloneServer(host='0.0.0.0', port=port, web_port=web_port)
        try:
            server.start()
        except KeyboardInterrupt:
            print("\n\n[!] Server stopped")
        except Exception as e:
            print(f"\n[!] Error: {e}")

    elif choice == '2':
        print("\n🔍 Detecting available servers...")
        local_ip = NetworkUtils.get_local_ip()
        print(f"   Local IP: {local_ip}")

        host = input(f"\nServer IP (press Enter for {local_ip}): ").strip()
        if not host:
            host = local_ip

        port = input("Server port (press Enter for 8888): ").strip()
        if not port:
            port = 8888
        else:
            port = int(port)

        client = DiscordCloneClient(host=host, port=port)
        try:
            if client.connect():
                print(f"\n✅ Connected to {host}:{port}")
                client.run()
        except ConnectionRefusedError:
            print(f"\n❌ Connection failed! Make sure server is running on {host}:{port}")
        except Exception as e:
            print(f"\n❌ Error: {e}")

    else:
        print("👋 Goodbye!")


if __name__ == "__main__":
    main()