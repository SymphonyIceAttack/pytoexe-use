import os, sys
import shutil
import numpy as np
from collections import defaultdict

import torch
from torchvision import transforms

from src.config import *
from src.utils import *



# Detectar si estamos en exe PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Referencia ahora apunta al folder agregado en Additional Files
REFERENCIA_DIR = os.path.join(BASE_DIR, "REFERENCIA")



print("📂 Selecciona la carpeta ORIGEN")
ORIGEN_DIR = ask_directory("Selecciona la carpeta ORIGEN (imágenes a procesar)")

print("📂 Selecciona la carpeta DESTINO")
OUTPUT_DIR = ask_directory("Selecciona la carpeta DESTINO (imágenes renombradas)")

# ================= LOAD DINOv2 =================

print("🔄 Loading DINOv2 model...")
model = torch.hub.load("facebookresearch/dinov2", "dinov2_vits14")
model.eval().to(DEVICE)

transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=(0.485, 0.456, 0.406),
        std=(0.229, 0.224, 0.225),
    ),
])

# ================= LOAD REFERENCE PROTOTYPES =================

print("📌 Building reference prototypes...")

format_groups = defaultdict(list)

for f in os.listdir(REFERENCIA_DIR):
    if not f.lower().endswith((".jpg", ".png", ".jpeg", ".webp")):
        continue

    fmt = FORMAT_MAP.get(extraer_sufijo(f))
    if not fmt:
        continue

    emb = encode_image(os.path.join(REFERENCIA_DIR, f), model, transform, DEVICE)
    format_groups[fmt].append(emb)

format_prototypes = {}
for fmt, embs in format_groups.items():
    proto = np.mean(np.vstack(embs), axis=0, keepdims=True)
    proto /= np.linalg.norm(proto, axis=1, keepdims=True)
    format_prototypes[fmt] = proto

# ================= HIGH-LEVEL PROTOTYPES =================

PRODUCT_PROTO = np.mean(
    np.vstack([format_prototypes[f] for f in PRODUCT_FORMATS if f in format_prototypes]),
    axis=0, keepdims=True)
PRODUCT_PROTO /= np.linalg.norm(PRODUCT_PROTO)

LIFESTYLE_PROTO = np.mean(
    np.vstack([format_prototypes[f] for f in LIFESTYLE_FORMATS if f in format_prototypes]),
    axis=0, keepdims=True)
LIFESTYLE_PROTO /= np.linalg.norm(LIFESTYLE_PROTO)

PACKAGING_PROTO = np.mean(
    np.vstack([format_prototypes[f] for f in PACKAGING_FORMATS if f in format_prototypes]),
    axis=0, keepdims=True)
PACKAGING_PROTO /= np.linalg.norm(PACKAGING_PROTO)

# ================= PROCESS ORIGEN =================

print("\n🔍 Processing ORIGEN...\n")

for img in os.listdir(ORIGEN_DIR):
    if not img.lower().endswith((".jpg", ".png", ".jpeg", ".webp")):
        continue

    path = os.path.join(ORIGEN_DIR, img)
    clean_img = limpiar_nombre_archivo(img)
    base = limpiar_base(clean_img)
    ext = os.path.splitext(img)[1]

    emb = encode_image(path, model, transform, DEVICE)

    score_life = cosine(emb, LIFESTYLE_PROTO)
    score_pack = cosine(emb, PACKAGING_PROTO)
    score_prod = cosine(emb, PRODUCT_PROTO)

    scores = {
        "LIFESTYLE": score_life,
        "PACKAGING": score_pack,
        "PRODUCT": score_prod,
    }

    best_category = max(scores, key=scores.get)
    best_score = scores[best_category]

    if best_score < MIN_SCORE_ANY:
        print(f"⚠️ {img} → unclassified {scores}")
        continue

    if best_category == "LIFESTYLE":
        suf = siguiente_en_rango(base, ext, LIFESTYLE_RANGE)
        reason = f"LIFESTYLE (score={best_score:.2f})"

    elif best_category == "PACKAGING":
        suf = siguiente_en_rango(base, ext, PACKAGING_RANGE)
        reason = f"PACKAGING (score={best_score:.2f})"

    else:
        best_fmt, best_fmt_score = None, -1
        for fmt in PRODUCT_FORMATS:
            proto = format_prototypes.get(fmt)
            if proto is None:
                continue
            s = cosine(emb, proto)
            if s > best_fmt_score:
                best_fmt_score, best_fmt = s, fmt

        suf = FORMAT_TO_SUFFIX[best_fmt]
        reason = f"{best_fmt} (score={best_fmt_score:.2f})"

    new_name = f"{base}{suf}{ext}"
    shutil.copy2(path, os.path.join(OUTPUT_DIR, new_name))
    print(f"✅ {img} → {new_name} [{reason}]")

print("\n🎉 DONE")
input("\n⏸️ Press ENTER to exit...")
