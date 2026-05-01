import os
import sys
import argparse
from fontTools.ttLib import TTFont


def convert_to_woff2(input_path, output_path=None):
    """
    Convert a TTF or OTF font file to WOFF2 format.
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not input_path.lower().endswith((".ttf", ".otf")):
        raise ValueError("Input file must be a .ttf or .otf font.")

    if not output_path:
        base_name = os.path.splitext(input_path)[0]
        output_path = base_name + ".woff2"

    font = TTFont(input_path)
    font.flavor = "woff2"
    font.save(output_path)

    return output_path


def run_cli():
    parser = argparse.ArgumentParser(
        description="Convert TTF/OTF font files to WOFF2.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python make_woff2_UI.py --input font.ttf\n"
            "  python make_woff2_UI.py --input font.ttf --output font.woff2\n"
            "  python make_woff2_UI.py --input a.ttf b.otf c.ttf\n"
        ),
    )
    parser.add_argument(
        "--input", "-i",
        nargs="+",
        required=True,
        metavar="FONT",
        help="one or more .ttf / .otf files to convert",
    )
    parser.add_argument(
        "--output", "-o",
        nargs="*",
        metavar="OUT",
        help="output path(s); must match the number of --input files if given",
    )

    args = parser.parse_args()

    inputs  = args.input
    outputs = args.output or []

    if outputs and len(outputs) != len(inputs):
        parser.error(
            f"--output count ({len(outputs)}) must match --input count ({len(inputs)})"
        )

    ok, failed = [], []

    for i, inp in enumerate(inputs):
        out = outputs[i] if outputs else None
        try:
            result = convert_to_woff2(inp, out)
            print(f"  ✔  {inp}  →  {result}")
            ok.append(result)
        except Exception as e:
            print(f"  ✘  {inp}: {e}", file=sys.stderr)
            failed.append(inp)

    print()
    if ok:
        print(f"Converted {len(ok)} file(s) successfully.")
    if failed:
        print(f"Failed:    {len(failed)} file(s).", file=sys.stderr)
        sys.exit(1)


def run_gui():
    from tkinter import Tk, filedialog, messagebox

    root = Tk()
    root.withdraw()

    input_files = filedialog.askopenfilenames(
        title="Select TTF or OTF font files",
        filetypes=[("Font files", "*.ttf *.otf")]
    )

    if not input_files:
        messagebox.showwarning("No files selected", "No input files were chosen.")
        return

    converted_files, errors = [], []

    for input_file in input_files:
        try:
            output_file = os.path.splitext(input_file)[0] + ".woff2"
            result = convert_to_woff2(input_file, output_file)
            converted_files.append(result)
        except Exception as e:
            errors.append(f"{input_file}: {e}")

    if converted_files:
        msg = "✅ Successfully converted:\n" + "\n".join(converted_files)
        if errors:
            msg += "\n\n⚠️ Some errors occurred:\n" + "\n".join(errors)
        messagebox.showinfo("Conversion Results", msg)
    else:
        messagebox.showerror(
            "Conversion Failed",
            "❌ No files were converted successfully.\n\n" + "\n".join(errors)
        )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_cli()
    else:
        run_gui()