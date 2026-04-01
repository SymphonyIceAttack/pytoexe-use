import json

with open("a.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("output.csv", "w", encoding="utf-8") as f:
    f.write("index;level;globalId-owner;number-part;descrizione-part;number-cad;globalId-cad\n")

    for item in data["bom"]:
        index = item.get("index")
        level = item.get("level")
        globalId_owner = item.get("globalId")

        part_attr = item.get("part", {}).get("attributes", {})
        number_part = part_attr.get("number")
        descrizione = part_attr.get("IBA|OMNIA_DESCRIZIONE")

        cad_attr = item.get("cad", {}).get("attributes", {})
        number_cad = cad_attr.get("number")
        globalId_cad = cad_attr.get("globalID")

        riga = f'{index};{level};"{globalId_owner}";"{number_part}";"{descrizione}";"{number_cad}";"{globalId_cad}"\n'
        f.write(riga)

print("File CSV creato: output.csv")
input("Premi INVIO per chiudere...")
