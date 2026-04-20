#!/usr/bin/env python3
"""
Arknights: Endfield - Mod Fix Script for v1.2
Fixes:
  1. ShaderOverride VS hashes (missing body parts)
  2. PS-T texture slots shifted by +2 (yellow tint)
     - Uses RabbitFX method if no cross-IB detected
     - Uses +2 slot shift if cross-IB detected

Run this script from inside your Mods folder.
"""

import os
import re

# ── Fix 1: Old → New ShaderOverride blocks ──────────────────────────────────

OLD_SHADER_BLOCK = """\
[ShaderOverridevs22]
hash = 617db42150841836
filter_index = 200

[ShaderOverridevs2]
hash = 847947b4a1ad40cf
filter_index = 200

[ShaderOverridevs10]
hash = cada6d476255bdcf
filter_index = 201

[ShaderOverridevs1]
hash = d9d6448a7b62687e
filter_index = 202

[ShaderOverridevs33]
hash = e8d242aae0b3bacf
filter_index = 203

[ShaderOverridevs88]
hash = f0e7d4b491273aae
filter_index = 203"""

NEW_SHADER_BLOCK = """\
[ShaderOverridevs1000]
hash = 241383a9d64b4978
filter_index = 200
allow_duplicate_hash = overrule

[ShaderOverridevs1001]
hash = 6733250da4e23fd6
filter_index = 200
allow_duplicate_hash = overrule

[ShaderOverridevs1002]
hash = 9bac7486f7930a24
filter_index = 201
allow_duplicate_hash = overrule

[ShaderOverridevs1003]
hash = b30cc5ad521e0700
filter_index = 202
allow_duplicate_hash = overrule

[ShaderOverridevs1004]
hash = 4921f64a7c74226d
filter_index = 203
allow_duplicate_hash = overrule

[ShaderOverridevs1005]
hash = 1b835d0e8dbbfb8f
filter_index = 203
allow_duplicate_hash = overrule

[ShaderOverridevs1006]
hash = 06c94dd56f447210
filter_index = 204
allow_duplicate_hash = overrule

[ShaderOverridevs1007]
hash = f47b1f797f5831d0
filter_index = 204
allow_duplicate_hash = overrule"""

# Old hashes that indicate the shader block needs updating
OLD_SHADER_HASHES = {
    "617db42150841836",
    "847947b4a1ad40cf",
    "cada6d476255bdcf",
    "d9d6448a7b62687e",
    "e8d242aae0b3bacf",
    "f0e7d4b491273aae",
}

# New hashes — if present, Fix 1 already applied
NEW_SHADER_HASHES = {
    "241383a9d64b4978",
    "6733250da4e23fd6",
    "9bac7486f7930a24",
    "b30cc5ad521e0700",
    "4921f64a7c74226d",
    "1b835d0e8dbbfb8f",
    "06c94dd56f447210",
    "f47b1f797f5831d0",
}


FIXED_MARKER = "; endfield_mod_fix: v1.2 applied"


def is_already_fixed(content):
    """Check if this file was already processed by this script."""
    return FIXED_MARKER in content


def has_cross_ib(content):
    """Detect cross-IB rendering: looks for CustomShader_ExtractCB1 or cross-IB markers."""
    return bool(re.search(r'CustomShader_ExtractCB1|跨\s*[iI][bB]', content))


def needs_fix1(content):
    """Check if any old ShaderOverride VS hashes are present."""
    for h in OLD_SHADER_HASHES:
        if h in content:
            return True
    return False


def already_fixed1(content):
    """Check if new ShaderOverride VS hashes are already present."""
    for h in NEW_SHADER_HASHES:
        if h in content:
            return True
    return False


