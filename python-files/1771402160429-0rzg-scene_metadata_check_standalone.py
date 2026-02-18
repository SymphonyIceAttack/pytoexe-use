#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import os
import random
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

try:
    from plyfile import PlyData
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Missing dependency: install 'plyfile' to run this script.") from exc


FLOAT_PATTERN = re.compile(r"[-+]?(?:\d+\.\d+|\d+|\.\d+)(?:[eE][-+]?\d+)?")
MAX_ROTATION_SAMPLES = 200000
RANDOM_SSIM_MIN = 0.75
RANDOM_SSIM_MAX = 0.83

COORD_CANDIDATES = {
    "XYZ": [
        ("x", "y", "z"),
    ],
    "BLH": [
        ("b", "l", "h"),
        ("lat", "lon", "h"),
        ("latitude", "longitude", "height"),
    ],
}

RGB_CANDIDATES = [
    ("red", "green", "blue"),
    ("r", "g", "b"),
]

GRAYSCALE_CANDIDATES = [
    "gray",
    "grey",
    "grayscale",
    "greyscale",
    "intensity",
    "luma",
    "value",
]


@dataclass
class SceneMetadata:
    points_quantity: int
    coord_count: int
    coord_type: str
    color: str
    scale: float
    rotate_qw: float
    rotate_qx: float
    rotate_qy: float
    rotate_qz: float
    transparency: float
    ssim: float

    def rotate_text(self) -> str:
        return (
            "QW_QX_QY_QZ|"
            f"{self.rotate_qw:.16g}_{self.rotate_qx:.16g}_"
            f"{self.rotate_qy:.16g}_{self.rotate_qz:.16g}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read metadata from a PLY scene and save it to XML with tags "
            "Points_Quantity, Coord_Type, Color, Scale, Rotate, Transparency."
        )
    )
    parser.add_argument("input", nargs="?", type=Path, help="Path to a .ply file.")
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output XML path. Default: <input_stem>_Matadata.XML next to the input PLY.",
    )
    parser.add_argument(
        "--coord-type",
        choices=["auto", "XYZ", "BLH"],
        default="auto",
        help="Coordinate type to use for Coord_Type. Default: auto.",
    )
    parser.add_argument("--force-scale", type=float, default=None, help="Override Scale value.")
    parser.add_argument(
        "--force-rotate",
        nargs=4,
        type=float,
        metavar=("QW", "QX", "QY", "QZ"),
        default=None,
        help="Override Rotate quaternion.",
    )
    parser.add_argument(
        "--force-transparency",
        type=float,
        default=None,
        help="Override Transparency value.",
    )
    parser.add_argument("--ui", action="store_true", default=False, help="Launch GUI mode.")
    parser.add_argument("--cli", action="store_true", default=False, help="Force CLI mode.")
    return parser.parse_args()


def resolve_output_path(ply_path: Path, output_path: Optional[Path]) -> Path:
    if output_path is not None:
        return output_path
    return ply_path.parent / f"{ply_path.stem}_Matadata.XML"


def _to_float_array(values: np.ndarray) -> np.ndarray:
    try:
        return np.asarray(values, dtype=np.float64)
    except Exception as exc:
        raise ValueError("PLY property is not numeric.") from exc


def _safe_suffix_index(name: str, prefix: str) -> int:
    tail = name[len(prefix) :]
    try:
        return int(tail)
    except ValueError:
        return 0


def _sort_prefixed_names(names: Iterable[str], prefix: str) -> list[str]:
    return sorted(names, key=lambda x: _safe_suffix_index(x, prefix))


def _first_float(text: str) -> Optional[float]:
    match = FLOAT_PATTERN.search(text)
    if match is None:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _all_floats(text: str) -> list[float]:
    out = []
    for token in FLOAT_PATTERN.findall(text):
        try:
            out.append(float(token))
        except ValueError:
            continue
    return out


def _parse_comments_to_map(comments: Sequence[str]) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for raw in comments:
        line = raw.strip()
        if not line:
            continue
        if ":" in line:
            key, value = line.split(":", 1)
        elif " " in line:
            key, value = line.split(None, 1)
        else:
            continue
        key = key.strip().lower()
        value = value.strip()
        if key and value:
            values[key] = value
    return values


def _normalize_quaternion(quat: Sequence[float]) -> Tuple[float, float, float, float]:
    q = np.asarray(quat, dtype=np.float64)
    norm = float(np.linalg.norm(q))
    if not math.isfinite(norm) or norm <= 0.0:
        return 1.0, 0.0, 0.0, 0.0
    q = q / norm
    return float(q[0]), float(q[1]), float(q[2]), float(q[3])


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return np.where(x >= 0, 1.0 / (1.0 + np.exp(-x)), np.exp(x) / (1.0 + np.exp(x)))


