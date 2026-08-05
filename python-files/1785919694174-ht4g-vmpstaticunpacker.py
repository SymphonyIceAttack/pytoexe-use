"""
Static VMProtect PE packer-layer unpacker.

Supported packer metadata layouts:

Legacy layout:

    struct {
        uint32_t properties_rva;
        uint32_t properties_size;       // normally 5
        struct {
            uint32_t source_rva;
            uint32_t destination_rva;   // plaintext
        } blocks[];
    };

VMProtect 3.9.5 layout observed on PE32+:

    struct {
        uint32_t properties_rva;        // properties size is implicitly 5
        struct {
            uint32_t source_rva;
            uint32_t encoded_destination_rva;
        } blocks[];
    };

For 3.9.5, the first effective key is recovered from the RVA of the first
packed PE section. Later keys are rotated left by seven bits:

    destination[i] = encoded_destination[i] ^ key[i]
    key[i + 1]     = ROL32(key[i], 7)

This restores the LZMA-packed sections into a memory-layout PE. It does not
devirtualize VMProtect or remove its runtime.
"""


import argparse
import lzma
import struct
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pefile

IMAGE_SCN_CNT_UNINITIALIZED_DATA = 0x00000080
LZMA_PROPERTIES_SIZE = 5
VMP_LZMA_PROPERTIES = b"\x5d\x00\x00\x00\x01"
VMP_KEY_ROTATION = 7

DEFAULT_MAX_BLOCK_SIZE = 512 * 1024 * 1024
DEFAULT_MAX_IMAGE_SIZE = 1024 * 1024 * 1024
DEFAULT_MAX_DICTIONARY_SIZE = 256 * 1024 * 1024


class UnpackError(RuntimeError):
    pass


@dataclass(frozen=True)
class LzmaProperties:
    lc: int
    lp: int
    pb: int
    dictionary_size: int

    @classmethod
    def parse(cls, raw: bytes) -> LzmaProperties:
        if len(raw) != LZMA_PROPERTIES_SIZE:
            raise UnpackError(
                f"invalid LZMA properties length: {len(raw)}"
            )

        value = raw[0]
        if value >= 9 * 5 * 5:
            raise UnpackError(
                f"invalid LZMA property byte: 0x{value:02x}"
            )

        lc = value % 9
        remainder = value // 9
        lp = remainder % 5
        pb = remainder // 5

        dictionary_size = max(
            int.from_bytes(raw[1:5], "little"), 4096
        )
        if dictionary_size > DEFAULT_MAX_DICTIONARY_SIZE:
            raise UnpackError(
                "LZMA dictionary is too large: "
                f"0x{dictionary_size:x}"
            )

        return cls(lc, lp, pb, dictionary_size)

    def filter(self) -> dict[str, int]:
        return {
            "id": lzma.FILTER_LZMA1,
            "dict_size": self.dictionary_size,
            "lc": self.lc,
            "lp": self.lp,
            "pb": self.pb,
        }


@dataclass(frozen=True)
class PackedBlock:
    source_rva: int
    encoded_destination: int
    destination_rva: int
    compressed_size: int
    decompressed_data: bytes


@dataclass(frozen=True)
class PackerTable:
    file_offset: int
    properties_rva: int
    properties: LzmaProperties
    format_name: str
    destination_key: int | None
    blocks: tuple[PackedBlock, ...]


def rotate_left32(value: int, count: int) -> int:
    count &= 31
    return (
        (value << count) | (value >> ((32 - count) & 31))
    ) & 0xFFFFFFFF


def iter_occurrences(data: bytes, needle: bytes) -> Iterable[int]:
    if not needle:
        return

    offset = 0
    while True:
        offset = data.find(needle, offset)
        if offset < 0:
            break
        yield offset
        offset += 1


def section_name(section: Any) -> str:
    raw_name = bytes(section.Name).split(b"\0", 1)[0]
    return raw_name.decode("ascii", errors="replace")


def is_packed_section(section: Any) -> bool:
    return (
        int(section.VirtualAddress) > 0
        and int(section.Misc_VirtualSize) > 0
        and int(section.SizeOfRawData) == 0
        and int(section.PointerToRawData) == 0
        and not (
            int(section.Characteristics)
            & IMAGE_SCN_CNT_UNINITIALIZED_DATA
        )
    )


