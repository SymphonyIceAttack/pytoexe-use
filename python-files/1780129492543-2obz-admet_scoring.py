import os
import threading
import webbrowser
import tempfile
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski, Crippen, QED

def read_pdbqt_file(file_path):
    try:
        pdbqt_content = []
        mol_name = ""
        with open(file_path, 'r') as f:
            for line in f:
                if line.startswith('REMARK') and 'Name' in line:
                    parts = line.split('=')
                    if len(parts) > 1:
                        mol_name = parts[1].strip()
                if line.startswith('ATOM') or line.startswith('HETATM'):
                    pdbqt_content.append(line)
        pdb_block = ''.join(pdbqt_content)
        mol = Chem.MolFromPDBBlock(pdb_block, sanitize=True)
        return mol, mol_name
    except Exception as e:
        return None, ""

def read_sdf_file(file_path):
    try:
        supplier = Chem.SDMolSupplier(file_path, sanitize=True)
        for mol in supplier:
            if mol is not None:
                mol_name = mol.GetProp('_Name') if mol.HasProp('_Name') else ""
                return mol, mol_name
        return None, ""
    except Exception as e:
        return None, ""

def calculate_admet_descriptors(mol):
    if mol is None:
        return None
    descriptors = {}
    descriptors['MW'] = Descriptors.MolWt(mol)
    descriptors['logP'] = Crippen.MolLogP(mol)
    descriptors['HBA'] = Lipinski.NumHAcceptors(mol)
    descriptors['HBD'] = Lipinski.NumHDonors(mol)
    descriptors['TPSA'] = Descriptors.TPSA(mol)
    descriptors['RotatableBonds'] = Lipinski.NumRotatableBonds(mol)
    descriptors['AromaticRings'] = Lipinski.NumAromaticRings(mol)
    descriptors['HeavyAtoms'] = Lipinski.HeavyAtomCount(mol)
    descriptors['FractionCSP3'] = Lipinski.FractionCSP3(mol)
    descriptors['QED'] = QED.qed(mol)
    return descriptors

def evaluate_admet_profile(descriptors):
    scores = {}
    score_total = 0
    criteria_count = 0

    if descriptors['MW'] <= 500:
        scores['MW'] = 1
    else:
        scores['MW'] = max(0, 1 - (descriptors['MW'] - 500) / 500)
    score_total += scores['MW']
    criteria_count += 1

    if -2 <= descriptors['logP'] <= 5:
        scores['logP'] = 1
    else:
        if descriptors['logP'] < -2:
            scores['logP'] = max(0, 1 - (-2 - descriptors['logP']) / 2)
        else:
            scores['logP'] = max(0, 1 - (descriptors['logP'] - 5) / 5)
    score_total += scores['logP']
    criteria_count += 1

    if descriptors['HBA'] <= 10:
        scores['HBA'] = 1
    else:
        scores['HBA'] = max(0, 1 - (descriptors['HBA'] - 10) / 10)
    score_total += scores['HBA']
    criteria_count += 1

    if descriptors['HBD'] <= 5:
        scores['HBD'] = 1
    else:
        scores['HBD'] = max(0, 1 - (descriptors['HBD'] - 5) / 5)
    score_total += scores['HBD']
    criteria_count += 1

    if descriptors['TPSA'] <= 140:
        scores['TPSA'] = 1
    else:
        scores['TPSA'] = max(0, 1 - (descriptors['TPSA'] - 140) / 100)
    score_total += scores['TPSA']
    criteria_count += 1

    if descriptors['RotatableBonds'] <= 10:
        scores['RotatableBonds'] = 1
    else:
        scores['RotatableBonds'] = max(0, 1 - (descriptors['RotatableBonds'] - 10) / 10)
    score_total += scores['RotatableBonds']
    criteria_count += 1

    scores['QED'] = descriptors['QED']
    score_total += descriptors['QED']
    criteria_count += 1

    admet_score = score_total / criteria_count

    if admet_score >= 0.8:
        grade = 'A'
        assessment = '优秀 - 成药潜力高'
    elif admet_score >= 0.6:
        grade = 'B'
        assessment = '良好 - 成药潜力中等'
    elif admet_score >= 0.4:
        grade = 'C'
        assessment = '一般 - 成药潜力较低'
    else:
        grade = 'D'
        assessment = '较差 - 成药潜力低'

    scores['ADMET_Score'] = admet_score
    scores['Grade'] = grade
    scores['Assessment'] = assessment
    return scores

class ADMETApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ADMET 评分工具")
        self.root.geometry("700x750")
        self.root.resizable(False, False)

        self.pdbqt_dir = tk.StringVar(value="PDBQT")
        self.sdf_dir = tk.StringVar(value="sdf")
        self.export_dir = tk.StringVar(value="")
        self.results = []
        self.total_files = 0
        self.processed_files = 0
        self.last_export_path = ""

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(main_frame, text="ADMET 评分工具", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 20))

        dir_frame = ttk.LabelFrame(main_frame, text="文件夹设置", padding="10")
        dir_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(dir_frame, text="PDBQT 文件夹:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_frame, textvariable=self.pdbqt_dir, width=40).grid(row=0, column=1, padx=10)
        ttk.Button(dir_frame, text="浏览", command=self.browse_pdbqt).grid(row=0, column=2)

        ttk.Label(dir_frame, text="SDF 文件夹:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_frame, textvariable=self.sdf_dir, width=40).grid(row=1, column=1, padx=10)
        ttk.Button(dir_frame, text="浏览", command=self.browse_sdf).grid(row=1, column=2)

        ttk.Label(dir_frame, text="导出目录:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(dir_frame, textvariable=self.export_dir, width=40).grid(row=2, column=1, padx=10)
        ttk.Button(dir_frame, text="浏览", command=self.browse_export_dir).grid(row=2, column=2)

        smiles_frame = ttk.LabelFrame(main_frame, text="SMILES 输入", padding="10")
        smiles_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(smiles_frame, text="SMILES (格式: 分子名称,smiles 或仅smiles):").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        self.smiles_text = tk.Text(smiles_frame, height=6, width=60)
        self.smiles_text.grid(row=1, column=0, padx=10, sticky=tk.W+tk.E)
        
        smiles_scroll = ttk.Scrollbar(smiles_frame, orient=tk.VERTICAL, command=self.smiles_text.yview)
        smiles_scroll.grid(row=1, column=1, sticky=tk.N+tk.S)
        self.smiles_text.config(yscrollcommand=smiles_scroll.set)
        
        smiles_btn_frame = ttk.Frame(smiles_frame)
        smiles_btn_frame.grid(row=1, column=2, padx=5)
        ttk.Button(smiles_btn_frame, text="打开文件", command=self.open_smiles_file).pack(pady=2)
        ttk.Button(smiles_btn_frame, text="示例", command=self.insert_example).pack(pady=2)

        self.progress_frame = ttk.LabelFrame(main_frame, text="处理进度", padding="10")
        self.progress_frame.pack(fill=tk.X, pady=(0, 15))

        self.progress_bar = ttk.Progressbar(self.progress_frame, orient='horizontal', 
                                           mode='determinate', length=600)
        self.progress_bar.pack(pady=10)

        self.progress_label = ttk.Label(self.progress_frame, text="准备就绪")
        self.progress_label.pack()

        self.stats_frame = ttk.LabelFrame(main_frame, text="统计信息", padding="10")
        self.stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.stats_text = tk.Text(self.stats_frame, height=8, width=80, state=tk.DISABLED)
        self.stats_text.pack()

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))

        self.run_button = ttk.Button(button_frame, text="开始评分", command=self.run_admet)
        self.run_button.pack(side=tk.LEFT, padx=5)

        self.open_button = ttk.Button(button_frame, text="打开结果文件", 
                                     command=self.open_results, state=tk.DISABLED)
        self.open_button.pack(side=tk.LEFT, padx=5)

        self.export_button = ttk.Button(button_frame, text="导出结果", 
                                       command=self.export_results, state=tk.DISABLED)
        self.export_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="清空", command=self.clear_results).pack(side=tk.RIGHT, padx=5)

    def browse_pdbqt(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.pdbqt_dir.set(dir_path)

    def browse_sdf(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.sdf_dir.set(dir_path)

    def browse_export_dir(self):
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.export_dir.set(dir_path)

    def open_smiles_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    self.smiles_text.delete(1.0, tk.END)
                    self.smiles_text.insert(1.0, content)
                self.update_stats(f"已加载SMILES文件: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"读取文件失败: {str(e)}")

    def insert_example(self):
        self.smiles_text.delete(1.0, tk.END)
        self.smiles_text.insert(1.0, "Salicylic acid,C1=CC=C(C(=C1)C(=O)O)O")

    def update_progress(self, current, total, filename=""):
        self.processed_files = current
        self.progress_bar['value'] = (current / total) * 100
        if filename:
            self.progress_label.config(text=f"正在处理: {filename} ({current}/{total})")
        else:
            self.progress_label.config(text=f"完成: {current}/{total}")
        self.root.update_idletasks()

    def update_stats(self, text):
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.insert(tk.END, text + "\n")
        self.stats_text.config(state=tk.DISABLED)
        self.stats_text.see(tk.END)
        self.root.update_idletasks()

    def run_admet(self):
        self.run_button.config(state=tk.DISABLED)
        self.open_button.config(state=tk.DISABLED)
        self.export_button.config(state=tk.DISABLED)
        self.progress_bar['value'] = 0
        self.results = []

        self.clear_stats()
        self.update_stats("开始处理...")

        threading.Thread(target=self.process_files).start()

    def process_files(self):
        pdbqt_dir = self.pdbqt_dir.get()
        sdf_dir = self.sdf_dir.get()
        smiles_text = self.smiles_text.get(1.0, tk.END).strip()

        all_files = []
        smiles_entries = []
        
        if smiles_text:
            for line in smiles_text.split('\n'):
                line = line.strip()
                if line:
                    smiles_entries.append(line)
        
        if os.path.exists(pdbqt_dir):
            for f in os.listdir(pdbqt_dir):
                if f.endswith('.pdbqt'):
                    all_files.append(('pdbqt', os.path.join(pdbqt_dir, f)))
        
        if os.path.exists(sdf_dir):
            for f in os.listdir(sdf_dir):
                if f.endswith('.sdf'):
                    all_files.append(('sdf', os.path.join(sdf_dir, f)))

        self.total_files = len(all_files) + len(smiles_entries)
        self.processed_files = 0

        if self.total_files == 0:
            self.update_stats("没有找到任何文件")
            self.run_button.config(state=tk.NORMAL)
            return

        success_count = 0
        failed_count = 0
        grade_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0}

        current_idx = 0
        
        for idx, line in enumerate(smiles_entries):
            current_idx += 1
            parts = line.split(',', 1)
            if len(parts) == 2:
                mol_name = parts[0].strip()
                smiles_str = parts[1].strip()
            else:
                mol_name = f"SMILES_{idx + 1}"
                smiles_str = line.strip()
            
            self.update_progress(current_idx, self.total_files, mol_name)
            
            mol = Chem.MolFromSmiles(smiles_str)
            if mol is None:
                failed_count += 1
                self.update_stats(f"✗ 无法处理SMILES: {mol_name}")
                continue
            
            descriptors = calculate_admet_descriptors(mol)
            scores = evaluate_admet_profile(descriptors)
            
            result = {
                'Compound': mol_name,
                'Name': mol_name,
                'Source': 'SMILES',
                'MW': round(descriptors['MW'], 2),
                'logP': round(descriptors['logP'], 2),
                'HBA': descriptors['HBA'],
                'HBD': descriptors['HBD'],
                'TPSA': round(descriptors['TPSA'], 2),
                'RotatableBonds': descriptors['RotatableBonds'],
                'AromaticRings': descriptors['AromaticRings'],
                'FractionCSP3': round(descriptors['FractionCSP3'], 2),
                'QED': round(descriptors['QED'], 3),
                'ADMET_Score': round(scores['ADMET_Score'], 3),
                'Grade': scores['Grade'],
                'Assessment': scores['Assessment']
            }
            self.results.append(result)
            success_count += 1
            grade_counts[scores['Grade']] += 1
            self.update_stats(f"✓ {mol_name} -> 评分: {scores['ADMET_Score']:.3f} ({scores['Grade']})")

        for idx, (file_type, file_path) in enumerate(all_files):
            current_idx += 1
            filename = os.path.basename(file_path)
            self.update_progress(current_idx, self.total_files, filename)

            if file_type == 'pdbqt':
                mol, mol_name = read_pdbqt_file(file_path)
                source = os.path.basename(pdbqt_dir)
            else:
                mol, mol_name = read_sdf_file(file_path)
                source = os.path.basename(sdf_dir)

            if mol is None:
                failed_count += 1
                self.update_stats(f"✗ 无法处理: {filename}")
                continue

            descriptors = calculate_admet_descriptors(mol)
            scores = evaluate_admet_profile(descriptors)

            result = {
                'Compound': os.path.splitext(filename)[0],
                'Name': mol_name if mol_name else os.path.splitext(filename)[0],
                'Source': source,
                'MW': round(descriptors['MW'], 2),
                'logP': round(descriptors['logP'], 2),
                'HBA': descriptors['HBA'],
                'HBD': descriptors['HBD'],
                'TPSA': round(descriptors['TPSA'], 2),
                'RotatableBonds': descriptors['RotatableBonds'],
                'AromaticRings': descriptors['AromaticRings'],
                'FractionCSP3': round(descriptors['FractionCSP3'], 2),
                'QED': round(descriptors['QED'], 3),
                'ADMET_Score': round(scores['ADMET_Score'], 3),
                'Grade': scores['Grade'],
                'Assessment': scores['Assessment']
            }
            self.results.append(result)
            success_count += 1
            grade_counts[scores['Grade']] += 1
            self.update_stats(f"✓ {filename} -> 评分: {scores['ADMET_Score']:.3f} ({scores['Grade']})")

        self.update_progress(self.total_files, self.total_files)

        if success_count > 0:
            export_dir = self.export_dir.get()
            
            if not export_dir:
                if os.path.exists(self.pdbqt_dir.get()):
                    export_dir = self.pdbqt_dir.get()
                elif os.path.exists(self.sdf_dir.get()):
                    export_dir = self.sdf_dir.get()
                else:
                    export_dir = os.getcwd()
            
            csv_path = os.path.join(export_dir, 'ADMET评分表.csv')
            excel_path = os.path.join(export_dir, 'ADMET评分表.xlsx')
            self.last_export_path = excel_path
            
            df = pd.DataFrame(self.results)
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            df.to_excel(excel_path, index=False)

            self.update_stats("\n=== 统计结果 ===")
            self.update_stats(f"总计文件数: {self.total_files}")
            self.update_stats(f"成功处理: {success_count}")
            self.update_stats(f"处理失败: {failed_count}")
            self.update_stats(f"A级 (优秀): {grade_counts['A']}")
            self.update_stats(f"B级 (良好): {grade_counts['B']}")
            self.update_stats(f"C级 (一般): {grade_counts['C']}")
            self.update_stats(f"D级 (较差): {grade_counts['D']}")
            self.update_stats(f"\n结果已保存到:\n{excel_path}")

            self.open_button.config(state=tk.NORMAL)
            self.export_button.config(state=tk.NORMAL)
        else:
            self.update_stats("\n没有成功处理任何文件")

        self.run_button.config(state=tk.NORMAL)

    def clear_stats(self):
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.config(state=tk.DISABLED)

    def clear_results(self):
        self.clear_stats()
        self.progress_bar['value'] = 0
        self.progress_label.config(text="准备就绪")
        self.results = []
        self.smiles_text.delete(1.0, tk.END)
        self.open_button.config(state=tk.DISABLED)
        self.export_button.config(state=tk.DISABLED)

    def open_results(self):
        if not self.results:
            messagebox.showwarning("警告", "没有结果可显示")
            return
        
        if not self.last_export_path or not os.path.exists(self.last_export_path):
            messagebox.showwarning("警告", "结果文件不存在")
            return
        
        try:
            webbrowser.open('file://' + self.last_export_path)
            self.update_stats(f"已打开结果文件: {self.last_export_path}")
        except Exception as e:
            messagebox.showerror("错误", f"打开文件失败: {str(e)}")

    def export_results(self):
        if not self.results:
            messagebox.showwarning("警告", "没有结果可导出")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                                filetypes=[("Excel文件", "*.xlsx"),
                                                           ("CSV文件", "*.csv")])
        if file_path:
            df = pd.DataFrame(self.results)
            if file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False)
            else:
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            messagebox.showinfo("成功", f"结果已导出到:\n{file_path}")

if __name__ == '__main__':
    root = tk.Tk()
    app = ADMETApp(root)
    root.mainloop()
