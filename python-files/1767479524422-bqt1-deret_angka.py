import tkinter as tk
from tkinter import messagebox
import requests

def prediksi_deret(angka_list):
    """
    Prediksi deret menggunakan berbagai pola:
    - Aritmatika
    - Geometri
    - Kuadrat / Kubik
    - Berselang / Berselang bertingkat
    - Pola CPNS Advanced
    """
    hasil = []

    # Pola 1: Aritmatika
    if len(angka_list) >= 2:
        selisih = angka_list[1] - angka_list[0]
        arit = angka_list[-1] + selisih
        hasil.append(('Aritmatika', arit, f'Selisih tetap {selisih}'))

    # Pola 2: Geometri
    if len(angka_list) >= 2 and angka_list[0] != 0:
        rasio = angka_list[1] / angka_list[0]
        geometri = round(angka_list[-1] * rasio)
        hasil.append(('Geometri', geometri, f'Rasio tetap {rasio:.3f}'))

    # Pola 3: Kuadrat bertingkat
    kuadrat = [x**0.5 if x>0 else 0 for x in angka_list]
    if all(int(x) == x for x in kuadrat):
        pred_kuadrat = int((angka_list[-1]**0.5 + 1)**2)
        hasil.append(('Kuadrat', pred_kuadrat, f'Bertingkat kuadrat'))

    # Pola 4: Kubik bertingkat
    kubik = [x**(1/3) if x>0 else 0 for x in angka_list]
    if all(round(x)**3 == y for x,y in zip(kubik, angka_list)):
        pred_kubik = round((kubik[-1]+1)**3)
        hasil.append(('Kubik', pred_kubik, 'Bertingkat kubik'))

    # Pola 5: Berselang sederhana
    if len(angka_list) >= 4:
        selisih1 = angka_list[1]-angka_list[0]
        selisih2 = angka_list[3]-angka_list[2]
        if selisih1 == selisih2:
            pred_berselang = angka_list[-2] + selisih1
            hasil.append(('Berselang', pred_berselang, f'Selisih berselang {selisih1}'))

    # Pola CPNS Advanced (contoh gabungan, modular, kombinasi)
    if len(angka_list) >=3:
        pred_cpns = round(sum(angka_list[-3:])/3)
        hasil.append(('CPNS Advanced', pred_cpns, 'Rata-rata 3 terakhir'))

    return hasil

def analisis_soal():
    soal = entry_soal.get()
    pilihan = entry_pilihan.get()

    if not soal:
        messagebox.showinfo("Error", "Masukkan soal deret angka dulu!")
        return

    label_jawaban.config(text="")
    label_pembahasan.config(text="")

    # Parsing angka
    angka_list = []
    try:
        parts = soal.replace('|', ',').split(',')
        for p in parts:
            if p.strip().isdigit():
                angka_list.append(int(p.strip()))
    except:
        messagebox.showinfo("Error", "Format angka tidak dikenali!")
        return

    # Coba OEIS
    try:
        query = ','.join(map(str, angka_list))
        url = f"https://oeis.org/search?q={query}&fmt=json"
        r = requests.get(url, timeout=5)
        data = r.json()
        sequences = data.get('results', [])
        if sequences:
            seq_data = sequences[0]['data'].split(',')
            jawaban = seq_data[len(angka_list)]
            label_jawaban.config(text=f"Jawaban OEIS: {jawaban}")
            label_pembahasan.config(text=f"Referensi OEIS: {sequences[0]['name']}")
            return
    except:
        pass  # fallback ke pola lokal

    # Fallback: prediksi pola lokal
    prediksi = prediksi_deret(angka_list)
    if prediksi:
        # Ambil prediksi pertama sebagai jawaban final
        nama, jawaban, penjelasan = prediksi[0]
        label_jawaban.config(text=f"Jawaban: {jawaban}")
        label_pembahasan.config(text=f"Pola: {nama} → {penjelasan}")
    else:
        label_jawaban.config(text="Tidak dapat menebak pola.")
        label_pembahasan.config(text="")

# GUI Tkinter
root = tk.Tk()
root.title("ESP Python - CPNS Deret Analyzer")
root.geometry("600x400")

tk.Label(root, text="Masukkan soal deret:", font=("Arial", 12)).pack(pady=5)
entry_soal = tk.Entry(root, width=50)
entry_soal.pack(pady=5)

tk.Label(root, text="Masukkan pilihan ganda (opsional, pisah koma):", font=("Arial", 12)).pack(pady=5)
entry_pilihan = tk.Entry(root, width=50)
entry_pilihan.pack(pady=5)

tk.Button(root, text="ANALISIS", command=analisis_soal, font=("Arial", 12, "bold")).pack(pady=10)

label_jawaban = tk.Label(root, text="", fg="green", font=("Arial", 14, "bold"))
label_jawaban.pack(pady=5)

label_pembahasan = tk.Label(root, text="", fg="blue", font=("Arial", 11))
label_pembahasan.pack(pady=5)

root.mainloop()
