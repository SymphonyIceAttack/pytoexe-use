import re
import sys

classes = {}
functions = {}

def run_minilang_lines(lines):
    current_class = None
    current_function = None

    for line in lines:
        line = line.strip()
        if line.startswith("@{downlowd p#}"):
            print("Standard library loaded")
        elif line.startswith("@{downlowd p}"):
            print("All functions loaded")
        elif line.startswith("$.("):
            match = re.match(r'\$\.\("(.*)"\)', line)
            if match:
                print(match.group(1))
        elif line.startswith('class"'):
            match = re.match(r'class"(.*)"', line)
            if match:
                class_name = match.group(1)
                classes[class_name] = {}
                current_class = class_name
                print(f"Class {class_name} defined")
        elif line.startswith('function@/'):
            match = re.match(r'function@/\{class="(.*)"\} (.*)', line)
            if match:
                class_name = match.group(1)
                func_name = match.group(2)
                if class_name in classes:
                    functions[func_name] = {"class": class_name, "body": []}
                    current_function = func_name
                    print(f"Function {func_name} defined in class {class_name}")
        elif line.startswith('@@run/code'):
            match = re.match(r'@@run/code (.*)', line)
            if match:
                run_file = match.group(1)
                print(f"Running MiniLang program {run_file}...")
                for fname, fdata in functions.items():
                    print(f"Executing function {fname} from class {fdata['class']}")
                print("Program finished")
        else:
            # Alles andere landet in der letzten Funktion
            if current_function:
                functions[current_function]["body"].append(line)
            else:
                print(f"Unknown command: {line}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: power# <filename.p#>")
        sys.exit(1)

    file_name = sys.argv[1]

    try:
        with open(file_name, "r") as f:
            lines = f.readlines()
        run_minilang_lines(lines)
    except FileNotFoundError:
        print(f"File '{file_name}' not found!")