"""
3D Animation Studio Pipeline — Complete Folder & Demo File Generator
==================================================================
Creates the entire pipeline folder structure with realistic demo files.

Usage:
  python make_pipeline.py
  python make_pipeline.py --project BLAZE
  python make_pipeline.py --project MYSHOW --type episode --output D:/Projects
"""

import os
import sys
import json
import argparse


def w(base, path, content):
    full = os.path.join(base, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)
    return full


def wj(base, path, data):
    return w(base, path, json.dumps(data, indent=2, ensure_ascii=False))


def empty(base, path):
    return w(base, path, "")


def build(code, ptype, out):
    created = []
    log = lambda p: created.append(p)

    if ptype == "movie":
        shot_rel = "SQ010/SQ010_SH020"
        shot_prefix = "SQ010_SH020"
        seq_word = "sequence"
        shot_naming = code + "_{SEQ}_{SHOT}_{dept}_v{###}.{ext}"
    else:
        shot_rel = "EP01/EP01_SH020"
        shot_prefix = "EP01_SH020"
        seq_word = "episode"
        shot_naming = code + "_EP{##}_{SHOT}_{dept}_v{###}.{ext}"

    # ── _pipeline/ ──────────────────────────────────────
    log(wj(out, "_pipeline/pipeline_config.json", {
        "project_code": code,
        "project_type": ptype,
        "fps": 24,
        "resolution": {"width": 1920, "height": 1080},
        "color_space": {
            "working": "ACEScg",
            "output": "sRGB",
            "ocio": "color_management.ocio"
        },
        "render_engine_maya": "Arnold",
        "render_engine_blender": "Cycles",
        "frame_pad": 4,
        "version_pad": 3,
        "paths": {
            "assets": "02_assets",
            "shots": "03_shots",
            "cache": "04_cache",
            "render_farm": "05_render",
            "comp": "06_comp",
            "editorial": "07_editorial",
            "delivery": "08_delivery"
        },
        "naming": {
            "asset": code + "_{TYPE}_{name}_{dept}_v{###}.{ext}",
            "shot": shot_naming,
            "texture": code + "_{TYPE}_{name}_{channel}_{res}.{ext}"
        },
        "maya_version": "2025",
        "blender_version": "4.2"
    }))

    log(w(out, "_pipeline/color_management.ocio",
         "ocio_profile_version: 2.0\n"
         "\n"
         "roles:\n"
         "  default: raw\n"
         "  data: raw\n"
         "  color_picking: sRGB\n"
         "  compositing_log: ACEScg\n"
         "  color_timing: ACEScct\n"
         "  scene_linear: ACEScg\n"
         "  texture_paint: sRGB\n"
         "\n"
         "colorspaces:\n"
         "  - !<ColorSpace>\n"
         "    name: raw\n"
         "    family: raw\n"
         "    bit_depth: 32f\n"
         "    isdata: true\n"
         "  - !<ColorSpace>\n"
         "    name: sRGB\n"
         "    family: sRGB\n"
         "    bit_depth: 8i\n"
         "  - !<ColorSpace>\n"
         "    name: ACEScg\n"
         "    family: ACES\n"
         "    bit_depth: 16f\n"
         "    allocation: lg2\n"
         "  - !<ColorSpace>\n"
         "    name: ACEScct\n"
         "    family: ACES\n"
         "    bit_depth: 16f\n"
         "    allocation: lg2\n"
         "\n"
         "displays:\n"
         "  sRGB:\n"
         "    - !<View> {name: default, colorspace: sRGB}\n"
         "\n"
         "active_displays: sRGB\n"
         "active_views: default"))

    log(w(out, "_pipeline/deadline_config.ini",
         "[DeadlineSettings]\n"
         "Pool=3d_farm\n"
         "Priority=50\n"
         "ChunkSize=10\n"
         "\n"
         "[MayaRender]\n"
         "Executable=render\n"
         "Arguments=-r arnold -s <START> -e <END> -b 1 <FILE>\n"
         "\n"
         "[BlenderRender]\n"
         "Executable=blender\n"
         "Arguments=-b <FILE> -o <OUT> -F OPEN_EXR -s <START> -e <END> -a"))

    # ── 01_prepro/ ─────────────────────────────────────
    log(empty(out, "01_prepro/scripts/.gitkeep"))
    log(w(out, "01_prepro/scripts/README.md",
         "# Scripts\n\n"
         "Locked screenplay and treatment.\n\n"
         "Naming: " + code + "_script_v001.fdx\n\n"
         "Rules:\n"
         "- Only locked version here\n"
         "- WIP stays on writers share\n"
         "- Version on every revision"))

    log(empty(out, "01_prepro/storyboards/.gitkeep"))
    log(w(out, "01_prepro/storyboards/README.md",
         "# Storyboards\n\n"
         "Per-" + seq_word + " storyboard PDFs.\n\n"
         "Naming: " + code + "_SQ010_storyboard_v001.pdf\n\n"
         "Export from Storyboard Pro as PDF."))

    log(empty(out, "01_prepro/concept_art/.gitkeep"))
    log(w(out, "01_prepro/concept_art/README.md",
         "# Concept Art\n\n"
         "Character turnarounds, environment paintings, prop sheets.\n\n"
         "Naming: " + code + "_CHAR_hero_turnaround_v001.psd\n\n"
         "Source: PSD layered. Flatten to PNG for 3D reference."))

    log(empty(out, "01_prepro/color_scripts/.gitkeep"))
    log(w(out, "01_prepro/color_scripts/README.md",
         "# Color Scripts\n\n"
         "Per-" + seq_word + " lighting palettes for lighting TDs.\n\n"
         "Naming: " + code + "_SQ010_colorscript_v001.psd"))

    log(empty(out, "01_prepro/animatic/.gitkeep"))
    log(w(out, "01_prepro/animatic/README.md",
         "# Animatic\n\n"
         "Timed storyboard cuts with temp audio.\n\n"
         "Naming: " + code + "_animatic_v001.mov\n"
         "Format: ProRes 422 internal, H.264 remote\n"
         "FPS: 24 (must match project)"))

    # ── 02_assets/characters/CHAR_hero/ ────────────────
    ch = "02_assets/characters/CHAR_hero"

    log(w(out, ch + "/model/" + code + "_CHAR_hero_model_v001.ma",
         "// Maya ASCII\n"
         "// " + code + "_CHAR_hero_model_v001.ma\n"
         "// Dept: model | v001\n"
         "\n"
         "requires maya \"2025\";\n"
         "currentUnit -l centimeter -a degree -t film;\n"
         "\n"
         "createNode transform -n \"CHAR_hero_GRP\";\n"
         "createNode transform -n \"CHAR_hero_body_GRP\" -p \"CHAR_hero_GRP\";\n"
         "createNode transform -n \"CHAR_hero_head_GRP\" -p \"CHAR_hero_GRP\";\n"
         "createNode transform -n \"CHAR_hero_eyes_GRP\" -p \"CHAR_hero_head_GRP\";\n"
         "createNode transform -n \"CHAR_hero_accessories_GRP\" -p \"CHAR_hero_GRP\";\n"
         "\n"
         "// Notes:\n"
         "// - All geometry under CHAR_hero_GRP\n"
         "// - Clean quad topology, no ngons\n"
         "// - Pivot at world origin (0, 0, 0)\n"
         "// - Scale: 1 unit = 1 cm, character height ~175 units\n"
         "// - UVs unwrapped, no overlaps on shared UV space\n"
         "// - Normals facing outward, soft/hard edges set\n"
         "// - History deleted, transforms frozen\n"
         "\n"
         "select -r \"CHAR_hero_GRP\";\n"))

    log(w(out, ch + "/model/" + code + "_CHAR_hero_model_v001.blend",
         "# Blender scene file (.blend is binary - this is a placeholder)\n"
         "# Real file: " + code + "_CHAR_hero_model_v001.blend\n"
         "#\n"
         "# Scene: CHAR_hero_model\n"
         "# Asset: CHAR_hero\n"
         "# Department: model\n"
         "# Version: v001\n"
         "# Blender: 4.2\n"
         "#\n"
         "# Contents:\n"
         "# - Collection \"CHAR_hero\" containing all mesh objects\n"
         "# - Clean quad topology, no ngons\n"
         "# - UVs unwrapped on UDIM 1001\n"
         "# - Pivot at world origin\n"
         "# - Scale: 1 unit = 1 m (apply scale 100 from Maya cm)\n"
         "# - Modifiers: Subdivision Surface (view:2, render:3)\n"
         "# - Shape keys: NONE (those live in rig/)\n"
         "#\n"
         "# IMPORTANT: Use File > Link (not Append) when referencing\n"
         "# this asset in shot scenes so updates propagate.\n"))

    log(w(out, ch + "/model/" + code + "_CHAR_hero_model_v001.fbx",
         "; FBX export placeholder\n"
         "; Real file: " + code + "_CHAR_hero_model_v001.fbx\n"
         ";\n"
         "; Export settings (Maya):\n"
         ";   - File type: FBX 2020\n"
         ";   - Geometry: Triangulate OFF, Smoothing Groups ON\n"
         ";   - Up axis: Y-up (Maya default)\n"
         ";   - Scale: 1.0 (cm)\n"
         ";   - Include: Mesh only (no rig, no animation)\n"
         ";\n"
         "; Export settings (Blender):\n"
         ";   - Forward: -Z Forward, Up: Y Up\n"
         ";   - Scale: 0.01 (m to cm)\n"
         ";   - Apply Transform: ON\n"
         ";   - Objects: Selected meshes only\n"
         ";\n"
         "; Use for: Transfer to Substance Painter, ZBrush, or Blender\n"))

    log(w(out, ch + "/rig/" + code + "_CHAR_hero_rig_v001.ma",
         "// Maya ASCII\n"
         "// " + code + "_CHAR_hero_rig_v001.ma\n"
         "// Asset: CHAR_hero\n"
         "// Department: rig\n"
         "// Version: v001 - skeleton only\n"
         "\n"
         "fileType \"mayaAscii\"\n"
         "requires maya \"2025\";\n"
         "currentUnit -l centimeter -a degree -t film;\n"
         "\n"
         "// Skeleton hierarchy:\n"
         "// CHAR_hero_RIG_GRP\n"
         "//   CHAR_hero_SKELETON_GRP\n"
         "//     ROOT_JNT\n"
         "//       SPINE_01_JNT\n"
         "//         SPINE_02_JNT\n"
         "//           SPINE_03_JNT\n"
         "//             CHEST_JNT\n"
         "//               NECK_JNT\n"
         "//                 HEAD_JNT\n"
         "//               L_CLAVICLE_JNT -> L_UPPER_ARM_JNT -> L_FOREARM_JNT -> L_HAND_JNT\n"
         "//               R_CLAVICLE_JNT -> R_UPPER_ARM_JNT -> R_FOREARM_JNT -> R_HAND_JNT\n"
         "//       L_HIP_JNT -> L_UPPER_LEG_JNT -> L_KNEE_JNT -> L_FOOT_JNT\n"
         "//       R_HIP_JNT -> R_UPPER_LEG_JNT -> R_KNEE_JNT -> R_FOOT_JNT\n"
         "//   CHAR_hero_GEOM_GRP (referenced model)\n"
         "\n"
         "// Joint orientation: XYZ\n"
         "// Left side: positive X, suffix _L\n"
         "// Right side: negative X, suffix _R\n"
         "// Center: X=0, no side suffix\n"))

    log(w(out, ch + "/rig/" + code + "_CHAR_hero_rig_v001.blend",
         "# Blender armature placeholder\n"
         "# Real file: " + code + "_CHAR_hero_rig_v001.blend\n"
         "#\n"
         "# Asset: CHAR_hero | Dept: rig | v001\n"
         "# Generated with Rigify meta-rig (biped)\n"
         "#\n"
         "# Bones follow same naming as Maya skeleton\n"
         "# for consistency across DCCs:\n"
         "#   ROOT -> spine.001 -> spine.002 -> spine.003\n"
         "#     -> chest -> neck -> head\n"
         "#     -> shoulder.L -> upper_arm.L -> forearm.L -> hand.L\n"
         "#     -> shoulder.R -> upper_arm.R -> forearm.R -> hand.R\n"
         "#     -> hip.L -> thigh.L -> shin.L -> foot.L\n"
         "#     -> hip.R -> thigh.R -> shin.R -> foot.R\n"))

    log(w(out, ch + "/rig/" + code + "_CHAR_hero_rig_anim_v001.fbx",
         "; FBX rig export - for game engine or cross-DCC sharing\n"
         ";\n"
         "; Includes: Skeleton + skin weights + bind pose\n"
         "; Does NOT include: Control rig (controllers, IK/FK setups)\n"
         ";\n"
         "; Maya export: Include Skins ON, Animations OFF\n"
         "; Blender export: Only Deform Bones ON, Add Leaf Bones OFF\n"))

    log(w(out, ch + "/lookdev/" + code + "_CHAR_hero_lookdev_v001.ma",
         "// Maya ASCII - Look Development\n"
         "// " + code + "_CHAR_hero_lookdev_v001.ma\n"
         "// Asset: CHAR_hero\n"
         "// Department: lookdev\n"
         "// Version: v001\n"
         "\n"
         "// Renderer: Arnold\n"
         "// Color space: ACEScg (via OCIO)\n"
         "\n"
         "// Shader assignments:\n"
         "// CHAR_hero_skin   -> aiStandardSurface (SSS profile)\n"
         "// CHAR_hero_eyes   -> aiStandardSurface (specular, clearcoat)\n"
         "// CHAR_hero_hair   -> aiStandardHair (melanin, roughness)\n"
         "// CHAR_hero_cloth  -> aiStandardSurface (sheen, anisotropy)\n"
         "// CHAR_hero_metal  -> aiStandardSurface (metalness=1, IOR)\n"
         "\n"
         "// Texture paths (relative to project):\n"
         "//   ../textures/" + code + "_CHAR_hero_diffuse_4k.tx\n"
         "//   ../textures/" + code + "_CHAR_hero_roughness_4k.tx\n"
         "//   ../textures/" + code + "_CHAR_hero_normal_4k.tx\n"
         "//   ../textures/" + code + "_CHAR_hero_displacement_4k.exr\n"
         "\n"
         "// Light rig for lookdev:\n"
         "//   - 3-point key/fill/rim\n"
         "//   - Neutral grey environment\n"
         "//   - Chrome and matte grey reference spheres\n"
         "//   - MacBeth color chart\n"
         "\n"
         "// Turnaround render: " + code + "_CHAR_hero_lookdev_turnaround_v001.0001.exr\n"))

    log(w(out, ch + "/lookdev/" + code + "_CHAR_hero_lookdev_v001.blend",
         "# Blender Cycles lookdev placeholder\n"
         "# Real file: " + code + "_CHAR_hero_lookdev_v001.blend\n"
         "#\n"
         "# Renderer: Cycles (GPU - CUDA/OptiX/Metal)\n"
         "# Color management: ACEScg, Filmic\n"
         "#\n"
         "# Shader nodes:\n"
         "#   - Principled BSDF for skin, cloth, metal\n"
         "#   - Subsurface Scattering for skin\n"
         "#   - Hair Curves for groom\n"
         "#\n"
         "# Texture paths:\n"
         "#   ../textures/" + code + "_CHAR_hero_diffuse_4k.png\n"
         "#   ../textures/" + code + "_CHAR_hero_roughness_4k.png\n"
         "#   ../textures/" + code + "_CHAR_hero_normal_4k.png\n"
         "#\n"
         "# Note: NO .tx conversion needed for Cycles\n"
         "# Use .png directly or .exr for float maps\n"))

    for tex in ["diffuse_4k.png", "roughness_4k.png", "normal_4k.png", "metallic_4k.png"]:
        log(empty(out, ch + "/textures/" + code + "_CHAR_hero_" + tex))

    log(w(out, ch + "/textures/" + code + "_CHAR_hero_diffuse_4k.tx",
         "; MIP-mapped tiled texture (Arnold only)\n"
         "; Generated via: maketx " + code + "_CHAR_hero_diffuse_4k.png\n"
         ";   -o " + code + "_CHAR_hero_diffuse_4k.tx\n"
         ";   --filter lanczos3 --oiio\n"
         ";\n"
         "; Benefits: 5-10x faster texture reads in Arnold\n"
         "; Not needed for Blender Cycles\n"))

    log(empty(out, ch + "/textures/" + code + "_CHAR_hero_displacement_4k.exr"))

    log(w(out, ch + "/textures/README.md",
         "# Textures - CHAR_hero\n\n"
         "## Naming Convention\n"
         "`{PROJ}_{TYPE}_{name}_{channel}_{res}.{ext}`\n\n"
         "## Channels\n"
         "| File        | Format | Bit Depth   | Notes              |\n"
         "|-------------|--------|-------------|--------------------|\n"
         "| diffuse     | .png   | 8-bit       | Base color         |\n"
         "| roughness   | .png   | 8-bit       |                    |\n"
         "| normal      | .png   | 16-bit      | OpenGL convention  |\n"
         "| metallic    | .png   | 8-bit       |                    |\n"
         "| displacement| .exr   | 32-bit float| Always EXR         |\n"
         "| diffuse     | .tx    | 8-bit       | Maya/Arnold only   |\n\n"
         "## Rules\n"
         "- Displacement ALWAYS .exr (32-bit float) - never .png for displacement\n"
         "- Maya: convert all non-float maps to .tx via maketx\n"
         "- Blender: use .png directly - no .tx conversion\n"
         "- Resolution suffix: 1k, 2k, 4k, 8k\n"
         "- Never edit .tx files - regenerate from source\n".replace(
             "{PROJ}", code)))

    # ── 02_assets/environments/ ────────────────────────
    for sub in ["model", "lookdev", "textures"]:
        log(empty(out, "02_assets/environments/ENV_forest/" + sub + "/.gitkeep"))

    log(w(out, "02_assets/environments/README.md",
         "# Environments\n\n"
         "Each environment gets the same sub-structure as characters:\n"
         "```\n"
         "ENV_forest/\n"
         "  model/     -> " + code + "_ENV_forest_model_v001.ma\n"
         "  lookdev/   -> " + code + "_ENV_forest_lookdev_v001.blend\n"
         "  textures/  -> PBR map set\n"
         "```\n\n"
         "## Asset Types\n"
         "- ENV = environment / set\n"
         "- Large environments may split into modular kits\n"))

    # ── 02_assets/props/ ───────────────────────────────
    for sub in ["model", "lookdev", "textures"]:
        log(empty(out, "02_assets/props/PROP_sword/" + sub + "/.gitkeep"))

    log(w(out, "02_assets/props/README.md",
         "# Props\n\n"
         "Simpler than characters - typically model + lookdev + textures only.\n"
         "No rig unless the prop has moving parts.\n\n"
         "## Asset Types\n"
         "- PROP = hand-held or set dressing props\n"
         "- VEH = vehicles (may need rig)\n"))

    # ── 02_assets/_library/ ────────────────────────────
    log(empty(out, "02_assets/_library/materials/.gitkeep"))
    log(w(out, "02_assets/_library/materials/README.md",
         "# Shared Materials\n\n"
         "Reusable shader presets and material library.\n\n"
         "- Maya: .ma scenes with Arnold shader networks\n"
         "- Blender: .blend asset library\n\n"
         "## Naming\n"
         "`" + code + "_MAT_metal_brushed_v001.ma`\n"
         "`" + code + "_MAT_fabric_cotton_v001.blend`\n"))

    log(empty(out, "02_assets/_library/hdri/.gitkeep"))
    log(w(out, "02_assets/_library/hdri/README.md",
         "# HDRI Environment Maps\n\n"
         "For IBL (Image Based Lighting) in both Arnold and Cycles.\n\n"
         "## Format\n"
         "- .hdr (Radiance HDR) - 8K+ preferred\n"
         "- .exr (OpenEXR) - alternative\n\n"
         "## Naming\n"
         "`studio_neutral_8k.hdr`\n"
         "`forest_clearing_8k.hdr`\n\n"
         "## Usage\n"
         "- Maya Arnold: aiSkyDomeLight > Image > HDRI file\n"
         "- Blender Cycles: World > Surface > Environment Texture\n"))

    # ── 03_shots/ ──────────────────────────────────────
    sh = "03_shots/" + shot_rel

    log(w(out, sh + "/layout/" + code + "_" + shot_prefix + "_layout_v001.ma",
         "// Maya ASCII - Layout / Pre-viz\n"
         "// Shot: " + code + "_" + shot_prefix + "\n"
         "// Department: layout\n"
         "// Version: v001\n"
         "\n"
         "// Scene contains:\n"
         "// - Camera: " + code + "_" + shot_prefix + "_CAM (positioned per storyboard)\n"
         "// - Set dressing (low-poly proxy geometry)\n"
         "// - Character stand-ins (bounding boxes)\n"
         "// - Ground plane with reference grid\n"
         "\n"
         "// Camera settings:\n"
         "//   Focal length: 35mm\n"
         "//   Film gate: 1920x1080\n"
         "//   Output: 24 fps\n"
         "\n"
         "// Notes from director:\n"
         "// - Wide establishing shot, push in on character\n"
         "// - Hold 2 seconds, then dolly left\n"))

    log(w(out, sh + "/layout/" + code + "_" + shot_prefix + "_layout_v001.blend",
         "# Blender layout placeholder\n"
         "# Shot: " + code + "_" + shot_prefix + "\n"
         "# Camera: " + code + "_" + shot_prefix + "_CAM\n"
         "# Low-poly proxy scene for blocking\n"))

    log(w(out, sh + "/anim/" + code + "_" + shot_prefix + "_anim_v001.ma",
         "// Maya ASCII - Animation\n"
         "// Shot: " + code + "_" + shot_prefix + "\n"
         "// Department: anim\n"
         "// Version: v001 - blocking pass\n"
         "\n"
         "// Referenced assets:\n"
         "// - " + code + "_CHAR_hero_rig_v001.ma (Reference)\n"
         "// - " + code + "_" + shot_prefix + "_layout_v001.ma (Reference)\n"
         "\n"
         "// Animation layers:\n"
         "//   BaseLayer - stepped tangents, pose-to-pose blocking\n"
         "//\n"
         "// Workflow:\n"
         "//   v001 = blocking (stepped tangents)\n"
         "//   v002 = blocking plus\n"
         "//   v003 = spline pass\n"
         "//   v004 = polish + facial\n"
         "//   v005 = camera final\n"
         "//\n"
         "// After approval: bake to Alembic\n"
         "//   " + code + "_" + shot_prefix + "_CHAR_hero_anim.0001.abc\n"))

    log(w(out, sh + "/anim/" + code + "_" + shot_prefix + "_anim_v001.blend",
         "# Blender animation placeholder\n"
         "# Shot: " + code + "_" + shot_prefix + "\n"
         "# Referenced: CHAR_hero rig (Linked, not Appended)\n"
         "# v001 = blocking pass\n"))

    log(empty(out, sh + "/anim/" + code + "_" + shot_prefix + "_CHAR_hero_anim.0001.abc"))

    log(empty(out, sh + "/fx/" + code + "_" + shot_prefix + "_fx_cloth_v001.abc"))
    log(empty(out, sh + "/fx/" + code + "_" + shot_prefix + "_fx_pyro.0001.vdb"))

    log(w(out, sh + "/fx/README.md",
         "# FX - " + code + "_" + shot_prefix + "\n\n"
         "## Input\n"
         "Animation Alembic cache from anim department.\n\n"
         "## Output\n"
         "- Cloth/RBD: .abc frame sequences\n"
         "- Pyro/Fluid: .vdb frame sequences\n\n"
         "## Naming\n"
         "`" + code + "_" + shot_prefix + "_fx_cloth_v001.abc` (single cache, folder-versioned)\n"
         "`" + code + "_" + shot_prefix + "_fx_pyro.0001.vdb` (frame sequence)\n\n"
         "## No version in frame sequence names\n"
         "Version the containing folder instead:\n"
         "  fx/v001/" + code + "_" + shot_prefix + "_fx_pyro.0001.vdb\n"
         "  fx/v002/" + code + "_" + shot_prefix + "_fx_pyro.0001.vdb\n"))

    log(w(out, sh + "/lighting/" + code + "_" + shot_prefix + "_lighting_v001.ma",
         "// Maya ASCII - Lighting\n"
         "// Shot: " + code + "_" + shot_prefix + "\n"
         "// Department: lighting\n"
         "// Version: v001\n"
         "\n"
         "// Renderer: Arnold\n"
         "// Color space: ACEScg\n"
         "\n"
         "// References:\n"
         "// - Set/environment from assets (Reference)\n"
         "// - Animation Alembic cache\n"
         "// - FX caches (ABC + VDB)\n"
         "\n"
         "// Light rig:\n"
         "//   KEY_light    - aiAreaLight, warm 4500K\n"
         "//   FILL_light   - aiAreaLight, cool 6500K, 0.3 intensity\n"
         "//   RIM_light    - aiSpotLight, back-edge\n"
         "//   ENV_hdri     - aiSkyDomeLight, forest_clearing_8k.hdr\n"
         "\n"
         "// AOVs enabled:\n"
         "//   beauty, diffuse, specular, sss, emission,\n"
         "//   depth, motion_vector, shadow_matte, normal\n"
         "\n"
         "// Render settings:\n"
         "//   Samples: 4 AA, 2 diffuse, 2 specular, 2 sss\n"
         "//   Output: multi-layer EXR, 16-bit half-float\n"
         "//   Frames: 1001-1240 (240 frames)\n"))

    log(w(out, sh + "/lighting/" + code + "_" + shot_prefix + "_lighting_v001.blend",
         "# Blender Cycles lighting placeholder\n"
         "# Shot: " + code + "_" + shot_prefix + "\n"
         "# References: linked assets + ABC caches + VDB volumes\n"
         "# AOVs: Diffuse, Glossy, Transmission, Emission, Shadow, Depth\n"))

    log(empty(out, sh + "/renders/beauty/" + code + "_" + shot_prefix + "_beauty_v001.0001.exr"))
    for pass_name in ["diffuse", "specular", "depth", "motion_vector", "shadow_matte"]:
        log(empty(out, sh + "/renders/" + pass_name + "/.gitkeep"))

    log(w(out, sh + "/renders/README.md",
         "# Render Output - " + code + "_" + shot_prefix + "\n\n"
         "## Format\n"
         "All passes as OpenEXR frame sequences.\n\n"
         "## Naming\n"
         "`" + code + "_" + shot_prefix + "_{pass}_v{###}.{####}.exr`\n\n"
         "## Passes\n"
         "| Folder        | Pass            | Bit Depth   |\n"
         "|---------------|-----------------|-------------|\n"
         "| beauty/       | beauty          | 16-bit half |\n"
         "| diffuse/      | diffuse_direct  | 16-bit half |\n"
         "| specular/     | specular_direct | 16-bit half |\n"
         "| depth/        | depth           | 32-bit float|\n"
         "| motion_vector/| motionvector    | 32-bit float|\n"
         "| shadow_matte/ | shadow_matte    | 16-bit half |\n\n"
         "## Rules\n"
         "- NEVER render to JPEG, PNG, or MP4\n"
         "- Frame padding: 4 digits (0001)\n"
         "- Version: 3 digits (v001)\n"
         "- Multi-layer EXR preferred (all AOVs in one file)\n"))

    log(w(out, sh + "/comp/" + code + "_" + shot_prefix + "_comp_v001.nk",
         "# Nuke Compositing Script (placeholder)\n"
         "# Shot: " + code + "_" + shot_prefix + "\n"
         "# Version: v001\n"
         "\n"
         "# Node graph:\n"
         "#   Read (beauty EXR)\n"
         "#   Read (diffuse EXR)\n"
         "#   Read (specular EXR)\n"
         "#   Read (depth EXR)\n"
         "#   Read (motion_vector EXR)\n"
         "#   Read (shadow_matte EXR)\n"
         "#   Read (VDB smoke - if any)\n"
         "#   -> Merge/Grade/Defocus/ZDefocus\n"
         "#   -> Lens distortion (if plate-based)\n"
         "#   -> Grain match\n"
         "#   -> Write (comp output EXR)\n"
         "#   -> Write (review MP4)\n"
         "\n"
         "# Grade LUT: from color_scripts/ reference\n"
         "# Output: " + code + "_" + shot_prefix + "_comp_v001.####.exr\n"))

    log(empty(out, sh + "/comp/" + code + "_" + shot_prefix + "_review_v001.mp4"))

    # ── 04_cache/ ──────────────────────────────────────
    log(empty(out, "04_cache/alembic/" + code + "_" + shot_prefix + "_CHAR_hero_anim.0001.abc"))

    log(w(out, "04_cache/alembic/README.md",
         "# Alembic Cache\n\n"
         "Baked geometry caches - no rigs, no shaders.\n\n"
         "## Naming\n"
         "`" + code + "_{SEQ}_{SHOT}_{TYPE}_{name}_{type}.{####}.abc`\n\n"
         "## Examples\n"
         "`" + code + "_" + shot_prefix + "_CHAR_hero_anim.0001.abc`\n"
         "`" + code + "_" + shot_prefix + "_PROP_sword_anim.0001.abc`\n"
         "`" + code + "_" + shot_prefix + "_fx_cloth.0001.abc`\n\n"
         "## Rules\n"
         "- Frame padding: 4 digits\n"
         "- No version in filename - version the folder\n"
         "- Contains: vertices, normals, UVs, face indices per frame\n"
         "- Written by: Maya AbcExport, Blender Alembic export\n"
         "- Read by: Lighting, FX, Rendering departments\n"))

    log(empty(out, "04_cache/vdb/" + code + "_" + shot_prefix + "_fx_smoke.0001.vdb"))

    log(w(out, "04_cache/vdb/README.md",
         "# OpenVDB Cache\n\n"
         "Volumetric data - smoke, fire, fluid, atmosphere.\n\n"
         "## Naming\n"
         "`" + code + "_{SEQ}_{SHOT}_fx_{type}.{####}.vdb`\n\n"
         "## Examples\n"
         "`" + code + "_" + shot_prefix + "_fx_smoke_pyro.0001.vdb`\n"
         "`" + code + "_" + shot_prefix + "_fx_fire.0001.vdb`\n"
         "`" + code + "_" + shot_prefix + "_fx_fluid_water.0001.vdb`\n\n"
         "## Sources\n"
         "- Houdini Pyro FX\n"
         "- Blender Mantaflow\n"
         "- PhoenixFD\n\n"
         "## Readers\n"
         "- Maya Arnold: aiVolume node\n"
         "- Blender Cycles: Volume object with Principled Volume shader\n"))

    # ── 05_render/ ─────────────────────────────────────
    log(w(out, "05_render/README.md",
         "# Render Farm Output Root\n\n"
         "This is the top-level output directory for Deadline/Tractor farm jobs.\n\n"
         "The farm dispatcher writes rendered EXR frames here, organized by:\n"
         "```\n"
         "05_render/\n"
         "  " + shot_rel + "/\n"
         "    beauty/\n"
         "    diffuse/\n"
         "    specular/\n"
         "    ...\n"
         "```\n\n"
         "## Note\n"
         "Per-shot `renders/` folders in `03_shots/` are for local/test renders.\n"
         "This directory is for farm-managed batch output.\n\n"
         "After render complete, frames are copied to `06_comp/` for compositing.\n"))

    # ── 06_comp/ ───────────────────────────────────────
    log(empty(out, "06_comp/scripts/.gitkeep"))
    log(w(out, "06_comp/scripts/README.md",
         "# Nuke Scripts\n\n"
         "Per-shot Nuke .nk files.\n\n"
         "Naming: `" + code + "_{shot_prefix}_comp_v{###}.nk`\n\n"
         "Version the script file - keep old versions for rollback.\n"))

    log(empty(out, "06_comp/output/.gitkeep"))
    log(w(out, "06_comp/output/README.md",
         "# Composited Output\n\n"
         "Final graded EXR sequences and review videos.\n\n"
         "Naming:\n"
         "- `" + code + "_{shot_prefix}_comp_v{###}.{####}.exr` - graded EXR\n"
         "- `" + code + "_{shot_prefix}_review_v{###}.mp4` - H.264 review\n"))

    # ── 07_editorial/ ─────────────────────────────────
    log(empty(out, "07_editorial/cuts/.gitkeep"))
    log(w(out, "07_editorial/cuts/README.md",
         "# Editorial\n\n"
         "Premiere Pro / DaVinci Resolve project files and cut sequences.\n\n"
         "## Contents\n"
         "- Project files (.prproj, .drp)\n"
         "- Cut sequences (ProRes .mov)\n"
         "- Temp music and SFX\n"
         "- Picture lock reference\n\n"
         "## Workflow\n"
         "1. Animatic from 01_prepro/animatic/\n"
         "2. Replace with CG renders as shots complete\n"
         "3. Picture lock before final grade and sound mix\n"))

    # ── 08_delivery/ ──────────────────────────────────
    log(w(out, "08_delivery/" + code + "_DCP_v001/README.md",
         "# DCP - Digital Cinema Package\n\n"
         "Theatrical release format.\n\n"
         "## Contents\n"
         "- JPEG 2000 image sequences in MXF\n"
         "- Sound (PCM or Dolby)\n"
         "- DCP metadata (CPL, PKL, XML)\n\n"
         "## Created with\n"
         "- DaVinci Resolve (Delivery page -> DCP)\n"
         "- Clipster\n"
         "- easyDCP\n\n"
         "## Specs\n"
         "- Resolution: 4096x1716 (Scope) or 3996x2160 (Flat)\n"
         "- Frame rate: 24 fps\n"
         "- Color: X'Y'Z' (DCI-P3)\n"))

    log(empty(out, "08_delivery/" + code + "_prores4444_v001.mov"))
    log(empty(out, "08_delivery/" + code + "_h264_review_v001.mp4"))

    log(w(out, "08_delivery/README.md",
         "# Delivery\n\n"
         "## Formats\n"
         "| Format       | File                                | Use Case        |\n"
         "|--------------|-------------------------------------|-----------------|\n"
         "| DCP          | " + code + "_DCP_v001/                    | Theatrical      |\n"
         "| ProRes 4444  | " + code + "_prores4444_v001.mov          | Master/broadcast|\n"
         "| H.264        | " + code + "_h264_review_v001.mp4         | Review only     |\n\n"
         "## Rules\n"
         "- H.264 is review ONLY - never use as intermediate\n"
         "- Always encode from EXR masters at the final step only\n"
         "- DCP from DaVinci Resolve or Clipster\n"
         "- ProRes from Resolve export (ProRes 4444 for master, 422 HQ for broadcast)\n"
         "- Include QC report (BATON or manual checklist) before studio handoff\n"))

    # ── Root README ────────────────────────────────────
    log(w(out, "README.md",
         "# " + code + " - 3D Animation Pipeline\n\n"
         "## Project Type: " + (ptype.capitalize() if ptype == "movie" else "Episode / Series") + "\n"
         "## Project Code: " + code + "\n\n"
         "---\n\n"
         "## Folder Structure\n\n"
         "```\n"
         + code + "/\n"
         "+-- _pipeline/          Configuration files (OCIO, Deadline, paths)\n"
         "+-- 01_prepro/          Scripts, storyboards, concept art, animatic\n"
         "+-- 02_assets/          Characters, environments, props, shared library\n"
         "+-- 03_shots/           Per-shot work: layout -> anim -> FX -> lighting -> render -> comp\n"
         "+-- 04_cache/           Alembic (.abc) and OpenVDB (.vdb) caches\n"
         "+-- 05_render/          Farm output root\n"
         "+-- 06_comp/            Nuke scripts and composited output\n"
         "+-- 07_editorial/       Premiere / Resolve projects and cuts\n"
         "+-- 08_delivery/        DCP, ProRes, H.264 final deliverables\n"
         "```\n\n"
         "## Naming Convention\n\n"
         "### Assets\n"
         "`" + code + "_{TYPE}_{name}_{dept}_v{###}.{ext}`\n\n"
         "Example: `" + code + "_CHAR_hero_model_v001.ma`\n\n"
         "### Shots (" + (ptype.capitalize() if ptype == "movie" else "Episode / Series") + ")\n"
         "`" + shot_naming + "`\n\n"
         "Example: `" + code + "_" + shot_prefix + "_anim_v001.ma`\n\n"
         "### Textures\n"
         "`" + code + "_{TYPE}_{name}_{channel}_{resolution}.{ext}`\n\n"
         "Example: `" + code + "_CHAR_hero_diffuse_4k.png`\n\n"
         "### Caches\n"
         "No version in filename - version the folder.\n"
         "Frame padding always 4 digits: 0001\n\n"
         "### Renders\n"
         "`" + code + "_" + shot_prefix + "_{pass}_v{###}.{####}.exr`\n\n"
         "## Key Rules\n\n"
         "1. Project code always first - UPPERCASE 2-6 chars, no spaces: " + code + "\n"
         "2. Type prefix UPPERCASE (CHAR, ENV, PROP, VEH, FX), everything else lowercase\n"
         "3. Underscores only - no spaces, hyphens, or dots except before version and extension\n"
         "4. Version always 3 digits: v001 not v1 - Frame always 4 digits: 0001 not 1\n"
         "5. " + ("Sequence/shot in steps of 10 (SQ010, SH020) - leaves room to insert new shots" if ptype == "movie" else "Episode always 2 digits: EP01 not EP1 - replaces sequence in all shot names") + "\n"
         "6. Never overwrite - always increment version. WIP in _wip/ subfolder, never in shared root\n"
         "7. Maya saves as .ma (ASCII) not .mb - diffable and recoverable\n"
         "8. Blender: File -> Link not Append for shared assets - keeps scenes updateable\n"
         "9. Displacement textures always .exr (32-bit float) - never .png for displacement\n"
         "10. All render output as .exr sequences - never render directly to MP4 or MOV\n\n"
         "## Format Flow\n\n"
         "```\n"
         "Concept .psd -> Sculpt .ztl -> Model .ma/.blend -> FBX -> Substance -> .png/.exr\n"
         "Rig .ma/.blend -> Anim .ma/.blend -> Alembic .abc -> Lighting/FX\n"
         "FX .abc + .vdb -> Lighting\n"
         "Lighting -> EXR passes -> Nuke -> Grade -> Delivery\n"
         "```\n\n"
         "## Interchange Rules\n\n"
         "- Maya <-> Blender mesh: FBX (with rig) or OBJ (static)\n"
         "- Animation to lighting/FX: Alembic .abc always - never share live rig files downstream\n"
         "- Volume FX: OpenVDB .vdb - both Arnold and Cycles read natively\n"
         "- All render output: OpenEXR .exr sequences - never render to JPEG or PNG\n"
         "- Arnold textures: convert to .tx via maketx - raw PNG works but .tx is 5-10x faster\n"
         "- Cycles textures: .png or .exr directly - no conversion needed\n"
         "- Scale: Maya 1 unit = 1 cm - Blender 1 unit = 1 m - set FBX scale on export\n"))

    return created