def needs_fix2(content):
    """
    Check if there are ps-t slot assignments pointing to mod textures
    (DiffuseMap, LightMap, NormalMap) that haven't been converted yet.
    We detect by resource name content, not slot number, so re-running is safe.
    """
    lines = content.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(';'):
            continue
        if 'CheckTextureOverride' in stripped:
            continue
        m = re.match(r'ps-t(\d+)\s*=\s*(\S+)', stripped)
        if m and int(m.group(1)) >= 2:
            res = m.group(2).lower()
            if any(k in res for k in ('diffusemap', 'lightmap', 'normalmap')):
                return True
    return False


def apply_fix1(content):
    """Replace old ShaderOverride block with new one."""
    # Normalize line endings for matching
    normalized = content.replace('\r\n', '\n')
    if OLD_SHADER_BLOCK in normalized:
        return normalized.replace(OLD_SHADER_BLOCK, NEW_SHADER_BLOCK), True
    # Fallback: try line-by-line section replacement if spacing differs
    # Replace each old section individually
    changed = False
    old_sections = [
        ("[ShaderOverridevs22]", "617db42150841836", "200"),
        ("[ShaderOverridevs2]",  "847947b4a1ad40cf", "200"),
        ("[ShaderOverridevs10]", "cada6d476255bdcf", "201"),
        ("[ShaderOverridevs1]",  "d9d6448a7b62687e", "202"),
        ("[ShaderOverridevs33]", "e8d242aae0b3bacf", "203"),
        ("[ShaderOverridevs88]", "f0e7d4b491273aae", "203"),
    ]
    for section, hash_val, _ in old_sections:
        pattern = re.compile(
            re.escape(section) + r'\s*\nhash\s*=\s*' + re.escape(hash_val) + r'.*?(?=\n\[|\Z)',
            re.DOTALL
        )
        if pattern.search(normalized):
            # Remove old sections; new block will be inserted once
            normalized = pattern.sub('', normalized)
            changed = True
    if changed:
        # Append the new block after the CustomShader_RedirectCB1 block if present
        insert_after = re.search(r'(\[CustomShader_RedirectCB1\].*?ResourceFakeCB1\s*=\s*copy\s*ResourceFakeCB1_UAV)', normalized, re.DOTALL)
        if insert_after:
            pos = insert_after.end()
            normalized = normalized[:pos] + '\n\n' + NEW_SHADER_BLOCK + normalized[pos:]
        else:
            normalized = NEW_SHADER_BLOCK + '\n\n' + normalized
    return normalized, changed


def apply_fix2_shift(content):
    """
    Shift ps-t slots by +2, but ONLY for lines pointing to mod textures
    (resource names containing DiffuseMap, LightMap, NormalMap).
    This prevents re-triggering on subsequent runs.
    """
    lines = content.splitlines()
    result = []
    changed = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(';') or 'CheckTextureOverride' in line:
            result.append(line)
            continue
        m = re.match(r'^(\s*ps-t)(\d+)(\s*=\s*)(\S+.*)$', line)
        if m and int(m.group(2)) >= 2:
            res = m.group(4).lower()
            if any(k in res for k in ('diffusemap', 'lightmap', 'normalmap')):
                new_line = m.group(1) + str(int(m.group(2)) + 2) + m.group(3) + m.group(4)
                result.append(new_line)
                changed = True
                continue
        result.append(line)
    return '\n'.join(result), changed


