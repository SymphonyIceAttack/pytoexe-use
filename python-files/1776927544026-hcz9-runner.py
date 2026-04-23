import sys
import datetime
import random
value = 0
score = 0
power = 1
arg = 0
honk_power = ["HONK"]
variables = {}
file_path = sys.argv[1]
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()
    for code in content.splitlines():
        if "ARG: PRINT" in content:
            arg = input("ARG:")
            print(arg)
        elif "ARG: VAR: VALUE" in content:
            arg = input("ARG:")
            value = input("VALUE:")
            variables[arg] = value
        elif "VAR: PRINT" in content:
            try:
                arg = input("VAR:")
                print(variables[arg])
            except:
                print("VAR: NOT FOUND")
        elif "VER: PRINT" in content:
            print("GS-GOOSESCRIPT 1.1.1")
        else:
            print(f"CMD: {content} NOT DEFINED")
