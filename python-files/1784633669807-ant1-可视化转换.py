#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tkinter GUI for convert_old_multiblock_project.py."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

"""
Convert old Multiblocked2 multiblock project files to the new split format.

Old format:
  <name>.mb
    placeholders
    layer_axis
    aisle_repetitions
    shape_infos

New format:
  <name>/<name>.mb
    patterns: [{file: "<name>.json"}]
    selected_pattern: 0
  <name>/<name>.json
    placeholders
    layer_axis
    aisle_repetitions
    shape_infos

The script writes uncompressed Minecraft NBT for .mb files, matching
net.minecraft.nbt.NbtIo.write(CompoundTag, File).
"""

from __future__ import annotations

import argparse
import copy
import gzip
import json
import re
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


TAG_END = 0
TAG_BYTE = 1
TAG_SHORT = 2
TAG_INT = 3
TAG_LONG = 4
TAG_FLOAT = 5
TAG_DOUBLE = 6
TAG_BYTE_ARRAY = 7
TAG_STRING = 8
TAG_LIST = 9
TAG_COMPOUND = 10
TAG_INT_ARRAY = 11
TAG_LONG_ARRAY = 12


TAG_NAMES = {
    TAG_END: "end",
    TAG_BYTE: "byte",
    TAG_SHORT: "short",
    TAG_INT: "int",
    TAG_LONG: "long",
    TAG_FLOAT: "float",
    TAG_DOUBLE: "double",
    TAG_BYTE_ARRAY: "byte_array",
    TAG_STRING: "string",
    TAG_LIST: "list",
    TAG_COMPOUND: "compound",
    TAG_INT_ARRAY: "int_array",
    TAG_LONG_ARRAY: "long_array",
}


@dataclass
class Tag:
    type_id: int
    value: Any


@dataclass
class ListPayload:
    element_type: int
    values: list[Tag]


@dataclass
class NbtDocument:
    name: str
    root: Tag
    compressed: bool = False


class NbtError(ValueError):
    pass


class NbtReader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def read(self, length: int) -> bytes:
        end = self.pos + length
        if end > len(self.data):
            raise NbtError("Unexpected end of NBT data")
        chunk = self.data[self.pos:end]
        self.pos = end
        return chunk

    def read_u8(self) -> int:
        return self.read(1)[0]

    def read_i8(self) -> int:
        return struct.unpack(">b", self.read(1))[0]

    def read_i16(self) -> int:
        return struct.unpack(">h", self.read(2))[0]

    def read_u16(self) -> int:
        return struct.unpack(">H", self.read(2))[0]

    def read_i32(self) -> int:
        return struct.unpack(">i", self.read(4))[0]

    def read_i64(self) -> int:
        return struct.unpack(">q", self.read(8))[0]

    def read_f32(self) -> float:
        return struct.unpack(">f", self.read(4))[0]

    def read_f64(self) -> float:
        return struct.unpack(">d", self.read(8))[0]

    def read_utf(self) -> str:
        length = self.read_u16()
        return decode_modified_utf8(self.read(length))

    def read_payload(self, type_id: int) -> Tag:
        if type_id == TAG_BYTE:
            return Tag(type_id, self.read_i8())
        if type_id == TAG_SHORT:
            return Tag(type_id, self.read_i16())
        if type_id == TAG_INT:
            return Tag(type_id, self.read_i32())
        if type_id == TAG_LONG:
            return Tag(type_id, self.read_i64())
        if type_id == TAG_FLOAT:
            return Tag(type_id, self.read_f32())
        if type_id == TAG_DOUBLE:
            return Tag(type_id, self.read_f64())
        if type_id == TAG_BYTE_ARRAY:
            return Tag(type_id, [self.read_i8() for _ in range(self.read_i32())])
        if type_id == TAG_STRING:
            return Tag(type_id, self.read_utf())
        if type_id == TAG_LIST:
            element_type = self.read_u8()
            length = self.read_i32()
            if length < 0:
                raise NbtError(f"Negative list length: {length}")
            return Tag(type_id, ListPayload(element_type, [self.read_payload(element_type) for _ in range(length)]))
        if type_id == TAG_COMPOUND:
            values: dict[str, Tag] = {}
            while True:
                child_type = self.read_u8()
                if child_type == TAG_END:
                    break
                name = self.read_utf()
                values[name] = self.read_payload(child_type)
            return Tag(type_id, values)
        if type_id == TAG_INT_ARRAY:
            return Tag(type_id, [self.read_i32() for _ in range(self.read_i32())])
        if type_id == TAG_LONG_ARRAY:
            return Tag(type_id, [self.read_i64() for _ in range(self.read_i32())])
        raise NbtError(f"Unsupported NBT tag type: {type_id}")


