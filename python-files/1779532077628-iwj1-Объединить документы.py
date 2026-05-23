import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

class LinkComparerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Сравнение ссылок")
        self.file1_links = []
        self.file2_links = []

        # Окна текста
        self.text1 = ScrolledText(root, width=50, height=30)
        self.text2 = ScrolledText(root, width=50, height=30)
        self.text1.grid(row=0, column=0, padx=10, pady=10)
        self.text2.grid(row=0, column=1, padx=10, pady=10)

        # Статистика
        self.stats1 = tk.Label(root, text="", anchor="w", justify="left")
        self.stats2 = tk.Label(root, text="", anchor="w", justify="left")
        self.stats1.grid(row=1, column=0, padx=10, sticky="w")
        self.stats2.grid(row=1, column=1, padx=10, sticky="w")

        # Кнопки
        btn_frame = tk.Frame(root)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)

        tk.Button(btn_frame, text="Загрузить файл 1", command=self.load_file1).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Загрузить файл 2", command=self.load_file2).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Объединить и сохранить", command=self.merge_and_save).grid(row=0, column=2, padx=5)

        self.merged_info = tk.Label(root, text="", fg="blue", anchor="w", justify="left")
        self.merged_info.grid(row=3, column=0, columnspan=2, sticky="w", padx=10)

        # Настройка тегов подсветки
        self.text1.tag_config("common", background="lightgreen")
        self.text1.tag_config("unique", background="lightyellow")
        self.text2.tag_config("common", background="lightgreen")
        self.text2.tag_config("unique", background="lightyellow")

    def load_file1(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if path:
            with open(path, encoding="utf-8") as f:
                self.file1_links = [line.strip() for line in f if line.strip()]
            self.update_display()

    def load_file2(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if path:
            with open(path, encoding="utf-8") as f:
                self.file2_links = [line.strip() for line in f if line.strip()]
            self.update_display()

    def update_display(self):
        self.text1.delete(1.0, tk.END)
        self.text2.delete(1.0, tk.END)

        set1 = set(self.file1_links)
        set2 = set(self.file2_links)
        common = set1 & set2
        only1 = set1 - set2
        only2 = set2 - set1

        for link in self.file1_links:
            tag = "common" if link in common else "unique"
            self.text1.insert(tk.END, link + "\n", tag)

        for link in self.file2_links:
            tag = "common" if link in common else "unique"
            self.text2.insert(tk.END, link + "\n", tag)

        self.stats1.config(text=f"Файл 1:\nВсего: {len(self.file1_links)}\nСовпадений: {len(common)}\nУникальных: {len(only1)}")
        self.stats2.config(text=f"Файл 2:\nВсего: {len(self.file2_links)}\nСовпадений: {len(common)}\nУникальных: {len(only2)}")
        self.merged_info.config(text="")

    def merge_and_save(self):
        max_len = max(len(self.file1_links), len(self.file2_links))
        merged = []
        seen = set()

        for i in range(max_len):
            if i < len(self.file1_links):
                link1 = self.file1_links[i]
                if link1 not in seen:
                    merged.append(link1)
                    seen.add(link1)
            if i < len(self.file2_links):
                link2 = self.file2_links[i]
                if link2 not in seen:
                    merged.append(link2)
                    seen.add(link2)

        save_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                for link in merged:
                    f.write(link + "\n")
            messagebox.showinfo("Успех", "Объединённый файл успешно сохранён!")

        self.merged_info.config(text=f"Объединённый документ содержит {len(merged)} уникальных ссылок.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LinkComparerApp(root)
    root.mainloop()
