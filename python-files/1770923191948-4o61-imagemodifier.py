from PIL import Image
import sys
import os

# Prüfen, ob eine Datei übergeben wurde
if len(sys.argv) > 1:
    input_file = sys.argv[1]
else:
    print("Bitte eine Bilddatei auf die EXE ziehen oder den Dateinamen als Argument angeben.")
    input("Drücke Enter zum Beenden...")
    sys.exit()

# Ausgabe-Dateiname
base, ext = os.path.splitext(os.path.basename(input_file))
output_file = base + "_transparent.png"

# Farben, die erhalten bleiben
allowed_colors = [(188, 188, 188), (92, 64, 51)]  # #bcbcbc und #5c4033

# Bild öffnen
img = Image.open(input_file).convert("RGBA")
pixels = img.load()
width, height = img.size

for y in range(height):
    for x in range(width):
        r, g, b, a = pixels[x, y]
        if (r, g, b) not in allowed_colors:
            pixels[x, y] = (0, 0, 0, 0)

img.save(output_file)
print(f"Fertig! Datei gespeichert als {output_file}")
input("Drücke Enter zum Beenden...")