class NbtWriter:
    def __init__(self) -> None:
        self.parts: list[bytes] = []

    def write(self, data: bytes) -> None:
        self.parts.append(data)

    def write_u8(self, value: int) -> None:
        self.write(struct.pack(">B", value & 0xFF))

    def write_i8(self, value: int) -> None:
        self.write(struct.pack(">b", int(value)))

    def write_i16(self, value: int) -> None:
        self.write(struct.pack(">h", int(value)))

    def write_u16(self, value: int) -> None:
        self.write(struct.pack(">H", int(value)))

    def write_i32(self, value: int) -> None:
        self.write(struct.pack(">i", int(value)))

    def write_i64(self, value: int) -> None:
        self.write(struct.pack(">q", int(value)))

    def write_f32(self, value: float) -> None:
        self.write(struct.pack(">f", float(value)))

    def write_f64(self, value: float) -> None:
        self.write(struct.pack(">d", float(value)))

    def write_utf(self, value: str) -> None:
        encoded = encode_modified_utf8(value)
        if len(encoded) > 65535:
            raise NbtError(f"NBT string is too long: {len(encoded)} bytes")
        self.write_u16(len(encoded))
        self.write(encoded)

    def write_payload(self, tag: Tag) -> None:
        type_id = tag.type_id
        value = tag.value
        if type_id == TAG_BYTE:
            self.write_i8(value)
        elif type_id == TAG_SHORT:
            self.write_i16(value)
        elif type_id == TAG_INT:
            self.write_i32(value)
        elif type_id == TAG_LONG:
            self.write_i64(value)
        elif type_id == TAG_FLOAT:
            self.write_f32(value)
        elif type_id == TAG_DOUBLE:
            self.write_f64(value)
        elif type_id == TAG_BYTE_ARRAY:
            self.write_i32(len(value))
            for item in value:
                self.write_i8(item)
        elif type_id == TAG_STRING:
            self.write_utf(value)
        elif type_id == TAG_LIST:
            payload: ListPayload = value
            self.write_u8(payload.element_type)
            self.write_i32(len(payload.values))
            for item in payload.values:
                if item.type_id != payload.element_type:
                    raise NbtError(
                        f"Mixed NBT list element type: expected {payload.element_type}, got {item.type_id}"
                    )
                self.write_payload(item)
        elif type_id == TAG_COMPOUND:
            for key, child in value.items():
                self.write_u8(child.type_id)
                self.write_utf(key)
                self.write_payload(child)
            self.write_u8(TAG_END)
        elif type_id == TAG_INT_ARRAY:
            self.write_i32(len(value))
            for item in value:
                self.write_i32(item)
        elif type_id == TAG_LONG_ARRAY:
            self.write_i32(len(value))
            for item in value:
                self.write_i64(item)
        else:
            raise NbtError(f"Unsupported NBT tag type: {type_id}")

    def bytes(self) -> bytes:
        return b"".join(self.parts)


def decode_modified_utf8(data: bytes) -> str:
    units: list[int] = []
    i = 0
    while i < len(data):
        b1 = data[i]
        if b1 >> 7 == 0:
            units.append(b1)
            i += 1
        elif (b1 & 0xE0) == 0xC0:
            if i + 1 >= len(data):
                raise NbtError("Invalid modified UTF-8 sequence")
            b2 = data[i + 1]
            units.append(((b1 & 0x1F) << 6) | (b2 & 0x3F))
            i += 2
        elif (b1 & 0xF0) == 0xE0:
            if i + 2 >= len(data):
                raise NbtError("Invalid modified UTF-8 sequence")
            b2 = data[i + 1]
            b3 = data[i + 2]
            units.append(((b1 & 0x0F) << 12) | ((b2 & 0x3F) << 6) | (b3 & 0x3F))
            i += 3
        else:
            raise NbtError("Invalid modified UTF-8 leading byte")
    raw = b"".join(struct.pack(">H", unit) for unit in units)
    return raw.decode("utf-16-be", errors="surrogatepass")