class PEImage:
    def __init__(self, data: bytes, pe: Any):
        self.data = data
        self.pe = pe
        self.size_of_image = int(pe.OPTIONAL_HEADER.SizeOfImage)
        self.size_of_headers = int(pe.OPTIONAL_HEADER.SizeOfHeaders)

    def rva_to_file_offset(
        self, rva: int, size: int = 1
    ) -> int | None:
        if rva < 0 or size < 0:
            return None

        if rva < self.size_of_headers:
            if rva + size <= min(self.size_of_headers, len(self.data)):
                return rva
            return None

        for section in self.pe.sections:
            virtual_address = int(section.VirtualAddress)
            virtual_size = int(section.Misc_VirtualSize)
            raw_size = int(section.SizeOfRawData)
            raw_offset = int(section.PointerToRawData)
            mapped_size = max(virtual_size, raw_size)

            if not (
                virtual_address
                <= rva
                < virtual_address + mapped_size
            ):
                continue

            delta = rva - virtual_address
            if (
                raw_offset == 0
                or delta + size > raw_size
                or raw_offset + delta + size > len(self.data)
            ):
                return None
            return raw_offset + delta

        return None

    def file_offset_to_rvas(
        self, file_offset: int, size: int = 1
    ) -> tuple[int, ...]:
        if file_offset < 0 or size < 0:
            return ()

        result: list[int] = []
        if (
            file_offset < self.size_of_headers
            and file_offset + size
            <= min(self.size_of_headers, len(self.data))
        ):
            result.append(file_offset)

        for section in self.pe.sections:
            raw_offset = int(section.PointerToRawData)
            raw_size = int(section.SizeOfRawData)
            if raw_offset == 0 or raw_size == 0:
                continue
            if (
                raw_offset
                <= file_offset
                and file_offset + size <= raw_offset + raw_size
            ):
                result.append(
                    int(section.VirtualAddress)
                    + file_offset
                    - raw_offset
                )

        return tuple(dict.fromkeys(result))

    def read_rva(self, rva: int, size: int) -> bytes:
        file_offset = self.rva_to_file_offset(rva, size)
        if file_offset is None:
            raise UnpackError(
                f"RVA 0x{rva:x} (size 0x{size:x}) is not file-backed"
            )
        return self.data[file_offset : file_offset + size]


def decode_lzma_stream(
    image: PEImage,
    source_rva: int,
    properties: LzmaProperties,
    max_output_size: int,
) -> tuple[bytes, int]:
    source_offset = image.rva_to_file_offset(source_rva)
    if source_offset is None:
        raise UnpackError(
            f"compressed stream RVA 0x{source_rva:x} is not file-backed"
        )
    if max_output_size <= 0:
        raise UnpackError(
            f"compressed stream RVA 0x{source_rva:x} has no output space"
        )

    compressed = image.data[source_offset:]
    if len(compressed) < 6:
        raise UnpackError(
            f"compressed stream RVA 0x{source_rva:x} is truncated"
        )

    decoder = lzma.LZMADecompressor(
        format=lzma.FORMAT_RAW,
        filters=[properties.filter()],
    )
    try:
        output = decoder.decompress(
            compressed, max_length=max_output_size + 1
        )
    except (lzma.LZMAError, ValueError) as exc:
        raise UnpackError(
            f"invalid LZMA stream at RVA 0x{source_rva:x}: {exc}"
        ) from exc

    if len(output) > max_output_size:
        raise UnpackError(
            f"LZMA stream at RVA 0x{source_rva:x} exceeds its "
            f"0x{max_output_size:x}-byte output limit"
        )
    if not decoder.eof:
        raise UnpackError(
            f"LZMA stream at RVA 0x{source_rva:x} has no end marker"
        )

    compressed_size = len(compressed) - len(decoder.unused_data)
    if compressed_size < 6:
        raise UnpackError(
            f"LZMA stream at RVA 0x{source_rva:x} is implausibly short"
        )

    return output, compressed_size


def destination_capacity(image: PEImage, destination_rva: int) -> int:
    next_section_rva = min(
        (
            int(section.VirtualAddress)
            for section in image.pe.sections
            if int(section.VirtualAddress) > destination_rva
        ),
        default=image.size_of_image,
    )
    end = min(next_section_rva, image.size_of_image)
    return end - destination_rva


