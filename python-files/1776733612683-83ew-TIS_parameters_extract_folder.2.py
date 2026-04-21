# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 16:36:31 2026

@author: TingLi
"""

# -*- coding: utf-8 -*-
"""
Created on Sun Jul 28 10:08:53 2024

@author: Li Ting
"""

import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog


def select_folder():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory(title="Select the folder containing CSV files")
    return folder_path


def select_output_file():
    root = tk.Tk()
    root.withdraw()
    output_file = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        title="Save summary data as"
    )
    return output_file


def safe_get(data_line, idx):
    return data_line[idx].strip() if len(data_line) > idx else ''


def process_files():
    folder_path = select_folder()
    if not folder_path:
        print("No folder selected.")
        return

    output_file = select_output_file()
    if not output_file:
        print("No output file selected.")
        return

    summary_data = []

    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.csv'):
            file_path = os.path.join(folder_path, filename)

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                lines = file.readlines()

            if len(lines) < 6:
                print(f"Skipped {filename}: file does not have enough lines.")
                continue

            identifier = lines[2].strip()
            data_line = [x.strip() for x in lines[5].split(',')]

            dom_wl = safe_get(data_line, 5)
            peak_wl = safe_get(data_line, 6)
            cie_x = safe_get(data_line, 7)
            cie_y = safe_get(data_line, 8)
            cct = safe_get(data_line, 9)
            cri = safe_get(data_line, 10)
            fwhm = safe_get(data_line, 11)
            power_ratio = safe_get(data_line, 18)
            cb_peak_ratio = safe_get(data_line, 19)

            summary_data.append([
                identifier,
                dom_wl,
                cie_x,
                cie_y,
                cct,
                fwhm,
                power_ratio,
                cb_peak_ratio,
                peak_wl,
                cri
            ])

    summary_df = pd.DataFrame(summary_data, columns=[
        'ID',
        'Dom_WL',
        'CIE_X',
        'CIE_Y',
        'CCT',
        'FWHM',
        'Power_Ratio',
        'C/B Peak Ratio',
        'Peak_WL',
        'CRI'
    ])

    summary_df.to_csv(output_file, index=False)
    print("Data extraction and summary file creation complete.")


if __name__ == "__main__":
    process_files()