def encode_modified_utf8(value: str) -> bytes:
    raw = value.encode("utf-16-be", errors="surrogatepass")
    encoded = bytearray()
    for i in range(0, len(raw), 2):
        unit = struct.unpack(">H", raw[i:i + 2])[0]
        if 0x0001 <= unit <= 0x007F:
            encoded.append(unit)
        elif unit <= 0x07FF:
            encoded.append(0xC0 | ((unit >> 6) & 0x1F))
            encoded.append(0x80 | (unit & 0x3F))
        else:
            encoded.append(0xE0 | ((unit >> 12) & 0x0F))
            encoded.append(0x80 | ((unit >> 6) & 0x3F))
            encoded.append(0x80 | (unit & 0x3F))
    return bytes(encoded)


def read_nbt(path: Path) -> NbtDocument:
    raw = path.read_bytes()
    compressed = len(raw) >= 2 and raw[0] == 0x1F and raw[1] == 0x8B
    data = gzip.decompress(raw) if compressed else raw
    reader = NbtReader(data)
    root_type = reader.read_u8()
    if root_type != TAG_COMPOUND:
        raise NbtError(f"Root tag must be a compound, got {TAG_NAMES.get(root_type, root_type)}")
    name = reader.read_utf()
    root = reader.read_payload(root_type)
    return NbtDocument(name, root, compressed)


def write_nbt(path: Path, document: NbtDocument, *, compressed: bool = False) -> None:
    writer = NbtWriter()
    writer.write_u8(TAG_COMPOUND)
    writer.write_utf(document.name)
    writer.write_payload(document.root)
    data = writer.bytes()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(data) if compressed else data)


def require_compound(tag: Tag, label: str) -> dict[str, Tag]:
    if tag.type_id != TAG_COMPOUND:
        raise NbtError(f"{label} must be a compound tag")
    return tag.value


def require_list(tag: Tag, label: str) -> ListPayload:
    if tag.type_id != TAG_LIST:
        raise NbtError(f"{label} must be a list tag")
    return tag.value


def get_int(compound: dict[str, Tag], key: str, default: int = 0) -> int:
    tag = compound.get(key)
    if tag is None:
        return default
    if tag.type_id not in (TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG):
        raise NbtError(f"{key} must be an integer tag")
    return int(tag.value)


def get_string(compound: dict[str, Tag], key: str, default: str = "") -> str:
    tag = compound.get(key)
    if tag is None:
        return default
    if tag.type_id != TAG_STRING:
        raise NbtError(f"{key} must be a string tag")
    return tag.value


def get_int_array(tag: Tag | None) -> list[int]:
    if tag is None:
        return []
    if tag.type_id == TAG_INT_ARRAY:
        return list(tag.value)
    if tag.type_id == TAG_LIST:
        payload = require_list(tag, "integer list")
        return [int(item.value) if item.type_id in (TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG) else 0 for item in payload.values]
    raise NbtError(f"Expected int array/list, got {TAG_NAMES.get(tag.type_id, tag.type_id)}")


def list_tag(element_type: int, values: Iterable[Tag]) -> Tag:
    return Tag(TAG_LIST, ListPayload(element_type, list(values)))


def compound_tag(values: dict[str, Tag] | None = None) -> Tag:
    return Tag(TAG_COMPOUND, values or {})


def deep_copy_tag(tag: Tag) -> Tag:
    return copy.deepcopy(tag)


def pattern_file_name(manifest: Path, index: int, count: int) -> str:
    base_name = sanitize_file_name(manifest.stem)
    if count <= 1:
        return f"{base_name}.json"
    return f"{base_name}_{index + 1}.json"


