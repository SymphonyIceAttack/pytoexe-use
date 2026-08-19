#!/usr/bin/env python3
"""
Convert DBC file to C header with union definitions for each CAN message.
"""

import re
import argparse
import cantools


def to_c_identifier(name):
    """Convert arbitrary string to valid C identifier."""
    # Replace non-alphanumeric/underscore with '_'
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    # If starts with digit, prepend '_'
    if name and name[0].isdigit():
        name = '_' + name
    return name


def get_message_members(msg):
    """
    Analyze signals of a CAN message and return list of members for the struct.
    Each member: (byte_index, member_name, bit_width, comment)
    """
    dlc = msg.length
    # bits[byte][bit] = signal object or None
    bits = [[None] * 8 for _ in range(dlc)]

    for sig in msg.signals:
        # Determine LSB start bit (global bit index)
        if sig.byte_order == 'little_endian':
            lsb_start = sig.start
        else:  # big_endian (Motorola)
            lsb_start = sig.start - sig.length + 1

        byte_idx = lsb_start // 8
        bit_offset = lsb_start % 8

        # Check for byte crossing
        if bit_offset + sig.length > 8:
            print(f"Warning: Signal '{sig.name}' in message '{msg.name}' "
                  f"crosses byte boundary, skipped.")
            continue

        # Fill bits
        for i in range(sig.length):
            bit_pos = bit_offset + i
            if bits[byte_idx][bit_pos] is not None:
                print(f"Warning: Overlapping bits for signal '{sig.name}' "
                      f"at byte {byte_idx} bit {bit_pos}")
            bits[byte_idx][bit_pos] = sig

    members = []

    for byte_idx in range(dlc):
        byte_bits = bits[byte_idx]
        i = 0
        while i < 8:
            if byte_bits[i] is None:
                # Reserved bits
                start_bit = i
                while i < 8 and byte_bits[i] is None:
                    i += 1
                end_bit = i - 1
                if start_bit == 0 and end_bit == 7:
                    name = f"RESERVE_Byte{byte_idx}_bit0_7"
                else:
                    name = f"RESERVED_Byte{byte_idx}_bit{start_bit}_{end_bit}"
                width = end_bit - start_bit + 1
                members.append((byte_idx, name, width, None))
            else:
                sig = byte_bits[i]
                start_bit = i
                while i < 8 and byte_bits[i] is not None and byte_bits[i] == sig:
                    i += 1
                width = i - start_bit
                # Use signal name as member name
                member_name = to_c_identifier(sig.name)
                comment = sig.comment if sig.comment else None
                members.append((byte_idx, member_name, width, comment))

    return members


def generate_union(msg):
    """Generate C union definition for a single message."""
    name = to_c_identifier(msg.name)
    msg_id_hex = f"{msg.frame_id:X}"  # uppercase hex without prefix
    dlc = msg.length

    members = get_message_members(msg)

    # Build struct definition
    struct_lines = []
    struct_lines.append("    struct")
    struct_lines.append("    {")

    current_byte = None
    for byte_idx, member_name, width, comment in members:
        if current_byte != byte_idx:
            struct_lines.append(f"        /* Byte {byte_idx} */")
            current_byte = byte_idx
        if comment:
            # Replace newlines with spaces for single-line comment
            comment = comment.replace('\n', ' ').strip()
            if comment:
                struct_lines.append(f"        /* {comment} */")
        struct_lines.append(f"        uint8_t {member_name} :{width};")

    struct_lines.append(f"    }} ID_0x{msg_id_hex};")
    struct_code = "\n".join(struct_lines)

    # Build union
    union_lines = []
    union_lines.append(f"typedef union")
    union_lines.append("{")
    union_lines.append(f"    uint8_t Data[{dlc}];")
    union_lines.append(struct_code)
    union_lines.append(f"}} ComManager_Cfg_RxPayload_{name}_t;")

    return "\n".join(union_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Convert DBC file to C header with union definitions."
    )
    parser.add_argument("dbc_file", help="Input DBC file")
    parser.add_argument("-o", "--output", help="Output C header file (default: stdout)")
    args = parser.parse_args()

    db = cantools.database.load_file(args.dbc_file)

    header_lines = []
    header_lines.append("#ifndef _DBC2C_GEN_H_")
    header_lines.append("#define _DBC2C_GEN_H_")
    header_lines.append("")
    header_lines.append("#include <stdint.h>")
    header_lines.append("")

    for msg in db.messages:
        header_lines.append(generate_union(msg))
        header_lines.append("")

    header_lines.append("#endif /* _DBC2C_GEN_H_ */")

    output = "\n".join(header_lines)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Generated {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()