import re
import sys
import os

# Speicher für Klassen und Funktionen
classes = {}
functions = {}

# MiniLang-Zeile ausführen
def run_minilang_line(line):
    global classes, functions
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
            print(f"Class {class_name} defined")
    elif line.startswith('function@/'):
        match = re.match(r'function@/\{class="(.*)"\} (.*)', line)
        if match:
            class_name = match.group(1)
            func_name = match.group(2)
            if class_name in classes:
                functions[func_name] = {"class": class_name, "body": []}
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
        # Alles andere landet in letzter Funktion, falls vorhanden
        if functions:
            last_func = list(functions.keys())[-1]
            functions[last_func]["body"].append(line)
        else:
            print(f"Unknown command: {line}")

# MiniLang-Datei ausführen
def run_file(file_path):
    if not os.path.isfile(file_path):
        print(f"File '{file_path}' not found!")
        return
    with open(file_path, "r") as f:
        lines = f.readlines()
    for line in lines:
        run_minilang_line(line)

# REPL starten
def start_repl():
    print("\n--- MiniLang REPL ---")
    print("Type 'exit' or 'quit' to quit")
    while True:
        try:
            line = input(">>> ")
        except EOFError:
            break
        if line.lower() in ["exit", "quit"]:
            break
        run_minilang_line(line)

# Hauptprogramm
if __name__ == "__main__":
    # Wenn eine Datei über Argument übergeben wurde, ausführen
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
        run_file(file_name)

    # REPL danach starten
    start_repl()

    # Terminal offen halten
    input("\nPress Enter to exit...")