def sanitize_file_name(name: str) -> str:
    sanitized = re.sub(r"[^a-z0-9_.-]", "_", name.lower())
    return sanitized or "multiblock"


def default_manifest_path(input_path: Path) -> Path:
    directory = input_path.with_suffix("") if input_path.suffix.lower() == ".mb" else Path(str(input_path))
    return directory / f"{directory.name}.mb"


def resolve_output_manifest(input_path: Path, output: Path | None) -> Path:
    if output is None:
        return default_manifest_path(input_path)
    if output.suffix.lower() == ".mb":
        return output
    return output / f"{output.name}.mb"


def copy_pattern_value(source: dict[str, Tag], target: dict[str, Tag], key: str) -> None:
    if key in source:
        target[key] = deep_copy_tag(source[key])


def copy_top_level_pattern(project: dict[str, Tag]) -> Tag:
    pattern: dict[str, Tag] = {}
    for key in ("placeholders", "layer_axis", "aisle_repetitions", "shape_infos"):
        copy_pattern_value(project, pattern, key)
    return compound_tag(pattern)


def remove_pattern_values(project: dict[str, Tag]) -> None:
    for key in ("placeholders", "layer_axis", "aisle_repetitions", "shape_infos", "pattern_files"):
        project.pop(key, None)


def predicate_reference_key(tag: Tag) -> tuple[str, str] | str:
    if tag.type_id == TAG_COMPOUND:
        compound = require_compound(tag, "predicate reference")
        ref_type = get_string(compound, "type", "builtin")
        key = get_string(compound, "key", "")
        return (ref_type, key)
    if tag.type_id == TAG_STRING:
        return ("builtin", tag.value)
    return json.dumps(tag_to_json(tag), sort_keys=True, separators=(",", ":"))


def predicate_reference_from_holder_predicate(tag: Tag) -> Tag:
    if tag.type_id == TAG_COMPOUND:
        return deep_copy_tag(tag)
    if tag.type_id == TAG_STRING:
        return compound_tag({
            "key": Tag(TAG_STRING, tag.value),
            "type": Tag(TAG_STRING, "builtin"),
        })
    raise NbtError(f"Unsupported old predicate reference tag: {TAG_NAMES.get(tag.type_id, tag.type_id)}")


def collect_holder_predicates(
    holder: dict[str, Tag],
    existing_refs: list[Tag],
) -> list[Tag]:
    predicates = holder.get("predicates")
    if predicates is None:
        return []
    if predicates.type_id == TAG_INT_ARRAY:
        return [deep_copy_tag(existing_refs[index]) for index in predicates.value if 0 <= index < len(existing_refs)]
    if predicates.type_id == TAG_LIST:
        payload = require_list(predicates, "holder predicates")
        if payload.element_type in (TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG):
            return [
                deep_copy_tag(existing_refs[int(item.value)])
                for item in payload.values
                if 0 <= int(item.value) < len(existing_refs)
            ]
        return [predicate_reference_from_holder_predicate(item) for item in payload.values]
    raise NbtError(f"Unsupported holder predicates tag: {TAG_NAMES.get(predicates.type_id, predicates.type_id)}")