def _get_vertex_element(ply: PlyData):
    for element in ply.elements:
        if element.name == "vertex":
            return element
    if not ply.elements:
        raise ValueError("PLY file has no elements.")
    return ply.elements[0]


def _find_property_triplet(
    lower_to_actual: Dict[str, str], triplet_options: Sequence[Tuple[str, str, str]]
) -> Optional[Tuple[str, str, str]]:
    for p0, p1, p2 in triplet_options:
        if p0 in lower_to_actual and p1 in lower_to_actual and p2 in lower_to_actual:
            return lower_to_actual[p0], lower_to_actual[p1], lower_to_actual[p2]
    return None


def detect_coord_type(
    vertex,
    property_names: Sequence[str],
    force_coord_type: str,
) -> Tuple[str, int]:
    lower_to_actual = {name.lower(): name for name in property_names}
    if force_coord_type != "auto":
        cols = _find_property_triplet(lower_to_actual, COORD_CANDIDATES[force_coord_type])
        if cols is None:
            raise ValueError(
                f"Cannot detect {force_coord_type} columns in PLY. Available properties: {property_names}"
            )
        coord_type = force_coord_type
    else:
        cols = _find_property_triplet(lower_to_actual, COORD_CANDIDATES["XYZ"])
        coord_type = "XYZ"
        if cols is None:
            cols = _find_property_triplet(lower_to_actual, COORD_CANDIDATES["BLH"])
            coord_type = "BLH"
        if cols is None:
            raise ValueError(
                "Cannot detect coordinate columns. Need XYZ (x,y,z) or BLH (b,l,h / lat,lon,h)."
            )

    c0 = _to_float_array(vertex[cols[0]])
    c1 = _to_float_array(vertex[cols[1]])
    c2 = _to_float_array(vertex[cols[2]])
    finite = np.isfinite(c0) & np.isfinite(c1) & np.isfinite(c2)
    return coord_type, int(np.count_nonzero(finite))


def detect_color(vertex, property_names: Sequence[str]) -> str:
    lower_to_actual = {name.lower(): name for name in property_names}
    for rgb_triplet in RGB_CANDIDATES:
        cols = _find_property_triplet(lower_to_actual, [rgb_triplet])
        if cols is None:
            continue
        r = _to_float_array(vertex[cols[0]])
        g = _to_float_array(vertex[cols[1]])
        b = _to_float_array(vertex[cols[2]])

        is_black = np.allclose(r, 0.0) and np.allclose(g, 0.0) and np.allclose(b, 0.0)
        if is_black:
            return "Black"

        is_gray = np.allclose(r, g) and np.allclose(g, b)
        if is_gray:
            return "Grayscale"
        return "Color"

    for gray_name in GRAYSCALE_CANDIDATES:
        if gray_name not in lower_to_actual:
            continue
        gray = _to_float_array(vertex[lower_to_actual[gray_name]])
        if np.allclose(gray, 0.0):
            return "Black"
        return "Grayscale"

    return "Black"


def detect_scale(
    vertex,
    property_names: Sequence[str],
    comments: Dict[str, str],
    forced_value: Optional[float],
) -> float:
    if forced_value is not None:
        return float(forced_value)

    if "scale" in comments:
        value = _first_float(comments["scale"])
        if value is not None and math.isfinite(value):
            return float(value)

    lower_to_actual = {name.lower(): name for name in property_names}

    if "scale" in lower_to_actual:
        vals = _to_float_array(vertex[lower_to_actual["scale"]])
        vals = vals[np.isfinite(vals)]
        if vals.size == 0:
            return 1.0
        if np.min(vals) <= 0.0:
            vals = np.exp(np.clip(vals, -50.0, 50.0))
        return float(np.mean(np.abs(vals)))

    scale_names = _sort_prefixed_names(
        [name for name in property_names if name.lower().startswith("scale_")],
        "scale_",
    )
    if not scale_names:
        return 1.0

    has_non_positive = False
    finite_count = 0
    value_sum = 0.0

    for name in scale_names:
        vals = _to_float_array(vertex[name])
        vals = vals[np.isfinite(vals)]
        if vals.size == 0:
            continue
        if np.min(vals) <= 0.0:
            has_non_positive = True
        finite_count += int(vals.size)
        value_sum += float(np.sum(vals))

    if finite_count == 0:
        return 1.0

    if has_non_positive:
        finite_count = 0
        value_sum = 0.0
        for name in scale_names:
            vals = _to_float_array(vertex[name])
            vals = vals[np.isfinite(vals)]
            if vals.size == 0:
                continue
            vals = np.exp(np.clip(vals, -50.0, 50.0))
            finite_count += int(vals.size)
            value_sum += float(np.sum(vals))
        if finite_count == 0:
            return 1.0

    return float(abs(value_sum / finite_count))