def apply_fix2_rabbitfx(content):
    """
    Replace ps-t14/15/16/17/18 texture assignments with RabbitFX references.
    Groups consecutive ps-t lines in a section and replaces them.
    """
    lines = content.splitlines()
    result = []
    i = 0
    changed = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Skip comments and CheckTextureOverride
        if stripped.startswith(';') or 'CheckTextureOverride' in line:
            result.append(line)
            i += 1
            continue

        # Collect a run of consecutive ps-t slot assignments (slots >= 2)
        m = re.match(r'^(\s*)ps-t(\d+)\s*=\s*(\S+)', line)
        if m and int(m.group(2)) >= 2:
            indent = m.group(1)
            group = []  # list of (slot, resource_name, original_line)
            j = i
            while j < len(lines):
                lj = lines[j]
                mj = re.match(r'^\s*ps-t(\d+)\s*=\s*(\S+)', lj)
                if mj and int(mj.group(1)) >= 2 and 'CheckTextureOverride' not in lj and not lj.strip().startswith(';'):
                    group.append((int(mj.group(1)), mj.group(2), lj))
                    j += 1
                else:
                    break

            if group:
                # Identify Diffuse, LightMap, NormalMap by resource name keywords
                diffuse = lightmap = normalmap = None
                for slot, res, _ in group:
                    rl = res.lower()
                    if 'diffuse' in rl:
                        diffuse = res
                    elif 'light' in rl or 'lightmap' in rl:
                        lightmap = res
                    elif 'normal' in rl or 'normalmap' in rl:
                        normalmap = res

                # Only convert if we can identify at least diffuse
                if diffuse:
                    result.append(f'{indent}Resource\\RabbitFX\\Diffuse = ref {diffuse}')
                    if lightmap:
                        result.append(f'{indent}Resource\\RabbitFX\\Lightmap = ref {lightmap}')
                    if normalmap:
                        result.append(f'{indent}Resource\\RabbitFX\\Normalmap = ref {normalmap}')
                    result.append(f'{indent}run = CommandList\\RabbitFX\\SetTextures')
                    changed = True
                    i = j
                    continue
                else:
                    # Can't identify textures by name, fall back to +2 shift for this group
                    for _, _, orig in group:
                        mm = re.match(r'^(\s*ps-t)(\d+)(\s*=\s*.+)$', orig)
                        if mm and int(mm.group(2)) >= 2:
                            result.append(mm.group(1) + str(int(mm.group(2)) + 2) + mm.group(3))
                            changed = True
                        else:
                            result.append(orig)
                    i = j
                    continue

        result.append(line)
        i += 1

    return '\n'.join(result), changed


def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        original = f.read()

    content = original.replace('\r\n', '\n')

    # Skip files already processed by this script
    if is_already_fixed(content):
        return []

    fixes_applied = []

    # ── Fix 1 ────────────────────────────────────────────────────────────────
    if needs_fix1(content) and not already_fixed1(content):
        content, changed = apply_fix1(content)
        if changed:
            fixes_applied.append("Fix 1: ShaderOverride VS hashes updated")

    # ── Fix 2 ────────────────────────────────────────────────────────────────
    if needs_fix2(content):
        cross_ib = has_cross_ib(content)
        if cross_ib:
            content, changed = apply_fix2_shift(content)
            if changed:
                fixes_applied.append("Fix 2: PS-T slots shifted +2 (cross-IB detected)")
        else:
            content, changed = apply_fix2_rabbitfx(content)
            if changed:
                fixes_applied.append("Fix 2: PS-T slots replaced with RabbitFX (no cross-IB)")

    if fixes_applied:
        # Append marker so this file is never processed again
        content = content.rstrip() + '\n\n' + FIXED_MARKER + '\n'
        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.write(content)
        return fixes_applied
    return []


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Scanning: {script_dir}\n")

    total_files = 0
    total_fixed = 0

    for root, dirs, files in os.walk(script_dir):
        # Skip hidden folders
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for fname in files:
            if not fname.lower().endswith('.ini'):
                continue
            # Skip this script itself if it ends up alongside ini files
            filepath = os.path.join(root, fname)
            rel = os.path.relpath(filepath, script_dir)
            total_files += 1

            fixes = process_file(filepath)
            if fixes:
                total_fixed += 1
                print(f"[FIXED] {rel}")
                for fix in fixes:
                    print(f"        → {fix}")
            else:
                print(f"[OK]    {rel}")

    print(f"\nDone. Scanned {total_files} file(s), fixed {total_fixed}.")
    print("Press F10 in-game to reload shaders.")
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