def normalize_placeholders(placeholders_tag: Tag) -> Tag:
    placeholders = require_compound(placeholders_tag, "placeholders")
    x_size = get_int(placeholders, "x")
    y_size = get_int(placeholders, "y")
    z_size = get_int(placeholders, "z")
    holders_payload = require_list(placeholders["holders"], "placeholders.holders")

    existing_refs: list[Tag] = []
    if "predicates" in placeholders:
        refs_payload = require_list(placeholders["predicates"], "placeholders.predicates")
        existing_refs = [deep_copy_tag(item) for item in refs_payload.values]

    predicate_refs: list[Tag] = []
    predicate_indexes: dict[tuple[str, str] | str, int] = {}

    def index_predicate(ref: Tag) -> int:
        key = predicate_reference_key(ref)
        if key not in predicate_indexes:
            predicate_indexes[key] = len(predicate_refs)
            predicate_refs.append(deep_copy_tag(ref))
        return predicate_indexes[key]

    new_holders: list[Tag] = []
    for holder_tag in holders_payload.values:
        holder = require_compound(holder_tag, "placeholder holder")
        indexes = [index_predicate(ref) for ref in collect_holder_predicates(holder, existing_refs)]
        new_holder = {
            "predicates": Tag(TAG_INT_ARRAY, indexes),
            "isController": deep_copy_tag(holder.get("isController", Tag(TAG_BYTE, 0))),
            "facing": deep_copy_tag(holder.get("facing", Tag(TAG_INT, 2))),
        }
        new_holders.append(compound_tag(new_holder))

    flat_pattern = flatten_placeholder_pattern(placeholders.get("pattern"), x_size, y_size, z_size)
    nested_pattern = serialize_placeholder_pattern(flat_pattern, x_size, y_size, z_size)

    return compound_tag({
        "holders": list_tag(TAG_COMPOUND, new_holders),
        "predicates": list_tag(TAG_COMPOUND, predicate_refs),
        "x": Tag(TAG_INT, x_size),
        "y": Tag(TAG_INT, y_size),
        "z": Tag(TAG_INT, z_size),
        "pattern": nested_pattern,
    })


def flatten_placeholder_pattern(pattern_tag: Tag | None, x_size: int, y_size: int, z_size: int) -> list[int]:
    expected = x_size * y_size * z_size
    if pattern_tag is None:
        return [-1] * expected
    if pattern_tag.type_id == TAG_INT_ARRAY:
        values = list(pattern_tag.value)
        return (values + [-1] * expected)[:expected]
    if pattern_tag.type_id != TAG_LIST:
        raise NbtError(f"placeholders.pattern must be an int array or list, got {TAG_NAMES.get(pattern_tag.type_id)}")

    values: list[int] = []
    x_payload = require_list(pattern_tag, "placeholders.pattern")
    for x_tag in x_payload.values:
        y_payload = require_list(x_tag, "placeholders.pattern[x]")
        for row_tag in y_payload.values:
            row = get_int_array(row_tag)
            values.extend((row + [-1] * z_size)[:z_size])
    return (values + [-1] * expected)[:expected]


def serialize_placeholder_pattern(flat: list[int], x_size: int, y_size: int, z_size: int) -> Tag:
    pattern: list[Tag] = []
    index = 0
    for _x in range(x_size):
        rows: list[Tag] = []
        for _y in range(y_size):
            row = flat[index:index + z_size]
            index += z_size
            if len(row) < z_size:
                row.extend([-1] * (z_size - len(row)))
            rows.append(Tag(TAG_INT_ARRAY, row))
        pattern.append(list_tag(TAG_INT_ARRAY, rows))
    return list_tag(TAG_LIST, pattern)


def normalize_pattern(pattern_tag: Tag) -> Tag:
    pattern = require_compound(pattern_tag, "pattern")
    result = deep_copy_tag(pattern_tag)
    result_value = require_compound(result, "pattern copy")
    if "placeholders" not in result_value:
        raise NbtError("Pattern does not contain placeholders")
    result_value["placeholders"] = normalize_placeholders(result_value["placeholders"])
    if "layer_axis" not in result_value:
        result_value["layer_axis"] = Tag(TAG_STRING, "Y")
    if "aisle_repetitions" not in result_value:
        placeholders = require_compound(result_value["placeholders"], "placeholders")
        axis = get_string(result_value, "layer_axis", "Y") or "Y"
        aisle_length = {
            "X": get_int(placeholders, "x"),
            "Y": get_int(placeholders, "y"),
            "Z": get_int(placeholders, "z"),
        }.get(axis, get_int(placeholders, "y"))
        result_value["aisle_repetitions"] = Tag(TAG_INT_ARRAY, [1, 1] * aisle_length)
    if "shape_infos" not in result_value:
        result_value["shape_infos"] = list_tag(TAG_COMPOUND, [])
    return result


