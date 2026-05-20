import os
import json
import shutil
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from lxml import etree

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
BASELINE_FILE = os.path.join(BASE_PATH, "baseline.json")


class GladiusEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Gladius Editor V7.2")
        self.root.geometry("1750x980")

        self.file_map = {}
        self.current_docs = []
        self.entry_map = []
        self.weapon_index = {}
        self.trait_index = {}
        self.lang_cache = {}
        self.baseline = {}

        self.vanilla_path = self.find_vanilla_path()

        self._build_ui()
        self.load_baseline()
        self.scan()

    # ---------------------------------------------------------
    # PATH
    # ---------------------------------------------------------
    def find_vanilla_path(self):
        current = BASE_PATH
        for _ in range(8):
            candidate = os.path.join(
                current,
                "steamapps",
                "common",
                "Warhammer 40000 Gladius - Relics of War",
                "Data",
                "World"
            )
            if os.path.exists(candidate):
                return candidate
            current = os.path.dirname(current)
        return None

    def get_all_roots(self):
        roots = []
        if self.vanilla_path:
            roots.append(("Оригинальная игра", self.vanilla_path))

        for d in os.listdir(BASE_PATH):
            full = os.path.join(BASE_PATH, d)
            if os.path.isdir(full):
                roots.append((d, full))
        return roots

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def _build_ui(self):
        top = ttk.Frame(self.root)
        top.pack(fill="x")

        ttk.Label(top, text="Поиск:").pack(side="left", padx=5)
        self.search_var = tk.StringVar()
        ttk.Entry(top, textvariable=self.search_var, width=40).pack(side="left", padx=5)
        ttk.Button(top, text="Поиск", command=self.scan).pack(side="left", padx=5)

        main = ttk.PanedWindow(self.root, orient="horizontal")
        main.pack(fill="both", expand=True)

        left = ttk.Frame(main)
        right = ttk.Frame(main)

        main.add(left, weight=1)
        main.add(right, weight=4)

        self.tree = ttk.Treeview(left)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.title = ttk.Label(right, text="Выберите юнита", font=("Arial", 14, "bold"))
        self.title.pack(anchor="w", padx=10, pady=5)

        self.canvas = tk.Canvas(right)
        self.canvas.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(right, orient="vertical", command=self.canvas.yview)
        sb.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=sb.set)

        self.editor = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.editor, anchor="nw")
        self.editor.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x")

        buttons = [
            ("Сохранить всё", self.save_all),
            ("Пересканировать", self.scan),
            ("Экспорт изменений", self.export_changes),
            ("Импорт изменений", self.import_changes),
            ("Откатить всё", self.restore_baseline),
            ("Обновить сброс", self.refresh_baseline)
        ]

        for text, cmd in buttons:
            ttk.Button(bottom, text=text, command=cmd).pack(side="left", padx=5, pady=5)

    # ---------------------------------------------------------
    # XML
    # ---------------------------------------------------------
    def parse(self, path):
        parser = etree.XMLParser(recover=True, remove_comments=False)
        return etree.parse(path, parser)

    # ---------------------------------------------------------
    # BASELINE
    # ---------------------------------------------------------
    def load_baseline(self):
        if os.path.exists(BASELINE_FILE):
            with open(BASELINE_FILE, "r", encoding="utf-8") as f:
                self.baseline = json.load(f)
        else:
            self.build_baseline()

    def build_baseline(self):
        self.baseline = {}
        for _, root_path in self.get_all_roots():
            for root_dir, _, files in os.walk(root_path):
                for f in files:
                    if not f.endswith(".xml"):
                        continue
                    path = os.path.join(root_dir, f)
                    try:
                        tree = self.parse(path)
                        values = {}
                        for elem in tree.xpath(".//*[@*]"):
                            for attr, val in elem.attrib.items():
                                key = f"{tree.getpath(elem)}|{attr}"
                                values[key] = val
                        self.baseline[path] = values
                    except:
                        pass

        with open(BASELINE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.baseline, f, ensure_ascii=False, indent=2)

    def refresh_baseline(self):
        if messagebox.askyesno("Подтверждение", "Обновить baseline?"):
            self.build_baseline()
            messagebox.showinfo("Готово", "baseline обновлён")

    # ---------------------------------------------------------
    # LANGUAGE
    # ---------------------------------------------------------
    def load_language(self, root_path):
        if not root_path:
            return {}

        if root_path in self.lang_cache:
            return self.lang_cache[root_path]

        result = {}
        base = root_path

        if base.endswith("Data\\World") or base.endswith("Data/World"):
            base = os.path.dirname(os.path.dirname(base))

        lang_root = os.path.join(base, "Data", "Core", "Languages")

        lang_dir = None
        for preferred in ["Russian", "English"]:
            candidate = os.path.join(lang_root, preferred)
            if os.path.exists(candidate):
                lang_dir = candidate
                break

        if not lang_dir:
            self.lang_cache[root_path] = {}
            return {}

        for f in os.listdir(lang_dir):
            if not f.endswith(".xml"):
                continue
            try:
                tree = self.parse(os.path.join(lang_dir, f))
                for e in tree.xpath(".//entry"):
                    name = e.attrib.get("name")
                    value = e.attrib.get("value")
                    if name and value:
                        result[name] = value
            except:
                pass

        self.lang_cache[root_path] = result
        return result

    def resolve_lang(self, key, lang, fallback):
        if not key:
            return fallback

        value = lang.get(key)
        if value:
            if "<string name=" in value:
                m = re.search(r"name=['\"](.+?)['\"]", value)
                if m:
                    nested = m.group(1)
                    nested_val = lang.get(nested)
                    if nested_val and "<string name=" not in nested_val:
                        return nested_val
            elif "<string name=" not in value:
                return value

        return fallback

    def get_display_name(self, path, lang):
        file_name = os.path.splitext(os.path.basename(path))[0]
        rel = path.replace("\\", "/")
        if "/Units/" in rel:
            key = rel.split("/Units/")[1].replace(".xml", "")
            return self.resolve_lang(key, lang, file_name)
        return file_name

    # ---------------------------------------------------------
    # SCAN
    # ---------------------------------------------------------
    def scan(self):
        self.tree.delete(*self.tree.get_children())
        self.file_map.clear()
        self.weapon_index.clear()
        self.trait_index.clear()

        search = self.search_var.get().lower().strip()

        for display_name, root_path in self.get_all_roots():
            mod_node = self.tree.insert("", "end", text=display_name)
            factions = {}
            lang = self.load_language(root_path)

            for root_dir, _, files in os.walk(root_path):
                for f in files:
                    if not f.endswith(".xml"):
                        continue

                    path = os.path.join(root_dir, f)

                    try:
                        tree = self.parse(path)
                        tag = tree.getroot().tag.lower()

                        file_key = os.path.splitext(f)[0]

                        if tag == "weapon":
                            self.weapon_index[file_key] = path
                            continue

                        if tag == "trait":
                            self.trait_index[file_key] = path
                            continue

                        if tag != "unit":
                            continue

                        shown_name = self.get_display_name(path, lang)

                        if search and search not in shown_name.lower():
                            continue

                        rel = path.replace("\\", "/")
                        parts = rel.split("/")

                        faction = "Unknown"
                        if "Units" in parts:
                            i = parts.index("Units")
                            if i + 1 < len(parts):
                                faction = parts[i + 1]

                        if faction not in factions:
                            factions[faction] = self.tree.insert(mod_node, "end", text=faction)

                        node = self.tree.insert(factions[faction], "end", text=shown_name)
                        self.file_map[node] = path

                    except:
                        pass

    # ---------------------------------------------------------
    # EDITOR
    # ---------------------------------------------------------
    def clear_editor(self):
        for w in self.editor.winfo_children():
            w.destroy()
        self.current_docs = []
        self.entry_map = []

    def add_section(self, title, elements, tree_index, descriptions=None):
        ttk.Label(
            self.editor,
            text=title,
            font=("Arial", 11, "bold")
        ).pack(anchor="w", padx=8, pady=(10, 4))

        descriptions = descriptions or {}

        for elem in elements:
            for attr, val in elem.attrib.items():
                frame = ttk.Frame(self.editor)
                frame.pack(fill="x", padx=10, pady=2)

                ttk.Label(frame, text=f"{elem.tag}.{attr}", width=45).pack(side="left")

                entry = tk.Entry(frame, width=40)
                entry.insert(0, val)
                entry.pack(side="left")

                self.entry_map.append((elem, attr, entry, tree_index))

            desc = descriptions.get(elem)
            if desc:
                ttk.Label(
                    self.editor,
                    text=desc,
                    foreground="gray",
                    wraplength=1200,
                    justify="left"
                ).pack(anchor="w", padx=50, pady=(0, 6))

    # ---------------------------------------------------------
    # SELECT
    # ---------------------------------------------------------
    def on_select(self, _):
        sel = self.tree.selection()
        if sel and sel[0] in self.file_map:
            self.load_unit(self.file_map[sel[0]])

    def load_unit(self, path):
        self.clear_editor()

        unit_tree = self.parse(path)
        unit_root = unit_tree.getroot()
        self.current_docs.append((unit_tree, path))

        lang = self.load_language(self.find_root_for_path(path))

        display_name = self.get_display_name(path, lang)
        file_name = os.path.splitext(os.path.basename(path))[0]

        self.title.config(text=f"{display_name} ({file_name})")

        # ----------------------------
        # 1. характеристики
        # ----------------------------
        stats = unit_root.xpath(".//modifiers/modifier/effects/*")
        self.add_section("Характеристики", stats, 0)

        # ----------------------------
        # 2. способности
        # ----------------------------
        for act in unit_root.xpath(".//actions/*"):
            if act.tag in ("attack", "move", "die", "levelUp", "shop"):
                continue

            if act.attrib.get("name", "").lower().endswith("/idle"):
                continue

            action_name = act.attrib.get("name", act.tag)
            short_name = action_name.split("/")[-1]

            display = self.resolve_lang(action_name, lang, short_name)
            desc = lang.get(action_name + "Description", "")

            idx = 0
            elems = [act]
            desc_map = {}

            tp = self.trait_index.get(short_name)
            if tp and os.path.exists(tp):
                t = self.parse(tp)
                self.current_docs.append((t, tp))
                idx = len(self.current_docs) - 1
                found = t.getroot().xpath(".//modifiers/modifier/effects/*")
                if found:
                    elems = found
                    for e in elems:
                        desc_map[e] = desc

            self.add_section(f"Способность: {display}", elems, idx, desc_map)

        # ----------------------------
        # 3. оружие (оба способа)
        # ----------------------------
        weapon_names = set()

        for w in unit_root.xpath(".//weapons/weapon"):
            name = w.attrib.get("name")
            if name and name != "None":
                weapon_names.add(name)

        for atk in unit_root.xpath(".//actions/attack"):
            name = atk.attrib.get("weapon")
            if name and name != "None":
                weapon_names.add(name)

        for weapon_name in sorted(weapon_names):
            short = weapon_name.split("/")[-1]
            wp = self.weapon_index.get(short)

            if not wp or not os.path.exists(wp):
                continue

            try:
                wtree = self.parse(wp)
                self.current_docs.append((wtree, wp))
                idx = len(self.current_docs) - 1

                wroot = wtree.getroot()
                elems = wroot.xpath(".//modifiers/modifier/effects/*")
                if not elems:
                    elems = [wroot]

                display = self.resolve_lang(weapon_name, lang, short)
                desc = lang.get(weapon_name + "Description", "")

                desc_map = {e: desc for e in elems}
                self.add_section(f"Оружие: {display}", elems, idx, desc_map)

            except:
                pass

    def find_root_for_path(self, path):
        for _, root in self.get_all_roots():
            if path.startswith(root):
                return root
        return None

    # ---------------------------------------------------------
    # SAVE
    # ---------------------------------------------------------
    def save_all(self):
        try:
            for _, path in self.current_docs:
                if os.path.exists(path):
                    shutil.copy2(path, path + ".bak")

            for elem, attr, entry, _ in self.entry_map:
                elem.attrib[attr] = entry.get()

            for tree, path in self.current_docs:
                tree.write(path, pretty_print=True, encoding="utf-8", xml_declaration=True)

            messagebox.showinfo("Успех", "Изменения сохранены")
            self.load_unit(self.current_docs[0][1])

        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    # ---------------------------------------------------------
    # EXPORT / IMPORT
    # ---------------------------------------------------------
    def export_changes(self):
        changes = {}
        for path, baseline_vals in self.baseline.items():
            if not os.path.exists(path):
                continue
            tree = self.parse(path)
            current = {}
            for elem in tree.xpath(".//*[@*]"):
                for attr, val in elem.attrib.items():
                    key = f"{tree.getpath(elem)}|{attr}"
                    current[key] = val
            diff = {k: v for k, v in current.items() if baseline_vals.get(k) != v}
            if diff:
                changes[path] = diff

        file = filedialog.asksaveasfilename(defaultextension=".json")
        if file:
            with open(file, "w", encoding="utf-8") as f:
                json.dump(changes, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Готово", "Изменения экспортированы")

    def import_changes(self):
        file = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not file:
            return

        with open(file, "r", encoding="utf-8") as f:
            changes = json.load(f)

        for path, vals in changes.items():
            if not os.path.exists(path):
                continue

            tree = self.parse(path)

            for key, val in vals.items():
                xpath, attr = key.split("|")
                elems = tree.xpath(xpath)
                if elems:
                    elems[0].attrib[attr] = val

            tree.write(path, pretty_print=True, encoding="utf-8", xml_declaration=True)

        self.scan()
        messagebox.showinfo("Готово", "Изменения импортированы")

    def restore_baseline(self):
        if not messagebox.askyesno("Подтверждение", "Откатить все изменения?"):
            return

        for path, vals in self.baseline.items():
            if not os.path.exists(path):
                continue

            tree = self.parse(path)

            for key, val in vals.items():
                xpath, attr = key.split("|")
                elems = tree.xpath(xpath)
                if elems:
                    elems[0].attrib[attr] = val

            tree.write(path, pretty_print=True, encoding="utf-8", xml_declaration=True)

        self.scan()
        messagebox.showinfo("Готово", "Все изменения откатены")


if __name__ == "__main__":
    root = tk.Tk()
    app = GladiusEditor(root)
    root.mainloop()