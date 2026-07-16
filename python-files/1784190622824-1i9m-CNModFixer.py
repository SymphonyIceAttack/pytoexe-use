import os
import shutil
import re

# RabbitFX CN Mod Fixer v1.1 - by Caverabbot assisted and supervised by Caverabbit

pattern_200 = re.compile(r"\bvs\s*(==|!=)\s*200\b")
pattern_202 = re.compile(r"\bvs\s*(==|!=)\s*202\b")

def remove_shaderoverride_blocks(lines):
	output = []
	skip = False

	for line in lines:
		stripped = line.strip()

		# Detect start of ShaderOverride block
		if stripped.lower().startswith("[shaderoverride"):
			skip = True
			continue

		# Detect start of next section → stop skipping
		if skip and stripped.startswith("[") and stripped.endswith("]"):
			skip = False

		# Only keep lines when not skipping
		if not skip:
			output.append(line)

	return output


def fix_ini(path):
	filename = os.path.basename(path)

	# Skip backup files
	if filename.lower().startswith("disabled_rabbitfx_cnmodfix_inibackup_"):
		return

	with open(path, 'r', encoding='utf-8', errors='ignore') as f:
		lines = f.readlines()

	original_text = "".join(lines)

	# Remove ShaderOverride blocks
	lines = remove_shaderoverride_blocks(lines)

	# Replace VS filter ID checks with RabbitFX Filter ID checks
	new_lines = []
	for line in lines:
		stripped = line.strip()
		indent = line[:len(line) - len(line.lstrip())]

		if stripped.startswith("if"):

			# Check for 200
			m = pattern_200.search(stripped)
			if m:
				comp = m.group(1)
				if comp == "==":
					new_lines.append(indent + "if vs == $\\RabbitFX\\RabbitFXShadow || vs == $\\RabbitFX\\RabbitFXShadowFace\n")
					continue
				if comp == "!=":
					new_lines.append(indent + "if vs != $\\RabbitFX\\RabbitFXShadow && vs != $\\RabbitFX\\RabbitFXShadowFace\n")
					continue

			# Check for 202
			m = pattern_202.search(stripped)
			if m:
				comp = m.group(1)
				if comp == "==":
					new_lines.append(indent + "if vs == $\\RabbitFX\\RabbitFXMain\n")
					continue
				if comp == "!=":
					new_lines.append(indent + "if vs != $\\RabbitFX\\RabbitFXMain\n")
					continue

		new_lines.append(line)

	text = "".join(new_lines)

	# Only write if something changed
	if text != original_text:
		dirpath, filename = os.path.split(path)
		backup_path = os.path.join(dirpath, "DISABLED_RABBITFX_CNMODFIX_INIBACKUP_" + filename)

		shutil.copy(path, backup_path)

		with open(path, 'w', encoding='utf-8') as f:
			f.write(text)

		print(f"Fixed: " + path + "  (backup created: " + backup_path + ")")


def scan(root):
	for dirpath, dirnames, files in os.walk(root):
		# Skip disabled directories
		dirnames[:] = [
			d for d in dirnames
			if not d.lower().startswith("disabled")
		]

		for file in files:
			if file.lower().endswith('.ini'):
				fix_ini(os.path.join(dirpath, file))


scan(".")
