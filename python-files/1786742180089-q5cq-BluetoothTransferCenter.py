import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading, asyncio, queue, time
from pathlib import Path

try:
    from bleak import BleakScanner, BleakClient
except ImportError:
    BleakScanner = None
    BleakClient = None

BATTERY_SERVICE = "0000180f-0000-1000-8000-00805f9b34fb"
BATTERY_LEVEL = "00002a19-0000-1000-8000-00805f9b34fb"

INFO_UUIDS = {
    "00002a29-0000-1000-8000-00805f9b34fb": "Manufacturer",
    "00002a24-0000-1000-8000-00805f9b34fb": "Model",
    "00002a25-0000-1000-8000-00805f9b34fb": "Serial",
    "00002a26-0000-1000-8000-00805f9b34fb": "Firmware",
    "00002a27-0000-1000-8000-00805f9b34fb": "Hardware",
    "00002a28-0000-1000-8000-00805f9b34fb": "Software",
}

def run(coro):
    return asyncio.run(coro)

def text(data):
    try:
        s = bytes(data).decode("utf-8", "replace").replace("\0", "").strip()
        return s or " ".join(f"{x:02X}" for x in data)
    except Exception:
        return " ".join(f"{x:02X}" for x in data)

def hexdata(data):
    return " ".join(f"{x:02X}" for x in data)

class Engine:
    def __init__(self, events):
        self.events = events
        self.client = None
        self.items = []

    def emit(self, kind, value=None):
        self.events.put((kind, value))

    def scan(self):
        threading.Thread(target=self._scan, daemon=True).start()

    def _scan(self):
        if not BleakScanner:
            self.emit("error", "Bleak is not installed. See the build instructions below.")
            return
        try:
            self.emit("status", "Scanning for BLE devices...")
            devices = run(BleakScanner.discover(timeout=6))
            result = []
            for d in devices:
                result.append({
                    "name": d.name or "Unknown device",
                    "address": d.address,
                    "rssi": getattr(d, "rssi", "?"),
                    "device": d
                })
            result.sort(key=lambda x: x["name"].lower())
            self.emit("scan", result)
            self.emit("status", f"Found {len(result)} BLE device(s).")
        except Exception as e:
            self.emit("error", f"Scan failed: {e}")

    def connect(self, item):
        threading.Thread(target=self._connect, args=(item,), daemon=True).start()

    def _connect(self, item):
        try:
            run(self._connect_async(item))
        except Exception as e:
            self.emit("error", f"Connection failed: {e}")

    async def _connect_async(self, item):
        self.emit("status", f"Connecting to {item['name']}...")
        self.client = BleakClient(item["device"])
        await self.client.connect()
        self.emit("connected", item)
        self.items = []
        for service in self.client.services:
            for c in service.characteristics:
                self.items.append({
                    "uuid": str(c.uuid),
                    "service": str(service.uuid),
                    "properties": list(c.properties),
                    "object": c
                })
        self.emit("services", self.items)

        try:
            s = self.client.services.get_service(BATTERY_SERVICE)
            c = s.get_characteristic(BATTERY_LEVEL) if s else None
            if c:
                v = await self.client.read_gatt_char(c)
                if v:
                    self.emit("battery", v[0])
                if "notify" in c.properties:
                    await self.client.start_notify(c, self._battery)
        except Exception:
            pass

        for item in self.items:
            u = item["uuid"].lower()
            if u in INFO_UUIDS and "read" in item["properties"]:
                try:
                    v = await self.client.read_gatt_char(item["object"])
                    self.emit("info", (INFO_UUIDS[u], text(v)))
                except Exception:
                    pass

        self.emit("status", f"Connected. {len(self.items)} characteristic(s) found.")

    def _battery(self, sender, data):
        if data:
            self.emit("battery", int(data[0]))

    def find(self, uuid):
        for x in self.items:
            if x["uuid"].lower() == uuid.lower():
                return x
        return None

    def read(self, uuid):
        threading.Thread(target=self._read, args=(uuid,), daemon=True).start()

    def _read(self, uuid):
        try:
            run(self._read_async(uuid))
        except Exception as e:
            self.emit("error", str(e))

    async def _read_async(self, uuid):
        x = self.find(uuid)
        if not x or "read" not in x["properties"]:
            raise RuntimeError("Characteristic is not readable.")
        v = await self.client.read_gatt_char(x["object"])
        self.emit("read", (uuid, bytes(v)))

    def write(self, uuid, data):
        threading.Thread(target=self._write, args=(uuid, data), daemon=True).start()

    def _write(self, uuid, data):
        try:
            run(self._write_async(uuid, data))
        except Exception as e:
            self.emit("error", str(e))

    async def _write_async(self, uuid, data):
        x = self.find(uuid)
        if not x:
            raise RuntimeError("Characteristic not found.")
        p = x["properties"]
        if "write" in p:
            await self.client.write_gatt_char(x["object"], data, response=True)
        elif "write-without-response" in p or "write_without_response" in p:
            await self.client.write_gatt_char(x["object"], data, response=False)
        else:
            raise RuntimeError("Characteristic is not writable.")
        self.emit("write", len(data))

    def notify(self, uuid, enable):
        threading.Thread(target=self._notify, args=(uuid, enable), daemon=True).start()

    def _notify(self, uuid, enable):
        try:
            run(self._notify_async(uuid, enable))
        except Exception as e:
            self.emit("error", str(e))

    async def _notify_async(self, uuid, enable):
        x = self.find(uuid)
        if not x:
            raise RuntimeError("Characteristic not found.")
        if enable:
            await self.client.start_notify(x["object"], self._notification)
        else:
            await self.client.stop_notify(x["object"])
        self.emit("notify", (uuid, enable))

    def _notification(self, sender, data):
        self.emit("notification", (str(sender), bytes(data)))

    def disconnect(self):
        threading.Thread(target=self._disconnect, daemon=True).start()

    def _disconnect(self):
        try:
            if self.client:
                run(self.client.disconnect())
            self.emit("disconnected")
        except Exception as e:
            self.emit("error", str(e))

