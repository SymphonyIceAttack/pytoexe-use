import zipfile
import os
import re
import xml.etree.ElementTree as ET


def get_output_filename(input_file):
    """
    Generate the next revision filename.

    Examples:
        Book.xlsx       -> Book R1.xlsx
        Book R1.xlsx    -> Book R2.xlsx
        Book r7.xlsx    -> Book R8.xlsx
        Book R.xlsx     -> Book R1.xlsx
        Book rx.xlsx    -> Book R1.xlsx
    """

    folder = os.path.dirname(input_file)
    filename = os.path.basename(input_file)

    name, extension = os.path.splitext(filename)

    # Look for " R", " r", " R1", " r1", etc. at the end.
    match = re.search(r"\s[Rr](\d*)$", name)

    if match:
        revision_text = match.group(1)

        if revision_text:
            revision = int(revision_text) + 1
        else:
            revision = 1

        base_name = name[:match.start()]
        output_name = f"{base_name} R{revision}{extension}"

    else:
        output_name = f"{name} R1{extension}"

    return os.path.join(folder, output_name)


def get_available_output_filename(input_file):
    """
    Generate an output filename that does not already exist.
    """

    folder = os.path.dirname(input_file)
    filename = os.path.basename(input_file)

    name, extension = os.path.splitext(filename)

    match = re.search(r"\s[Rr](\d*)$", name)

    if match:
        base_name = name[:match.start()]

        if match.group(1):
            revision = int(match.group(1))
        else:
            revision = 0

    else:
        base_name = name
        revision = 0

    while True:

        revision += 1

        output_name = (
            f"{base_name} R{revision}{extension}"
        )

        output_file = os.path.join(
            folder,
            output_name
        )

        if not os.path.exists(output_file):
            return output_file


def is_print_name(defined_name):
    """
    Determine whether an Excel defined name is a
    print area or print title.

    Excel normally stores these as:

        _xlnm.Print_Area
        _xlnm.Print_Titles

    Some workbooks may contain the names without
    the _xlnm prefix, so those are also retained.
    """

    name = defined_name.get("name", "")

    # Remove any leading workbook prefix.
    clean_name = name.lower()

    if clean_name.startswith("_xlnm."):
        clean_name = clean_name[6:]

    return clean_name in (
        "print_area",
        "print_titles"
    )