def parse_table_candidate(
    image: PEImage,
    table_offset: int,
    properties_rva: int,
    first_block_delta: int,
    expected_destinations: Sequence[int],
    encrypted_destinations: bool,
    format_name: str,
    max_block_size: int,
) -> PackerTable | None:
    try:
        properties = LzmaProperties.parse(
            image.read_rva(
                properties_rva, LZMA_PROPERTIES_SIZE
            )
        )
    except UnpackError:
        return None

    block_count = len(expected_destinations)
    blocks_offset = table_offset + first_block_delta
    table_end = blocks_offset + block_count * 8
    if (
        table_offset < 0
        or blocks_offset < 0
        or table_end > len(image.data)
    ):
        return None

    raw_blocks = [
        struct.unpack_from("<II", image.data, blocks_offset + i * 8)
        for i in range(block_count)
    ]
    if not raw_blocks:
        return None

    destination_key: int | None
    if encrypted_destinations:
        destination_key = (
            raw_blocks[0][1] ^ expected_destinations[0]
        )
        # A zero key is the legacy plaintext representation, not a useful
        # rotating-XOR candidate.
        if destination_key == 0:
            return None
    else:
        destination_key = None

    decoded_destinations: list[int] = []
    current_key = destination_key
    for index, (_, stored_destination) in enumerate(raw_blocks):
        if encrypted_destinations:
            assert current_key is not None
            destination = stored_destination ^ current_key
            current_key = rotate_left32(
                current_key, VMP_KEY_ROTATION
            )
        else:
            destination = stored_destination

        if destination != expected_destinations[index]:
            return None
        decoded_destinations.append(destination)

    blocks: list[PackedBlock] = []
    for (
        source_rva,
        stored_destination,
    ), destination in zip(raw_blocks, decoded_destinations):
        available = destination_capacity(image, destination)
        if available <= 0:
            return None

        try:
            output, compressed_size = decode_lzma_stream(
                image,
                source_rva,
                properties,
                min(max_block_size, available),
            )
        except UnpackError:
            return None

        if not output:
            return None

        blocks.append(
            PackedBlock(
                source_rva=source_rva,
                encoded_destination=stored_destination,
                destination_rva=destination,
                compressed_size=compressed_size,
                decompressed_data=output,
            )
        )

    return PackerTable(
        file_offset=table_offset,
        properties_rva=properties_rva,
        properties=properties,
        format_name=format_name,
        destination_key=destination_key,
        blocks=tuple(blocks),
    )


def find_legacy_candidates_by_destinations(
    image: PEImage,
    expected_destinations: Sequence[int],
    max_block_size: int,
) -> list[PackerTable]:
    if not expected_destinations:
        return []

    candidates: list[PackerTable] = []
    first_destination_bytes = struct.pack(
        "<I", expected_destinations[0]
    )

    for destination_offset in iter_occurrences(
        image.data, first_destination_bytes
    ):
        first_block_offset = destination_offset - 4
        table_offset = first_block_offset - 8
        if table_offset < 0:
            continue
        if (
            table_offset + 8 + len(expected_destinations) * 8
            > len(image.data)
        ):
            continue

        matches = True
        for index, destination in enumerate(expected_destinations):
            stored_destination = struct.unpack_from(
                "<I",
                image.data,
                first_block_offset + index * 8 + 4,
            )[0]
            if stored_destination != destination:
                matches = False
                break
        if not matches:
            continue

        properties_rva, properties_size = struct.unpack_from(
            "<II", image.data, table_offset
        )
        if properties_size != LZMA_PROPERTIES_SIZE:
            continue

        candidate = parse_table_candidate(
            image=image,
            table_offset=table_offset,
            properties_rva=properties_rva,
            first_block_delta=8,
            expected_destinations=expected_destinations,
            encrypted_destinations=False,
            format_name="legacy plaintext PACKER_INFO",
            max_block_size=max_block_size,
        )
        if candidate is not None:
            candidates.append(candidate)

    return candidates


