import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import xml.etree.ElementTree as ET
from collections import OrderedDict
import os

# NOTE:
# This should be the actual XML namespace URI used by your source files.
# If your input XML uses a real URI, replace this with that exact URI.
# If the files literally use "wtt" as the namespace URI, keep it as-is.
WTT_NS = "wtt"
ET.register_namespace("wtt", WTT_NS)


class WaferXMLProcessor:
    def __init__(self, root):
        self.root = root
        self.root.title("Wafer XML Coordinate Processor")
        self.root.geometry("1600x1000")

        self.wafer_xml_path = None
        self.xml_tree = None
        self.tray_xml_tree = None
        self.tray_xml_path = None

        self.x_offset = 0
        self.y_offset = 0

        self.coordinate_data = []
        self.reject_die_data = []
        self.reject_coordinates = set()

        self.misalignment_data = []
        self.misalignment_processed = False
        self.unused_good_coordinates = []

        self.setup_ui()

    # -------------------------
    # UI
    # -------------------------
    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        self.main_tab = ttk.Frame(self.notebook, padding="10")
        self.misalignment_tab = ttk.Frame(self.notebook, padding="10")

        self.notebook.add(self.main_tab, text="Coordinate Processor")
        self.notebook.add(self.misalignment_tab, text="Wafer Misalignment Correction")

        self.setup_main_tab()
        self.setup_misalignment_tab()

    def setup_main_tab(self):
        main_frame = ttk.Frame(self.main_tab, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.main_tab.columnconfigure(0, weight=1)
        self.main_tab.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)

        file_frame = ttk.LabelFrame(main_frame, text="Wafer XML File Selection", padding="5")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        ttk.Label(file_frame, text="Wafer XML:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.wafer_xml_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.wafer_xml_var, state="readonly").grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5)
        )
        ttk.Button(file_frame, text="Browse", command=self.browse_wafer_xml).grid(row=0, column=2)

        reject_frame = ttk.LabelFrame(main_frame, text="Reject Dies (Old WX / Old WY)", padding="5")
        reject_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        reject_frame.columnconfigure(0, weight=1)

        reject_input_frame = ttk.Frame(reject_frame)
        reject_input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        reject_input_frame.columnconfigure(1, weight=1)

        ttk.Label(reject_input_frame, text="Old WX:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.reject_wx_var = tk.StringVar()
        ttk.Entry(reject_input_frame, textvariable=self.reject_wx_var, width=12).grid(
            row=0, column=1, sticky=tk.W, padx=(0, 15)
        )

        ttk.Label(reject_input_frame, text="Old WY:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.reject_wy_var = tk.StringVar()
        ttk.Entry(reject_input_frame, textvariable=self.reject_wy_var, width=12).grid(
            row=0, column=3, sticky=tk.W, padx=(0, 15)
        )

        ttk.Button(reject_input_frame, text="Add Reject Die", command=self.add_reject_die).grid(
            row=0, column=4, padx=(0, 10)
        )
        ttk.Button(reject_input_frame, text="Delete Selected", command=self.delete_reject_die).grid(row=0, column=5)

        reject_list_frame = ttk.Frame(reject_frame)
        reject_list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        reject_list_frame.columnconfigure(0, weight=1)
        reject_list_frame.rowconfigure(0, weight=1)

        self.reject_tree = ttk.Treeview(
            reject_list_frame, columns=("Old_WX", "Old_WY"), show="headings", height=4
        )
        self._setup_tree_columns(
            self.reject_tree,
            [("Old_WX", "Old WX", 95), ("Old_WY", "Old WY", 95)]
        )

        reject_scroll = ttk.Scrollbar(reject_list_frame, orient=tk.VERTICAL, command=self.reject_tree.yview)
        self.reject_tree.configure(yscrollcommand=reject_scroll.set)

        self.reject_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        reject_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))

        offset_frame = ttk.LabelFrame(main_frame, text="WTT Reference Offsets", padding="5")
        offset_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(offset_frame, text="X Offset:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.x_offset_var = tk.StringVar(value="0")
        ttk.Label(offset_frame, textvariable=self.x_offset_var, font=("Arial", 10, "bold")).grid(
            row=0, column=1, sticky=tk.W, padx=(0, 20)
        )

        ttk.Label(offset_frame, text="Y Offset:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.y_offset_var = tk.StringVar(value="0")
        ttk.Label(offset_frame, textvariable=self.y_offset_var, font=("Arial", 10, "bold")).grid(
            row=0, column=3, sticky=tk.W, padx=(0, 20)
        )

        ttk.Button(offset_frame, text="Process Coordinates", command=self.process_coordinates).grid(
            row=0, column=4, padx=(20, 0)
        )

        formula_frame = ttk.LabelFrame(main_frame, text="Transformation Formulas", padding="5")
        formula_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(formula_frame, text="X Formula:", font=("Arial", 9, "bold")).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5)
        )
        ttk.Label(formula_frame, text="(old WX + X Offset) * -1 = new WX", font=("Arial", 9), foreground="blue").grid(
            row=0, column=1, sticky=tk.W, padx=(0, 20)
        )

        ttk.Label(formula_frame, text="Y Formula:", font=("Arial", 9, "bold")).grid(
            row=0, column=2, sticky=tk.W, padx=(0, 5)
        )
        ttk.Label(formula_frame, text="(old WY + Y Offset) * -1 = new WY", font=("Arial", 9), foreground="blue").grid(
            row=0, column=3, sticky=tk.W
        )

        results_frame = ttk.LabelFrame(main_frame, text="Coordinate Transformations", padding="5")
        results_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)

        self.results_tree = ttk.Treeview(
            results_frame,
            columns=("TraySequence", "TX", "TY", "Original_WX", "Original_WY", "New_WX", "New_WY", "BinCode"),
            show="headings",
            height=10,
        )
        self.results_tree.tag_configure("reject", background="#ff9999")

        self._setup_tree_columns(
            self.results_tree,
            [
                ("TraySequence", "Tray Sequence", 95),
                ("TX", "TX", 50),
                ("TY", "TY", 50),
                ("Original_WX", "Old WX", 70),
                ("Original_WY", "Old WY", 70),
                ("New_WX", "New WX", 70),
                ("New_WY", "New WY", 70),
                ("BinCode", "Bin Code", 65),
            ],
        )

        v_scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        self.results_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        export_frame = ttk.Frame(main_frame)
        export_frame.grid(row=5, column=0, columnspan=2, pady=(0, 10))

        ttk.Button(export_frame, text="Generate New XML", command=self.generate_new_xml).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(export_frame, text="Export Results to CSV", command=self.export_csv).pack(side=tk.LEFT)

        self.status_var = tk.StringVar(value="Ready - Load a wafer XML file to begin")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN).grid(
            row=6, column=0, columnspan=2, sticky=(tk.W, tk.E)
        )

    def setup_misalignment_tab(self):
        mis_frame = ttk.Frame(self.misalignment_tab, padding="10")
        mis_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.misalignment_tab.columnconfigure(0, weight=1)
        self.misalignment_tab.rowconfigure(0, weight=1)
        mis_frame.columnconfigure(1, weight=1)

        ttk.Label(
            mis_frame,
            text="If the wafer has misaligned, this app will account for and create a new XML.",
            wraplength=900,
        ).grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 20))

        prompt_frame = ttk.LabelFrame(mis_frame, text="Enter Misalignment Values", padding="10")
        prompt_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 15))
        prompt_frame.columnconfigure(1, weight=1)
        prompt_frame.columnconfigure(3, weight=1)

        ttk.Label(prompt_frame, text="Rows misaligned:").grid(row=0, column=0, sticky=tk.W, padx=(0, 8), pady=5)
        self.row_count_var = tk.StringVar()
        ttk.Entry(prompt_frame, textvariable=self.row_count_var, width=10).grid(
            row=0, column=1, sticky=tk.W, padx=(0, 15), pady=5
        )

        ttk.Label(prompt_frame, text="Row direction:").grid(row=0, column=2, sticky=tk.W, padx=(0, 8), pady=5)
        self.row_direction_var = tk.StringVar(value="UP")
        ttk.Combobox(
            prompt_frame, textvariable=self.row_direction_var, values=["UP", "DOWN"], state="readonly", width=10
        ).grid(row=0, column=3, sticky=tk.W, pady=5)

        ttk.Label(prompt_frame, text="Columns misaligned:").grid(row=1, column=0, sticky=tk.W, padx=(0, 8), pady=5)
        self.column_count_var = tk.StringVar()
        ttk.Entry(prompt_frame, textvariable=self.column_count_var, width=10).grid(
            row=1, column=1, sticky=tk.W, padx=(0, 15), pady=5
        )

        ttk.Label(prompt_frame, text="Column direction:").grid(row=1, column=2, sticky=tk.W, padx=(0, 8), pady=5)
        self.column_direction_var = tk.StringVar(value="RIGHT")
        ttk.Combobox(
            prompt_frame, textvariable=self.column_direction_var, values=["RIGHT", "LEFT"], state="readonly", width=10
        ).grid(row=1, column=3, sticky=tk.W, pady=5)

        button_frame = ttk.Frame(mis_frame)
        button_frame.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(0, 20))

        ttk.Button(
            button_frame,
            text="Process Misalignment Coordinates",
            command=self.process_misalignment_coordinates
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            button_frame,
            text="Save Misalignment Corrected XML",
            command=self.save_misalignment_corrected_xml
        ).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(
            button_frame,
            text="Save Unused Good Coordinates XML",
            command=self.save_unused_good_coordinates_xml
        ).pack(side=tk.LEFT)

        preview_frame = ttk.LabelFrame(mis_frame, text="Misalignment Preview", padding="5")
        preview_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        mis_frame.rowconfigure(3, weight=1)

        self.preview_tree = ttk.Treeview(
            preview_frame,
            columns=("TraySeq", "TX", "TY", "Old_WX", "Old_WY", "Corrected_WX", "Corrected_WY", "BinCode"),
            show="headings",
            height=10,
        )
        self.preview_tree.tag_configure("reject", background="#ff9999")
        self.preview_tree.tag_configure("edge", background="#cc99ff")
        self.preview_tree.tag_configure("bin0", background="#fff2a8")

        self._setup_tree_columns(
            self.preview_tree,
            [
                ("TraySeq", "Tray Seq", 80),
                ("TX", "TX", 50),
                ("TY", "TY", 50),
                ("Old_WX", "Old WX", 70),
                ("Old_WY", "Old WY", 70),
                ("Corrected_WX", "Corrected WX", 90),
                ("Corrected_WY", "Corrected WY", 90),
                ("BinCode", "Bin Code", 65),
            ],
        )

        pv_v_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_tree.yview)
        pv_h_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.preview_tree.xview)
        self.preview_tree.configure(yscrollcommand=pv_v_scrollbar.set, xscrollcommand=pv_h_scrollbar.set)

        self.preview_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        pv_v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        pv_h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))

        unused_frame = ttk.LabelFrame(mis_frame, text="Unused Good Coordinates", padding="5")
        unused_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        unused_frame.columnconfigure(0, weight=1)
        unused_frame.rowconfigure(0, weight=1)
        mis_frame.rowconfigure(4, weight=1)

        self.unused_tree = ttk.Treeview(
            unused_frame,
            columns=("TraySeq", "TX", "TY", "WX", "WY"),
            show="headings",
            height=6,
        )
        self.unused_tree.tag_configure("unused", background="#e8f5e9")

        self._setup_tree_columns(
            self.unused_tree,
            [
                ("TraySeq", "Tray Seq", 80),
                ("TX", "TX", 50),
                ("TY", "TY", 50),
                ("WX", "WX", 70),
                ("WY", "WY", 70),
            ],
        )

        u_v_scrollbar = ttk.Scrollbar(unused_frame, orient=tk.VERTICAL, command=self.unused_tree.yview)
        self.unused_tree.configure(yscrollcommand=u_v_scrollbar.set)

        self.unused_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        u_v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

    # -------------------------
    # Helpers
    # -------------------------
    def _setup_tree_columns(self, tree, columns):
        for col, heading, width in columns:
            tree.heading(col, text=heading, command=lambda c=col: self._sort_treeview(tree, c, False))
            tree.column(col, width=width, anchor="center")

    def _sort_treeview(self, tree, col, reverse):
        items = []
        for child in tree.get_children(""):
            value = tree.set(child, col)
            try:
                sort_value = int(value)
            except (ValueError, TypeError):
                sort_value = value
            items.append((sort_value, child))
        items.sort(key=lambda x: x[0], reverse=reverse)
        for index, (_, child) in enumerate(items):
            tree.move(child, "", index)
        tree.heading(col, command=lambda: self._sort_treeview(tree, col, not reverse))

    def _is_valid_int(self, value):
        try:
            int(value)
            return True
        except (ValueError, TypeError):
            return False

    def _get_unit_data_elements(self, root):
        return root.findall(".//UnitData") + root.findall(".//{*}UnitData")

    def _clone_root(self, root):
        return ET.fromstring(ET.tostring(root))

    def _serialize_xml(self, root_element):
        return ET.tostring(root_element, encoding="unicode")

    def _get_corrected_coordinates(self, wx, wy, row_count, row_direction, column_count, column_direction):
        corrected_wx = wx
        corrected_wy = wy

        if row_direction == "UP":
            corrected_wy += row_count
        elif row_direction == "DOWN":
            corrected_wy -= row_count

        if column_direction == "RIGHT":
            corrected_wx -= column_count
        elif column_direction == "LEFT":
            corrected_wx += column_count

        return corrected_wx, corrected_wy

    def _clear_tree(self, tree):
        for item in tree.get_children():
            tree.delete(item)

    def _sequence_sort_key(self, seq):
        return int(seq) if str(seq).isdigit() else str(seq)

    # -------------------------
    # Main tab actions
    # -------------------------
    def add_reject_die(self):
        wx = self.reject_wx_var.get().strip()
        wy = self.reject_wy_var.get().strip()

        if not self._is_valid_int(wx) or not self._is_valid_int(wy):
            messagebox.showerror("Error", "Reject die WX and WY must be integers.")
            return

        pair = (int(wx), int(wy))
        if pair in self.reject_die_data:
            messagebox.showwarning("Warning", "This reject die already exists.")
            return

        self.reject_die_data.append(pair)
        self.reject_tree.insert("", "end", values=pair)
        self.reject_wx_var.set("")
        self.reject_wy_var.set("")

    def delete_reject_die(self):
        selected = self.reject_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a reject die to delete.")
            return

        for item in selected:
            values = self.reject_tree.item(item, "values")
            if values:
                pair = (int(values[0]), int(values[1]))
                if pair in self.reject_die_data:
                    self.reject_die_data.remove(pair)
            self.reject_tree.delete(item)

    def browse_wafer_xml(self):
        filename = filedialog.askopenfilename(
            title="Select Wafer XML File",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if filename:
            self.wafer_xml_path = filename
            self.wafer_xml_var.set(os.path.basename(filename))
            self.load_wafer_xml()

    def load_wafer_xml(self):
        try:
            self.xml_tree = ET.parse(self.wafer_xml_path)
            root = self.xml_tree.getroot()

            wtt_ref_elements = root.findall(".//WTTReference") + root.findall(".//{*}WTTReference")
            if not wtt_ref_elements:
                messagebox.showerror("Error", "WTTReference element not found in XML")
                return

            wtt_ref = wtt_ref_elements[0]
            self.x_offset = int(wtt_ref.get("X", 0))
            self.y_offset = int(wtt_ref.get("Y", 0)) - 1

            self.x_offset_var.set(str(self.x_offset))
            self.y_offset_var.set(str(self.y_offset))

            unit_data_elements = self._get_unit_data_elements(root)
            coord_count = len([e for e in unit_data_elements if e.get("WX") and e.get("WY")])

            self.status_var.set(
                f"Loaded XML: Found WTTReference (X={self.x_offset}, Y={self.y_offset + 1}), {coord_count} coordinate entries"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load wafer XML: {str(e)}")
            self.status_var.set("Error loading wafer XML")

    def process_coordinates(self):
        if not self.xml_tree:
            messagebox.showwarning("Warning", "Please load a wafer XML file first")
            return

        self._clear_tree(self.results_tree)
        self.coordinate_data = []
        self.reject_coordinates = set()

        root = self.xml_tree.getroot()
        unit_data_elements = self._get_unit_data_elements(root)
        reject_set = set(self.reject_die_data)

        processed_count = 0
        for unit_elem in unit_data_elements:
            wx_str = unit_elem.get("WX")
            wy_str = unit_elem.get("WY")
            if wx_str is None or wy_str is None:
                continue

            try:
                old_wx = int(wx_str)
                old_wy = int(wy_str)
                tx = int(unit_elem.get("TX", 0))
                ty = int(unit_elem.get("TY", 0))
                tray_seq = unit_elem.get("TraySequence", "")
                old_bin = int(unit_elem.get("BinCode")) if self._is_valid_int(unit_elem.get("BinCode")) else None

                new_wx = (old_wx + self.x_offset) * -1
                new_wy = (old_wy + self.y_offset) * -1

                is_reject = (old_wx, old_wy) in reject_set
                new_bin = 88 if is_reject else (old_bin if old_bin is not None else 1)

                if is_reject:
                    self.reject_coordinates.add((new_wx, new_wy))

                coord_data = {
                    "element": unit_elem,
                    "tx": tx,
                    "ty": ty,
                    "tray_seq": tray_seq,
                    "old_wx": old_wx,
                    "old_wy": old_wy,
                    "new_wx": new_wx,
                    "new_wy": new_wy,
                    "old_bin": old_bin,
                    "new_bin": new_bin,
                    "is_reject": is_reject,
                }
                self.coordinate_data.append(coord_data)

                tags = ("reject",) if is_reject else ()
                self.results_tree.insert(
                    "", "end",
                    values=(tray_seq, tx, ty, old_wx, old_wy, new_wx, new_wy, new_bin),
                    tags=tags
                )
                processed_count += 1
            except (ValueError, TypeError):
                continue

        self.status_var.set(f"Processed {processed_count} coordinates using offsets (X={self.x_offset}, Y={self.y_offset})")

    def generate_new_xml(self):
        if not self.coordinate_data:
            messagebox.showwarning("Warning", "No coordinate data to process. Please process coordinates first.")
            return

        filename = filedialog.asksaveasfilename(
            title="Save New Wafer XML",
            defaultextension=".xml",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if not filename:
            return

        try:
            new_root = self._clone_root(self.xml_tree.getroot())
            unit_data_elements = self._get_unit_data_elements(new_root)
            coord_lookup = {(c["old_wx"], c["old_wy"]): c for c in self.coordinate_data}

            for unit_elem in unit_data_elements:
                wx_str = unit_elem.get("WX")
                wy_str = unit_elem.get("WY")
                if wx_str is None or wy_str is None:
                    continue

                try:
                    old_wx = int(wx_str)
                    old_wy = int(wy_str)
                except ValueError:
                    continue

                coord_data = coord_lookup.get((old_wx, old_wy))
                if not coord_data:
                    continue

                unit_elem.set("WX", str(coord_data["new_wx"]))
                unit_elem.set("WY", str(coord_data["new_wy"]))
                unit_elem.set("BinCode", "88" if coord_data["is_reject"] else "1")

            with open(filename, "w", encoding="utf-8") as f:
                f.write(self._serialize_xml(new_root))

            self.tray_xml_tree = ET.ElementTree(new_root)
            self.tray_xml_path = filename

            messagebox.showinfo("Success", f"New XML file generated successfully:\n{filename}")
            self.status_var.set(f"Generated new XML: {os.path.basename(filename)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate new XML: {str(e)}")

    def export_csv(self):
        if not self.coordinate_data:
            messagebox.showwarning("Warning", "No coordinate data to export")
            return

        filename = filedialog.asksaveasfilename(
            title="Export Coordinate Results",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if not filename:
            return

        try:
            import pandas as pd

            csv_data = [
                {
                    "TraySequence": coord["tray_seq"],
                    "TX": coord["tx"],
                    "TY": coord["ty"],
                    "Original_WX": coord["old_wx"],
                    "Original_WY": coord["old_wy"],
                    "New_WX": coord["new_wx"],
                    "New_WY": coord["new_wy"],
                    "BinCode": coord["new_bin"],
                    "Is_Reject_Die": coord["is_reject"],
                }
                for coord in self.coordinate_data
            ]

            pd.DataFrame(csv_data).to_csv(filename, index=False)
            messagebox.showinfo("Success", f"Results exported to {filename}")
            self.status_var.set(f"Exported results: {os.path.basename(filename)}")
        except ImportError:
            messagebox.showerror("Error", "pandas library required for CSV export")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export CSV: {str(e)}")

    # -------------------------
    # Misalignment tab actions
    # -------------------------
    def process_misalignment_coordinates(self):
        if self.tray_xml_tree is None:
            messagebox.showwarning(
                "Warning",
                "Please generate the wafer-to-tray XML first before applying misalignment correction."
            )
            return

        row_count = self.row_count_var.get().strip()
        column_count = self.column_count_var.get().strip()
        row_direction = self.row_direction_var.get()
        column_direction = self.column_direction_var.get()

        if not self._is_valid_int(row_count) or not self._is_valid_int(column_count):
            messagebox.showerror("Error", "Please enter valid integers for rows and columns.")
            return

        row_count = int(row_count)
        column_count = int(column_count)

        try:
            new_tree = ET.ElementTree(self._clone_root(self.tray_xml_tree.getroot()))
            root = new_tree.getroot()
            unit_data_elements = self._get_unit_data_elements(root)

            self.misalignment_data = []
            old_coord_set = set()
            temp_rows = []

            for unit_elem in unit_data_elements:
                wx_str = unit_elem.get("WX")
                wy_str = unit_elem.get("WY")
                if wx_str is None or wy_str is None:
                    continue

                try:
                    original_wx = int(wx_str)
                    original_wy = int(wy_str)
                    tx = int(unit_elem.get("TX", 0))
                    ty = int(unit_elem.get("TY", 0))
                    tray_seq = unit_elem.get("TraySequence", "")

                    corrected_wx, corrected_wy = self._get_corrected_coordinates(
                        original_wx, original_wy, row_count, row_direction, column_count, column_direction
                    )

                    old_coord_set.add((original_wx, original_wy))
                    temp_rows.append({
                        "tray_seq": tray_seq,
                        "tx": tx,
                        "ty": ty,
                        "old_wx": original_wx,
                        "old_wy": original_wy,
                        "corrected_wx": corrected_wx,
                        "corrected_wy": corrected_wy,
                        "bin_code": 1,
                        "is_edge": False,
                        "is_bin0": False,
                    })
                except ValueError:
                    continue

            reject_coords = self.reject_coordinates
            corrected_positions = {(r["corrected_wx"], r["corrected_wy"]) for r in temp_rows}

            self.unused_good_coordinates = []
            for row in temp_rows:
                if (row["corrected_wx"], row["corrected_wy"]) in reject_coords:
                    row["bin_code"] = 0
                    row["is_bin0"] = True
                elif (row["corrected_wx"], row["corrected_wy"]) not in old_coord_set:
                    row["bin_code"] = "EDGE DIE"
                    row["is_edge"] = True
                else:
                    row["bin_code"] = 1

                if row["bin_code"] == 1 and (row["old_wx"], row["old_wy"]) not in corrected_positions:
                    self.unused_good_coordinates.append({
                        "tray_seq": row["tray_seq"],
                        "tx": row["tx"],
                        "ty": row["ty"],
                        "wx": row["old_wx"],
                        "wy": row["old_wy"],
                    })

                self.misalignment_data.append(row)

            self._refresh_unused_good_tree()

            self._clear_tree(self.preview_tree)
            for row in self.misalignment_data:
                tags = ()
                if row["is_edge"]:
                    tags = ("edge",)
                elif row["is_bin0"]:
                    tags = ("bin0",)

                self.preview_tree.insert(
                    "", "end",
                    values=(
                        row["tray_seq"],
                        row["tx"],
                        row["ty"],
                        row["old_wx"],
                        row["old_wy"],
                        row["corrected_wx"],
                        row["corrected_wy"],
                        row["bin_code"],
                    ),
                    tags=tags,
                )

            self.misalignment_processed = True
            messagebox.showinfo("Success", "Misalignment correction processed. You can now save the XML file.")
            self.status_var.set("Misalignment processed - ready to save corrected XML")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process misalignment coordinates: {str(e)}")

    def _refresh_unused_good_tree(self):
        self._clear_tree(self.unused_tree)
        for row in self.unused_good_coordinates:
            self.unused_tree.insert(
                "", "end",
                values=(row["tray_seq"], row["tx"], row["ty"], row["wx"], row["wy"]),
                tags=("unused",)
            )

    def save_unused_good_coordinates_xml(self):
        if not self.unused_good_coordinates:
            messagebox.showwarning("Warning", "No unused good coordinates available to save.")
            return

        filename = filedialog.asksaveasfilename(
            title="Save Unused Good Coordinates XML",
            defaultextension=".xml",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if not filename:
            return

        self._save_unused_good_coordinates_xml(filename)
        messagebox.showinfo("Success", f"Unused good coordinates XML saved successfully:\n{filename}")

    def save_misalignment_corrected_xml(self):
        if not self.misalignment_processed:
            messagebox.showwarning("Warning", "Please process misalignment coordinates first before saving the XML file.")
            return
        if self.tray_xml_tree is None:
            messagebox.showwarning("Warning", "No tray XML available. Please generate the wafer-to-tray XML first.")
            return

        filename = filedialog.asksaveasfilename(
            title="Save Misalignment Corrected XML",
            defaultextension=".xml",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if not filename:
            return

        try:
            new_root = self._clone_root(self.tray_xml_tree.getroot())
            row_count = int(self.row_count_var.get().strip())
            column_count = int(self.column_count_var.get().strip())
            row_direction = self.row_direction_var.get()
            column_direction = self.column_direction_var.get()

            corrected_lookup = {}
            old_coord_set = set()

            for unit_elem in self._get_unit_data_elements(new_root):
                wx_str = unit_elem.get("WX")
                wy_str = unit_elem.get("WY")
                if wx_str is None or wy_str is None:
                    continue

                try:
                    original_wx = int(wx_str)
                    original_wy = int(wy_str)
                except ValueError:
                    continue

                corrected_wx, corrected_wy = self._get_corrected_coordinates(
                    original_wx, original_wy, row_count, row_direction, column_count, column_direction
                )

                old_coord_set.add((original_wx, original_wy))
                corrected_lookup[(original_wx, original_wy)] = {
                    "TX": unit_elem.get("TX", "0"),
                    "TY": unit_elem.get("TY", "0"),
                    "TraySequence": unit_elem.get("TraySequence", ""),
                    "WX": corrected_wx,
                    "WY": corrected_wy,
                }

            reject_coords = self.reject_coordinates

            def remove_unitdata_nodes(elem):
                for child in list(elem):
                    if child.tag.endswith("UnitData"):
                        elem.remove(child)
                    else:
                        remove_unitdata_nodes(child)

            remove_unitdata_nodes(new_root)

            sequence_map = {}
            for data in corrected_lookup.values():
                seq = data["TraySequence"] if data["TraySequence"] else "0"
                sequence_map.setdefault(seq, []).append(data)

            for seq, dies in sorted(sequence_map.items(), key=lambda x: self._sequence_sort_key(x[0])):
                new_root.append(ET.Comment(f"Sequence {seq}"))
                for die in dies:
                    corrected_xy = (die["WX"], die["WY"])
                    if corrected_xy in reject_coords:
                        bin_code = "0"
                        error_code = "REJECT"
                    elif corrected_xy not in old_coord_set:
                        bin_code = "EDGE DIE"
                        error_code = ""
                    else:
                        bin_code = "1"
                        error_code = ""

                    unit = ET.SubElement(new_root, f"{{{WTT_NS}}}UnitData")
                    unit.attrib = OrderedDict([
                        ("WX", str(die["WX"])),
                        ("WY", str(die["WY"])),
                        ("TX", str(die["TX"])),
                        ("TY", str(die["TY"])),
                        ("BinCode", bin_code),
                        ("ErrorCode", error_code),
                    ])

            with open(filename, "w", encoding="utf-8") as f:
                f.write(self._serialize_xml(new_root))

            messagebox.showinfo("Success", f"Misalignment-corrected XML saved successfully:\n{filename}")
            self.status_var.set(f"Misalignment corrected XML saved: {os.path.basename(filename)}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save misalignment corrected XML: {str(e)}")

    def _save_unused_good_coordinates_xml(self, filename):
        try:
            root = ET.Element(f"{{{WTT_NS}}}Wafer")
            root.append(ET.Comment("Unused Good Coordinates"))

            sequence_map = {}
            for row in self.unused_good_coordinates:
                seq = row.get("tray_seq", "")
                sequence_map.setdefault(seq, []).append(row)

            for seq, rows in sorted(sequence_map.items(), key=lambda x: self._sequence_sort_key(x[0])):
                root.append(ET.Comment(f"Sequence {seq}"))
                for row in rows:
                    unit = ET.SubElement(root, f"{{{WTT_NS}}}UnitData")
                    unit.attrib = OrderedDict([
                        ("WX", str(row["wx"])),
                        ("WY", str(row["wy"])),
                        ("TX", ""),
                        ("TY", ""),
                        ("BinCode", ""),
                        ("ErrorCode", ""),
                    ])

            with open(filename, "w", encoding="utf-8") as f:
                f.write(self._serialize_xml(root))

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save unused good coordinates XML: {str(e)}")


def main():
    root = tk.Tk()
    app = WaferXMLProcessor(root)
    root.mainloop()


if __name__ == "__main__":
    main()