def remove_unwanted_named_ranges(input_file, output_file):

    print("\nOpening workbook...")
    print("Reading workbook contents...")

    namespace = {
        "main":
        "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    }

    removed_count = 0
    retained_count = 0

    with zipfile.ZipFile(input_file, "r") as zin:

        with zipfile.ZipFile(
            output_file,
            "w",
            zipfile.ZIP_DEFLATED
        ) as zout:

            for item in zin.infolist():

                data = zin.read(item.filename)

                if item.filename == "xl/workbook.xml":

                    print("\nProcessing workbook.xml...")
                    print("Checking defined names...")

                    root = ET.fromstring(data)

                    defined_names = root.find(
                        "main:definedNames",
                        namespace
                    )

                    if defined_names is not None:

                        original_count = len(
                            defined_names
                        )

                        print(
                            f"Found {original_count:,} "
                            "defined name(s)."
                        )

                        # Build a list of names to remove.
                        names_to_remove = []

                        for defined_name in defined_names:

                            name = defined_name.get(
                                "name",
                                ""
                            )

                            if is_print_name(
                                defined_name
                            ):

                                retained_count += 1

                                print(
                                    f"Keeping: {name}"
                                )

                            else:

                                names_to_remove.append(
                                    defined_name
                                )

                        # Remove unwanted names.
                        for defined_name in names_to_remove:

                            defined_names.remove(
                                defined_name
                            )

                            removed_count += 1

                        # If no names remain, remove the
                        # definedNames container itself.
                        if len(defined_names) == 0:

                            root.remove(
                                defined_names
                            )

                        data = ET.tostring(
                            root,
                            encoding="utf-8",
                            xml_declaration=True
                        )

                        print(
                            f"\nRemoved: "
                            f"{removed_count:,}"
                        )

                        print(
                            f"Retained: "
                            f"{retained_count:,}"
                        )

                    else:

                        print(
                            "No defined names were found."
                        )

                zout.writestr(
                    item,
                    data
                )

    return removed_count, retained_count


def main():

    print("=" * 72)
    print("EXCEL NAMED RANGE CLEANER")
    print("=" * 72)

    print(
        "\nThis program removes unwanted named ranges "
        "from an Excel workbook."
    )

    print(
        "\nOnly the following defined names will be retained:"
    )

    print(
        "  - Print_Area"
    )

    print(
        "  - Print_Titles"
    )

    print(
        "\nEvery other defined name will be removed."
    )

    print(
        "\nThe program works directly on the Excel file's "
        "internal XML."
    )

    print(
        "This avoids deleting 100,000+ names individually "
        "through Excel/VBA."
    )

    print(
        "\nThe original file will NOT be modified."
    )

    print(
        "A new revisioned file will be created."
    )

    print("\n" + "-" * 72)

    # ------------------------------------------------------------------
    # Get input file
    # ------------------------------------------------------------------

    input_file = input(
        "\nEnter the full path of the input Excel file: "
    ).strip().strip('"')

    if not input_file:

        print(
            "\nERROR: No input file was provided."
        )

        input(
            "\nPress Enter to exit..."
        )

        return

    if not os.path.isfile(input_file):

        print(
            f"\nERROR: File not found:\n{input_file}"
        )

        input(
            "\nPress Enter to exit..."
        )

        return

    # ------------------------------------------------------------------
    # Check extension
    # ------------------------------------------------------------------

    extension = os.path.splitext(
        input_file
    )[1].lower()

    supported_extensions = (
        ".xlsx",
        ".xlsm",
        ".xltx",
        ".xltm"
    )

    if extension not in supported_extensions:

        print(
            f"\nWARNING: {extension} is not a standard "
            "Excel Open XML workbook extension."
        )

        answer = input(
            "Continue anyway? (Y/N): "
        ).strip().lower()

        if answer != "y":

            print(
                "\nOperation cancelled."
            )

            input(
                "\nPress Enter to exit..."
            )

            return

    # ------------------------------------------------------------------
    # Generate output filename
    # ------------------------------------------------------------------

    output_file = get_output_filename(
        input_file
    )

    # If that revision already exists, find next one.
    if os.path.exists(output_file):

        output_file = get_available_output_filename(
            input_file
        )

    print(
        f"\nInput file:\n{input_file}"
    )

    print(
        f"\nOutput file:\n{output_file}"
    )

    print("\n" + "-" * 72)

    # ------------------------------------------------------------------
    # Process workbook
    # ------------------------------------------------------------------

    try:

        removed_count, retained_count = (
            remove_unwanted_named_ranges(
                input_file,
                output_file
            )
        )

        print("\n" + "=" * 72)
        print("PROCESS COMPLETED SUCCESSFULLY")
        print("=" * 72)

        print(
            f"\nNamed ranges removed : "
            f"{removed_count:,}"
        )

        print(
            f"Print names retained : "
            f"{retained_count:,}"
        )

        print(
            f"\nOutput file:\n{output_file}"
        )

        print(
            "\nThe original input file was not modified."
        )

        print(
            "\nYou can now open the output file in Excel "
            "and verify the workbook."
        )

    except zipfile.BadZipFile:

        print(
            "\nERROR: The input file is not a valid "
            "Excel Open XML workbook."
        )

        if os.path.exists(output_file):

            try:
                os.remove(output_file)
            except Exception:
                pass

    except Exception as e:

        print(
            f"\nERROR: An unexpected error occurred:\n{e}"
        )

        if os.path.exists(output_file):

            try:
                os.remove(output_file)
            except Exception:
                pass

    print("\n" + "-" * 72)

    input(
        "Press Enter to exit..."
    )


if __name__ == "__main__":
    main()