def find_packer_table(
    image: PEImage,
    packed_sections: Sequence[Any],
    max_block_size: int,
) -> PackerTable:
    expected_destinations = tuple(
        int(section.VirtualAddress) for section in packed_sections
    )
    if not expected_destinations:
        raise UnpackError(
            "no packed PE sections were identified"
        )

    candidates: list[PackerTable] = []

    for properties_offset in iter_occurrences(
        image.data, VMP_LZMA_PROPERTIES
    ):
        for properties_rva in image.file_offset_to_rvas(
            properties_offset, LZMA_PROPERTIES_SIZE
        ):
            encoded_properties_rva = struct.pack(
                "<I", properties_rva
            )
            for table_offset in iter_occurrences(
                image.data, encoded_properties_rva
            ):
                compact_candidate = parse_table_candidate(
                    image=image,
                    table_offset=table_offset,
                    properties_rva=properties_rva,
                    first_block_delta=4,
                    expected_destinations=expected_destinations,
                    encrypted_destinations=True,
                    format_name=(
                        "VMProtect 3.9.5 compact rotating-XOR "
                        "destinations"
                    ),
                    max_block_size=max_block_size,
                )
                if compact_candidate is not None:
                    candidates.append(compact_candidate)

                if table_offset + 8 > len(image.data):
                    continue
                properties_size = struct.unpack_from(
                    "<I", image.data, table_offset + 4
                )[0]
                if properties_size != LZMA_PROPERTIES_SIZE:
                    continue

                legacy_candidate = parse_table_candidate(
                    image=image,
                    table_offset=table_offset,
                    properties_rva=properties_rva,
                    first_block_delta=8,
                    expected_destinations=expected_destinations,
                    encrypted_destinations=False,
                    format_name="legacy plaintext PACKER_INFO",
                    max_block_size=max_block_size,
                )
                if legacy_candidate is not None:
                    candidates.append(legacy_candidate)

    # Preserve compatibility with legacy files whose properties are not the
    # VMProtect default. The old destination sequence is still a strong
    # locator, and every resulting stream is validated below.
    if not candidates:
        candidates.extend(
            find_legacy_candidates_by_destinations(
                image, expected_destinations, max_block_size
            )
        )

    if not candidates:
        raise UnpackError(
            "no valid VMProtect packer table was found; the file may use "
            "a different metadata/key scheme"
        )
    if len(candidates) > 1:
        descriptions = ", ".join(
            f"0x{candidate.file_offset:x} ({candidate.format_name})"
            for candidate in candidates
        )
        raise UnpackError(
            f"multiple valid packer tables were found: {descriptions}"
        )

    return candidates[0]


def build_unpacked_image(
    image: PEImage,
    packed_sections: Sequence[Any],
    table: PackerTable,
) -> bytes:
    if image.size_of_headers > len(image.data):
        raise UnpackError(
            "SizeOfHeaders exceeds the packed file"
        )
    if image.size_of_headers > image.size_of_image:
        raise UnpackError(
            "SizeOfHeaders exceeds SizeOfImage"
        )

    output = bytearray(image.size_of_image)
    output[: image.size_of_headers] = image.data[
        : image.size_of_headers
    ]

    blocks_by_destination = {
        block.destination_rva: block for block in table.blocks
    }
    packed_section_ids = {id(section) for section in packed_sections}

    for section in image.pe.sections:
        virtual_address = int(section.VirtualAddress)
        virtual_size = int(section.Misc_VirtualSize)
        raw_size = int(section.SizeOfRawData)
        raw_offset = int(section.PointerToRawData)
        name = section_name(section)

        if raw_size > 0:
            if raw_offset == 0:
                raise UnpackError(
                    f"section {name} has raw data but a zero file offset"
                )
            if raw_offset + raw_size > len(image.data):
                raise UnpackError(
                    f"section {name} raw data exceeds the input file"
                )
            if virtual_address + raw_size > image.size_of_image:
                raise UnpackError(
                    f"section {name} raw data exceeds SizeOfImage"
                )

            output[
                virtual_address : virtual_address + raw_size
            ] = image.data[raw_offset : raw_offset + raw_size]

        block = blocks_by_destination.get(virtual_address)
        if block is not None:
            block_end = (
                virtual_address + len(block.decompressed_data)
            )
            if block_end > image.size_of_image:
                raise UnpackError(
                    f"decompressed section {name} exceeds SizeOfImage"
                )
            output[virtual_address:block_end] = (
                block.decompressed_data
            )

        if id(section) in packed_section_ids and block is None:
            raise UnpackError(
                f"packed section {name} has no decompressed block"
            )

        if block is not None:
            restored_raw_size = len(block.decompressed_data)
            restored_raw_offset = virtual_address
        elif raw_size > 0:
            restored_raw_size = raw_size
            restored_raw_offset = virtual_address
        elif (
            int(section.Characteristics)
            & IMAGE_SCN_CNT_UNINITIALIZED_DATA
        ):
            restored_raw_size = 0
            restored_raw_offset = 0
        elif virtual_size > 0:
            # A non-BSS zero-raw section not listed in the packer table is
            # materialized as zero-filled data in the memory-layout file.
            restored_raw_size = virtual_size
            restored_raw_offset = virtual_address
        else:
            restored_raw_size = 0
            restored_raw_offset = 0

        section_header_offset = int(section.get_file_offset())
        if section_header_offset + 40 > len(output):
            raise UnpackError(
                f"section header for {name} exceeds the output image"
            )

        struct.pack_into(
            "<I",
            output,
            section_header_offset + 16,
            restored_raw_size,
        )
        struct.pack_into(
            "<I",
            output,
            section_header_offset + 20,
            restored_raw_offset,
        )

    # The original checksum no longer describes the rebuilt image. A zero
    # checksum is valid for ordinary user-mode executables.
    checksum_offset = int(
        image.pe.OPTIONAL_HEADER.get_field_absolute_offset(
            "CheckSum"
        )
    )
    if checksum_offset + 4 <= len(output):
        struct.pack_into("<I", output, checksum_offset, 0)

    return bytes(output)


