import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

def resource_path(relative_path):
    """Exe veya script modunda logo dosyasının konumunu dinamik olarak bulur."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def init_db():
    """Veritabanını başlatır ve gerekli tabloyu oluşturur."""
    conn = sqlite3.connect("melek_events.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS musteriler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT, saat TEXT, musteri_adi TEXT, telefon TEXT, e_posta TEXT,
            etkinlik_yeri TEXT, konsept TEXT, katilimci_sayisi INTEGER,
            istenilen_malzemeler TEXT, ozel_notlar TEXT, teklif_tutari REAL,
            kapora REAL, kalan_bakiye REAL, odeme_durumu TEXT, sorumlu_personel TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class MelekEventsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MELEK EVENTS - Müşteri Takip Programı v2")
        self.geometry("1200x750")
        self.configure(bg="#f4f6f9")
        
        # Stil Yapılandırması
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background="#f4f6f9", font=("Segoe UI", 10))
        style.configure("TLabel", background="#f4f6f9", foreground="#333333")
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#2c3e50", background="#ffffff")
        style.configure("TButton", font=("Segoe UI", 10, "bold"), foreground="#ffffff", background="#2980b9", borderwidth=0)
        style.map("TButton", background=[("active", "#3498db")])
        style.configure("Delete.TButton", font=("Segoe UI", 10, "bold"), foreground="#ffffff", background="#c0392b", borderwidth=0)
        style.map("Delete.TButton", background=[("active", "#e74c3c")])
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=25, background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#e2e8f0", foreground="#2c3e50")

        # Üst Başlık ve Logo Alanı
        header_frame = tk.Frame(self, bg="#ffffff", height=80)
        header_frame.pack(fill="x", side="top", ipady=10)
        header_frame.pack_propagate(False)

        logo_path = resource_path("MELEK EVENTS LOGO.png")
        if os.path.exists(logo_path):
            try:
                self.logo_img = tk.PhotoImage(file=logo_path)
                self.logo_img = self.logo_img.subsample(4, 4)
                logo_label = tk.Label(header_frame, image=self.logo_img, bg="#ffffff")
                logo_label.pack(side="left", padx=20)
            except Exception as e:
                print(f"Logo yükleme hatası: {e}")

        title_label = ttk.Label(header_frame, text="MELEK EVENTS - MÜŞTERİ YÖNETİM SİSTEMİ", style="Header.TLabel")
        title_label.pack(side="left", padx=10, pady=15)

        # Sekme Yapısı
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=15)

        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.tab3 = ttk.Frame(self.notebook)

        self.notebook.add(self.tab1, text=" Müşteri Formu & Yönetimi ")
        self.notebook.add(self.tab2, text=" Ödeme Takibi ")
        self.notebook.add(self.tab3, text=" Organizasyon Takvimi ")

        self.create_musteri_tab()
        self.create_odeme_tab()
        self.create_takvim_tab()
        self.refresh_all()

    def create_musteri_tab(self):
        # Sol Panel: Veri Giriş Formu
        form_container = ttk.Frame(self.tab1)
        form_container.pack(side="left", fill="y", padx=10, pady=10)
        
        form_frame = ttk.LabelFrame(form_container, text=" Müşteri Organizasyon Formu ")
        form_frame.pack(fill="both", expand=True, padx=5, pady=5)

        fields = [
            ("Tarih (GG.AA.YYYY):", "tarih"),
            ("Saat (SS:DD):", "saat"),
            ("Müşteri Adı Soyadı:", "adi"),
            ("Telefon:", "tel"),
            ("E-Posta:", "mail"),
            ("Etkinlik Yeri:", "yer"),
            ("Konsept:", "konsept"),
            ("Katılımcı Sayısı:", "katilimci"),
            ("İstenilen Malzemeler:", "malzeme"),
            ("Özel Notlar:", "not"),
            ("Teklif Tutarı (TL):", "teklif"),
            ("Kapora (TL):", "kapora"),
            ("Sorumlu Personel:", "personel")
        ]

        self.entries = {}
        for i, (label_text, field_name) in enumerate(fields):
            ttk.Label(form_frame, text=label_text).grid(row=i, column=0, sticky="w", padx=10, pady=3)
            entry = ttk.Entry(form_frame, width=28)
            entry.grid(row=i, column=1, padx=10, pady=3)
            self.entries[field_name] = entry

        save_btn = ttk.Button(form_frame, text="YENİ KAYIT EKLE", command=self.save_musteri, padding=5)
        save_btn.grid(row=len(fields), column=0, columnspan=2, pady=10, padx=10, sticky="we")

        # Sağ Panel: Tablo ve Silme Butonu
        list_frame = ttk.LabelFrame(self.tab1, text=" Müşteri Takip Listesi ")
        list_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        cols = ("ID", "Tarih", "Müşteri", "Telefon", "Organizasyon", "Teklif", "Kapora", "Bakiye", "Durum")
        self.tree_musteri = ttk.Treeview(list_frame, columns=cols, show="headings")
        
        widths = {"ID": 40, "Tarih": 90, "Müşteri": 130, "Telefon": 100, "Organizasyon": 110, "Teklif": 80, "Kapora": 80, "Bakiye": 80, "Durum": 90}
        for col in cols:
            self.tree_musteri.heading(col, text=col)
            self.tree_musteri.column(col, width=widths.get(col, 100), anchor="center" if col in ["ID", "Tarih", "Durum", "Telefon"] else "w")
            
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_musteri.yview)
        self.tree_musteri.configure(yscrollcommand=scrollbar.set)
        
        self.tree_musteri.pack(side="top", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y", before=self.tree_musteri) # Scroll düzgün yerleşim

        # Seçili Kaydı Silme Butonu
        delete_btn = ttk.Button(list_frame, text="SEÇİLİ MÜŞTERİ KAYDINI SİL", style="Delete.TButton", command=self.delete_musteri, padding=8)
        delete_btn.pack(side="bottom", fill="x", padx=10, pady=10)

    def create_odeme_tab(self):
        cols = ("Müşteri", "Toplam Tutar", "Ödenen (Kapora)", "Kalan Bakiye", "Son Ödeme Tarihi", "Durum")
        self.tree_odeme = ttk.Treeview(self.tab2, columns=cols, show="headings")
        for col in cols:
            self.tree_odeme.heading(col, text=col)
            self.tree_odeme.column(col, anchor="center" if "Tarih" in col or "Durum" in col else "w", width=150)
        self.tree_odeme.pack(fill="both", expand=True, padx=15, pady=15)

    def create_takvim_tab(self):
        cols = ("Tarih", "Saat", "Müşteri", "Lokasyon", "Konsept", "Personel")
        self.tree_takvim = ttk.Treeview(self.tab3, columns=cols, show="headings")
        for col in cols:
            self.tree_takvim.heading(col, text=col)
            self.tree_takvim.column(col, anchor="center" if col in ["Tarih", "Saat"] else "w", width=150)
        self.tree_takvim.pack(fill="both", expand=True, padx=15, pady=15)

    def save_musteri(self):
        try:
            teklif = float(self.entries["teklif"].get() or 0)
            kapora = float(self.entries["kapora"].get() or 0)
            kalan = teklif - kapora
            durum = "Ödendi" if kalan <= 0 else "Bakiye Var"
            
            conn = sqlite3.connect("melek_events.db")
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO musteriler (tarih, saat, musteri_adi, telefon, e_posta, etkinlik_yeri, konsept, katilimci_sayisi, istenilen_malzemeler, ozel_notlar, teklif_tutari, kapora, kalan_bakiye, odeme_durumu, sorumlu_personel)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.entries["tarih"].get(), self.entries["saat"].get(), self.entries["adi"].get(),
                self.entries["tel"].get(), self.entries["mail"].get(), self.entries["yer"].get(),
                self.entries["konsept"].get(), self.entries["katilimci"].get(), self.entries["malzeme"].get(),
                self.entries["not"].get(), teklif, kapora, kalan, durum, self.entries["personel"].get()
            ))
            conn.commit()
            conn.close()
            messagebox.showinfo("Başarılı", "Kayıt eklendi!")
            self.refresh_all()
            
            for entry in self.entries.values():
                entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Hata", f"Kayıt eklenemedi: {e}")

    def delete_musteri(self):
        """Tablodan seçilen müşteriyi veritabanından tamamen siler ve arayüzü günceller."""
        selected_item = self.tree_musteri.selection()
        if not selected_item:
            messagebox.showwarning("Seçim Yapılmadı", "Lütfen silmek istediğiniz müşteri kaydını tablodan seçin.")
            return
        
        # Seçili satırın değerlerini al (ID ilk sütunda)
        item_values = self.tree_musteri.item(selected_item, "values")
        record_id = item_values[0]
        musteri_adi = item_values[2]
        
        # Silme onayı iste
        onay = messagebox.askyesno("Kayıt Silme Onayı", f"'{musteri_adi}' isimli müşteriye ait TÜM kayıtlar (Ödeme ve Takvim dahil) kalıcı olarak silinecektir.\n\nDevam etmek istiyor musunuz?")
        
        if onay:
            try:
                conn = sqlite3.connect("melek_events.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM musteriler WHERE id = ?", (record_id,))
                conn.commit()
                conn.close()
                
                messagebox.showinfo("Başarılı", "Müşteri kaydı sistemden kalıcı olarak silindi.")
                self.refresh_all()
            except Exception as e:
                messagebox.showerror("Hata", f"Kayıt silinirken bir hata oluştu: {e}")

    def refresh_all(self):
        for tree in [self.tree_musteri, self.tree_odeme, self.tree_takvim]:
            for row in tree.get_children():
                tree.delete(row)

        conn = sqlite3.connect("melek_events.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM musteriler ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()

        for r in rows:
            self.tree_musteri.insert("", "end", values=(r[0], r[1], r[3], r[4], r[7], f"{r[11]:,.2f} TL", f"{r[12]:,.2f} TL", f"{r[13]:,.2f} TL", r[14]))
            self.tree_odeme.insert("", "end", values=(r[3], f"{r[11]:,.2f} TL", f"{r[12]:,.2f} TL", f"{r[13]:,.2f} TL", r[1], r[14]))
            self.tree_takvim.insert("", "end", values=(r[1], r[2], r[3], r[6], r[7], r[15]))

if __name__ == "__main__":
    app = MelekEventsApp()
    app.mainloop()