class App:
    def __init__(self, root):
        self.root = root
        root.title("Bluetooth Transfer Center")
        root.geometry("1150x750")
        self.events = queue.Queue()
        self.engine = Engine(self.events)
        self.devices = []
        self.selected = None
        self.file = None
        self.running = True

        self.build()
        root.after(100, self.events_loop)
        root.protocol("WM_DELETE_WINDOW", self.close)

        self.log("Ready. Scan to find BLE devices.")
        if not BleakScanner:
            self.log("Bleak is missing. This source requires Python + Bleak.", "error")

    def build(self):
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text="Bluetooth Transfer Center", font=("Segoe UI", 20, "bold")).pack(side="left")
        self.status = tk.StringVar(value="Ready")
        ttk.Label(top, textvariable=self.status).pack(side="right")

        pane = ttk.PanedWindow(self.root, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=10, pady=10)

        left = ttk.Frame(pane, padding=8)
        right = ttk.Frame(pane, padding=8)
        pane.add(left, weight=1)
        pane.add(right, weight=3)

        ttk.Label(left, text="Devices", font=("Segoe UI", 13, "bold")).pack(anchor="w")
        b = ttk.Frame(left); b.pack(fill="x", pady=8)
        ttk.Button(b, text="Scan", command=self.engine.scan).pack(side="left")
        ttk.Button(b, text="Connect", command=self.connect).pack(side="left", padx=5)
        ttk.Button(b, text="Disconnect", command=self.engine.disconnect).pack(side="left")

        self.tree = ttk.Treeview(left, columns=("name","address","rssi"), show="headings")
        for c, h, w in [("name","Name",170),("address","Address",150),("rssi","RSSI",60)]:
            self.tree.heading(c, text=h); self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.select_device)

        ttk.Label(left, text="Details").pack(anchor="w", pady=(8,3))
        self.details = tk.Text(left, height=9, wrap="word")
        self.details.pack(fill="x")
        self.details.config(state="disabled")

        nb = ttk.Notebook(right); nb.pack(fill="both", expand=True)
        overview = ttk.Frame(nb, padding=10)
        gatt = ttk.Frame(nb, padding=10)
        transfer = ttk.Frame(nb, padding=10)
        events = ttk.Frame(nb, padding=10)
        nb.add(overview, text="Device")
        nb.add(gatt, text="GATT")
        nb.add(transfer, text="Transfer")
        nb.add(events, text="Events")

        self.conn = tk.StringVar(value="Disconnected")
        self.battery = tk.StringVar(value="Unknown")
        vars_ = {"Connection":self.conn, "Battery":self.battery}
        for name in ["Manufacturer","Model","Serial","Firmware","Hardware","Software"]:
            vars_[name] = tk.StringVar(value="Unknown")
        self.vars = vars_

        frame = ttk.Frame(overview); frame.pack(fill="x")
        for i,(name,var) in enumerate(vars_.items()):
            box=ttk.LabelFrame(frame,text=name,padding=10)
            box.grid(row=i//2,column=i%2,sticky="ew",padx=5,pady=5)
            ttk.Label(box,textvariable=var,font=("Segoe UI",11,"bold")).pack(anchor="w")
        frame.columnconfigure(0,weight=1); frame.columnconfigure(1,weight=1)

        ttk.Label(overview,text="Live notifications",font=("Segoe UI",12,"bold")).pack(anchor="w",pady=(12,4))
        self.notifications=tk.Text(overview,wrap="word")
        self.notifications.pack(fill="both",expand=True)
        self.notifications.config(state="disabled")

        self.char_tree=ttk.Treeview(gatt,columns=("service","uuid","props"),show="headings")
        for c,h,w in [("service","Service",260),("uuid","Characteristic",330),("props","Properties",240)]:
            self.char_tree.heading(c,text=h); self.char_tree.column(c,width=w)
        self.char_tree.pack(fill="both",expand=True)
        self.char_tree.bind("<<TreeviewSelect>>", self.select_char)

        gb=ttk.Frame(gatt); gb.pack(fill="x",pady=8)
        ttk.Button(gb,text="Read",command=self.read).pack(side="left",padx=3)
        ttk.Button(gb,text="Enable Notify",command=lambda:self.notify(True)).pack(side="left",padx=3)
        ttk.Button(gb,text="Disable Notify",command=lambda:self.notify(False)).pack(side="left",padx=3)

        ttk.Label(transfer,text="Characteristic UUID").pack(anchor="w")
        self.uuid=tk.StringVar()
        self.combo=ttk.Combobox(transfer,textvariable=self.uuid,state="readonly")
        self.combo.pack(fill="x",pady=5)

        ttk.Label(transfer,text="Payload").pack(anchor="w")
        self.payload=tk.Text(transfer,height=7); self.payload.pack(fill="x",pady=5)
        tb=ttk.Frame(transfer); tb.pack(fill="x")
        ttk.Button(tb,text="Send UTF-8",command=self.send_text).pack(side="left",padx=3)
        ttk.Button(tb,text="Send HEX",command=self.send_hex).pack(side="left",padx=3)

        ttk.Separator(transfer).pack(fill="x",pady=15)
        ttk.Button(transfer,text="Choose File",command=self.choose_file).pack(side="left",padx=3)
        ttk.Button(transfer,text="Send File",command=self.send_file).pack(side="left",padx=3)
        self.file_label=tk.StringVar(value="No file selected")
        ttk.Label(transfer,textvariable=self.file_label).pack(anchor="w",pady=8)
        self.progress=ttk.Progressbar(transfer,mode="determinate"); self.progress.pack(fill="x")
        self.progress_text=tk.StringVar(value="Idle")
        ttk.Label(transfer,textvariable=self.progress_text).pack()

        self.logbox=tk.Text(events,wrap="none"); self.logbox.pack(fill="both",expand=True)
        ttk.Button(events,text="Clear",command=lambda:self.logbox.delete("1.0","end")).pack(anchor="e",pady=5)

    def log(self,msg,level="info"):
        prefix={"success":"✓","error":"✕","warning":"!"}.get(level,"•")
        self.logbox.insert("end",f"[{time.strftime('%H:%M:%S')}] {prefix} {msg}\n")
        self.logbox.see("end")

    def select_device(self,_=None):
        s=self.tree.selection()
        if not s:return
        self.selected=self.devices[int(s[0])]
        d=self.selected
        self.details.config(state="normal"); self.details.delete("1.0","end")
        self.details.insert("end",f"Name: {d['name']}\nAddress/ID: {d['address']}\nRSSI: {d['rssi']}")
        self.details.config(state="disabled")

    def connect(self):
        if not self.selected:
            messagebox.showinfo("Bluetooth Transfer Center","Select a device first.")
            return
        self.engine.connect(self.selected)

    def select_char(self,_=None):
        s=self.char_tree.selection()
        if s:self.uuid.set(self.char_tree.item(s[0],"values")[1])

    def get_uuid(self):
        if not self.uuid.get():
            messagebox.showinfo("Bluetooth Transfer Center","Select a characteristic.")
            return None
        return self.uuid.get()

    def read(self):
        u=self.get_uuid()
        if u:self.engine.read(u)

    def notify(self,on):
        u=self.get_uuid()
        if u:self.engine.notify(u,on)

    def send_text(self):
        u=self.get_uuid()
        if u:self.engine.write(u,self.payload.get("1.0","end-1c").encode())

    def send_hex(self):
        u=self.get_uuid()
        if not u:return
        try:data=bytes.fromhex(self.payload.get("1.0","end-1c"))
        except ValueError:
            messagebox.showerror("Bluetooth Transfer Center","Invalid HEX.")
            return
        self.engine.write(u,data)

    def choose_file(self):
        p=filedialog.askopenfilename()
        if p:
            self.file=Path(p)
            self.file_label.set(str(self.file))

    def send_file(self):
        u=self.get_uuid()
        if not u or not self.file:return
        threading.Thread(target=self._file,args=(u,self.file),daemon=True).start()

    def _file(self,u,path):
        size=path.stat().st_size; sent=0; chunk=180
        try:
            with open(path,"rb") as f:
                while True:
                    d=f.read(chunk)
                    if not d:break
                    self.engine.write(u,d)
                    time.sleep(.03)
                    sent+=len(d)
                    pct=sent*100/size if size else 100
                    self.root.after(0,lambda p=pct:self.progress.configure(value=p))
                    self.root.after(0,lambda p=pct:self.progress_text.set(f"{p:.1f}%"))
            self.events.put(("status",f"File transfer finished: {path.name}"))
        except Exception as e:self.events.put(("error",f"File transfer failed: {e}"))

    def events_loop(self):
        try:
            while True:
                kind,data=self.events.get_nowait()
                if kind=="scan":
                    self.devices=data
                    for x in self.tree.get_children():self.tree.delete(x)
                    for i,d in enumerate(data):
                        self.tree.insert("", "end", iid=str(i), values=(d["name"],d["address"],d["rssi"]))
                elif kind=="connected":
                    self.conn.set("Connected")
                    self.log(f"Connected to {data['name']} ({data['address']})","success")
                elif kind=="disconnected":
                    self.conn.set("Disconnected"); self.log("Disconnected","warning")
                elif kind=="services":
                    for x in self.char_tree.get_children():self.char_tree.delete(x)
                    uuids=[]
                    for x in data:
                        self.char_tree.insert("", "end", values=(x["service"],x["uuid"],", ".join(x["properties"])))
                        uuids.append(x["uuid"])
                    self.combo["values"]=uuids
                elif kind=="battery":self.battery.set(f"{data}%")
                elif kind=="info":self.vars[data[0]].set(data[1])
                elif kind=="read":
                    self.log(f"READ {data[0]} | TEXT: {text(data[1])} | HEX: {hexdata(data[1])}","success")
                elif kind=="write":
                    self.log(f"WRITE accepted by Windows Bluetooth stack: {data} bytes. Device ACK is still required for receipt confirmation.","success")
                elif kind=="notify":
                    self.log(f"Notifications {'enabled' if data[1] else 'disabled'}: {data[0]}","success")
                elif kind=="notification":
                    self.notifications.config(state="normal")
                    self.notifications.insert("end",f"[{time.strftime('%H:%M:%S')}] {data[0]}\nTEXT: {text(data[1])}\nHEX: {hexdata(data[1])}\n\n")
                    self.notifications.see("end"); self.notifications.config(state="disabled")
                    self.log(f"NOTIFICATION received from {data[0]}","success")
                elif kind=="status":
                    self.status.set(data); self.log(data)
                elif kind=="error":
                    self.status.set("Error"); self.log(data,"error")
        except queue.Empty:pass
        if self.running:self.root.after(100,self.events_loop)

    def close(self):
        self.running=False
        try:self.engine.disconnect()
        except:pass
        self.root.destroy()

if __name__=="__main__":
    root=tk.Tk()
    App(root)
    root.mainloop()
