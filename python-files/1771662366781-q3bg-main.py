import tkinter as tk
from tkinter import ttk, messagebox
import math
import os

class BaseShearGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Base Shear Calculator (ASCE 7-22)")
        self.root.geometry("700x650")
        self.root.resizable(False, False)
        
        # Data storage
        self.floors = []
        self.floor_count = 0
        
        self.setup_ui()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="SEISMIC BASE SHEAR CALCULATOR", 
                                font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)
        
        sub_title = ttk.Label(main_frame, text="ASCE 7-22 Equivalent Lateral Force Procedure",
                             font=('Arial', 10))
        sub_title.grid(row=1, column=0, columnspan=3, pady=5)
        
        # Input Parameters Frame
        param_frame = ttk.LabelFrame(main_frame, text="Design Parameters", padding="10")
        param_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # SDS
        ttk.Label(param_frame, text="SDS (g):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.sds_entry = ttk.Entry(param_frame, width=15)
        self.sds_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.sds_entry.insert(0, "0.5")
        
        # SD1
        ttk.Label(param_frame, text="SD1 (g):").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.sd1_entry = ttk.Entry(param_frame, width=15)
        self.sd1_entry.grid(row=0, column=3, sticky=tk.W, padx=5)
        self.sd1_entry.insert(0, "0.3")
        
        # R
        ttk.Label(param_frame, text="R Factor:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.r_entry = ttk.Entry(param_frame, width=15)
        self.r_entry.grid(row=1, column=1, sticky=tk.W, padx=5)
        self.r_entry.insert(0, "6.0")
        
        # Ie
        ttk.Label(param_frame, text="Ie Factor:").grid(row=1, column=2, sticky=tk.W, padx=5)
        self.ie_entry = ttk.Entry(param_frame, width=15)
        self.ie_entry.grid(row=1, column=3, sticky=tk.W, padx=5)
        self.ie_entry.insert(0, "1.0")
        
        # Structure Type
        ttk.Label(param_frame, text="Structure Type:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.structure_type = tk.StringVar(value="concrete")
        ttk.Radiobutton(param_frame, text="Concrete", variable=self.structure_type, 
                       value="concrete").grid(row=2, column=1, sticky=tk.W)
        ttk.Radiobutton(param_frame, text="Steel", variable=self.structure_type,
                       value="steel").grid(row=2, column=2, sticky=tk.W)
        
        # Floor Input Frame
        floor_frame = ttk.LabelFrame(main_frame, text="Floor Data", padding="10")
        floor_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(floor_frame, text="Floor Name:").grid(row=0, column=0, padx=5)
        self.floor_name = ttk.Entry(floor_frame, width=15)
        self.floor_name.grid(row=0, column=1, padx=5)
        
        ttk.Label(floor_frame, text="Height (m):").grid(row=0, column=2, padx=5)
        self.floor_height = ttk.Entry(floor_frame, width=10)
        self.floor_height.grid(row=0, column=3, padx=5)
        
        ttk.Label(floor_frame, text="Weight (kN):").grid(row=0, column=4, padx=5)
        self.floor_weight = ttk.Entry(floor_frame, width=10)
        self.floor_weight.grid(row=0, column=5, padx=5)
        
        ttk.Button(floor_frame, text="Add Floor", command=self.add_floor).grid(row=0, column=6, padx=10)
        
        # Floor Listbox
        ttk.Label(floor_frame, text="Added Floors:").grid(row=1, column=0, columnspan=7, pady=5)
        
        list_frame = ttk.Frame(floor_frame)
        list_frame.grid(row=2, column=0, columnspan=7)
        
        self.floor_listbox = tk.Listbox(list_frame, width=70, height=5)
        self.floor_listbox.pack(side=tk.LEFT, fill=tk.BOTH)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.floor_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.floor_listbox.config(yscrollcommand=scrollbar.set)
        
        ttk.Button(floor_frame, text="Remove Selected", command=self.remove_floor).grid(row=3, column=0, columnspan=7, pady=5)
        
        # Calculate Button
        ttk.Button(main_frame, text="CALCULATE BASE SHEAR", command=self.calculate).grid(row=4, column=0, columnspan=3, pady=15)
        
        # Results Frame
        self.result_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        self.result_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.result_text = tk.Text(self.result_frame, width=80, height=12, font=('Courier', 9))
        self.result_text.pack()
        
        # Buttons Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=10)
        
        ttk.Button(button_frame, text="Save Results", command=self.save_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.root.quit).pack(side=tk.LEFT, padx=5)
    
    def add_floor(self):
        name = self.floor_name.get()
        height = self.floor_height.get()
        weight = self.floor_weight.get()
        
        if not name or not height or not weight:
            messagebox.showerror("Error", "Please fill all floor fields")
            return
        
        try:
            height = float(height)
            weight = float(weight)
            
            self.floors.append({
                'name': name,
                'height': height,
                'weight': weight
            })
            
            self.floor_listbox.insert(tk.END, f"{name}: {height} m, {weight} kN")
            
            # Clear entries
            self.floor_name.delete(0, tk.END)
            self.floor_height.delete(0, tk.END)
            self.floor_weight.delete(0, tk.END)
            
        except ValueError:
            messagebox.showerror("Error", "Height and weight must be numbers")
    
    def remove_floor(self):
        selected = self.floor_listbox.curselection()
        if selected:
            index = selected[0]
            self.floor_listbox.delete(index)
            del self.floors[index]
    
    def calculate_base_shear(self):
        # Get parameters
        SDS = float(self.sds_entry.get())
        SD1 = float(self.sd1_entry.get())
        R = float(self.r_entry.get())
        Ie = float(self.ie_entry.get())
        
        # Calculate total height and weight
        total_height = sum([f['height'] for f in self.floors])
        total_weight = sum([f['weight'] for f in self.floors])
        
        # Calculate approximate period Ta
        if self.structure_type.get() == "concrete":
            Ct, x = 0.0466, 0.9
        else:
            Ct, x = 0.0723, 0.8
        
        Ta = Ct * (total_height ** x)
        
        # Calculate Cs
        Cs = SDS / (R / Ie)
        
        # Upper limit
        TL = 8.0  # Default value, can be modified
        if Ta <= TL:
            Cs_max = SD1 / (Ta * (R / Ie))
        else:
            Cs_max = SD1 * TL / (Ta**2 * (R / Ie))
        
        # Lower limit
        Cs_min = 0.044 * SDS * Ie
        
        Cs = max(min(Cs, Cs_max), Cs_min)
        Cs = max(Cs, 0.01)
        
        # Base shear
        V = Cs * total_weight
        
        # Calculate k exponent
        if Ta < 0.5:
            k = 1.0
        elif Ta > 2.5:
            k = 2.0
        else:
            k = 1.0 + (Ta - 0.5) / 2.0
        
        # Calculate cumulative heights
        cumulative = 0
        for floor in self.floors:
            cumulative += floor['height']
            floor['z'] = cumulative
        
        # Calculate distribution
        sum_w_h_k = 0
        for floor in self.floors:
            floor['w_h_k'] = floor['weight'] * (floor['z'] ** k)
            sum_w_h_k += floor['w_h_k']
        
        forces = []
        story_shear = 0
        story_shears = []
        
        for floor in self.floors:
            Cvx = floor['w_h_k'] / sum_w_h_k
            Fx = Cvx * V
            forces.append({
                'name': floor['name'],
                'z': floor['z'],
                'weight': floor['weight'],
                'Fx': Fx
            })
        
        # Calculate story shears (from top down)
        for i in range(len(forces)-1, -1, -1):
            story_shear += forces[i]['Fx']
            story_shears.insert(0, story_shear)
        
        return {
            'total_height': total_height,
            'total_weight': total_weight,
            'Ta': Ta,
            'Cs': Cs,
            'V': V,
            'k': k,
            'forces': forces,
            'story_shears': story_shears
        }
    
    def calculate(self):
        if len(self.floors) == 0:
            messagebox.showerror("Error", "Please add at least one floor")
            return
        
        try:
            results = self.calculate_base_shear()
            self.display_results(results)
        except Exception as e:
            messagebox.showerror("Error", f"Calculation error: {str(e)}")
    
    def display_results(self, results):
        self.result_text.delete(1.0, tk.END)
        
        text = "="*70 + "\n"
        text += "BASE SHEAR ANALYSIS RESULTS (ASCE 7-22)\n"
        text += "="*70 + "\n\n"
        
        text += f"Total Building Height: {results['total_height']:.2f} m\n"
        text += f"Total Building Weight: {results['total_weight']:.2f} kN\n"
        text += f"Approximate Period Ta: {results['Ta']:.3f} sec\n"
        text += f"Seismic Coefficient Cs: {results['Cs']:.4f}\n"
        text += f"Base Shear V: {results['V']:.2f} kN\n"
        text += f"Distribution Exponent k: {results['k']:.2f}\n\n"
        
        text += "-"*70 + "\n"
        text += f"{'Floor':<12} {'Height (m)':<12} {'Weight (kN)':<12} {'Force Fx (kN)':<15} {'Story Shear (kN)':<15}\n"
        text += "-"*70 + "\n"
        
        for i, force in enumerate(results['forces']):
            text += f"{force['name']:<12} {force['z']:<12.2f} {force['weight']:<12.2f} {force['Fx']:<15.2f} {results['story_shears'][i]:<15.2f}\n"
        
        text += "="*70 + "\n"
        text += f"Sum of forces: {sum([f['Fx'] for f in results['forces']]):.2f} kN\n"
        
        self.result_text.insert(1.0, text)
        self.results_data = results
    
    def save_results(self):
        if not hasattr(self, 'results_data'):
            messagebox.showerror("Error", "No results to save")
            return
        
        filename = "base_shear_results.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.result_text.get(1.0, tk.END))
            messagebox.showinfo("Success", f"Results saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def clear_all(self):
        self.floors = []
        self.floor_listbox.delete(0, tk.END)
        self.result_text.delete(1.0, tk.END)
        self.sds_entry.delete(0, tk.END)
        self.sds_entry.insert(0, "0.5")
        self.sd1_entry.delete(0, tk.END)
        self.sd1_entry.insert(0, "0.3")
        self.r_entry.delete(0, tk.END)
        self.r_entry.insert(0, "6.0")
        self.ie_entry.delete(0, tk.END)
        self.ie_entry.insert(0, "1.0")

def main():
    root = tk.Tk()
    app = BaseShearGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()