def describe_table(
    table: PackerTable, packed_sections: Sequence[Any]
) -> None:
    print(
        f"Packer table: file offset 0x{table.file_offset:x}"
    )
    print(
        f"Format: {table.format_name}; "
        f"properties RVA=0x{table.properties_rva:x}, "
        f"lc={table.properties.lc}, "
        f"lp={table.properties.lp}, "
        f"pb={table.properties.pb}, "
        f"dict=0x{table.properties.dictionary_size:x}"
    )
    if table.destination_key is not None:
        print(
            f"Destination key[0]=0x{table.destination_key:08x}; "
            f"ROL={VMP_KEY_ROTATION}"
        )

    for index, (section, block) in enumerate(
        zip(packed_sections, table.blocks), 1
    ):
        print(
            f"Block {index:02d} {section_name(section)}: "
            f"src=0x{block.source_rva:x}, "
            f"encoded_dst=0x{block.encoded_destination:08x}, "
            f"dst=0x{block.destination_rva:x}, "
            f"compressed=0x{block.compressed_size:x}, "
            f"uncompressed=0x{len(block.decompressed_data):x}"
        )


def unpack_pe(
    packed_pe_data: bytes,
    max_block_size: int = DEFAULT_MAX_BLOCK_SIZE,
    max_image_size: int = DEFAULT_MAX_IMAGE_SIZE,
) -> bytes:
    if not packed_pe_data:
        raise UnpackError("packed PE data is empty")
    if max_block_size <= 0:
        raise UnpackError("max_block_size must be positive")
    if max_image_size <= 0:
        raise UnpackError("max_image_size must be positive")

    try:
        pe = pefile.PE(data=packed_pe_data)
    except pefile.PEFormatError as exc:
        raise UnpackError(f"invalid PE file: {exc}") from exc

    image = PEImage(packed_pe_data, pe)
    if image.size_of_image <= 0:
        raise UnpackError("PE SizeOfImage is zero")
    if image.size_of_image > max_image_size:
        raise UnpackError(
            f"PE SizeOfImage 0x{image.size_of_image:x} exceeds the "
            f"0x{max_image_size:x}-byte limit"
        )

    packed_sections = [
        section for section in pe.sections
        if is_packed_section(section)
    ]
    table = find_packer_table(
        image, packed_sections, max_block_size
    )
    describe_table(table, packed_sections)

    return build_unpacked_image(
        image, packed_sections, table
    )


def parse_int(value: str) -> int:
    try:
        return int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid integer: {value}"
        ) from exc


def make_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Restore legacy or VMProtect 3.9.5 LZMA-packed PE "
            "sections into a memory-layout PE."
        )
    )
    parser.add_argument("packed_file", type=Path)
    parser.add_argument("unpacked_file", type=Path)
    parser.add_argument(
        "--max-block-size",
        type=parse_int,
        default=DEFAULT_MAX_BLOCK_SIZE,
        help="maximum decompressed size per block (default: 0x20000000)",
    )
    parser.add_argument(
        "--max-image-size",
        type=parse_int,
        default=DEFAULT_MAX_IMAGE_SIZE,
        help="maximum PE SizeOfImage (default: 0x40000000)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = make_argument_parser().parse_args(argv)

    try:
        packed_data = args.packed_file.read_bytes()
        print(
            f"Packed file loaded: {args.packed_file}, "
            f"size=0x{len(packed_data):x}"
        )

        unpacked_data = unpack_pe(
            packed_data,
            max_block_size=args.max_block_size,
            max_image_size=args.max_image_size,
        )
        args.unpacked_file.write_bytes(unpacked_data)
        print(
            f"Wrote {args.unpacked_file} "
            f"(0x{len(unpacked_data):x} bytes)"
        )
        return 0
    except (OSError, UnpackError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
