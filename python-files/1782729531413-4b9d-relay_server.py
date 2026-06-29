#!/usr/bin/env python3
import asyncio
import base64
import hashlib
import json
import os
import random
import struct
import time
from dataclasses import dataclass, field


PORT = int(os.environ.get("PORT", "7716"))
MAX_CLIENTS_PER_ROOM = int(os.environ.get("MAX_CLIENTS_PER_ROOM", "3"))
ROOM_TIMEOUT_MS = int(os.environ.get("ROOM_TIMEOUT_MS", str(30 * 60 * 1000)))
HEADER_SIZE = 4
MAX_PLAYERS_PER_ROOM = 4

rooms = {}


@dataclass(eq=False)
class Peer:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    room: "Room | None" = None
    role: str = ""
    id: int = 0
    name: str = ""
    buffer: bytearray = field(default_factory=bytearray)


@dataclass
class Room:
    code: str
    host: Peer | None
    clients: set[Peer] = field(default_factory=set)
    next_peer_id: int = 2
    last_active: float = field(default_factory=lambda: time.time() * 1000)


def ws_accept_key(key: str) -> str:
    guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    digest = hashlib.sha1((key + guid).encode("ascii")).digest()
    return base64.b64encode(digest).decode("ascii")


def encode_frame(opcode: int, payload: bytes = b"") -> bytes:
    length = len(payload)
    first = 0x80 | opcode

    if length < 126:
        header = bytes([first, length])
    elif length <= 0xFFFF:
        header = bytes([first, 126]) + struct.pack(">H", length)
    else:
        header = bytes([first, 127]) + struct.pack(">Q", length)

    return header + payload


def try_parse_frame(peer: Peer):
    buffer = peer.buffer
    if len(buffer) < 2:
        return None

    opcode = buffer[0] & 0x0F
    masked = (buffer[1] & 0x80) != 0
    length = buffer[1] & 0x7F
    offset = 2

    if length == 126:
        if len(buffer) < offset + 2:
            return None
        length = struct.unpack(">H", buffer[offset : offset + 2])[0]
        offset += 2
    elif length == 127:
        if len(buffer) < offset + 8:
            return None
        length = struct.unpack(">Q", buffer[offset : offset + 8])[0]
        if length > (2**53 - 1):
            raise ValueError("frame too large")
        offset += 8

    mask = None
    if masked:
        if len(buffer) < offset + 4:
            return None
        mask = buffer[offset : offset + 4]
        offset += 4

    if len(buffer) < offset + length:
        return None

    payload = bytearray(buffer[offset : offset + length])
    del buffer[: offset + length]

    if masked and mask is not None:
        for i in range(len(payload)):
            payload[i] ^= mask[i % 4]

    return opcode, bytes(payload)


async def send(peer: Peer, opcode: int, payload: bytes = b""):
    if peer.writer.is_closing():
        return
    peer.writer.write(encode_frame(opcode, payload))
    try:
        await peer.writer.drain()
    except (ConnectionError, RuntimeError):
        pass


async def send_control(peer: Peer, message: dict):
    payload = json.dumps(message, separators=(",", ":")).encode("utf-8")
    await send(peer, 0x1, payload)


async def send_data(peer: Peer, sender_id: int, payload: bytes):
    packet = struct.pack("<i", sender_id) + payload
    await send(peer, 0x2, packet)


def room_peers(room: Room) -> list[Peer]:
    peers = []
    if room.host:
        peers.append(room.host)
    peers.extend(room.clients)
    return peers


async def route_packet(peer: Peer, payload: bytes):
    if len(payload) <= HEADER_SIZE or peer.room is None:
        return

    peer.room.last_active = time.time() * 1000
    target_id = struct.unpack("<i", payload[:HEADER_SIZE])[0]
    game_payload = payload[HEADER_SIZE:]
    peers = room_peers(peer.room)

    if target_id == 0:
        for receiver in peers:
            if receiver.id != peer.id:
                await send_data(receiver, peer.id, game_payload)
        return

    if target_id < 0:
        excluded_id = abs(target_id)
        for receiver in peers:
            if receiver.id != peer.id and receiver.id != excluded_id:
                await send_data(receiver, peer.id, game_payload)
        return

    for receiver in peers:
        if receiver.id == target_id:
            await send_data(receiver, peer.id, game_payload)
            return


def generate_room_code() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    for _ in range(1000):
        code = "".join(random.choice(alphabet) for _ in range(4))
        if code not in rooms:
            return code
    raise RuntimeError("room code exhausted")