def convert_document(document: NbtDocument, manifest: Path) -> tuple[NbtDocument, list[tuple[str, Tag]]]:
    root = require_compound(document.root, "root")
    new_root_tag = deep_copy_tag(document.root)
    new_root = require_compound(new_root_tag, "root copy")

    patterns: list[Tag]
    selected_pattern = get_int(new_root, "selected_pattern", 0)
    if "patterns" in root:
        payload = require_list(root["patterns"], "patterns")
        patterns = [deep_copy_tag(item) for item in payload.values]
    elif "placeholders" in root:
        patterns = [copy_top_level_pattern(root)]
        selected_pattern = 0
    else:
        raise NbtError("Input does not look like an old multiblock project: missing top-level placeholders")

    normalized_patterns = [normalize_pattern(pattern) for pattern in patterns]
    refs: list[Tag] = []
    pattern_files: list[tuple[str, Tag]] = []
    for index, pattern in enumerate(normalized_patterns):
        file_name = pattern_file_name(manifest, index, len(normalized_patterns))
        refs.append(compound_tag({"file": Tag(TAG_STRING, file_name)}))
        pattern_files.append((file_name, pattern))

    remove_pattern_values(new_root)
    new_root["patterns"] = list_tag(TAG_COMPOUND, refs)
    new_root["selected_pattern"] = Tag(TAG_INT, max(0, min(selected_pattern, len(pattern_files) - 1)))
    return NbtDocument(document.name, new_root_tag, compressed=False), pattern_files


def tag_to_json(tag: Tag) -> Any:
    if tag.type_id in (TAG_BYTE, TAG_SHORT, TAG_INT, TAG_LONG):
        return int(tag.value)
    if tag.type_id in (TAG_FLOAT, TAG_DOUBLE):
        return float(tag.value)
    if tag.type_id == TAG_STRING:
        return tag.value
    if tag.type_id in (TAG_BYTE_ARRAY, TAG_INT_ARRAY, TAG_LONG_ARRAY):
        return [int(item) for item in tag.value]
    if tag.type_id == TAG_LIST:
        payload: ListPayload = tag.value
        return [tag_to_json(item) for item in payload.values]
    if tag.type_id == TAG_COMPOUND:
        return {key: tag_to_json(value) for key, value in tag.value.items()}
    raise NbtError(f"Cannot convert NBT tag to JSON: {TAG_NAMES.get(tag.type_id, tag.type_id)}")


def compress_pattern_rows(json_value: Any) -> None:
    if not isinstance(json_value, dict):
        return
    placeholders = json_value.get("placeholders")
    if not isinstance(placeholders, dict):
        return
    z_size = int(placeholders.get("z", 0) or 0)
    pattern = placeholders.get("pattern")
    if not isinstance(pattern, list):
        return
    for x_tag in pattern:
        if not isinstance(x_tag, list):
            continue
        for y_index, row in enumerate(x_tag):
            if (
                isinstance(row, list)
                and len(row) == z_size
                and row
                and all(isinstance(value, int) for value in row)
                and all(value == row[0] for value in row)
            ):
                x_tag[y_index] = row[0]


def write_pattern_json(path: Path, pattern: Tag) -> None:
    json_value = tag_to_json(pattern)
    compress_pattern_rows(json_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_can_write(paths: list[Path], force: bool) -> None:
    if force:
        return
    existing = [path for path in paths if path.exists()]
    if existing:
        formatted = "\n  ".join(str(path) for path in existing)
        raise FileExistsError(f"Refusing to overwrite existing file(s). Use --force:\n  {formatted}")


def convert_file(input_path: Path, output: Path | None, *, force: bool) -> tuple[Path, list[Path]]:
    input_path = input_path.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(input_path)
    manifest = resolve_output_manifest(input_path, output.resolve() if output else None)
    document = read_nbt(input_path)
    converted, pattern_files = convert_document(document, manifest)
    json_paths = [manifest.parent / file_name for file_name, _pattern in pattern_files]
    ensure_can_write([manifest, *json_paths], force)
    for file_name, pattern in pattern_files:
        write_pattern_json(manifest.parent / file_name, pattern)
    write_nbt(manifest, converted, compressed=False)
    return manifest, json_paths


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert old flat Multiblocked2 multiblock .mb projects to the new split .mb + JSON format.",
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="Old .mb project file(s) to convert.")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output directory or manifest .mb path. Only valid with one input.",
    )
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite output files if they already exist.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.output and len(args.inputs) != 1:
        print("--output can only be used with one input file", file=sys.stderr)
        return 2
    try:
        for input_path in args.inputs:
            manifest, json_paths = convert_file(input_path, args.output, force=args.force)
            print(f"Converted: {input_path}")
            print(f"  manifest: {manifest}")
            for path in json_paths:
                print(f"  pattern:  {path}")
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


class ConverterApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("MBD2 旧版多方块项目转换器")
        self.geometry("900x620")
        self.minsize(760, 520)

        self.files: list[Path] = []
        self.log_queue: queue.Queue[tuple[str, object | None]] = queue.Queue()
        self.worker: threading.Thread | None = None

        self.force_var = tk.BooleanVar(value=False)
        self.recursive_var = tk.BooleanVar(value=True)
        self.custom_output_var = tk.BooleanVar(value=False)
        self.output_dir_var = tk.StringVar(value="")

        self._build_ui()
        self.after(100, self._drain_log_queue)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=12)
        root.pack(fill=tk.BOTH, expand=True)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)
        root.rowconfigure(4, weight=1)

        toolbar = ttk.Frame(root)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(8, weight=1)

        ttk.Button(toolbar, text="添加文件", command=self.add_files).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(toolbar, text="添加目录", command=self.add_directory).grid(row=0, column=1, padx=(0, 8))
        ttk.Checkbutton(toolbar, text="递归扫描", variable=self.recursive_var).grid(row=0, column=2, padx=(0, 14))
        ttk.Button(toolbar, text="移除选中", command=self.remove_selected).grid(row=0, column=3, padx=(0, 8))
        ttk.Button(toolbar, text="清空", command=self.clear_files).grid(row=0, column=4, padx=(0, 14))
        ttk.Checkbutton(toolbar, text="覆盖已有输出", variable=self.force_var).grid(row=0, column=5, padx=(0, 14))
        self.convert_button = ttk.Button(toolbar, text="开始转换", command=self.start_conversion)
        self.convert_button.grid(row=0, column=6, padx=(0, 8))

        file_frame = ttk.LabelFrame(root, text="待转换 .mb 文件")
        file_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 8))
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(0, weight=1)

        self.file_list = tk.Listbox(file_frame, activestyle="none", selectmode=tk.EXTENDED)
        self.file_list.grid(row=0, column=0, sticky="nsew")
        file_scroll = ttk.Scrollbar(file_frame, orient=tk.VERTICAL, command=self.file_list.yview)
        file_scroll.grid(row=0, column=1, sticky="ns")
        self.file_list.configure(yscrollcommand=file_scroll.set)

        output_frame = ttk.LabelFrame(root, text="输出")
        output_frame.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        output_frame.columnconfigure(1, weight=1)
        ttk.Checkbutton(
            output_frame,
            text="输出到指定目录",
            variable=self.custom_output_var,
            command=self._update_output_state,
        ).grid(row=0, column=0, sticky="w", padx=(8, 8), pady=8)
        self.output_entry = ttk.Entry(output_frame, textvariable=self.output_dir_var, state=tk.DISABLED)
        self.output_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=8)
        self.output_button = ttk.Button(output_frame, text="选择目录", command=self.choose_output_dir, state=tk.DISABLED)
        self.output_button.grid(row=0, column=2, padx=(0, 8), pady=8)

        self.progress = ttk.Progressbar(root, mode="determinate")
        self.progress.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        log_frame = ttk.LabelFrame(root, text="日志")
        log_frame.grid(row=4, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.status_var = tk.StringVar(value="准备就绪")
        ttk.Label(root, textvariable=self.status_var).grid(row=5, column=0, sticky="ew", pady=(8, 0))

    def add_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="选择旧版 .mb 文件",
            filetypes=[("MBD2 project", "*.mb"), ("All files", "*.*")],
        )
        self._add_paths(Path(path) for path in paths)

    def add_directory(self) -> None:
        directory = filedialog.askdirectory(title="选择包含旧版 .mb 文件的目录")
        if not directory:
            return
        root = Path(directory)
        pattern = "**/*.mb" if self.recursive_var.get() else "*.mb"
        self._add_paths(path for path in root.glob(pattern) if path.is_file())

    def remove_selected(self) -> None:
        selected = set(self.file_list.curselection())
        if not selected:
            return
        self.files = [path for index, path in enumerate(self.files) if index not in selected]
        self._refresh_file_list()

    def clear_files(self) -> None:
        self.files.clear()
        self._refresh_file_list()

    def choose_output_dir(self) -> None:
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir_var.set(directory)

    def start_conversion(self) -> None:
        if self.worker and self.worker.is_alive():
            return
        if not self.files:
            messagebox.showwarning("没有文件", "请先添加要转换的 .mb 文件。")
            return
        output_dir = None
        if self.custom_output_var.get():
            if not self.output_dir_var.get().strip():
                messagebox.showwarning("缺少输出目录", "请先选择输出目录，或取消“输出到指定目录”。")
                return
            output_dir = Path(self.output_dir_var.get()).expanduser()

        self._set_busy(True)
        self.progress.configure(value=0, maximum=len(self.files))
        self._append_log("开始转换...\n")
        self.worker = threading.Thread(
            target=self._convert_worker,
            args=(list(self.files), output_dir, self.force_var.get()),
            daemon=True,
        )
        self.worker.start()

    def _convert_worker(self, files: list[Path], output_dir: Path | None, force: bool) -> None:
        ok = 0
        failed = 0
        for index, input_path in enumerate(files, start=1):
            try:
                output = output_dir / input_path.stem if output_dir else None
                manifest, json_paths = convert_file(input_path, output, force=force)
                ok += 1
                self.log_queue.put(("log", f"[OK] {input_path}\n"))
                self.log_queue.put(("log", f"     manifest: {manifest}\n"))
                for path in json_paths:
                    self.log_queue.put(("log", f"     pattern:  {path}\n"))
            except Exception as exc:
                failed += 1
                self.log_queue.put(("log", f"[失败] {input_path}\n     {exc}\n"))
            self.log_queue.put(("progress", index))
        self.log_queue.put(("done", (ok, failed)))

    def _drain_log_queue(self) -> None:
        try:
            while True:
                kind, payload = self.log_queue.get_nowait()
                if kind == "log":
                    self._append_log(str(payload))
                elif kind == "progress":
                    self.progress.configure(value=int(payload))
                    self.status_var.set(f"已处理 {int(payload)} / {len(self.files)}")
                elif kind == "done":
                    ok, failed = payload  # type: ignore[misc]
                    self._set_busy(False)
                    self._append_log(f"完成：成功 {ok}，失败 {failed}\n")
                    self.status_var.set(f"完成：成功 {ok}，失败 {failed}")
                    if failed:
                        messagebox.showwarning("转换完成", f"成功 {ok} 个，失败 {failed} 个。请查看日志。")
                    else:
                        messagebox.showinfo("转换完成", f"成功转换 {ok} 个文件。")
        except queue.Empty:
            pass
        self.after(100, self._drain_log_queue)

    def _add_paths(self, paths: Iterable[Path]) -> None:
        existing = {path.resolve() for path in self.files}
        added = 0
        for path in paths:
            resolved = path.resolve()
            if resolved.suffix.lower() != ".mb" or resolved in existing:
                continue
            self.files.append(resolved)
            existing.add(resolved)
            added += 1
        self._refresh_file_list()
        if added:
            self.status_var.set(f"已添加 {added} 个文件")

    def _refresh_file_list(self) -> None:
        self.file_list.delete(0, tk.END)
        for path in self.files:
            self.file_list.insert(tk.END, str(path))
        self.status_var.set(f"待转换 {len(self.files)} 个文件")

    def _update_output_state(self) -> None:
        state = tk.NORMAL if self.custom_output_var.get() else tk.DISABLED
        self.output_entry.configure(state=state)
        self.output_button.configure(state=state)

    def _set_busy(self, busy: bool) -> None:
        state = tk.DISABLED if busy else tk.NORMAL
        self.convert_button.configure(state=state)
        self.status_var.set("转换中..." if busy else "准备就绪")

    def _append_log(self, text: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)


def main() -> None:
    app = ConverterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
