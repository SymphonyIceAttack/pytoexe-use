import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import xml.etree.ElementTree as ET
import os
from PIL import Image, ImageTk

class MonsterSpotEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("SSEmu Monster Spot Editor")
        self.root.geometry("1250x750")

        self.xml_path = None
        self.tree_xml = None
        self.root_xml = None

        self.current_map_image = None
        self.monsters = {}  # id -> name
        self.selected_item = None

        self.create_ui()

    # ================= UI =================
    def create_ui(self):
        top = tk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=5)

        tk.Button(top, text="Open XML", command=self.load_xml).pack(side="left", padx=5)
        tk.Button(top, text="Save XML", command=self.save_xml).pack(side="left", padx=5)
        tk.Button(top, text="Load Monsters", command=self.load_monster_definitions).pack(side="left", padx=5)
        tk.Button(top, text="Add Spot", command=self.add_spot).pack(side="left", padx=5)
        tk.Button(top, text="Delete Spot", command=self.delete_spot).pack(side="left", padx=5)

        mid = tk.Frame(self.root)
        mid.pack(fill="both", expand=True)

        columns = ("Map","Monster","X","Y","Range","Count","Dir")
        self.table = ttk.Treeview(mid, columns=columns, show="headings")

        for c in columns:
            self.table.heading(c, text=c)
            self.table.column(c, width=110)

        self.table.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        self.table.bind("<<TreeviewSelect>>", self.on_select)
        self.table.bind("<Double-1>", self.edit_cell)

        right = tk.Frame(mid)
        right.pack(side="right", fill="both", expand=False)

        self.map_canvas = tk.Canvas(right, width=512, height=512, bg="black")
        self.map_canvas.pack(padx=5, pady=5)

        self.map_canvas.bind("<Button-1>", self.on_map_click)

    # ================= MONSTERS =================
    def load_monster_definitions(self):
        path = filedialog.askopenfilename(filetypes=[("XML", "*.xml")])
        if not path:
            return

        try:
            tree = ET.parse(path)
            root = tree.getroot()

            self.monsters.clear()

            for m in root.findall(".//Monster"):
                mid = m.attrib.get("ID") or m.attrib.get("MonsterClass")
                name = m.attrib.get("Name", "Unknown")

                if mid is not None:
                    try:
                        self.monsters[int(mid)] = name
                    except ValueError:
                        continue

            messagebox.showinfo("OK", f"Loaded {len(self.monsters)} monsters")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= MAP =================
    def load_map_image(self, map_id):
        folder = os.path.join(os.getcwd(), "Maps")

        self.map_canvas.delete("all")

        for ext in ["png","jpg","bmp"]:
            p = os.path.join(folder, f"{map_id}.{ext}")
            if os.path.exists(p):
                img = Image.open(p).resize((512,512))
                self.current_map_image = ImageTk.PhotoImage(img)

                self.map_canvas.create_image(0,0,anchor="nw",image=self.current_map_image)
                self.draw_spawns(map_id)
                return

        self.map_canvas.create_text(256,256,text="Map not found",fill="white")

    def draw_spawns(self, map_id):
        self.map_canvas.delete("spawn")

        for item in self.table.get_children():
            v = self.table.item(item)["values"]
            if str(v[0]) != str(map_id):
                continue

            x = int(v[2])
            y = int(v[3])

            dx = int((x/255)*512)
            dy = int((y/255)*512)

            self.map_canvas.create_oval(dx-4,dy-4,dx+4,dy+4,fill="red",tags="spawn")

    # ================= CLICK MAP =================
    def on_map_click(self, event):
        if not self.table.selection():
            return

        item = self.table.selection()[0]
        vals = list(self.table.item(item)["values"])

        vals[2] = int((event.x/512)*255)
        vals[3] = int((event.y/512)*255)

        self.table.item(item, values=vals)
        self.load_map_image(vals[0])

    # ================= SELECT =================
    def on_select(self, event):
        sel = self.table.selection()
        if not sel:
            return

        v = self.table.item(sel[0])["values"]
        self.load_map_image(v[0])

    # ================= XML LOAD =================
    def load_xml(self):
        path = filedialog.askopenfilename(filetypes=[("XML","*.xml")])
        if not path:
            return

        self.tree_xml = ET.parse(path)
        self.root_xml = self.tree_xml.getroot()
        self.xml_path = path

        self.table.delete(*self.table.get_children())

        for m in self.root_xml.findall(".//Monster"):
            self.table.insert("","end",values=(
                m.attrib.get("Map","0"),
                m.attrib.get("MonsterClass","0"),
                m.attrib.get("SpawnX","0"),
                m.attrib.get("SpawnY","0"),
                m.attrib.get("Range","0"),
                m.attrib.get("Count","1"),
                m.attrib.get("Dir","0")
            ))

    # ================= SAVE =================
    def save_xml(self):
        if not self.root_xml:
            return

        parent = self.root_xml.find(".//MonsterList") or self.root_xml

        for i in list(parent):
            parent.remove(i)

        for i in self.table.get_children():
            v = self.table.item(i)["values"]

            m = ET.Element("Monster")
            m.set("Map",str(v[0]))
            m.set("MonsterClass",str(v[1]))
            m.set("SpawnX",str(v[2]))
            m.set("SpawnY",str(v[3]))
            m.set("Range",str(v[4]))
            m.set("Count",str(max(1,int(v[5]))))
            m.set("Dir",str(max(-1,min(9,int(v[6])))))

            parent.append(m)

        self.tree_xml.write(self.xml_path,encoding="utf-8",xml_declaration=True)
        messagebox.showinfo("OK","Saved")

    # ================= ADD =================
    def add_spot(self):
        self.table.insert("","end",values=(0,1,120,120,3,1,0))

    def delete_spot(self):
        for i in self.table.selection():
            self.table.delete(i)

    # ================= EDIT CELL =================
    def edit_cell(self, event):
        r = self.table.identify_row(event.y)
        c = self.table.identify_column(event.x)
        if not r or not c:
            return

        x,y,w,h = self.table.bbox(r,c)
        idx = int(c[1:]) - 1

        item = self.table.item(r)

        e = tk.Entry(self.table)
        e.place(x=x,y=y,width=w,height=h)
        e.insert(0,item["values"][idx])
        e.focus()

        def save(_=None):
            v = list(item["values"])
            v[idx] = e.get()
            self.table.item(r,values=v)
            e.destroy()

        e.bind("<Return>",save)
        e.bind("<FocusOut>",save)

if __name__ == "__main__":
    root = tk.Tk()
    app = MonsterSpotEditor(root)
    root.mainloop()