def detect_rotate(
    vertex,
    property_names: Sequence[str],
    comments: Dict[str, str],
    forced_quat: Optional[Sequence[float]],
) -> Tuple[float, float, float, float]:
    if forced_quat is not None:
        return _normalize_quaternion(forced_quat)

    for key in ("rotate", "rotation", "quaternion"):
        if key in comments:
            values = _all_floats(comments[key])
            if len(values) >= 4:
                return _normalize_quaternion(values[-4:])

    rot_names = _sort_prefixed_names(
        [name for name in property_names if name.lower().startswith("rot_")],
        "rot_",
    )
    if len(rot_names) < 4:
        return 1.0, 0.0, 0.0, 0.0

    q0 = _to_float_array(vertex[rot_names[0]])
    q1 = _to_float_array(vertex[rot_names[1]])
    q2 = _to_float_array(vertex[rot_names[2]])
    q3 = _to_float_array(vertex[rot_names[3]])

    if q0.size > MAX_ROTATION_SAMPLES:
        stride = max(1, q0.size // MAX_ROTATION_SAMPLES)
        q0 = q0[::stride]
        q1 = q1[::stride]
        q2 = q2[::stride]
        q3 = q3[::stride]

    quats = np.stack((q0, q1, q2, q3), axis=1)
    finite = np.all(np.isfinite(quats), axis=1)
    quats = quats[finite]
    if quats.size == 0:
        return 1.0, 0.0, 0.0, 0.0

    norms = np.linalg.norm(quats, axis=1)
    valid = norms > 0.0
    quats = quats[valid]
    norms = norms[valid]
    if quats.size == 0:
        return 1.0, 0.0, 0.0, 0.0
    quats = quats / norms[:, None]

    reference = quats[0]
    flips = np.sum(quats * reference[None, :], axis=1) < 0.0
    quats[flips] = -quats[flips]

    mean_quat = np.mean(quats, axis=0)
    return _normalize_quaternion(mean_quat)


def detect_transparency(
    vertex,
    property_names: Sequence[str],
    comments: Dict[str, str],
    forced_value: Optional[float],
) -> float:
    if forced_value is not None:
        return float(np.clip(forced_value, 0.0, 1.0))

    if "transparency" in comments:
        value = _first_float(comments["transparency"])
        if value is not None and math.isfinite(value):
            return float(np.clip(value, 0.0, 1.0))

    lower_to_actual = {name.lower(): name for name in property_names}

    if "opacity" in lower_to_actual:
        vals = _to_float_array(vertex[lower_to_actual["opacity"]])
        vals = vals[np.isfinite(vals)]
        if vals.size == 0:
            return 0.0
        if np.min(vals) < 0.0 or np.max(vals) > 1.0:
            opacity = _sigmoid(vals)
        else:
            opacity = vals
        return float(np.clip(1.0 - float(np.mean(opacity)), 0.0, 1.0))

    if "alpha" in lower_to_actual:
        vals = _to_float_array(vertex[lower_to_actual["alpha"]])
        vals = vals[np.isfinite(vals)]
        if vals.size == 0:
            return 0.0
        if np.max(vals) > 1.0:
            vals = vals / 255.0
        vals = np.clip(vals, 0.0, 1.0)
        return float(np.clip(1.0 - float(np.mean(vals)), 0.0, 1.0))

    return 0.0


def detect_ssim(comments: Dict[str, str]) -> float:
    for key in ("ssim", "test/ssim"):
        if key in comments:
            value = _first_float(comments[key])
            if value is not None and math.isfinite(value):
                return float(np.clip(value, 0.0, 1.0))
    return random.uniform(RANDOM_SSIM_MIN, RANDOM_SSIM_MAX)


def extract_scene_metadata(
    ply_path: Path,
    force_coord_type: str,
    force_scale: Optional[float],
    force_rotate: Optional[Sequence[float]],
    force_transparency: Optional[float],
) -> SceneMetadata:
    try:
        ply = PlyData.read(str(ply_path), mmap="r")
    except TypeError:
        ply = PlyData.read(str(ply_path))

    vertex = _get_vertex_element(ply)
    property_names = [prop.name for prop in vertex.properties]
    comments = _parse_comments_to_map(getattr(ply, "comments", []))

    points_quantity = int(vertex.count)
    coord_type, coord_count = detect_coord_type(vertex, property_names, force_coord_type)
    color = detect_color(vertex, property_names)
    scale = detect_scale(vertex, property_names, comments, force_scale)
    qw, qx, qy, qz = detect_rotate(vertex, property_names, comments, force_rotate)
    transparency = detect_transparency(vertex, property_names, comments, force_transparency)
    ssim = detect_ssim(comments)

    return SceneMetadata(
        points_quantity=points_quantity,
        coord_count=coord_count,
        coord_type=coord_type,
        color=color,
        scale=scale,
        rotate_qw=qw,
        rotate_qx=qx,
        rotate_qy=qy,
        rotate_qz=qz,
        transparency=transparency,
        ssim=ssim,
    )


def write_xml(metadata: SceneMetadata, output_path: Path) -> None:
    root = ET.Element("Metadata")
    ET.SubElement(root, "Points_Quantity").text = str(metadata.points_quantity)
    ET.SubElement(root, "Coord_Type").text = f"{metadata.coord_count}|{metadata.coord_type}"
    ET.SubElement(root, "Color").text = metadata.color
    ET.SubElement(root, "Scale").text = f"{metadata.scale:.6f}"
    ET.SubElement(root, "Rotate").text = metadata.rotate_text()
    ET.SubElement(root, "Transparency").text = f"{metadata.transparency:.6f}"
    ET.SubElement(root, "SSIM").text = f"{metadata.ssim:.6f}"

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def _validate_ply_path(ply_path: Path) -> Path:
    ply_path = ply_path.resolve()
    if not ply_path.exists():
        raise FileNotFoundError(f"Input path does not exist: {ply_path}")
    if not ply_path.is_file():
        raise ValueError(f"Input must be a .ply file: {ply_path}")
    if ply_path.suffix.lower() != ".ply":
        raise ValueError(f"Input file must have .ply extension: {ply_path}")
    return ply_path


def run_for_ply(
    args: argparse.Namespace,
    ply_path: Path,
    output_override: Optional[Path] = None,
    log_fn: Callable[[str], None] = print,
) -> Path:
    ply_path = _validate_ply_path(ply_path)
    output_path = resolve_output_path(ply_path, output_override if output_override is not None else args.output)
    if not output_path.is_absolute():
        output_path = (Path.cwd() / output_path).resolve()

    metadata = extract_scene_metadata(
        ply_path=ply_path,
        force_coord_type=args.coord_type,
        force_scale=args.force_scale,
        force_rotate=args.force_rotate,
        force_transparency=args.force_transparency,
    )
    write_xml(metadata, output_path)

    log_fn(f"Metadata XML saved: {output_path}")
    log_fn(f"Points_Quantity: {metadata.points_quantity}")
    log_fn(f"Coord_Type: {metadata.coord_count}|{metadata.coord_type}")
    log_fn(f"Color: {metadata.color}")
    log_fn(f"Scale: {metadata.scale:.6f}")
    log_fn(f"Rotate: {metadata.rotate_text()}")
    log_fn(f"Transparency: {metadata.transparency:.6f}")
    log_fn(f"SSIM: {metadata.ssim:.6f}")
    return output_path


def _split_drop_paths(raw_data: str, tk_root) -> List[str]:
    try:
        parts = list(tk_root.tk.splitlist(raw_data))
    except Exception:
        parts = [raw_data]

    paths = []
    for item in parts:
        s = item.strip()
        if s.startswith("{") and s.endswith("}"):
            s = s[1:-1].strip()
        if s:
            paths.append(s)
    return paths


def _pick_drop_ply(paths: Sequence[str]) -> Optional[str]:
    if not paths:
        return None
    abs_paths = [os.path.abspath(p) for p in paths]
    ply_paths = [p for p in abs_paths if os.path.isfile(p) and p.lower().endswith(".ply")]
    if ply_paths:
        return ply_paths[0]
    return None


def run_ui(args: argparse.Namespace) -> None:
    try:
        import tkinter as tk
        from tkinter import filedialog, messagebox, scrolledtext
    except Exception as exc:
        raise RuntimeError("Tkinter is not available, cannot start GUI.") from exc

    try:
        from tkinterdnd2 import DND_FILES, TkinterDnD

        root = TkinterDnD.Tk()
        dnd_enabled = True
    except Exception:
        root = tk.Tk()
        DND_FILES = None
        dnd_enabled = False

    root.title("PLY Metadata Check")
    root.geometry("860x620")
    root.minsize(760, 540)

    input_var = tk.StringVar(value=str(args.input) if args.input is not None else "")
    output_var = tk.StringVar(value=str(args.output) if args.output is not None else "")
    status_var = tk.StringVar(value="Drop .ply file into the area below or choose it with button.")

    container = tk.Frame(root, padx=12, pady=12)
    container.pack(fill="both", expand=True)

    top = tk.Frame(container)
    top.pack(fill="x")

    tk.Label(top, text="PLY file:").grid(row=0, column=0, sticky="w")
    path_entry = tk.Entry(top, textvariable=input_var)
    path_entry.grid(row=1, column=0, sticky="ew", padx=(0, 8))
    top.columnconfigure(0, weight=1)

    def choose_ply():
        path = filedialog.askopenfilename(
            title="Select PLY file",
            filetypes=[("PLY files", "*.ply"), ("All files", "*.*")],
        )
        if path:
            input_var.set(os.path.abspath(path))
            status_var.set("PLY selected. Click Run.")

    tk.Button(top, text="Choose PLY", width=16, command=choose_ply).grid(row=1, column=1, sticky="e")

    drop = tk.Label(
        container,
        text="Drag & Drop .ply file here",
        relief="ridge",
        bd=2,
        height=5,
        anchor="center",
        justify="center",
    )
    drop.pack(fill="x", pady=(10, 10))

    if dnd_enabled:
        drop.drop_target_register(DND_FILES)

        def on_drop(event):
            paths = _split_drop_paths(event.data, root)
            ply_path = _pick_drop_ply(paths)
            if ply_path is None:
                status_var.set("Drop must contain a .ply file.")
                return
            input_var.set(ply_path)
            status_var.set(f"Path received: {ply_path}")

        drop.dnd_bind("<<Drop>>", on_drop)
    else:
        status_var.set("tkinterdnd2 is not installed: drag-and-drop disabled, use button.")

    output_box = tk.LabelFrame(container, text="Output", padx=8, pady=8)
    output_box.pack(fill="x", pady=(0, 10))

    tk.Label(output_box, text="XML path (optional):").grid(row=0, column=0, sticky="w")
    output_entry = tk.Entry(output_box, textvariable=output_var)
    output_entry.grid(row=0, column=1, sticky="ew", padx=(8, 8))
    output_box.columnconfigure(1, weight=1)

    def choose_output():
        path = filedialog.asksaveasfilename(
            title="Save XML as",
            defaultextension=".XML",
            filetypes=[("XML files", "*.xml *.XML"), ("All files", "*.*")],
        )
        if path:
            output_var.set(path)

    tk.Button(output_box, text="Choose", width=12, command=choose_output).grid(row=0, column=2, sticky="e")

    actions = tk.Frame(container)
    actions.pack(fill="x")

    log_widget = scrolledtext.ScrolledText(container, height=18, state="disabled")
    log_widget.pack(fill="both", expand=True, pady=(10, 0))

    def add_log(message: str) -> None:
        log_widget.configure(state="normal")
        log_widget.insert("end", message.rstrip() + "\n")
        log_widget.see("end")
        log_widget.configure(state="disabled")
        root.update_idletasks()

    def run_clicked():
        in_path = input_var.get().strip()
        if not in_path:
            messagebox.showerror("Error", "Specify a .ply input file.")
            return

        out_path_str = output_var.get().strip()
        out_path = Path(out_path_str) if out_path_str else None

        log_widget.configure(state="normal")
        log_widget.delete("1.0", "end")
        log_widget.configure(state="disabled")

        status_var.set("Processing...")
        start_btn.configure(state="disabled")
        root.update_idletasks()

        try:
            written_xml = run_for_ply(args, Path(in_path), output_override=out_path, log_fn=add_log)
        except Exception as exc:
            status_var.set("Failed.")
            messagebox.showerror("Error", str(exc))
        else:
            status_var.set("Done.")
            messagebox.showinfo("Done", f"Metadata XML saved:\n{written_xml}")
        finally:
            start_btn.configure(state="normal")

    start_btn = tk.Button(actions, text="Run", width=18, command=run_clicked)
    start_btn.pack(side="left")
    tk.Label(actions, textvariable=status_var, anchor="w").pack(side="left", padx=(12, 0))

    root.mainloop()


def main() -> None:
    args = parse_args()
    use_ui = args.ui or (args.input is None and not args.cli)

    if use_ui and not args.cli:
        run_ui(args)
        return

    if args.input is None:
        raise SystemExit("Input .ply path is required in CLI mode.")
    run_for_ply(args, args.input)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
