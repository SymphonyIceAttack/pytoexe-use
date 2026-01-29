import re
import sys

# Speicher für Klassen und Funktionen
classes = {}
functions = {}

# Funktion, um eine Zeile MiniLang auszuführen
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
        # Alles andere landet in der letzten Funktion, falls definiert
        if functions:
            last_func = list(functions.keys())[-1]
            functions[last_func]["body"].append(line)
        else:
            print(f"Unknown command: {line}")

# REPL starten (für interaktives Arbeiten)
def start_repl():
    print("MiniLang REPL - type 'exit' to quit")
    while True:
        try:
            line = input(">>> ")
        except EOFError:
            break  # Strg+D beendet die REPL
        if line.lower() in ["exit", "quit"]:
            break
        run_minilang_line(line)

# MiniLang-Datei ausführen
def run_file(filename):
    try:
        with open(filename, "r") as f:
            lines = f.readlines()
        for line in lines:
            run_minilang_line(line)
    except FileNotFoundError:
        print(f"File '{filename}' not found!")

if __name__ == "__main__":
    # Wenn ein Dateiname angegeben wurde -> Datei ausführen
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
        run_file(file_name)

    # REPL danach starten, damit das Terminal offen bleibt
    print("\n--- MiniLang Terminal ---")
    start_repl()

    # Am Ende sicherstellen, dass das Fenster offen bleibt
    input("\nPress Enter to exit...")