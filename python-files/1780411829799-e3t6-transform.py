from PIL import Image
import os
namelist = os.listdir(os.getcwd())
print(namelist)
try:
    os.makedirs("output")
except:
    None
def check(img):
    if img.mode == "P" or img.mode == "RGBA":
        return 1
    return 0
for name in namelist[::-1]:
    try:
        img = Image.open(name)
        if check(img):
            img = img.convert("LA")
        else:
            img = img.convert("L")
        img.save("output/" + name)
    except:
        continue
    