def show_tree(path, prefix=""):
    items = sorted(os.listdir(path))
    dirs = [i for i in items if os.path.isdir(os.path.join(path, i))]
    files = [i for i in items if not os.path.isdir(os.path.join(path, i))]
    all_items = dirs + files
    for i, item in enumerate(all_items):
        is_last = i == len(all_items) - 1
        connector = "+-- " if is_last else "|-- "
        full = os.path.join(path, item)
        if os.path.isdir(full):
            print("  " + prefix + connector + item + "/")
            next_prefix = prefix + ("    " if is_last else "|   ")
            show_tree(full, next_prefix)
        else:
            print("  " + prefix + connector + item)


def main():
    parser = argparse.ArgumentParser(
        description="Generate 3D animation pipeline folder structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python make_pipeline.py\n"
               "  python make_pipeline.py --project BLAZE\n"
               "  python make_pipeline.py --project MYSHOW --type episode\n"
               "  python make_pipeline.py --project BLAZE --output D:/Projects"
    )
    parser.add_argument("--project", "-p", default="BLAZE",
                        help="Project code (UPPERCASE, no spaces). Default: BLAZE")
    parser.add_argument("--type", "-t", choices=["movie", "episode"], default="movie",
                        help="Movie or Episode/Series. Default: movie")
    parser.add_argument("--output", "-o", default=".",
                        help="Output directory. Default: current folder")
    args = parser.parse_args()

    code = args.project.upper().replace(" ", "").replace("-", "").replace("_", "")[:8]
    if not code:
        print("Error: Project code cannot be empty")
        sys.exit(1)

    out = os.path.abspath(args.output)
    root = os.path.join(out, code)

    print()
    print("  +==============================================+")
    print("  |   3D Animation Pipeline Generator            |")
    print("  +==============================================+")
    print("  |  Project:  " + code.ljust(36) + "|")
    print("  |  Type:     " + args.type.capitalize().ljust(36) + "|")
    print("  |  Output:   " + root.ljust(36) + "|")
    print("  +==============================================+")
    print()
    print("  Creating...")

    try:
        created = build(code, args.type, root)
    except Exception as e:
        print("\n  ERROR: " + str(e) + "\n")
        sys.exit(1)

    real_folders = sorted({os.path.dirname(p) for p in created if os.path.dirname(p)})
    real_files = [p for p in created if os.path.isfile(p)]

    print("  Done!\n")
    print("  ------------------------------------------")
    print("  Total items created:    " + str(len(created)).rjust(4))
    print("  Folders:                " + str(len(real_folders)).rjust(4))
    print("  Files with content:     " + str(len(real_files)).rjust(4))
    print("  ------------------------------------------")
    print("  Location: " + root)
    print()
    print("  Folder tree:")
    print()
    show_tree(root)
    print()
    print("  Ready to use. Open " + root + " in your file explorer.")
    print()


if __name__ == "__main__":
    main()