async def handle_control(peer: Peer, payload: bytes):
    try:
        message = json.loads(payload.decode("utf-8"))
    except Exception:
        await send_control(peer, {"type": "error", "message": "Invalid JSON"})
        return

    msg_type = str(message.get("type") or "")
    name = str(message.get("player_name") or "Player")[:24]

    if msg_type == "create_room":
        if peer.room:
            await send_control(peer, {"type": "error", "message": "Already in room"})
            return

        code = generate_room_code()
        room = Room(code=code, host=peer)
        rooms[code] = room
        peer.room = room
        peer.role = "host"
        peer.id = 1
        peer.name = name

        await send_control(peer, {"type": "room_created", "room_code": code, "peer_id": 1})
        print(f"[{code}] created by {name}", flush=True)
        return

    if msg_type == "join_room":
        if peer.room:
            await send_control(peer, {"type": "error", "message": "Already in room"})
            return

        code = str(message.get("room_code") or "").strip().upper()
        room = rooms.get(code)
        if not room or not room.host:
            await send_control(peer, {"type": "error", "message": "Room not found"})
            return

        if len(room.clients) + 1 >= MAX_PLAYERS_PER_ROOM:
            await send_control(peer, {"type": "error", "message": "Room full"})
            return

        peer.room = room
        peer.role = "client"
        peer.id = room.next_peer_id
        room.next_peer_id += 1
        peer.name = name
        room.clients.add(peer)

        peers = [
            {"peer_id": room_peer.id, "name": room_peer.name or ""}
            for room_peer in room_peers(room)
            if room_peer.id != peer.id
        ]
        await send_control(
            peer,
            {
                "type": "room_joined",
                "room_code": code,
                "peer_id": peer.id,
                "peers": peers,
            },
        )

        for room_peer in room_peers(room):
            if room_peer.id != peer.id:
                await send_control(
                    room_peer,
                    {"type": "peer_connected", "peer_id": peer.id, "name": name},
                )

        print(f"[{code}] {name} joined as peer {peer.id}", flush=True)
        return

    if msg_type == "leave_room":
        await remove_peer(peer)
        return

    await send_control(peer, {"type": "error", "message": f"Unknown message: {msg_type}"})


async def remove_peer(peer: Peer):
    room = peer.room
    if not room:
        return

    peer.room = None

    if room.host is peer:
        for client in list(room.clients):
            await send_control(client, {"type": "peer_disconnected", "peer_id": peer.id})
            await send(client, 0x8)
            client.writer.close()
        rooms.pop(room.code, None)
        return

    room.clients.discard(peer)
    if room.host:
        await send_control(room.host, {"type": "peer_disconnected", "peer_id": peer.id})
    for client in list(room.clients):
        await send_control(client, {"type": "peer_disconnected", "peer_id": peer.id})

    if not room.host and len(room.clients) == 0:
        rooms.pop(room.code, None)


def close_with_http(writer: asyncio.StreamWriter, status: int, message: str):
    writer.write(f"HTTP/1.1 {status} {message}\r\nConnection: close\r\n\r\n".encode("ascii"))
    writer.close()


async def read_http_headers(reader: asyncio.StreamReader):
    data = await reader.readuntil(b"\r\n\r\n")
    text = data.decode("iso-8859-1")
    lines = text.split("\r\n")
    request_line = lines[0]
    headers = {}

    for line in lines[1:]:
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()

    return request_line, headers


async def handle_websocket(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, headers: dict):
    key = headers.get("sec-websocket-key")
    if not key:
        close_with_http(writer, 400, "Missing WebSocket key")
        return

    response = "\r\n".join(
        [
            "HTTP/1.1 101 Switching Protocols",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Accept: {ws_accept_key(key)}",
            "\r\n",
        ]
    )
    writer.write(response.encode("ascii"))
    await writer.drain()

    peer = Peer(reader=reader, writer=writer)

    try:
        while not reader.at_eof():
            chunk = await reader.read(65536)
            if not chunk:
                break

            peer.buffer.extend(chunk)
            while True:
                frame = try_parse_frame(peer)
                if not frame:
                    break

                opcode, payload = frame
                if opcode == 0x8:
                    writer.write(encode_frame(0x8, payload))
                    await writer.drain()
                    return

                if opcode == 0x9:
                    await send(peer, 0xA, payload)
                    continue

                if opcode == 0x1:
                    await handle_control(peer, payload)
                elif opcode == 0x2 or opcode == 0x0:
                    await route_packet(peer, payload)
    except Exception:
        writer.close()
    finally:
        await remove_peer(peer)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass


async def handle_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    try:
        _, headers = await read_http_headers(reader)
    except Exception:
        writer.close()
        return

    if headers.get("upgrade", "").lower() == "websocket":
        await handle_websocket(reader, writer, headers)
        return

    body = b"Enter The Nyangeon relay is running.\n"
    writer.write(
        b"HTTP/1.1 200 OK\r\n"
        b"content-type: text/plain\r\n"
        + f"content-length: {len(body)}\r\n".encode("ascii")
        + b"\r\n"
        + body
    )
    await writer.drain()
    writer.close()


async def cleanup_rooms():
    while True:
        await asyncio.sleep(30)
        now = time.time() * 1000
        for room in list(rooms.values()):
            if now - room.last_active <= ROOM_TIMEOUT_MS:
                continue
            if room.host:
                room.host.writer.close()
            for client in list(room.clients):
                client.writer.close()
            rooms.pop(room.code, None)


async def main():
    asyncio.create_task(cleanup_rooms())
    server = await asyncio.start_server(handle_connection, "0.0.0.0", PORT)
    print(f"Relay server listening on ws://0.0.0.0:{PORT}", flush=True)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
