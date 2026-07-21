import os
import shutil
import re

# RabbitFX CN Mod Fixer v2.0 - by Caverabbot assisted and supervised by Caverabbit

edited_files = []


#  Remove conflicting Shader Override blocks
def remove_shaderoverride_blocks(lines):
    output = []
    header_re = re.compile(r"\[(shaderoverride[^\]]*)\]", re.IGNORECASE)
    in_block = False
    keep_block = True

    for line in lines:
        stripped = line.strip()
        m = header_re.match(stripped)

        if m:
            in_block = True
            keep_block = True
            continue

        if in_block:
            s = stripped.lower()
            if s.startswith("filter_index"):
                try:
                    _, val = s.split("=", 1)
                    val = val.strip()
                    if not val.startswith("1718."):
                        keep_block = False
                except:
                    pass

            if stripped.startswith("[") and stripped.endswith("]"):
                in_block = False
                if keep_block:
                    output.append(line)
                continue

            if keep_block:
                output.append(line)
            continue

        output.append(line)

    return output

#  Remove conflicting Shader Regex blocks
def remove_shaderregex_blocks(lines):
    output = []
    header_re = re.compile(r"\[(shaderregex([^\]]*))\]", re.IGNORECASE)
    foreign_bases = set()

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        m = header_re.match(stripped)

        if m:
            full_name = m.group(1)
            base_name = full_name.split(".", 1)[0]

            if full_name.lower() == base_name.lower():
                block = [line]
                j = i + 1
                while j < len(lines):
                    s2 = lines[j].strip()
                    if header_re.match(s2):
                        break
                    block.append(lines[j])
                    j += 1

                has_filter = False
                filter_valid = False
                shader_models = []

                for bline in block:
                    s = bline.strip().lower()

                    if s.startswith("shader_model"):
                        try:
                            _, val = s.split("=", 1)
                            tokens = re.split(r"[^\w]+", val.strip())
                            for t in tokens:
                                t = t.lower()
                                if t.startswith(("vs_", "ps_", "gs_", "hs_", "ds_", "cs_")):
                                    shader_models.append(t)
                        except:
                            pass

                    if s.startswith("filter_index"):
                        has_filter = True
                        try:
                            _, val = s.split("=", 1)
                            val = val.strip()
                            if val.startswith("1718."):
                                filter_valid = True
                        except:
                            pass

                is_vertex_only = shader_models and all(m.startswith("vs_") for m in shader_models)

                if has_filter and is_vertex_only and not filter_valid:
                    foreign_bases.add(base_name)

                i = j
                continue

        i += 1

    skip = False

    for line in lines:
        stripped = line.strip()
        m = header_re.match(stripped)

        if m:
            full_name = m.group(1)
            base_name = full_name.split(".", 1)[0]

            if base_name in foreign_bases:
                skip = True
                continue
            else:
                skip = False
                output.append(line)
                continue

        if skip:
            continue

        output.append(line)

    return output

#  Replace CN filters with RabbitFX filters 
def fix_ini(path):
    filename = os.path.basename(path)
    if filename.lower().startswith("disabled"):
        return

    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    original_text = "".join(lines)

    lines = remove_shaderoverride_blocks(lines)
    lines = remove_shaderregex_blocks(lines)

    new_lines = []
    for line in lines:
        stripped = line.strip()
        indent = line[:len(line) - len(line.lstrip())]

        if stripped.lower().startswith("if"):
            if re.search(r"\bvs\s*==\s*200\b", stripped, re.IGNORECASE):
                new_lines.append(indent + "if vs == 1718.2\n")
                continue
            if re.search(r"\bvs\s*==\s*202\b", stripped, re.IGNORECASE):
                new_lines.append(indent + "if vs == 1718.1\n")
                continue

        new_lines.append(line)

    text = "".join(new_lines)

    if text != original_text:
        dirpath, filename = os.path.split(path)
        backup_path = os.path.join(dirpath, "DISABLED_RABBITFX_CNFIX_INIBACKUP_" + filename)
        shutil.copy(path, backup_path)
        edited_files.append(path)

        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)

        print(f"Fixed: " + path + "  (backup created: " + backup_path + ")")


#  DIRECTORY SCAN
def scan(root):
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.lower().startswith("disabled")]
        for file in files:
            if file.lower().endswith('.ini'):
                fix_ini(os.path.join(dirpath, file))

scan(".")

print("\nSummary of edited files:")
if edited_files:
    for f in edited_files:
        print(" - " + f)
else:
    print("No files were modified.")

input("\nPress Enter to exit...")